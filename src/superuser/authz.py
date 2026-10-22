"""Cisco Duo Agentic Identity authorization.

Implements the client side of Duo's "Duo decides, the gateway enforces" model
for per-tool-call authorization:

- The agent authenticates as a registered non-human identity using the OAuth 2.1
  client-credentials grant, requesting scopes (and, per RFC 8707, a resource
  indicator naming the audience it intends to access).
- Before each tool runs, the call is authorized either by an explicit Duo
  decision endpoint (``authorization_url``) or, by default, by checking the
  tool's required scope against the scopes Duo granted in the token.

Only ``requests`` is needed (no extra SDK). When Duo is not configured the
authorizer degrades gracefully: calls are allowed but flagged UNGOVERNED. In
``enforce`` mode, authorization errors fail closed; in ``monitor`` they are
logged and allowed.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import requests

from .config import DuoConfig

logger = logging.getLogger("superuser.authz")


@dataclass
class AuthzDecision:
    allowed: bool
    governed: bool
    reason: str

    @classmethod
    def ungoverned(cls) -> "AuthzDecision":
        return cls(allowed=True, governed=False, reason="Duo not configured")

    @classmethod
    def allow(cls, reason: str = "authorized") -> "AuthzDecision":
        return cls(allowed=True, governed=True, reason=reason)

    @classmethod
    def deny(cls, reason: str) -> "AuthzDecision":
        return cls(allowed=False, governed=True, reason=reason)


class DuoAuthorizer:
    def __init__(self, config: DuoConfig) -> None:
        self.config = config
        self._token: str | None = None
        self._granted_scopes: set[str] = set()
        self._token_expiry: float = 0.0

    def _fetch_token(self) -> str | None:
        """Client-credentials grant; caches the token until shortly before expiry."""
        now = time.time()
        if self._token and now < self._token_expiry:
            return self._token

        data = {"grant_type": "client_credentials"}
        if self.config.scopes:
            data["scope"] = " ".join(self.config.scopes)
        if self.config.resource:
            data["resource"] = self.config.resource  # RFC 8707

        resp = requests.post(
            self.config.token_url,
            data=data,
            auth=(self.config.client_id, self.config.client_secret),
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Duo token endpoint {resp.status_code}: {resp.text[:300]}")

        body = resp.json()
        self._token = body.get("access_token")
        granted = body.get("scope", "")
        self._granted_scopes = set(granted.split()) if granted else set(self.config.scopes)
        self._token_expiry = now + int(body.get("expires_in", 300)) - 30
        return self._token

    def authorize(self, tool_name: str, arguments: dict, risk: str) -> AuthzDecision:
        if not self.config.can_enforce:
            return AuthzDecision.ungoverned()
        try:
            token = self._fetch_token()
            if not token:
                raise RuntimeError("no access token returned by Duo")

            if self.config.authorization_url:
                return self._authorize_via_endpoint(token, tool_name, arguments, risk)
            return self._authorize_via_scopes(tool_name)
        except Exception as exc:
            logger.error("Duo authorization error for %s: %s", tool_name, exc)
            if self.config.mode == "monitor":
                return AuthzDecision(True, True, f"authorization error (monitor): {exc}")
            return AuthzDecision.deny(f"authorization error: {exc}")

    def _authorize_via_scopes(self, tool_name: str) -> AuthzDecision:
        required = self.config.tool_scopes.get(tool_name)
        if required is None:
            # No scope mapping for this tool: allow but note it's unmapped.
            return AuthzDecision.allow("no scope requirement mapped")
        if required in self._granted_scopes:
            return AuthzDecision.allow(f"scope '{required}' granted")
        reason = f"missing required scope '{required}'"
        if self.config.mode == "monitor":
            logger.warning("Duo (monitor) would deny %s: %s", tool_name, reason)
            return AuthzDecision(True, True, f"{reason} (monitor)")
        return AuthzDecision.deny(reason)

    def _authorize_via_endpoint(
        self, token: str, tool_name: str, arguments: dict, risk: str
    ) -> AuthzDecision:
        resp = requests.post(
            self.config.authorization_url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
            json={
                "agent_id": self.config.agent_id,
                "resource": self.config.resource,
                "tool": tool_name,
                "action": tool_name,
                "risk": risk,
                "arguments": arguments,
            },
            timeout=15,
        )
        if resp.status_code == 403:
            return AuthzDecision.deny("Duo policy denied this tool call")
        if resp.status_code >= 400:
            raise RuntimeError(f"Duo decision endpoint {resp.status_code}: {resp.text[:300]}")

        body = resp.json() if resp.text else {}
        decision = str(body.get("decision", body.get("action", "allow"))).lower()
        if decision in ("allow", "permit", "allowed"):
            return AuthzDecision.allow(body.get("reason", "authorized by Duo"))
        reason = body.get("reason", "denied by Duo policy")
        if self.config.mode == "monitor":
            return AuthzDecision(True, True, f"{reason} (monitor)")
        return AuthzDecision.deny(reason)

    @property
    def status(self) -> dict:
        return {
            "enabled": self.config.enabled,
            "mode": self.config.mode,
            "enforcing": self.config.can_enforce,
            "agent_id": self.config.agent_id,
            "authorization": "endpoint" if self.config.authorization_url else "scopes",
        }

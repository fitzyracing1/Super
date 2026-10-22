"""Opt-in remote "phone bridge": MCP over streamable HTTP with bearer-token auth.

Binds to 127.0.0.1 by default. Expose it off-device only through an outbound
tunnel (e.g. ``cloudflared tunnel --url http://127.0.0.1:8765``). Every request
must carry ``Authorization: Bearer <token>``; the token is generated on first
run and stored at ``~/.superuser/token`` (mode 0600). The token is never logged.
All tools still go through the same Guard (approvals, guardrails, audit log).
"""

from __future__ import annotations

import hmac
import logging
import os
import secrets
from pathlib import Path
from typing import Any, Awaitable, Callable

logger = logging.getLogger("superuser.bridge")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def default_token_path() -> Path:
    env = os.environ.get("SUPERUSER_TOKEN_FILE")
    return Path(env).expanduser() if env else Path.home() / ".superuser" / "token"


def load_or_create_token(path: Path | None = None) -> str:
    """Return the bridge token, creating it (0600) on first use."""
    path = path or default_token_path()
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
            return token
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    token = secrets.token_urlsafe(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(token + "\n")
    os.chmod(path, 0o600)
    logger.warning("Bridge token saved to %s", path)
    return token


ASGIApp = Callable[[dict, Callable, Callable], Awaitable[None]]


class BearerAuthMiddleware:
    """Pure-ASGI middleware rejecting HTTP requests without the right bearer token."""

    def __init__(self, app: ASGIApp, token: str) -> None:
        if not token:
            raise ValueError("bridge token must be non-empty")
        self.app = app
        self._token = token.encode()

    def _authorized(self, scope: dict) -> bool:
        for name, value in scope.get("headers") or []:
            if name.lower() == b"authorization":
                scheme, _, cred = value.partition(b" ")
                if scheme.lower() == b"bearer" and hmac.compare_digest(cred.strip(), self._token):
                    return True
        return False

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] == "lifespan":
            await self.app(scope, receive, send)
            return
        if scope["type"] in ("http", "websocket") and not self._authorized(scope):
            client = scope.get("client") or ("?", 0)
            logger.warning("Rejected unauthenticated bridge request from %s", client[0])
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
                return
            body = b'{"error":"unauthorized"}'
            await send({
                "type": "http.response.start", "status": 401,
                "headers": [(b"content-type", b"application/json"),
                            (b"www-authenticate", b'Bearer realm="superuser"'),
                            (b"content-length", str(len(body)).encode())],
            })
            await send({"type": "http.response.body", "body": body})
            return
        await self.app(scope, receive, send)


def build_bridge_app(server: Any, token: str) -> ASGIApp:
    """Wrap a FastMCP server's streamable-HTTP app with bearer auth.

    The MCP SDK's Host-header (DNS-rebinding) check is relaxed here because the
    tunnel forwards a public hostname; the mandatory bearer token is what
    protects the endpoint (a rebinding page cannot know the token).
    """
    settings = getattr(server, "settings", None)
    if settings is not None and hasattr(settings, "transport_security"):
        try:
            from mcp.server.transport_security import TransportSecuritySettings

            settings.transport_security = TransportSecuritySettings(
                enable_dns_rebinding_protection=False
            )
        except ImportError:  # older mcp without the check
            pass
    return BearerAuthMiddleware(server.streamable_http_app(), token)


def run_bridge(server: Any, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
               token_path: Path | None = None) -> None:
    import uvicorn

    token = load_or_create_token(token_path)
    if host not in ("127.0.0.1", "localhost", "::1"):
        logger.warning("Bridge bound to %s (not loopback). Prefer 127.0.0.1 + a tunnel.", host)
    app = build_bridge_app(server, token)
    logger.info("Superuser bridge listening on http://%s:%d/mcp (bearer auth required)",
                host, port)
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=False)

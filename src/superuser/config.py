"""Configuration for the superuser agent.

Settings are resolved with the following precedence (highest first):
1. Explicit values in a YAML config file (path from ``SUPERUSER_CONFIG``).
2. Environment variables.
3. Built-in safe defaults.

The defaults are deliberately conservative: manual approval is required for
anything above low risk, and GitHub / shell writes are locked down until the
operator opts in.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

import yaml


class Risk(IntEnum):
    """Relative risk of a tool invocation. Higher means more dangerous."""

    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3

    @classmethod
    def parse(cls, value: Any) -> "Risk":
        if isinstance(value, Risk):
            return value
        if isinstance(value, int):
            return cls(value)
        return cls[str(value).strip().upper()]


# Commands that are never allowed to run, regardless of approval. These are
# blunt substring/word checks — a defense-in-depth backstop, not the primary
# control (Cisco AI Defense + approval gating are the primary controls).
DEFAULT_COMMAND_DENYLIST: tuple[str, ...] = (
    "rm -rf /",
    "mkfs",
    ":(){:|:&};:",  # fork bomb
    "dd if=/dev/zero",
    "dd if=/dev/random",
    "> /dev/sda",
    "chmod -r 000 /",
    "shutdown",
    "reboot",
    "halt",
    "poweroff",
)


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_bool(name: str, default: bool) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class CiscoConfig:
    """Cisco AI Defense runtime-guardrail settings.

    ``mode`` mirrors the AI Defense Agent Runtime SDK:
    - ``enforce``: block requests/responses that violate policy.
    - ``monitor``: log violations but allow the call through.
    - ``off``: do not call AI Defense at all.
    """

    enabled: bool = True
    mode: str = "enforce"
    # Inspection-API key used for explicit MCP tool-call inspection.
    inspection_api_key: str | None = None
    # agentsec.protect() API-mode endpoint/key for auto-patched LLM+MCP calls.
    runtime_endpoint: str | None = None
    runtime_api_key: str | None = None
    # Path to an agentsec.yaml; if present, it takes precedence for protect().
    agentsec_config_path: str | None = None

    @property
    def can_inspect(self) -> bool:
        return self.enabled and self.mode != "off" and bool(self.inspection_api_key)

    @property
    def can_protect(self) -> bool:
        return self.enabled and self.mode != "off" and bool(
            self.agentsec_config_path or (self.runtime_endpoint and self.runtime_api_key)
        )


@dataclass
class DuoConfig:
    """Cisco Duo Agentic Identity authorization settings.

    Duo follows a "Duo decides, the gateway enforces" model: per-tool-call
    authorization is evaluated against Duo's policy engine, keyed to the agent's
    registered identity and its accountable human owner. This agent
    authenticates via the OAuth 2.1 client-credentials grant (machine-to-machine)
    and checks each tool call against the scopes/policy Duo grants.

    ``mode`` mirrors the other guardrails: ``enforce`` blocks unauthorized
    calls, ``monitor`` logs them but allows, ``off`` disables.
    """

    enabled: bool = False
    mode: str = "enforce"
    agent_id: str | None = None
    token_url: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    # Optional explicit per-tool-call decision endpoint. When unset, the granted
    # OAuth scopes are used to authorize (scope-based access control).
    authorization_url: str | None = None
    # RFC 8707 resource indicator (the audience this agent intends to access).
    resource: str | None = None
    # Scopes requested at token time and/or matched per tool.
    scopes: list[str] = field(default_factory=list)
    # Map of tool name -> scope required to invoke it.
    tool_scopes: dict[str, str] = field(default_factory=dict)

    @property
    def can_enforce(self) -> bool:
        return (
            self.enabled
            and self.mode != "off"
            and bool(self.token_url and self.client_id and self.client_secret)
        )


@dataclass
class StripeConfig:
    """Stripe usage-based (metered) billing settings.

    A successful, authorized tool call emits a Stripe meter event so the agent
    can be sold on a per-action basis. Billing never blocks or fails a tool
    call — metering errors are logged and the action still returns.
    """

    enabled: bool = False
    api_key: str | None = None
    customer_id: str | None = None
    event_name: str = "superuser_tool_call"
    default_value: int = 1
    # Optional per-tool billing weights (e.g. high-risk actions cost more).
    per_tool_values: dict[str, int] = field(default_factory=dict)

    @property
    def can_bill(self) -> bool:
        return self.enabled and bool(self.api_key and self.customer_id)

    def value_for(self, tool_name: str) -> int:
        return int(self.per_tool_values.get(tool_name, self.default_value))


@dataclass
class GitHubConfig:
    """Least-privilege GitHub access settings."""

    token: str | None = None
    api_url: str = "https://api.github.com"
    # Empty means no repositories are permitted (fail closed).
    allowed_repos: list[str] = field(default_factory=list)
    allow_writes: bool = False

    def repo_allowed(self, repo: str) -> bool:
        if not self.allowed_repos:
            return False
        if "*" in self.allowed_repos:
            return True
        return repo in self.allowed_repos


@dataclass
class Config:
    """Top-level agent configuration."""

    approval_required_at: Risk = Risk.MEDIUM
    command_allowlist: list[str] = field(default_factory=list)
    command_denylist: list[str] = field(default_factory=lambda: list(DEFAULT_COMMAND_DENYLIST))
    command_timeout_seconds: int = 60
    audit_log_path: Path = field(default_factory=lambda: Path("superuser-audit.log"))
    human_owner: str = "unknown"
    cisco: CiscoConfig = field(default_factory=CiscoConfig)
    duo: DuoConfig = field(default_factory=DuoConfig)
    stripe: StripeConfig = field(default_factory=StripeConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)

    def requires_approval(self, risk: Risk) -> bool:
        return risk >= self.approval_required_at

    @classmethod
    def load(cls, config_path: str | os.PathLike[str] | None = None) -> "Config":
        cfg = cls.from_env()
        path = config_path or _env("SUPERUSER_CONFIG")
        if path and Path(path).is_file():
            cfg._apply_yaml(yaml.safe_load(Path(path).read_text()) or {})
        return cfg

    @classmethod
    def from_env(cls) -> "Config":
        cfg = cls()
        cfg.human_owner = _env("SUPERUSER_HUMAN_OWNER", cfg.human_owner)
        approval = _env("SUPERUSER_APPROVAL_AT")
        if approval:
            cfg.approval_required_at = Risk.parse(approval)
        cfg.command_timeout_seconds = int(
            _env("SUPERUSER_COMMAND_TIMEOUT", str(cfg.command_timeout_seconds))
        )
        audit = _env("SUPERUSER_AUDIT_LOG")
        if audit:
            cfg.audit_log_path = Path(audit)

        cfg.cisco = CiscoConfig(
            enabled=_env_bool("AI_DEFENSE_ENABLED", True),
            mode=_env("AI_DEFENSE_MODE", "enforce"),
            inspection_api_key=_env("AI_DEFENSE_INSPECTION_API_KEY"),
            runtime_endpoint=_env("AI_DEFENSE_API_MODE_LLM_ENDPOINT"),
            runtime_api_key=_env("AI_DEFENSE_API_MODE_LLM_API_KEY"),
            agentsec_config_path=_env("AI_DEFENSE_AGENTSEC_CONFIG"),
        )

        duo_scopes = _env("DUO_SCOPES", "")
        cfg.duo = DuoConfig(
            enabled=_env_bool("DUO_ENABLED", False),
            mode=_env("DUO_MODE", "enforce"),
            agent_id=_env("DUO_AGENT_ID"),
            token_url=_env("DUO_TOKEN_URL"),
            client_id=_env("DUO_CLIENT_ID"),
            client_secret=_env("DUO_CLIENT_SECRET"),
            authorization_url=_env("DUO_AUTHORIZATION_URL"),
            resource=_env("DUO_RESOURCE"),
            scopes=[s.strip() for s in (duo_scopes or "").split() if s.strip()],
        )

        cfg.stripe = StripeConfig(
            enabled=_env_bool("STRIPE_ENABLED", False),
            api_key=_env("STRIPE_API_KEY"),
            customer_id=_env("STRIPE_CUSTOMER_ID"),
            event_name=_env("STRIPE_METER_EVENT_NAME", "superuser_tool_call"),
            default_value=int(_env("STRIPE_DEFAULT_VALUE", "1")),
        )

        repos = _env("GITHUB_ALLOWED_REPOS", "")
        cfg.github = GitHubConfig(
            token=_env("GITHUB_TOKEN"),
            api_url=_env("GITHUB_API_URL", "https://api.github.com"),
            allowed_repos=[r.strip() for r in (repos or "").split(",") if r.strip()],
            allow_writes=_env_bool("GITHUB_ALLOW_WRITES", False),
        )
        return cfg

    def _apply_yaml(self, data: dict[str, Any]) -> None:
        if "approval_required_at" in data:
            self.approval_required_at = Risk.parse(data["approval_required_at"])
        if "command_allowlist" in data:
            self.command_allowlist = list(data["command_allowlist"] or [])
        if "command_denylist" in data:
            # Extend rather than replace, so operators can't accidentally drop
            # the built-in dangerous-command backstops.
            self.command_denylist = list(DEFAULT_COMMAND_DENYLIST) + list(
                data["command_denylist"] or []
            )
        if "command_timeout_seconds" in data:
            self.command_timeout_seconds = int(data["command_timeout_seconds"])
        if "audit_log_path" in data:
            self.audit_log_path = Path(data["audit_log_path"])
        if "human_owner" in data:
            self.human_owner = str(data["human_owner"])

        cisco = data.get("cisco") or {}
        for key in ("enabled", "mode", "inspection_api_key", "runtime_endpoint",
                    "runtime_api_key", "agentsec_config_path"):
            if key in cisco:
                setattr(self.cisco, key, cisco[key])

        duo = data.get("duo") or {}
        for key in ("enabled", "mode", "agent_id", "token_url", "client_id",
                    "client_secret", "authorization_url", "resource"):
            if key in duo:
                setattr(self.duo, key, duo[key])
        if "scopes" in duo:
            self.duo.scopes = list(duo["scopes"] or [])
        if "tool_scopes" in duo:
            self.duo.tool_scopes = dict(duo["tool_scopes"] or {})

        stripe = data.get("stripe") or {}
        for key in ("enabled", "api_key", "customer_id", "event_name", "default_value"):
            if key in stripe:
                setattr(self.stripe, key, stripe[key])
        if "per_tool_values" in stripe:
            self.stripe.per_tool_values = {
                k: int(v) for k, v in (stripe["per_tool_values"] or {}).items()
            }

        gh = data.get("github") or {}
        if "token" in gh:
            self.github.token = gh["token"]
        if "api_url" in gh:
            self.github.api_url = gh["api_url"]
        if "allowed_repos" in gh:
            self.github.allowed_repos = list(gh["allowed_repos"] or [])
        if "allow_writes" in gh:
            self.github.allow_writes = bool(gh["allow_writes"])

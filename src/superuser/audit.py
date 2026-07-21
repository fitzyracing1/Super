"""Append-only audit logging.

Every tool invocation produces an identity-correlated record:
``human owner -> agent -> tool -> action -> outcome``. This is the local
counterpart to the audit chain enforced by Cisco Duo's MCP gateway, and it is
what makes the agent's actions reviewable after the fact.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Argument keys whose values must never be written to the audit log verbatim.
_SENSITIVE_KEYS = {"token", "api_key", "apikey", "password", "secret", "authorization"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("***REDACTED***" if k.lower() in _SENSITIVE_KEYS else _redact(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_redact(v) for v in value]
    if isinstance(value, str) and len(value) > 2000:
        return value[:2000] + f"...[truncated {len(value) - 2000} chars]"
    return value


class AuditLog:
    """Thread-safe JSONL audit logger."""

    def __init__(self, path: str | os.PathLike[str], human_owner: str = "unknown") -> None:
        self.path = Path(path)
        self.human_owner = human_owner
        self._lock = threading.Lock()
        if self.path.parent and not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(
        self,
        tool: str,
        arguments: dict[str, Any],
        decision: str,
        status: str,
        *,
        risk: str | None = None,
        detail: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "human_owner": self.human_owner,
            "agent": "superuser",
            "tool": tool,
            "arguments": _redact(arguments),
            "risk": risk,
            "decision": decision,
            "status": status,
            "detail": detail,
        }
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return entry

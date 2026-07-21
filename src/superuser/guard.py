"""The guard: the single choke point every tool invocation passes through.

Order of checks for each call:
1. Cisco AI Defense inspects the tool call (may block).
2. Approval gate: risky calls require explicit ``confirm=True`` from a human.
3. The operation runs.
4. Cisco AI Defense inspects the response (may block before it is returned).
5. The outcome is written to the audit log.

Every branch produces a structured dict so the MCP client always gets a clear,
machine-readable status instead of an opaque error.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .audit import AuditLog
from .authz import DuoAuthorizer
from .billing import StripeMeter
from .config import Config, Risk
from .security import CiscoAIDefense

logger = logging.getLogger("superuser.guard")


class Guard:
    def __init__(
        self,
        config: Config,
        audit: AuditLog,
        defense: CiscoAIDefense,
        authorizer: DuoAuthorizer | None = None,
        meter: StripeMeter | None = None,
    ) -> None:
        self.config = config
        self.audit = audit
        self.defense = defense
        self.authorizer = authorizer
        self.meter = meter

    def run(
        self,
        *,
        tool_name: str,
        args: dict[str, Any],
        risk: Risk,
        op: Callable[[], Any],
        confirm: bool = False,
    ) -> dict[str, Any]:
        risk_name = risk.name

        # 1. Pre-execution inspection.
        pre = self.defense.inspect_tool_call(tool_name, args)
        if not pre.safe:
            self.audit.record(tool_name, args, decision="blocked_by_ai_defense",
                              status="denied", risk=risk_name, detail=", ".join(pre.reasons))
            return _denied(
                tool_name,
                reason="Cisco AI Defense blocked this tool call.",
                risk=risk_name,
                details=pre.reasons,
            )

        # 2. Duo Agentic Identity authorization (per-tool-call policy).
        if self.authorizer is not None:
            authz = self.authorizer.authorize(tool_name, args, risk_name)
            if not authz.allowed:
                self.audit.record(tool_name, args, decision="denied_by_duo",
                                  status="denied", risk=risk_name, detail=authz.reason)
                return _denied(
                    tool_name,
                    reason="Cisco Duo Agentic Identity denied this tool call.",
                    risk=risk_name,
                    details=[authz.reason],
                )
        else:
            authz = None

        # 3. Approval gate.
        if self.config.requires_approval(risk) and not confirm:
            self.audit.record(tool_name, args, decision="approval_required",
                              status="pending", risk=risk_name)
            return {
                "status": "approval_required",
                "tool": tool_name,
                "risk": risk_name,
                "protected": pre.protected,
                "message": (
                    f"'{tool_name}' is a {risk_name}-risk action and needs explicit "
                    "human approval. Review the arguments and call again with confirm=true."
                ),
                "arguments": args,
            }

        # 4. Execute.
        try:
            output = op()
        except Exception as exc:
            self.audit.record(tool_name, args, decision="allowed", status="error",
                              risk=risk_name, detail=str(exc))
            logger.exception("Tool %s failed", tool_name)
            return {"status": "error", "tool": tool_name, "error": str(exc)}

        # 5. Post-execution (response) inspection.
        response_payload = output if isinstance(output, dict) else {"result": output}
        post = self.defense.inspect_response(tool_name, _stringify_for_inspection(response_payload))
        if not post.safe:
            self.audit.record(tool_name, args, decision="response_blocked_by_ai_defense",
                              status="denied", risk=risk_name, detail=", ".join(post.reasons))
            return _denied(
                tool_name,
                reason="Cisco AI Defense blocked the tool response (possible data leakage).",
                risk=risk_name,
                details=post.reasons,
            )

        # 6. Meter the successful call (best-effort; never blocks).
        billing = self.meter.record(tool_name) if self.meter is not None else None

        # 7. Success audit.
        self.audit.record(tool_name, args, decision="allowed", status="success", risk=risk_name)
        response: dict[str, Any] = {
            "status": "ok",
            "tool": tool_name,
            "risk": risk_name,
            "protected": pre.protected and post.protected,
            "result": output,
        }
        if authz is not None:
            response["governed"] = authz.governed
        if billing is not None:
            response["billed"] = billing.billed
        return response


def _denied(tool_name: str, *, reason: str, risk: str, details: list[str]) -> dict[str, Any]:
    return {
        "status": "denied",
        "tool": tool_name,
        "risk": risk,
        "reason": reason,
        "details": details,
    }


def _stringify_for_inspection(payload: dict[str, Any]) -> dict[str, Any]:
    """AI Defense response inspection expects text content blocks."""
    import json

    return {"content": [{"type": "text", "text": json.dumps(payload, default=str)[:20000]}]}

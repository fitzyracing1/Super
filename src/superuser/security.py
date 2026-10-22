"""Cisco AI Defense integration.

Two layers of protection are wired in:

1. Runtime protection via ``agentsec.protect()`` — auto-patches LLM and MCP
   client libraries so every model call and tool invocation is inspected.
   Enabled once at process start.

2. Explicit MCP tool-call inspection via ``MCPInspectionClient`` — used by the
   guard before a tool runs and after it returns, so this server inspects its
   *own* tools even when the caller is not auto-patched.

The Cisco SDK is imported lazily. If it is not installed, or no credentials are
configured, the server still runs but every tool result is annotated as
UNPROTECTED so the gap is never silent.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import CiscoConfig

logger = logging.getLogger("superuser.security")


@dataclass
class InspectionResult:
    """Normalized outcome of an AI Defense inspection."""

    safe: bool
    protected: bool
    reasons: list[str]
    action: str  # "allow", "block", or "unprotected"

    @classmethod
    def unprotected(cls) -> "InspectionResult":
        return cls(safe=True, protected=False, reasons=[], action="unprotected")

    @classmethod
    def allow(cls) -> "InspectionResult":
        return cls(safe=True, protected=True, reasons=[], action="allow")

    @classmethod
    def block(cls, reasons: list[str]) -> "InspectionResult":
        return cls(safe=False, protected=True, reasons=reasons, action="block")


class CiscoAIDefense:
    """Wraps the Cisco AI Defense SDK with graceful degradation."""

    def __init__(self, config: CiscoConfig) -> None:
        self.config = config
        self._mcp_client = None
        self._protected = False
        self._available = self._probe_sdk()
        if config.enabled and not self._available:
            logger.warning(
                "Cisco AI Defense SDK not installed; tools will run UNPROTECTED. "
                "Install with: pip install 'superuser[security]'"
            )

    @staticmethod
    def _probe_sdk() -> bool:
        try:
            import aidefense  # noqa: F401
        except Exception:
            return False
        return True

    def enable_runtime_protection(self) -> bool:
        """Call agentsec.protect() to auto-patch LLM + MCP clients.

        Returns True if protection was enabled.
        """
        if not (self._available and self.config.can_protect):
            return False
        try:
            from aidefense.runtime import agentsec

            if self.config.agentsec_config_path:
                agentsec.protect(config=self.config.agentsec_config_path)
            else:
                agentsec.protect(
                    llm_integration_mode="api",
                    api_mode={
                        "llm": {
                            "mode": self.config.mode,
                            "endpoint": self.config.runtime_endpoint,
                            "api_key": self.config.runtime_api_key,
                        }
                    },
                )
            self._protected = True
            logger.info("Cisco AI Defense runtime protection enabled (mode=%s).", self.config.mode)
        except Exception as exc:  # protection must never crash the server
            logger.error("Failed to enable Cisco AI Defense runtime protection: %s", exc)
        return self._protected

    def _client(self):
        if self._mcp_client is not None:
            return self._mcp_client
        if not (self._available and self.config.can_inspect):
            return None
        try:
            from aidefense import MCPInspectionClient

            self._mcp_client = MCPInspectionClient(api_key=self.config.inspection_api_key)
        except Exception as exc:
            logger.error("Could not initialize MCPInspectionClient: %s", exc)
            self._mcp_client = None
        return self._mcp_client

    def inspect_tool_call(self, tool_name: str, arguments: dict) -> InspectionResult:
        client = self._client()
        if client is None:
            return InspectionResult.unprotected()
        try:
            result = client.inspect_tool_call(tool_name=tool_name, arguments=arguments)
            return self._normalize(result)
        except Exception as exc:
            logger.error("AI Defense tool-call inspection error: %s", exc)
            # Fail closed in enforce mode, open in monitor mode.
            if self.config.mode == "enforce":
                return InspectionResult.block([f"inspection error: {exc}"])
            return InspectionResult.unprotected()

    def inspect_response(self, tool_name: str, result_data: dict) -> InspectionResult:
        client = self._client()
        if client is None:
            return InspectionResult.unprotected()
        try:
            result = client.inspect_response(
                result_data=result_data,
                method="tools/call",
                params={"name": tool_name},
            )
            return self._normalize(result)
        except Exception as exc:
            logger.error("AI Defense response inspection error: %s", exc)
            if self.config.mode == "enforce":
                return InspectionResult.block([f"inspection error: {exc}"])
            return InspectionResult.unprotected()

    def _normalize(self, result) -> InspectionResult:
        """Map the SDK's response object onto our InspectionResult."""
        inner = getattr(result, "result", result)
        is_safe = bool(getattr(inner, "is_safe", True))
        reasons: list[str] = []
        for rule in getattr(inner, "rules", None) or []:
            name = getattr(rule, "rule_name", None) or getattr(rule, "classification", "rule")
            reasons.append(str(name))
        if is_safe:
            return InspectionResult.allow()
        # In monitor mode we surface the finding but do not block.
        if self.config.mode == "monitor":
            logger.warning("AI Defense flagged (monitor): %s", ", ".join(reasons) or "unsafe")
            return InspectionResult(safe=True, protected=True, reasons=reasons, action="allow")
        return InspectionResult.block(reasons or ["policy violation"])

    @property
    def status(self) -> dict:
        return {
            "sdk_installed": self._available,
            "enabled": self.config.enabled,
            "mode": self.config.mode,
            "runtime_protection": self._protected,
            "inspection_configured": bool(self.config.can_inspect),
        }

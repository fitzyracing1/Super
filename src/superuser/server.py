"""MCP server exposing the superuser toolset behind the guard."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from .audit import AuditLog
from .authz import DuoAuthorizer
from .billing import StripeMeter
from .config import Config, Risk
from .guard import Guard
from .security import CiscoAIDefense
from .tools import github as gh_tools
from .tools import shell as shell_tools
from .tools import system as system_tools

logger = logging.getLogger("superuser.server")


def build_server(config: Config | None = None) -> FastMCP:
    config = config or Config.load()
    audit = AuditLog(config.audit_log_path, human_owner=config.human_owner)
    defense = CiscoAIDefense(config.cisco)
    defense.enable_runtime_protection()
    authorizer = DuoAuthorizer(config.duo)
    meter = StripeMeter(config.stripe)
    guard = Guard(config, audit, defense, authorizer=authorizer, meter=meter)
    github_client = gh_tools.GitHubClient(config.github)

    mcp = FastMCP("superuser")

    # -- System inspection (low risk, read-only) --------------------------------

    @mcp.tool()
    def system_status() -> dict[str, Any]:
        """Report host, CPU, memory, and uptime for this machine."""
        return guard.run(
            tool_name="system_status", args={}, risk=Risk.LOW,
            op=system_tools.system_status,
        )

    @mcp.tool()
    def disk_usage() -> dict[str, Any]:
        """Report disk usage per mounted partition."""
        return guard.run(
            tool_name="disk_usage", args={}, risk=Risk.LOW, op=system_tools.disk_usage,
        )

    @mcp.tool()
    def list_processes(limit: int = 20, sort_by: str = "memory") -> dict[str, Any]:
        """List top processes. sort_by is 'memory' or 'cpu'."""
        return guard.run(
            tool_name="list_processes",
            args={"limit": limit, "sort_by": sort_by},
            risk=Risk.LOW,
            op=lambda: system_tools.list_processes(limit=limit, sort_by=sort_by),
        )

    # -- Shell execution (high risk, approval-gated) ----------------------------

    @mcp.tool()
    def run_command(command: str, timeout: int = 0, confirm: bool = False) -> dict[str, Any]:
        """Run a shell command on this machine.

        Non-allowlisted commands are HIGH risk and require confirm=true. Commands
        matching the dangerous-command denylist are always rejected, and every
        call is inspected by Cisco AI Defense and written to the audit log.
        """
        effective_timeout = timeout or config.command_timeout_seconds
        return guard.run(
            tool_name="run_command",
            args={"command": command, "timeout": effective_timeout},
            risk=shell_tools.classify_risk(command, config),
            confirm=confirm,
            op=lambda: shell_tools.execute_command(command, config, effective_timeout),
        )

    # -- GitHub (least-privilege) -----------------------------------------------

    @mcp.tool()
    def github_get_repo(repo: str) -> dict[str, Any]:
        """Get metadata for an allowlisted repo (e.g. 'owner/name')."""
        return guard.run(
            tool_name="github_get_repo", args={"repo": repo}, risk=Risk.LOW,
            op=lambda: github_client.get_repo(repo),
        )

    @mcp.tool()
    def github_list_issues(repo: str, state: str = "open", limit: int = 20) -> dict[str, Any]:
        """List issues for an allowlisted repo."""
        return guard.run(
            tool_name="github_list_issues",
            args={"repo": repo, "state": state, "limit": limit},
            risk=Risk.LOW,
            op=lambda: github_client.list_issues(repo, state=state, limit=limit),
        )

    @mcp.tool()
    def github_create_issue_comment(
        repo: str, issue_number: int, body: str, confirm: bool = False
    ) -> dict[str, Any]:
        """Comment on an issue/PR. Write action: requires confirm=true and GITHUB_ALLOW_WRITES."""
        return guard.run(
            tool_name="github_create_issue_comment",
            args={"repo": repo, "issue_number": issue_number, "body": body},
            risk=Risk.HIGH,
            confirm=confirm,
            op=lambda: github_client.create_issue_comment(repo, issue_number, body),
        )

    # -- Introspection -----------------------------------------------------------

    @mcp.tool()
    def security_status() -> dict[str, Any]:
        """Report the agent's guardrail configuration and Cisco AI Defense status."""
        return {
            "status": "ok",
            "result": {
                "human_owner": config.human_owner,
                "approval_required_at": config.approval_required_at.name,
                "command_allowlist": config.command_allowlist,
                "denylist_entries": len(config.command_denylist),
                "audit_log": str(config.audit_log_path),
                "github": {
                    "configured": bool(config.github.token),
                    "allowed_repos": config.github.allowed_repos,
                    "writes_allowed": config.github.allow_writes,
                },
                "cisco_ai_defense": defense.status,
                "cisco_duo_agentic_identity": authorizer.status,
                "stripe_billing": meter.status,
            },
        }

    return mcp

"""Tests for the guard, config, shell policy, and audit log."""

from __future__ import annotations

import json

import pytest

from superuser.audit import AuditLog
from superuser.config import Config, Risk
from superuser.guard import Guard
from superuser.security import CiscoAIDefense
from superuser.tools import shell as shell_tools


@pytest.fixture
def guard(tmp_path):
    config = Config()
    config.approval_required_at = Risk.MEDIUM
    config.audit_log_path = tmp_path / "audit.log"
    # Cisco disabled => unprotected but non-blocking, so we test the local gate.
    config.cisco.enabled = False
    audit = AuditLog(config.audit_log_path, human_owner="tester")
    defense = CiscoAIDefense(config.cisco)
    return Guard(config, audit, defense), config, audit


def test_low_risk_runs_without_confirmation(guard):
    g, _, _ = guard
    result = g.run(tool_name="probe", args={}, risk=Risk.LOW, op=lambda: {"ok": True})
    assert result["status"] == "ok"
    assert result["result"] == {"ok": True}


def test_high_risk_requires_confirmation(guard):
    g, _, _ = guard
    ran = {"called": False}

    def op():
        ran["called"] = True
        return "done"

    result = g.run(tool_name="danger", args={"x": 1}, risk=Risk.HIGH, op=op)
    assert result["status"] == "approval_required"
    assert ran["called"] is False


def test_high_risk_runs_with_confirmation(guard):
    g, _, _ = guard
    result = g.run(tool_name="danger", args={}, risk=Risk.HIGH, confirm=True, op=lambda: "done")
    assert result["status"] == "ok"
    assert result["result"] == "done"


def test_errors_are_captured_and_audited(guard):
    g, _, audit = guard

    def boom():
        raise RuntimeError("kaboom")

    result = g.run(tool_name="boom", args={}, risk=Risk.LOW, op=boom)
    assert result["status"] == "error"
    assert "kaboom" in result["error"]
    lines = audit.path.read_text().strip().splitlines()
    assert any(json.loads(line)["status"] == "error" for line in lines)


def test_audit_redacts_secrets(tmp_path):
    audit = AuditLog(tmp_path / "a.log", human_owner="tester")
    audit.record("t", {"token": "supersecret", "cmd": "ls"}, "allowed", "success")
    entry = json.loads(audit.path.read_text().strip())
    assert entry["arguments"]["token"] == "***REDACTED***"
    assert entry["arguments"]["cmd"] == "ls"


def test_denylist_blocks_dangerous_commands():
    config = Config()
    with pytest.raises(shell_tools.CommandRejected):
        shell_tools.execute_command("rm -rf /", config)


def test_allowlist_classifies_low_risk():
    config = Config()
    config.command_allowlist = ["ls"]
    assert shell_tools.classify_risk("ls -la", config) == Risk.LOW
    assert shell_tools.classify_risk("curl http://x", config) == Risk.HIGH


def test_command_executes_and_captures_output():
    config = Config()
    result = shell_tools.execute_command("echo hello", config)
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]


def test_github_repo_allowlist_fails_closed():
    from superuser.config import GitHubConfig
    from superuser.tools.github import GitHubClient, GitHubError

    client = GitHubClient(GitHubConfig(token="x", allowed_repos=[]))
    with pytest.raises(GitHubError):
        client.get_repo("owner/repo")

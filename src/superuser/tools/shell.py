"""Shell command execution with denylist and allowlist controls."""

from __future__ import annotations

import shlex
import subprocess
from typing import Any

from ..config import Config, Risk


class CommandRejected(Exception):
    """Raised when a command is blocked by policy before execution."""


def _matches_denylist(command: str, denylist: list[str]) -> str | None:
    normalized = " ".join(command.split()).lower()
    for pattern in denylist:
        if pattern.lower() in normalized:
            return pattern
    return None


def _base_command(command: str) -> str:
    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()
    return parts[0] if parts else ""


def classify_risk(command: str, config: Config) -> Risk:
    """Allowlisted base commands are LOW risk; everything else is HIGH."""
    if _base_command(command) in config.command_allowlist:
        return Risk.LOW
    return Risk.HIGH


def execute_command(command: str, config: Config, timeout: int | None = None) -> dict[str, Any]:
    hit = _matches_denylist(command, config.command_denylist)
    if hit is not None:
        raise CommandRejected(f"Command matches denylist entry: {hit!r}")

    timeout = timeout or config.command_timeout_seconds
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise CommandRejected(f"Command timed out after {timeout}s")

    return {
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout[-20000:],
        "stderr": completed.stderr[-20000:],
    }

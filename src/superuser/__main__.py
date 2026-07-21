"""Entry point: `superuser` / `python -m superuser`."""

from __future__ import annotations

import argparse
import logging
import sys

from .config import Config
from .server import build_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="superuser",
        description="Permission-gated superuser MCP agent with Cisco AI Defense guardrails.",
    )
    parser.add_argument("--config", help="Path to a YAML config file (or set SUPERUSER_CONFIG).")
    parser.add_argument(
        "--transport", default="stdio", choices=["stdio", "sse", "streamable-http"],
        help="MCP transport (default: stdio).",
    )
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument(
        "--check", action="store_true",
        help="Validate config and print security status, then exit (no server).",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    config = Config.load(args.config)
    server = build_server(config)

    if args.check:
        from .security import CiscoAIDefense

        defense = CiscoAIDefense(config.cisco)
        print("Superuser agent configuration OK.")
        print(f"  Human owner:          {config.human_owner}")
        print(f"  Approval required at: {config.approval_required_at.name}")
        print(f"  Audit log:            {config.audit_log_path}")
        print(f"  Cisco AI Defense:     {defense.status}")
        print(f"  GitHub configured:    {bool(config.github.token)}")
        return 0

    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

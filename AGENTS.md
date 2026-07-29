# AGENTS.md

## Cursor Cloud specific instructions

`superuser` is a **permission-gated sysadmin agent exposed over MCP** (Python 3.10+). It is a
stdio MCP server, **not** a web app — there is no HTTP port or UI by default. See `README.md`
for the full feature/config reference and the canonical install/run/test commands.

### Environment layout
- Dependencies live in a repo-root virtualenv at `.venv` (maintained by the startup update
  script). Use it via `. .venv/bin/activate` or by calling `.venv/bin/<cmd>` directly.
- The venv is built with `python3 -m venv`, which requires the `python3.12-venv` system package.
  That package is not on the stock base image; it is installed during environment setup and
  persists in the snapshot. If venv creation ever fails with an `ensurepip`/`python3-venv` error,
  that system package is missing and must be reinstalled (`apt-get install -y python3.12-venv`).
- The `[all]` extra installs the optional `cisco-aidefense-sdk` and `stripe` SDKs. All three
  integration layers (Cisco AI Defense, Cisco Duo authz, Stripe billing) **degrade gracefully**
  when SDKs/credentials are absent — the server still runs and annotates results
  (`protected` / `governed` / `billed`) rather than failing.

### Lint / test / run
- Lint: `.venv/bin/ruff check src tests`
- Tests: `.venv/bin/pytest`
- Validate config without starting the server: `.venv/bin/superuser --check`
  (set `SUPERUSER_HUMAN_OWNER`, or pass `--config <file>`).
- Start the server: `.venv/bin/superuser` — this **blocks on stdio** waiting for an MCP client;
  it does not return or open a port. To exercise tools end-to-end, connect an MCP client over
  stdio (`mcp.client.stdio`) and call tools, or use `--transport streamable-http` / `sse` for an
  HTTP transport. Do not treat a "hanging" `superuser` process as a failure — that is the server
  waiting for a client.

### Notes
- Secrets/config (`.env`, `superuser.yaml`, `agentsec.yaml`) and `*.log` audit files are
  gitignored; provide integration credentials via env vars (see `.env.example`).
- The actual application code currently lives on the feature branch / PR, not on a bare `main`.
  The update script only installs dependencies when `pyproject.toml` is present, so it is a
  safe no-op on branches that only contain the README.

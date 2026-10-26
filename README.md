# Super

<!-- mcp-name: io.github.fitzyracing1/superuser -->

A **permission-gated superuser agent** exposed over the [Model Context Protocol
(MCP)](https://modelcontextprotocol.io). It gives an AI agent real
system-administration powers on this machine — running shell commands, checking
system state, and acting on GitHub — while wrapping every action in guardrails:
a dangerous-command denylist, a human-approval gate for risky operations,
least-privilege GitHub access, an append-only audit log, and **Cisco AI Defense**
runtime inspection of every tool call and response.

The design goal is the version of a "superuser agent" you can actually ship:
powerful, but safe, auditable, and compatible with enterprise guardrails.

> **Landing site:** https://fitzyracing1.github.io/super-landing/ (source: [fitzyracing1/super-landing](https://github.com/fitzyracing1/super-landing)).
> The previous Pages site in this repo is preserved at tag `site-v1` / branch `site-archive`.

## Why it's built this way

An agent that can do *anything* as root is a liability, not a product. Buyers
(and marketplace security reviews) expect scoping, approvals, and an audit
trail. So capabilities here always pass through a single choke point — the
`Guard` — which enforces, in order:

1. **Cisco AI Defense** inspects the tool call (can block).
2. **Cisco Duo Agentic Identity** authorizes the tool call per-policy (can block).
3. **Approval gate** — anything at or above `approval_required_at` (default
   `MEDIUM`) needs an explicit `confirm=true` from a human.
4. The operation runs.
5. **Cisco AI Defense** inspects the response before it is returned (catches
   data leakage).
6. **Stripe** meters the successful call (best-effort; never blocks).
7. The outcome is written to the **audit log** as
   `human owner -> agent -> tool -> action -> outcome`.

This mirrors the enterprise model: your app owns scoping + approvals + local
audit; **Cisco AI Defense** provides runtime threat inspection at the MCP layer;
**Cisco Duo Agentic Identity** provides per-tool-call authorization tied to an
accountable human owner; and **Stripe** turns metered tool calls into revenue.

### Cisco Duo Agentic Identity (authorization)

Duo follows a "Duo decides, the gateway enforces" model. This agent registers as
a non-human identity, authenticates via the OAuth 2.1 **client-credentials**
grant (with an RFC 8707 resource indicator), and authorizes every tool call
either by matching the tool's required **scope** against what Duo granted, or by
calling an explicit Duo **decision endpoint**. Set `DUO_ENABLED=true` plus
`DUO_TOKEN_URL` / `DUO_CLIENT_ID` / `DUO_CLIENT_SECRET` (see `.env.example`). When
Duo is not configured, calls are allowed but flagged `governed: false`; in
`enforce` mode authorization errors fail closed.

### Stripe usage-based billing (monetization)

Each authorized, successful tool call emits a Stripe **meter event**
(v2 billing meter events API), so the agent can be sold per-action. Configure a
meter in Stripe, then set `STRIPE_ENABLED=true`, `STRIPE_API_KEY`,
`STRIPE_CUSTOMER_ID`, and `STRIPE_METER_EVENT_NAME`. Per-tool weights let
higher-risk actions cost more. Billing is best-effort: metering failures are
logged and never block or fail the tool call (results are annotated
`billed: true|false`).

## Tools

| Tool | Risk | Notes |
|------|------|-------|
| `system_status` | LOW | Host, CPU, memory, uptime |
| `disk_usage` | LOW | Per-partition disk usage |
| `list_processes` | LOW | Top processes by memory/cpu |
| `run_command` | HIGH* | Shell command; denylist + approval + audit |
| `github_get_repo` | LOW | Repo metadata (allowlisted repos only) |
| `github_list_issues` | LOW | Issues for an allowlisted repo |
| `github_create_issue_comment` | HIGH | Write; needs approval + `GITHUB_ALLOW_WRITES` |
| `security_status` | — | Reports the active guardrail configuration |

\* `run_command` is LOW risk only when its base command is in
`command_allowlist`; otherwise HIGH (requires `confirm=true`).

## Install

Not yet on PyPI. Install straight from git:

```bash
pip install "superuser @ git+https://github.com/fitzyracing1/Super.git"
pip install "superuser[all] @ git+https://github.com/fitzyracing1/Super.git"   # + Cisco AI Defense + Stripe SDKs
```

From a clone:

Requires Python 3.10+.

```bash
pip install -e .              # core agent (Duo authz uses requests; no extra dep)
pip install -e '.[security]'  # + Cisco AI Defense SDK (cisco-aidefense-sdk)
pip install -e '.[billing]'   # + Stripe SDK (usage-based billing)
pip install -e '.[all]'       # security + billing
pip install -e '.[dev]'       # + pytest / ruff
```

## Configure

Copy `.env.example` to `.env` (or use a YAML file — see `superuser.example.yaml`)
and set values. Key settings:

- `SUPERUSER_HUMAN_OWNER` — the human accountable for the agent's actions.
- `SUPERUSER_APPROVAL_AT` — risk threshold for the approval gate (`LOW`…`CRITICAL`).
- `AI_DEFENSE_*` — Cisco AI Defense credentials/mode (see below).
- `DUO_*` — Cisco Duo Agentic Identity authorization (see below).
- `STRIPE_*` — Stripe usage-based billing (see below).
- `GITHUB_TOKEN`, `GITHUB_ALLOWED_REPOS`, `GITHUB_ALLOW_WRITES` — least-privilege GitHub.

> For a full console-value → env-var mapping for all three services, see
> [`docs/INTEGRATIONS.md`](docs/INTEGRATIONS.md).

### Cisco AI Defense

Install the SDK (`pip install 'superuser[security]'`) and provide credentials:

- **Explicit inspection** of this server's own tool calls/responses:
  set `AI_DEFENSE_INSPECTION_API_KEY`.
- **Runtime protection** (`agentsec.protect()` auto-patches LLM + MCP clients):
  set `AI_DEFENSE_API_MODE_LLM_ENDPOINT` + `AI_DEFENSE_API_MODE_LLM_API_KEY`,
  or point `AI_DEFENSE_AGENTSEC_CONFIG` at an `agentsec.yaml`
  (see `agentsec.example.yaml`).
- `AI_DEFENSE_MODE`: `enforce` (block), `monitor` (log only), or `off`.

If the SDK is not installed or no credentials are set, the agent still runs but
every result is annotated `protected: false` / `UNPROTECTED` — the gap is never
silent. In `enforce` mode, inspection errors **fail closed** (the call is
blocked); in `monitor` mode they fail open (logged, allowed).

## Environment variables

| Area | Variables |
|------|-----------|
| Core | `SUPERUSER_CONFIG`, `SUPERUSER_HUMAN_OWNER`, `SUPERUSER_APPROVAL_AT`, `SUPERUSER_COMMAND_TIMEOUT`, `SUPERUSER_AUDIT_LOG` |
| Cisco AI Defense | `AI_DEFENSE_ENABLED` (default `true`; set `false` for local dev), `AI_DEFENSE_MODE`, `AI_DEFENSE_INSPECTION_API_KEY`, `AI_DEFENSE_API_MODE_LLM_ENDPOINT`, `AI_DEFENSE_API_MODE_LLM_API_KEY`, `AI_DEFENSE_AGENTSEC_CONFIG` |
| Cisco Duo | `DUO_ENABLED`, `DUO_MODE`, `DUO_AGENT_ID`, `DUO_TOKEN_URL`, `DUO_CLIENT_ID`, `DUO_CLIENT_SECRET`, `DUO_AUTHORIZATION_URL`, `DUO_RESOURCE`, `DUO_SCOPES` |
| Stripe | `STRIPE_ENABLED`, `STRIPE_API_KEY`, `STRIPE_CUSTOMER_ID`, `STRIPE_METER_EVENT_NAME`, `STRIPE_DEFAULT_VALUE` |
| GitHub | `GITHUB_TOKEN`, `GITHUB_ALLOWED_REPOS`, `GITHUB_ALLOW_WRITES`, `GITHUB_API_URL` |

With no keys set the server still runs: Duo and Stripe are off by default, and Cisco AI Defense runs unprotected (clearly flagged) if the SDK/keys are missing.

## Run

```bash
# Validate configuration and print guardrail/Cisco status, then exit:
superuser --check

# Start the MCP server (stdio transport, for MCP clients like Cursor/Claude):
superuser
# or: python -m superuser
```

### Register with an MCP client

Example client config (stdio):

```json
{
  "mcpServers": {
    "superuser": {
      "command": "superuser",
      "env": {
        "SUPERUSER_HUMAN_OWNER": "you@example.com",
        "AI_DEFENSE_MODE": "enforce",
        "AI_DEFENSE_INSPECTION_API_KEY": "..."
      }
    }
  }
}
```

## Test

```bash
pytest
```

## Security notes

- The dangerous-command denylist is a backstop, not the primary control. The
  primary controls are Cisco AI Defense inspection and the approval gate.
- GitHub access **fails closed**: no token or an empty repo allowlist means no
  access. Use a fine-grained, least-privilege token.
- Secrets are redacted in the audit log. Keep `.env` / `*.yaml` config files out
  of version control (already in `.gitignore`).

## License

Apache-2.0.

## Plans

This project is free, and its license stays as is. Support it through [GitHub Sponsors](https://github.com/sponsors/fitzyracing1):

- **Free**: use the code, community support.
- **Pro ($49/month)**: priority issues and support.
- **Team ($199/month)**: priority support for your team plus early access.

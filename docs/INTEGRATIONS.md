# Integration setup: Cisco AI Defense, Cisco Duo, Stripe

This document maps each external service's console values to the agent's
environment variables. **Do not commit real secrets or tenant-specific IDs** —
put them in a `.env` file (gitignored) locally, or in Cursor **Cloud Agents →
Secrets** for cloud runs. Placeholders below use `<angle brackets>`.

Verify any setup with:

```bash
superuser --check
```

---

## Cisco AI Defense (runtime threat inspection)

Console: **Cisco Security Cloud** (`security.cisco.com`; API at
`api.security.cisco.com`). Try-before-you-buy via **AI Defense: Explorer Edition**.

Install the SDK: `pip install 'superuser[security]'`.

| Console value | Env var |
|---|---|
| Inspection API key | `AI_DEFENSE_INSPECTION_API_KEY` |
| Agent Runtime (API mode) endpoint | `AI_DEFENSE_API_MODE_LLM_ENDPOINT` |
| Agent Runtime (API mode) key | `AI_DEFENSE_API_MODE_LLM_API_KEY` |
| — (enable/disable) | `AI_DEFENSE_ENABLED=true` |
| — (`enforce`\|`monitor`\|`off`) | `AI_DEFENSE_MODE=enforce` |
| Path to an `agentsec.yaml` (alt to endpoint/key) | `AI_DEFENSE_AGENTSEC_CONFIG` |

`monitor` logs violations but allows calls; `enforce` blocks them and fails
closed on inspection errors.

---

## Cisco Duo Agentic Identity (per-tool-call authorization)

Console: **Duo Admin Panel** (`admin.duosecurity.com`). No extra Python
dependency — the agent uses OAuth 2.1 client-credentials over `requests`.

### Where to find the values

1. **Configure Single Sign-On (SSO)** must be set up first (the OAuth 2.1
   authorization server lives inside Duo SSO).
2. **Application Catalog → search "OAuth 2.1 / OIDC"** → create the app.
3. **Metadata** tab → **Token URL** and **Issuer**.
4. **Scopes** tab → create `superuser.read`, `superuser.exec`, `superuser.write`.
5. **Clients** tab → **Client 1** (a confidential client) →
   **Client ID**, and **Reset Client Secret** to reveal the secret **once**
   (do this on a **desktop** browser; the reveal often fails on mobile).

| Console value | Env var |
|---|---|
| — (enable/disable) | `DUO_ENABLED=true` |
| — (`enforce`\|`monitor`\|`off`) | `DUO_MODE=enforce` |
| A name/id for this agent identity | `DUO_AGENT_ID=<agent-id>` |
| Metadata → Token URL | `DUO_TOKEN_URL=https://sso-<tenant>.sso.duosecurity.com/oauth2/<app>/token` |
| Clients → Client 1 → Client ID | `DUO_CLIENT_ID=<client-id>` |
| Clients → Client 1 → Client Secret (reset to reveal) | `DUO_CLIENT_SECRET=<secret>` |
| Scopes (space-separated) | `DUO_SCOPES=superuser.read superuser.exec superuser.write` |
| RFC 8707 resource indicator (audience), optional | `DUO_RESOURCE=<resource>` |
| Explicit decision endpoint, optional | `DUO_AUTHORIZATION_URL=<url>` |

### Scope → tool mapping

Set under `duo.tool_scopes` in `superuser.yaml` (see `superuser.example.yaml`):

| Tool | Required scope |
|---|---|
| `system_status`, `disk_usage`, `list_processes` | `superuser.read` |
| `github_get_repo`, `github_list_issues` | `superuser.read` |
| `run_command` | `superuser.exec` |
| `github_create_issue_comment` | `superuser.write` |

### Notes

- The client must support the **Client Credentials** grant (machine-to-machine).
- The **Client Secret is shown only once**, at reset time — copy it immediately.
- Without Duo configured, calls run but are flagged `governed: false`.
- `monitor` logs would-be denials without blocking; `enforce` blocks and fails
  closed on authorization errors.

---

## Stripe (usage-based billing)

Console: **Stripe Dashboard** (`dashboard.stripe.com`). Create a **billing
meter** whose event name matches `STRIPE_METER_EVENT_NAME`.

Install the SDK: `pip install 'superuser[billing]'`.

| Console value | Env var |
|---|---|
| — (enable/disable) | `STRIPE_ENABLED=true` |
| Secret API key | `STRIPE_API_KEY=sk_live_<...>` |
| Customer id to bill | `STRIPE_CUSTOMER_ID=cus_<...>` |
| Meter event name | `STRIPE_METER_EVENT_NAME=superuser_tool_call` |
| Default units per call | `STRIPE_DEFAULT_VALUE=1` |

Per-tool billing weights go under `stripe.per_tool_values` in `superuser.yaml`
(e.g. charge more for `run_command`). Billing is best-effort: metering failures
are logged and never block or fail a tool call (results annotated
`billed: true|false`).

---

## Quick local test without any credentials

Everything degrades gracefully, so you can exercise the full guard pipeline with
no external services:

```bash
DUO_ENABLED=true DUO_MODE=monitor \
AI_DEFENSE_ENABLED=false \
SUPERUSER_HUMAN_OWNER="you@example.com" \
superuser --check
```

Then register the server with an MCP client (see `README.md`) and call tools;
results will show `protected/governed/billed: false` until the respective
services are configured.

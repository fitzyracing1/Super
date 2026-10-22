# Super (superuser)

The README describes **superuser**, a permission-gated sysadmin agent exposed over MCP and wrapped in guard rails: Cisco AI Defense inspection, Cisco Duo agentic identity authorization, human approval gates, a command denylist, append-only audit logging, and Stripe usage billing.

**What `main` actually contains:** documentation and a static site, but no agent code. The README says the implementation lives on the branch `cursor/superuser-mcp-agent-1ae7` and in open PRs #1 and #2. These docs describe `main` only.

| File | Content |
|---|---|
| `README.md` | overview and links |
| `RULES.md` | guard ruleset ("one look, two fight, three listen, four break") |
| `projects-inventory.md`, `CHANGELOG.md`, `AUDIT.md` | registry, changelog and append-only audit, all auto-updated |
| `index.html` | GitHub Pages site (https://fitzyracing1.github.io/Super/) |
| `.github/workflows/merge-sync-audit.yml` | on a merged PR to `main`, appends to the inventory, changelog and audit, then pushes with `[skip ci]` |
| `CONTRIBUTING.md` | contribution rules |

There is no install or run step on `main`. The repo has no LICENSE file.

Copyright (c) 2026 Joshua Almeida

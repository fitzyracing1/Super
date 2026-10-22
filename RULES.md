# Superuser Guard Ruleset

**One look • two fight • three listen • four break**

This is the formal, listed ruleset for the superuser MCP agent and its public presence. Every action, contribution, and update must follow these rules.

## 1. Core Guard Protocol (Mandatory Sequence)
Every tool call and every contribution must survive this exact order:

1. **One look** — Cisco AI Defense inspects the request/response for threats or policy violations.
2. **Two fight** — Cisco Duo Agentic Identity + policy engine authorizes (or blocks) the action.
3. **Three listen** — Approval gate + append-only audit log. Risky actions require explicit human `confirm=true`.
4. **Four break** — Denylist blocks dangerous commands. Post-execution inspection catches leaks.

Failure at any step halts the action.

## 2. Write & Update Policy (Accepted PR Rule) — Extended

**On accepted and merged PRs to `main` (this repo or any of your linked repos), writes, updates, inventory sync, and guard-style auditing are permitted — and everything stays fully public.**

This directly extends the original Rule 2 to cover ecosystem-wide automation:

- Accepted PRs merged to `main` **automatically**:
  - Update the central `projects-inventory.md` (ecosystem registry + recent merges).
  - Append merge details to `CHANGELOG.md`.
  - Trigger site redeploy checks / verification in the dedicated workflow.
  - Log the full decision in append-only `AUDIT.md` in the exact style of the superuser guard: `[timestamp] MERGE_DECISION: PR #N by @author → main | updates: inventory+changelog+audit | outcome: success | extends Rule 2`.

- The GitHub Pages site (https://fitzyracing1.github.io/Super/) redeploys automatically on the resulting push to `main`.

- The superuser agent may perform GitHub write actions (e.g., `github_create_issue_comment` on accepted PRs or issues) only after passing the full Guard pipeline + explicit human approval.

- All writes, site updates, inventory changes, and agent actions remain public and auditable via the immutable log (`human owner → agent → tool → action → outcome`).

- No silent writes. No private deploys. No hidden state. Every merge decision is inventoried and logged.

This rule ensures contributions scale safely while preserving complete transparency and a living central projects registry.

## 3. Tool Risk Levels & Gating
| Tool                        | Default Risk | Notes                                      |
|-----------------------------|--------------|--------------------------------------------|
| system_status, disk_usage, list_processes | LOW         | Read-only system inspection                |
| run_command                 | HIGH*       | Requires denylist check + approval gate    |
| github_get_repo, github_list_issues | LOW     | Allowlisted repos only                     |
| github_create_issue_comment | HIGH        | Write action — requires approval + `GITHUB_ALLOW_WRITES` |
| security_status             | —           | Reports live guardrail status              |

* `run_command` is LOW only if the base command is in the allowlist.

## 4. Contribution & PR Rules
- All changes (site or agent code) must be submitted via Pull Request.
- High-risk changes go through the Guard review process.
- Accepted PRs = automatic public deploy for the site + advancement of the agent + central inventory update + audit log entry.
- The same 4-phase protocol applies to human contributions and agent actions alike.

## 5. Public & Auditable by Default
- The repository, all PRs, issues, audit logs, `projects-inventory.md`, and the live site are public.
- No private branches or deploys for the official presence.
- Every decision is recorded and visible.

## 6. Graceful Degradation
If any integration (Cisco AI Defense, Duo, Stripe) is missing or disabled, the system continues to run but annotates results (`protected: false`, `governed: false`, `billed: false`). In `enforce` mode, failures fail closed.

---

**This ruleset is the single source of truth.**
It lives in `RULES.md` on `main` and is linked from the public site, README, and CONTRIBUTING.md.

Violations of these rules are not permitted. The Guard enforces them.
# Contributing to Super (superuser MCP agent + public site)

Thank you for your interest in contributing! We keep everything public, auditable, and gated by the same guardrails that protect the agent.

## Core Principles

- **Public by default**: All code, PRs, issues, and audit logs are public.
- **Accepted PRs deploy publicly**: When a PR is accepted and merged to `main`, the GitHub Pages site (https://fitzyracing1.github.io/Super/) updates automatically within minutes.
- **Writes are approval-gated**: The superuser agent can perform write actions (e.g. GitHub comments on PRs/issues) only after explicit human approval through the Guard pipeline. Everything is logged.
- **Safety first**: Dangerous actions are denied or require `confirm=true`. No silent writes.

## Automatic Inventory Sync, Changelog & Audit on Accepted PRs (Rule 2 Extension)

**This is the new automated flow that directly extends Rule 2 of RULES.md.**

When a PR is accepted and merged to `main` on this repo (or any of your repos that adopt the pattern):

1. The dedicated GitHub Action (`.github/workflows/merge-sync-audit.yml`) automatically triggers.
2. It performs:
   - Update to the **central `projects-inventory.md`** — adds structured entry with PR number, title, author, merge date, and link. This becomes the living ecosystem registry.
   - Append to **`CHANGELOG.md`** — documents the change for humans.
   - Append to **append-only `AUDIT.md`** — records the decision in immutable guard-style format: `[timestamp] MERGE_DECISION: PR #N ... | outcome: success | extends: Rule 2`
   - Runs **site redeploy checks** (verifies files, confirms Pages will deploy).
3. The workflow commits the updates back to `main` (with `[skip ci]` to avoid loops).
4. GitHub Pages automatically redeploys the updated site (including the fresh inventory and audit log).

This ensures **every accepted contribution** is:
- Visible in the central projects inventory
- Documented in changelog
- Permanently logged in the public append-only audit (exactly like the superuser guard does internally)
- Part of a fresh public site deploy

No merge is silent. Everything is traceable.

See `RULES.md` §2 for the formal policy and `AUDIT.md` for the log format.

## Updating the Public Website

The live site is built from static files in the root of the `main` branch:

- `index.html` (the beautiful landing page)
- `README.md`
- Supporting docs: `RULES.md`, `CONTRIBUTING.md`, `projects-inventory.md`, `CHANGELOG.md`, `AUDIT.md`

### How to contribute to the site or docs

1. Create a feature branch from `main`
2. Edit `index.html`, `RULES.md`, `CONTRIBUTING.md`, or add/update `projects-inventory.md` etc.
3. Commit and push your branch
4. Open a Pull Request
5. Get the PR accepted and merged to `main`

→ The merge-sync workflow runs, inventory + changelog + audit are updated, and the site redeploys automatically. Everything stays fully public.

No build step required. Pure GitHub Pages + Action magic.

## Contributing to the superuser Agent

Active development happens on feature branches (currently `cursor/*` branches created with Cursor agents).

- Open PRs are listed in the repo (see PR #1 and PR #2 for current work on the guard pipeline, integrations, and dev environment).
- PRs are reviewed for safety, test coverage, and alignment with the "One look two fight three listen four break" guard protocol.
- Accepted merges advance the agent and automatically update the central inventory, changelog, and audit log.

## The Guard Pipeline Applies to Contributions Too

Even when contributing, high-risk changes go through review. Once accepted, the update becomes part of the public site, the agent codebase, **and** the central audited inventory.

## Quick Links

- [Live Public Site](https://fitzyracing1.github.io/Super/)
- [projects-inventory.md](projects-inventory.md) — Central auto-updated registry
- [CHANGELOG.md](CHANGELOG.md)
- [AUDIT.md](AUDIT.md) — Append-only merge decisions
- [Open PR #1](https://github.com/fitzyracing1/Super/pull/1) — Core MCP agent + guardrails
- [Open PR #2](https://github.com/fitzyracing1/Super/pull/2) — Dev environment & AGENTS.md
- Main branch: always the source of truth for the public site

## Questions?

Open an issue or comment on a PR. The superuser agent itself can help surface information (with approval), and all interactions are audited publicly.

---

*One look • two fight • three listen • four break*

Everything that gets accepted stays public, inventoried, changelogged, and immutably audited.
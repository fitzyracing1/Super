# Contributing to Super (superuser MCP agent + public site)

Thank you for your interest in contributing! We keep everything public, auditable, and gated by the same guardrails that protect the agent.

## Core Principles

- **Public by default**: All code, PRs, issues, and audit logs are public.
- **Accepted PRs deploy publicly**: When a PR is accepted and merged to `main`, the GitHub Pages site (https://fitzyracing1.github.io/Super/) updates automatically within minutes.
- **Writes are approval-gated**: The superuser agent can perform write actions (e.g. GitHub comments on PRs/issues) only after explicit human approval through the Guard pipeline. Everything is logged.
- **Safety first**: Dangerous actions are denied or require `confirm=true`. No silent writes.

## Updating the Public Website

The live site is built from static files in the root of the `main` branch:

- `index.html` (the beautiful landing page)
- `README.md`

### How to contribute to the site

1. Create a feature branch from `main`
2. Edit `index.html` or `README.md` (or add new static assets)
3. Commit and push your branch
4. Open a Pull Request
5. Get the PR accepted and merged to `main`

→ The site redeploys automatically and stays fully public.

No build step required. Pure GitHub Pages magic.

## Contributing to the superuser Agent

Active development happens on feature branches (currently `cursor/*` branches created with Cursor agents).

- Open PRs are listed in the repo (see PR #1 and PR #2 for current work on the guard pipeline, integrations, and dev environment).
- PRs are reviewed for safety, test coverage, and alignment with the "One look two fight three listen four break" guard protocol.
- Accepted merges advance the agent and can also update docs referenced by the public site.

## The Guard Pipeline Applies to Contributions Too

Even when contributing, high-risk changes go through review. Once accepted, the update becomes part of the public site and the agent codebase.

## Quick Links

- [Live Public Site](https://fitzyracing1.github.io/Super/)
- [Open PR #1](https://github.com/fitzyracing1/Super/pull/1) — Core MCP agent + guardrails
- [Open PR #2](https://github.com/fitzyracing1/Super/pull/2) — Dev environment & AGENTS.md
- Main branch: always the source of truth for the public site

## Questions?

Open an issue or comment on a PR. The superuser agent itself can help surface information (with approval), and all interactions are audited publicly.

---

*One look • two fight • three listen • four break*

Everything that gets accepted stays public and auditable.
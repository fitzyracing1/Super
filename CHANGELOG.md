# Changelog

All notable changes to the Super public site, RULES.md, superuser ecosystem, and automation.

> **Note**: This changelog is itself auto-updated on accepted PR merges via the merge-sync workflow.

## [Unreleased]

### Added
- **Accepted PR → Public Site / Docs Sync + Audit** (major Rule 2 extension)
  - Central `projects-inventory.md` — living ecosystem registry, auto-updated on merges
  - `CHANGELOG.md` appends on every accepted merge
  - Append-only `AUDIT.md` — guard-style immutable logging of every merge decision
  - Site redeploy checks triggered automatically in workflow
  - New GitHub Action workflow: `.github/workflows/merge-sync-audit.yml`
- Updated `RULES.md` Section 2 to formally document the new policy and automation
- Updated `CONTRIBUTING.md` with section on the automatic sync flow

### Changed
- Rule 2 now mandates inventory sync, changelog append, audit logging, and redeploy checks for every accepted merge (this repo + any of your repos adopting the pattern).

## [0.1.0] — 2026-07-21

### Added
- Initial public GitHub Pages site launch (`index.html` with full guard protocol UI)
- Formal `RULES.md` documenting the 4-phase guard protocol and Write & Update Policy
- `CONTRIBUTING.md` explaining PR process and public-by-default philosophy
- `README.md` with project overview and links to active development PRs
- References to PR #1 (Core MCP agent + guardrails + Cisco/Duo/Stripe) and PR #2 (Dev environment + AGENTS.md)

### Notes
- Repo created and seeded with public documentation while core agent development happens on feature branches (`cursor/*`).
- Everything public and auditable from day one.
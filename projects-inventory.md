# Central Projects Inventory

> **Auto-synced on every accepted & merged PR to `main`**  
> Powered by `.github/workflows/merge-sync-audit.yml` • Extends Rule 2 of RULES.md

This is the canonical, living registry of projects in the fitzyracing1 / superuser ecosystem. 

Every time a PR is accepted and merged to `main` in any participating repo, this file (plus CHANGELOG.md and AUDIT.md) is **automatically updated** with structured merge metadata by the guard-style workflow. The update commit itself triggers a fresh public GitHub Pages deploy.

## How Automation Works
- **Trigger**: `pull_request` event (closed + merged == true + base.ref == 'main')
- **Actions**:
  - Append entry to `projects-inventory.md` (this file)
  - Append to `CHANGELOG.md`
  - Append guard-style entry to append-only `AUDIT.md`
  - Run site redeploy checks (workflow step)
- **Commit**: Pushes back to `main` with `[skip ci]` to avoid loops
- **Result**: Living docs + full audit trail for every contribution

## Core Project

### fitzyracing1/Super
**Public GitHub Pages site + formal RULES.md source of truth for the superuser MCP agent.**

- **Live Site**: https://fitzyracing1.github.io/Super/
- **Focus**: Guard protocol ("One look two fight three listen four break"), public documentation, contribution workflows, and now this automatic PR-merge sync + audit system.
- **Key Files**: `index.html`, `RULES.md`, `CONTRIBUTING.md`, `README.md`, `projects-inventory.md`, `CHANGELOG.md`, `AUDIT.md`
- **Status**: Active. GitHub Pages auto-deploys on every merge to main.
- **Seed Date**: 2026-07-21 — Foundational automation for Rule 2 extension (inventory, changelog, audit logging)

## Ecosystem / Related Repos
(Selected active or notable; comprehensive history accumulates via merge entries below)

- **fitzyracing1/nexus-ai** — Nexus AI local bridge + Chrome extension that lets any local AI drive real Chrome tabs.
- **fitzyracing1/1bit** — Minimal / 1-bit computing experiments and interfaces.
- **fitzyracing1/lp5** — LP5 (large Python project).
- **fitzyracing1/bci_interface** — Brain-computer interface experiments.
- (Additional repos auto-added to inventory on their first merged PR or via manual ecosystem PRs)

## Recent Merged PRs

*(Structured entries are auto-appended here by the merge-sync-audit workflow on every successful merge to main. Newest at top or chronological append.)*

---

**Seed entry (this automation setup)**

No production merges yet. The first real accepted PR merged to `main` will trigger the first automated inventory + audit entry.

See `RULES.md` §2 and `.github/workflows/merge-sync-audit.yml` for implementation details.
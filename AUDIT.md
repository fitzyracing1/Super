# Append-Only Audit Log — Superuser Guard Extended to PR Merges

**Core Principle**: Every accepted merge decision is recorded immutably, publicly, and in the exact style of the superuser MCP agent's internal audit log (`human owner → agent → tool → action → outcome`).

This file is **append-only**. The only way to add entries is via accepted PR merge (which triggers the `merge-sync-audit` workflow) or explicit high-audit human PR. No edits, no rewrites.

## Format
```
[ISO8601_UTC] MERGE_DECISION: PR #N "Title" by @author → main | updates: projects-inventory.md + CHANGELOG.md + AUDIT.md | site_redeploy_check: passed | outcome: success | extends: Rule 2 | guard: one-look-two-fight-three-listen-four-break
```

## Log Entries

### Seed (Automation Foundation)
[2026-07-21T05:03:00Z] SEED_MERGE: Initial Rule 2 extension setup (inventory sync, changelog, append-only audit, merge-sync workflow) by @fitzyracing1 (via secure tool) → main | updates: RULES.md + projects-inventory.md + CHANGELOG.md + AUDIT.md + .github/workflows/merge-sync-audit.yml | site_redeploy_check: n/a (initial) | outcome: success | extends: Rule 2 | note: foundational commit enabling automatic sync for all future accepted PRs across repos

---

*(All future accepted PR merges to main will append their MERGE_DECISION entries here automatically. This log grows forever as an immutable public record.)*

See `RULES.md` §2 and the workflow for how this mirrors the superuser guard's own append-only audit.
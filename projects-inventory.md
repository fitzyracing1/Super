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

## Hardware Prototypes & BOM/Progress Tracking

**New capability seeded 2026-07-23**: Simple structured tracking for ambitious hardware / prototype projects (Tesla Bot Cruiser, Open Source Spaceship, Nanocraft, Organic Spin Processor, and future ones).

Fully integrated with the superuser ecosystem:
- **Structured data**: YAML blocks + Markdown BOM/progress tables in issue bodies (machine-readable + human-friendly).
- **Status & updates**: Via GitHub labels (`hardware-prototype`, project-specific) + comments.
- **Phone-first updates (voice/text)**: Use official GitHub mobile app (iOS/Android) — open relevant issue → tap comment → use built-in voice dictation (microphone). No laptop needed. Perfect for workshop, field tests, or on-the-go.
  - Example voice note: "Voice update from garage: Tesla Bot Cruiser chassis frame successfully 3D printed and vibration tested at 1500 RPM. Sourced 4x high-torque NEMA17 motors for $68 total from local supplier. Added to BOM. Overall progress bumped to 35%. Next: motor driver selection and Fusion 360 mount design."
- **Turns into GitHub Issues**: Each major project has its own issue with sub-issue support for components/tasks. Meta tracking system in #4.
- **Live Dashboard**: 
  - Filter issues by label `hardware-prototype` for overview.
  - **Recommended (user action)**: Create a GitHub Project (classic or new) named "Hardware Prototypes Tracker", add issues #4–#8 as items. Add custom fields: `Status` (single-select: Concept / Research / Early Prototyping / Testing / Complete), `Progress %` (number), `Est. BOM USD` (number), `Last Updated` (date), `Priority`. Use Table layout for BOM roll-up view, Board for Kanban workflow, Roadmap for milestones.
  - Pin project to repo sidebar for quick access.
- **Auditability**: All updates public. Future enhancements can parse YAML from comments/bodies via Actions to auto-update inventory or generate reports (extends Rule 2 automation).

**Tracked Projects (see linked issues for full BOM tables, YAML, progress logs)**:

- **#4 Hardware/Prototype Tracking + BOM/Progress System** (meta): Goal, templates, phone instructions, and ecosystem integration. Labels: hardware-prototype, bom
- **#5 [Tesla Bot Cruiser]**: Mobile robotic cruiser platform. Vision: robust locomotion + autonomy prototype. Current: 20% (Early Prototyping). Est. BOM subtotal ~$495. High priority. Labels: hardware-prototype, tesla-bot-cruiser, bom
- **#6 [Open Source Spaceship]**: Fully open modular spacecraft concepts. Current: 5% (Concept/High-level Design). Focus on subsystems like propulsion, ADCS, power. Labels: hardware-prototype, open-source-spaceship
- **#7 [Nanocraft]**: Gram-scale interstellar probe / lightsail concepts (Breakthrough Starshot inspired). Current: 10% (Research & Miniaturization). Key challenges: lightsail deployment + onboard compute mass budget. Labels: hardware-prototype, nanocraft, bom
- **#8 [Organic Spin Processor]**: Organic molecules + spintronics for next-gen low-power spin-logic processors. Current: 5% (Literature Review & Concept). Focus areas: molecular synthesis, device fab, simulation (DFT/spin dynamics). Labels: hardware-prototype, organic-spin-processor

All issues include ready-to-use YAML structured data templates for scripting/automation and detailed BOM tables. Sub-issues encouraged for granular component tracking (e.g. specific motor mounts or sail deployment tests).

This brings physical hardware prototyping into the same public, guard-railed, auditable workflow as software contributions. One look • two fight • three listen • four break.

See issues for latest comments/updates. Voice/text updates from phone directly enrich the living tracker.

## Recent Merged PRs

*(Structured entries are auto-appended here by the merge-sync-audit workflow on every successful merge to main. Newest at top or chronological append.)*

---

**First production merge (backfilled to reflect accepted PR under extended Rule 2)**

## Merged PR #3 — feat(site): add Contact Sales & Help section with direct pricing email

- **Author**: @fitzyracing1
- **Merged**: 2026-07-21 20:13 UTC
- **URL**: https://github.com/fitzyracing1/Super/pull/3
- **Action**: inventory + changelog + audit updated | site redeploy triggered

This PR added a professional Contact Sales & Help section to the public site (new navbar link + two-column cards with direct email CTA for pricing/enterprise inquiries). Keeps everything fully public, auditable, and aligned with the guard protocol. One look • two fight • three listen • four break.

**Seed entry (this automation setup)**

Automation foundation (workflow + Rule 2 docs) established prior. This backfill ensures the living central registry accurately reflects the first accepted & merged PR to `main`. All future merges (this repo + any participating ecosystem repos) will automatically trigger the full sync + audit + redeploy check.

See `RULES.md` §2 and `.github/workflows/merge-sync-audit.yml` for implementation details.
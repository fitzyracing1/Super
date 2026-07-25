# Decision Audit Log — Parallel Projects

**Lightweight system inspired by superuser’s append-only AUDIT.md**

Records key decisions across all ventures (Pie Face, 3XB, Super ecosystem, hardware prototypes, etc.).
Queryable later. Perfect for phone-based reflection.

**Core Principle**: Append-only. Never rewrite history. Every decision is timestamped, structured, and reviewable.

Format mirrors the guard spirit:
```
[ISO8601_UTC] DECISION: Project="..." | Title="..." | Reason=... | Tags=[...] | Author=... | Outcome=...
```

---

## How to use (CLI)

```bash
python decision_audit.py log --project "Pie Face" --title "..." --reason "..." --tags a,b,c
python decision_audit.py query --project "3XB"
python decision_audit.py query --keyword investor
python decision_audit.py recent --n 10
python decision_audit.py list-projects
```

Or ask the agent on your phone: “show me decisions for Pie Face” or “why did I choose X for 3XB”.

---

## Log Entries (newest first)

### [2026-07-25T10:01:33Z] Tesla Bot Cruiser

**Selected NEMA17 high-torque motors + local supplier over imported BLDC**

- **Reason**: Immediate availability, known vibration characteristics from garage tests, and $68 total cost. BLDC would require custom drivers and longer lead times. Keeps Early Prototyping velocity high.
- **Tags**: `hardware, bom, motors, sourcing`
- **Author**: @fitzyracing1
- **Outcome**: implemented

---

### [2026-07-25T10:01:32Z] Pie Face

**Chose React + Tailwind + Vite architecture**

- **Reason**: Mobile-first progressive web app needs fast iteration on phone. Existing component patterns, excellent DX, and easy static deploy to GitHub Pages. Avoided heavier frameworks to keep bundle small for field use.
- **Tags**: `architecture, frontend, mobile, pwa`
- **Author**: @fitzyracing1
- **Outcome**: implemented

---

### [2026-07-25T10:01:32Z] 3XB

**Investor outreach plan — start with CDFI / community lender network**

- **Reason**: 3XB is entity-intelligence for community lending. Warm intros via existing CDFI relationships and open-source transparency (public Super audit style) will build trust faster than cold SaaS pitches. Lead with the logic-gate policy engine demo.
- **Tags**: `investor, outreach, cdfi, strategy`
- **Author**: @fitzyracing1
- **Outcome**: in-progress

---

### [2026-07-25T10:01:32Z] Super

**Extended Rule 2 to auto-sync inventory + AUDIT.md on every accepted PR**

- **Reason**: Parallel projects need a single living registry and immutable decision trail. Automation removes human friction while preserving the one-look-two-fight-three-listen-four-break spirit. Public by default.
- **Tags**: `architecture, audit, automation, guard`
- **Author**: @fitzyracing1
- **Outcome**: implemented

---

### [2026-07-25T10:01:32Z] Nanocraft

**Prioritize lightsail deployment mechanism over onboard compute for first prototype**

- **Reason**: Mass budget is the primary constraint (gram-scale). Lightsail reliability determines mission viability; compute can be minimal or even ground-commanded for early tests. Research phase confirmed this ordering.
- **Tags**: `hardware, prototype, priority, mass-budget`
- **Author**: @fitzyracing1
- **Outcome**: recorded

---

*(This markdown is regenerated from the append-only `decisions.jsonl`. Do not edit by hand.)*

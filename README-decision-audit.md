# Decision Audit Log for Parallel Projects

Lightweight system (inspired by superuser’s `AUDIT.md` and the “one look • two fight • three listen • four break” guard protocol) that records key decisions across all ventures.

Examples of the kind of decisions it captures:
- “why I chose X architecture for Pie Face”
- “investor outreach plan for 3XB”
- hardware prioritization, BOM choices, Rule 2 extensions, etc.

**Queryable later. Perfect for phone-based reflection.**

## Files

| File | Purpose |
|------|---------|
| `tools/decision_audit.py` | CLI tool (stdlib only) |
| `decisions.jsonl` | Append-only source of truth (JSON Lines) |
| `DECISION_AUDIT.md` | Human-readable mirror (auto-regenerated) |
| `README-decision-audit.md` | This guide |

## Quick start

```bash
# From repo root
python tools/decision_audit.py seed          # only on empty log
python tools/decision_audit.py log --project "Pie Face" --title "..." --reason "..." --tags a,b
python tools/decision_audit.py query --project "3XB"
python tools/decision_audit.py query --keyword investor
python tools/decision_audit.py recent --n 10
python tools/decision_audit.py list-projects
```

## Phone workflow

1. Open this repo on GitHub mobile.
2. View `DECISION_AUDIT.md` for a clean reading experience.
3. When a decision crystallizes, either:
   - Ask the agent (“log a decision for 3XB: …”), or
   - Use the CLI from Termux / a cloud shell, or
   - Open a PR that appends to `decisions.jsonl` (or opens an issue with structured body for later harvest).

The append-only nature + structured fields make it trivial for the agent (or a future GitHub Action) to answer “why did we choose X?” months later.

## Integration notes

- Lives alongside the existing PR-merge `AUDIT.md` (which records accepted PRs).
- This log is for *human / strategic / architectural* decisions across the whole parallel-project portfolio.
- Future: optional LOW-risk MCP tool inside superuser, or auto-harvest from PRs that contain a `Decision:` footer.

One look • two fight • three listen • four break.

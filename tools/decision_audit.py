#!/usr/bin/env python3
"""
Decision Audit Log for Parallel Projects
=======================================
Lightweight, append-only system inspired by superuser's AUDIT.md / guard protocol.

Records key decisions across all ventures (Pie Face, 3XB, Super, hardware prototypes, etc.).
Queryable later. Perfect for phone-based reflection via simple CLI or agent queries.

Core principles (mirroring superuser):
- Append-only (never rewrite history)
- Public / auditable by default when pushed
- Timestamped, structured, human + machine readable
- One look / two fight / three listen / four break spirit: deliberate, logged, reviewable

Usage:
  python decision_audit.py log --project "Pie Face" --title "Chose React + Tailwind architecture" --reason "Fast mobile-first UI, existing component library, low learning curve for phone prototyping" --tags architecture,frontend,mobile
  python decision_audit.py query --project "3XB"
  python decision_audit.py query --keyword "investor"
  python decision_audit.py recent --n 5
  python decision_audit.py list-projects
  python decision_audit.py export --format md   # regenerates DECISION_AUDIT.md

Data file: decisions.jsonl (append-only JSON Lines)
Markdown mirror: DECISION_AUDIT.md (regenerated on demand or after log)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Paths (sandbox-friendly, relative to this script or CWD)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
# Prefer repo-root data files when running from tools/
REPO_ROOT = SCRIPT_DIR.parent if SCRIPT_DIR.name == "tools" else SCRIPT_DIR
DATA_FILE = REPO_ROOT / "decisions.jsonl"
MD_FILE = REPO_ROOT / "DECISION_AUDIT.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_data_file() -> None:
    if not DATA_FILE.exists():
        DATA_FILE.touch()


def load_entries() -> List[Dict[str, Any]]:
    ensure_data_file()
    entries = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # skip corrupt lines
    return entries


def append_entry(entry: Dict[str, Any]) -> None:
    ensure_data_file()
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def regenerate_markdown(entries: Optional[List[Dict[str, Any]]] = None) -> None:
    if entries is None:
        entries = load_entries()
    # Sort newest first for readability
    entries = sorted(entries, key=lambda e: e.get("ts", ""), reverse=True)

    lines = [
        "# Decision Audit Log — Parallel Projects",
        "",
        "**Lightweight system inspired by superuser’s append-only AUDIT.md**",
        "",
        "Records key decisions across all ventures (Pie Face, 3XB, Super ecosystem, hardware prototypes, etc.).",
        "Queryable later. Perfect for phone-based reflection.",
        "",
        "**Core Principle**: Append-only. Never rewrite history. Every decision is timestamped, structured, and reviewable.",
        "",
        "Format mirrors the guard spirit:",
        "```",
        "[ISO8601_UTC] DECISION: Project=\"...\" | Title=\"...\" | Reason=... | Tags=[...] | Author=... | Outcome=...",
        "```",
        "",
        "---",
        "",
        "## How to use (CLI)",
        "",
        "```bash",
        "python tools/decision_audit.py log --project \"Pie Face\" --title \"...\" --reason \"...\" --tags a,b,c",
        "python tools/decision_audit.py query --project \"3XB\"",
        "python tools/decision_audit.py query --keyword investor",
        "python tools/decision_audit.py recent --n 10",
        "python tools/decision_audit.py list-projects",
        "```",
        "",
        "Or ask the agent on your phone: “show me decisions for Pie Face” or “why did I choose X for 3XB”.",
        "",
        "---",
        "",
        "## Log Entries (newest first)",
        "",
    ]

    if not entries:
        lines.append("(No decisions logged yet. Use the `log` command to add the first entry.)")
        lines.append("")
    else:
        for e in entries:
            ts = e.get("ts", "????")
            project = e.get("project", "?")
            title = e.get("title", "?")
            reason = e.get("reason", "")
            tags = e.get("tags", [])
            author = e.get("author", "unknown")
            outcome = e.get("outcome", "recorded")
            tags_str = ", ".join(tags) if tags else "—"
            lines.append(f"### [{ts}] {project}")
            lines.append("")
            lines.append(f"**{title}**")
            lines.append("")
            lines.append(f"- **Reason**: {reason}")
            lines.append(f"- **Tags**: `{tags_str}`")
            lines.append(f"- **Author**: @{author}")
            lines.append(f"- **Outcome**: {outcome}")
            lines.append("")
            lines.append("---")
            lines.append("")

    lines.append("")
    lines.append("(This markdown is regenerated from the append-only `decisions.jsonl`. Do not edit by hand.)")
    lines.append("")

    with open(MD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_log(args: argparse.Namespace) -> None:
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    entry = {
        "ts": utc_now_iso(),
        "project": args.project.strip(),
        "title": args.title.strip(),
        "reason": args.reason.strip(),
        "tags": tags,
        "author": args.author or "fitzyracing1",
        "outcome": args.outcome or "recorded",
    }
    append_entry(entry)
    regenerate_markdown()
    print(f"✅ Logged decision for [{entry['project']}]")
    print(f"   Title : {entry['title']}")
    print(f"   TS    : {entry['ts']}")
    print(f"   File  : {DATA_FILE}")
    print(f"   MD    : {MD_FILE} (regenerated)")


def cmd_query(args: argparse.Namespace) -> None:
    entries = load_entries()
    results = entries

    if args.project:
        proj = args.project.lower()
        results = [e for e in results if proj in e.get("project", "").lower()]

    if args.keyword:
        kw = args.keyword.lower()
        results = [
            e
            for e in results
            if kw in e.get("title", "").lower()
            or kw in e.get("reason", "").lower()
            or any(kw in t.lower() for t in e.get("tags", []))
        ]

    if args.tag:
        tag = args.tag.lower()
        results = [e for e in results if any(tag == t.lower() for t in e.get("tags", []))]

    # Sort newest first
    results = sorted(results, key=lambda e: e.get("ts", ""), reverse=True)

    if not results:
        print("No matching decisions found.")
        return

    print(f"Found {len(results)} decision(s):\n")
    for e in results:
        tags_str = ", ".join(e.get("tags", [])) or "—"
        print(f"[{e.get('ts')}] {e.get('project')}")
        print(f"  Title  : {e.get('title')}")
        print(f"  Reason : {e.get('reason')}")
        print(f"  Tags   : {tags_str}")
        print(f"  Author : @{e.get('author')} | Outcome: {e.get('outcome')}")
        print()


def cmd_recent(args: argparse.Namespace) -> None:
    entries = load_entries()
    entries = sorted(entries, key=lambda e: e.get("ts", ""), reverse=True)[: args.n]
    if not entries:
        print("No decisions logged yet.")
        return
    print(f"Most recent {len(entries)} decision(s):\n")
    for e in entries:
        tags_str = ", ".join(e.get("tags", [])) or "—"
        print(f"[{e.get('ts')}] {e.get('project')} — {e.get('title')}")
        print(f"  {e.get('reason')[:120]}{'...' if len(e.get('reason','')) > 120 else ''}")
        print(f"  Tags: {tags_str}")
        print()


def cmd_list_projects(args: argparse.Namespace) -> None:
    entries = load_entries()
    projects: Dict[str, int] = {}
    for e in entries:
        p = e.get("project", "unknown")
        projects[p] = projects.get(p, 0) + 1
    if not projects:
        print("No projects yet.")
        return
    print("Projects with decision counts:")
    for p, c in sorted(projects.items(), key=lambda x: (-x[1], x[0].lower())):
        print(f"  {p}: {c}")


def cmd_export(args: argparse.Namespace) -> None:
    regenerate_markdown()
    print(f"✅ Regenerated {MD_FILE}")
    if args.format == "json":
        entries = load_entries()
        print(json.dumps(entries, indent=2, ensure_ascii=False))


def cmd_seed(args: argparse.Namespace) -> None:
    """Seed a few realistic example decisions so the log is immediately useful."""
    seeds = [
        {
            "project": "Pie Face",
            "title": "Chose React + Tailwind + Vite architecture",
            "reason": "Mobile-first progressive web app needs fast iteration on phone. Existing component patterns, excellent DX, and easy static deploy to GitHub Pages. Avoided heavier frameworks to keep bundle small for field use.",
            "tags": ["architecture", "frontend", "mobile", "pwa"],
            "outcome": "implemented",
        },
        {
            "project": "3XB",
            "title": "Investor outreach plan — start with CDFI / community lender network",
            "reason": "3XB is entity-intelligence for community lending. Warm intros via existing CDFI relationships and open-source transparency (public Super audit style) will build trust faster than cold SaaS pitches. Lead with the logic-gate policy engine demo.",
            "tags": ["investor", "outreach", "cdfi", "strategy"],
            "outcome": "in-progress",
        },
        {
            "project": "Super",
            "title": "Extended Rule 2 to auto-sync inventory + AUDIT.md on every accepted PR",
            "reason": "Parallel projects need a single living registry and immutable decision trail. Automation removes human friction while preserving the one-look-two-fight-three-listen-four-break spirit. Public by default.",
            "tags": ["architecture", "audit", "automation", "guard"],
            "outcome": "implemented",
        },
        {
            "project": "Nanocraft",
            "title": "Prioritize lightsail deployment mechanism over onboard compute for first prototype",
            "reason": "Mass budget is the primary constraint (gram-scale). Lightsail reliability determines mission viability; compute can be minimal or even ground-commanded for early tests. Research phase confirmed this ordering.",
            "tags": ["hardware", "prototype", "priority", "mass-budget"],
            "outcome": "recorded",
        },
        {
            "project": "Tesla Bot Cruiser",
            "title": "Selected NEMA17 high-torque motors + local supplier over imported BLDC",
            "reason": "Immediate availability, known vibration characteristics from garage tests, and $68 total cost. BLDC would require custom drivers and longer lead times. Keeps Early Prototyping velocity high.",
            "tags": ["hardware", "bom", "motors", "sourcing"],
            "outcome": "implemented",
        },
    ]

    existing = load_entries()
    if existing:
        print(f"Log already has {len(existing)} entries. Skipping seed (use --force to override, but not implemented for safety).")
        return

    for s in seeds:
        entry = {
            "ts": utc_now_iso(),
            "project": s["project"],
            "title": s["title"],
            "reason": s["reason"],
            "tags": s["tags"],
            "author": "fitzyracing1",
            "outcome": s["outcome"],
        }
        append_entry(entry)

    regenerate_markdown()
    print(f"✅ Seeded {len(seeds)} example decisions.")
    print(f"   Data : {DATA_FILE}")
    print(f"   MD   : {MD_FILE}")
    print("\nRun `python tools/decision_audit.py recent` or `query --project \"Pie Face\"` to explore.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decision Audit Log for Parallel Projects (inspired by superuser AUDIT)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # log
    p_log = sub.add_parser("log", help="Append a new decision")
    p_log.add_argument("--project", required=True, help="Project / venture name (e.g. Pie Face, 3XB)")
    p_log.add_argument("--title", required=True, help="Short decision title")
    p_log.add_argument("--reason", required=True, help="Why this decision was made")
    p_log.add_argument("--tags", default="", help="Comma-separated tags")
    p_log.add_argument("--author", default="fitzyracing1")
    p_log.add_argument("--outcome", default="recorded", help="recorded | implemented | in-progress | reversed")
    p_log.set_defaults(func=cmd_log)

    # query
    p_q = sub.add_parser("query", help="Search decisions")
    p_q.add_argument("--project", help="Filter by project name (substring)")
    p_q.add_argument("--keyword", help="Search title + reason + tags")
    p_q.add_argument("--tag", help="Exact tag match")
    p_q.set_defaults(func=cmd_query)

    # recent
    p_r = sub.add_parser("recent", help="Show most recent decisions")
    p_r.add_argument("--n", type=int, default=5, help="How many (default 5)")
    p_r.set_defaults(func=cmd_recent)

    # list-projects
    p_lp = sub.add_parser("list-projects", help="List projects and decision counts")
    p_lp.set_defaults(func=cmd_list_projects)

    # export
    p_e = sub.add_parser("export", help="Regenerate markdown (and optionally dump JSON)")
    p_e.add_argument("--format", choices=["md", "json"], default="md")
    p_e.set_defaults(func=cmd_export)

    # seed
    p_s = sub.add_parser("seed", help="Seed realistic example decisions (only if log is empty)")
    p_s.set_defaults(func=cmd_seed)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

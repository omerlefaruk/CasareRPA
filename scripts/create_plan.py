from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _slugify(value: str) -> str:
    slug = value.strip().lower().replace(" ", "-")
    return "".join(ch for ch in slug if ch.isalnum() or ch in ("-", "_"))


def _plan_template(title: str) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return (
        f"# Plan: {title}\n"
        f"**Created**: {today}\n"
        "**Status**: Draft\n\n"
        "## Goal\n"
        "- \n\n"
        "## Scope\n"
        "- In:\n"
        "- Out:\n\n"
        "## Phases\n"
        "1. Research (indexes, rules, prior patterns)\n"
        "2. Plan review (confirm with user)\n"
        "3. Execute (small, testable changes)\n"
        "4. Validate (tests, QA, code review)\n"
        "5. Docs (rules + guide sync)\n\n"
        "## Risks / Open Questions\n"
        "- \n\n"
        "## Files\n"
        "- \n\n"
        "## Tests\n"
        "- \n\n"
        "## Docs / Rules Updates\n"
        "- AGENTS.md + sync CLAUDE.md/GEMINI.md\n"
        "- .agent/rules/\n"
        "- .brain/\n"
        "- docs/\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a plan file in .claude/plans/.")
    parser.add_argument("name", help="Plan name (used for filename and title).")
    parser.add_argument("--title", help="Optional title override.")
    parser.add_argument("--force", action="store_true", help="Overwrite if exists.")
    args = parser.parse_args()

    root = _repo_root()
    plans_dir = root / ".claude" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)

    title = args.title or args.name
    filename = _slugify(args.name)
    if not filename.endswith(".md"):
        filename = f"{filename}.md"
    path = plans_dir / filename

    if path.exists() and not args.force:
        print(f"Plan already exists: {path}")
        return 1

    path.write_text(_plan_template(title), encoding="utf-8")
    print(f"Created plan: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

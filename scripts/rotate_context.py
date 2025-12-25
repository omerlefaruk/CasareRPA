#!/usr/bin/env python3
"""Rotate .brain/context/current.md to archive when it exceeds line limit.

Keeps current.md lean for token optimization. Archives old content to
.brain/context/archive/context-YYYY-MM-DD.md before resetting.

Usage:
    python scripts/rotate_context.py           # Auto-rotate if >50 lines
    python scripts/rotate_context.py --force   # Force rotation
    python scripts/rotate_context.py --limit 30  # Custom line limit
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# Lean template for current.md after rotation
_CURRENT_TEMPLATE = """# Current Context

**Updated**: {date} | **Branch**: {branch}

## Active Work
- **Focus**: {focus}
- **Status**: IN PROGRESS
- **Plan**: {plan}
- **Area**: {area}

## Quick References
- **Context**: `.brain/context/current.md` (this file)
- **Patterns**: `.brain/systemPatterns.md`
- **Rules**: `.brain/projectRules.md`
- **Nodes Index**: `src/casare_rpa/nodes/_index.md`

## Recent Session Archive
- See `.brain/context/recent.md` for last 7 days
- See `.brain/context/archive/` for historical sessions

---

**Note**: This file should stay under 50 lines. Archive completed work to `recent.md` or daily archive files.
"""


def _get_branch() -> str:
    """Get current git branch."""
    root = _repo_root()
    try:
        head_file = root / ".git" / "HEAD"
        if head_file.exists():
            content = head_file.read_text().strip()
            if content.startswith("ref:"):
                return content.split("/")[-1]
    except Exception:
        pass
    return "main"


def count_lines(path: Path) -> int:
    """Count non-empty lines in a file."""
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def rotate_context(
    current_path: Path,
    archive_dir: Path,
    limit: int = 50,
    force: bool = False,
) -> bool:
    """Rotate current.md to archive if it exceeds limit.

    Returns True if rotation occurred.
    """
    lines = count_lines(current_path)

    if not force and lines <= limit:
        print(f"Context has {lines} lines (limit: {limit}). No rotation needed.")
        return False

    # Archive current content
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d")
    archive_path = archive_dir / f"context-{timestamp}.md"
    archive_dir.mkdir(parents=True, exist_ok=True)

    content = current_path.read_text(encoding="utf-8")
    archive_path.write_text(content, encoding="utf-8")
    print(f"Archived {lines} lines to: {archive_path.relative_to(_repo_root())}")

    # Write lean template
    branch = _get_branch()
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    template = _CURRENT_TEMPLATE.format(
        date=date,
        branch=branch,
        focus="[Description]",
        plan="[.claude/plans/...]",
        area="[.brain/...]",
    )
    current_path.write_text(template, encoding="utf-8")
    print(f"Reset current.md to lean template ({len(template.splitlines())} lines)")

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rotate .brain/context/current.md to archive when it exceeds line limit."
    )
    parser.add_argument(
        "--file",
        default=".brain/context/current.md",
        help="Path to current context file (default: .brain/context/current.md)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Line limit threshold (default: 50)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rotation even if under limit",
    )
    args = parser.parse_args()

    root = _repo_root()
    current_path = root / args.file
    archive_dir = root / ".brain" / "context" / "archive"

    if not current_path.exists():
        print(f"Context file not found: {current_path}")
        return 1

    rotated = rotate_context(current_path, archive_dir, args.limit, args.force)
    return 0 if rotated else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Archive old plans from .brain/plans/ directory."""

import os
import shutil
import time
from pathlib import Path


def archive_old_plans(days_old: int = 30) -> int:
    """Move plans older than N days to archive/."""
    plans_dir = Path(".brain/plans")
    archive_dir = plans_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    threshold = days_old * 24 * 60 * 60
    now = time.time()
    cutoff = now - threshold

    archived = 0
    for f in plans_dir.glob("*.md"):
        if f.name in ("_index.md", ".gitkeep"):
            continue
        if os.path.getmtime(f) < cutoff:
            shutil.move(str(f), archive_dir / f.name)
            archived += 1

    print(f"Archived {archived} plans to {archive_dir}")
    return archived


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    archive_old_plans(days)

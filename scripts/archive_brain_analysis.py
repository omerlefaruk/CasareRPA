#!/usr/bin/env python3
"""Archive old .brain/analysis files to keep context lean."""

import os
import shutil
from pathlib import Path


def archive_analysis_files(days_old: int = 7) -> int:
    """Move analysis files older than N days to archive/."""
    analysis_dir = Path(".brain/analysis")
    archive_dir = analysis_dir / "archive"
    archive_dir.mkdir(exist_ok=True)

    threshold = days_old * 24 * 60 * 60
    now = os.path.getmtime(__file__)  # Use file mtime as "now"
    cutoff = now - threshold

    archived = 0
    for f in analysis_dir.glob("*.md"):
        if f.name == "_index.md":
            continue
        if os.path.getmtime(f) < cutoff:
            shutil.move(str(f), archive_dir / f.name)
            archived += 1

    print(f"Archived {archived} analysis files to {archive_dir}")
    return archived


if __name__ == "__main__":
    import sys

    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    archive_analysis_files(days)

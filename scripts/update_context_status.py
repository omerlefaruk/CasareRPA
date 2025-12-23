from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _build_entry(
    phase: str | None,
    status: str | None,
    in_progress: str | None,
    completed: str | None,
    next_step: str | None,
    notes: str | None,
) -> str:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"## Status Update ({timestamp})"]
    if phase:
        lines.append(f"- Phase: {phase}")
    if status:
        lines.append(f"- Status: {status}")
    if in_progress:
        lines.append(f"- In Progress: {in_progress}")
    if completed:
        lines.append(f"- Completed: {completed}")
    if next_step:
        lines.append(f"- Next: {next_step}")
    if notes:
        lines.append(f"- Notes: {notes}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append a status update to .brain/context/current.md."
    )
    parser.add_argument("--file", default=".brain/context/current.md")
    parser.add_argument("--phase", help="Current phase (Research/Plan/Execute/Validate/Docs).")
    parser.add_argument("--status", help="Overall status (in progress/completed/blocked).")
    parser.add_argument("--in-progress", dest="in_progress", help="What is being worked on.")
    parser.add_argument("--completed", help="What is completed.")
    parser.add_argument("--next", dest="next_step", help="Next steps.")
    parser.add_argument("--notes", help="Additional notes.")
    args = parser.parse_args()

    root = _repo_root()
    path = root / args.file
    if not path.exists():
        print(f"Context file not found: {path}")
        return 1

    entry = _build_entry(
        args.phase,
        args.status,
        args.in_progress,
        args.completed,
        args.next_step,
        args.notes,
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + entry)
    print(f"Appended status update to: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

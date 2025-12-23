from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _build_block(
    phase: str,
    in_progress: str | None,
    completed: str | None,
    next_step: str | None,
) -> str:
    lines = [f"Phase: {phase}"]
    if in_progress:
        lines.append(f"In progress: {in_progress}")
    if completed:
        lines.append(f"Completed: {completed}")
    if next_step:
        lines.append(f"Next: {next_step}")
    return "\n".join(lines)


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def _current_branch(root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), "branch", "--show-current"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return "unknown"
    branch = result.stdout.strip()
    return branch or "unknown"


def _update_header(path: Path, timestamp: str, branch: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    updated_line = f"**Updated**: {timestamp} | **Branch**: {branch}"
    for index, line in enumerate(lines):
        if line.startswith("**Updated**:"):
            lines[index] = updated_line
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    if lines:
        lines.insert(1, "")
        lines.insert(2, updated_line)
    else:
        lines = ["# Current Context", "", updated_line]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _append_to_context(path: Path, block: str, timestamp: str, branch: str) -> None:
    _update_header(path, timestamp, branch)
    entry = f"\n## Phase Report ({timestamp})\n{block}\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a phase report block and append to .brain/context/current.md.",
    )
    parser.add_argument("--phase", required=True, help="Current phase name.")
    parser.add_argument("--in-progress", dest="in_progress", help="What is in progress.")
    parser.add_argument("--completed", help="What is completed.")
    parser.add_argument("--next", dest="next_step", help="Next steps.")
    parser.add_argument(
        "--context",
        default=".brain/context/current.md",
        help="Context file to append to.",
    )
    parser.add_argument(
        "--no-append",
        action="store_true",
        help="Do not append to context file; print only.",
    )
    args = parser.parse_args()

    block = _build_block(args.phase, args.in_progress, args.completed, args.next_step)
    timestamp = _timestamp()
    branch = _current_branch(_repo_root())
    print(block)

    if args.no_append:
        return 0

    path = _repo_root() / args.context
    if not path.exists():
        print(f"Context file not found: {path}")
        return 1
    _append_to_context(path, block, timestamp, branch)
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _current_branch() -> str:
    result = subprocess.run(
        ["git", "-C", str(_repo_root()), "rev-parse", "--abbrev-ref", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def main() -> int:
    branch = _current_branch()
    if not branch:
        print("Unable to determine current branch.")
        return 1
    if branch in {"main", "master"}:
        print("Do not work on main/master. Create a worktree branch first.")
        print('Example: python scripts/create_worktree.py "feature-name"')
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

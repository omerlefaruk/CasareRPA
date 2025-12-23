from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(_repo_root()), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _branch_exists(branch: str) -> bool:
    result = _run_git(["show-ref", "--verify", f"refs/heads/{branch}"])
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a git worktree.")
    parser.add_argument("branch", help="Branch name for the worktree.")
    parser.add_argument(
        "--path",
        help="Path for the worktree (default: .worktrees/<branch>).",
    )
    parser.add_argument(
        "--base",
        default="main",
        help="Base branch if creating a new branch (default: main).",
    )
    args = parser.parse_args()

    root = _repo_root()
    worktrees_dir = root / ".worktrees"
    worktrees_dir.mkdir(parents=True, exist_ok=True)
    path = Path(args.path) if args.path else worktrees_dir / args.branch

    if path.exists():
        print(f"Worktree path already exists: {path}")
        return 1

    if _branch_exists(args.branch):
        cmd = ["worktree", "add", str(path), args.branch]
    else:
        cmd = ["worktree", "add", "-b", args.branch, str(path), args.base]

    result = _run_git(cmd)
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr.strip())
        else:
            print("Failed to create worktree.")
        return result.returncode

    print(f"Created worktree: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

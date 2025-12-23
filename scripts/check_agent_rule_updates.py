from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

POLICY_FILES = {
    ".brain/systemPatterns.md",
    ".brain/projectRules.md",
    ".brain/errors.md",
    ".brain/dependencies.md",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _diff_names_status(base: str | None) -> list[tuple[str, str]]:
    if base:
        output = _run_git(["diff", "--name-status", f"{base}...HEAD"])
    else:
        output = _run_git(["diff", "--name-status", "--cached"])
        if not output:
            output = _run_git(["diff", "--name-status", "HEAD"])
    if not output:
        return []
    rows: list[tuple[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if not parts:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            rows.append((status, parts[2]))
        elif len(parts) >= 2:
            rows.append((status, parts[1]))
    return rows


def _is_policy_path(path: str) -> bool:
    if path.startswith(".agent/"):
        return True
    if path.startswith("agent-rules/"):
        return True
    if path.startswith(".brain/docs/"):
        return True
    if path.startswith(".brain/decisions/"):
        return True
    if path in POLICY_FILES:
        return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Require AGENTS.md update when agent rules/docs change.",
    )
    parser.add_argument(
        "--base",
        help="Base ref for diff (e.g. origin/main). If omitted, uses staged diff.",
    )
    args = parser.parse_args()

    changes = _diff_names_status(args.base)
    if not changes:
        return 0

    changed_paths = {path for _, path in changes}
    policy_changes = [path for path in changed_paths if _is_policy_path(path)]
    if not policy_changes:
        return 0

    if "AGENTS.md" not in changed_paths:
        print("AGENTS.md must be updated when agent rules/docs change.")
        print("Changed policy files:")
        for path in sorted(policy_changes):
            print(f"  - {path}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

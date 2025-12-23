from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


ROOTS = (".brain/", ".agent/", "agent-rules/", "docs/")


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


def _root_for_path(path: str) -> str | None:
    for root in ROOTS:
        if path.startswith(root):
            return root
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure _index.md updates when new docs are added in .brain/ or .agent/.",
    )
    parser.add_argument(
        "--base",
        help="Base ref for diff (e.g. origin/main). If omitted, uses staged diff.",
    )
    args = parser.parse_args()

    changes = _diff_names_status(args.base)
    if not changes:
        return 0

    added_docs_by_root: dict[str, list[str]] = {}
    for status, path in changes:
        if not status.startswith("A"):
            continue
        if not path.endswith(".md"):
            continue
        if path.endswith("_index.md"):
            continue
        root = _root_for_path(path)
        if not root:
            continue
        added_docs_by_root.setdefault(root, []).append(path)

    if not added_docs_by_root:
        return 0

    changed_paths = {path for _, path in changes}
    missing_roots: list[str] = []
    missing_docs: list[str] = []
    for root, paths in added_docs_by_root.items():
        index_changed = any(
            path.endswith("_index.md") and path.startswith(root) for path in changed_paths
        )
        if not index_changed:
            missing_roots.append(root)
            missing_docs.extend(paths)

    if not missing_roots:
        return 0

    print("New docs added without updating an _index.md in the same root.")
    print("Missing index roots:")
    for root in sorted(set(missing_roots)):
        print(f"  - {root}")
    print("New docs:")
    for path in sorted(set(missing_docs)):
        print(f"  - {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

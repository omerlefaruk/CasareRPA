from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


DOC_ROOTS = (".agent/", ".brain/", "docs/", "agent-rules/")
DOC_FILES = {"AGENTS.md", "CLAUDE.md", "GEMINI.md"}


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


def _is_doc_path(path: str) -> bool:
    if path in DOC_FILES:
        return True
    return any(path.startswith(root) for root in DOC_ROOTS)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Require docs/rules updates when src/ changes.",
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
    src_changes = [path for path in changed_paths if path.startswith("src/")]
    if not src_changes:
        return 0

    doc_changes = [path for path in changed_paths if _is_doc_path(path)]
    if doc_changes:
        return 0

    print("Detected src/ changes without any docs/rules updates.")
    print("Update at least one of: AGENTS.md, docs/, .agent/, .brain/")
    print("Changed src files:")
    for path in sorted(src_changes):
        print(f"  - {path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

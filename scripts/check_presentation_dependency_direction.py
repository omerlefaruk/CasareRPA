#!/usr/bin/env python3
"""
Incremental presentation dependency direction enforcement.

Rule (target): presentation/ must not import infrastructure/ directly.

Practical rollout: this script enforces *newly added* infrastructure imports
only, so legacy violations can be migrated gradually without blocking unrelated
work.

Defaults:
- Local (pre-commit): checks staged diffs only.
- CI: checks the PR diff range if available, otherwise HEAD~1..HEAD.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path


FORBIDDEN_PREFIX = "casare_rpa.infrastructure"

# Composition roots may wire dependencies.
ALLOW_PATH_CONTAINS = (
    "src/casare_rpa/presentation/canvas/app.py",
    "src/casare_rpa/presentation/canvas/main.py",
)

_HUNK_FILE_RE = re.compile(r"^\+\+\+\s+b/(.+)$")
_ADDED_IMPORT_RE = re.compile(r"^\+\s*(from|import)\s+([a-zA-Z0-9_\.]+)")


def _repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return Path(out)
    except Exception:
        return Path(__file__).resolve().parent.parent


def _run_git(root: Path, args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True)
    except Exception:
        return ""


def _default_range() -> str:
    base = os.environ.get("GITHUB_BASE_REF", "").strip()
    if base:
        return f"origin/{base}...HEAD"
    return "HEAD~1..HEAD"


def _git_diff_text(root: Path, *, staged: bool, diff_range: str | None) -> str:
    if staged:
        return _run_git(
            root,
            ["diff", "--cached", "-U6", "--", "src/casare_rpa/presentation"],
        )
    if diff_range:
        return _run_git(
            root, ["diff", diff_range, "-U6", "--", "src/casare_rpa/presentation"]
        )
    return _run_git(
        root, ["diff", _default_range(), "-U6", "--", "src/casare_rpa/presentation"]
    )


def _iter_added_imports_with_type_checking(diff_text: str) -> list[tuple[str, int, str, str]]:
    """
    Returns [(path, approx_line, module, raw_line), ...] for added imports.
    Attempts to ignore imports added inside `if TYPE_CHECKING:` blocks using
    hunk context.
    """
    results: list[tuple[str, int, str, str]] = []
    current_file: str | None = None
    approx_line = 0
    type_checking_indent: int | None = None

    def _indent_of(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    for raw in diff_text.splitlines():
        m_file = _HUNK_FILE_RE.match(raw)
        if m_file:
            current_file = m_file.group(1)
            approx_line = 0
            type_checking_indent = None
            continue

        if raw.startswith("@@ "):
            type_checking_indent = None
            try:
                plus = raw.split("+", 1)[1]
                start = plus.split(",", 1)[0]
                approx_line = int(start)
            except Exception:
                approx_line = 0
            continue

        if current_file is None:
            continue

        # Track entering/leaving TYPE_CHECKING blocks using context/additions.
        if raw.startswith((" ", "+")) and "if TYPE_CHECKING:" in raw:
            type_checking_indent = _indent_of(raw[1:])

        if raw.startswith((" ", "+")) and type_checking_indent is not None:
            if raw.strip() and not raw.strip().startswith(("#", "elif", "else")):
                current_indent = _indent_of(raw[1:])
                if current_indent <= type_checking_indent and "if TYPE_CHECKING:" not in raw:
                    type_checking_indent = None

        if raw.startswith("+") and not raw.startswith("+++"):
            m_imp = _ADDED_IMPORT_RE.match(raw)
            if m_imp:
                # If this import is inside a TYPE_CHECKING block, ignore it.
                if type_checking_indent is not None and _indent_of(raw[1:]) > type_checking_indent:
                    approx_line += 1
                    continue
                results.append((current_file, approx_line, m_imp.group(2), raw[1:].rstrip()))
            approx_line += 1
        elif raw.startswith(" ") and approx_line:
            approx_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            continue

    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all presentation files (strict; will fail on legacy debt).",
    )
    parser.add_argument(
        "--range",
        dest="diff_range",
        default=None,
        help="Git diff range for CI (e.g. origin/main...HEAD). Ignored with --all.",
    )
    parser.add_argument(
        "--no-staged",
        action="store_true",
        help="Do not use staged diff; useful for local ad-hoc checks.",
    )
    args = parser.parse_args()

    root = _repo_root()
    pres_root = root / "src" / "casare_rpa" / "presentation"
    if not pres_root.exists():
        return 0

    if args.all:
        failures: list[str] = []
        for file in pres_root.rglob("*.py"):
            rel = file.relative_to(root).as_posix()
            if any(token in rel for token in ALLOW_PATH_CONTAINS):
                continue
            text = file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                if stripped.startswith(("import ", "from ")) and FORBIDDEN_PREFIX in stripped:
                    failures.append(f"{rel}:{i} - forbidden import: {stripped}")
        if failures:
            print("[ERROR] Presentation dependency direction violations (strict scan):")
            for f in failures[:50]:
                print(f"  {f}")
            if len(failures) > 50:
                print(f"  ... and {len(failures) - 50} more")
            return 1
        return 0

    diff_text = _git_diff_text(root, staged=not args.no_staged, diff_range=args.diff_range)
    if not diff_text.strip():
        return 0

    failures: list[str] = []
    for path, approx_line, module, raw_line in _iter_added_imports_with_type_checking(diff_text):
        if not path.endswith(".py") or not path.startswith("src/casare_rpa/presentation/"):
            continue
        if any(token in path for token in ALLOW_PATH_CONTAINS):
            continue
        if module.startswith(FORBIDDEN_PREFIX):
            failures.append(f"{path}:{approx_line} - new forbidden import: {raw_line}")

    if failures:
        print("[ERROR] New presentation → infrastructure import violations detected:")
        for f in failures:
            print(f"  {f}")
        print()
        print("Fix: move the dependency behind an application port/use-case, or wire it in a composition root.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


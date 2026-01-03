#!/usr/bin/env python3
"""
Incremental application purity enforcement.

Rule (target): application/ must not import infrastructure/ or presentation/.

Practical rollout: this script enforces *newly added* forbidden imports only,
so legacy violations can be migrated gradually without blocking unrelated work.

Defaults:
- Local (pre-commit): checks staged diffs only.
- CI: checks the PR diff range if available, otherwise HEAD~1..HEAD.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_PREFIXES = (
    "casare_rpa.infrastructure",
    "casare_rpa.presentation",
)

# Treat nodes as “outer layer” for application purity (can be relaxed if needed)
FORBIDDEN_NODES_PREFIX = "casare_rpa.nodes"

# Composition/wiring is allowed to reference infrastructure.
ALLOW_PATH_CONTAINS = (
    "src/casare_rpa/application/dependency_injection/",
)

# Current known transitional dependency (node instantiation) – track via registry.
ALLOW_NODES_IMPORT_IN = (
    "src/casare_rpa/application/use_cases/execute_workflow.py",
    "src/casare_rpa/application/use_cases/subflow_executor.py",
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
        return _run_git(root, ["diff", "--cached", "-U3", "--", "src/casare_rpa/application"])
    if diff_range:
        return _run_git(root, ["diff", diff_range, "-U3", "--", "src/casare_rpa/application"])
    return _run_git(root, ["diff", _default_range(), "-U3", "--", "src/casare_rpa/application"])


def _iter_added_imports(diff_text: str) -> list[tuple[str, int, str, str]]:
    """
    Returns [(path, approx_line, module, raw_line), ...] from unified diff.
    Note: line numbers are approximate (hunk context dependent); good enough
    for actionable errors.
    """
    results: list[tuple[str, int, str, str]] = []
    current_file: str | None = None
    approx_line = 0

    for raw in diff_text.splitlines():
        m_file = _HUNK_FILE_RE.match(raw)
        if m_file:
            current_file = m_file.group(1)
            approx_line = 0
            continue

        if raw.startswith("@@ "):
            # @@ -a,b +c,d @@
            try:
                plus = raw.split("+", 1)[1]
                start = plus.split(",", 1)[0]
                approx_line = int(start)
            except Exception:
                approx_line = 0
            continue

        if current_file is None:
            continue

        if raw.startswith("+") and not raw.startswith("+++"):
            m_imp = _ADDED_IMPORT_RE.match(raw)
            if m_imp:
                results.append((current_file, approx_line, m_imp.group(2), raw[1:].rstrip()))
            approx_line += 1
        elif raw.startswith(" ") and approx_line:
            approx_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            # removed line does not advance new-file line number
            continue

    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all application files (strict; will fail on legacy debt).",
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
    app_root = root / "src" / "casare_rpa" / "application"
    if not app_root.exists():
        return 0

    if args.all:
        # Strict mode: scan current file contents.
        failures: list[str] = []
        for file in app_root.rglob("*.py"):
            rel = file.relative_to(root).as_posix()
            if any(token in rel for token in ALLOW_PATH_CONTAINS):
                continue
            text = file.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(text.splitlines(), 1):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if not ("import " in line or "from " in line):
                    continue
                if any(prefix in line for prefix in FORBIDDEN_PREFIXES):
                    failures.append(f"{rel}:{i} - forbidden import: {line.strip()}")
                if FORBIDDEN_NODES_PREFIX in line and rel not in ALLOW_NODES_IMPORT_IN:
                    failures.append(f"{rel}:{i} - forbidden import: {line.strip()}")
        if failures:
            print("[ERROR] Application purity violations (strict scan):")
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
    for path, approx_line, module, raw_line in _iter_added_imports(diff_text):
        if not path.endswith(".py"):
            continue
        if not path.startswith("src/casare_rpa/application/"):
            continue
        if any(token in path for token in ALLOW_PATH_CONTAINS):
            continue
        if module.startswith(FORBIDDEN_NODES_PREFIX) and path not in ALLOW_NODES_IMPORT_IN:
            failures.append(f"{path}:{approx_line} - new forbidden import: {raw_line}")
            continue
        if any(module.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
            failures.append(f"{path}:{approx_line} - new forbidden import: {raw_line}")

    if failures:
        print("[ERROR] New application purity violations detected:")
        for f in failures:
            print(f"  {f}")
        print()
        print("Fix: move IO/framework deps to infrastructure and depend on ports in application.")
        print("If this is wiring, keep it under application/dependency_injection/.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

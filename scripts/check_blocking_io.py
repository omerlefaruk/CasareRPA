#!/usr/bin/env python3
"""
Detect blocking I/O operations in async functions.
Block: time.sleep(), open() (not async), blocking file operations.
"""

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

BLOCKING_CALLS = {
    "sleep",
    "open",
}


class BlockingIOChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        self.in_async_func = False

    def visit_AsyncFunctionDef(self, node):
        old_async = self.in_async_func
        self.in_async_func = True
        self.generic_visit(node)
        self.in_async_func = old_async

    def visit_Call(self, node):
        if self.in_async_func:
            # Check function name
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKING_CALLS:
                    self.errors.append(
                        f"{self.filepath}:{node.lineno} - Blocking call '{node.func.id}()' in async function"
                    )
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in BLOCKING_CALLS:
                    self.errors.append(
                        f"{self.filepath}:{node.lineno} - Blocking call '{node.func.attr}()' in async function"
                    )
        self.generic_visit(node)


def check_file(filepath: str) -> list[str]:
    """Check for blocking I/O in async functions"""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        checker = BlockingIOChecker(filepath)
        checker.visit(tree)
        return checker.errors
    except Exception:
        return []


def _get_staged_python_files(base_dir: Path, src_dir: Path) -> list[Path]:
    try:
        output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=base_dir,
            text=True,
        )
    except Exception:
        return []

    staged_files: list[Path] = []
    for raw in output.splitlines():
        raw = raw.strip()
        if not raw or not raw.endswith(".py"):
            continue
        path = (base_dir / raw).resolve()
        if not path.is_file():
            continue
        if not path.is_relative_to(src_dir):
            continue
        staged_files.append(path)

    return staged_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all Python files under src/casare_rpa instead of only staged files.",
    )
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    src_dir = base / "src" / "casare_rpa"

    if not src_dir.exists():
        return 0

    all_errors = []
    if args.all:
        for root, _, files in os.walk(src_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    errors = check_file(filepath)
                    all_errors.extend(errors)
    else:
        staged_files = _get_staged_python_files(base, src_dir)
        if not staged_files:
            return 0
        for path in staged_files:
            errors = check_file(str(path))
            all_errors.extend(errors)

    if all_errors:
        print(
            "[ERROR] Blocking I/O in async context (use async alternatives like asyncio.sleep, aiofiles):"
        )
        for error in all_errors[:10]:
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

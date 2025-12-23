#!/usr/bin/env python3
"""
Detect blocking I/O operations in async functions.
Block: time.sleep(), open() (not async), blocking file operations.
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

BLOCKING_CALLS = {
    "sleep",
    "open",
}


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


def _changed_paths() -> list[str]:
    output = _run_git(["diff", "--name-only", "--cached"])
    if not output:
        output = _run_git(["diff", "--name-only", "HEAD"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


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


def main() -> int:
    base = Path(__file__).parent.parent
    src_dir = base / "src" / "casare_rpa"

    if not src_dir.exists():
        return 0

    changed = _changed_paths()
    if not changed:
        return 0

    all_errors: list[str] = []
    for rel_path in changed:
        if not rel_path.endswith(".py"):
            continue

        abs_path = base / rel_path
        if not abs_path.exists():
            continue

        normalized = str(abs_path).replace("\\", "/")
        if "/src/casare_rpa/" not in normalized:
            continue
        if "/tests/" in normalized or "__pycache__" in normalized:
            continue

        all_errors.extend(check_file(str(abs_path)))

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

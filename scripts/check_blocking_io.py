#!/usr/bin/env python3
"""
Detect blocking I/O operations in async functions.
Block: time.sleep(), open() (not async), blocking file operations.
"""

import ast
import os
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


def main():
    base = Path(__file__).parent.parent
    src_dir = base / "src" / "casare_rpa"

    if not src_dir.exists():
        return 0

    all_errors = []
    for root, _, files in os.walk(src_dir):
        # Skip test and cache directories
        if "test" in root or "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                errors = check_file(filepath)
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

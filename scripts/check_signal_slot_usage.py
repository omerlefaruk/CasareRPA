#!/usr/bin/env python3
"""
Verify Signal/Slot best practices:
- @Slot decorators required on slot methods
- No lambda functions in .connect()
- Use functools.partial for captures
"""

import argparse
import ast
import os
import re
import subprocess
import sys
from pathlib import Path


class SignalSlotChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        self.in_class = False
        self.function_depth = 0

    def visit_ClassDef(self, node):
        old_in_class = self.in_class
        self.in_class = True
        self.generic_visit(node)
        self.in_class = old_in_class

    def visit_FunctionDef(self, node):
        if self.in_class and self.function_depth == 0:
            # Check if method has @Slot or @AsyncSlot decorator
            has_slot = any(
                isinstance(dec, ast.Name) and dec.id in ("Slot", "AsyncSlot")
                for dec in node.decorator_list
            )

            # Check for Qt signal/slot naming convention
            is_slot_method = node.name.startswith("on_")

            if is_slot_method and not has_slot and "test" not in self.filepath:
                if not any(
                    isinstance(d, ast.Name) and d.id == "abstractmethod"
                    for d in node.decorator_list
                ):
                    self.errors.append(
                        f"{self.filepath}:{node.lineno} - Slot method '{node.name}' missing @Slot decorator"
                    )

        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1


def check_lambdas(filepath: str) -> list[str]:
    """Check for lambda in .connect() calls"""
    errors = []
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    # Find .connect(lambda patterns, but skip comments
    lines = content.split("\n")
    for line_num, line in enumerate(lines, 1):
        if line.strip().startswith("#"):
            continue
        if re.search(r"\.connect\s*\(\s*lambda", line):
            errors.append(
                f"{filepath}:{line_num} - Lambda in .connect(). Use functools.partial instead."
            )

    return errors


def check_file(filepath: str) -> list[str]:
    """Check for signal/slot violations"""
    errors = []

    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        checker = SignalSlotChecker(filepath)
        checker.visit(tree)
        errors.extend(checker.errors)
    except Exception:
        pass

    errors.extend(check_lambdas(filepath))
    return errors


def _get_staged_presentation_files(base_dir: Path, presentation_dir: Path) -> list[Path]:
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
        if not path.is_relative_to(presentation_dir):
            continue
        staged_files.append(path)

    return staged_files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all Python files under src/casare_rpa/presentation instead of only staged files.",
    )
    args = parser.parse_args()

    base = Path(__file__).parent.parent
    presentation_dir = base / "src" / "casare_rpa" / "presentation"

    if not presentation_dir.exists():
        return 0

    all_errors = []
    if args.all:
        for root, _, files in os.walk(presentation_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    errors = check_file(filepath)
                    all_errors.extend(errors)
    else:
        staged_files = _get_staged_presentation_files(base, presentation_dir)
        if not staged_files:
            return 0
        for path in staged_files:
            errors = check_file(str(path))
            all_errors.extend(errors)

    if all_errors:
        print("[ERROR] Signal/Slot violations (@Slot required, no lambdas in .connect()):")
        for error in all_errors[:10]:
            print(f"   {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

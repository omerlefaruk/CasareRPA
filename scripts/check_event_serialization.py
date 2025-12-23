#!/usr/bin/env python3
"""
Verify that domain events only use serializable data types.
Block: page, driver, browser, response (complex objects).
Allow: str, int, float, bool, list, dict, Optional types.
"""

import ast
import os
import sys
from pathlib import Path

FORBIDDEN_TYPES = {
    "page",
    "driver",
    "browser",
    "response",
    "request",
    "playwright",
    "Page",
    "Browser",
    "BrowserContext",
}


class EventFieldChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        self.in_dataclass = False
        self.dataclass_name = ""

    def visit_ClassDef(self, node):
        # Check if it's a dataclass (domain event)
        is_dataclass = any(
            isinstance(dec, ast.Name)
            and dec.id == "dataclass"
            or isinstance(dec, ast.Call)
            and isinstance(dec.func, ast.Name)
            and dec.func.id == "dataclass"
            for dec in node.decorator_list
        )

        if is_dataclass:
            old_in_dataclass = self.in_dataclass
            old_name = self.dataclass_name
            self.in_dataclass = True
            self.dataclass_name = node.name
            self.generic_visit(node)
            self.in_dataclass = old_in_dataclass
            self.dataclass_name = old_name
        else:
            self.generic_visit(node)

    def visit_AnnAssign(self, node):
        if self.in_dataclass:
            forbidden_types = self._extract_forbidden_types(node.annotation)
            if forbidden_types:
                var_name = node.target.id if isinstance(node.target, ast.Name) else "unknown"
                self.errors.append(
                    f"{self.filepath}: Event '{self.dataclass_name}' field '{var_name}' "
                    f"contains non-serializable types: {', '.join(sorted(forbidden_types))}"
                )
        self.generic_visit(node)

    def _extract_forbidden_types(self, annotation) -> set[str]:
        """Recursively extract forbidden types from generic annotations"""
        if isinstance(annotation, ast.Name):
            return {annotation.id} if annotation.id in FORBIDDEN_TYPES else set()
        elif isinstance(annotation, ast.Subscript):  # Optional[], List[], Dict[]
            result = self._extract_forbidden_types(annotation.value)
            if isinstance(annotation.slice, ast.Tuple):
                for elt in annotation.slice.elts:
                    result |= self._extract_forbidden_types(elt)
            else:
                result |= self._extract_forbidden_types(annotation.slice)
            return result
        elif isinstance(annotation, ast.Tuple):
            return set().union(*(self._extract_forbidden_types(el) for el in annotation.elts))
        elif isinstance(annotation, ast.Constant):
            return set()
        return set()


def check_file(filepath: str) -> list[str]:
    """Parse Python file and check for forbidden types in events"""
    try:
        with open(filepath, encoding="utf-8") as f:
            tree = ast.parse(f.read())
        checker = EventFieldChecker(filepath)
        checker.visit(tree)
        return checker.errors
    except Exception as e:
        return [f"{filepath}: Parse error - {e}"]


def main():
    base = Path(__file__).parent.parent
    events_dir = base / "src" / "casare_rpa" / "domain" / "events"

    if not events_dir.exists():
        return 0

    all_errors = []
    for root, _, files in os.walk(events_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                filepath = os.path.join(root, file)
                errors = check_file(filepath)
                all_errors.extend(errors)

    if all_errors:
        print("[ERROR] Event serialization violations (use serializable types only):")
        for error in all_errors:
            print(f"   {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

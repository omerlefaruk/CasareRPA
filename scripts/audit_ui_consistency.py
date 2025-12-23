#!/usr/bin/env python3
"""
UI Consistency Audit Script for CasareRPA.

Scans all node files for "Raw Widget" violations where developers used
QLineEdit or QTextEdit directly instead of the custom wrappers.

Valid node implementations should use:
- VariableAwareLineEdit (from variable_picker.py)
- create_variable_text_widget() (from node_widgets.py)
- _add_variable_aware_text_input() method (from base_visual_node.py)
- NodeFilePathWidget, NodeSelectorWidget, etc. (from node_widgets.py)

Usage:
    python scripts/audit_ui_consistency.py [--fix] [--verbose]

Options:
    --fix       Show suggested fixes for each violation
    --verbose   Show detailed output including scanned files
"""

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Tuple

# =============================================================================
# Configuration
# =============================================================================

# Directories to scan for node definitions
SCAN_DIRECTORIES = [
    "src/casare_rpa/presentation/canvas/visual_nodes",
    "src/casare_rpa/nodes",
]

# Files to exclude (custom widget definition files)
EXCLUDE_FILES = {
    "variable_picker.py",
    "node_widgets.py",
    "validated_input.py",
    "base_visual_node.py",
    "__init__.py",
}

# Raw widget classes that should not be used directly
RAW_WIDGET_CLASSES = {
    "QLineEdit",
    "QTextEdit",
    "QPlainTextEdit",
}

# Base classes that indicate a node definition
NODE_BASE_CLASSES = {
    "VisualNode",
    "BaseNode",
    "NodeGraphQtBaseNode",
}

# Approved wrapper methods/classes
APPROVED_WRAPPERS = {
    # Methods
    "_add_variable_aware_text_input",
    "add_text_input",  # From base class, auto-styled
    "create_variable_text_widget",
    "create_file_path_widget",
    "create_directory_path_widget",
    "create_selector_widget",
    # Classes
    "VariableAwareLineEdit",
    "NodeFilePathWidget",
    "NodeDirectoryPathWidget",
    "NodeSelectorWidget",
    "NodeGoogleCredentialWidget",
    "NodeGoogleSpreadsheetWidget",
}


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Violation:
    """Represents a raw widget violation."""

    file_path: Path
    line_number: int
    class_name: str
    widget_class: str
    context: str  # The code line containing the violation

    def __str__(self) -> str:
        return (
            f"{self.file_path}:{self.line_number} - "
            f"Raw {self.widget_class} in {self.class_name}"
        )


# =============================================================================
# AST Visitor
# =============================================================================


class RawWidgetVisitor(ast.NodeVisitor):
    """AST visitor that detects raw QLineEdit/QTextEdit instantiation in node classes."""

    def __init__(self, source_lines: list[str]) -> None:
        self.source_lines = source_lines
        self.violations: list[tuple[int, str, str, str]] = []
        self.current_class: str = ""
        self.in_node_class: bool = False
        self.class_bases: set[str] = set()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class definitions and check if it's a node class."""
        # Check if this class inherits from a node base class
        bases = set()
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.add(base.id)
            elif isinstance(base, ast.Attribute):
                bases.add(base.attr)

        is_node_class = bool(bases & NODE_BASE_CLASSES)

        # Store previous state
        prev_class = self.current_class
        prev_in_node = self.in_node_class
        prev_bases = self.class_bases

        # Update state for this class
        self.current_class = node.name
        self.in_node_class = is_node_class
        self.class_bases = bases

        # Visit class body
        self.generic_visit(node)

        # Restore state
        self.current_class = prev_class
        self.in_node_class = prev_in_node
        self.class_bases = prev_bases

    def visit_Call(self, node: ast.Call) -> None:
        """Check for raw widget instantiation calls."""
        if not self.in_node_class:
            self.generic_visit(node)
            return

        # Get the function name being called
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle QtWidgets.QLineEdit or similar
            func_name = node.func.attr

        # Check if it's a raw widget instantiation
        if func_name in RAW_WIDGET_CLASSES:
            # Get the source line for context
            line_num = node.lineno
            context = ""
            if 0 < line_num <= len(self.source_lines):
                context = self.source_lines[line_num - 1].strip()

            self.violations.append((line_num, self.current_class, func_name, context))

        self.generic_visit(node)


# =============================================================================
# Audit Functions
# =============================================================================


def scan_file(file_path: Path) -> list[Violation]:
    """
    Scan a single Python file for raw widget violations.

    Args:
        file_path: Path to the Python file

    Returns:
        List of Violation objects found in the file
    """
    violations = []

    try:
        source = file_path.read_text(encoding="utf-8")
        source_lines = source.splitlines()
        tree = ast.parse(source, filename=str(file_path))

        visitor = RawWidgetVisitor(source_lines)
        visitor.visit(tree)

        for line_num, class_name, widget_class, context in visitor.violations:
            violations.append(
                Violation(
                    file_path=file_path,
                    line_number=line_num,
                    class_name=class_name,
                    widget_class=widget_class,
                    context=context,
                )
            )

    except SyntaxError as e:
        print(f"  WARNING: Syntax error in {file_path}: {e}")
    except Exception as e:
        print(f"  WARNING: Error scanning {file_path}: {e}")

    return violations


def scan_directory(directory: Path, verbose: bool = False) -> list[Violation]:
    """
    Scan a directory recursively for raw widget violations.

    Args:
        directory: Path to the directory to scan
        verbose: Whether to print scanned files

    Returns:
        List of all Violation objects found
    """
    all_violations = []

    if not directory.exists():
        print(f"  WARNING: Directory not found: {directory}")
        return all_violations

    python_files = list(directory.rglob("*.py"))

    for file_path in python_files:
        # Skip excluded files
        if file_path.name in EXCLUDE_FILES:
            if verbose:
                print(f"  SKIP: {file_path.name} (excluded)")
            continue

        if verbose:
            print(f"  Scanning: {file_path.relative_to(directory.parent.parent)}")

        violations = scan_file(file_path)
        all_violations.extend(violations)

    return all_violations


def generate_fix_suggestion(violation: Violation) -> str:
    """
    Generate a fix suggestion for a violation.

    Args:
        violation: The Violation to generate a fix for

    Returns:
        String with the suggested fix
    """
    widget = violation.widget_class

    if widget == "QLineEdit":
        return (
            "  FIX: Replace with self._add_variable_aware_text_input() method\n"
            "       or use create_variable_text_widget() from node_widgets.py\n"
            "       Example:\n"
            "         self._add_variable_aware_text_input(\n"
            '             name="property_name",\n'
            '             label="Label",\n'
            '             placeholder_text="Enter value...",\n'
            "         )"
        )
    elif widget in ("QTextEdit", "QPlainTextEdit"):
        return (
            "  FIX: Replace with a styled custom widget.\n"
            "       For multi-line text, consider using VariableAwareLineEdit\n"
            "       with increased height, or create a custom styled wrapper."
        )

    return "  FIX: Use an appropriate custom wrapper from node_widgets.py"


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    """Run the UI consistency audit."""
    parser = argparse.ArgumentParser(description="Audit node files for raw widget violations")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Show suggested fixes for each violation",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed output including scanned files",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("CasareRPA UI Consistency Audit")
    print("=" * 70)
    print()
    print("Scanning for raw QLineEdit/QTextEdit usage in node classes...")
    print("(Use custom wrappers like VariableAwareLineEdit for consistency)")
    print()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    all_violations: list[Violation] = []

    for rel_dir in SCAN_DIRECTORIES:
        directory = project_root / rel_dir
        print(f"\nScanning: {rel_dir}")
        print("-" * 50)

        violations = scan_directory(directory, verbose=args.verbose)
        all_violations.extend(violations)

        if violations:
            print(f"  Found {len(violations)} violation(s)")
        else:
            print("  No violations found")

    print()
    print("=" * 70)
    print("AUDIT RESULTS")
    print("=" * 70)

    if not all_violations:
        print()
        print("SUCCESS: No raw widget violations found!")
        print()
        return 0

    print()
    print(f"VIOLATIONS FOUND: {len(all_violations)}")
    print()

    # Group violations by file
    by_file: dict[Path, list[Violation]] = {}
    for v in all_violations:
        if v.file_path not in by_file:
            by_file[v.file_path] = []
        by_file[v.file_path].append(v)

    for file_path, violations in sorted(by_file.items()):
        rel_path = file_path.relative_to(project_root)
        print(f"FILE: {rel_path}")
        print("-" * 50)

        for v in sorted(violations, key=lambda x: x.line_number):
            print(f"  Line {v.line_number}: {v.widget_class} in {v.class_name}")
            print(f"    Code: {v.context}")

            if args.fix:
                print()
                print(generate_fix_suggestion(v))

            print()

    print("=" * 70)
    print(f"Total violations: {len(all_violations)}")
    print()
    print("To see fix suggestions, run with --fix flag:")
    print("  python scripts/audit_ui_consistency.py --fix")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Linting script to detect duplicate manual widgets in visual nodes.

Checks visual node files for manual widget creation that duplicates
@node_schema auto-generated widgets.

Usage:
    python scripts/lint_duplicate_widgets.py
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


class WidgetCallVisitor(ast.NodeVisitor):
    """AST visitor to find widget creation calls in __init__ methods."""

    def __init__(self):
        self.in_init = False
        self.widget_calls: List[
            Tuple[int, str, str]
        ] = []  # (line, method, widget_name)

    def visit_FunctionDef(self, node):
        """Track when we're inside __init__."""
        if node.name == "__init__":
            self.in_init = True
            self.generic_visit(node)
            self.in_init = False
        else:
            self.generic_visit(node)

    def visit_Call(self, node):
        """Find widget creation method calls."""
        if not self.in_init:
            return

        # Check for self.add_* method calls
        if isinstance(node.func, ast.Attribute):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr.startswith("add_")
            ):
                # Extract widget name from first argument
                widget_name = None
                if node.args and isinstance(node.args[0], ast.Constant):
                    widget_name = node.args[0].value

                self.widget_calls.append(
                    (node.lineno, node.func.attr, widget_name or "<unknown>")
                )

        self.generic_visit(node)


def check_file(file_path: Path) -> List[str]:
    """
    Check a visual node file for potential duplicate widgets.

    Args:
        file_path: Path to the Python file to check

    Returns:
        List of warning messages
    """
    warnings = []

    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        visitor = WidgetCallVisitor()
        visitor.visit(tree)

        if visitor.widget_calls:
            warnings.append(f"\n{file_path.relative_to(Path.cwd())}:")
            warnings.append(
                f"  Found {len(visitor.widget_calls)} manual widget calls in __init__():"
            )
            for line, method, widget_name in visitor.widget_calls:
                warnings.append(f"    Line {line}: {method}('{widget_name}')")
            warnings.append(
                "  ⚠️  Check if these widgets are duplicated by @node_schema decorator"
            )

    except SyntaxError as e:
        warnings.append(f"  Syntax error in {file_path}: {e}")
    except Exception as e:
        warnings.append(f"  Error processing {file_path}: {e}")

    return warnings


def main():
    """Main entry point."""
    print("🔍 Checking visual nodes for duplicate manual widgets...\n")

    # Find all visual node files
    visual_nodes_dir = Path("src/casare_rpa/presentation/canvas/visual_nodes")
    if not visual_nodes_dir.exists():
        print(f"❌ Directory not found: {visual_nodes_dir}")
        return 1

    python_files = list(visual_nodes_dir.rglob("*.py"))
    print(f"Found {len(python_files)} Python files to check\n")

    all_warnings = []
    for file_path in python_files:
        # Skip __init__.py and base files
        if file_path.name in ("__init__.py", "base_visual_node.py"):
            continue

        warnings = check_file(file_path)
        all_warnings.extend(warnings)

    if all_warnings:
        print("\n".join(all_warnings))
        print(
            f"\n⚠️  Found {len([w for w in all_warnings if w.startswith(' ')])} files "
            f"with manual widget creation"
        )
        print("\nRecommendation:")
        print("  1. Check if domain node has @node_schema decorator")
        print("  2. If yes, remove manual widget creation from __init__()")
        print("  3. If no, migrate domain node to @node_schema pattern")
        return 1
    else:
        print("✅ No manual widget creation found in visual nodes!")
        print("   All widgets are auto-generated from @node_schema decorators")
        return 0


if __name__ == "__main__":
    sys.exit(main())

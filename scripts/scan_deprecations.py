#!/usr/bin/env python
"""Scan codebase for deprecated imports and DeprecationWarnings"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set
import json


class DeprecationFinder(ast.NodeVisitor):
    """AST visitor to find deprecated imports"""

    DEPRECATED_MODULES = {
        "casare_rpa.core",
        "casare_rpa.core.types",
        "casare_rpa.core.base_node",
        "casare_rpa.core.workflow_schema",
        "casare_rpa.core.execution_context",
        "casare_rpa.presentation.canvas.visual_nodes.visual_nodes",
    }

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.deprecated_imports: List[Dict] = []

    def visit_Import(self, node: ast.Import):
        """Visit 'import X' statements"""
        for alias in node.names:
            if any(alias.name.startswith(dep) for dep in self.DEPRECATED_MODULES):
                self.deprecated_imports.append(
                    {
                        "type": "import",
                        "module": alias.name,
                        "lineno": node.lineno,
                        "col_offset": node.col_offset,
                    }
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Visit 'from X import Y' statements"""
        if node.module and any(
            node.module.startswith(dep) for dep in self.DEPRECATED_MODULES
        ):
            self.deprecated_imports.append(
                {
                    "type": "from_import",
                    "module": node.module,
                    "names": [alias.name for alias in node.names],
                    "lineno": node.lineno,
                    "col_offset": node.col_offset,
                }
            )
        self.generic_visit(node)


def scan_file(filepath: Path) -> List[Dict]:
    """Scan single file for deprecated imports"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        finder = DeprecationFinder(filepath)
        finder.visit(tree)
        return finder.deprecated_imports
    except SyntaxError:
        print(f"Warning: Syntax error in {filepath}, skipping")
        return []


def scan_directory(root: Path) -> Dict[str, List[Dict]]:
    """Scan directory recursively"""
    results = {}

    for pyfile in root.rglob("*.py"):
        # Skip test files, migrations, and this script
        if (
            "test_" in pyfile.name
            or "migration" in str(pyfile)
            or pyfile.name == "scan_deprecations.py"
        ):
            continue

        deprecated = scan_file(pyfile)
        if deprecated:
            results[str(pyfile)] = deprecated

    return results


def generate_report(results: Dict[str, List[Dict]], output_format: str = "text"):
    """Generate report in text or JSON format"""
    if output_format == "json":
        print(json.dumps(results, indent=2))
        return

    # Text format
    total_files = len(results)
    total_imports = sum(len(v) for v in results.values())

    print(f"\n{'='*70}")
    print(" Deprecation Scan Report")
    print(f"{'='*70}\n")
    print("Summary:")
    print(f"   Files with deprecated imports: {total_files}")
    print(f"   Total deprecated imports: {total_imports}\n")

    for filepath, imports in sorted(results.items()):
        print(f"File: {filepath}")
        for imp in imports:
            if imp["type"] == "import":
                print(f"   Line {imp['lineno']}: import {imp['module']}")
            else:
                names = ", ".join(imp["names"])
                print(f"   Line {imp['lineno']}: from {imp['module']} import {names}")
        print()

    print(f"{'='*70}")
    print(" Next Steps:")
    print(f"{'='*70}")
    print(
        "1. Run automated import rewriter: python scripts/migrate_imports_v3.py --dry-run"
    )
    print("2. Review suggested changes")
    print("3. Run migration: python scripts/migrate_imports_v3.py --backup")
    print("4. Run tests: pytest tests/ -v")
    print("5. Commit changes if tests pass\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Scan for deprecated imports")
    parser.add_argument("--path", default="src/casare_rpa", help="Path to scan")
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )
    parser.add_argument("--output", help="Output file (default: stdout)")

    args = parser.parse_args()

    results = scan_directory(Path(args.path))

    if args.output:
        with open(args.output, "w") as f:
            sys.stdout = f
            generate_report(results, args.format)
            sys.stdout = sys.__stdout__
        print(f"Report written to {args.output}")
    else:
        generate_report(results, args.format)

    sys.exit(0 if not results else 1)  # Exit 1 if deprecated imports found

#!/usr/bin/env python
"""
Add metadata tags to CasareRPA node files.

This script automatically adds metadata comment tags to node class files:
- @category: Detected from folder path (browser, file, http, etc.)
- @requires: Detected from imports (playwright, requests, etc.)
- @ports: Parsed from _define_ports() method

Usage:
    python scripts/add_node_tags.py              # Modify files
    python scripts/add_node_tags.py --dry-run    # Preview changes only

Examples:
    # Preview changes without modifying files:
    python scripts/add_node_tags.py --dry-run

    # Apply tags to all node files:
    python scripts/add_node_tags.py

    # Process a specific file:
    python scripts/add_node_tags.py --file src/casare_rpa/nodes/browser_nodes.py

Author: CasareRPA Team
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Optional


# Known dependencies and their import patterns
DEPENDENCY_PATTERNS: dict[str, list[str]] = {
    "playwright": ["playwright", "playwright.async_api"],
    "uiautomation": ["uiautomation", "comtypes", "pywinauto"],
    "requests": ["requests", "httpx", "aiohttp"],
    "googleapi": ["googleapiclient", "google.oauth2", "google.auth"],
    "pillow": ["PIL", "pillow"],
    "opencv": ["cv2", "opencv"],
    "pandas": ["pandas"],
    "pywin32": ["win32", "win32api", "win32gui", "win32con", "pythoncom"],
    "email": ["smtplib", "imaplib", "email"],
    "ftp": ["ftplib", "aioftp"],
    "database": ["asyncpg", "aiomysql", "sqlite3", "pyodbc"],
    "pdf": ["pypdf", "pypdf2", "pdfplumber", "fitz"],
    "xml": ["xml.etree", "lxml"],
    "telegram": ["telegram", "aiogram"],
    "whatsapp": ["twilio", "whatsapp"],
}

# Category mapping from folder names to standard categories
CATEGORY_MAP: dict[str, str] = {
    "browser": "browser",
    "desktop_nodes": "desktop",
    "file": "file",
    "database": "database",
    "email": "email",
    "http": "http",
    "google": "google",
    "system": "system",
    "messaging": "integration",
    "llm": "integration",
    "document": "data",
    "trigger_nodes": "trigger",
}

# Map filename patterns to categories for files directly in nodes/
FILENAME_CATEGORY_MAP: dict[str, str] = {
    "basic_nodes": "control_flow",
    "browser_nodes": "browser",
    "navigation_nodes": "browser",
    "interaction_nodes": "browser",
    "data_nodes": "data",
    "data_operation_nodes": "data",
    "control_flow_nodes": "control_flow",
    "error_handling_nodes": "control_flow",
    "parallel_nodes": "control_flow",
    "variable_nodes": "data",
    "wait_nodes": "browser",
    "text_nodes": "data",
    "string_nodes": "data",
    "list_nodes": "data",
    "dict_nodes": "data",
    "math_nodes": "data",
    "random_nodes": "data",
    "datetime_nodes": "data",
    "script_nodes": "system",
    "xml_nodes": "data",
    "pdf_nodes": "file",
    "ftp_nodes": "file",
    "utility_nodes": "data",
    "subflow_node": "control_flow",
}


class NodeTagExtractor:
    """Extracts metadata from node files using AST parsing."""

    def __init__(self, file_path: Path) -> None:
        """
        Initialize extractor with file path.

        Args:
            file_path: Path to the Python file to analyze
        """
        self.file_path = file_path
        self.content = file_path.read_text(encoding="utf-8")
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in {file_path}: {e}") from e

    def detect_category(self) -> str:
        """
        Detect node category from folder path or filename.

        Returns:
            Category string (browser, file, http, etc.)
        """
        # Get path relative to nodes folder
        parts = self.file_path.parts
        try:
            nodes_idx = parts.index("nodes")
            # Check if there's a subfolder
            if nodes_idx + 2 < len(parts):
                # File is in a subfolder (e.g., nodes/browser/browser_base.py)
                folder = parts[nodes_idx + 1]
                if folder in CATEGORY_MAP:
                    return CATEGORY_MAP[folder]
                return folder.replace("_nodes", "").replace("_", "")
            elif nodes_idx + 1 < len(parts):
                # File is directly in nodes/ folder
                filename = self.file_path.stem
                if filename in FILENAME_CATEGORY_MAP:
                    return FILENAME_CATEGORY_MAP[filename]
                # Infer from filename
                return filename.replace("_nodes", "").replace("_", "")
        except ValueError:
            pass
        return "general"

    def detect_requires(self) -> list[str]:
        """
        Detect required dependencies from imports.

        Returns:
            List of dependency names (playwright, requests, etc.)
        """
        requires = set()

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    for dep, patterns in DEPENDENCY_PATTERNS.items():
                        if any(module.startswith(p.split(".")[0]) for p in patterns):
                            requires.add(dep)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module = node.module.split(".")[0]
                    for dep, patterns in DEPENDENCY_PATTERNS.items():
                        if any(module.startswith(p.split(".")[0]) for p in patterns):
                            requires.add(dep)

        return sorted(requires)

    def find_node_classes(self) -> list[ast.ClassDef]:
        """
        Find all node classes in the file.

        Returns:
            List of ClassDef AST nodes for node classes, sorted by line number
        """
        node_classes = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Check if class inherits from a base node class
                for base in node.bases:
                    base_name = self._get_base_name(base)
                    if base_name and ("Node" in base_name or "Base" in base_name):
                        node_classes.append(node)
                        break

        # Sort by line number for consistent processing
        return sorted(node_classes, key=lambda c: c.lineno)

    def _get_base_name(self, base: ast.expr) -> Optional[str]:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return None

    def extract_ports(self, class_def: ast.ClassDef) -> dict[str, list[str]]:
        """
        Extract port definitions from _define_ports() method.

        Args:
            class_def: AST ClassDef node

        Returns:
            Dict with 'inputs' and 'outputs' port name lists,
            or 'has_helpers' flag if using helper methods
        """
        ports = {"inputs": [], "outputs": [], "has_helpers": False}

        for node in ast.walk(class_def):
            if isinstance(node, ast.FunctionDef) and node.name == "_define_ports":
                # Parse method body for add_*_port calls
                for stmt in ast.walk(node):
                    if isinstance(stmt, ast.Call):
                        func = stmt.func
                        func_name = None

                        if isinstance(func, ast.Attribute):
                            func_name = func.attr
                        elif isinstance(func, ast.Name):
                            func_name = func.id

                        if func_name:
                            # Check for direct add_*_port calls
                            if stmt.args:
                                port_name = self._extract_string_value(stmt.args[0])
                                if port_name:
                                    if "input" in func_name.lower():
                                        ports["inputs"].append(port_name)
                                    elif "output" in func_name.lower():
                                        ports["outputs"].append(port_name)

                            # Check for helper method calls (passthrough, selector, etc.)
                            helper_methods = [
                                "add_page_passthrough_ports",
                                "add_selector_input_port",
                                "add_exec_ports",
                            ]
                            if func_name in helper_methods:
                                ports["has_helpers"] = True

        return ports

    def _extract_string_value(self, node: ast.expr) -> Optional[str]:
        """Extract string value from AST node."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def has_existing_tags(self, class_def: ast.ClassDef) -> bool:
        """
        Check if class already has metadata tags.

        Args:
            class_def: AST ClassDef node

        Returns:
            True if tags already exist
        """
        # Get the source lines for this class (first 20 lines after class definition)
        start_line = class_def.lineno
        end_line = min(start_line + 20, class_def.end_lineno or start_line + 20)

        lines = self.content.split("\n")
        class_source = "\n".join(lines[start_line - 1 : end_line])

        # Check for existing tags
        return bool(re.search(r"#\s*@category:", class_source))


def find_docstring_end(lines: list[str], start_idx: int) -> int:
    """
    Find the line index where the docstring ends.

    Args:
        lines: List of file lines
        start_idx: Line index where class definition starts (0-based)

    Returns:
        Line index to insert tags after (0-based)
    """
    in_docstring = False
    docstring_delimiter = None
    found_docstring_start = False

    for i in range(start_idx + 1, min(start_idx + 50, len(lines))):
        line = lines[i]
        stripped = line.strip()

        if not in_docstring:
            # Look for start of docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_delimiter = stripped[:3]
                in_docstring = True
                found_docstring_start = True
                # Check if docstring ends on same line (single-line docstring)
                rest = stripped[3:]
                if docstring_delimiter in rest:
                    return i + 1
            elif stripped.startswith("def ") or stripped.startswith("async def "):
                # We hit a method definition before finding a docstring
                # Insert right after class definition
                return start_idx + 1
            # Skip empty lines, comments, and other content - keep looking for docstring
        else:
            # Looking for end of multi-line docstring
            if docstring_delimiter in stripped:
                return i + 1

    # Fallback: insert right after class line
    return start_idx + 1


def process_file(file_path: Path, dry_run: bool = False) -> dict:
    """
    Process a single node file.

    Args:
        file_path: Path to the Python file
        dry_run: If True, only preview changes

    Returns:
        Dict with processing results
    """
    result = {
        "file": str(file_path),
        "status": "skipped",
        "classes_processed": 0,
        "classes_skipped": 0,
        "errors": [],
    }

    try:
        extractor = NodeTagExtractor(file_path)

        category = extractor.detect_category()
        requires = extractor.detect_requires()

        classes = extractor.find_node_classes()

        if not classes:
            result["status"] = "no_classes"
            return result

        # Work with the content as lines for easier manipulation
        lines = extractor.content.split("\n")

        # Track line offset as we insert tags
        line_offset = 0
        modified = False

        for class_def in classes:
            if extractor.has_existing_tags(class_def):
                result["classes_skipped"] += 1
                continue

            ports = extractor.extract_ports(class_def)

            # Format the tags
            requires_str = ", ".join(requires) if requires else "none"

            inputs = ports.get("inputs", [])
            outputs = ports.get("outputs", [])
            has_helpers = ports.get("has_helpers", False)

            if inputs or outputs:
                input_str = ", ".join(inputs) if inputs else "none"
                output_str = ", ".join(outputs) if outputs else "none"
                ports_str = f"{input_str} -> {output_str}"
            elif has_helpers:
                # Uses helper methods for port definition
                ports_str = "via base class helpers"
            else:
                ports_str = "none -> none"

            tags = [
                f"    # @category: {category}",
                f"    # @requires: {requires_str}",
                f"    # @ports: {ports_str}",
            ]

            # Find insertion point - after class docstring
            # Adjust for previous insertions
            class_line_idx = class_def.lineno - 1 + line_offset
            insert_idx = find_docstring_end(lines, class_line_idx)

            # Add blank line before tags if needed
            if insert_idx < len(lines) and lines[insert_idx - 1].strip():
                tags.insert(0, "")

            # Insert tags
            for i, tag in enumerate(tags):
                lines.insert(insert_idx + i, tag)

            line_offset += len(tags)
            result["classes_processed"] += 1
            modified = True

        if modified:
            content = "\n".join(lines)
            if not dry_run:
                file_path.write_text(content, encoding="utf-8")
            result["status"] = "modified" if not dry_run else "would_modify"
        elif result["classes_skipped"] > 0:
            result["status"] = "already_tagged"

    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))

    return result


def find_node_files(base_path: Path) -> list[Path]:
    """
    Find all Python files in the nodes directory.

    Args:
        base_path: Base path to search (nodes directory)

    Returns:
        List of Python file paths
    """
    files = []

    # Exclusion patterns
    exclude_patterns = [
        "__init__.py",
        "conftest.py",
        "*_test.py",
        "test_*.py",
    ]

    for py_file in base_path.rglob("*.py"):
        # Skip excluded files
        skip = False
        for pattern in exclude_patterns:
            if py_file.match(pattern):
                skip = True
                break

        if not skip:
            files.append(py_file)

    return sorted(files)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add metadata tags to CasareRPA node files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/add_node_tags.py --dry-run    # Preview changes
    python scripts/add_node_tags.py              # Apply changes
    python scripts/add_node_tags.py --file path/to/node.py
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process a specific file instead of all nodes",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed output",
    )

    args = parser.parse_args()

    # Determine base path
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    nodes_dir = project_root / "src" / "casare_rpa" / "nodes"

    if not nodes_dir.exists():
        print(f"Error: Nodes directory not found: {nodes_dir}")
        return 1

    # Get files to process
    if args.file:
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            return 1
        files = [args.file]
    else:
        files = find_node_files(nodes_dir)

    if not files:
        print("No node files found.")
        return 0

    # Process files
    summary = {
        "total": len(files),
        "modified": 0,
        "skipped": 0,
        "already_tagged": 0,
        "no_classes": 0,
        "errors": 0,
    }

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Processing {len(files)} files...")
    print("-" * 60)

    for file_path in files:
        result = process_file(file_path, args.dry_run)

        if result["status"] == "modified":
            summary["modified"] += 1
            if args.verbose:
                print(
                    f"MODIFIED: {file_path.name} ({result['classes_processed']} classes)"
                )
        elif result["status"] == "would_modify":
            summary["modified"] += 1
            if args.verbose or args.dry_run:
                print(
                    f"WOULD MODIFY: {file_path.name} ({result['classes_processed']} classes)"
                )
        elif result["status"] == "already_tagged":
            summary["already_tagged"] += 1
            if args.verbose:
                print(f"SKIPPED (tagged): {file_path.name}")
        elif result["status"] == "no_classes":
            summary["no_classes"] += 1
            if args.verbose:
                print(f"SKIPPED (no classes): {file_path.name}")
        elif result["status"] == "error":
            summary["errors"] += 1
            print(f"ERROR: {file_path.name}: {result['errors']}")
        else:
            summary["skipped"] += 1
            if args.verbose:
                print(f"SKIPPED: {file_path.name}")

    # Print summary
    print("-" * 60)
    print("Summary:")
    print(f"  Total files: {summary['total']}")
    if args.dry_run:
        print(f"  Would modify: {summary['modified']}")
    else:
        print(f"  Modified: {summary['modified']}")
    print(f"  Already tagged: {summary['already_tagged']}")
    print(f"  No node classes: {summary['no_classes']}")
    print(f"  Errors: {summary['errors']}")

    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

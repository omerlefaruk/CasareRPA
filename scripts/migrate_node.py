#!/usr/bin/env python
"""
Node migration script.

Converts nodes from old decorator style (@node_schema/@executable_node)
to new style (@node/@properties).

Usage:
    python scripts/migrate_node.py path/to/node.py
    python scripts/migrate_node.py path/to/nodes/ --recursive
    python scripts/migrate_node.py path/to/node.py --dry-run
    python scripts/migrate_node.py path/to/nodes/ -r -n  # Preview all

Examples:
    # Preview changes without writing
    python scripts/migrate_node.py src/casare_rpa/nodes/basic_nodes.py --dry-run

    # Migrate a single file
    python scripts/migrate_node.py src/casare_rpa/nodes/basic_nodes.py

    # Migrate entire directory recursively
    python scripts/migrate_node.py src/casare_rpa/nodes/ --recursive

    # Generate migration report
    python scripts/migrate_node.py src/casare_rpa/nodes/ -r --report
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger


def parse_old_decorators(content: str) -> List[Dict]:
    """
    Extract old-style decorator information from file content.

    Finds @node_schema(...) @executable_node patterns and extracts
    the property definitions for migration.

    Args:
        content: Python file content

    Returns:
        List of dicts with decorator info (start, end, properties, type)
    """
    nodes = []

    # Find @node_schema decorators followed by @executable_node
    # Pattern handles multi-line definitions
    schema_pattern = re.compile(
        r"@node_schema\(\s*\n?(.*?)\)\s*\n@executable_node",
        re.DOTALL,
    )

    for match in schema_pattern.finditer(content):
        properties_str = match.group(1).strip()
        nodes.append(
            {
                "start": match.start(),
                "end": match.end(),
                "properties": properties_str,
                "type": "node_schema_executable",
            }
        )

    # Also find standalone @executable_node (no schema)
    standalone_pattern = re.compile(r"@executable_node\s*\nclass")

    for match in standalone_pattern.finditer(content):
        # Check if this isn't already part of a node_schema match
        is_part_of_schema = any(
            node["end"] == match.start()
            or (node["start"] < match.start() < node["end"])
            for node in nodes
        )
        if not is_part_of_schema:
            nodes.append(
                {
                    "start": match.start(),
                    "end": match.end() - len("class"),  # Don't include 'class'
                    "properties": "",
                    "type": "executable_only",
                }
            )

    return nodes


def extract_class_info(content: str, decorator_end: int) -> Optional[Dict]:
    """
    Extract class information following a decorator.

    Args:
        content: File content
        decorator_end: Position where decorator ends

    Returns:
        Dict with class name, docstring, category if found
    """
    # Find the class definition after the decorator
    after_decorator = content[decorator_end:]
    class_match = re.search(r"class\s+(\w+)\s*\(([^)]*)\)", after_decorator)

    if not class_match:
        return None

    class_name = class_match.group(1)
    base_classes = class_match.group(2)

    # Try to find category from class body
    category = "General"
    category_match = re.search(
        r'category\s*[=:]\s*["\'](\w+)["\']',
        after_decorator[: after_decorator.find("def ")],
    )
    if category_match:
        category = category_match.group(1)

    # Try to extract docstring
    docstring = ""
    docstring_match = re.search(
        r'class\s+\w+\s*\([^)]*\):\s*"""(.*?)"""',
        after_decorator,
        re.DOTALL,
    )
    if docstring_match:
        docstring = docstring_match.group(1).strip().split("\n")[0]  # First line only

    return {
        "name": class_name,
        "base_classes": base_classes,
        "category": category,
        "docstring": docstring,
    }


def convert_to_new_style(
    node_info: Dict,
    class_info: Dict,
) -> str:
    """
    Convert old decorator info to new @node + @properties style.

    Args:
        node_info: Decorator information from parse_old_decorators
        class_info: Class information from extract_class_info

    Returns:
        New-style decorator string
    """
    properties = node_info.get("properties", "")
    class_name = class_info.get("name", "Unknown")
    category = class_info.get("category", "General")
    description = class_info.get("docstring", "")

    # Generate display name from class name
    name = class_name.replace("Node", "").replace("_", " ")

    # Build new decorators
    if node_info["type"] == "executable_only":
        # No properties, just @node
        new_code = f"""@node(
    name="{name}",
    category="{category}",
)"""
    else:
        # Has properties
        new_code = f"""@node(
    name="{name}",
    category="{category}",
)
@properties(
{properties}
)"""

    return new_code


def update_imports(content: str) -> str:
    """
    Update import statements from old to new decorator names.

    Args:
        content: File content

    Returns:
        Content with updated imports
    """
    # Update decorator imports
    old_import = r"from casare_rpa\.domain\.decorators import\s+([^;\n]+)"

    def replace_import(match):
        imports = match.group(1).strip()

        # Parse existing imports
        import_list = [i.strip() for i in imports.split(",")]

        # Map old to new
        mapping = {
            "executable_node": "node",
            "node_schema": "properties",
        }

        new_imports = []
        for imp in import_list:
            if imp in mapping:
                new_imports.append(mapping[imp])
            else:
                new_imports.append(imp)

        # Remove duplicates and sort
        new_imports = sorted(set(new_imports))

        return f"from casare_rpa.domain.decorators import {', '.join(new_imports)}"

    content = re.sub(old_import, replace_import, content)

    return content


def migrate_file(filepath: Path, dry_run: bool = False) -> Tuple[bool, str, Dict]:
    """
    Migrate a single file from old to new decorator style.

    Args:
        filepath: Path to the Python file
        dry_run: If True, show changes without writing

    Returns:
        Tuple of (success, message, stats)
    """
    stats = {
        "nodes_found": 0,
        "nodes_migrated": 0,
        "already_migrated": False,
        "no_migration_needed": False,
    }

    try:
        content = filepath.read_text(encoding="utf-8")
        original = content

        # Check if already migrated
        if "@node(" in content and "@properties(" in content:
            stats["already_migrated"] = True
            return True, "Already migrated", stats

        # Check if uses old decorators
        if "@node_schema" not in content and "@executable_node" not in content:
            stats["no_migration_needed"] = True
            return True, "No migration needed", stats

        nodes = parse_old_decorators(content)
        stats["nodes_found"] = len(nodes)

        if not nodes:
            return True, "No nodes found to migrate", stats

        migrations = []
        for node in nodes:
            # Find the class that follows this decorator
            class_info = extract_class_info(content, node["end"])
            if class_info:
                new_decorator = convert_to_new_style(node, class_info)
                migrations.append(
                    {
                        "old": content[node["start"] : node["end"]],
                        "new": new_decorator,
                        "class": class_info["name"],
                    }
                )

        # Apply migrations (in reverse to preserve positions)
        for migration in reversed(migrations):
            content = content.replace(migration["old"], migration["new"], 1)
            stats["nodes_migrated"] += 1

        # Update imports
        content = update_imports(content)

        if dry_run:
            print(f"\n{'='*60}")
            print(f"FILE: {filepath}")
            print(f"{'='*60}")
            if content != original:
                print("\nMigrations:")
                for m in migrations:
                    print(f"  - {m['class']}")
                print("\n--- PREVIEW ---")
                # Show first 100 lines of the file
                lines = content.split("\n")[:100]
                for i, line in enumerate(lines, 1):
                    print(f"{i:4}: {line}")
                if len(content.split("\n")) > 100:
                    print(f"... ({len(content.split(chr(10)))} total lines)")
            return True, f"Would migrate {len(migrations)} node(s)", stats

        if content != original:
            filepath.write_text(content, encoding="utf-8")
            return True, f"Migrated {len(migrations)} node(s)", stats

        return True, "No changes needed", stats

    except Exception as e:
        logger.error(f"Error migrating {filepath}: {e}")
        return False, f"Error: {e}", stats


def generate_report(files: List[Path]) -> str:
    """
    Generate a migration report for multiple files.

    Args:
        files: List of file paths to analyze

    Returns:
        Report string
    """
    report_lines = [
        "Node Migration Report",
        "=" * 60,
        "",
    ]

    total_nodes = 0
    legacy_nodes = 0
    migrated_nodes = 0
    files_needing_migration = []

    for filepath in files:
        try:
            content = filepath.read_text(encoding="utf-8")

            # Count nodes
            old_style = len(re.findall(r"@node_schema", content))
            old_exec = len(re.findall(r"@executable_node", content))
            new_style = len(re.findall(r"@node\(", content))

            legacy_count = max(old_style, old_exec)
            total_nodes += legacy_count + new_style
            legacy_nodes += legacy_count
            migrated_nodes += new_style

            if legacy_count > 0:
                files_needing_migration.append((filepath, legacy_count))

        except Exception as e:
            report_lines.append(f"Error reading {filepath}: {e}")

    report_lines.extend(
        [
            f"Total files scanned: {len(files)}",
            f"Total nodes found: {total_nodes}",
            f"Legacy nodes: {legacy_nodes}",
            f"Already migrated: {migrated_nodes}",
            f"Files needing migration: {len(files_needing_migration)}",
            "",
        ]
    )

    if files_needing_migration:
        report_lines.append("Files to migrate:")
        for fp, count in sorted(files_needing_migration, key=lambda x: -x[1]):
            report_lines.append(f"  {fp}: {count} node(s)")

    return "\n".join(report_lines)


def main():
    """Main entry point for migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate nodes from old to new decorator style",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_node.py src/casare_rpa/nodes/basic_nodes.py --dry-run
  python scripts/migrate_node.py src/casare_rpa/nodes/ --recursive
  python scripts/migrate_node.py src/casare_rpa/nodes/ -r --report
        """,
    )
    parser.add_argument("path", help="File or directory to migrate")
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursively migrate directory",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Show changes without writing",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate migration report instead of migrating",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()
    path = Path(args.path)

    if not path.exists():
        print(f"Error: {path} does not exist")
        sys.exit(1)

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    # Collect files
    files: List[Path] = []
    if path.is_file():
        files = [path]
    elif path.is_dir():
        pattern = "**/*.py" if args.recursive else "*.py"
        files = [
            f
            for f in path.glob(pattern)
            if not f.name.startswith("_")  # Skip __init__.py etc for analysis
            or f.name == "__init__.py"  # But include for actual migration
        ]

    if not files:
        print("No Python files found")
        sys.exit(0)

    # Generate report mode
    if args.report:
        print(generate_report(files))
        sys.exit(0)

    # Migration mode
    success_count = 0
    fail_count = 0
    skip_count = 0

    for filepath in files:
        success, message, stats = migrate_file(filepath, args.dry_run)
        status = "OK" if success else "FAIL"

        if stats.get("already_migrated") or stats.get("no_migration_needed"):
            skip_count += 1
            if args.verbose:
                print(f"[SKIP] {filepath}: {message}")
        else:
            print(f"[{status}] {filepath}: {message}")

        if success:
            success_count += 1
        else:
            fail_count += 1

    print(
        f"\nTotal: {success_count} succeeded, {fail_count} failed, {skip_count} skipped"
    )

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()

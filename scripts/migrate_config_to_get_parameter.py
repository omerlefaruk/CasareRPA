#!/usr/bin/env python3
"""
Automated migration script: self.config.get -> self.get_parameter

Converts legacy config access patterns to the modern dual-source pattern.
This enables nodes to receive values from both port connections AND config.

Usage:
    python scripts/migrate_config_to_get_parameter.py [--dry-run] [--file PATH]
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Pattern to match self.config.get("key", default)
CONFIG_GET_PATTERN = re.compile(
    r'self\.config\.get\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*([^)]+))?\s*\)'
)


def migrate_file(file_path: Path, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Migrate a single file from self.config.get to self.get_parameter.

    Returns:
        Tuple of (replacement_count, list of changes made)
    """
    content = file_path.read_text(encoding="utf-8")
    changes = []

    def replace_match(match: re.Match) -> str:
        key = match.group(1)
        default = match.group(2)

        if default:
            # Has default value: self.config.get("key", default) -> self.get_parameter("key", default)
            replacement = f'self.get_parameter("{key}", {default.strip()})'
        else:
            # No default: self.config.get("key") -> self.get_parameter("key")
            replacement = f'self.get_parameter("{key}")'

        changes.append(f"  {match.group(0)} -> {replacement}")
        return replacement

    new_content = CONFIG_GET_PATTERN.sub(replace_match, content)
    count = len(changes)

    if count > 0 and not dry_run:
        file_path.write_text(new_content, encoding="utf-8")

    return count, changes


def scan_nodes_directory(nodes_dir: Path, dry_run: bool = False) -> dict:
    """Scan and migrate all Python files in nodes directory."""
    results = {
        "total_files": 0,
        "migrated_files": 0,
        "total_replacements": 0,
        "files": {},
    }

    for py_file in nodes_dir.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue

        results["total_files"] += 1
        count, changes = migrate_file(py_file, dry_run)

        if count > 0:
            results["migrated_files"] += 1
            results["total_replacements"] += count
            results["files"][str(py_file.relative_to(nodes_dir))] = {
                "count": count,
                "changes": changes,
            }

    return results


def main():
    dry_run = "--dry-run" in sys.argv
    single_file = None

    for i, arg in enumerate(sys.argv):
        if arg == "--file" and i + 1 < len(sys.argv):
            single_file = Path(sys.argv[i + 1])
            break

    print("=" * 60)
    print("Node Modernization: self.config.get -> self.get_parameter")
    print("=" * 60)

    if dry_run:
        print("MODE: DRY RUN (no files will be modified)\n")
    else:
        print("MODE: LIVE (files will be modified)\n")

    if single_file:
        if not single_file.exists():
            print(f"ERROR: File not found: {single_file}")
            sys.exit(1)

        count, changes = migrate_file(single_file, dry_run)
        print(f"File: {single_file}")
        print(f"Replacements: {count}")
        if changes:
            print("Changes:")
            for c in changes:
                print(c)
    else:
        # Process entire nodes directory
        project_root = Path(__file__).parent.parent
        nodes_dir = project_root / "src" / "casare_rpa" / "nodes"

        if not nodes_dir.exists():
            print(f"ERROR: Nodes directory not found: {nodes_dir}")
            sys.exit(1)

        results = scan_nodes_directory(nodes_dir, dry_run)

        print(f"Scanned: {results['total_files']} files")
        print(f"Migrated: {results['migrated_files']} files")
        print(f"Total replacements: {results['total_replacements']}")
        print()

        if results["files"]:
            print("Files with changes:")
            for file_path, data in sorted(results["files"].items()):
                print(f"\n  {file_path} ({data['count']} replacements)")
                if dry_run:
                    for change in data["changes"][:3]:  # Show first 3
                        print(f"    {change}")
                    if len(data["changes"]) > 3:
                        print(f"    ... and {len(data['changes']) - 3} more")

    print("\n" + "=" * 60)
    if dry_run:
        print("Re-run without --dry-run to apply changes")
    else:
        print("Migration complete!")


if __name__ == "__main__":
    main()

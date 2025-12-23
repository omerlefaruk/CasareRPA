"""
Exec Port Migration Script
Migrates nodes from old exec port pattern to new pattern.

OLD:  self.add_input_port("exec_in", DataType.EXEC)
NEW:  self.add_exec_input("exec_in")
"""

import os
import re
from pathlib import Path
from typing import List, Tuple


def find_old_exec_patterns(content: str) -> List[Tuple[str, int]]:
    """Find all occurrences of old exec port patterns."""
    patterns = []

    # Pattern 1: add_input_port with DataType.EXEC
<<<<<<< HEAD
    input_pattern = (
        r'self\.add_input_port\s*\(\s*["\']([^"\']+)["\']\s*,\s*DataType\.EXEC\s*\)'
    )
=======
    input_pattern = r'self\.add_input_port\s*\(\s*["\']([^"\']+)["\']\s*,\s*DataType\.EXEC\s*\)'
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
    for match in re.finditer(input_pattern, content):
        patterns.append(("input", match.group(1), match.start(), match.end()))

    # Pattern 2: add_output_port with DataType.EXEC
<<<<<<< HEAD
    output_pattern = (
        r'self\.add_output_port\s*\(\s*["\']([^"\']+)["\']\s*,\s*DataType\.EXEC\s*\)'
    )
=======
    output_pattern = r'self\.add_output_port\s*\(\s*["\']([^"\']+)["\']\s*,\s*DataType\.EXEC\s*\)'
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
    for match in re.finditer(output_pattern, content):
        patterns.append(("output", match.group(1), match.start(), match.end()))

    return patterns


def migrate_content(content: str) -> Tuple[str, int]:
    """Migrate content from old to new exec port pattern."""
    changes = 0

    # Replace input ports
    new_content, count = re.subn(
        r'self\.add_input_port\s*\(\s*["\']([^"\']+)["\']\s*,\s*DataType\.EXEC\s*\)',
        r'self.add_exec_input("\1")',
        content,
    )
    changes += count

    # Replace output ports
    new_content, count = re.subn(
        r'self\.add_output_port\s*\(\s*["\']([^"\']+)["\']\s*,\s*DataType\.EXEC\s*\)',
        r'self.add_exec_output("\1")',
        new_content,
    )
    changes += count

    return new_content, changes


def analyze_file(filepath: Path) -> dict:
    """Analyze a single file for migration needs."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": str(e), "path": str(filepath)}

    patterns = find_old_exec_patterns(content)

    return {
        "path": str(filepath),
        "old_input_count": len([p for p in patterns if p[0] == "input"]),
        "old_output_count": len([p for p in patterns if p[0] == "output"]),
        "total_old": len(patterns),
        "needs_migration": len(patterns) > 0,
    }


def migrate_file(filepath: Path, dry_run: bool = True) -> dict:
    """Migrate a single file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": str(e), "path": str(filepath)}

    new_content, changes = migrate_content(content)

    if not dry_run and changes > 0:
        filepath.write_text(new_content, encoding="utf-8")

    return {
        "path": str(filepath),
        "changes": changes,
        "migrated": not dry_run and changes > 0,
    }


def scan_category(category_path: Path) -> List[dict]:
    """Scan all Python files in a category."""
    results = []
    for py_file in category_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            results.append(analyze_file(py_file))
    return results


def migrate_category(category_path: Path, dry_run: bool = True) -> List[dict]:
    """Migrate all Python files in a category."""
    results = []
    for py_file in category_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            results.append(migrate_file(py_file, dry_run))
    return results


if __name__ == "__main__":
    import sys

    # Default nodes path
    nodes_path = Path(r"c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\nodes")

    # Categories to migrate
    categories = [
        "browser",
        "control_flow",
        "file",
        "data",
        "data_operation",
        "google",
        "desktop_nodes",
        "system",
        "text",
        "email",
        "http",
        "llm",
        "trigger_nodes",
    ]

    mode = sys.argv[1] if len(sys.argv) > 1 else "analyze"

    if mode == "analyze":
        print("=== Exec Port Migration Analysis ===\n")
        total_files = 0
        total_migrations = 0

        for category in categories:
            cat_path = nodes_path / category
            if cat_path.exists():
                results = scan_category(cat_path)
                needs_migration = [r for r in results if r.get("needs_migration")]

                if needs_migration:
                    print(f"\n{category}/:")
                    for r in needs_migration:
                        print(f"  {Path(r['path']).name}: {r['total_old']} patterns")
                    total_files += len(needs_migration)
                    total_migrations += sum(r["total_old"] for r in needs_migration)

<<<<<<< HEAD
        print(
            f"\n\nTotal: {total_files} files need migration ({total_migrations} patterns)"
        )
=======
        print(f"\n\nTotal: {total_files} files need migration ({total_migrations} patterns)")
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

    elif mode == "migrate":
        print("=== Exec Port Migration (DRY RUN) ===\n")
        category = sys.argv[2] if len(sys.argv) > 2 else None
        dry_run = "--apply" not in sys.argv

        if category:
            cat_path = nodes_path / category
            if cat_path.exists():
                results = migrate_category(cat_path, dry_run=dry_run)
                for r in results:
                    if r.get("changes", 0) > 0:
                        print(f"  {Path(r['path']).name}: {r['changes']} changes")
        else:
            print("Usage: python migrate_exec_ports.py migrate <category> [--apply]")

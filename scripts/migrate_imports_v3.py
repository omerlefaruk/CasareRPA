#!/usr/bin/env python
"""
Automated import migration tool for v2.x to v3.0.

This script uses AST (Abstract Syntax Tree) transformation to rewrite deprecated
imports from casare_rpa.core.* to their new canonical locations in domain/,
infrastructure/, and presentation/ layers.

Usage:
    python scripts/migrate_imports_v3.py --dry-run
    python scripts/migrate_imports_v3.py --backup
    python scripts/migrate_imports_v3.py --file src/casare_rpa/nodes/basic_nodes.py
"""

import ast
import shutil
import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from utils.import_mapper import ImportMapper


@dataclass
class ImportChange:
    """Record of a single import change."""

    lineno: int
    col_offset: int
    old_text: str
    new_text: str
    change_type: str


@dataclass
class FileChanges:
    """Collection of changes for a single file."""

    filepath: Path
    changes: List[ImportChange] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0


class ImportRewriter(ast.NodeTransformer):
    """AST transformer that rewrites deprecated imports."""

    def __init__(self, filepath: Path, source_lines: List[str]) -> None:
        self.filepath = filepath
        self.source_lines = source_lines
        self.changes: List[ImportChange] = []
        self._package_path = self._compute_package_path()

    def _compute_package_path(self) -> str:
        parts = self.filepath.parts
        try:
            idx = parts.index("casare_rpa")
            package_parts = list(parts[idx:])
            if package_parts[-1].endswith(".py"):
                package_parts[-1] = package_parts[-1][:-3]
            return ".".join(package_parts)
        except ValueError:
            return ""

    def _resolve_relative_import(self, module: Optional[str], level: int) -> str:
        if level == 0:
            return module or ""
        package_parts = self._package_path.split(".")
        if level <= len(package_parts):
            base_parts = package_parts[:-level] if level > 0 else package_parts
        else:
            base_parts = []
        if module:
            return ".".join(base_parts + [module]) if base_parts else module
        return ".".join(base_parts)

    def visit_Import(self, node: ast.Import) -> ast.Import:
        new_names: List[ast.alias] = []
        changed = False
        for alias in node.names:
            if ImportMapper.is_deprecated_module(alias.name):
                new_module = ImportMapper.map_module(alias.name)
                if new_module != alias.name:
                    changed = True
                    old_text = f"import {alias.name}"
                    new_text = f"import {new_module}"
                    if alias.asname:
                        old_text += f" as {alias.asname}"
                        new_text += f" as {alias.asname}"
                    self.changes.append(
                        ImportChange(
                            node.lineno, node.col_offset, old_text, new_text, "import"
                        )
                    )
                    new_names.append(ast.alias(name=new_module, asname=alias.asname))
                else:
                    new_names.append(alias)
            else:
                new_names.append(alias)
        if changed:
            node.names = new_names
        return node

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        if not node.module and node.level > 0:
            return node
        is_relative = node.level > 0
        if is_relative:
            absolute_module = self._resolve_relative_import(node.module, node.level)
        else:
            absolute_module = node.module or ""
        if not ImportMapper.is_deprecated_module(absolute_module):
            return node
        grouped: Dict[str, List[ast.alias]] = {}
        for alias in node.names:
            new_module, new_name = ImportMapper.map_name(absolute_module, alias.name)
            if new_module not in grouped:
                grouped[new_module] = []
            grouped[new_module].append(ast.alias(name=new_name, asname=alias.asname))
        dots = "." * node.level
        old_module_text = f"{dots}{node.module}" if node.module else dots
        if len(grouped) == 1:
            new_module = list(grouped.keys())[0]
            new_names = list(grouped.values())[0]
            if new_module != absolute_module:
                old_names = ", ".join(
                    a.name + (f" as {a.asname}" if a.asname else "") for a in node.names
                )
                new_names_str = ", ".join(
                    a.name + (f" as {a.asname}" if a.asname else "") for a in new_names
                )
                self.changes.append(
                    ImportChange(
                        node.lineno,
                        node.col_offset,
                        f"from {old_module_text} import {old_names}",
                        f"from {new_module} import {new_names_str}",
                        "from_import",
                    )
                )
                node.module = new_module
                node.level = 0
                node.names = new_names
        else:
            old_names = ", ".join(
                a.name + (f" as {a.asname}" if a.asname else "") for a in node.names
            )
            new_imports = []
            for mod, names in sorted(grouped.items()):
                names_str = ", ".join(
                    a.name + (f" as {a.asname}" if a.asname else "") for a in names
                )
                new_imports.append(f"from {mod} import {names_str}")
            self.changes.append(
                ImportChange(
                    node.lineno,
                    node.col_offset,
                    f"from {old_module_text} import {old_names}",
                    "\n".join(new_imports),
                    "from_import_split",
                )
            )
            first_module = sorted(grouped.keys())[0]
            node.module = first_module
            node.level = 0
            node.names = grouped[first_module]
        return node


def rewrite_source_text(source: str, changes: List[ImportChange]) -> str:
    if not changes:
        return source
    lines = source.splitlines(keepends=True)
    result_lines: List[str] = []
    sorted_changes = sorted(changes, key=lambda c: c.lineno)
    processed_lines: Set[int] = set()
    change_idx = 0
    for i, line in enumerate(lines, start=1):
        if change_idx < len(sorted_changes):
            change = sorted_changes[change_idx]
            if i == change.lineno:
                import_lines = [line]
                j = i
                if "(" in line and ")" not in line:
                    while j < len(lines) and ")" not in import_lines[-1]:
                        j += 1
                        import_lines.append(lines[j - 1])
                        processed_lines.add(j)
                elif line.rstrip().endswith("\\"):
                    while j < len(lines) and import_lines[-1].rstrip().endswith("\\"):
                        j += 1
                        import_lines.append(lines[j - 1])
                        processed_lines.add(j)
                original_text = "".join(import_lines)
                indent = len(original_text) - len(original_text.lstrip())
                indent_str = " " * indent
                if change.change_type == "from_import_split":
                    new_lines = change.new_text.split("\n")
                    replacement = "\n".join(indent_str + nl for nl in new_lines) + "\n"
                else:
                    replacement = indent_str + change.new_text + "\n"
                result_lines.append(replacement)
                processed_lines.add(i)
                change_idx += 1
                continue
        if i not in processed_lines:
            result_lines.append(line)
    return "".join(result_lines)


def analyze_file(filepath: Path) -> FileChanges:
    file_changes = FileChanges(filepath=filepath)
    try:
        source = filepath.read_text(encoding="utf-8")
        source_lines = source.splitlines()
    except Exception as e:
        file_changes.error = f"Cannot read file: {e}"
        return file_changes
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        file_changes.error = f"Syntax error: {e}"
        return file_changes
    rewriter = ImportRewriter(filepath, source_lines)
    rewriter.visit(tree)
    file_changes.changes = rewriter.changes
    return file_changes


def rewrite_file(
    filepath: Path, dry_run: bool = True, backup: bool = True
) -> FileChanges:
    file_changes = analyze_file(filepath)
    if file_changes.error or not file_changes.has_changes:
        return file_changes
    if dry_run:
        return file_changes
    source = filepath.read_text(encoding="utf-8")
    if backup:
        backup_path = filepath.with_suffix(filepath.suffix + ".v2_backup")
        shutil.copy2(filepath, backup_path)
    new_source = rewrite_source_text(source, file_changes.changes)
    filepath.write_text(new_source, encoding="utf-8")
    return file_changes


def rewrite_directory(
    root: Path, dry_run: bool = True, backup: bool = True, include_tests: bool = False
) -> List[FileChanges]:
    results: List[FileChanges] = []
    skip_patterns = [
        "_backup",
        "migration",
        "__pycache__",
        ".git",
        "venv",
        ".venv",
        "env",
    ]
    if not include_tests:
        skip_patterns.extend(["test_", "tests/", "conftest"])
    for pyfile in root.rglob("*.py"):
        path_str = str(pyfile)
        if any(pat in path_str for pat in skip_patterns):
            continue
        if pyfile.name == "migrate_imports_v3.py":
            continue
        file_changes = rewrite_file(pyfile, dry_run, backup)
        if file_changes.has_changes or file_changes.error:
            results.append(file_changes)
    return results


def print_report(results: List[FileChanges], dry_run: bool) -> None:
    print(f"\n{'='*70}")
    print(f" v3.0 Import Migration {'(DRY RUN)' if dry_run else 'Results'}")
    print(f"{'='*70}\n")
    files_with_changes = [r for r in results if r.has_changes]
    files_with_errors = [r for r in results if r.error]
    total_changes = sum(len(r.changes) for r in files_with_changes)
    print("Summary:")
    print(f"  Files with changes: {len(files_with_changes)}")
    print(f"  Total import changes: {total_changes}")
    print(f"  Files with errors: {len(files_with_errors)}")
    print()
    if files_with_changes:
        print("Changes:")
        for fc in sorted(files_with_changes, key=lambda x: str(x.filepath)):
            print(f"\n  {fc.filepath} ({len(fc.changes)} changes):")
            for change in fc.changes:
                print(f"    Line {change.lineno}:")
                print(f"      - {change.old_text}")
                print(f"      + {change.new_text}")
    if files_with_errors:
        print("\nErrors:")
        for fc in files_with_errors:
            print(f"  {fc.filepath}: {fc.error}")
    print(f"\n{'='*70}")
    if dry_run:
        print("This was a DRY RUN. No files were modified.")
    else:
        print("Changes applied successfully.")
    print(f"{'='*70}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate imports from v2.x to v3.0")
    parser.add_argument("--path", default="src/casare_rpa", help="Path to rewrite")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show changes without modifying"
    )
    parser.add_argument("--backup", action="store_true", default=True)
    parser.add_argument("--no-backup", dest="backup", action="store_false")
    parser.add_argument("--file", help="Rewrite a single file")
    parser.add_argument("--include-tests", action="store_true")
    args = parser.parse_args()
    print("\nv3.0 Import Migration Tool")
    print("--------------------------")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'REWRITE'}")
    print(f"Backup: {'Enabled' if args.backup else 'Disabled'}")
    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            return 1
        print(f"Target: {filepath}")
        results = [rewrite_file(filepath, args.dry_run, args.backup)]
    else:
        root = Path(args.path)
        if not root.exists():
            print(f"Error: Directory not found: {root}")
            return 1
        print(f"Target: {root}")
        results = rewrite_directory(root, args.dry_run, args.backup, args.include_tests)
    print_report(results, args.dry_run)
    return 1 if any(r.error for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())

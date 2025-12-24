#!/usr/bin/env python3
"""
Verify that @node-decorated node classes are registered in registry_data.py and have visual nodes.

This hook uses Python AST parsing (not regex) to avoid false positives from docstrings/examples.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


def _run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _changed_paths() -> list[str]:
    output = _run_git(["diff", "--name-only", "--cached"])
    if not output:
        output = _run_git(["diff", "--name-only", "HEAD"])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def _is_node_decorator(decorator: ast.expr) -> bool:
    func = decorator.func if isinstance(decorator, ast.Call) else decorator
    return (isinstance(func, ast.Name) and func.id == "node") or (
        isinstance(func, ast.Attribute) and func.attr == "node"
    )


def _iter_python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if filename.endswith(".py") and filename != "__init__.py":
                files.append(Path(dirpath) / filename)
    return files


def _get_node_classes_from_files(paths: list[Path]) -> set[str]:
    classes: set[str] = set()
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, OSError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if any(_is_node_decorator(dec) for dec in node.decorator_list):
                classes.add(node.name)

    return classes


def get_registered_nodes(registry_file: Path) -> set[str]:
    registered: set[str] = set()
    try:
        tree = ast.parse(registry_file.read_text(encoding="utf-8"), filename=str(registry_file))
    except Exception:
        return registered

    for node in ast.walk(tree):
        target_name: str | None = None
        value: ast.AST | None = None

        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            target_name = node.targets[0].id
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value

        if target_name != "NODE_REGISTRY" or not isinstance(value, ast.Dict):
            continue

        for key in value.keys:
            if isinstance(key, ast.Constant) and isinstance(key.value, str):
                registered.add(key.value)

    return registered


def get_visual_mapped_nodes(visual_dir: Path) -> set[str]:
    """
    Return Casare node class names that have visual counterparts.

    Strategy:
    - Prefer explicit `CASARE_NODE_CLASS = "XNode"` assignments inside visual classes.
    - Fallback to naming convention: VisualXNode -> XNode.
    """

    mapped: set[str] = set()
    for path in _iter_python_files(visual_dir):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, OSError):
            continue

        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue

            casare_name: str | None = None
            for stmt in node.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                ):
                    if stmt.targets[0].id != "CASARE_NODE_CLASS":
                        continue
                    if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
                        casare_name = stmt.value.value
                        break

            if casare_name:
                mapped.add(casare_name)
                continue

            if node.name.startswith("Visual") and node.name.endswith("Node"):
                mapped.add(node.name[6:])

    return mapped


def main() -> int:
    base = Path(__file__).resolve().parents[1]
    node_dir = base / "src" / "casare_rpa" / "nodes"
    registry_file = node_dir / "registry_data.py"
    visual_dir = base / "src" / "casare_rpa" / "presentation" / "canvas" / "visual_nodes"

    if not node_dir.exists() or not registry_file.exists() or not visual_dir.exists():
        return 0

    changed = _changed_paths()
    node_files = [
        (base / rel)
        for rel in changed
        if rel.replace("\\", "/").startswith("src/casare_rpa/nodes/")
        and rel.endswith(".py")
        and not rel.endswith("__init__.py")
    ]

    # Incremental enforcement: only validate @node classes in changed node files.
    if not node_files:
        return 0

    nodes = _get_node_classes_from_files(node_files)
    if not nodes:
        return 0

    registered = get_registered_nodes(registry_file)
    visual_mapped = get_visual_mapped_nodes(visual_dir)

    errors: list[str] = []

    unregistered = nodes - registered
    if unregistered:
        errors.append(
            f"Unregistered nodes (add to registry_data.py): {', '.join(sorted(unregistered))}"
        )

    missing_visual = nodes - visual_mapped
    if missing_visual:
        errors.append(f"Nodes without visual counterparts: {', '.join(sorted(missing_visual))}")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

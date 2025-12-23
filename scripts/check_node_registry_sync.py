#!/usr/bin/env python3
"""
Verify that newly added nodes are registered in registry_data.py and have visual nodes.
"""

import os
import re
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


def get_node_classes_from_files(paths: list[Path]) -> set[str]:
    """Extract @node decorated class names from provided files."""
    classes: set[str] = set()
    for path in paths:
        if path.name == "__init__.py" or path.suffix != ".py":
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        matches = re.findall(r"@node\([^)]*\)\s*class\s+(\w+)\(", content)
        classes.update(matches)

    return classes


def get_registered_nodes(registry_file: str) -> set[str]:
    """Extract all registered nodes from registry_data.py"""
    registered = set()
    with open(registry_file, encoding="utf-8") as f:
        content = f.read()
        # Find NODE_TYPE_MAP entries - match actual node class names
        matches = re.findall(r'"(\w+Node)"\s*:\s*', content)
        registered.update(matches)
    return registered


def get_visual_nodes(visual_dir: str) -> set[str]:
    """Extract all visual node class names"""
    visual = set()
    for root, _, files in os.walk(visual_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                path = os.path.join(root, file)
                with open(path) as f:
                    content = f.read()
                    matches = re.findall(r"class\s+(\w+)\(.*Node.*\):", content)
                    visual.update(matches)
    return visual


def main():
    base = Path(__file__).parent.parent
    node_dir = base / "src" / "casare_rpa" / "nodes"
    registry_file = node_dir / "registry_data.py"
    visual_dir = base / "src" / "casare_rpa" / "presentation" / "canvas" / "visual_nodes"

    if not node_dir.exists() or not registry_file.exists():
        return 0

    changed = _changed_paths()

    node_files = [
        (base / rel)
        for rel in changed
        if rel.replace("\\", "/").startswith("src/casare_rpa/nodes/")
        and rel.endswith(".py")
        and not rel.endswith("__init__.py")
    ]

    nodes = get_node_classes_from_files(node_files)
    if not nodes:
        return 0

    registered = get_registered_nodes(str(registry_file))
    visual = get_visual_nodes(str(visual_dir))

    errors = []

    # Check unregistered nodes
    unregistered = nodes - registered
    if unregistered:
        errors.append(
            f"Unregistered nodes (add to registry_data.py): {', '.join(sorted(unregistered))}"
        )

    # Check nodes without visual nodes
    missing_visual = nodes - visual
    if missing_visual:
        errors.append(f"Nodes without visual counterparts: {', '.join(sorted(missing_visual))}")

    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

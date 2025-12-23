#!/usr/bin/env python3
"""
Verify that newly added nodes are registered in registry_data.py and have visual nodes.
"""

import os
import re
import sys
from pathlib import Path


def get_node_classes(node_dir: str) -> set[str]:
    """Extract all node class names from src/casare_rpa/nodes/"""
    classes = set()
    for root, _, files in os.walk(node_dir):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                path = os.path.join(root, file)
                with open(path) as f:
                    content = f.read()
                    # Find @node decorated classes
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

    nodes = get_node_classes(str(node_dir))
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

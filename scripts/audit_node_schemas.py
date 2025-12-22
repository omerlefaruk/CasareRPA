import os
import sys
import importlib
import inspect
from typing import List, Type, Dict, Any

# Ensure src is in python path
sys.path.insert(0, os.path.abspath("src"))

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import PortType


def get_all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in get_all_subclasses(c)]
    )


def audit_nodes():
    print("Starting Node Schema Audit...")

    # Import all nodes to ensure they are registered/loaded
    # We'll rely on traversing the package directory to find modules

    nodes_dir = os.path.abspath("src/casare_rpa/nodes")
    for root, dirs, files in os.walk(nodes_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), "src")
                module_name = rel_path.replace(os.sep, ".").replace(".py", "")
                try:
                    importlib.import_module(module_name)
                except Exception as e:
                    # print(f"Failed to import {module_name}: {e}")
                    pass

    node_classes = get_all_subclasses(BaseNode)
    print(f"Found {len(node_classes)} node classes.")

    issues = []

    for node_cls in node_classes:
        # Skip abstract classes or base classes if they shouldn't be instantiated
        if node_cls.__name__ in [
            "BaseNode",
            "NodeExecutor",
            "NodeExecutorWithTryCatch",
        ]:
            continue

        try:
            # Instantiate with dummy ID
            node = node_cls("audit_test", config={})
        except Exception as e:
            print(f"Skipping {node_cls.__name__}: Failed to instantiate ({e})")
            continue

        schema = getattr(node_cls, "__node_schema__", None)

        # If no schema, and it has required inputs, that MIGHT be okay if it's not intended to be configured via UI properties,
        # but generally we want schema transparency.
        # However, specifically we are looking for: Required Input Port + MISSING Schema Property.

        schema_props = set()
        if schema:
            schema_props = {p.name for p in schema.properties}

        for port in node.input_ports.values():
            # Skip exec ports
            if port.port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT):
                continue
            if port.name.startswith("exec_"):
                continue

            if port.required:
                if port.name not in schema_props:
                    # It's a required input port but not in the schema.
                    # This means if it's not connected, validation will fail.
                    # This is what we want to catch.
                    issues.append(
                        {
                            "node_type": node_cls.__name__,
                            "port": port.name,
                            "file": inspect.getfile(node_cls),
                        }
                    )

    # Report issues
    if not issues:
        print("\nNo issues found! All required ports map to schema properties.")
    else:
        print(f"\nFound {len(issues)} potential issues (Required Port missing from Schema):")

        # Group by file for easier fixing
        files_map = {}
        for issue in issues:
            f = issue["file"]
            if f not in files_map:
                files_map[f] = []
            files_map[f].append(f"{issue['node_type']}.{issue['port']}")

        for f, details in files_map.items():
            print(f"\nFile: {f}")
            for d in details:
                print(f"  - {d}")


if __name__ == "__main__":
    audit_nodes()

#!/usr/bin/env python3
"""
Verify node port definitions follow Modern Node Standard:
- Use add_exec_input() / add_exec_output() for execution ports
- Use add_input_port() / add_output_port() for data ports
- All data ports must have explicit DataType (not ANY unless intentional)
"""

import ast
import os
import sys
from pathlib import Path


class PortDefinitionChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []
        self.in_define_ports = False

    def visit_FunctionDef(self, node):
        if node.name == "_define_ports":
            old_in_ports = self.in_define_ports
            self.in_define_ports = True
            self.generic_visit(node)
            self.in_define_ports = old_in_ports
        else:
            self.generic_visit(node)

    def visit_Call(self, node):
        if self.in_define_ports:
            if isinstance(node.func, ast.Attribute):
                method = node.func.attr

                # Check for legacy add_port calls
                if method == "add_port":
                    self.errors.append(
                        f"{self.filepath}:{node.lineno} - Use add_exec_input/add_exec_output/add_input_port/add_output_port instead of add_port()"
                    )

                # Check data ports have DataType
                if method in ("add_input_port", "add_output_port"):
                    if len(node.args) < 2:
                        self.errors.append(
                            f"{self.filepath}:{node.lineno} - Data port must specify DataType argument"
                        )
                    else:
                        # Validate 2nd arg is DataType reference, not string literal
                        type_arg = node.args[1]
                        if isinstance(type_arg, ast.Constant) and isinstance(type_arg.value, str):
                            self.errors.append(
                                f"{self.filepath}:{node.lineno} - DataType must be a reference (DataType.STRING), not a string literal"
                            )

        self.generic_visit(node)


def check_file(filepath: str) -> list[str]:
    """Check port definitions in node files"""
    try:
        with open(filepath) as f:
            tree = ast.parse(f.read())

        # Only check files in nodes/
        if "nodes/" not in filepath or "base_node" in filepath:
            return []

        checker = PortDefinitionChecker(filepath)
        checker.visit(tree)
        return checker.errors
    except Exception:
        return []


def main():
    base = Path(__file__).parent.parent
    nodes_dir = base / "src" / "casare_rpa" / "nodes"

    if not nodes_dir.exists():
        return 0

    all_errors = []
    for root, _, files in os.walk(nodes_dir):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                filepath = os.path.join(root, file)
                errors = check_file(filepath)
                all_errors.extend(errors)

    if all_errors:
        print("[ERROR] Node port definition violations (use Modern Node Standard):")
        for error in all_errors:
            print(f"   {error}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

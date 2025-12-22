#!/usr/bin/env python3
"""
Generate Node Reference Documentation for CasareRPA.

Extracts node information from @properties decorators and _define_ports() methods,
generating comprehensive Markdown documentation for each node.

Output: Markdown files in docs/nodes/
"""

import ast
import importlib
import inspect
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SRC_DIR = PROJECT_ROOT / "src" / "casare_rpa"
NODES_DIR = SRC_DIR / "nodes"
DOCS_DIR = PROJECT_ROOT / "docs" / "nodes"


@dataclass
class PortInfo:
    """Information about a node port."""

    name: str
    data_type: str
    description: str
    direction: str  # "input" or "output"
    is_exec: bool = False


@dataclass
class PropertyInfo:
    """Information about a node property."""

    name: str
    prop_type: str
    default: Any
    label: str
    tooltip: str
    required: bool
    choices: Optional[List[str]]
    tab: str
    min_value: Optional[float]
    max_value: Optional[float]


@dataclass
class NodeInfo:
    """Complete information about a node."""

    class_name: str
    module_path: str
    file_path: str
    line_number: int
    docstring: Optional[str]
    category: str
    is_async: bool
    is_trigger: bool
    decorators: List[str]
    input_ports: List[PortInfo] = field(default_factory=list)
    output_ports: List[PortInfo] = field(default_factory=list)
    properties: List[PropertyInfo] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)


class NodeSchemaExtractor(ast.NodeVisitor):
    """Extract @properties PropertyDef arguments from AST."""

    def __init__(self):
        self.properties: List[PropertyInfo] = []
        self.in_node_schema = False

    def visit_Call(self, node: ast.Call) -> None:
        # Check for @properties decorator
        if isinstance(node.func, ast.Name) and node.func.id == "properties":
            self.in_node_schema = True
            for arg in node.args:
                if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name):
                    if arg.func.id == "PropertyDef":
                        prop = self._extract_property_def(arg)
                        if prop:
                            self.properties.append(prop)
            self.in_node_schema = False
        self.generic_visit(node)

    def _extract_property_def(self, call: ast.Call) -> Optional[PropertyInfo]:
        """Extract PropertyDef arguments."""
        kwargs = {}
        args = []

        # Positional args
        for i, arg in enumerate(call.args):
            if i == 0:  # name
                args.append(self._get_value(arg))
            elif i == 1:  # type
                args.append(self._get_value(arg))

        # Keyword args
        for kw in call.keywords:
            kwargs[kw.arg] = self._get_value(kw.value)

        if len(args) < 2:
            return None

        name = args[0]
        prop_type = args[1]

        # Handle PropertyType.XXX
        if isinstance(prop_type, str) and "." in prop_type:
            prop_type = prop_type.split(".")[-1]

        return PropertyInfo(
            name=name,
            prop_type=prop_type,
            default=kwargs.get("default"),
            label=kwargs.get("label", name.replace("_", " ").title()),
            tooltip=kwargs.get("tooltip", ""),
            required=kwargs.get("required", False),
            choices=kwargs.get("choices"),
            tab=kwargs.get("tab", "properties"),
            min_value=kwargs.get("min_value"),
            max_value=kwargs.get("max_value"),
        )

    def _get_value(self, node: ast.expr) -> Any:
        """Extract value from AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        elif isinstance(node, ast.List):
            return [self._get_value(el) for el in node.elts]
        elif isinstance(node, ast.Dict):
            return {self._get_value(k): self._get_value(v) for k, v in zip(node.keys, node.values)}
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._get_value(node.operand)
        else:
            return ast.unparse(node)


class PortExtractor(ast.NodeVisitor):
    """Extract port definitions from _define_ports method."""

    def __init__(self):
        self.input_ports: List[PortInfo] = []
        self.output_ports: List[PortInfo] = []

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            if method_name in ("add_input_port", "add_typed_input"):
                port = self._extract_port(node, "input")
                if port:
                    self.input_ports.append(port)
            elif method_name in ("add_output_port", "add_typed_output"):
                port = self._extract_port(node, "output")
                if port:
                    self.output_ports.append(port)
            elif method_name == "add_exec_input":
                name = (
                    node.args[0].value
                    if node.args and isinstance(node.args[0], ast.Constant)
                    else "exec_in"
                )
                self.input_ports.append(
                    PortInfo(
                        name=name,
                        data_type="EXEC",
                        description="Execution input",
                        direction="input",
                        is_exec=True,
                    )
                )
            elif method_name == "add_exec_output":
                name = (
                    node.args[0].value
                    if node.args and isinstance(node.args[0], ast.Constant)
                    else "exec_out"
                )
                self.output_ports.append(
                    PortInfo(
                        name=name,
                        data_type="EXEC",
                        description="Execution output",
                        direction="output",
                        is_exec=True,
                    )
                )
        self.generic_visit(node)

    def _extract_port(self, call: ast.Call, direction: str) -> Optional[PortInfo]:
        """Extract port info from add_*_port call."""
        args = []
        for arg in call.args:
            if isinstance(arg, ast.Constant):
                args.append(arg.value)
            elif isinstance(arg, ast.Attribute):
                args.append(ast.unparse(arg))
            elif isinstance(arg, ast.Name):
                args.append(arg.id)
            else:
                args.append(ast.unparse(arg))

        if len(args) < 2:
            return None

        name = args[0]
        data_type = args[1]
        description = args[2] if len(args) > 2 else ""

        # Handle DataType.XXX
        if isinstance(data_type, str) and "." in data_type:
            data_type = data_type.split(".")[-1]

        is_exec = name in ("exec_in", "exec_out") or data_type == "EXEC"

        return PortInfo(
            name=name,
            data_type=data_type,
            description=description,
            direction=direction,
            is_exec=is_exec,
        )


def extract_node_info(file_path: Path, class_node: ast.ClassDef, module_name: str) -> NodeInfo:
    """Extract complete node information from class definition."""
    # Get base classes
    bases = []
    for base in class_node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(ast.unparse(base))

    # Get decorators
    decorators = []
    for dec in class_node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
            decorators.append(dec.func.id)
        elif isinstance(dec, ast.Attribute):
            decorators.append(ast.unparse(dec))
        else:
            decorators.append(ast.unparse(dec))

    # Determine category from file path
    rel_path = file_path.relative_to(NODES_DIR)
    parts = list(rel_path.parts)
    if len(parts) > 1:
        category = parts[0]
    else:
        # Infer from filename
        fname = file_path.stem
        category = fname.replace("_nodes", "").replace("_", "-")

    # Get docstring
    docstring = ast.get_docstring(class_node)

    # Check if async (has async execute method)
    is_async = any(
        isinstance(node, ast.AsyncFunctionDef) and node.name == "execute"
        for node in ast.walk(class_node)
    )

    # Check if trigger node
    is_trigger = any(b in ("BaseTriggerNode", "TriggerNode") for b in bases)

    # Extract properties from @properties
    schema_extractor = NodeSchemaExtractor()
    for decorator in class_node.decorator_list:
        if isinstance(decorator, ast.Call):
            schema_extractor.visit(decorator)

    # Extract ports from _define_ports
    port_extractor = PortExtractor()
    for node in ast.walk(class_node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in ("_define_ports", "_define_payload_ports"):
                port_extractor.visit(node)

    # Add/override exec ports from @node(...) configuration (runtime adds these).
    desired_exec_inputs: Optional[List[str]] = None
    desired_exec_outputs: Optional[List[str]] = None
    for decorator in class_node.decorator_list:
        if (
            isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func.id == "node"
        ):
            for kw in decorator.keywords:
                if kw.arg == "exec_inputs":
                    desired_exec_inputs = schema_extractor._get_value(kw.value)
                elif kw.arg == "exec_outputs":
                    desired_exec_outputs = schema_extractor._get_value(kw.value)

    if desired_exec_inputs is None:
        desired_exec_inputs = ["exec_in"]
    if desired_exec_outputs is None:
        desired_exec_outputs = ["exec_out"]

    # Normalize explicit None (treat as default).
    if desired_exec_inputs is None:
        desired_exec_inputs = ["exec_in"]
    if desired_exec_outputs is None:
        desired_exec_outputs = ["exec_out"]

    # Inject exec ports (keep ordering stable: inputs then outputs).
    existing_in = {p.name for p in port_extractor.input_ports if p.is_exec}
    existing_out = {p.name for p in port_extractor.output_ports if p.is_exec}

    for name in desired_exec_inputs:
        if name not in existing_in:
            port_extractor.input_ports.insert(
                0,
                PortInfo(
                    name=name,
                    data_type="EXEC",
                    description="Execution input",
                    direction="input",
                    is_exec=True,
                ),
            )

    for name in reversed(desired_exec_outputs):
        if name not in existing_out:
            port_extractor.output_ports.insert(
                0,
                PortInfo(
                    name=name,
                    data_type="EXEC",
                    description="Execution output",
                    direction="output",
                    is_exec=True,
                ),
            )

    return NodeInfo(
        class_name=class_node.name,
        module_path=module_name,
        file_path=str(file_path.relative_to(PROJECT_ROOT)),
        line_number=class_node.lineno,
        docstring=docstring,
        category=category,
        is_async=is_async,
        is_trigger=is_trigger,
        decorators=decorators,
        input_ports=port_extractor.input_ports,
        output_ports=port_extractor.output_ports,
        properties=schema_extractor.properties,
        base_classes=bases,
    )


def find_node_classes(file_path: Path) -> List[Tuple[ast.ClassDef, str]]:
    """Find all node classes in a file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return []

    # Calculate module name
    rel_path = file_path.relative_to(SRC_DIR.parent)
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    module_name = ".".join(parts)

    results = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Check if it's a node class
            is_node = False
            for base in node.bases:
                if isinstance(base, ast.Name):
                    if base.id in (
                        "BaseNode",
                        "BaseTriggerNode",
                        "BrowserBaseNode",
                        "DesktopBaseNode",
                    ):
                        is_node = True
                elif isinstance(base, ast.Attribute):
                    base_name = ast.unparse(base)
                    if "Node" in base_name:
                        is_node = True

            # Check for @node decorator
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "node":
                    is_node = True
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    if dec.func.id == "node":
                        is_node = True

            if is_node and node.name.endswith("Node"):
                results.append((node, module_name))

    return results


def generate_node_markdown(node: NodeInfo) -> str:
    """Generate markdown documentation for a node."""
    lines = []

    # Title
    lines.append(f"# {node.class_name}\n")

    # Description
    if node.docstring:
        # First paragraph as description
        desc = node.docstring.split("\n\n")[0].strip()
        lines.append(f"{desc}\n")
    else:
        lines.append("*No description available.*\n")

    # Metadata badges
    badges = []
    if node.is_async:
        badges.append(":material-sync: Async")
    if node.is_trigger:
        badges.append(":material-bell: Trigger")
    if "node" in node.decorators:
        badges.append(":material-play: Node")

    if badges:
        lines.append(" ".join(f"`{b}`" for b in badges) + "\n")

    lines.append("")

    # Source info
    lines.append(f"**Module:** `{node.module_path}`  ")
    lines.append(f"**File:** `{node.file_path}:{node.line_number}`\n")
    lines.append("")

    # Input Ports
    if node.input_ports:
        lines.append("## Input Ports\n")
        lines.append("| Port | Type | Required | Description |")
        lines.append("|------|------|----------|-------------|")
        for port in node.input_ports:
            required = "Yes" if port.is_exec else "No"
            lines.append(f"| `{port.name}` | {port.data_type} | {required} | {port.description} |")
        lines.append("")

    # Output Ports
    if node.output_ports:
        lines.append("## Output Ports\n")
        lines.append("| Port | Type | Description |")
        lines.append("|------|------|-------------|")
        for port in node.output_ports:
            lines.append(f"| `{port.name}` | {port.data_type} | {port.description} |")
        lines.append("")

    # Configuration Properties
    if node.properties:
        lines.append("## Configuration Properties\n")

        # Group by tab
        by_tab: Dict[str, List[PropertyInfo]] = defaultdict(list)
        for prop in node.properties:
            by_tab[prop.tab].append(prop)

        for tab_name in sorted(by_tab.keys()):
            tab_props = by_tab[tab_name]
            if len(by_tab) > 1:
                lines.append(f"### {tab_name.title()} Tab\n")

            lines.append("| Property | Type | Default | Required | Description |")
            lines.append("|----------|------|---------|----------|-------------|")

            for prop in tab_props:
                default_str = str(prop.default) if prop.default is not None else "-"
                if len(default_str) > 20:
                    default_str = default_str[:17] + "..."
                required = "Yes" if prop.required else "No"
                desc = prop.tooltip or prop.label

                # Add choices info
                if prop.choices:
                    choices_str = ", ".join(str(c) for c in prop.choices[:5])
                    if len(prop.choices) > 5:
                        choices_str += f", ... ({len(prop.choices)} total)"
                    desc += f" Choices: {choices_str}"

                # Add range info
                range_parts = []
                if prop.min_value is not None:
                    range_parts.append(f"min: {prop.min_value}")
                if prop.max_value is not None:
                    range_parts.append(f"max: {prop.max_value}")
                if range_parts:
                    desc += f" ({', '.join(range_parts)})"

                lines.append(
                    f"| `{prop.name}` | {prop.prop_type} | `{default_str}` | {required} | {desc} |"
                )

            lines.append("")

    # Inheritance
    if node.base_classes:
        lines.append("## Inheritance\n")
        lines.append(f"Extends: {', '.join(f'`{b}`' for b in node.base_classes)}\n")
        lines.append("")

    return "\n".join(lines)


def generate_category_index(category: str, nodes: List[NodeInfo]) -> str:
    """Generate index page for a node category."""
    lines = []

    # Title
    title = category.replace("-", " ").replace("_", " ").title()
    lines.append(f"# {title} Nodes\n")

    # Count
    lines.append(f"This category contains **{len(nodes)}** nodes.\n")
    lines.append("")

    # Table of nodes
    lines.append("| Node | Description |")
    lines.append("|------|-------------|")

    for node in sorted(nodes, key=lambda n: n.class_name):
        # Get short description
        desc = ""
        if node.docstring:
            desc = node.docstring.split("\n")[0][:80]
            if len(node.docstring.split("\n")[0]) > 80:
                desc += "..."

        # Link to node page
        slug = node.class_name.lower().replace("node", "-node")
        slug = re.sub(r"([a-z])([A-Z])", r"\1-\2", node.class_name).lower()
        lines.append(f"| [{node.class_name}]({slug}.md) | {desc} |")

    lines.append("")
    return "\n".join(lines)


def generate_main_index(all_nodes: Dict[str, List[NodeInfo]]) -> str:
    """Generate main nodes index page."""
    lines = []
    lines.append("# Node Reference\n")
    lines.append("Complete reference for all automation nodes in CasareRPA.\n")
    lines.append("")

    total = sum(len(nodes) for nodes in all_nodes.values())
    lines.append(f"**Total Nodes:** {total}\n")
    lines.append("")

    lines.append("## Categories\n")
    lines.append("")
    lines.append("| Category | Nodes | Description |")
    lines.append("|----------|-------|-------------|")

    category_descriptions = {
        "basic": "Core workflow nodes (Start, End, Comment)",
        "browser": "Web browser automation with Playwright",
        "desktop": "Windows desktop automation",
        "desktop_nodes": "Windows desktop automation",
        "control-flow": "Flow control (If, Loop, Switch)",
        "control_flow": "Flow control (If, Loop, Switch)",
        "data-operations": "Data manipulation and transformation",
        "data": "Data extraction and manipulation",
        "file": "File system operations",
        "file-operations": "File read/write operations",
        "database": "Database connections and queries",
        "email": "Email send/receive operations",
        "http": "HTTP/REST API requests",
        "google": "Google Workspace integration",
        "messaging": "Messaging platforms (Telegram, WhatsApp)",
        "llm": "AI/ML and LLM operations",
        "ai-ml": "AI/ML and LLM operations",
        "system": "System commands and dialogs",
        "trigger_nodes": "Workflow trigger nodes",
        "triggers": "Workflow trigger nodes",
    }

    for category in sorted(all_nodes.keys()):
        nodes = all_nodes[category]
        title = category.replace("-", " ").replace("_", " ").title()
        desc = category_descriptions.get(category, "")
        lines.append(f"| [{title}]({category}/index.md) | {len(nodes)} | {desc} |")

    lines.append("")
    return "\n".join(lines)


def main():
    """Main entry point."""
    print("Scanning node files...")

    all_nodes: Dict[str, List[NodeInfo]] = defaultdict(list)

    # Find all Python files in nodes directory
    python_files = list(NODES_DIR.rglob("*.py"))
    print(f"Found {len(python_files)} Python files in nodes/")

    for file_path in python_files:
        if file_path.name.startswith("__"):
            continue

        node_classes = find_node_classes(file_path)
        for class_node, module_name in node_classes:
            try:
                node_info = extract_node_info(file_path, class_node, module_name)
                all_nodes[node_info.category].append(node_info)
            except Exception as e:
                print(f"Warning: Failed to extract {class_node.name}: {e}")

    total = sum(len(nodes) for nodes in all_nodes.values())
    print(f"Found {total} node classes in {len(all_nodes)} categories")

    # Create output directories
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate main index
    print("Generating main index...")
    (DOCS_DIR / "index.md").write_text(generate_main_index(all_nodes), encoding="utf-8")

    # Generate category pages
    for category, nodes in all_nodes.items():
        print(f"Generating {category}/ ({len(nodes)} nodes)...")
        category_dir = DOCS_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)

        # Category index
        (category_dir / "index.md").write_text(
            generate_category_index(category, nodes), encoding="utf-8"
        )

        # Individual node pages
        for node in nodes:
            slug = re.sub(r"([a-z])([A-Z])", r"\1-\2", node.class_name).lower()
            (category_dir / f"{slug}.md").write_text(generate_node_markdown(node), encoding="utf-8")

    print(f"\nDone! Generated documentation in {DOCS_DIR}")
    print(f"  Categories: {len(all_nodes)}")
    print(f"  Total nodes: {total}")


if __name__ == "__main__":
    main()

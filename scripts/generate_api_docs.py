#!/usr/bin/env python3
"""
Generate API Reference Documentation for CasareRPA.

Extracts class and function information from all layers,
generating comprehensive Markdown API documentation.

Output: Markdown files in docs/api/
"""

import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SRC_DIR = PROJECT_ROOT / "src" / "casare_rpa"
DOCS_DIR = PROJECT_ROOT / "docs" / "api"


@dataclass
class ParameterInfo:
    """Information about a function parameter."""

    name: str
    type_hint: str | None
    default: str | None
    is_required: bool


@dataclass
class MethodInfo:
    """Information about a method or function."""

    name: str
    parameters: list[ParameterInfo]
    return_type: str | None
    docstring: str | None
    decorators: list[str]
    is_async: bool
    is_property: bool
    is_classmethod: bool
    is_staticmethod: bool
    is_private: bool
    line_number: int


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    module: str
    file_path: str
    line_number: int
    bases: list[str]
    docstring: str | None
    decorators: list[str]
    methods: list[MethodInfo] = field(default_factory=list)
    class_attributes: dict[str, str] = field(default_factory=dict)


@dataclass
class ModuleInfo:
    """Information about a module."""

    name: str
    file_path: str
    docstring: str | None
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[MethodInfo] = field(default_factory=list)
    constants: dict[str, str] = field(default_factory=dict)


class ModuleAnalyzer(ast.NodeVisitor):
    """AST visitor to extract module information."""

    def __init__(self, module_name: str, file_path: str):
        self.module = ModuleInfo(
            name=module_name,
            file_path=file_path,
            docstring=None,
        )
        self.current_class: ClassInfo | None = None

    def visit_Module(self, node: ast.Module) -> None:
        self.module.docstring = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Skip private classes for documentation
        if node.name.startswith("_") and not node.name.startswith("__"):
            return

        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))
            else:
                bases.append(ast.unparse(base))

        decorators = [self._get_decorator_name(d) for d in node.decorator_list]

        class_info = ClassInfo(
            name=node.name,
            module=self.module.name,
            file_path=self.module.file_path,
            line_number=node.lineno,
            bases=bases,
            docstring=ast.get_docstring(node),
            decorators=decorators,
        )

        # Extract class attributes
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attr_name = item.target.id
                attr_type = ast.unparse(item.annotation) if item.annotation else "Any"
                class_info.class_attributes[attr_name] = attr_type
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        class_info.class_attributes[target.id] = self._infer_type(item.value)

        # Visit methods
        old_class = self.current_class
        self.current_class = class_info
        self.generic_visit(node)
        self.current_class = old_class

        self.module.classes.append(class_info)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node, is_async=True)

    def _process_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
        # Skip very private methods (double underscore except dunder)
        if node.name.startswith("__") and not node.name.endswith("__"):
            return

        # Determine decorator types
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        is_property = "property" in decorators or any("setter" in d for d in decorators)
        is_classmethod = "classmethod" in decorators
        is_staticmethod = "staticmethod" in decorators
        is_private = node.name.startswith("_") and not node.name.startswith("__")

        # Extract parameters
        params = self._extract_parameters(node)

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        method_info = MethodInfo(
            name=node.name,
            parameters=params,
            return_type=return_type,
            docstring=ast.get_docstring(node),
            decorators=decorators,
            is_async=is_async,
            is_property=is_property,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
            is_private=is_private,
            line_number=node.lineno,
        )

        if self.current_class:
            self.current_class.methods.append(method_info)
        else:
            self.module.functions.append(method_info)

    def _extract_parameters(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[ParameterInfo]:
        """Extract parameter information from function definition."""
        params = []
        args = node.args

        # Calculate defaults offset
        num_defaults = len(args.defaults)
        num_args = len(args.args)
        first_default_idx = num_args - num_defaults

        for i, arg in enumerate(args.args):
            # Skip self/cls
            if arg.arg in ("self", "cls"):
                continue

            type_hint = None
            if arg.annotation:
                type_hint = ast.unparse(arg.annotation)

            default = None
            is_required = True
            if i >= first_default_idx:
                default_idx = i - first_default_idx
                default = ast.unparse(args.defaults[default_idx])
                is_required = False

            params.append(
                ParameterInfo(
                    name=arg.arg,
                    type_hint=type_hint,
                    default=default,
                    is_required=is_required,
                )
            )

        # Add *args
        if args.vararg:
            params.append(
                ParameterInfo(
                    name=f"*{args.vararg.arg}",
                    type_hint=ast.unparse(args.vararg.annotation)
                    if args.vararg.annotation
                    else None,
                    default=None,
                    is_required=False,
                )
            )

        # Add **kwargs
        if args.kwarg:
            params.append(
                ParameterInfo(
                    name=f"**{args.kwarg.arg}",
                    type_hint=ast.unparse(args.kwarg.annotation) if args.kwarg.annotation else None,
                    default=None,
                    is_required=False,
                )
            )

        return params

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return ast.unparse(node.func)
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

    def _infer_type(self, node: ast.expr) -> str:
        """Infer type from value node."""
        if isinstance(node, ast.Constant):
            return type(node.value).__name__
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
        return "Any"


def analyze_file(file_path: Path, base_path: Path) -> ModuleInfo | None:
    """Analyze a single Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return None

    # Calculate module name
    rel_path = file_path.relative_to(base_path)
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    module_name = ".".join(parts)

    analyzer = ModuleAnalyzer(module_name, str(file_path.relative_to(PROJECT_ROOT)))
    analyzer.visit(tree)

    # Skip empty modules
    if not analyzer.module.classes and not analyzer.module.functions:
        return None

    return analyzer.module


def generate_method_signature(method: MethodInfo) -> str:
    """Generate method signature string."""
    parts = []

    # Add decorators indicator
    if method.is_property:
        parts.append("@property")
    elif method.is_classmethod:
        parts.append("@classmethod")
    elif method.is_staticmethod:
        parts.append("@staticmethod")

    # Build signature
    if method.is_async:
        sig = "async def "
    else:
        sig = "def "

    sig += method.name + "("

    param_strs = []
    for param in method.parameters:
        p = param.name
        if param.type_hint:
            p += f": {param.type_hint}"
        if param.default is not None:
            p += f" = {param.default}"
        param_strs.append(p)

    sig += ", ".join(param_strs)
    sig += ")"

    if method.return_type:
        sig += f" -> {method.return_type}"

    if parts:
        return "\n".join(parts) + "\n" + sig
    return sig


def generate_class_markdown(cls: ClassInfo) -> str:
    """Generate markdown for a class."""
    lines = []

    # Class header
    lines.append(f"### {cls.name}\n")

    # Inheritance
    if cls.bases:
        lines.append(f"**Inherits from:** {', '.join(f'`{b}`' for b in cls.bases)}\n")

    # Decorators
    if cls.decorators:
        lines.append(f"**Decorators:** {', '.join(f'`@{d}`' for d in cls.decorators)}\n")

    # Docstring
    if cls.docstring:
        lines.append(f"\n{cls.docstring}\n")

    lines.append("")

    # Class attributes
    if cls.class_attributes:
        lines.append("**Attributes:**\n")
        for name, type_hint in sorted(cls.class_attributes.items()):
            lines.append(f"- `{name}: {type_hint}`")
        lines.append("")

    # Methods
    public_methods = [m for m in cls.methods if not m.is_private]
    private_methods = [m for m in cls.methods if m.is_private]

    if public_methods:
        lines.append("**Methods:**\n")
        lines.append("| Method | Returns | Description |")
        lines.append("|--------|---------|-------------|")

        for method in sorted(public_methods, key=lambda m: m.name):
            # Build signature summary
            async_prefix = "async " if method.is_async else ""
            params_summary = ", ".join(p.name for p in method.parameters[:3])
            if len(method.parameters) > 3:
                params_summary += ", ..."

            sig = f"`{async_prefix}{method.name}({params_summary})`"

            returns = f"`{method.return_type}`" if method.return_type else "-"

            # First line of docstring
            desc = ""
            if method.docstring:
                desc = method.docstring.split("\n")[0][:60]
                if len(method.docstring.split("\n")[0]) > 60:
                    desc += "..."

            lines.append(f"| {sig} | {returns} | {desc} |")

        lines.append("")

    # Detailed method documentation
    if public_methods:
        lines.append("#### Method Details\n")
        for method in sorted(public_methods, key=lambda m: m.name):
            lines.append(f"##### `{method.name}`\n")
            lines.append("```python")
            lines.append(generate_method_signature(method))
            lines.append("```\n")

            if method.docstring:
                lines.append(method.docstring)
                lines.append("")

            if method.parameters:
                lines.append("**Parameters:**\n")
                for param in method.parameters:
                    type_str = f": {param.type_hint}" if param.type_hint else ""
                    default_str = f" = {param.default}" if param.default else ""
                    required = " *(required)*" if param.is_required else ""
                    lines.append(f"- `{param.name}{type_str}{default_str}`{required}")
                lines.append("")

    return "\n".join(lines)


def generate_module_markdown(module: ModuleInfo) -> str:
    """Generate markdown for a module."""
    lines = []

    # Module header
    lines.append(f"## {module.name}\n")
    lines.append(f"**File:** `{module.file_path}`\n")

    if module.docstring:
        lines.append(f"\n{module.docstring}\n")

    lines.append("")

    # Module-level functions
    if module.functions:
        public_funcs = [f for f in module.functions if not f.is_private]
        if public_funcs:
            lines.append("### Functions\n")
            for func in sorted(public_funcs, key=lambda f: f.name):
                lines.append(f"#### `{func.name}`\n")
                lines.append("```python")
                lines.append(generate_method_signature(func))
                lines.append("```\n")
                if func.docstring:
                    lines.append(func.docstring)
                    lines.append("")
            lines.append("")

    # Classes
    for cls in sorted(module.classes, key=lambda c: c.name):
        lines.append(generate_class_markdown(cls))

    return "\n".join(lines)


def generate_layer_index(layer: str, modules: list[ModuleInfo]) -> str:
    """Generate index page for a layer."""
    lines = []

    title = layer.replace("-", " ").replace("_", " ").title()
    lines.append(f"# {title} Layer API\n")

    # Count stats
    total_classes = sum(len(m.classes) for m in modules)
    total_functions = sum(len(m.functions) for m in modules)

    lines.append(
        f"**Modules:** {len(modules)} | **Classes:** {total_classes} | **Functions:** {total_functions}\n"
    )
    lines.append("")

    # Module list
    lines.append("## Modules\n")
    lines.append("| Module | Classes | Functions | Description |")
    lines.append("|--------|---------|-----------|-------------|")

    for module in sorted(modules, key=lambda m: m.name):
        desc = ""
        if module.docstring:
            desc = module.docstring.split("\n")[0][:50]
            if len(module.docstring.split("\n")[0]) > 50:
                desc += "..."
        lines.append(
            f"| `{module.name}` | {len(module.classes)} | {len(module.functions)} | {desc} |"
        )

    lines.append("")

    # Detailed documentation
    for module in sorted(modules, key=lambda m: m.name):
        lines.append(generate_module_markdown(module))
        lines.append("---\n")

    return "\n".join(lines)


def generate_main_index(layers: dict[str, list[ModuleInfo]]) -> str:
    """Generate main API index."""
    lines = []
    lines.append("# API Reference\n")
    lines.append("Complete API documentation for CasareRPA.\n")
    lines.append("")

    # Stats
    total_modules = sum(len(mods) for mods in layers.values())
    total_classes = sum(sum(len(m.classes) for m in mods) for mods in layers.values())
    total_functions = sum(sum(len(m.functions) for m in mods) for mods in layers.values())

    lines.append(
        f"**Total:** {total_modules} modules, {total_classes} classes, {total_functions} functions\n"
    )
    lines.append("")

    # Layer summary
    lines.append("## Architecture Layers\n")
    lines.append("")
    lines.append("| Layer | Modules | Classes | Description |")
    lines.append("|-------|---------|---------|-------------|")

    layer_descriptions = {
        "domain": "Pure business logic, entities, value objects, and domain services",
        "application": "Use cases, orchestration, and application services",
        "infrastructure": "External integrations, persistence, security, and resources",
        "presentation": "UI components, canvas, controllers, and panels",
    }

    for layer in ["domain", "application", "infrastructure", "presentation"]:
        if layer in layers:
            mods = layers[layer]
            total = sum(len(m.classes) for m in mods)
            desc = layer_descriptions.get(layer, "")
            lines.append(
                f"| [{layer.title()}]({layer}/index.md) | {len(mods)} | {total} | {desc} |"
            )

    lines.append("")

    # Quick links
    lines.append("## Quick Links\n")
    lines.append("")
    lines.append("### Domain Layer")
    lines.append("- [Entities](domain/entities.md) - Core domain objects")
    lines.append("- [Value Objects](domain/value-objects.md) - Immutable values")
    lines.append("- [Services](domain/services.md) - Domain services")
    lines.append("- [Decorators](domain/decorators.md) - Node decorators")
    lines.append("")
    lines.append("### Application Layer")
    lines.append("- [Use Cases](application/use-cases.md) - Application use cases")
    lines.append("- [Services](application/services.md) - Application services")
    lines.append("")
    lines.append("### Infrastructure Layer")
    lines.append("- [Resources](infrastructure/resources.md) - Resource managers")
    lines.append("- [Persistence](infrastructure/persistence.md) - Data persistence")
    lines.append("- [Security](infrastructure/security.md) - Security components")
    lines.append("- [Orchestrator API](infrastructure/orchestrator-api.md) - REST API")
    lines.append("")
    lines.append("### Presentation Layer")
    lines.append("- [Controllers](presentation/controllers.md) - UI controllers")
    lines.append("- [Panels](presentation/panels.md) - UI panels")

    return "\n".join(lines)


def main():
    """Main entry point."""
    print("Scanning source files...")

    layers: dict[str, list[ModuleInfo]] = defaultdict(list)

    # Define layer paths
    layer_paths = {
        "domain": SRC_DIR / "domain",
        "application": SRC_DIR / "application",
        "infrastructure": SRC_DIR / "infrastructure",
        "presentation": SRC_DIR / "presentation",
    }

    for layer_name, layer_path in layer_paths.items():
        if not layer_path.exists():
            print(f"Warning: {layer_path} does not exist")
            continue

        python_files = list(layer_path.rglob("*.py"))
        print(f"Found {len(python_files)} files in {layer_name}/")

        for file_path in python_files:
            if file_path.name.startswith("__"):
                continue

            module = analyze_file(file_path, SRC_DIR.parent)
            if module:
                layers[layer_name].append(module)

    # Summary
    for layer, mods in layers.items():
        total_classes = sum(len(m.classes) for m in mods)
        print(f"  {layer}: {len(mods)} modules, {total_classes} classes")

    # Create output directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate main index
    print("\nGenerating main index...")
    (DOCS_DIR / "index.md").write_text(generate_main_index(layers), encoding="utf-8")

    # Generate layer pages
    for layer_name, modules in layers.items():
        print(f"Generating {layer_name}/ ...")
        layer_dir = DOCS_DIR / layer_name
        layer_dir.mkdir(parents=True, exist_ok=True)

        # Layer index with all content
        (layer_dir / "index.md").write_text(
            generate_layer_index(layer_name, modules), encoding="utf-8"
        )

    print(f"\nDone! Generated documentation in {DOCS_DIR}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate Function Inventory for CasareRPA.

Extracts ALL functions, methods, and classes from the codebase,
builds a call graph, and identifies potentially unused code.

Output: Markdown files in docs/inventory/
"""

import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SRC_DIR = PROJECT_ROOT / "src" / "casare_rpa"
DOCS_DIR = PROJECT_ROOT / "docs" / "inventory"


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    module: str
    file_path: str
    line_number: int
    is_method: bool
    is_async: bool
    is_private: bool
    is_dunder: bool
    class_name: str | None
    parameters: list[str]
    return_type: str | None
    docstring: str | None
    decorators: list[str]
    calls: set[str] = field(default_factory=set)
    called_by: set[str] = field(default_factory=set)

    @property
    def full_name(self) -> str:
        if self.class_name:
            return f"{self.module}.{self.class_name}.{self.name}"
        return f"{self.module}.{self.name}"

    @property
    def status(self) -> str:
        if self.is_dunder:
            return "DUNDER"
        if self.is_private:
            return "INTERNAL"
        if not self.called_by:
            return "UNUSED"
        return "USED"


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
    methods: list[str] = field(default_factory=list)


class CodeAnalyzer(ast.NodeVisitor):
    """AST visitor to extract functions, methods, and calls."""

    def __init__(self, module_name: str, file_path: str):
        self.module = module_name
        self.file_path = file_path
        self.functions: list[FunctionInfo] = []
        self.classes: list[ClassInfo] = []
        self.current_class: str | None = None
        self.current_function: FunctionInfo | None = None
        self.imports: dict[str, str] = {}  # alias -> full module

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = f"{module}.{alias.name}"
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(ast.unparse(base))

        decorators = [ast.unparse(d) for d in node.decorator_list]
        docstring = ast.get_docstring(node)

        class_info = ClassInfo(
            name=node.name,
            module=self.module,
            file_path=self.file_path,
            line_number=node.lineno,
            bases=bases,
            docstring=docstring,
            decorators=decorators,
        )
        self.classes.append(class_info)

        # Visit methods
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node, is_async=True)

    def _process_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool
    ) -> None:
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_str = arg.arg
            if arg.annotation:
                param_str += f": {ast.unparse(arg.annotation)}"
            params.append(param_str)

        # Extract return type
        return_type = None
        if node.returns:
            return_type = ast.unparse(node.returns)

        # Extract decorators
        decorators = [ast.unparse(d) for d in node.decorator_list]

        # Get docstring
        docstring = ast.get_docstring(node)

        func_info = FunctionInfo(
            name=node.name,
            module=self.module,
            file_path=self.file_path,
            line_number=node.lineno,
            is_method=self.current_class is not None,
            is_async=is_async,
            is_private=node.name.startswith("_") and not node.name.startswith("__"),
            is_dunder=node.name.startswith("__") and node.name.endswith("__"),
            class_name=self.current_class,
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            decorators=decorators,
        )

        # Visit function body to find calls
        old_function = self.current_function
        self.current_function = func_info
        self.generic_visit(node)
        self.current_function = old_function

        self.functions.append(func_info)

        # Add to class methods list
        if self.current_class:
            for cls in self.classes:
                if cls.name == self.current_class and cls.module == self.module:
                    cls.methods.append(node.name)
                    break

    def visit_Call(self, node: ast.Call) -> None:
        if self.current_function:
            call_name = self._get_call_name(node)
            if call_name:
                self.current_function.calls.add(call_name)
        self.generic_visit(node)

    def _get_call_name(self, node: ast.Call) -> str | None:
        func = node.func
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        return None


def analyze_file(file_path: Path, base_path: Path) -> tuple[list[FunctionInfo], list[ClassInfo]]:
    """Analyze a single Python file."""
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}")
        return [], []

    # Calculate module name
    rel_path = file_path.relative_to(base_path)
    parts = list(rel_path.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    module_name = ".".join(parts)

    analyzer = CodeAnalyzer(module_name, str(file_path.relative_to(PROJECT_ROOT)))
    analyzer.visit(tree)

    return analyzer.functions, analyzer.classes


def build_call_graph(functions: list[FunctionInfo]) -> None:
    """Build call relationships between functions."""
    # Create lookup by name
    by_name: dict[str, list[FunctionInfo]] = defaultdict(list)
    for func in functions:
        by_name[func.name].append(func)

    # Match calls to functions
    for func in functions:
        for call_name in func.calls:
            if call_name in by_name:
                for target in by_name[call_name]:
                    target.called_by.add(func.full_name)


def categorize_functions(
    functions: list[FunctionInfo],
) -> dict[str, list[FunctionInfo]]:
    """Categorize functions by layer."""
    categories = {
        "domain": [],
        "application": [],
        "infrastructure": [],
        "presentation": [],
        "nodes": [],
        "other": [],
    }

    for func in functions:
        module = func.module
        if module.startswith("casare_rpa.domain"):
            categories["domain"].append(func)
        elif module.startswith("casare_rpa.application"):
            categories["application"].append(func)
        elif module.startswith("casare_rpa.infrastructure"):
            categories["infrastructure"].append(func)
        elif module.startswith("casare_rpa.presentation"):
            categories["presentation"].append(func)
        elif module.startswith("casare_rpa.nodes"):
            categories["nodes"].append(func)
        else:
            categories["other"].append(func)

    return categories


def generate_markdown_table(functions: list[FunctionInfo], include_calls: bool = False) -> str:
    """Generate markdown table for functions."""
    if not functions:
        return "*No functions found*\n"

    lines = []
    lines.append("| Function | Class | Parameters | Returns | Status |")
    lines.append("|----------|-------|------------|---------|--------|")

    for func in sorted(functions, key=lambda f: (f.class_name or "", f.name)):
        params = ", ".join(func.parameters[:3])
        if len(func.parameters) > 3:
            params += ", ..."

        class_name = func.class_name or "-"
        return_type = func.return_type or "-"
        status = func.status

        # Add async indicator
        name = func.name
        if func.is_async:
            name = f"async {name}"

        lines.append(f"| `{name}` | {class_name} | `{params}` | `{return_type}` | {status} |")

    return "\n".join(lines) + "\n"


def generate_module_docs(functions: list[FunctionInfo], module_prefix: str) -> str:
    """Generate documentation grouped by module."""
    by_module: dict[str, list[FunctionInfo]] = defaultdict(list)
    for func in functions:
        by_module[func.module].append(func)

    lines = []
    for module in sorted(by_module.keys()):
        module_funcs = by_module[module]
        lines.append(f"## {module}\n")
        lines.append(f"**File:** `{module_funcs[0].file_path}`\n")
        lines.append(generate_markdown_table(module_funcs))
        lines.append("")

    return "\n".join(lines)


def generate_unused_report(functions: list[FunctionInfo]) -> str:
    """Generate report of potentially unused functions."""
    unused = [f for f in functions if f.status == "UNUSED" and not f.is_dunder]

    lines = []
    lines.append("# Potentially Unused Functions\n")
    lines.append('!!! warning "Review Required"\n')
    lines.append("    These functions appear to have no callers in the codebase.\n")
    lines.append("    They may be: entry points, event handlers, or truly unused.\n")
    lines.append("")
    lines.append(f"**Total:** {len(unused)} potentially unused functions\n")
    lines.append("")

    # Group by module
    by_module: dict[str, list[FunctionInfo]] = defaultdict(list)
    for func in unused:
        by_module[func.module].append(func)

    for module in sorted(by_module.keys()):
        module_funcs = by_module[module]
        lines.append(f"## {module}\n")
        lines.append(f"**{len(module_funcs)} unused functions**\n")
        lines.append("")
        for func in sorted(module_funcs, key=lambda f: f.line_number):
            class_prefix = f"{func.class_name}." if func.class_name else ""
            lines.append(f"- `{class_prefix}{func.name}` (line {func.line_number})")
        lines.append("")

    return "\n".join(lines)


def generate_cross_references(functions: list[FunctionInfo]) -> str:
    """Generate cross-reference documentation."""
    lines = []
    lines.append("# Cross References\n")
    lines.append("This page shows which functions call which other functions.\n")
    lines.append("")

    # Find functions with most callers (most important)
    with_callers = [(f, len(f.called_by)) for f in functions if f.called_by]
    with_callers.sort(key=lambda x: -x[1])

    lines.append("## Most Called Functions\n")
    lines.append("| Function | Called By (count) |")
    lines.append("|----------|-------------------|")

    for func, count in with_callers[:50]:
        class_prefix = f"{func.class_name}." if func.class_name else ""
        lines.append(f"| `{func.module}.{class_prefix}{func.name}` | {count} |")

    lines.append("")

    # Functions with most outgoing calls (most complex)
    with_calls = [(f, len(f.calls)) for f in functions if f.calls]
    with_calls.sort(key=lambda x: -x[1])

    lines.append("## Most Complex Functions (by call count)\n")
    lines.append("| Function | Calls (count) |")
    lines.append("|----------|---------------|")

    for func, count in with_calls[:50]:
        class_prefix = f"{func.class_name}." if func.class_name else ""
        lines.append(f"| `{func.module}.{class_prefix}{func.name}` | {count} |")

    return "\n".join(lines)


def generate_index(functions: list[FunctionInfo], classes: list[ClassInfo]) -> str:
    """Generate index page with statistics."""
    categories = categorize_functions(functions)

    used = sum(1 for f in functions if f.status == "USED")
    unused = sum(1 for f in functions if f.status == "UNUSED")
    internal = sum(1 for f in functions if f.status == "INTERNAL")
    dunder = sum(1 for f in functions if f.status == "DUNDER")

    async_count = sum(1 for f in functions if f.is_async)
    method_count = sum(1 for f in functions if f.is_method)

    lines = []
    lines.append("# Function Inventory\n")
    lines.append("Complete inventory of all Python functions in CasareRPA.\n")
    lines.append("")
    lines.append("## Summary Statistics\n")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|--------|-------|")
    lines.append(f"| **Total Functions** | {len(functions)} |")
    lines.append(f"| **Total Classes** | {len(classes)} |")
    lines.append(f"| Methods | {method_count} |")
    lines.append(f"| Async Functions | {async_count} |")
    lines.append("")
    lines.append("### By Status\n")
    lines.append("")
    lines.append("| Status | Count | Description |")
    lines.append("|--------|-------|-------------|")
    lines.append(f"| USED | {used} | Called by other functions |")
    lines.append(f"| UNUSED | {unused} | No callers found (review needed) |")
    lines.append(f"| INTERNAL | {internal} | Private functions (_prefix) |")
    lines.append(f"| DUNDER | {dunder} | Magic methods (__name__) |")
    lines.append("")
    lines.append("### By Layer\n")
    lines.append("")
    lines.append("| Layer | Functions | Classes |")
    lines.append("|-------|-----------|---------|")

    for layer, funcs in categories.items():
        layer_classes = sum(1 for c in classes if c.module.startswith(f"casare_rpa.{layer}"))
        lines.append(f"| {layer.title()} | {len(funcs)} | {layer_classes} |")

    lines.append("")
    lines.append("## Navigation\n")
    lines.append("")
    lines.append("- [Domain Functions](domain-functions.md) - Pure business logic")
    lines.append("- [Application Functions](application-functions.md) - Use cases & orchestration")
    lines.append(
        "- [Infrastructure Functions](infrastructure-functions.md) - External integrations"
    )
    lines.append("- [Presentation Functions](presentation-functions.md) - UI & canvas")
    lines.append("- [Node Functions](nodes-functions.md) - Automation nodes")
    lines.append("- [Unused Functions](unused-functions.md) - Potential dead code")
    lines.append("- [Cross References](cross-references.md) - Call graph analysis")

    return "\n".join(lines)


def main():
    """Main entry point."""
    print("Scanning codebase...")

    all_functions: list[FunctionInfo] = []
    all_classes: list[ClassInfo] = []

    # Find all Python files
    python_files = list(SRC_DIR.rglob("*.py"))
    print(f"Found {len(python_files)} Python files")

    for file_path in python_files:
        functions, classes = analyze_file(file_path, SRC_DIR.parent)
        all_functions.extend(functions)
        all_classes.extend(classes)

    print(f"Found {len(all_functions)} functions and {len(all_classes)} classes")

    # Build call graph
    print("Building call graph...")
    build_call_graph(all_functions)

    # Categorize
    categories = categorize_functions(all_functions)

    # Create output directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate index
    print("Generating index...")
    (DOCS_DIR / "index.md").write_text(generate_index(all_functions, all_classes), encoding="utf-8")

    # Generate category pages
    category_map = {
        "domain": ("domain-functions.md", "Domain Layer Functions"),
        "application": ("application-functions.md", "Application Layer Functions"),
        "infrastructure": (
            "infrastructure-functions.md",
            "Infrastructure Layer Functions",
        ),
        "presentation": ("presentation-functions.md", "Presentation Layer Functions"),
        "nodes": ("nodes-functions.md", "Node Functions"),
    }

    for category, (filename, title) in category_map.items():
        print(f"Generating {filename}...")
        funcs = categories.get(category, [])
        content = f"# {title}\n\n"
        content += f"**Total:** {len(funcs)} functions\n\n"
        content += generate_module_docs(funcs, f"casare_rpa.{category}")
        (DOCS_DIR / filename).write_text(content, encoding="utf-8")

    # Generate unused functions report
    print("Generating unused functions report...")
    (DOCS_DIR / "unused-functions.md").write_text(
        generate_unused_report(all_functions), encoding="utf-8"
    )

    # Generate cross-references
    print("Generating cross-references...")
    (DOCS_DIR / "cross-references.md").write_text(
        generate_cross_references(all_functions), encoding="utf-8"
    )

    print(f"\nDone! Generated documentation in {DOCS_DIR}")

    # Print summary
    unused_count = sum(1 for f in all_functions if f.status == "UNUSED")
    print("\nSummary:")
    print(f"  Total functions: {len(all_functions)}")
    print(f"  Total classes: {len(all_classes)}")
    print(f"  Potentially unused: {unused_count}")


if __name__ == "__main__":
    main()

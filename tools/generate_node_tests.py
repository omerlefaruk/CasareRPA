#!/usr/bin/env python
"""
CasareRPA - Node Test Generator CLI.

Auto-generates pytest test templates for node classes.
Inspects node schemas to create appropriate test scaffolding.

Usage:
    python tools/generate_node_tests.py ClickElementNode
    python tools/generate_node_tests.py ClickElementNode --output tests/nodes/browser/
    python tools/generate_node_tests.py --list  # List all available nodes
    python tools/generate_node_tests.py --category browser  # Generate for category

Example output:
    Generated: tests/nodes/browser/test_click_element_node.py
"""

import importlib
import inspect
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Generate pytest test templates for CasareRPA nodes.")
console = Console()


def get_node_registry() -> Dict[str, Type]:
    """
    Get all node classes from casare_rpa.nodes.

    Returns:
        Dictionary mapping node type names to classes.
    """
    try:
        from casare_rpa.nodes import get_all_node_classes

        return get_all_node_classes()
    except ImportError as e:
        console.print(f"[red]Failed to import node registry: {e}[/red]")
        sys.exit(1)


def get_node_class(node_name: str) -> Optional[Type]:
    """
    Get a node class by name.

    Args:
        node_name: Node class name (e.g., 'ClickElementNode')

    Returns:
        Node class or None if not found
    """
    registry = get_node_registry()
    return registry.get(node_name)


def get_node_schema(node_class: Type) -> Dict[str, Any]:
    """
    Extract schema information from a node class.

    Looks for @properties decorator metadata and inspects port definitions.

    Args:
        node_class: Node class to inspect

    Returns:
        Dictionary with schema information
    """
    schema = {
        "name": node_class.__name__,
        "docstring": inspect.getdoc(node_class) or "",
        "input_ports": [],
        "output_ports": [],
        "config_properties": [],
        "is_async": True,  # Assume async by default
    }

    # Check for _input_ports and _output_ports class attributes
    if hasattr(node_class, "_input_ports"):
        schema["input_ports"] = list(node_class._input_ports.keys())
    if hasattr(node_class, "_output_ports"):
        schema["output_ports"] = list(node_class._output_ports.keys())

    node_schema = getattr(node_class, "__node_schema__", None)
    if node_schema is not None and getattr(node_schema, "properties", None):
        schema["config_properties"] = [p.name for p in node_schema.properties]

    # Try to instantiate to get port info
    try:
        # Create with dummy node_id
        instance = node_class(node_id="test_node", config={})
        if hasattr(instance, "input_ports"):
            schema["input_ports"] = list(instance.input_ports.keys())
        if hasattr(instance, "output_ports"):
            schema["output_ports"] = list(instance.output_ports.keys())
        if hasattr(instance, "config"):
            schema["config_properties"] = list(instance.config.keys())
    except Exception:
        pass  # Use default schema

    # Check if execute method is async
    if hasattr(node_class, "execute"):
        schema["is_async"] = inspect.iscoroutinefunction(node_class.execute)

    return schema


def generate_test_template(node_class: Type, schema: Dict[str, Any]) -> str:
    """
    Generate a pytest test template for a node.

    Args:
        node_class: Node class
        schema: Node schema information

    Returns:
        Python source code for test file
    """
    class_name = schema["name"]
    snake_name = camel_to_snake(class_name)
    test_class_name = f"Test{class_name}"

    # Determine category from module path
    module = node_class.__module__
    category = "nodes"
    if "browser" in module:
        category = "browser"
    elif "desktop" in module:
        category = "desktop"
    elif "data" in module:
        category = "data"
    elif "file" in module:
        category = "file"
    elif "http" in module:
        category = "http"
    elif "email" in module:
        category = "email"

    # Build import statement
    module_path = node_class.__module__
    import_stmt = f"from {module_path} import {class_name}"

    # Generate test methods
    async_marker = "@pytest.mark.asyncio\n    " if schema["is_async"] else ""
    async_def = "async def" if schema["is_async"] else "def"
    await_prefix = "await " if schema["is_async"] else ""

    # Input setup based on ports
    input_setup = ""
    for port in schema["input_ports"]:
        if port == "exec_in":
            continue
        input_setup += f"        # context.variables['{port}'] = 'test_value'\n"

    if not input_setup:
        input_setup = "        # Set up input variables as needed\n"

    template = f'''"""
Tests for {class_name}.

Auto-generated on {datetime.now().strftime('%Y-%m-%d')}.
Review and customize assertions for your specific use cases.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch

{import_stmt}
from tests.helpers import MockFactory, WorkflowAssertions


class {test_class_name}:
    """Test cases for {class_name}."""

    @pytest.fixture
    def node(self) -> {class_name}:
        """Create node instance for testing."""
        return {class_name}(node_id="test_{snake_name}")

    @pytest.fixture
    def context(self, execution_context):
        """Execution context fixture."""
        return execution_context

    # =========================================================================
    # SUCCESS TESTS
    # =========================================================================

    {async_marker}{async_def} test_execute_success(self, node, context):
        """Test successful execution of {class_name}."""
        # Arrange: Set up inputs
{input_setup}
        # Act
        result = {await_prefix}node.execute(context)

        # Assert
        assert result is not None
        assert result.get("success") is True

    # =========================================================================
    # ERROR TESTS
    # =========================================================================

    {async_marker}{async_def} test_execute_missing_required_input(self, node, context):
        """Test error handling when required input is missing."""
        # Arrange: Don't set required inputs

        # Act
        result = {await_prefix}node.execute(context)

        # Assert: Should fail gracefully
        assert result.get("success") is False or "error" in result

    # =========================================================================
    # EDGE CASE TESTS
    # =========================================================================

    {async_marker}{async_def} test_execute_with_empty_input(self, node, context):
        """Test handling of empty input values."""
        # Arrange: Set empty values
{input_setup.replace("'test_value'", "''")}
        # Act
        result = {await_prefix}node.execute(context)

        # Assert: Should handle gracefully
        assert result is not None

    {async_marker}{async_def} test_execute_with_none_input(self, node, context):
        """Test handling of None input values."""
        # Arrange: Set None values
{input_setup.replace("'test_value'", "None")}
        # Act
        result = {await_prefix}node.execute(context)

        # Assert: Should handle gracefully
        assert result is not None
'''

    # Add category-specific tests
    if category == "browser":
        template += f'''
    # =========================================================================
    # BROWSER-SPECIFIC TESTS
    # =========================================================================

    {async_marker}{async_def} test_execute_with_mock_page(self, node, context):
        """Test with mock Playwright page."""
        # Arrange
        mock_page = MockFactory.mock_page()
        context.set_active_page(mock_page, "default")

        # Set up any selector expectations
        mock_element = MockFactory.mock_element()
        mock_page.query_selector.return_value = mock_element

        # Act
        result = {await_prefix}node.execute(context)

        # Assert
        assert result is not None
        # Verify page interactions
        # mock_page.query_selector.assert_awaited_once()
'''

    elif category == "desktop":
        template += f'''
    # =========================================================================
    # DESKTOP-SPECIFIC TESTS
    # =========================================================================

    {async_marker}{async_def} test_execute_with_mock_ui_element(self, node, context):
        """Test with mock UI automation element."""
        # Arrange
        mock_element = MockFactory.mock_ui_control()
        # context.desktop_context = mock_element

        # Act
        result = {await_prefix}node.execute(context)

        # Assert
        assert result is not None
'''

    elif category == "http":
        template += f'''
    # =========================================================================
    # HTTP-SPECIFIC TESTS
    # =========================================================================

    {async_marker}{async_def} test_execute_with_mock_http_client(self, node, context):
        """Test with mock HTTP client."""
        # Arrange
        mock_response = MockFactory.mock_http_response(
            status=200,
            json={{"success": True}}
        )
        mock_client = MockFactory.mock_http_client(mock_response)
        context.resources["http_client"] = mock_client

        # Act
        result = {await_prefix}node.execute(context)

        # Assert
        assert result is not None
'''

    return template


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def get_output_path(node_class: Type, output_dir: Optional[str] = None) -> Path:
    """
    Determine output path for test file.

    Args:
        node_class: Node class
        output_dir: Optional custom output directory

    Returns:
        Path for the test file
    """
    module = node_class.__module__
    snake_name = camel_to_snake(node_class.__name__)

    if output_dir:
        return Path(output_dir) / f"test_{snake_name}.py"

    # Determine category from module path
    if "browser" in module:
        category = "browser"
    elif "desktop" in module:
        category = "desktop"
    elif "data" in module:
        category = "data"
    elif "file" in module:
        category = "file"
    elif "http" in module:
        category = "http"
    elif "email" in module:
        category = "email"
    elif "database" in module:
        category = "database"
    elif "messaging" in module:
        category = "messaging"
    else:
        category = "nodes"

    return Path(f"tests/nodes/{category}/test_{snake_name}.py")


@app.command("generate")
def generate(
    node_name: str = typer.Argument(
        ..., help="Node class name (e.g., ClickElementNode)"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Custom output directory"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Overwrite existing test file"
    ),
):
    """Generate a test template for a specific node."""
    node_class = get_node_class(node_name)

    if not node_class:
        console.print(f"[red]Node '{node_name}' not found in registry.[/red]")
        console.print("Use --list to see available nodes.")
        raise typer.Exit(1)

    schema = get_node_schema(node_class)
    template = generate_test_template(node_class, schema)

    output_path = get_output_path(node_class, output)

    # Check if file exists
    if output_path.exists() and not force:
        console.print(f"[yellow]Test file already exists: {output_path}[/yellow]")
        console.print("Use --force to overwrite.")
        raise typer.Exit(1)

    # Create directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    output_path.write_text(template)
    console.print(f"[green]Generated:[/green] {output_path}")


@app.command("list")
def list_nodes(
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Filter by category"
    ),
):
    """List all available nodes in the registry."""
    # For listing we prefer registry data (no imports), but fall back to class loading.
    try:
        from casare_rpa.nodes.registry_data import NODE_REGISTRY

        registry_data = NODE_REGISTRY
    except Exception:
        registry_data = {}
    registry = get_node_registry()

    table = Table(title="CasareRPA Node Registry")
    table.add_column("Node", style="cyan")
    table.add_column("Module", style="dim")
    table.add_column("Category", style="green")

    for name in sorted(set(registry.keys()) | set(registry_data.keys())):
        node_class = registry.get(name)
        module = (
            node_class.__module__ if node_class else str(registry_data.get(name, ""))
        )

        # Determine category
        if "browser" in module:
            cat = "browser"
        elif "desktop" in module:
            cat = "desktop"
        elif "data" in module:
            cat = "data"
        elif "file" in module:
            cat = "file"
        elif "http" in module:
            cat = "http"
        elif "control_flow" in module:
            cat = "control_flow"
        elif "basic" in module:
            cat = "basic"
        else:
            cat = "other"

        # Filter by category if specified
        if category and cat != category:
            continue

        table.add_row(name, module, cat)

    console.print(table)
    console.print(
        f"\n[dim]Total: {len(set(registry.keys()) | set(registry_data.keys()))} nodes[/dim]"
    )


@app.command("category")
def generate_category(
    category: str = typer.Argument(..., help="Category name (e.g., browser)"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Custom output directory"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing files"),
):
    """Generate test templates for all nodes in a category."""
    registry = get_node_registry()
    generated = 0
    skipped = 0

    for name, node_class in registry.items():
        module = node_class.__module__

        # Check category match
        if category not in module:
            continue

        schema = get_node_schema(node_class)
        template = generate_test_template(node_class, schema)
        output_path = get_output_path(node_class, output)

        if output_path.exists() and not force:
            console.print(f"[dim]Skipped (exists): {name}[/dim]")
            skipped += 1
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(template)
        console.print(f"[green]Generated:[/green] {output_path}")
        generated += 1

    console.print(f"\n[green]Generated: {generated}[/green]")
    if skipped:
        console.print(f"[yellow]Skipped: {skipped} (use --force to overwrite)[/yellow]")


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

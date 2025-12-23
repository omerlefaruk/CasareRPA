---
skill: node-template-generator
description: Generate boilerplate code for new CasareRPA automation nodes following the established patterns and clean architecture principles.
---

When the user requests a new automation node, generate the complete boilerplate code following these exact patterns:

## Node Implementation Template

```python
# File: src/casare_rpa/nodes/{category}/{node_name}_node.py

from casare_rpa.domain.value_objects import ExecutionResult, DataType, Port
from casare_rpa.nodes.base_node import BaseNode
from loguru import logger
from typing import Any


class {NodeName}Node(BaseNode):
    """
    {Brief description of what this node does}.

    Inputs:
        {input_name} ({DataType}): {Description}

    Outputs:
        {output_name} ({DataType}): {Description}

    Example:
        {Concrete usage example}
    """

    def __init__(self):
        super().__init__(
            id="{node_id}",
            name="{Node Display Name}",
            category="{category}",
        )
        # Define input ports
        self.add_input("{input_name}", DataType.{TYPE})

        # Define output ports
        self.add_output("{output_name}", DataType.{TYPE})

    async def execute(self, context: Any) -> ExecutionResult:
        """
        Execute the {node_name} operation.

        Args:
            context: Execution context containing workflow variables

        Returns:
            ExecutionResult with success status and output data
        """
        try:
            # Get input values from context
            input_value = context.get_variable(self.inputs["{input_name}"].id)

            logger.info(f"Executing {NodeName}Node with input: {input_value}")

            result_data = self._perform_operation(input_value)

            logger.info(f"{NodeName}Node completed successfully")

            return ExecutionResult(
                success=True,
                output={"{output_name}": result_data}
            )

        except Exception as e:
            logger.error(f"{NodeName}Node failed: {str(e)}")
            return ExecutionResult(
                success=False,
                error=str(e)
            )

    def _perform_operation(self, input_value: Any) -> Any:
        """
        Internal method to perform the actual operation.

        Args:
            input_value: The input data to process

        Returns:
            The processed result
        """
        # Default implementation: return input value (override as needed).
        return input_value
```

## Visual Node Wrapper Template

```python
# File: src/casare_rpa/presentation/canvas/visual_nodes/{category}_nodes.py

from NodeGraphQt import BaseNode as GraphNode
from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node


class Visual{NodeName}Node(GraphNode):
    """Visual wrapper for {NodeName}Node."""

    __identifier__ = 'casare_rpa'
    NODE_NAME = '{Node Display Name}'

    def __init__(self):
        super().__init__()
        self.logic_node = {NodeName}Node()

        # Create visual ports matching logic node
        self.add_input('{input_name}')
        self.add_output('{output_name}')

        # Set node appearance
        self.set_color(85, 107, 47)  # Adjust color per category
        self.set_icon('path/to/icon.png')  # Optional
```

## Test Template

```python
# File: tests/nodes/{category}/test_{node_name}_node.py

import pytest
from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node
from casare_rpa.domain.value_objects import DataType
from unittest.mock import MagicMock


@pytest.fixture
def node():
    """Create a {NodeName}Node instance for testing."""
    return {NodeName}Node()


@pytest.fixture
def mock_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.get_variable = MagicMock(return_value="test_value")
    return context


class Test{NodeName}Node:
    """Test suite for {NodeName}Node."""

    def test_initialization(self, node):
        """Test that node initializes with correct properties."""
        assert node.id == "{node_id}"
        assert node.name == "{Node Display Name}"
        assert node.category == "{category}"

    def test_has_required_ports(self, node):
        """Test that node has all required input and output ports."""
        # Check inputs
        assert "{input_name}" in node.inputs
        assert node.inputs["{input_name}"].data_type == DataType.{TYPE}

        # Check outputs
        assert "{output_name}" in node.outputs
        assert node.outputs["{output_name}"].data_type == DataType.{TYPE}

    @pytest.mark.asyncio
    async def test_execute_success(self, node, mock_context):
        """Test successful execution."""
        result = await node.execute(mock_context)

        assert result.success is True
        assert "{output_name}" in result.output
        mock_context.get_variable.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_failure(self, node, mock_context):
        """Test execution with error."""
        mock_context.get_variable.side_effect = ValueError("Test error")

        result = await node.execute(mock_context)

        assert result.success is False
        assert result.error is not None
        assert "Test error" in result.error

    @pytest.mark.asyncio
    async def test_perform_operation(self, node):
        """Test the internal operation logic."""
        input_value = "test_input"
        result = node._perform_operation(input_value)

        # Assert expected behavior
        assert result is not None
```

## Category-Specific Guidelines

### Browser Nodes (`nodes/browser/`)
- Use BrowserResourceManager for browser access
- Always use `await page.wait_for_*()` for element interactions
- Handle navigation with `await page.goto()`
- Color: RGB(65, 105, 225) - Royal Blue

### Desktop Nodes (`nodes/desktop/`)
- Use `uiautomation` library for Windows automation
- Handle window/element not found errors
- Color: RGB(139, 69, 19) - Saddle Brown

### Data Operations (`nodes/data_operations/`)
- Support multiple data types (STRING, NUMBER, LIST, DICT)
- Validate input types
- Color: RGB(70, 130, 180) - Steel Blue

### Control Flow (`nodes/control_flow/`)
- Must handle conditional execution
- Return ExecutionResult with control flow signals if needed
- Color: RGB(255, 140, 0) - Dark Orange

### File System (`nodes/file_system/`)
- Use async file I/O where possible
- Handle file not found, permission errors
- Support both absolute and relative paths
- Color: RGB(46, 139, 87) - Sea Green

## Usage

When user requests: "Create a new node that {does X}"

1. Ask clarifying questions:
   - What category does this belong to? (browser, desktop, data, etc.)
   - What inputs does it need?
   - What outputs does it produce?
   - What's the primary operation?

2. Generate the three files:
   - Logic node implementation
   - Visual node wrapper
   - Test file

3. Provide usage example showing how to use the node in a workflow

4. Suggest next steps:
   - Add node to visual node registry
   - Update documentation
   - Add integration tests

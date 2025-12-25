---
name: test-generator
description: Generate comprehensive pytest test suites for CasareRPA components, including nodes, controllers, use cases, and domain entities, following the project's testing patterns.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: testing
---

When generating tests, follow these established patterns for each component type:

## Test File Structure

```python
# Standard imports
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Any

# Component under test
from casare_rpa.{module}.{component} import {Component}

# Domain objects
from casare_rpa.domain.value_objects import ExecutionResult, DataType, Port

# Fixtures
@pytest.fixture
def component():
    """Create component instance for testing."""
    return {Component}()

@pytest.fixture
def mock_context():
    """Create mock execution context."""
    context = MagicMock()
    context.get_variable = MagicMock(return_value="test_value")
    context.set_variable = MagicMock()
    return context

# Test class
class Test{Component}:
    """Test suite for {Component}."""

    # Tests go here
```

## Node Tests Template

```python
# File: tests/nodes/{category}/test_{node_name}_node.py

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from casare_rpa.nodes.{category}.{node_name}_node import {NodeName}Node
from casare_rpa.domain.value_objects import ExecutionResult, DataType


@pytest.fixture
def node():
    """Create {NodeName}Node instance."""
    return {NodeName}Node()


@pytest.fixture
def mock_context():
    """Create mock execution context with test data."""
    context = MagicMock()
    context.get_variable = MagicMock(side_effect=lambda x: {
        'input_port_1': 'test_value_1',
        'input_port_2': 'test_value_2',
    }.get(x))
    context.set_variable = MagicMock()
    return context


class Test{NodeName}Node:
    """Comprehensive test suite for {NodeName}Node."""

    # 1. Initialization Tests

    def test_initialization(self, node):
        """Test node initializes with correct properties."""
        assert node.id == "{node_id}"
        assert node.name == "{Node Display Name}"
        assert node.category == "{category}"

    def test_has_correct_input_ports(self, node):
        """Test node has all required input ports with correct types."""
        assert "input_port_1" in node.inputs
        assert node.inputs["input_port_1"].data_type == DataType.STRING

    def test_has_correct_output_ports(self, node):
        """Test node has all required output ports with correct types."""
        assert "output_port_1" in node.outputs
        assert node.outputs["output_port_1"].data_type == DataType.STRING

    # 2. Execution Tests - Success Cases

    @pytest.mark.asyncio
    async def test_execute_success(self, node, mock_context):
        """Test successful execution returns ExecutionResult."""
        result = await node.execute(mock_context)

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        assert result.error is None
        assert "output_port_1" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_valid_input(self, node, mock_context):
        """Test execution with valid input produces expected output."""
        result = await node.execute(mock_context)

        # Verify context was queried for input
        mock_context.get_variable.assert_called()

        # Verify output is correct
        assert result.success is True
        # Add specific output assertions based on node logic

    # 3. Execution Tests - Error Cases

    @pytest.mark.asyncio
    async def test_execute_with_missing_input(self, node, mock_context):
        """Test execution fails gracefully when input is missing."""
        mock_context.get_variable.return_value = None

        result = await node.execute(mock_context)

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_with_invalid_input_type(self, node, mock_context):
        """Test execution fails with appropriate error for invalid input type."""
        mock_context.get_variable.return_value = 12345  # Wrong type

        result = await node.execute(mock_context)

        assert result.success is False
        assert "type" in result.error.lower() or "invalid" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, node, mock_context):
        """Test execution catches and handles exceptions properly."""
        mock_context.get_variable.side_effect = RuntimeError("Test error")

        result = await node.execute(mock_context)

        assert result.success is False
        assert "Test error" in result.error

    # 4. Edge Cases

    @pytest.mark.asyncio
    async def test_execute_with_empty_string(self, node, mock_context):
        """Test execution handles empty string input."""
        mock_context.get_variable.return_value = ""

        result = await node.execute(mock_context)

        # Behavior depends on node - might succeed or fail
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execute_with_special_characters(self, node, mock_context):
        """Test execution handles special characters in input."""
        mock_context.get_variable.return_value = "test\n\t\\\"special"

        result = await node.execute(mock_context)

        assert isinstance(result, ExecutionResult)

    # 5. Integration with External Resources (if applicable)

    @pytest.mark.asyncio
    @patch('casare_rpa.infrastructure.resources.browser_manager.BrowserResourceManager')
    async def test_execute_with_browser_resource(self, mock_browser_manager, node, mock_context):
        """Test node correctly uses browser resource manager."""
        # Setup mock browser
        mock_page = AsyncMock()
        mock_browser_manager.get_page.return_value = mock_page

        result = await node.execute(mock_context)

        # Verify browser was acquired and used
        mock_browser_manager.get_page.assert_called_once()
        assert result.success is True

    # 6. Logging Tests

    @pytest.mark.asyncio
    async def test_execute_logs_info_on_success(self, node, mock_context, caplog):
        """Test successful execution logs info message."""
        result = await node.execute(mock_context)

        assert result.success is True
        # Verify info log was created
        assert any("completed" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_execute_logs_error_on_failure(self, node, mock_context, caplog):
        """Test failed execution logs error message."""
        mock_context.get_variable.side_effect = ValueError("Test error")

        result = await node.execute(mock_context)

        assert result.success is False
        # Verify error log was created
        assert any(record.levelname == "ERROR" for record in caplog.records)
```

## Controller Tests Template

```python
# File: tests/presentation/canvas/controllers/test_{controller_name}.py

import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import Qt
from casare_rpa.presentation.canvas.controllers.{controller_name} import {ControllerName}


@pytest.fixture
def mock_graph():
    """Create mock node graph."""
    graph = MagicMock()
    graph.add_node = MagicMock()
    graph.remove_node = MagicMock()
    graph.selected_nodes = MagicMock(return_value=[])
    return graph


@pytest.fixture
def mock_event_bus():
    """Create mock event bus."""
    bus = MagicMock()
    bus.emit = MagicMock()
    bus.subscribe = MagicMock()
    return bus


@pytest.fixture
def controller(mock_graph, mock_event_bus):
    """Create controller instance."""
    return {ControllerName}(mock_graph, mock_event_bus)


class Test{ControllerName}:
    """Test suite for {ControllerName}."""

    def test_initialization(self, controller, mock_graph, mock_event_bus):
        """Test controller initializes with correct dependencies."""
        assert controller.graph == mock_graph
        assert controller.event_bus == mock_event_bus

    def test_subscribes_to_events(self, mock_event_bus):
        """Test controller subscribes to required events."""
        controller = {ControllerName}(MagicMock(), mock_event_bus)

        # Verify subscriptions
        assert mock_event_bus.subscribe.call_count > 0

    def test_handle_primary_action(self, controller, mock_graph):
        """Test primary action handler."""
        # Trigger action
        controller.handle_action("test_data")

        # Verify graph interaction
        mock_graph.some_method.assert_called_once()

    def test_emits_event_on_action(self, controller, mock_event_bus):
        """Test controller emits events on actions."""
        controller.handle_action("test_data")

        # Verify event emission
        mock_event_bus.emit.assert_called()
        call_args = mock_event_bus.emit.call_args[0]
        assert call_args[0] == "expected_event_name"

    def test_error_handling(self, controller, mock_graph):
        """Test controller handles errors gracefully."""
        mock_graph.some_method.side_effect = RuntimeError("Test error")

        # Should not raise, should handle internally
        controller.handle_action("test_data")

        # Verify error was logged or event emitted
```

## Use Case Tests Template

```python
# File: tests/application/use_cases/test_{use_case_name}.py

import pytest
from unittest.mock import MagicMock, AsyncMock
from casare_rpa.application.use_cases.{use_case_name} import {UseCaseName}
from casare_rpa.domain.entities import Workflow
from casare_rpa.domain.value_objects import ExecutionResult


@pytest.fixture
def mock_workflow_repository():
    """Create mock workflow repository."""
    repo = MagicMock()
    repo.get = AsyncMock(return_value=Workflow(...))
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def use_case(mock_workflow_repository):
    """Create use case instance."""
    return {UseCaseName}(workflow_repository=mock_workflow_repository)


class Test{UseCaseName}:
    """Test suite for {UseCaseName}."""

    @pytest.mark.asyncio
    async def test_execute_success(self, use_case, mock_workflow_repository):
        """Test successful use case execution."""
        result = await use_case.execute(workflow_id="test_id")

        assert isinstance(result, ExecutionResult)
        assert result.success is True
        mock_workflow_repository.get.assert_called_once_with("test_id")

    @pytest.mark.asyncio
    async def test_execute_with_invalid_workflow(self, use_case, mock_workflow_repository):
        """Test execution fails with invalid workflow."""
        mock_workflow_repository.get.return_value = None

        result = await use_case.execute(workflow_id="invalid_id")

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_coordinates_dependencies(self, use_case):
        """Test use case coordinates multiple dependencies correctly."""
        result = await use_case.execute(workflow_id="test_id")

        # Verify all dependencies were called in correct order
        assert result.success is True
```

## Domain Entity Tests Template

```python
# File: tests/domain/entities/test_{entity_name}.py

import pytest
from casare_rpa.domain.entities.{entity_name} import {EntityName}


class Test{EntityName}:
    """Test suite for {EntityName} entity."""

    def test_create_entity(self):
        """Test entity creation with valid data."""
        entity = {EntityName}(id="test_id", name="Test")

        assert entity.id == "test_id"
        assert entity.name == "Test"

    def test_entity_validation(self):
        """Test entity validates required fields."""
        with pytest.raises(ValueError):
            {EntityName}(id="", name="Test")  # Empty ID should fail

    def test_entity_immutability(self):
        """Test entity value objects are immutable (if applicable)."""
        entity = {EntityName}(id="test_id", name="Test")

        with pytest.raises(AttributeError):
            entity.id = "new_id"  # Should not allow modification

    def test_entity_equality(self):
        """Test entity equality comparison."""
        entity1 = {EntityName}(id="test_id", name="Test")
        entity2 = {EntityName}(id="test_id", name="Test")
        entity3 = {EntityName}(id="other_id", name="Test")

        assert entity1 == entity2
        assert entity1 != entity3
```

## Test Coverage Checklist

For comprehensive test coverage, ensure tests include:

- [ ] **Initialization**: Constructor, default values
- [ ] **Happy Path**: Expected usage with valid inputs
- [ ] **Error Cases**: Invalid inputs, missing data, exceptions
- [ ] **Edge Cases**: Empty values, special characters, boundary conditions
- [ ] **Integration**: External resources, dependencies
- [ ] **Logging**: Info logs on success, error logs on failure
- [ ] **Type Safety**: Correct data types for inputs/outputs
- [ ] **Async Behavior**: Proper async/await usage (for async methods)
- [ ] **Mocking**: External dependencies properly mocked
- [ ] **Events**: Event emission and subscription (for event-driven code)

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific category
pytest tests/nodes/browser/ -v

# Run with coverage
pytest tests/ --cov=casare_rpa --cov-report=html

# Run only specific test
pytest tests/nodes/browser/test_click_node.py::TestClickNode::test_execute_success -v
```

## Usage

When user requests test generation:

1. Identify component type (node, controller, use case, entity)
2. Analyze component code to understand:
   - Inputs and outputs
   - External dependencies
   - Error conditions
   - Edge cases
3. Generate test file with appropriate template
4. Include 10-15 tests minimum covering all checklist items
5. Ensure all tests use proper async patterns if testing async code
6. Provide instructions for running the tests

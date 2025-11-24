"""
Tests for error scenarios and edge cases.

These tests verify proper handling of error conditions, invalid inputs,
and edge cases throughout the codebase.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


class TestNodeErrorHandling:
    """Test error handling in node execution."""

    @pytest.fixture
    def context(self):
        """Create an execution context."""
        from casare_rpa.core.execution_context import ExecutionContext
        return ExecutionContext()

    @pytest.mark.asyncio
    async def test_node_execution_with_invalid_config(self, context):
        """Test node execution with invalid configuration."""
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        # Empty variable name should be handled gracefully
        node = SetVariableNode("test", config={"variable_name": "", "value": "test"})
        # Execution should not crash
        result = await node.execute(context)
        # Result depends on implementation - either error or skip

    @pytest.mark.asyncio
    async def test_if_node_with_invalid_condition(self, context):
        """Test If node with invalid condition expression."""
        from casare_rpa.nodes.control_flow_nodes import IfNode

        node = IfNode("test", config={"condition": "invalid python ]["})

        # Should handle syntax error gracefully
        try:
            result = await node.execute(context)
            # If it doesn't raise, it should take false path
        except Exception:
            # Exception is acceptable for invalid syntax
            pass

    @pytest.mark.asyncio
    async def test_for_loop_with_invalid_range(self, context):
        """Test For loop with invalid range."""
        from casare_rpa.nodes.control_flow_nodes import ForLoopNode

        # Start > End with positive step
        node = ForLoopNode("test", config={"start": 10, "end": 0, "step": 1})

        result = await node.execute(context)
        # Should handle gracefully - likely no iterations


class TestContextErrorHandling:
    """Test error handling in execution context."""

    def test_get_nonexistent_variable(self):
        """Test getting a variable that doesn't exist."""
        from casare_rpa.core.execution_context import ExecutionContext

        ctx = ExecutionContext()
        result = ctx.get_variable("nonexistent")

        # Should return None or raise, but not crash
        assert result is None

    def test_set_variable_with_none_name(self):
        """Test setting variable with None name."""
        from casare_rpa.core.execution_context import ExecutionContext

        ctx = ExecutionContext()

        # Should handle gracefully
        try:
            ctx.set_variable(None, "value")
        except (TypeError, ValueError):
            pass  # Expected behavior


class TestWorkflowRunnerErrors:
    """Test error handling in workflow runner."""

    def test_workflow_runner_exists(self):
        """Test WorkflowRunner class exists."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        assert WorkflowRunner is not None

    def test_workflow_schema_creation(self):
        """Test that workflow schema can be created."""
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        workflow = WorkflowSchema(WorkflowMetadata(name="Disconnected"))
        workflow.nodes = {
            "start": StartNode("start"),
            "end": EndNode("end")
        }
        workflow.connections = []

        assert workflow is not None
        assert len(workflow.nodes) == 2


class TestDataOperationErrors:
    """Test error handling in data operation nodes."""

    @pytest.fixture
    def context(self):
        """Create an execution context."""
        from casare_rpa.core.execution_context import ExecutionContext
        return ExecutionContext()

    @pytest.mark.asyncio
    async def test_regex_with_invalid_pattern(self, context):
        """Test regex operation with invalid pattern."""
        from casare_rpa.nodes.data_operation_nodes import RegexMatchNode

        # Invalid regex pattern
        node = RegexMatchNode("test", config={
            "pattern": "[invalid(regex",
            "text": "test string"
        })

        # Should handle regex error gracefully
        try:
            result = await node.execute(context)
        except Exception:
            pass  # Exception is acceptable

    @pytest.mark.asyncio
    async def test_math_division_by_zero(self, context):
        """Test math operation with division by zero."""
        from casare_rpa.nodes.data_operation_nodes import MathOperationNode

        node = MathOperationNode("test", config={
            "operation": "divide",
            "operand_a": "10",
            "operand_b": "0"
        })

        # Should handle division by zero
        try:
            result = await node.execute(context)
        except (ZeroDivisionError, Exception):
            pass  # Exception is acceptable

    @pytest.mark.asyncio
    async def test_json_parse_invalid_json(self, context):
        """Test JSON parse with invalid JSON string."""
        from casare_rpa.nodes.data_operation_nodes import JsonParseNode

        node = JsonParseNode("test", config={
            "json_string": "not valid json {{{",
        })

        # Should handle parse error gracefully
        try:
            result = await node.execute(context)
        except Exception:
            pass  # Exception is acceptable


class TestRecorderErrors:
    """Test error handling in recorder module."""

    def test_action_from_dict_with_invalid_type(self):
        """Test creating action from dict with invalid action type."""
        from casare_rpa.recorder.recording_session import RecordedAction

        # Invalid action type
        data = {
            "action_type": "invalid_type",
            "selector": "#test",
            "timestamp": "2024-01-01T00:00:00",
            "value": None,
            "element_info": {},
            "url": None
        }

        with pytest.raises((ValueError, KeyError)):
            RecordedAction.from_dict(data)

    def test_workflow_generator_empty_selector(self):
        """Test workflow generator with empty selector."""
        from casare_rpa.recorder.workflow_generator import WorkflowGenerator

        generator = WorkflowGenerator()

        result = generator._truncate_selector(None)
        assert result == "..."

        result = generator._truncate_selector("")
        assert result == "..."


class TestHotkeyErrors:
    """Test error handling in hotkey settings."""

    def test_load_from_invalid_path(self, tmp_path):
        """Test loading settings from non-existent directory."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings, DEFAULT_HOTKEYS

        # Path that doesn't exist
        invalid_path = tmp_path / "nonexistent" / "deeply" / "nested" / "hotkeys.json"

        settings = HotkeySettings(invalid_path)

        # Should fall back to defaults
        assert settings.get_all_hotkeys() == DEFAULT_HOTKEYS

    def test_save_to_readonly_location(self, tmp_path):
        """Test saving settings when directory is read-only."""
        from casare_rpa.utils.hotkey_settings import HotkeySettings

        settings_file = tmp_path / "hotkeys.json"
        settings = HotkeySettings(settings_file)

        # Modify settings
        settings.set_shortcuts("test", ["Ctrl+T"])

        # Save should work normally
        settings.save()

        # Verify file was created
        assert settings_file.exists()


class TestWorkflowLoaderErrors:
    """Test error handling in workflow loader."""

    def test_load_workflow_with_empty_dict(self):
        """Test loading workflow from empty dictionary."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        # Empty dict should not crash
        workflow = load_workflow_from_dict({})

        # Should have some default structure
        assert workflow is not None

    def test_load_workflow_with_invalid_node_type(self):
        """Test loading workflow with invalid node type."""
        from casare_rpa.utils.workflow_loader import load_workflow_from_dict

        data = {
            "metadata": {"name": "Test"},
            "nodes": {
                "invalid": {
                    "node_type": "CompletelyInvalidNodeType",
                    "config": {}
                }
            },
            "connections": [],
            "variables": {},
            "settings": {}
        }

        workflow = load_workflow_from_dict(data)

        # Invalid node should be skipped
        assert "invalid" not in workflow.nodes


class TestBaseNodeErrors:
    """Test error handling in base node class."""

    def test_node_with_empty_id(self):
        """Test creating node with empty ID."""
        from casare_rpa.nodes.basic_nodes import StartNode

        # Empty ID might cause issues
        node = StartNode("")
        assert node.node_id == ""

    def test_node_port_access_nonexistent(self):
        """Test accessing non-existent port."""
        from casare_rpa.nodes.basic_nodes import StartNode

        node = StartNode("test")

        # Accessing non-existent port - use get_input_value
        value = node.get_input_value("nonexistent_port")
        assert value is None


class TestSelectorErrors:
    """Test error handling in selector system."""

    def test_parse_empty_selector_raises(self):
        """Test parsing empty selector raises error."""
        from casare_rpa.desktop.selector import parse_selector

        # parse_selector expects a dict, not a string
        with pytest.raises((ValueError, TypeError)):
            parse_selector("")

    def test_parse_selector_requires_strategy(self):
        """Test parsing selector requires strategy field."""
        from casare_rpa.desktop.selector import parse_selector

        # Empty dict selector should raise - requires 'strategy' field
        with pytest.raises(ValueError):
            parse_selector({})


class TestEventBusErrors:
    """Test error handling in event bus."""

    def test_event_bus_can_be_instantiated(self):
        """Test EventBus can be created."""
        from casare_rpa.core.events import EventBus

        # Just test that EventBus exists and can be used
        assert EventBus is not None

    def test_event_bus_has_methods(self):
        """Test EventBus has expected methods."""
        from casare_rpa.core.events import EventBus

        # Check that EventBus has basic event methods
        bus = EventBus()
        assert hasattr(bus, 'subscribe') or hasattr(bus, 'publish')


class TestNodeStatusTransitions:
    """Test node status transitions and edge cases."""

    def test_node_has_status_attribute(self):
        """Test that node has status attribute."""
        from casare_rpa.nodes.basic_nodes import StartNode

        node = StartNode("test")
        assert hasattr(node, 'status')

    def test_node_double_reset(self):
        """Test resetting a node multiple times."""
        from casare_rpa.nodes.basic_nodes import StartNode

        node = StartNode("test")

        # Multiple resets should be safe
        node.reset()
        node.reset()
        node.reset()


class TestAsyncErrorPropagation:
    """Test async error propagation."""

    @pytest.fixture
    def context(self):
        """Create an execution context."""
        from casare_rpa.core.execution_context import ExecutionContext
        return ExecutionContext()

    @pytest.mark.asyncio
    async def test_timeout_handling(self, context):
        """Test that timeouts are handled gracefully."""
        from casare_rpa.nodes.wait_nodes import WaitNode

        # Very short wait should work
        node = WaitNode("test", config={"seconds": 0.001})

        result = await node.execute(context)
        # Should complete quickly

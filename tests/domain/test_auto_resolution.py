"""
Test for auto-resolution in get_parameter().

This test verifies that the Concept 3 variable resolution unification works:
- get_parameter() now auto-resolves {{variables}} when context is available
- get_raw_parameter() returns un-resolved values
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Dict, Any

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType


class AutoResolutionTestNode(BaseNode):
    """Test node that uses get_parameter()."""

    def _define_ports(self):
        self.add_input_port("message", DataType.STRING)
        self.add_exec_input()
        self.add_exec_output()

    async def execute(self, context):
        # This should be auto-resolved!
        message = self.get_parameter("message")
        raw_message = self.get_raw_parameter("message")

        return {
            "success": True,
            "resolved": message,
            "raw": raw_message,
        }


class TestGetParameterAutoResolution:
    """Test the new auto-resolution feature in get_parameter()."""

    def test_auto_resolves_when_context_set(self):
        """get_parameter() should auto-resolve {{variables}} when context is set."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {"message": "Hello {{name}}!"})

        # Mock context with resolve_value
        mock_context = MagicMock()
        mock_context.resolve_value = MagicMock(return_value="Hello World!")

        # Set execution context (this is what NodeExecutor does)
        node.set_execution_context(mock_context)

        # Act
        result = node.get_parameter("message")

        # Assert
        assert result == "Hello World!"
        mock_context.resolve_value.assert_called_once_with("Hello {{name}}!")

    def test_raw_parameter_does_not_resolve(self):
        """get_raw_parameter() should NOT resolve variables."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {"message": "Hello {{name}}!"})

        # Mock context with resolve_value
        mock_context = MagicMock()
        mock_context.resolve_value = MagicMock(return_value="Hello World!")

        # Set execution context
        node.set_execution_context(mock_context)

        # Act
        result = node.get_raw_parameter("message")

        # Assert
        assert result == "Hello {{name}}!"  # Should be unchanged
        mock_context.resolve_value.assert_not_called()

    def test_resolve_false_flag_prevents_resolution(self):
        """get_parameter(resolve=False) should not resolve variables."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {"message": "Hello {{name}}!"})

        mock_context = MagicMock()
        mock_context.resolve_value = MagicMock(return_value="Hello World!")
        node.set_execution_context(mock_context)

        # Act
        result = node.get_parameter("message", resolve=False)

        # Assert
        assert result == "Hello {{name}}!"
        mock_context.resolve_value.assert_not_called()

    def test_no_resolution_when_context_not_set(self):
        """get_parameter() should return raw value when no context is set."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {"message": "Hello {{name}}!"})
        # Note: NOT setting execution context

        # Act
        result = node.get_parameter("message")

        # Assert - should be unchanged since no context
        assert result == "Hello {{name}}!"

    def test_port_value_also_resolved(self):
        """Values from input ports should also be resolved."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {})
        node.set_input_value("message", "Port value: {{value}}")

        mock_context = MagicMock()
        mock_context.resolve_value = MagicMock(return_value="Port value: 42")
        node.set_execution_context(mock_context)

        # Act
        result = node.get_parameter("message")

        # Assert
        assert result == "Port value: 42"
        mock_context.resolve_value.assert_called_once_with("Port value: {{value}}")

    def test_none_values_not_resolved(self):
        """None values should not be passed to resolve_value."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {})  # No message set

        mock_context = MagicMock()
        mock_context.resolve_value = MagicMock()
        node.set_execution_context(mock_context)

        # Act
        result = node.get_parameter("message")

        # Assert
        assert result is None
        mock_context.resolve_value.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_auto_resolution(self):
        """Full integration: execute() should get auto-resolved values."""
        # Arrange
        node = AutoResolutionTestNode("test-node", {"message": "Hello {{name}}!"})

        mock_context = MagicMock()
        mock_context.resolve_value = MagicMock(side_effect=lambda v: v.replace("{{name}}", "World"))
        mock_context.set_current_node = MagicMock()

        # Simulate what NodeExecutor does
        node.set_execution_context(mock_context)

        try:
            result = await node.execute(mock_context)
        finally:
            node.set_execution_context(None)

        # Assert
        assert result["success"] is True
        assert result["resolved"] == "Hello World!"
        assert result["raw"] == "Hello {{name}}!"

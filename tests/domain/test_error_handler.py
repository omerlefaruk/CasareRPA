"""
Tests for the @error_handler decorator.

Tests cover:
- Async function handling
- Sync function handling
- Status management
- Error logging
- Custom log format
- Error outputs
- Traceback inclusion
- Re-raise behavior
"""

import asyncio
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

from casare_rpa.domain.decorators.error_handler import error_handler
from casare_rpa.domain.value_objects.types import NodeStatus


class MockNode:
    """Mock node class for testing the decorator."""

    def __init__(self):
        self.status = NodeStatus.IDLE
        self.node_id = "test_node_123"
        self.node_type = "MockTestNode"
        self.outputs: Dict[str, Any] = {}

    def set_output_value(self, key: str, value: Any) -> None:
        """Mock set_output_value method."""
        self.outputs[key] = value


class TestErrorHandlerAsync:
    """Tests for async function handling."""

    @pytest.mark.asyncio
    async def test_success_returns_result(self):
        """Test that successful execution returns the result unchanged."""
        node = MockNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            return {"success": True, "data": "test", "next_nodes": ["exec_out"]}

        result = await execute(node, None)

        assert result["success"] is True
        assert result["data"] == "test"
        assert result["next_nodes"] == ["exec_out"]

    @pytest.mark.asyncio
    async def test_success_sets_status(self):
        """Test that success sets NodeStatus.SUCCESS."""
        node = MockNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            return {"success": True, "data": "test", "next_nodes": ["exec_out"]}

        await execute(node, None)

        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_error_returns_error_result(self):
        """Test that exceptions return standardized error result."""
        node = MockNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Test error message")

        result = await execute(node, None)

        assert result["success"] is False
        assert result["error"] == "Test error message"
        assert result["error_type"] == "ValueError"
        assert result["next_nodes"] == []

    @pytest.mark.asyncio
    async def test_error_sets_error_status(self):
        """Test that errors set NodeStatus.ERROR."""
        node = MockNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            raise RuntimeError("Test error")

        await execute(node, None)

        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_error_logs_message(self):
        """Test that errors are logged with correct format."""
        node = MockNode()

        @error_handler(log_format="{class_name}[{node_id}]: {error}")
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Something went wrong")

        with patch("casare_rpa.domain.decorators.error_handler.logger") as mock_logger:
            await execute(node, None)

<<<<<<< HEAD
        mock_logger.error.assert_called_once_with(
            "MockNode[test_node_123]: Something went wrong"
        )
=======
        mock_logger.error.assert_called_once_with("MockNode[test_node_123]: Something went wrong")
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

    @pytest.mark.asyncio
    async def test_include_traceback_uses_exception_logger(self):
        """Test that include_traceback=True uses logger.exception."""
        node = MockNode()

        @error_handler(include_traceback=True)
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Traceback test")

        with patch("casare_rpa.domain.decorators.error_handler.logger") as mock_logger:
            await execute(node, None)

        mock_logger.exception.assert_called_once()
        mock_logger.error.assert_not_called()


class TestErrorHandlerSync:
    """Tests for sync function handling."""

    def test_sync_success_returns_result(self):
        """Test that sync functions work correctly."""
        node = MockNode()

        @error_handler()
        def execute(self, context) -> Dict[str, Any]:
            return {"success": True, "data": "sync_test", "next_nodes": ["exec_out"]}

        result = execute(node, None)

        assert result["success"] is True
        assert result["data"] == "sync_test"

    def test_sync_error_returns_error_result(self):
        """Test that sync errors return standardized result."""
        node = MockNode()

        @error_handler()
        def execute(self, context) -> Dict[str, Any]:
            raise KeyError("missing_key")

        result = execute(node, None)

        assert result["success"] is False
        assert "missing_key" in result["error"]
        assert result["error_type"] == "KeyError"


class TestErrorHandlerOptions:
    """Tests for decorator options."""

    @pytest.mark.asyncio
    async def test_set_status_false_skips_status(self):
        """Test that set_status=False doesn't modify status."""
        node = MockNode()
        node.status = NodeStatus.RUNNING

        @error_handler(set_status=False)
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Error without status change")

        await execute(node, None)

        # Status should remain unchanged
        assert node.status == NodeStatus.RUNNING

    @pytest.mark.asyncio
    async def test_reraise_propagates_exception(self):
        """Test that reraise=True re-raises the exception."""
        node = MockNode()

        @error_handler(reraise=True)
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Must be raised")

        with pytest.raises(ValueError, match="Must be raised"):
            await execute(node, None)

    @pytest.mark.asyncio
    async def test_error_outputs_sets_values(self):
        """Test that error_outputs sets output values on error."""
        node = MockNode()

        @error_handler(error_outputs={"success": False, "result": None})
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Output test error")

        await execute(node, None)

        assert node.outputs["success"] is False
        assert node.outputs["result"] is None

    @pytest.mark.asyncio
    async def test_custom_log_format_with_node_type(self):
        """Test custom log format with node_type placeholder."""
        node = MockNode()

        @error_handler(log_format="[{node_type}] Error: {error}")
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("Format test")

        with patch("casare_rpa.domain.decorators.error_handler.logger") as mock_logger:
            await execute(node, None)

        mock_logger.error.assert_called_once_with("[MockTestNode] Error: Format test")


class TestErrorHandlerEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_node_without_status_attribute(self):
        """Test decorator works with nodes missing status attribute."""

        class SimpleNode:
            node_id = "simple"

        node = SimpleNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("No status attribute")

        result = await execute(node, None)

        assert result["success"] is False
        # Should not raise AttributeError

    @pytest.mark.asyncio
    async def test_node_without_node_id_uses_unknown(self):
        """Test decorator uses 'unknown' for missing node_id."""

        class MinimalNode:
            status = NodeStatus.IDLE

        node = MinimalNode()

        @error_handler(log_format="{node_id}: {error}")
        async def execute(self, context) -> Dict[str, Any]:
            raise ValueError("ID test")

        with patch("casare_rpa.domain.decorators.error_handler.logger") as mock_logger:
            await execute(node, None)

        mock_logger.error.assert_called_once_with("unknown: ID test")

    @pytest.mark.asyncio
    async def test_preserves_function_metadata(self):
        """Test that functools.wraps preserves function metadata."""
        node = MockNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            """Execute method docstring."""
            return {"success": True, "next_nodes": []}

        assert execute.__name__ == "execute"
        assert execute.__doc__ == "Execute method docstring."

    @pytest.mark.asyncio
    async def test_result_without_success_key_defaults_true(self):
        """Test that results without success key don't fail."""
        node = MockNode()

        @error_handler()
        async def execute(self, context) -> Dict[str, Any]:
            return {"data": "no success key"}

        result = await execute(node, None)

        assert result["data"] == "no success key"
        # Should set SUCCESS since no success=False
        assert node.status == NodeStatus.SUCCESS

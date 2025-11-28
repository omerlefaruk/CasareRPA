"""
Tests for Basic workflow nodes.

Tests 3 basic nodes (9 tests total):
- StartNode: workflow entry point (3 tests)
- EndNode: workflow exit point (3 tests)
- CommentNode: workflow documentation (3 tests)
"""

import pytest
from unittest.mock import Mock
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class TestStartNode:
    """Tests for StartNode - workflow entry point."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_start_node_executes_successfully(self, execution_context) -> None:
        """Test StartNode executes and returns success."""
        from casare_rpa.nodes.basic_nodes import StartNode

        node = StartNode(node_id="start_1", name="Workflow Start")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["message"] == "Workflow started"
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_start_node_has_only_exec_output(self, execution_context) -> None:
        """Test StartNode has no inputs, only execution output."""
        from casare_rpa.nodes.basic_nodes import StartNode

        node = StartNode(node_id="start_2")

        # Check port configuration
        assert "exec_out" in node.output_ports
        assert len(node.input_ports) == 0  # No inputs

    @pytest.mark.asyncio
    async def test_start_node_validation_always_valid(self, execution_context) -> None:
        """Test StartNode validation always passes (no config required)."""
        from casare_rpa.nodes.basic_nodes import StartNode

        node = StartNode(node_id="start_3")

        is_valid, error = node._validate_config()

        assert is_valid is True
        assert error == ""


class TestEndNode:
    """Tests for EndNode - workflow exit point."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_execution_summary = lambda: {
            "workflow_name": "Test Workflow",
            "nodes_executed": 5,
            "errors": [],
            "duration_ms": 1234,
        }
        return context

    @pytest.mark.asyncio
    async def test_end_node_executes_successfully(self, execution_context) -> None:
        """Test EndNode executes and returns success with summary."""
        from casare_rpa.nodes.basic_nodes import EndNode

        node = EndNode(node_id="end_1", name="Workflow End")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["message"] == "Workflow completed"
        assert "summary" in result["data"]
        assert result["next_nodes"] == []  # No next nodes
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_end_node_has_only_exec_input(self, execution_context) -> None:
        """Test EndNode has only execution input, no outputs."""
        from casare_rpa.nodes.basic_nodes import EndNode

        node = EndNode(node_id="end_2")

        # Check port configuration
        assert "exec_in" in node.input_ports
        assert len(node.output_ports) == 0  # No outputs

    @pytest.mark.asyncio
    async def test_end_node_validation_always_valid(self, execution_context) -> None:
        """Test EndNode validation always passes (no config required)."""
        from casare_rpa.nodes.basic_nodes import EndNode

        node = EndNode(node_id="end_3")

        is_valid, error = node._validate_config()

        assert is_valid is True
        assert error == ""


class TestCommentNode:
    """Tests for CommentNode - workflow documentation."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        return context

    @pytest.mark.asyncio
    async def test_comment_node_executes_with_skipped_status(
        self, execution_context
    ) -> None:
        """Test CommentNode executes and returns skipped status."""
        from casare_rpa.nodes.basic_nodes import CommentNode

        node = CommentNode(
            node_id="comment_1",
            name="Documentation",
            comment="This is a test comment",
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["comment"] == "This is a test comment"
        assert result["data"]["skipped"] is True
        assert result["next_nodes"] == []
        assert node.status == NodeStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_comment_node_has_no_ports(self, execution_context) -> None:
        """Test CommentNode has no input or output ports."""
        from casare_rpa.nodes.basic_nodes import CommentNode

        node = CommentNode(node_id="comment_2")

        # Check port configuration - comment nodes are isolated
        assert len(node.input_ports) == 0
        assert len(node.output_ports) == 0

    @pytest.mark.asyncio
    async def test_comment_node_set_get_comment(self, execution_context) -> None:
        """Test CommentNode set_comment and get_comment methods."""
        from casare_rpa.nodes.basic_nodes import CommentNode

        node = CommentNode(node_id="comment_3", comment="Initial comment")

        # Test get_comment
        assert node.get_comment() == "Initial comment"

        # Test set_comment
        node.set_comment("Updated comment")
        assert node.get_comment() == "Updated comment"

        # Verify it executes with updated comment
        result = await node.execute(execution_context)
        assert result["data"]["comment"] == "Updated comment"


class TestBasicNodesIntegration:
    """Integration tests for basic nodes in workflow context."""

    @pytest.fixture
    def execution_context(self) -> Mock:
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_execution_summary = lambda: {
            "workflow_name": "Integration Test",
            "nodes_executed": 3,
            "errors": [],
        }
        return context

    @pytest.mark.asyncio
    async def test_basic_workflow_flow(self, execution_context) -> None:
        """Test Start -> Comment -> End flow follows ExecutionResult pattern."""
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode, CommentNode

        start = StartNode(node_id="start")
        comment = CommentNode(node_id="comment", comment="Middle step")
        end = EndNode(node_id="end")

        # Execute flow
        start_result = await start.execute(execution_context)
        comment_result = await comment.execute(execution_context)
        end_result = await end.execute(execution_context)

        # All should succeed
        assert start_result["success"] is True
        assert comment_result["success"] is True
        assert end_result["success"] is True

        # Verify ExecutionResult structure
        for result in [start_result, comment_result, end_result]:
            assert "success" in result
            assert "data" in result
            assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_node_type_attribute(self, execution_context) -> None:
        """Test all basic nodes have correct node_type attribute."""
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode, CommentNode

        start = StartNode(node_id="s1")
        end = EndNode(node_id="e1")
        comment = CommentNode(node_id="c1")

        assert start.node_type == "StartNode"
        assert end.node_type == "EndNode"
        assert comment.node_type == "CommentNode"

    @pytest.mark.asyncio
    async def test_node_name_customization(self, execution_context) -> None:
        """Test basic nodes accept custom names."""
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode, CommentNode

        start = StartNode(node_id="s1", name="Custom Start")
        end = EndNode(node_id="e1", name="Custom End")
        comment = CommentNode(node_id="c1", name="Custom Comment")

        assert start.name == "Custom Start"
        assert end.name == "Custom End"
        assert comment.name == "Custom Comment"

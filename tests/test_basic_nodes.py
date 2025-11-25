"""
Tests for basic nodes: StartNode, EndNode, CommentNode.

These nodes form the fundamental building blocks of any workflow.
"""

import pytest

from casare_rpa.nodes.basic_nodes import StartNode, EndNode, CommentNode
from casare_rpa.core.types import NodeStatus, PortType


class TestStartNode:
    """Tests for the StartNode - workflow entry point."""

    def test_start_node_creation(self):
        """Test that StartNode can be created with default settings."""
        node = StartNode(node_id="start_1")

        assert node.node_id == "start_1"
        assert node.name == "Start"
        assert node.node_type == "StartNode"

    def test_start_node_with_custom_name(self):
        """Test StartNode with custom name."""
        node = StartNode(node_id="start_1", name="Workflow Entry")

        assert node.name == "Workflow Entry"

    def test_start_node_ports(self):
        """Test that StartNode has only execution output port."""
        node = StartNode(node_id="start_1")

        # Should have no input ports
        assert len(node.input_ports) == 0

        # Should have one output port (exec_out)
        assert "exec_out" in node.output_ports
        # Note: BaseNode's add_output_port sets PortType.OUTPUT
        assert node.output_ports["exec_out"].port_type == PortType.OUTPUT

    @pytest.mark.asyncio
    async def test_start_node_execution(self, execution_context):
        """Test StartNode execution returns success."""
        node = StartNode(node_id="start_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["message"] == "Workflow started"
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_start_node_execution_in_debug_mode(self, debug_context):
        """Test StartNode execution in debug mode."""
        node = StartNode(node_id="start_1")

        result = await node.execute(debug_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS

    def test_start_node_validation(self):
        """Test StartNode validation always passes."""
        node = StartNode(node_id="start_1")

        is_valid, error = node._validate_config()

        assert is_valid is True
        assert error == ""

    def test_start_node_serialization(self):
        """Test StartNode can be serialized to dict."""
        node = StartNode(node_id="start_1", name="My Start")

        data = node.serialize()

        assert data["node_id"] == "start_1"
        assert data["node_type"] == "StartNode"


class TestEndNode:
    """Tests for the EndNode - workflow exit point."""

    def test_end_node_creation(self):
        """Test that EndNode can be created with default settings."""
        node = EndNode(node_id="end_1")

        assert node.node_id == "end_1"
        assert node.name == "End"
        assert node.node_type == "EndNode"

    def test_end_node_with_custom_name(self):
        """Test EndNode with custom name."""
        node = EndNode(node_id="end_1", name="Workflow Exit")

        assert node.name == "Workflow Exit"

    def test_end_node_ports(self):
        """Test that EndNode has only execution input port."""
        node = EndNode(node_id="end_1")

        # Should have one input port (exec_in)
        assert "exec_in" in node.input_ports
        # Note: BaseNode's add_input_port sets PortType.INPUT
        assert node.input_ports["exec_in"].port_type == PortType.INPUT

        # Should have no output ports
        assert len(node.output_ports) == 0

    @pytest.mark.asyncio
    async def test_end_node_execution(self, execution_context):
        """Test EndNode execution returns success with summary."""
        node = EndNode(node_id="end_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["message"] == "Workflow completed"
        assert "summary" in result["data"]
        assert result["next_nodes"] == []  # No next nodes - this is the end
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_end_node_execution_includes_summary(self, execution_context):
        """Test EndNode includes execution summary in result."""
        node = EndNode(node_id="end_1")

        # Add some execution history
        execution_context.set_variable("test_var", "test_value")
        execution_context.set_current_node("node_1")
        execution_context.set_current_node("node_2")

        result = await node.execute(execution_context)

        summary = result["data"]["summary"]
        assert summary["workflow_name"] == "TestWorkflow"
        assert summary["nodes_executed"] == 2

    @pytest.mark.asyncio
    async def test_end_node_stops_workflow(self, execution_context):
        """Test EndNode returns empty next_nodes to stop workflow."""
        node = EndNode(node_id="end_1")

        result = await node.execute(execution_context)

        # End node should return empty next_nodes
        assert result["next_nodes"] == []

    def test_end_node_validation(self):
        """Test EndNode validation always passes."""
        node = EndNode(node_id="end_1")

        is_valid, error = node._validate_config()

        assert is_valid is True
        assert error == ""


class TestCommentNode:
    """Tests for the CommentNode - workflow documentation."""

    def test_comment_node_creation(self):
        """Test that CommentNode can be created with default settings."""
        node = CommentNode(node_id="comment_1")

        assert node.node_id == "comment_1"
        assert node.name == "Comment"
        assert node.node_type == "CommentNode"

    def test_comment_node_with_text(self):
        """Test CommentNode with comment text."""
        node = CommentNode(
            node_id="comment_1",
            comment="This section handles user authentication"
        )

        assert node.get_comment() == "This section handles user authentication"

    def test_comment_node_with_config(self):
        """Test CommentNode with comment in config."""
        node = CommentNode(
            node_id="comment_1",
            config={"comment": "Config-based comment"}
        )

        assert node.get_comment() == "Config-based comment"

    def test_comment_node_no_ports(self):
        """Test that CommentNode has no ports."""
        node = CommentNode(node_id="comment_1")

        assert len(node.input_ports) == 0
        assert len(node.output_ports) == 0

    @pytest.mark.asyncio
    async def test_comment_node_execution_skipped(self, execution_context):
        """Test CommentNode execution is skipped."""
        node = CommentNode(
            node_id="comment_1",
            comment="Test comment"
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["skipped"] is True
        assert result["data"]["comment"] == "Test comment"
        assert result["next_nodes"] == []
        assert node.status == NodeStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_comment_node_empty_comment(self, execution_context):
        """Test CommentNode with empty comment."""
        node = CommentNode(node_id="comment_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["comment"] == ""

    def test_comment_node_set_comment(self):
        """Test setting comment text."""
        node = CommentNode(node_id="comment_1")

        node.set_comment("Updated comment text")

        assert node.get_comment() == "Updated comment text"

    def test_comment_node_validation(self):
        """Test CommentNode validation always passes."""
        node = CommentNode(node_id="comment_1")

        is_valid, error = node._validate_config()

        assert is_valid is True
        assert error == ""

    def test_comment_node_special_characters(self):
        """Test CommentNode with special characters in comment."""
        special_comment = "Special chars: !@#$%^&*() \n\t Unicode: \u4e2d\u6587"
        node = CommentNode(node_id="comment_1", comment=special_comment)

        assert node.get_comment() == special_comment

    def test_comment_node_long_text(self):
        """Test CommentNode with long comment text."""
        long_comment = "A" * 10000  # 10K characters
        node = CommentNode(node_id="comment_1", comment=long_comment)

        assert node.get_comment() == long_comment
        assert len(node.get_comment()) == 10000


class TestBasicWorkflowScenario:
    """Integration tests using basic nodes together."""

    @pytest.mark.asyncio
    async def test_start_to_end_workflow(self, execution_context):
        """Test a simple Start -> End workflow."""
        start = StartNode(node_id="start")
        end = EndNode(node_id="end")

        # Execute start
        start_result = await start.execute(execution_context)
        assert start_result["success"] is True
        assert "exec_out" in start_result["next_nodes"]

        # Execute end
        end_result = await end.execute(execution_context)
        assert end_result["success"] is True
        assert end_result["next_nodes"] == []

    @pytest.mark.asyncio
    async def test_workflow_with_comments(self, execution_context):
        """Test workflow with comment nodes - comments are skipped."""
        start = StartNode(node_id="start")
        comment = CommentNode(
            node_id="comment",
            comment="This is a documentation comment"
        )
        end = EndNode(node_id="end")

        # Execute in sequence
        start_result = await start.execute(execution_context)
        assert start_result["success"] is True

        comment_result = await comment.execute(execution_context)
        assert comment_result["success"] is True
        assert comment_result["data"]["skipped"] is True

        end_result = await end.execute(execution_context)
        assert end_result["success"] is True

    @pytest.mark.asyncio
    async def test_multiple_end_nodes_scenario(self, execution_context):
        """Test workflow with multiple possible end points."""
        start = StartNode(node_id="start")
        end_success = EndNode(node_id="end_success", name="Success End")
        end_failure = EndNode(node_id="end_failure", name="Failure End")

        # Start
        await start.execute(execution_context)

        # Can end at either end node
        success_result = await end_success.execute(execution_context)
        assert success_result["success"] is True

        # Both end nodes work independently
        failure_result = await end_failure.execute(execution_context)
        assert failure_result["success"] is True

    @pytest.mark.asyncio
    async def test_workflow_execution_tracking(self, execution_context):
        """Test that execution context tracks node execution."""
        start = StartNode(node_id="start")
        end = EndNode(node_id="end")

        # Track execution
        execution_context.set_current_node("start")
        await start.execute(execution_context)

        execution_context.set_current_node("end")
        await end.execute(execution_context)

        # Verify execution path is tracked
        assert "start" in execution_context.execution_path
        assert "end" in execution_context.execution_path

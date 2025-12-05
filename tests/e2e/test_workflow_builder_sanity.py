"""
Sanity tests for the E2E WorkflowBuilder.

These tests verify the WorkflowBuilder infrastructure works correctly.
"""

import pytest

# Import from relative path within the tests directory
from .helpers.workflow_builder import WorkflowBuilder, WorkflowExecutionResult


class TestWorkflowBuilderConstruction:
    """Test WorkflowBuilder construction methods."""

    def test_create_builder(self):
        """Test basic builder creation."""
        builder = WorkflowBuilder()
        assert builder is not None
        assert builder._name == "E2E Test Workflow"

    def test_create_builder_with_name(self):
        """Test builder creation with custom name."""
        builder = WorkflowBuilder(name="My Test Workflow")
        assert builder._name == "My Test Workflow"

    def test_add_start_node(self):
        """Test adding a start node."""
        builder = WorkflowBuilder()
        builder.add_start()

        assert len(builder._nodes) == 1
        assert "StartNode" in [n.node_type for n in builder._nodes.values()]

    def test_add_end_node(self):
        """Test adding an end node."""
        builder = WorkflowBuilder()
        builder.add_start().add_end()

        assert len(builder._nodes) == 2
        node_types = [n.node_type for n in builder._nodes.values()]
        assert "StartNode" in node_types
        assert "EndNode" in node_types

    def test_add_set_variable_node(self):
        """Test adding a set variable node."""
        builder = WorkflowBuilder()
        builder.add_start().add_set_variable("counter", 42).add_end()

        assert len(builder._nodes) == 3
        node_types = [n.node_type for n in builder._nodes.values()]
        assert "SetVariableNode" in node_types

    def test_add_increment_variable_node(self):
        """Test adding an increment variable node."""
        builder = WorkflowBuilder()
        builder.add_start().add_set_variable("counter", 0).add_increment_variable(
            "counter"
        ).add_end()

        assert len(builder._nodes) == 4
        node_types = [n.node_type for n in builder._nodes.values()]
        assert "IncrementVariableNode" in node_types

    def test_connections_created(self):
        """Test that connections are automatically created."""
        builder = WorkflowBuilder()
        builder.add_start().add_set_variable("x", 1).add_end()

        # Start -> SetVariable -> End (2 connections)
        assert len(builder._connections) == 2


class TestWorkflowBuilderBuild:
    """Test WorkflowBuilder build method."""

    def test_build_simple_workflow(self):
        """Test building a simple workflow."""
        builder = WorkflowBuilder()
        builder.add_start().add_end()

        workflow = builder.build()

        assert workflow is not None
        assert workflow.metadata.name == "E2E Test Workflow"
        assert len(workflow.nodes) == 2
        assert len(workflow.connections) == 1

    def test_build_workflow_with_variables(self):
        """Test building workflow with variable nodes."""
        builder = WorkflowBuilder()
        builder.add_start().add_set_variable("counter", 0).add_increment_variable(
            "counter"
        ).add_end()

        workflow = builder.build()

        assert len(workflow.nodes) == 4
        assert len(workflow.connections) == 3


class TestWorkflowBuilderControlFlow:
    """Test WorkflowBuilder control flow methods."""

    def test_for_loop_structure(self):
        """Test For loop structure creation."""
        builder = WorkflowBuilder()
        builder.add_start().add_for_loop(range_end=5).add_increment_variable(
            "sum"
        ).add_for_loop_end().add_end()

        # Start, ForLoopStart, Increment, ForLoopEnd, End = 5 nodes
        assert len(builder._nodes) == 5
        node_types = [n.node_type for n in builder._nodes.values()]
        assert "ForLoopStartNode" in node_types
        assert "ForLoopEndNode" in node_types

    def test_while_loop_structure(self):
        """Test While loop structure creation."""
        builder = WorkflowBuilder()
        builder.add_start().add_set_variable("counter", 0).add_while_loop(
            "counter < 5"
        ).add_increment_variable("counter").add_while_loop_end().add_end()

        node_types = [n.node_type for n in builder._nodes.values()]
        assert "WhileLoopStartNode" in node_types
        assert "WhileLoopEndNode" in node_types

    def test_if_structure(self):
        """Test If/Else structure creation."""
        builder = WorkflowBuilder()
        (
            builder.add_start()
            .add_set_variable("x", 10)
            .add_if("x > 5")
            .branch_true()
            .add_set_variable("result", "big")
            .branch_false()
            .add_set_variable("result", "small")
            .end_if()
            .add_end()
        )

        node_types = [n.node_type for n in builder._nodes.values()]
        assert "IfNode" in node_types
        assert "MergeNode" in node_types


@pytest.mark.asyncio
class TestWorkflowBuilderExecution:
    """Test WorkflowBuilder execute method."""

    async def test_execute_minimal_workflow(self):
        """Test executing a minimal workflow (Start -> End)."""
        result = await WorkflowBuilder().add_start().add_end().execute()

        assert result["success"] is True
        assert result["error"] is None
        assert result["executed_nodes"] >= 2

    async def test_execute_set_variable(self):
        """Test executing workflow with SetVariable."""
        result = (
            await WorkflowBuilder()
            .add_start()
            .add_set_variable("counter", 42)
            .add_end()
            .execute()
        )

        assert result["success"] is True
        assert result["variables"]["counter"] == 42

    async def test_execute_increment_variable(self):
        """Test executing workflow with IncrementVariable."""
        result = await (
            WorkflowBuilder()
            .add_start()
            .add_set_variable("counter", 0)
            .add_increment_variable("counter")
            .add_increment_variable("counter")
            .add_end()
            .execute()
        )

        assert result["success"] is True
        assert result["variables"]["counter"] == 2

    async def test_execute_with_initial_vars(self):
        """Test executing workflow with initial variables."""
        result = (
            await WorkflowBuilder()
            .add_start()
            .add_increment_variable("counter")
            .add_end()
            .execute(initial_vars={"counter": 10})
        )

        assert result["success"] is True
        assert result["variables"]["counter"] == 11

    async def test_execute_returns_duration(self):
        """Test that execution returns duration."""
        result = await WorkflowBuilder().add_start().add_end().execute()

        assert result["duration_ms"] >= 0

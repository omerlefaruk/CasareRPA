"""
Tests for the chain testing infrastructure itself.

Verifies that WorkflowBuilder and ChainExecutor work correctly
before using them in actual node chain tests.
"""

import pytest
from unittest.mock import AsyncMock

from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.value_objects.types import EXEC_IN_PORT, EXEC_OUT_PORT

from .conftest import WorkflowBuilder, ChainExecutor, ChainExecutionResult


class TestWorkflowBuilder:
    """Tests for the WorkflowBuilder class."""

    def test_add_single_node(self, workflow_builder: WorkflowBuilder) -> None:
        """Verify adding a single node to the workflow."""
        node = StartNode("start_1")

        workflow_builder.add(node)
        workflow = workflow_builder.build()

        assert "start_1" in workflow.nodes
        assert workflow.nodes["start_1"] is node

    def test_add_node_with_custom_id(self, workflow_builder: WorkflowBuilder) -> None:
        """Verify adding a node with a custom ID override."""
        node = StartNode("original_id")

        workflow_builder.add(node, id="custom_id")
        workflow = workflow_builder.build()

        assert "custom_id" in workflow.nodes
        assert "original_id" not in workflow.nodes
        assert node.node_id == "custom_id"

    def test_add_duplicate_id_raises_error(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify that adding a duplicate node ID raises ValueError."""
        node1 = StartNode("same_id")
        node2 = EndNode("same_id")

        workflow_builder.add(node1)

        with pytest.raises(ValueError, match="already exists"):
            workflow_builder.add(node2)

    def test_connect_nodes_default_ports(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify connecting nodes uses default exec ports."""
        start = StartNode("start")
        end = EndNode("end")

        workflow = workflow_builder.add(start).add(end).connect("start", "end").build()

        assert len(workflow.connections) == 1
        conn = workflow.connections[0]
        assert conn.source_node == "start"
        assert conn.source_port == EXEC_OUT_PORT
        assert conn.target_node == "end"
        assert conn.target_port == EXEC_IN_PORT

    def test_connect_nodes_explicit_ports(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify connecting nodes with explicit port names."""
        start = StartNode("start")
        end = EndNode("end")

        workflow = (
            workflow_builder.add(start)
            .add(end)
            .connect("start.exec_out", "end.exec_in")
            .build()
        )

        assert len(workflow.connections) == 1
        conn = workflow.connections[0]
        assert conn.source_port == "exec_out"
        assert conn.target_port == "exec_in"

    def test_connect_missing_source_raises_error(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify connecting from missing source raises ValueError."""
        end = EndNode("end")
        workflow_builder.add(end)

        with pytest.raises(ValueError, match="Source node.*not found"):
            workflow_builder.connect("missing", "end")

    def test_connect_missing_target_raises_error(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify connecting to missing target raises ValueError."""
        start = StartNode("start")
        workflow_builder.add(start)

        with pytest.raises(ValueError, match="Target node.*not found"):
            workflow_builder.connect("start", "missing")

    def test_connect_sequential_linear_chain(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify connect_sequential creates linear chain."""
        start = StartNode("start")
        set_var = SetVariableNode("set_var", config={"name": "x", "value": 10})
        end = EndNode("end")

        workflow = (
            workflow_builder.add(start)
            .add(set_var)
            .add(end)
            .connect_sequential()
            .build()
        )

        assert len(workflow.connections) == 2

        conn1 = workflow.connections[0]
        assert conn1.source_node == "start"
        assert conn1.target_node == "set_var"

        conn2 = workflow.connections[1]
        assert conn2.source_node == "set_var"
        assert conn2.target_node == "end"

    def test_connect_sequential_insufficient_nodes(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify connect_sequential with < 2 nodes raises error."""
        start = StartNode("start")
        workflow_builder.add(start)

        with pytest.raises(ValueError, match="fewer than 2 nodes"):
            workflow_builder.connect_sequential()

    def test_build_empty_workflow_raises_error(
        self, workflow_builder: WorkflowBuilder
    ) -> None:
        """Verify building empty workflow raises ValueError."""
        with pytest.raises(ValueError, match="no nodes"):
            workflow_builder.build()

    def test_reset_clears_state(self, workflow_builder: WorkflowBuilder) -> None:
        """Verify reset clears all builder state."""
        start = StartNode("start")
        end = EndNode("end")

        workflow_builder.add(start).add(end).connect("start", "end")
        workflow_builder.reset()

        assert len(workflow_builder._nodes) == 0
        assert len(workflow_builder._connections) == 0
        assert len(workflow_builder._node_order) == 0

    def test_method_chaining(self, workflow_builder: WorkflowBuilder) -> None:
        """Verify all methods return self for chaining."""
        start = StartNode("start")
        end = EndNode("end")

        result = workflow_builder.add(start).add(end).connect("start", "end")

        assert result is workflow_builder


class TestChainExecutor:
    """Tests for the ChainExecutor class."""

    @pytest.mark.asyncio
    async def test_execute_simple_chain(
        self,
        workflow_builder: WorkflowBuilder,
        chain_executor: ChainExecutor,
    ) -> None:
        """Verify executing a simple Start -> End chain."""
        start = StartNode("start")
        end = EndNode("end")

        workflow = workflow_builder.add(start).add(end).connect_sequential().build()

        result = await chain_executor.execute(workflow)

        assert result.success
        assert "start" in result.nodes_executed
        assert "end" in result.nodes_executed
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_execute_with_initial_variables(
        self,
        workflow_builder: WorkflowBuilder,
        chain_executor: ChainExecutor,
    ) -> None:
        """Verify initial variables are available to nodes."""
        start = StartNode("start")
        get_var = GetVariableNode("get_x", config={"variable_name": "x"})
        end = EndNode("end")

        workflow = (
            workflow_builder.add(start)
            .add(get_var)
            .add(end)
            .connect_sequential()
            .build()
        )

        result = await chain_executor.execute(workflow, variables={"x": 42})

        assert result.success
        assert result.node_results["get_x"]["data"]["value"] == 42

    @pytest.mark.asyncio
    async def test_execute_variable_chain(
        self,
        workflow_builder: WorkflowBuilder,
        chain_executor: ChainExecutor,
    ) -> None:
        """Verify SetVariable -> GetVariable chain works."""
        start = StartNode("start")
        set_var = SetVariableNode(
            "set_x", config={"variable_name": "my_var", "default_value": "hello"}
        )
        get_var = GetVariableNode("get_x", config={"variable_name": "my_var"})
        end = EndNode("end")

        workflow = (
            workflow_builder.add(start)
            .add(set_var)
            .add(get_var)
            .add(end)
            .connect_sequential()
            .build()
        )

        result = await chain_executor.execute(workflow)

        assert result.success
        assert result.final_variables.get("my_var") == "hello"
        assert result.node_results["get_x"]["data"]["value"] == "hello"

    @pytest.mark.asyncio
    async def test_execute_missing_start_node(
        self,
        workflow_builder: WorkflowBuilder,
        chain_executor: ChainExecutor,
    ) -> None:
        """Verify execution fails gracefully without StartNode."""
        end = EndNode("end")

        workflow = workflow_builder.add(end).build()

        result = await chain_executor.execute(workflow)

        assert not result.success
        assert any("StartNode" in err[1] for err in result.errors)

    @pytest.mark.asyncio
    async def test_result_contains_node_results(
        self,
        workflow_builder: WorkflowBuilder,
        chain_executor: ChainExecutor,
    ) -> None:
        """Verify node_results contains each node's execution result."""
        start = StartNode("start")
        end = EndNode("end")

        workflow = workflow_builder.add(start).add(end).connect_sequential().build()

        result = await chain_executor.execute(workflow)

        assert "start" in result.node_results
        assert "end" in result.node_results
        assert result.node_results["start"].get("success") is True


class TestChainExecutionResult:
    """Tests for the ChainExecutionResult dataclass."""

    def test_default_values(self) -> None:
        """Verify default values are set correctly."""
        result = ChainExecutionResult(success=True)

        assert result.success is True
        assert result.nodes_executed == []
        assert result.final_variables == {}
        assert result.errors == []
        assert result.node_results == {}

    def test_mutable_fields_are_independent(self) -> None:
        """Verify mutable fields don't share state between instances."""
        result1 = ChainExecutionResult(success=True)
        result2 = ChainExecutionResult(success=False)

        result1.nodes_executed.append("node1")
        result1.errors.append(("node1", "error"))

        assert result2.nodes_executed == []
        assert result2.errors == []

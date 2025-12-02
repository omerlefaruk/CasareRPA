"""
Unit tests for parallel execution nodes.

Tests ForkNode, JoinNode, and ParallelForEachNode covering:
- SUCCESS scenarios (happy path)
- ERROR scenarios (exception handling)
- EDGE CASES (boundary conditions, unusual inputs)

Following CasareRPA TDD patterns from CLAUDE.md.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock

from casare_rpa.nodes.parallel_nodes import (
    ForkNode,
    JoinNode,
    ParallelForEachNode,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import NodeStatus, PortType, DataType


@pytest.fixture
def execution_context():
    """Create a fresh execution context for each test."""
    return ExecutionContext(workflow_name="test_workflow")


# =============================================================================
# ForkNode Tests
# =============================================================================


class TestForkNodeInit:
    """Tests for ForkNode initialization."""

    def test_init_default_config(self):
        """Test ForkNode initialization with default config."""
        node = ForkNode(node_id="fork_1")

        assert node.node_id == "fork_1"
        assert node.name == "Fork"
        assert node.node_type == "ForkNode"
        assert node.paired_join_id == ""

    def test_init_custom_branch_count(self):
        """Test ForkNode with custom branch count."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 4, "fail_fast": True})

        assert node.get_parameter("branch_count", 2) == 4
        assert node.get_parameter("fail_fast", False) is True

    def test_init_with_none_config(self):
        """Test ForkNode with None config uses defaults."""
        node = ForkNode(node_id="fork_1", config=None)

        assert node.get_parameter("branch_count", 2) == 2
        assert node.get_parameter("fail_fast", False) is False


class TestForkNodePorts:
    """Tests for ForkNode port definitions."""

    def test_ports_default_two_branches(self):
        """Test default port definition with 2 branches."""
        node = ForkNode(node_id="fork_1")

        # Verify exec_in port exists
        assert "exec_in" in node.input_ports
        # Note: Port uses PortType.INPUT for input ports, data_type stores the exec type
        assert node.input_ports["exec_in"].port_type == PortType.INPUT

        # Verify branch output ports
        assert "branch_1" in node.output_ports
        assert "branch_2" in node.output_ports
        assert node.output_ports["branch_1"].port_type == PortType.OUTPUT

    def test_ports_custom_branch_count(self):
        """Test port definition with custom branch count."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 5})

        # Verify all branch ports created
        for i in range(1, 6):
            assert f"branch_{i}" in node.output_ports

        # Verify no extra branches
        assert "branch_6" not in node.output_ports

    def test_ports_minimum_branches(self):
        """Test port definition with minimum 2 branches."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 2})

        assert "branch_1" in node.output_ports
        assert "branch_2" in node.output_ports
        assert len([k for k in node.output_ports if k.startswith("branch_")]) == 2

    def test_ports_maximum_branches(self):
        """Test port definition with maximum 10 branches."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 10})

        for i in range(1, 11):
            assert f"branch_{i}" in node.output_ports


class TestForkNodePairing:
    """Tests for Fork-Join pairing."""

    def test_set_paired_join(self):
        """Test setting paired JoinNode."""
        node = ForkNode(node_id="fork_1")
        node.set_paired_join("join_1")

        assert node.paired_join_id == "join_1"
        assert node.config.get("paired_join_id") == "join_1"

    def test_set_paired_join_updates_config(self):
        """Test that pairing updates both attribute and config."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 3})
        node.set_paired_join("join_abc")

        # Both should be updated
        assert node.paired_join_id == "join_abc"
        assert node.config["paired_join_id"] == "join_abc"
        # Original config preserved
        assert node.config["branch_count"] == 3


class TestForkNodeExecuteSuccess:
    """Tests for ForkNode execute - SUCCESS scenarios."""

    @pytest.mark.asyncio
    async def test_execute_returns_parallel_branches(self, execution_context):
        """Test that execute returns parallel_branches for executor."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 3})
        node.set_paired_join("join_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "parallel_branches" in result
        assert result["parallel_branches"] == ["branch_1", "branch_2", "branch_3"]
        assert result["fork_id"] == "fork_1"
        assert result["paired_join_id"] == "join_1"
        assert result["fail_fast"] is False
        assert result["next_nodes"] == []
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_execute_with_fail_fast(self, execution_context):
        """Test that fail_fast parameter is passed in result."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 2, "fail_fast": True})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["fail_fast"] is True

    @pytest.mark.asyncio
    async def test_execute_returns_data_dict(self, execution_context):
        """Test that execute returns proper data dict."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 4})

        result = await node.execute(execution_context)

        assert result["data"]["branch_count"] == 4
        assert result["data"]["branches"] == [
            "branch_1",
            "branch_2",
            "branch_3",
            "branch_4",
        ]

    @pytest.mark.asyncio
    async def test_execute_sets_running_then_success_status(self, execution_context):
        """Test that status transitions correctly during execution."""
        node = ForkNode(node_id="fork_1")
        assert node.status == NodeStatus.IDLE

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS


class TestForkNodeExecuteError:
    """Tests for ForkNode execute - ERROR scenarios."""

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, execution_context):
        """Test that execute handles exceptions gracefully."""
        node = ForkNode(node_id="fork_1")

        # Mock get_parameter to raise exception
        with patch.object(
            node, "get_parameter", side_effect=RuntimeError("Config error")
        ):
            result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
        assert "Config error" in result["error"]
        assert result["next_nodes"] == []
        assert node.status == NodeStatus.ERROR


# =============================================================================
# JoinNode Tests
# =============================================================================


class TestJoinNodeInit:
    """Tests for JoinNode initialization."""

    def test_init_default_config(self):
        """Test JoinNode initialization with default config."""
        node = JoinNode(node_id="join_1")

        assert node.node_id == "join_1"
        assert node.name == "Join"
        assert node.node_type == "JoinNode"
        assert node.paired_fork_id == ""

    def test_init_with_merge_strategy(self):
        """Test JoinNode with custom merge strategy."""
        node = JoinNode(node_id="join_1", config={"merge_strategy": "first"})

        assert node.get_parameter("merge_strategy", "all") == "first"


class TestJoinNodePorts:
    """Tests for JoinNode port definitions."""

    def test_ports_defined_correctly(self):
        """Test that all required ports are defined."""
        node = JoinNode(node_id="join_1")

        # Input port - PortType.INPUT is used for all input ports by add_input_port
        assert "exec_in" in node.input_ports
        assert node.input_ports["exec_in"].port_type == PortType.INPUT

        # Output ports - verify they exist
        # Note: JoinNode uses PortType values in add_output_port where DataType is expected
        # This is an implementation quirk we're documenting with this test
        assert "exec_out" in node.output_ports
        assert node.output_ports["exec_out"].port_type == PortType.OUTPUT

        assert "results" in node.output_ports
        assert node.output_ports["results"].port_type == PortType.OUTPUT

        assert "branch_count" in node.output_ports
        assert node.output_ports["branch_count"].port_type == PortType.OUTPUT


class TestJoinNodePairing:
    """Tests for Fork-Join pairing from Join side."""

    def test_set_paired_fork(self):
        """Test setting paired ForkNode."""
        node = JoinNode(node_id="join_1")
        node.set_paired_fork("fork_1")

        assert node.paired_fork_id == "fork_1"
        assert node.config.get("paired_fork_id") == "fork_1"


class TestJoinNodeExecuteSuccess:
    """Tests for JoinNode execute - SUCCESS scenarios."""

    @pytest.mark.asyncio
    async def test_execute_merges_branch_results(self, execution_context):
        """Test that execute merges branch results correctly."""
        node = JoinNode(node_id="join_1", config={"paired_fork_id": "fork_1"})
        node.set_paired_fork("fork_1")

        # Simulate branch results stored by executor
        execution_context.set_variable(
            "fork_1_branch_results",
            {
                "branch_1": {"result_a": "value_a", "count": 10},
                "branch_2": {"result_b": "value_b", "count": 20},
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["branch_count"] == 2
        assert result["next_nodes"] == ["exec_out"]
        assert node.status == NodeStatus.SUCCESS

        # Check that results are output
        assert node.get_output_value("branch_count") == 2
        results_output = node.get_output_value("results")
        assert "branch_1" in results_output
        assert "branch_2" in results_output

        # Check that branch results are cleaned up
        assert not execution_context.has_variable("fork_1_branch_results")

    @pytest.mark.asyncio
    async def test_execute_with_merge_strategy_first(self, execution_context):
        """Test merge strategy 'first' keeps only first branch."""
        node = JoinNode(
            node_id="join_1",
            config={"paired_fork_id": "fork_1", "merge_strategy": "first"},
        )
        node.set_paired_fork("fork_1")

        execution_context.set_variable(
            "fork_1_branch_results",
            {
                "branch_1": {"data": "first"},
                "branch_2": {"data": "second"},
                "branch_3": {"data": "third"},
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["merge_strategy"] == "first"
        # Results should only contain first branch
        results = node.get_output_value("results")
        assert len(results) == 1
        assert "branch_1" in results

    @pytest.mark.asyncio
    async def test_execute_with_merge_strategy_last(self, execution_context):
        """Test merge strategy 'last' keeps only last branch."""
        node = JoinNode(
            node_id="join_1",
            config={"paired_fork_id": "fork_1", "merge_strategy": "last"},
        )
        node.set_paired_fork("fork_1")

        execution_context.set_variable(
            "fork_1_branch_results",
            {
                "branch_1": {"data": "first"},
                "branch_2": {"data": "second"},
                "branch_3": {"data": "third"},
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["merge_strategy"] == "last"
        # Results should only contain last branch
        results = node.get_output_value("results")
        assert len(results) == 1
        assert "branch_3" in results

    @pytest.mark.asyncio
    async def test_execute_with_merge_strategy_all(self, execution_context):
        """Test merge strategy 'all' keeps all branches (default)."""
        node = JoinNode(
            node_id="join_1",
            config={"paired_fork_id": "fork_1", "merge_strategy": "all"},
        )
        node.set_paired_fork("fork_1")

        execution_context.set_variable(
            "fork_1_branch_results",
            {
                "branch_1": {"data": "first"},
                "branch_2": {"data": "second"},
            },
        )

        result = await node.execute(execution_context)

        results = node.get_output_value("results")
        assert len(results) == 2
        assert "branch_1" in results
        assert "branch_2" in results

    @pytest.mark.asyncio
    async def test_execute_uses_paired_fork_from_attribute(self, execution_context):
        """Test that paired_fork_id attribute takes precedence."""
        node = JoinNode(node_id="join_1")
        node.set_paired_fork("fork_attr")

        execution_context.set_variable(
            "fork_attr_branch_results",
            {"branch_1": {"key": "value"}},
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["branch_count"] == 1

    @pytest.mark.asyncio
    async def test_execute_uses_paired_fork_from_config_fallback(
        self, execution_context
    ):
        """Test that config is used when attribute is empty."""
        node = JoinNode(node_id="join_1", config={"paired_fork_id": "fork_cfg"})
        # Don't set via set_paired_fork - let it use config fallback

        execution_context.set_variable(
            "fork_cfg_branch_results",
            {"branch_1": {"key": "value"}},
        )

        result = await node.execute(execution_context)

        assert result["success"] is True


class TestJoinNodeExecuteEdgeCases:
    """Tests for JoinNode execute - EDGE CASES."""

    @pytest.mark.asyncio
    async def test_execute_empty_branches(self, execution_context):
        """Test execution with no branch results."""
        node = JoinNode(node_id="join_1", config={"paired_fork_id": "fork_1"})
        node.set_paired_fork("fork_1")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["branch_count"] == 0
        assert node.get_output_value("branch_count") == 0
        assert node.get_output_value("results") == {}

    @pytest.mark.asyncio
    async def test_execute_merge_first_with_empty_results(self, execution_context):
        """Test merge strategy 'first' with empty branch results."""
        node = JoinNode(
            node_id="join_1",
            config={"paired_fork_id": "fork_1", "merge_strategy": "first"},
        )
        node.set_paired_fork("fork_1")

        # Empty branch results
        execution_context.set_variable("fork_1_branch_results", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("results") == {}

    @pytest.mark.asyncio
    async def test_execute_merge_last_with_empty_results(self, execution_context):
        """Test merge strategy 'last' with empty branch results."""
        node = JoinNode(
            node_id="join_1",
            config={"paired_fork_id": "fork_1", "merge_strategy": "last"},
        )
        node.set_paired_fork("fork_1")

        execution_context.set_variable("fork_1_branch_results", {})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("results") == {}

    @pytest.mark.asyncio
    async def test_execute_merges_non_dict_branch_results(self, execution_context):
        """Test that non-dict branch values don't break merge_branch_results."""
        node = JoinNode(node_id="join_1", config={"paired_fork_id": "fork_1"})
        node.set_paired_fork("fork_1")

        # Branch results with non-dict values (e.g., primitive results)
        execution_context.set_variable(
            "fork_1_branch_results",
            {
                "branch_1": "string_result",  # Not a dict
                "branch_2": 42,  # Not a dict
                "branch_3": {"proper": "dict"},  # Dict
            },
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["branch_count"] == 3


class TestJoinNodeExecuteError:
    """Tests for JoinNode execute - ERROR scenarios."""

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, execution_context):
        """Test that execute handles exceptions gracefully."""
        node = JoinNode(node_id="join_1")
        node.set_paired_fork("fork_1")

        # Mock get_parameter to raise exception
        with patch.object(
            node, "get_parameter", side_effect=RuntimeError("Merge error")
        ):
            result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
        assert "Merge error" in result["error"]
        assert result["next_nodes"] == []
        assert node.status == NodeStatus.ERROR


# =============================================================================
# ParallelForEachNode Tests
# =============================================================================


class TestParallelForEachNodeInit:
    """Tests for ParallelForEachNode initialization."""

    def test_init_default_config(self):
        """Test ParallelForEachNode initialization with default config."""
        node = ParallelForEachNode(node_id="pfe_1")

        assert node.node_id == "pfe_1"
        assert node.name == "Parallel ForEach"
        assert node.node_type == "ParallelForEachNode"

    def test_init_custom_config(self):
        """Test ParallelForEachNode with custom config."""
        node = ParallelForEachNode(
            node_id="pfe_1",
            config={"batch_size": 10, "fail_fast": True, "timeout_per_item": 120},
        )

        assert node.get_parameter("batch_size", 5) == 10
        assert node.get_parameter("fail_fast", False) is True
        assert node.get_parameter("timeout_per_item", 60) == 120


class TestParallelForEachNodePorts:
    """Tests for ParallelForEachNode port definitions."""

    def test_ports_defined_correctly(self):
        """Test that all required ports are defined."""
        node = ParallelForEachNode(node_id="pfe_1")

        # Input ports - PortType.INPUT is used for all input ports
        assert "exec_in" in node.input_ports
        assert "items" in node.input_ports
        # items port exists (implementation uses PortType in data_type position)
        assert node.input_ports["items"].port_type == PortType.INPUT

        # Output ports - verify they exist
        assert "body" in node.output_ports
        assert node.output_ports["body"].port_type == PortType.OUTPUT

        assert "completed" in node.output_ports
        assert node.output_ports["completed"].port_type == PortType.OUTPUT

        assert "current_item" in node.output_ports
        assert node.output_ports["current_item"].port_type == PortType.OUTPUT

        assert "current_index" in node.output_ports
        assert node.output_ports["current_index"].port_type == PortType.OUTPUT

        assert "results" in node.output_ports
        assert node.output_ports["results"].port_type == PortType.OUTPUT


class TestParallelForEachNodeExecuteSuccess:
    """Tests for ParallelForEachNode execute - SUCCESS scenarios."""

    @pytest.mark.asyncio
    async def test_execute_first_call_initializes_state(self, execution_context):
        """Test first execution initializes state."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 2})
        node.set_input_value("items", ["a", "b", "c", "d", "e"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "parallel_foreach_batch" in result
        batch_info = result["parallel_foreach_batch"]
        assert batch_info["items"] == ["a", "b"]
        assert batch_info["indices"] == [0, 1]
        assert batch_info["body_port"] == "body"

        # State should be stored
        state_key = "pfe_1_parallel_foreach"
        assert execution_context.has_variable(state_key)
        state = execution_context.get_variable(state_key)
        assert state["index"] == 2
        assert len(state["items"]) == 5

    @pytest.mark.asyncio
    async def test_execute_subsequent_batches(self, execution_context):
        """Test subsequent batch execution."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 2})
        node.set_input_value("items", ["a", "b", "c", "d", "e"])

        # First batch
        result1 = await node.execute(execution_context)
        assert result1["parallel_foreach_batch"]["items"] == ["a", "b"]

        # Second batch
        result2 = await node.execute(execution_context)
        assert result2["parallel_foreach_batch"]["items"] == ["c", "d"]

        # Third batch (last item)
        result3 = await node.execute(execution_context)
        assert result3["parallel_foreach_batch"]["items"] == ["e"]

    @pytest.mark.asyncio
    async def test_execute_completion(self, execution_context):
        """Test that execute returns 'completed' when all items processed."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 3})
        node.set_input_value("items", ["a", "b"])

        # First batch processes all items
        result1 = await node.execute(execution_context)
        assert "parallel_foreach_batch" in result1

        # Simulate results stored by executor
        state_key = "pfe_1_parallel_foreach"
        state = execution_context.get_variable(state_key)
        state["results"] = ["result_a", "result_b"]
        execution_context.set_variable(state_key, state)

        # Second call should complete
        result2 = await node.execute(execution_context)
        assert result2["success"] is True
        assert result2["next_nodes"] == ["completed"]
        assert result2["data"]["total_items"] == 2
        assert result2["data"]["processed"] == 2

        # State should be cleaned up
        assert not execution_context.has_variable(state_key)

    @pytest.mark.asyncio
    async def test_execute_with_fail_fast(self, execution_context):
        """Test that fail_fast is passed in result."""
        node = ParallelForEachNode(
            node_id="pfe_1", config={"batch_size": 2, "fail_fast": True}
        )
        node.set_input_value("items", ["a", "b", "c"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["fail_fast"] is True
        assert result["timeout_per_item"] == 60  # default

    @pytest.mark.asyncio
    async def test_execute_with_custom_timeout(self, execution_context):
        """Test that custom timeout is passed in result."""
        node = ParallelForEachNode(
            node_id="pfe_1", config={"batch_size": 2, "timeout_per_item": 120}
        )
        node.set_input_value("items", ["a", "b"])

        result = await node.execute(execution_context)

        assert result["timeout_per_item"] == 120

    @pytest.mark.asyncio
    async def test_execute_returns_foreach_id(self, execution_context):
        """Test that foreach_id is returned for executor tracking."""
        node = ParallelForEachNode(node_id="pfe_custom_id")
        node.set_input_value("items", ["x"])

        result = await node.execute(execution_context)

        assert result["foreach_id"] == "pfe_custom_id"

    @pytest.mark.asyncio
    async def test_execute_returns_batch_metadata(self, execution_context):
        """Test that batch metadata is correctly computed."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 3})
        node.set_input_value("items", ["a", "b", "c", "d", "e", "f", "g"])

        result = await node.execute(execution_context)

        assert result["data"]["batch_size"] == 3
        assert result["data"]["batch_start"] == 0
        assert result["data"]["batch_end"] == 3
        assert result["data"]["remaining"] == 4  # 7 - 3 = 4 remaining


class TestParallelForEachNodeExecuteEdgeCases:
    """Tests for ParallelForEachNode execute - EDGE CASES."""

    @pytest.mark.asyncio
    async def test_execute_empty_list(self, execution_context):
        """Test execution with empty items list."""
        node = ParallelForEachNode(node_id="pfe_1")
        node.set_input_value("items", [])

        # First call initializes with empty list
        result1 = await node.execute(execution_context)

        # Should immediately go to completion on second call
        result2 = await node.execute(execution_context)

        assert result2["success"] is True
        assert result2["next_nodes"] == ["completed"]
        assert result2["data"]["total_items"] == 0

    @pytest.mark.asyncio
    async def test_execute_single_item_converted_to_list(self, execution_context):
        """Test that single item is converted to list."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 5})
        node.set_input_value("items", "single_value")

        result = await node.execute(execution_context)

        assert result["success"] is True
        batch_info = result["parallel_foreach_batch"]
        assert batch_info["items"] == ["single_value"]

    @pytest.mark.asyncio
    async def test_execute_tuple_converted_to_list(self, execution_context):
        """Test that tuple input is converted to list."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 2})
        node.set_input_value("items", ("x", "y", "z"))

        result = await node.execute(execution_context)

        assert result["success"] is True
        batch_info = result["parallel_foreach_batch"]
        assert batch_info["items"] == ["x", "y"]
        assert batch_info["indices"] == [0, 1]

    @pytest.mark.asyncio
    async def test_execute_none_items_treated_as_empty(self, execution_context):
        """Test that None items input is treated as empty list."""
        node = ParallelForEachNode(node_id="pfe_1")
        node.set_input_value("items", None)

        # First call initializes
        result1 = await node.execute(execution_context)

        # Second call completes (empty list)
        result2 = await node.execute(execution_context)

        assert result2["success"] is True
        assert result2["next_nodes"] == ["completed"]
        assert result2["data"]["total_items"] == 0

    @pytest.mark.asyncio
    async def test_execute_batch_larger_than_items(self, execution_context):
        """Test when batch_size > number of items."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 10})
        node.set_input_value("items", ["a", "b", "c"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        batch_info = result["parallel_foreach_batch"]
        assert batch_info["items"] == ["a", "b", "c"]
        assert len(batch_info["items"]) == 3  # All items in one batch

    @pytest.mark.asyncio
    async def test_execute_preserves_errors_in_state(self, execution_context):
        """Test that errors are tracked in state."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 2})
        node.set_input_value("items", ["a", "b", "c"])

        # First batch
        await node.execute(execution_context)

        # Simulate executor adding errors
        state_key = "pfe_1_parallel_foreach"
        state = execution_context.get_variable(state_key)
        state["errors"] = ["Error in item 0", "Error in item 1"]
        state["results"] = ["result_a", None]
        execution_context.set_variable(state_key, state)

        # Process remaining batch
        await node.execute(execution_context)

        # Update state again
        state = execution_context.get_variable(state_key)
        state["results"].append("result_c")
        execution_context.set_variable(state_key, state)

        # Completion
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["errors"] == 2

    @pytest.mark.asyncio
    async def test_execute_outputs_results_on_completion(self, execution_context):
        """Test that results output is set on completion."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 5})
        node.set_input_value("items", ["x", "y"])

        # First call
        await node.execute(execution_context)

        # Simulate results
        state_key = "pfe_1_parallel_foreach"
        state = execution_context.get_variable(state_key)
        state["results"] = ["processed_x", "processed_y"]
        execution_context.set_variable(state_key, state)

        # Completion call
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("results") == ["processed_x", "processed_y"]


class TestParallelForEachNodeExecuteError:
    """Tests for ParallelForEachNode execute - ERROR scenarios."""

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, execution_context):
        """Test that execute handles exceptions gracefully."""
        node = ParallelForEachNode(node_id="pfe_1")
        node.set_input_value("items", ["a", "b"])

        # Mock get_parameter to raise on second call
        original_get_param = node.get_parameter
        call_count = [0]

        def mock_get_param(name, default=None):
            call_count[0] += 1
            if call_count[0] > 2:
                raise RuntimeError("Parameter error")
            return original_get_param(name, default)

        with patch.object(node, "get_parameter", side_effect=mock_get_param):
            result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
        assert result["next_nodes"] == []
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_execute_cleans_up_state_on_error(self, execution_context):
        """Test that state is cleaned up when exception occurs."""
        node = ParallelForEachNode(node_id="pfe_error")
        node.set_input_value("items", ["a", "b"])

        # First call to initialize state
        await node.execute(execution_context)
        state_key = "pfe_error_parallel_foreach"
        assert execution_context.has_variable(state_key)

        # Force an error on second call
        with patch.object(
            node, "get_parameter", side_effect=RuntimeError("Forced error")
        ):
            result = await node.execute(execution_context)

        assert result["success"] is False
        # State should be cleaned up
        assert not execution_context.has_variable(state_key)


# =============================================================================
# ExecutionContext Cloning Tests
# =============================================================================


class TestExecutionContextCloning:
    """Tests for ExecutionContext cloning for parallel execution."""

    def test_clone_for_branch_creates_isolated_context(self, execution_context):
        """Test that clone_for_branch creates isolated variable context."""
        execution_context.set_variable("shared_var", "original_value")
        execution_context.set_variable("counter", 0)

        branch_context = execution_context.clone_for_branch("branch_1")

        # Branch should have copied variables
        assert branch_context.get_variable("shared_var") == "original_value"
        assert branch_context.get_variable("counter") == 0

        # Modifying branch should not affect original
        branch_context.set_variable("shared_var", "modified_in_branch")
        branch_context.set_variable("new_var", "branch_only")

        assert execution_context.get_variable("shared_var") == "original_value"
        assert not execution_context.has_variable("new_var")

    def test_clone_for_branch_sets_branch_name(self, execution_context):
        """Test that cloned context has branch name variable."""
        branch_context = execution_context.clone_for_branch("branch_a")

        assert branch_context.get_variable("_branch_name") == "branch_a"

    def test_clone_for_branch_shares_resources(self, execution_context):
        """Test that cloned context shares browser resources reference."""
        # Set up mock browser on original context
        mock_browser = MagicMock()
        execution_context.set_browser(mock_browser)

        branch_context = execution_context.clone_for_branch("branch_1")

        # Branch should share the same resources manager (read-only access)
        assert branch_context._resources is execution_context._resources
        assert branch_context.browser is mock_browser

    def test_clone_for_branch_preserves_workflow_name(self, execution_context):
        """Test that cloned context has namespaced workflow name."""
        branch_context = execution_context.clone_for_branch("branch_x")

        assert "branch_x" in branch_context.workflow_name
        assert "::" in branch_context.workflow_name

    def test_clone_for_branch_shares_pause_event(self, execution_context):
        """Test that cloned context shares pause event for coordination."""
        branch_context = execution_context.clone_for_branch("branch_1")

        assert branch_context.pause_event is execution_context.pause_event

    def test_merge_branch_results(self, execution_context):
        """Test merging branch results back to main context."""
        branch_vars = {
            "result": "success",
            "data": {"key": "value"},
            "_internal": "should_skip",
        }

        execution_context.merge_branch_results("branch_1", branch_vars)

        # Check namespaced variables were merged
        assert execution_context.get_variable("branch_1_result") == "success"
        assert execution_context.get_variable("branch_1_data") == {"key": "value"}

        # Internal variables should not be merged
        assert not execution_context.has_variable("branch_1__internal")

    def test_merge_branch_results_multiple_branches(self, execution_context):
        """Test merging results from multiple branches."""
        execution_context.merge_branch_results("branch_1", {"count": 10})
        execution_context.merge_branch_results("branch_2", {"count": 20})
        execution_context.merge_branch_results("branch_3", {"count": 30})

        assert execution_context.get_variable("branch_1_count") == 10
        assert execution_context.get_variable("branch_2_count") == 20
        assert execution_context.get_variable("branch_3_count") == 30


# =============================================================================
# Node Validation Tests
# =============================================================================


class TestNodeValidation:
    """Tests for node validation."""

    def test_fork_node_validate(self):
        """Test ForkNode validation."""
        node = ForkNode(node_id="fork_1", config={"branch_count": 2})
        is_valid, error = node.validate()
        assert is_valid is True
        assert error is None

    def test_join_node_validate(self):
        """Test JoinNode validation."""
        node = JoinNode(node_id="join_1")
        is_valid, error = node.validate()
        assert is_valid is True
        assert error is None

    def test_parallel_foreach_node_validate(self):
        """Test ParallelForEachNode validation."""
        node = ParallelForEachNode(node_id="pfe_1")
        # Set required input to pass validation
        node.set_input_value("items", ["a", "b", "c"])
        is_valid, error = node.validate()
        assert is_valid is True
        assert error is None

    def test_parallel_foreach_node_validate_fails_without_items(self):
        """Test ParallelForEachNode validation fails without items."""
        node = ParallelForEachNode(node_id="pfe_1")
        is_valid, error = node.validate()
        # Validation should fail because 'items' is required
        assert is_valid is False
        assert error is not None


# =============================================================================
# Integration Scenarios
# =============================================================================


class TestParallelExecutionScenarios:
    """Integration-style tests for parallel execution scenarios."""

    @pytest.mark.asyncio
    async def test_fork_join_workflow_simulation(self, execution_context):
        """Simulate a complete Fork-Join workflow."""
        # Create Fork node
        fork = ForkNode(node_id="fork_1", config={"branch_count": 3})
        join = JoinNode(node_id="join_1")

        # Pair them
        fork.set_paired_join("join_1")
        join.set_paired_fork("fork_1")

        # Execute fork
        fork_result = await fork.execute(execution_context)
        assert fork_result["success"] is True
        assert fork_result["parallel_branches"] == ["branch_1", "branch_2", "branch_3"]

        # Simulate executor running branches and storing results
        execution_context.set_variable(
            "fork_1_branch_results",
            {
                "branch_1": {"processed": "data_a", "time": 100},
                "branch_2": {"processed": "data_b", "time": 150},
                "branch_3": {"processed": "data_c", "time": 120},
            },
        )

        # Execute join
        join_result = await join.execute(execution_context)
        assert join_result["success"] is True
        assert join_result["data"]["branch_count"] == 3
        assert join_result["next_nodes"] == ["exec_out"]

    @pytest.mark.asyncio
    async def test_parallel_foreach_full_iteration(self, execution_context):
        """Test complete ParallelForEach iteration through all items."""
        node = ParallelForEachNode(node_id="pfe_1", config={"batch_size": 2})
        items = ["url1", "url2", "url3", "url4", "url5"]
        node.set_input_value("items", items)

        processed_batches = []
        iteration = 0
        max_iterations = 10  # Safety limit

        while iteration < max_iterations:
            iteration += 1
            result = await node.execute(execution_context)

            if "parallel_foreach_batch" in result:
                batch = result["parallel_foreach_batch"]
                processed_batches.append(batch["items"])

                # Simulate executor adding results
                state_key = batch["state_key"]
                state = execution_context.get_variable(state_key)
                for item in batch["items"]:
                    state["results"].append(f"processed_{item}")
                execution_context.set_variable(state_key, state)

            elif result["next_nodes"] == ["completed"]:
                break

        # Verify all items were processed in correct batches
        assert processed_batches == [
            ["url1", "url2"],
            ["url3", "url4"],
            ["url5"],
        ]
        assert iteration < max_iterations  # Ensure we didn't hit safety limit

    @pytest.mark.asyncio
    async def test_nested_parallel_execution_ids(self, execution_context):
        """Test that nested parallel executions have unique state keys."""
        # Outer parallel foreach
        outer = ParallelForEachNode(node_id="outer_pfe", config={"batch_size": 2})
        outer.set_input_value("items", ["a", "b"])

        # Inner parallel foreach (would run inside outer's body)
        inner = ParallelForEachNode(node_id="inner_pfe", config={"batch_size": 1})
        inner.set_input_value("items", ["x", "y"])

        # Execute both
        outer_result = await outer.execute(execution_context)
        inner_result = await inner.execute(execution_context)

        # Verify they use different state keys
        assert execution_context.has_variable("outer_pfe_parallel_foreach")
        assert execution_context.has_variable("inner_pfe_parallel_foreach")

        # States should be independent
        outer_state = execution_context.get_variable("outer_pfe_parallel_foreach")
        inner_state = execution_context.get_variable("inner_pfe_parallel_foreach")
        assert outer_state["items"] == ["a", "b"]
        assert inner_state["items"] == ["x", "y"]

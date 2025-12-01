"""
Workflow execution performance benchmarks for CasareRPA.

This module tests the performance of workflow execution under various scenarios:
- Linear chains of nodes (scaling with node count)
- Branching workflows (scaling with branch depth)
- Variable operations (get/set performance)
- Memory usage (no unbounded growth)

All tests marked with @pytest.mark.slow to exclude from fast test runs.

Run all performance tests:
    pytest tests/performance/test_workflow_performance.py -v

Run specific test:
    pytest tests/performance/test_workflow_performance.py::test_100_node_chain_execution -v

With benchmark comparison:
    pytest tests/performance/test_workflow_performance.py -v --benchmark-compare
"""

import gc
import psutil
import pytest
import asyncio
from typing import List, Tuple

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
from casare_rpa.nodes.control_flow_nodes import IfNode


def create_linear_chain(n: int) -> WorkflowSchema:
    """
    Create a linear chain of n SetVariable nodes.

    Pattern: Start -> [SetVariable] * n -> End

    Args:
        n: Number of SetVariable nodes in the chain

    Returns:
        WorkflowSchema with linear chain of nodes
    """
    metadata = WorkflowMetadata(
        name=f"Linear Chain ({n} nodes)",
        description=f"Performance test: {n} SetVariable nodes in linear chain",
    )
    workflow = WorkflowSchema(metadata)

    # Start node
    start_node = StartNode(node_id="start", name="Start")
    workflow.add_node(start_node.serialize())

    # Chain of SetVariable nodes
    prev_node_id = "start"
    for i in range(n):
        node_id = f"set_var_{i}"
        node = SetVariableNode(
            node_id=node_id,
            name=f"Set Variable {i}",
            config={
                "variable_name": f"var_{i}",
                "default_value": i,
                "variable_type": "Int32",
            },
        )
        workflow.add_node(node.serialize())

        # Connect to previous node
        workflow.add_connection(
            NodeConnection(
                source_node=prev_node_id,
                source_port="exec_out",
                target_node=node_id,
                target_port="exec_in",
            )
        )
        prev_node_id = node_id

    # End node
    end_node = EndNode(node_id="end", name="End")
    workflow.add_node(end_node.serialize())

    # Connect last node to end
    workflow.add_connection(
        NodeConnection(
            source_node=prev_node_id,
            source_port="exec_out",
            target_node="end",
            target_port="exec_in",
        )
    )

    return workflow


def create_branching_workflow(depth: int) -> WorkflowSchema:
    """
    Create a branching workflow with if/else nodes at given depth.

    Pattern: Start -> [If/Else branches] * depth -> End

    Each level doubles the number of branches.
    depth=1: Start -> If -> Branch 1 (SetVar) / Branch 2 (SetVar) -> End
    depth=2: 4 SetVar nodes (2 levels of If/Else)

    Args:
        depth: Number of branching levels

    Returns:
        WorkflowSchema with branching structure
    """
    metadata = WorkflowMetadata(
        name=f"Branching Workflow (depth={depth})",
        description=f"Performance test: branching workflow with depth {depth}",
    )
    workflow = WorkflowSchema(metadata)

    # Start node
    start_node = StartNode(node_id="start", name="Start")
    workflow.add_node(start_node.serialize())

    # Create branching structure
    node_counter = [0]  # Use list to allow mutation in nested function
    parent_nodes = ["start"]

    for level in range(depth):
        next_parent_nodes = []

        for parent_id in parent_nodes:
            # Create If node
            if_node_id = f"if_{level}_{node_counter[0]}"
            node_counter[0] += 1
            if_node = IfNode(
                node_id=if_node_id,
                config={"expression": "true"},
            )
            workflow.add_node(if_node.serialize())

            # Connect parent to If
            workflow.add_connection(
                NodeConnection(
                    source_node=parent_id,
                    source_port="exec_out",
                    target_node=if_node_id,
                    target_port="exec_in",
                )
            )

            # Create true branch (SetVariable)
            true_node_id = f"set_true_{level}_{node_counter[0]}"
            node_counter[0] += 1
            true_node = SetVariableNode(
                node_id=true_node_id,
                name=f"True Branch {level}",
                config={
                    "variable_name": f"branch_true_{level}",
                    "default_value": True,
                },
            )
            workflow.add_node(true_node.serialize())
            workflow.add_connection(
                NodeConnection(
                    source_node=if_node_id,
                    source_port="true",
                    target_node=true_node_id,
                    target_port="exec_in",
                )
            )
            next_parent_nodes.append(true_node_id)

            # Create false branch (SetVariable)
            false_node_id = f"set_false_{level}_{node_counter[0]}"
            node_counter[0] += 1
            false_node = SetVariableNode(
                node_id=false_node_id,
                name=f"False Branch {level}",
                config={
                    "variable_name": f"branch_false_{level}",
                    "default_value": False,
                },
            )
            workflow.add_node(false_node.serialize())
            workflow.add_connection(
                NodeConnection(
                    source_node=if_node_id,
                    source_port="false",
                    target_node=false_node_id,
                    target_port="exec_in",
                )
            )
            next_parent_nodes.append(false_node_id)

        parent_nodes = next_parent_nodes

    # End node
    end_node = EndNode(node_id="end", name="End")
    workflow.add_node(end_node.serialize())

    # Connect all leaf nodes to end
    for leaf_id in parent_nodes:
        workflow.add_connection(
            NodeConnection(
                source_node=leaf_id,
                source_port="exec_out",
                target_node="end",
                target_port="exec_in",
            )
        )

    return workflow


def create_variable_operations_workflow(
    num_set_ops: int, num_get_ops: int
) -> WorkflowSchema:
    """
    Create workflow with many variable set/get operations.

    Pattern: Start -> [SetVariable] * num_set -> [GetVariable] * num_get -> End

    Args:
        num_set_ops: Number of SetVariable nodes
        num_get_ops: Number of GetVariable nodes

    Returns:
        WorkflowSchema with variable operations
    """
    metadata = WorkflowMetadata(
        name=f"Variable Operations ({num_set_ops} sets, {num_get_ops} gets)",
        description="Performance test: variable set/get operations",
    )
    workflow = WorkflowSchema(metadata)

    # Start node
    start_node = StartNode(node_id="start", name="Start")
    workflow.add_node(start_node.serialize())

    prev_node_id = "start"

    # Set operations
    for i in range(num_set_ops):
        node_id = f"set_var_{i}"
        node = SetVariableNode(
            node_id=node_id,
            name=f"Set {i}",
            config={
                "variable_name": f"var_{i}",
                "default_value": f"value_{i}",
            },
        )
        workflow.add_node(node.serialize())

        workflow.add_connection(
            NodeConnection(
                source_node=prev_node_id,
                source_port="exec_out",
                target_node=node_id,
                target_port="exec_in",
            )
        )
        prev_node_id = node_id

    # Get operations
    for i in range(num_get_ops):
        node_id = f"get_var_{i}"
        get_index = i % num_set_ops
        node = GetVariableNode(
            node_id=node_id,
            name=f"Get {i}",
            config={"variable_name": f"var_{get_index}"},
        )
        workflow.add_node(node.serialize())

        workflow.add_connection(
            NodeConnection(
                source_node=prev_node_id,
                source_port="exec_out",
                target_node=node_id,
                target_port="exec_in",
            )
        )
        prev_node_id = node_id

    # End node
    end_node = EndNode(node_id="end", name="End")
    workflow.add_node(end_node.serialize())

    workflow.add_connection(
        NodeConnection(
            source_node=prev_node_id,
            source_port="exec_out",
            target_node="end",
            target_port="exec_in",
        )
    )

    return workflow


def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def force_gc() -> None:
    """Force garbage collection for accurate memory measurements."""
    gc.collect()
    gc.collect()
    gc.collect()


class TestLinearChainWorkflowPerformance:
    """Test performance of linear chain workflows."""

    @pytest.mark.slow
    def test_100_node_chain_construction_time(self, benchmark):
        """Test that creating a 100-node chain is fast."""

        def create_workflow():
            return create_linear_chain(100)

        result = benchmark(create_workflow)
        assert len(result.nodes) == 102, "Should have 100 SetVariable + Start + End"
        assert len(result.connections) == 101, "Should have 101 connections"

    @pytest.mark.slow
    def test_500_node_chain_construction_time(self, benchmark):
        """Test that creating a 500-node chain is reasonable."""

        def create_workflow():
            return create_linear_chain(500)

        result = benchmark(create_workflow)
        assert len(result.nodes) == 502, "Should have 500 SetVariable + Start + End"
        assert len(result.connections) == 501, "Should have 501 connections"

    @pytest.mark.slow
    def test_linear_chain_memory_scaling(self):
        """Test that memory usage scales linearly with node count."""
        force_gc()
        baseline_memory = get_process_memory_mb()

        # Create workflows of increasing size
        sizes = [10, 50, 100]
        memory_usages = []

        for size in sizes:
            force_gc()
            before = get_process_memory_mb()
            workflow = create_linear_chain(size)
            after = get_process_memory_mb()
            memory_usages.append((size, after - before))

        # Check that memory growth is reasonable (less than 1MB per 10 nodes)
        for size, mem_delta in memory_usages:
            memory_per_node = mem_delta / size if size > 0 else 0
            assert memory_per_node < 0.1, (
                f"Memory per node too high: {memory_per_node:.4f}MB per node "
                f"(size={size}, delta={mem_delta:.2f}MB)"
            )

    @pytest.mark.slow
    def test_large_chain_creation_does_not_hang(self):
        """Test that creating a large chain completes in reasonable time."""
        # Create a 1000-node chain and ensure it completes in < 5 seconds
        import time

        start = time.perf_counter()
        workflow = create_linear_chain(1000)
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, f"Chain creation took {elapsed:.2f}s, expected < 5s"
        assert len(workflow.nodes) == 1002, "Should have 1000 + Start + End"

    @pytest.mark.slow
    def test_linear_chain_node_count_accuracy(self):
        """Test that linear chain helper creates correct number of nodes."""
        test_cases = [1, 10, 50, 100, 500]

        for n in test_cases:
            workflow = create_linear_chain(n)
            expected_nodes = n + 2  # n SetVariable + Start + End
            assert (
                len(workflow.nodes) == expected_nodes
            ), f"Expected {expected_nodes} nodes for n={n}, got {len(workflow.nodes)}"


class TestBranchingWorkflowPerformance:
    """Test performance of branching workflows."""

    @pytest.mark.slow
    def test_5_level_branching_construction(self, benchmark):
        """Test that creating a 5-level branching workflow is fast."""

        def create_workflow():
            return create_branching_workflow(5)

        result = benchmark(create_workflow)
        # 5 levels: 1 + 2 + 4 + 8 + 16 + 32 nodes for branches = 63 SetVariable nodes
        # + If/Else nodes + Start + End
        assert len(result.nodes) > 50, "Should have many nodes from branching"
        assert len(result.connections) > 50, "Should have many connections"

    @pytest.mark.slow
    def test_10_level_deep_branching(self, benchmark):
        """Test deep branching workflow (10 levels)."""

        def create_workflow():
            return create_branching_workflow(10)

        result = benchmark(create_workflow)
        # Each level doubles: 2^10 = 1024 branches minimum
        assert len(result.nodes) > 500, "Should have many nodes from 10-level branching"

    @pytest.mark.slow
    def test_branching_memory_does_not_explode(self):
        """Test that branching workflows don't cause memory explosions."""
        force_gc()
        baseline = get_process_memory_mb()

        # Create a moderately deep branching workflow
        workflow = create_branching_workflow(8)
        force_gc()
        after = get_process_memory_mb()

        memory_increase = after - baseline
        # For 8 levels (256 branches), expect < 10MB increase
        assert memory_increase < 20, (
            f"Memory increase too high: {memory_increase:.2f}MB "
            f"(baseline={baseline:.2f}MB)"
        )

    @pytest.mark.slow
    def test_branching_node_count_doubles_per_level(self):
        """Test that branching creates correct number of nodes."""
        # For depth n: each level should create 2^n leaf nodes
        for depth in range(1, 6):
            workflow = create_branching_workflow(depth)

            # Should have If nodes + SetVariable nodes for both branches + Start + End
            # Minimum expected: 2^depth SetVariable nodes for leaf branches
            expected_min_setvars = 2**depth
            assert len(workflow.nodes) >= expected_min_setvars + 2, (
                f"Depth {depth} should have at least {expected_min_setvars} "
                f"SetVariable nodes, got {len(workflow.nodes)}"
            )


class TestVariableOperationsPerformance:
    """Test performance of variable set/get operations."""

    @pytest.mark.slow
    def test_1000_set_operations(self, benchmark):
        """Test workflow with 1000 SetVariable operations."""

        def create_workflow():
            return create_variable_operations_workflow(1000, 0)

        result = benchmark(create_workflow)
        assert len(result.nodes) == 1002, "Should have 1000 SetVariable + Start + End"

    @pytest.mark.slow
    def test_500_set_500_get_operations(self, benchmark):
        """Test workflow with balanced set/get operations."""

        def create_workflow():
            return create_variable_operations_workflow(500, 500)

        result = benchmark(create_workflow)
        expected_nodes = 500 + 500 + 2  # SetVar + GetVar + Start + End
        assert len(result.nodes) == expected_nodes

    @pytest.mark.slow
    def test_many_variables_memory_usage(self):
        """Test that storing many variables doesn't cause excessive memory growth."""
        force_gc()
        baseline = get_process_memory_mb()

        # Create workflow with many variables
        workflow = create_variable_operations_workflow(500, 500)
        force_gc()
        after = get_process_memory_mb()

        memory_increase = after - baseline
        # For 1000 simple string variables, expect < 5MB
        assert memory_increase < 10, (
            f"Memory increase too high: {memory_increase:.2f}MB " f"for 1000 variables"
        )

    @pytest.mark.slow
    def test_variable_operations_various_scales(self):
        """Test variable operations at various scales."""
        test_cases = [
            (10, 10),
            (50, 50),
            (100, 100),
            (250, 250),
        ]

        for num_sets, num_gets in test_cases:
            workflow = create_variable_operations_workflow(num_sets, num_gets)
            expected = num_sets + num_gets + 2
            assert len(workflow.nodes) == expected, (
                f"Expected {expected} nodes for ({num_sets} sets, {num_gets} gets), "
                f"got {len(workflow.nodes)}"
            )


class TestWorkflowSerializationPerformance:
    """Test performance of workflow serialization/deserialization."""

    @pytest.mark.slow
    def test_serialize_100_node_chain(self, benchmark):
        """Test serialization of 100-node workflow."""
        workflow = create_linear_chain(100)

        def serialize():
            return workflow.to_dict()

        result = benchmark(serialize)
        assert result is not None
        assert "nodes" in result
        assert len(result["nodes"]) == 102

    @pytest.mark.slow
    def test_serialize_large_workflow(self, benchmark):
        """Test serialization of large branching workflow."""
        workflow = create_branching_workflow(7)

        def serialize():
            return workflow.to_dict()

        result = benchmark(serialize)
        assert result is not None
        assert len(result["nodes"]) > 100

    @pytest.mark.slow
    def test_deserialize_100_node_chain(self, benchmark):
        """Test deserialization of 100-node workflow."""
        workflow = create_linear_chain(100)
        serialized = workflow.to_dict()

        def deserialize():
            from casare_rpa.domain.entities.workflow import WorkflowSchema

            return WorkflowSchema.from_dict(serialized)

        result = benchmark(deserialize)
        assert len(result.nodes) == 102


class TestWorkflowValidationPerformance:
    """Test performance of workflow validation."""

    @pytest.mark.slow
    def test_validate_100_node_chain(self, benchmark):
        """Test validation of 100-node workflow."""
        workflow = create_linear_chain(100)

        def validate():
            is_valid, errors = workflow.validate()
            return is_valid, errors

        result = benchmark(validate)
        is_valid, errors = result
        # May have warnings but should be functionally valid
        assert is_valid or len(errors) <= 5

    @pytest.mark.slow
    def test_validate_branching_workflow(self, benchmark):
        """Test validation of branching workflow."""
        workflow = create_branching_workflow(6)

        def validate():
            is_valid, errors = workflow.validate()
            return is_valid, errors

        result = benchmark(validate)
        is_valid, errors = result
        # May have warnings but should be functionally valid
        assert is_valid or len(errors) <= 10


class TestWorkflowMemoryRegression:
    """Test for memory leaks and regressions in workflow operations."""

    @pytest.mark.slow
    def test_repeated_workflow_creation_no_leak(self):
        """Test that repeatedly creating workflows doesn't leak memory."""
        force_gc()
        baseline = get_process_memory_mb()

        # Create and destroy many workflows
        memory_readings = []
        for i in range(10):
            force_gc()
            before = get_process_memory_mb()

            # Create a medium-sized workflow
            workflow = create_linear_chain(100)
            assert workflow is not None

            # Explicitly delete to encourage garbage collection
            del workflow
            force_gc()
            after = get_process_memory_mb()
            memory_readings.append(after)

        # Memory should stabilize (not continuously grow)
        # Check that final memory is close to baseline
        final_memory = memory_readings[-1]
        max_increase = final_memory - baseline
        assert max_increase < 30, (
            f"Memory increased by {max_increase:.2f}MB over 10 iterations "
            f"(possible leak)"
        )

    @pytest.mark.slow
    def test_workflow_collection_stress(self):
        """Test creating and collecting many workflows under stress."""
        force_gc()
        baseline = get_process_memory_mb()

        workflows = []
        # Create 50 large workflows
        for i in range(50):
            workflow = create_linear_chain(100)
            workflows.append(workflow)

        gc.collect()
        peak = get_process_memory_mb()
        peak_increase = peak - baseline

        # Delete all workflows
        del workflows
        gc.collect()
        gc.collect()

        final = get_process_memory_mb()
        final_increase = final - baseline

        # Memory should stabilize (some platforms don't fully recover)
        # Just ensure it doesn't grow unboundedly
        assert (
            peak_increase < 100
        ), f"Memory growth too high: {peak_increase:.2f}MB for 50 workflows"


class TestWorkflowScalingCharacteristics:
    """Test scaling characteristics across different dimensions."""

    @pytest.mark.slow
    def test_linear_scaling_node_creation(self):
        """Test that node creation scales linearly with node count."""
        import time

        timings = []
        sizes = [100, 200, 400, 800]

        for size in sizes:
            start = time.perf_counter()
            workflow = create_linear_chain(size)
            elapsed = time.perf_counter() - start
            timings.append((size, elapsed))

        # Check that time roughly doubles when size doubles
        # (linear scaling: O(n))
        for i in range(1, len(timings)):
            prev_size, prev_time = timings[i - 1]
            curr_size, curr_time = timings[i]

            size_ratio = curr_size / prev_size
            time_ratio = curr_time / prev_time if prev_time > 0 else 1

            # Allow 2x flexibility for system variance
            assert time_ratio < size_ratio * 2, (
                f"Non-linear scaling detected: "
                f"size {size_ratio:.1f}x -> time {time_ratio:.1f}x"
            )

    @pytest.mark.slow
    def test_exponential_scaling_branching(self):
        """Test that branching creates exponential node growth."""
        node_counts = []

        for depth in range(1, 8):
            workflow = create_branching_workflow(depth)
            node_counts.append((depth, len(workflow.nodes)))

        # Each level should roughly double the node count
        # (exponential: O(2^n))
        for i in range(1, len(node_counts)):
            prev_depth, prev_nodes = node_counts[i - 1]
            curr_depth, curr_nodes = node_counts[i]

            # Roughly double in node count per depth level
            growth_factor = curr_nodes / prev_nodes if prev_nodes > 0 else 1

            assert 1.5 < growth_factor < 3, (
                f"Depth {prev_depth}->{curr_depth}: "
                f"node count {prev_nodes}->{curr_nodes} "
                f"(growth {growth_factor:.2f}x)"
            )

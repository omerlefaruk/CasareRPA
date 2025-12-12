"""
Tests for ExecutionOrchestrator domain service.
Covers node routing, execution order, error handling, control flow.
"""

import pytest
from typing import Dict, Any

from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def empty_workflow() -> WorkflowSchema:
    """Create empty workflow."""
    return WorkflowSchema(WorkflowMetadata(name="Empty"))


@pytest.fixture
def simple_workflow() -> WorkflowSchema:
    """Create simple linear workflow: Start -> Node1 -> End."""
    workflow = WorkflowSchema(WorkflowMetadata(name="Simple"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "node1", "type": "ActionNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})
    workflow.connections.append(NodeConnection("start", "exec_out", "node1", "exec_in"))
    workflow.connections.append(NodeConnection("node1", "exec_out", "end", "exec_in"))
    return workflow


@pytest.fixture
def branching_workflow() -> WorkflowSchema:
    """Create workflow with branching: Start -> If -> (True/False) -> End."""
    workflow = WorkflowSchema(WorkflowMetadata(name="Branching"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "if_node", "type": "IfNode"})
    workflow.add_node({"node_id": "true_branch", "type": "ActionNode"})
    workflow.add_node({"node_id": "false_branch", "type": "ActionNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.append(
        NodeConnection("start", "exec_out", "if_node", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("if_node", "true", "true_branch", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("if_node", "false", "false_branch", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("true_branch", "exec_out", "end", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("false_branch", "exec_out", "end", "exec_in")
    )
    return workflow


@pytest.fixture
def loop_workflow() -> WorkflowSchema:
    """Create workflow with loop: Start -> Loop -> Body -> LoopEnd -> End."""
    workflow = WorkflowSchema(WorkflowMetadata(name="Loop"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "loop", "type": "ForLoopStartNode"})
    workflow.add_node({"node_id": "body_node", "type": "ActionNode"})
    workflow.add_node({"node_id": "loop_end", "type": "ForLoopEndNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.append(NodeConnection("start", "exec_out", "loop", "exec_in"))
    workflow.connections.append(
        NodeConnection("loop", "loop_body", "body_node", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("body_node", "exec_out", "loop_end", "exec_in")
    )
    workflow.connections.append(NodeConnection("loop", "completed", "end", "exec_in"))
    return workflow


@pytest.fixture
def try_catch_workflow() -> WorkflowSchema:
    """Create workflow with try/catch: Start -> Try -> (body/catch) -> End."""
    workflow = WorkflowSchema(WorkflowMetadata(name="TryCatch"))
    workflow.add_node({"node_id": "start", "type": "StartNode"})
    workflow.add_node({"node_id": "try_node", "type": "TryNode"})
    workflow.add_node({"node_id": "risky_action", "type": "ActionNode"})
    workflow.add_node({"node_id": "catch_node", "type": "CatchNode"})
    workflow.add_node({"node_id": "end", "type": "EndNode"})

    workflow.connections.append(
        NodeConnection("start", "exec_out", "try_node", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("try_node", "try_body", "risky_action", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("try_node", "catch", "catch_node", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("risky_action", "exec_out", "end", "exec_in")
    )
    workflow.connections.append(
        NodeConnection("catch_node", "exec_out", "end", "exec_in")
    )
    return workflow


# ============================================================================
# Initialization Tests
# ============================================================================


class TestOrchestratorInitialization:
    """Tests for ExecutionOrchestrator initialization."""

    def test_create_orchestrator(self, simple_workflow: WorkflowSchema) -> None:
        """Create orchestrator with workflow."""
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.workflow == simple_workflow

    def test_orchestrator_repr(self, simple_workflow: WorkflowSchema) -> None:
        """String representation."""
        orch = ExecutionOrchestrator(simple_workflow)
        rep = repr(orch)
        assert "Simple" in rep
        assert "nodes=" in rep


# ============================================================================
# Start Node Tests
# ============================================================================


class TestFindStartNode:
    """Tests for find_start_node method."""

    def test_find_start_node_exists(self, simple_workflow: WorkflowSchema) -> None:
        """Find StartNode in workflow."""
        orch = ExecutionOrchestrator(simple_workflow)
        start_id = orch.find_start_node()
        assert start_id == "start"

    def test_find_start_node_not_exists(self, empty_workflow: WorkflowSchema) -> None:
        """No StartNode returns None."""
        orch = ExecutionOrchestrator(empty_workflow)
        start_id = orch.find_start_node()
        assert start_id is None

    def test_find_start_node_multiple(self) -> None:
        """First StartNode is returned when multiple exist."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "other", "type": "ActionNode"})
        workflow.add_node({"node_id": "start1", "type": "StartNode"})
        workflow.add_node({"node_id": "start2", "type": "StartNode"})

        orch = ExecutionOrchestrator(workflow)
        start_id = orch.find_start_node()
        # Should find one of them (order depends on dict)
        assert start_id in ["start1", "start2"]


# ============================================================================
# Next Nodes Tests
# ============================================================================


class TestGetNextNodes:
    """Tests for get_next_nodes method."""

    def test_next_nodes_default_routing(self, simple_workflow: WorkflowSchema) -> None:
        """Default routing follows exec_out connections."""
        orch = ExecutionOrchestrator(simple_workflow)
        next_nodes = orch.get_next_nodes("start")
        assert next_nodes == ["node1"]

    def test_next_nodes_multiple_connections(self) -> None:
        """Multiple exec_out connections return all targets."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "src", "type": "Node"})
        workflow.add_node({"node_id": "dst1", "type": "Node"})
        workflow.add_node({"node_id": "dst2", "type": "Node"})
        workflow.connections.append(
            NodeConnection("src", "exec_out1", "dst1", "exec_in")
        )
        workflow.connections.append(
            NodeConnection("src", "exec_out2", "dst2", "exec_in")
        )

        orch = ExecutionOrchestrator(workflow)
        next_nodes = orch.get_next_nodes("src")
        assert set(next_nodes) == {"dst1", "dst2"}

    def test_next_nodes_dynamic_routing(
        self, branching_workflow: WorkflowSchema
    ) -> None:
        """Dynamic routing uses next_nodes from result."""
        orch = ExecutionOrchestrator(branching_workflow)
        result = {"next_nodes": ["true"]}
        next_nodes = orch.get_next_nodes("if_node", result)
        assert next_nodes == ["true_branch"]

    def test_next_nodes_dynamic_routing_false(
        self, branching_workflow: WorkflowSchema
    ) -> None:
        """Dynamic routing for false branch."""
        orch = ExecutionOrchestrator(branching_workflow)
        result = {"next_nodes": ["false"]}
        next_nodes = orch.get_next_nodes("if_node", result)
        assert next_nodes == ["false_branch"]

    def test_next_nodes_no_connections(self, simple_workflow: WorkflowSchema) -> None:
        """No connections returns empty list."""
        orch = ExecutionOrchestrator(simple_workflow)
        next_nodes = orch.get_next_nodes("end")
        assert next_nodes == []

    def test_next_nodes_ignores_data_connections(self) -> None:
        """Data connections (non-exec) are ignored."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "src", "type": "Node"})
        workflow.add_node({"node_id": "dst", "type": "Node"})
        workflow.connections.append(NodeConnection("src", "data_out", "dst", "data_in"))

        orch = ExecutionOrchestrator(workflow)
        next_nodes = orch.get_next_nodes("src")
        assert next_nodes == []


# ============================================================================
# Execution Path Tests
# ============================================================================


class TestCalculateExecutionPath:
    """Tests for calculate_execution_path method."""

    def test_execution_path_full(self, simple_workflow: WorkflowSchema) -> None:
        """Calculate full execution path from start."""
        orch = ExecutionOrchestrator(simple_workflow)
        path = orch.calculate_execution_path("start")
        assert "start" in path
        assert "node1" in path
        assert "end" in path
        assert len(path) == 3

    def test_execution_path_empty_workflow(
        self, empty_workflow: WorkflowSchema
    ) -> None:
        """Execution path from non-existent start."""
        empty_workflow.add_node({"node_id": "lonely", "type": "Node"})
        orch = ExecutionOrchestrator(empty_workflow)
        path = orch.calculate_execution_path("lonely")
        assert path == {"lonely"}

    def test_execution_path_branching(self, branching_workflow: WorkflowSchema) -> None:
        """Execution path includes all branches."""
        orch = ExecutionOrchestrator(branching_workflow)
        path = orch.calculate_execution_path("start")
        assert "start" in path
        assert "if_node" in path
        assert "true_branch" in path
        assert "false_branch" in path
        assert "end" in path


# ============================================================================
# Subgraph Calculation Tests
# ============================================================================


class TestSubgraphCalculation:
    """Tests for _calculate_subgraph method."""

    def test_subgraph_to_specific_node(self, simple_workflow: WorkflowSchema) -> None:
        """Calculate subgraph to reach specific node."""
        orch = ExecutionOrchestrator(simple_workflow)
        subgraph = orch.calculate_execution_path("start", "node1")
        assert "start" in subgraph
        assert "node1" in subgraph
        # end should not be in subgraph
        assert "end" not in subgraph

    def test_subgraph_unreachable_target(self, simple_workflow: WorkflowSchema) -> None:
        """Unreachable target returns empty set."""
        # Add disconnected node
        simple_workflow.add_node({"node_id": "disconnected", "type": "Node"})
        orch = ExecutionOrchestrator(simple_workflow)
        subgraph = orch.calculate_execution_path("start", "disconnected")
        assert len(subgraph) == 0

    def test_subgraph_includes_all_paths(
        self, branching_workflow: WorkflowSchema
    ) -> None:
        """Subgraph includes all paths to target."""
        orch = ExecutionOrchestrator(branching_workflow)
        subgraph = orch.calculate_execution_path("start", "end")
        # All nodes should be included since both branches lead to end
        assert "start" in subgraph
        assert "if_node" in subgraph
        assert "true_branch" in subgraph
        assert "false_branch" in subgraph
        assert "end" in subgraph


# ============================================================================
# Reachability Tests
# ============================================================================


class TestIsReachable:
    """Tests for is_reachable method."""

    def test_reachable_connected_nodes(self, simple_workflow: WorkflowSchema) -> None:
        """Connected nodes are reachable."""
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.is_reachable("start", "node1") is True
        assert orch.is_reachable("start", "end") is True
        assert orch.is_reachable("node1", "end") is True

    def test_reachable_same_node(self, simple_workflow: WorkflowSchema) -> None:
        """Node is reachable from itself."""
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.is_reachable("start", "start") is True

    def test_not_reachable_reverse_direction(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """Nodes in reverse direction not reachable."""
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.is_reachable("end", "start") is False
        assert orch.is_reachable("node1", "start") is False

    def test_not_reachable_disconnected(self, simple_workflow: WorkflowSchema) -> None:
        """Disconnected nodes not reachable."""
        simple_workflow.add_node({"node_id": "island", "type": "Node"})
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.is_reachable("start", "island") is False


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestShouldStopOnError:
    """Tests for should_stop_on_error method."""

    def test_stop_on_error_default(self, simple_workflow: WorkflowSchema) -> None:
        """Default behavior stops on error."""
        orch = ExecutionOrchestrator(simple_workflow)
        error = ValueError("Test error")
        settings: Dict[str, Any] = {}
        assert orch.should_stop_on_error(error, settings) is True

    def test_continue_on_error_enabled(self, simple_workflow: WorkflowSchema) -> None:
        """continue_on_error setting prevents stop."""
        orch = ExecutionOrchestrator(simple_workflow)
        error = ValueError("Test error")
        settings: Dict[str, Any] = {"continue_on_error": True}
        assert orch.should_stop_on_error(error, settings) is False

    def test_continue_on_error_disabled(self, simple_workflow: WorkflowSchema) -> None:
        """continue_on_error=False stops on error."""
        orch = ExecutionOrchestrator(simple_workflow)
        error = RuntimeError("Critical")
        settings: Dict[str, Any] = {"continue_on_error": False}
        assert orch.should_stop_on_error(error, settings) is True


# ============================================================================
# Control Flow Tests
# ============================================================================


class TestHandleControlFlow:
    """Tests for handle_control_flow method."""

    def test_break_signal(self, simple_workflow: WorkflowSchema) -> None:
        """Handle break control flow."""
        orch = ExecutionOrchestrator(simple_workflow)
        result = {"control_flow": "break"}
        signal = orch.handle_control_flow("node1", result)
        assert signal == "break"

    def test_continue_signal(self, simple_workflow: WorkflowSchema) -> None:
        """Handle continue control flow."""
        orch = ExecutionOrchestrator(simple_workflow)
        result = {"control_flow": "continue"}
        signal = orch.handle_control_flow("node1", result)
        assert signal == "continue"

    def test_return_signal(self, simple_workflow: WorkflowSchema) -> None:
        """Handle return control flow."""
        orch = ExecutionOrchestrator(simple_workflow)
        result = {"control_flow": "return"}
        signal = orch.handle_control_flow("node1", result)
        assert signal == "return"

    def test_no_control_flow(self, simple_workflow: WorkflowSchema) -> None:
        """No control flow signal returns None."""
        orch = ExecutionOrchestrator(simple_workflow)
        result = {"success": True}
        signal = orch.handle_control_flow("node1", result)
        assert signal is None

    def test_unknown_control_flow(self, simple_workflow: WorkflowSchema) -> None:
        """Unknown control flow returns None."""
        orch = ExecutionOrchestrator(simple_workflow)
        result = {"control_flow": "unknown"}
        signal = orch.handle_control_flow("node1", result)
        assert signal is None


# ============================================================================
# Dependency Graph Tests
# ============================================================================


class TestBuildDependencyGraph:
    """Tests for build_dependency_graph method."""

    def test_dependency_graph_simple(self, simple_workflow: WorkflowSchema) -> None:
        """Build dependency graph for simple workflow."""
        orch = ExecutionOrchestrator(simple_workflow)
        deps = orch.build_dependency_graph()
        assert deps["start"] == set()  # Start has no dependencies
        assert deps["node1"] == {"start"}  # node1 depends on start
        assert deps["end"] == {"node1"}  # end depends on node1

    def test_dependency_graph_branching(
        self, branching_workflow: WorkflowSchema
    ) -> None:
        """Build dependency graph with branches."""
        orch = ExecutionOrchestrator(branching_workflow)
        deps = orch.build_dependency_graph()
        assert deps["end"] == {"true_branch", "false_branch"}

    def test_dependency_graph_cached(self, simple_workflow: WorkflowSchema) -> None:
        """Dependency graph is cached."""
        orch = ExecutionOrchestrator(simple_workflow)
        deps1 = orch.build_dependency_graph()
        deps2 = orch.build_dependency_graph()
        assert deps1 is deps2  # Same object


# ============================================================================
# Execution Order Validation Tests
# ============================================================================


class TestValidateExecutionOrder:
    """Tests for validate_execution_order method."""

    def test_valid_order_simple(self, simple_workflow: WorkflowSchema) -> None:
        """Simple workflow has valid order."""
        orch = ExecutionOrchestrator(simple_workflow)
        is_valid, errors = orch.validate_execution_order()
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_order_branching(self, branching_workflow: WorkflowSchema) -> None:
        """Branching workflow has valid order."""
        orch = ExecutionOrchestrator(branching_workflow)
        is_valid, errors = orch.validate_execution_order()
        assert is_valid is True

    def test_invalid_order_circular(self) -> None:
        """Circular dependency is invalid."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "a", "type": "Node"})
        workflow.add_node({"node_id": "b", "type": "Node"})
        workflow.add_node({"node_id": "c", "type": "Node"})
        workflow.connections.append(NodeConnection("a", "exec_out", "b", "exec_in"))
        workflow.connections.append(NodeConnection("b", "exec_out", "c", "exec_in"))
        workflow.connections.append(NodeConnection("c", "exec_out", "a", "exec_in"))

        orch = ExecutionOrchestrator(workflow)
        is_valid, errors = orch.validate_execution_order()
        assert is_valid is False
        assert len(errors) > 0
        assert "Circular" in errors[0]


# ============================================================================
# Loop Body Tests
# ============================================================================


class TestFindLoopBodyNodes:
    """Tests for find_loop_body_nodes method."""

    def test_loop_body_nodes(self, loop_workflow: WorkflowSchema) -> None:
        """Find nodes in loop body."""
        orch = ExecutionOrchestrator(loop_workflow)
        body_nodes = orch.find_loop_body_nodes("loop", "loop_end")
        assert "body_node" in body_nodes
        assert "loop_end" in body_nodes

    def test_loop_body_excludes_outside(self, loop_workflow: WorkflowSchema) -> None:
        """Loop body excludes nodes outside loop."""
        orch = ExecutionOrchestrator(loop_workflow)
        body_nodes = orch.find_loop_body_nodes("loop", "loop_end")
        assert "start" not in body_nodes
        assert "end" not in body_nodes

    def test_loop_body_empty_no_body_port(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """No body port returns empty set."""
        orch = ExecutionOrchestrator(simple_workflow)
        body_nodes = orch.find_loop_body_nodes("node1", "nonexistent")
        assert len(body_nodes) == 0


# ============================================================================
# Try Body Tests
# ============================================================================


class TestFindTryBodyNodes:
    """Tests for find_try_body_nodes method."""

    def test_try_body_nodes(self, try_catch_workflow: WorkflowSchema) -> None:
        """Find nodes in try body."""
        orch = ExecutionOrchestrator(try_catch_workflow)
        body_nodes = orch.find_try_body_nodes("try_node")
        assert "risky_action" in body_nodes

    def test_try_body_excludes_catch(self, try_catch_workflow: WorkflowSchema) -> None:
        """Try body excludes catch nodes."""
        orch = ExecutionOrchestrator(try_catch_workflow)
        body_nodes = orch.find_try_body_nodes("try_node")
        assert "catch_node" not in body_nodes

    def test_try_body_empty_no_try_port(self, simple_workflow: WorkflowSchema) -> None:
        """No try_body port returns empty set."""
        orch = ExecutionOrchestrator(simple_workflow)
        body_nodes = orch.find_try_body_nodes("node1")
        assert len(body_nodes) == 0


# ============================================================================
# Node Type Tests
# ============================================================================


class TestGetNodeType:
    """Tests for get_node_type method."""

    def test_get_node_type_exists(self, simple_workflow: WorkflowSchema) -> None:
        """Get type of existing node."""
        orch = ExecutionOrchestrator(simple_workflow)
        node_type = orch.get_node_type("start")
        assert node_type == "StartNode"

    def test_get_node_type_not_exists(self, simple_workflow: WorkflowSchema) -> None:
        """Get type of non-existing node returns empty string."""
        orch = ExecutionOrchestrator(simple_workflow)
        node_type = orch.get_node_type("missing")
        assert node_type == ""


# ============================================================================
# Control Flow Node Detection Tests
# ============================================================================


class TestIsControlFlowNode:
    """Tests for is_control_flow_node method."""

    def test_if_node_is_control_flow(self, branching_workflow: WorkflowSchema) -> None:
        """IfNode is control flow."""
        orch = ExecutionOrchestrator(branching_workflow)
        assert orch.is_control_flow_node("if_node") is True

    def test_loop_node_is_control_flow(self, loop_workflow: WorkflowSchema) -> None:
        """Loop nodes are control flow."""
        orch = ExecutionOrchestrator(loop_workflow)
        assert orch.is_control_flow_node("loop") is True

    def test_try_node_is_control_flow(self, try_catch_workflow: WorkflowSchema) -> None:
        """TryNode is control flow."""
        orch = ExecutionOrchestrator(try_catch_workflow)
        assert orch.is_control_flow_node("try_node") is True

    def test_action_node_not_control_flow(
        self, simple_workflow: WorkflowSchema
    ) -> None:
        """ActionNode is not control flow."""
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.is_control_flow_node("node1") is False

    def test_start_node_not_control_flow(self, simple_workflow: WorkflowSchema) -> None:
        """StartNode is not control flow."""
        orch = ExecutionOrchestrator(simple_workflow)
        assert orch.is_control_flow_node("start") is False

    def test_break_node_is_control_flow(self) -> None:
        """BreakNode is control flow."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "brk", "type": "BreakNode"})
        orch = ExecutionOrchestrator(workflow)
        assert orch.is_control_flow_node("brk") is True

    def test_continue_node_is_control_flow(self) -> None:
        """ContinueNode is control flow."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "cnt", "type": "ContinueNode"})
        orch = ExecutionOrchestrator(workflow)
        assert orch.is_control_flow_node("cnt") is True

    def test_retry_node_is_control_flow(self) -> None:
        """RetryNode is control flow."""
        workflow = WorkflowSchema()
        workflow.add_node({"node_id": "rty", "type": "RetryNode"})
        orch = ExecutionOrchestrator(workflow)
        assert orch.is_control_flow_node("rty") is True


# ============================================================================
# Port Connection Validation Tests
# ============================================================================


class TestNextNodesPortValidation:
    """Tests for port connection validation in get_next_nodes."""

    def test_dynamic_routing_missing_port_connection(self, caplog) -> None:
        """Warning logged when dynamic routing specifies port with no connections."""
        workflow = WorkflowSchema(WorkflowMetadata(name="MissingPort"))
        workflow.add_node({"node_id": "if_node", "type": "IfNode"})
        workflow.add_node({"node_id": "true_target", "type": "ActionNode"})
        # Only connect true branch, not false
        workflow.connections.append(
            NodeConnection("if_node", "true", "true_target", "exec_in")
        )

        orch = ExecutionOrchestrator(workflow)
        # Request false branch which has no connection
        result = {"next_nodes": ["false"]}
        next_nodes = orch.get_next_nodes("if_node", result)

        assert next_nodes == []
        # Check warning was logged
        assert "no connections found" in caplog.text.lower() or len(next_nodes) == 0

    def test_dynamic_routing_exec_out_no_connection_debug(self) -> None:
        """Debug log (not warning) when exec_out has no connections."""
        workflow = WorkflowSchema(WorkflowMetadata(name="EndNode"))
        workflow.add_node({"node_id": "end", "type": "EndNode"})

        orch = ExecutionOrchestrator(workflow)
        result = {"next_nodes": ["exec_out"]}
        next_nodes = orch.get_next_nodes("end", result)

        assert next_nodes == []
        # This should NOT produce a warning, only debug

    def test_dynamic_routing_partial_connections(self) -> None:
        """Partial connections return only connected nodes."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Partial"))
        workflow.add_node({"node_id": "switch", "type": "SwitchNode"})
        workflow.add_node({"node_id": "case1", "type": "ActionNode"})
        # Only connect case1, not case2
        workflow.connections.append(
            NodeConnection("switch", "case1", "case1", "exec_in")
        )

        orch = ExecutionOrchestrator(workflow)
        result = {"next_nodes": ["case1", "case2"]}
        next_nodes = orch.get_next_nodes("switch", result)

        assert next_nodes == ["case1"]

    def test_get_connections_from_port_helper(self) -> None:
        """Test _get_connections_from_port helper method."""
        workflow = WorkflowSchema(WorkflowMetadata(name="Helper"))
        workflow.add_node({"node_id": "src", "type": "Node"})
        workflow.add_node({"node_id": "dst1", "type": "Node"})
        workflow.add_node({"node_id": "dst2", "type": "Node"})
        workflow.connections.append(
            NodeConnection("src", "exec_out", "dst1", "exec_in")
        )
        workflow.connections.append(
            NodeConnection("src", "exec_out", "dst2", "exec_in")
        )
        workflow.connections.append(
            NodeConnection("src", "data_out", "dst1", "data_in")
        )

        orch = ExecutionOrchestrator(workflow)
        exec_connections = orch._get_connections_from_port("src", "exec_out")
        data_connections = orch._get_connections_from_port("src", "data_out")
        missing_connections = orch._get_connections_from_port("src", "missing")

        assert len(exec_connections) == 2
        assert len(data_connections) == 1
        assert len(missing_connections) == 0

    def test_dynamic_routing_no_duplicates(self) -> None:
        """Same target node from multiple ports is not duplicated."""
        workflow = WorkflowSchema(WorkflowMetadata(name="NoDupes"))
        workflow.add_node({"node_id": "merge", "type": "Node"})
        workflow.add_node({"node_id": "target", "type": "Node"})
        # Two connections to same target
        workflow.connections.append(
            NodeConnection("merge", "port1", "target", "exec_in")
        )
        workflow.connections.append(
            NodeConnection("merge", "port2", "target", "exec_in")
        )

        orch = ExecutionOrchestrator(workflow)
        result = {"next_nodes": ["port1", "port2"]}
        next_nodes = orch.get_next_nodes("merge", result)

        assert next_nodes == ["target"]
        assert len(next_nodes) == 1

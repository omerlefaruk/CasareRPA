import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from casare_rpa.application.use_cases.execution_engine import WorkflowExecutionEngine
from casare_rpa.domain.value_objects.types import NodeId


@pytest.mark.asyncio
async def test_execution_engine_sequential():
    # Setup mocks
    orchestrator = MagicMock()
    node_executor = AsyncMock()
    variable_resolver = MagicMock()
    state_manager = MagicMock()
    node_getter = MagicMock()
    context = MagicMock()

    # Configure mocks for a 2-node sequence: Node1 -> Node2
    orchestrator.is_control_flow_node.return_value = False
    orchestrator.get_next_nodes.side_effect = lambda nid, res: ["Node2"] if nid == "Node1" else []

    state_manager.is_stopped = False
    state_manager.executed_nodes = set()
    state_manager.should_execute_node.return_value = True
    state_manager.mark_target_reached.return_value = False
    state_manager.pause_checkpoint = AsyncMock()

    node1 = MagicMock()
    node1.output_ports = {}
    node2 = MagicMock()
    node2.output_ports = {}
    node_getter.side_effect = lambda nid: node1 if nid == "Node1" else node2

    exec_result = MagicMock()
    exec_result.success = True
    exec_result.result = {"next": "ok"}
    node_executor.execute.return_value = exec_result

    # Initialize engine
    engine = WorkflowExecutionEngine(
        orchestrator=orchestrator,
        node_executor=node_executor,
        variable_resolver=variable_resolver,
        state_manager=state_manager,
        node_getter=node_getter,
        context=context,
    )

    # Run
    await engine.run_from_node("Node1")

    # Verify
    assert node_executor.execute.call_count == 2
    state_manager.mark_node_executed.assert_any_call("Node1")
    state_manager.mark_node_executed.assert_any_call("Node2")


@pytest.mark.asyncio
async def test_execution_engine_stop():
    orchestrator = MagicMock()
    node_executor = AsyncMock()
    state_manager = MagicMock()

    # Stop after first node
    state_manager.is_stopped = True
    state_manager.pause_checkpoint = AsyncMock()

    engine = WorkflowExecutionEngine(
        orchestrator=orchestrator,
        node_executor=node_executor,
        variable_resolver=MagicMock(),
        state_manager=state_manager,
        node_getter=MagicMock(),
        context=MagicMock(),
    )

    await engine.run_from_node("Node1")

    # Should stop immediately
    assert node_executor.execute.call_count == 0

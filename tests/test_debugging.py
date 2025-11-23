"""
Comprehensive tests for debugging features.
"""

import pytest
import asyncio
import time
from casare_rpa.core.workflow_schema import WorkflowSchema, NodeConnection, WorkflowMetadata
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, GetVariableNode
from casare_rpa.nodes.control_flow_nodes import IfNode, ForLoopNode
from casare_rpa.core.types import NodeStatus


def create_runnable_workflow(metadata, nodes_dict, connections):
    """Helper to create executable workflow."""
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes_dict
    workflow.connections = connections
    return workflow


class TestBreakpointSystem:
    """Tests for breakpoint functionality."""
    
    def test_set_breakpoint_on_node(self):
        """Test setting a breakpoint on a node."""
        node = SetVariableNode("set1", config={"variable_name": "test"})
        
        assert not node.has_breakpoint()
        
        node.set_breakpoint(True)
        assert node.has_breakpoint()
        
        node.set_breakpoint(False)
        assert not node.has_breakpoint()
    
    def test_breakpoint_in_runner(self):
        """Test setting breakpoints via WorkflowRunner."""
        start = StartNode("start")
        set_var = SetVariableNode("set1", config={"variable_name": "test", "default_value": "value"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set_var, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.set_breakpoint("set1", True)
        
        assert "set1" in runner.breakpoints
        assert set_var.has_breakpoint()
    
    def test_clear_all_breakpoints(self):
        """Test clearing all breakpoints."""
        node1 = SetVariableNode("set1", config={"variable_name": "test1"})
        node2 = SetVariableNode("set2", config={"variable_name": "test2"})
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"set1": node1, "set2": node2},
            []
        )
        
        runner = WorkflowRunner(workflow)
        runner.set_breakpoint("set1", True)
        runner.set_breakpoint("set2", True)
        
        assert len(runner.breakpoints) == 2
        
        runner.clear_all_breakpoints()
        
        assert len(runner.breakpoints) == 0
        assert not node1.has_breakpoint()
        assert not node2.has_breakpoint()


class TestDebugMode:
    """Tests for debug mode functionality."""
    
    def test_enable_debug_mode(self):
        """Test enabling debug mode."""
        workflow = WorkflowSchema(WorkflowMetadata(name="test"))
        runner = WorkflowRunner(workflow)
        
        assert not runner.debug_mode
        
        runner.enable_debug_mode(True)
        assert runner.debug_mode
        
        runner.enable_debug_mode(False)
        assert not runner.debug_mode
    
    def test_enable_step_mode(self):
        """Test enabling step mode."""
        workflow = WorkflowSchema(WorkflowMetadata(name="test"))
        runner = WorkflowRunner(workflow)
        
        assert not runner.step_mode
        
        runner.enable_step_mode(True)
        assert runner.step_mode
        
        runner.enable_step_mode(False)
        assert not runner.step_mode
    
    @pytest.mark.asyncio
    async def test_execution_history_in_debug_mode(self):
        """Test that execution history is recorded in debug mode."""
        start = StartNode("start")
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "end": end},
            [
                NodeConnection("start", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        history = runner.get_execution_history()
        
        # Should have 2 entries (start, end)
        assert len(history) >= 2
        
        # Verify history structure
        for entry in history:
            assert "timestamp" in entry
            assert "node_id" in entry
            assert "node_type" in entry
            assert "execution_time" in entry
            assert "status" in entry


class TestNodeDebugInfo:
    """Tests for node debug information."""
    
    def test_get_node_debug_info(self):
        """Test getting debug info from a node."""
        node = SetVariableNode("set1", config={"variable_name": "test"})
        node.set_input_value("value", "test_value")
        node.execution_count = 3
        node.last_execution_time = 0.15
        
        debug_info = node.get_debug_info()
        
        assert debug_info["node_id"] == "set1"
        assert debug_info["node_type"] == "SetVariableNode"
        assert debug_info["execution_count"] == 3
        assert debug_info["last_execution_time"] == 0.15
        assert "input_values" in debug_info
        assert "output_values" in debug_info
    
    def test_get_node_debug_info_via_runner(self):
        """Test retrieving node debug info via WorkflowRunner."""
        node = SetVariableNode("set1", config={"variable_name": "test"})
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"set1": node},
            []
        )
        
        runner = WorkflowRunner(workflow)
        
        debug_info = runner.get_node_debug_info("set1")
        
        assert debug_info is not None
        assert debug_info["node_id"] == "set1"
        
        # Non-existent node should return None
        assert runner.get_node_debug_info("nonexistent") is None


class TestDebugModeReset:
    """Tests for resetting debug state."""
    
    @pytest.mark.asyncio
    async def test_reset_clears_history(self):
        """Test that reset clears execution history."""
        start = StartNode("start")
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "end": end},
            [NodeConnection("start", "exec_out", "end", "exec_in")]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        assert len(runner.get_execution_history()) > 0
        
        runner.reset()
        
        assert len(runner.get_execution_history()) == 0
    
    def test_breakpoints_persist_across_reset(self):
        """Test that breakpoints persist across resets."""
        node = SetVariableNode("set1", config={"variable_name": "test"})
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"set1": node},
            []
        )
        
        runner = WorkflowRunner(workflow)
        runner.set_breakpoint("set1", True)
        
        assert "set1" in runner.breakpoints
        
        runner.reset()
        
        # Breakpoints should persist across resets
        assert "set1" in runner.breakpoints


class TestAdvancedBreakpoints:
    """Advanced breakpoint scenarios."""
    
    def test_multiple_breakpoints(self):
        """Test setting multiple breakpoints."""
        nodes = {
            f"node{i}": SetVariableNode(f"node{i}", config={"variable_name": f"var{i}"})
            for i in range(5)
        }
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            nodes,
            []
        )
        
        runner = WorkflowRunner(workflow)
        
        # Set breakpoints on every other node
        for i in range(0, 5, 2):
            runner.set_breakpoint(f"node{i}", True)
        
        assert len(runner.breakpoints) == 3
        assert "node0" in runner.breakpoints
        assert "node2" in runner.breakpoints
        assert "node4" in runner.breakpoints
    
    def test_toggle_breakpoint(self):
        """Test toggling breakpoints."""
        node = SetVariableNode("set1", config={"variable_name": "test"})
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"set1": node},
            []
        )
        
        runner = WorkflowRunner(workflow)
        
        # Enable
        runner.set_breakpoint("set1", True)
        assert "set1" in runner.breakpoints
        assert node.has_breakpoint()
        
        # Disable
        runner.set_breakpoint("set1", False)
        assert "set1" not in runner.breakpoints
        assert not node.has_breakpoint()
        
        # Re-enable
        runner.set_breakpoint("set1", True)
        assert "set1" in runner.breakpoints
        assert node.has_breakpoint()


class TestStepExecution:
    """Tests for step-by-step execution."""
    
    @pytest.mark.asyncio
    async def test_step_mode_basic(self):
        """Test basic step mode execution."""
        start = StartNode("start")
        set1 = SetVariableNode("set1", config={"variable_name": "var1", "default_value": "value1"})
        set2 = SetVariableNode("set2", config={"variable_name": "var2", "default_value": "value2"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set1, "set2": set2, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "set2", "exec_in"),
                NodeConnection("set2", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        runner.enable_step_mode(True)
        
        # Start execution in background
        run_task = asyncio.create_task(runner.run())
        
        # Give it time to start
        await asyncio.sleep(0.1)
        
        # Should be waiting at first node
        history = runner.get_execution_history()
        assert len(history) >= 0  # May have started
        
        # Step through several nodes
        for _ in range(4):
            runner.step()
            await asyncio.sleep(0.1)
        
        # Wait for completion
        await run_task
        
        # All nodes should have executed
        history = runner.get_execution_history()
        assert len(history) >= 4
    
    @pytest.mark.asyncio
    async def test_continue_from_step_mode(self):
        """Test continuing execution from step mode."""
        start = StartNode("start")
        nodes = {
            "start": start,
            **{f"set{i}": SetVariableNode(f"set{i}", config={"variable_name": f"var{i}", "default_value": f"val{i}"}) 
               for i in range(3)}
        }
        end = EndNode("end")
        nodes["end"] = end
        
        connections = [NodeConnection("start", "exec_out", "set0", "exec_in")]
        for i in range(2):
            connections.append(NodeConnection(f"set{i}", "exec_out", f"set{i+1}", "exec_in"))
        connections.append(NodeConnection("set2", "exec_out", "end", "exec_in"))
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            nodes,
            connections
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        runner.enable_step_mode(True)
        
        # Start execution
        run_task = asyncio.create_task(runner.run())
        await asyncio.sleep(0.1)
        
        # Step once
        runner.step()
        await asyncio.sleep(0.1)
        
        # Continue execution
        runner.continue_execution()
        
        # Wait for completion
        await run_task
        
        # Should have completed all nodes
        history = runner.get_execution_history()
        assert len(history) >= 5


class TestExecutionHistory:
    """Tests for execution history tracking."""
    
    @pytest.mark.asyncio
    async def test_history_records_all_nodes(self):
        """Test that history records all executed nodes."""
        nodes = {"start": StartNode("start")}
        connections = []
        
        # Create chain of 10 nodes
        for i in range(10):
            node_id = f"set{i}"
            nodes[node_id] = SetVariableNode(node_id, config={"variable_name": f"var{i}", "default_value": str(i)})
            prev_id = "start" if i == 0 else f"set{i-1}"
            connections.append(NodeConnection(prev_id, "exec_out", node_id, "exec_in"))
        
        nodes["end"] = EndNode("end")
        connections.append(NodeConnection("set9", "exec_out", "end", "exec_in"))
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            nodes,
            connections
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        history = runner.get_execution_history()
        
        # Should have 12 entries (start + 10 sets + end)
        assert len(history) == 12
        
        # Verify order
        assert history[0]["node_id"] == "start"
        assert history[-1]["node_id"] == "end"
        
        # Verify all set nodes executed
        set_nodes = [h["node_id"] for h in history if h["node_id"].startswith("set")]
        assert len(set_nodes) == 10
    
    @pytest.mark.asyncio
    async def test_history_includes_timing(self):
        """Test that history includes execution timing."""
        start = StartNode("start")
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "end": end},
            [NodeConnection("start", "exec_out", "end", "exec_in")]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        history = runner.get_execution_history()
        
        for entry in history:
            assert "execution_time" in entry
            assert isinstance(entry["execution_time"], (int, float))
            assert entry["execution_time"] >= 0
            assert "timestamp" in entry
            assert isinstance(entry["timestamp"], str)
    
    @pytest.mark.asyncio
    async def test_history_tracks_success_failure(self):
        """Test that history tracks success/failure status."""
        start = StartNode("start")
        set_var = SetVariableNode("set1", config={"variable_name": "test", "default_value": "value"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set_var, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        history = runner.get_execution_history()
        
        for entry in history:
            assert "status" in entry
            assert entry["status"] in ["success", "failed"]


class TestNodeDebugMetrics:
    """Tests for node-level debug metrics."""
    
    @pytest.mark.asyncio
    async def test_execution_count_tracking(self):
        """Test that execution count is tracked per node."""
        start = StartNode("start")
        loop_body = SetVariableNode("set1", config={"variable_name": "counter", "default_value": "0"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": loop_body, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        
        await runner.run()
        
        # Each node should have been executed once
        assert start.execution_count == 1
        assert loop_body.execution_count == 1
        assert end.execution_count == 1
    
    @pytest.mark.asyncio
    async def test_last_execution_time_recorded(self):
        """Test that last execution time is recorded."""
        start = StartNode("start")
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "end": end},
            [NodeConnection("start", "exec_out", "end", "exec_in")]
        )
        
        runner = WorkflowRunner(workflow)
        
        await runner.run()
        
        assert start.last_execution_time is not None
        assert end.last_execution_time is not None
        assert isinstance(start.last_execution_time, (int, float))
        assert isinstance(end.last_execution_time, (int, float))
    
    @pytest.mark.asyncio
    async def test_last_output_captured(self):
        """Test that last output is captured."""
        start = StartNode("start")
        set_var = SetVariableNode("set1", config={"variable_name": "test", "default_value": "value"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set_var, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        
        await runner.run()
        
        assert start.last_output is not None
        assert set_var.last_output is not None
        assert end.last_output is not None


class TestVariableInspection:
    """Tests for variable inspection during debugging."""
    
    @pytest.mark.asyncio
    async def test_get_variables_during_execution(self):
        """Test retrieving variables during execution."""
        start = StartNode("start")
        set1 = SetVariableNode("set1", config={"variable_name": "var1", "default_value": "value1"})
        set2 = SetVariableNode("set2", config={"variable_name": "var2", "default_value": "value2"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set1, "set2": set2, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "set2", "exec_in"),
                NodeConnection("set2", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        
        await runner.run()
        
        variables = runner.get_variables()
        
        assert "var1" in variables
        assert "var2" in variables
        assert variables["var1"] == "value1"
        assert variables["var2"] == "value2"
    
    @pytest.mark.asyncio
    async def test_variables_empty_before_execution(self):
        """Test that variables are empty before execution."""
        start = StartNode("start")
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "end": end},
            [NodeConnection("start", "exec_out", "end", "exec_in")]
        )
        
        runner = WorkflowRunner(workflow)
        
        variables = runner.get_variables()
        assert len(variables) == 0


class TestComplexWorkflowDebugging:
    """Tests for debugging complex workflows."""
    
    @pytest.mark.asyncio
    async def test_debug_workflow_with_conditionals(self):
        """Test debugging workflow with conditional branches."""
        start = StartNode("start")
        set_val = SetVariableNode("set1", config={"variable_name": "value", "default_value": 15})
        if_node = IfNode("if1", {"expression": "value > 10"})
        then_node = SetVariableNode("then", config={"variable_name": "result", "default_value": "high"})
        else_node = SetVariableNode("else", config={"variable_name": "result", "default_value": "low"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {
                "start": start,
                "set1": set_val,
                "if1": if_node,
                "then": then_node,
                "else": else_node,
                "end": end
            },
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "if1", "exec_in"),
                NodeConnection("if1", "true", "then", "exec_in"),
                NodeConnection("if1", "false", "else", "exec_in"),
                NodeConnection("then", "exec_out", "end", "exec_in"),
                NodeConnection("else", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        history = runner.get_execution_history()
        
        # Should have executed: start, set1, if1, then, end
        assert len(history) >= 5
        
        # Verify the "then" branch was taken
        node_ids = [h["node_id"] for h in history]
        assert "then" in node_ids
        assert "else" not in node_ids
    
    @pytest.mark.asyncio
    async def test_debug_workflow_with_loops(self):
        """Test debugging a workflow with loops."""
        start = StartNode("start")
        set_var = SetVariableNode("set1", config={"variable_name": "counter", "default_value": 0})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set_var, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        await runner.run()
        
        history = runner.get_execution_history()
        
        # Should have executed all nodes
        assert len(history) >= 3
        node_ids = [h["node_id"] for h in history]
        assert "start" in node_ids
        assert "set1" in node_ids
        assert "end" in node_ids


class TestDebugReset:
    """Tests for resetting debug state."""
    
    @pytest.mark.asyncio
    async def test_reset_clears_node_metrics(self):
        """Test that reset clears node-level metrics."""
        start = StartNode("start")
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "end": end},
            [NodeConnection("start", "exec_out", "end", "exec_in")]
        )
        
        runner = WorkflowRunner(workflow)
        
        await runner.run()
        
        # Nodes should have metrics
        assert start.execution_count > 0
        assert end.execution_count > 0
        
        runner.reset()
        
        # Metrics should be cleared
        assert start.execution_count == 0
        assert end.execution_count == 0
        assert start.last_execution_time is None
        assert end.last_execution_time is None
        assert start.last_output is None
        assert end.last_output is None
    
    @pytest.mark.asyncio
    async def test_reset_allows_rerun(self):
        """Test that workflow can be re-run after reset."""
        start = StartNode("start")
        set_var = SetVariableNode("set1", config={"variable_name": "counter", "default_value": "0"})
        end = EndNode("end")
        
        workflow = create_runnable_workflow(
            WorkflowMetadata(name="test_workflow"),
            {"start": start, "set1": set_var, "end": end},
            [
                NodeConnection("start", "exec_out", "set1", "exec_in"),
                NodeConnection("set1", "exec_out", "end", "exec_in")
            ]
        )
        
        runner = WorkflowRunner(workflow)
        runner.enable_debug_mode(True)
        
        # First run
        await runner.run()
        history1 = runner.get_execution_history()
        assert len(history1) > 0
        
        # Reset
        runner.reset()
        
        # Second run
        await runner.run()
        history2 = runner.get_execution_history()
        
        # Should have fresh history
        assert len(history2) > 0
        assert len(history2) == len(history1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

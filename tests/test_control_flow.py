"""
Tests for control flow nodes.

This module tests conditional logic and loop nodes.
"""

import pytest
from casare_rpa.nodes.control_flow_nodes import IfNode, ForLoopNode, WhileLoopNode
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class TestIfNode:
    """Test If conditional node."""
    
    @pytest.mark.asyncio
    async def test_if_true_path(self) -> None:
        """Test If node taking true path."""
        node = IfNode("if_1")
        node.set_input_value("condition", True)
        
        context = ExecutionContext("test_workflow")
        result = await node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["true"]
        assert node.status == NodeStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_if_false_path(self) -> None:
        """Test If node taking false path."""
        node = IfNode("if_1")
        node.set_input_value("condition", False)
        
        context = ExecutionContext("test_workflow")
        result = await node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["false"]
        assert node.status == NodeStatus.SUCCESS
    
    @pytest.mark.asyncio
    async def test_if_expression_true(self) -> None:
        """Test If node with expression evaluation (true)."""
        node = IfNode("if_1", {"expression": "x > 5"})
        
        context = ExecutionContext("test_workflow")
        context.set_variable("x", 10)
        result = await node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["true"]
    
    @pytest.mark.asyncio
    async def test_if_expression_false(self) -> None:
        """Test If node with expression evaluation (false)."""
        node = IfNode("if_1", {"expression": "x > 5"})
        
        context = ExecutionContext("test_workflow")
        context.set_variable("x", 3)
        result = await node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["false"]
    
    @pytest.mark.asyncio
    async def test_if_truthy_values(self) -> None:
        """Test If node with various truthy values."""
        node = IfNode("if_1")
        context = ExecutionContext("test_workflow")
        
        # Test truthy values
        for value in [1, "text", [1, 2], {"key": "value"}]:
            node.set_input_value("condition", value)
            result = await node.execute(context)
            assert result["next_nodes"] == ["true"], f"Failed for {value}"
    
    @pytest.mark.asyncio
    async def test_if_falsy_values(self) -> None:
        """Test If node with various falsy values."""
        node = IfNode("if_1")
        context = ExecutionContext("test_workflow")
        
        # Test falsy values
        for value in [0, "", [], {}, None]:
            node.set_input_value("condition", value)
            result = await node.execute(context)
            assert result["next_nodes"] == ["false"], f"Failed for {value}"


class TestForLoopNode:
    """Test For Loop node."""
    
    @pytest.mark.asyncio
    async def test_for_loop_range(self) -> None:
        """Test For Loop with range."""
        node = ForLoopNode("loop_1", {"start": 0, "end": 3, "step": 1})
        context = ExecutionContext("test_workflow")
        
        # First iteration
        result = await node.execute(context)
        assert result["success"] is True
        assert result["next_nodes"] == ["loop_body"]
        assert node.get_output_value("item") == 0
        assert node.get_output_value("index") == 0
        
        # Second iteration
        result = await node.execute(context)
        assert result["next_nodes"] == ["loop_body"]
        assert node.get_output_value("item") == 1
        assert node.get_output_value("index") == 1
        
        # Third iteration
        result = await node.execute(context)
        assert result["next_nodes"] == ["loop_body"]
        assert node.get_output_value("item") == 2
        assert node.get_output_value("index") == 2
        
        # Loop complete
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
        assert result["data"]["iterations"] == 3
    
    @pytest.mark.asyncio
    async def test_for_loop_list(self) -> None:
        """Test For Loop with list input."""
        node = ForLoopNode("loop_1")
        node.set_input_value("items", ["a", "b", "c"])
        context = ExecutionContext("test_workflow")
        
        # Iterate through list
        items = []
        for i in range(3):
            result = await node.execute(context)
            assert result["next_nodes"] == ["loop_body"]
            items.append(node.get_output_value("item"))
            assert node.get_output_value("index") == i
        
        assert items == ["a", "b", "c"]
        
        # Loop complete
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
    
    @pytest.mark.asyncio
    async def test_for_loop_empty(self) -> None:
        """Test For Loop with empty list."""
        node = ForLoopNode("loop_1")
        node.set_input_value("items", [])
        context = ExecutionContext("test_workflow")
        
        # Should immediately complete
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
        assert result["data"]["iterations"] == 0
    
    @pytest.mark.asyncio
    async def test_for_loop_step(self) -> None:
        """Test For Loop with step."""
        node = ForLoopNode("loop_1", {"start": 0, "end": 10, "step": 2})
        context = ExecutionContext("test_workflow")
        
        # Should iterate: 0, 2, 4, 6, 8
        expected = [0, 2, 4, 6, 8]
        items = []
        
        for _ in range(5):
            result = await node.execute(context)
            assert result["next_nodes"] == ["loop_body"]
            items.append(node.get_output_value("item"))
        
        assert items == expected
        
        # Loop complete
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]


class TestWhileLoopNode:
    """Test While Loop node."""
    
    @pytest.mark.asyncio
    async def test_while_loop_basic(self) -> None:
        """Test While Loop with basic condition."""
        node = WhileLoopNode("loop_1", {"expression": "counter < 3"})
        context = ExecutionContext("test_workflow")
        context.set_variable("counter", 0)
        
        # Execute loop 3 times
        for i in range(3):
            result = await node.execute(context)
            assert result["success"] is True
            assert result["next_nodes"] == ["loop_body"]
            assert node.get_output_value("iteration") == i
            # Increment counter
            context.set_variable("counter", context.get_variable("counter") + 1)
        
        # Loop should exit
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
        assert result["data"]["iterations"] == 3
    
    @pytest.mark.asyncio
    async def test_while_loop_immediate_exit(self) -> None:
        """Test While Loop that exits immediately."""
        node = WhileLoopNode("loop_1", {"expression": "False"})
        context = ExecutionContext("test_workflow")
        
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
        assert result["data"]["iterations"] == 0
    
    @pytest.mark.asyncio
    async def test_while_loop_input_condition(self) -> None:
        """Test While Loop with input condition."""
        node = WhileLoopNode("loop_1")
        context = ExecutionContext("test_workflow")
        
        # First iteration (true)
        node.set_input_value("condition", True)
        result = await node.execute(context)
        assert result["next_nodes"] == ["loop_body"]
        
        # Second iteration (false)
        node.set_input_value("condition", False)
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
    
    @pytest.mark.asyncio
    async def test_while_loop_max_iterations(self) -> None:
        """Test While Loop respects max iterations."""
        node = WhileLoopNode("loop_1", {
            "expression": "True",  # Always true
            "max_iterations": 5
        })
        context = ExecutionContext("test_workflow")
        
        # Execute 5 times
        for i in range(5):
            result = await node.execute(context)
            assert result["next_nodes"] == ["loop_body"]
        
        # Should hit max iterations
        result = await node.execute(context)
        assert result["next_nodes"] == ["completed"]
        assert result["data"]["reason"] == "max_iterations"
        assert result["data"]["iterations"] == 5


class TestControlFlowIntegration:
    """Integration tests for control flow nodes."""
    
    @pytest.mark.asyncio
    async def test_if_with_variable(self) -> None:
        """Test If node integrated with variable system."""
        context = ExecutionContext("test_workflow")
        context.set_variable("age", 25)
        
        node = IfNode("if_1", {"expression": "age >= 18"})
        result = await node.execute(context)
        
        assert result["next_nodes"] == ["true"]
    
    @pytest.mark.asyncio
    async def test_nested_loops(self) -> None:
        """Test nested loop scenario."""
        context = ExecutionContext("test_workflow")
        
        # Outer loop
        outer = ForLoopNode("outer", {"start": 0, "end": 2, "step": 1})
        
        # Inner loop
        inner = ForLoopNode("inner", {"start": 0, "end": 2, "step": 1})
        
        # Outer iteration 1
        result = await outer.execute(context)
        assert result["next_nodes"] == ["loop_body"]
        outer_item = outer.get_output_value("item")
        assert outer_item == 0
        
        # Inner loop iterations
        for i in range(2):
            result = await inner.execute(context)
            assert result["next_nodes"] == ["loop_body"]
        
        # Complete inner loop
        result = await inner.execute(context)
        assert result["next_nodes"] == ["completed"]
        
        # Continue outer loop
        result = await outer.execute(context)
        assert result["next_nodes"] == ["loop_body"]
        assert outer.get_output_value("item") == 1

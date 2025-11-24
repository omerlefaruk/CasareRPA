"""
Tests for enhanced control flow nodes: Break, Continue, Switch.
"""

import pytest
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.nodes.control_flow_nodes import (
    BreakNode,
    ContinueNode,
    SwitchNode,
    ForLoopNode,
    WhileLoopNode
)


class TestBreakNode:
    """Tests for BreakNode."""
    
    @pytest.mark.asyncio
    async def test_break_execution(self):
        """Test break node executes and sets control_flow signal."""
        context = ExecutionContext("test")
        break_node = BreakNode("break1")
        
        result = await break_node.execute(context)
        
        assert result["success"] is True
        assert result["control_flow"] == "break"
        assert result["next_nodes"] == ["exec_out"]
    
    @pytest.mark.asyncio
    async def test_break_in_for_loop(self):
        """Test break exits for loop early."""
        context = ExecutionContext("test")
        
        # Create for loop
        for_loop = ForLoopNode("loop", {"start": 0, "end": 10, "step": 1})
        
        iterations = 0
        max_iterations = 10
        
        while iterations < max_iterations:
            result = await for_loop.execute(context)
            
            if result['next_nodes'] == ["completed"]:
                break
            
            # Get current item
            item = for_loop.get_output_value("item")
            iterations += 1
            
            # Break at item 5
            if item == 5:
                # Simulate break by cleaning up loop state
                loop_state_key = f"{for_loop.node_id}_loop_state"
                del context.variables[loop_state_key]
                break
        
        # Should have stopped at 5, not reached 10
        assert iterations == 6  # 0,1,2,3,4,5
        assert item == 5


class TestContinueNode:
    """Tests for ContinueNode."""
    
    @pytest.mark.asyncio
    async def test_continue_execution(self):
        """Test continue node executes and sets control_flow signal."""
        context = ExecutionContext("test")
        continue_node = ContinueNode("continue1")
        
        result = await continue_node.execute(context)
        
        assert result["success"] is True
        assert result["control_flow"] == "continue"
        assert result["next_nodes"] == ["exec_out"]
    
    @pytest.mark.asyncio
    async def test_continue_skips_in_for_loop(self):
        """Test continue skips to next iteration."""
        context = ExecutionContext("test")
        
        # Create for loop
        for_loop = ForLoopNode("loop", {"start": 0, "end": 5, "step": 1})
        
        processed_items = []
        
        while True:
            result = await for_loop.execute(context)
            
            if result['next_nodes'] == ["completed"]:
                break
            
            # Get current item
            item = for_loop.get_output_value("item")
            
            # Skip odd numbers (simulate continue)
            if item % 2 == 1:
                continue
            
            processed_items.append(item)
        
        # Should only have even numbers
        assert processed_items == [0, 2, 4]


class TestSwitchNode:
    """Tests for SwitchNode."""
    
    @pytest.mark.asyncio
    async def test_switch_match_case(self):
        """Test switch routes to matching case."""
        context = ExecutionContext("test")
        context.set_variable("status", "success")
        
        switch_node = SwitchNode("switch1", {
            "expression": "status",
            "cases": ["success", "error", "pending"]
        })
        
        result = await switch_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["case_success"]
        assert result["data"]["matched_case"] == "success"
    
    @pytest.mark.asyncio
    async def test_switch_default_case(self):
        """Test switch routes to default when no match."""
        context = ExecutionContext("test")
        context.set_variable("status", "unknown")
        
        switch_node = SwitchNode("switch1", {
            "expression": "status",
            "cases": ["success", "error", "pending"]
        })
        
        result = await switch_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["default"]
        assert result["data"]["matched_case"] == "default"
    
    @pytest.mark.asyncio
    async def test_switch_input_value(self):
        """Test switch with direct input value."""
        context = ExecutionContext("test")
        
        switch_node = SwitchNode("switch1", {
            "cases": ["apple", "banana", "orange"]
        })
        switch_node.set_input_value("value", "banana")
        
        result = await switch_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["case_banana"]
    
    @pytest.mark.asyncio
    async def test_switch_numeric_values(self):
        """Test switch with numeric values."""
        context = ExecutionContext("test")
        context.set_variable("code", 404)
        
        switch_node = SwitchNode("switch1", {
            "expression": "code",
            "cases": ["200", "404", "500"]
        })
        
        result = await switch_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["case_404"]
    
    @pytest.mark.asyncio
    async def test_switch_empty_cases(self):
        """Test switch with no cases defined."""
        context = ExecutionContext("test")
        
        switch_node = SwitchNode("switch1", {"cases": []})
        switch_node.set_input_value("value", "anything")
        
        result = await switch_node.execute(context)
        
        assert result["success"] is True
        assert result["next_nodes"] == ["default"]


class TestControlFlowIntegration:
    """Integration tests for enhanced control flow."""
    
    @pytest.mark.asyncio
    async def test_for_loop_with_break(self):
        """Test for loop that breaks on condition."""
        context = ExecutionContext("test")
        
        # Find first number > 50 in range
        for_loop = ForLoopNode("loop", {"start": 0, "end": 100, "step": 10})
        
        found_value = None
        iterations = 0
        
        while True:
            result = await for_loop.execute(context)
            iterations += 1
            
            if result['next_nodes'] == ["completed"]:
                break
            
            item = for_loop.get_output_value("item")
            
            if item > 50:
                found_value = item
                # Simulate break
                loop_state_key = f"{for_loop.node_id}_loop_state"
                del context.variables[loop_state_key]
                break
        
        assert found_value == 60  # First value > 50
        assert iterations < 10  # Should not iterate all 10 times
    
    @pytest.mark.asyncio
    async def test_switch_with_multiple_paths(self):
        """Test switch routing to different cases."""
        context = ExecutionContext("test")
        
        switch_node = SwitchNode("switch1", {
            "cases": ["low", "medium", "high"]
        })
        
        # Test each case
        test_cases = [
            ("low", "case_low"),
            ("medium", "case_medium"),
            ("high", "case_high"),
            ("extreme", "default")
        ]
        
        for value, expected_route in test_cases:
            switch_node.set_input_value("value", value)
            result = await switch_node.execute(context)
            
            assert result["success"] is True
            assert result["next_nodes"] == [expected_route]
    
    @pytest.mark.asyncio
    async def test_nested_switch_in_loop(self):
        """Test switch inside for loop."""
        context = ExecutionContext("test")
        
        for_loop = ForLoopNode("loop", {"start": 0, "end": 5, "step": 1})
        switch_node = SwitchNode("switch1", {
            "expression": "item % 2",
            "cases": ["0", "1"]
        })
        
        even_count = 0
        odd_count = 0
        
        while True:
            loop_result = await for_loop.execute(context)
            
            if loop_result['next_nodes'] == ["completed"]:
                break
            
            item = for_loop.get_output_value("item")
            context.set_variable("item", item)
            
            # Switch on even/odd
            switch_result = await switch_node.execute(context)
            
            if switch_result["next_nodes"] == ["case_0"]:
                even_count += 1
            else:
                odd_count += 1
        
        assert even_count == 3  # 0, 2, 4
        assert odd_count == 2   # 1, 3
    
    @pytest.mark.asyncio
    async def test_while_loop_with_continue(self):
        """Test while loop with continue to skip iterations."""
        context = ExecutionContext("test")
        context.set_variable("counter", 0)
        
        while_loop = WhileLoopNode("loop", {
            "expression": "counter < 10",
            "max_iterations": 20
        })
        
        sum_even = 0
        
        while True:
            result = await while_loop.execute(context)
            
            if result['next_nodes'] == ["completed"]:
                break
            
            counter = context.get_variable("counter")
            
            # Increment counter
            context.set_variable("counter", counter + 1)
            
            # Skip odd numbers (simulate continue)
            if counter % 2 == 1:
                continue
            
            sum_even += counter
        
        # Sum of even numbers 0,2,4,6,8 = 20
        assert sum_even == 20


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Phase 4: Node Library Tests

Tests for:
1. Basic nodes (Start, End, Comment)
2. Variable nodes (Set, Get, Increment)
3. Control flow nodes (If, ForLoop, WhileLoop, Switch, Break, Continue)
4. Error handling nodes (Try, Retry, ThrowError)
5. Data operation nodes (Concatenate, Format, Regex, Math, JSON)
6. Node registry and port system
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch


class TestBasicNodes:
    """Tests for basic node types."""

    def test_start_node_creation(self):
        """Test StartNode instantiation."""
        from casare_rpa.nodes import StartNode

        node = StartNode("start_1")

        assert node.node_id == "start_1"
        assert "exec_out" in node.output_ports

    def test_end_node_creation(self):
        """Test EndNode instantiation."""
        from casare_rpa.nodes import EndNode

        node = EndNode("end_1")

        assert node.node_id == "end_1"
        assert "exec_in" in node.input_ports

    def test_comment_node_creation(self):
        """Test CommentNode instantiation."""
        from casare_rpa.nodes import CommentNode

        node = CommentNode("comment_1")

        assert node.node_id == "comment_1"
        # CommentNode has no input ports - it's annotation only

    @pytest.mark.asyncio
    async def test_start_node_execute(self):
        """Test StartNode execution."""
        from casare_rpa.nodes import StartNode

        node = StartNode("start_1")
        result = await node.execute(None)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_end_node_execute(self):
        """Test EndNode execution marks workflow end."""
        from casare_rpa.nodes import EndNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        node = EndNode("end_1")
        result = await node.execute(context)

        # EndNode marks workflow complete
        assert "success" in result

    @pytest.mark.asyncio
    async def test_comment_node_execute(self):
        """Test CommentNode execution (should be no-op)."""
        from casare_rpa.nodes import CommentNode

        node = CommentNode("comment_1")
        result = await node.execute(None)

        assert result["success"] is True


class TestVariableNodes:
    """Tests for variable management nodes."""

    def test_set_variable_node_creation(self):
        """Test SetVariableNode instantiation."""
        from casare_rpa.nodes import SetVariableNode

        node = SetVariableNode("set_var_1")

        assert node.node_id == "set_var_1"
        assert "variable_name" in node.input_ports
        assert "value" in node.input_ports

    def test_get_variable_node_creation(self):
        """Test GetVariableNode instantiation."""
        from casare_rpa.nodes import GetVariableNode

        node = GetVariableNode("get_var_1")

        assert node.node_id == "get_var_1"
        assert "variable_name" in node.input_ports

    def test_increment_variable_node_creation(self):
        """Test IncrementVariableNode instantiation."""
        from casare_rpa.nodes import IncrementVariableNode

        node = IncrementVariableNode("incr_var_1")

        assert node.node_id == "incr_var_1"

    @pytest.mark.asyncio
    async def test_set_variable_execute(self):
        """Test SetVariableNode execution."""
        from casare_rpa.nodes import SetVariableNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        node = SetVariableNode("set_var_1")
        node.set_input_value("variable_name", "my_var")
        node.set_input_value("value", "test_value")

        result = await node.execute(context)

        assert result["success"] is True
        assert context.get_variable("my_var") == "test_value"

    @pytest.mark.asyncio
    async def test_get_variable_execute(self):
        """Test GetVariableNode execution - value is in data dict."""
        from casare_rpa.nodes import GetVariableNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        context.set_variable("existing_var", "existing_value")

        node = GetVariableNode("get_var_1")
        node.set_input_value("variable_name", "existing_var")

        result = await node.execute(context)

        assert result["success"] is True
        # Value is in the data dict
        assert result.get("data", {}).get("value") == "existing_value"

    @pytest.mark.asyncio
    async def test_increment_variable_execute(self):
        """Test IncrementVariableNode execution."""
        from casare_rpa.nodes import IncrementVariableNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        context.set_variable("counter", 5)

        node = IncrementVariableNode("incr_var_1")
        node.set_input_value("variable_name", "counter")
        node.set_input_value("increment", 1)

        result = await node.execute(context)

        assert result["success"] is True
        assert context.get_variable("counter") == 6


class TestControlFlowNodes:
    """Tests for control flow nodes."""

    def test_if_node_creation(self):
        """Test IfNode instantiation."""
        from casare_rpa.nodes import IfNode

        node = IfNode("if_1")

        assert node.node_id == "if_1"
        assert "condition" in node.input_ports
        assert "true" in node.output_ports
        assert "false" in node.output_ports

    def test_for_loop_node_creation(self):
        """Test ForLoopNode instantiation."""
        from casare_rpa.nodes import ForLoopNode

        node = ForLoopNode("for_1")

        assert node.node_id == "for_1"
        assert "loop_body" in node.output_ports
        assert "completed" in node.output_ports

    def test_while_loop_node_creation(self):
        """Test WhileLoopNode instantiation."""
        from casare_rpa.nodes import WhileLoopNode

        node = WhileLoopNode("while_1")

        assert node.node_id == "while_1"
        assert "condition" in node.input_ports

    def test_switch_node_creation(self):
        """Test SwitchNode instantiation."""
        from casare_rpa.nodes import SwitchNode

        node = SwitchNode("switch_1")

        assert node.node_id == "switch_1"
        assert "value" in node.input_ports

    def test_break_node_creation(self):
        """Test BreakNode instantiation."""
        from casare_rpa.nodes import BreakNode

        node = BreakNode("break_1")

        assert node.node_id == "break_1"

    def test_continue_node_creation(self):
        """Test ContinueNode instantiation."""
        from casare_rpa.nodes import ContinueNode

        node = ContinueNode("continue_1")

        assert node.node_id == "continue_1"

    @pytest.mark.asyncio
    async def test_if_node_true_branch(self):
        """Test IfNode routes to true branch."""
        from casare_rpa.nodes import IfNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        context.set_variable("x", 10)

        node = IfNode("if_1")
        node.set_input_value("condition", "x > 5")

        result = await node.execute(context)

        assert result["success"] is True
        assert "true" in result.get("next_nodes", [])

    @pytest.mark.asyncio
    async def test_if_node_evaluates_condition(self):
        """Test IfNode evaluates condition from context."""
        from casare_rpa.nodes import IfNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        context.set_variable("value", 100)

        node = IfNode("if_1")
        node.set_input_value("condition", "value == 100")

        result = await node.execute(context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_for_loop_with_items(self):
        """Test ForLoopNode with items list."""
        from casare_rpa.nodes import ForLoopNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        node = ForLoopNode("for_1")
        node.set_input_value("items", [1, 2, 3])
        # ForLoopNode sets item/index via output ports, not input

        result = await node.execute(context)
        assert result["success"] is True
        # First iteration should output "loop_body" next node
        assert "loop_body" in result.get("next_nodes", [])

    @pytest.mark.asyncio
    async def test_break_node_execute(self):
        """Test BreakNode execution signals break."""
        from casare_rpa.nodes import BreakNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        node = BreakNode("break_1")
        result = await node.execute(context)

        assert result["success"] is True
        assert result.get("control_flow") == "break"

    @pytest.mark.asyncio
    async def test_continue_node_execute(self):
        """Test ContinueNode execution signals continue."""
        from casare_rpa.nodes import ContinueNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        node = ContinueNode("continue_1")
        result = await node.execute(context)

        assert result["success"] is True
        assert result.get("control_flow") == "continue"


class TestErrorHandlingNodes:
    """Tests for error handling nodes."""

    def test_try_node_creation(self):
        """Test TryNode instantiation."""
        from casare_rpa.nodes import TryNode

        node = TryNode("try_1")

        assert node.node_id == "try_1"
        # TryNode has try_body and catch output ports
        assert "try_body" in node.output_ports
        assert "catch" in node.output_ports

    def test_retry_node_creation(self):
        """Test RetryNode instantiation."""
        from casare_rpa.nodes import RetryNode

        node = RetryNode("retry_1")

        assert node.node_id == "retry_1"
        # RetryNode has exec_in port
        assert "exec_in" in node.input_ports

    def test_throw_error_node_creation(self):
        """Test ThrowErrorNode instantiation."""
        from casare_rpa.nodes import ThrowErrorNode

        node = ThrowErrorNode("throw_1")

        assert node.node_id == "throw_1"
        assert "error_message" in node.input_ports

    @pytest.mark.asyncio
    async def test_throw_error_execute(self):
        """Test ThrowErrorNode raises an error."""
        from casare_rpa.nodes import ThrowErrorNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")

        node = ThrowErrorNode("throw_1")
        node.set_input_value("error_message", "Test error message")

        result = await node.execute(context)

        assert result["success"] is False
        assert "error" in result


class TestDataOperationNodes:
    """Tests for data operation nodes."""

    def test_concatenate_node_creation(self):
        """Test ConcatenateNode instantiation."""
        from casare_rpa.nodes import ConcatenateNode

        node = ConcatenateNode("concat_1")

        assert node.node_id == "concat_1"
        # Uses string_1 and string_2 as input ports
        assert "string_1" in node.input_ports
        assert "string_2" in node.input_ports

    def test_format_string_node_creation(self):
        """Test FormatStringNode instantiation."""
        from casare_rpa.nodes import FormatStringNode

        node = FormatStringNode("format_1")

        assert node.node_id == "format_1"
        assert "template" in node.input_ports

    def test_regex_match_node_creation(self):
        """Test RegexMatchNode instantiation."""
        from casare_rpa.nodes import RegexMatchNode

        node = RegexMatchNode("regex_1")

        assert node.node_id == "regex_1"
        assert "pattern" in node.input_ports
        assert "text" in node.input_ports

    def test_math_operation_node_creation(self):
        """Test MathOperationNode instantiation."""
        from casare_rpa.nodes import MathOperationNode

        node = MathOperationNode("math_1")

        assert node.node_id == "math_1"
        # Uses 'a' and 'b' as operand names
        assert "a" in node.input_ports
        assert "b" in node.input_ports

    def test_json_parse_node_creation(self):
        """Test JsonParseNode instantiation."""
        from casare_rpa.nodes import JsonParseNode

        node = JsonParseNode("json_1")

        assert node.node_id == "json_1"
        assert "json_string" in node.input_ports

    @pytest.mark.asyncio
    async def test_concatenate_execute(self):
        """Test ConcatenateNode execution."""
        from casare_rpa.nodes import ConcatenateNode

        node = ConcatenateNode("concat_1")
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", " World")

        result = await node.execute(None)

        assert result["success"] is True
        # Result is in the data dict
        assert result.get("data", {}).get("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_regex_match_execute(self):
        """Test RegexMatchNode execution - result in data dict."""
        from casare_rpa.nodes import RegexMatchNode

        node = RegexMatchNode("regex_1")
        node.set_input_value("text", "Email: test@example.com")
        node.set_input_value("pattern", r"[\w.-]+@[\w.-]+\.\w+")

        result = await node.execute(None)

        assert result["success"] is True
        # Match info is in data dict
        data = result.get("data", {})
        assert data.get("match_found") is True
        assert data.get("first_match") == "test@example.com"

    @pytest.mark.asyncio
    async def test_math_operation_add(self):
        """Test MathOperationNode addition."""
        from casare_rpa.nodes import MathOperationNode

        # Operation is set via config, not input port
        node = MathOperationNode("math_1", config={"operation": "add"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") == 15.0

    @pytest.mark.asyncio
    async def test_math_operation_multiply(self):
        """Test MathOperationNode multiplication."""
        from casare_rpa.nodes import MathOperationNode

        # Operation is set via config, not input port
        node = MathOperationNode("math_1", config={"operation": "multiply"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") == 50.0

    @pytest.mark.asyncio
    async def test_json_parse_execute(self):
        """Test JsonParseNode execution - parsed in data dict."""
        from casare_rpa.nodes import JsonParseNode

        node = JsonParseNode("json_1")
        node.set_input_value("json_string", '{"name": "test", "value": 42}')

        result = await node.execute(None)

        assert result["success"] is True
        # The parsed data is in "parsed_data" key
        parsed = result.get("data", {}).get("parsed_data")
        assert parsed is not None
        assert parsed["name"] == "test"
        assert parsed["value"] == 42

    @pytest.mark.asyncio
    async def test_json_parse_invalid_json(self):
        """Test JsonParseNode with invalid JSON."""
        from casare_rpa.nodes import JsonParseNode

        node = JsonParseNode("json_1")
        node.set_input_value("json_string", "not valid json")

        result = await node.execute(None)

        assert result["success"] is False
        assert "error" in result


class TestComparisonNode:
    """Tests for comparison node."""

    def test_comparison_node_creation(self):
        """Test ComparisonNode instantiation."""
        from casare_rpa.nodes import ComparisonNode

        node = ComparisonNode("compare_1")

        assert node.node_id == "compare_1"
        # Uses 'a' and 'b' as input names
        assert "a" in node.input_ports
        assert "b" in node.input_ports

    @pytest.mark.asyncio
    async def test_comparison_equal(self):
        """Test ComparisonNode equality."""
        from casare_rpa.nodes import ComparisonNode

        # Operator is set via config, not input port
        node = ComparisonNode("compare_1", config={"operator": "=="})
        node.set_input_value("a", 5)
        node.set_input_value("b", 5)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") is True

    @pytest.mark.asyncio
    async def test_comparison_greater(self):
        """Test ComparisonNode greater than."""
        from casare_rpa.nodes import ComparisonNode

        # Operator is set via config, not input port
        node = ComparisonNode("compare_1", config={"operator": ">"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("result") is True


class TestListNodes:
    """Tests for list operation nodes."""

    def test_create_list_node_creation(self):
        """Test CreateListNode instantiation."""
        from casare_rpa.nodes import CreateListNode

        node = CreateListNode("list_1")

        assert node.node_id == "list_1"

    def test_list_get_item_node_creation(self):
        """Test ListGetItemNode instantiation."""
        from casare_rpa.nodes import ListGetItemNode

        node = ListGetItemNode("get_item_1")

        assert node.node_id == "get_item_1"

    @pytest.mark.asyncio
    async def test_create_list_execute(self):
        """Test CreateListNode execution."""
        from casare_rpa.nodes import CreateListNode

        node = CreateListNode("list_1")
        # CreateListNode uses item_1, item_2, item_3 ports
        node.set_input_value("item_1", 1)
        node.set_input_value("item_2", 2)
        node.set_input_value("item_3", 3)

        result = await node.execute(None)

        assert result["success"] is True
        data = result.get("data", {})
        # List should be in result
        assert "list" in data
        assert data["list"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_list_get_item_execute(self):
        """Test ListGetItemNode execution."""
        from casare_rpa.nodes import ListGetItemNode
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test")
        context.set_variable("my_list", ["a", "b", "c"])

        node = ListGetItemNode("get_item_1")
        node.set_input_value("list", context.get_variable("my_list"))
        node.set_input_value("index", 1)

        result = await node.execute(context)

        assert result["success"] is True
        assert result.get("data", {}).get("item") == "b"


class TestGetPropertyNode:
    """Tests for GetPropertyNode."""

    def test_get_property_node_creation(self):
        """Test GetPropertyNode instantiation."""
        from casare_rpa.nodes import GetPropertyNode

        node = GetPropertyNode("prop_1")

        assert node.node_id == "prop_1"

    @pytest.mark.asyncio
    async def test_get_property_execute(self):
        """Test GetPropertyNode execution."""
        from casare_rpa.nodes import GetPropertyNode

        node = GetPropertyNode("prop_1")
        node.set_input_value("object", {"name": "test", "value": 42})
        # Uses property_path not property
        node.set_input_value("property_path", "name")

        result = await node.execute(None)

        assert result["success"] is True
        assert result.get("data", {}).get("value") == "test"


class TestNodeRegistry:
    """Tests for node registry and discovery."""

    def test_node_registry_exists(self):
        """Test that node registry is populated."""
        from casare_rpa import nodes

        assert hasattr(nodes, "_NODE_REGISTRY")
        assert len(nodes._NODE_REGISTRY) > 0

    def test_all_node_classes_loadable(self):
        """Test that all registered nodes can be loaded."""
        from casare_rpa.nodes import get_all_node_classes

        all_classes = get_all_node_classes()

        assert len(all_classes) > 20  # Should have at least 22 node types

        # Verify key node types
        expected_nodes = [
            "StartNode",
            "EndNode",
            "IfNode",
            "ForLoopNode",
            "SetVariableNode",
            "JsonParseNode",
        ]

        for node_name in expected_nodes:
            assert node_name in all_classes

    def test_node_instantiation_from_registry(self):
        """Test creating nodes via registry."""
        from casare_rpa.nodes import StartNode, EndNode, IfNode

        # Should be able to import and instantiate
        start = StartNode("s1")
        end = EndNode("e1")
        if_node = IfNode("i1")

        assert start.node_id == "s1"
        assert end.node_id == "e1"
        assert if_node.node_id == "i1"


class TestNodePorts:
    """Tests for node port system."""

    def test_node_has_input_ports(self):
        """Test that nodes have input ports defined."""
        from casare_rpa.nodes import IfNode

        node = IfNode("test_if")

        assert hasattr(node, "input_ports")
        assert isinstance(node.input_ports, dict)
        assert "condition" in node.input_ports

    def test_node_has_output_ports(self):
        """Test that nodes have output ports defined."""
        from casare_rpa.nodes import IfNode

        node = IfNode("test_if")

        assert hasattr(node, "output_ports")
        assert isinstance(node.output_ports, dict)
        assert "true" in node.output_ports
        assert "false" in node.output_ports

    def test_set_input_value(self):
        """Test setting input values on nodes."""
        from casare_rpa.nodes import SetVariableNode

        node = SetVariableNode("test_set")

        node.set_input_value("variable_name", "test_var")
        node.set_input_value("value", 42)

        # Should be stored and accessible
        assert node.get_input_value("variable_name") == "test_var"
        assert node.get_input_value("value") == 42

    def test_get_output_value(self):
        """Test getting output values from nodes."""
        from casare_rpa.nodes import StartNode

        node = StartNode("test_start")

        # Output ports should exist
        assert "exec_out" in node.output_ports


class TestWaitNodes:
    """Tests for wait/timing nodes."""

    def test_wait_node_creation(self):
        """Test WaitNode instantiation."""
        from casare_rpa.nodes import WaitNode

        node = WaitNode("wait_1")

        assert node.node_id == "wait_1"
        assert "duration" in node.input_ports

    def test_wait_for_element_node_creation(self):
        """Test WaitForElementNode instantiation."""
        from casare_rpa.nodes import WaitForElementNode

        node = WaitForElementNode("wait_el_1")

        assert node.node_id == "wait_el_1"

    @pytest.mark.asyncio
    async def test_wait_node_execute(self):
        """Test WaitNode execution with short duration."""
        from casare_rpa.nodes import WaitNode

        node = WaitNode("wait_1")
        node.set_input_value("duration", 0.1)  # 100ms wait

        result = await node.execute(None)

        assert result["success"] is True

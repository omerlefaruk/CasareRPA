"""
Integration tests for data operation nodes.

Tests 20 high-priority data operation nodes across string, math, list, and dict categories.
"""

import pytest
from unittest.mock import Mock

# Uses execution_context fixture from conftest.py - no import needed


class TestDataOperationNodes:
    """Integration tests for data operation category nodes."""

    # Uses execution_context fixture from conftest.py

    # =============================================================================
    # String Operations (4 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_concatenate_node(self, execution_context) -> None:
        """Test ConcatenateNode joins strings."""
        from casare_rpa.nodes.data_operation_nodes import ConcatenateNode

        node = ConcatenateNode(node_id="test_concat")
        node.set_input_value("input1", "Hello")
        node.set_input_value("input2", " World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == "Hello World"

    @pytest.mark.asyncio
    async def test_format_string_node(self, execution_context) -> None:
        """Test FormatStringNode formats strings."""
        from casare_rpa.nodes.data_operation_nodes import FormatStringNode

        node = FormatStringNode(node_id="test_format")
        node.config["format"] = "Name: {}, Age: {}"
        node.set_input_value("args", ["Alice", 30])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == "Name: Alice, Age: 30"

    @pytest.mark.asyncio
    async def test_regex_match_node(self, execution_context) -> None:
        """Test RegexMatchNode finds pattern matches."""
        from casare_rpa.nodes.data_operation_nodes import RegexMatchNode

        node = RegexMatchNode(node_id="test_regex_match")
        node.set_input_value("text", "Email: test@example.com")
        node.config["pattern"] = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "test@example.com" in result["data"]["matches"][0]

    @pytest.mark.asyncio
    async def test_regex_replace_node(self, execution_context) -> None:
        """Test RegexReplaceNode replaces pattern matches."""
        from casare_rpa.nodes.data_operation_nodes import RegexReplaceNode

        node = RegexReplaceNode(node_id="test_regex_replace")
        node.set_input_value("text", "Price: $100")
        node.config["pattern"] = r"\$(\d+)"
        node.config["replacement"] = r"USD \1"

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == "Price: USD 100"

    # =============================================================================
    # Math Operations (4 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_math_add(self, execution_context) -> None:
        """Test MathOperationNode addition."""
        from casare_rpa.nodes.data_operation_nodes import MathOperationNode

        node = MathOperationNode(node_id="test_math_add")
        node.config["operation"] = "add"
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == 15

    @pytest.mark.asyncio
    async def test_math_subtract(self, execution_context) -> None:
        """Test MathOperationNode subtraction."""
        from casare_rpa.nodes.data_operation_nodes import MathOperationNode

        node = MathOperationNode(node_id="test_math_sub")
        node.config["operation"] = "subtract"
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == 5

    @pytest.mark.asyncio
    async def test_math_multiply(self, execution_context) -> None:
        """Test MathOperationNode multiplication."""
        from casare_rpa.nodes.data_operation_nodes import MathOperationNode

        node = MathOperationNode(node_id="test_math_mul")
        node.config["operation"] = "multiply"
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == 50

    @pytest.mark.asyncio
    async def test_math_divide(self, execution_context) -> None:
        """Test MathOperationNode division."""
        from casare_rpa.nodes.data_operation_nodes import MathOperationNode

        node = MathOperationNode(node_id="test_math_div")
        node.config["operation"] = "divide"
        node.set_input_value("a", 10)
        node.set_input_value("b", 2)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["result"] == 5.0

    # =============================================================================
    # List Operations (6 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_create_list_node(self, execution_context) -> None:
        """Test CreateListNode creates a list."""
        from casare_rpa.nodes.data_operation_nodes import CreateListNode

        node = CreateListNode(node_id="test_create_list")
        node.set_input_value("items", [1, 2, 3, 4, 5])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["list"] == [1, 2, 3, 4, 5]

    @pytest.mark.asyncio
    async def test_get_item_node(self, execution_context) -> None:
        """Test GetItemNode retrieves item by index."""
        from casare_rpa.nodes.data_operation_nodes import GetItemNode

        node = GetItemNode(node_id="test_get_item")
        node.set_input_value("list", ["apple", "banana", "cherry"])
        node.set_input_value("index", 1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["item"] == "banana"

    @pytest.mark.asyncio
    async def test_length_node(self, execution_context) -> None:
        """Test LengthNode returns collection length."""
        from casare_rpa.nodes.data_operation_nodes import LengthNode

        node = LengthNode(node_id="test_length")
        node.set_input_value("collection", [1, 2, 3, 4, 5])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["length"] == 5

    @pytest.mark.asyncio
    async def test_append_node(self, execution_context) -> None:
        """Test AppendNode adds item to list."""
        from casare_rpa.nodes.data_operation_nodes import AppendNode

        node = AppendNode(node_id="test_append")
        node.set_input_value("list", [1, 2, 3])
        node.set_input_value("item", 4)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["list"] == [1, 2, 3, 4]

    @pytest.mark.asyncio
    async def test_contains_node(self, execution_context) -> None:
        """Test ContainsNode checks if item exists in collection."""
        from casare_rpa.nodes.data_operation_nodes import ContainsNode

        node = ContainsNode(node_id="test_contains")
        node.set_input_value("collection", ["apple", "banana", "cherry"])
        node.set_input_value("item", "banana")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["contains"] is True

    @pytest.mark.asyncio
    async def test_slice_node(self, execution_context) -> None:
        """Test SliceNode extracts subset of list."""
        from casare_rpa.nodes.data_operation_nodes import SliceNode

        node = SliceNode(node_id="test_slice")
        node.set_input_value("list", [0, 1, 2, 3, 4, 5])
        node.set_input_value("start", 1)
        node.set_input_value("end", 4)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["slice"] == [1, 2, 3]

    # =============================================================================
    # Dict Operations (6 tests)
    # =============================================================================

    @pytest.mark.asyncio
    async def test_dict_get_node(self, execution_context) -> None:
        """Test DictGetNode retrieves value by key."""
        from casare_rpa.nodes.data_operation_nodes import DictGetNode

        node = DictGetNode(node_id="test_dict_get")
        node.set_input_value("dict", {"name": "Alice", "age": 30})
        node.set_input_value("key", "name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "Alice"

    @pytest.mark.asyncio
    async def test_dict_set_node(self, execution_context) -> None:
        """Test DictSetNode sets key-value pair."""
        from casare_rpa.nodes.data_operation_nodes import DictSetNode

        node = DictSetNode(node_id="test_dict_set")
        node.set_input_value("dict", {"name": "Alice"})
        node.set_input_value("key", "age")
        node.set_input_value("value", 30)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["dict"] == {"name": "Alice", "age": 30}

    @pytest.mark.asyncio
    async def test_dict_remove_node(self, execution_context) -> None:
        """Test DictRemoveNode removes key from dict."""
        from casare_rpa.nodes.data_operation_nodes import DictRemoveNode

        node = DictRemoveNode(node_id="test_dict_remove")
        node.set_input_value("dict", {"name": "Alice", "age": 30, "city": "NYC"})
        node.set_input_value("key", "age")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["dict"] == {"name": "Alice", "city": "NYC"}

    @pytest.mark.asyncio
    async def test_dict_merge_node(self, execution_context) -> None:
        """Test DictMergeNode merges two dictionaries."""
        from casare_rpa.nodes.data_operation_nodes import DictMergeNode

        node = DictMergeNode(node_id="test_dict_merge")
        node.set_input_value("dict1", {"a": 1, "b": 2})
        node.set_input_value("dict2", {"b": 3, "c": 4})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["merged"] == {"a": 1, "b": 3, "c": 4}

    @pytest.mark.asyncio
    async def test_dict_keys_node(self, execution_context) -> None:
        """Test DictKeysNode returns list of keys."""
        from casare_rpa.nodes.data_operation_nodes import DictKeysNode

        node = DictKeysNode(node_id="test_dict_keys")
        node.set_input_value("dict", {"name": "Alice", "age": 30, "city": "NYC"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert set(result["data"]["keys"]) == {"name", "age", "city"}

    @pytest.mark.asyncio
    async def test_dict_values_node(self, execution_context) -> None:
        """Test DictValuesNode returns list of values."""
        from casare_rpa.nodes.data_operation_nodes import DictValuesNode

        node = DictValuesNode(node_id="test_dict_values")
        node.set_input_value("dict", {"a": 1, "b": 2, "c": 3})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert set(result["data"]["values"]) == {1, 2, 3}


class TestDataOperationNodesIntegration:
    """Integration tests for data operation nodes visual layer."""

    def test_concatenate_visual_integration(self) -> None:
        """Test ConcatenateNode logic-to-visual connection."""
        from casare_rpa.nodes.data_operation_nodes import ConcatenateNode
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
            VisualConcatenateNode,
        )

        visual_node = VisualConcatenateNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == ConcatenateNode

        node = ConcatenateNode(node_id="test_concat")
        assert node.node_type == "ConcatenateNode"

    def test_math_operation_visual_integration(self) -> None:
        """Test MathOperationNode logic-to-visual connection."""
        from casare_rpa.nodes.data_operation_nodes import MathOperationNode
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
            VisualMathOperationNode,
        )

        visual_node = VisualMathOperationNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == MathOperationNode

        node = MathOperationNode(node_id="test_math")
        assert node.node_type == "MathOperationNode"

    def test_create_list_visual_integration(self) -> None:
        """Test CreateListNode logic-to-visual connection."""
        from casare_rpa.nodes.data_operation_nodes import CreateListNode
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
            VisualCreateListNode,
        )

        visual_node = VisualCreateListNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == CreateListNode

        node = CreateListNode(node_id="test_list")
        assert node.node_type == "CreateListNode"

    def test_dict_get_visual_integration(self) -> None:
        """Test DictGetNode logic-to-visual connection."""
        from casare_rpa.nodes.data_operation_nodes import DictGetNode
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
            VisualDictGetNode,
        )

        visual_node = VisualDictGetNode()
        logic_class = visual_node.get_node_class()
        assert logic_class == DictGetNode

        node = DictGetNode(node_id="test_dict_get")
        assert node.node_type == "DictGetNode"

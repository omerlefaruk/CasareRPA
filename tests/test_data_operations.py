import pytest
import asyncio
from casare_rpa.core.types import NodeStatus, DataType
from casare_rpa.nodes.data_operation_nodes import (
    ConcatenateNode,
    FormatStringNode,
    RegexMatchNode,
    RegexReplaceNode,
    MathOperationNode,
    ComparisonNode,
    CreateListNode,
    ListGetItemNode,
    JsonParseNode,
    GetPropertyNode
)

class TestStringOperations:
    @pytest.mark.asyncio
    async def test_concatenate(self):
        node = ConcatenateNode("test_concat")
        node.set_input_value("string_1", "Hello")
        node.set_input_value("string_2", "World")
        node.separator = " "
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_format_string(self):
        node = FormatStringNode("test_format")
        node.set_input_value("template", "Hello {name}, you are {age} years old.")
        node.set_input_value("variables", {"name": "Alice", "age": 30})
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "Hello Alice, you are 30 years old."

    @pytest.mark.asyncio
    async def test_regex_match(self):
        node = RegexMatchNode("test_regex")
        node.set_input_value("text", "The price is $123.45")
        node.set_input_value("pattern", r"\$(\d+\.\d+)")
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("match_found") is True
        assert node.get_output_value("first_match") == "$123.45"
        assert node.get_output_value("groups") == ["123.45"]

    @pytest.mark.asyncio
    async def test_regex_replace(self):
        node = RegexReplaceNode("test_replace")
        node.set_input_value("text", "apple banana apple")
        node.set_input_value("pattern", "apple")
        node.set_input_value("replacement", "orange")
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("result") == "orange banana orange"
        assert node.get_output_value("count") == 2

class TestMathOperations:
    @pytest.mark.asyncio
    async def test_math_add(self):
        node = MathOperationNode("test_add", {"operation": "add"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 15

    @pytest.mark.asyncio
    async def test_math_divide(self):
        node = MathOperationNode("test_div", {"operation": "divide"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 2)
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("result") == 5

    @pytest.mark.asyncio
    async def test_comparison(self):
        node = ComparisonNode("test_comp", {"operator": ">"})
        node.set_input_value("a", 10)
        node.set_input_value("b", 5)
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("result") is True

class TestListOperations:
    @pytest.mark.asyncio
    async def test_create_list(self):
        node = CreateListNode("test_create_list")
        node.set_input_value("item_1", "a")
        node.set_input_value("item_2", "b")
        node.set_input_value("item_3", "c")
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("list") == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_list_get_item(self):
        node = ListGetItemNode("test_get_item")
        node.set_input_value("list", ["a", "b", "c"])
        node.set_input_value("index", 1)
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("item") == "b"

class TestJsonOperations:
    @pytest.mark.asyncio
    async def test_json_parse(self):
        node = JsonParseNode("test_json")
        node.set_input_value("json_string", '{"name": "Bob", "active": true}')
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        data = node.get_output_value("data")
        assert data["name"] == "Bob"
        assert data["active"] is True

    @pytest.mark.asyncio
    async def test_get_property(self):
        node = GetPropertyNode("test_prop")
        data = {"user": {"address": {"city": "New York"}}}
        node.set_input_value("object", data)
        node.set_input_value("property_path", "user.address.city")
        
        status = await node.execute(None)
        assert status == NodeStatus.SUCCESS
        assert node.get_output_value("value") == "New York"

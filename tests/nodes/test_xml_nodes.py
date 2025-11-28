"""
Tests for XML operation nodes.

Tests 8 XML nodes for XML parsing, XPath queries, and JSON conversion.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET

# Uses execution_context fixture from conftest.py - no import needed


class TestXMLNodes:
    """Tests for XML category nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_variable = lambda k: context.variables.get(k)
        context.set_variable = lambda k, v: context.variables.__setitem__(k, v)
        return context

    @pytest.fixture
    def sample_xml(self) -> None:
        """Sample XML string for testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<root>
    <person id="1" role="admin">
        <name>Alice</name>
        <age>30</age>
        <city>NYC</city>
    </person>
    <person id="2" role="user">
        <name>Bob</name>
        <age>25</age>
        <city>LA</city>
    </person>
    <metadata>
        <created>2024-01-01</created>
    </metadata>
</root>"""

    @pytest.fixture
    def simple_xml(self) -> None:
        """Simple XML for basic tests."""
        return "<root><item>value</item></root>"

    # =========================================================================
    # ParseXMLNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_parse_xml_node_success(self, execution_context, sample_xml) -> None:
        """Test ParseXMLNode parses valid XML."""
        from casare_rpa.nodes.xml_nodes import ParseXMLNode

        node = ParseXMLNode(node_id="test_parse")
        node.set_input_value("xml_string", sample_xml)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["root_tag"] == "root"
        assert result["data"]["child_count"] == 3
        assert node.get_output_value("success") is True
        assert node.get_output_value("root_tag") == "root"

    @pytest.mark.asyncio
    async def test_parse_xml_node_invalid_xml(self, execution_context) -> None:
        """Test ParseXMLNode handles invalid XML."""
        from casare_rpa.nodes.xml_nodes import ParseXMLNode

        node = ParseXMLNode(node_id="test_invalid")
        node.set_input_value("xml_string", "<root><unclosed>")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert (
            "parse error" in result["error"].lower() or "xml" in result["error"].lower()
        )
        assert node.get_output_value("success") is False

    @pytest.mark.asyncio
    async def test_parse_xml_node_empty_input(self, execution_context) -> None:
        """Test ParseXMLNode handles empty input."""
        from casare_rpa.nodes.xml_nodes import ParseXMLNode

        node = ParseXMLNode(node_id="test_empty")
        node.set_input_value("xml_string", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_parse_xml_node_stores_in_context(
        self, execution_context, simple_xml
    ) -> None:
        """Test ParseXMLNode stores parsed XML in context."""
        from casare_rpa.nodes.xml_nodes import ParseXMLNode

        node = ParseXMLNode(node_id="test_context")
        node.set_input_value("xml_string", simple_xml)

        await node.execute(execution_context)

        assert "_xml_root" in execution_context.variables
        assert execution_context.variables["_xml_root"].tag == "root"

    # =========================================================================
    # XPathQueryNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_xpath_query_node_find_elements(
        self, execution_context, sample_xml
    ) -> None:
        """Test XPathQueryNode finds elements."""
        from casare_rpa.nodes.xml_nodes import XPathQueryNode

        node = XPathQueryNode(node_id="test_xpath")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", ".//person")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 2
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_xpath_query_node_with_attributes(
        self, execution_context, sample_xml
    ) -> None:
        """Test XPathQueryNode finds elements with attribute filter."""
        from casare_rpa.nodes.xml_nodes import XPathQueryNode

        node = XPathQueryNode(node_id="test_xpath_attr")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", ".//person[@role='admin']")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 1
        results = node.get_output_value("results")
        assert len(results) == 1
        assert results[0]["attrib"]["role"] == "admin"

    @pytest.mark.asyncio
    async def test_xpath_query_node_no_match(
        self, execution_context, sample_xml
    ) -> None:
        """Test XPathQueryNode handles no matches."""
        from casare_rpa.nodes.xml_nodes import XPathQueryNode

        node = XPathQueryNode(node_id="test_no_match")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", ".//nonexistent")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 0
        assert node.get_output_value("first_text") == ""

    @pytest.mark.asyncio
    async def test_xpath_query_node_missing_xpath(
        self, execution_context, sample_xml
    ) -> None:
        """Test XPathQueryNode handles missing xpath."""
        from casare_rpa.nodes.xml_nodes import XPathQueryNode

        node = XPathQueryNode(node_id="test_missing")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    # =========================================================================
    # XMLToJsonNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_xml_to_json_node_basic(self, execution_context, simple_xml) -> None:
        """Test XMLToJsonNode converts simple XML."""
        from casare_rpa.nodes.xml_nodes import XMLToJsonNode

        node = XMLToJsonNode(node_id="test_to_json")
        node.set_input_value("xml_string", simple_xml)

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_data = node.get_output_value("json_data")
        assert "root" in json_data
        assert json_data["root"]["item"] == "value"

    @pytest.mark.asyncio
    async def test_xml_to_json_node_with_attributes(self, execution_context) -> None:
        """Test XMLToJsonNode preserves attributes."""
        from casare_rpa.nodes.xml_nodes import XMLToJsonNode

        xml = '<root><item id="1" type="test">content</item></root>'
        node = XMLToJsonNode(node_id="test_attrs", config={"include_attributes": True})
        node.set_input_value("xml_string", xml)

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_data = node.get_output_value("json_data")
        assert "@attributes" in json_data["root"]["item"]
        assert json_data["root"]["item"]["@attributes"]["id"] == "1"

    @pytest.mark.asyncio
    async def test_xml_to_json_node_nested(self, execution_context, sample_xml) -> None:
        """Test XMLToJsonNode handles nested structure."""
        from casare_rpa.nodes.xml_nodes import XMLToJsonNode

        node = XMLToJsonNode(node_id="test_nested")
        node.set_input_value("xml_string", sample_xml)

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_data = node.get_output_value("json_data")
        assert "root" in json_data
        # Should have person array
        assert "person" in json_data["root"]

    @pytest.mark.asyncio
    async def test_xml_to_json_node_empty_input(self, execution_context) -> None:
        """Test XMLToJsonNode handles empty input."""
        from casare_rpa.nodes.xml_nodes import XMLToJsonNode

        node = XMLToJsonNode(node_id="test_empty_json")
        node.set_input_value("xml_string", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    # =========================================================================
    # JsonToXMLNode Tests (4 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_json_to_xml_node_basic(self, execution_context) -> None:
        """Test JsonToXMLNode converts simple JSON."""
        from casare_rpa.nodes.xml_nodes import JsonToXMLNode

        json_data = {"name": "Alice", "age": "30"}
        node = JsonToXMLNode(node_id="test_from_json", config={"root_tag": "person"})
        node.set_input_value("json_data", json_data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_string = node.get_output_value("xml_string")
        assert "<person>" in xml_string
        assert "<name>Alice</name>" in xml_string

    @pytest.mark.asyncio
    async def test_json_to_xml_node_from_string(self, execution_context) -> None:
        """Test JsonToXMLNode handles JSON string input."""
        from casare_rpa.nodes.xml_nodes import JsonToXMLNode

        json_str = '{"item": "value"}'
        node = JsonToXMLNode(node_id="test_str_json")
        node.set_input_value("json_data", json_str)

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_string = node.get_output_value("xml_string")
        assert "<item>value</item>" in xml_string

    @pytest.mark.asyncio
    async def test_json_to_xml_node_nested(self, execution_context) -> None:
        """Test JsonToXMLNode handles nested JSON."""
        from casare_rpa.nodes.xml_nodes import JsonToXMLNode

        json_data = {
            "person": {
                "name": "Bob",
                "address": {"city": "NYC", "zip": "10001"},
            }
        }
        node = JsonToXMLNode(node_id="test_nested_json")
        node.set_input_value("json_data", json_data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_string = node.get_output_value("xml_string")
        assert "<city>NYC</city>" in xml_string

    @pytest.mark.asyncio
    async def test_json_to_xml_node_empty_input(self, execution_context) -> None:
        """Test JsonToXMLNode handles empty input."""
        from casare_rpa.nodes.xml_nodes import JsonToXMLNode

        node = JsonToXMLNode(node_id="test_empty_xml")
        node.set_input_value("json_data", None)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    # =========================================================================
    # GetXMLElementNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_xml_element_node_found(
        self, execution_context, sample_xml
    ) -> None:
        """Test GetXMLElementNode finds element."""
        from casare_rpa.nodes.xml_nodes import GetXMLElementNode

        node = GetXMLElementNode(node_id="test_get_elem")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("tag_name", "name")
        node.set_input_value("index", 0)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("text") == "Alice"
        assert node.get_output_value("tag") == "name"

    @pytest.mark.asyncio
    async def test_get_xml_element_node_with_index(
        self, execution_context, sample_xml
    ) -> None:
        """Test GetXMLElementNode uses index correctly."""
        from casare_rpa.nodes.xml_nodes import GetXMLElementNode

        node = GetXMLElementNode(node_id="test_get_idx")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("tag_name", "name")
        node.set_input_value("index", 1)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("text") == "Bob"

    @pytest.mark.asyncio
    async def test_get_xml_element_node_not_found(
        self, execution_context, sample_xml
    ) -> None:
        """Test GetXMLElementNode handles missing element."""
        from casare_rpa.nodes.xml_nodes import GetXMLElementNode

        node = GetXMLElementNode(node_id="test_not_found")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("tag_name", "nonexistent")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is False

    # =========================================================================
    # GetXMLAttributeNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_xml_attribute_node_found(
        self, execution_context, sample_xml
    ) -> None:
        """Test GetXMLAttributeNode finds attribute."""
        from casare_rpa.nodes.xml_nodes import GetXMLAttributeNode

        node = GetXMLAttributeNode(node_id="test_get_attr")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", ".//person")
        node.set_input_value("attribute_name", "id")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("value") == "1"

    @pytest.mark.asyncio
    async def test_get_xml_attribute_node_role(
        self, execution_context, sample_xml
    ) -> None:
        """Test GetXMLAttributeNode gets role attribute."""
        from casare_rpa.nodes.xml_nodes import GetXMLAttributeNode

        node = GetXMLAttributeNode(node_id="test_get_role")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", ".//person[@id='2']")
        node.set_input_value("attribute_name", "role")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is True
        assert node.get_output_value("value") == "user"

    @pytest.mark.asyncio
    async def test_get_xml_attribute_node_not_found(
        self, execution_context, sample_xml
    ) -> None:
        """Test GetXMLAttributeNode handles missing attribute."""
        from casare_rpa.nodes.xml_nodes import GetXMLAttributeNode

        node = GetXMLAttributeNode(node_id="test_no_attr")
        node.set_input_value("xml_string", sample_xml)
        node.set_input_value("xpath", ".//person")
        node.set_input_value("attribute_name", "nonexistent")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is False

    # =========================================================================
    # ReadXMLFileNode Tests (3 tests)
    # =========================================================================

    @pytest.mark.asyncio
    async def test_read_xml_file_node_success(
        self, execution_context, tmp_path, sample_xml
    ) -> None:
        """Test ReadXMLFileNode reads XML file."""
        from casare_rpa.nodes.xml_nodes import ReadXMLFileNode

        xml_file = tmp_path / "test.xml"
        xml_file.write_text(sample_xml, encoding="utf-8")

        node = ReadXMLFileNode(node_id="test_read_xml")
        node.set_input_value("file_path", str(xml_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("root_tag") == "root"
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_read_xml_file_node_not_found(self, execution_context) -> None:
        """Test ReadXMLFileNode handles missing file."""
        from casare_rpa.nodes.xml_nodes import ReadXMLFileNode

        node = ReadXMLFileNode(node_id="test_no_file")
        node.set_input_value("file_path", "/nonexistent/file.xml")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_read_xml_file_node_stores_context(
        self, execution_context, tmp_path, simple_xml
    ) -> None:
        """Test ReadXMLFileNode stores tree in context."""
        from casare_rpa.nodes.xml_nodes import ReadXMLFileNode

        xml_file = tmp_path / "simple.xml"
        xml_file.write_text(simple_xml, encoding="utf-8")

        node = ReadXMLFileNode(node_id="test_ctx")
        node.set_input_value("file_path", str(xml_file))

        await node.execute(execution_context)

        assert "_xml_root" in execution_context.variables
        assert "_xml_tree" in execution_context.variables


class TestXMLNodesEdgeCases:
    """Edge case and error handling tests for XML nodes."""

    @pytest.fixture
    def execution_context(self) -> None:
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.variables = {}
        context.resolve_value = lambda x: x
        context.get_variable = lambda k: context.variables.get(k)
        context.set_variable = lambda k, v: context.variables.__setitem__(k, v)
        return context

    @pytest.mark.asyncio
    async def test_xpath_uses_context_xml(self, execution_context) -> None:
        """Test XPathQueryNode uses XML from context when no input."""
        from casare_rpa.nodes.xml_nodes import XPathQueryNode

        # Pre-populate context with parsed XML
        root = ET.fromstring("<data><item>test</item></data>")
        execution_context.variables["_xml_root"] = root

        node = XPathQueryNode(node_id="test_ctx_xpath")
        node.set_input_value("xml_string", None)
        node.set_input_value("xpath", ".//item")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 1
        assert node.get_output_value("first_text") == "test"

    @pytest.mark.asyncio
    async def test_get_element_uses_context_xml(self, execution_context) -> None:
        """Test GetXMLElementNode uses XML from context."""
        from casare_rpa.nodes.xml_nodes import GetXMLElementNode

        root = ET.fromstring("<data><item>context_value</item></data>")
        execution_context.variables["_xml_root"] = root

        node = GetXMLElementNode(node_id="test_ctx_elem")
        node.set_input_value("xml_string", None)
        node.set_input_value("tag_name", "item")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("text") == "context_value"

    @pytest.mark.asyncio
    async def test_xml_to_json_without_attributes(self, execution_context) -> None:
        """Test XMLToJsonNode without attributes."""
        from casare_rpa.nodes.xml_nodes import XMLToJsonNode

        xml = '<root><item id="1">value</item></root>'
        node = XMLToJsonNode(
            node_id="test_no_attrs", config={"include_attributes": False}
        )
        node.set_input_value("xml_string", xml)

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_data = node.get_output_value("json_data")
        # Should not have @attributes
        if isinstance(json_data["root"]["item"], dict):
            assert "@attributes" not in json_data["root"]["item"]

    @pytest.mark.asyncio
    async def test_json_to_xml_with_list(self, execution_context) -> None:
        """Test JsonToXMLNode handles lists."""
        from casare_rpa.nodes.xml_nodes import JsonToXMLNode

        json_data = {"items": ["a", "b", "c"]}
        node = JsonToXMLNode(node_id="test_list")
        node.set_input_value("json_data", json_data)

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_string = node.get_output_value("xml_string")
        assert "items" in xml_string

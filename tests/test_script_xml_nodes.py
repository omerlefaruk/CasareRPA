"""
Tests for Script execution and XML operation nodes.

Tests Python script execution, expression evaluation, and XML parsing/manipulation.
"""

import pytest
import tempfile
import os
from pathlib import Path

from casare_rpa.nodes.script_nodes import (
    RunPythonScriptNode,
    RunPythonFileNode,
    EvalExpressionNode,
    RunBatchScriptNode,
)
from casare_rpa.nodes.xml_nodes import (
    ParseXMLNode,
    ReadXMLFileNode,
    WriteXMLFileNode,
    XPathQueryNode,
    GetXMLElementNode,
    GetXMLAttributeNode,
    XMLToJsonNode,
    JsonToXMLNode,
)
from casare_rpa.core.types import NodeStatus


class TestRunPythonScriptNode:
    """Tests for RunPythonScript node."""

    @pytest.mark.asyncio
    async def test_run_python_basic(self, execution_context):
        """Test running basic Python code."""
        node = RunPythonScriptNode(node_id="py_1")
        node.set_input_value("code", "result = 2 + 2")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 4
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_run_python_with_output(self, execution_context):
        """Test Python code with print output."""
        node = RunPythonScriptNode(node_id="py_1")
        node.set_input_value("code", "print('Hello')\nresult = 'done'")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Hello" in node.get_output_value("output")
        assert node.get_output_value("result") == "done"

    @pytest.mark.asyncio
    async def test_run_python_with_variables(self, execution_context):
        """Test Python code with input variables."""
        node = RunPythonScriptNode(node_id="py_1")
        node.set_input_value("code", "result = x + y")
        node.set_input_value("variables", {"x": 10, "y": 20})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 30

    @pytest.mark.asyncio
    async def test_run_python_error_handling(self, execution_context):
        """Test Python code error handling."""
        node = RunPythonScriptNode(node_id="py_1")
        node.set_input_value("code", "result = 1 / 0")

        result = await node.execute(execution_context)

        assert node.get_output_value("success") is False
        assert "division" in node.get_output_value("error").lower()

    @pytest.mark.asyncio
    async def test_run_python_empty_code_fails(self, execution_context):
        """Test that empty code fails."""
        node = RunPythonScriptNode(node_id="py_1")
        node.set_input_value("code", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestRunPythonFileNode:
    """Tests for RunPythonFile node."""

    @pytest.mark.asyncio
    async def test_run_python_file(self, execution_context, tmp_path):
        """Test running a Python file."""
        # Create a test Python file
        script_file = tmp_path / "test_script.py"
        script_file.write_text("print('Hello from file')")

        node = RunPythonFileNode(node_id="pyf_1")
        node.set_input_value("file_path", str(script_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Hello from file" in node.get_output_value("stdout")
        assert node.get_output_value("return_code") == 0

    @pytest.mark.asyncio
    async def test_run_python_file_not_found(self, execution_context):
        """Test running non-existent file fails."""
        node = RunPythonFileNode(node_id="pyf_1")
        node.set_input_value("file_path", "/nonexistent/file.py")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_python_file_with_args(self, execution_context, tmp_path):
        """Test running Python file with arguments."""
        script_file = tmp_path / "args_script.py"
        script_file.write_text("""
import sys
print(' '.join(sys.argv[1:]))
""")

        node = RunPythonFileNode(node_id="pyf_1")
        node.set_input_value("file_path", str(script_file))
        node.set_input_value("args", ["arg1", "arg2"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "arg1 arg2" in node.get_output_value("stdout")


class TestEvalExpressionNode:
    """Tests for EvalExpression node."""

    @pytest.mark.asyncio
    async def test_eval_simple(self, execution_context):
        """Test evaluating simple expression."""
        node = EvalExpressionNode(node_id="eval_1")
        node.set_input_value("expression", "2 + 2")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 4
        assert node.get_output_value("type") == "int"

    @pytest.mark.asyncio
    async def test_eval_with_variables(self, execution_context):
        """Test evaluating expression with variables."""
        node = EvalExpressionNode(node_id="eval_1")
        node.set_input_value("expression", "x * y + z")
        node.set_input_value("variables", {"x": 2, "y": 3, "z": 4})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 10

    @pytest.mark.asyncio
    async def test_eval_string_operations(self, execution_context):
        """Test evaluating string operations."""
        node = EvalExpressionNode(node_id="eval_1")
        node.set_input_value("expression", "name.upper()")
        node.set_input_value("variables", {"name": "hello"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "HELLO"

    @pytest.mark.asyncio
    async def test_eval_list_comprehension(self, execution_context):
        """Test evaluating list comprehension."""
        node = EvalExpressionNode(node_id="eval_1")
        node.set_input_value("expression", "[x**2 for x in range(5)]")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [0, 1, 4, 9, 16]

    @pytest.mark.asyncio
    async def test_eval_error(self, execution_context):
        """Test expression evaluation error."""
        node = EvalExpressionNode(node_id="eval_1")
        node.set_input_value("expression", "undefined_var")

        result = await node.execute(execution_context)

        assert node.get_output_value("success") is False


class TestRunBatchScriptNode:
    """Tests for RunBatchScript node."""

    @pytest.mark.asyncio
    async def test_run_batch_script(self, execution_context):
        """Test running a batch script."""
        node = RunBatchScriptNode(node_id="batch_1")
        # Use echo which works on both Windows and Unix
        node.set_input_value("script", "echo Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Hello" in node.get_output_value("stdout")


class TestParseXMLNode:
    """Tests for ParseXML node."""

    @pytest.mark.asyncio
    async def test_parse_xml_basic(self, execution_context):
        """Test parsing basic XML."""
        node = ParseXMLNode(node_id="xml_1")
        node.set_input_value("xml_string", "<root><item>Hello</item></root>")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("root_tag") == "root"
        assert node.get_output_value("child_count") == 1
        assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_parse_xml_with_attributes(self, execution_context):
        """Test parsing XML with attributes."""
        node = ParseXMLNode(node_id="xml_1")
        node.set_input_value("xml_string", '<root version="1.0"><item id="1">Text</item></root>')

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("root_tag") == "root"

    @pytest.mark.asyncio
    async def test_parse_xml_invalid_fails(self, execution_context):
        """Test parsing invalid XML fails."""
        node = ParseXMLNode(node_id="xml_1")
        node.set_input_value("xml_string", "<root><unclosed>")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "parse" in result["error"].lower()


class TestReadXMLFileNode:
    """Tests for ReadXMLFile node."""

    @pytest.mark.asyncio
    async def test_read_xml_file(self, execution_context, tmp_path):
        """Test reading XML from file."""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text('<?xml version="1.0"?><data><item>Test</item></data>')

        node = ReadXMLFileNode(node_id="xmlf_1")
        node.set_input_value("file_path", str(xml_file))

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("root_tag") == "data"
        assert "<item>Test</item>" in node.get_output_value("xml_string")

    @pytest.mark.asyncio
    async def test_read_xml_file_not_found(self, execution_context):
        """Test reading non-existent XML file fails."""
        node = ReadXMLFileNode(node_id="xmlf_1")
        node.set_input_value("file_path", "/nonexistent/file.xml")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestWriteXMLFileNode:
    """Tests for WriteXMLFile node."""

    @pytest.mark.asyncio
    async def test_write_xml_file(self, execution_context, tmp_path):
        """Test writing XML to file."""
        output_file = tmp_path / "output.xml"

        node = WriteXMLFileNode(node_id="xmlw_1")
        node.set_input_value("file_path", str(output_file))
        node.set_input_value("xml_string", "<root><item>Data</item></root>")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert output_file.exists()
        content = output_file.read_text()
        assert "<root>" in content


class TestXPathQueryNode:
    """Tests for XPathQuery node."""

    @pytest.mark.asyncio
    async def test_xpath_query_basic(self, execution_context):
        """Test basic XPath query."""
        node = XPathQueryNode(node_id="xpath_1")
        node.set_input_value("xml_string", "<root><item>A</item><item>B</item></root>")
        node.set_input_value("xpath", ".//item")

        result = await node.execute(execution_context)

        assert result["success"] is True
        results = node.get_output_value("results")
        assert len(results) == 2
        assert node.get_output_value("count") == 2

    @pytest.mark.asyncio
    async def test_xpath_query_with_text(self, execution_context):
        """Test XPath query getting text content."""
        node = XPathQueryNode(node_id="xpath_1")
        node.set_input_value("xml_string", "<root><name>John</name></root>")
        node.set_input_value("xpath", ".//name")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("first_text") == "John"


class TestGetXMLElementNode:
    """Tests for GetXMLElement node."""

    @pytest.mark.asyncio
    async def test_get_element_basic(self, execution_context):
        """Test getting element by tag name."""
        node = GetXMLElementNode(node_id="elem_1")
        node.set_input_value("xml_string", '<root><user id="1">Admin</user></root>')
        node.set_input_value("tag_name", "user")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("tag") == "user"
        assert node.get_output_value("text") == "Admin"
        assert node.get_output_value("found") is True

    @pytest.mark.asyncio
    async def test_get_element_with_attributes(self, execution_context):
        """Test getting element attributes."""
        node = GetXMLElementNode(node_id="elem_1")
        node.set_input_value("xml_string", '<root><item id="123" type="data">Content</item></root>')
        node.set_input_value("tag_name", "item")

        result = await node.execute(execution_context)

        assert result["success"] is True
        attrs = node.get_output_value("attributes")
        assert attrs["id"] == "123"
        assert attrs["type"] == "data"

    @pytest.mark.asyncio
    async def test_get_element_not_found(self, execution_context):
        """Test getting non-existent element."""
        node = GetXMLElementNode(node_id="elem_1")
        node.set_input_value("xml_string", "<root><item>Data</item></root>")
        node.set_input_value("tag_name", "nonexistent")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is False


class TestGetXMLAttributeNode:
    """Tests for GetXMLAttribute node."""

    @pytest.mark.asyncio
    async def test_get_attribute_basic(self, execution_context):
        """Test getting attribute value."""
        node = GetXMLAttributeNode(node_id="attr_1")
        node.set_input_value("xml_string", '<root version="2.0"><item/></root>')
        node.set_input_value("xpath", ".")
        node.set_input_value("attribute_name", "version")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("value") == "2.0"
        assert node.get_output_value("found") is True

    @pytest.mark.asyncio
    async def test_get_attribute_not_found(self, execution_context):
        """Test getting non-existent attribute."""
        node = GetXMLAttributeNode(node_id="attr_1")
        node.set_input_value("xml_string", "<root><item/></root>")
        node.set_input_value("xpath", ".")
        node.set_input_value("attribute_name", "missing")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("found") is False


class TestXMLToJsonNode:
    """Tests for XMLToJson node."""

    @pytest.mark.asyncio
    async def test_xml_to_json_basic(self, execution_context):
        """Test converting XML to JSON."""
        node = XMLToJsonNode(node_id="tojson_1")
        node.set_input_value("xml_string", "<root><name>John</name><age>30</age></root>")

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_data = node.get_output_value("json_data")
        assert "root" in json_data
        assert json_data["root"]["name"] == "John"
        assert json_data["root"]["age"] == "30"

    @pytest.mark.asyncio
    async def test_xml_to_json_with_attributes(self, execution_context):
        """Test XML to JSON with attributes."""
        node = XMLToJsonNode(node_id="tojson_1")
        node.set_input_value("xml_string", '<item id="1">Data</item>')

        result = await node.execute(execution_context)

        assert result["success"] is True
        json_data = node.get_output_value("json_data")
        assert "@attributes" in json_data.get("item", {})


class TestJsonToXMLNode:
    """Tests for JsonToXML node."""

    @pytest.mark.asyncio
    async def test_json_to_xml_basic(self, execution_context):
        """Test converting JSON to XML."""
        node = JsonToXMLNode(node_id="toxml_1")
        node.set_input_value("json_data", {"name": "John", "age": 30})

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_str = node.get_output_value("xml_string")
        assert "<name>John</name>" in xml_str
        assert "<age>30</age>" in xml_str

    @pytest.mark.asyncio
    async def test_json_to_xml_from_string(self, execution_context):
        """Test converting JSON string to XML."""
        node = JsonToXMLNode(node_id="toxml_1")
        node.set_input_value("json_data", '{"key": "value"}')

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_str = node.get_output_value("xml_string")
        assert "<key>value</key>" in xml_str

    @pytest.mark.asyncio
    async def test_json_to_xml_nested(self, execution_context):
        """Test converting nested JSON to XML."""
        node = JsonToXMLNode(node_id="toxml_1")
        node.set_input_value("json_data", {
            "user": {
                "name": "Alice",
                "email": "alice@example.com"
            }
        })

        result = await node.execute(execution_context)

        assert result["success"] is True
        xml_str = node.get_output_value("xml_string")
        assert "<user>" in xml_str
        assert "<name>Alice</name>" in xml_str

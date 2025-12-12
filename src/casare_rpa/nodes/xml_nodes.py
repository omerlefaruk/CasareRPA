"""
XML operation nodes for CasareRPA.

This module provides nodes for XML parsing and manipulation:
- ParseXMLNode: Parse XML from string
- ReadXMLFileNode: Read and parse XML file
- WriteXMLFileNode: Write XML to file
- XPathQueryNode: Query XML with XPath
- GetXMLElementNode: Get element by tag name
- GetXMLAttributeNode: Get element attribute
- XMLToJsonNode: Convert XML to JSON
- JsonToXMLNode: Convert JSON to XML
"""

import defusedxml.ElementTree as DefusedET
from defusedxml.minidom import parseString as safe_parseString
import xml.etree.ElementTree as ET  # For XML creation (defusedxml only for parsing)
import json
from pathlib import Path


from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.utils import safe_int


@node(category="data")
@properties()  # Input port driven
class ParseXMLNode(BaseNode):
    """
    Parse XML from a string.

    Inputs:
        xml_string: XML string to parse

    Outputs:
        root_tag: Root element tag name
        root_text: Root element text content
        child_count: Number of child elements
        success: Whether parsing succeeded
    """

    # @category: data
    # @requires: xml
    # @ports: xml_string -> root_tag, root_text, child_count, success

    def __init__(self, node_id: str, name: str = "Parse XML", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ParseXMLNode"
        self._xml_root = None

    def _define_ports(self) -> None:
        self.add_input_port("xml_string", DataType.STRING)
        self.add_output_port("root_tag", DataType.STRING)
        self.add_output_port("root_text", DataType.STRING)
        self.add_output_port("child_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            xml_string = str(self.get_parameter("xml_string", "") or "")

            if not xml_string:
                raise ValueError("xml_string is required")

            root = DefusedET.fromstring(xml_string)
            self._xml_root = root

            # Store parsed XML in context for other nodes
            context.set_variable("_xml_root", root)

            self.set_output_value("root_tag", root.tag)
            self.set_output_value("root_text", root.text or "")
            self.set_output_value("child_count", len(list(root)))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"root_tag": root.tag, "child_count": len(list(root))},
                "next_nodes": ["exec_out"],
            }

        except DefusedET.ParseError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": f"XML parse error: {e}",
                "next_nodes": [],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties(
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="File encoding (e.g., utf-8, latin-1)",
    ),
)
class ReadXMLFileNode(BaseNode):
    """
    Read and parse an XML file.

    Config:
        encoding: File encoding (default: utf-8)

    Inputs:
        file_path: Path to XML file

    Outputs:
        root_tag: Root element tag name
        xml_string: Raw XML content
        success: Whether operation succeeded
    """

    # @category: data
    # @requires: xml
    # @ports: file_path -> root_tag, xml_string, success

    def __init__(self, node_id: str, name: str = "Read XML File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadXMLFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_output_port("root_tag", DataType.STRING)
        self.add_output_port("xml_string", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = str(self.get_parameter("file_path", "") or "")
            encoding = self.get_parameter("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"XML file not found: {file_path}")

            with open(path, "r", encoding=encoding) as f:
                xml_string = f.read()

            tree = DefusedET.parse(path)
            root = tree.getroot()

            context.set_variable("_xml_root", root)
            context.set_variable("_xml_tree", tree)

            self.set_output_value("root_tag", root.tag)
            self.set_output_value("xml_string", xml_string)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"root_tag": root.tag},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties(
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="File encoding for output",
    ),
    PropertyDef(
        "pretty_print",
        PropertyType.BOOLEAN,
        default=True,
        label="Pretty Print",
        tooltip="Format output with indentation",
    ),
    PropertyDef(
        "xml_declaration",
        PropertyType.BOOLEAN,
        default=True,
        label="XML Declaration",
        tooltip="Include <?xml version...?> declaration",
    ),
)
class WriteXMLFileNode(BaseNode):
    """
    Write XML to a file.

    Config:
        encoding: File encoding (default: utf-8)
        pretty_print: Format output with indentation (default: True)
        xml_declaration: Include XML declaration (default: True)

    Inputs:
        file_path: Path to write to
        xml_string: XML content to write

    Outputs:
        file_path: Written file path
        success: Whether operation succeeded
    """

    # @category: data
    # @requires: xml
    # @ports: file_path, xml_string -> file_path, success

    def __init__(self, node_id: str, name: str = "Write XML File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteXMLFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_input_port("xml_string", DataType.STRING)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = str(self.get_parameter("file_path", "") or "")
            xml_string = str(self.get_parameter("xml_string", "") or "")
            encoding = self.get_parameter("encoding", "utf-8")
            pretty_print = self.get_parameter("pretty_print", True)
            xml_declaration = self.get_parameter("xml_declaration", True)

            if not file_path:
                raise ValueError("file_path is required")
            if not xml_string:
                raise ValueError("xml_string is required")

            path = Path(file_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Parse and optionally pretty print
            if pretty_print:
                try:
                    parsed = safe_parseString(xml_string)
                    xml_string = parsed.toprettyxml(indent="  ", encoding=None)
                    if isinstance(xml_string, bytes):
                        xml_string = xml_string.decode(encoding)
                except Exception:
                    pass  # Keep original if pretty print fails

            # Add XML declaration if requested
            if xml_declaration and not xml_string.startswith("<?xml"):
                xml_string = (
                    f'<?xml version="1.0" encoding="{encoding}"?>\n' + xml_string
                )

            with open(path, "w", encoding=encoding) as f:
                f.write(xml_string)

            self.set_output_value("file_path", str(path))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties()  # Input port driven
class XPathQueryNode(BaseNode):
    """
    Query XML using XPath.

    Inputs:
        xml_string: XML to query (or uses last parsed XML from context)
        xpath: XPath expression

    Outputs:
        results: List of matching elements (as dicts with tag, text, attrib)
        count: Number of matches
        first_text: Text of first match
        success: Whether query succeeded
    """

    # @category: data
    # @requires: xml
    # @ports: xml_string, xpath -> results, count, first_text, success

    def __init__(self, node_id: str, name: str = "XPath Query", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "XPathQueryNode"

    def _define_ports(self) -> None:
        self.add_input_port("xml_string", DataType.STRING)
        self.add_input_port("xpath", DataType.STRING)
        self.add_output_port("results", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)
        self.add_output_port("first_text", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            xml_string = self.get_parameter("xml_string")
            xpath = str(self.get_parameter("xpath", "") or "")

            if not xpath:
                raise ValueError("xpath is required")

            # Get root element
            if xml_string:
                root = DefusedET.fromstring(xml_string)
            else:
                root = context.get_variable("_xml_root")
                if root is None:
                    raise ValueError(
                        "No XML available. Parse XML first or provide xml_string."
                    )

            # Execute XPath query
            elements = root.findall(xpath)

            # Convert to list of dicts
            results = []
            for elem in elements:
                results.append(
                    {
                        "tag": elem.tag,
                        "text": elem.text or "",
                        "attrib": dict(elem.attrib),
                        "tail": elem.tail or "",
                    }
                )

            first_text = elements[0].text if elements and elements[0].text else ""

            self.set_output_value("results", results)
            self.set_output_value("count", len(results))
            self.set_output_value("first_text", first_text)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(results)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("results", [])
            self.set_output_value("count", 0)
            self.set_output_value("first_text", "")
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties()  # Input port driven
class GetXMLElementNode(BaseNode):
    """
    Get XML element by tag name.

    Inputs:
        xml_string: XML to search (or uses context)
        tag_name: Tag name to find
        index: Index if multiple elements (default: 0)

    Outputs:
        tag: Element tag name
        text: Element text content
        attributes: Element attributes as dict
        child_count: Number of child elements
        found: Whether element was found
    """

    # @category: data
    # @requires: xml
    # @ports: xml_string, tag_name, index -> tag, text, attributes, child_count, found

    def __init__(self, node_id: str, name: str = "Get XML Element", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetXMLElementNode"

    def _define_ports(self) -> None:
        self.add_input_port("xml_string", DataType.STRING)
        self.add_input_port("tag_name", DataType.STRING)
        self.add_input_port("index", DataType.INTEGER)
        self.add_output_port("tag", DataType.STRING)
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("attributes", DataType.DICT)
        self.add_output_port("child_count", DataType.INTEGER)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            xml_string = self.get_parameter("xml_string")
            tag_name = str(self.get_parameter("tag_name", "") or "")
            index = safe_int(self.get_parameter("index", 0), 0)

            if not tag_name:
                raise ValueError("tag_name is required")

            if xml_string:
                root = DefusedET.fromstring(xml_string)
            else:
                root = context.get_variable("_xml_root")
                if root is None:
                    raise ValueError("No XML available")

            # Find elements
            elements = root.findall(f".//{tag_name}")

            if elements and 0 <= index < len(elements):
                elem = elements[index]
                self.set_output_value("tag", elem.tag)
                self.set_output_value("text", elem.text or "")
                self.set_output_value("attributes", dict(elem.attrib))
                self.set_output_value("child_count", len(list(elem)))
                self.set_output_value("found", True)
            else:
                self.set_output_value("tag", "")
                self.set_output_value("text", "")
                self.set_output_value("attributes", {})
                self.set_output_value("child_count", 0)
                self.set_output_value("found", False)

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"found": self.get_output_value("found")},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("found", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties()  # Input port driven
class GetXMLAttributeNode(BaseNode):
    """
    Get an attribute value from an XML element.

    Inputs:
        xml_string: XML to search (or uses context)
        xpath: XPath to element
        attribute_name: Attribute name to get

    Outputs:
        value: Attribute value
        found: Whether attribute was found
    """

    # @category: data
    # @requires: xml
    # @ports: xml_string, xpath, attribute_name -> value, found

    def __init__(self, node_id: str, name: str = "Get XML Attribute", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetXMLAttributeNode"

    def _define_ports(self) -> None:
        self.add_input_port("xml_string", DataType.STRING)
        self.add_input_port("xpath", DataType.STRING)
        self.add_input_port("attribute_name", DataType.STRING)
        self.add_output_port("value", DataType.STRING)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            xml_string = self.get_parameter("xml_string")
            xpath = str(self.get_parameter("xpath", ".") or ".")
            attribute_name = str(self.get_parameter("attribute_name", "") or "")

            if not attribute_name:
                raise ValueError("attribute_name is required")

            if xml_string:
                root = DefusedET.fromstring(xml_string)
            else:
                root = context.get_variable("_xml_root")
                if root is None:
                    raise ValueError("No XML available")

            elem = root.find(xpath)

            if elem is not None and attribute_name in elem.attrib:
                self.set_output_value("value", elem.attrib[attribute_name])
                self.set_output_value("found", True)
            else:
                self.set_output_value("value", "")
                self.set_output_value("found", False)

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"found": self.get_output_value("found")},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("found", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties(
    PropertyDef(
        "include_attributes",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Attributes",
        tooltip="Include element attributes in JSON output",
    ),
    PropertyDef(
        "text_key",
        PropertyType.STRING,
        default="#text",
        label="Text Key",
        tooltip="Key name for element text content in JSON",
    ),
)
class XMLToJsonNode(BaseNode):
    """
    Convert XML to JSON.

    Config:
        include_attributes: Include @attributes in output (default: True)
        text_key: Key name for text content (default: '#text')

    Inputs:
        xml_string: XML to convert

    Outputs:
        json_data: Converted JSON data (as dict)
        json_string: JSON as string
        success: Whether conversion succeeded
    """

    # @category: data
    # @requires: xml
    # @ports: xml_string -> json_data, json_string, success

    def __init__(self, node_id: str, name: str = "XML to JSON", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "XMLToJsonNode"

    def _define_ports(self) -> None:
        self.add_input_port("xml_string", DataType.STRING)
        self.add_output_port("json_data", DataType.DICT)
        self.add_output_port("json_string", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            xml_string = str(self.get_parameter("xml_string", "") or "")
            include_attributes = self.get_parameter("include_attributes", True)
            text_key = self.get_parameter("text_key", "#text")

            if not xml_string:
                raise ValueError("xml_string is required")

            root = DefusedET.fromstring(xml_string)

            def element_to_dict(elem):
                result = {}

                # Add attributes
                if include_attributes and elem.attrib:
                    result["@attributes"] = dict(elem.attrib)

                # Add text content
                if elem.text and elem.text.strip():
                    if len(list(elem)) == 0 and not result:
                        return elem.text.strip()
                    result[text_key] = elem.text.strip()

                # Add children
                for child in elem:
                    child_data = element_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data

                return result if result else ""

            json_data = {root.tag: element_to_dict(root)}
            json_string = json.dumps(json_data, indent=2, ensure_ascii=False)

            self.set_output_value("json_data", json_data)
            self.set_output_value("json_string", json_string)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("json_data", {})
            self.set_output_value("json_string", "")
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node(category="data")
@properties(
    PropertyDef(
        "root_tag",
        PropertyType.STRING,
        default="root",
        label="Root Tag",
        tooltip="Name of the root XML element",
    ),
    PropertyDef(
        "pretty_print",
        PropertyType.BOOLEAN,
        default=True,
        label="Pretty Print",
        tooltip="Format XML output with indentation",
    ),
)
class JsonToXMLNode(BaseNode):
    """
    Convert JSON to XML.

    Config:
        root_tag: Root element tag name (default: 'root')
        pretty_print: Format output (default: True)

    Inputs:
        json_data: JSON data to convert (dict or string)

    Outputs:
        xml_string: Converted XML string
        success: Whether conversion succeeded
    """

    # @category: data
    # @requires: xml
    # @ports: json_data -> xml_string, success

    def __init__(self, node_id: str, name: str = "JSON to XML", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "JsonToXMLNode"

    def _define_ports(self) -> None:
        self.add_input_port("json_data", DataType.ANY)
        self.add_output_port("xml_string", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            json_data = self.get_parameter("json_data")
            root_tag = self.get_parameter("root_tag", "root")
            pretty_print = self.get_parameter("pretty_print", True)

            if json_data is None:
                raise ValueError("json_data is required")

            # Parse if string
            if isinstance(json_data, str):
                json_data = json.loads(json_data)

            def dict_to_xml(data, parent):
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == "@attributes":
                            for attr_name, attr_value in value.items():
                                parent.set(attr_name, str(attr_value))
                        elif key == "#text":
                            parent.text = str(value)
                        elif isinstance(value, list):
                            for item in value:
                                child = ET.SubElement(parent, key)
                                dict_to_xml(item, child)
                        else:
                            child = ET.SubElement(parent, key)
                            dict_to_xml(value, child)
                elif isinstance(data, list):
                    for item in data:
                        child = ET.SubElement(parent, "item")
                        dict_to_xml(item, child)
                else:
                    parent.text = str(data) if data is not None else ""

            root = ET.Element(root_tag)
            dict_to_xml(json_data, root)

            xml_string = ET.tostring(root, encoding="unicode")

            if pretty_print:
                try:
                    parsed = safe_parseString(xml_string)
                    xml_string = parsed.toprettyxml(indent="  ")
                    # Remove extra newlines
                    lines = [line for line in xml_string.split("\n") if line.strip()]
                    xml_string = "\n".join(lines)
                except Exception:
                    pass

            self.set_output_value("xml_string", xml_string)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("xml_string", "")
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

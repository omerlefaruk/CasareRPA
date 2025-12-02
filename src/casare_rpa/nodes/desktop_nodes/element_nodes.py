"""
Desktop Element Interaction Nodes

Nodes for finding and interacting with Windows desktop UI elements.
"""

from typing import Any, Dict
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode as Node
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import NodeStatus, PortType, DataType


@executable_node
@node_schema(
    PropertyDef(
        "selector",
        PropertyType.JSON,
        required=False,
        label="Selector",
        tooltip="Element selector dictionary with 'strategy' and 'value'",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for element",
    ),
    PropertyDef(
        "throw_on_not_found",
        PropertyType.BOOLEAN,
        default=True,
        label="Throw on Not Found",
        tooltip="Raise error if element is not found",
    ),
)
class FindElementNode(Node):
    """
    Find a desktop UI element within a window.

    Uses selector to locate an element for further automation.

    Config (via @node_schema):
        selector: Element selector dictionary (can also be input port)
        timeout: Maximum time to wait for element (default: 5.0 seconds)
        throw_on_not_found: Raise error if not found (default: True)

    Inputs:
        window: Parent window object
        selector: Element selector dictionary

    Outputs:
        element: Found element object
        found: Boolean indicating if element was found
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Find Element"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Find Element",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FindElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)

        # Output ports
        self.add_output_port("element", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("found", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - find element.

        Args:
            context: Execution context

        Returns:
            Dictionary with element and found status
        """
        # Get inputs
        window = self.get_input_value("window")
        selector = self.get_parameter("selector", context)

        # Get configuration
        timeout = self.get_parameter("timeout", context)
        throw_on_not_found = self.get_parameter("throw_on_not_found", context)

        # Validate inputs
        if not window:
            error_msg = "Window is required. Connect a window from Launch Application or Activate Window node."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        if not selector:
            error_msg = "Selector is required. Provide a selector dictionary with 'strategy' and 'value'."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        logger.info(f"[{self.name}] Finding element with selector: {selector}")
        logger.debug(f"[{self.name}] Timeout: {timeout}s")

        try:
            # Find element
            element = window.find_child(selector, timeout=timeout)

            if element:
                logger.info(f"[{self.name}] Found element: {element}")
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "element": element,
                    "found": True,
                    "next_nodes": ["exec_out"],
                }
            else:
                if throw_on_not_found:
                    error_msg = f"Element not found with selector: {selector}"
                    logger.error(f"[{self.name}] {error_msg}")
                    self.status = NodeStatus.ERROR
                    raise RuntimeError(error_msg)
                else:
                    logger.warning(
                        f"[{self.name}] Element not found, but throw_on_not_found is False"
                    )
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "element": None,
                        "found": False,
                        "next_nodes": ["exec_out"],
                    }

        except Exception as e:
            error_msg = f"Failed to find element: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "selector",
        PropertyType.JSON,
        required=False,
        label="Selector",
        tooltip="Element selector dictionary (if element not provided directly)",
    ),
    PropertyDef(
        "simulate",
        PropertyType.BOOLEAN,
        default=False,
        label="Simulate",
        tooltip="Use simulated click (programmatic) vs physical mouse click",
    ),
    PropertyDef(
        "x_offset",
        PropertyType.INTEGER,
        default=0,
        label="X Offset",
        tooltip="Horizontal offset from element center",
    ),
    PropertyDef(
        "y_offset",
        PropertyType.INTEGER,
        default=0,
        label="Y Offset",
        tooltip="Vertical offset from element center",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for element (if finding by selector)",
    ),
)
class ClickElementNode(Node):
    """
    Click a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @node_schema):
        selector: Element selector (if element not provided)
        simulate: Use simulated click (default: False)
        x_offset: Horizontal offset from center (default: 0)
        y_offset: Vertical offset from center (default: 0)
        timeout: Wait time for element (default: 5.0 seconds)

    Inputs:
        element: Element to click (direct)
        window: Parent window (for selector-based finding)
        selector: Element selector (for finding)

    Outputs:
        success: Whether the click succeeded
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Click Element"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Click Element",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClickElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)

        # Output ports
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - click element.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get element - directly or via window+selector
        element = self.get_input_value("element")

        if not element:
            window = self.get_input_value("window")
            selector = self.get_parameter("selector", context)

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.get_parameter("timeout", context)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        # Get configuration
        simulate = self.get_parameter("simulate", context)
        x_offset = self.get_parameter("x_offset", context)
        y_offset = self.get_parameter("y_offset", context)

        logger.info(f"[{self.name}] Clicking element: {element}")
        logger.debug(
            f"[{self.name}] simulate={simulate}, offset=({x_offset}, {y_offset})"
        )

        try:
            # Perform click
            element.click(simulate=simulate, x_offset=x_offset, y_offset=y_offset)

            logger.info(f"[{self.name}] Click successful")
            self.status = NodeStatus.SUCCESS
            return {"success": True, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"Failed to click element: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "text",
        PropertyType.STRING,
        default="",
        label="Text",
        tooltip="Text to type into the element",
    ),
    PropertyDef(
        "selector",
        PropertyType.JSON,
        required=False,
        label="Selector",
        tooltip="Element selector (if element not provided directly)",
    ),
    PropertyDef(
        "clear_first",
        PropertyType.BOOLEAN,
        default=False,
        label="Clear First",
        tooltip="Clear existing text before typing",
    ),
    PropertyDef(
        "interval",
        PropertyType.FLOAT,
        default=0.01,
        min_value=0.0,
        label="Interval (seconds)",
        tooltip="Delay between keystrokes",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for element (if finding by selector)",
    ),
)
class TypeTextNode(Node):
    """
    Type text into a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @node_schema):
        text: Text to type (can also be input port)
        selector: Element selector (if element not provided)
        clear_first: Clear existing text (default: False)
        interval: Delay between keystrokes (default: 0.01 seconds)
        timeout: Wait time for element (default: 5.0 seconds)

    Inputs:
        text: Text to type
        element: Element to type into (direct)
        window: Parent window (for selector-based finding)
        selector: Element selector (for finding)

    Outputs:
        success: Whether the operation succeeded
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Type Text"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Type Text",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TypeTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - type text.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get text to type
        text = self.get_parameter("text", context)

        if not text:
            error_msg = "Text is required. Provide text to type."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        # Get element - directly or via window+selector
        element = self.get_input_value("element")

        if not element:
            window = self.get_input_value("window")
            selector = self.get_parameter("selector", context)

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.get_parameter("timeout", context)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        # Get configuration
        clear_first = self.get_parameter("clear_first", context)
        interval = self.get_parameter("interval", context)

        logger.info(f"[{self.name}] Typing text into element: {element}")
        logger.debug(
            f"[{self.name}] Text length: {len(text)}, clear_first={clear_first}"
        )

        try:
            # Type text
            element.type_text(text=text, clear_first=clear_first, interval=interval)

            logger.info(f"[{self.name}] Text typed successfully")
            self.status = NodeStatus.SUCCESS
            return {"success": True, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"Failed to type text: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "selector",
        PropertyType.JSON,
        required=False,
        label="Selector",
        tooltip="Element selector (if element not provided directly)",
    ),
    PropertyDef(
        "variable_name",
        PropertyType.STRING,
        default="",
        label="Variable Name",
        tooltip="Store text in this context variable",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for element (if finding by selector)",
    ),
)
class GetElementTextNode(Node):
    """
    Get text content from a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @node_schema):
        selector: Element selector (if element not provided)
        variable_name: Store text in this variable (default: "")
        timeout: Wait time for element (default: 5.0 seconds)

    Inputs:
        element: Element to get text from (direct)
        window: Parent window (for selector-based finding)
        selector: Element selector (for finding)

    Outputs:
        text: The extracted text content
        element: The element object
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Get Element Text"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Get Element Text",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetElementTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)

        # Output ports
        self.add_output_port("text", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("element", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - get element text.

        Args:
            context: Execution context

        Returns:
            Dictionary with text and element
        """
        # Get element - directly or via window+selector
        element = self.get_input_value("element")

        if not element:
            window = self.get_input_value("window")
            selector = self.get_parameter("selector", context)

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.get_parameter("timeout", context)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        logger.info(f"[{self.name}] Getting text from element: {element}")

        try:
            # Get text
            text = element.get_text()

            logger.info(
                f"[{self.name}] Got text: '{text[:50]}...' ({len(text)} chars)"
                if len(text) > 50
                else f"[{self.name}] Got text: '{text}'"
            )

            # Store in context variable if specified
            variable_name = self.get_parameter("variable_name", context)
            if variable_name and hasattr(context, "set_variable"):
                context.set_variable(variable_name, text)
                logger.debug(f"[{self.name}] Stored text in variable: {variable_name}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "text": text,
                "element": element,
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Failed to get element text: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "property_name",
        PropertyType.STRING,
        default="Name",
        required=True,
        label="Property Name",
        tooltip="Name of the property to get (e.g., Name, Value, IsEnabled)",
    ),
    PropertyDef(
        "selector",
        PropertyType.JSON,
        required=False,
        label="Selector",
        tooltip="Element selector (if element not provided directly)",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for element (if finding by selector)",
    ),
)
class GetElementPropertyNode(Node):
    """
    Get a property value from a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @node_schema):
        property_name: Name of the property to get (default: "Name")
        selector: Element selector (if element not provided)
        timeout: Wait time for element (default: 5.0 seconds)

    Inputs:
        property_name: Property to retrieve (can override config)
        element: Element to get property from (direct)
        window: Parent window (for selector-based finding)
        selector: Element selector (for finding)

    Outputs:
        value: The property value
        element: The element object
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Get Element Property"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Get Element Property",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetElementPropertyNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)
        self.add_input_port("property_name", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("value", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("element", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - get element property.

        Args:
            context: Execution context

        Returns:
            Dictionary with property value and element
        """
        # Get property name
        property_name = self.get_parameter("property_name", context)

        # Get element - directly or via window+selector
        element = self.get_input_value("element")

        if not element:
            window = self.get_input_value("window")
            selector = self.get_parameter("selector", context)

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.get_parameter("timeout", context)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        logger.info(
            f"[{self.name}] Getting property '{property_name}' from element: {element}"
        )

        try:
            # Get property
            value = element.get_property(property_name)

            logger.info(f"[{self.name}] Got property '{property_name}': {value}")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "value": value,
                "element": element,
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Failed to get element property '{property_name}': {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)

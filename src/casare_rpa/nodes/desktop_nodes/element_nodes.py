"""
Desktop Element Interaction Nodes

Nodes for finding and interacting with Windows desktop UI elements.
"""

from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, NodeStatus
from casare_rpa.nodes.desktop_nodes.desktop_base import (
    DesktopNodeBase,
    ElementInteractionMixin,
)
from casare_rpa.nodes.desktop_nodes.properties import (
    CLEAR_FIRST_PROP,
    INTERVAL_PROP,
    SELECTOR_PROP,
    SIMULATE_PROP,
    TEXT_PROP,
    THROW_ON_NOT_FOUND_PROP,
    TIMEOUT_PROP,
    VARIABLE_NAME_PROP,
    X_OFFSET_PROP,
    Y_OFFSET_PROP,
)

# Custom property for property_name (specific to GetElementPropertyNode)
PROPERTY_NAME_PROP = PropertyDef(
    "property_name",
    PropertyType.STRING,
    default="Name",
    required=True,
    label="Property Name",
    tooltip="Name of the property to get (e.g., Name, Value, IsEnabled)",
    tab="properties",
)


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Parent window object",
    ),
    SELECTOR_PROP,
    TIMEOUT_PROP,
    THROW_ON_NOT_FOUND_PROP,
)
@node(category="desktop")
class FindElementNode(DesktopNodeBase):
    """
    Find a desktop UI element within a window.

    Uses selector to locate an element for further automation.

    Config (via @properties):
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

    # @category: desktop
    # @requires: none
    # @ports: window, selector -> element, found

    NODE_NAME = "Find Element"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Find Element",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "FindElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_input_port("selector", DataType.ANY)
        self.add_output_port("element", DataType.ANY)
        self.add_output_port("found", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - find element."""
        window = self.get_input_value("window")
        selector = self.get_parameter("selector", context)
        timeout = self.get_parameter("timeout", context)
        throw_on_not_found = self.get_parameter("throw_on_not_found", context)

        if not window:
            error_msg = "Window is required. Connect a window from Launch Application or Activate Window node."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        if not selector:
            error_msg = (
                "Selector is required. Provide a selector dictionary with 'strategy' and 'value'."
            )
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        logger.info(f"[{self.name}] Finding element with selector: {selector}")
        logger.debug(f"[{self.name}] Timeout: {timeout}s")

        try:
            element = window.find_child(selector, timeout=timeout)

            if element:
                logger.info(f"[{self.name}] Found element: {element}")
                return self.success_result(element=element, found=True)
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
                    return self.success_result(element=None, found=False)

        except Exception as e:
            self.handle_error(e, "find element")
            return {"success": False, "data": {}, "next_nodes": []}


@properties(
    SELECTOR_PROP,
    SIMULATE_PROP,
    X_OFFSET_PROP,
    Y_OFFSET_PROP,
    TIMEOUT_PROP,
)
@node(category="desktop")
class ClickElementNode(DesktopNodeBase, ElementInteractionMixin):
    """
    Click a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @properties):
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

    # @category: desktop
    # @requires: none
    # @ports: element, window, selector -> success

    NODE_NAME = "Click Element"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Click Element",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "ClickElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Can target by element directly OR by window+selector - all optional but one path needed
        self.add_input_port("element", DataType.ANY, required=False)
        self.add_input_port("window", DataType.ANY, required=False)
        self.add_input_port("selector", DataType.ANY, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - click element."""
        desktop_ctx = self.get_desktop_context(context)
        timeout = self.get_parameter("timeout", context)

        try:
            element = await self.find_element_from_inputs(context, desktop_ctx, timeout)
        except ValueError as e:
            logger.error(f"[{self.name}] {e}")
            self.status = NodeStatus.ERROR
            raise
        except RuntimeError as e:
            logger.error(f"[{self.name}] {e}")
            self.status = NodeStatus.ERROR
            raise

        simulate = self.get_parameter("simulate", context)
        x_offset = self.get_parameter("x_offset", context)
        y_offset = self.get_parameter("y_offset", context)

        logger.info(f"[{self.name}] Clicking element: {element}")
        logger.debug(f"[{self.name}] simulate={simulate}, offset=({x_offset}, {y_offset})")

        try:
            element.click(simulate=simulate, x_offset=x_offset, y_offset=y_offset)
            logger.info(f"[{self.name}] Click successful")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, "click element")
            return {"success": False, "data": {}, "next_nodes": []}


@properties(
    TEXT_PROP,
    SELECTOR_PROP,
    CLEAR_FIRST_PROP,
    INTERVAL_PROP,
    TIMEOUT_PROP,
)
@node(category="desktop")
class TypeTextNode(DesktopNodeBase, ElementInteractionMixin):
    """
    Type text into a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @properties):
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

    # @category: desktop
    # @requires: none
    # @ports: element, window, selector, text -> success

    NODE_NAME = "Type Text"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Type Text",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "TypeTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Can target by element directly OR by window+selector - all optional but one path needed
        self.add_input_port("element", DataType.ANY, required=False)
        self.add_input_port("window", DataType.ANY, required=False)
        self.add_input_port("selector", DataType.ANY, required=False)
        self.add_input_port("text", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - type text."""
        text = self.get_parameter("text", context)

        if not text:
            error_msg = "Text is required. Provide text to type."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        desktop_ctx = self.get_desktop_context(context)
        timeout = self.get_parameter("timeout", context)

        try:
            element = await self.find_element_from_inputs(context, desktop_ctx, timeout)
        except (ValueError, RuntimeError) as e:
            logger.error(f"[{self.name}] {e}")
            self.status = NodeStatus.ERROR
            raise

        clear_first = self.get_parameter("clear_first", context)
        interval = self.get_parameter("interval", context)

        logger.info(f"[{self.name}] Typing text into element: {element}")
        logger.debug(f"[{self.name}] Text length: {len(text)}, clear_first={clear_first}")

        try:
            element.type_text(text=text, clear_first=clear_first, interval=interval)
            logger.info(f"[{self.name}] Text typed successfully")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, "type text")
            return {"success": False, "data": {}, "next_nodes": []}


@properties(
    SELECTOR_PROP,
    VARIABLE_NAME_PROP,
    TIMEOUT_PROP,
)
@node(category="desktop")
class GetElementTextNode(DesktopNodeBase, ElementInteractionMixin):
    """
    Get text content from a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @properties):
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

    # @category: desktop
    # @requires: none
    # @ports: element, window, selector -> text, element

    NODE_NAME = "Get Element Text"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Get Element Text",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "GetElementTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Can target by element directly OR by window+selector - all optional but one path needed
        self.add_input_port("element", DataType.ANY, required=False)
        self.add_input_port("window", DataType.ANY, required=False)
        self.add_input_port("selector", DataType.ANY, required=False)
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("element", DataType.ANY)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - get element text."""
        desktop_ctx = self.get_desktop_context(context)
        timeout = self.get_parameter("timeout", context)

        try:
            element = await self.find_element_from_inputs(context, desktop_ctx, timeout)
        except (ValueError, RuntimeError) as e:
            logger.error(f"[{self.name}] {e}")
            self.status = NodeStatus.ERROR
            raise

        logger.info(f"[{self.name}] Getting text from element: {element}")

        try:
            text = element.get_text()

            log_text = f"'{text[:50]}...' ({len(text)} chars)" if len(text) > 50 else f"'{text}'"
            logger.info(f"[{self.name}] Got text: {log_text}")

            # Store in context variable if specified
            variable_name = self.get_parameter("variable_name", context)
            if variable_name and hasattr(context, "set_variable"):
                context.set_variable(variable_name, text)
                logger.debug(f"[{self.name}] Stored text in variable: {variable_name}")

            return self.success_result(text=text, element=element)
        except Exception as e:
            self.handle_error(e, "get element text")
            return {"success": False, "data": {}, "next_nodes": []}


@properties(
    PROPERTY_NAME_PROP,
    SELECTOR_PROP,
    TIMEOUT_PROP,
)
@node(category="desktop")
class GetElementPropertyNode(DesktopNodeBase, ElementInteractionMixin):
    """
    Get a property value from a desktop UI element.

    Can accept an element directly or find it using window + selector.

    Config (via @properties):
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

    # @category: desktop
    # @requires: none
    # @ports: element, window, selector, property_name -> value, element

    NODE_NAME = "Get Element Property"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Get Element Property",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "GetElementPropertyNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Can target by element directly OR by window+selector - all optional but one path needed
        self.add_input_port("element", DataType.ANY, required=False)
        self.add_input_port("window", DataType.ANY, required=False)
        self.add_input_port("selector", DataType.ANY, required=False)
        self.add_input_port("property_name", DataType.STRING)
        self.add_output_port("value", DataType.ANY)
        self.add_output_port("element", DataType.ANY)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - get element property."""
        property_name = self.get_parameter("property_name", context)
        desktop_ctx = self.get_desktop_context(context)
        timeout = self.get_parameter("timeout", context)

        try:
            element = await self.find_element_from_inputs(context, desktop_ctx, timeout)
        except (ValueError, RuntimeError) as e:
            logger.error(f"[{self.name}] {e}")
            self.status = NodeStatus.ERROR
            raise

        logger.info(f"[{self.name}] Getting property '{property_name}' from element: {element}")

        try:
            value = element.get_property(property_name)
            logger.info(f"[{self.name}] Got property '{property_name}': {value}")
            return self.success_result(value=value, element=element)
        except Exception as e:
            self.handle_error(e, f"get element property '{property_name}'")
            return {"success": False, "data": {}, "next_nodes": []}

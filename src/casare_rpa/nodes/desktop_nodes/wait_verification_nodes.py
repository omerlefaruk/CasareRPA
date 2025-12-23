"""
Wait and Verification Nodes

Provides nodes for waiting and verifying desktop element states:
- WaitForElementNode: Wait for element to appear/disappear/enable/disable
- WaitForWindowNode: Wait for window to appear/disappear
- VerifyElementExistsNode: Check if element exists
- VerifyElementPropertyNode: Verify element property value
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, NodeStatus

from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    TIMEOUT_LONG_PROP,
    TIMEOUT_PROP,
    WAIT_STATE_PROP,
    POLL_INTERVAL_PROP,
    COMPARISON_PROP,
    SELECTOR_PROP,
)


@properties(
    SELECTOR_PROP,
    TIMEOUT_LONG_PROP,
    WAIT_STATE_PROP,
    POLL_INTERVAL_PROP,
)
@node(category="desktop")
class WaitForElementNode(DesktopNodeBase):
    """
    Wait for an element to reach a specific state.

    Config (via @properties):
        timeout: Maximum wait time in seconds (default: 10.0)
        state: State to wait for - visible/hidden/enabled/disabled (default: "visible")
        poll_interval: Interval between checks (default: 0.5)

    Inputs:
        selector: Element selector dictionary
        timeout: Maximum wait time (overrides config)

    Outputs:
        element: Found element (if visible/enabled)
        success: Whether wait succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: selector, timeout -> element, success

    NODE_NAME = "Wait For Element"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Wait For Element",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "WaitForElementNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("selector", DataType.ANY)
        self.add_input_port("timeout", DataType.FLOAT)
        self.add_output_port("element", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute wait for element."""
        selector = self.get_input_value("selector")
        timeout = self.get_parameter("timeout", context)
        state = self.get_parameter("state", context)
        poll_interval = self.get_parameter("poll_interval", context)

        if not selector:
            raise ValueError("Element selector is required")

        desktop_ctx = self.require_desktop_context(context)

        logger.info(f"[{self.name}] Waiting for element state: {state}")

        try:
            element = await desktop_ctx.async_wait_for_element(
                selector=selector,
                timeout=float(timeout),
                state=state,
                poll_interval=float(poll_interval),
            )

            self.set_output_value("element", element)
            self.set_output_value("success", True)

            return self.success_result(element=element, state=state, timeout=timeout)

        except TimeoutError as e:
            self.set_output_value("element", None)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR

            return self.error_result(str(e), state=state, timeout=timeout)


@properties(
    PropertyDef(
        "title",
        PropertyType.STRING,
        required=False,
        label="Window Title",
        tooltip="Window title to match (partial match)",
    ),
    PropertyDef(
        "title_regex",
        PropertyType.STRING,
        required=False,
        label="Title Regex",
        tooltip="Regex pattern to match window title",
    ),
    PropertyDef(
        "class_name",
        PropertyType.STRING,
        required=False,
        label="Class Name",
        tooltip="Window class name",
    ),
    TIMEOUT_LONG_PROP,
    WAIT_STATE_PROP,
    POLL_INTERVAL_PROP,
)
@node(category="desktop")
class WaitForWindowNode(DesktopNodeBase):
    """
    Wait for a window to reach a specific state.

    Config (via @properties):
        timeout: Maximum wait time in seconds (default: 10.0)
        state: State to wait for - visible/hidden (default: "visible")
        poll_interval: Interval between checks (default: 0.5)

    Inputs:
        title: Window title (partial match)
        title_regex: Window title regex pattern
        class_name: Window class name
        timeout: Maximum wait time (overrides config)

    Outputs:
        window: Found window (if visible)
        success: Whether wait succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: title, title_regex, class_name, timeout -> window, success

    NODE_NAME = "Wait For Window"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Wait For Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "WaitForWindowNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("title", DataType.STRING)
        self.add_input_port("title_regex", DataType.STRING)
        self.add_input_port("class_name", DataType.STRING)
        self.add_input_port("timeout", DataType.FLOAT)
        self.add_output_port("window", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute wait for window."""
        title = self.resolve_variable(context, self.get_input_value("title"))
        title_regex = self.resolve_variable(context, self.get_input_value("title_regex"))
        class_name = self.resolve_variable(context, self.get_input_value("class_name"))
        timeout = self.get_parameter("timeout", context)
        state = self.get_parameter("state", context)
        poll_interval = self.get_parameter("poll_interval", context)

        if not title and not title_regex and not class_name:
            raise ValueError("Must provide at least one of: title, title_regex, class_name")

        desktop_ctx = self.require_desktop_context(context)

        logger.info(f"[{self.name}] Waiting for window state: {state}")

        try:
            window = await desktop_ctx.async_wait_for_window(
                title=title,
                title_regex=title_regex,
                class_name=class_name,
                timeout=float(timeout),
                state=state,
                poll_interval=float(poll_interval),
            )

            self.set_output_value("window", window)
            self.set_output_value("success", True)

            return self.success_result(window=window, state=state, timeout=timeout)

        except TimeoutError as e:
            self.set_output_value("window", None)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR

            return self.error_result(str(e), state=state, timeout=timeout)


@properties(
    SELECTOR_PROP,
    TIMEOUT_PROP,
)
@node(category="desktop")
class VerifyElementExistsNode(DesktopNodeBase):
    """
    Verify if an element exists.

    Config (via @properties):
        timeout: Maximum time to search (default: 0.0 for immediate)

    Inputs:
        selector: Element selector dictionary
        timeout: Maximum search time (overrides config)

    Outputs:
        exists: Whether element exists
        element: The element if found (None if not)
    """

    # @category: desktop
    # @requires: none
    # @ports: selector, timeout -> exists, element

    NODE_NAME = "Verify Element Exists"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Verify Element Exists",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "VerifyElementExistsNode"

    def _get_default_config(self) -> Dict[str, Any]:
        """Override default timeout to 0.0 for immediate check."""
        return {"timeout": 0.0}

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("selector", DataType.ANY)
        self.add_input_port("timeout", DataType.FLOAT)
        self.add_output_port("exists", DataType.BOOLEAN)
        self.add_output_port("element", DataType.ANY)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute element exists check."""
        selector = self.get_input_value("selector")
        timeout = self.get_parameter("timeout", context)

        if not selector:
            raise ValueError("Element selector is required")

        desktop_ctx = self.require_desktop_context(context)

        logger.info(f"[{self.name}] Checking if element exists")

        exists = desktop_ctx.element_exists(selector=selector, timeout=float(timeout))

        # Try to get the element if it exists
        element = None
        if exists:
            try:
                element = await desktop_ctx.async_wait_for_element(selector=selector, timeout=0.1)
            except Exception:
                pass

        self.set_output_value("exists", exists)
        self.set_output_value("element", element)

        return self.success_result(exists=exists, element=element)


@properties(
    PropertyDef(
        "element",
        PropertyType.ANY,
        required=True,
        label="Element",
        tooltip="Desktop element to verify",
    ),
    PropertyDef(
        "property_name",
        PropertyType.STRING,
        required=True,
        label="Property Name",
        tooltip="Name of the property to verify (e.g., text, name, enabled)",
    ),
    PropertyDef(
        "expected_value",
        PropertyType.ANY,
        required=True,
        label="Expected Value",
        tooltip="Expected value of the property",
    ),
    COMPARISON_PROP,
)
@node(category="desktop")
class VerifyElementPropertyNode(DesktopNodeBase):
    """
    Verify an element property has an expected value.

    Config (via @properties):
        comparison: Comparison type (default: "equals")
            Options: equals, contains, startswith, endswith, regex

    Inputs:
        element: DesktopElement to check
        property_name: Name of property to check
        expected_value: Expected value of the property

    Outputs:
        result: Whether verification passed
        actual_value: Actual property value
    """

    # @category: desktop
    # @requires: none
    # @ports: element, property_name, expected_value -> result, actual_value

    NODE_NAME = "Verify Element Property"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Verify Element Property",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "VerifyElementPropertyNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("element", DataType.ANY)
        self.add_input_port("property_name", DataType.STRING)
        self.add_input_port("expected_value", DataType.ANY)
        self.add_output_port("result", DataType.BOOLEAN)
        self.add_output_port("actual_value", DataType.ANY)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute property verification."""
        element = self.get_input_value("element")
        property_name = self.get_input_value("property_name")
        expected_value = self.get_input_value("expected_value")
        comparison = self.get_parameter("comparison", context)

        if not element:
            raise ValueError("Element is required")
        if not property_name:
            raise ValueError("Property name is required")

        desktop_ctx = self.require_desktop_context(context)

        logger.info(f"[{self.name}] Verifying property '{property_name}' with {comparison}")

        result = desktop_ctx.verify_element_property(
            element=element,
            property_name=property_name,
            expected_value=expected_value,
            comparison=comparison,
        )

        # Get actual value for output
        actual_value = None
        try:
            control = element._control
            actual_value = getattr(control, property_name, None)
            if actual_value is None:
                property_map = {
                    "text": control.Name,
                    "name": control.Name,
                    "class": control.ClassName,
                    "classname": control.ClassName,
                    "enabled": control.IsEnabled,
                    "isenabled": control.IsEnabled,
                }
                actual_value = property_map.get(property_name.lower())
        except Exception:
            pass

        self.set_output_value("result", result)
        self.set_output_value("actual_value", actual_value)
        self.status = NodeStatus.SUCCESS if result else NodeStatus.ERROR

        return self.success_result(
            result=result,
            actual_value=actual_value,
            expected_value=expected_value,
            property_name=property_name,
            comparison=comparison,
        )

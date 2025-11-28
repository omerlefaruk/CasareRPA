"""
Wait and Verification Nodes for CasareRPA

Provides nodes for waiting and verifying desktop element states:
- WaitForElementNode: Wait for element to appear/disappear/enable/disable
- WaitForWindowNode: Wait for window to appear/disappear
- VerifyElementExistsNode: Check if element exists
- VerifyElementPropertyNode: Verify element property value
"""

from typing import Any, Dict

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus
from casare_rpa.nodes.utils.type_converters import safe_int


class WaitForElementNode(BaseNode):
    """
    Node to wait for an element to reach a specific state.

    Inputs:
        - selector: Element selector dictionary
        - timeout: Maximum wait time in seconds
        - state: State to wait for (visible, hidden, enabled, disabled)

    Outputs:
        - element: Found element (if visible/enabled)
        - success: Whether wait succeeded
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Wait For Element",
    ):
        default_config = {"timeout": 10.0, "state": "visible", "poll_interval": 0.5}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "WaitForElementNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("selector", DataType.ANY, "Element selector")
        self.add_input_port("timeout", DataType.FLOAT, "Timeout in seconds")
        self.add_output_port("element", DataType.ANY, "Found element")
        self.add_output_port("success", DataType.BOOLEAN, "Wait succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute wait for element"""
        selector = self.get_input_value("selector")
        timeout = self.get_input_value("timeout") or self.config.get("timeout", 10.0)
        state = self.config.get("state", "visible")
        poll_interval = self.config.get("poll_interval", 0.5)

        if not selector:
            raise ValueError("Element selector is required")

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        try:
            # Use async method to avoid blocking event loop
            element = await desktop_ctx.async_wait_for_element(
                selector=selector,
                timeout=float(timeout),
                state=state,
                poll_interval=float(poll_interval),
            )

            self.set_output_value("element", element)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "element": element,
                "state": state,
                "timeout": timeout,
            }

        except TimeoutError as e:
            self.set_output_value("element", None)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR

            return {
                "success": False,
                "error": str(e),
                "state": state,
                "timeout": timeout,
            }


class WaitForWindowNode(BaseNode):
    """
    Node to wait for a window to reach a specific state.

    Inputs:
        - title: Window title (partial match)
        - title_regex: Window title regex pattern
        - class_name: Window class name
        - timeout: Maximum wait time in seconds

    Config:
        - state: State to wait for (visible, hidden)

    Outputs:
        - window: Found window (if visible)
        - success: Whether wait succeeded
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Wait For Window",
    ):
        default_config = {"timeout": 10.0, "state": "visible", "poll_interval": 0.5}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "WaitForWindowNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("title", DataType.STRING, "Window title")
        self.add_input_port("title_regex", DataType.STRING, "Title regex pattern")
        self.add_input_port("class_name", DataType.STRING, "Window class name")
        self.add_input_port("timeout", DataType.FLOAT, "Timeout in seconds")
        self.add_output_port("window", DataType.ANY, "Found window")
        self.add_output_port("success", DataType.BOOLEAN, "Wait succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute wait for window"""
        title = self.get_input_value("title")
        title_regex = self.get_input_value("title_regex")
        class_name = self.get_input_value("class_name")
        timeout = self.get_input_value("timeout") or self.config.get("timeout", 10.0)
        state = self.config.get("state", "visible")
        poll_interval = self.config.get("poll_interval", 0.5)

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if title:
                title = context.resolve_value(title)
            if title_regex:
                title_regex = context.resolve_value(title_regex)
            if class_name:
                class_name = context.resolve_value(class_name)

        if not title and not title_regex and not class_name:
            raise ValueError(
                "Must provide at least one of: title, title_regex, class_name"
            )

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        try:
            # Use async method to avoid blocking event loop
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
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "window": window,
                "state": state,
                "timeout": timeout,
            }

        except TimeoutError as e:
            self.set_output_value("window", None)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR

            return {
                "success": False,
                "error": str(e),
                "state": state,
                "timeout": timeout,
            }


class VerifyElementExistsNode(BaseNode):
    """
    Node to verify if an element exists.

    Inputs:
        - selector: Element selector dictionary
        - timeout: Maximum time to search (0 for immediate)

    Outputs:
        - exists: Whether element exists
        - element: The element if found (None if not)
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Verify Element Exists",
    ):
        default_config = {"timeout": 0.0}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "VerifyElementExistsNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("selector", DataType.ANY, "Element selector")
        self.add_input_port("timeout", DataType.FLOAT, "Search timeout")
        self.add_output_port("exists", DataType.BOOLEAN, "Element exists")
        self.add_output_port("element", DataType.ANY, "Found element")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute element exists check"""
        selector = self.get_input_value("selector")
        timeout = self.get_input_value("timeout") or self.config.get("timeout", 0.0)

        if not selector:
            raise ValueError("Element selector is required")

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        exists = desktop_ctx.element_exists(selector=selector, timeout=float(timeout))

        # Try to get the element if it exists (use async to avoid blocking)
        element = None
        if exists:
            try:
                element = await desktop_ctx.async_wait_for_element(
                    selector=selector, timeout=0.1
                )
            except Exception:
                pass

        self.set_output_value("exists", exists)
        self.set_output_value("element", element)
        self.status = NodeStatus.SUCCESS

        return {"success": True, "exists": exists, "element": element}


class VerifyElementPropertyNode(BaseNode):
    """
    Node to verify an element property has an expected value.

    Inputs:
        - element: DesktopElement to check
        - property_name: Name of property to check
        - expected_value: Expected value of the property

    Config:
        - comparison: Comparison type (equals, contains, startswith, etc.)

    Outputs:
        - result: Whether verification passed
        - actual_value: Actual property value
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Verify Element Property",
    ):
        default_config = {"comparison": "equals"}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "VerifyElementPropertyNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("element", DataType.ANY, "Element to check")
        self.add_input_port("property_name", DataType.STRING, "Property name")
        self.add_input_port("expected_value", DataType.ANY, "Expected value")
        self.add_output_port("result", DataType.BOOLEAN, "Verification result")
        self.add_output_port("actual_value", DataType.ANY, "Actual value")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute property verification"""
        element = self.get_input_value("element")
        property_name = self.get_input_value("property_name")
        expected_value = self.get_input_value("expected_value")
        comparison = self.config.get("comparison", "equals")

        if not element:
            raise ValueError("Element is required")
        if not property_name:
            raise ValueError("Property name is required")

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

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

        return {
            "success": True,
            "result": result,
            "actual_value": actual_value,
            "expected_value": expected_value,
            "property_name": property_name,
            "comparison": comparison,
        }

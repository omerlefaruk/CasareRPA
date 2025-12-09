"""
Desktop Advanced Interaction Nodes

Nodes for advanced interactions with Windows desktop UI elements:
dropdowns, checkboxes, radio buttons, tabs, tree items, and scrolling.
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.value_objects.types import PortType, DataType
from casare_rpa.domain.schemas import PropertyDef, PropertyType

from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase


# =============================================================================
# Interaction-specific PropertyDef constants
# =============================================================================

BY_TEXT_PROP = PropertyDef(
    "by_text",
    PropertyType.BOOLEAN,
    default=True,
    label="Select By Text",
    tooltip="Select by text (True) or by index (False)",
    tab="properties",
)

CHECK_PROP = PropertyDef(
    "check",
    PropertyType.BOOLEAN,
    default=True,
    label="Check",
    tooltip="Check (True) or uncheck (False)",
    tab="properties",
)

EXPAND_PROP = PropertyDef(
    "expand",
    PropertyType.BOOLEAN,
    default=True,
    label="Expand",
    tooltip="Expand (True) or collapse (False)",
    tab="properties",
)

TAB_NAME_PROP = PropertyDef(
    "tab_name",
    PropertyType.STRING,
    default="",
    label="Tab Name",
    tooltip="Name of the tab to select",
    tab="properties",
)

TAB_INDEX_PROP = PropertyDef(
    "tab_index",
    PropertyType.INTEGER,
    default=-1,
    label="Tab Index",
    tooltip="Index of the tab to select (-1 to use name)",
    tab="properties",
)

SCROLL_DIRECTION_PROP = PropertyDef(
    "direction",
    PropertyType.CHOICE,
    default="down",
    choices=["up", "down", "left", "right"],
    label="Scroll Direction",
    tooltip="Direction to scroll",
    tab="properties",
)

SCROLL_AMOUNT_PROP = PropertyDef(
    "amount",
    PropertyType.FLOAT,
    default=0.5,
    min_value=0.0,
    max_value=1.0,
    label="Scroll Amount",
    tooltip="Amount to scroll (0.0 to 1.0)",
    tab="properties",
)


class InteractionNodeBase(DesktopNodeBase):
    """
    Base class for element interaction nodes.

    Provides common element handling patterns.
    """

    # @category: desktop
    # @requires: none
    # @ports: none -> none

    def get_element_from_input(self) -> Any:
        """
        Get element from input port.

        Returns:
            Element object

        Raises:
            ValueError: If element not provided
        """
        element = self.get_input_value("element")
        if not element:
            raise ValueError(f"{self._element_type()} element is required")
        return element

    def _element_type(self) -> str:
        """Return element type name for error messages."""
        return "Element"


@node_schema(BY_TEXT_PROP)
@executable_node
class SelectFromDropdownNode(InteractionNodeBase):
    """
    Select an item from a dropdown/combobox.

    Supports selection by text (partial or exact match) or by index.

    Config (via @node_schema):
        by_text: Select by text vs index (default: True)

    Inputs:
        element: Dropdown element
        value: Value to select (text or index)

    Outputs:
        success: Whether selection succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: element, value -> success

    NODE_NAME = "Select From Dropdown"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Select From Dropdown",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "SelectFromDropdownNode"

    def _element_type(self) -> str:
        return "Dropdown"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("value", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - select from dropdown."""
        element = self.get_element_from_input()
        value = self.get_parameter("value", context)
        by_text = self.get_parameter("by_text", context)

        if not value:
            raise ValueError("Value to select is required")

        logger.info(f"[{self.name}] Selecting '{value}' from dropdown")

        desktop_ctx = self.get_desktop_context(context)

        try:
            desktop_ctx.select_from_dropdown(element, value, by_text=by_text)
            logger.info(f"[{self.name}] Successfully selected '{value}'")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, "select from dropdown")


@node_schema(CHECK_PROP)
@executable_node
class CheckCheckboxNode(InteractionNodeBase):
    """
    Check or uncheck a checkbox.

    Uses TogglePattern for reliable checkbox interaction.

    Config (via @node_schema):
        check: Check vs uncheck (default: True)

    Inputs:
        element: Checkbox element

    Outputs:
        success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: element -> success

    NODE_NAME = "Check Checkbox"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Check Checkbox",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "CheckCheckboxNode"

    def _element_type(self) -> str:
        return "Checkbox"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - check or uncheck checkbox."""
        element = self.get_element_from_input()
        check = self.get_parameter("check", context)

        action = "checking" if check else "unchecking"
        logger.info(f"[{self.name}] {action.capitalize()} checkbox")

        desktop_ctx = self.get_desktop_context(context)

        try:
            desktop_ctx.check_checkbox(element, check=check)
            result_action = "checked" if check else "unchecked"
            logger.info(f"[{self.name}] Checkbox {result_action} successfully")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, f"{action} checkbox")


@executable_node
class SelectRadioButtonNode(InteractionNodeBase):
    """
    Select a radio button.

    Uses SelectionItemPattern for reliable radio button selection.

    Inputs:
        element: Radio button element

    Outputs:
        success: Whether selection succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: element -> success

    NODE_NAME = "Select Radio Button"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Select Radio Button",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "SelectRadioButtonNode"

    def _element_type(self) -> str:
        return "Radio button"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - select radio button."""
        element = self.get_element_from_input()

        logger.info(f"[{self.name}] Selecting radio button")

        desktop_ctx = self.get_desktop_context(context)

        try:
            desktop_ctx.select_radio_button(element)
            logger.info(f"[{self.name}] Radio button selected successfully")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, "select radio button")


@node_schema(TAB_NAME_PROP, TAB_INDEX_PROP)
@executable_node
class SelectTabNode(InteractionNodeBase):
    """
    Select a tab in a tab control.

    Supports selection by tab name or index.

    Config (via @node_schema):
        tab_name: Name of the tab to select (default: "")
        tab_index: Index of the tab (-1 to use name) (default: -1)

    Inputs:
        tab_control: Tab control element
        tab_name: Tab name (overrides config)
        tab_index: Tab index (overrides config)

    Outputs:
        success: Whether selection succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: tab_control, tab_name, tab_index -> success

    NODE_NAME = "Select Tab"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Select Tab",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "SelectTabNode"

    def _element_type(self) -> str:
        return "Tab control"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("tab_control", PortType.INPUT, DataType.ANY)
        self.add_input_port("tab_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("tab_index", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - select tab."""
        tab_control = self.get_input_value("tab_control")
        tab_name = self.get_parameter("tab_name", context) or None
        tab_index = self.get_parameter("tab_index", context)

        if tab_index == -1:
            tab_index = None

        if not tab_control:
            raise ValueError("Tab control element is required")
        if tab_name is None and tab_index is None:
            raise ValueError("Must provide either tab_name or tab_index")

        logger.info(
            f"[{self.name}] Selecting tab: name='{tab_name}', index={tab_index}"
        )

        desktop_ctx = self.get_desktop_context(context)

        try:
            desktop_ctx.select_tab(tab_control, tab_name=tab_name, tab_index=tab_index)
            logger.info(f"[{self.name}] Tab selected successfully")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, "select tab")


@node_schema(EXPAND_PROP)
@executable_node
class ExpandTreeItemNode(InteractionNodeBase):
    """
    Expand or collapse a tree item.

    Uses ExpandCollapsePattern for reliable tree item manipulation.

    Config (via @node_schema):
        expand: Expand vs collapse (default: True)

    Inputs:
        element: Tree item element

    Outputs:
        success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: element -> success

    NODE_NAME = "Expand Tree Item"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Expand Tree Item",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "ExpandTreeItemNode"

    def _element_type(self) -> str:
        return "Tree item"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - expand or collapse tree item."""
        element = self.get_element_from_input()
        expand = self.get_parameter("expand", context)

        action = "Expanding" if expand else "Collapsing"
        logger.info(f"[{self.name}] {action} tree item")

        desktop_ctx = self.get_desktop_context(context)

        try:
            desktop_ctx.expand_tree_item(element, expand=expand)
            result_action = "expanded" if expand else "collapsed"
            logger.info(f"[{self.name}] Tree item {result_action} successfully")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, f"{'expand' if expand else 'collapse'} tree item")


@node_schema(SCROLL_DIRECTION_PROP, SCROLL_AMOUNT_PROP)
@executable_node
class ScrollElementNode(InteractionNodeBase):
    """
    Scroll an element (scrollbar, list, window, etc.).

    Supports vertical and horizontal scrolling with configurable amount.

    Config (via @node_schema):
        direction: Scroll direction - up/down/left/right (default: "down")
        amount: Scroll amount 0.0 to 1.0 (default: 0.5)

    Inputs:
        element: Element to scroll

    Outputs:
        success: Whether scroll succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: element -> success

    NODE_NAME = "Scroll Element"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Scroll Element",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "ScrollElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - scroll element."""
        element = self.get_element_from_input()
        direction = self.get_parameter("direction", context)
        amount = self.get_parameter("amount", context)

        logger.info(f"[{self.name}] Scrolling {direction} by {amount}")

        desktop_ctx = self.get_desktop_context(context)

        try:
            desktop_ctx.scroll_element(element, direction=direction, amount=amount)
            logger.info(f"[{self.name}] Scrolled {direction} successfully")
            return self.success_result()
        except Exception as e:
            self.handle_error(e, "scroll element")

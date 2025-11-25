"""
Desktop Advanced Interaction Nodes

Nodes for advanced interactions with Windows desktop UI elements:
dropdowns, checkboxes, radio buttons, tabs, tree items, and scrolling.
"""

from typing import Any, Dict
from loguru import logger

from ...core.base_node import BaseNode as Node
from ...core.types import NodeStatus
from ...desktop import DesktopContext


def safe_int(value, default: int) -> int:
    """Safely parse int values with defaults."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class SelectFromDropdownNode(Node):
    """
    Select an item from a dropdown/combobox.

    Supports selection by text (partial or exact match) or by index.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Select From Dropdown'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Select From Dropdown"):
        """
        Initialize Select From Dropdown node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "by_text": True
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SelectFromDropdownNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)  # Dropdown element
        self.add_input_port("value", PortType.INPUT, DataType.STRING)  # Value to select

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - select from dropdown.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        element = self.get_input_value('element')
        value = self.get_input_value('value') or self.config.get('value', '')
        by_text = self.config.get('by_text', True)

        # Resolve {{variable}} patterns in value
        if hasattr(context, 'resolve_value') and value:
            value = context.resolve_value(value)

        if not element:
            raise ValueError("Dropdown element is required")
        if not value:
            raise ValueError("Value to select is required")

        logger.info(f"[{self.name}] Selecting '{value}' from dropdown")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.select_from_dropdown(element, value, by_text=by_text)

            logger.info(f"[{self.name}] Successfully selected '{value}'")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to select from dropdown: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class CheckCheckboxNode(Node):
    """
    Check or uncheck a checkbox.

    Uses TogglePattern for reliable checkbox interaction.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Check Checkbox'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Check Checkbox"):
        """
        Initialize Check Checkbox node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "check": True
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CheckCheckboxNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)  # Checkbox element

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - check or uncheck checkbox.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        element = self.get_input_value('element')
        check = self.config.get('check', True)

        if not element:
            raise ValueError("Checkbox element is required")

        action = "checking" if check else "unchecking"
        logger.info(f"[{self.name}] {action.capitalize()} checkbox")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.check_checkbox(element, check=check)

            logger.info(f"[{self.name}] Checkbox {'checked' if check else 'unchecked'} successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to {action} checkbox: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class SelectRadioButtonNode(Node):
    """
    Select a radio button.

    Uses SelectionItemPattern for reliable radio button selection.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Select Radio Button'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Select Radio Button"):
        """
        Initialize Select Radio Button node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SelectRadioButtonNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)  # Radio button element

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - select radio button.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        element = self.get_input_value('element')

        if not element:
            raise ValueError("Radio button element is required")

        logger.info(f"[{self.name}] Selecting radio button")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.select_radio_button(element)

            logger.info(f"[{self.name}] Radio button selected successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to select radio button: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class SelectTabNode(Node):
    """
    Select a tab in a tab control.

    Supports selection by tab name or index.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Select Tab'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Select Tab"):
        """
        Initialize Select Tab node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "tab_name": "",
                "tab_index": -1
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SelectTabNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("tab_control", PortType.INPUT, DataType.ANY)  # Tab control element
        self.add_input_port("tab_name", PortType.INPUT, DataType.STRING)
        self.add_input_port("tab_index", PortType.INPUT, DataType.INTEGER)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - select tab.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        tab_control = self.get_input_value('tab_control')
        tab_name = self.get_input_value('tab_name') or self.config.get('tab_name') or None
        tab_index = self.get_input_value('tab_index')
        if tab_index is None:
            tab_index = safe_int(self.config.get('tab_index'), -1)
        if tab_index == -1:
            tab_index = None

        # Resolve {{variable}} patterns in tab_name
        if hasattr(context, 'resolve_value') and tab_name:
            tab_name = context.resolve_value(tab_name)

        if not tab_control:
            raise ValueError("Tab control element is required")
        if tab_name is None and tab_index is None:
            raise ValueError("Must provide either tab_name or tab_index")

        logger.info(f"[{self.name}] Selecting tab: name='{tab_name}', index={tab_index}")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.select_tab(tab_control, tab_name=tab_name, tab_index=tab_index)

            logger.info(f"[{self.name}] Tab selected successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to select tab: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class ExpandTreeItemNode(Node):
    """
    Expand or collapse a tree item.

    Uses ExpandCollapsePattern for reliable tree item manipulation.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Expand Tree Item'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Expand Tree Item"):
        """
        Initialize Expand Tree Item node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "expand": True
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ExpandTreeItemNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)  # Tree item element

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - expand or collapse tree item.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        element = self.get_input_value('element')
        expand = self.config.get('expand', True)

        if not element:
            raise ValueError("Tree item element is required")

        action = "Expanding" if expand else "Collapsing"
        logger.info(f"[{self.name}] {action} tree item")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.expand_tree_item(element, expand=expand)

            logger.info(f"[{self.name}] Tree item {'expanded' if expand else 'collapsed'} successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to {'expand' if expand else 'collapse'} tree item: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class ScrollElementNode(Node):
    """
    Scroll an element (scrollbar, list, window, etc.).

    Supports vertical and horizontal scrolling with configurable amount.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Scroll Element'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Scroll Element"):
        """
        Initialize Scroll Element node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "direction": "down",
                "amount": 0.5
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ScrollElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)  # Element to scroll

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - scroll element.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        element = self.get_input_value('element')
        direction = self.config.get('direction', 'down')
        amount = self.config.get('amount', 0.5)

        if not element:
            raise ValueError("Element to scroll is required")

        logger.info(f"[{self.name}] Scrolling {direction} by {amount}")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.scroll_element(element, direction=direction, amount=amount)

            logger.info(f"[{self.name}] Scrolled {direction} successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to scroll element: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)

"""
Desktop Element Interaction Nodes

Nodes for finding and interacting with Windows desktop UI elements.
"""

from typing import Any, Dict, Optional
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


class FindElementNode(Node):
    """
    Find a desktop UI element within a window.

    Uses selector to locate an element for further automation.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Find Element'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Find Element"):
        """
        Initialize Find Element node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "timeout": 5.0,
                "throw_on_not_found": True
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FindElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        window = self.get_input_value('window')
        selector = self.get_input_value('selector') or self.config.get('selector')

        # Get configuration
        timeout = self.config.get('timeout', 5.0)
        throw_on_not_found = self.config.get('throw_on_not_found', True)

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
                    'success': True,
                    'element': element,
                    'found': True,
                    'next_nodes': ['exec_out']
                }
            else:
                if throw_on_not_found:
                    error_msg = f"Element not found with selector: {selector}"
                    logger.error(f"[{self.name}] {error_msg}")
                    self.status = NodeStatus.ERROR
                    raise RuntimeError(error_msg)
                else:
                    logger.warning(f"[{self.name}] Element not found, but throw_on_not_found is False")
                    self.status = NodeStatus.SUCCESS
                    return {
                        'success': True,
                        'element': None,
                        'found': False,
                        'next_nodes': ['exec_out']
                    }

        except Exception as e:
            error_msg = f"Failed to find element: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class ClickElementNode(Node):
    """
    Click a desktop UI element.

    Can accept an element directly or find it using window + selector.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Click Element'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Click Element"):
        """
        Initialize Click Element node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "simulate": False,
                "x_offset": 0,
                "y_offset": 0,
                "timeout": 5.0
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClickElementNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        element = self.get_input_value('element')

        if not element:
            window = self.get_input_value('window')
            selector = self.get_input_value('selector') or self.config.get('selector')

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.config.get('timeout', 5.0)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        # Get configuration
        simulate = self.config.get('simulate', False)
        x_offset = self.config.get('x_offset', 0)
        y_offset = self.config.get('y_offset', 0)

        logger.info(f"[{self.name}] Clicking element: {element}")
        logger.debug(f"[{self.name}] simulate={simulate}, offset=({x_offset}, {y_offset})")

        try:
            # Perform click
            element.click(
                simulate=simulate,
                x_offset=x_offset,
                y_offset=y_offset
            )

            logger.info(f"[{self.name}] Click successful")
            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to click element: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class TypeTextNode(Node):
    """
    Type text into a desktop UI element.

    Can accept an element directly or find it using window + selector.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Type Text'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Type Text"):
        """
        Initialize Type Text node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "clear_first": False,
                "interval": 0.01,
                "timeout": 5.0
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TypeTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)
        self.add_input_port("text", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        text = self.get_input_value('text') or self.config.get('text', '')

        # Resolve {{variable}} patterns in text
        if hasattr(context, 'resolve_value') and text:
            text = context.resolve_value(text)

        if not text:
            error_msg = "Text is required. Provide text to type."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        # Get element - directly or via window+selector
        element = self.get_input_value('element')

        if not element:
            window = self.get_input_value('window')
            selector = self.get_input_value('selector') or self.config.get('selector')

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.config.get('timeout', 5.0)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        # Get configuration
        clear_first = self.config.get('clear_first', False)
        interval = self.config.get('interval', 0.01)

        logger.info(f"[{self.name}] Typing text into element: {element}")
        logger.debug(f"[{self.name}] Text length: {len(text)}, clear_first={clear_first}")

        try:
            # Type text
            element.type_text(
                text=text,
                clear_first=clear_first,
                interval=interval
            )

            logger.info(f"[{self.name}] Text typed successfully")
            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to type text: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class GetElementTextNode(Node):
    """
    Get text content from a desktop UI element.

    Can accept an element directly or find it using window + selector.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Element Text'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Get Element Text"):
        """
        Initialize Get Element Text node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "timeout": 5.0,
                "variable_name": ""
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetElementTextNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        element = self.get_input_value('element')

        if not element:
            window = self.get_input_value('window')
            selector = self.get_input_value('selector') or self.config.get('selector')

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.config.get('timeout', 5.0)
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

            logger.info(f"[{self.name}] Got text: '{text[:50]}...' ({len(text)} chars)" if len(text) > 50 else f"[{self.name}] Got text: '{text}'")

            # Store in context variable if specified
            variable_name = self.config.get('variable_name', '')
            # Resolve {{variable}} patterns in variable_name
            if hasattr(context, 'resolve_value') and variable_name:
                variable_name = context.resolve_value(variable_name)
            if variable_name and hasattr(context, 'set_variable'):
                context.set_variable(variable_name, text)
                logger.debug(f"[{self.name}] Stored text in variable: {variable_name}")

            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'text': text,
                'element': element,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to get element text: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class GetElementPropertyNode(Node):
    """
    Get a property value from a desktop UI element.

    Can accept an element directly or find it using window + selector.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Element Property'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Get Element Property"):
        """
        Initialize Get Element Property node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "timeout": 5.0,
                "property_name": "Name"
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetElementPropertyNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("element", PortType.INPUT, DataType.ANY)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("selector", PortType.INPUT, DataType.ANY)
        self.add_input_port("property_name", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        property_name = self.get_input_value('property_name') or self.config.get('property_name', 'Name')

        # Get element - directly or via window+selector
        element = self.get_input_value('element')

        if not element:
            window = self.get_input_value('window')
            selector = self.get_input_value('selector') or self.config.get('selector')

            if not window or not selector:
                error_msg = "Must provide 'element' or both 'window' and 'selector'"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise ValueError(error_msg)

            timeout = self.config.get('timeout', 5.0)
            logger.info(f"[{self.name}] Finding element with selector: {selector}")

            element = window.find_child(selector, timeout=timeout)
            if not element:
                error_msg = f"Element not found with selector: {selector}"
                logger.error(f"[{self.name}] {error_msg}")
                self.status = NodeStatus.ERROR
                raise RuntimeError(error_msg)

        logger.info(f"[{self.name}] Getting property '{property_name}' from element: {element}")

        try:
            # Get property
            value = element.get_property(property_name)

            logger.info(f"[{self.name}] Got property '{property_name}': {value}")

            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'value': value,
                'element': element,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to get element property '{property_name}': {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)

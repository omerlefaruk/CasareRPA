"""
Desktop Window Management Nodes

Nodes for resizing, moving, and managing Windows desktop windows.
"""

from typing import Any, Dict, Optional
from loguru import logger

from ...core.base_node import BaseNode as Node
from ...core.types import NodeStatus
from ...desktop import DesktopContext


class ResizeWindowNode(Node):
    """
    Resize a Windows desktop window.

    Changes the dimensions of a window to specified width and height.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Resize Window'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Resize Window"):
        """
        Initialize Resize Window node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "width": 800,
                "height": 600
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ResizeWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object
        self.add_input_port("width", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("height", PortType.INPUT, DataType.INTEGER)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - resize window.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value('window')
        width = self.get_input_value('width') or self.config.get('width', 800)
        height = self.get_input_value('height') or self.config.get('height', 600)

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Resizing window to {width}x{height}")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.resize_window(window, int(width), int(height))

            logger.info(f"[{self.name}] Window resized successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to resize window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class MoveWindowNode(Node):
    """
    Move a Windows desktop window.

    Moves a window to specified screen coordinates.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Move Window'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Move Window"):
        """
        Initialize Move Window node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "x": 100,
                "y": 100
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MoveWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object
        self.add_input_port("x", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("y", PortType.INPUT, DataType.INTEGER)

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - move window.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value('window')
        x = self.get_input_value('x') or self.config.get('x', 100)
        y = self.get_input_value('y') or self.config.get('y', 100)

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Moving window to ({x}, {y})")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.move_window(window, int(x), int(y))

            logger.info(f"[{self.name}] Window moved successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to move window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class MaximizeWindowNode(Node):
    """
    Maximize a Windows desktop window.

    Maximizes a window to fill the screen.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Maximize Window'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Maximize Window"):
        """
        Initialize Maximize Window node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MaximizeWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - maximize window.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value('window')

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Maximizing window")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.maximize_window(window)

            logger.info(f"[{self.name}] Window maximized successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to maximize window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class MinimizeWindowNode(Node):
    """
    Minimize a Windows desktop window.

    Minimizes a window to the taskbar.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Minimize Window'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Minimize Window"):
        """
        Initialize Minimize Window node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MinimizeWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - minimize window.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value('window')

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Minimizing window")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.minimize_window(window)

            logger.info(f"[{self.name}] Window minimized successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to minimize window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class RestoreWindowNode(Node):
    """
    Restore a Windows desktop window.

    Restores a window to normal state from maximized or minimized.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Restore Window'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Restore Window"):
        """
        Initialize Restore Window node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RestoreWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - restore window.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value('window')

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Restoring window")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            success = desktop_ctx.restore_window(window)

            logger.info(f"[{self.name}] Window restored successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to restore window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class GetWindowPropertiesNode(Node):
    """
    Get properties of a Windows desktop window.

    Returns comprehensive information about a window including title, size, position, state, etc.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Window Properties'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Get Window Properties"):
        """
        Initialize Get Window Properties node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetWindowPropertiesNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("properties", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("title", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("x", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("y", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("width", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("height", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("state", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("is_maximized", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_minimized", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - get window properties.

        Args:
            context: Execution context

        Returns:
            Dictionary with window properties
        """
        # Get inputs
        window = self.get_input_value('window')

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Getting window properties")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            properties = desktop_ctx.get_window_properties(window)

            logger.info(f"[{self.name}] Got window properties: {properties.get('title', 'Unknown')}")

            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'properties': properties,
                'title': properties.get('title', ''),
                'x': properties.get('x', 0),
                'y': properties.get('y', 0),
                'width': properties.get('width', 0),
                'height': properties.get('height', 0),
                'state': properties.get('state', 'unknown'),
                'is_maximized': properties.get('is_maximized', False),
                'is_minimized': properties.get('is_minimized', False),
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to get window properties: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class SetWindowStateNode(Node):
    """
    Set the state of a Windows desktop window.

    Sets window state to normal, maximized, minimized, or hidden.
    """

    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Set Window State'

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Set Window State"):
        """
        Initialize Set Window State node.

        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "state": "normal"  # normal, maximized, minimized
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SetWindowStateNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        from ...core.types import PortType, DataType

        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object
        self.add_input_port("state", PortType.INPUT, DataType.STRING)  # normal, maximized, minimized

        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - set window state.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value('window')
        state = self.get_input_value('state') or self.config.get('state', 'normal')

        if not window:
            raise ValueError("Window input is required")

        logger.info(f"[{self.name}] Setting window state to '{state}'")

        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            state = state.lower().strip()

            if state == 'maximized':
                success = desktop_ctx.maximize_window(window)
            elif state == 'minimized':
                success = desktop_ctx.minimize_window(window)
            elif state in ('normal', 'restored'):
                success = desktop_ctx.restore_window(window)
            else:
                raise ValueError(f"Invalid state: '{state}'. Use 'normal', 'maximized', or 'minimized'.")

            logger.info(f"[{self.name}] Window state set to '{state}' successfully")

            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }

        except Exception as e:
            error_msg = f"Failed to set window state: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)

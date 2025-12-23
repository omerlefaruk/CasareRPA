"""
Desktop Window Management Nodes

Nodes for resizing, moving, and managing Windows desktop windows.
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    BRING_TO_FRONT_PROP,
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)

# Window-specific PropertyDef constants
WIDTH_PROP = PropertyDef(
    "width",
    PropertyType.INTEGER,
    default=800,
    min_value=1,
    label="Width",
    tooltip="Window width in pixels",
    tab="properties",
)

HEIGHT_PROP = PropertyDef(
    "height",
    PropertyType.INTEGER,
    default=600,
    min_value=1,
    label="Height",
    tooltip="Window height in pixels",
    tab="properties",
)

POSITION_X_PROP = PropertyDef(
    "x",
    PropertyType.INTEGER,
    default=100,
    label="X Position",
    tooltip="Window X position from left",
    tab="properties",
)

POSITION_Y_PROP = PropertyDef(
    "y",
    PropertyType.INTEGER,
    default=100,
    label="Y Position",
    tooltip="Window Y position from top",
    tab="properties",
)


class WindowNodeBase(DesktopNodeBase):
    """
    Base class for window operation nodes.

    Provides common window handling patterns.
    """

    # @category: desktop
    # @requires: none
    # @ports: none -> none

    def get_window_from_input(self) -> Any:
        """
        Get window from input port.

        Returns:
            Window object

        Raises:
            ValueError: If window not provided
        """
        window = self.get_input_value("window")
        if not window:
            raise ValueError("Window input is required")
        return window


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
    WIDTH_PROP,
    HEIGHT_PROP,
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
    BRING_TO_FRONT_PROP,
)
@node(category="desktop")
class ResizeWindowNode(WindowNodeBase):
    """
    Resize a Windows desktop window.

    Changes the dimensions of a window to specified width and height.

    Config (via @properties):
        width: Target width in pixels (default: 800)
        height: Target height in pixels (default: 600)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries (default: 1.0 seconds)
        bring_to_front: Bring window to front before operation (default: False)

    Inputs:
        window: Desktop window object
        width: Target width (overrides config)
        height: Target height (overrides config)

    Outputs:
        success: Whether the resize succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: window, width, height -> success

    NODE_NAME = "Resize Window"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Resize Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "ResizeWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_input_port("width", DataType.INTEGER)
        self.add_input_port("height", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - resize window."""
        window = self.get_window_from_input()
        width = self.get_parameter("width", context)
        height = self.get_parameter("height", context)
        bring_to_front = self.get_parameter("bring_to_front", context)

        logger.info(f"[{self.name}] Resizing window to {width}x{height}")

        desktop_ctx = self.get_desktop_context(context)

        async def do_resize():
            if bring_to_front:
                try:
                    desktop_ctx.bring_to_front(window)
                except Exception:
                    pass

            desktop_ctx.resize_window(window, int(width), int(height))
            return self.success_result()

        return await self.execute_with_retry(do_resize, context, operation_name="resize window")


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
    POSITION_X_PROP,
    POSITION_Y_PROP,
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
    BRING_TO_FRONT_PROP,
)
@node(category="desktop")
class MoveWindowNode(WindowNodeBase):
    """
    Move a Windows desktop window.

    Moves a window to specified screen coordinates.

    Config (via @properties):
        x: Target X position (default: 100)
        y: Target Y position (default: 100)
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries (default: 1.0 seconds)
        bring_to_front: Bring window to front before operation (default: False)

    Inputs:
        window: Desktop window object
        x: Target X position (overrides config)
        y: Target Y position (overrides config)

    Outputs:
        success: Whether the move succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: window, x, y -> success

    NODE_NAME = "Move Window"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Move Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "MoveWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_input_port("x", DataType.INTEGER)
        self.add_input_port("y", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - move window."""
        window = self.get_window_from_input()
        x = self.get_parameter("x", context)
        y = self.get_parameter("y", context)
        bring_to_front = self.get_parameter("bring_to_front", context)

        logger.info(f"[{self.name}] Moving window to ({x}, {y})")

        desktop_ctx = self.get_desktop_context(context)

        async def do_move():
            if bring_to_front:
                try:
                    desktop_ctx.bring_to_front(window)
                except Exception:
                    pass

            desktop_ctx.move_window(window, int(x), int(y))
            return self.success_result()

        return await self.execute_with_retry(do_move, context, operation_name="move window")


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)
@node(category="desktop")
class MaximizeWindowNode(WindowNodeBase):
    """
    Maximize a Windows desktop window.

    Maximizes a window to fill the screen.

    Config (via @properties):
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries (default: 1.0 seconds)

    Inputs:
        window: Desktop window object

    Outputs:
        success: Whether the maximize succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: window -> success

    NODE_NAME = "Maximize Window"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Maximize Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "MaximizeWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - maximize window."""
        window = self.get_window_from_input()
        retry_count = self.get_parameter("retry_count")
        retry_interval = self.get_parameter("retry_interval")

        logger.info(f"[{self.name}] Maximizing window")

        desktop_ctx = self.get_desktop_context(context)

        async def do_maximize():
            desktop_ctx.maximize_window(window)
            return self.success_result()

        return await self.execute_with_retry(
            do_maximize,
            context,
            retry_count=retry_count,
            retry_interval=retry_interval,
            operation_name="maximize window",
        )


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)
@node(category="desktop")
class MinimizeWindowNode(WindowNodeBase):
    """
    Minimize a Windows desktop window.

    Minimizes a window to the taskbar.

    Config (via @properties):
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries (default: 1.0 seconds)

    Inputs:
        window: Desktop window object

    Outputs:
        success: Whether the minimize succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: window -> success

    NODE_NAME = "Minimize Window"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Minimize Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "MinimizeWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - minimize window."""
        window = self.get_window_from_input()
        retry_count = self.get_parameter("retry_count")
        retry_interval = self.get_parameter("retry_interval")

        logger.info(f"[{self.name}] Minimizing window")

        desktop_ctx = self.get_desktop_context(context)

        async def do_minimize():
            desktop_ctx.minimize_window(window)
            return self.success_result()

        return await self.execute_with_retry(
            do_minimize,
            context,
            retry_count=retry_count,
            retry_interval=retry_interval,
            operation_name="minimize window",
        )


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)
@node(category="desktop")
class RestoreWindowNode(WindowNodeBase):
    """
    Restore a Windows desktop window.

    Restores a window to normal state from maximized or minimized.

    Config (via @properties):
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries (default: 1.0 seconds)

    Inputs:
        window: Desktop window object

    Outputs:
        success: Whether the restore succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: window -> success

    NODE_NAME = "Restore Window"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Restore Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "RestoreWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - restore window."""
        window = self.get_window_from_input()
        retry_count = self.get_parameter("retry_count")
        retry_interval = self.get_parameter("retry_interval")

        logger.info(f"[{self.name}] Restoring window")

        desktop_ctx = self.get_desktop_context(context)

        async def do_restore():
            desktop_ctx.restore_window(window)
            return self.success_result()

        return await self.execute_with_retry(
            do_restore,
            context,
            retry_count=retry_count,
            retry_interval=retry_interval,
            operation_name="restore window",
        )


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
)
@node(category="desktop")
class GetWindowPropertiesNode(WindowNodeBase):
    """
    Get properties of a Windows desktop window.

    Returns comprehensive information about a window including title,
    size, position, state, etc.

    Inputs:
        window: Desktop window object

    Outputs:
        properties: Dictionary of all window properties
        title: Window title
        x: X position
        y: Y position
        width: Window width
        height: Window height
        state: Window state (normal/maximized/minimized)
        is_maximized: Whether window is maximized
        is_minimized: Whether window is minimized
    """

    # @category: desktop
    # @requires: none
    # @ports: window -> properties, title, x, y, width, height, state, is_maximized, is_minimized

    NODE_NAME = "Get Window Properties"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Get Window Properties",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "GetWindowPropertiesNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_output_port("properties", DataType.DICT)
        self.add_output_port("title", DataType.STRING)
        self.add_output_port("x", DataType.INTEGER)
        self.add_output_port("y", DataType.INTEGER)
        self.add_output_port("width", DataType.INTEGER)
        self.add_output_port("height", DataType.INTEGER)
        self.add_output_port("state", DataType.STRING)
        self.add_output_port("is_maximized", DataType.BOOLEAN)
        self.add_output_port("is_minimized", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - get window properties."""
        window = self.get_window_from_input()

        logger.info(f"[{self.name}] Getting window properties")

        desktop_ctx = self.get_desktop_context(context)

        try:
            properties = desktop_ctx.get_window_properties(window)

            logger.info(
                f"[{self.name}] Got window properties: {properties.get('title', 'Unknown')}"
            )

            return self.success_result(
                properties=properties,
                title=properties.get("title", ""),
                x=properties.get("x", 0),
                y=properties.get("y", 0),
                width=properties.get("width", 0),
                height=properties.get("height", 0),
                state=properties.get("state", "unknown"),
                is_maximized=properties.get("is_maximized", False),
                is_minimized=properties.get("is_minimized", False),
            )

        except Exception as e:
            self.handle_error(e, "get window properties")
            return {"success": False, "data": {}, "next_nodes": []}


@properties(
    PropertyDef(
        "window",
        PropertyType.ANY,
        required=True,
        label="Window",
        tooltip="Desktop window object",
    ),
    PropertyDef(
        "state",
        PropertyType.CHOICE,
        default="normal",
        choices=["normal", "maximized", "minimized"],
        required=True,
        label="State",
        tooltip="Target window state",
    ),
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)
@node(category="desktop")
class SetWindowStateNode(WindowNodeBase):
    """
    Set the state of a Windows desktop window.

    Sets window state to normal, maximized, or minimized.

    Config (via @properties):
        state: Target state (normal/maximized/minimized) (default: "normal")
        retry_count: Number of retries on failure (default: 0)
        retry_interval: Delay between retries (default: 1.0 seconds)

    Inputs:
        window: Desktop window object
        state: Target state (overrides config)

    Outputs:
        success: Whether the state change succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: window, state -> success

    NODE_NAME = "Set Window State"

    def __init__(
        self,
        node_id: str | None = None,
        config: dict[str, Any] | None = None,
        name: str = "Set Window State",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "SetWindowStateNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("window", DataType.ANY)
        self.add_input_port("state", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> dict[str, Any]:
        """Execute the node - set window state."""
        window = self.get_window_from_input()
        state = self.get_parameter("state")

        logger.info(f"[{self.name}] Setting window state to '{state}'")

        desktop_ctx = self.get_desktop_context(context)

        async def do_set_state():
            state_lower = str(state).lower().strip()

            if state_lower == "maximized":
                desktop_ctx.maximize_window(window)
            elif state_lower == "minimized":
                desktop_ctx.minimize_window(window)
            elif state_lower in ("normal", "restored"):
                desktop_ctx.restore_window(window)
            else:
                raise ValueError(
                    f"Invalid state: '{state}'. Use 'normal', 'maximized', or 'minimized'."
                )

            return self.success_result()

        return await self.execute_with_retry(
            do_set_state, context, operation_name=f"set window state to '{state}'"
        )

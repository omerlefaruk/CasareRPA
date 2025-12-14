"""
Super Node for CasareRPA Window Management Operations.

This module provides a consolidated "Window Management Super Node" that replaces 7
atomic window nodes with action-based dynamic ports and properties.

WindowManagementSuperNode (7 operations):
    - Resize: Resize window to specified dimensions
    - Move: Move window to specified position
    - Maximize: Maximize window to fill screen
    - Minimize: Minimize window to taskbar
    - Restore: Restore window to normal state
    - Get Properties: Get window title, size, position, state
    - Set State: Set window state (normal/maximized/minimized)
"""

from enum import Enum
from typing import TYPE_CHECKING, Dict, Callable, Awaitable, Any

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.domain.value_objects.dynamic_port_config import (
    PortDef,
    ActionPortConfig,
    DynamicPortSchema,
)
from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces import IExecutionContext


class WindowAction(str, Enum):
    """Actions available in WindowManagementSuperNode."""

    RESIZE = "Resize"
    MOVE = "Move"
    MAXIMIZE = "Maximize"
    MINIMIZE = "Minimize"
    RESTORE = "Restore"
    GET_PROPERTIES = "Get Properties"
    SET_STATE = "Set State"


# Port schema for dynamic port visibility
WINDOW_PORT_SCHEMA = DynamicPortSchema()

# Resize ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.RESIZE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
            PortDef("width", DataType.INTEGER),
            PortDef("height", DataType.INTEGER),
        ],
        outputs=[
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Move ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.MOVE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
            PortDef("x", DataType.INTEGER),
            PortDef("y", DataType.INTEGER),
        ],
        outputs=[
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Maximize ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.MAXIMIZE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
        ],
        outputs=[
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Minimize ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.MINIMIZE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
        ],
        outputs=[
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Restore ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.RESTORE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
        ],
        outputs=[
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Get Properties ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.GET_PROPERTIES.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
        ],
        outputs=[
            PortDef("properties", DataType.DICT),
            PortDef("title", DataType.STRING),
            PortDef("x", DataType.INTEGER),
            PortDef("y", DataType.INTEGER),
            PortDef("width", DataType.INTEGER),
            PortDef("height", DataType.INTEGER),
            PortDef("state", DataType.STRING),
            PortDef("is_maximized", DataType.BOOLEAN),
            PortDef("is_minimized", DataType.BOOLEAN),
        ],
    ),
)

# Set State ports
WINDOW_PORT_SCHEMA.register(
    WindowAction.SET_STATE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("window", DataType.ANY),
            PortDef("state", DataType.STRING),
        ],
        outputs=[
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)


@node(category="desktop")
@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=WindowAction.RESIZE.value,
        label="Action",
        tooltip="Window operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in WindowAction],
    ),
    # === RESIZE OPTIONS ===
    PropertyDef(
        "width",
        PropertyType.INTEGER,
        default=800,
        min_value=1,
        label="Width",
        tooltip="Window width in pixels",
        order=10,
        display_when={"action": [WindowAction.RESIZE.value]},
    ),
    PropertyDef(
        "height",
        PropertyType.INTEGER,
        default=600,
        min_value=1,
        label="Height",
        tooltip="Window height in pixels",
        order=11,
        display_when={"action": [WindowAction.RESIZE.value]},
    ),
    # === MOVE OPTIONS ===
    PropertyDef(
        "x",
        PropertyType.INTEGER,
        default=100,
        label="X Position",
        tooltip="Window X position from left",
        order=10,
        display_when={"action": [WindowAction.MOVE.value]},
    ),
    PropertyDef(
        "y",
        PropertyType.INTEGER,
        default=100,
        label="Y Position",
        tooltip="Window Y position from top",
        order=11,
        display_when={"action": [WindowAction.MOVE.value]},
    ),
    # === SET STATE OPTIONS ===
    PropertyDef(
        "window_state",
        PropertyType.CHOICE,
        default="normal",
        choices=["normal", "maximized", "minimized"],
        label="Window State",
        tooltip="Target window state",
        order=10,
        display_when={"action": [WindowAction.SET_STATE.value]},
    ),
    # === COMMON OPTIONS ===
    PropertyDef(
        "bring_to_front",
        PropertyType.BOOLEAN,
        default=False,
        label="Bring to Front",
        tooltip="Bring window to front before operation",
        order=50,
        display_when={
            "action": [
                WindowAction.RESIZE.value,
                WindowAction.MOVE.value,
            ]
        },
    ),
    PropertyDef(
        "retry_count",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Retry Count",
        tooltip="Number of retries on failure",
        order=60,
        tab="advanced",
    ),
    PropertyDef(
        "retry_interval",
        PropertyType.FLOAT,
        default=1.0,
        min_value=0.1,
        label="Retry Interval",
        tooltip="Delay between retries in seconds",
        order=61,
        tab="advanced",
    ),
)
class WindowManagementSuperNode(DesktopNodeBase):
    """
    Unified window management node.

    Consolidates 7 atomic window operations into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        - Resize: Resize window to specified dimensions
        - Move: Move window to specified position
        - Maximize: Maximize window to fill screen
        - Minimize: Minimize window to taskbar
        - Restore: Restore window to normal state
        - Get Properties: Get window title, size, position, state
        - Set State: Set window state (normal/maximized/minimized)

    Inputs:
        window: Desktop window object (required for all actions)

    Outputs:
        success: Whether operation succeeded (most actions)
        properties: Window properties dict (Get Properties)
        title, x, y, width, height, state: Individual properties (Get Properties)
    """

    NODE_NAME = "Window Management"

    def __init__(self, node_id: str, name: str = "Window Management", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config, name=name)
        self.node_type = "WindowManagementSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Default to Resize ports
        self.add_input_port("window", DataType.ANY)
        self.add_input_port("width", DataType.INTEGER)
        self.add_input_port("height", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected window action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", WindowAction.RESIZE.value)

        # Map actions to handlers
        handlers: Dict[
            str, Callable[["IExecutionContext"], Awaitable[ExecutionResult]]
        ] = {
            WindowAction.RESIZE.value: self._execute_resize,
            WindowAction.MOVE.value: self._execute_move,
            WindowAction.MAXIMIZE.value: self._execute_maximize,
            WindowAction.MINIMIZE.value: self._execute_minimize,
            WindowAction.RESTORE.value: self._execute_restore,
            WindowAction.GET_PROPERTIES.value: self._execute_get_properties,
            WindowAction.SET_STATE.value: self._execute_set_state,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Error in WindowManagementSuperNode ({action}): {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    def _get_window(self) -> Any:
        """Get window from input port."""
        window = self.get_input_value("window")
        if not window:
            raise ValueError("Window input is required")
        return window

    async def _execute_resize(self, context: "IExecutionContext") -> ExecutionResult:
        """Resize window."""
        window = self._get_window()
        width = self.get_input_value("width")
        height = self.get_input_value("height")

        if width is None:
            width = self.get_parameter("width", 800)
        if height is None:
            height = self.get_parameter("height", 600)

        bring_to_front = self.get_parameter("bring_to_front", False)

        logger.info(f"[{self.name}] Resizing window to {width}x{height}")

        desktop_ctx = self.get_desktop_context(context)

        if bring_to_front:
            try:
                desktop_ctx.bring_to_front(window)
            except Exception:
                pass

        desktop_ctx.resize_window(window, int(width), int(height))

        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"width": width, "height": height},
            "next_nodes": ["exec_out"],
        }

    async def _execute_move(self, context: "IExecutionContext") -> ExecutionResult:
        """Move window."""
        window = self._get_window()
        x = self.get_input_value("x")
        y = self.get_input_value("y")

        if x is None:
            x = self.get_parameter("x", 100)
        if y is None:
            y = self.get_parameter("y", 100)

        bring_to_front = self.get_parameter("bring_to_front", False)

        logger.info(f"[{self.name}] Moving window to ({x}, {y})")

        desktop_ctx = self.get_desktop_context(context)

        if bring_to_front:
            try:
                desktop_ctx.bring_to_front(window)
            except Exception:
                pass

        desktop_ctx.move_window(window, int(x), int(y))

        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"x": x, "y": y},
            "next_nodes": ["exec_out"],
        }

    async def _execute_maximize(self, context: "IExecutionContext") -> ExecutionResult:
        """Maximize window."""
        window = self._get_window()

        logger.info(f"[{self.name}] Maximizing window")

        desktop_ctx = self.get_desktop_context(context)
        desktop_ctx.maximize_window(window)

        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"state": "maximized"},
            "next_nodes": ["exec_out"],
        }

    async def _execute_minimize(self, context: "IExecutionContext") -> ExecutionResult:
        """Minimize window."""
        window = self._get_window()

        logger.info(f"[{self.name}] Minimizing window")

        desktop_ctx = self.get_desktop_context(context)
        desktop_ctx.minimize_window(window)

        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"state": "minimized"},
            "next_nodes": ["exec_out"],
        }

    async def _execute_restore(self, context: "IExecutionContext") -> ExecutionResult:
        """Restore window."""
        window = self._get_window()

        logger.info(f"[{self.name}] Restoring window")

        desktop_ctx = self.get_desktop_context(context)
        desktop_ctx.restore_window(window)

        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"state": "normal"},
            "next_nodes": ["exec_out"],
        }

    async def _execute_get_properties(
        self, context: "IExecutionContext"
    ) -> ExecutionResult:
        """Get window properties."""
        window = self._get_window()

        logger.info(f"[{self.name}] Getting window properties")

        desktop_ctx = self.get_desktop_context(context)
        properties = desktop_ctx.get_window_properties(window)

        logger.info(
            f"[{self.name}] Got properties: {properties.get('title', 'Unknown')}"
        )

        self.set_output_value("properties", properties)
        self.set_output_value("title", properties.get("title", ""))
        self.set_output_value("x", properties.get("x", 0))
        self.set_output_value("y", properties.get("y", 0))
        self.set_output_value("width", properties.get("width", 0))
        self.set_output_value("height", properties.get("height", 0))
        self.set_output_value("state", properties.get("state", "unknown"))
        self.set_output_value("is_maximized", properties.get("is_maximized", False))
        self.set_output_value("is_minimized", properties.get("is_minimized", False))

        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": properties,
            "next_nodes": ["exec_out"],
        }

    async def _execute_set_state(self, context: "IExecutionContext") -> ExecutionResult:
        """Set window state."""
        window = self._get_window()
        state = self.get_input_value("state")

        if state is None:
            state = self.get_parameter("window_state", "normal")

        logger.info(f"[{self.name}] Setting window state to '{state}'")

        desktop_ctx = self.get_desktop_context(context)

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

        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"state": state_lower},
            "next_nodes": ["exec_out"],
        }


__all__ = [
    "WindowManagementSuperNode",
    "WindowAction",
    "WINDOW_PORT_SCHEMA",
]

"""
Mouse and Keyboard Control Nodes

Provides nodes for direct mouse and keyboard input:
- MoveMouseNode: Move cursor to position
- MouseClickNode: Click at position
- SendKeysNode: Send keyboard input
- SendHotKeyNode: Send hotkey combinations
- GetMousePositionNode: Get current cursor position
- DragMouseNode: Drag from one position to another
"""

import asyncio
from typing import Any, Dict, Optional

from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.value_objects.types import DataType, NodeStatus, PortType

from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    DURATION_PROP,
    MOUSE_BUTTON_PROP,
    CLICK_TYPE_PROP,
    KEYS_PROP,
    INTERVAL_PROP,
    HOTKEY_MODIFIER_PROP,
    WITH_CTRL_PROP,
    WITH_SHIFT_PROP,
    WITH_ALT_PROP,
    CLEAR_FIRST_PROP,
)
from casare_rpa.domain.schemas import PropertyDef, PropertyType


# =============================================================================
# Mouse/Keyboard specific PropertyDef constants
# =============================================================================

EASE_PROP = PropertyDef(
    "ease",
    PropertyType.CHOICE,
    default="linear",
    choices=["linear", "ease_in", "ease_out", "ease_in_out"],
    label="Easing",
    tooltip="Easing function for movement",
    tab="advanced",
)

STEPS_PROP = PropertyDef(
    "steps",
    PropertyType.INTEGER,
    default=10,
    min_value=1,
    label="Steps",
    tooltip="Number of interpolation steps",
    tab="advanced",
)

CLICK_COUNT_PROP = PropertyDef(
    "click_count",
    PropertyType.INTEGER,
    default=1,
    min_value=1,
    label="Click Count",
    tooltip="Number of clicks",
    tab="advanced",
)

CLICK_DELAY_PROP = PropertyDef(
    "delay",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Click Delay (ms)",
    tooltip="Delay between click down and up",
    tab="advanced",
)

PRESS_ENTER_AFTER_PROP = PropertyDef(
    "press_enter_after",
    PropertyType.BOOLEAN,
    default=False,
    label="Press Enter After",
    tooltip="Press Enter after typing",
    tab="advanced",
)

WAIT_TIME_PROP = PropertyDef(
    "wait_time",
    PropertyType.FLOAT,
    default=0.0,
    min_value=0.0,
    label="Wait Time (seconds)",
    tooltip="Delay after sending hotkey",
    tab="advanced",
)

KEY_PROP = PropertyDef(
    "key",
    PropertyType.STRING,
    default="Enter",
    label="Key",
    tooltip="Main key to press",
    tab="properties",
)


@node_schema(DURATION_PROP, EASE_PROP, STEPS_PROP)
@executable_node
class MoveMouseNode(DesktopNodeBase):
    """
    Move the mouse cursor to a specific position.

    Config (via @node_schema):
        duration: Animation duration in seconds (default: 0.0)
        ease: Easing function (default: "linear")
        steps: Number of interpolation steps (default: 10)

    Inputs:
        x: Target X coordinate
        y: Target Y coordinate
        duration: Animation duration (overrides config)

    Outputs:
        success: Whether operation succeeded
        final_x: Final X position
        final_y: Final Y position
    """

    # @category: desktop
    # @requires: none
    # @ports: x, y, duration -> success, final_x, final_y

    NODE_NAME = "Move Mouse"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Move Mouse",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "MoveMouseNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("x", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("y", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("duration", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("final_x", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("final_y", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute mouse movement."""
        x = self.get_input_value("x")
        y = self.get_input_value("y")
        duration = self.get_parameter("duration", context)
        ease = self.get_parameter("ease", context)
        steps = self.get_parameter("steps", context)

        if x is None:
            raise ValueError("X coordinate is required")
        if y is None:
            raise ValueError("Y coordinate is required")

        desktop_ctx = self.get_desktop_context(context)

        # Build kwargs for move_mouse
        import inspect

        move_kwargs: Dict[str, Any] = {}
        if hasattr(desktop_ctx, "move_mouse"):
            sig = inspect.signature(desktop_ctx.move_mouse)
            if "ease" in sig.parameters:
                move_kwargs["ease"] = ease
            if "steps" in sig.parameters:
                move_kwargs["steps"] = steps

        success = desktop_ctx.move_mouse(int(x), int(y), float(duration), **move_kwargs)

        self.set_output_value("success", success)
        self.set_output_value("final_x", int(x))
        self.set_output_value("final_y", int(y))
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return self.success_result(x=x, y=y, duration=duration, ease=ease)


@node_schema(
    MOUSE_BUTTON_PROP,
    CLICK_TYPE_PROP,
    CLICK_COUNT_PROP,
    WITH_CTRL_PROP,
    WITH_SHIFT_PROP,
    WITH_ALT_PROP,
    CLICK_DELAY_PROP,
)
@executable_node
class MouseClickNode(DesktopNodeBase):
    """
    Perform mouse clicks at a position.

    Config (via @node_schema):
        button: Mouse button - left/right/middle (default: "left")
        click_type: Click type - single/double/triple (default: "single")
        click_count: Number of clicks (default: 1)
        with_ctrl: Hold Ctrl (default: False)
        with_shift: Hold Shift (default: False)
        with_alt: Hold Alt (default: False)
        delay: Delay between down/up in ms (default: 0)

    Inputs:
        x: X coordinate (optional, uses current position)
        y: Y coordinate (optional, uses current position)

    Outputs:
        success: Whether click succeeded
        click_x: X coordinate of click
        click_y: Y coordinate of click
    """

    # @category: desktop
    # @requires: none
    # @ports: x, y -> success, click_x, click_y

    NODE_NAME = "Mouse Click"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Mouse Click",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "MouseClickNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("x", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("y", PortType.INPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("click_x", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("click_y", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute mouse click."""
        x = self.get_input_value("x")
        y = self.get_input_value("y")
        button = self.get_parameter("button", context)
        click_type = self.get_parameter("click_type", context)
        click_count = self.get_parameter("click_count", context)
        ctrl = self.get_parameter("with_ctrl", context)
        shift = self.get_parameter("with_shift", context)
        alt = self.get_parameter("with_alt", context)
        delay = self.get_parameter("delay", context)

        # Determine actual click count from click_type
        if click_type == "double":
            click_count = 2
        elif click_type == "triple":
            click_count = 3

        desktop_ctx = self.get_desktop_context(context)

        # Build modifiers list
        modifiers = []
        if ctrl:
            modifiers.append("ctrl")
        if shift:
            modifiers.append("shift")
        if alt:
            modifiers.append("alt")

        # Build click kwargs
        click_kwargs: Dict[str, Any] = {
            "x": int(x) if x is not None else None,
            "y": int(y) if y is not None else None,
            "button": button,
            "click_type": click_type,
        }

        # Add optional parameters if supported
        import inspect

        if hasattr(desktop_ctx, "click_mouse"):
            sig = inspect.signature(desktop_ctx.click_mouse)
            if "modifiers" in sig.parameters and modifiers:
                click_kwargs["modifiers"] = modifiers
            if "click_count" in sig.parameters:
                click_kwargs["click_count"] = click_count
            if "delay" in sig.parameters and delay > 0:
                click_kwargs["delay"] = delay

        success = desktop_ctx.click_mouse(**click_kwargs)

        self.set_output_value("success", success)
        self.set_output_value("click_x", int(x) if x is not None else 0)
        self.set_output_value("click_y", int(y) if y is not None else 0)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return self.success_result(
            x=x, y=y, button=button, click_type=click_type, modifiers=modifiers
        )


@node_schema(
    KEYS_PROP,
    INTERVAL_PROP,
    WITH_SHIFT_PROP,
    WITH_CTRL_PROP,
    WITH_ALT_PROP,
    PRESS_ENTER_AFTER_PROP,
    CLEAR_FIRST_PROP,
)
@executable_node
class SendKeysNode(DesktopNodeBase):
    """
    Send keyboard input.

    Config (via @node_schema):
        keys: Keys to send (default: "")
        interval: Delay between keystrokes (default: 0.0)
        with_shift: Hold Shift (default: False)
        with_ctrl: Hold Ctrl (default: False)
        with_alt: Hold Alt (default: False)
        press_enter_after: Press Enter after typing (default: False)
        clear_first: Clear field before typing (default: False)

    Inputs:
        keys: Keys to send (overrides config)
        interval: Delay between keystrokes (overrides config)

    Outputs:
        success: Whether operation succeeded
        keys_sent: Number of keys sent

    Special keys use {Key} format: {Enter}, {Tab}, {Ctrl}, etc.
    """

    # @category: desktop
    # @requires: none
    # @ports: keys, interval -> success, keys_sent

    NODE_NAME = "Send Keys"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Send Keys",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "SendKeysNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("keys", PortType.INPUT, DataType.STRING)
        self.add_input_port("interval", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("keys_sent", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute key sending."""
        keys = self.get_parameter("keys", context)
        interval = self.get_parameter("interval", context)
        with_shift = self.get_parameter("with_shift", context)
        with_ctrl = self.get_parameter("with_ctrl", context)
        with_alt = self.get_parameter("with_alt", context)
        press_enter_after = self.get_parameter("press_enter_after", context)
        clear_first = self.get_parameter("clear_first", context)

        if not keys:
            raise ValueError("Keys to send are required")

        desktop_ctx = self.get_desktop_context(context)

        # Clear field first if requested
        if clear_first:
            desktop_ctx.send_hotkey("Ctrl", "a")
            desktop_ctx.send_keys("{Delete}", 0)

        # Build modifiers
        modifiers = []
        if with_shift:
            modifiers.append("shift")
        if with_ctrl:
            modifiers.append("ctrl")
        if with_alt:
            modifiers.append("alt")

        # Send keys with or without modifiers
        if modifiers and hasattr(desktop_ctx, "send_keys_with_modifiers"):
            success = desktop_ctx.send_keys_with_modifiers(
                str(keys), modifiers, float(interval)
            )
        else:
            success = desktop_ctx.send_keys(str(keys), float(interval))

        # Press Enter after if requested
        if press_enter_after and success:
            desktop_ctx.send_keys("{Enter}", 0)

        self.set_output_value("success", success)
        self.set_output_value("keys_sent", len(str(keys)))
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return self.success_result(keys=keys, interval=interval, modifiers=modifiers)


@node_schema(HOTKEY_MODIFIER_PROP, KEY_PROP, KEYS_PROP, WAIT_TIME_PROP)
@executable_node
class SendHotKeyNode(DesktopNodeBase):
    """
    Send hotkey combinations (e.g., Ctrl+C, Alt+Tab, Enter).

    Config (via @node_schema):
        modifier: Modifier key (default: "none")
        key: Main key to press (default: "Enter")
        keys: Custom comma-separated keys (default: "")
        wait_time: Delay after sending (default: 0.0)

    Inputs:
        keys: Comma-separated list of keys (overrides config)
        wait_time: Delay after sending (overrides config)

    Outputs:
        success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: keys, wait_time -> success

    NODE_NAME = "Send Hotkey"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Send Hotkey",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "SendHotKeyNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("keys", PortType.INPUT, DataType.STRING)
        self.add_input_port("wait_time", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute hotkey combination."""
        keys_input = self.get_parameter("keys", context)

        # Determine which keys to send
        if keys_input:
            keys_str = keys_input
        else:
            # Build from modifier + key
            modifier = self.get_parameter("modifier", context)
            key = self.get_parameter("key", context)

            if modifier and str(modifier).lower() != "none":
                keys_str = f"{modifier},{key}"
            else:
                keys_str = key

        if not keys_str:
            raise ValueError("Hotkey combination is required")

        # Parse comma-separated keys
        keys = [k.strip() for k in str(keys_str).split(",")]

        desktop_ctx = self.get_desktop_context(context)

        success = desktop_ctx.send_hotkey(*keys)

        # Apply wait time after sending
        wait_time = self.get_parameter("wait_time", context)
        if wait_time and float(wait_time) > 0:
            await asyncio.sleep(float(wait_time))

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return self.success_result(keys=keys)


@executable_node
class GetMousePositionNode(DesktopNodeBase):
    """
    Get the current mouse cursor position.

    Outputs:
        x: Current X coordinate
        y: Current Y coordinate
    """

    # @category: desktop
    # @requires: none
    # @ports: none -> x, y

    NODE_NAME = "Get Mouse Position"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Get Mouse Position",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "GetMousePositionNode"

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_output_port("x", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("y", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Get current mouse position."""
        desktop_ctx = self.get_desktop_context(context)

        x, y = desktop_ctx.get_mouse_position()

        self.set_output_value("x", x)
        self.set_output_value("y", y)
        self.status = NodeStatus.SUCCESS

        return self.success_result(x=x, y=y)


@node_schema(MOUSE_BUTTON_PROP, DURATION_PROP)
@executable_node
class DragMouseNode(DesktopNodeBase):
    """
    Drag the mouse from one position to another.

    Config (via @node_schema):
        button: Mouse button to hold (default: "left")
        duration: Drag duration in seconds (default: 0.5)

    Inputs:
        start_x: Starting X coordinate
        start_y: Starting Y coordinate
        end_x: Ending X coordinate
        end_y: Ending Y coordinate
        duration: Drag duration (overrides config)

    Outputs:
        success: Whether operation succeeded
    """

    # @category: desktop
    # @requires: none
    # @ports: start_x, start_y, end_x, end_y, duration -> success

    NODE_NAME = "Drag Mouse"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Drag Mouse",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "DragMouseNode"

    def _get_default_config(self) -> Dict[str, Any]:
        """Override default duration for drag."""
        return {"duration": 0.5}

    def _define_ports(self) -> None:
        """Define input and output ports."""
        self.add_input_port("start_x", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("start_y", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("end_x", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("end_y", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("duration", PortType.INPUT, DataType.FLOAT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute mouse drag."""
        start_x = self.get_input_value("start_x")
        start_y = self.get_input_value("start_y")
        end_x = self.get_input_value("end_x")
        end_y = self.get_input_value("end_y")
        duration = self.get_parameter("duration", context)
        button = self.get_parameter("button", context)

        if start_x is None or start_y is None:
            raise ValueError("Start coordinates are required")
        if end_x is None or end_y is None:
            raise ValueError("End coordinates are required")

        desktop_ctx = self.get_desktop_context(context)

        success = desktop_ctx.drag_mouse(
            int(start_x),
            int(start_y),
            int(end_x),
            int(end_y),
            button=button,
            duration=float(duration),
        )

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return self.success_result(
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            button=button,
            duration=duration,
        )

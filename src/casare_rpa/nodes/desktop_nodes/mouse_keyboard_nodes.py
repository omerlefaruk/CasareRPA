"""
Mouse and Keyboard Control Nodes for CasareRPA

Provides nodes for direct mouse and keyboard input:
- MoveMouseNode: Move cursor to position
- MouseClickNode: Click at position
- SendKeysNode: Send keyboard input
- SendHotKeyNode: Send hotkey combinations
- GetMousePositionNode: Get current cursor position
- DragMouseNode: Drag from one position to another
"""

from typing import Any, Dict, Optional
from loguru import logger

from ...core.base_node import BaseNode
from ...core.types import PortType, DataType, NodeStatus
from ...desktop import DesktopContext


def safe_int(value, default: int) -> int:
    """Safely parse int values with defaults."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


class MoveMouseNode(BaseNode):
    """
    Node to move the mouse cursor to a specific position.

    Inputs:
        - x: X coordinate
        - y: Y coordinate
        - duration: Animation duration in seconds (0 for instant)

    Config:
        - ease: Easing function ('linear', 'ease_in', 'ease_out', 'ease_in_out')
        - steps: Number of interpolation steps for smooth movement

    Outputs:
        - success: Whether the operation succeeded
        - final_x: Final X position
        - final_y: Final Y position
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Move Mouse"):
        default_config = {
            "duration": 0.0,
            "ease": "linear",  # linear, ease_in, ease_out, ease_in_out
            "steps": 10,  # Number of interpolation steps
        }
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "MoveMouseNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("x", DataType.INTEGER, "X coordinate")
        self.add_input_port("y", DataType.INTEGER, "Y coordinate")
        self.add_input_port("duration", DataType.FLOAT, "Animation duration (seconds)")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")
        self.add_output_port("final_x", DataType.INTEGER, "Final X position")
        self.add_output_port("final_y", DataType.INTEGER, "Final Y position")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute mouse movement"""
        x = self.get_input_value("x")
        y = self.get_input_value("y")
        duration = self.get_input_value("duration") or self.config.get("duration", 0.0)
        ease = self.config.get("ease", "linear")
        steps = self.config.get("steps", 10)

        if x is None:
            raise ValueError("X coordinate is required")
        if y is None:
            raise ValueError("Y coordinate is required")

        if not hasattr(context, 'desktop_context') or context.desktop_context is None:
            context.desktop_context = DesktopContext()
        desktop_ctx = context.desktop_context

        # Pass ease and steps to desktop context if supported
        move_kwargs = {}
        if hasattr(desktop_ctx, 'move_mouse'):
            import inspect
            sig = inspect.signature(desktop_ctx.move_mouse)
            if 'ease' in sig.parameters:
                move_kwargs['ease'] = ease
            if 'steps' in sig.parameters:
                move_kwargs['steps'] = steps

        success = desktop_ctx.move_mouse(int(x), int(y), float(duration), **move_kwargs)

        self.set_output_value("success", success)
        self.set_output_value("final_x", int(x))
        self.set_output_value("final_y", int(y))
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "x": x,
            "y": y,
            "duration": duration,
            "ease": ease
        }


class MouseClickNode(BaseNode):
    """
    Node to perform mouse clicks at a position.

    Inputs:
        - x: X coordinate (optional, uses current position if not provided)
        - y: Y coordinate (optional, uses current position if not provided)

    Config:
        - button: "left", "right", or "middle"
        - click_type: "single", "double", or "triple"
        - click_count: Number of clicks (alternative to click_type)
        - ctrl: Hold Ctrl key during click
        - shift: Hold Shift key during click
        - alt: Hold Alt key during click
        - delay: Delay between click down and up (ms)

    Outputs:
        - success: Whether the click succeeded
        - click_x: X coordinate where click occurred
        - click_y: Y coordinate where click occurred
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Mouse Click"):
        default_config = {
            "button": "left",
            "click_type": "single",
            "click_count": 1,
            "ctrl": False,
            "shift": False,
            "alt": False,
            "delay": 0,  # ms between down and up
        }
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "MouseClickNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("x", DataType.INTEGER, "X coordinate (optional)")
        self.add_input_port("y", DataType.INTEGER, "Y coordinate (optional)")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")
        self.add_output_port("click_x", DataType.INTEGER, "X coordinate of click")
        self.add_output_port("click_y", DataType.INTEGER, "Y coordinate of click")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute mouse click"""
        x = self.get_input_value("x")
        y = self.get_input_value("y")
        button = self.config.get("button", "left")
        click_type = self.config.get("click_type", "single")
        click_count = self.config.get("click_count", 1)
        ctrl = self.config.get("ctrl", False)
        shift = self.config.get("shift", False)
        alt = self.config.get("alt", False)
        delay = self.config.get("delay", 0)

        # Determine actual click count from click_type or click_count
        if click_type == "double":
            click_count = 2
        elif click_type == "triple":
            click_count = 3

        if not hasattr(context, 'desktop_context') or context.desktop_context is None:
            context.desktop_context = DesktopContext()
        desktop_ctx = context.desktop_context

        # Build modifiers list
        modifiers = []
        if ctrl:
            modifiers.append("ctrl")
        if shift:
            modifiers.append("shift")
        if alt:
            modifiers.append("alt")

        # Check if desktop context supports modifiers
        click_kwargs = {
            "x": int(x) if x is not None else None,
            "y": int(y) if y is not None else None,
            "button": button,
            "click_type": click_type,
        }

        # Add optional parameters if supported
        import inspect
        if hasattr(desktop_ctx, 'click_mouse'):
            sig = inspect.signature(desktop_ctx.click_mouse)
            if 'modifiers' in sig.parameters and modifiers:
                click_kwargs['modifiers'] = modifiers
            if 'click_count' in sig.parameters:
                click_kwargs['click_count'] = click_count
            if 'delay' in sig.parameters and delay > 0:
                click_kwargs['delay'] = delay

        success = desktop_ctx.click_mouse(**click_kwargs)

        self.set_output_value("success", success)
        self.set_output_value("click_x", int(x) if x is not None else 0)
        self.set_output_value("click_y", int(y) if y is not None else 0)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "x": x,
            "y": y,
            "button": button,
            "click_type": click_type,
            "modifiers": modifiers
        }


class SendKeysNode(BaseNode):
    """
    Node to send keyboard input.

    Inputs:
        - keys: Text or key sequence to send
        - interval: Delay between keystrokes (seconds)

    Config:
        - interval: Default delay between keystrokes (seconds)
        - with_shift: Hold Shift while typing
        - with_ctrl: Hold Ctrl while typing
        - with_alt: Hold Alt while typing
        - press_enter_after: Press Enter after typing
        - clear_first: Send Ctrl+A, Delete before typing to clear field

    Outputs:
        - success: Whether the operation succeeded
        - keys_sent: Number of keys sent

    Special keys can be enclosed in braces: {Enter}, {Tab}, {Ctrl}, etc.
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Send Keys"):
        default_config = {
            "interval": 0.0,
            "with_shift": False,
            "with_ctrl": False,
            "with_alt": False,
            "press_enter_after": False,
            "clear_first": False,
        }
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "SendKeysNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("keys", DataType.STRING, "Keys to send")
        self.add_input_port("interval", DataType.FLOAT, "Delay between keys (seconds)")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")
        self.add_output_port("keys_sent", DataType.INTEGER, "Number of keys sent")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute key sending"""
        keys = self.get_input_value("keys")
        interval = self.get_input_value("interval") or self.config.get("interval", 0.0)
        with_shift = self.config.get("with_shift", False)
        with_ctrl = self.config.get("with_ctrl", False)
        with_alt = self.config.get("with_alt", False)
        press_enter_after = self.config.get("press_enter_after", False)
        clear_first = self.config.get("clear_first", False)

        # Resolve {{variable}} patterns in keys
        if hasattr(context, 'resolve_value') and keys:
            keys = context.resolve_value(keys)

        if not keys:
            raise ValueError("Keys to send are required")

        if not hasattr(context, 'desktop_context') or context.desktop_context is None:
            context.desktop_context = DesktopContext()
        desktop_ctx = context.desktop_context

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
        if modifiers and hasattr(desktop_ctx, 'send_keys_with_modifiers'):
            success = desktop_ctx.send_keys_with_modifiers(str(keys), modifiers, float(interval))
        else:
            success = desktop_ctx.send_keys(str(keys), float(interval))

        # Press Enter after if requested
        if press_enter_after and success:
            desktop_ctx.send_keys("{Enter}", 0)

        self.set_output_value("success", success)
        self.set_output_value("keys_sent", len(str(keys)))
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "keys": keys,
            "interval": interval,
            "modifiers": modifiers
        }


class SendHotKeyNode(BaseNode):
    """
    Node to send hotkey combinations (e.g., Ctrl+C, Alt+Tab, Enter).

    Config:
        - modifier: Modifier key (none, Ctrl, Alt, Shift, Win)
        - key: Main key to press (e.g., Enter, C, Delete)
        - keys: Custom comma-separated keys (overrides modifier+key if provided)

    Inputs:
        - keys: Comma-separated list of keys (overrides config)

    Outputs:
        - success: Whether the operation succeeded
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Send Hotkey"):
        default_config = {
            "modifier": "none",
            "key": "Enter",
            "keys": ""
        }
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "SendHotKeyNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("keys", DataType.STRING, "Hotkey combination (e.g., 'Ctrl,C')")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute hotkey combination"""
        # Priority: input port > config.keys > config.modifier+key
        keys_input = self.get_input_value("keys")

        # Resolve {{variable}} patterns
        if hasattr(context, 'resolve_value') and keys_input:
            keys_input = context.resolve_value(keys_input)

        # Determine which keys to send
        if keys_input:
            # Input port has highest priority
            keys_str = keys_input
        elif self.config.get("keys"):
            # Custom keys from config
            keys_str = self.config.get("keys")
            if hasattr(context, 'resolve_value'):
                keys_str = context.resolve_value(keys_str)
        else:
            # Build from modifier + key
            modifier = self.config.get("modifier", "none")
            key = self.config.get("key", "Enter")

            # Resolve variables
            if hasattr(context, 'resolve_value'):
                modifier = context.resolve_value(str(modifier))
                key = context.resolve_value(str(key))

            # Build keys string
            if modifier and modifier.lower() != "none":
                keys_str = f"{modifier},{key}"
            else:
                keys_str = key

        if not keys_str:
            raise ValueError("Hotkey combination is required")

        # Parse comma-separated keys
        keys = [k.strip() for k in str(keys_str).split(",")]

        if not hasattr(context, 'desktop_context') or context.desktop_context is None:
            context.desktop_context = DesktopContext()
        desktop_ctx = context.desktop_context

        success = desktop_ctx.send_hotkey(*keys)

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "keys": keys
        }


class GetMousePositionNode(BaseNode):
    """
    Node to get the current mouse cursor position.

    Outputs:
        - x: Current X coordinate
        - y: Current Y coordinate
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Get Mouse Position"):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetMousePositionNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_output_port("x", DataType.INTEGER, "X coordinate")
        self.add_output_port("y", DataType.INTEGER, "Y coordinate")

    async def execute(self, context) -> Dict[str, Any]:
        """Get current mouse position"""
        if not hasattr(context, 'desktop_context') or context.desktop_context is None:
            context.desktop_context = DesktopContext()
        desktop_ctx = context.desktop_context

        x, y = desktop_ctx.get_mouse_position()

        self.set_output_value("x", x)
        self.set_output_value("y", y)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "x": x,
            "y": y
        }


class DragMouseNode(BaseNode):
    """
    Node to drag the mouse from one position to another.

    Inputs:
        - start_x: Starting X coordinate
        - start_y: Starting Y coordinate
        - end_x: Ending X coordinate
        - end_y: Ending Y coordinate
        - duration: Drag duration in seconds

    Config:
        - button: Mouse button to hold ("left", "right", "middle")

    Outputs:
        - success: Whether the operation succeeded
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Drag Mouse"):
        default_config = {
            "button": "left",
            "duration": 0.5
        }
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "DragMouseNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("start_x", DataType.INTEGER, "Start X coordinate")
        self.add_input_port("start_y", DataType.INTEGER, "Start Y coordinate")
        self.add_input_port("end_x", DataType.INTEGER, "End X coordinate")
        self.add_input_port("end_y", DataType.INTEGER, "End Y coordinate")
        self.add_input_port("duration", DataType.FLOAT, "Drag duration (seconds)")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute mouse drag"""
        start_x = self.get_input_value("start_x")
        start_y = self.get_input_value("start_y")
        end_x = self.get_input_value("end_x")
        end_y = self.get_input_value("end_y")
        duration = self.get_input_value("duration") or self.config.get("duration", 0.5)
        button = self.config.get("button", "left")

        if start_x is None or start_y is None:
            raise ValueError("Start coordinates are required")
        if end_x is None or end_y is None:
            raise ValueError("End coordinates are required")

        if not hasattr(context, 'desktop_context') or context.desktop_context is None:
            context.desktop_context = DesktopContext()
        desktop_ctx = context.desktop_context

        success = desktop_ctx.drag_mouse(
            int(start_x), int(start_y),
            int(end_x), int(end_y),
            button=button,
            duration=float(duration)
        )

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "start_x": start_x,
            "start_y": start_y,
            "end_x": end_x,
            "end_y": end_y,
            "button": button,
            "duration": duration
        }

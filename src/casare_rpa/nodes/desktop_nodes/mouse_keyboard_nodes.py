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
from ...core.base_node import BaseNode
from ...core.types import PortType, DataType, NodeStatus


class MoveMouseNode(BaseNode):
    """
    Node to move the mouse cursor to a specific position.

    Inputs:
        - x: X coordinate
        - y: Y coordinate
        - duration: Animation duration in seconds (0 for instant)

    Outputs:
        - success: Whether the operation succeeded
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Move Mouse"):
        if config is None:
            config = {"duration": 0.0}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MoveMouseNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("x", DataType.INTEGER, "X coordinate")
        self.add_input_port("y", DataType.INTEGER, "Y coordinate")
        self.add_input_port("duration", DataType.FLOAT, "Animation duration (seconds)")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute mouse movement"""
        x = self.get_input_value("x")
        y = self.get_input_value("y")
        duration = self.get_input_value("duration") or self.config.get("duration", 0.0)

        if x is None:
            raise ValueError("X coordinate is required")
        if y is None:
            raise ValueError("Y coordinate is required")

        desktop_ctx = getattr(context, 'desktop_context', None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        success = desktop_ctx.move_mouse(int(x), int(y), float(duration))

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "x": x,
            "y": y,
            "duration": duration
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

    Outputs:
        - success: Whether the click succeeded
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Mouse Click"):
        default_config = {
            "button": "left",
            "click_type": "single"
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

    async def execute(self, context) -> Dict[str, Any]:
        """Execute mouse click"""
        x = self.get_input_value("x")
        y = self.get_input_value("y")
        button = self.config.get("button", "left")
        click_type = self.config.get("click_type", "single")

        desktop_ctx = getattr(context, 'desktop_context', None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        success = desktop_ctx.click_mouse(
            x=int(x) if x is not None else None,
            y=int(y) if y is not None else None,
            button=button,
            click_type=click_type
        )

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "x": x,
            "y": y,
            "button": button,
            "click_type": click_type
        }


class SendKeysNode(BaseNode):
    """
    Node to send keyboard input.

    Inputs:
        - keys: Text or key sequence to send
        - interval: Delay between keystrokes (seconds)

    Outputs:
        - success: Whether the operation succeeded

    Special keys can be enclosed in braces: {Enter}, {Tab}, {Ctrl}, etc.
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Send Keys"):
        default_config = {
            "interval": 0.0
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

    async def execute(self, context) -> Dict[str, Any]:
        """Execute key sending"""
        keys = self.get_input_value("keys")
        interval = self.get_input_value("interval") or self.config.get("interval", 0.0)

        if not keys:
            raise ValueError("Keys to send are required")

        desktop_ctx = getattr(context, 'desktop_context', None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        success = desktop_ctx.send_keys(str(keys), float(interval))

        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.FAILED

        return {
            "success": success,
            "keys": keys,
            "interval": interval
        }


class SendHotKeyNode(BaseNode):
    """
    Node to send hotkey combinations (e.g., Ctrl+C, Alt+Tab).

    Inputs:
        - keys: Comma-separated list of keys (e.g., "Ctrl,C" or "Alt,Tab")

    Outputs:
        - success: Whether the operation succeeded
    """

    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Send Hotkey"):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SendHotKeyNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("keys", DataType.STRING, "Hotkey combination (e.g., 'Ctrl,C')")
        self.add_output_port("success", DataType.BOOLEAN, "Operation success")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute hotkey combination"""
        keys_input = self.get_input_value("keys")

        if not keys_input:
            raise ValueError("Hotkey combination is required")

        # Parse comma-separated keys
        keys = [k.strip() for k in str(keys_input).split(",")]

        desktop_ctx = getattr(context, 'desktop_context', None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

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
        desktop_ctx = getattr(context, 'desktop_context', None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

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

        desktop_ctx = getattr(context, 'desktop_context', None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

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

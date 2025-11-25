"""
Desktop Recorder for CasareRPA

Captures mouse clicks, keyboard input, and desktop actions with global hotkeys.
Converts recorded actions into workflow nodes.
"""

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable
from loguru import logger

try:
    import uiautomation as auto
    HAS_UIAUTOMATION = True
except ImportError:
    HAS_UIAUTOMATION = False
    logger.warning("uiautomation not available - desktop recording limited")

try:
    from pynput import mouse, keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
    logger.warning("pynput not available - install with: pip install pynput")


class DesktopActionType(Enum):
    """Types of desktop actions that can be recorded."""
    MOUSE_CLICK = "mouse_click"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    MOUSE_RIGHT_CLICK = "mouse_right_click"
    KEYBOARD_TYPE = "keyboard_type"
    KEYBOARD_HOTKEY = "keyboard_hotkey"
    MOUSE_DRAG = "mouse_drag"
    WINDOW_ACTIVATE = "window_activate"


@dataclass
class DesktopRecordedAction:
    """Represents a single recorded desktop action."""

    action_type: DesktopActionType
    timestamp: datetime = field(default_factory=datetime.now)

    # Mouse properties
    x: int = 0
    y: int = 0
    end_x: int = 0  # For drag
    end_y: int = 0  # For drag

    # Keyboard properties
    text: str = ""
    keys: List[str] = field(default_factory=list)

    # Element properties (from UI Automation)
    element_name: str = ""
    element_type: str = ""
    element_automation_id: str = ""
    element_class_name: str = ""
    window_title: str = ""

    # Selector for replay
    selector: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary."""
        return {
            'action_type': self.action_type.value,
            'timestamp': self.timestamp.isoformat(),
            'x': self.x,
            'y': self.y,
            'end_x': self.end_x,
            'end_y': self.end_y,
            'text': self.text,
            'keys': self.keys,
            'element_name': self.element_name,
            'element_type': self.element_type,
            'element_automation_id': self.element_automation_id,
            'element_class_name': self.element_class_name,
            'window_title': self.window_title,
            'selector': self.selector,
        }

    def get_description(self) -> str:
        """Get human-readable description of the action."""
        if self.action_type == DesktopActionType.MOUSE_CLICK:
            target = self.element_name or f"({self.x}, {self.y})"
            return f"Click on {target}"
        elif self.action_type == DesktopActionType.MOUSE_DOUBLE_CLICK:
            target = self.element_name or f"({self.x}, {self.y})"
            return f"Double-click on {target}"
        elif self.action_type == DesktopActionType.MOUSE_RIGHT_CLICK:
            target = self.element_name or f"({self.x}, {self.y})"
            return f"Right-click on {target}"
        elif self.action_type == DesktopActionType.KEYBOARD_TYPE:
            return f"Type: {self.text[:30]}..." if len(self.text) > 30 else f"Type: {self.text}"
        elif self.action_type == DesktopActionType.KEYBOARD_HOTKEY:
            return f"Hotkey: {'+'.join(self.keys)}"
        elif self.action_type == DesktopActionType.MOUSE_DRAG:
            return f"Drag from ({self.x}, {self.y}) to ({self.end_x}, {self.end_y})"
        elif self.action_type == DesktopActionType.WINDOW_ACTIVATE:
            return f"Activate window: {self.window_title}"
        return "Unknown action"


class DesktopRecorder:
    """
    Desktop action recorder with global hotkeys.

    Hotkeys:
    - F9: Start/Stop recording
    - F10: Pause/Resume recording
    - Escape: Cancel recording
    """

    def __init__(self):
        """Initialize the desktop recorder."""
        self.actions: List[DesktopRecordedAction] = []
        self.is_recording = False
        self.is_paused = False
        self.start_time: Optional[datetime] = None

        # Listeners
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None

        # Callbacks
        self._on_action_recorded: Optional[Callable[[DesktopRecordedAction], None]] = None
        self._on_recording_started: Optional[Callable[[], None]] = None
        self._on_recording_stopped: Optional[Callable[[], None]] = None
        self._on_recording_paused: Optional[Callable[[bool], None]] = None

        # Keyboard state tracking
        self._pressed_keys: set = set()
        self._text_buffer: str = ""
        self._last_key_time: float = 0
        self._text_flush_delay: float = 0.5  # Flush text after 500ms of no typing

        # Mouse state tracking
        self._drag_start: Optional[tuple] = None
        self._last_click_time: float = 0
        self._double_click_threshold: float = 0.3

        # Global hotkey tracking
        self._hotkey_active = False

        logger.info("Desktop recorder initialized")

    def set_callbacks(
        self,
        on_action_recorded: Optional[Callable[[DesktopRecordedAction], None]] = None,
        on_recording_started: Optional[Callable[[], None]] = None,
        on_recording_stopped: Optional[Callable[[], None]] = None,
        on_recording_paused: Optional[Callable[[bool], None]] = None
    ):
        """Set callback functions for recording events."""
        self._on_action_recorded = on_action_recorded
        self._on_recording_started = on_recording_started
        self._on_recording_stopped = on_recording_stopped
        self._on_recording_paused = on_recording_paused

    def start(self):
        """Start recording desktop actions."""
        if not HAS_PYNPUT:
            raise RuntimeError("pynput not installed. Install with: pip install pynput")

        if self.is_recording:
            logger.warning("Recording already in progress")
            return

        self.actions.clear()
        self.is_recording = True
        self.is_paused = False
        self.start_time = datetime.now()
        self._text_buffer = ""
        self._pressed_keys.clear()

        # Start listeners
        self._start_listeners()

        logger.info("Desktop recording started")

        if self._on_recording_started:
            self._on_recording_started()

    def stop(self) -> List[DesktopRecordedAction]:
        """Stop recording and return recorded actions."""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return []

        # Flush any remaining text
        self._flush_text_buffer()

        # Stop listeners
        self._stop_listeners()

        self.is_recording = False
        self.is_paused = False

        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        logger.info(f"Desktop recording stopped. Duration: {duration:.2f}s, Actions: {len(self.actions)}")

        if self._on_recording_stopped:
            self._on_recording_stopped()

        return self.actions.copy()

    def pause(self):
        """Pause recording."""
        if not self.is_recording:
            return

        self.is_paused = True
        self._flush_text_buffer()

        logger.info("Desktop recording paused")

        if self._on_recording_paused:
            self._on_recording_paused(True)

    def resume(self):
        """Resume recording."""
        if not self.is_recording:
            return

        self.is_paused = False

        logger.info("Desktop recording resumed")

        if self._on_recording_paused:
            self._on_recording_paused(False)

    def toggle_pause(self):
        """Toggle pause state."""
        if self.is_paused:
            self.resume()
        else:
            self.pause()

    def _start_listeners(self):
        """Start mouse and keyboard listeners."""
        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )
        self._mouse_listener.start()

        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self._keyboard_listener.start()

    def _stop_listeners(self):
        """Stop mouse and keyboard listeners."""
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None

    def _on_mouse_click(self, x: int, y: int, button, pressed: bool):
        """Handle mouse click events."""
        if not self.is_recording or self.is_paused or not pressed:
            return

        # Flush any pending text
        self._flush_text_buffer()

        # Determine action type
        current_time = time.time()

        if button == mouse.Button.left:
            # Check for double-click
            if current_time - self._last_click_time < self._double_click_threshold:
                action_type = DesktopActionType.MOUSE_DOUBLE_CLICK
            else:
                action_type = DesktopActionType.MOUSE_CLICK
            self._last_click_time = current_time
        elif button == mouse.Button.right:
            action_type = DesktopActionType.MOUSE_RIGHT_CLICK
        else:
            return  # Ignore middle button

        # Get element at position
        element_info = self._get_element_at_position(x, y)

        action = DesktopRecordedAction(
            action_type=action_type,
            x=x,
            y=y,
            **element_info
        )

        self._add_action(action)

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse scroll events (currently not recorded)."""
        pass  # Could be implemented if needed

    def _on_key_press(self, key):
        """Handle key press events."""
        if not self.is_recording or self.is_paused:
            return

        # Check for global hotkeys (these should work even when recording)
        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
        except AttributeError:
            key_name = str(key)

        # Handle F9 (toggle recording) - handled externally
        # Handle F10 (pause) - handled externally
        # Handle Escape (cancel) - handled externally

        # Track pressed modifier keys
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                   keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r,
                   keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r,
                   keyboard.Key.cmd):
            self._pressed_keys.add(key)
            return

        # Check if this is a hotkey combination
        if self._pressed_keys:
            self._flush_text_buffer()
            keys = [self._key_to_string(k) for k in self._pressed_keys]
            keys.append(self._key_to_string(key))

            action = DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_HOTKEY,
                keys=keys
            )
            self._add_action(action)
            return

        # Regular key - add to text buffer
        if hasattr(key, 'char') and key.char:
            self._text_buffer += key.char
            self._last_key_time = time.time()
        elif key == keyboard.Key.space:
            self._text_buffer += ' '
            self._last_key_time = time.time()
        elif key == keyboard.Key.enter:
            self._flush_text_buffer()
            # Record Enter as a separate action
            action = DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_HOTKEY,
                keys=['Enter']
            )
            self._add_action(action)
        elif key == keyboard.Key.tab:
            self._flush_text_buffer()
            action = DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_HOTKEY,
                keys=['Tab']
            )
            self._add_action(action)
        elif key == keyboard.Key.backspace:
            if self._text_buffer:
                self._text_buffer = self._text_buffer[:-1]
            else:
                action = DesktopRecordedAction(
                    action_type=DesktopActionType.KEYBOARD_HOTKEY,
                    keys=['Backspace']
                )
                self._add_action(action)

    def _on_key_release(self, key):
        """Handle key release events."""
        self._pressed_keys.discard(key)

    def _key_to_string(self, key) -> str:
        """Convert a key to its string representation."""
        if hasattr(key, 'char') and key.char:
            return key.char.upper()

        key_map = {
            keyboard.Key.ctrl: 'Ctrl',
            keyboard.Key.ctrl_l: 'Ctrl',
            keyboard.Key.ctrl_r: 'Ctrl',
            keyboard.Key.alt: 'Alt',
            keyboard.Key.alt_l: 'Alt',
            keyboard.Key.alt_r: 'Alt',
            keyboard.Key.shift: 'Shift',
            keyboard.Key.shift_l: 'Shift',
            keyboard.Key.shift_r: 'Shift',
            keyboard.Key.cmd: 'Win',
            keyboard.Key.enter: 'Enter',
            keyboard.Key.tab: 'Tab',
            keyboard.Key.backspace: 'Backspace',
            keyboard.Key.delete: 'Delete',
            keyboard.Key.escape: 'Escape',
            keyboard.Key.space: 'Space',
            keyboard.Key.f1: 'F1',
            keyboard.Key.f2: 'F2',
            keyboard.Key.f3: 'F3',
            keyboard.Key.f4: 'F4',
            keyboard.Key.f5: 'F5',
            keyboard.Key.f6: 'F6',
            keyboard.Key.f7: 'F7',
            keyboard.Key.f8: 'F8',
            keyboard.Key.f9: 'F9',
            keyboard.Key.f10: 'F10',
            keyboard.Key.f11: 'F11',
            keyboard.Key.f12: 'F12',
        }

        return key_map.get(key, str(key).replace('Key.', ''))

    def _flush_text_buffer(self):
        """Flush accumulated text as a single type action."""
        if self._text_buffer:
            action = DesktopRecordedAction(
                action_type=DesktopActionType.KEYBOARD_TYPE,
                text=self._text_buffer
            )
            self._add_action(action)
            self._text_buffer = ""

    def _get_element_at_position(self, x: int, y: int) -> Dict[str, Any]:
        """Get UI element information at the given position."""
        result = {
            'element_name': '',
            'element_type': '',
            'element_automation_id': '',
            'element_class_name': '',
            'window_title': '',
            'selector': {}
        }

        if not HAS_UIAUTOMATION:
            return result

        try:
            element = auto.ControlFromPoint(x, y)
            if element:
                result['element_name'] = element.Name or ''
                result['element_type'] = element.ControlTypeName or ''
                result['element_automation_id'] = element.AutomationId or ''
                result['element_class_name'] = element.ClassName or ''

                # Get window title
                window = element
                while window and window.ControlTypeName != 'WindowControl':
                    window = window.GetParentControl()
                if window:
                    result['window_title'] = window.Name or ''

                # Build selector
                result['selector'] = {
                    'name': result['element_name'],
                    'automation_id': result['element_automation_id'],
                    'control_type': result['element_type'],
                    'class_name': result['element_class_name'],
                }
        except Exception as e:
            logger.debug(f"Could not get element at ({x}, {y}): {e}")

        return result

    def _add_action(self, action: DesktopRecordedAction):
        """Add an action to the recording."""
        self.actions.append(action)
        logger.debug(f"Recorded: {action.get_description()}")

        if self._on_action_recorded:
            self._on_action_recorded(action)

    def get_actions(self) -> List[DesktopRecordedAction]:
        """Get all recorded actions."""
        return self.actions.copy()

    def clear(self):
        """Clear all recorded actions."""
        self.actions.clear()
        self._text_buffer = ""
        logger.info("Recording cleared")


class WorkflowGenerator:
    """Generates workflow nodes from recorded desktop actions."""

    @staticmethod
    def generate_workflow_data(actions: List[DesktopRecordedAction]) -> Dict[str, Any]:
        """
        Generate workflow JSON data from recorded actions.

        Args:
            actions: List of recorded desktop actions

        Returns:
            Workflow data dictionary ready for loading
        """
        nodes = []
        connections = []

        # Start node
        start_node_id = "start_1"
        nodes.append({
            "id": start_node_id,
            "type": "StartNode",
            "name": "Start",
            "position": [100, 100],
            "config": {}
        })

        prev_node_id = start_node_id
        y_offset = 200

        for i, action in enumerate(actions):
            node_id = f"action_{i+1}"
            node_data = WorkflowGenerator._action_to_node(action, node_id, y_offset)

            if node_data:
                nodes.append(node_data)

                # Connect to previous node
                connections.append({
                    "from_node": prev_node_id,
                    "from_port": "exec_out",
                    "to_node": node_id,
                    "to_port": "exec_in"
                })

                prev_node_id = node_id
                y_offset += 100

        # End node
        end_node_id = "end_1"
        nodes.append({
            "id": end_node_id,
            "type": "EndNode",
            "name": "End",
            "position": [100, y_offset],
            "config": {}
        })

        connections.append({
            "from_node": prev_node_id,
            "from_port": "exec_out",
            "to_node": end_node_id,
            "to_port": "exec_in"
        })

        return {
            "name": f"Recorded Workflow {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "description": f"Auto-generated from {len(actions)} recorded actions",
            "nodes": nodes,
            "connections": connections
        }

    @staticmethod
    def _action_to_node(action: DesktopRecordedAction, node_id: str, y_pos: int) -> Optional[Dict[str, Any]]:
        """Convert a recorded action to a workflow node."""

        if action.action_type in (DesktopActionType.MOUSE_CLICK,
                                   DesktopActionType.MOUSE_DOUBLE_CLICK,
                                   DesktopActionType.MOUSE_RIGHT_CLICK):
            # Use element selector if available, otherwise use coordinates
            if action.selector and action.selector.get('automation_id'):
                return {
                    "id": node_id,
                    "type": "DesktopClickElementNode",
                    "name": f"Click {action.element_name or 'Element'}",
                    "position": [100, y_pos],
                    "config": {
                        "click_type": "double" if action.action_type == DesktopActionType.MOUSE_DOUBLE_CLICK else
                                     "right" if action.action_type == DesktopActionType.MOUSE_RIGHT_CLICK else "left"
                    },
                    "inputs": {
                        "selector": action.selector
                    }
                }
            else:
                return {
                    "id": node_id,
                    "type": "MouseClickNode",
                    "name": f"Click at ({action.x}, {action.y})",
                    "position": [100, y_pos],
                    "config": {
                        "x": action.x,
                        "y": action.y,
                        "button": "right" if action.action_type == DesktopActionType.MOUSE_RIGHT_CLICK else "left",
                        "clicks": 2 if action.action_type == DesktopActionType.MOUSE_DOUBLE_CLICK else 1
                    }
                }

        elif action.action_type == DesktopActionType.KEYBOARD_TYPE:
            return {
                "id": node_id,
                "type": "DesktopTypeTextNode",
                "name": f"Type: {action.text[:20]}..." if len(action.text) > 20 else f"Type: {action.text}",
                "position": [100, y_pos],
                "config": {},
                "inputs": {
                    "text": action.text
                }
            }

        elif action.action_type == DesktopActionType.KEYBOARD_HOTKEY:
            return {
                "id": node_id,
                "type": "SendHotKeyNode",
                "name": f"Hotkey: {'+'.join(action.keys)}",
                "position": [100, y_pos],
                "config": {
                    "keys": action.keys
                }
            }

        elif action.action_type == DesktopActionType.MOUSE_DRAG:
            return {
                "id": node_id,
                "type": "DragMouseNode",
                "name": f"Drag to ({action.end_x}, {action.end_y})",
                "position": [100, y_pos],
                "config": {
                    "start_x": action.x,
                    "start_y": action.y,
                    "end_x": action.end_x,
                    "end_y": action.end_y
                }
            }

        elif action.action_type == DesktopActionType.WINDOW_ACTIVATE:
            return {
                "id": node_id,
                "type": "ActivateWindowNode",
                "name": f"Activate: {action.window_title[:20]}",
                "position": [100, y_pos],
                "config": {},
                "inputs": {
                    "window_title": action.window_title
                }
            }

        return None

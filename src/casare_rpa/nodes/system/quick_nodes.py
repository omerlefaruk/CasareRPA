"""
Quick Nodes for CasareRPA

Fast utility nodes for hotkey waiting, system beeps, and clipboard monitoring.
"""

import asyncio

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@node_schema(
    PropertyDef(
        "hotkey",
        PropertyType.STRING,
        default="ctrl+shift+a",
        label="Hotkey",
        tooltip="Key combination to wait for (e.g., ctrl+shift+a, f5, alt+tab)",
        essential=True,
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        max_value=300000,
        label="Timeout (ms)",
        tooltip="Maximum wait time in ms (0 = wait forever)",
    ),
    PropertyDef(
        "consume_key",
        PropertyType.BOOLEAN,
        default=True,
        label="Consume Key",
        tooltip="Prevent the key from reaching other applications",
    ),
)
@executable_node
class HotkeyWaitNode(BaseNode):
    """
    Wait for a specific hotkey combination.

    Config (via @node_schema):
        hotkey: Key combination (e.g., 'ctrl+shift+a') (essential)
        timeout: Max wait time in ms, 0 = forever (default: 0)
        consume_key: Block key from other apps (default: True)

    Outputs:
        triggered: True if hotkey was pressed
        timed_out: True if timeout occurred
    """

    # @category: system
    # @requires: none
    # @ports: hotkey -> triggered, timed_out

    def __init__(self, node_id: str, name: str = "Hotkey Wait", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "HotkeyWaitNode"

    def _define_ports(self) -> None:
        self.add_input_port("hotkey", DataType.STRING, required=False)
        self.add_output_port("triggered", DataType.BOOLEAN)
        self.add_output_port("timed_out", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            hotkey_input = self.get_input_value("hotkey")
            if hotkey_input is None:
                hotkey = self.get_parameter("hotkey", "ctrl+shift+a")
            else:
                hotkey = str(hotkey_input)

            hotkey = context.resolve_value(hotkey).lower()
            timeout_ms = int(self.get_parameter("timeout", 0) or 0)
            consume_key = self.get_parameter("consume_key", True)

            triggered = False
            timed_out = False

            try:
                import keyboard

                # Create event for hotkey detection
                hotkey_event = asyncio.Event()

                def on_hotkey():
                    hotkey_event.set()

                # Register hotkey
                keyboard.add_hotkey(hotkey, on_hotkey, suppress=consume_key)

                try:
                    if timeout_ms > 0:
                        try:
                            await asyncio.wait_for(
                                hotkey_event.wait(), timeout=timeout_ms / 1000
                            )
                            triggered = True
                        except asyncio.TimeoutError:
                            timed_out = True
                    else:
                        # Wait indefinitely
                        await hotkey_event.wait()
                        triggered = True

                finally:
                    # Unregister hotkey
                    try:
                        keyboard.remove_hotkey(on_hotkey)
                    except Exception:
                        pass

            except ImportError:
                logger.warning("keyboard library not installed, using fallback")
                # Fallback: Just wait for timeout
                if timeout_ms > 0:
                    await asyncio.sleep(timeout_ms / 1000)
                    timed_out = True
                else:
                    # Can't wait forever without keyboard library
                    logger.error("Cannot wait for hotkey without keyboard library")
                    timed_out = True

            except Exception as e:
                logger.error(f"Hotkey wait error: {e}")
                timed_out = True

            self.set_output_value("triggered", triggered)
            self.set_output_value("timed_out", timed_out)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"triggered": triggered, "timed_out": timed_out},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"HotkeyWaitNode error: {e}")
            self.set_output_value("triggered", False)
            self.set_output_value("timed_out", True)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "frequency",
        PropertyType.INTEGER,
        default=440,
        min_value=37,
        max_value=32767,
        label="Frequency (Hz)",
        tooltip="Beep frequency in Hz (37-32767)",
    ),
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=200,
        min_value=10,
        max_value=10000,
        label="Duration (ms)",
        tooltip="Beep duration in milliseconds",
    ),
)
@executable_node
class BeepNode(BaseNode):
    """
    Play a simple system beep.

    Config (via @node_schema):
        frequency: Beep frequency Hz (default: 440)
        duration: Beep duration ms (default: 200)

    Inputs:
        frequency: Optional - overrides config if connected
        duration: Optional - overrides config if connected

    Outputs:
        success: True if beep was played
    """

    # @category: system
    # @requires: none
    # @ports: frequency, duration -> success

    def __init__(self, node_id: str, name: str = "Beep", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "BeepNode"

    def _define_ports(self) -> None:
        self.add_input_port("frequency", DataType.INTEGER, required=False)
        self.add_input_port("duration", DataType.INTEGER, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            freq_input = self.get_input_value("frequency")
            if freq_input is not None:
                frequency = int(freq_input)
            else:
                frequency = int(self.get_parameter("frequency", 440) or 440)

            dur_input = self.get_input_value("duration")
            if dur_input is not None:
                duration = int(dur_input)
            else:
                duration = int(self.get_parameter("duration", 200) or 200)

            # Clamp values
            frequency = max(37, min(32767, frequency))
            duration = max(10, min(10000, duration))

            success = False

            try:
                import winsound

                winsound.Beep(frequency, duration)
                success = True
            except Exception as e:
                logger.warning(f"winsound.Beep failed: {e}")
                # Try MessageBeep as fallback
                try:
                    import winsound

                    winsound.MessageBeep()
                    success = True
                except Exception:
                    logger.error("Could not play system beep")

            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "played": success,
                    "frequency": frequency,
                    "duration": duration,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"BeepNode error: {e}")
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        min_value=0,
        max_value=300000,
        label="Timeout (ms)",
        tooltip="Maximum wait time in ms (0 = wait forever)",
    ),
    PropertyDef(
        "trigger_on_change",
        PropertyType.BOOLEAN,
        default=True,
        label="Trigger on Change",
        tooltip="Trigger when clipboard content changes",
    ),
    PropertyDef(
        "content_type",
        PropertyType.CHOICE,
        default="text",
        choices=["text", "any"],
        label="Content Type",
        tooltip="Type of clipboard content to monitor",
    ),
)
@executable_node
class ClipboardMonitorNode(BaseNode):
    """
    Monitor clipboard for changes.

    Config (via @node_schema):
        timeout: Max wait time in ms, 0 = forever (default: 30000)
        trigger_on_change: Trigger on content change (default: True)
        content_type: text/any (default: 'text')

    Outputs:
        content: New clipboard content
        changed: True if content changed
        timed_out: True if timeout occurred
    """

    # @category: system
    # @requires: none
    # @ports: none -> content, changed, timed_out

    def __init__(self, node_id: str, name: str = "Clipboard Monitor", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardMonitorNode"

    def _define_ports(self) -> None:
        self.add_output_port("content", DataType.STRING)
        self.add_output_port("changed", DataType.BOOLEAN)
        self.add_output_port("timed_out", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            timeout_ms = int(self.get_parameter("timeout", 30000) or 30000)
            trigger_on_change = self.get_parameter("trigger_on_change", True)
            content_type = self.get_parameter("content_type", "text")

            content = ""
            changed = False
            timed_out = False

            try:
                import pyperclip

                # Get initial clipboard content
                try:
                    initial_content = pyperclip.paste()
                except Exception:
                    initial_content = ""

                poll_interval = 0.1  # 100ms polling
                elapsed = 0

                while True:
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval * 1000

                    try:
                        current_content = pyperclip.paste()
                    except Exception:
                        current_content = ""

                    if trigger_on_change:
                        if current_content != initial_content:
                            content = current_content
                            changed = True
                            break
                    else:
                        # Just return current content immediately if not waiting for change
                        content = current_content
                        break

                    if timeout_ms > 0 and elapsed >= timeout_ms:
                        content = current_content
                        timed_out = True
                        break

            except ImportError:
                logger.warning("pyperclip not installed, trying PySide6")

                try:
                    from PySide6.QtWidgets import QApplication
                    from PySide6.QtGui import QClipboard

                    app = QApplication.instance()
                    if app is None:
                        raise ImportError("No QApplication")

                    clipboard = app.clipboard()

                    try:
                        initial_content = clipboard.text() or ""
                    except Exception:
                        initial_content = ""

                    poll_interval = 0.1
                    elapsed = 0

                    while True:
                        await asyncio.sleep(poll_interval)
                        elapsed += poll_interval * 1000

                        try:
                            current_content = clipboard.text() or ""
                        except Exception:
                            current_content = ""

                        if trigger_on_change:
                            if current_content != initial_content:
                                content = current_content
                                changed = True
                                break
                        else:
                            content = current_content
                            break

                        if timeout_ms > 0 and elapsed >= timeout_ms:
                            content = current_content
                            timed_out = True
                            break

                except ImportError:
                    logger.error(
                        "Neither pyperclip nor PySide6 available for clipboard"
                    )
                    timed_out = True

            self.set_output_value("content", content)
            self.set_output_value("changed", changed)
            self.set_output_value("timed_out", timed_out)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "content": content[:100] if content else "",
                    "changed": changed,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"ClipboardMonitorNode error: {e}")
            self.set_output_value("content", "")
            self.set_output_value("changed", False)
            self.set_output_value("timed_out", True)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

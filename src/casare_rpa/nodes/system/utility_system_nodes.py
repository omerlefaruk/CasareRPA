"""
Utility system nodes for CasareRPA.

This module provides utility nodes for system-level operations:
- FileWatcherNode: Monitor file/folder for changes
- QRCodeNode: Generate or read QR codes
- Base64Node: Encode/decode base64
- UUIDGeneratorNode: Generate UUIDs
- AssertNode: Validate conditions
- LogToFileNode: Write to custom log file
"""

import asyncio
import base64
import os
import uuid as uuid_module
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
)
from casare_rpa.infrastructure.execution import ExecutionContext


# =============================================================================
# FileWatcherNode - Monitor file/folder for changes
# =============================================================================


@properties(
    PropertyDef(
        "watch_path",
        PropertyType.FILE_PATH,
        required=True,
        label="Path",
        tooltip="File or folder path to monitor",
        essential=True,
    ),
    PropertyDef(
        "events",
        PropertyType.CHOICE,
        default="all",
        choices=["create", "modify", "delete", "all"],
        label="Events",
        tooltip="Type of file system events to monitor",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30,
        min_value=1,
        max_value=3600,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for an event",
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=False,
        label="Recursive",
        tooltip="Monitor subdirectories as well",
    ),
)
@node(category="system")
class FileWatcherNode(BaseNode):
    """
    Monitor a file or folder for changes.

    Uses watchdog library to observe file system events.
    """

    # @category: system
    # @requires: pillow
    # @ports: none -> event_type, file_path, triggered, timed_out

    def __init__(self, node_id: str, name: str = "File Watcher", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FileWatcherNode"

    def _define_ports(self) -> None:
        self.add_output_port("event_type", DataType.STRING)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("triggered", DataType.BOOLEAN)
        self.add_output_port("timed_out", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            watch_path = self.get_parameter("watch_path", "")
            events = self.get_parameter("events", "all")
            timeout = int(self.get_parameter("timeout", 30) or 30)
            recursive = self.get_parameter("recursive", False)

            if not watch_path:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Path is required",
                    "outputs": {
                        "event_type": "",
                        "file_path": "",
                        "triggered": False,
                        "timed_out": False,
                    },
                }

            path = Path(watch_path)
            if not path.exists():
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": f"Path does not exist: {watch_path}",
                    "outputs": {
                        "event_type": "",
                        "file_path": "",
                        "triggered": False,
                        "timed_out": False,
                    },
                }

            try:
                from watchdog.observers import Observer
                from watchdog.events import FileSystemEventHandler
            except ImportError:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "watchdog library not installed. Install with: pip install watchdog",
                    "outputs": {
                        "event_type": "",
                        "file_path": "",
                        "triggered": False,
                        "timed_out": False,
                    },
                }

            event_result: Dict[str, Any] = {
                "event_type": "",
                "file_path": "",
                "triggered": False,
            }
            event_occurred = asyncio.Event()

            class EventHandler(FileSystemEventHandler):
                def __init__(self, target_events: str):
                    super().__init__()
                    self.target_events = target_events

                def _should_handle(self, event_type: str) -> bool:
                    if self.target_events == "all":
                        return True
                    return event_type == self.target_events

                def on_created(self, event):
                    if not event.is_directory and self._should_handle("create"):
                        event_result["event_type"] = "created"
                        event_result["file_path"] = event.src_path
                        event_result["triggered"] = True
                        event_occurred.set()

                def on_modified(self, event):
                    if not event.is_directory and self._should_handle("modify"):
                        event_result["event_type"] = "modified"
                        event_result["file_path"] = event.src_path
                        event_result["triggered"] = True
                        event_occurred.set()

                def on_deleted(self, event):
                    if not event.is_directory and self._should_handle("delete"):
                        event_result["event_type"] = "deleted"
                        event_result["file_path"] = event.src_path
                        event_result["triggered"] = True
                        event_occurred.set()

            handler = EventHandler(events)
            observer = Observer()

            watch_dir = str(path) if path.is_dir() else str(path.parent)
            observer.schedule(handler, watch_dir, recursive=recursive)
            observer.start()

            try:
                await asyncio.wait_for(event_occurred.wait(), timeout=timeout)
                timed_out = False
            except asyncio.TimeoutError:
                timed_out = True
            finally:
                observer.stop()
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: observer.join(timeout=2)
                )

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": {
                    "event_type": event_result["event_type"],
                    "file_path": event_result["file_path"],
                    "triggered": event_result["triggered"],
                    "timed_out": timed_out,
                },
            }

        except Exception as e:
            logger.error(f"FileWatcherNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {
                    "event_type": "",
                    "file_path": "",
                    "triggered": False,
                    "timed_out": False,
                },
            }


# =============================================================================
# QRCodeNode - Generate or read QR codes
# =============================================================================


@properties(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default="generate",
        choices=["generate", "read"],
        label="Action",
        tooltip="Generate a QR code or read from an image",
        essential=True,
    ),
    PropertyDef(
        "data",
        PropertyType.STRING,
        default="",
        label="Data",
        tooltip="Data to encode (for generate action)",
    ),
    PropertyDef(
        "image_path",
        PropertyType.FILE_PATH,
        default="",
        label="Image Path",
        tooltip="Path to QR code image (for read action)",
    ),
    PropertyDef(
        "output_path",
        PropertyType.FILE_PATH,
        default="",
        label="Output Path",
        tooltip="Path to save generated QR code image",
    ),
    PropertyDef(
        "size",
        PropertyType.INTEGER,
        default=200,
        min_value=50,
        max_value=1000,
        label="Size (pixels)",
        tooltip="Size of the generated QR code in pixels",
    ),
)
@node(category="system")
class QRCodeNode(BaseNode):
    """Generate or read QR codes."""

    # @category: system
    # @requires: pillow
    # @ports: data -> result, success

    def __init__(self, node_id: str, name: str = "QR Code", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "QRCodeNode"

    def _define_ports(self) -> None:
        self.add_input_port("data", DataType.STRING)
        self.add_output_port("result", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            action = self.get_parameter("action", "generate")
            size = int(self.get_parameter("size", 200) or 200)

            if action == "generate":
                data = self.get_input_value("data")
                if data is None:
                    data = self.get_parameter("data", "")

                output_path = self.get_parameter("output_path", "")

                if not data:
                    self.status = NodeStatus.ERROR
                    return {
                        "success": False,
                        "error": "Data is required for QR code generation",
                        "outputs": {"result": "", "success": False},
                    }

                if not output_path:
                    output_path = os.path.join(
                        os.getcwd(),
                        f"qrcode_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    )

                try:
                    import qrcode
                except ImportError:
                    self.status = NodeStatus.ERROR
                    return {
                        "success": False,
                        "error": "qrcode library not installed. Install with: pip install qrcode[pil]",
                        "outputs": {"result": "", "success": False},
                    }

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=size // 20,
                    border=4,
                )
                qr.add_data(data)
                qr.make(fit=True)

                img = qr.make_image(fill_color="black", back_color="white")
                img = img.resize((size, size))
                img.save(output_path)

                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "outputs": {"result": output_path, "success": True},
                }

            else:  # read
                image_path = self.get_parameter("image_path", "")

                if not image_path or not os.path.exists(image_path):
                    self.status = NodeStatus.ERROR
                    return {
                        "success": False,
                        "error": f"Image path is required or does not exist: {image_path}",
                        "outputs": {"result": "", "success": False},
                    }

                try:
                    from pyzbar import pyzbar
                    from PIL import Image
                except ImportError:
                    self.status = NodeStatus.ERROR
                    return {
                        "success": False,
                        "error": "pyzbar and Pillow libraries required. Install with: pip install pyzbar Pillow",
                        "outputs": {"result": "", "success": False},
                    }

                img = Image.open(image_path)
                decoded_objects = pyzbar.decode(img)

                if not decoded_objects:
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "outputs": {"result": "", "success": False},
                    }

                result = decoded_objects[0].data.decode("utf-8")
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "outputs": {"result": result, "success": True},
                }

        except Exception as e:
            logger.error(f"QRCodeNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"result": "", "success": False},
            }


# =============================================================================
# Base64Node - Encode/decode base64
# =============================================================================


@properties(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default="encode",
        choices=["encode", "decode"],
        label="Action",
        tooltip="Encode to base64 or decode from base64",
        essential=True,
    ),
    PropertyDef(
        "input_text",
        PropertyType.TEXT,
        default="",
        label="Input",
        tooltip="Text to encode or base64 string to decode",
        essential=True,
    ),
)
@node(category="system")
class Base64Node(BaseNode):
    """Encode or decode base64 strings."""

    # @category: system
    # @requires: pillow
    # @ports: input_text -> output, success

    def __init__(self, node_id: str, name: str = "Base64", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "Base64Node"

    def _define_ports(self) -> None:
        self.add_input_port("input_text", DataType.STRING)
        self.add_output_port("output", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            action = self.get_parameter("action", "encode")

            input_text = self.get_input_value("input_text")
            if input_text is None:
                input_text = self.get_parameter("input_text", "")

            if not input_text:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Input text is required",
                    "outputs": {"output": "", "success": False},
                }

            if action == "encode":
                result = base64.b64encode(input_text.encode("utf-8")).decode("utf-8")
            else:  # decode
                try:
                    result = base64.b64decode(input_text.encode("utf-8")).decode("utf-8")
                except Exception as decode_error:
                    self.status = NodeStatus.ERROR
                    return {
                        "success": False,
                        "error": f"Invalid base64 string: {decode_error}",
                        "outputs": {"output": "", "success": False},
                    }

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": {"output": result, "success": True},
            }

        except Exception as e:
            logger.error(f"Base64Node error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"output": "", "success": False},
            }


# =============================================================================
# UUIDGeneratorNode - Generate UUIDs
# =============================================================================


@properties(
    PropertyDef(
        "uuid_version",
        PropertyType.CHOICE,
        default="4",
        choices=["1", "4"],
        label="Version",
        tooltip="UUID version (1=time-based, 4=random)",
    ),
    PropertyDef(
        "count",
        PropertyType.INTEGER,
        default=1,
        min_value=1,
        max_value=100,
        label="Count",
        tooltip="Number of UUIDs to generate",
    ),
)
@node(category="system")
class UUIDGeneratorNode(BaseNode):
    """Generate UUIDs."""

    # @category: system
    # @requires: pillow
    # @ports: none -> uuid, uuids, success

    def __init__(self, node_id: str, name: str = "UUID Generator", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "UUIDGeneratorNode"

    def _define_ports(self) -> None:
        self.add_output_port("uuid", DataType.STRING)
        self.add_output_port("uuids", DataType.LIST)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            version = self.get_parameter("uuid_version", "4")
            count = int(self.get_parameter("count", 1) or 1)
            count = max(1, min(count, 100))

            uuids: List[str] = []
            for _ in range(count):
                if version == "1":
                    new_uuid = str(uuid_module.uuid1())
                else:
                    new_uuid = str(uuid_module.uuid4())
                uuids.append(new_uuid)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": {
                    "uuid": uuids[0] if uuids else "",
                    "uuids": uuids,
                    "success": True,
                },
            }

        except Exception as e:
            logger.error(f"UUIDGeneratorNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"uuid": "", "uuids": [], "success": False},
            }


# =============================================================================
# AssertSystemNode - Validate conditions
# =============================================================================


@properties(
    PropertyDef(
        "condition",
        PropertyType.STRING,
        required=True,
        label="Condition",
        tooltip="Expression to evaluate (supports {{var}}, operators like >, <, ==)",
        essential=True,
    ),
    PropertyDef(
        "value",
        PropertyType.ANY,
        required=False,
        label="Value",
        tooltip="Value to compare in condition",
    ),
    PropertyDef(
        "assert_message",
        PropertyType.STRING,
        default="Assertion failed",
        label="Message",
        tooltip="Message to show if assertion fails",
    ),
    PropertyDef(
        "fail_on_false",
        PropertyType.BOOLEAN,
        default=True,
        label="Fail on False",
        tooltip="If true, node fails when condition is false; if false, just outputs result",
    ),
)
@node(category="system")
class AssertSystemNode(BaseNode):
    """Validate conditions and optionally fail the workflow."""

    # @category: system
    # @requires: pillow
    # @ports: condition, value -> passed, message

    def __init__(self, node_id: str, name: str = "Assert", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "AssertSystemNode"

    def _define_ports(self) -> None:
        self.add_input_port("condition", DataType.ANY)
        self.add_input_port("value", DataType.ANY)
        self.add_output_port("passed", DataType.BOOLEAN)
        self.add_output_port("message", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            condition_expr = self.get_parameter("condition", "")
            message = self.get_parameter("assert_message", "Assertion failed")
            fail_on_false = self.get_parameter("fail_on_false", True)

            condition_input = self.get_input_value("condition")
            value_input = self.get_input_value("value")

            if not condition_expr and condition_input is not None:
                passed = bool(condition_input)
            elif condition_expr:
                passed = self._evaluate_condition(condition_expr, condition_input, value_input)
            else:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Condition is required",
                    "outputs": {"passed": False, "message": "Condition is required"},
                }

            if passed:
                result_message = "Assertion passed"
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "outputs": {"passed": True, "message": result_message},
                }
            else:
                result_message = message
                if fail_on_false:
                    self.status = NodeStatus.ERROR
                    return {
                        "success": False,
                        "error": result_message,
                        "outputs": {"passed": False, "message": result_message},
                    }
                else:
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "outputs": {"passed": False, "message": result_message},
                    }

        except Exception as e:
            logger.error(f"AssertSystemNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"passed": False, "message": str(e)},
            }

    def _evaluate_condition(
        self,
        condition: str,
        condition_input: Any,
        value_input: Any,
    ) -> bool:
        """Safely evaluate a condition expression."""
        if condition.lower() in ("true", "false"):
            return condition.lower() == "true"

        operators = [">=", "<=", "!=", "==", ">", "<"]
        for op in operators:
            if op in condition:
                parts = condition.split(op, 1)
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()

                    try:
                        left_val = float(left)
                    except ValueError:
                        left_val = left

                    try:
                        right_val = float(right)
                    except ValueError:
                        right_val = right

                    if op == ">=":
                        return left_val >= right_val
                    elif op == "<=":
                        return left_val <= right_val
                    elif op == "!=":
                        return left_val != right_val
                    elif op == "==":
                        return left_val == right_val
                    elif op == ">":
                        return left_val > right_val
                    elif op == "<":
                        return left_val < right_val

        # Truthy check (no eval for security)
        return bool(condition and condition.lower() not in ("false", "0", "none", "null", ""))


# =============================================================================
# LogToFileNode - Write to custom log file
# =============================================================================


@properties(
    PropertyDef(
        "log_file_path",
        PropertyType.FILE_PATH,
        required=True,
        label="File Path",
        tooltip="Path to the log file",
        essential=True,
    ),
    PropertyDef(
        "log_message",
        PropertyType.TEXT,
        required=True,
        label="Message",
        tooltip="Message to write to the log",
        essential=True,
    ),
    PropertyDef(
        "level",
        PropertyType.CHOICE,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        label="Level",
        tooltip="Log level",
    ),
    PropertyDef(
        "append",
        PropertyType.BOOLEAN,
        default=True,
        label="Append",
        tooltip="Append to file or overwrite",
    ),
    PropertyDef(
        "add_timestamp",
        PropertyType.BOOLEAN,
        default=True,
        label="Timestamp",
        tooltip="Add timestamp to log entries",
    ),
)
@node(category="system")
class LogToFileNode(BaseNode):
    """Write messages to a custom log file."""

    # @category: system
    # @requires: pillow
    # @ports: log_message -> success, lines_written

    def __init__(self, node_id: str, name: str = "Log to File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LogToFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("log_message", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("lines_written", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("log_file_path", "")
            level = self.get_parameter("level", "INFO")
            append = self.get_parameter("append", True)
            add_timestamp = self.get_parameter("add_timestamp", True)

            message = self.get_input_value("log_message")
            if message is None:
                message = self.get_parameter("log_message", "")
            # Resolve variables first, THEN convert to string (resolve preserves types for {{var}} patterns)
            message = str(context.resolve_value(message) or "")
            file_path = str(context.resolve_value(file_path) or "")

            if not file_path:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "File path is required",
                    "outputs": {"success": False, "lines_written": 0},
                }

            if not message:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Message is required",
                    "outputs": {"success": False, "lines_written": 0},
                }

            lines: List[str] = []
            for line in message.split("\n"):
                if add_timestamp:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_line = f"[{timestamp}] [{level}] {line}"
                else:
                    log_line = f"[{level}] {line}"
                lines.append(log_line)

            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            mode = "a" if append else "w"
            with open(file_path, mode, encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": {"success": True, "lines_written": len(lines)},
            }

        except Exception as e:
            logger.error(f"LogToFileNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"success": False, "lines_written": 0},
            }

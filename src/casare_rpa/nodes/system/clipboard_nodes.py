"""
Clipboard operation nodes for CasareRPA.

This module provides nodes for clipboard operations:
- Copy text to clipboard
- Paste text from clipboard
- Clear clipboard
"""

import sys

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


from casare_rpa.domain.schemas import PropertyDef, PropertyType


@properties(
    PropertyDef(
        "text",
        PropertyType.TEXT,
        required=True,
        label="Text",
        tooltip="Text to copy to clipboard",
    ),
)
@node(category="system")
class ClipboardCopyNode(BaseNode):
    """
    Copy text to the clipboard.

    Inputs:
        text: Text to copy to clipboard

    Outputs:
        success: Whether operation succeeded
    """

    # @category: system
    # @requires: none
    # @ports: text -> success

    def __init__(self, node_id: str, name: str = "Clipboard Copy", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardCopyNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")

            # Use pyperclip if available, otherwise fall back to platform-specific
            try:
                import pyperclip

                pyperclip.copy(text)
            except ImportError:
                # Fallback for Windows
                if sys.platform == "win32":
                    import ctypes

                    CF_UNICODETEXT = 13
                    GMEM_MOVEABLE = 0x0002

                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32

                    user32.OpenClipboard(0)
                    user32.EmptyClipboard()

                    if text:
                        data = text.encode("utf-16-le") + b"\x00\x00"
                        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                        mem_ptr = kernel32.GlobalLock(h_mem)
                        ctypes.memmove(mem_ptr, data, len(data))
                        kernel32.GlobalUnlock(h_mem)
                        user32.SetClipboardData(CF_UNICODETEXT, h_mem)

                    user32.CloseClipboard()
                else:
                    raise RuntimeError("pyperclip not installed and no native clipboard support")

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"copied_length": len(text)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties()  # No config - output only
@node(category="system")
class ClipboardPasteNode(BaseNode):
    """
    Get text from the clipboard.

    Outputs:
        text: Text from clipboard
        success: Whether operation succeeded
    """

    # @category: system
    # @requires: none
    # @ports: none -> text, success

    def __init__(self, node_id: str, name: str = "Clipboard Paste", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardPasteNode"

    def _define_ports(self) -> None:
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = ""

            # Use pyperclip if available
            try:
                import pyperclip

                text = pyperclip.paste()
            except ImportError:
                # Fallback for Windows
                if sys.platform == "win32":
                    import ctypes

                    CF_UNICODETEXT = 13
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32

                    user32.OpenClipboard(0)
                    try:
                        h_data = user32.GetClipboardData(CF_UNICODETEXT)
                        if h_data:
                            mem_ptr = kernel32.GlobalLock(h_data)
                            if mem_ptr:
                                text = ctypes.wstring_at(mem_ptr)
                                kernel32.GlobalUnlock(h_data)
                    finally:
                        user32.CloseClipboard()
                else:
                    raise RuntimeError("pyperclip not installed and no native clipboard support")

            self.set_output_value("text", text)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"text_length": len(text)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("text", "")
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties()  # No config
@node(category="system")
class ClipboardClearNode(BaseNode):
    """
    Clear the clipboard.

    Outputs:
        success: Whether operation succeeded
    """

    # @category: system
    # @requires: none
    # @ports: none -> success

    def __init__(self, node_id: str, name: str = "Clipboard Clear", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardClearNode"

    def _define_ports(self) -> None:
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            try:
                import pyperclip

                pyperclip.copy("")
            except ImportError:
                if sys.platform == "win32":
                    import ctypes

                    user32 = ctypes.windll.user32
                    user32.OpenClipboard(0)
                    user32.EmptyClipboard()
                    user32.CloseClipboard()
                else:
                    raise RuntimeError("pyperclip not installed and no native clipboard support")

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

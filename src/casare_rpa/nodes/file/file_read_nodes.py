"""
File read operation nodes for CasareRPA.

This module provides nodes for reading file content:
- ReadFileNode: Read text or binary content from files

SECURITY: All file operations are subject to path sandboxing.
NOTE: File I/O uses AsyncFileOperations for non-blocking operations.
"""

import os

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
)
from casare_rpa.utils.async_file_ops import AsyncFileOperations


@properties(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        tooltip="Path to the file to read",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="Text encoding (utf-8, ascii, latin-1, etc.)",
    ),
    PropertyDef(
        "binary_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Binary Mode",
        tooltip="Read as binary data (returns bytes instead of string)",
    ),
    PropertyDef(
        "errors",
        PropertyType.CHOICE,
        default="strict",
        choices=[
            "strict",
            "ignore",
            "replace",
            "backslashreplace",
            "xmlcharrefreplace",
        ],
        label="Error Handling",
        tooltip="How to handle encoding errors",
    ),
    PropertyDef(
        "max_size",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Max Size (bytes)",
        tooltip="Maximum file size to read (0 = unlimited)",
    ),
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories",
    ),
)
@node(category="file")
class ReadFileNode(BaseNode):
    """
    Read content from a text or binary file.

    Config (via @properties):
        file_path: Path to the file to read (required)
        encoding: Text encoding (default: utf-8)
        binary_mode: Read as binary (default: False)
        errors: Error handling mode (default: strict)
        max_size: Maximum file size in bytes (0 = unlimited)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)

    Outputs:
        content: File contents (string or bytes)
        size: File size in bytes
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path -> content, size, success

    def __init__(self, node_id: str, name: str = "Read File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_output_port("content", DataType.STRING)
        self.add_output_port("size", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("file_path")
            encoding = self.get_parameter("encoding", "utf-8")
            binary_mode = self.get_parameter("binary_mode", False)
            errors = self.get_parameter("errors", "strict")
            max_size = self.get_parameter("max_size", 0)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before any operation
            path = validate_path_security(file_path, "read", allow_dangerous)

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check file size against max_size limit
            size = path.stat().st_size
            if max_size > 0 and size > max_size:
                raise ValueError(
                    f"File size ({size} bytes) exceeds max_size limit ({max_size} bytes)"
                )

            logger.info(f"Reading file: {path} (binary={binary_mode}, encoding={encoding})")

            # Use async file operations for non-blocking I/O
            if binary_mode:
                content = await AsyncFileOperations.read_binary(path)
            else:
                content = await AsyncFileOperations.read_text(path, encoding, errors)

            self.set_output_value("content", content)
            self.set_output_value("size", size)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "content": content[:100] + "..." if len(str(content)) > 100 else content,
                    "size": size,
                },
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in ReadFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

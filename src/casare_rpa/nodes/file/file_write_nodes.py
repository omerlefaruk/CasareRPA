"""
File write operation nodes for CasareRPA.

This module provides nodes for writing file content:
- WriteFileNode: Write or overwrite file content
- AppendFileNode: Append content to existing files

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
        tooltip="Path to write to",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "content",
        PropertyType.STRING,
        required=True,
        label="Content",
        tooltip="Content to write to file",
    ),
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="Text encoding",
    ),
    PropertyDef(
        "binary_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Binary Mode",
        tooltip="Write as binary data",
    ),
    PropertyDef(
        "create_dirs",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Directories",
        tooltip="Create parent directories if needed",
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
        "append_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Append Mode",
        tooltip="Append to file instead of overwrite",
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
class WriteFileNode(BaseNode):
    """
    Write content to a file, creating or overwriting.

    Config (via @properties):
        file_path: Path to write to (required)
        content: Content to write (required)
        encoding: Text encoding (default: utf-8)
        binary_mode: Write as binary (default: False)
        create_dirs: Create parent directories (default: True)
        errors: Error handling mode (default: strict)
        append_mode: Append instead of overwrite (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)
        content: Content override (if connected)

    Outputs:
        file_path: Path that was written
        bytes_written: Number of bytes written
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path, content -> file_path, attachment_file, bytes_written, success

    def __init__(self, node_id: str, name: str = "Write File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_input_port("content", DataType.STRING)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("attachment_file", DataType.LIST)
        self.add_output_port("bytes_written", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("file_path")
            content = self.get_parameter("content")
            encoding = self.get_parameter("encoding", "utf-8")
            binary_mode = self.get_parameter("binary_mode", False)
            create_dirs = self.get_parameter("create_dirs", True)
            errors = self.get_parameter("errors", "strict")
            append_mode = self.get_parameter("append_mode", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path and content
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before any operation
            path = validate_path_security(file_path, "write", allow_dangerous)

            if create_dirs and path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Determine file mode based on binary and append settings
            if binary_mode:
                mode = "ab" if append_mode else "wb"
            else:
                mode = "a" if append_mode else "w"

            logger.info(f"Writing file: {path} (mode={mode}, encoding={encoding})")

            # Use async file operations for non-blocking I/O
            if binary_mode:
                # Prepare content for binary writing
                if isinstance(content, str):
                    content = content.encode(encoding)
                if append_mode:
                    # For binary append, read existing content first
                    existing = b""
                    if path.exists():
                        existing = await AsyncFileOperations.read_binary(path)
                    bytes_written = await AsyncFileOperations.write_binary(
                        path, existing + content, create_dirs=create_dirs
                    )
                else:
                    bytes_written = await AsyncFileOperations.write_binary(
                        path, content, create_dirs=create_dirs
                    )
            else:
                # Text mode
                text_content = str(content) if content else ""
                if append_mode:
                    bytes_written = await AsyncFileOperations.append_text(
                        path, text_content, encoding, errors, create_dirs=create_dirs
                    )
                else:
                    bytes_written = await AsyncFileOperations.write_text(
                        path, text_content, encoding, errors, create_dirs=create_dirs
                    )

            self.set_output_value("file_path", str(path))
            self.set_output_value("attachment_file", [str(path)])
            self.set_output_value("bytes_written", bytes_written)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path), "bytes_written": bytes_written},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in WriteFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        tooltip="Path to append to",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "content",
        PropertyType.STRING,
        required=True,
        label="Content",
        tooltip="Content to append to file",
    ),
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="Text encoding",
    ),
    PropertyDef(
        "create_if_missing",
        PropertyType.BOOLEAN,
        default=True,
        label="Create If Missing",
        tooltip="Create file if it doesn't exist",
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
class AppendFileNode(BaseNode):
    """
    Append content to an existing file.

    Config (via @properties):
        file_path: Path to append to (required)
        content: Content to append (required)
        encoding: Text encoding (default: utf-8)
        create_if_missing: Create file if it doesn't exist (default: True)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)
        content: Content override (if connected)

    Outputs:
        file_path: Path that was written
        bytes_written: Number of bytes appended
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path, content -> file_path, bytes_written, success

    def __init__(self, node_id: str, name: str = "Append File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "AppendFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_input_port("content", DataType.STRING)
        self.add_output_port("file_path", DataType.STRING)
        self.add_output_port("bytes_written", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("file_path")
            content = self.get_parameter("content")
            encoding = self.get_parameter("encoding", "utf-8")
            create_if_missing = self.get_parameter("create_if_missing", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path and content
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before any operation
            path = validate_path_security(file_path, "append", allow_dangerous)

            if not path.exists() and not create_if_missing:
                raise FileNotFoundError(f"File not found: {file_path}")

            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Use async file operations for non-blocking I/O
            text_content = str(content) if content else ""
            bytes_written = await AsyncFileOperations.append_text(
                path, text_content, encoding, "replace", create_dirs=True
            )

            self.set_output_value("file_path", str(path))
            self.set_output_value("bytes_written", bytes_written)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path), "bytes_written": bytes_written},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in AppendFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

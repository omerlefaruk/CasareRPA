"""
Path information nodes for CasareRPA.

This module provides nodes for path and file information:
- FileExistsNode: Check if a file or directory exists
- GetFileSizeNode: Get file size in bytes
- GetFileInfoNode: Get detailed file information

SECURITY: All file operations are subject to path sandboxing.
"""

import os
from datetime import datetime

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.file.file_security import validate_path_security_readonly


@properties(
    PropertyDef(
        "path",
        PropertyType.STRING,
        required=True,
        label="Path",
        tooltip="File or directory path to check",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "check_type",
        PropertyType.CHOICE,
        default="any",
        choices=["file", "directory", "any"],
        label="Check Type",
        tooltip="Type of path to check: file only, directory only, or any",
    ),
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories (use with caution)",
    ),
)
@node(category="file")
class FileExistsNode(BaseNode):
    """
    Check if a file or directory exists.

    Config (via @properties):
        path: Path to check (required)
        check_type: "file", "directory", or "any" (default: any)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        path: Path to check (overrides config if connected)

    Outputs:
        exists: Whether the path exists
        is_file: Whether it's a file
        is_dir: Whether it's a directory
    """

    # @category: file
    # @requires: none
    # @ports: path -> exists, is_file, is_dir

    def __init__(self, node_id: str, name: str = "File Exists", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FileExistsNode"

    def _define_ports(self) -> None:
        self.add_input_port("path", DataType.STRING)
        self.add_output_port("exists", DataType.BOOLEAN)
        self.add_output_port("is_file", DataType.BOOLEAN)
        self.add_output_port("is_dir", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("path")
            check_type = self.get_parameter("check_type", "any")

            if not file_path:
                raise ValueError("path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = context.resolve_value(file_path)
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path (read-only, allows system paths)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)
            path = validate_path_security_readonly(file_path, "check", allow_dangerous)
            exists = path.exists()
            is_file = path.is_file() if exists else False
            is_directory = path.is_dir() if exists else False

            # Apply type filter
            if check_type == "file":
                exists = is_file
            elif check_type == "directory":
                exists = is_directory

            self.set_output_value("exists", exists)
            self.set_output_value("is_file", is_file)
            self.set_output_value("is_dir", is_directory)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "exists": exists,
                    "is_file": is_file,
                    "is_dir": is_directory,
                },
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e)}

    def _validate_config(self) -> tuple[bool, str]:
        check_type = self.get_parameter("check_type", "any")
        if check_type not in ["file", "directory", "any"]:
            return False, "check_type must be 'file', 'directory', or 'any'"
        return True, ""


@properties(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        tooltip="Path to the file to check size",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories (use with caution)",
    ),
)
@node(category="file")
class GetFileSizeNode(BaseNode):
    """
    Get the size of a file in bytes.

    Config (via @properties):
        file_path: Path to the file (required)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)

    Outputs:
        size: File size in bytes
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path -> size, success

    def __init__(self, node_id: str, name: str = "Get File Size", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetFileSizeNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_output_port("size", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("file_path")
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = context.resolve_value(file_path)
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path (read-only)
            path = validate_path_security_readonly(file_path, "stat", allow_dangerous)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            size = path.stat().st_size

            self.set_output_value("size", size)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {"size": size}}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e)}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        tooltip="Path to the file to get information about",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories (use with caution)",
    ),
)
@node(category="file")
class GetFileInfoNode(BaseNode):
    """
    Get detailed information about a file.

    Config (via @properties):
        file_path: Path to the file (required)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)

    Outputs:
        size: File size in bytes
        created: Creation timestamp
        modified: Last modified timestamp
        extension: File extension
        name: File name without path
        parent: Parent directory
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path -> size, created, modified, extension, name, parent, success

    def __init__(self, node_id: str, name: str = "Get File Info", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetFileInfoNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_output_port("size", DataType.INTEGER)
        self.add_output_port("created", DataType.STRING)
        self.add_output_port("modified", DataType.STRING)
        self.add_output_port("extension", DataType.STRING)
        self.add_output_port("name", DataType.STRING)
        self.add_output_port("parent", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("file_path")
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = context.resolve_value(file_path)
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path (read-only)
            path = validate_path_security_readonly(file_path, "stat", allow_dangerous)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            stat = path.stat()

            self.set_output_value("size", stat.st_size)
            self.set_output_value(
                "created", datetime.fromtimestamp(stat.st_ctime).isoformat()
            )
            self.set_output_value(
                "modified", datetime.fromtimestamp(stat.st_mtime).isoformat()
            )
            self.set_output_value("extension", path.suffix)
            self.set_output_value("name", path.name)
            self.set_output_value("parent", str(path.parent))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "name": path.name,
                    "size": stat.st_size,
                    "extension": path.suffix,
                },
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e)}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

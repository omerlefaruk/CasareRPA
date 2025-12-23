"""
Directory operation nodes for CasareRPA.

This module provides nodes for directory operations:
- CreateDirectoryNode: Create directories
- ListFilesNode: List files in a directory
- ListDirectoryNode: List files and directories

SECURITY: All file operations are subject to path sandboxing.
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
    validate_path_security_readonly,
)


@properties(
    PropertyDef(
        "directory_path",
        PropertyType.STRING,
        required=True,
        label="Directory Path",
        tooltip="Path to create",
        placeholder="C:\\path\\to\\directory",
    ),
    PropertyDef(
        "parents",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Parents",
        tooltip="Create parent directories as needed",
    ),
    PropertyDef(
        "exist_ok",
        PropertyType.BOOLEAN,
        default=True,
        label="Exist OK",
        tooltip="Don't error if directory already exists",
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
class CreateDirectoryNode(BaseNode):
    """
    Create a directory.

    Config (via @properties):
        directory_path: Path to create (required)
        parents: Create parent directories (default: True)
        exist_ok: Don't error if exists (default: True)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        directory_path: Path override (if connected)

    Outputs:
        dir_path: Created directory path
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: directory_path -> dir_path, success

    def __init__(self, node_id: str, name: str = "Create Directory", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateDirectoryNode"

    def _define_ports(self) -> None:
        self.add_input_port("directory_path", DataType.STRING)
        self.add_output_port("dir_path", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.get_parameter("directory_path")
            parents = self.get_parameter("parents", True)
            exist_ok = self.get_parameter("exist_ok", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not dir_path:
                raise ValueError("directory_path is required")

            # Resolve {{variable}} patterns and environment variables in dir_path
            dir_path = os.path.expandvars(dir_path)

            # SECURITY: Validate path before directory creation
            path = validate_path_security(dir_path, "mkdir", allow_dangerous)
            path.mkdir(parents=parents, exist_ok=exist_ok)

            self.set_output_value("dir_path", str(path))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"dir_path": str(path)},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in CreateDirectoryNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "directory_path",
        PropertyType.STRING,
        default="",
        label="Directory Path",
        tooltip="Directory to list files from (required at runtime)",
        placeholder="C:\\path\\to\\directory",
    ),
    PropertyDef(
        "pattern",
        PropertyType.STRING,
        default="*",
        label="Pattern",
        tooltip="Glob pattern to filter files (e.g., *.txt, *.py)",
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=False,
        label="Recursive",
        tooltip="Search subdirectories recursively",
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
class ListFilesNode(BaseNode):
    """
    List files in a directory.

    Config (via @properties):
        directory_path: Directory to list (required)
        pattern: Glob pattern to filter (default: *)
        recursive: Search recursively (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        directory_path: Directory override (if connected)

    Outputs:
        files: List of file paths
        count: Number of files found
    """

    # @category: file
    # @requires: none
    # @ports: directory_path -> files, count, success

    def __init__(self, node_id: str, name: str = "List Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("directory_path", DataType.STRING)
        self.add_output_port("files", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.get_parameter("directory_path")
            pattern = self.get_parameter("pattern", "*")
            recursive = self.get_parameter("recursive", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not dir_path:
                raise ValueError("directory_path is required")

            # Resolve {{variable}} patterns and environment variables in dir_path and pattern
            dir_path = os.path.expandvars(dir_path)

            # SECURITY: Validate directory path (read-only)
            path = validate_path_security_readonly(dir_path, "list", allow_dangerous)
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")

            if not path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")

            if recursive:
                matches = list(path.rglob(pattern))
            else:
                matches = list(path.glob(pattern))

            # Filter to only files (not directories)
            files = [str(item) for item in matches if item.is_file()]

            self.set_output_value("files", files)
            self.set_output_value("count", len(files))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(files), "files": files[:10]},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("success", False)
            logger.error(f"Security violation in ListFilesNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("success", False)
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "dir_path",
        PropertyType.STRING,
        required=True,
        label="Directory Path",
        tooltip="Path to the directory to list",
        placeholder="C:\\path\\to\\directory",
    ),
    PropertyDef(
        "pattern",
        PropertyType.STRING,
        default="*",
        label="Pattern",
        tooltip="Glob pattern to filter results (e.g., *.txt, *.pdf)",
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=False,
        label="Recursive",
        tooltip="Search subdirectories recursively",
    ),
    PropertyDef(
        "files_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Files Only",
        tooltip="Only return files (exclude directories)",
    ),
    PropertyDef(
        "dirs_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Directories Only",
        tooltip="Only return directories (exclude files)",
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
class ListDirectoryNode(BaseNode):
    """
    List files and directories in a folder.

    Config (via @properties):
        dir_path: Path to the directory to list (required)
        pattern: Glob pattern to filter (default: *)
        recursive: Search recursively (default: False)
        files_only: Only return files (default: False)
        dirs_only: Only return directories (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        dir_path: Directory path override (if connected)

    Outputs:
        items: List of file/directory paths
        count: Number of items found
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: dir_path -> items, count, success

    def __init__(self, node_id: str, name: str = "List Directory", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListDirectoryNode"

    def _define_ports(self) -> None:
        self.add_input_port("dir_path", DataType.STRING)
        self.add_output_port("items", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.get_parameter("dir_path")
            pattern = self.get_parameter("pattern", "*")
            recursive = self.get_parameter("recursive", False)
            files_only = self.get_parameter("files_only", False)
            dirs_only = self.get_parameter("dirs_only", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not dir_path:
                raise ValueError("dir_path is required")

            # Resolve {{variable}} patterns and environment variables in dir_path and pattern
            dir_path = os.path.expandvars(dir_path)

            # SECURITY: Validate directory path (read-only)
            path = validate_path_security_readonly(dir_path, "list", allow_dangerous)
            if not path.exists():
                raise FileNotFoundError(f"Directory not found: {dir_path}")

            if not path.is_dir():
                raise NotADirectoryError(f"Not a directory: {dir_path}")

            if recursive:
                matches = list(path.rglob(pattern))
            else:
                matches = list(path.glob(pattern))

            items = []
            for item in matches:
                if files_only and not item.is_file():
                    continue
                if dirs_only and not item.is_dir():
                    continue
                items.append(str(item))

            self.set_output_value("items", items)
            self.set_output_value("count", len(items))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(items), "items": items[:10]},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in ListDirectoryNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

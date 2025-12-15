"""
File system operation nodes for CasareRPA.

This module provides nodes for file system operations:
- DeleteFileNode: Delete files
- CopyFileNode: Copy files to new locations
- MoveFileNode: Move or rename files

SECURITY: All file operations are subject to path sandboxing.
"""

import os
import shutil

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
)


@properties(
    PropertyDef(
        "file_path",
        PropertyType.STRING,
        required=True,
        label="File Path",
        tooltip="Path to delete",
        placeholder="C:\\path\\to\\file.txt",
    ),
    PropertyDef(
        "ignore_missing",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Missing",
        tooltip="Don't error if file doesn't exist",
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
class DeleteFileNode(BaseNode):
    """
    Delete a file.

    Config (via @properties):
        file_path: Path to delete (required)
        ignore_missing: Don't error if file doesn't exist (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)

    Outputs:
        deleted_path: Path that was deleted
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: file_path -> deleted_path, success

    def __init__(self, node_id: str, name: str = "Delete File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DeleteFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING)
        self.add_output_port("deleted_path", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_parameter("file_path")
            ignore_missing = self.get_parameter("ignore_missing", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns and environment variables in file_path
            file_path = context.resolve_value(file_path)
            file_path = os.path.expandvars(file_path)

            # SECURITY: Validate path before delete operation
            path = validate_path_security(file_path, "delete", allow_dangerous)

            if not path.exists():
                if ignore_missing:
                    self.set_output_value("deleted_path", str(path))
                    self.set_output_value("success", True)
                    self.status = NodeStatus.SUCCESS
                    return {
                        "success": True,
                        "data": {
                            "deleted_path": str(path),
                            "message": "File did not exist",
                        },
                        "next_nodes": ["exec_out"],
                    }
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")

            # SECURITY: Log deletion for audit
            logger.warning(f"Deleting file: {path}")
            path.unlink()

            self.set_output_value("deleted_path", str(path))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"deleted_path": str(path)},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in DeleteFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "source_path",
        PropertyType.STRING,
        required=True,
        label="Source Path",
        tooltip="Path to the file to copy",
        placeholder="C:\\path\\to\\source.txt",
    ),
    PropertyDef(
        "dest_path",
        PropertyType.STRING,
        required=True,
        label="Destination Path",
        tooltip="Path to copy the file to",
        placeholder="C:\\path\\to\\destination.txt",
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite",
        tooltip="Overwrite if destination exists",
    ),
    PropertyDef(
        "create_dirs",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Directories",
        tooltip="Create destination directories if needed",
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
class CopyFileNode(BaseNode):
    """
    Copy a file to a new location.

    Config (via @properties):
        source_path: Source file path (required)
        dest_path: Destination file path (required)
        overwrite: Overwrite if destination exists (default: False)
        create_dirs: Create destination directories (default: True)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        source_path: Source path override (if connected)
        dest_path: Destination path override (if connected)

    Outputs:
        dest_path: Destination path
        bytes_copied: Size of copied file
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: source_path, dest_path -> dest_path, bytes_copied, success

    def __init__(self, node_id: str, name: str = "Copy File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CopyFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("source_path", DataType.STRING)
        self.add_input_port("dest_path", DataType.STRING)
        self.add_output_port("dest_path", DataType.STRING)
        self.add_output_port("bytes_copied", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            source_path = self.get_parameter("source_path")
            dest_path = self.get_parameter("dest_path")
            overwrite = self.get_parameter("overwrite", False)
            create_dirs = self.get_parameter("create_dirs", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not source_path or not dest_path:
                raise ValueError("source_path and dest_path are required")

            # Resolve {{variable}} patterns and environment variables in paths
            source_path = context.resolve_value(source_path)
            source_path = os.path.expandvars(source_path)
            dest_path = context.resolve_value(dest_path)
            dest_path = os.path.expandvars(dest_path)

            # SECURITY: Validate paths before any operation
            source = validate_path_security(source_path, "read", allow_dangerous)
            dest = validate_path_security(dest_path, "write", allow_dangerous)

            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            if dest.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {dest_path}")

            if create_dirs and dest.parent:
                dest.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Copying file: {source} -> {dest}")
            shutil.copy2(source, dest)
            bytes_copied = dest.stat().st_size

            self.set_output_value("dest_path", str(dest))
            self.set_output_value("bytes_copied", bytes_copied)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"dest_path": str(dest), "bytes_copied": bytes_copied},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in CopyFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@properties(
    PropertyDef(
        "source_path",
        PropertyType.STRING,
        required=True,
        label="Source Path",
        tooltip="Path to the file to move",
        placeholder="C:\\path\\to\\source.txt",
    ),
    PropertyDef(
        "dest_path",
        PropertyType.STRING,
        required=True,
        label="Destination Path",
        tooltip="Path to move the file to",
        placeholder="C:\\path\\to\\destination.txt",
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite",
        tooltip="Overwrite if destination exists",
    ),
    PropertyDef(
        "create_dirs",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Directories",
        tooltip="Create destination directories if needed",
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
class MoveFileNode(BaseNode):
    """
    Move or rename a file.

    Config (via @properties):
        source_path: Source file path (required)
        dest_path: Destination file path (required)
        overwrite: Overwrite if destination exists (default: False)
        create_dirs: Create destination directories (default: True)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        source_path: Source path override (if connected)
        dest_path: Destination path override (if connected)

    Outputs:
        dest_path: Final destination path
        success: Whether operation succeeded
    """

    # @category: file
    # @requires: none
    # @ports: source_path, dest_path -> dest_path, success

    def __init__(self, node_id: str, name: str = "Move File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MoveFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("source_path", DataType.STRING)
        self.add_input_port("dest_path", DataType.STRING)
        self.add_output_port("dest_path", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            source_path = self.get_parameter("source_path")
            dest_path = self.get_parameter("dest_path")
            overwrite = self.get_parameter("overwrite", False)
            create_dirs = self.get_parameter("create_dirs", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not source_path or not dest_path:
                raise ValueError("source_path and dest_path are required")

            # Resolve {{variable}} patterns and environment variables in paths
            source_path = context.resolve_value(source_path)
            source_path = os.path.expandvars(source_path)
            dest_path = context.resolve_value(dest_path)
            dest_path = os.path.expandvars(dest_path)

            # SECURITY: Validate paths before any operation
            source = validate_path_security(source_path, "read", allow_dangerous)
            dest = validate_path_security(dest_path, "write", allow_dangerous)

            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            if dest.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {dest_path}")

            if create_dirs and dest.parent:
                dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists() and overwrite:
                dest.unlink()

            logger.info(f"Moving file: {source} -> {dest}")
            shutil.move(str(source), str(dest))

            self.set_output_value("dest_path", str(dest))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"dest_path": str(dest)},
                "next_nodes": ["exec_out"],
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in MoveFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

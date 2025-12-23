"""
Super Nodes for CasareRPA File Operations.

This module provides consolidated "Super Nodes" that replace multiple
atomic nodes with action-based dynamic ports and properties.

FileSystemSuperNode (12 operations):
    - Read File: Read text or binary content from files
    - Write File: Write or overwrite file content
    - Append File: Append content to existing files
    - Delete File: Delete files
    - Copy File: Copy files to new locations
    - Move File: Move or rename files
    - File Exists: Check if file/directory exists
    - Get File Size: Get file size in bytes
    - Get File Info: Get detailed file metadata
    - Create Directory: Create directories
    - List Files: List files matching pattern
    - List Directory: List files and directories

StructuredDataSuperNode (7 operations):
    - Read CSV: Read and parse CSV files
    - Write CSV: Write data to CSV files
    - Read JSON: Read and parse JSON files
    - Write JSON: Write data to JSON files
    - Zip: Create ZIP archives
    - Unzip: Extract ZIP archives
    - Image Convert: Convert images between formats

SECURITY: All operations are subject to path sandboxing.
"""

import asyncio
import glob as glob_module
import os
import shutil
import zipfile
from collections.abc import Awaitable, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Dict

from loguru import logger
from PIL import Image, ImageOps

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.dynamic_port_config import (
    ActionPortConfig,
    DynamicPortSchema,
    PortDef,
)
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
    validate_path_security_readonly,
)
from casare_rpa.utils.async_file_ops import AsyncFileOperations

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces import IExecutionContext


class FileSystemAction(str, Enum):
    """Actions available in FileSystemSuperNode."""

    READ = "Read File"
    WRITE = "Write File"
    APPEND = "Append File"
    DELETE = "Delete File"
    COPY = "Copy File"
    MOVE = "Move File"
    EXISTS = "File Exists"
    GET_SIZE = "Get File Size"
    GET_INFO = "Get File Info"
    CREATE_DIR = "Create Directory"
    LIST_FILES = "List Files"
    LIST_DIR = "List Directory"


# Port schema for dynamic port visibility
FILE_SYSTEM_PORT_SCHEMA = DynamicPortSchema()

# Read File ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.READ.value,
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("content", DataType.STRING),
            PortDef("size", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Write File ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.WRITE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("content", DataType.STRING),
        ],
        outputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("bytes_written", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Append File ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.APPEND.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("content", DataType.STRING),
        ],
        outputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("bytes_written", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Delete File ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.DELETE.value,
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("deleted_path", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Copy File ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.COPY.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("source_path", DataType.STRING),
            PortDef("dest_path", DataType.STRING),
        ],
        outputs=[
            PortDef("dest_path", DataType.STRING),
            PortDef("bytes_copied", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Move File ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.MOVE.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("source_path", DataType.STRING),
            PortDef("dest_path", DataType.STRING),
        ],
        outputs=[
            PortDef("dest_path", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# File Exists ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.EXISTS.value,
    ActionPortConfig.create(
        inputs=[PortDef("path", DataType.STRING)],
        outputs=[
            PortDef("exists", DataType.BOOLEAN),
            PortDef("is_file", DataType.BOOLEAN),
            PortDef("is_dir", DataType.BOOLEAN),
        ],
    ),
)

# Get File Size ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.GET_SIZE.value,
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("size", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Get File Info ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.GET_INFO.value,
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("size", DataType.INTEGER),
            PortDef("created", DataType.STRING),
            PortDef("modified", DataType.STRING),
            PortDef("extension", DataType.STRING),
            PortDef("name", DataType.STRING),
            PortDef("parent", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Create Directory ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.CREATE_DIR.value,
    ActionPortConfig.create(
        inputs=[PortDef("directory_path", DataType.STRING)],
        outputs=[
            PortDef("dir_path", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# List Files ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.LIST_FILES.value,
    ActionPortConfig.create(
        inputs=[PortDef("directory_path", DataType.STRING)],
        outputs=[
            PortDef("files", DataType.LIST),
            PortDef("count", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# List Directory ports
FILE_SYSTEM_PORT_SCHEMA.register(
    FileSystemAction.LIST_DIR.value,
    ActionPortConfig.create(
        inputs=[PortDef("dir_path", DataType.STRING)],
        outputs=[
            PortDef("items", DataType.LIST),
            PortDef("count", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)


# Actions that need file_path input
FILE_PATH_ACTIONS = [
    FileSystemAction.READ.value,
    FileSystemAction.WRITE.value,
    FileSystemAction.APPEND.value,
    FileSystemAction.DELETE.value,
    FileSystemAction.GET_SIZE.value,
    FileSystemAction.GET_INFO.value,
]

# Actions that need source_path and dest_path
DUAL_PATH_ACTIONS = [
    FileSystemAction.COPY.value,
    FileSystemAction.MOVE.value,
]

# Actions that need directory_path
DIRECTORY_PATH_ACTIONS = [
    FileSystemAction.CREATE_DIR.value,
    FileSystemAction.LIST_FILES.value,
]

# Actions that need content input
CONTENT_ACTIONS = [
    FileSystemAction.WRITE.value,
    FileSystemAction.APPEND.value,
]


@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=FileSystemAction.READ.value,
        label="Action",
        tooltip="File system operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in FileSystemAction],
    ),
    # === FILE PATH PROPERTIES ===
    PropertyDef(
        "file_path",
        PropertyType.FILE_PATH,
        label="File Path",
        tooltip="Path to the file",
        placeholder="C:\\path\\to\\file.txt",
        order=10,
        display_when={"action": FILE_PATH_ACTIONS},
    ),
    PropertyDef(
        "path",
        PropertyType.STRING,
        label="Path",
        tooltip="File or directory path to check",
        placeholder="C:\\path\\to\\file.txt",
        order=10,
        display_when={"action": [FileSystemAction.EXISTS.value]},
    ),
    PropertyDef(
        "source_path",
        PropertyType.FILE_PATH,
        label="Source Path",
        tooltip="Path to the source file",
        placeholder="C:\\path\\to\\source.txt",
        order=10,
        display_when={"action": DUAL_PATH_ACTIONS},
    ),
    PropertyDef(
        "dest_path",
        PropertyType.FILE_PATH,
        label="Destination Path",
        tooltip="Path to the destination",
        placeholder="C:\\path\\to\\destination.txt",
        order=11,
        display_when={"action": DUAL_PATH_ACTIONS},
    ),
    PropertyDef(
        "directory_path",
        PropertyType.DIRECTORY_PATH,
        label="Directory Path",
        tooltip="Path to the directory",
        placeholder="C:\\path\\to\\directory",
        order=10,
        display_when={"action": DIRECTORY_PATH_ACTIONS},
    ),
    PropertyDef(
        "dir_path",
        PropertyType.DIRECTORY_PATH,
        label="Directory Path",
        tooltip="Path to the directory",
        placeholder="C:\\path\\to\\directory",
        order=10,
        display_when={"action": [FileSystemAction.LIST_DIR.value]},
    ),
    # === CONTENT PROPERTIES ===
    PropertyDef(
        "content",
        PropertyType.TEXT,
        label="Content",
        tooltip="Content to write to file",
        order=20,
        display_when={"action": CONTENT_ACTIONS},
    ),
    # === READ OPTIONS ===
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="Text encoding (utf-8, ascii, latin-1, etc.)",
        order=30,
        display_when={
            "action": [
                FileSystemAction.READ.value,
                FileSystemAction.WRITE.value,
                FileSystemAction.APPEND.value,
            ]
        },
    ),
    PropertyDef(
        "binary_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Binary Mode",
        tooltip="Read/write as binary data",
        order=31,
        display_when={"action": [FileSystemAction.READ.value, FileSystemAction.WRITE.value]},
    ),
    PropertyDef(
        "max_size",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Max Size (bytes)",
        tooltip="Maximum file size to read (0 = unlimited)",
        order=32,
        display_when={"action": [FileSystemAction.READ.value]},
    ),
    # === WRITE OPTIONS ===
    PropertyDef(
        "create_dirs",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Directories",
        tooltip="Create parent directories if needed",
        order=33,
        display_when={
            "action": [
                FileSystemAction.WRITE.value,
                FileSystemAction.COPY.value,
                FileSystemAction.MOVE.value,
            ]
        },
    ),
    PropertyDef(
        "create_if_missing",
        PropertyType.BOOLEAN,
        default=True,
        label="Create If Missing",
        tooltip="Create file if it doesn't exist",
        order=33,
        display_when={"action": [FileSystemAction.APPEND.value]},
    ),
    # === DELETE OPTIONS ===
    PropertyDef(
        "ignore_missing",
        PropertyType.BOOLEAN,
        default=False,
        label="Ignore Missing",
        tooltip="Don't error if file doesn't exist",
        order=34,
        display_when={"action": [FileSystemAction.DELETE.value]},
    ),
    # === COPY/MOVE OPTIONS ===
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite",
        tooltip="Overwrite if destination exists",
        order=35,
        display_when={"action": DUAL_PATH_ACTIONS},
    ),
    # === EXISTS OPTIONS ===
    PropertyDef(
        "check_type",
        PropertyType.CHOICE,
        default="any",
        choices=["file", "directory", "any"],
        label="Check Type",
        tooltip="Type of path to check",
        order=36,
        display_when={"action": [FileSystemAction.EXISTS.value]},
    ),
    # === DIRECTORY OPTIONS ===
    PropertyDef(
        "parents",
        PropertyType.BOOLEAN,
        default=True,
        label="Create Parents",
        tooltip="Create parent directories as needed",
        order=37,
        display_when={"action": [FileSystemAction.CREATE_DIR.value]},
    ),
    PropertyDef(
        "exist_ok",
        PropertyType.BOOLEAN,
        default=True,
        label="Exist OK",
        tooltip="Don't error if directory already exists",
        order=38,
        display_when={"action": [FileSystemAction.CREATE_DIR.value]},
    ),
    # === LIST OPTIONS ===
    PropertyDef(
        "pattern",
        PropertyType.STRING,
        default="*",
        label="Pattern",
        tooltip="Glob pattern to filter results (e.g., *.txt)",
        order=39,
        display_when={
            "action": [
                FileSystemAction.LIST_FILES.value,
                FileSystemAction.LIST_DIR.value,
            ]
        },
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=False,
        label="Recursive",
        tooltip="Search subdirectories recursively",
        order=40,
        display_when={
            "action": [
                FileSystemAction.LIST_FILES.value,
                FileSystemAction.LIST_DIR.value,
            ]
        },
    ),
    PropertyDef(
        "files_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Files Only",
        tooltip="Only return files (exclude directories)",
        order=41,
        display_when={"action": [FileSystemAction.LIST_DIR.value]},
    ),
    PropertyDef(
        "dirs_only",
        PropertyType.BOOLEAN,
        default=False,
        label="Directories Only",
        tooltip="Only return directories (exclude files)",
        order=42,
        display_when={"action": [FileSystemAction.LIST_DIR.value]},
    ),
    # === SECURITY (always available) ===
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories (use with caution)",
        order=100,
    ),
)
@node(category="file")
class FileSystemSuperNode(BaseNode):
    """
    Unified file system operations node.

    Consolidates 12 atomic file operations into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        - Read File: Read content from a file
        - Write File: Write content to a file (overwrites)
        - Append File: Append content to a file
        - Delete File: Delete a file
        - Copy File: Copy a file to a new location
        - Move File: Move/rename a file
        - File Exists: Check if a path exists
        - Get File Size: Get file size in bytes
        - Get File Info: Get detailed file metadata
        - Create Directory: Create a directory
        - List Files: List files in a directory
        - List Directory: List files and directories
    """

    def __init__(self, node_id: str, name: str = "File System", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FileSystemSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Get current action from config
        action = self.get_parameter("action", FileSystemAction.READ.value)

        # Get port configuration for this action from schema
        port_config = FILE_SYSTEM_PORT_SCHEMA.get_config(action)

        if port_config:
            # Create input ports from schema
            for port_def in port_config.inputs:
                self.add_input_port(port_def.name, port_def.data_type)

            # Create output ports from schema
            for port_def in port_config.outputs:
                self.add_output_port(port_def.name, port_def.data_type)
        else:
            # Fallback to default Read File ports if action not found
            self.add_input_port("file_path", DataType.STRING)
            self.add_output_port("content", DataType.STRING)
            self.add_output_port("size", DataType.INTEGER)
            self.add_output_port("success", DataType.BOOLEAN)

    def _ensure_ports_for_action(self, action: str) -> None:
        """
        Ensure ports match the current action.

        This handles cases where the action was changed after initialization.
        Called at the start of execute() to guarantee correct ports exist.
        """
        port_config = FILE_SYSTEM_PORT_SCHEMA.get_config(action)
        if not port_config:
            return

        # Check if we need to update ports
        expected_inputs = {p.name for p in port_config.inputs}
        expected_outputs = {p.name for p in port_config.outputs}

        current_inputs = {name for name in self.input_ports if name != "exec_in"}
        current_outputs = {name for name in self.output_ports if name != "exec_out"}

        if expected_inputs != current_inputs or expected_outputs != current_outputs:
            # Remove unexpected input ports (keep exec_in)
            for name in list(self.input_ports.keys()):
                if name != "exec_in" and name not in expected_inputs:
                    del self.input_ports[name]

            # Remove unexpected output ports (keep exec_out)
            for name in list(self.output_ports.keys()):
                if name != "exec_out" and name not in expected_outputs:
                    del self.output_ports[name]

            # Create missing input ports
            for port_def in port_config.inputs:
                if port_def.name not in self.input_ports:
                    self.add_input_port(port_def.name, port_def.data_type)

            # Create missing output ports
            for port_def in port_config.outputs:
                if port_def.name not in self.output_ports:
                    self.add_output_port(port_def.name, port_def.data_type)

            logger.debug(f"FileSystemSuperNode: Updated ports for action '{action}'")

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected file system action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", FileSystemAction.READ.value)

        # CRITICAL: Ensure ports match the current action
        # This handles cases where action changed after node initialization
        self._ensure_ports_for_action(action)

        # Map actions to handlers
        handlers: dict[str, Callable[[IExecutionContext], Awaitable[ExecutionResult]]] = {
            FileSystemAction.READ.value: self._execute_read,
            FileSystemAction.WRITE.value: self._execute_write,
            FileSystemAction.APPEND.value: self._execute_append,
            FileSystemAction.DELETE.value: self._execute_delete,
            FileSystemAction.COPY.value: self._execute_copy,
            FileSystemAction.MOVE.value: self._execute_move,
            FileSystemAction.EXISTS.value: self._execute_exists,
            FileSystemAction.GET_SIZE.value: self._execute_get_size,
            FileSystemAction.GET_INFO.value: self._execute_get_info,
            FileSystemAction.CREATE_DIR.value: self._execute_create_dir,
            FileSystemAction.LIST_FILES.value: self._execute_list_files,
            FileSystemAction.LIST_DIR.value: self._execute_list_dir,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except PathSecurityError as e:
            # Safely set success if the port exists
            if "success" in self.output_ports:
                self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in FileSystemSuperNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
        except Exception as e:
            # Safely set success if the port exists
            if "success" in self.output_ports:
                self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Error in FileSystemSuperNode ({action}): {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    # === ACTION HANDLERS ===

    async def _execute_read(self, context: "IExecutionContext") -> ExecutionResult:
        """Read file content."""
        file_path = self.get_parameter("file_path")
        encoding = self.get_parameter("encoding", "utf-8")
        binary_mode = self.get_parameter("binary_mode", False)
        max_size = self.get_parameter("max_size", 0)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security(file_path, "read", allow_dangerous)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        size = path.stat().st_size
        if max_size > 0 and size > max_size:
            raise ValueError(f"File size ({size}) exceeds limit ({max_size})")

        logger.info(f"Reading file: {path} (binary={binary_mode})")

        if binary_mode:
            content = await AsyncFileOperations.read_binary(path)
        else:
            content = await AsyncFileOperations.read_text(path, encoding, "replace")

        self.set_output_value("content", content)
        self.set_output_value("size", size)
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"size": size},
            "next_nodes": ["exec_out"],
        }

    async def _execute_write(self, context: "IExecutionContext") -> ExecutionResult:
        """Write content to file."""
        file_path = self.get_parameter("file_path")
        content = self.get_parameter("content", "")
        encoding = self.get_parameter("encoding", "utf-8")
        binary_mode = self.get_parameter("binary_mode", False)
        create_dirs = self.get_parameter("create_dirs", True)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        content = content if content else ""
        path = validate_path_security(file_path, "write", allow_dangerous)

        if create_dirs and path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing file: {path}")

        if binary_mode:
            if isinstance(content, str):
                content = content.encode(encoding)
            bytes_written = await AsyncFileOperations.write_binary(
                path, content, create_dirs=create_dirs
            )
        else:
            text_content = str(content) if content else ""
            bytes_written = await AsyncFileOperations.write_text(
                path, text_content, encoding, "replace", create_dirs=create_dirs
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

    async def _execute_append(self, context: "IExecutionContext") -> ExecutionResult:
        """Append content to file."""
        file_path = self.get_parameter("file_path")
        content = self.get_parameter("content", "")
        encoding = self.get_parameter("encoding", "utf-8")
        create_if_missing = self.get_parameter("create_if_missing", True)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        content = content if content else ""
        path = validate_path_security(file_path, "append", allow_dangerous)

        if not path.exists() and not create_if_missing:
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

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

    async def _execute_delete(self, context: "IExecutionContext") -> ExecutionResult:
        """Delete a file."""
        file_path = self.get_parameter("file_path")
        ignore_missing = self.get_parameter("ignore_missing", False)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
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
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.warning(f"Deleting file: {path}")
        await asyncio.to_thread(path.unlink)

        self.set_output_value("deleted_path", str(path))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"deleted_path": str(path)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_copy(self, context: "IExecutionContext") -> ExecutionResult:
        """Copy a file."""
        source_path = self.get_parameter("source_path")
        dest_path = self.get_parameter("dest_path")
        overwrite = self.get_parameter("overwrite", False)
        create_dirs = self.get_parameter("create_dirs", True)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not source_path or not dest_path:
            raise ValueError("source_path and dest_path are required")

        source_path = os.path.expandvars(source_path)
        dest_path = os.path.expandvars(dest_path)

        source = validate_path_security(source_path, "read", allow_dangerous)
        dest = validate_path_security(dest_path, "write", allow_dangerous)

        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        if dest.exists() and not overwrite:
            raise FileExistsError(f"Destination exists: {dest_path}")

        if create_dirs and dest.parent:
            dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Copying: {source} -> {dest}")
        await asyncio.to_thread(shutil.copy2, source, dest)
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

    async def _execute_move(self, context: "IExecutionContext") -> ExecutionResult:
        """Move/rename a file."""
        source_path = self.get_parameter("source_path")
        dest_path = self.get_parameter("dest_path")
        overwrite = self.get_parameter("overwrite", False)
        create_dirs = self.get_parameter("create_dirs", True)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not source_path or not dest_path:
            raise ValueError("source_path and dest_path are required")

        source_path = os.path.expandvars(source_path)
        dest_path = os.path.expandvars(dest_path)

        source = validate_path_security(source_path, "read", allow_dangerous)
        dest = validate_path_security(dest_path, "write", allow_dangerous)

        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source_path}")

        if dest.exists() and not overwrite:
            raise FileExistsError(f"Destination exists: {dest_path}")

        if create_dirs and dest.parent:
            dest.parent.mkdir(parents=True, exist_ok=True)

        if dest.exists() and overwrite:
            await asyncio.to_thread(dest.unlink)

        logger.info(f"Moving: {source} -> {dest}")
        await asyncio.to_thread(shutil.move, str(source), str(dest))

        self.set_output_value("dest_path", str(dest))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"dest_path": str(dest)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_exists(self, context: "IExecutionContext") -> ExecutionResult:
        """Check if path exists."""
        file_path = self.get_parameter("path")
        check_type = self.get_parameter("check_type", "any")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security_readonly(file_path, "check", allow_dangerous)

        exists = path.exists()
        is_file = path.is_file() if exists else False
        is_dir = path.is_dir() if exists else False

        if check_type == "file":
            exists = is_file
        elif check_type == "directory":
            exists = is_dir

        self.set_output_value("exists", exists)
        self.set_output_value("is_file", is_file)
        self.set_output_value("is_dir", is_dir)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"exists": exists, "is_file": is_file, "is_dir": is_dir},
            "next_nodes": ["exec_out"],
        }

    async def _execute_get_size(self, context: "IExecutionContext") -> ExecutionResult:
        """Get file size."""
        file_path = self.get_parameter("file_path")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security_readonly(file_path, "stat", allow_dangerous)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        size = path.stat().st_size

        self.set_output_value("size", size)
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"size": size},
            "next_nodes": ["exec_out"],
        }

    async def _execute_get_info(self, context: "IExecutionContext") -> ExecutionResult:
        """Get detailed file info."""
        file_path = self.get_parameter("file_path")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security_readonly(file_path, "stat", allow_dangerous)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        stat = path.stat()

        self.set_output_value("size", stat.st_size)
        self.set_output_value("created", datetime.fromtimestamp(stat.st_ctime).isoformat())
        self.set_output_value("modified", datetime.fromtimestamp(stat.st_mtime).isoformat())
        self.set_output_value("extension", path.suffix)
        self.set_output_value("name", path.name)
        self.set_output_value("parent", str(path.parent))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"name": path.name, "size": stat.st_size},
            "next_nodes": ["exec_out"],
        }

    async def _execute_create_dir(self, context: "IExecutionContext") -> ExecutionResult:
        """Create directory."""
        dir_path = self.get_parameter("directory_path")
        parents = self.get_parameter("parents", True)
        exist_ok = self.get_parameter("exist_ok", True)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not dir_path:
            raise ValueError("directory_path is required")

        dir_path = os.path.expandvars(dir_path)
        path = validate_path_security(dir_path, "mkdir", allow_dangerous)
        await asyncio.to_thread(path.mkdir, parents=parents, exist_ok=exist_ok)

        self.set_output_value("dir_path", str(path))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"dir_path": str(path)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_list_files(self, context: "IExecutionContext") -> ExecutionResult:
        """List files in directory."""
        dir_path = self.get_parameter("directory_path")
        pattern = self.get_parameter("pattern", "*")
        recursive = self.get_parameter("recursive", False)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not dir_path:
            raise ValueError("directory_path is required")

        dir_path = os.path.expandvars(dir_path)

        # SECURITY: Validate pattern doesn't contain path traversal
        if ".." in pattern:
            raise PathSecurityError("Pattern cannot contain path traversal sequences (..)")

        path = validate_path_security_readonly(dir_path, "list", allow_dangerous)

        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")

        if recursive:
            matches = list(path.rglob(pattern))
        else:
            matches = list(path.glob(pattern))

        files = [str(item) for item in matches if item.is_file()]

        self.set_output_value("files", files)
        self.set_output_value("count", len(files))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"count": len(files)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_list_dir(self, context: "IExecutionContext") -> ExecutionResult:
        """List files and directories."""
        dir_path = self.get_parameter("dir_path")
        pattern = self.get_parameter("pattern", "*")
        recursive = self.get_parameter("recursive", False)
        files_only = self.get_parameter("files_only", False)
        dirs_only = self.get_parameter("dirs_only", False)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not dir_path:
            raise ValueError("dir_path is required")

        dir_path = os.path.expandvars(dir_path)

        # SECURITY: Validate pattern doesn't contain path traversal
        if ".." in pattern:
            raise PathSecurityError("Pattern cannot contain path traversal sequences (..)")

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
            "data": {"count": len(items)},
            "next_nodes": ["exec_out"],
        }

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


# =============================================================================
# StructuredDataSuperNode - Consolidates 7 structured data operations
# =============================================================================


class StructuredDataAction(str, Enum):
    """Actions available in StructuredDataSuperNode."""

    READ_CSV = "Read CSV"
    WRITE_CSV = "Write CSV"
    READ_JSON = "Read JSON"
    WRITE_JSON = "Write JSON"
    ZIP = "Zip Files"
    UNZIP = "Unzip Files"
    IMAGE_CONVERT = "Image Convert"


# Port schema for dynamic port visibility
STRUCTURED_DATA_PORT_SCHEMA = DynamicPortSchema()

# Read CSV ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.READ_CSV.value,
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("data", DataType.LIST),
            PortDef("headers", DataType.LIST),
            PortDef("row_count", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Write CSV ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.WRITE_CSV.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("data", DataType.LIST),
            PortDef("headers", DataType.LIST),
        ],
        outputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("row_count", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Read JSON ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.READ_JSON.value,
    ActionPortConfig.create(
        inputs=[PortDef("file_path", DataType.STRING)],
        outputs=[
            PortDef("data", DataType.ANY),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Write JSON ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.WRITE_JSON.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("data", DataType.ANY),
        ],
        outputs=[
            PortDef("file_path", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Zip ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.ZIP.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("zip_path", DataType.STRING),
            PortDef("source_path", DataType.STRING),
            PortDef("files", DataType.LIST),
        ],
        outputs=[
            PortDef("zip_path", DataType.STRING),
            PortDef("file_count", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Unzip ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.UNZIP.value,
    ActionPortConfig.create(
        inputs=[
            PortDef("zip_path", DataType.STRING),
            PortDef("extract_to", DataType.STRING),
        ],
        outputs=[
            PortDef("extract_to", DataType.STRING),
            PortDef("files", DataType.LIST),
            PortDef("file_count", DataType.INTEGER),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)

# Image Convert ports
STRUCTURED_DATA_PORT_SCHEMA.register(
    StructuredDataAction.IMAGE_CONVERT.value,
    ActionPortConfig.create(
        inputs=[PortDef("source_path", DataType.STRING)],
        outputs=[
            PortDef("output_path", DataType.STRING),
            PortDef("files", DataType.LIST),
            PortDef("file_count", DataType.INTEGER),
            PortDef("format", DataType.STRING),
            PortDef("success", DataType.BOOLEAN),
        ],
    ),
)


# Actions that need file_path input
STRUCTURED_FILE_PATH_ACTIONS = [
    StructuredDataAction.READ_CSV.value,
    StructuredDataAction.WRITE_CSV.value,
    StructuredDataAction.READ_JSON.value,
    StructuredDataAction.WRITE_JSON.value,
]

# Actions that need data input
STRUCTURED_DATA_INPUT_ACTIONS = [
    StructuredDataAction.WRITE_CSV.value,
    StructuredDataAction.WRITE_JSON.value,
]

# CSV actions
CSV_ACTIONS = [
    StructuredDataAction.READ_CSV.value,
    StructuredDataAction.WRITE_CSV.value,
]

# JSON actions
JSON_ACTIONS = [
    StructuredDataAction.READ_JSON.value,
    StructuredDataAction.WRITE_JSON.value,
]

# Supported image formats
SUPPORTED_IMAGE_FORMATS = {
    "PNG": ".png",
    "JPEG": ".jpg",
    "WEBP": ".webp",
    "BMP": ".bmp",
    "GIF": ".gif",
}

SUPPORTED_INPUT_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".bmp",
    ".gif",
}

SCALE_PERCENT_CHOICES = ["5%", "10%", "25%", "50%", "75%", "100%"]


@properties(
    # === ESSENTIAL: Action selector (always visible) ===
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default=StructuredDataAction.READ_CSV.value,
        label="Action",
        tooltip="Structured data operation to perform",
        essential=True,
        order=0,
        choices=[a.value for a in StructuredDataAction],
    ),
    # === FILE PATH PROPERTIES ===
    PropertyDef(
        "file_path",
        PropertyType.FILE_PATH,
        label="File Path",
        tooltip="Path to the file",
        placeholder="C:\\path\\to\\file",
        order=10,
        display_when={"action": STRUCTURED_FILE_PATH_ACTIONS},
    ),
    PropertyDef(
        "zip_path",
        PropertyType.FILE_PATH,
        label="ZIP Path",
        tooltip="Path to the ZIP archive",
        placeholder="C:\\path\\to\\archive.zip",
        order=10,
        display_when={"action": [StructuredDataAction.ZIP.value, StructuredDataAction.UNZIP.value]},
    ),
    PropertyDef(
        "source_path",
        PropertyType.STRING,
        label="Source Path",
        tooltip="Source path (folder, glob pattern, or image file)",
        placeholder="C:\\folder or C:\\folder\\*.txt or C:\\image.png",
        order=11,
        display_when={
            "action": [
                StructuredDataAction.ZIP.value,
                StructuredDataAction.IMAGE_CONVERT.value,
            ]
        },
    ),
    PropertyDef(
        "extract_to",
        PropertyType.DIRECTORY_PATH,
        label="Extract To",
        tooltip="Directory to extract files to",
        placeholder="C:\\extracted",
        order=12,
        display_when={"action": [StructuredDataAction.UNZIP.value]},
    ),
    PropertyDef(
        "output_path",
        PropertyType.FILE_PATH,
        label="Output Path",
        tooltip="Output path (auto-generated if empty)",
        placeholder="C:\\path\\to\\output.jpg",
        order=12,
        display_when={"action": [StructuredDataAction.IMAGE_CONVERT.value]},
    ),
    # === CSV OPTIONS ===
    PropertyDef(
        "delimiter",
        PropertyType.STRING,
        default=",",
        label="Delimiter",
        tooltip="CSV field delimiter",
        order=20,
        display_when={"action": CSV_ACTIONS},
    ),
    PropertyDef(
        "has_header",
        PropertyType.BOOLEAN,
        default=True,
        label="Has Header",
        tooltip="First row contains headers",
        order=21,
        display_when={"action": [StructuredDataAction.READ_CSV.value]},
    ),
    PropertyDef(
        "write_header",
        PropertyType.BOOLEAN,
        default=True,
        label="Write Header",
        tooltip="Write headers as first row",
        order=21,
        display_when={"action": [StructuredDataAction.WRITE_CSV.value]},
    ),
    PropertyDef(
        "encoding",
        PropertyType.STRING,
        default="utf-8",
        label="Encoding",
        tooltip="Text encoding (utf-8, ascii, latin-1, etc.)",
        order=22,
        display_when={"action": STRUCTURED_FILE_PATH_ACTIONS},
    ),
    PropertyDef(
        "skip_rows",
        PropertyType.INTEGER,
        default=0,
        label="Skip Rows",
        tooltip="Number of rows to skip",
        order=23,
        display_when={"action": [StructuredDataAction.READ_CSV.value]},
    ),
    PropertyDef(
        "max_rows",
        PropertyType.INTEGER,
        default=0,
        label="Max Rows (0=unlimited)",
        tooltip="Maximum rows to read (0 = unlimited)",
        order=24,
        display_when={"action": [StructuredDataAction.READ_CSV.value]},
    ),
    # === JSON OPTIONS ===
    PropertyDef(
        "indent",
        PropertyType.INTEGER,
        default=2,
        label="Indent",
        tooltip="JSON indentation spaces",
        order=25,
        display_when={"action": [StructuredDataAction.WRITE_JSON.value]},
    ),
    PropertyDef(
        "ensure_ascii",
        PropertyType.BOOLEAN,
        default=False,
        label="Ensure ASCII",
        tooltip="Escape non-ASCII characters",
        order=26,
        display_when={"action": [StructuredDataAction.WRITE_JSON.value]},
    ),
    # === ZIP OPTIONS ===
    PropertyDef(
        "compression",
        PropertyType.CHOICE,
        default="ZIP_DEFLATED",
        choices=["ZIP_STORED", "ZIP_DEFLATED"],
        label="Compression",
        tooltip="ZIP compression method",
        order=30,
        display_when={"action": [StructuredDataAction.ZIP.value]},
    ),
    PropertyDef(
        "base_dir",
        PropertyType.STRING,
        default="",
        label="Base Directory",
        tooltip="Base directory for relative paths in archive",
        placeholder="C:\\source\\folder",
        order=31,
        display_when={"action": [StructuredDataAction.ZIP.value]},
    ),
    # === IMAGE CONVERT OPTIONS ===
    PropertyDef(
        "output_format",
        PropertyType.CHOICE,
        default="JPEG",
        choices=["PNG", "JPEG", "WEBP", "BMP", "GIF"],
        label="Output Format",
        tooltip="Target image format",
        order=40,
        display_when={"action": [StructuredDataAction.IMAGE_CONVERT.value]},
    ),
    PropertyDef(
        "quality",
        PropertyType.INTEGER,
        default=85,
        label="Quality",
        tooltip="Quality for JPEG/WEBP (1-100)",
        min_value=1,
        max_value=100,
        order=41,
        display_when={"action": [StructuredDataAction.IMAGE_CONVERT.value]},
    ),
    PropertyDef(
        "scale_percent",
        PropertyType.CHOICE,
        default="100%",
        choices=SCALE_PERCENT_CHOICES,
        label="Scale (%)",
        tooltip="Resize output dimensions to this percentage of original",
        order=42,
        display_when={"action": [StructuredDataAction.IMAGE_CONVERT.value]},
    ),
    PropertyDef(
        "overwrite",
        PropertyType.BOOLEAN,
        default=False,
        label="Overwrite",
        tooltip="Overwrite if destination exists",
        order=43,
        display_when={"action": [StructuredDataAction.IMAGE_CONVERT.value]},
    ),
    PropertyDef(
        "recursive",
        PropertyType.BOOLEAN,
        default=False,
        label="Recursive",
        tooltip="When source_path is a folder, convert images in subfolders too",
        order=44,
        display_when={"action": [StructuredDataAction.IMAGE_CONVERT.value]},
    ),
    # === SECURITY (always available) ===
    PropertyDef(
        "allow_dangerous_paths",
        PropertyType.BOOLEAN,
        default=False,
        label="Allow Dangerous Paths",
        tooltip="Allow access to system directories (use with caution)",
        order=100,
    ),
)
@node(category="file")
class StructuredDataSuperNode(BaseNode):
    """
    Unified structured data operations node.

    Consolidates 7 atomic structured data operations into a single configurable node.
    Select an action from the dropdown to see relevant properties and ports.

    Actions:
        - Read CSV: Read and parse CSV files into data/headers
        - Write CSV: Write data to CSV files
        - Read JSON: Read and parse JSON files
        - Write JSON: Write data to JSON files
        - Zip Files: Create ZIP archives from files/folders
        - Unzip Files: Extract ZIP archives
        - Image Convert: Convert images between formats
    """

    def __init__(self, node_id: str, name: str = "Structured Data", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "StructuredDataSuperNode"

    def _define_ports(self) -> None:
        """Define ports based on current action."""
        # Get current action from config
        action = self.get_parameter("action", StructuredDataAction.READ_CSV.value)

        # Get port configuration for this action from schema
        port_config = STRUCTURED_DATA_PORT_SCHEMA.get_config(action)

        if port_config:
            # Create input ports from schema
            for port_def in port_config.inputs:
                self.add_input_port(port_def.name, port_def.data_type)

            # Create output ports from schema
            for port_def in port_config.outputs:
                self.add_output_port(port_def.name, port_def.data_type)
        else:
            # Fallback to default Read CSV ports
            self.add_input_port("file_path", DataType.STRING)
            self.add_output_port("data", DataType.LIST)
            self.add_output_port("headers", DataType.LIST)
            self.add_output_port("row_count", DataType.INTEGER)
            self.add_output_port("success", DataType.BOOLEAN)

    def _ensure_ports_for_action(self, action: str) -> None:
        """
        Ensure ports match the current action.

        This handles cases where the action was changed after initialization.
        Called at the start of execute() to guarantee correct ports exist.
        """
        port_config = STRUCTURED_DATA_PORT_SCHEMA.get_config(action)
        if not port_config:
            return

        # Check if we need to update ports
        expected_inputs = {p.name for p in port_config.inputs}
        expected_outputs = {p.name for p in port_config.outputs}

        current_inputs = {name for name in self.input_ports if name != "exec_in"}
        current_outputs = {name for name in self.output_ports if name != "exec_out"}

        if expected_inputs != current_inputs or expected_outputs != current_outputs:
            # Remove unexpected input ports (keep exec_in)
            for name in list(self.input_ports.keys()):
                if name != "exec_in" and name not in expected_inputs:
                    del self.input_ports[name]

            # Remove unexpected output ports (keep exec_out)
            for name in list(self.output_ports.keys()):
                if name != "exec_out" and name not in expected_outputs:
                    del self.output_ports[name]

            # Create missing input ports
            for port_def in port_config.inputs:
                if port_def.name not in self.input_ports:
                    self.add_input_port(port_def.name, port_def.data_type)

            # Create missing output ports
            for port_def in port_config.outputs:
                if port_def.name not in self.output_ports:
                    self.add_output_port(port_def.name, port_def.data_type)

            logger.debug(f"StructuredDataSuperNode: Updated ports for action '{action}'")

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """Execute the selected structured data action."""
        self.status = NodeStatus.RUNNING

        action = self.get_parameter("action", StructuredDataAction.READ_CSV.value)

        # CRITICAL: Ensure ports match the current action
        self._ensure_ports_for_action(action)

        # Map actions to handlers
        handlers: dict[str, Callable[[IExecutionContext], Awaitable[ExecutionResult]]] = {
            StructuredDataAction.READ_CSV.value: self._execute_read_csv,
            StructuredDataAction.WRITE_CSV.value: self._execute_write_csv,
            StructuredDataAction.READ_JSON.value: self._execute_read_json,
            StructuredDataAction.WRITE_JSON.value: self._execute_write_json,
            StructuredDataAction.ZIP.value: self._execute_zip,
            StructuredDataAction.UNZIP.value: self._execute_unzip,
            StructuredDataAction.IMAGE_CONVERT.value: self._execute_image_convert,
        }

        handler = handlers.get(action)
        if not handler:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Unknown action: {action}"}

        try:
            return await handler(context)
        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in StructuredDataSuperNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}
        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Error in StructuredDataSuperNode ({action}): {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

    # === ACTION HANDLERS ===

    async def _execute_read_csv(self, context: "IExecutionContext") -> ExecutionResult:
        """Read and parse CSV file."""
        file_path = self.get_parameter("file_path")
        delimiter = self.get_parameter("delimiter", ",")
        has_header = self.get_parameter("has_header", True)
        encoding = self.get_parameter("encoding", "utf-8")
        skip_rows = self.get_parameter("skip_rows", 0)
        max_rows = self.get_parameter("max_rows", 0)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security(file_path, "read", allow_dangerous)

        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        logger.info(f"Reading CSV: {path} (delimiter='{delimiter}', has_header={has_header})")

        data, headers = await AsyncFileOperations.read_csv(
            path,
            encoding=encoding,
            delimiter=delimiter,
            has_header=has_header,
            skip_rows=skip_rows,
            max_rows=max_rows,
        )

        self.set_output_value("data", data)
        self.set_output_value("headers", headers)
        self.set_output_value("row_count", len(data))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        logger.info(f"CSV read successfully: {len(data)} rows, {len(headers)} columns")

        return {
            "success": True,
            "data": {"row_count": len(data), "headers": headers},
            "next_nodes": ["exec_out"],
        }

    async def _execute_write_csv(self, context: "IExecutionContext") -> ExecutionResult:
        """Write data to CSV file."""
        file_path = self.get_parameter("file_path")
        data = self.get_parameter("data") or []
        headers = self.get_parameter("headers")
        delimiter = self.get_parameter("delimiter", ",")
        write_header = self.get_parameter("write_header", True)
        encoding = self.get_parameter("encoding", "utf-8")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        data = data or []
        headers = headers if headers else None
        path = validate_path_security(file_path, "write", allow_dangerous)

        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        row_count = await AsyncFileOperations.write_csv(
            path,
            data,
            headers=headers,
            encoding=encoding,
            delimiter=delimiter,
            write_header=write_header,
            create_dirs=True,
        )

        self.set_output_value("file_path", str(path))
        self.set_output_value("row_count", row_count)
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"file_path": str(path), "row_count": row_count},
            "next_nodes": ["exec_out"],
        }

    async def _execute_read_json(self, context: "IExecutionContext") -> ExecutionResult:
        """Read and parse JSON file."""
        file_path = self.get_parameter("file_path")
        encoding = self.get_parameter("encoding", "utf-8")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security(file_path, "read", allow_dangerous)

        if not path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")

        data = await AsyncFileOperations.read_json(path, encoding=encoding)

        self.set_output_value("data", data)
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"type": type(data).__name__},
            "next_nodes": ["exec_out"],
        }

    async def _execute_write_json(self, context: "IExecutionContext") -> ExecutionResult:
        """Write data to JSON file."""
        file_path = self.get_parameter("file_path")
        data = self.get_parameter("data")
        encoding = self.get_parameter("encoding", "utf-8")
        indent = self.get_parameter("indent", 2)
        ensure_ascii = self.get_parameter("ensure_ascii", False)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not file_path:
            raise ValueError("file_path is required")

        file_path = os.path.expandvars(file_path)
        path = validate_path_security(file_path, "write", allow_dangerous)

        if path.parent:
            path.parent.mkdir(parents=True, exist_ok=True)

        await AsyncFileOperations.write_json(
            path,
            data,
            encoding=encoding,
            indent=indent,
            ensure_ascii=ensure_ascii,
            create_dirs=True,
        )

        self.set_output_value("file_path", str(path))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"file_path": str(path)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_zip(self, context: "IExecutionContext") -> ExecutionResult:
        """Create ZIP archive."""
        zip_path = self.get_parameter("zip_path")
        source_path = self.get_parameter("source_path")
        files = self.get_parameter("files") or []
        base_dir = self.get_parameter("base_dir")
        compression = self.get_parameter("compression", "ZIP_DEFLATED")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not zip_path:
            raise ValueError("zip_path is required")

        zip_path = os.path.expandvars(zip_path)
        if source_path:
            source_path = os.path.expandvars(source_path)
        if base_dir:
            base_dir = os.path.expandvars(base_dir)

        zip_validated_path = validate_path_security(zip_path, "write", allow_dangerous)

        # Auto-discover files from source_path if files list is empty
        if not files and source_path:
            source = Path(source_path)

            if source.is_dir():
                files = [str(f) for f in source.rglob("*") if f.is_file()]
                if not base_dir:
                    base_dir = str(source)
                logger.info(f"Auto-discovered {len(files)} files from folder: {source}")
            elif "*" in source_path or "?" in source_path:
                files = [
                    f for f in glob_module.glob(source_path, recursive=True) if Path(f).is_file()
                ]
                if not base_dir:
                    parts = Path(source_path).parts
                    non_glob_parts = []
                    for part in parts:
                        if "*" in part or "?" in part:
                            break
                        non_glob_parts.append(part)
                    if non_glob_parts:
                        base_dir = str(Path(*non_glob_parts))
                logger.info(f"Auto-discovered {len(files)} files from glob pattern")
            elif source.is_file():
                files = [str(source)]
            else:
                raise ValueError(f"source_path not found: {source_path}")

        if not files:
            raise ValueError("No files to zip. Provide 'source_path' or connect 'files' input.")

        zip_compression = (
            zipfile.ZIP_DEFLATED if compression == "ZIP_DEFLATED" else zipfile.ZIP_STORED
        )

        if zip_validated_path.parent:
            zip_validated_path.parent.mkdir(parents=True, exist_ok=True)

        base = Path(base_dir) if base_dir else None

        def _create_zip() -> int:
            """Create ZIP archive synchronously (runs in thread)."""
            count = 0
            with zipfile.ZipFile(zip_validated_path, "w", compression=zip_compression) as zf:
                for fp_str in files:
                    fp = Path(fp_str)
                    if not fp.exists():
                        continue

                    if base and fp.is_relative_to(base):
                        arcname = str(fp.relative_to(base))
                    else:
                        arcname = fp.name

                    zf.write(fp, arcname)
                    count += 1
            return count

        file_count = await asyncio.to_thread(_create_zip)

        self.set_output_value("zip_path", str(zip_validated_path))
        self.set_output_value("file_count", file_count)
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        logger.info(f"Created ZIP archive: {zip_validated_path} with {file_count} files")

        return {
            "success": True,
            "data": {"zip_path": str(zip_validated_path), "file_count": file_count},
            "next_nodes": ["exec_out"],
        }

    async def _execute_unzip(self, context: "IExecutionContext") -> ExecutionResult:
        """Extract ZIP archive."""
        zip_path = self.get_parameter("zip_path")
        extract_to = self.get_parameter("extract_to")
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not zip_path:
            raise ValueError("zip_path is required")
        if not extract_to:
            raise ValueError("extract_to is required")

        zip_path = os.path.expandvars(zip_path)
        extract_to = os.path.expandvars(extract_to)

        zip_file = validate_path_security(zip_path, "read", allow_dangerous)
        dest = validate_path_security(extract_to, "write", allow_dangerous)

        if not zip_file.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        dest.mkdir(parents=True, exist_ok=True)

        def _extract_zip() -> list:
            """Extract ZIP archive synchronously (runs in thread)."""
            extracted = []
            with zipfile.ZipFile(zip_file, "r") as zf:
                for member in zf.namelist():
                    # SECURITY: Validate entry path to prevent Zip Slip
                    target_dir = dest.resolve()
                    target_path = (target_dir / member).resolve()

                    if not str(target_path).startswith(str(target_dir)):
                        raise PathSecurityError(
                            f"Zip Slip attack detected! Entry '{member}' would extract "
                            f"outside the target directory."
                        )

                    if member.endswith("/"):
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with (
                            zf.open(member) as source,
                            open(target_path, "wb") as target,
                        ):
                            target.write(source.read())

                    extracted.append(str(target_path))
            return extracted

        extracted_files = await asyncio.to_thread(_extract_zip)

        logger.info(f"Extracted {len(extracted_files)} files to {dest}")

        self.set_output_value("extract_to", str(dest))
        self.set_output_value("files", extracted_files)
        self.set_output_value("file_count", len(extracted_files))
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"extract_to": str(dest), "file_count": len(extracted_files)},
            "next_nodes": ["exec_out"],
        }

    async def _execute_image_convert(self, context: "IExecutionContext") -> ExecutionResult:
        """Convert image between formats."""
        source_path = self.get_parameter("source_path")
        output_path = self.get_parameter("output_path", "")
        output_format = self.get_parameter("output_format", "JPEG")
        quality = self.get_parameter("quality", 85)
        scale_percent = self.get_parameter("scale_percent", "100%")
        overwrite = self.get_parameter("overwrite", False)
        recursive = self.get_parameter("recursive", False)
        allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

        if not source_path:
            raise ValueError("source_path is required")

        output_format = output_format.upper()
        if output_format not in SUPPORTED_IMAGE_FORMATS:
            raise ValueError(
                f"Unsupported format: {output_format}. "
                f"Supported: {', '.join(SUPPORTED_IMAGE_FORMATS.keys())}"
            )

        try:
            quality = int(quality)
        except (TypeError, ValueError):
            raise ValueError("quality must be an integer between 1 and 100")

        if quality < 1 or quality > 100:
            raise ValueError("quality must be between 1 and 100")

        try:
            if isinstance(scale_percent, str):
                scale_percent = scale_percent.strip()
                if scale_percent.endswith("%"):
                    scale_percent = scale_percent[:-1]
            scale_percent = int(scale_percent)
        except (TypeError, ValueError):
            raise ValueError("scale_percent must be one of: " + ", ".join(SCALE_PERCENT_CHOICES))

        if scale_percent not in (5, 10, 25, 50, 75, 100):
            raise ValueError("scale_percent must be one of: " + ", ".join(SCALE_PERCENT_CHOICES))

        source_path = os.path.expandvars(source_path)
        source = validate_path_security(source_path, "read", allow_dangerous)

        if not source.exists():
            raise FileNotFoundError(f"Source image not found: {source_path}")

        ext = SUPPORTED_IMAGE_FORMATS[output_format]

        if source.is_dir():
            if output_path:
                output_path = os.path.expandvars(output_path)
            else:
                output_path = str(source / "converted")

            output_dir = validate_path_security(output_path, "write", allow_dangerous)
            if output_dir.exists() and output_dir.is_file():
                raise ValueError(
                    f"output_path must be a directory when source_path is a folder: {output_path}"
                )
            output_dir.mkdir(parents=True, exist_ok=True)

            candidates = source.rglob("*") if recursive else source.iterdir()
            input_files = [
                p
                for p in candidates
                if p.is_file() and p.suffix.lower() in SUPPORTED_INPUT_IMAGE_EXTENSIONS
            ]
            if not input_files:
                raise ValueError(f"No images found in folder: {source}")

            logger.info(
                f"Batch converting {len(input_files)} images: {source} -> {output_dir} ({output_format})"
            )

            def _convert_batch() -> list[str]:
                converted: list[str] = []
                resample = (
                    Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
                )
                for input_file in input_files:
                    safe_source = validate_path_security(input_file, "read", allow_dangerous)
                    rel = input_file.relative_to(source) if recursive else Path(input_file.name)
                    dest_candidate = (output_dir / rel).with_suffix(ext)
                    dest_candidate.parent.mkdir(parents=True, exist_ok=True)
                    dest = validate_path_security(dest_candidate, "write", allow_dangerous)

                    if dest.exists() and not overwrite:
                        raise FileExistsError(f"Destination already exists: {dest_candidate}")

                    with Image.open(safe_source) as img:
                        img = ImageOps.exif_transpose(img)

                        if scale_percent != 100:
                            new_width = max(1, int(round(img.width * scale_percent / 100)))
                            new_height = max(1, int(round(img.height * scale_percent / 100)))
                            img = img.resize((new_width, new_height), resample=resample)
                        # Handle transparency for JPEG
                        if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                            background = Image.new("RGB", img.size, (255, 255, 255))
                            if img.mode == "P":
                                img = img.convert("RGBA")
                            background.paste(img, mask=img.split()[3])
                            img = background
                        elif output_format == "JPEG" and img.mode != "RGB":
                            img = img.convert("RGB")

                        save_kwargs = {}
                        if output_format in ("JPEG", "WEBP"):
                            save_kwargs["quality"] = quality
                        if output_format in ("PNG", "JPEG"):
                            save_kwargs["optimize"] = True

                        img.save(dest, format=output_format, **save_kwargs)

                    converted.append(str(dest))

                return converted

            converted_files = await asyncio.to_thread(_convert_batch)

            self.set_output_value("output_path", str(output_dir))
            self.set_output_value("files", converted_files)
            self.set_output_value("file_count", len(converted_files))
            self.set_output_value("format", output_format)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "output_path": str(output_dir),
                    "format": output_format,
                    "file_count": len(converted_files),
                },
                "next_nodes": ["exec_out"],
            }

        if not output_path:
            output_path = str(source.with_suffix(ext))
            if not overwrite and Path(output_path).resolve() == source.resolve():
                output_path = str(source.with_name(f"{source.stem}_converted{ext}"))
        else:
            output_path = os.path.expandvars(output_path)

        # SECURITY: Validate output path (supports directory targets)
        directory_hint = output_path.endswith(os.sep) or (
            os.altsep is not None and output_path.endswith(os.altsep)
        )
        dest_candidate = validate_path_security(output_path, "write", allow_dangerous)
        if directory_hint or (dest_candidate.exists() and dest_candidate.is_dir()):
            dest_candidate.mkdir(parents=True, exist_ok=True)
            dest_candidate = dest_candidate / f"{source.stem}{ext}"

        dest = validate_path_security(dest_candidate, "write", allow_dangerous)

        if dest.exists() and not overwrite:
            raise FileExistsError(f"Destination already exists: {output_path}")

        if dest.parent:
            dest.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converting image: {source} -> {dest} ({output_format})")

        def _convert_image() -> None:
            """Convert image synchronously (runs in thread)."""
            with Image.open(source) as img:
                img = ImageOps.exif_transpose(img)

                if scale_percent != 100:
                    resample = (
                        Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS
                    )
                    new_width = max(1, int(round(img.width * scale_percent / 100)))
                    new_height = max(1, int(round(img.height * scale_percent / 100)))
                    img = img.resize((new_width, new_height), resample=resample)
                # Handle transparency for JPEG
                if output_format == "JPEG" and img.mode in ("RGBA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    background.paste(img, mask=img.split()[3])
                    img = background
                elif output_format == "JPEG" and img.mode != "RGB":
                    img = img.convert("RGB")

                save_kwargs = {}
                if output_format in ("JPEG", "WEBP"):
                    save_kwargs["quality"] = quality
                if output_format in ("PNG", "JPEG"):
                    save_kwargs["optimize"] = True

                img.save(dest, format=output_format, **save_kwargs)

        await asyncio.to_thread(_convert_image)

        self.set_output_value("output_path", str(dest))
        self.set_output_value("files", [str(dest)])
        self.set_output_value("file_count", 1)
        self.set_output_value("format", output_format)
        self.set_output_value("success", True)
        self.status = NodeStatus.SUCCESS

        return {
            "success": True,
            "data": {"output_path": str(dest), "format": output_format},
            "next_nodes": ["exec_out"],
        }

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

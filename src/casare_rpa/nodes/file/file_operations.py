"""
File system operation nodes for CasareRPA.

This module provides core file and directory operations:
- ReadFileNode, WriteFileNode, AppendFileNode, DeleteFileNode
- CopyFileNode, MoveFileNode
- CreateDirectoryNode, ListDirectoryNode, ListFilesNode
- FileExistsNode, GetFileInfoNode, GetFileSizeNode

SECURITY: All file operations are subject to path sandboxing.
"""

import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


class PathSecurityError(Exception):
    """Raised when a path fails security validation."""

    pass


# SECURITY: Default allowed directories for file operations
# Can be customized via environment variable CASARE_ALLOWED_PATHS
_DEFAULT_ALLOWED_PATHS = [
    Path.home() / "Documents",
    Path.home() / "Downloads",
    Path.home() / "Desktop",
    Path.cwd(),  # Current working directory
]

# SECURITY: Paths that should NEVER be accessed
_BLOCKED_PATHS = [
    Path.home() / ".ssh",
    Path.home() / ".gnupg",
    Path.home() / ".aws",
    Path.home() / ".azure",
    Path.home() / ".config",
    Path.home() / "AppData" / "Local" / "Microsoft" / "Credentials",
    Path.home() / "AppData" / "Roaming" / "Microsoft" / "Credentials",
    Path("C:/Windows/System32"),
    Path("C:/Windows/SysWOW64"),
    Path("C:/Program Files"),
    Path("C:/Program Files (x86)"),
]


def validate_path_security(
    path: str | Path,
    operation: str = "access",
    allow_dangerous: bool = False,
) -> Path:
    """Validate that a file path is safe to access.

    SECURITY: This function prevents path traversal attacks and blocks
    access to sensitive system directories.

    Args:
        path: The path to validate
        operation: The operation being performed (for logging)
        allow_dangerous: If True, skip security checks (NOT RECOMMENDED)

    Returns:
        The validated, canonicalized Path object

    Raises:
        PathSecurityError: If the path fails security validation
    """
    if allow_dangerous:
        logger.warning(f"Path security check BYPASSED for {operation}: {path}")
        return Path(path).resolve()

    try:
        # Resolve to absolute path (handles .. and symlinks)
        resolved_path = Path(path).resolve()
    except Exception as e:
        raise PathSecurityError(f"Invalid path '{path}': {e}")

    # SECURITY: Check for blocked paths
    for blocked in _BLOCKED_PATHS:
        try:
            blocked_resolved = blocked.resolve()
            if (
                resolved_path == blocked_resolved
                or blocked_resolved in resolved_path.parents
            ):
                raise PathSecurityError(
                    f"Access to '{resolved_path}' is blocked for security reasons. "
                    f"This path is in a protected system directory."
                )
        except Exception:
            pass  # Blocked path doesn't exist, skip

    # SECURITY: Check original path string for traversal attempts
    path_str = str(path)
    if ".." in path_str:
        raise PathSecurityError(
            f"Path traversal detected in '{path}'. "
            f"Paths containing '..' are not allowed."
        )

    # SECURITY: Check for null bytes (can be used to bypass checks)
    if "\x00" in path_str:
        raise PathSecurityError(
            f"Null byte detected in path '{path}'. "
            f"This is a potential security exploit."
        )

    # SECURITY: Check for special Windows device names
    stem = resolved_path.stem.upper()
    windows_devices = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]
    if stem in windows_devices:
        raise PathSecurityError(f"Access to Windows device '{stem}' is not allowed.")

    # Log the operation for audit
    logger.debug(f"File {operation}: {resolved_path}")

    return resolved_path


def validate_path_security_readonly(
    path: str | Path,
    operation: str = "read",
    allow_dangerous: bool = False,
) -> Path:
    """Validate path for read-only operations with relaxed restrictions.

    SECURITY: Read-only validation allows checking system paths but still
    prevents path traversal and null byte attacks. Blocked paths are logged
    but not rejected since read operations don't modify system state.

    Args:
        path: The path to validate
        operation: The operation being performed (for logging)
        allow_dangerous: If True, skip all validation

    Returns:
        The validated, canonicalized Path object

    Raises:
        PathSecurityError: Only for path traversal or null byte attacks
    """
    if allow_dangerous:
        logger.warning(f"Path security check BYPASSED for {operation}: {path}")
        return Path(path).resolve()

    try:
        # Resolve to absolute path (handles .. and symlinks)
        resolved_path = Path(path).resolve()
    except Exception as e:
        raise PathSecurityError(f"Invalid path '{path}': {e}")

    # SECURITY: Still block path traversal attempts
    path_str = str(path)
    if ".." in path_str:
        raise PathSecurityError(
            f"Path traversal detected in '{path}'. "
            f"Paths containing '..' are not allowed."
        )

    # SECURITY: Still block null bytes
    if "\x00" in path_str:
        raise PathSecurityError(
            f"Null byte detected in path '{path}'. "
            f"This is a potential security exploit."
        )

    # SECURITY: Still block Windows device names
    stem = resolved_path.stem.upper()
    windows_devices = [
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    ]
    if stem in windows_devices:
        raise PathSecurityError(f"Access to Windows device '{stem}' is not allowed.")

    # SECURITY: Log access to blocked paths for audit (but don't prevent)
    for blocked in _BLOCKED_PATHS:
        try:
            blocked_resolved = blocked.resolve()
            if (
                resolved_path == blocked_resolved
                or blocked_resolved in resolved_path.parents
            ):
                logger.warning(
                    f"Read-only access to protected path: {resolved_path} "
                    f"(operation: {operation})"
                )
                break
        except Exception:
            pass

    # Log the operation for audit
    logger.debug(f"File {operation} (read-only): {resolved_path}")

    return resolved_path


@executable_node
@node_schema(
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
class ReadFileNode(BaseNode):
    """
    Read content from a text or binary file.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Read File", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("content", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            file_path = self.get_parameter("file_path")
            encoding = self.get_parameter("encoding", "utf-8")
            binary_mode = self.get_parameter("binary_mode", False)
            errors = self.get_parameter("errors", "strict")
            max_size = self.get_parameter("max_size", 0)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

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

            logger.info(
                f"Reading file: {path} (binary={binary_mode}, encoding={encoding})"
            )

            if binary_mode:
                with open(path, "rb") as f:
                    content = f.read()
            else:
                # Use encoding and errors options for text mode
                with open(path, "r", encoding=encoding, errors=errors) as f:
                    content = f.read()

            self.set_output_value("content", content)
            self.set_output_value("size", size)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "content": content[:100] + "..."
                    if len(str(content)) > 100
                    else content,
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


@node_schema(
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
@executable_node
class WriteFileNode(BaseNode):
    """
    Write content to a file, creating or overwriting.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Write File", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("content", PortType.INPUT, DataType.STRING)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("bytes_written", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
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

            # Resolve {{variable}} patterns in file_path and content
            file_path = context.resolve_value(file_path)
            content = context.resolve_value(content)

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

            if binary_mode:
                if isinstance(content, str):
                    content = content.encode(encoding)
                with open(path, mode) as f:
                    bytes_written = f.write(content)
            else:
                with open(path, mode, encoding=encoding, errors=errors) as f:
                    bytes_written = f.write(str(content) if content else "")

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
            logger.error(f"Security violation in WriteFileNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
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
@executable_node
class AppendFileNode(BaseNode):
    """
    Append content to an existing file.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Append File", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "AppendFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("content", PortType.INPUT, DataType.STRING)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("bytes_written", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            file_path = self.get_parameter("file_path")
            content = self.get_parameter("content")
            encoding = self.get_parameter("encoding", "utf-8")
            create_if_missing = self.get_parameter("create_if_missing", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path and content
            file_path = context.resolve_value(file_path)
            content = context.resolve_value(content)

            # SECURITY: Validate path before any operation
            path = validate_path_security(file_path, "append", allow_dangerous)

            if not path.exists() and not create_if_missing:
                raise FileNotFoundError(f"File not found: {file_path}")

            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "a", encoding=encoding) as f:
                bytes_written = f.write(str(content) if content else "")

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


@node_schema(
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
@executable_node
class DeleteFileNode(BaseNode):
    """
    Delete a file.

    Config (via @node_schema):
        file_path: Path to delete (required)
        ignore_missing: Don't error if file doesn't exist (default: False)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)

    Outputs:
        deleted_path: Path that was deleted
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Delete File", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DeleteFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("deleted_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            file_path = self.get_parameter("file_path")
            ignore_missing = self.get_parameter("ignore_missing", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            # SECURITY: Validate path before delete operation (extra important for delete!)
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


@node_schema(
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
@executable_node
class CopyFileNode(BaseNode):
    """
    Copy a file to a new location.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Copy File", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CopyFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("source_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("dest_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("dest_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("bytes_copied", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            source_path = self.get_parameter("source_path")
            dest_path = self.get_parameter("dest_path")
            overwrite = self.get_parameter("overwrite", False)
            create_dirs = self.get_parameter("create_dirs", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not source_path or not dest_path:
                raise ValueError("source_path and dest_path are required")

            # Resolve {{variable}} patterns in paths
            source_path = context.resolve_value(source_path)
            dest_path = context.resolve_value(dest_path)

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


@node_schema(
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
@executable_node
class MoveFileNode(BaseNode):
    """
    Move or rename a file.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Move File", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MoveFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("source_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("dest_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("dest_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            source_path = self.get_parameter("source_path")
            dest_path = self.get_parameter("dest_path")
            overwrite = self.get_parameter("overwrite", False)
            create_dirs = self.get_parameter("create_dirs", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not source_path or not dest_path:
                raise ValueError("source_path and dest_path are required")

            # Resolve {{variable}} patterns in paths
            source_path = context.resolve_value(source_path)
            dest_path = context.resolve_value(dest_path)

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


@node_schema(
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
@executable_node
class CreateDirectoryNode(BaseNode):
    """
    Create a directory.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Create Directory", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateDirectoryNode"

    def _define_ports(self) -> None:
        self.add_input_port("directory_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("dir_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            dir_path = self.get_parameter("directory_path")
            parents = self.get_parameter("parents", True)
            exist_ok = self.get_parameter("exist_ok", True)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not dir_path:
                raise ValueError("directory_path is required")

            # Resolve {{variable}} patterns in dir_path
            dir_path = context.resolve_value(dir_path)

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

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
    PropertyDef(
        "directory_path",
        PropertyType.STRING,
        required=True,
        label="Directory Path",
        tooltip="Directory to list files from",
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
@executable_node
class ListFilesNode(BaseNode):
    """
    List files in a directory.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "List Files", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("directory_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            dir_path = self.get_parameter("directory_path")
            pattern = self.get_parameter("pattern", "*")
            recursive = self.get_parameter("recursive", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not dir_path:
                raise ValueError("directory_path is required")

            # Resolve {{variable}} patterns in dir_path and pattern
            dir_path = context.resolve_value(dir_path)
            pattern = context.resolve_value(pattern)

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
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(files), "files": files[:10]},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            self.set_output_value("success", False)
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
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
@executable_node
class ListDirectoryNode(BaseNode):
    """
    List files and directories in a folder.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "List Directory", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListDirectoryNode"

    def _define_ports(self) -> None:
        self.add_input_port("dir_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("items", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            dir_path = self.get_parameter("dir_path")
            pattern = self.get_parameter("pattern", "*")
            recursive = self.get_parameter("recursive", False)
            files_only = self.get_parameter("files_only", False)
            dirs_only = self.get_parameter("dirs_only", False)
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not dir_path:
                raise ValueError("dir_path is required")

            # Resolve {{variable}} patterns in dir_path and pattern
            dir_path = context.resolve_value(dir_path)
            pattern = context.resolve_value(pattern)

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

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
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
@executable_node
class FileExistsNode(BaseNode):
    """
    Check if a file or directory exists.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "File Exists", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FileExistsNode"

    def _define_ports(self) -> None:
        self.add_input_port("path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exists", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_file", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_dir", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor (port OR config)
            file_path = self.get_parameter("path")
            check_type = self.get_parameter("check_type", "any")

            if not file_path:
                raise ValueError("path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        check_type = self.config.get("check_type", "any")
        if check_type not in ["file", "directory", "any"]:
            return False, "check_type must be 'file', 'directory', or 'any'"
        return True, ""


@node_schema(
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
@executable_node
class GetFileSizeNode(BaseNode):
    """
    Get the size of a file in bytes.

    Config (via @node_schema):
        file_path: Path to the file (required)
        allow_dangerous_paths: Allow system paths (default: False)

    Inputs:
        file_path: Path override (if connected)

    Outputs:
        size: File size in bytes
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Get File Size", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetFileSizeNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            file_path = self.get_parameter("file_path")
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            # SECURITY: Validate path (read-only)
            path = validate_path_security_readonly(file_path, "stat", allow_dangerous)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            size = path.stat().st_size

            self.set_output_value("size", size)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {"size": size}, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@node_schema(
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
@executable_node
class GetFileInfoNode(BaseNode):
    """
    Get detailed information about a file.

    Config (via @node_schema):
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

    def __init__(self, node_id: str, name: str = "Get File Info", **kwargs) -> None:
        # Config auto-merged by @node_schema decorator
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetFileInfoNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("created", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("modified", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("extension", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("name", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("parent", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # NEW: Unified parameter accessor
            file_path = self.get_parameter("file_path")
            allow_dangerous = self.get_parameter("allow_dangerous_paths", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

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
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

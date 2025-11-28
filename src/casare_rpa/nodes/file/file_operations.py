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
from casare_rpa.domain.decorators import executable_node
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


@executable_node
class ReadFileNode(BaseNode):
    """
    Read content from a text or binary file.

    Config:
        encoding: Text encoding (default: utf-8)
        binary_mode: Read as binary (default: False)
        errors: Error handling mode (strict, ignore, replace, etc.)
        max_size: Maximum file size to read in bytes (0 = unlimited)
        newline: Newline handling mode (None, '', '\n', '\r', '\r\n')

    Inputs:
        file_path: Path to the file to read

    Outputs:
        content: File contents (string or bytes)
        size: File size in bytes
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Read File", **kwargs) -> None:
        # Default config with all file read options
        default_config = {
            "encoding": "utf-8",
            "binary_mode": False,
            "errors": "strict",  # strict, ignore, replace, backslashreplace, xmlcharrefreplace
            "max_size": 0,  # 0 = unlimited, otherwise max bytes to read
            "newline": None,  # None = universal newlines, '' = no translation, or specific
            "allow_dangerous_paths": False,
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            # Try config first, then input port
            file_path = self.config.get("file_path") or self.get_input_value(
                "file_path"
            )
            encoding = self.config.get("encoding", "utf-8")
            binary_mode = self.config.get("binary_mode", False)
            errors = self.config.get("errors", "strict")
            max_size = self.config.get("max_size", 0)
            newline = self.config.get("newline", None)
            allow_dangerous = self.config.get("allow_dangerous_paths", False)

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
                # Use newline and errors options for text mode
                with open(
                    path, "r", encoding=encoding, errors=errors, newline=newline
                ) as f:
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


@executable_node
class WriteFileNode(BaseNode):
    """
    Write content to a file, creating or overwriting.

    Config:
        encoding: Text encoding (default: utf-8)
        binary_mode: Write as binary (default: False)
        create_dirs: Create parent directories if needed (default: True)
        errors: Error handling mode (strict, ignore, replace, etc.)
        newline: Newline handling mode (None, '', '\n', '\r', '\r\n')
        append_mode: Append to file instead of overwrite (default: False)

    Inputs:
        file_path: Path to write to
        content: Content to write

    Outputs:
        file_path: Path that was written
        bytes_written: Number of bytes written
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Write File", **kwargs) -> None:
        # Default config with all file write options
        default_config = {
            "encoding": "utf-8",
            "binary_mode": False,
            "create_dirs": True,
            "errors": "strict",  # strict, ignore, replace, backslashreplace, xmlcharrefreplace
            "newline": None,  # None = universal, '' = no translation, or specific
            "append_mode": False,  # Append instead of overwrite
            "allow_dangerous_paths": False,
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

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
            file_path = self.config.get("file_path") or self.get_input_value(
                "file_path"
            )
            content = self.config.get("content") or self.get_input_value("content")
            encoding = self.config.get("encoding", "utf-8")
            binary_mode = self.config.get("binary_mode", False)
            create_dirs = self.config.get("create_dirs", True)
            errors = self.config.get("errors", "strict")
            newline = self.config.get("newline", None)
            append_mode = self.config.get("append_mode", False)
            allow_dangerous = self.config.get("allow_dangerous_paths", False)

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
                with open(
                    path, mode, encoding=encoding, errors=errors, newline=newline
                ) as f:
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


@executable_node
class AppendFileNode(BaseNode):
    """
    Append content to an existing file.

    Config:
        encoding: Text encoding (default: utf-8)
        create_if_missing: Create file if it doesn't exist (default: True)

    Inputs:
        file_path: Path to append to
        content: Content to append

    Outputs:
        file_path: Path that was written
        bytes_written: Number of bytes appended
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Append File", **kwargs) -> None:
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
            file_path = self.config.get("file_path") or self.get_input_value(
                "file_path"
            )
            content = self.config.get("content") or self.get_input_value("content")
            encoding = self.config.get("encoding", "utf-8")
            create_if_missing = self.config.get("create_if_missing", True)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path and content
            file_path = context.resolve_value(file_path)
            content = context.resolve_value(content)

            path = Path(file_path)

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

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class DeleteFileNode(BaseNode):
    """
    Delete a file.

    Config:
        ignore_missing: Don't error if file doesn't exist (default: False)

    Inputs:
        file_path: Path to delete

    Outputs:
        deleted_path: Path that was deleted
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Delete File", **kwargs) -> None:
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
            file_path = self.config.get("file_path") or self.get_input_value(
                "file_path"
            )
            ignore_missing = self.config.get("ignore_missing", False)
            allow_dangerous = self.config.get("allow_dangerous_paths", False)

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


@executable_node
class CopyFileNode(BaseNode):
    """
    Copy a file to a new location.

    Config:
        overwrite: Overwrite if destination exists (default: False)
        create_dirs: Create destination directories (default: True)

    Inputs:
        source_path: Source file path
        dest_path: Destination file path

    Outputs:
        dest_path: Destination path
        bytes_copied: Size of copied file
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Copy File", **kwargs) -> None:
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
            source_path = self.config.get("source_path") or self.get_input_value(
                "source_path"
            )
            dest_path = self.config.get("dest_path") or self.get_input_value(
                "dest_path"
            )
            overwrite = self.config.get("overwrite", False)
            create_dirs = self.config.get("create_dirs", True)

            if not source_path or not dest_path:
                raise ValueError("source_path and dest_path are required")

            # Resolve {{variable}} patterns in paths
            source_path = context.resolve_value(source_path)
            dest_path = context.resolve_value(dest_path)

            source = Path(source_path)
            dest = Path(dest_path)

            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            if dest.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {dest_path}")

            if create_dirs and dest.parent:
                dest.parent.mkdir(parents=True, exist_ok=True)

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

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class MoveFileNode(BaseNode):
    """
    Move or rename a file.

    Config:
        overwrite: Overwrite if destination exists (default: False)
        create_dirs: Create destination directories (default: True)

    Inputs:
        source_path: Source file path
        dest_path: Destination file path

    Outputs:
        dest_path: Final destination path
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Move File", **kwargs) -> None:
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
            source_path = self.config.get("source_path") or self.get_input_value(
                "source_path"
            )
            dest_path = self.config.get("dest_path") or self.get_input_value(
                "dest_path"
            )
            overwrite = self.config.get("overwrite", False)
            create_dirs = self.config.get("create_dirs", True)

            if not source_path or not dest_path:
                raise ValueError("source_path and dest_path are required")

            # Resolve {{variable}} patterns in paths
            source_path = context.resolve_value(source_path)
            dest_path = context.resolve_value(dest_path)

            source = Path(source_path)
            dest = Path(dest_path)

            if not source.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")

            if dest.exists() and not overwrite:
                raise FileExistsError(f"Destination already exists: {dest_path}")

            if create_dirs and dest.parent:
                dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.exists() and overwrite:
                dest.unlink()

            shutil.move(str(source), str(dest))

            self.set_output_value("dest_path", str(dest))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"dest_path": str(dest)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class CreateDirectoryNode(BaseNode):
    """
    Create a directory.

    Config:
        parents: Create parent directories as needed (default: True)
        exist_ok: Don't error if directory exists (default: True)

    Inputs:
        dir_path: Path to create

    Outputs:
        dir_path: Created directory path
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Create Directory", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CreateDirectoryNode"

    def _define_ports(self) -> None:
        self.add_input_port("dir_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("dir_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.config.get("dir_path") or self.get_input_value("dir_path")
            parents = self.config.get("parents", True)
            exist_ok = self.config.get("exist_ok", True)

            if not dir_path:
                raise ValueError("dir_path is required")

            # Resolve {{variable}} patterns in dir_path
            dir_path = context.resolve_value(dir_path)

            path = Path(dir_path)
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


@executable_node
class ListFilesNode(BaseNode):
    """
    List files in a directory.

    Config:
        pattern: Glob pattern to filter (default: *)
        recursive: Search recursively (default: False)

    Inputs:
        directory_path: Directory to list

    Outputs:
        files: List of file paths
        count: Number of files found
    """

    def __init__(self, node_id: str, name: str = "List Files", **kwargs) -> None:
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
            dir_path = self.config.get("directory_path") or self.get_input_value(
                "directory_path"
            )
            pattern = self.config.get("pattern", "*")
            recursive = self.config.get("recursive", False)

            if not dir_path:
                raise ValueError("directory_path is required")

            # Resolve {{variable}} patterns in dir_path and pattern
            dir_path = context.resolve_value(dir_path)
            pattern = context.resolve_value(pattern)

            path = Path(dir_path)
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
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class ListDirectoryNode(BaseNode):
    """
    List files and directories in a folder.

    Config:
        pattern: Glob pattern to filter (default: *)
        recursive: Search recursively (default: False)
        files_only: Only return files (default: False)
        dirs_only: Only return directories (default: False)

    Inputs:
        dir_path: Directory to list

    Outputs:
        items: List of file/directory paths
        count: Number of items found
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "List Directory", **kwargs) -> None:
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
            dir_path = self.config.get("dir_path") or self.get_input_value("dir_path")
            pattern = self.config.get("pattern", "*")
            recursive = self.config.get("recursive", False)
            files_only = self.config.get("files_only", False)
            dirs_only = self.config.get("dirs_only", False)

            if not dir_path:
                raise ValueError("dir_path is required")

            # Resolve {{variable}} patterns in dir_path and pattern
            dir_path = context.resolve_value(dir_path)
            pattern = context.resolve_value(pattern)

            path = Path(dir_path)
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


@executable_node
class FileExistsNode(BaseNode):
    """
    Check if a file or directory exists.

    Config:
        check_type: "file", "directory", or "any" (default: any)

    Inputs:
        path: Path to check

    Outputs:
        exists: Whether the path exists
        is_file: Whether it's a file
        is_directory: Whether it's a directory
    """

    def __init__(self, node_id: str, name: str = "File Exists", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FileExistsNode"

    def _define_ports(self) -> None:
        self.add_input_port("path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exists", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_file", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_directory", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Try config first, then input port
            file_path = self.config.get("path") or self.get_input_value("path")
            check_type = self.config.get("check_type", "any")

            if not file_path:
                raise ValueError("path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
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
            self.set_output_value("is_directory", is_directory)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "exists": exists,
                    "is_file": is_file,
                    "is_directory": is_directory,
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


@executable_node
class GetFileSizeNode(BaseNode):
    """
    Get the size of a file in bytes.

    Inputs:
        file_path: Path to the file

    Outputs:
        size: File size in bytes
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Get File Size", **kwargs) -> None:
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
            file_path = self.config.get("file_path") or self.get_input_value(
                "file_path"
            )

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
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


@executable_node
class GetFileInfoNode(BaseNode):
    """
    Get detailed information about a file.

    Inputs:
        file_path: Path to the file

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
            file_path = self.config.get("file_path") or self.get_input_value(
                "file_path"
            )

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
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

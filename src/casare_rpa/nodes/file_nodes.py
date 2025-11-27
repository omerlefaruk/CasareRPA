"""
File system operation nodes for CasareRPA.

This module provides nodes for file and directory operations:
- ReadFileNode, WriteFileNode, AppendFileNode, DeleteFileNode
- CopyFileNode, MoveFileNode, CreateDirectoryNode, ListDirectoryNode
- FileExistsNode, GetFileInfoNode
- ReadCSVNode, WriteCSVNode, ReadJSONFileNode, WriteJSONFileNode
- ZipFilesNode

SECURITY: All file operations are subject to path sandboxing.
"""

import csv
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger

from ..core.base_node import BaseNode
from ..core.types import NodeStatus, PortType, DataType, ExecutionResult
from ..core.execution_context import ExecutionContext


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
            if resolved_path == blocked_resolved or blocked_resolved in resolved_path.parents:
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
    windows_devices = ["CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4",
                       "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2",
                       "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]
    if stem in windows_devices:
        raise PathSecurityError(
            f"Access to Windows device '{stem}' is not allowed."
        )

    # Log the operation for audit
    logger.debug(f"File {operation}: {resolved_path}")

    return resolved_path


def validate_zip_entry(zip_path: str, entry_name: str) -> Path:
    """Validate a zip entry name to prevent Zip Slip attacks.

    SECURITY: Prevents path traversal via malicious zip entries.

    Args:
        zip_path: The path where files will be extracted
        entry_name: The name of the entry in the zip file

    Returns:
        The validated target path

    Raises:
        PathSecurityError: If the entry would escape the target directory
    """
    target_dir = Path(zip_path).resolve()
    target_path = (target_dir / entry_name).resolve()

    # SECURITY: Ensure the target path is within the target directory
    if not str(target_path).startswith(str(target_dir)):
        raise PathSecurityError(
            f"Zip Slip attack detected! Entry '{entry_name}' would extract "
            f"outside the target directory. This is a security vulnerability."
        )

    return target_path


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("content", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
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
                raise ValueError(f"File size ({size} bytes) exceeds max_size limit ({max_size} bytes)")

            logger.info(f"Reading file: {path} (binary={binary_mode}, encoding={encoding})")

            if binary_mode:
                with open(path, "rb") as f:
                    content = f.read()
            else:
                # Use newline and errors options for text mode
                with open(path, "r", encoding=encoding, errors=errors, newline=newline) as f:
                    content = f.read()

            self.set_output_value("content", content)
            self.set_output_value("size", size)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"content": content[:100] + "..." if len(str(content)) > 100 else content, "size": size},
                "next_nodes": ["exec_out"]
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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("content", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("bytes_written", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
            content = self.get_input_value("content", context)
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
                with open(path, mode, encoding=encoding, errors=errors, newline=newline) as f:
                    bytes_written = f.write(str(content) if content else "")

            self.set_output_value("file_path", str(path))
            self.set_output_value("bytes_written", bytes_written)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path), "bytes_written": bytes_written},
                "next_nodes": ["exec_out"]
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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("content", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("bytes_written", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
            content = self.get_input_value("content", context)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("deleted_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
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
                        "data": {"deleted_path": str(path), "message": "File did not exist"},
                        "next_nodes": ["exec_out"]
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
                "next_nodes": ["exec_out"]
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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("source_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("dest_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("dest_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("bytes_copied", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            source_path = self.get_input_value("source_path", context)
            dest_path = self.get_input_value("dest_path", context)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("source_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("dest_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("dest_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            source_path = self.get_input_value("source_path", context)
            dest_path = self.get_input_value("dest_path", context)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("dir_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("dir_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.get_input_value("dir_path", context)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("directory_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.get_input_value("directory_path", context)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("dir_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("items", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            dir_path = self.get_input_value("dir_path", context)
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
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("exists", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_file", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("is_directory", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("path", context)
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
                "data": {"exists": exists, "is_file": is_file, "is_directory": is_directory},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        check_type = self.config.get("check_type", "any")
        if check_type not in ["file", "directory", "any"]:
            return False, "check_type must be 'file', 'directory', or 'any'"
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("size", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)

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

            return {
                "success": True,
                "data": {"size": size},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


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
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
            file_path = self.get_input_value("file_path", context)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
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
                "data": {
                    "name": path.name,
                    "size": stat.st_size,
                    "extension": path.suffix
                },
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class ReadCSVNode(BaseNode):
    """
    Read and parse a CSV file.

    Config:
        delimiter: Field delimiter (default: ,)
        has_header: First row is header (default: True)
        encoding: File encoding (default: utf-8)
        quotechar: Character for quoting fields (default: ")
        skip_rows: Number of initial rows to skip (default: 0)
        max_rows: Maximum rows to read, 0 = unlimited (default: 0)
        strict: Strict mode - error on malformed rows (default: False)

    Inputs:
        file_path: Path to CSV file

    Outputs:
        data: List of rows (dicts if has_header, else lists)
        headers: Column headers (if has_header)
        row_count: Number of rows
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Read CSV", **kwargs) -> None:
        # Default config with all CSV read options
        default_config = {
            "delimiter": ",",
            "has_header": True,
            "encoding": "utf-8",
            "quotechar": '"',
            "skip_rows": 0,  # Number of initial rows to skip
            "max_rows": 0,  # Maximum rows to read, 0 = unlimited
            "strict": False,  # Error on malformed rows
            "doublequote": True,  # Whether to interpret "" as escaped "
            "escapechar": None,  # Character to escape special chars
        }

        config = kwargs.get("config", {})
        # Merge with defaults
        for key, value in default_config.items():
            if key not in config:
                config[key] = value

        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadCSVNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("data", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("headers", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
            delimiter = self.config.get("delimiter", ",")
            has_header = self.config.get("has_header", True)
            encoding = self.config.get("encoding", "utf-8")
            quotechar = self.config.get("quotechar", '"')
            skip_rows = self.config.get("skip_rows", 0)
            max_rows = self.config.get("max_rows", 0)
            strict = self.config.get("strict", False)
            doublequote = self.config.get("doublequote", True)
            escapechar = self.config.get("escapechar", None)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"CSV file not found: {file_path}")

            data = []
            headers = []

            logger.info(f"Reading CSV: {path} (delimiter='{delimiter}', has_header={has_header})")

            with open(path, "r", encoding=encoding, newline="") as f:
                # Build CSV reader options
                csv_options = {
                    "delimiter": delimiter,
                    "quotechar": quotechar,
                    "doublequote": doublequote,
                    "strict": strict,
                }
                if escapechar:
                    csv_options["escapechar"] = escapechar

                # Skip initial rows if configured
                for _ in range(skip_rows):
                    next(f, None)

                if has_header:
                    reader = csv.DictReader(f, **csv_options)
                    headers = reader.fieldnames or []

                    # Read data with optional max_rows limit
                    if max_rows > 0:
                        for i, row in enumerate(reader):
                            if i >= max_rows:
                                break
                            data.append(row)
                    else:
                        data = list(reader)
                else:
                    reader = csv.reader(f, **csv_options)

                    # Read data with optional max_rows limit
                    if max_rows > 0:
                        for i, row in enumerate(reader):
                            if i >= max_rows:
                                break
                            data.append(row)
                    else:
                        data = list(reader)

            self.set_output_value("data", data)
            self.set_output_value("headers", headers)
            self.set_output_value("row_count", len(data))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            logger.info(f"CSV read successfully: {len(data)} rows, {len(headers)} columns")

            return {
                "success": True,
                "data": {"row_count": len(data), "headers": headers},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class WriteCSVNode(BaseNode):
    """
    Write data to a CSV file.

    Config:
        delimiter: Field delimiter (default: ,)
        write_header: Write header row (default: True)
        encoding: File encoding (default: utf-8)

    Inputs:
        file_path: Path to write
        data: List of rows (dicts or lists)
        headers: Column headers (optional if data is dicts)

    Outputs:
        file_path: Written file path
        row_count: Number of rows written
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Write CSV", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteCSVNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("data", PortType.INPUT, DataType.LIST)
        self.add_input_port("headers", PortType.INPUT, DataType.LIST)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
            data = self.get_input_value("data", context) or []
            headers = self.get_input_value("headers", context)
            delimiter = self.config.get("delimiter", ",")
            write_header = self.config.get("write_header", True)
            encoding = self.config.get("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            row_count = 0

            with open(path, "w", encoding=encoding, newline="") as f:
                if data and isinstance(data[0], dict):
                    # Dict data
                    fieldnames = headers or (list(data[0].keys()) if data else [])
                    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                    if write_header:
                        writer.writeheader()
                    writer.writerows(data)
                    row_count = len(data)
                else:
                    # List data
                    writer = csv.writer(f, delimiter=delimiter)
                    if write_header and headers:
                        writer.writerow(headers)
                    writer.writerows(data)
                    row_count = len(data)

            self.set_output_value("file_path", str(path))
            self.set_output_value("row_count", row_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path), "row_count": row_count},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class ReadJSONFileNode(BaseNode):
    """
    Read and parse a JSON file.

    Config:
        encoding: File encoding (default: utf-8)

    Inputs:
        file_path: Path to JSON file

    Outputs:
        data: Parsed JSON data
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Read JSON File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ReadJSONFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("data", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
            encoding = self.config.get("encoding", "utf-8")

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"JSON file not found: {file_path}")

            with open(path, "r", encoding=encoding) as f:
                data = json.load(f)

            self.set_output_value("data", data)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"type": type(data).__name__},
                "next_nodes": ["exec_out"]
            }

        except json.JSONDecodeError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": f"Invalid JSON: {e}", "next_nodes": []}
        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class WriteJSONFileNode(BaseNode):
    """
    Write data to a JSON file.

    Config:
        encoding: File encoding (default: utf-8)
        indent: Indentation level (default: 2)
        ensure_ascii: Escape non-ASCII (default: False)

    Inputs:
        file_path: Path to write
        data: Data to serialize as JSON

    Outputs:
        file_path: Written file path
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Write JSON File", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WriteJSONFileNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("file_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("data", PortType.INPUT, DataType.ANY)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("file_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            file_path = self.get_input_value("file_path", context)
            data = self.get_input_value("data", context)
            encoding = self.config.get("encoding", "utf-8")
            indent = self.config.get("indent", 2)
            ensure_ascii = self.config.get("ensure_ascii", False)

            if not file_path:
                raise ValueError("file_path is required")

            # Resolve {{variable}} patterns in file_path
            file_path = context.resolve_value(file_path)

            path = Path(file_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, "w", encoding=encoding) as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)

            self.set_output_value("file_path", str(path))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": str(path)},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


class ZipFilesNode(BaseNode):
    """
    Create a ZIP archive from files.

    Config:
        compression: ZIP_STORED or ZIP_DEFLATED (default: ZIP_DEFLATED)

    Inputs:
        zip_path: Path for the ZIP file to create
        files: List of file paths to include
        base_dir: Base directory for relative paths (optional)

    Outputs:
        zip_path: Created ZIP file path
        file_count: Number of files added
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Zip Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ZipFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("zip_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("files", PortType.INPUT, DataType.LIST)
        self.add_input_port("base_dir", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("zip_path", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("file_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            zip_path = self.get_input_value("zip_path", context)
            files = self.get_input_value("files", context) or []
            base_dir = self.get_input_value("base_dir", context)
            compression = self.config.get("compression", "ZIP_DEFLATED")

            if not zip_path:
                raise ValueError("zip_path is required")

            # Resolve {{variable}} patterns in zip_path and base_dir
            zip_path = context.resolve_value(zip_path)
            if base_dir:
                base_dir = context.resolve_value(base_dir)

            if not files:
                raise ValueError("files list is required")

            zip_compression = (
                zipfile.ZIP_DEFLATED if compression == "ZIP_DEFLATED"
                else zipfile.ZIP_STORED
            )

            path = Path(zip_path)
            if path.parent:
                path.parent.mkdir(parents=True, exist_ok=True)

            file_count = 0
            base = Path(base_dir) if base_dir else None

            with zipfile.ZipFile(path, "w", compression=zip_compression) as zf:
                for file_path in files:
                    fp = Path(file_path)
                    if not fp.exists():
                        continue

                    if base and fp.is_relative_to(base):
                        arcname = str(fp.relative_to(base))
                    else:
                        arcname = fp.name

                    zf.write(fp, arcname)
                    file_count += 1

            self.set_output_value("zip_path", str(path))
            self.set_output_value("file_count", file_count)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"zip_path": str(path), "file_count": file_count},
                "next_nodes": ["exec_out"]
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        compression = self.config.get("compression", "ZIP_DEFLATED")
        if compression not in ["ZIP_STORED", "ZIP_DEFLATED"]:
            return False, "compression must be 'ZIP_STORED' or 'ZIP_DEFLATED'"
        return True, ""


class UnzipFilesNode(BaseNode):
    """
    Extract files from a ZIP archive.

    Config:
        None

    Inputs:
        zip_path: Path to ZIP file
        extract_to: Directory to extract to

    Outputs:
        extract_to: Extraction directory
        files: List of extracted file paths
        file_count: Number of files extracted
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Unzip Files", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "UnzipFilesNode"

    def _define_ports(self) -> None:
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("zip_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("extract_to", PortType.INPUT, DataType.STRING)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("extract_to", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("files", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("file_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            zip_path = self.get_input_value("zip_path", context)
            extract_to = self.get_input_value("extract_to", context)
            allow_dangerous = self.config.get("allow_dangerous_paths", False)

            if not zip_path:
                raise ValueError("zip_path is required")
            if not extract_to:
                raise ValueError("extract_to is required")

            # Resolve {{variable}} patterns in zip_path and extract_to
            zip_path = context.resolve_value(zip_path)
            extract_to = context.resolve_value(extract_to)

            # SECURITY: Validate paths
            zip_file = validate_path_security(zip_path, "read", allow_dangerous)
            dest = validate_path_security(extract_to, "write", allow_dangerous)

            if not zip_file.exists():
                raise FileNotFoundError(f"ZIP file not found: {zip_path}")

            dest.mkdir(parents=True, exist_ok=True)

            extracted_files = []

            with zipfile.ZipFile(zip_file, "r") as zf:
                # SECURITY: Do NOT use extractall() - vulnerable to Zip Slip!
                # Instead, validate each entry and extract manually
                for member in zf.namelist():
                    # SECURITY: Validate entry path to prevent Zip Slip
                    target_path = validate_zip_entry(str(dest), member)

                    # Extract the file safely
                    if member.endswith('/'):
                        # Directory entry
                        target_path.mkdir(parents=True, exist_ok=True)
                    else:
                        # File entry - ensure parent directory exists
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as source, open(target_path, 'wb') as target:
                            target.write(source.read())

                    extracted_files.append(str(target_path))

            logger.info(f"Extracted {len(extracted_files)} files to {dest}")

            self.set_output_value("extract_to", str(dest))
            self.set_output_value("files", extracted_files)
            self.set_output_value("file_count", len(extracted_files))
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"extract_to": str(dest), "file_count": len(extracted_files)},
                "next_nodes": ["exec_out"]
            }

        except PathSecurityError as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            logger.error(f"Security violation in UnzipFilesNode: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""

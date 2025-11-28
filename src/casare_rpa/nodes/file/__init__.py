"""
File operation nodes for CasareRPA.

This package provides file system and structured data operations:

File Operations (file_operations.py):
- ReadFileNode, WriteFileNode, AppendFileNode, DeleteFileNode
- CopyFileNode, MoveFileNode
- CreateDirectoryNode, ListDirectoryNode, ListFilesNode
- FileExistsNode, GetFileInfoNode, GetFileSizeNode

Structured Data (structured_data.py):
- ReadCSVNode, WriteCSVNode
- ReadJSONFileNode, WriteJSONFileNode
- ZipFilesNode, UnzipFilesNode

Security utilities:
- PathSecurityError, validate_path_security, validate_zip_entry

Usage:
    from casare_rpa.nodes.file import ReadFileNode, ReadCSVNode
    from casare_rpa.nodes.file.file_operations import WriteFileNode
    from casare_rpa.nodes.file.structured_data import ZipFilesNode
"""

# File operations
from .file_operations import (
    PathSecurityError,
    validate_path_security,
    ReadFileNode,
    WriteFileNode,
    AppendFileNode,
    DeleteFileNode,
    CopyFileNode,
    MoveFileNode,
    CreateDirectoryNode,
    ListFilesNode,
    ListDirectoryNode,
    FileExistsNode,
    GetFileSizeNode,
    GetFileInfoNode,
)

# Structured data operations
from .structured_data import (
    validate_zip_entry,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    ZipFilesNode,
    UnzipFilesNode,
)

__all__ = [
    # Security utilities
    "PathSecurityError",
    "validate_path_security",
    "validate_zip_entry",
    # File operations
    "ReadFileNode",
    "WriteFileNode",
    "AppendFileNode",
    "DeleteFileNode",
    "CopyFileNode",
    "MoveFileNode",
    "CreateDirectoryNode",
    "ListFilesNode",
    "ListDirectoryNode",
    "FileExistsNode",
    "GetFileSizeNode",
    "GetFileInfoNode",
    # Structured data
    "ReadCSVNode",
    "WriteCSVNode",
    "ReadJSONFileNode",
    "WriteJSONFileNode",
    "ZipFilesNode",
    "UnzipFilesNode",
]

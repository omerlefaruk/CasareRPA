"""
File operation nodes for CasareRPA.

This package provides file system and structured data operations:

File Security (file_security.py):
- PathSecurityError, validate_path_security, validate_path_security_readonly

File Read (file_read_nodes.py):
- ReadFileNode

File Write (file_write_nodes.py):
- WriteFileNode, AppendFileNode

File System (file_system_nodes.py):
- DeleteFileNode, CopyFileNode, MoveFileNode

Directory (directory_nodes.py):
- CreateDirectoryNode, ListDirectoryNode, ListFilesNode

Path Info (path_nodes.py):
- FileExistsNode, GetFileInfoNode, GetFileSizeNode

Structured Data (structured_data.py):
- ReadCSVNode, WriteCSVNode
- ReadJSONFileNode, WriteJSONFileNode
- ZipFilesNode, UnzipFilesNode

Usage:
    from casare_rpa.nodes.file import ReadFileNode, ReadCSVNode
    from casare_rpa.nodes.file.file_write_nodes import WriteFileNode
    from casare_rpa.nodes.file.structured_data import ZipFilesNode
"""

# Super Nodes (consolidated operations)
# Directory operations
from casare_rpa.nodes.file.directory_nodes import (
    CreateDirectoryNode,
    ListDirectoryNode,
    ListFilesNode,
)

# File read operations
from casare_rpa.nodes.file.file_read_nodes import ReadFileNode

# Security utilities
from casare_rpa.nodes.file.file_security import (
    PathSecurityError,
    validate_path_security,
    validate_path_security_readonly,
)

# File system operations
from casare_rpa.nodes.file.file_system_nodes import (
    CopyFileNode,
    DeleteFileNode,
    MoveFileNode,
)

# File write operations
from casare_rpa.nodes.file.file_write_nodes import (
    AppendFileNode,
    WriteFileNode,
)

# Image operations
from casare_rpa.nodes.file.image_nodes import ImageConvertNode

# Path info operations
from casare_rpa.nodes.file.path_nodes import (
    FileExistsNode,
    GetFileInfoNode,
    GetFileSizeNode,
)

# Structured data operations
from casare_rpa.nodes.file.structured_data import (
    ReadCSVNode,
    ReadJSONFileNode,
    UnzipFilesNode,
    WriteCSVNode,
    WriteJSONFileNode,
    ZipFilesNode,
    validate_zip_entry,
)
from casare_rpa.nodes.file.super_node import (
    FILE_SYSTEM_PORT_SCHEMA,
    STRUCTURED_DATA_PORT_SCHEMA,
    FileSystemAction,
    FileSystemSuperNode,
    StructuredDataAction,
    StructuredDataSuperNode,
)

__all__ = [
    # Super Nodes (consolidated operations)
    "FileSystemSuperNode",
    "FileSystemAction",
    "FILE_SYSTEM_PORT_SCHEMA",
    "StructuredDataSuperNode",
    "StructuredDataAction",
    "STRUCTURED_DATA_PORT_SCHEMA",
    # Security utilities
    "PathSecurityError",
    "validate_path_security",
    "validate_path_security_readonly",
    "validate_zip_entry",
    # File read operations
    "ReadFileNode",
    # File write operations
    "WriteFileNode",
    "AppendFileNode",
    # File system operations
    "DeleteFileNode",
    "CopyFileNode",
    "MoveFileNode",
    # Directory operations
    "CreateDirectoryNode",
    "ListFilesNode",
    "ListDirectoryNode",
    # Path info operations
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
    # Image operations
    "ImageConvertNode",
]

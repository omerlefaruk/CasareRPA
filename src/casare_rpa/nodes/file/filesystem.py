"""
FileSystemSuperNode Re-export Module.

This module re-exports the FileSystemSuperNode and related constants
from the consolidated super_node.py file.

Usage:
    from casare_rpa.nodes.file.filesystem import FileSystemSuperNode, FileSystemAction
"""

from casare_rpa.domain.decorators import node, properties

from casare_rpa.nodes.file.super_node import (
    FileSystemAction,
    FileSystemSuperNode,
    FILE_SYSTEM_PORT_SCHEMA,
    FILE_PATH_ACTIONS,
    DUAL_PATH_ACTIONS,
    DIRECTORY_PATH_ACTIONS,
    CONTENT_ACTIONS,
)

__all__ = [
    "FileSystemAction",
    "FileSystemSuperNode",
    "FILE_SYSTEM_PORT_SCHEMA",
    "FILE_PATH_ACTIONS",
    "DUAL_PATH_ACTIONS",
    "DIRECTORY_PATH_ACTIONS",
    "CONTENT_ACTIONS",
]

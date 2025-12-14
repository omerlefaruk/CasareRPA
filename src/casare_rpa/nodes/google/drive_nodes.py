"""
CasareRPA - Google Drive Nodes (Compatibility Module)

This module re-exports Drive nodes from the drive/ subpackage
for backward compatibility with existing imports in google/__init__.py.
"""

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult
from casare_rpa.infrastructure.execution import ExecutionContext

# Import implemented nodes from drive/ subpackage
from casare_rpa.nodes.google.google_base import DriveBaseNode
from casare_rpa.nodes.google.drive.drive_files import (
    DriveBatchDownloadNode,
    DriveCopyFileNode,
    DriveDeleteFileNode,
    DriveDownloadFileNode,
    DriveDownloadFolderNode,
    DriveExportFileNode,
    DriveGetFileNode,
    DriveMoveFileNode,
    DriveRenameFileNode,
    DriveUploadFileNode,
)
from casare_rpa.nodes.google.drive.drive_folders import (
    DriveCreateFolderNode,
    DriveListFilesNode,
    DriveSearchFilesNode,
)
from casare_rpa.nodes.google.drive.drive_share import (
    DriveCreateShareLinkNode,
    DriveGetPermissionsNode,
    DriveRemoveShareNode,
    DriveShareFileNode,
)
from casare_rpa.nodes.google.drive.drive_batch import (
    DriveBatchCopyNode,
    DriveBatchDeleteNode,
    DriveBatchMoveNode,
)

# Alias for backward compatibility
DriveRemovePermissionNode = DriveRemoveShareNode


__all__ = [
    # Base
    "DriveBaseNode",
    # File operations - Single file
    "DriveUploadFileNode",
    "DriveDownloadFileNode",
    "DriveCopyFileNode",
    "DriveMoveFileNode",
    "DriveDeleteFileNode",
    "DriveRenameFileNode",
    "DriveGetFileNode",
    # File operations - Bulk download
    "DriveDownloadFolderNode",
    "DriveBatchDownloadNode",
    # Folder operations
    "DriveCreateFolderNode",
    "DriveListFilesNode",
    "DriveSearchFilesNode",
    # Sharing operations
    "DriveShareFileNode",
    "DriveRemoveShareNode",
    "DriveRemovePermissionNode",
    "DriveGetPermissionsNode",
    "DriveCreateShareLinkNode",
    # Export
    "DriveExportFileNode",
    # Batch operations
    "DriveBatchDeleteNode",
    "DriveBatchMoveNode",
    "DriveBatchCopyNode",
]

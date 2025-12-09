"""
CasareRPA - Google Drive Nodes (Compatibility Module)

This module re-exports Drive nodes from the drive/ subpackage
for backward compatibility with existing imports in google/__init__.py.
"""

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, ExecutionResult, PortType
from casare_rpa.infrastructure.execution import ExecutionContext

# Import implemented nodes from drive/ subpackage
from casare_rpa.nodes.google.google_base import DriveBaseNode
from casare_rpa.nodes.google.drive.drive_files import (
    DriveCopyFileNode,
    DriveDeleteFileNode,
    DriveDownloadFileNode,
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


# ============================================================================
# Placeholder nodes for future implementation
# ============================================================================


class _NotImplementedDriveNode(BaseNode):
    """Base class for not-yet-implemented Drive nodes."""

    # @category: google
    # @requires: none
    # @ports: none -> success, error

    NODE_CATEGORY = "google_drive"

    def __init__(self, node_id: str, **kwargs):
        super().__init__(node_id, kwargs.get("config", {}))

    def _define_ports(self) -> None:
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        return {
            "success": False,
            "error": f"{self.__class__.__name__} is not yet implemented",
            "next_nodes": [],
        }


class DriveExportFileNode(_NotImplementedDriveNode):
    """Placeholder: Export a Google Workspace file to a standard format."""

    # @category: google
    # @requires: none
    # @ports: none -> none

    NODE_TYPE = "drive_export_file"
    NODE_DISPLAY_NAME = "Drive: Export File"


__all__ = [
    # Base
    "DriveBaseNode",
    # File operations
    "DriveUploadFileNode",
    "DriveDownloadFileNode",
    "DriveCopyFileNode",
    "DriveMoveFileNode",
    "DriveDeleteFileNode",
    "DriveRenameFileNode",
    "DriveGetFileNode",
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
    # Export (placeholder)
    "DriveExportFileNode",
    # Batch operations
    "DriveBatchDeleteNode",
    "DriveBatchMoveNode",
    "DriveBatchCopyNode",
]

"""
CasareRPA - Google Drive Nodes

Nodes for file and folder operations with Google Drive API v3.
"""

from casare_rpa.nodes.google.google_base import DriveBaseNode
from casare_rpa.nodes.google.drive.drive_files import (
    DriveUploadFileNode,
    DriveDownloadFileNode,
    DriveDownloadFolderNode,
    DriveBatchDownloadNode,
    DriveCopyFileNode,
    DriveMoveFileNode,
    DriveDeleteFileNode,
    DriveRenameFileNode,
    DriveGetFileNode,
)
from casare_rpa.nodes.google.drive.drive_folders import (
    DriveCreateFolderNode,
    DriveListFilesNode,
    DriveSearchFilesNode,
)

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
]

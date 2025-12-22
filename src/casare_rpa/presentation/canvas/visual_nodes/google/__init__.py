"""
Visual nodes for Google Workspace category.

Provides visual node representations for:
- Gmail: Email operations
- Sheets: Spreadsheet operations
- Drive: File storage operations
"""

# Calendar nodes removed - see Calendar/Docs cleanup 2025

from casare_rpa.presentation.canvas.visual_nodes.google.gmail_nodes import (
    # Send operations
    VisualGmailSendEmailNode,
    VisualGmailSendWithAttachmentNode,
    VisualGmailReplyToEmailNode,
    VisualGmailForwardEmailNode,
    VisualGmailCreateDraftNode,
    VisualGmailSendDraftNode,
    # Read operations
    VisualGmailGetEmailNode,
    VisualGmailListEmailsNode,
    VisualGmailSearchEmailsNode,
    VisualGmailGetThreadNode,
    VisualGmailGetAttachmentNode,
    # Management operations
    VisualGmailModifyLabelsNode,
    VisualGmailMoveToTrashNode,
    VisualGmailMarkAsReadNode,
    VisualGmailMarkAsUnreadNode,
    VisualGmailStarEmailNode,
    VisualGmailArchiveEmailNode,
    VisualGmailDeleteEmailNode,
    # Batch operations
    VisualGmailBatchSendNode,
    VisualGmailBatchModifyNode,
    VisualGmailBatchDeleteNode,
)

from casare_rpa.presentation.canvas.visual_nodes.google.sheets_nodes import (
    # Cell operations
    VisualSheetsGetCellNode,
    VisualSheetsSetCellNode,
    VisualSheetsGetRangeNode,
    VisualSheetsWriteRangeNode,
    VisualSheetsClearRangeNode,
    # Sheet operations
    VisualSheetsCreateSpreadsheetNode,
    VisualSheetsGetSpreadsheetNode,
    VisualSheetsAddSheetNode,
    VisualSheetsDeleteSheetNode,
    VisualSheetsDuplicateSheetNode,
    VisualSheetsRenameSheetNode,
    # Row/Column operations
    VisualSheetsAppendRowNode,
    VisualSheetsInsertRowNode,
    VisualSheetsDeleteRowNode,
    VisualSheetsInsertColumnNode,
    VisualSheetsDeleteColumnNode,
    # Format operations
    VisualSheetsFormatCellsNode,
    VisualSheetsAutoResizeNode,
    # Batch operations
    VisualSheetsBatchUpdateNode,
    VisualSheetsBatchGetNode,
    VisualSheetsBatchClearNode,
)

# Docs nodes removed - see Calendar/Docs cleanup 2025

from casare_rpa.presentation.canvas.visual_nodes.google.drive_nodes import (
    # File operations - Single file
    VisualDriveUploadFileNode,
    VisualDriveDownloadFileNode,
    VisualDriveDeleteFileNode,
    VisualDriveCopyFileNode,
    VisualDriveMoveFileNode,
    VisualDriveRenameFileNode,
    VisualDriveGetFileNode,
    # File operations - Bulk download
    VisualDriveDownloadFolderNode,
    VisualDriveBatchDownloadNode,
    # Folder operations
    VisualDriveCreateFolderNode,
    VisualDriveListFilesNode,
    VisualDriveSearchFilesNode,
    # Permissions
    VisualDriveShareFileNode,
    VisualDriveRemoveShareNode,
    VisualDriveGetPermissionsNode,
    VisualDriveCreateShareLinkNode,
    # Export
    VisualDriveExportFileNode,
    # Batch operations
    VisualDriveBatchDeleteNode,
    VisualDriveBatchMoveNode,
    VisualDriveBatchCopyNode,
)

__all__ = [
    # Calendar nodes removed - see Calendar/Docs cleanup 2025
    # Gmail - Send operations (6)
    "VisualGmailSendEmailNode",
    "VisualGmailSendWithAttachmentNode",
    "VisualGmailReplyToEmailNode",
    "VisualGmailForwardEmailNode",
    "VisualGmailCreateDraftNode",
    "VisualGmailSendDraftNode",
    # Gmail - Read operations (5)
    "VisualGmailGetEmailNode",
    "VisualGmailListEmailsNode",
    "VisualGmailSearchEmailsNode",
    "VisualGmailGetThreadNode",
    "VisualGmailGetAttachmentNode",
    # Gmail - Management operations (7)
    "VisualGmailModifyLabelsNode",
    "VisualGmailMoveToTrashNode",
    "VisualGmailMarkAsReadNode",
    "VisualGmailMarkAsUnreadNode",
    "VisualGmailStarEmailNode",
    "VisualGmailArchiveEmailNode",
    "VisualGmailDeleteEmailNode",
    # Gmail - Batch operations (3)
    "VisualGmailBatchSendNode",
    "VisualGmailBatchModifyNode",
    "VisualGmailBatchDeleteNode",
    # Sheets - Cell operations (5)
    "VisualSheetsGetCellNode",
    "VisualSheetsSetCellNode",
    "VisualSheetsGetRangeNode",
    "VisualSheetsWriteRangeNode",
    "VisualSheetsClearRangeNode",
    # Sheets - Sheet operations (6)
    "VisualSheetsCreateSpreadsheetNode",
    "VisualSheetsGetSpreadsheetNode",
    "VisualSheetsAddSheetNode",
    "VisualSheetsDeleteSheetNode",
    "VisualSheetsDuplicateSheetNode",
    "VisualSheetsRenameSheetNode",
    # Sheets - Row/Column operations (5)
    "VisualSheetsAppendRowNode",
    "VisualSheetsInsertRowNode",
    "VisualSheetsDeleteRowNode",
    "VisualSheetsInsertColumnNode",
    "VisualSheetsDeleteColumnNode",
    # Sheets - Format operations (2)
    "VisualSheetsFormatCellsNode",
    "VisualSheetsAutoResizeNode",
    # Sheets - Batch operations (3)
    "VisualSheetsBatchUpdateNode",
    "VisualSheetsBatchGetNode",
    "VisualSheetsBatchClearNode",
    # Docs nodes removed - see Calendar/Docs cleanup 2025
    # Drive - File operations - Single file (7)
    "VisualDriveUploadFileNode",
    "VisualDriveDownloadFileNode",
    "VisualDriveDeleteFileNode",
    "VisualDriveCopyFileNode",
    "VisualDriveMoveFileNode",
    "VisualDriveRenameFileNode",
    "VisualDriveGetFileNode",
    # Drive - File operations - Bulk download (2)
    "VisualDriveDownloadFolderNode",
    "VisualDriveBatchDownloadNode",
    # Drive - Folder operations (3)
    "VisualDriveCreateFolderNode",
    "VisualDriveListFilesNode",
    "VisualDriveSearchFilesNode",
    # Drive - Permissions (4)
    "VisualDriveShareFileNode",
    "VisualDriveRemoveShareNode",
    "VisualDriveGetPermissionsNode",
    "VisualDriveCreateShareLinkNode",
    # Drive - Export (1)
    "VisualDriveExportFileNode",
    # Drive - Batch operations (3)
    "VisualDriveBatchDeleteNode",
    "VisualDriveBatchMoveNode",
    "VisualDriveBatchCopyNode",
]

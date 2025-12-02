"""
Visual nodes for Google Workspace category.

Provides visual node representations for:
- Gmail: Email operations
- Sheets: Spreadsheet operations
- Docs: Document operations
- Drive: File storage operations
- Calendar: Event and calendar management
"""

from .calendar_nodes import (
    # Event operations (8)
    VisualCalendarListEventsNode,
    VisualCalendarGetEventNode,
    VisualCalendarCreateEventNode,
    VisualCalendarUpdateEventNode,
    VisualCalendarDeleteEventNode,
    VisualCalendarQuickAddNode,
    VisualCalendarMoveEventNode,
    VisualCalendarGetFreeBusyNode,
    # Calendar management operations (4)
    VisualCalendarListCalendarsNode,
    VisualCalendarGetCalendarNode,
    VisualCalendarCreateCalendarNode,
    VisualCalendarDeleteCalendarNode,
)

from .gmail_nodes import (
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

from .sheets_nodes import (
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

from .docs_nodes import (
    # Document operations
    VisualDocsCreateDocumentNode,
    VisualDocsGetDocumentNode,
    VisualDocsGetContentNode,
    # Text operations
    VisualDocsInsertTextNode,
    VisualDocsDeleteContentNode,
    VisualDocsReplaceTextNode,
    # Formatting
    VisualDocsInsertTableNode,
    VisualDocsInsertImageNode,
    VisualDocsUpdateStyleNode,
    VisualDocsBatchUpdateNode,
)

from .drive_nodes import (
    # File operations
    VisualDriveUploadFileNode,
    VisualDriveDownloadFileNode,
    VisualDriveDeleteFileNode,
    VisualDriveCopyFileNode,
    VisualDriveMoveFileNode,
    VisualDriveRenameFileNode,
    VisualDriveGetFileNode,
    # Folder operations
    VisualDriveCreateFolderNode,
    VisualDriveListFilesNode,
    VisualDriveSearchFilesNode,
    # Permissions
    VisualDriveShareFileNode,
    VisualDriveRemovePermissionNode,
    VisualDriveGetPermissionsNode,
    # Export
    VisualDriveExportFileNode,
    # Batch operations
    VisualDriveBatchDeleteNode,
    VisualDriveBatchMoveNode,
    VisualDriveBatchCopyNode,
)

__all__ = [
    # Calendar - Event operations (8)
    "VisualCalendarListEventsNode",
    "VisualCalendarGetEventNode",
    "VisualCalendarCreateEventNode",
    "VisualCalendarUpdateEventNode",
    "VisualCalendarDeleteEventNode",
    "VisualCalendarQuickAddNode",
    "VisualCalendarMoveEventNode",
    "VisualCalendarGetFreeBusyNode",
    # Calendar - Management operations (4)
    "VisualCalendarListCalendarsNode",
    "VisualCalendarGetCalendarNode",
    "VisualCalendarCreateCalendarNode",
    "VisualCalendarDeleteCalendarNode",
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
    # Docs - Document operations (3)
    "VisualDocsCreateDocumentNode",
    "VisualDocsGetDocumentNode",
    "VisualDocsGetContentNode",
    # Docs - Text operations (3)
    "VisualDocsInsertTextNode",
    "VisualDocsDeleteContentNode",
    "VisualDocsReplaceTextNode",
    # Docs - Formatting (4)
    "VisualDocsInsertTableNode",
    "VisualDocsInsertImageNode",
    "VisualDocsUpdateStyleNode",
    "VisualDocsBatchUpdateNode",
    # Drive - File operations (7)
    "VisualDriveUploadFileNode",
    "VisualDriveDownloadFileNode",
    "VisualDriveDeleteFileNode",
    "VisualDriveCopyFileNode",
    "VisualDriveMoveFileNode",
    "VisualDriveRenameFileNode",
    "VisualDriveGetFileNode",
    # Drive - Folder operations (3)
    "VisualDriveCreateFolderNode",
    "VisualDriveListFilesNode",
    "VisualDriveSearchFilesNode",
    # Drive - Permissions (3)
    "VisualDriveShareFileNode",
    "VisualDriveRemovePermissionNode",
    "VisualDriveGetPermissionsNode",
    # Drive - Export (1)
    "VisualDriveExportFileNode",
    # Drive - Batch operations (3)
    "VisualDriveBatchDeleteNode",
    "VisualDriveBatchMoveNode",
    "VisualDriveBatchCopyNode",
]

"""
Google Workspace nodes for CasareRPA.

This package provides nodes for interacting with Google Workspace services:
- Gmail: Email sending, reading, managing
- Sheets: Spreadsheet operations
- Docs: Document operations
- Drive: File storage operations
- Calendar: Event and calendar management

Base classes and utilities:
- GoogleBaseNode: Abstract base for all Google nodes
- GoogleAPIClient: Async client with OAuth2 and rate limiting
"""

from casare_rpa.nodes.google.google_base import (
    # Base classes
    GoogleBaseNode,
    GmailBaseNode as GoogleGmailBaseNode,  # Alias to avoid conflict with gmail/ package
    DocsBaseNode as GoogleDocsBaseNode,
    SheetsBaseNode as GoogleSheetsBaseNode,
    DriveBaseNode as GoogleDriveBaseNode,
    CalendarBaseNode as GoogleCalendarBaseNode,
    # Client and credentials
    GoogleAPIClient,
    GoogleCredentials,
    # Errors
    GoogleAPIError,
    GoogleAuthError,
    GoogleQuotaError,
    # Scopes
    SCOPES,
    get_gmail_scopes,
    get_sheets_scopes,
    get_docs_scopes,
    get_drive_scopes,
    get_calendar_scopes,
    # PropertyDef constants
    GOOGLE_CREDENTIAL_NAME,
    GOOGLE_ACCESS_TOKEN,
    GOOGLE_REFRESH_TOKEN,
    GOOGLE_SERVICE_ACCOUNT_JSON,
    GOOGLE_TIMEOUT,
    GOOGLE_MAX_RETRIES,
    GOOGLE_CREDENTIAL_PROPERTIES,
    GOOGLE_COMMON_PROPERTIES,
)

# Gmail nodes from gmail/ subpackage (standalone OAuth implementation)
from casare_rpa.nodes.google.gmail import (
    GmailBaseNode,
    # Send operations (new standalone)
    GmailSendEmailNode,
    GmailSendWithAttachmentNode,
    GmailReplyToEmailNode,
    GmailForwardEmailNode,
    GmailCreateDraftNode,
    # Read operations (new standalone)
    GmailGetEmailNode,
    GmailSearchEmailsNode,
    GmailGetThreadNode,
    GmailGetAttachmentNode,
)

# Legacy gmail_nodes.py imports (require pre-authenticated google_client)
# Note: Some nodes are shadowed by gmail/ subpackage versions above
from casare_rpa.nodes.google.gmail_nodes import (
    # GmailSendEmailNode,  # Shadowed by gmail/ subpackage
    # GmailSendWithAttachmentNode,  # Shadowed by gmail/ subpackage
    # GmailCreateDraftNode,  # Shadowed by gmail/ subpackage
    GmailSendDraftNode,
    # GmailGetEmailNode,  # Shadowed by gmail/ subpackage
    GmailListEmailsNode,
    # GmailSearchEmailsNode,  # Shadowed by gmail/ subpackage
    # GmailGetThreadNode,  # Shadowed by gmail/ subpackage
    # Management operations
    GmailModifyLabelsNode,
    GmailMoveToTrashNode,
    GmailMarkAsReadNode,
    GmailMarkAsUnreadNode,
    GmailStarEmailNode,
    GmailArchiveEmailNode,
    GmailDeleteEmailNode,
    # Additional management
    GmailAddLabelNode,
    GmailRemoveLabelNode,
    GmailGetLabelsNode,
    GmailTrashEmailNode,
    # Batch operations
    GmailBatchSendNode,
    GmailBatchModifyNode,
    GmailBatchDeleteNode,
)

from casare_rpa.nodes.google.sheets import (
    # Base
    SheetsBaseNode,
    # Read nodes (6)
    SheetsGetCellNode,
    SheetsGetRangeNode,
    SheetsGetRowNode,
    SheetsGetColumnNode,
    SheetsSearchNode,
    SheetsGetSheetInfoNode,
    # Write nodes (7)
    SheetsWriteCellNode,
    SheetsWriteRangeNode,
    SheetsAppendRowNode,
    SheetsUpdateRowNode,
    SheetsInsertRowNode,
    SheetsDeleteRowNode,
    SheetsClearRangeNode,
    # Management nodes (7)
    SheetsCreateSpreadsheetNode,
    SheetsGetSpreadsheetNode,
    SheetsAddSheetNode,
    SheetsDeleteSheetNode,
    SheetsCopySheetNode,
    SheetsDuplicateSheetNode,
    SheetsRenameSheetNode,
    # Batch nodes (3)
    SheetsBatchUpdateNode,
    SheetsBatchGetNode,
    SheetsBatchClearNode,
)

from casare_rpa.nodes.google.docs_nodes import (
    # Document operations (legacy - require pre-authenticated google_client)
    DocsCreateDocumentNode,
    DocsGetDocumentNode,
    DocsGetContentNode,
    # Text operations
    DocsInsertTextNode,
    DocsDeleteContentNode,
    DocsReplaceTextNode,
    # Formatting
    DocsInsertTableNode,
    DocsInsertImageNode,
    DocsUpdateStyleNode,
    DocsBatchUpdateNode,
)

# Standalone Docs nodes from docs/ subpackage (with own OAuth handling)
from casare_rpa.nodes.google.docs import (
    DocsBaseNode,
    # Read operations (standalone)
    DocsGetDocumentNode as DocsGetDocumentStandaloneNode,
    DocsGetTextNode,
    DocsExportNode,
    # Write operations (standalone)
    DocsCreateDocumentNode as DocsCreateDocumentStandaloneNode,
    DocsInsertTextNode as DocsInsertTextStandaloneNode,
    DocsAppendTextNode,
    DocsReplaceTextNode as DocsReplaceTextStandaloneNode,
    DocsInsertTableNode as DocsInsertTableStandaloneNode,
    DocsInsertImageNode as DocsInsertImageStandaloneNode,
    DocsApplyStyleNode,
)

from casare_rpa.nodes.google.drive_nodes import (
    # File operations - Single file
    DriveUploadFileNode,
    DriveDownloadFileNode,
    DriveDeleteFileNode,
    DriveCopyFileNode,
    DriveMoveFileNode,
    DriveRenameFileNode,
    DriveGetFileNode,
    # File operations - Bulk download
    DriveDownloadFolderNode,
    DriveBatchDownloadNode,
    # Folder operations
    DriveCreateFolderNode,
    DriveListFilesNode,
    DriveSearchFilesNode,
    # Sharing operations
    DriveShareFileNode,
    DriveRemoveShareNode,
    DriveRemovePermissionNode,  # Alias for backward compatibility
    DriveGetPermissionsNode,
    DriveCreateShareLinkNode,
    # Export
    DriveExportFileNode,
    # Batch operations
    DriveBatchDeleteNode,
    DriveBatchMoveNode,
    DriveBatchCopyNode,
)

# Calendar nodes from calendar/ subpackage
from casare_rpa.nodes.google.calendar import (
    # Base
    CalendarBaseNode,
    # Event nodes (8)
    CalendarListEventsNode,
    CalendarGetEventNode,
    CalendarCreateEventNode,
    CalendarUpdateEventNode,
    CalendarDeleteEventNode,
    CalendarQuickAddNode,
    CalendarMoveEventNode,
    CalendarGetFreeBusyNode,
    # Management nodes (4)
    CalendarListCalendarsNode,
    CalendarGetCalendarNode,
    CalendarCreateCalendarNode,
    CalendarDeleteCalendarNode,
)

__all__ = [
    # Base classes (unified from google_base)
    "GoogleBaseNode",
    "GoogleGmailBaseNode",
    "GoogleDocsBaseNode",
    "GoogleSheetsBaseNode",
    "GoogleDriveBaseNode",
    "GoogleCalendarBaseNode",
    # Client and credentials
    "GoogleAPIClient",
    "GoogleCredentials",
    # Errors
    "GoogleAPIError",
    "GoogleAuthError",
    "GoogleQuotaError",
    # Scopes
    "SCOPES",
    "get_gmail_scopes",
    "get_sheets_scopes",
    "get_docs_scopes",
    "get_drive_scopes",
    "get_calendar_scopes",
    # PropertyDef constants
    "GOOGLE_CREDENTIAL_NAME",
    "GOOGLE_ACCESS_TOKEN",
    "GOOGLE_REFRESH_TOKEN",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GOOGLE_TIMEOUT",
    "GOOGLE_MAX_RETRIES",
    "GOOGLE_CREDENTIAL_PROPERTIES",
    "GOOGLE_COMMON_PROPERTIES",
    # Gmail - Base (from gmail/ subpackage)
    "GmailBaseNode",
    # Gmail - Send operations (5 from gmail/ subpackage)
    "GmailSendEmailNode",
    "GmailSendWithAttachmentNode",
    "GmailReplyToEmailNode",
    "GmailForwardEmailNode",
    "GmailCreateDraftNode",
    "GmailSendDraftNode",  # Legacy
    # Gmail - Read operations (5 - 4 from gmail/ subpackage + 1 legacy)
    "GmailGetEmailNode",
    "GmailListEmailsNode",  # Legacy
    "GmailSearchEmailsNode",
    "GmailGetThreadNode",
    "GmailGetAttachmentNode",
    # Gmail - Management operations (7)
    "GmailModifyLabelsNode",
    "GmailMoveToTrashNode",
    "GmailMarkAsReadNode",
    "GmailMarkAsUnreadNode",
    "GmailStarEmailNode",
    "GmailArchiveEmailNode",
    "GmailDeleteEmailNode",
    # Gmail - Additional management (4)
    "GmailAddLabelNode",
    "GmailRemoveLabelNode",
    "GmailGetLabelsNode",
    "GmailTrashEmailNode",
    # Gmail - Batch operations (3)
    "GmailBatchSendNode",
    "GmailBatchModifyNode",
    "GmailBatchDeleteNode",
    # Sheets - Base
    "SheetsBaseNode",
    # Sheets - Read nodes (6)
    "SheetsGetCellNode",
    "SheetsGetRangeNode",
    "SheetsGetRowNode",
    "SheetsGetColumnNode",
    "SheetsSearchNode",
    "SheetsGetSheetInfoNode",
    # Sheets - Write nodes (7)
    "SheetsWriteCellNode",
    "SheetsWriteRangeNode",
    "SheetsAppendRowNode",
    "SheetsUpdateRowNode",
    "SheetsInsertRowNode",
    "SheetsDeleteRowNode",
    "SheetsClearRangeNode",
    # Sheets - Management nodes (7)
    "SheetsCreateSpreadsheetNode",
    "SheetsGetSpreadsheetNode",
    "SheetsAddSheetNode",
    "SheetsDeleteSheetNode",
    "SheetsCopySheetNode",
    "SheetsDuplicateSheetNode",
    "SheetsRenameSheetNode",
    # Sheets - Batch nodes (3)
    "SheetsBatchUpdateNode",
    "SheetsBatchGetNode",
    "SheetsBatchClearNode",
    # Docs - Document operations (3) - Legacy
    "DocsCreateDocumentNode",
    "DocsGetDocumentNode",
    "DocsGetContentNode",
    # Docs - Text operations (3) - Legacy
    "DocsInsertTextNode",
    "DocsDeleteContentNode",
    "DocsReplaceTextNode",
    # Docs - Formatting (4) - Legacy
    "DocsInsertTableNode",
    "DocsInsertImageNode",
    "DocsUpdateStyleNode",
    "DocsBatchUpdateNode",
    # Docs - Standalone (new, with own OAuth handling)
    "DocsBaseNode",
    "DocsGetDocumentStandaloneNode",
    "DocsGetTextNode",
    "DocsExportNode",
    "DocsCreateDocumentStandaloneNode",
    "DocsInsertTextStandaloneNode",
    "DocsAppendTextNode",
    "DocsReplaceTextStandaloneNode",
    "DocsInsertTableStandaloneNode",
    "DocsInsertImageStandaloneNode",
    "DocsApplyStyleNode",
    # Drive - File operations - Single file (7)
    "DriveUploadFileNode",
    "DriveDownloadFileNode",
    "DriveDeleteFileNode",
    "DriveCopyFileNode",
    "DriveMoveFileNode",
    "DriveRenameFileNode",
    "DriveGetFileNode",
    # Drive - File operations - Bulk download (2)
    "DriveDownloadFolderNode",
    "DriveBatchDownloadNode",
    # Drive - Folder operations (3)
    "DriveCreateFolderNode",
    "DriveListFilesNode",
    "DriveSearchFilesNode",
    # Drive - Sharing operations (4)
    "DriveShareFileNode",
    "DriveRemoveShareNode",
    "DriveRemovePermissionNode",  # Alias
    "DriveGetPermissionsNode",
    "DriveCreateShareLinkNode",
    # Drive - Export (1)
    "DriveExportFileNode",
    # Drive - Batch operations (3)
    "DriveBatchDeleteNode",
    "DriveBatchMoveNode",
    "DriveBatchCopyNode",
    # Calendar - Base
    "CalendarBaseNode",
    # Calendar - Event nodes (8)
    "CalendarListEventsNode",
    "CalendarGetEventNode",
    "CalendarCreateEventNode",
    "CalendarUpdateEventNode",
    "CalendarDeleteEventNode",
    "CalendarQuickAddNode",
    "CalendarMoveEventNode",
    "CalendarGetFreeBusyNode",
    # Calendar - Management nodes (4)
    "CalendarListCalendarsNode",
    "CalendarGetCalendarNode",
    "CalendarCreateCalendarNode",
    "CalendarDeleteCalendarNode",
]

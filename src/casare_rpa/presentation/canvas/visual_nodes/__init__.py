"""
CasareRPA Visual Nodes - Organized by Category

All visual nodes organized into categories for better navigation.
"""

# Basic (3 nodes)
from casare_rpa.presentation.canvas.visual_nodes.basic import (
    VisualStartNode,
    VisualEndNode,
    VisualCommentNode,
)

# Browser (23 nodes)
from casare_rpa.presentation.canvas.visual_nodes.browser import (
    VisualLaunchBrowserNode,
    VisualCloseBrowserNode,
    VisualNewTabNode,
    VisualGetAllImagesNode,
    VisualDownloadFileNode,
    VisualGoToURLNode,
    VisualGoBackNode,
    VisualGoForwardNode,
    VisualRefreshPageNode,
    VisualClickElementNode,
    VisualTypeTextNode,
    VisualSelectDropdownNode,
    VisualImageClickNode,
    VisualExtractTextNode,
    VisualGetAttributeNode,
    VisualScreenshotNode,
    VisualTableScraperNode,
    VisualWaitNode,
    VisualWaitForElementNode,
    VisualWaitForNavigationNode,
    VisualFormFieldNode,
    VisualFormFillerNode,
    VisualDetectFormsNode,
)

# Control Flow (16 nodes)
from casare_rpa.presentation.canvas.visual_nodes.control_flow import (
    VisualIfNode,
    VisualForLoopNode,
    VisualForLoopStartNode,
    VisualForLoopEndNode,
    VisualWhileLoopNode,
    VisualWhileLoopStartNode,
    VisualWhileLoopEndNode,
    VisualBreakNode,
    VisualContinueNode,
    VisualMergeNode,
    VisualSwitchNode,
    # Try/Catch/Finally nodes
    VisualTryCatchFinallyNode,
    VisualTryNode,
    VisualCatchNode,
    VisualFinallyNode,
)

# Database (10 nodes)
from casare_rpa.presentation.canvas.visual_nodes.database import (
    VisualDatabaseConnectNode,
    VisualExecuteQueryNode,
    VisualExecuteNonQueryNode,
    VisualBeginTransactionNode,
    VisualCommitTransactionNode,
    VisualRollbackTransactionNode,
    VisualCloseDatabaseNode,
    VisualTableExistsNode,
    VisualGetTableColumnsNode,
    VisualExecuteBatchNode,
)

# Data Operations (40 nodes) - NEW
from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
    # Data operations
    VisualConcatenateNode,
    VisualFormatStringNode,
    VisualRegexMatchNode,
    VisualRegexReplaceNode,
    VisualMathOperationNode,
    VisualComparisonNode,
    VisualCreateListNode,
    VisualListGetItemNode,
    VisualJsonParseNode,
    VisualGetPropertyNode,
    # List operations
    VisualListLengthNode,
    VisualListAppendNode,
    VisualListContainsNode,
    VisualListSliceNode,
    VisualListJoinNode,
    VisualListSortNode,
    VisualListReverseNode,
    VisualListUniqueNode,
    VisualListFilterNode,
    VisualListMapNode,
    VisualListReduceNode,
    VisualListFlattenNode,
    # Dict operations
    VisualDictGetNode,
    VisualDictSetNode,
    VisualDictRemoveNode,
    VisualDictMergeNode,
    VisualDictKeysNode,
    VisualDictValuesNode,
    VisualDictHasKeyNode,
    VisualCreateDictNode,
    VisualDictToJsonNode,
    VisualDictItemsNode,
)

# Desktop Automation (36 nodes)
from casare_rpa.presentation.canvas.visual_nodes.desktop_automation import (
    VisualLaunchApplicationNode,
    VisualCloseApplicationNode,
    VisualActivateWindowNode,
    VisualGetWindowListNode,
    VisualFindElementNode,
    VisualClickElementDesktopNode,
    VisualTypeTextDesktopNode,
    VisualGetElementTextNode,
    VisualGetElementPropertyNode,
    VisualResizeWindowNode,
    VisualMoveWindowNode,
    VisualMaximizeWindowNode,
    VisualMinimizeWindowNode,
    VisualRestoreWindowNode,
    VisualGetWindowPropertiesNode,
    VisualSetWindowStateNode,
    VisualSelectFromDropdownNode,
    VisualCheckCheckboxNode,
    VisualSelectRadioButtonNode,
    VisualSelectTabNode,
    VisualExpandTreeItemNode,
    VisualScrollElementNode,
    VisualMoveMouseNode,
    VisualMouseClickNode,
    VisualSendKeysNode,
    VisualSendHotKeyNode,
    VisualGetMousePositionNode,
    VisualDragMouseNode,
    VisualDesktopWaitForElementNode,
    VisualWaitForWindowNode,
    VisualVerifyElementExistsNode,
    VisualVerifyElementPropertyNode,
    VisualCaptureScreenshotNode,
    VisualCaptureElementImageNode,
    VisualOCRExtractTextNode,
    VisualCompareImagesNode,
)

# Email (8 nodes)
from casare_rpa.presentation.canvas.visual_nodes.email import (
    VisualSendEmailNode,
    VisualReadEmailsNode,
    VisualGetEmailContentNode,
    VisualSaveAttachmentNode,
    VisualFilterEmailsNode,
    VisualMarkEmailNode,
    VisualDeleteEmailNode,
    VisualMoveEmailNode,
)

# Error Handling (9 nodes - TryNode moved to control_flow)
from casare_rpa.presentation.canvas.visual_nodes.error_handling import (
    VisualRetryNode,
    VisualRetrySuccessNode,
    VisualRetryFailNode,
    VisualThrowErrorNode,
    VisualWebhookNotifyNode,
    VisualOnErrorNode,
    VisualErrorRecoveryNode,
    VisualLogErrorNode,
    VisualAssertNode,
)

# File Operations (40 nodes)
from casare_rpa.presentation.canvas.visual_nodes.file_operations import (
    VisualReadFileNode,
    VisualWriteFileNode,
    VisualAppendFileNode,
    VisualDeleteFileNode,
    VisualCopyFileNode,
    VisualMoveFileNode,
    VisualFileExistsNode,
    VisualGetFileSizeNode,
    VisualGetFileInfoNode,
    VisualListFilesNode,
    VisualReadCsvNode,
    VisualWriteCsvNode,
    VisualReadJsonNode,
    VisualWriteJsonNode,
    VisualZipFilesNode,
    VisualUnzipFileNode,
    VisualParseXMLNode,
    VisualReadXMLFileNode,
    VisualWriteXMLFileNode,
    VisualXPathQueryNode,
    VisualGetXMLElementNode,
    VisualGetXMLAttributeNode,
    VisualXMLToJsonNode,
    VisualJsonToXMLNode,
    VisualReadPDFTextNode,
    VisualGetPDFInfoNode,
    VisualMergePDFsNode,
    VisualSplitPDFNode,
    VisualExtractPDFPagesNode,
    VisualPDFToImagesNode,
    VisualFTPConnectNode,
    VisualFTPUploadNode,
    VisualFTPDownloadNode,
    VisualFTPListNode,
    VisualFTPDeleteNode,
    VisualFTPMakeDirNode,
    VisualFTPRemoveDirNode,
    VisualFTPRenameNode,
    VisualFTPDisconnectNode,
    VisualFTPGetSizeNode,
)

# Scripts (5 nodes)
from casare_rpa.presentation.canvas.visual_nodes.scripts import (
    VisualRunPythonScriptNode,
    VisualRunPythonFileNode,
    VisualEvalExpressionNode,
    VisualRunBatchScriptNode,
    VisualRunJavaScriptNode,
)

# System (13 nodes)
from casare_rpa.presentation.canvas.visual_nodes.system import (
    # Clipboard operations
    VisualClipboardCopyNode,
    VisualClipboardPasteNode,
    VisualClipboardClearNode,
    # Dialogs
    VisualMessageBoxNode,
    VisualInputDialogNode,
    VisualTooltipNode,
    # Terminal
    VisualRunCommandNode,
    VisualRunPowerShellNode,
    # Windows Services
    VisualGetServiceStatusNode,
    VisualStartServiceNode,
    VisualStopServiceNode,
    VisualRestartServiceNode,
    VisualListServicesNode,
)

# Utility (26 nodes)
from casare_rpa.presentation.canvas.visual_nodes.utility import (
    VisualRandomNumberNode,
    VisualRandomChoiceNode,
    VisualRandomStringNode,
    VisualRandomUUIDNode,
    VisualShuffleListNode,
    VisualGetCurrentDateTimeNode,
    VisualFormatDateTimeNode,
    VisualParseDateTimeNode,
    VisualDateTimeAddNode,
    VisualDateTimeDiffNode,
    VisualDateTimeCompareNode,
    VisualGetTimestampNode,
    VisualTextSplitNode,
    VisualTextReplaceNode,
    VisualTextTrimNode,
    VisualTextCaseNode,
    VisualTextPadNode,
    VisualTextSubstringNode,
    VisualTextContainsNode,
    VisualTextStartsWithNode,
    VisualTextEndsWithNode,
    VisualTextLinesNode,
    VisualTextReverseNode,
    VisualTextCountNode,
    VisualTextJoinNode,
    VisualTextExtractNode,
)

# Office Automation (12 nodes)
from casare_rpa.presentation.canvas.visual_nodes.office_automation import (
    VisualExcelOpenNode,
    VisualExcelReadCellNode,
    VisualExcelWriteCellNode,
    VisualExcelGetRangeNode,
    VisualExcelCloseNode,
    VisualWordOpenNode,
    VisualWordGetTextNode,
    VisualWordReplaceTextNode,
    VisualWordCloseNode,
    VisualOutlookSendEmailNode,
    VisualOutlookReadEmailsNode,
    VisualOutlookGetInboxCountNode,
)

# REST API (7 nodes)
from casare_rpa.presentation.canvas.visual_nodes.rest_api import (
    VisualHttpRequestNode,
    VisualSetHttpHeadersNode,
    VisualHttpAuthNode,
    VisualParseJsonResponseNode,
    VisualHttpDownloadFileNode,
    VisualHttpUploadFileNode,
    VisualBuildUrlNode,
)

# Variable (3 nodes)
from casare_rpa.presentation.canvas.visual_nodes.variable import (
    VisualSetVariableNode,
    VisualGetVariableNode,
    VisualIncrementVariableNode,
)

# Triggers (17 nodes)
from casare_rpa.presentation.canvas.visual_nodes.triggers import (
    VisualWebhookTriggerNode,
    VisualScheduleTriggerNode,
    VisualFileWatchTriggerNode,
    VisualEmailTriggerNode,
    VisualAppEventTriggerNode,
    VisualErrorTriggerNode,
    VisualWorkflowCallTriggerNode,
    VisualFormTriggerNode,
    VisualChatTriggerNode,
    VisualRSSFeedTriggerNode,
    VisualSSETriggerNode,
    # Messaging triggers
    VisualTelegramTriggerNode,
    VisualWhatsAppTriggerNode,
    # Google triggers
    VisualGmailTriggerNode,
    VisualDriveTriggerNode,
    VisualSheetsTriggerNode,
    VisualCalendarTriggerNode,
)

# AI/ML (6 nodes)
from casare_rpa.presentation.canvas.visual_nodes.ai_ml import (
    VisualLLMCompletionNode,
    VisualLLMChatNode,
    VisualLLMExtractDataNode,
    VisualLLMSummarizeNode,
    VisualLLMClassifyNode,
    VisualLLMTranslateNode,
)

# Document AI (5 nodes)
from casare_rpa.presentation.canvas.visual_nodes.document import (
    VisualClassifyDocumentNode,
    VisualExtractFormNode,
    VisualExtractInvoiceNode,
    VisualExtractTableNode,
    VisualValidateExtractionNode,
)

# Messaging (16 nodes)
from casare_rpa.presentation.canvas.visual_nodes.messaging import (
    # Telegram - Send (4)
    VisualTelegramSendMessageNode,
    VisualTelegramSendPhotoNode,
    VisualTelegramSendDocumentNode,
    VisualTelegramSendLocationNode,
    # Telegram - Actions (5)
    VisualTelegramEditMessageNode,
    VisualTelegramDeleteMessageNode,
    VisualTelegramSendMediaGroupNode,
    VisualTelegramAnswerCallbackNode,
    VisualTelegramGetUpdatesNode,
    # WhatsApp (7)
    VisualWhatsAppSendMessageNode,
    VisualWhatsAppSendTemplateNode,
    VisualWhatsAppSendImageNode,
    VisualWhatsAppSendDocumentNode,
    VisualWhatsAppSendVideoNode,
    VisualWhatsAppSendLocationNode,
    VisualWhatsAppSendInteractiveNode,
)

# Google Workspace (77 nodes = 65 + 12 Calendar)
from casare_rpa.presentation.canvas.visual_nodes.google import (
    # Calendar - Event operations (8)
    VisualCalendarListEventsNode,
    VisualCalendarGetEventNode,
    VisualCalendarCreateEventNode,
    VisualCalendarUpdateEventNode,
    VisualCalendarDeleteEventNode,
    VisualCalendarQuickAddNode,
    VisualCalendarMoveEventNode,
    VisualCalendarGetFreeBusyNode,
    # Calendar - Management operations (4)
    VisualCalendarListCalendarsNode,
    VisualCalendarGetCalendarNode,
    VisualCalendarCreateCalendarNode,
    VisualCalendarDeleteCalendarNode,
    # Gmail - Send operations (6)
    VisualGmailSendEmailNode,
    VisualGmailSendWithAttachmentNode,
    VisualGmailReplyToEmailNode,
    VisualGmailForwardEmailNode,
    VisualGmailCreateDraftNode,
    VisualGmailSendDraftNode,
    # Gmail - Read operations (5)
    VisualGmailGetEmailNode,
    VisualGmailListEmailsNode,
    VisualGmailSearchEmailsNode,
    VisualGmailGetThreadNode,
    VisualGmailGetAttachmentNode,
    # Gmail - Management operations (7)
    VisualGmailModifyLabelsNode,
    VisualGmailMoveToTrashNode,
    VisualGmailMarkAsReadNode,
    VisualGmailMarkAsUnreadNode,
    VisualGmailStarEmailNode,
    VisualGmailArchiveEmailNode,
    VisualGmailDeleteEmailNode,
    # Gmail - Batch operations (3)
    VisualGmailBatchSendNode,
    VisualGmailBatchModifyNode,
    VisualGmailBatchDeleteNode,
    # Sheets - Cell operations (5)
    VisualSheetsGetCellNode,
    VisualSheetsSetCellNode,
    VisualSheetsGetRangeNode,
    VisualSheetsWriteRangeNode,
    VisualSheetsClearRangeNode,
    # Sheets - Sheet operations (6)
    VisualSheetsCreateSpreadsheetNode,
    VisualSheetsGetSpreadsheetNode,
    VisualSheetsAddSheetNode,
    VisualSheetsDeleteSheetNode,
    VisualSheetsDuplicateSheetNode,
    VisualSheetsRenameSheetNode,
    # Sheets - Row/Column operations (5)
    VisualSheetsAppendRowNode,
    VisualSheetsInsertRowNode,
    VisualSheetsDeleteRowNode,
    VisualSheetsInsertColumnNode,
    VisualSheetsDeleteColumnNode,
    # Sheets - Format operations (2)
    VisualSheetsFormatCellsNode,
    VisualSheetsAutoResizeNode,
    # Sheets - Batch operations (3)
    VisualSheetsBatchUpdateNode,
    VisualSheetsBatchGetNode,
    VisualSheetsBatchClearNode,
    # Docs - Document operations (3)
    VisualDocsCreateDocumentNode,
    VisualDocsGetDocumentNode,
    VisualDocsGetContentNode,
    # Docs - Text operations (2)
    VisualDocsInsertTextNode,
    VisualDocsReplaceTextNode,
    # Docs - Formatting (3)
    VisualDocsInsertTableNode,
    VisualDocsInsertImageNode,
    VisualDocsUpdateStyleNode,
    # Drive - File operations (7)
    VisualDriveUploadFileNode,
    VisualDriveDownloadFileNode,
    VisualDriveDeleteFileNode,
    VisualDriveCopyFileNode,
    VisualDriveMoveFileNode,
    VisualDriveRenameFileNode,
    VisualDriveGetFileNode,
    # Drive - Folder operations (3)
    VisualDriveCreateFolderNode,
    VisualDriveListFilesNode,
    VisualDriveSearchFilesNode,
    # Drive - Permissions (3)
    VisualDriveShareFileNode,
    VisualDriveRemovePermissionNode,
    VisualDriveGetPermissionsNode,
    # Drive - Export (1)
    VisualDriveExportFileNode,
    # Drive - Batch operations (3)
    VisualDriveBatchDeleteNode,
    VisualDriveBatchMoveNode,
    VisualDriveBatchCopyNode,
)

__all__ = [
    # basic
    "VisualStartNode",
    "VisualEndNode",
    "VisualCommentNode",
    # browser
    "VisualLaunchBrowserNode",
    "VisualCloseBrowserNode",
    "VisualNewTabNode",
    "VisualGetAllImagesNode",
    "VisualDownloadFileNode",
    "VisualGoToURLNode",
    "VisualGoBackNode",
    "VisualGoForwardNode",
    "VisualRefreshPageNode",
    "VisualClickElementNode",
    "VisualTypeTextNode",
    "VisualSelectDropdownNode",
    "VisualImageClickNode",
    "VisualExtractTextNode",
    "VisualGetAttributeNode",
    "VisualScreenshotNode",
    "VisualTableScraperNode",
    "VisualWaitNode",
    "VisualWaitForElementNode",
    "VisualWaitForNavigationNode",
    "VisualFormFieldNode",
    "VisualFormFillerNode",
    "VisualDetectFormsNode",
    # control_flow
    "VisualIfNode",
    "VisualForLoopNode",
    "VisualForLoopStartNode",
    "VisualForLoopEndNode",
    "VisualWhileLoopNode",
    "VisualWhileLoopStartNode",
    "VisualWhileLoopEndNode",
    "VisualBreakNode",
    "VisualContinueNode",
    "VisualMergeNode",
    "VisualSwitchNode",
    # Try/Catch/Finally nodes
    "VisualTryCatchFinallyNode",
    "VisualTryNode",
    "VisualCatchNode",
    "VisualFinallyNode",
    # database
    "VisualDatabaseConnectNode",
    "VisualExecuteQueryNode",
    "VisualExecuteNonQueryNode",
    "VisualBeginTransactionNode",
    "VisualCommitTransactionNode",
    "VisualRollbackTransactionNode",
    "VisualCloseDatabaseNode",
    "VisualTableExistsNode",
    "VisualGetTableColumnsNode",
    "VisualExecuteBatchNode",
    # data_operations
    "VisualConcatenateNode",
    "VisualFormatStringNode",
    "VisualRegexMatchNode",
    "VisualRegexReplaceNode",
    "VisualMathOperationNode",
    "VisualComparisonNode",
    "VisualCreateListNode",
    "VisualListGetItemNode",
    "VisualJsonParseNode",
    "VisualGetPropertyNode",
    "VisualListLengthNode",
    "VisualListAppendNode",
    "VisualListContainsNode",
    "VisualListSliceNode",
    "VisualListJoinNode",
    "VisualListSortNode",
    "VisualListReverseNode",
    "VisualListUniqueNode",
    "VisualListFilterNode",
    "VisualListMapNode",
    "VisualListReduceNode",
    "VisualListFlattenNode",
    "VisualDictGetNode",
    "VisualDictSetNode",
    "VisualDictRemoveNode",
    "VisualDictMergeNode",
    "VisualDictKeysNode",
    "VisualDictValuesNode",
    "VisualDictHasKeyNode",
    "VisualCreateDictNode",
    "VisualDictToJsonNode",
    "VisualDictItemsNode",
    # desktop_automation
    "VisualLaunchApplicationNode",
    "VisualCloseApplicationNode",
    "VisualActivateWindowNode",
    "VisualGetWindowListNode",
    "VisualFindElementNode",
    "VisualClickElementDesktopNode",
    "VisualTypeTextDesktopNode",
    "VisualGetElementTextNode",
    "VisualGetElementPropertyNode",
    "VisualResizeWindowNode",
    "VisualMoveWindowNode",
    "VisualMaximizeWindowNode",
    "VisualMinimizeWindowNode",
    "VisualRestoreWindowNode",
    "VisualGetWindowPropertiesNode",
    "VisualSetWindowStateNode",
    "VisualSelectFromDropdownNode",
    "VisualCheckCheckboxNode",
    "VisualSelectRadioButtonNode",
    "VisualSelectTabNode",
    "VisualExpandTreeItemNode",
    "VisualScrollElementNode",
    "VisualMoveMouseNode",
    "VisualMouseClickNode",
    "VisualSendKeysNode",
    "VisualSendHotKeyNode",
    "VisualGetMousePositionNode",
    "VisualDragMouseNode",
    "VisualDesktopWaitForElementNode",
    "VisualWaitForWindowNode",
    "VisualVerifyElementExistsNode",
    "VisualVerifyElementPropertyNode",
    "VisualCaptureScreenshotNode",
    "VisualCaptureElementImageNode",
    "VisualOCRExtractTextNode",
    "VisualCompareImagesNode",
    # email
    "VisualSendEmailNode",
    "VisualReadEmailsNode",
    "VisualGetEmailContentNode",
    "VisualSaveAttachmentNode",
    "VisualFilterEmailsNode",
    "VisualMarkEmailNode",
    "VisualDeleteEmailNode",
    "VisualMoveEmailNode",
    # error_handling (TryNode moved to control_flow)
    "VisualRetryNode",
    "VisualRetrySuccessNode",
    "VisualRetryFailNode",
    "VisualThrowErrorNode",
    "VisualWebhookNotifyNode",
    "VisualOnErrorNode",
    "VisualErrorRecoveryNode",
    "VisualLogErrorNode",
    "VisualAssertNode",
    # file_operations
    "VisualReadFileNode",
    "VisualWriteFileNode",
    "VisualAppendFileNode",
    "VisualDeleteFileNode",
    "VisualCopyFileNode",
    "VisualMoveFileNode",
    "VisualFileExistsNode",
    "VisualGetFileSizeNode",
    "VisualGetFileInfoNode",
    "VisualListFilesNode",
    "VisualReadCsvNode",
    "VisualWriteCsvNode",
    "VisualReadJsonNode",
    "VisualWriteJsonNode",
    "VisualZipFilesNode",
    "VisualUnzipFileNode",
    "VisualParseXMLNode",
    "VisualReadXMLFileNode",
    "VisualWriteXMLFileNode",
    "VisualXPathQueryNode",
    "VisualGetXMLElementNode",
    "VisualGetXMLAttributeNode",
    "VisualXMLToJsonNode",
    "VisualJsonToXMLNode",
    "VisualReadPDFTextNode",
    "VisualGetPDFInfoNode",
    "VisualMergePDFsNode",
    "VisualSplitPDFNode",
    "VisualExtractPDFPagesNode",
    "VisualPDFToImagesNode",
    "VisualFTPConnectNode",
    "VisualFTPUploadNode",
    "VisualFTPDownloadNode",
    "VisualFTPListNode",
    "VisualFTPDeleteNode",
    "VisualFTPMakeDirNode",
    "VisualFTPRemoveDirNode",
    "VisualFTPRenameNode",
    "VisualFTPDisconnectNode",
    "VisualFTPGetSizeNode",
    # scripts
    "VisualRunPythonScriptNode",
    "VisualRunPythonFileNode",
    "VisualEvalExpressionNode",
    "VisualRunBatchScriptNode",
    "VisualRunJavaScriptNode",
    # system
    "VisualClipboardCopyNode",
    "VisualClipboardPasteNode",
    "VisualClipboardClearNode",
    "VisualMessageBoxNode",
    "VisualInputDialogNode",
    "VisualTooltipNode",
    "VisualRunCommandNode",
    "VisualRunPowerShellNode",
    "VisualGetServiceStatusNode",
    "VisualStartServiceNode",
    "VisualStopServiceNode",
    "VisualRestartServiceNode",
    "VisualListServicesNode",
    # utility
    "VisualRandomNumberNode",
    "VisualRandomChoiceNode",
    "VisualRandomStringNode",
    "VisualRandomUUIDNode",
    "VisualShuffleListNode",
    "VisualGetCurrentDateTimeNode",
    "VisualFormatDateTimeNode",
    "VisualParseDateTimeNode",
    "VisualDateTimeAddNode",
    "VisualDateTimeDiffNode",
    "VisualDateTimeCompareNode",
    "VisualGetTimestampNode",
    "VisualTextSplitNode",
    "VisualTextReplaceNode",
    "VisualTextTrimNode",
    "VisualTextCaseNode",
    "VisualTextPadNode",
    "VisualTextSubstringNode",
    "VisualTextContainsNode",
    "VisualTextStartsWithNode",
    "VisualTextEndsWithNode",
    "VisualTextLinesNode",
    "VisualTextReverseNode",
    "VisualTextCountNode",
    "VisualTextJoinNode",
    "VisualTextExtractNode",
    # office_automation
    "VisualExcelOpenNode",
    "VisualExcelReadCellNode",
    "VisualExcelWriteCellNode",
    "VisualExcelGetRangeNode",
    "VisualExcelCloseNode",
    "VisualWordOpenNode",
    "VisualWordGetTextNode",
    "VisualWordReplaceTextNode",
    "VisualWordCloseNode",
    "VisualOutlookSendEmailNode",
    "VisualOutlookReadEmailsNode",
    "VisualOutlookGetInboxCountNode",
    # rest_api
    "VisualHttpRequestNode",
    "VisualSetHttpHeadersNode",
    "VisualHttpAuthNode",
    "VisualParseJsonResponseNode",
    "VisualHttpDownloadFileNode",
    "VisualHttpUploadFileNode",
    "VisualBuildUrlNode",
    # variable
    "VisualSetVariableNode",
    "VisualGetVariableNode",
    "VisualIncrementVariableNode",
    # triggers
    "VisualWebhookTriggerNode",
    "VisualScheduleTriggerNode",
    "VisualFileWatchTriggerNode",
    "VisualEmailTriggerNode",
    "VisualAppEventTriggerNode",
    "VisualErrorTriggerNode",
    "VisualWorkflowCallTriggerNode",
    "VisualFormTriggerNode",
    "VisualChatTriggerNode",
    "VisualRSSFeedTriggerNode",
    "VisualSSETriggerNode",
    # triggers - Messaging
    "VisualTelegramTriggerNode",
    "VisualWhatsAppTriggerNode",
    # triggers - Google
    "VisualGmailTriggerNode",
    "VisualDriveTriggerNode",
    "VisualSheetsTriggerNode",
    "VisualCalendarTriggerNode",
    # ai_ml
    "VisualLLMCompletionNode",
    "VisualLLMChatNode",
    "VisualLLMExtractDataNode",
    "VisualLLMSummarizeNode",
    "VisualLLMClassifyNode",
    "VisualLLMTranslateNode",
    # document
    "VisualClassifyDocumentNode",
    "VisualExtractFormNode",
    "VisualExtractInvoiceNode",
    "VisualExtractTableNode",
    "VisualValidateExtractionNode",
    # messaging - Telegram Send
    "VisualTelegramSendMessageNode",
    "VisualTelegramSendPhotoNode",
    "VisualTelegramSendDocumentNode",
    "VisualTelegramSendLocationNode",
    # messaging - Telegram Actions
    "VisualTelegramEditMessageNode",
    "VisualTelegramDeleteMessageNode",
    "VisualTelegramSendMediaGroupNode",
    "VisualTelegramAnswerCallbackNode",
    "VisualTelegramGetUpdatesNode",
    # messaging - WhatsApp
    "VisualWhatsAppSendMessageNode",
    "VisualWhatsAppSendTemplateNode",
    "VisualWhatsAppSendImageNode",
    "VisualWhatsAppSendDocumentNode",
    "VisualWhatsAppSendVideoNode",
    "VisualWhatsAppSendLocationNode",
    "VisualWhatsAppSendInteractiveNode",
    # google - Calendar Event (8)
    "VisualCalendarListEventsNode",
    "VisualCalendarGetEventNode",
    "VisualCalendarCreateEventNode",
    "VisualCalendarUpdateEventNode",
    "VisualCalendarDeleteEventNode",
    "VisualCalendarQuickAddNode",
    "VisualCalendarMoveEventNode",
    "VisualCalendarGetFreeBusyNode",
    # google - Calendar Management (4)
    "VisualCalendarListCalendarsNode",
    "VisualCalendarGetCalendarNode",
    "VisualCalendarCreateCalendarNode",
    "VisualCalendarDeleteCalendarNode",
    # google - Gmail Send (6)
    "VisualGmailSendEmailNode",
    "VisualGmailSendWithAttachmentNode",
    "VisualGmailReplyToEmailNode",
    "VisualGmailForwardEmailNode",
    "VisualGmailCreateDraftNode",
    "VisualGmailSendDraftNode",
    # google - Gmail Read (5)
    "VisualGmailGetEmailNode",
    "VisualGmailListEmailsNode",
    "VisualGmailSearchEmailsNode",
    "VisualGmailGetThreadNode",
    "VisualGmailGetAttachmentNode",
    # google - Gmail Management (7)
    "VisualGmailModifyLabelsNode",
    "VisualGmailMoveToTrashNode",
    "VisualGmailMarkAsReadNode",
    "VisualGmailMarkAsUnreadNode",
    "VisualGmailStarEmailNode",
    "VisualGmailArchiveEmailNode",
    "VisualGmailDeleteEmailNode",
    # google - Gmail Batch (3)
    "VisualGmailBatchSendNode",
    "VisualGmailBatchModifyNode",
    "VisualGmailBatchDeleteNode",
    # google - Sheets Cell (5)
    "VisualSheetsGetCellNode",
    "VisualSheetsSetCellNode",
    "VisualSheetsGetRangeNode",
    "VisualSheetsWriteRangeNode",
    "VisualSheetsClearRangeNode",
    # google - Sheets Sheet (6)
    "VisualSheetsCreateSpreadsheetNode",
    "VisualSheetsGetSpreadsheetNode",
    "VisualSheetsAddSheetNode",
    "VisualSheetsDeleteSheetNode",
    "VisualSheetsDuplicateSheetNode",
    "VisualSheetsRenameSheetNode",
    # google - Sheets Row/Column (5)
    "VisualSheetsAppendRowNode",
    "VisualSheetsInsertRowNode",
    "VisualSheetsDeleteRowNode",
    "VisualSheetsInsertColumnNode",
    "VisualSheetsDeleteColumnNode",
    # google - Sheets Format (2)
    "VisualSheetsFormatCellsNode",
    "VisualSheetsAutoResizeNode",
    # google - Sheets Batch (3)
    "VisualSheetsBatchUpdateNode",
    "VisualSheetsBatchGetNode",
    "VisualSheetsBatchClearNode",
    # google - Docs Document (3)
    "VisualDocsCreateDocumentNode",
    "VisualDocsGetDocumentNode",
    "VisualDocsGetContentNode",
    # google - Docs Text (2)
    "VisualDocsInsertTextNode",
    "VisualDocsReplaceTextNode",
    # google - Docs Formatting (3)
    "VisualDocsInsertTableNode",
    "VisualDocsInsertImageNode",
    "VisualDocsUpdateStyleNode",
    # google - Drive File (7)
    "VisualDriveUploadFileNode",
    "VisualDriveDownloadFileNode",
    "VisualDriveDeleteFileNode",
    "VisualDriveCopyFileNode",
    "VisualDriveMoveFileNode",
    "VisualDriveRenameFileNode",
    "VisualDriveGetFileNode",
    # google - Drive Folder (3)
    "VisualDriveCreateFolderNode",
    "VisualDriveListFilesNode",
    "VisualDriveSearchFilesNode",
    # google - Drive Permissions (3)
    "VisualDriveShareFileNode",
    "VisualDriveRemovePermissionNode",
    "VisualDriveGetPermissionsNode",
    # google - Drive Export (1)
    "VisualDriveExportFileNode",
    # google - Drive Batch (3)
    "VisualDriveBatchDeleteNode",
    "VisualDriveBatchMoveNode",
    "VisualDriveBatchCopyNode",
]

# =============================================================================
# ALL_VISUAL_NODE_CLASSES - For node registration
# =============================================================================

# Collect all classes from this module's __all__ list
_THIS_MODULE_CLASSES = [globals()[name] for name in __all__]

# Import extended nodes from old location (until migration is complete)
try:
    from casare_rpa.presentation.canvas.visual_nodes.extended_visual_nodes import (
        EXTENDED_VISUAL_NODE_CLASSES,
    )

    _EXTENDED_CLASSES = EXTENDED_VISUAL_NODE_CLASSES
except ImportError:
    _EXTENDED_CLASSES = []

# Combine all classes: this module + extended
# Note: data_operations nodes are now in _THIS_MODULE_CLASSES
ALL_VISUAL_NODE_CLASSES = _THIS_MODULE_CLASSES + _EXTENDED_CLASSES

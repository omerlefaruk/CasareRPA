"""
CasareRPA Visual Nodes - Organized by Category

All visual nodes organized into categories for better navigation.
Uses lazy loading to improve startup performance.
"""

import importlib
from typing import TYPE_CHECKING, Any, Dict, List, Type

# Type hints for IDE support - these don't actually import at runtime
if TYPE_CHECKING:
    from .basic.nodes import VisualStartNode, VisualEndNode, VisualCommentNode
    # Add other type hints as needed for IDE support


# =============================================================================
# LAZY LOADING REGISTRY
# =============================================================================

# Maps visual node class names to their module paths (relative to visual_nodes)
_VISUAL_NODE_REGISTRY: Dict[str, str] = {
    # Basic (3 nodes)
    "VisualStartNode": "basic.nodes",
    "VisualEndNode": "basic.nodes",
    "VisualCommentNode": "basic.nodes",
    # Browser (26 nodes)
    "VisualLaunchBrowserNode": "browser.nodes",
    "VisualCloseBrowserNode": "browser.nodes",
    "VisualNewTabNode": "browser.nodes",
    "VisualGetAllImagesNode": "browser.nodes",
    "VisualDownloadFileNode": "browser.nodes",
    "VisualGoToURLNode": "browser.nodes",
    "VisualGoBackNode": "browser.nodes",
    "VisualGoForwardNode": "browser.nodes",
    "VisualRefreshPageNode": "browser.nodes",
    "VisualClickElementNode": "browser.nodes",
    "VisualTypeTextNode": "browser.nodes",
    "VisualSelectDropdownNode": "browser.nodes",
    "VisualImageClickNode": "browser.nodes",
    "VisualPressKeyNode": "browser.nodes",
    "VisualExtractTextNode": "browser.nodes",
    "VisualGetAttributeNode": "browser.nodes",
    "VisualScreenshotNode": "browser.nodes",
    "VisualTableScraperNode": "browser.nodes",
    "VisualWaitNode": "browser.nodes",
    "VisualWaitForElementNode": "browser.nodes",
    "VisualWaitForNavigationNode": "browser.nodes",
    "VisualFormFieldNode": "browser.nodes",
    "VisualFormFillerNode": "browser.nodes",
    "VisualDetectFormsNode": "browser.nodes",
    # Smart Selector AI nodes
    "VisualSmartSelectorNode": "browser.nodes",
    "VisualSmartSelectorOptionsNode": "browser.nodes",
    "VisualRefineSelectorNode": "browser.nodes",
    # Browser Evaluate (JavaScript execution)
    "VisualBrowserEvaluateNode": "browser.evaluate_node",
    # Control Flow (16 nodes)
    "VisualIfNode": "control_flow.nodes",
    "VisualForLoopNode": "control_flow.nodes",
    "VisualForLoopStartNode": "control_flow.nodes",
    "VisualForLoopEndNode": "control_flow.nodes",
    "VisualWhileLoopNode": "control_flow.nodes",
    "VisualWhileLoopStartNode": "control_flow.nodes",
    "VisualWhileLoopEndNode": "control_flow.nodes",
    "VisualBreakNode": "control_flow.nodes",
    "VisualContinueNode": "control_flow.nodes",
    "VisualMergeNode": "control_flow.nodes",
    "VisualSwitchNode": "control_flow.nodes",
    "VisualTryCatchFinallyNode": "control_flow.nodes",
    "VisualTryNode": "control_flow.nodes",
    "VisualCatchNode": "control_flow.nodes",
    "VisualFinallyNode": "control_flow.nodes",
    # Database (10 nodes)
    "VisualDatabaseConnectNode": "database.nodes",
    "VisualExecuteQueryNode": "database.nodes",
    "VisualExecuteNonQueryNode": "database.nodes",
    "VisualBeginTransactionNode": "database.nodes",
    "VisualCommitTransactionNode": "database.nodes",
    "VisualRollbackTransactionNode": "database.nodes",
    "VisualCloseDatabaseNode": "database.nodes",
    "VisualTableExistsNode": "database.nodes",
    "VisualGetTableColumnsNode": "database.nodes",
    "VisualExecuteBatchNode": "database.nodes",
    # Data Operations (32 nodes)
    "VisualConcatenateNode": "data_operations.nodes",
    "VisualFormatStringNode": "data_operations.nodes",
    "VisualRegexMatchNode": "data_operations.nodes",
    "VisualRegexReplaceNode": "data_operations.nodes",
    "VisualMathOperationNode": "data_operations.nodes",
    "VisualComparisonNode": "data_operations.nodes",
    "VisualCreateListNode": "data_operations.nodes",
    "VisualListGetItemNode": "data_operations.nodes",
    "VisualJsonParseNode": "data_operations.nodes",
    "VisualGetPropertyNode": "data_operations.nodes",
    "VisualListLengthNode": "data_operations.nodes",
    "VisualListAppendNode": "data_operations.nodes",
    "VisualListContainsNode": "data_operations.nodes",
    "VisualListSliceNode": "data_operations.nodes",
    "VisualListJoinNode": "data_operations.nodes",
    "VisualListSortNode": "data_operations.nodes",
    "VisualListReverseNode": "data_operations.nodes",
    "VisualListUniqueNode": "data_operations.nodes",
    "VisualListFilterNode": "data_operations.nodes",
    "VisualListMapNode": "data_operations.nodes",
    "VisualListReduceNode": "data_operations.nodes",
    "VisualListFlattenNode": "data_operations.nodes",
    "VisualDictGetNode": "data_operations.nodes",
    "VisualDictSetNode": "data_operations.nodes",
    "VisualDictRemoveNode": "data_operations.nodes",
    "VisualDictMergeNode": "data_operations.nodes",
    "VisualDictKeysNode": "data_operations.nodes",
    "VisualDictValuesNode": "data_operations.nodes",
    "VisualDictHasKeyNode": "data_operations.nodes",
    "VisualCreateDictNode": "data_operations.nodes",
    "VisualDictToJsonNode": "data_operations.nodes",
    "VisualDictItemsNode": "data_operations.nodes",
    "VisualDataCompareNode": "data_operations.nodes",
    # Desktop Automation (36 nodes)
    "VisualLaunchApplicationNode": "desktop_automation.nodes",
    "VisualCloseApplicationNode": "desktop_automation.nodes",
    "VisualActivateWindowNode": "desktop_automation.nodes",
    "VisualGetWindowListNode": "desktop_automation.nodes",
    "VisualFindElementNode": "desktop_automation.nodes",
    "VisualClickElementDesktopNode": "desktop_automation.nodes",
    "VisualTypeTextDesktopNode": "desktop_automation.nodes",
    "VisualGetElementTextNode": "desktop_automation.nodes",
    "VisualGetElementPropertyNode": "desktop_automation.nodes",
    "VisualResizeWindowNode": "desktop_automation.nodes",
    "VisualMoveWindowNode": "desktop_automation.nodes",
    "VisualMaximizeWindowNode": "desktop_automation.nodes",
    "VisualMinimizeWindowNode": "desktop_automation.nodes",
    "VisualRestoreWindowNode": "desktop_automation.nodes",
    "VisualGetWindowPropertiesNode": "desktop_automation.nodes",
    "VisualSetWindowStateNode": "desktop_automation.nodes",
    "VisualSelectFromDropdownNode": "desktop_automation.nodes",
    "VisualCheckCheckboxNode": "desktop_automation.nodes",
    "VisualSelectRadioButtonNode": "desktop_automation.nodes",
    "VisualSelectTabNode": "desktop_automation.nodes",
    "VisualExpandTreeItemNode": "desktop_automation.nodes",
    "VisualScrollElementNode": "desktop_automation.nodes",
    "VisualMoveMouseNode": "desktop_automation.nodes",
    "VisualMouseClickNode": "desktop_automation.nodes",
    "VisualSendKeysNode": "desktop_automation.nodes",
    "VisualSendHotKeyNode": "desktop_automation.nodes",
    "VisualGetMousePositionNode": "desktop_automation.nodes",
    "VisualDragMouseNode": "desktop_automation.nodes",
    "VisualDesktopWaitForElementNode": "desktop_automation.nodes",
    "VisualWaitForWindowNode": "desktop_automation.nodes",
    "VisualVerifyElementExistsNode": "desktop_automation.nodes",
    "VisualVerifyElementPropertyNode": "desktop_automation.nodes",
    "VisualCaptureScreenshotNode": "desktop_automation.nodes",
    "VisualCaptureElementImageNode": "desktop_automation.nodes",
    "VisualOCRExtractTextNode": "desktop_automation.nodes",
    "VisualCompareImagesNode": "desktop_automation.nodes",
    # Email (8 nodes)
    "VisualSendEmailNode": "email.nodes",
    "VisualReadEmailsNode": "email.nodes",
    "VisualGetEmailContentNode": "email.nodes",
    "VisualSaveAttachmentNode": "email.nodes",
    "VisualFilterEmailsNode": "email.nodes",
    "VisualMarkEmailNode": "email.nodes",
    "VisualDeleteEmailNode": "email.nodes",
    "VisualMoveEmailNode": "email.nodes",
    # Error Handling (10 nodes)
    "VisualRetryNode": "error_handling.nodes",
    "VisualRetrySuccessNode": "error_handling.nodes",
    "VisualRetryFailNode": "error_handling.nodes",
    "VisualThrowErrorNode": "error_handling.nodes",
    "VisualWebhookNotifyNode": "error_handling.nodes",
    "VisualOnErrorNode": "error_handling.nodes",
    "VisualErrorRecoveryNode": "error_handling.nodes",
    "VisualLogErrorNode": "error_handling.nodes",
    "VisualAssertNode": "error_handling.nodes",
    "VisualAIRecoveryNode": "error_handling.nodes",
    # File Operations - Super Nodes
    "VisualFileSystemSuperNode": "file_operations.super_nodes",
    # File Operations - Structured Data
    "VisualReadCSVNode": "file_operations.nodes",
    "VisualWriteCSVNode": "file_operations.nodes",
    "VisualReadJSONFileNode": "file_operations.nodes",
    "VisualWriteJSONFileNode": "file_operations.nodes",
    "VisualZipFilesNode": "file_operations.nodes",
    "VisualUnzipFilesNode": "file_operations.nodes",
    "VisualImageConvertNode": "file_operations.nodes",
    # Text Operations - Super Nodes
    "VisualTextSuperNode": "text.super_nodes",
    # Desktop Automation - Super Nodes
    "VisualWindowManagementSuperNode": "desktop_automation.super_nodes",
    # File Operations - XML, PDF, FTP (legacy nodes removed, now using super nodes)
    "VisualParseXMLNode": "file_operations.nodes",
    "VisualReadXMLFileNode": "file_operations.nodes",
    "VisualWriteXMLFileNode": "file_operations.nodes",
    "VisualXPathQueryNode": "file_operations.nodes",
    "VisualGetXMLElementNode": "file_operations.nodes",
    "VisualGetXMLAttributeNode": "file_operations.nodes",
    "VisualXMLToJsonNode": "file_operations.nodes",
    "VisualJsonToXMLNode": "file_operations.nodes",
    "VisualReadPDFTextNode": "file_operations.nodes",
    "VisualGetPDFInfoNode": "file_operations.nodes",
    "VisualMergePDFsNode": "file_operations.nodes",
    "VisualSplitPDFNode": "file_operations.nodes",
    "VisualExtractPDFPagesNode": "file_operations.nodes",
    "VisualPDFToImagesNode": "file_operations.nodes",
    "VisualFTPConnectNode": "file_operations.nodes",
    "VisualFTPUploadNode": "file_operations.nodes",
    "VisualFTPDownloadNode": "file_operations.nodes",
    "VisualFTPListNode": "file_operations.nodes",
    "VisualFTPDeleteNode": "file_operations.nodes",
    "VisualFTPMakeDirNode": "file_operations.nodes",
    "VisualFTPRemoveDirNode": "file_operations.nodes",
    "VisualFTPRenameNode": "file_operations.nodes",
    "VisualFTPDisconnectNode": "file_operations.nodes",
    "VisualFTPGetSizeNode": "file_operations.nodes",
    # Scripts (5 nodes)
    "VisualRunPythonScriptNode": "scripts.nodes",
    "VisualRunPythonFileNode": "scripts.nodes",
    "VisualEvalExpressionNode": "scripts.nodes",
    "VisualRunBatchScriptNode": "scripts.nodes",
    "VisualRunJavaScriptNode": "scripts.nodes",
    # System (40 nodes)
    "VisualClipboardCopyNode": "system.nodes",
    "VisualClipboardPasteNode": "system.nodes",
    "VisualClipboardClearNode": "system.nodes",
    "VisualMessageBoxNode": "system.nodes",
    "VisualInputDialogNode": "system.nodes",
    "VisualTooltipNode": "system.nodes",
    "VisualSystemNotificationNode": "system.nodes",
    "VisualConfirmDialogNode": "system.nodes",
    "VisualProgressDialogNode": "system.nodes",
    "VisualFilePickerDialogNode": "system.nodes",
    "VisualFolderPickerDialogNode": "system.nodes",
    "VisualColorPickerDialogNode": "system.nodes",
    "VisualDateTimePickerDialogNode": "system.nodes",
    "VisualSnackbarNode": "system.nodes",
    "VisualBalloonTipNode": "system.nodes",
    "VisualRunCommandNode": "system.nodes",
    "VisualRunPowerShellNode": "system.nodes",
    "VisualGetServiceStatusNode": "system.nodes",
    "VisualStartServiceNode": "system.nodes",
    "VisualStopServiceNode": "system.nodes",
    "VisualRestartServiceNode": "system.nodes",
    "VisualListServicesNode": "system.nodes",
    # New dialog nodes (9 nodes)
    "VisualListPickerDialogNode": "system.nodes",
    "VisualMultilineInputDialogNode": "system.nodes",
    "VisualCredentialDialogNode": "system.nodes",
    "VisualFormDialogNode": "system.nodes",
    "VisualImagePreviewDialogNode": "system.nodes",
    "VisualTableDialogNode": "system.nodes",
    "VisualWizardDialogNode": "system.nodes",
    "VisualSplashScreenNode": "system.nodes",
    "VisualAudioAlertNode": "system.nodes",
    # System utilities (6 nodes)
    "VisualScreenRegionPickerNode": "system.nodes",
    "VisualVolumeControlNode": "system.nodes",
    "VisualProcessListNode": "system.nodes",
    "VisualProcessKillNode": "system.nodes",
    "VisualEnvironmentVariableNode": "system.nodes",
    "VisualSystemInfoNode": "system.nodes",
    # Quick nodes (3 nodes)
    "VisualHotkeyWaitNode": "system.nodes",
    "VisualBeepNode": "system.nodes",
    "VisualClipboardMonitorNode": "system.nodes",
    # Utility system nodes (6 nodes)
    "VisualFileWatcherNode": "system.nodes",
    "VisualQRCodeNode": "system.nodes",
    "VisualBase64Node": "system.nodes",
    "VisualUUIDGeneratorNode": "system.nodes",
    "VisualAssertSystemNode": "system.nodes",
    "VisualLogToFileNode": "system.nodes",
    # Media nodes (3 nodes)
    "VisualTextToSpeechNode": "system.nodes",
    "VisualPDFPreviewDialogNode": "system.nodes",
    "VisualWebcamCaptureNode": "system.nodes",
    # Utility (26 nodes)
    "VisualRandomNumberNode": "utility.nodes",
    "VisualRandomChoiceNode": "utility.nodes",
    "VisualRandomStringNode": "utility.nodes",
    "VisualRandomUUIDNode": "utility.nodes",
    "VisualShuffleListNode": "utility.nodes",
    "VisualGetCurrentDateTimeNode": "utility.nodes",
    "VisualFormatDateTimeNode": "utility.nodes",
    "VisualParseDateTimeNode": "utility.nodes",
    "VisualDateTimeAddNode": "utility.nodes",
    "VisualDateTimeDiffNode": "utility.nodes",
    "VisualDateTimeCompareNode": "utility.nodes",
    "VisualGetTimestampNode": "utility.nodes",
    "VisualTextSplitNode": "utility.nodes",
    "VisualTextReplaceNode": "utility.nodes",
    "VisualTextTrimNode": "utility.nodes",
    "VisualTextCaseNode": "utility.nodes",
    "VisualTextPadNode": "utility.nodes",
    "VisualTextSubstringNode": "utility.nodes",
    "VisualTextContainsNode": "utility.nodes",
    "VisualTextStartsWithNode": "utility.nodes",
    "VisualTextEndsWithNode": "utility.nodes",
    "VisualTextLinesNode": "utility.nodes",
    "VisualTextReverseNode": "utility.nodes",
    "VisualTextCountNode": "utility.nodes",
    "VisualTextJoinNode": "utility.nodes",
    "VisualTextExtractNode": "utility.nodes",
    # Reroute (1 node)
    "VisualRerouteNode": "utility.reroute_node",
    # Office Automation (12 nodes)
    "VisualExcelOpenNode": "office_automation.nodes",
    "VisualExcelReadCellNode": "office_automation.nodes",
    "VisualExcelWriteCellNode": "office_automation.nodes",
    "VisualExcelGetRangeNode": "office_automation.nodes",
    "VisualExcelCloseNode": "office_automation.nodes",
    "VisualWordOpenNode": "office_automation.nodes",
    "VisualWordGetTextNode": "office_automation.nodes",
    "VisualWordReplaceTextNode": "office_automation.nodes",
    "VisualWordCloseNode": "office_automation.nodes",
    "VisualOutlookSendEmailNode": "office_automation.nodes",
    "VisualOutlookReadEmailsNode": "office_automation.nodes",
    "VisualOutlookGetInboxCountNode": "office_automation.nodes",
    # REST API (8 nodes)
    "VisualHttpRequestNode": "rest_api.nodes",
    "VisualSetHttpHeadersNode": "rest_api.nodes",
    "VisualHttpAuthNode": "rest_api.nodes",
    "VisualParseJsonResponseNode": "rest_api.nodes",
    "VisualHttpDownloadFileNode": "rest_api.nodes",
    "VisualHttpUploadFileNode": "rest_api.nodes",
    "VisualBuildUrlNode": "rest_api.nodes",
    "VisualHttpSuperNode": "rest_api.nodes",
    # Variable (3 nodes)
    "VisualSetVariableNode": "variable.nodes",
    "VisualGetVariableNode": "variable.nodes",
    "VisualIncrementVariableNode": "variable.nodes",
    # Triggers (17 nodes)
    "VisualWebhookTriggerNode": "triggers.nodes",
    "VisualScheduleTriggerNode": "triggers.nodes",
    "VisualFileWatchTriggerNode": "triggers.nodes",
    "VisualEmailTriggerNode": "triggers.nodes",
    "VisualAppEventTriggerNode": "triggers.nodes",
    "VisualErrorTriggerNode": "triggers.nodes",
    "VisualWorkflowCallTriggerNode": "triggers.nodes",
    "VisualFormTriggerNode": "triggers.nodes",
    "VisualChatTriggerNode": "triggers.nodes",
    "VisualRSSFeedTriggerNode": "triggers.nodes",
    "VisualSSETriggerNode": "triggers.nodes",
    "VisualTelegramTriggerNode": "triggers.nodes",
    "VisualWhatsAppTriggerNode": "triggers.nodes",
    "VisualGmailTriggerNode": "triggers.nodes",
    "VisualDriveTriggerNode": "triggers.nodes",
    "VisualSheetsTriggerNode": "triggers.nodes",
    "VisualCalendarTriggerNode": "triggers.nodes",
    # AI/ML (10 nodes)
    "VisualLLMCompletionNode": "ai_ml.nodes",
    "VisualLLMChatNode": "ai_ml.nodes",
    "VisualLLMExtractDataNode": "ai_ml.nodes",
    "VisualLLMSummarizeNode": "ai_ml.nodes",
    "VisualLLMClassifyNode": "ai_ml.nodes",
    "VisualLLMTranslateNode": "ai_ml.nodes",
    # AI Condition nodes
    "VisualAIConditionNode": "ai_ml.nodes",
    "VisualAISwitchNode": "ai_ml.nodes",
    "VisualAIDecisionTableNode": "ai_ml.nodes",
    # AI Agent
    "VisualAIAgentNode": "ai_ml.nodes",
    # Document AI (5 nodes)
    "VisualClassifyDocumentNode": "document.nodes",
    "VisualExtractFormNode": "document.nodes",
    "VisualExtractInvoiceNode": "document.nodes",
    "VisualExtractTableNode": "document.nodes",
    "VisualValidateExtractionNode": "document.nodes",
    # Messaging - Telegram Send (4 nodes)
    "VisualTelegramSendMessageNode": "messaging.nodes",
    "VisualTelegramSendPhotoNode": "messaging.nodes",
    "VisualTelegramSendDocumentNode": "messaging.nodes",
    "VisualTelegramSendLocationNode": "messaging.nodes",
    # Messaging - Telegram Actions (5 nodes)
    "VisualTelegramEditMessageNode": "messaging.telegram_action_nodes",
    "VisualTelegramDeleteMessageNode": "messaging.telegram_action_nodes",
    "VisualTelegramSendMediaGroupNode": "messaging.telegram_action_nodes",
    "VisualTelegramAnswerCallbackNode": "messaging.telegram_action_nodes",
    "VisualTelegramGetUpdatesNode": "messaging.telegram_action_nodes",
    # Messaging - WhatsApp (7 nodes)
    "VisualWhatsAppSendMessageNode": "messaging.whatsapp_nodes",
    "VisualWhatsAppSendTemplateNode": "messaging.whatsapp_nodes",
    "VisualWhatsAppSendImageNode": "messaging.whatsapp_nodes",
    "VisualWhatsAppSendDocumentNode": "messaging.whatsapp_nodes",
    "VisualWhatsAppSendVideoNode": "messaging.whatsapp_nodes",
    "VisualWhatsAppSendLocationNode": "messaging.whatsapp_nodes",
    "VisualWhatsAppSendInteractiveNode": "messaging.whatsapp_nodes",
    # Google Calendar (12 nodes)
    "VisualCalendarListEventsNode": "google",
    "VisualCalendarGetEventNode": "google",
    "VisualCalendarCreateEventNode": "google",
    "VisualCalendarUpdateEventNode": "google",
    "VisualCalendarDeleteEventNode": "google",
    "VisualCalendarQuickAddNode": "google",
    "VisualCalendarMoveEventNode": "google",
    "VisualCalendarGetFreeBusyNode": "google",
    "VisualCalendarListCalendarsNode": "google",
    "VisualCalendarGetCalendarNode": "google",
    "VisualCalendarCreateCalendarNode": "google",
    "VisualCalendarDeleteCalendarNode": "google",
    # Google Gmail (21 nodes)
    "VisualGmailSendEmailNode": "google",
    "VisualGmailSendWithAttachmentNode": "google",
    "VisualGmailReplyToEmailNode": "google",
    "VisualGmailForwardEmailNode": "google",
    "VisualGmailCreateDraftNode": "google",
    "VisualGmailSendDraftNode": "google",
    "VisualGmailGetEmailNode": "google",
    "VisualGmailListEmailsNode": "google",
    "VisualGmailSearchEmailsNode": "google",
    "VisualGmailGetThreadNode": "google",
    "VisualGmailGetAttachmentNode": "google",
    "VisualGmailModifyLabelsNode": "google",
    "VisualGmailMoveToTrashNode": "google",
    "VisualGmailMarkAsReadNode": "google",
    "VisualGmailMarkAsUnreadNode": "google",
    "VisualGmailStarEmailNode": "google",
    "VisualGmailArchiveEmailNode": "google",
    "VisualGmailDeleteEmailNode": "google",
    "VisualGmailBatchSendNode": "google",
    "VisualGmailBatchModifyNode": "google",
    "VisualGmailBatchDeleteNode": "google",
    # Google Sheets (21 nodes)
    "VisualSheetsGetCellNode": "google",
    "VisualSheetsSetCellNode": "google",
    "VisualSheetsGetRangeNode": "google",
    "VisualSheetsWriteRangeNode": "google",
    "VisualSheetsClearRangeNode": "google",
    "VisualSheetsCreateSpreadsheetNode": "google",
    "VisualSheetsGetSpreadsheetNode": "google",
    "VisualSheetsAddSheetNode": "google",
    "VisualSheetsDeleteSheetNode": "google",
    "VisualSheetsDuplicateSheetNode": "google",
    "VisualSheetsRenameSheetNode": "google",
    "VisualSheetsAppendRowNode": "google",
    "VisualSheetsInsertRowNode": "google",
    "VisualSheetsDeleteRowNode": "google",
    "VisualSheetsInsertColumnNode": "google",
    "VisualSheetsDeleteColumnNode": "google",
    "VisualSheetsFormatCellsNode": "google",
    "VisualSheetsAutoResizeNode": "google",
    "VisualSheetsBatchUpdateNode": "google",
    "VisualSheetsBatchGetNode": "google",
    "VisualSheetsBatchClearNode": "google",
    # Google Docs (8 nodes)
    "VisualDocsCreateDocumentNode": "google",
    "VisualDocsGetDocumentNode": "google",
    "VisualDocsGetContentNode": "google",
    "VisualDocsInsertTextNode": "google",
    "VisualDocsReplaceTextNode": "google",
    "VisualDocsInsertTableNode": "google",
    "VisualDocsInsertImageNode": "google",
    "VisualDocsUpdateStyleNode": "google",
    # Google Drive (21 nodes)
    "VisualDriveUploadFileNode": "google",
    "VisualDriveDownloadFileNode": "google",
    "VisualDriveDownloadFolderNode": "google",
    "VisualDriveBatchDownloadNode": "google",
    "VisualDriveDeleteFileNode": "google",
    "VisualDriveCopyFileNode": "google",
    "VisualDriveMoveFileNode": "google",
    "VisualDriveRenameFileNode": "google",
    "VisualDriveGetFileNode": "google",
    "VisualDriveCreateFolderNode": "google",
    "VisualDriveListFilesNode": "google",
    "VisualDriveSearchFilesNode": "google",
    "VisualDriveShareFileNode": "google",
    "VisualDriveRemoveShareNode": "google",
    "VisualDriveGetPermissionsNode": "google",
    "VisualDriveCreateShareLinkNode": "google",
    "VisualDriveExportFileNode": "google",
    "VisualDriveBatchDeleteNode": "google",
    "VisualDriveBatchMoveNode": "google",
    "VisualDriveBatchCopyNode": "google",
    # Subflows (1 node)
    "VisualSubflowNode": "subflows.nodes",
    # Note: SubflowVisualNode is an alias available via import from subflows.nodes
    # but NOT registered here to avoid duplicate __identifier__ conflict
    # Workflow nodes (1 node)
    "VisualCallSubworkflowNode": "workflow",
}

# Cache for loaded modules and classes
_loaded_modules: Dict[str, Any] = {}
_loaded_classes: Dict[str, Type] = {}

# Cached list of all visual node classes (built on first access)
_all_visual_node_classes: List[Type] = None


def _lazy_import(name: str) -> Type:
    """
    Lazily import a visual node class by name.

    Args:
        name: The name of the visual node class to import

    Returns:
        The visual node class

    Raises:
        AttributeError: If the class doesn't exist
    """
    # Check cache first
    if name in _loaded_classes:
        return _loaded_classes[name]

    # Check if it's a known visual node class
    if name not in _VISUAL_NODE_REGISTRY:
        raise AttributeError(
            f"module 'casare_rpa.presentation.canvas.visual_nodes' has no attribute '{name}'"
        )

    module_name = _VISUAL_NODE_REGISTRY[name]

    # Load the module if not already loaded
    if module_name not in _loaded_modules:
        full_module_name = f".{module_name}"
        _loaded_modules[module_name] = importlib.import_module(
            full_module_name, package="casare_rpa.presentation.canvas.visual_nodes"
        )

    # Get the class from the module
    module = _loaded_modules[module_name]
    cls = getattr(module, name)

    # Cache and return
    _loaded_classes[name] = cls
    return cls


def __getattr__(name: str) -> Any:
    """
    Module-level __getattr__ for lazy loading.

    This is called when an attribute is accessed that doesn't exist
    in the module's namespace.
    """
    # Handle ALL_VISUAL_NODE_CLASSES specially - build it on first access
    if name == "ALL_VISUAL_NODE_CLASSES":
        return get_all_visual_node_classes()

    if name in _VISUAL_NODE_REGISTRY:
        return _lazy_import(name)

    # Handle special attributes
    if name == "__all__":
        return list(_VISUAL_NODE_REGISTRY.keys())

    raise AttributeError(
        f"module 'casare_rpa.presentation.canvas.visual_nodes' has no attribute '{name}'"
    )


def __dir__() -> List[str]:
    """Return the list of available attributes for tab completion."""
    return list(_VISUAL_NODE_REGISTRY.keys()) + [
        "ALL_VISUAL_NODE_CLASSES",
        "get_all_visual_node_classes",
        "preload_visual_nodes",
    ]


def get_all_visual_node_classes() -> List[Type]:
    """
    Get all visual node classes.

    This triggers loading of all modules on first call.
    The result is cached for subsequent calls.

    Returns:
        List of all visual node class objects
    """
    global _all_visual_node_classes

    if _all_visual_node_classes is None:
        _all_visual_node_classes = []
        for name in _VISUAL_NODE_REGISTRY:
            try:
                cls = _lazy_import(name)
                _all_visual_node_classes.append(cls)
            except Exception:
                # Skip classes that fail to import
                pass

        # Also try to import extended nodes
        try:
            from casare_rpa.presentation.canvas.visual_nodes.extended_visual_nodes import (
                EXTENDED_VISUAL_NODE_CLASSES,
            )

            _all_visual_node_classes.extend(EXTENDED_VISUAL_NODE_CLASSES)
        except ImportError:
            pass

    return _all_visual_node_classes


def preload_visual_nodes(node_names: List[str] = None) -> None:
    """
    Preload specific visual nodes or all visual nodes.

    This can be called during application startup to preload
    frequently used nodes, or in a background thread.

    Args:
        node_names: List of visual node class names to preload, or None for all
    """
    names_to_load = node_names if node_names else list(_VISUAL_NODE_REGISTRY.keys())
    for name in names_to_load:
        if name in _VISUAL_NODE_REGISTRY:
            try:
                _lazy_import(name)
            except Exception:
                pass


# =============================================================================
# __all__ - For explicit imports
# =============================================================================

__all__ = list(_VISUAL_NODE_REGISTRY.keys()) + [
    "ALL_VISUAL_NODE_CLASSES",
    "get_all_visual_node_classes",
    "preload_visual_nodes",
]

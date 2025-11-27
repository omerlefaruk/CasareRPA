"""
CasareRPA Visual Nodes - Organized by Category

All visual nodes organized into categories for better navigation.
"""

# Basic (3 nodes)
from .basic import (
    VisualStartNode,
    VisualEndNode,
    VisualCommentNode,
)

# Browser (18 nodes)
from .browser import (
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
    VisualExtractTextNode,
    VisualGetAttributeNode,
    VisualScreenshotNode,
    VisualWaitNode,
    VisualWaitForElementNode,
    VisualWaitForNavigationNode,
)

# Control Flow (10 nodes)
from .control_flow import (
    VisualIfNode,
    VisualForLoopNode,
    VisualForLoopStartNode,
    VisualForLoopEndNode,
    VisualWhileLoopNode,
    VisualWhileLoopStartNode,
    VisualWhileLoopEndNode,
    VisualBreakNode,
    VisualContinueNode,
    VisualSwitchNode,
)

# Database (10 nodes)
from .database import (
    VisualDatabaseConnectNode,
    VisualDatabaseDisconnectNode,
    VisualDatabaseExecuteQueryNode,
    VisualDatabaseFetchOneNode,
    VisualDatabaseFetchAllNode,
    VisualDatabaseCommitNode,
    VisualDatabaseRollbackNode,
    VisualDatabaseInsertNode,
    VisualDatabaseUpdateNode,
    VisualDatabaseDeleteNode,
)

# Data Operations (40 nodes) - NEW
from .data_operations import (
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
from .desktop_automation import (
    VisualLaunchApplicationNode,
    VisualCloseApplicationNode,
    VisualActivateWindowNode,
    VisualMinimizeWindowNode,
    VisualMaximizeWindowNode,
    VisualResizeWindowNode,
    VisualMoveWindowNode,
    VisualGetWindowTitleNode,
    VisualGetWindowPositionNode,
    VisualGetWindowSizeNode,
    VisualFindElementNode,
    VisualClickElementDesktopNode,
    VisualDoubleClickElementNode,
    VisualRightClickElementNode,
    VisualTypeIntoElementNode,
    VisualGetElementTextNode,
    VisualGetElementAttributeNode,
    VisualSetElementValueNode,
    VisualWaitForElementDesktopNode,
    VisualElementExistsNode,
    VisualMouseMoveNode,
    VisualMouseClickNode,
    VisualMouseDoubleClickNode,
    VisualMouseRightClickNode,
    VisualMouseDragNode,
    VisualMouseScrollNode,
    VisualKeyboardTypeNode,
    VisualKeyboardPressNode,
    VisualKeyboardHotkeyNode,
    VisualGetScreenshotNode,
    VisualFindImageNode,
    VisualClickImageNode,
    VisualWaitForImageNode,
    VisualGetActiveWindowNode,
    VisualListWindowsNode,
    VisualGetProcessListNode,
)

# Email (8 nodes)
from .email import (
    VisualSendEmailNode,
    VisualReadEmailNode,
    VisualFilterEmailNode,
    VisualGetEmailAttachmentsNode,
    VisualSaveEmailAttachmentNode,
    VisualDeleteEmailNode,
    VisualMarkEmailAsReadNode,
    VisualMoveEmailToFolderNode,
)

# Error Handling (10 nodes)
from .error_handling import (
    VisualTryNode,
    VisualCatchNode,
    VisualFinallyNode,
    VisualThrowNode,
    VisualRetryNode,
    VisualTimeoutNode,
    VisualAssertNode,
    VisualLogErrorNode,
    VisualIgnoreErrorNode,
    VisualErrorHandlerNode,
)

# File Operations (40 nodes)
from .file_operations import (
    # Basic file operations
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
    # CSV operations
    VisualReadCsvNode,
    VisualWriteCsvNode,
    # JSON operations
    VisualReadJsonNode,
    VisualWriteJsonNode,
    # ZIP operations
    VisualZipFilesNode,
    VisualUnzipFileNode,
    # XML operations
    VisualParseXMLNode,
    VisualReadXMLFileNode,
    VisualWriteXMLFileNode,
    VisualXPathQueryNode,
    VisualGetXMLElementNode,
    VisualGetXMLAttributeNode,
    VisualXMLToJsonNode,
    VisualJsonToXMLNode,
    # PDF operations
    VisualReadPDFTextNode,
    VisualGetPDFInfoNode,
    VisualMergePDFsNode,
    VisualSplitPDFNode,
    VisualExtractPDFPagesNode,
    VisualPDFToImagesNode,
    # FTP operations
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
from .scripts import (
    VisualRunPythonScriptNode,
    VisualRunPythonFileNode,
    VisualEvalExpressionNode,
    VisualRunBatchScriptNode,
    VisualRunJavaScriptNode,
)

# System (13 nodes)
from .system import (
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
from .utility import (
    # Random operations
    VisualRandomNumberNode,
    VisualRandomChoiceNode,
    VisualRandomStringNode,
    VisualRandomUUIDNode,
    VisualShuffleListNode,
    # DateTime operations
    VisualGetCurrentDateTimeNode,
    VisualFormatDateTimeNode,
    VisualParseDateTimeNode,
    VisualDateTimeAddNode,
    VisualDateTimeDiffNode,
    VisualDateTimeCompareNode,
    VisualGetTimestampNode,
    # Text operations
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
from .office_automation import (
    VisualExcelOpenNode,
    VisualExcelCloseNode,
    VisualExcelReadCellNode,
    VisualExcelWriteCellNode,
    VisualExcelReadRangeNode,
    VisualExcelWriteRangeNode,
    VisualExcelGetSheetNamesNode,
    VisualExcelSaveNode,
    VisualWordOpenNode,
    VisualWordCloseNode,
    VisualWordReplaceTextNode,
    VisualWordSaveNode,
)

# REST API (12 nodes)
from .rest_api import (
    VisualHttpRequestNode,
    VisualHttpGetNode,
    VisualHttpPostNode,
    VisualHttpPutNode,
    VisualHttpPatchNode,
    VisualHttpDeleteNode,
    VisualSetHttpHeadersNode,
    VisualHttpAuthNode,
    VisualParseJsonResponseNode,
    VisualHttpDownloadFileNode,
    VisualHttpUploadFileNode,
    VisualBuildUrlNode,
)

# Variable (3 nodes)
from .variable import (
    VisualSetVariableNode,
    VisualGetVariableNode,
    VisualIncrementVariableNode,
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
    "VisualExtractTextNode",
    "VisualGetAttributeNode",
    "VisualScreenshotNode",
    "VisualWaitNode",
    "VisualWaitForElementNode",
    "VisualWaitForNavigationNode",
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
    "VisualSwitchNode",
    # database
    "VisualDatabaseConnectNode",
    "VisualDatabaseDisconnectNode",
    "VisualDatabaseExecuteQueryNode",
    "VisualDatabaseFetchOneNode",
    "VisualDatabaseFetchAllNode",
    "VisualDatabaseCommitNode",
    "VisualDatabaseRollbackNode",
    "VisualDatabaseInsertNode",
    "VisualDatabaseUpdateNode",
    "VisualDatabaseDeleteNode",
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
    "VisualMinimizeWindowNode",
    "VisualMaximizeWindowNode",
    "VisualResizeWindowNode",
    "VisualMoveWindowNode",
    "VisualGetWindowTitleNode",
    "VisualGetWindowPositionNode",
    "VisualGetWindowSizeNode",
    "VisualFindElementNode",
    "VisualClickElementDesktopNode",
    "VisualDoubleClickElementNode",
    "VisualRightClickElementNode",
    "VisualTypeIntoElementNode",
    "VisualGetElementTextNode",
    "VisualGetElementAttributeNode",
    "VisualSetElementValueNode",
    "VisualWaitForElementDesktopNode",
    "VisualElementExistsNode",
    "VisualMouseMoveNode",
    "VisualMouseClickNode",
    "VisualMouseDoubleClickNode",
    "VisualMouseRightClickNode",
    "VisualMouseDragNode",
    "VisualMouseScrollNode",
    "VisualKeyboardTypeNode",
    "VisualKeyboardPressNode",
    "VisualKeyboardHotkeyNode",
    "VisualGetScreenshotNode",
    "VisualFindImageNode",
    "VisualClickImageNode",
    "VisualWaitForImageNode",
    "VisualGetActiveWindowNode",
    "VisualListWindowsNode",
    "VisualGetProcessListNode",
    # email
    "VisualSendEmailNode",
    "VisualReadEmailNode",
    "VisualFilterEmailNode",
    "VisualGetEmailAttachmentsNode",
    "VisualSaveEmailAttachmentNode",
    "VisualDeleteEmailNode",
    "VisualMarkEmailAsReadNode",
    "VisualMoveEmailToFolderNode",
    # error_handling
    "VisualTryNode",
    "VisualCatchNode",
    "VisualFinallyNode",
    "VisualThrowNode",
    "VisualRetryNode",
    "VisualTimeoutNode",
    "VisualAssertNode",
    "VisualLogErrorNode",
    "VisualIgnoreErrorNode",
    "VisualErrorHandlerNode",
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
    "VisualExcelCloseNode",
    "VisualExcelReadCellNode",
    "VisualExcelWriteCellNode",
    "VisualExcelReadRangeNode",
    "VisualExcelWriteRangeNode",
    "VisualExcelGetSheetNamesNode",
    "VisualExcelSaveNode",
    "VisualWordOpenNode",
    "VisualWordCloseNode",
    "VisualWordReplaceTextNode",
    "VisualWordSaveNode",
    # rest_api
    "VisualHttpRequestNode",
    "VisualHttpGetNode",
    "VisualHttpPostNode",
    "VisualHttpPutNode",
    "VisualHttpPatchNode",
    "VisualHttpDeleteNode",
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
]

# =============================================================================
# ALL_VISUAL_NODE_CLASSES - For node registration
# =============================================================================

# Collect all classes from this module's __all__ list
_THIS_MODULE_CLASSES = [
    globals()[name] for name in __all__
]

# Import extended nodes from old location (until migration is complete)
try:
    from casare_rpa.canvas.visual_nodes.extended_visual_nodes import EXTENDED_VISUAL_NODE_CLASSES
    _EXTENDED_CLASSES = EXTENDED_VISUAL_NODE_CLASSES
except ImportError:
    _EXTENDED_CLASSES = []

# Combine all classes: this module + extended
# Note: data_operations nodes are now in _THIS_MODULE_CLASSES
ALL_VISUAL_NODE_CLASSES = _THIS_MODULE_CLASSES + _EXTENDED_CLASSES

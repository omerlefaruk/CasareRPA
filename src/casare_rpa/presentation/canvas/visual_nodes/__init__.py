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

# File Operations (16 nodes)
from .file_operations import (
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

"""
CasareRPA - Nodes Package
Contains all automation node implementations.

This module uses lazy loading to improve startup performance.
Node classes are only imported when first accessed.
"""

import importlib
from typing import TYPE_CHECKING, Any, Dict, List, Type

__version__ = "0.1.0"

# Type hints for IDE support - these don't actually import at runtime
if TYPE_CHECKING:
    from .basic_nodes import StartNode, EndNode, CommentNode
    from .browser_nodes import (
        LaunchBrowserNode,
        CloseBrowserNode,
        NewTabNode,
        GetAllImagesNode,
        DownloadFileNode,
    )
    from .navigation_nodes import (
        GoToURLNode,
        GoBackNode,
        GoForwardNode,
        RefreshPageNode,
    )
    from .interaction_nodes import (
        ClickElementNode,
        TypeTextNode,
        SelectDropdownNode,
    )
    from .data_nodes import (
        ExtractTextNode,
        GetAttributeNode,
        ScreenshotNode,
    )
    from .wait_nodes import (
        WaitNode,
        WaitForElementNode,
        WaitForNavigationNode,
    )
    from .variable_nodes import (
        SetVariableNode,
        GetVariableNode,
        IncrementVariableNode,
    )
    from .control_flow_nodes import (
        IfNode,
        ForLoopStartNode,
        ForLoopEndNode,
        WhileLoopStartNode,
        WhileLoopEndNode,
        BreakNode,
        ContinueNode,
        SwitchNode,
    )
    from .error_handling_nodes import (
        TryNode,
        RetryNode,
        RetrySuccessNode,
        RetryFailNode,
        ThrowErrorNode,
        WebhookNotifyNode,
        OnErrorNode,
        ErrorRecoveryNode,
        LogErrorNode,
        AssertNode,
    )
    from .data_operation_nodes import (
        ConcatenateNode,
        FormatStringNode,
        RegexMatchNode,
        RegexReplaceNode,
        MathOperationNode,
        ComparisonNode,
        CreateListNode,
        ListGetItemNode,
        JsonParseNode,
        GetPropertyNode,
        # List operations
        ListLengthNode,
        ListAppendNode,
        ListContainsNode,
        ListSliceNode,
        ListJoinNode,
        ListSortNode,
        ListReverseNode,
        ListUniqueNode,
        ListFilterNode,
        ListMapNode,
        ListReduceNode,
        ListFlattenNode,
        # Dict operations
        DictGetNode,
        DictSetNode,
        DictRemoveNode,
        DictMergeNode,
        DictKeysNode,
        DictValuesNode,
        DictHasKeyNode,
        CreateDictNode,
        DictToJsonNode,
        DictItemsNode,
    )
    from .utility_nodes import (
        HttpRequestNode,
        ValidateNode,
        TransformNode,
        LogNode,
    )
    from casare_rpa.nodes.file import (
        ReadFileNode,
        WriteFileNode,
        AppendFileNode,
        DeleteFileNode,
        CopyFileNode,
        MoveFileNode,
        CreateDirectoryNode,
        ListDirectoryNode,
        ListFilesNode,
        FileExistsNode,
        GetFileSizeNode,
        GetFileInfoNode,
        ReadCSVNode,
        WriteCSVNode,
        ReadJSONFileNode,
        WriteJSONFileNode,
        ZipFilesNode,
        UnzipFilesNode,
    )
    from .email_nodes import (
        SendEmailNode,
        ReadEmailsNode,
        GetEmailContentNode,
        SaveAttachmentNode,
        FilterEmailsNode,
        MarkEmailNode,
        DeleteEmailNode,
        MoveEmailNode,
    )
    from casare_rpa.nodes.http import (
        HttpRequestNode as HttpRequestNodeNew,
        HttpGetNode,
        HttpPostNode,
        HttpPutNode,
        HttpPatchNode,
        HttpDeleteNode,
        SetHttpHeadersNode,
        HttpAuthNode,
        ParseJsonResponseNode,
        HttpDownloadFileNode,
        HttpUploadFileNode,
        BuildUrlNode,
    )
    from casare_rpa.nodes.database import (
        DatabaseConnectNode,
        ExecuteQueryNode,
        ExecuteNonQueryNode,
        BeginTransactionNode,
        CommitTransactionNode,
        RollbackTransactionNode,
        CloseDatabaseNode,
        TableExistsNode,
        GetTableColumnsNode,
        ExecuteBatchNode,
    )
    from .random_nodes import (
        RandomNumberNode,
        RandomChoiceNode,
        RandomStringNode,
        RandomUUIDNode,
        ShuffleListNode,
    )
    from .datetime_nodes import (
        GetCurrentDateTimeNode,
        FormatDateTimeNode,
        ParseDateTimeNode,
        DateTimeAddNode,
        DateTimeDiffNode,
        DateTimeCompareNode,
        GetTimestampNode,
    )
    from .text_nodes import (
        TextSplitNode,
        TextReplaceNode,
        TextTrimNode,
        TextCaseNode,
        TextPadNode,
        TextSubstringNode,
        TextContainsNode,
        TextStartsWithNode,
        TextEndsWithNode,
        TextLinesNode,
        TextReverseNode,
        TextCountNode,
        TextJoinNode,
        TextExtractNode,
    )
    from .system_nodes import (
        ClipboardCopyNode,
        ClipboardPasteNode,
        ClipboardClearNode,
        MessageBoxNode,
        InputDialogNode,
        TooltipNode,
        RunCommandNode,
        RunPowerShellNode,
        GetServiceStatusNode,
        StartServiceNode,
        StopServiceNode,
        RestartServiceNode,
        ListServicesNode,
    )
    from .script_nodes import (
        RunPythonScriptNode,
        RunPythonFileNode,
        EvalExpressionNode,
        RunBatchScriptNode,
        RunJavaScriptNode,
    )
    from .xml_nodes import (
        ParseXMLNode,
        ReadXMLFileNode,
        WriteXMLFileNode,
        XPathQueryNode,
        GetXMLElementNode,
        GetXMLAttributeNode,
        XMLToJsonNode,
        JsonToXMLNode,
    )
    from .pdf_nodes import (
        ReadPDFTextNode,
        GetPDFInfoNode,
        MergePDFsNode,
        SplitPDFNode,
        ExtractPDFPagesNode,
        PDFToImagesNode,
    )
    from .ftp_nodes import (
        FTPConnectNode,
        FTPUploadNode,
        FTPDownloadNode,
        FTPListNode,
        FTPDeleteNode,
        FTPMakeDirNode,
        FTPRemoveDirNode,
        FTPRenameNode,
        FTPDisconnectNode,
        FTPGetSizeNode,
    )


# Lazy loading registry - maps node class names to their module paths
_NODE_REGISTRY: Dict[str, str] = {
    # Basic nodes
    "StartNode": "basic_nodes",
    "EndNode": "basic_nodes",
    "CommentNode": "basic_nodes",
    # Browser control nodes
    "LaunchBrowserNode": "browser_nodes",
    "CloseBrowserNode": "browser_nodes",
    "NewTabNode": "browser_nodes",
    "GetAllImagesNode": "browser_nodes",
    "DownloadFileNode": "browser_nodes",
    # Navigation nodes
    "GoToURLNode": "navigation_nodes",
    "GoBackNode": "navigation_nodes",
    "GoForwardNode": "navigation_nodes",
    "RefreshPageNode": "navigation_nodes",
    # Interaction nodes
    "ClickElementNode": "interaction_nodes",
    "TypeTextNode": "interaction_nodes",
    "SelectDropdownNode": "interaction_nodes",
    # Data extraction nodes
    "ExtractTextNode": "data_nodes",
    "GetAttributeNode": "data_nodes",
    "ScreenshotNode": "data_nodes",
    # Wait nodes
    "WaitNode": "wait_nodes",
    "WaitForElementNode": "wait_nodes",
    "WaitForNavigationNode": "wait_nodes",
    # Variable nodes
    "SetVariableNode": "variable_nodes",
    "GetVariableNode": "variable_nodes",
    "IncrementVariableNode": "variable_nodes",
    # Control flow nodes
    "IfNode": "control_flow_nodes",
    "ForLoopStartNode": "control_flow_nodes",
    "ForLoopEndNode": "control_flow_nodes",
    "WhileLoopStartNode": "control_flow_nodes",
    "WhileLoopEndNode": "control_flow_nodes",
    "BreakNode": "control_flow_nodes",
    "ContinueNode": "control_flow_nodes",
    "SwitchNode": "control_flow_nodes",
    # Error handling nodes
    "TryNode": "error_handling_nodes",
    "RetryNode": "error_handling_nodes",
    "RetrySuccessNode": "error_handling_nodes",
    "RetryFailNode": "error_handling_nodes",
    "ThrowErrorNode": "error_handling_nodes",
    "WebhookNotifyNode": "error_handling_nodes",
    "OnErrorNode": "error_handling_nodes",
    "ErrorRecoveryNode": "error_handling_nodes",
    "LogErrorNode": "error_handling_nodes",
    "AssertNode": "error_handling_nodes",
    # Data operation nodes
    "ConcatenateNode": "data_operation_nodes",
    "FormatStringNode": "data_operation_nodes",
    "RegexMatchNode": "data_operation_nodes",
    "RegexReplaceNode": "data_operation_nodes",
    "MathOperationNode": "data_operation_nodes",
    "ComparisonNode": "data_operation_nodes",
    "CreateListNode": "data_operation_nodes",
    "ListGetItemNode": "data_operation_nodes",
    "JsonParseNode": "data_operation_nodes",
    "GetPropertyNode": "data_operation_nodes",
    # List operation nodes
    "ListLengthNode": "data_operation_nodes",
    "ListAppendNode": "data_operation_nodes",
    "ListContainsNode": "data_operation_nodes",
    "ListSliceNode": "data_operation_nodes",
    "ListJoinNode": "data_operation_nodes",
    "ListSortNode": "data_operation_nodes",
    "ListReverseNode": "data_operation_nodes",
    "ListUniqueNode": "data_operation_nodes",
    "ListFilterNode": "data_operation_nodes",
    "ListMapNode": "data_operation_nodes",
    "ListReduceNode": "data_operation_nodes",
    "ListFlattenNode": "data_operation_nodes",
    # Dict operation nodes
    "DictGetNode": "data_operation_nodes",
    "DictSetNode": "data_operation_nodes",
    "DictRemoveNode": "data_operation_nodes",
    "DictMergeNode": "data_operation_nodes",
    "DictKeysNode": "data_operation_nodes",
    "DictValuesNode": "data_operation_nodes",
    "DictHasKeyNode": "data_operation_nodes",
    "CreateDictNode": "data_operation_nodes",
    "DictToJsonNode": "data_operation_nodes",
    "DictItemsNode": "data_operation_nodes",
    # Utility nodes
    "ValidateNode": "utility_nodes",
    "TransformNode": "utility_nodes",
    "LogNode": "utility_nodes",
    # File system nodes - file operations
    "ReadFileNode": "file.file_operations",
    "WriteFileNode": "file.file_operations",
    "AppendFileNode": "file.file_operations",
    "DeleteFileNode": "file.file_operations",
    "CopyFileNode": "file.file_operations",
    "MoveFileNode": "file.file_operations",
    "CreateDirectoryNode": "file.file_operations",
    "ListDirectoryNode": "file.file_operations",
    "ListFilesNode": "file.file_operations",
    "FileExistsNode": "file.file_operations",
    "GetFileSizeNode": "file.file_operations",
    "GetFileInfoNode": "file.file_operations",
    # File system nodes - structured data
    "ReadCSVNode": "file.structured_data",
    "WriteCSVNode": "file.structured_data",
    "ReadJSONFileNode": "file.structured_data",
    "WriteJSONFileNode": "file.structured_data",
    "ZipFilesNode": "file.structured_data",
    "UnzipFilesNode": "file.structured_data",
    # Email nodes
    "SendEmailNode": "email_nodes",
    "ReadEmailsNode": "email_nodes",
    "GetEmailContentNode": "email_nodes",
    "SaveAttachmentNode": "email_nodes",
    "FilterEmailsNode": "email_nodes",
    "MarkEmailNode": "email_nodes",
    "DeleteEmailNode": "email_nodes",
    "MoveEmailNode": "email_nodes",
    # HTTP/REST API nodes - basic methods
    "HttpRequestNode": "http.http_basic",
    "HttpGetNode": "http.http_basic",
    "HttpPostNode": "http.http_basic",
    "HttpPutNode": "http.http_basic",
    "HttpPatchNode": "http.http_basic",
    "HttpDeleteNode": "http.http_basic",
    # HTTP/REST API nodes - advanced operations
    "SetHttpHeadersNode": "http.http_advanced",
    "ParseJsonResponseNode": "http.http_advanced",
    "HttpDownloadFileNode": "http.http_advanced",
    "HttpUploadFileNode": "http.http_advanced",
    "BuildUrlNode": "http.http_advanced",
    # HTTP/REST API nodes - authentication
    "HttpAuthNode": "http.http_auth",
    # Database nodes - SQL operations
    "DatabaseConnectNode": "database.sql_nodes",
    "ExecuteQueryNode": "database.sql_nodes",
    "ExecuteNonQueryNode": "database.sql_nodes",
    "BeginTransactionNode": "database.sql_nodes",
    "CommitTransactionNode": "database.sql_nodes",
    "RollbackTransactionNode": "database.sql_nodes",
    "CloseDatabaseNode": "database.sql_nodes",
    "ExecuteBatchNode": "database.sql_nodes",
    # Database nodes - utilities
    "TableExistsNode": "database.database_utils",
    "GetTableColumnsNode": "database.database_utils",
    # Random nodes
    "RandomNumberNode": "random_nodes",
    "RandomChoiceNode": "random_nodes",
    "RandomStringNode": "random_nodes",
    "RandomUUIDNode": "random_nodes",
    "ShuffleListNode": "random_nodes",
    # DateTime nodes
    "GetCurrentDateTimeNode": "datetime_nodes",
    "FormatDateTimeNode": "datetime_nodes",
    "ParseDateTimeNode": "datetime_nodes",
    "DateTimeAddNode": "datetime_nodes",
    "DateTimeDiffNode": "datetime_nodes",
    "DateTimeCompareNode": "datetime_nodes",
    "GetTimestampNode": "datetime_nodes",
    # Text nodes
    "TextSplitNode": "text_nodes",
    "TextReplaceNode": "text_nodes",
    "TextTrimNode": "text_nodes",
    "TextCaseNode": "text_nodes",
    "TextPadNode": "text_nodes",
    "TextSubstringNode": "text_nodes",
    "TextContainsNode": "text_nodes",
    "TextStartsWithNode": "text_nodes",
    "TextEndsWithNode": "text_nodes",
    "TextLinesNode": "text_nodes",
    "TextReverseNode": "text_nodes",
    "TextCountNode": "text_nodes",
    "TextJoinNode": "text_nodes",
    "TextExtractNode": "text_nodes",
    # System nodes (Clipboard, Dialogs, Terminal, Services)
    "ClipboardCopyNode": "system_nodes",
    "ClipboardPasteNode": "system_nodes",
    "ClipboardClearNode": "system_nodes",
    "MessageBoxNode": "system_nodes",
    "InputDialogNode": "system_nodes",
    "TooltipNode": "system_nodes",
    "RunCommandNode": "system_nodes",
    "RunPowerShellNode": "system_nodes",
    "GetServiceStatusNode": "system_nodes",
    "StartServiceNode": "system_nodes",
    "StopServiceNode": "system_nodes",
    "RestartServiceNode": "system_nodes",
    "ListServicesNode": "system_nodes",
    # Script nodes
    "RunPythonScriptNode": "script_nodes",
    "RunPythonFileNode": "script_nodes",
    "EvalExpressionNode": "script_nodes",
    "RunBatchScriptNode": "script_nodes",
    "RunJavaScriptNode": "script_nodes",
    # XML nodes
    "ParseXMLNode": "xml_nodes",
    "ReadXMLFileNode": "xml_nodes",
    "WriteXMLFileNode": "xml_nodes",
    "XPathQueryNode": "xml_nodes",
    "GetXMLElementNode": "xml_nodes",
    "GetXMLAttributeNode": "xml_nodes",
    "XMLToJsonNode": "xml_nodes",
    "JsonToXMLNode": "xml_nodes",
    # PDF nodes
    "ReadPDFTextNode": "pdf_nodes",
    "GetPDFInfoNode": "pdf_nodes",
    "MergePDFsNode": "pdf_nodes",
    "SplitPDFNode": "pdf_nodes",
    "ExtractPDFPagesNode": "pdf_nodes",
    "PDFToImagesNode": "pdf_nodes",
    # FTP nodes
    "FTPConnectNode": "ftp_nodes",
    "FTPUploadNode": "ftp_nodes",
    "FTPDownloadNode": "ftp_nodes",
    "FTPListNode": "ftp_nodes",
    "FTPDeleteNode": "ftp_nodes",
    "FTPMakeDirNode": "ftp_nodes",
    "FTPRemoveDirNode": "ftp_nodes",
    "FTPRenameNode": "ftp_nodes",
    "FTPDisconnectNode": "ftp_nodes",
    "FTPGetSizeNode": "ftp_nodes",
}

# Cache for loaded modules and classes
_loaded_modules: Dict[str, Any] = {}
_loaded_classes: Dict[str, Type] = {}


def _lazy_import(name: str) -> Type:
    """
    Lazily import a node class by name.

    Args:
        name: The name of the node class to import

    Returns:
        The node class

    Raises:
        AttributeError: If the class doesn't exist
    """
    # Check cache first
    if name in _loaded_classes:
        return _loaded_classes[name]

    # Check if it's a known node class
    if name not in _NODE_REGISTRY:
        raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")

    module_name = _NODE_REGISTRY[name]

    # Load the module if not already loaded
    if module_name not in _loaded_modules:
        full_module_name = f".{module_name}"
        _loaded_modules[module_name] = importlib.import_module(
            full_module_name, package="casare_rpa.nodes"
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
    if name in _NODE_REGISTRY:
        return _lazy_import(name)

    # Handle special attributes
    if name == "__all__":
        return list(_NODE_REGISTRY.keys()) + ["__version__"]

    raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")


def __dir__() -> List[str]:
    """Return the list of available attributes for tab completion."""
    return list(_NODE_REGISTRY.keys()) + [
        "__version__",
        "get_all_node_classes",
        "preload_nodes",
    ]


def get_all_node_classes() -> Dict[str, Type]:
    """
    Get all node classes (this will trigger loading all modules).

    Returns:
        Dictionary mapping class names to class objects
    """
    result = {}
    for name in _NODE_REGISTRY:
        result[name] = _lazy_import(name)
    return result


def preload_nodes(node_names: List[str] = None) -> None:
    """
    Preload specific nodes or all nodes.

    This can be called during application startup to preload
    frequently used nodes, or in a background thread.

    Args:
        node_names: List of node class names to preload, or None for all
    """
    names_to_load = node_names if node_names else list(_NODE_REGISTRY.keys())
    for name in names_to_load:
        if name in _NODE_REGISTRY:
            _lazy_import(name)


# Export __all__ for explicit imports
__all__ = [
    "__version__",
    # Basic nodes
    "StartNode",
    "EndNode",
    "CommentNode",
    # Browser control
    "LaunchBrowserNode",
    "CloseBrowserNode",
    "NewTabNode",
    "GetAllImagesNode",
    "DownloadFileNode",
    # Navigation
    "GoToURLNode",
    "GoBackNode",
    "GoForwardNode",
    "RefreshPageNode",
    # Interaction
    "ClickElementNode",
    "TypeTextNode",
    "SelectDropdownNode",
    # Data extraction
    "ExtractTextNode",
    "GetAttributeNode",
    "ScreenshotNode",
    # Wait nodes
    "WaitNode",
    "WaitForElementNode",
    "WaitForNavigationNode",
    # Variable nodes
    "SetVariableNode",
    "GetVariableNode",
    "IncrementVariableNode",
    # Control flow nodes
    "IfNode",
    "ForLoopStartNode",
    "ForLoopEndNode",
    "WhileLoopStartNode",
    "WhileLoopEndNode",
    "BreakNode",
    "ContinueNode",
    "SwitchNode",
    # Error handling nodes
    "TryNode",
    "RetryNode",
    "RetrySuccessNode",
    "RetryFailNode",
    "ThrowErrorNode",
    "WebhookNotifyNode",
    "OnErrorNode",
    "ErrorRecoveryNode",
    "LogErrorNode",
    "AssertNode",
    # Data operation nodes
    "ConcatenateNode",
    "FormatStringNode",
    "RegexMatchNode",
    "RegexReplaceNode",
    "MathOperationNode",
    "ComparisonNode",
    "CreateListNode",
    "ListGetItemNode",
    "JsonParseNode",
    "GetPropertyNode",
    # List operation nodes
    "ListLengthNode",
    "ListAppendNode",
    "ListContainsNode",
    "ListSliceNode",
    "ListJoinNode",
    "ListSortNode",
    "ListReverseNode",
    "ListUniqueNode",
    "ListFilterNode",
    "ListMapNode",
    "ListReduceNode",
    "ListFlattenNode",
    # Dict operation nodes
    "DictGetNode",
    "DictSetNode",
    "DictRemoveNode",
    "DictMergeNode",
    "DictKeysNode",
    "DictValuesNode",
    "DictHasKeyNode",
    "CreateDictNode",
    "DictToJsonNode",
    "DictItemsNode",
    # Utility nodes
    "HttpRequestNode",
    "ValidateNode",
    "TransformNode",
    "LogNode",
    # File system nodes
    "ReadFileNode",
    "WriteFileNode",
    "AppendFileNode",
    "DeleteFileNode",
    "CopyFileNode",
    "MoveFileNode",
    "CreateDirectoryNode",
    "ListDirectoryNode",
    "ListFilesNode",
    "FileExistsNode",
    "GetFileInfoNode",
    "ReadCSVNode",
    "WriteCSVNode",
    "ReadJSONFileNode",
    "WriteJSONFileNode",
    "ZipFilesNode",
    "UnzipFilesNode",
    # Email nodes
    "SendEmailNode",
    "ReadEmailsNode",
    "GetEmailContentNode",
    "SaveAttachmentNode",
    "FilterEmailsNode",
    "MarkEmailNode",
    "DeleteEmailNode",
    "MoveEmailNode",
    # HTTP/REST API nodes
    "HttpGetNode",
    "HttpPostNode",
    "HttpPutNode",
    "HttpPatchNode",
    "HttpDeleteNode",
    "SetHttpHeadersNode",
    "HttpAuthNode",
    "ParseJsonResponseNode",
    "HttpDownloadFileNode",
    "HttpUploadFileNode",
    "BuildUrlNode",
    # Database nodes
    "DatabaseConnectNode",
    "ExecuteQueryNode",
    "ExecuteNonQueryNode",
    "BeginTransactionNode",
    "CommitTransactionNode",
    "RollbackTransactionNode",
    "CloseDatabaseNode",
    "TableExistsNode",
    "GetTableColumnsNode",
    "ExecuteBatchNode",
    # Random nodes
    "RandomNumberNode",
    "RandomChoiceNode",
    "RandomStringNode",
    "RandomUUIDNode",
    "ShuffleListNode",
    # DateTime nodes
    "GetCurrentDateTimeNode",
    "FormatDateTimeNode",
    "ParseDateTimeNode",
    "DateTimeAddNode",
    "DateTimeDiffNode",
    "DateTimeCompareNode",
    "GetTimestampNode",
    # Text nodes
    "TextSplitNode",
    "TextReplaceNode",
    "TextTrimNode",
    "TextCaseNode",
    "TextPadNode",
    "TextSubstringNode",
    "TextContainsNode",
    "TextStartsWithNode",
    "TextEndsWithNode",
    "TextLinesNode",
    "TextReverseNode",
    "TextCountNode",
    "TextJoinNode",
    "TextExtractNode",
    # System nodes
    "ClipboardCopyNode",
    "ClipboardPasteNode",
    "ClipboardClearNode",
    "MessageBoxNode",
    "InputDialogNode",
    "TooltipNode",
    "RunCommandNode",
    "RunPowerShellNode",
    "GetServiceStatusNode",
    "StartServiceNode",
    "StopServiceNode",
    "RestartServiceNode",
    "ListServicesNode",
    # Script nodes
    "RunPythonScriptNode",
    "RunPythonFileNode",
    "EvalExpressionNode",
    "RunBatchScriptNode",
    "RunJavaScriptNode",
    # XML nodes
    "ParseXMLNode",
    "ReadXMLFileNode",
    "WriteXMLFileNode",
    "XPathQueryNode",
    "GetXMLElementNode",
    "GetXMLAttributeNode",
    "XMLToJsonNode",
    "JsonToXMLNode",
    # PDF nodes
    "ReadPDFTextNode",
    "GetPDFInfoNode",
    "MergePDFsNode",
    "SplitPDFNode",
    "ExtractPDFPagesNode",
    "PDFToImagesNode",
    # FTP nodes
    "FTPConnectNode",
    "FTPUploadNode",
    "FTPDownloadNode",
    "FTPListNode",
    "FTPDeleteNode",
    "FTPMakeDirNode",
    "FTPRemoveDirNode",
    "FTPRenameNode",
    "FTPDisconnectNode",
    "FTPGetSizeNode",
    # Utility functions
    "get_all_node_classes",
    "preload_nodes",
]

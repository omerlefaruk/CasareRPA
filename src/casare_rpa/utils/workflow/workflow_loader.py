"""
Workflow Loader Utility
Deserializes workflow JSON into executable WorkflowSchema with node instances.

SECURITY: All workflows are validated against a strict schema before execution.
"""

from typing import Any, Dict
from loguru import logger

from casare_rpa.domain.entities.workflow import WorkflowSchema
from casare_rpa.domain.entities.workflow_metadata import WorkflowMetadata
from casare_rpa.domain.entities.node_connection import NodeConnection
from casare_rpa.domain.entities.base_node import BaseNode


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""

    pass


# SECURITY: Maximum limits to prevent resource exhaustion
MAX_NODES = 1000
MAX_CONNECTIONS = 5000
MAX_NODE_ID_LENGTH = 256
MAX_CONFIG_DEPTH = 10
MAX_STRING_LENGTH = 10000


def _validate_string(
    value: Any, field_name: str, max_length: int = MAX_STRING_LENGTH
) -> str:
    """Validate a string field."""
    if value is None:
        return ""
    if not isinstance(value, str):
        raise WorkflowValidationError(
            f"Field '{field_name}' must be a string, got {type(value).__name__}"
        )
    if len(value) > max_length:
        raise WorkflowValidationError(
            f"Field '{field_name}' exceeds maximum length of {max_length}"
        )
    return value


def _validate_config_value(value: Any, path: str, depth: int = 0) -> Any:
    """Recursively validate config values to prevent malicious payloads."""
    if depth > MAX_CONFIG_DEPTH:
        raise WorkflowValidationError(
            f"Config at '{path}' exceeds maximum nesting depth of {MAX_CONFIG_DEPTH}"
        )

    if value is None:
        return value

    if isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            raise WorkflowValidationError(
                f"Config value at '{path}' exceeds maximum length of {MAX_STRING_LENGTH}"
            )
        # SECURITY: Check for potential code injection patterns - BLOCK, don't just log
        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "os.system",
            "subprocess.",
            "open(",
            "pickle.",
            "marshal.",
            "__builtins__",
            "__globals__",
        ]
        value_lower = value.lower()
        for pattern in dangerous_patterns:
            if pattern in value_lower:
                logger.error(
                    f"SECURITY: Blocked dangerous pattern '{pattern}' in config at '{path}'"
                )
                raise WorkflowValidationError(
                    f"Security error: Potentially dangerous pattern '{pattern}' found in "
                    f"config value at '{path}'. This workflow cannot be loaded for security reasons."
                )
        return value

    if isinstance(value, list):
        return [
            _validate_config_value(item, f"{path}[{i}]", depth + 1)
            for i, item in enumerate(value)
        ]

    if isinstance(value, dict):
        return {
            _validate_string(
                k, f"{path}.key", MAX_NODE_ID_LENGTH
            ): _validate_config_value(v, f"{path}.{k}", depth + 1)
            for k, v in value.items()
        }

    raise WorkflowValidationError(
        f"Unsupported config value type at '{path}': {type(value).__name__}"
    )


def validate_workflow_structure(workflow_data: Dict) -> None:
    """
    SECURITY: Validate workflow structure before loading.

    Checks:
    - Required fields present
    - Field types correct
    - No malicious payloads
    - Size limits respected

    Args:
        workflow_data: Raw workflow dictionary from JSON

    Raises:
        WorkflowValidationError: If validation fails
    """
    if not isinstance(workflow_data, dict):
        raise WorkflowValidationError(
            f"Workflow must be a dictionary, got {type(workflow_data).__name__}"
        )

    # Validate metadata
    metadata = workflow_data.get("metadata", {})
    if not isinstance(metadata, dict):
        raise WorkflowValidationError("'metadata' must be a dictionary")

    _validate_string(metadata.get("name"), "metadata.name", 256)
    _validate_string(metadata.get("description"), "metadata.description", 10000)
    _validate_string(metadata.get("version"), "metadata.version", 50)

    # Validate nodes
    nodes = workflow_data.get("nodes", {})
    if not isinstance(nodes, dict):
        raise WorkflowValidationError("'nodes' must be a dictionary")

    if len(nodes) > MAX_NODES:
        raise WorkflowValidationError(
            f"Workflow exceeds maximum of {MAX_NODES} nodes (has {len(nodes)})"
        )

    for node_id, node_data in nodes.items():
        # Validate node_id
        _validate_string(node_id, "node_id", MAX_NODE_ID_LENGTH)

        if not isinstance(node_data, dict):
            raise WorkflowValidationError(f"Node '{node_id}' must be a dictionary")

        # Validate node_type
        node_type = node_data.get("node_type")
        _validate_string(node_type, f"nodes.{node_id}.node_type", 128)

        if not node_type:
            raise WorkflowValidationError(f"Node '{node_id}' is missing 'node_type'")

        # Validate config
        config = node_data.get("config", {})
        if not isinstance(config, dict):
            raise WorkflowValidationError(
                f"Node '{node_id}' config must be a dictionary"
            )

        _validate_config_value(config, f"nodes.{node_id}.config")

    # Validate connections
    connections = workflow_data.get("connections", [])
    if not isinstance(connections, list):
        raise WorkflowValidationError("'connections' must be a list")

    if len(connections) > MAX_CONNECTIONS:
        raise WorkflowValidationError(
            f"Workflow exceeds maximum of {MAX_CONNECTIONS} connections (has {len(connections)})"
        )

    for i, conn in enumerate(connections):
        if not isinstance(conn, dict):
            raise WorkflowValidationError(f"Connection {i} must be a dictionary")

        _validate_string(
            conn.get("source_node"), f"connections[{i}].source_node", MAX_NODE_ID_LENGTH
        )
        _validate_string(
            conn.get("target_node"), f"connections[{i}].target_node", MAX_NODE_ID_LENGTH
        )
        _validate_string(
            conn.get("source_port", ""), f"connections[{i}].source_port", 128
        )
        _validate_string(
            conn.get("target_port", ""), f"connections[{i}].target_port", 128
        )

    logger.debug(
        f"Workflow validation passed: {len(nodes)} nodes, {len(connections)} connections"
    )


# Import all node classes
# Basic nodes
from casare_rpa.nodes.basic_nodes import StartNode, EndNode, CommentNode

# Variable nodes
from casare_rpa.nodes.variable_nodes import (
    SetVariableNode,
    GetVariableNode,
    IncrementVariableNode,
)

# Control flow nodes
from casare_rpa.nodes.control_flow_nodes import (
    IfNode,
    ForLoopStartNode,
    ForLoopEndNode,
    WhileLoopStartNode,
    WhileLoopEndNode,
    BreakNode,
    ContinueNode,
    MergeNode,
    SwitchNode,
)

# Error handling nodes
from casare_rpa.nodes.error_handling_nodes import (
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

# Wait nodes (browser)
from casare_rpa.nodes.wait_nodes import (
    WaitNode,
    WaitForElementNode,
    WaitForNavigationNode,
)

# Browser nodes
from casare_rpa.nodes.browser_nodes import (
    LaunchBrowserNode,
    CloseBrowserNode,
    NewTabNode,
    GetAllImagesNode,
    DownloadFileNode,
)

# Navigation nodes
from casare_rpa.nodes.navigation_nodes import (
    GoToURLNode,
    GoBackNode,
    GoForwardNode,
    RefreshPageNode,
)

# Interaction nodes (browser)
from casare_rpa.nodes.interaction_nodes import (
    ClickElementNode,
    TypeTextNode,
    SelectDropdownNode,
    ImageClickNode,
)

# Data extraction nodes
from casare_rpa.nodes.data_nodes import (
    ExtractTextNode,
    GetAttributeNode,
    ScreenshotNode,
)

# Table scraping nodes
from casare_rpa.nodes.browser.table_scraper_node import TableScraperNode

# Form nodes
from casare_rpa.nodes.browser.form_field_node import FormFieldNode
from casare_rpa.nodes.browser.form_filler_node import FormFillerNode
from casare_rpa.nodes.browser.detect_forms_node import DetectFormsNode

# DateTime nodes
from casare_rpa.nodes.datetime_nodes import (
    GetCurrentDateTimeNode,
    FormatDateTimeNode,
    ParseDateTimeNode,
    DateTimeAddNode,
    DateTimeDiffNode,
    DateTimeCompareNode,
    GetTimestampNode,
)

# Database nodes
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

# Data operation nodes
from casare_rpa.nodes.data_operation_nodes import (
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

# File nodes
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
    GetFileInfoNode,
    GetFileSizeNode,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    ZipFilesNode,
    UnzipFilesNode,
)

# Text nodes
from casare_rpa.nodes.text_nodes import (
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

# HTTP nodes
from casare_rpa.nodes.http import (
    HttpRequestNode,
    SetHttpHeadersNode,
    HttpAuthNode,
    ParseJsonResponseNode,
    HttpDownloadFileNode,
    HttpUploadFileNode,
    BuildUrlNode,
)

# Email nodes
from casare_rpa.nodes.email import (
    SendEmailNode,
    ReadEmailsNode,
    GetEmailContentNode,
    SaveAttachmentNode,
    FilterEmailsNode,
    MarkEmailNode,
    DeleteEmailNode,
    MoveEmailNode,
)

# FTP nodes
from casare_rpa.nodes.ftp_nodes import (
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

# PDF nodes
from casare_rpa.nodes.pdf_nodes import (
    ReadPDFTextNode,
    GetPDFInfoNode,
    MergePDFsNode,
    SplitPDFNode,
    ExtractPDFPagesNode,
    PDFToImagesNode,
)

# XML nodes
from casare_rpa.nodes.xml_nodes import (
    ParseXMLNode,
    ReadXMLFileNode,
    WriteXMLFileNode,
    XPathQueryNode,
    GetXMLElementNode,
    GetXMLAttributeNode,
    XMLToJsonNode,
    JsonToXMLNode,
)

# Random nodes
from casare_rpa.nodes.random_nodes import (
    RandomNumberNode,
    RandomChoiceNode,
    RandomStringNode,
    RandomUUIDNode,
    ShuffleListNode,
)

# System nodes
from casare_rpa.nodes.system import (
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

# Script nodes
from casare_rpa.nodes.script_nodes import (
    RunPythonScriptNode,
    RunPythonFileNode,
    EvalExpressionNode,
    RunBatchScriptNode,
    RunJavaScriptNode,
)

# Utility nodes
from casare_rpa.nodes.utility_nodes import ValidateNode, TransformNode, LogNode

# Desktop nodes (aliased where they conflict with browser nodes)
from casare_rpa.nodes.desktop_nodes import (
    # Application nodes
    LaunchApplicationNode,
    CloseApplicationNode,
    ActivateWindowNode,
    GetWindowListNode,
    # Element nodes (aliased to avoid conflict with browser interaction_nodes)
    FindElementNode as DesktopFindElementNode,
    ClickElementNode as DesktopClickElementNode,
    TypeTextNode as DesktopTypeTextNode,
    GetElementTextNode,
    GetElementPropertyNode,
    # Window management nodes
    ResizeWindowNode,
    MoveWindowNode,
    MaximizeWindowNode,
    MinimizeWindowNode,
    RestoreWindowNode,
    GetWindowPropertiesNode,
    SetWindowStateNode,
    # Interaction nodes
    SelectFromDropdownNode,
    CheckCheckboxNode,
    SelectRadioButtonNode,
    SelectTabNode,
    ExpandTreeItemNode,
    ScrollElementNode,
    # Mouse and keyboard nodes
    MoveMouseNode,
    MouseClickNode,
    SendKeysNode,
    SendHotKeyNode,
    GetMousePositionNode,
    DragMouseNode,
    # Wait and verification nodes (aliased for desktop)
    WaitForElementNode as DesktopWaitForElementNode,
    WaitForWindowNode,
    VerifyElementExistsNode,
    VerifyElementPropertyNode,
    # Screenshot and OCR nodes
    CaptureScreenshotNode,
    CaptureElementImageNode,
    OCRExtractTextNode,
    CompareImagesNode,
    # Office automation nodes
    ExcelOpenNode,
    ExcelReadCellNode,
    ExcelWriteCellNode,
    ExcelGetRangeNode,
    ExcelCloseNode,
    WordOpenNode,
    WordGetTextNode,
    WordReplaceTextNode,
    WordCloseNode,
    OutlookSendEmailNode,
    OutlookReadEmailsNode,
    OutlookGetInboxCountNode,
)

# Trigger nodes
from casare_rpa.nodes.trigger_nodes import (
    WebhookTriggerNode,
    ScheduleTriggerNode,
    FileWatchTriggerNode,
    EmailTriggerNode,
    AppEventTriggerNode,
    ErrorTriggerNode,
    WorkflowCallTriggerNode,
    FormTriggerNode,
    ChatTriggerNode,
    RSSFeedTriggerNode,
    SSETriggerNode,
)

# LLM nodes (AI/ML)
from casare_rpa.nodes.llm import (
    LLMCompletionNode,
    LLMChatNode,
    LLMExtractDataNode,
    LLMSummarizeNode,
    LLMClassifyNode,
    LLMTranslateNode,
)

# Map node types to classes
NODE_TYPE_MAP = {
    # Basic nodes
    "StartNode": StartNode,
    "EndNode": EndNode,
    "CommentNode": CommentNode,
    # Variable nodes
    "SetVariableNode": SetVariableNode,
    "GetVariableNode": GetVariableNode,
    "IncrementVariableNode": IncrementVariableNode,
    # Control flow nodes
    "IfNode": IfNode,
    "ForLoopStartNode": ForLoopStartNode,
    "ForLoopEndNode": ForLoopEndNode,
    "WhileLoopStartNode": WhileLoopStartNode,
    "WhileLoopEndNode": WhileLoopEndNode,
    "BreakNode": BreakNode,
    "ContinueNode": ContinueNode,
    "MergeNode": MergeNode,
    "SwitchNode": SwitchNode,
    # Error handling nodes
    "TryNode": TryNode,
    "RetryNode": RetryNode,
    "RetrySuccessNode": RetrySuccessNode,
    "RetryFailNode": RetryFailNode,
    "ThrowErrorNode": ThrowErrorNode,
    "WebhookNotifyNode": WebhookNotifyNode,
    "OnErrorNode": OnErrorNode,
    "ErrorRecoveryNode": ErrorRecoveryNode,
    "LogErrorNode": LogErrorNode,
    "AssertNode": AssertNode,
    # Wait nodes (browser)
    "WaitNode": WaitNode,
    "WaitForElementNode": WaitForElementNode,
    "WaitForNavigationNode": WaitForNavigationNode,
    # Browser nodes
    "LaunchBrowserNode": LaunchBrowserNode,
    "CloseBrowserNode": CloseBrowserNode,
    "NewTabNode": NewTabNode,
    "GetAllImagesNode": GetAllImagesNode,
    "DownloadFileNode": DownloadFileNode,
    # Navigation nodes
    "GoToURLNode": GoToURLNode,
    "GoBackNode": GoBackNode,
    "GoForwardNode": GoForwardNode,
    "RefreshPageNode": RefreshPageNode,
    # Interaction nodes (browser)
    "ClickElementNode": ClickElementNode,
    "TypeTextNode": TypeTextNode,
    "SelectDropdownNode": SelectDropdownNode,
    "ImageClickNode": ImageClickNode,
    # Data extraction nodes
    "ExtractTextNode": ExtractTextNode,
    "GetAttributeNode": GetAttributeNode,
    "ScreenshotNode": ScreenshotNode,
    # Table scraping nodes
    "TableScraperNode": TableScraperNode,
    # Form nodes
    "FormFieldNode": FormFieldNode,
    "FormFillerNode": FormFillerNode,
    "DetectFormsNode": DetectFormsNode,
    # DateTime nodes
    "GetCurrentDateTimeNode": GetCurrentDateTimeNode,
    "FormatDateTimeNode": FormatDateTimeNode,
    "ParseDateTimeNode": ParseDateTimeNode,
    "DateTimeAddNode": DateTimeAddNode,
    "DateTimeDiffNode": DateTimeDiffNode,
    "DateTimeCompareNode": DateTimeCompareNode,
    "GetTimestampNode": GetTimestampNode,
    # Database nodes
    "DatabaseConnectNode": DatabaseConnectNode,
    "ExecuteQueryNode": ExecuteQueryNode,
    "ExecuteNonQueryNode": ExecuteNonQueryNode,
    "BeginTransactionNode": BeginTransactionNode,
    "CommitTransactionNode": CommitTransactionNode,
    "RollbackTransactionNode": RollbackTransactionNode,
    "CloseDatabaseNode": CloseDatabaseNode,
    "TableExistsNode": TableExistsNode,
    "GetTableColumnsNode": GetTableColumnsNode,
    "ExecuteBatchNode": ExecuteBatchNode,
    # Data operation nodes
    "ConcatenateNode": ConcatenateNode,
    "FormatStringNode": FormatStringNode,
    "RegexMatchNode": RegexMatchNode,
    "RegexReplaceNode": RegexReplaceNode,
    "MathOperationNode": MathOperationNode,
    "ComparisonNode": ComparisonNode,
    "CreateListNode": CreateListNode,
    "ListGetItemNode": ListGetItemNode,
    "JsonParseNode": JsonParseNode,
    "GetPropertyNode": GetPropertyNode,
    "ListLengthNode": ListLengthNode,
    "ListAppendNode": ListAppendNode,
    "ListContainsNode": ListContainsNode,
    "ListSliceNode": ListSliceNode,
    "ListJoinNode": ListJoinNode,
    "ListSortNode": ListSortNode,
    "ListReverseNode": ListReverseNode,
    "ListUniqueNode": ListUniqueNode,
    "ListFilterNode": ListFilterNode,
    "ListMapNode": ListMapNode,
    "ListReduceNode": ListReduceNode,
    "ListFlattenNode": ListFlattenNode,
    "DictGetNode": DictGetNode,
    "DictSetNode": DictSetNode,
    "DictRemoveNode": DictRemoveNode,
    "DictMergeNode": DictMergeNode,
    "DictKeysNode": DictKeysNode,
    "DictValuesNode": DictValuesNode,
    "DictHasKeyNode": DictHasKeyNode,
    "CreateDictNode": CreateDictNode,
    "DictToJsonNode": DictToJsonNode,
    "DictItemsNode": DictItemsNode,
    # File nodes
    "ReadFileNode": ReadFileNode,
    "WriteFileNode": WriteFileNode,
    "AppendFileNode": AppendFileNode,
    "DeleteFileNode": DeleteFileNode,
    "CopyFileNode": CopyFileNode,
    "MoveFileNode": MoveFileNode,
    "CreateDirectoryNode": CreateDirectoryNode,
    "ListDirectoryNode": ListDirectoryNode,
    "ListFilesNode": ListFilesNode,
    "FileExistsNode": FileExistsNode,
    "GetFileInfoNode": GetFileInfoNode,
    "GetFileSizeNode": GetFileSizeNode,
    "ReadCSVNode": ReadCSVNode,
    "WriteCSVNode": WriteCSVNode,
    "ReadJSONFileNode": ReadJSONFileNode,
    "WriteJSONFileNode": WriteJSONFileNode,
    "ZipFilesNode": ZipFilesNode,
    "UnzipFilesNode": UnzipFilesNode,
    # Text nodes
    "TextSplitNode": TextSplitNode,
    "TextReplaceNode": TextReplaceNode,
    "TextTrimNode": TextTrimNode,
    "TextCaseNode": TextCaseNode,
    "TextPadNode": TextPadNode,
    "TextSubstringNode": TextSubstringNode,
    "TextContainsNode": TextContainsNode,
    "TextStartsWithNode": TextStartsWithNode,
    "TextEndsWithNode": TextEndsWithNode,
    "TextLinesNode": TextLinesNode,
    "TextReverseNode": TextReverseNode,
    "TextCountNode": TextCountNode,
    "TextJoinNode": TextJoinNode,
    "TextExtractNode": TextExtractNode,
    # HTTP nodes
    "HttpRequestNode": HttpRequestNode,
    "SetHttpHeadersNode": SetHttpHeadersNode,
    "HttpAuthNode": HttpAuthNode,
    "ParseJsonResponseNode": ParseJsonResponseNode,
    "HttpDownloadFileNode": HttpDownloadFileNode,
    "HttpUploadFileNode": HttpUploadFileNode,
    "BuildUrlNode": BuildUrlNode,
    # Email nodes
    "SendEmailNode": SendEmailNode,
    "ReadEmailsNode": ReadEmailsNode,
    "GetEmailContentNode": GetEmailContentNode,
    "SaveAttachmentNode": SaveAttachmentNode,
    "FilterEmailsNode": FilterEmailsNode,
    "MarkEmailNode": MarkEmailNode,
    "DeleteEmailNode": DeleteEmailNode,
    "MoveEmailNode": MoveEmailNode,
    # FTP nodes
    "FTPConnectNode": FTPConnectNode,
    "FTPUploadNode": FTPUploadNode,
    "FTPDownloadNode": FTPDownloadNode,
    "FTPListNode": FTPListNode,
    "FTPDeleteNode": FTPDeleteNode,
    "FTPMakeDirNode": FTPMakeDirNode,
    "FTPRemoveDirNode": FTPRemoveDirNode,
    "FTPRenameNode": FTPRenameNode,
    "FTPDisconnectNode": FTPDisconnectNode,
    "FTPGetSizeNode": FTPGetSizeNode,
    # PDF nodes
    "ReadPDFTextNode": ReadPDFTextNode,
    "GetPDFInfoNode": GetPDFInfoNode,
    "MergePDFsNode": MergePDFsNode,
    "SplitPDFNode": SplitPDFNode,
    "ExtractPDFPagesNode": ExtractPDFPagesNode,
    "PDFToImagesNode": PDFToImagesNode,
    # XML nodes
    "ParseXMLNode": ParseXMLNode,
    "ReadXMLFileNode": ReadXMLFileNode,
    "WriteXMLFileNode": WriteXMLFileNode,
    "XPathQueryNode": XPathQueryNode,
    "GetXMLElementNode": GetXMLElementNode,
    "GetXMLAttributeNode": GetXMLAttributeNode,
    "XMLToJsonNode": XMLToJsonNode,
    "JsonToXMLNode": JsonToXMLNode,
    # Random nodes
    "RandomNumberNode": RandomNumberNode,
    "RandomChoiceNode": RandomChoiceNode,
    "RandomStringNode": RandomStringNode,
    "RandomUUIDNode": RandomUUIDNode,
    "ShuffleListNode": ShuffleListNode,
    # System nodes
    "ClipboardCopyNode": ClipboardCopyNode,
    "ClipboardPasteNode": ClipboardPasteNode,
    "ClipboardClearNode": ClipboardClearNode,
    "MessageBoxNode": MessageBoxNode,
    "InputDialogNode": InputDialogNode,
    "TooltipNode": TooltipNode,
    "RunCommandNode": RunCommandNode,
    "RunPowerShellNode": RunPowerShellNode,
    "GetServiceStatusNode": GetServiceStatusNode,
    "StartServiceNode": StartServiceNode,
    "StopServiceNode": StopServiceNode,
    "RestartServiceNode": RestartServiceNode,
    "ListServicesNode": ListServicesNode,
    # Script nodes
    "RunPythonScriptNode": RunPythonScriptNode,
    "RunPythonFileNode": RunPythonFileNode,
    "EvalExpressionNode": EvalExpressionNode,
    "RunBatchScriptNode": RunBatchScriptNode,
    "RunJavaScriptNode": RunJavaScriptNode,
    # Utility nodes
    "ValidateNode": ValidateNode,
    "TransformNode": TransformNode,
    "LogNode": LogNode,
    # Desktop nodes - Application
    "LaunchApplicationNode": LaunchApplicationNode,
    "CloseApplicationNode": CloseApplicationNode,
    "ActivateWindowNode": ActivateWindowNode,
    "GetWindowListNode": GetWindowListNode,
    # Desktop nodes - Element (prefixed to distinguish from browser nodes)
    "DesktopFindElementNode": DesktopFindElementNode,
    "DesktopClickElementNode": DesktopClickElementNode,
    "DesktopTypeTextNode": DesktopTypeTextNode,
    "GetElementTextNode": GetElementTextNode,
    "GetElementPropertyNode": GetElementPropertyNode,
    # Desktop nodes - Window management
    "ResizeWindowNode": ResizeWindowNode,
    "MoveWindowNode": MoveWindowNode,
    "MaximizeWindowNode": MaximizeWindowNode,
    "MinimizeWindowNode": MinimizeWindowNode,
    "RestoreWindowNode": RestoreWindowNode,
    "GetWindowPropertiesNode": GetWindowPropertiesNode,
    "SetWindowStateNode": SetWindowStateNode,
    # Desktop nodes - Interaction
    "SelectFromDropdownNode": SelectFromDropdownNode,
    "CheckCheckboxNode": CheckCheckboxNode,
    "SelectRadioButtonNode": SelectRadioButtonNode,
    "SelectTabNode": SelectTabNode,
    "ExpandTreeItemNode": ExpandTreeItemNode,
    "ScrollElementNode": ScrollElementNode,
    # Desktop nodes - Mouse and keyboard
    "MoveMouseNode": MoveMouseNode,
    "MouseClickNode": MouseClickNode,
    "SendKeysNode": SendKeysNode,
    "SendHotKeyNode": SendHotKeyNode,
    "GetMousePositionNode": GetMousePositionNode,
    "DragMouseNode": DragMouseNode,
    # Desktop nodes - Wait and verification (prefixed to distinguish from browser)
    "DesktopWaitForElementNode": DesktopWaitForElementNode,
    "WaitForWindowNode": WaitForWindowNode,
    "VerifyElementExistsNode": VerifyElementExistsNode,
    "VerifyElementPropertyNode": VerifyElementPropertyNode,
    # Desktop nodes - Screenshot and OCR
    "CaptureScreenshotNode": CaptureScreenshotNode,
    "CaptureElementImageNode": CaptureElementImageNode,
    "OCRExtractTextNode": OCRExtractTextNode,
    "CompareImagesNode": CompareImagesNode,
    # Desktop nodes - Office automation
    "ExcelOpenNode": ExcelOpenNode,
    "ExcelReadCellNode": ExcelReadCellNode,
    "ExcelWriteCellNode": ExcelWriteCellNode,
    "ExcelGetRangeNode": ExcelGetRangeNode,
    "ExcelCloseNode": ExcelCloseNode,
    "WordOpenNode": WordOpenNode,
    "WordGetTextNode": WordGetTextNode,
    "WordReplaceTextNode": WordReplaceTextNode,
    "WordCloseNode": WordCloseNode,
    "OutlookSendEmailNode": OutlookSendEmailNode,
    "OutlookReadEmailsNode": OutlookReadEmailsNode,
    "OutlookGetInboxCountNode": OutlookGetInboxCountNode,
    # Trigger nodes
    "WebhookTriggerNode": WebhookTriggerNode,
    "ScheduleTriggerNode": ScheduleTriggerNode,
    "FileWatchTriggerNode": FileWatchTriggerNode,
    "EmailTriggerNode": EmailTriggerNode,
    "AppEventTriggerNode": AppEventTriggerNode,
    "ErrorTriggerNode": ErrorTriggerNode,
    "WorkflowCallTriggerNode": WorkflowCallTriggerNode,
    "FormTriggerNode": FormTriggerNode,
    "ChatTriggerNode": ChatTriggerNode,
    "RSSFeedTriggerNode": RSSFeedTriggerNode,
    "SSETriggerNode": SSETriggerNode,
    # LLM nodes (AI/ML)
    "LLMCompletionNode": LLMCompletionNode,
    "LLMChatNode": LLMChatNode,
    "LLMExtractDataNode": LLMExtractDataNode,
    "LLMSummarizeNode": LLMSummarizeNode,
    "LLMClassifyNode": LLMClassifyNode,
    "LLMTranslateNode": LLMTranslateNode,
}


def load_workflow_from_dict(
    workflow_data: Dict, skip_validation: bool = False
) -> WorkflowSchema:
    """
    Load a workflow from serialized dictionary data.

    SECURITY: Validates workflow structure before loading unless skip_validation=True.

    Args:
        workflow_data: Serialized workflow data
        skip_validation: Skip security validation (NOT RECOMMENDED)

    Returns:
        WorkflowSchema with actual node instances

    Raises:
        WorkflowValidationError: If validation fails
    """
    # SECURITY: Validate workflow structure before processing
    if not skip_validation:
        validate_workflow_structure(workflow_data)
        logger.info("Workflow validation passed")
    else:
        logger.warning(
            "Workflow validation SKIPPED - this is not recommended for untrusted workflows"
        )

    # Create metadata
    metadata = WorkflowMetadata.from_dict(workflow_data.get("metadata", {}))
    workflow = WorkflowSchema(metadata)

    # Deserialize nodes into instances
    nodes_dict: Dict[str, BaseNode] = {}

    for node_id, node_data in workflow_data.get("nodes", {}).items():
        node_type = node_data.get("node_type")
        config = node_data.get("config", {})

        if node_type in NODE_TYPE_MAP:
            node_class = NODE_TYPE_MAP[node_type]
            # Pass config as keyword argument
            node_instance = node_class(node_id, config=config)
            nodes_dict[node_id] = node_instance
            logger.debug(f"Loaded node {node_id}: {node_type} with config: {config}")
        else:
            logger.warning(f"Unknown node type: {node_type}")

    # Check if workflow already has a StartNode (from Canvas)
    has_start_node = any(node.node_type == "StartNode" for node in nodes_dict.values())

    # Auto-create hidden Start node ONLY if workflow doesn't have one (like Canvas does)
    if not has_start_node:
        start_node = StartNode("__auto_start__")
        nodes_dict["__auto_start__"] = start_node
        logger.info("Added auto-start node (no StartNode found in workflow)")
    else:
        logger.info("Workflow already has a StartNode, skipping auto-start creation")

    # Set nodes as instances (WorkflowRunner needs this)
    workflow.nodes = nodes_dict

    # Load connections
    for conn_data in workflow_data.get("connections", []):
        workflow.connections.append(NodeConnection.from_dict(conn_data))

    # Find entry points (nodes without exec_in connections) and auto-connect Start node
    # Only do this if we created __auto_start__
    if not has_start_node:
        connected_exec_ins = set()
        trigger_output_targets = set()  # Nodes connected to trigger exec_out

        for conn in workflow.connections:
            if conn.target_port == "exec_in":
                connected_exec_ins.add(conn.target_node)
            # Track what trigger nodes connect to
            source_node = nodes_dict.get(conn.source_node)
            if (
                source_node
                and "Trigger" in source_node.node_type
                and conn.source_port == "exec_out"
            ):
                trigger_output_targets.add(conn.target_node)

        # Auto-connect Start to entry points
        for node_id, node in nodes_dict.items():
            if node_id == "__auto_start__":
                continue

            # Skip trigger nodes - they're entry points themselves, not execution targets
            if "Trigger" in node.node_type:
                continue

            # Connect Start to:
            # 1. Nodes with unconnected exec_in, OR
            # 2. Nodes that are targets of trigger exec_out (so workflow runs from trigger's target)
            should_connect = (
                "exec_in" in node.input_ports and node_id not in connected_exec_ins
            ) or node_id in trigger_output_targets

            if should_connect:
                connection = NodeConnection(
                    source_node="__auto_start__",
                    source_port="exec_out",
                    target_node=node_id,
                    target_port="exec_in",
                )
                workflow.connections.append(connection)
                logger.info(f"Auto-connected Start → {node_id}")

    # Load variables and settings
    workflow.variables = workflow_data.get("variables", {})
    workflow.settings = workflow_data.get("settings", workflow.settings)

    logger.info(
        f"Loaded workflow '{metadata.name}' with {len(nodes_dict)} nodes and {len(workflow.connections)} connections"
    )
    return workflow

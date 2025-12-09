"""
CasareRPA - Nodes Package

Automation node implementations for workflow execution.

Entry Points:
    - StartNode, EndNode: Workflow entry/exit points
    - LaunchBrowserNode, ClickElementNode, TypeTextNode: Browser automation
    - ReadFileNode, WriteFileNode: File system operations
    - HttpRequestNode: REST API integration
    - ForLoopStartNode, IfNode, TryNode: Control flow
    - get_all_node_classes(): Get all registered node classes
    - preload_nodes(names): Preload specific nodes for performance

Key Patterns:
    - Lazy Loading: Nodes imported on first access via _NODE_REGISTRY
    - Decorator Registration: @executable_node registers node metadata
    - Base Classes: BrowserBaseNode, GoogleBaseNode for shared functionality
    - Async Execution: All node execute() methods are async
    - Property System: Nodes define input/output via typed properties
    - Category Organization: Nodes grouped by domain (browser, file, database)

Related:
    - Domain layer: Nodes implement BaseNode protocol
    - Application layer: NodeExecutor orchestrates node execution
    - Infrastructure layer: Nodes use adapters (Playwright, database drivers)
    - visual_nodes package: Visual representation for Canvas UI

Node Categories:
    - basic: Start, End, Comment
    - browser: Navigation, interaction, data extraction (Playwright)
    - file: Read, write, CSV, JSON, ZIP operations
    - database: SQL connections, queries, transactions
    - http: REST API requests, authentication, downloads
    - control_flow: If, loops, switch, try/catch
    - data_operation: String, list, dict, JSON operations
    - system: Clipboard, dialogs, commands, services
    - google: Gmail, Drive, Sheets, Docs, Calendar
    - messaging: Telegram, WhatsApp
    - desktop: Windows UI automation, Office integration
    - llm: AI/LLM integration nodes
    - trigger: Event-driven workflow triggers

This module uses lazy loading to improve startup performance.
Node classes are only imported when first accessed.
"""

import importlib
from typing import TYPE_CHECKING, Any, Dict, List, Type

__version__ = "0.1.0"

# Type hints for IDE support - these don't actually import at runtime
if TYPE_CHECKING:
    # Browser base classes and utilities
    from .browser import (
        BrowserBaseNode,
        get_page_from_context,
        take_failure_screenshot,
        BROWSER_TIMEOUT,
        BROWSER_RETRY_COUNT,
        BROWSER_RETRY_INTERVAL,
        BROWSER_SCREENSHOT_ON_FAIL,
        BROWSER_SCREENSHOT_PATH,
        BROWSER_SELECTOR,
        BROWSER_SELECTOR_STRICT,
        BROWSER_WAIT_UNTIL,
        BROWSER_FORCE,
        BROWSER_NO_WAIT_AFTER,
        BROWSER_HIGHLIGHT,
    )
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
        ImageClickNode,
    )
    from .data_nodes import (
        ExtractTextNode,
        GetAttributeNode,
        ScreenshotNode,
    )
    from .browser.table_scraper_node import TableScraperNode
    from .browser.form_field_node import FormFieldNode
    from .browser.form_filler_node import FormFillerNode
    from .browser.detect_forms_node import DetectFormsNode
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
        MergeNode,
        SwitchNode,
        TryNode,
        CatchNode,
        FinallyNode,
    )
    from .parallel_nodes import (
        ForkNode,
        JoinNode,
        ParallelForEachNode,
    )
    from .error_handling_nodes import (
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
    from casare_rpa.nodes.http import (
        HttpRequestNode as HttpRequestNodeNew,
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
    from .system import (
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
    from .llm import (
        LLMCompletionNode,
        LLMChatNode,
        LLMExtractDataNode,
        LLMSummarizeNode,
        LLMClassifyNode,
        LLMTranslateNode,
    )
    from .document import (
        ClassifyDocumentNode,
        ExtractInvoiceNode,
        ExtractFormNode,
        ExtractTableNode,
        ValidateExtractionNode,
    )
    from .messaging.telegram import (
        TelegramSendMessageNode,
        TelegramSendPhotoNode,
        TelegramSendDocumentNode,
        TelegramSendLocationNode,
        TelegramEditMessageNode,
        TelegramDeleteMessageNode,
        TelegramSendMediaGroupNode,
        TelegramAnswerCallbackNode,
        TelegramGetUpdatesNode,
    )
    from .messaging.whatsapp import (
        WhatsAppSendMessageNode,
        WhatsAppSendTemplateNode,
        WhatsAppSendImageNode,
        WhatsAppSendDocumentNode,
        WhatsAppSendVideoNode,
        WhatsAppSendLocationNode,
        WhatsAppSendInteractiveNode,
    )
    from .google.docs import (
        DocsGetDocumentNode,
        DocsGetTextNode,
        DocsExportNode,
        DocsCreateDocumentNode,
        DocsInsertTextNode,
        DocsAppendTextNode,
        DocsReplaceTextNode,
        DocsInsertTableNode,
        DocsInsertImageNode,
        DocsApplyStyleNode,
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
    "ImageClickNode": "interaction_nodes",
    # Data extraction nodes
    "ExtractTextNode": "data_nodes",
    "GetAttributeNode": "data_nodes",
    "ScreenshotNode": "data_nodes",
    # Table scraping nodes
    "TableScraperNode": "browser.table_scraper_node",
    # Form nodes
    "FormFieldNode": "browser.form_field_node",
    "FormFillerNode": "browser.form_filler_node",
    "DetectFormsNode": "browser.detect_forms_node",
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
    "MergeNode": "control_flow_nodes",
    "SwitchNode": "control_flow_nodes",
    # Try/Catch/Finally nodes
    "TryNode": "control_flow_nodes",
    "CatchNode": "control_flow_nodes",
    "FinallyNode": "control_flow_nodes",
    # Parallel execution nodes
    "ForkNode": "parallel_nodes",
    "JoinNode": "parallel_nodes",
    "ParallelForEachNode": "parallel_nodes",
    # Error handling nodes
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
    # File system nodes - read operations
    "ReadFileNode": "file.file_read_nodes",
    # File system nodes - write operations
    "WriteFileNode": "file.file_write_nodes",
    "AppendFileNode": "file.file_write_nodes",
    # File system nodes - file operations
    "DeleteFileNode": "file.file_system_nodes",
    "CopyFileNode": "file.file_system_nodes",
    "MoveFileNode": "file.file_system_nodes",
    # File system nodes - directory operations
    "CreateDirectoryNode": "file.directory_nodes",
    "ListDirectoryNode": "file.directory_nodes",
    "ListFilesNode": "file.directory_nodes",
    # File system nodes - path info operations
    "FileExistsNode": "file.path_nodes",
    "GetFileSizeNode": "file.path_nodes",
    "GetFileInfoNode": "file.path_nodes",
    # File system nodes - structured data
    "ReadCSVNode": "file.structured_data",
    "WriteCSVNode": "file.structured_data",
    "ReadJSONFileNode": "file.structured_data",
    "WriteJSONFileNode": "file.structured_data",
    "ZipFilesNode": "file.structured_data",
    "UnzipFilesNode": "file.structured_data",
    # Email nodes - send operations
    "SendEmailNode": "email.send_nodes",
    # Email nodes - receive/read operations
    "ReadEmailsNode": "email.receive_nodes",
    "GetEmailContentNode": "email.receive_nodes",
    "FilterEmailsNode": "email.receive_nodes",
    # Email nodes - IMAP management
    "SaveAttachmentNode": "email.imap_nodes",
    "MarkEmailNode": "email.imap_nodes",
    "DeleteEmailNode": "email.imap_nodes",
    "MoveEmailNode": "email.imap_nodes",
    # HTTP/REST API nodes
    "HttpRequestNode": "http.http_basic",
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
    # System nodes - Clipboard operations
    "ClipboardCopyNode": "system.clipboard_nodes",
    "ClipboardPasteNode": "system.clipboard_nodes",
    "ClipboardClearNode": "system.clipboard_nodes",
    # System nodes - Dialog operations
    "MessageBoxNode": "system.dialog_nodes",
    "InputDialogNode": "system.dialog_nodes",
    "TooltipNode": "system.dialog_nodes",
    "SystemNotificationNode": "system.dialog_nodes",
    "ConfirmDialogNode": "system.dialog_nodes",
    "ProgressDialogNode": "system.dialog_nodes",
    "FilePickerDialogNode": "system.dialog_nodes",
    "FolderPickerDialogNode": "system.dialog_nodes",
    "ColorPickerDialogNode": "system.dialog_nodes",
    "DateTimePickerDialogNode": "system.dialog_nodes",
    "SnackbarNode": "system.dialog_nodes",
    "BalloonTipNode": "system.dialog_nodes",
    # System nodes - Command execution
    "RunCommandNode": "system.command_nodes",
    "RunPowerShellNode": "system.command_nodes",
    # System nodes - Windows Services
    "GetServiceStatusNode": "system.service_nodes",
    "StartServiceNode": "system.service_nodes",
    "StopServiceNode": "system.service_nodes",
    "RestartServiceNode": "system.service_nodes",
    "ListServicesNode": "system.service_nodes",
    # System nodes - New dialog nodes
    "ListPickerDialogNode": "system.dialog_nodes",
    "MultilineInputDialogNode": "system.dialog_nodes",
    "CredentialDialogNode": "system.dialog_nodes",
    "FormDialogNode": "system.dialog_nodes",
    "ImagePreviewDialogNode": "system.dialog_nodes",
    "TableDialogNode": "system.dialog_nodes",
    "WizardDialogNode": "system.dialog_nodes",
    "SplashScreenNode": "system.dialog_nodes",
    "AudioAlertNode": "system.dialog_nodes",
    # System nodes - System utilities
    "ScreenRegionPickerNode": "system.system_nodes",
    "VolumeControlNode": "system.system_nodes",
    "ProcessListNode": "system.system_nodes",
    "ProcessKillNode": "system.system_nodes",
    "EnvironmentVariableNode": "system.system_nodes",
    "SystemInfoNode": "system.system_nodes",
    # System nodes - Quick nodes
    "HotkeyWaitNode": "system.quick_nodes",
    "BeepNode": "system.quick_nodes",
    "ClipboardMonitorNode": "system.quick_nodes",
    # System nodes - Utility nodes
    "FileWatcherNode": "system.utility_system_nodes",
    "QRCodeNode": "system.utility_system_nodes",
    "Base64Node": "system.utility_system_nodes",
    "UUIDGeneratorNode": "system.utility_system_nodes",
    "AssertSystemNode": "system.utility_system_nodes",
    "LogToFileNode": "system.utility_system_nodes",
    # System nodes - Media nodes
    "TextToSpeechNode": "system.media_nodes",
    "PDFPreviewDialogNode": "system.media_nodes",
    "WebcamCaptureNode": "system.media_nodes",
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
    # LLM nodes
    "LLMCompletionNode": "llm.llm_nodes",
    "LLMChatNode": "llm.llm_nodes",
    "LLMExtractDataNode": "llm.llm_nodes",
    "LLMSummarizeNode": "llm.llm_nodes",
    "LLMClassifyNode": "llm.llm_nodes",
    "LLMTranslateNode": "llm.llm_nodes",
    # Document AI nodes
    "ClassifyDocumentNode": "document.document_nodes",
    "ExtractInvoiceNode": "document.document_nodes",
    "ExtractFormNode": "document.document_nodes",
    "ExtractTableNode": "document.document_nodes",
    "ValidateExtractionNode": "document.document_nodes",
    # Trigger nodes - General
    "WebhookTriggerNode": "trigger_nodes.webhook_trigger_node",
    "ScheduleTriggerNode": "trigger_nodes.schedule_trigger_node",
    "FileWatchTriggerNode": "trigger_nodes.file_watch_trigger_node",
    "EmailTriggerNode": "trigger_nodes.email_trigger_node",
    "AppEventTriggerNode": "trigger_nodes.app_event_trigger_node",
    "ErrorTriggerNode": "trigger_nodes.error_trigger_node",
    "WorkflowCallTriggerNode": "trigger_nodes.workflow_call_trigger_node",
    "FormTriggerNode": "trigger_nodes.form_trigger_node",
    "ChatTriggerNode": "trigger_nodes.chat_trigger_node",
    "RSSFeedTriggerNode": "trigger_nodes.rss_feed_trigger_node",
    "SSETriggerNode": "trigger_nodes.sse_trigger_node",
    # Trigger nodes - Messaging
    "TelegramTriggerNode": "trigger_nodes.telegram_trigger_node",
    "WhatsAppTriggerNode": "trigger_nodes.whatsapp_trigger_node",
    # Trigger nodes - Google
    "GmailTriggerNode": "trigger_nodes.gmail_trigger_node",
    "DriveTriggerNode": "trigger_nodes.drive_trigger_node",
    "SheetsTriggerNode": "trigger_nodes.sheets_trigger_node",
    "CalendarTriggerNode": "trigger_nodes.calendar_trigger_node",
    # Google Calendar nodes - Event operations
    "CalendarListEventsNode": "google.calendar.calendar_events",
    "CalendarGetEventNode": "google.calendar.calendar_events",
    "CalendarCreateEventNode": "google.calendar.calendar_events",
    "CalendarUpdateEventNode": "google.calendar.calendar_events",
    "CalendarDeleteEventNode": "google.calendar.calendar_events",
    "CalendarQuickAddNode": "google.calendar.calendar_events",
    "CalendarMoveEventNode": "google.calendar.calendar_events",
    "CalendarGetFreeBusyNode": "google.calendar.calendar_events",
    # Google Calendar nodes - Management operations
    "CalendarListCalendarsNode": "google.calendar.calendar_manage",
    "CalendarGetCalendarNode": "google.calendar.calendar_manage",
    "CalendarCreateCalendarNode": "google.calendar.calendar_manage",
    "CalendarDeleteCalendarNode": "google.calendar.calendar_manage",
    # Telegram messaging nodes - Send
    "TelegramSendMessageNode": "messaging.telegram.telegram_send",
    "TelegramSendPhotoNode": "messaging.telegram.telegram_send",
    "TelegramSendDocumentNode": "messaging.telegram.telegram_send",
    "TelegramSendLocationNode": "messaging.telegram.telegram_send",
    # Telegram messaging nodes - Actions
    "TelegramEditMessageNode": "messaging.telegram.telegram_actions",
    "TelegramDeleteMessageNode": "messaging.telegram.telegram_actions",
    "TelegramSendMediaGroupNode": "messaging.telegram.telegram_actions",
    "TelegramAnswerCallbackNode": "messaging.telegram.telegram_actions",
    "TelegramGetUpdatesNode": "messaging.telegram.telegram_actions",
    # WhatsApp messaging nodes
    "WhatsAppSendMessageNode": "messaging.whatsapp.whatsapp_send",
    "WhatsAppSendTemplateNode": "messaging.whatsapp.whatsapp_send",
    "WhatsAppSendImageNode": "messaging.whatsapp.whatsapp_send",
    "WhatsAppSendDocumentNode": "messaging.whatsapp.whatsapp_send",
    "WhatsAppSendVideoNode": "messaging.whatsapp.whatsapp_send",
    "WhatsAppSendLocationNode": "messaging.whatsapp.whatsapp_send",
    "WhatsAppSendInteractiveNode": "messaging.whatsapp.whatsapp_send",
    # Google Docs nodes (standalone - with own OAuth)
    "DocsGetDocumentNode": "google.docs.docs_read",
    "DocsGetTextNode": "google.docs.docs_read",
    "DocsExportNode": "google.docs.docs_read",
    "DocsCreateDocumentNode": "google.docs.docs_write",
    "DocsInsertTextNode": "google.docs.docs_write",
    "DocsAppendTextNode": "google.docs.docs_write",
    "DocsReplaceTextNode": "google.docs.docs_write",
    "DocsInsertTableNode": "google.docs.docs_write",
    "DocsInsertImageNode": "google.docs.docs_write",
    "DocsApplyStyleNode": "google.docs.docs_write",
    # Gmail nodes (from google.gmail_nodes)
    "GmailSendEmailNode": "google.gmail_nodes",
    "GmailSendWithAttachmentNode": "google.gmail_nodes",
    "GmailCreateDraftNode": "google.gmail_nodes",
    "GmailSendDraftNode": "google.gmail_nodes",
    "GmailGetEmailNode": "google.gmail_nodes",
    "GmailListEmailsNode": "google.gmail_nodes",
    "GmailSearchEmailsNode": "google.gmail_nodes",
    "GmailGetThreadNode": "google.gmail_nodes",
    "GmailModifyLabelsNode": "google.gmail_nodes",
    "GmailMoveToTrashNode": "google.gmail_nodes",
    "GmailMarkAsReadNode": "google.gmail_nodes",
    "GmailMarkAsUnreadNode": "google.gmail_nodes",
    "GmailStarEmailNode": "google.gmail_nodes",
    "GmailArchiveEmailNode": "google.gmail_nodes",
    "GmailDeleteEmailNode": "google.gmail_nodes",
    "GmailBatchSendNode": "google.gmail_nodes",
    "GmailBatchModifyNode": "google.gmail_nodes",
    "GmailBatchDeleteNode": "google.gmail_nodes",
    "GmailReplyToEmailNode": "google.gmail.gmail_send",
    "GmailForwardEmailNode": "google.gmail.gmail_send",
    "GmailGetAttachmentNode": "google.gmail.gmail_read",
    # Sheets nodes (from google.sheets_nodes)
    "SheetsGetCellNode": "google.sheets_nodes",
    "SheetsSetCellNode": "google.sheets_nodes",
    "SheetsGetRangeNode": "google.sheets_nodes",
    "SheetsWriteRangeNode": "google.sheets_nodes",
    "SheetsClearRangeNode": "google.sheets_nodes",
    "SheetsCreateSpreadsheetNode": "google.sheets_nodes",
    "SheetsGetSpreadsheetNode": "google.sheets_nodes",
    "SheetsAddSheetNode": "google.sheets_nodes",
    "SheetsDeleteSheetNode": "google.sheets_nodes",
    "SheetsDuplicateSheetNode": "google.sheets_nodes",
    "SheetsRenameSheetNode": "google.sheets_nodes",
    "SheetsAppendRowNode": "google.sheets_nodes",
    "SheetsInsertRowNode": "google.sheets_nodes",
    "SheetsDeleteRowNode": "google.sheets_nodes",
    "SheetsInsertColumnNode": "google.sheets_nodes",
    "SheetsDeleteColumnNode": "google.sheets_nodes",
    "SheetsFormatCellsNode": "google.sheets_nodes",
    "SheetsAutoResizeNode": "google.sheets_nodes",
    "SheetsBatchUpdateNode": "google.sheets_nodes",
    "SheetsBatchGetNode": "google.sheets_nodes",
    "SheetsBatchClearNode": "google.sheets_nodes",
    # Drive nodes (from google.drive_nodes)
    "DriveUploadFileNode": "google.drive_nodes",
    "DriveDownloadFileNode": "google.drive_nodes",
    "DriveDeleteFileNode": "google.drive_nodes",
    "DriveCopyFileNode": "google.drive_nodes",
    "DriveMoveFileNode": "google.drive_nodes",
    "DriveRenameFileNode": "google.drive_nodes",
    "DriveGetFileNode": "google.drive_nodes",
    "DriveCreateFolderNode": "google.drive_nodes",
    "DriveListFilesNode": "google.drive_nodes",
    "DriveSearchFilesNode": "google.drive_nodes",
    "DriveShareFileNode": "google.drive_nodes",
    "DriveRemovePermissionNode": "google.drive_nodes",
    "DriveGetPermissionsNode": "google.drive_nodes",
    "DriveExportFileNode": "google.drive_nodes",
    "DriveBatchDeleteNode": "google.drive_nodes",
    "DriveBatchMoveNode": "google.drive_nodes",
    "DriveBatchCopyNode": "google.drive_nodes",
    # Desktop/Office automation nodes
    "ExcelOpenNode": "desktop_nodes.office_nodes",
    "ExcelReadCellNode": "desktop_nodes.office_nodes",
    "ExcelWriteCellNode": "desktop_nodes.office_nodes",
    "ExcelGetRangeNode": "desktop_nodes.office_nodes",
    "ExcelCloseNode": "desktop_nodes.office_nodes",
    "WordOpenNode": "desktop_nodes.office_nodes",
    "WordGetTextNode": "desktop_nodes.office_nodes",
    "WordReplaceTextNode": "desktop_nodes.office_nodes",
    "WordCloseNode": "desktop_nodes.office_nodes",
    "OutlookSendEmailNode": "desktop_nodes.office_nodes",
    "OutlookReadEmailsNode": "desktop_nodes.office_nodes",
    "OutlookGetInboxCountNode": "desktop_nodes.office_nodes",
    # Desktop Automation Nodes - Application
    "LaunchApplicationNode": "desktop_nodes",
    "CloseApplicationNode": "desktop_nodes",
    "ActivateWindowNode": "desktop_nodes",
    "GetWindowListNode": "desktop_nodes",
    # Desktop Automation Nodes - Element
    "FindElementNode": "desktop_nodes",
    "DesktopClickElementNode": ("desktop_nodes", "ClickElementNode"),
    "DesktopTypeTextNode": ("desktop_nodes", "TypeTextNode"),
    "GetElementTextNode": "desktop_nodes",
    "GetElementPropertyNode": "desktop_nodes",
    # Desktop Automation Nodes - Window
    "ResizeWindowNode": "desktop_nodes",
    "MoveWindowNode": "desktop_nodes",
    "MaximizeWindowNode": "desktop_nodes",
    "MinimizeWindowNode": "desktop_nodes",
    "RestoreWindowNode": "desktop_nodes",
    "GetWindowPropertiesNode": "desktop_nodes",
    "SetWindowStateNode": "desktop_nodes",
    # Desktop Automation Nodes - Interaction
    "SelectFromDropdownNode": "desktop_nodes",
    "CheckCheckboxNode": "desktop_nodes",
    "SelectRadioButtonNode": "desktop_nodes",
    "SelectTabNode": "desktop_nodes",
    "ExpandTreeItemNode": "desktop_nodes",
    "ScrollElementNode": "desktop_nodes",
    # Desktop Automation Nodes - Mouse/Keyboard
    "MoveMouseNode": "desktop_nodes",
    "MouseClickNode": "desktop_nodes",
    "SendKeysNode": "desktop_nodes",
    "SendHotKeyNode": "desktop_nodes",
    "GetMousePositionNode": "desktop_nodes",
    "DragMouseNode": "desktop_nodes",
    # Desktop Automation Nodes - Wait/Verification
    "DesktopWaitForElementNode": ("desktop_nodes", "WaitForElementNode"),
    "WaitForWindowNode": "desktop_nodes",
    "VerifyElementExistsNode": "desktop_nodes",
    "VerifyElementPropertyNode": "desktop_nodes",
    # Desktop Automation Nodes - Screenshot/OCR
    "CaptureScreenshotNode": "desktop_nodes",
    "CaptureElementImageNode": "desktop_nodes",
    "OCRExtractTextNode": "desktop_nodes",
    "CompareImagesNode": "desktop_nodes",
    # Gmail Label Management Nodes
    "GmailAddLabelNode": "google.gmail_nodes",
    "GmailRemoveLabelNode": "google.gmail_nodes",
    "GmailGetLabelsNode": "google.gmail_nodes",
    "GmailTrashEmailNode": "google.gmail_nodes",
    # Subflow nodes
    "SubflowNode": "subflow_node",
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

    Registry format:
        - String: module path, class name matches registry key
        - Tuple (module_path, class_name): for aliases where key != class name
    """
    # Check cache first
    if name in _loaded_classes:
        return _loaded_classes[name]

    # Check if it's a known node class
    if name not in _NODE_REGISTRY:
        raise AttributeError(f"module 'casare_rpa.nodes' has no attribute '{name}'")

    registry_entry = _NODE_REGISTRY[name]

    # Handle both string and tuple entries
    if isinstance(registry_entry, tuple):
        module_name, class_name = registry_entry
    else:
        module_name = registry_entry
        class_name = name

    # Load the module if not already loaded
    if module_name not in _loaded_modules:
        full_module_name = f".{module_name}"
        _loaded_modules[module_name] = importlib.import_module(
            full_module_name, package="casare_rpa.nodes"
        )

    # Get the class from the module
    module = _loaded_modules[module_name]
    cls = getattr(module, class_name)

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
    "ImageClickNode",
    # Data extraction
    "ExtractTextNode",
    "GetAttributeNode",
    "ScreenshotNode",
    # Table scraping
    "TableScraperNode",
    # Form nodes
    "FormFieldNode",
    "FormFillerNode",
    "DetectFormsNode",
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
    "MergeNode",
    "SwitchNode",
    # Parallel execution nodes
    "ForkNode",
    "JoinNode",
    "ParallelForEachNode",
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
    "HttpRequestNode",
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
    "SystemNotificationNode",
    "ConfirmDialogNode",
    "ProgressDialogNode",
    "FilePickerDialogNode",
    "FolderPickerDialogNode",
    "ColorPickerDialogNode",
    "DateTimePickerDialogNode",
    "SnackbarNode",
    "BalloonTipNode",
    "RunCommandNode",
    "RunPowerShellNode",
    "GetServiceStatusNode",
    "StartServiceNode",
    "StopServiceNode",
    "RestartServiceNode",
    "ListServicesNode",
    # New dialog nodes
    "ListPickerDialogNode",
    "MultilineInputDialogNode",
    "CredentialDialogNode",
    "FormDialogNode",
    "ImagePreviewDialogNode",
    "TableDialogNode",
    "WizardDialogNode",
    "SplashScreenNode",
    "AudioAlertNode",
    # System utilities
    "ScreenRegionPickerNode",
    "VolumeControlNode",
    "ProcessListNode",
    "ProcessKillNode",
    "EnvironmentVariableNode",
    "SystemInfoNode",
    # Quick nodes
    "HotkeyWaitNode",
    "BeepNode",
    "ClipboardMonitorNode",
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
    # LLM nodes
    "LLMCompletionNode",
    "LLMChatNode",
    "LLMExtractDataNode",
    "LLMSummarizeNode",
    "LLMClassifyNode",
    "LLMTranslateNode",
    # Document AI nodes
    "ClassifyDocumentNode",
    "ExtractInvoiceNode",
    "ExtractFormNode",
    "ExtractTableNode",
    "ValidateExtractionNode",
    # Trigger nodes - General
    "WebhookTriggerNode",
    "ScheduleTriggerNode",
    "FileWatchTriggerNode",
    "EmailTriggerNode",
    "AppEventTriggerNode",
    "ErrorTriggerNode",
    "WorkflowCallTriggerNode",
    "FormTriggerNode",
    "ChatTriggerNode",
    "RSSFeedTriggerNode",
    "SSETriggerNode",
    # Trigger nodes - Messaging
    "TelegramTriggerNode",
    "WhatsAppTriggerNode",
    # Trigger nodes - Google
    "GmailTriggerNode",
    "DriveTriggerNode",
    "SheetsTriggerNode",
    "CalendarTriggerNode",
    # Telegram messaging nodes - Send
    "TelegramSendMessageNode",
    "TelegramSendPhotoNode",
    "TelegramSendDocumentNode",
    "TelegramSendLocationNode",
    # Telegram messaging nodes - Actions
    "TelegramEditMessageNode",
    "TelegramDeleteMessageNode",
    "TelegramSendMediaGroupNode",
    "TelegramAnswerCallbackNode",
    "TelegramGetUpdatesNode",
    # WhatsApp messaging nodes
    "WhatsAppSendMessageNode",
    "WhatsAppSendTemplateNode",
    "WhatsAppSendImageNode",
    "WhatsAppSendDocumentNode",
    "WhatsAppSendVideoNode",
    "WhatsAppSendLocationNode",
    "WhatsAppSendInteractiveNode",
    # Google Docs nodes (standalone)
    "DocsGetDocumentNode",
    "DocsGetTextNode",
    "DocsExportNode",
    "DocsCreateDocumentNode",
    "DocsInsertTextNode",
    "DocsAppendTextNode",
    "DocsReplaceTextNode",
    "DocsInsertTableNode",
    "DocsInsertImageNode",
    "DocsApplyStyleNode",
    # Desktop/Office automation nodes
    "ExcelOpenNode",
    "ExcelReadCellNode",
    "ExcelWriteCellNode",
    "ExcelGetRangeNode",
    "ExcelCloseNode",
    "WordOpenNode",
    "WordGetTextNode",
    "WordReplaceTextNode",
    "WordCloseNode",
    "OutlookSendEmailNode",
    "OutlookReadEmailsNode",
    "OutlookGetInboxCountNode",
    # Desktop Automation Nodes - Application
    "LaunchApplicationNode",
    "CloseApplicationNode",
    "ActivateWindowNode",
    "GetWindowListNode",
    # Desktop Automation Nodes - Element
    "FindElementNode",
    "DesktopClickElementNode",
    "DesktopTypeTextNode",
    "GetElementTextNode",
    "GetElementPropertyNode",
    # Desktop Automation Nodes - Window
    "ResizeWindowNode",
    "MoveWindowNode",
    "MaximizeWindowNode",
    "MinimizeWindowNode",
    "RestoreWindowNode",
    "GetWindowPropertiesNode",
    "SetWindowStateNode",
    # Desktop Automation Nodes - Interaction
    "SelectFromDropdownNode",
    "CheckCheckboxNode",
    "SelectRadioButtonNode",
    "SelectTabNode",
    "ExpandTreeItemNode",
    "ScrollElementNode",
    # Desktop Automation Nodes - Mouse/Keyboard
    "MoveMouseNode",
    "MouseClickNode",
    "SendKeysNode",
    "SendHotKeyNode",
    "GetMousePositionNode",
    "DragMouseNode",
    # Desktop Automation Nodes - Wait/Verification
    "DesktopWaitForElementNode",
    "WaitForWindowNode",
    "VerifyElementExistsNode",
    "VerifyElementPropertyNode",
    # Desktop Automation Nodes - Screenshot/OCR
    "CaptureScreenshotNode",
    "CaptureElementImageNode",
    "OCRExtractTextNode",
    "CompareImagesNode",
    # Gmail Label Management Nodes
    "GmailAddLabelNode",
    "GmailRemoveLabelNode",
    "GmailGetLabelsNode",
    "GmailTrashEmailNode",
    # Utility functions
    "get_all_node_classes",
    "preload_nodes",
    # Preloader for startup optimization
    "start_node_preload",
    "is_preload_complete",
    "wait_for_preload",
]


# Re-export preloader functions for convenience
def start_node_preload() -> None:
    """Start background node preloading for improved startup performance."""
    from casare_rpa.nodes.preloader import start_node_preload as _start

    _start()


def is_preload_complete() -> bool:
    """Check if preloading has completed."""
    from casare_rpa.nodes.preloader import is_preload_complete as _check

    return _check()


def wait_for_preload(timeout: float = 5.0) -> bool:
    """Wait for preloading to complete."""
    from casare_rpa.nodes.preloader import wait_for_preload as _wait

    return _wait(timeout)

"""
System operation nodes for CasareRPA.

This package provides nodes for system-level operations:
- Clipboard operations (copy, paste, clear)
- Message boxes and dialogs
- Terminal/CMD command execution
- Windows Services management
- System utilities (volume, processes, env vars)
- Quick nodes (hotkeys, beeps, clipboard monitor)
"""

from casare_rpa.nodes.system.clipboard_nodes import (
    ClipboardCopyNode,
    ClipboardPasteNode,
    ClipboardClearNode,
)
from casare_rpa.nodes.system.dialog_nodes import (
    MessageBoxNode,
    InputDialogNode,
    TooltipNode,
    SystemNotificationNode,
    ConfirmDialogNode,
    ProgressDialogNode,
    FilePickerDialogNode,
    FolderPickerDialogNode,
    ColorPickerDialogNode,
    DateTimePickerDialogNode,
    SnackbarNode,
    BalloonTipNode,
    # New dialog nodes
    ListPickerDialogNode,
    MultilineInputDialogNode,
    CredentialDialogNode,
    FormDialogNode,
    ImagePreviewDialogNode,
    TableDialogNode,
    WizardDialogNode,
    SplashScreenNode,
    AudioAlertNode,
)
from casare_rpa.nodes.system.command_nodes import (
    RunCommandNode,
    RunPowerShellNode,
    SecurityError,
)
from casare_rpa.nodes.system.service_nodes import (
    GetServiceStatusNode,
    StartServiceNode,
    StopServiceNode,
    RestartServiceNode,
    ListServicesNode,
)
from casare_rpa.nodes.system.system_nodes import (
    ScreenRegionPickerNode,
    VolumeControlNode,
    ProcessListNode,
    ProcessKillNode,
    EnvironmentVariableNode,
    SystemInfoNode,
)
from casare_rpa.nodes.system.quick_nodes import (
    HotkeyWaitNode,
    BeepNode,
    ClipboardMonitorNode,
)
from casare_rpa.nodes.system.utility_system_nodes import (
    FileWatcherNode,
    QRCodeNode,
    Base64Node,
    UUIDGeneratorNode,
    AssertSystemNode,
    LogToFileNode,
)
from casare_rpa.nodes.system.media_nodes import (
    TextToSpeechNode,
    PDFPreviewDialogNode,
    WebcamCaptureNode,
)

__all__ = [
    # Clipboard operations
    "ClipboardCopyNode",
    "ClipboardPasteNode",
    "ClipboardClearNode",
    # Dialog/Message operations
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
    # Command execution
    "RunCommandNode",
    "RunPowerShellNode",
    "SecurityError",
    # Windows Services
    "GetServiceStatusNode",
    "StartServiceNode",
    "StopServiceNode",
    "RestartServiceNode",
    "ListServicesNode",
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
    # Utility system nodes
    "FileWatcherNode",
    "QRCodeNode",
    "Base64Node",
    "UUIDGeneratorNode",
    "AssertSystemNode",
    "LogToFileNode",
    # Media nodes
    "TextToSpeechNode",
    "PDFPreviewDialogNode",
    "WebcamCaptureNode",
]

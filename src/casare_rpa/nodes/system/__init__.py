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
    ClipboardClearNode,
    ClipboardCopyNode,
    ClipboardPasteNode,
)
from casare_rpa.nodes.system.command_nodes import (
    RunCommandNode,
    RunPowerShellNode,
    SecurityError,
)
from casare_rpa.nodes.system.dialog_nodes import (
    AudioAlertNode,
    BalloonTipNode,
    ColorPickerDialogNode,
    ConfirmDialogNode,
    CredentialDialogNode,
    DateTimePickerDialogNode,
    FilePickerDialogNode,
    FolderPickerDialogNode,
    FormDialogNode,
    ImagePreviewDialogNode,
    InputDialogNode,
    # New dialog nodes
    ListPickerDialogNode,
    MessageBoxNode,
    MultilineInputDialogNode,
    ProgressDialogNode,
    SnackbarNode,
    SplashScreenNode,
    SystemNotificationNode,
    TableDialogNode,
    TooltipNode,
    WizardDialogNode,
)
from casare_rpa.nodes.system.media_nodes import (
    PDFPreviewDialogNode,
    TextToSpeechNode,
    WebcamCaptureNode,
)
from casare_rpa.nodes.system.quick_nodes import (
    BeepNode,
    ClipboardMonitorNode,
    HotkeyWaitNode,
)
from casare_rpa.nodes.system.service_nodes import (
    GetServiceStatusNode,
    ListServicesNode,
    RestartServiceNode,
    StartServiceNode,
    StopServiceNode,
)
from casare_rpa.nodes.system.system_nodes import (
    EnvironmentVariableNode,
    ProcessKillNode,
    ProcessListNode,
    ScreenRegionPickerNode,
    SystemInfoNode,
    VolumeControlNode,
)
from casare_rpa.nodes.system.utility_system_nodes import (
    AssertSystemNode,
    Base64Node,
    FileWatcherNode,
    LogToFileNode,
    QRCodeNode,
    UUIDGeneratorNode,
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

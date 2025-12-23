"""
Visual Nodes - System
"""

from casare_rpa.presentation.canvas.visual_nodes.system.nodes import (
    VisualAssertSystemNode,
    VisualAudioAlertNode,
    VisualBalloonTipNode,
    VisualBase64Node,
    VisualBeepNode,
    VisualClipboardClearNode,
    # Clipboard operations
    VisualClipboardCopyNode,
    VisualClipboardMonitorNode,
    VisualClipboardPasteNode,
    VisualColorPickerDialogNode,
    VisualConfirmDialogNode,
    VisualCredentialDialogNode,
    VisualDateTimePickerDialogNode,
    VisualEnvironmentVariableNode,
    VisualFilePickerDialogNode,
    # Utility system nodes
    VisualFileWatcherNode,
    VisualFolderPickerDialogNode,
    VisualFormDialogNode,
    # Windows Services
    VisualGetServiceStatusNode,
    # Quick nodes
    VisualHotkeyWaitNode,
    VisualImagePreviewDialogNode,
    VisualInputDialogNode,
    # New dialog nodes
    VisualListPickerDialogNode,
    VisualListServicesNode,
    VisualLogToFileNode,
    # Dialogs
    VisualMessageBoxNode,
    VisualMultilineInputDialogNode,
    VisualPDFPreviewDialogNode,
    VisualProcessKillNode,
    VisualProcessListNode,
    VisualProgressDialogNode,
    VisualQRCodeNode,
    VisualRestartServiceNode,
    # Terminal
    VisualRunCommandNode,
    VisualRunPowerShellNode,
    # System utilities
    VisualScreenRegionPickerNode,
    VisualSnackbarNode,
    VisualSplashScreenNode,
    VisualStartServiceNode,
    VisualStopServiceNode,
    VisualSystemInfoNode,
    VisualSystemNotificationNode,
    VisualTableDialogNode,
    # Media nodes
    VisualTextToSpeechNode,
    VisualTooltipNode,
    VisualUUIDGeneratorNode,
    VisualVolumeControlNode,
    VisualWebcamCaptureNode,
    VisualWizardDialogNode,
)

__all__ = [
    # Clipboard operations
    "VisualClipboardCopyNode",
    "VisualClipboardPasteNode",
    "VisualClipboardClearNode",
    # Dialogs
    "VisualMessageBoxNode",
    "VisualInputDialogNode",
    "VisualTooltipNode",
    "VisualSystemNotificationNode",
    "VisualConfirmDialogNode",
    "VisualProgressDialogNode",
    "VisualFilePickerDialogNode",
    "VisualFolderPickerDialogNode",
    "VisualColorPickerDialogNode",
    "VisualDateTimePickerDialogNode",
    "VisualSnackbarNode",
    "VisualBalloonTipNode",
    # New dialog nodes
    "VisualListPickerDialogNode",
    "VisualMultilineInputDialogNode",
    "VisualCredentialDialogNode",
    "VisualFormDialogNode",
    "VisualImagePreviewDialogNode",
    "VisualTableDialogNode",
    "VisualWizardDialogNode",
    "VisualSplashScreenNode",
    "VisualAudioAlertNode",
    # Terminal
    "VisualRunCommandNode",
    "VisualRunPowerShellNode",
    # Windows Services
    "VisualGetServiceStatusNode",
    "VisualStartServiceNode",
    "VisualStopServiceNode",
    "VisualRestartServiceNode",
    "VisualListServicesNode",
    # System utilities
    "VisualScreenRegionPickerNode",
    "VisualVolumeControlNode",
    "VisualProcessListNode",
    "VisualProcessKillNode",
    "VisualEnvironmentVariableNode",
    "VisualSystemInfoNode",
    # Quick nodes
    "VisualHotkeyWaitNode",
    "VisualBeepNode",
    "VisualClipboardMonitorNode",
    # Utility system nodes
    "VisualFileWatcherNode",
    "VisualQRCodeNode",
    "VisualBase64Node",
    "VisualUUIDGeneratorNode",
    "VisualAssertSystemNode",
    "VisualLogToFileNode",
    # Media nodes
    "VisualTextToSpeechNode",
    "VisualPDFPreviewDialogNode",
    "VisualWebcamCaptureNode",
]

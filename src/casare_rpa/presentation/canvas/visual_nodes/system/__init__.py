"""
Visual Nodes - System
"""

from casare_rpa.presentation.canvas.visual_nodes.system.nodes import (
    # Clipboard operations
    VisualClipboardCopyNode,
    VisualClipboardPasteNode,
    VisualClipboardClearNode,
    # Dialogs
    VisualMessageBoxNode,
    VisualInputDialogNode,
    VisualTooltipNode,
    VisualSystemNotificationNode,
    VisualConfirmDialogNode,
    VisualProgressDialogNode,
    VisualFilePickerDialogNode,
    VisualFolderPickerDialogNode,
    VisualColorPickerDialogNode,
    VisualDateTimePickerDialogNode,
    VisualSnackbarNode,
    VisualBalloonTipNode,
    # New dialog nodes
    VisualListPickerDialogNode,
    VisualMultilineInputDialogNode,
    VisualCredentialDialogNode,
    VisualFormDialogNode,
    VisualImagePreviewDialogNode,
    VisualTableDialogNode,
    VisualWizardDialogNode,
    VisualSplashScreenNode,
    VisualAudioAlertNode,
    # Terminal
    VisualRunCommandNode,
    VisualRunPowerShellNode,
    # Windows Services
    VisualGetServiceStatusNode,
    VisualStartServiceNode,
    VisualStopServiceNode,
    VisualRestartServiceNode,
    VisualListServicesNode,
    # System utilities
    VisualScreenRegionPickerNode,
    VisualVolumeControlNode,
    VisualProcessListNode,
    VisualProcessKillNode,
    VisualEnvironmentVariableNode,
    VisualSystemInfoNode,
    # Quick nodes
    VisualHotkeyWaitNode,
    VisualBeepNode,
    VisualClipboardMonitorNode,
    # Utility system nodes
    VisualFileWatcherNode,
    VisualQRCodeNode,
    VisualBase64Node,
    VisualUUIDGeneratorNode,
    VisualAssertSystemNode,
    VisualLogToFileNode,
    # Media nodes
    VisualTextToSpeechNode,
    VisualPDFPreviewDialogNode,
    VisualWebcamCaptureNode,
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

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

__all__ = [
    # Clipboard operations
    "VisualClipboardCopyNode",
    "VisualClipboardPasteNode",
    "VisualClipboardClearNode",
    # Dialogs
    "VisualMessageBoxNode",
    "VisualInputDialogNode",
    "VisualTooltipNode",
    # Terminal
    "VisualRunCommandNode",
    "VisualRunPowerShellNode",
    # Windows Services
    "VisualGetServiceStatusNode",
    "VisualStartServiceNode",
    "VisualStopServiceNode",
    "VisualRestartServiceNode",
    "VisualListServicesNode",
]

"""
System operation nodes for CasareRPA.

This package provides nodes for system-level operations:
- Clipboard operations (copy, paste, clear)
- Message boxes and dialogs
- Terminal/CMD command execution
- Windows Services management
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

__all__ = [
    # Clipboard operations
    "ClipboardCopyNode",
    "ClipboardPasteNode",
    "ClipboardClearNode",
    # Dialog/Message operations
    "MessageBoxNode",
    "InputDialogNode",
    "TooltipNode",
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
]

"""
Managers for MainWindow.

Managers handle specific subsystems like popups, reducing
MainWindow's direct responsibilities.
"""

from .popup_manager import PopupManager, get_popup_manager
from .quick_node_manager import QuickNodeBinding, QuickNodeManager

__all__ = [
    "PopupManager",
    "get_popup_manager",
    "QuickNodeBinding",
    "QuickNodeManager",
]

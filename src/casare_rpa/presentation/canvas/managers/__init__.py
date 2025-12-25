"""
Managers for MainWindow.

Managers handle specific subsystems like panels and popups, reducing
MainWindow's direct responsibilities.
"""

from .panel_manager import PanelManager
from .popup_manager import PopupManager, get_popup_manager

__all__ = ["PanelManager", "PopupManager", "get_popup_manager"]

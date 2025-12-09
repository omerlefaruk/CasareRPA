"""
Managers for MainWindow.

Managers handle specific subsystems like panels, reducing
MainWindow's direct responsibilities.
"""

from .panel_manager import PanelManager

__all__ = ["PanelManager"]

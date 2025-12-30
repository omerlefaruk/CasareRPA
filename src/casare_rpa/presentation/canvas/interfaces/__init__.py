"""Presentation layer interfaces.

This package contains protocol/interface definitions for the Canvas UI layer.
These protocols enable loose coupling between UI components.

Epic 1.1: Enhanced IMainWindow protocol with comprehensive interface.
"""

from casare_rpa.presentation.canvas.interfaces.main_window import IMainWindow

# Type alias for controller use
MainWindowLike = IMainWindow
"""
Type alias for IMainWindow.

Use in controller type hints:

    from casare_rpa.presentation.canvas.interfaces import IMainWindow, MainWindowLike

    class MyController(BaseController):
        def __init__(self, main_window: MainWindowLike):
            self.main_window = main_window
"""

__all__ = [
    "IMainWindow",
    "MainWindowLike",
]

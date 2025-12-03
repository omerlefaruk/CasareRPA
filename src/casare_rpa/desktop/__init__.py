"""
Desktop Automation Module for CasareRPA

Provides Windows desktop automation capabilities using UI Automation.
Supports Win32, WPF, UWP, WinForms, Qt applications.

Architecture:
- DesktopContext: Main facade composing all managers (sync + async API)
- Managers: Focused classes for specific automation domains
  - WindowManager: Window operations (find, launch, close, resize, etc.)
  - MouseController: Mouse operations (move, click, drag, scroll)
  - KeyboardController: Keyboard operations (send keys, hotkeys, type)
  - FormInteractor: Form controls (dropdowns, checkboxes, tabs, trees)
  - ScreenCapture: Screenshots, OCR, image comparison
  - WaitManager: Wait for elements, windows, conditions
"""

from casare_rpa.desktop.context import DesktopContext
from casare_rpa.desktop.element import DesktopElement
from casare_rpa.desktop.managers import (
    FormInteractor,
    KeyboardController,
    MouseController,
    ScreenCapture,
    WaitManager,
    WindowManager,
)
from casare_rpa.desktop.selector import find_element, find_elements, parse_selector

__all__ = [
    # Main facade
    "DesktopContext",
    # Element wrapper
    "DesktopElement",
    # Selector utilities
    "parse_selector",
    "find_element",
    "find_elements",
    # Individual managers (async-first)
    "WindowManager",
    "MouseController",
    "KeyboardController",
    "FormInteractor",
    "ScreenCapture",
    "WaitManager",
]

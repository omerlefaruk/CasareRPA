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

from .context import DesktopContext
from .element import DesktopElement
from .selector import parse_selector, find_element, find_elements

# Export managers for direct async usage
from .managers import (
    WindowManager,
    MouseController,
    KeyboardController,
    FormInteractor,
    ScreenCapture,
    WaitManager,
)

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

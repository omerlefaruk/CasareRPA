"""
Desktop Automation Module for CasareRPA

Provides Windows desktop automation capabilities using UI Automation.
Supports Win32, WPF, UWP, WinForms, Qt applications.
"""

from .context import DesktopContext
from .element import DesktopElement
from .selector import parse_selector, find_element, find_elements

__all__ = [
    "DesktopContext",
    "DesktopElement",
    "parse_selector",
    "find_element",
    "find_elements",
]

"""Unified Selector Dialog Tabs."""

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    AnchorData,
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)
from casare_rpa.presentation.canvas.selectors.tabs.browser_tab import BrowserSelectorTab
from casare_rpa.presentation.canvas.selectors.tabs.desktop_tab import DesktopSelectorTab
from casare_rpa.presentation.canvas.selectors.tabs.image_match_tab import ImageMatchTab
from casare_rpa.presentation.canvas.selectors.tabs.ocr_tab import OCRSelectorTab

__all__ = [
    # Base classes and data structures
    "BaseSelectorTab",
    "SelectorResult",
    "SelectorStrategy",
    "AnchorData",
    # Tab implementations
    "BrowserSelectorTab",
    "DesktopSelectorTab",
    "OCRSelectorTab",
    "ImageMatchTab",
]

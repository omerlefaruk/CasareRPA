"""
Selector Dialog Components.

Extracted components from UnifiedSelectorDialog for separation of concerns:
- SelectorPicker: Element picking logic for browser/desktop/OCR/image modes
- SelectorValidator: Selector validation and testing
- SelectorPreview: Preview rendering and strategies display
- SelectorHistoryManager: History management and persistence
"""

from casare_rpa.presentation.canvas.selectors.components.selector_history_manager import (
    SelectorHistoryManager,
)
from casare_rpa.presentation.canvas.selectors.components.selector_picker import (
    SelectorPicker,
)
from casare_rpa.presentation.canvas.selectors.components.selector_preview import (
    SelectorPreview,
)
from casare_rpa.presentation.canvas.selectors.components.selector_validator import (
    SelectorValidator,
)

__all__ = [
    "SelectorPicker",
    "SelectorValidator",
    "SelectorPreview",
    "SelectorHistoryManager",
]

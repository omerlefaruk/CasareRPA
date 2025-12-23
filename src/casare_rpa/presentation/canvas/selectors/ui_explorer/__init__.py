"""
UI Explorer Module.

UiPath-style UI Explorer dialog for deep element inspection and selector building.
Complements UnifiedSelectorDialog with advanced features:
- Full visual tree navigation
- Property explorer
- Selector attribute editor (checkbox-based)
- Selector preview with XML syntax highlighting
- Multi-framework support (Browser/Desktop)
"""

from casare_rpa.presentation.canvas.selectors.ui_explorer.models import (
    ElementSource,
    SelectorAttribute,
    SelectorModel,
    UIExplorerElement,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels import (
    PropertyExplorerPanel,
    SelectedAttributesPanel,
    SelectorEditorPanel,
    SelectorPreviewPanel,
    VisualTreeItem,
    VisualTreePanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.toolbar import (
    UIExplorerToolbar,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.ui_explorer_dialog import (
    UIExplorerDialog,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets import (
    AttributeRow,
    UIExplorerStatusBar,
    XMLHighlighter,
)

__all__ = [
    # Dialog and Toolbar
    "UIExplorerDialog",
    "UIExplorerToolbar",
    # Models
    "UIExplorerElement",
    "ElementSource",
    "SelectorModel",
    "SelectorAttribute",
    # Panels
    "VisualTreePanel",
    "VisualTreeItem",
    "SelectorEditorPanel",
    "SelectedAttributesPanel",
    "PropertyExplorerPanel",
    "SelectorPreviewPanel",
    # Widgets
    "AttributeRow",
    "XMLHighlighter",
    "UIExplorerStatusBar",
]

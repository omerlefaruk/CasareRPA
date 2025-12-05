"""
UI Explorer Panels Module.

Contains panel components for the UI Explorer dialog:
- VisualTreePanel: Tree with DOM/UI hierarchy
- SelectorEditorPanel: Checkbox-based attribute editor
- SelectedAttributesPanel: Quick view of selected attributes
- PropertyExplorerPanel: Full property table
- SelectorPreviewPanel: XML/CSS/XPath preview with highlighting
"""

from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.visual_tree_panel import (
    VisualTreePanel,
    VisualTreeItem,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.selector_editor_panel import (
    SelectorEditorPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.selected_attrs_panel import (
    SelectedAttributesPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.property_explorer_panel import (
    PropertyExplorerPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.selector_preview_panel import (
    SelectorPreviewPanel,
)

__all__ = [
    "VisualTreePanel",
    "VisualTreeItem",
    "SelectorEditorPanel",
    "SelectedAttributesPanel",
    "PropertyExplorerPanel",
    "SelectorPreviewPanel",
]

"""
UI Explorer Widgets Module.

Contains custom widgets for the UI Explorer:
- AttributeRow: Checkbox + name + value row widget
- XMLHighlighter: QSyntaxHighlighter for XML preview
- UIExplorerStatusBar: Enhanced status bar with three sections
- AnchorPanel: Anchor element display and management panel
"""

from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.attribute_row import (
    AttributeRow,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.xml_highlighter import (
    XMLHighlighter,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.status_bar_widget import (
    UIExplorerStatusBar,
    StatusSection,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.anchor_panel import (
    AnchorPanel,
)

__all__ = [
    "AttributeRow",
    "XMLHighlighter",
    "UIExplorerStatusBar",
    "StatusSection",
    "AnchorPanel",
]

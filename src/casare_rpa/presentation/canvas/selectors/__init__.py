"""
Selector UI components.

This package provides UI components for element selection:
- ElementSelectorDialog: New streamlined element picker (recommended)
- UIExplorerDialog: Advanced full-featured UI explorer
- UnifiedSelectorDialog: Legacy unified dialog

State Management:
- ElementSelectorState: Centralized state for selector dialog
- StateManager: Qt signals-based state management

Widgets:
- ToolbarWidget: Pick/Stop/Mode controls
- ElementPreviewWidget: HTML preview with properties
- SelectorBuilderWidget: Attribute rows with scores
- AnchorWidget: Anchor configuration
- AdvancedOptionsWidget: Fuzzy/CV/Image options
- PickerToolbar: Floating toolbar during picking

History:
- SelectorHistory: JSON-based history storage
"""

from casare_rpa.presentation.canvas.selectors.unified_selector_dialog import (
    UnifiedSelectorDialog,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer import (
    UIExplorerDialog,
    UIExplorerToolbar,
)
from casare_rpa.presentation.canvas.selectors.element_selector_dialog import (
    ElementSelectorDialog,
)
from casare_rpa.presentation.canvas.selectors.selector_history import (
    SelectorHistory,
    SelectorHistoryEntry,
    get_selector_history,
)
from casare_rpa.presentation.canvas.selectors.state.selector_state import (
    ElementSelectorState,
    StateManager,
    AttributeRow,
    ValidationStatus,
    PickingMode,
)
from casare_rpa.presentation.canvas.selectors.widgets.toolbar_widget import (
    ToolbarWidget,
    ModeButton,
)
from casare_rpa.presentation.canvas.selectors.widgets.element_preview_widget import (
    ElementPreviewWidget,
)
from casare_rpa.presentation.canvas.selectors.widgets.selector_builder_widget import (
    SelectorBuilderWidget,
    AttributeRowWidget,
)
from casare_rpa.presentation.canvas.selectors.widgets.anchor_widget import (
    AnchorWidget,
)
from casare_rpa.presentation.canvas.selectors.widgets.advanced_options_widget import (
    AdvancedOptionsWidget,
)
from casare_rpa.presentation.canvas.selectors.widgets.picker_toolbar import (
    PickerToolbar,
)
from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    SelectorResult,
    SelectorStrategy,
    AnchorData,
)

__all__ = [
    # Dialogs
    "ElementSelectorDialog",
    "UIExplorerDialog",
    "UIExplorerToolbar",
    "UnifiedSelectorDialog",
    # State
    "ElementSelectorState",
    "StateManager",
    "AttributeRow",
    "ValidationStatus",
    "PickingMode",
    # History
    "SelectorHistory",
    "SelectorHistoryEntry",
    "get_selector_history",
    # Widgets
    "ToolbarWidget",
    "ModeButton",
    "ElementPreviewWidget",
    "SelectorBuilderWidget",
    "AttributeRowWidget",
    "AnchorWidget",
    "AdvancedOptionsWidget",
    "PickerToolbar",
    # Data Classes
    "SelectorResult",
    "SelectorStrategy",
    "AnchorData",
]

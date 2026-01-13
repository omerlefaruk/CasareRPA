"""
CasareRPA Selector UI Components.

This package provides UI components for element selection and management.

=============================================================================
CANONICAL DIALOG (USE THIS)
=============================================================================

UnifiedSelectorDialog:
    UiPath-inspired single-panel element picker providing:
    - Browser element picking (CSS, XPath, ARIA)
    - Desktop element picking (AutomationId, Name, Path)
    - OCR text detection
    - Image/template matching
    - Anchor configuration for relative positioning
    - Self-healing context capture

    Usage:
        from casare_rpa.presentation.canvas.selectors import UnifiedSelectorDialog

        dialog = UnifiedSelectorDialog(parent=self)
        if dialog.exec():
            result = dialog.get_result()
            selector = result.primary_selector
            healing_context = result.healing_context

=============================================================================
DEPRECATED DIALOGS (DO NOT USE FOR NEW CODE)
=============================================================================

ElementSelectorDialog: (DEPRECATED)
    Legacy compact dialog. Use UnifiedSelectorDialog instead.
    Will be removed in a future version.

SelectorDialog: (DEPRECATED)
    Legacy simple dialog. Use UnifiedSelectorDialog instead.
    Will be removed in a future version.

UIExplorerDialog:
    Advanced full-featured UI explorer for debugging.
    Still supported for advanced use cases (element tree browsing, etc).

=============================================================================
Supporting Components
=============================================================================

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

import warnings

# =============================================================================
# Deprecated Dialogs (Backward Compatibility Only)
# =============================================================================
from casare_rpa.presentation.canvas.selectors.element_selector_dialog import (
    ElementSelectorDialog as _ElementSelectorDialog)

# =============================================================================
# Advanced UI Explorer (Still Supported)
# =============================================================================
from casare_rpa.presentation.canvas.selectors.ui_explorer import (
    UIExplorerDialog,
    UIExplorerToolbar)

# =============================================================================
# Canonical Dialog (PRIMARY API)
# =============================================================================
from casare_rpa.presentation.canvas.selectors.unified_selector_dialog import (
    UnifiedSelectorDialog)


def ElementSelectorDialog(*args, **kwargs):
    """
    DEPRECATED: Use UnifiedSelectorDialog instead.

    This dialog is provided for backward compatibility only.
    """
    warnings.warn(
        "ElementSelectorDialog is deprecated. Use UnifiedSelectorDialog instead.",
        DeprecationWarning,
        stacklevel=2)
    return _ElementSelectorDialog(*args, **kwargs)


# SelectorDialog import with deprecation
try:
    from casare_rpa.presentation.canvas.selectors.selector_dialog import (
        SelectorDialog as _SelectorDialog)

    def SelectorDialog(*args, **kwargs):
        """
        DEPRECATED: Use UnifiedSelectorDialog instead.

        This dialog is provided for backward compatibility only.
        """
        warnings.warn(
            "SelectorDialog is deprecated. Use UnifiedSelectorDialog instead.",
            DeprecationWarning,
            stacklevel=2)
        return _SelectorDialog(*args, **kwargs)
except ImportError:
    SelectorDialog = None

# =============================================================================
# State Management
# =============================================================================

from casare_rpa.presentation.canvas.selectors.selector_history import (
    SelectorHistory,
    SelectorHistoryEntry,
    get_selector_history)
from casare_rpa.presentation.canvas.selectors.state.selector_state import (
    AttributeRow,
    ElementSelectorState,
    PickingMode,
    StateManager,
    ValidationStatus)

# =============================================================================
# Data Classes
# =============================================================================
from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    AnchorData,
    SelectorResult,
    SelectorStrategy)
from casare_rpa.presentation.canvas.selectors.widgets.advanced_options_widget import (
    AdvancedOptionsWidget)
from casare_rpa.presentation.canvas.selectors.widgets.anchor_widget import (
    AnchorWidget)
from casare_rpa.presentation.canvas.selectors.widgets.element_preview_widget import (
    ElementPreviewWidget)
from casare_rpa.presentation.canvas.selectors.widgets.picker_toolbar import (
    PickerToolbar)
from casare_rpa.presentation.canvas.selectors.widgets.selector_builder_widget import (
    AttributeRowWidget,
    SelectorBuilderWidget)

# =============================================================================
# Widgets
# =============================================================================
from casare_rpa.presentation.canvas.selectors.widgets.toolbar_widget import (
    ModeButton,
    ToolbarWidget)

__all__ = [
    # Canonical Dialog (USE THIS)
    "UnifiedSelectorDialog",
    # Advanced Explorer (still supported)
    "UIExplorerDialog",
    "UIExplorerToolbar",
    # Deprecated (backward compat only)
    "ElementSelectorDialog",
    "SelectorDialog",
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

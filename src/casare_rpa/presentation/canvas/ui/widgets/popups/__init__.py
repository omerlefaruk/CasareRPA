"""
V2 Popup Components Library.

Provides reusable base classes for all popup windows in the v2 UI.
All popups inherit from PopupWindowBase for consistent behavior.

Available Popup Variants:
- PopupWindowBase: Base class for all v2 popups
- AutocompleteV2: Command palette/autocomplete popup
- ContextMenuV2: Context menu popup
- DropdownV2: Single-selection dropdown with search/filter
- TooltipV2: Enhanced tooltip with rich content
- InspectorV2: Property/value inspector with search and inline editing
- ToastV2: Non-modal notification with level-based styling and auto-dismiss
- NodeSearchV2: Node search popup with keyboard navigation (Epic 3.2)

NOTE: CommandPaletteV2 removed per decision log (2025-12-30).

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.popups import (
        PopupWindowBase, show_success
    )

    # Toast notification
    show_success("Operation completed")
"""

from .autocomplete_v2 import AutocompleteItem, AutocompleteListItem, AutocompleteV2
from .context_menu_v2 import ContextMenuV2
from .dropdown_v2 import DropdownV2
from .inspector_v2 import InspectorContent, InspectorV2, PropertyRow
from .node_search_v2 import NodeSearchResult, NodeSearchV2
from .popup_items import (
    DropdownItem,
    MenuItem,
    MenuItemSpec,
    MenuItemType,
    MenuSeparator,
    TypeBadge,
)
from .popup_utils import ToastManager
from .popup_window_base import AnchorPosition, DraggableHeader, PopupWindowBase
from .toast_v2 import ToastLevel, ToastV2, show_error, show_info, show_success, show_warning
from .tooltip_v2 import TooltipV2

__all__ = [
    # Base
    "PopupWindowBase",
    "AnchorPosition",
    "DraggableHeader",
    # Popups
    "AutocompleteV2",
    "AutocompleteItem",
    "AutocompleteListItem",
    "ContextMenuV2",
    "DropdownV2",
    "TooltipV2",
    "InspectorV2",
    "ToastV2",
    "NodeSearchV2",
    # Node Search
    "NodeSearchResult",
    # Inspector internals
    "InspectorContent",
    "PropertyRow",
    # Toast
    "ToastLevel",
    "show_info",
    "show_success",
    "show_warning",
    "show_error",
    # Shared items
    "MenuItem",
    "MenuItemType",
    "MenuItemSpec",
    "MenuSeparator",
    "DropdownItem",
    "TypeBadge",
    # Utilities
    "ToastManager",
]

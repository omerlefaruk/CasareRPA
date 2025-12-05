"""
UI Explorer Models Module.

Contains data models for the UI Explorer:
- UIExplorerElement: Unified element representation for browser/desktop
- ElementSource: Enum for element source type
- SelectorModel: State management for selector attributes
- SelectorAttribute: Single attribute in selector
- AnchorModel: Anchor state management for UI Explorer
- AnchorPosition/AnchorStrategy: Anchor enums
- AnchorElementData/AnchorConfiguration: Anchor data structures
"""

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.element_model import (
    UIExplorerElement,
    ElementSource,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.models.selector_model import (
    SelectorModel,
    SelectorAttribute,
    BROWSER_ATTRIBUTES,
    DESKTOP_ATTRIBUTES,
    BROWSER_ATTRIBUTE_PRIORITY,
    DESKTOP_ATTRIBUTE_PRIORITY,
    REQUIRED_ATTRIBUTES,
    DEFAULT_INCLUDED,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.models.anchor_model import (
    AnchorPosition,
    AnchorStrategy,
    AnchorElementData,
    AnchorConfiguration,
    AnchorModel,
    STABLE_ANCHOR_TAGS,
    LANDMARK_ROLES,
    calculate_anchor_stability,
)

__all__ = [
    # Element models
    "UIExplorerElement",
    "ElementSource",
    # Selector models
    "SelectorModel",
    "SelectorAttribute",
    "BROWSER_ATTRIBUTES",
    "DESKTOP_ATTRIBUTES",
    "BROWSER_ATTRIBUTE_PRIORITY",
    "DESKTOP_ATTRIBUTE_PRIORITY",
    "REQUIRED_ATTRIBUTES",
    "DEFAULT_INCLUDED",
    # Anchor models
    "AnchorPosition",
    "AnchorStrategy",
    "AnchorElementData",
    "AnchorConfiguration",
    "AnchorModel",
    "STABLE_ANCHOR_TAGS",
    "LANDMARK_ROLES",
    "calculate_anchor_stability",
]

"""
UI Components Module.

Reusable UI components for the CasareRPA Canvas application.

This module provides a comprehensive set of UI components following
consistent design patterns:

- BaseWidget: Abstract base class for all UI components
- Panels: Dockable panels (Debug, Variables, Minimap, BottomPanel)
- Toolbars: Action toolbars (Main, Debug, Zoom)
- Dialogs: Modal dialogs (Node Properties, Workflow Settings, Preferences)
- Widgets: Reusable widgets (Variable Editor, Output Console, Search)

All components:
- Follow dark theme styling
- Use consistent signal/slot patterns
- Include comprehensive logging
- Support type hints
- Are fully testable
"""

from casare_rpa.presentation.canvas.ui.base_widget import (
    BaseWidget,
    BaseDockWidget,
    BaseDialog,
)

# Theme System
from casare_rpa.presentation.canvas.ui.theme import (
    Theme,
    ThemeMode,
    Colors,
    Spacing,
    BorderRadius,
    FontSizes,
    ButtonSizes,
    IconSizes,
    Animations,
    DARK_COLORS,
    LIGHT_COLORS,
    THEME,
    TYPE_COLORS,
    TYPE_BADGES,
    get_canvas_stylesheet,
    get_node_status_color,
    get_wire_color,
    get_status_color,
    get_type_color,
    get_type_badge,
)

# Panels
from casare_rpa.presentation.canvas.ui.panels import (
    VariablesPanel,
    MinimapPanel,
    MinimapChangeTracker,
    VARIABLE_TYPES,
    TYPE_DEFAULTS,
)
from casare_rpa.presentation.canvas.ui.debug_panel import DebugPanel

# Toolbars
from casare_rpa.presentation.canvas.ui.toolbars import (
    MainToolbar,
)

# Dialogs
from casare_rpa.presentation.canvas.ui.dialogs import (
    NodePropertiesDialog,
    WorkflowSettingsDialog,
    PreferencesDialog,
)

# Widgets
from casare_rpa.presentation.canvas.ui.widgets import (
    VariableEditorWidget,
    OutputConsoleWidget,
    SearchWidget,
)

# Animation Utilities
from casare_rpa.presentation.canvas.ui.animation_utils import (
    EASING_PRESETS,
    get_easing,
    AnimationThrottler,
    BatchUpdater,
    get_throttler,
    get_batch_updater,
)

# Animation Pool
from casare_rpa.presentation.canvas.ui.animation_pool import (
    AnimationPool,
    POOL_SIZES,
    DEFAULT_DURATIONS,
    DEFAULT_EASINGS,
    create_fade_animation,
    create_slide_animation,
    create_scale_animation,
    create_color_animation,
)

# Animation LOD (Level of Detail)
from casare_rpa.presentation.canvas.ui.animation_lod import (
    AnimationLOD,
    AnimationLevel,
    AnimationCategory,
    should_animate,
    get_duration_multiplier,
)

# Accessibility
from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings

__all__ = [
    # Base Classes
    "BaseWidget",
    "BaseDockWidget",
    "BaseDialog",
    # Theme System
    "Theme",
    "ThemeMode",
    "Colors",
    "Spacing",
    "BorderRadius",
    "FontSizes",
    "ButtonSizes",
    "IconSizes",
    "Animations",
    "DARK_COLORS",
    "LIGHT_COLORS",
    "THEME",
    "TYPE_COLORS",
    "TYPE_BADGES",
    "get_canvas_stylesheet",
    "get_node_status_color",
    "get_wire_color",
    "get_status_color",
    "get_type_color",
    "get_type_badge",
    # Panels
    "DebugPanel",
    "VariablesPanel",
    "MinimapPanel",
    "MinimapChangeTracker",
    # Toolbars
    "MainToolbar",
    # Dialogs
    "NodePropertiesDialog",
    "WorkflowSettingsDialog",
    "PreferencesDialog",
    # Widgets
    "VariableEditorWidget",
    "OutputConsoleWidget",
    "SearchWidget",
    # Constants
    "VARIABLE_TYPES",
    "TYPE_DEFAULTS",
    # Animation Utilities
    "EASING_PRESETS",
    "get_easing",
    "AnimationThrottler",
    "BatchUpdater",
    "get_throttler",
    "get_batch_updater",
    # Animation Pool
    "AnimationPool",
    "POOL_SIZES",
    "DEFAULT_DURATIONS",
    "DEFAULT_EASINGS",
    "create_fade_animation",
    "create_slide_animation",
    "create_scale_animation",
    "create_color_animation",
    # Animation LOD
    "AnimationLOD",
    "AnimationLevel",
    "AnimationCategory",
    "should_animate",
    "get_duration_multiplier",
    # Accessibility
    "AccessibilitySettings",
]

__version__ = "1.0.0"

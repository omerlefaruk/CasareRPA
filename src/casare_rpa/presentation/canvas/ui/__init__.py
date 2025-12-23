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
    BaseDialog,
    BaseDockWidget,
    BaseWidget,
)
from casare_rpa.presentation.canvas.ui.debug_panel import DebugPanel

# Dialogs
from casare_rpa.presentation.canvas.ui.dialogs import (
    NodePropertiesDialog,
    PreferencesDialog,
    WorkflowSettingsDialog,
)

# Panels
from casare_rpa.presentation.canvas.ui.panels import (
    TYPE_DEFAULTS,
    VARIABLE_TYPES,
    MinimapChangeTracker,
    MinimapPanel,
    VariablesPanel,
)

# Theme System
from casare_rpa.presentation.canvas.ui.theme import (
    CATEGORY_COLOR_MAP,
    DARK_CANVAS_COLORS,
    DARK_COLORS,
    THEME,
    TYPE_BADGES,
    TYPE_COLORS,
    Animations,
    BorderRadius,
    ButtonSizes,
    CanvasColors,
    Colors,
    FontSizes,
    IconSizes,
    Spacing,
    Theme,
    ThemeMode,
    get_canvas_stylesheet,
    get_node_status_color,
    get_status_color,
    get_type_badge,
    get_type_color,
    get_wire_color,
)

# Toolbars
from casare_rpa.presentation.canvas.ui.toolbars import (
    MainToolbar,
)

# Widgets
from casare_rpa.presentation.canvas.ui.widgets import (
    OutputConsoleWidget,
    SearchWidget,
    VariableEditorWidget,
)

__all__ = [
    # Base Classes
    "BaseWidget",
    "BaseDockWidget",
    "BaseDialog",
    # Theme System
    "Theme",
    "ThemeMode",
    "Colors",
    "CanvasColors",
    "Spacing",
    "BorderRadius",
    "FontSizes",
    "ButtonSizes",
    "IconSizes",
    "Animations",
    "DARK_COLORS",
    "DARK_CANVAS_COLORS",
    "CATEGORY_COLOR_MAP",
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
]

__version__ = "1.0.0"

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
- Chrome v2: V2 toolbar and status bar for NewMainWindow

All components:
- Follow dark theme styling
- Use consistent signal/slot patterns
- Include comprehensive logging
- Support type hints
- Are fully testable
"""

# Theme System
from casare_rpa.presentation.canvas.theme_system import (
    THEME,
    TOKENS,
    get_canvas_stylesheet,
    get_node_status_color,
    get_status_color,
    get_wire_color,
)
from casare_rpa.presentation.canvas.ui.base_widget import (
    BaseDialog,
    BaseDockWidget,
    BaseWidget,
)

# Chrome v2 (Epic 4.2)
from casare_rpa.presentation.canvas.ui.chrome import (
    StatusBarV2,
    ToolbarV2,
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
from casare_rpa.presentation.canvas.ui.widgets.popups import (
    PopupWindowBase,
)

__all__ = [
    # Base Classes
    "BaseWidget",
    "BaseDockWidget",
    "BaseDialog",
    # Theme System
    "THEME",
    "TOKENS",
    "get_canvas_stylesheet",
    "get_node_status_color",
    "get_wire_color",
    "get_status_color",
    # Panels
    "DebugPanel",
    "VariablesPanel",
    "MinimapPanel",
    "MinimapChangeTracker",
    # Toolbars
    "MainToolbar",
    # Chrome v2 (Epic 4.2)
    "ToolbarV2",
    "StatusBarV2",
    # Dialogs
    "NodePropertiesDialog",
    "WorkflowSettingsDialog",
    "PreferencesDialog",
    # Widgets
    "VariableEditorWidget",
    "OutputConsoleWidget",
    "SearchWidget",
    # Popups
    "PopupWindowBase",
    # Constants
    "VARIABLE_TYPES",
    "TYPE_DEFAULTS",
]

__version__ = "1.0.0"

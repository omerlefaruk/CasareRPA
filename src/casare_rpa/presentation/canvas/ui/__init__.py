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

__all__ = [
    # Base Classes
    "BaseWidget",
    "BaseDockWidget",
    "BaseDialog",
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

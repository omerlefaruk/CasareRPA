"""
UI Components Module.

Reusable UI components for the CasareRPA Canvas application.

This module provides a comprehensive set of UI components following
consistent design patterns:

- BaseWidget: Abstract base class for all UI components
- Panels: Dockable panels (Properties, Debug, Variables, Minimap)
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

from .base_widget import BaseWidget, BaseDockWidget, BaseDialog

# Panels
from .panels import (
    PropertiesPanel,
    DebugPanel,
    VariablesPanel,
    MinimapPanel,
    CollapsibleSection,
    MinimapChangeTracker,
    VARIABLE_TYPES,
    TYPE_DEFAULTS,
)

# Toolbars
from .toolbars import (
    MainToolbar,
    DebugToolbar,
    ZoomToolbar,
)

# Dialogs
from .dialogs import (
    NodePropertiesDialog,
    WorkflowSettingsDialog,
    PreferencesDialog,
)

# Widgets
from .widgets import (
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
    "PropertiesPanel",
    "DebugPanel",
    "VariablesPanel",
    "MinimapPanel",
    "CollapsibleSection",
    "MinimapChangeTracker",
    # Toolbars
    "MainToolbar",
    "DebugToolbar",
    "ZoomToolbar",
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

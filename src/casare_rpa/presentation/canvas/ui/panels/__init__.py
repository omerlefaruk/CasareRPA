"""
UI Panels Module.

Reusable panel components for the CasareRPA Canvas application.
All panels are designed to be dockable and follow consistent UI patterns.
"""

from .properties_panel import PropertiesPanel, CollapsibleSection
from .debug_panel import DebugPanel
from .variables_panel import VariablesPanel, VARIABLE_TYPES, TYPE_DEFAULTS
from .minimap_panel import MinimapPanel, MinimapChangeTracker

__all__ = [
    # Panels
    "PropertiesPanel",
    "DebugPanel",
    "VariablesPanel",
    "MinimapPanel",
    # Supporting Classes
    "CollapsibleSection",
    "MinimapChangeTracker",
    # Constants
    "VARIABLE_TYPES",
    "TYPE_DEFAULTS",
]

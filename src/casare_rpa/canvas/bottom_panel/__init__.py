"""
Bottom Panel Module for CasareRPA Canvas.

Provides a dockable panel with tabs for Variables, Output, Log, and Validation.
"""

from .bottom_panel_dock import BottomPanelDock
from .variables_tab import VariablesTab
from .output_tab import OutputTab
from .log_tab import LogTab
from .validation_tab import ValidationTab
from .variable_editor_dialog import VariableEditorDialog

__all__ = [
    "BottomPanelDock",
    "VariablesTab",
    "OutputTab",
    "LogTab",
    "ValidationTab",
    "VariableEditorDialog",
]

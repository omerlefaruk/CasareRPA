"""
CasareRPA - Canvas Dialogs

This module provides dialog windows for the Canvas application.
"""

from .new_project_dialog import NewProjectDialog
from .new_scenario_dialog import NewScenarioDialog
from .variable_editor_dialog import VariableEditorDialog
from .credential_editor_dialog import CredentialEditorDialog
from .trigger_type_selector import TriggerTypeSelectorDialog
from .trigger_config_dialog import TriggerConfigDialog

__all__ = [
    "NewProjectDialog",
    "NewScenarioDialog",
    "VariableEditorDialog",
    "CredentialEditorDialog",
    "TriggerTypeSelectorDialog",
    "TriggerConfigDialog",
]

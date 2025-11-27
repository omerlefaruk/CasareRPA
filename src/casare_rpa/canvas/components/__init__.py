"""
Canvas components package.

This package contains modular components extracted from the monolithic
CasareRPAApp class to improve maintainability and testability.
"""

from .base_component import BaseComponent
from .workflow_lifecycle_component import WorkflowLifecycleComponent
from .execution_component import ExecutionComponent
from .node_registry_component import NodeRegistryComponent
from .selector_component import SelectorComponent
from .trigger_component import TriggerComponent
from .project_component import ProjectComponent
from .preferences_component import PreferencesComponent
from .dragdrop_component import DragDropComponent
from .autosave_component import AutosaveComponent

__all__ = [
    "BaseComponent",
    "WorkflowLifecycleComponent",
    "ExecutionComponent",
    "NodeRegistryComponent",
    "SelectorComponent",
    "TriggerComponent",
    "ProjectComponent",
    "PreferencesComponent",
    "DragDropComponent",
    "AutosaveComponent",
]

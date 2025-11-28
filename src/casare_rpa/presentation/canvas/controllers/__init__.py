"""
Controllers package for Canvas UI.

This package contains all controllers that manage UI interactions and coordinate
between different components of the Canvas application. Controllers follow the
MVC pattern and are responsible for handling user input, updating models, and
coordinating UI updates.

Architecture:
    - BaseController: Abstract base class for all controllers
    - WorkflowController: Workflow lifecycle (new, open, save, close)
    - ExecutionController: Workflow execution (run, pause, stop, debug)
    - NodeController: Node operations (select, disable, navigate)
    - ConnectionController: Connection management (create, delete, validate)
    - PanelController: Panel visibility (properties, debug, minimap, variables)
    - MenuController: Menu/action management (shortcuts, recent files)
    - EventBusController: Centralized event routing and coordination
    - ViewportController: Canvas viewport, minimap, zoom, and frame management
    - SchedulingController: Workflow scheduling and schedule management
    - TriggerController: Trigger creation, editing, deletion, and management
    - UIStateController: UI state persistence (window geometry, panels, recent files)
    - SelectorController: Element selector/picker (browser, desktop)
    - ProjectController: Project and scenario management
    - PreferencesController: Settings and preferences management
    - AutosaveController: Automatic workflow saving

Usage:
    from casare_rpa.presentation.canvas.controllers import (
        WorkflowController,
        ExecutionController,
        NodeController,
        ViewportController,
        SchedulingController,
        TriggerController,
        UIStateController,
        SelectorController,
        ProjectController,
        PreferencesController,
        AutosaveController,
    )

    workflow_controller = WorkflowController(main_window)
    workflow_controller.initialize()
"""

from .base_controller import BaseController
from .workflow_controller import WorkflowController
from .execution_controller import ExecutionController
from .node_controller import NodeController
from .connection_controller import ConnectionController
from .panel_controller import PanelController
from .menu_controller import MenuController
from .event_bus_controller import EventBusController, EventTypes, Event
from .viewport_controller import ViewportController
from .scheduling_controller import SchedulingController
from .trigger_controller import TriggerController
from .ui_state_controller import UIStateController
from .selector_controller import SelectorController
from .project_controller import ProjectController
from .preferences_controller import PreferencesController
from .autosave_controller import AutosaveController

__all__ = [
    # Base
    "BaseController",
    # Controllers
    "WorkflowController",
    "ExecutionController",
    "NodeController",
    "ConnectionController",
    "PanelController",
    "MenuController",
    "EventBusController",
    "ViewportController",
    "SchedulingController",
    "TriggerController",
    "UIStateController",
    "SelectorController",
    "ProjectController",
    "PreferencesController",
    "AutosaveController",
    # Event utilities
    "EventTypes",
    "Event",
]

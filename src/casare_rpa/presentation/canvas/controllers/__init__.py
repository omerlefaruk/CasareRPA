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
    - (Triggers and scheduling are now visual nodes - see visual_nodes/triggers/)
    - UIStateController: UI state persistence (window geometry, panels, recent files)
    - SelectorController: Element selector/picker (browser, desktop)
    - PreferencesController: Settings and preferences management
    - AutosaveController: Automatic workflow saving

Usage:
    from casare_rpa.presentation.canvas.controllers import (
        WorkflowController,
        ExecutionController,
        NodeController,
        ViewportController,
        UIStateController,
        SelectorController,
        PreferencesController,
        AutosaveController,
    )

    workflow_controller = WorkflowController(main_window)
    workflow_controller.initialize()
"""

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController
from casare_rpa.presentation.canvas.controllers.workflow_controller import (
    WorkflowController,
)
from casare_rpa.presentation.canvas.controllers.execution_controller import (
    ExecutionController,
)
from casare_rpa.presentation.canvas.controllers.node_controller import NodeController
from casare_rpa.presentation.canvas.controllers.connection_controller import (
    ConnectionController,
)
from casare_rpa.presentation.canvas.controllers.panel_controller import PanelController
from casare_rpa.presentation.canvas.controllers.menu_controller import MenuController
from casare_rpa.presentation.canvas.controllers.event_bus_controller import (
    EventBusController,
    EventTypes,
    Event,
)
from casare_rpa.presentation.canvas.controllers.viewport_controller import (
    ViewportController,
)

# TriggerController and SchedulingController removed - use trigger nodes instead
from casare_rpa.presentation.canvas.controllers.ui_state_controller import (
    UIStateController,
)
from casare_rpa.presentation.canvas.controllers.selector_controller import (
    SelectorController,
)
from casare_rpa.presentation.canvas.controllers.preferences_controller import (
    PreferencesController,
)
from casare_rpa.presentation.canvas.controllers.autosave_controller import (
    AutosaveController,
)
from casare_rpa.presentation.canvas.controllers.project_autosave_controller import (
    ProjectAutosaveController,
)
from casare_rpa.presentation.canvas.controllers.project_controller import (
    ProjectController,
)
from casare_rpa.presentation.canvas.controllers.robot_controller import RobotController

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
    "UIStateController",
    "SelectorController",
    "PreferencesController",
    "AutosaveController",
    "ProjectAutosaveController",
    "ProjectController",
    "RobotController",
    # Event utilities
    "EventTypes",
    "Event",
]

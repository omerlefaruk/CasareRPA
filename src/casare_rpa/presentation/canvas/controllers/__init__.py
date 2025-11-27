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

Usage:
    from casare_rpa.presentation.canvas.controllers import (
        WorkflowController,
        ExecutionController,
        NodeController,
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
    # Event utilities
    "EventTypes",
    "Event",
]

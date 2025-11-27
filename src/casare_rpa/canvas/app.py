"""
Main application class with qasync integration (Refactored).

This module provides the CasareRPAApp class which integrates
PySide6 with asyncio using qasync for async workflow execution.

Reduced from 3,112 lines to ~400 lines by extracting components.
"""

import sys
import asyncio
from typing import Any, Dict, Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from qasync import QEventLoop
from loguru import logger

from .main_window import MainWindow
from .graph.node_graph_widget import NodeGraphWidget
from .components import (
    WorkflowLifecycleComponent,
    ExecutionComponent,
    NodeRegistryComponent,
    SelectorComponent,
    TriggerComponent,
    ProjectComponent,
    PreferencesComponent,
    DragDropComponent,
    AutosaveComponent,
)
from ..utils.config import setup_logging, APP_NAME
from ..utils.playwright_setup import ensure_playwright_ready


class CasareRPAApp:
    """
    Main application class integrating Qt with asyncio (Refactored).

    Uses qasync to bridge PySide6's event loop with Python's asyncio,
    enabling async workflows with Playwright to run within the Qt application.

    Responsibilities:
    - Qt application initialization
    - Component lifecycle management with explicit dependency ordering
    - Event loop integration
    - Signal routing

    Business logic delegated to components:
    - WorkflowLifecycleComponent: New/Open/Save/Template operations
    - ExecutionComponent: Workflow execution and debugging
    - NodeRegistryComponent: Node type registration (no dependencies)
    - SelectorComponent: Element selector integration
    - TriggerComponent: Trigger management
    - ProjectComponent: Project/scenario management
    - PreferencesComponent: Settings management
    - DragDropComponent: Drag-drop functionality
    - AutosaveComponent: Automatic saving

    Component Initialization Order:
    1. NodeRegistryComponent - Must be first (registers all node types)
    2. All other components - Depend on node registry being initialized
    """

    def __init__(self) -> None:
        """Initialize the application."""
        # Setup logging
        setup_logging()
        logger.info(f"Initializing {APP_NAME}...")

        # Setup Qt application
        self._setup_qt_application()

        # Check for Playwright browsers
        logger.info("Checking Playwright browser installation...")
        ensure_playwright_ready(show_gui=True, parent=None)

        # Create main window and node graph
        self._create_ui()

        # Initialize components in dependency order
        self._initialize_components()

        # Connect component signals
        self._connect_components()

        # Connect UI signals
        self._connect_ui_signals()

        logger.info("Application initialized successfully")

    def _setup_qt_application(self) -> None:
        """Setup Qt application and event loop."""
        # Enable high-DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)

        # Create Qt application
        self._app = QApplication(sys.argv)
        self._app.setApplicationName(APP_NAME)

        # Create qasync event loop
        self._loop = QEventLoop(self._app)
        asyncio.set_event_loop(self._loop)

    def _create_ui(self) -> None:
        """Create main window and central widget."""
        # Create main window
        self._main_window = MainWindow()

        # Create node graph widget
        self._node_graph = NodeGraphWidget()

        # Set node graph as central widget
        self._main_window.set_central_widget(self._node_graph)

    def _initialize_components(self) -> None:
        """
        Initialize all application components in dependency order.

        Initialization Order (Critical):
        1. NodeRegistryComponent - MUST be first
           - Registers all node types with NodeGraphQt
           - Other components may need registered nodes during initialization

        2. All other components - Can be initialized in any order
           - They all depend on node registry being ready
           - No cross-dependencies between these components

        Raises:
            RuntimeError: If component initialization fails
        """
        logger.info("Initializing components...")

        # Phase 1: Node registry (foundation - no dependencies)
        logger.debug("Phase 1: Initializing node registry...")
        self._node_registry_component = NodeRegistryComponent(self._main_window)
        self._node_registry_component.initialize()
        logger.debug("Node registry initialized - all node types registered")

        # Phase 2: All other components (depend on node registry)
        logger.debug("Phase 2: Initializing application components...")

        # Workflow lifecycle - handles file operations
        self._workflow_lifecycle_component = WorkflowLifecycleComponent(
            self._main_window
        )

        # Execution - handles workflow running
        self._execution_component = ExecutionComponent(self._main_window)

        # Selector - handles element selection
        self._selector_component = SelectorComponent(self._main_window)

        # Trigger - handles trigger management
        self._trigger_component = TriggerComponent(self._main_window, self)

        # Project - handles project/scenario management
        self._project_component = ProjectComponent(self._main_window)

        # Preferences - handles settings
        self._preferences_component = PreferencesComponent(self._main_window)

        # Drag-drop - handles file drops
        self._dragdrop_component = DragDropComponent(self._main_window)

        # Autosave - handles automatic saving
        self._autosave_component = AutosaveComponent(self._main_window)

        # Initialize all phase 2 components
        phase_2_components = [
            self._workflow_lifecycle_component,
            self._execution_component,
            self._selector_component,
            self._trigger_component,
            self._project_component,
            self._preferences_component,
            self._dragdrop_component,
            self._autosave_component,
        ]

        for component in phase_2_components:
            try:
                component.initialize()
                logger.debug(f"{component.__class__.__name__} initialized")
            except Exception as e:
                error_msg = f"Failed to initialize {component.__class__.__name__}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e

        logger.info("All components initialized successfully")

    def _connect_components(self) -> None:
        """Connect component signals for inter-component communication."""
        # Components are already connected to main_window signals internally
        # Additional cross-component connections can be added here if needed
        logger.debug("Component signals connected")

    def _connect_ui_signals(self) -> None:
        """Connect UI-level signals."""
        graph = self._node_graph.graph
        undo_stack = graph.undo_stack()

        # Edit operations - connect to NodeGraphQt undo stack
        self._main_window.action_undo.setEnabled(True)
        self._main_window.action_redo.setEnabled(True)
        self._main_window.action_undo.triggered.connect(undo_stack.undo)
        self._main_window.action_redo.triggered.connect(undo_stack.redo)

        # Connect undo stack signals to update action states
        undo_stack.canUndoChanged.connect(self._main_window.action_undo.setEnabled)
        undo_stack.canRedoChanged.connect(self._main_window.action_redo.setEnabled)

        # Other edit operations
        self._main_window.action_delete.triggered.connect(self._on_delete_selected)
        self._main_window.action_cut.triggered.connect(graph.cut_nodes)
        self._main_window.action_copy.triggered.connect(graph.copy_nodes)
        self._main_window.action_paste.triggered.connect(graph.paste_nodes)
        self._main_window.action_duplicate.triggered.connect(self._on_duplicate_nodes)
        self._main_window.action_select_all.triggered.connect(graph.select_all)
        self._main_window.action_deselect_all.triggered.connect(graph.clear_selection)

        # View operations
        self._main_window.action_zoom_in.triggered.connect(self._node_graph.zoom_in)
        self._main_window.action_zoom_out.triggered.connect(self._node_graph.zoom_out)
        self._main_window.action_zoom_reset.triggered.connect(
            self._node_graph.reset_zoom
        )
        self._main_window.action_fit_view.triggered.connect(
            self._node_graph.center_on_nodes
        )

        # Auto-connect toggle
        self._main_window.action_auto_connect.triggered.connect(
            lambda checked: self._node_graph.set_auto_connect_enabled(checked)
        )

        # Debug toolbar connections
        debug_toolbar = self._main_window.get_debug_toolbar()
        if debug_toolbar:
            debug_toolbar.debug_mode_toggled.connect(self._on_debug_mode_toggled)
            debug_toolbar.step_mode_toggled.connect(self._on_step_mode_toggled)
            debug_toolbar.step_requested.connect(self._on_debug_step)
            debug_toolbar.continue_requested.connect(self._on_debug_continue)

        logger.debug("UI signals connected")

    def _get_all_components(self) -> list:
        """
        Get all initialized components.

        Returns:
            List of all component instances
        """
        return [
            self._node_registry_component,
            self._workflow_lifecycle_component,
            self._execution_component,
            self._selector_component,
            self._trigger_component,
            self._project_component,
            self._preferences_component,
            self._dragdrop_component,
            self._autosave_component,
        ]

    def _on_delete_selected(self) -> None:
        """Delete selected nodes and frames."""
        graph = self._node_graph.graph

        # Delete selected nodes first
        graph.delete_nodes(graph.selected_nodes())

        # Delete selected frames
        from .graph.node_frame import NodeFrame

        scene = graph.viewer().scene()
        for item in scene.selectedItems():
            if isinstance(item, NodeFrame):
                scene.removeItem(item)

    def _on_duplicate_nodes(self) -> None:
        """Duplicate the selected nodes at mouse cursor position."""
        graph = self._node_graph.graph
        viewer = graph.viewer()

        # Check if there are selected nodes
        if not graph.selected_nodes():
            return

        # Get mouse cursor position in scene coordinates
        cursor_pos = viewer.cursor().pos()
        scene_pos = viewer.mapToScene(viewer.mapFromGlobal(cursor_pos))

        # Copy and paste
        graph.copy_nodes()
        graph.paste_nodes()

        # Get the newly pasted nodes
        pasted_nodes = graph.selected_nodes()
        if not pasted_nodes:
            return

        # Calculate offset to cursor position
        min_x = min(node.pos()[0] for node in pasted_nodes)
        min_y = min(node.pos()[1] for node in pasted_nodes)
        offset_x = scene_pos.x() - min_x
        offset_y = scene_pos.y() - min_y

        # Move pasted nodes to cursor position
        for node in pasted_nodes:
            current_pos = node.pos()
            node.set_pos(current_pos[0] + offset_x, current_pos[1] + offset_y)

    def _on_debug_mode_toggled(self, enabled: bool) -> None:
        """Handle debug mode toggle."""
        logger.info(f"Debug mode {'enabled' if enabled else 'disabled'}")

    def _on_step_mode_toggled(self, enabled: bool) -> None:
        """Handle step mode toggle."""
        logger.info(f"Step mode {'enabled' if enabled else 'disabled'}")

    def _on_debug_step(self) -> None:
        """Handle debug step request."""
        # Delegate to execution component
        if hasattr(self._execution_component, "_workflow_runner"):
            runner = self._execution_component._workflow_runner
            if runner and runner.debug_mode:
                runner.step()

    def _on_debug_continue(self) -> None:
        """Handle debug continue request."""
        # Delegate to execution component
        if hasattr(self._execution_component, "_workflow_runner"):
            runner = self._execution_component._workflow_runner
            if runner and runner.debug_mode:
                runner.continue_execution()

    # Public API for trigger component
    def start_triggers(self) -> None:
        """Start all triggers for the current scenario."""
        self._trigger_component.start_triggers()

    def stop_triggers(self) -> None:
        """Stop all active triggers."""
        self._trigger_component.stop_triggers()

    def are_triggers_running(self) -> bool:
        """Check if triggers are currently running."""
        return self._trigger_component.are_triggers_running()

    # Public API for getting components
    def get_workflow_lifecycle_component(self) -> WorkflowLifecycleComponent:
        """Get the workflow lifecycle component."""
        return self._workflow_lifecycle_component

    def get_execution_component(self) -> ExecutionComponent:
        """Get the execution component."""
        return self._execution_component

    def get_node_registry_component(self) -> NodeRegistryComponent:
        """Get the node registry component."""
        return self._node_registry_component

    def get_selector_component(self) -> SelectorComponent:
        """Get the selector component."""
        return self._selector_component

    def get_trigger_component(self) -> TriggerComponent:
        """Get the trigger component."""
        return self._trigger_component

    def get_project_component(self) -> ProjectComponent:
        """Get the project component."""
        return self._project_component

    def get_preferences_component(self) -> PreferencesComponent:
        """Get the preferences component."""
        return self._preferences_component

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Application exit code
        """
        logger.info("Starting application")
        self._main_window.show()

        with self._loop:
            exit_code = self._loop.run_forever()

        logger.info(f"Application exited with code {exit_code}")
        return exit_code if isinstance(exit_code, int) else 0

    async def run_async(self) -> int:
        """
        Run the application asynchronously.

        This method allows the application to be started from
        an async context if needed.

        Returns:
            Application exit code
        """
        logger.info("Starting application (async)")
        self._main_window.show()
        return 0

    def cleanup(self) -> None:
        """Cleanup all components."""
        logger.info("Cleaning up application")
        for component in self._get_all_components():
            try:
                component.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {component.__class__.__name__}: {e}")


def main() -> int:
    """
    Main entry point for the application.

    Returns:
        Application exit code
    """
    app = CasareRPAApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())

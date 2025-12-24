"""
Main application class with qasync integration (Refactored).

This module provides the CasareRPAApp class which integrates
PySide6 with asyncio using qasync for async workflow execution.

Reduced from 3,112 lines to ~400 lines by extracting components.
"""

from __future__ import annotations  # PEP 563: Deferred evaluation of annotations

import asyncio
import sys

# Apply QFont fix FIRST - before any Qt widget imports that might create fonts
from casare_rpa.presentation.canvas.graph.patches import apply_early_patches

apply_early_patches()

from loguru import logger
from PySide6.QtCore import Qt, QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

# =============================================================================
# QT MESSAGE HANDLER - Filter unsupported CSS warnings
# =============================================================================

# Store the original handler to chain calls
_original_qt_handler = None

# Patterns to suppress (known harmless Qt warnings)
_SUPPRESSED_PATTERNS = (
    "Unknown property box-shadow",
    "Unknown property text-shadow",
    # Windows DPI scaling can cause minor geometry adjustments - this is normal
    "QWindowsWindow::setGeometry",
    # Qt internal warning when font size is invalid (even if we patched Python side)
    "QFont::setPointSize: Point size <= 0",
)


def _qt_message_handler(msg_type: QtMsgType, context, message: str) -> None:
    """
    Custom Qt message handler to suppress known harmless warnings.

    Suppresses:
    - "Unknown property box-shadow" - Qt CSS doesn't support box-shadow
    - "Unknown property text-shadow" - Qt CSS doesn't support text-shadow
    - "QWindowsWindow::setGeometry" - Windows DPI scaling causes minor geometry
      adjustments when restoring window size/position. The window still functions
      correctly, the warning is purely informational.
    - "QFont::setPointSize" - Internal Qt warning when font size is <= 0.
    """
    # Suppress known harmless warnings
    if any(pattern in message for pattern in _SUPPRESSED_PATTERNS):
        return  # Silently ignore

    # For all other messages, log appropriately
    if msg_type == QtMsgType.QtDebugMsg:
        logger.debug(f"[Qt] {message}")
    elif msg_type == QtMsgType.QtInfoMsg:
        logger.info(f"[Qt] {message}")
    elif msg_type == QtMsgType.QtWarningMsg:
        logger.warning(f"[Qt] {message}")
    elif msg_type == QtMsgType.QtCriticalMsg:
        logger.error(f"[Qt] {message}")
    elif msg_type == QtMsgType.QtFatalMsg:
        logger.critical(f"[Qt] {message}")


from casare_rpa.config import APP_NAME, setup_logging
from casare_rpa.nodes.file.file_security import PathSecurityError
from casare_rpa.presentation.canvas.main_window import MainWindow
from casare_rpa.presentation.canvas.serialization import write_workflow_file
from casare_rpa.presentation.canvas.telemetry import (
    IMPORT_START,
    StartupTimer,
    log_canvas_event,
)

# Lazy import for litellm cleanup to avoid import if litellm not used
_litellm_cleanup_registered = False

# C3 PERFORMANCE: NodeGraphWidget imported lazily in _create_ui()
# C3 PERFORMANCE: Controllers imported lazily in _initialize_components()
# This defers ~20-40ms of import time until after module load

# TYPE_CHECKING imports for type hints (not imported at runtime)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.controllers import (
        AutosaveController,
        ExecutionController,
        NodeController,
        PreferencesController,
        SelectorController,
        WorkflowController,
    )

# NOTE: ensure_playwright_ready is imported lazily in ensure_playwright_on_demand()
# to defer the import cost until a browser node is actually used

# =============================================================================
# MODULE-LEVEL APP INSTANCE TRACKING
# =============================================================================
# Used by browser nodes to access the app for deferred Playwright check

_app_instance: CasareRPAApp | None = None


def get_app_instance() -> CasareRPAApp | None:
    """
    Get the running app instance.

    Returns:
        CasareRPAApp instance or None if not initialized
    """
    return _app_instance


def ensure_playwright_on_demand() -> None:
    """
    Module-level function to check Playwright installation on demand.

    PERFORMANCE: Deferred from startup to first browser node use.
    Call this from browser nodes before execution to ensure Playwright is ready.

    Example:
        from casare_rpa.presentation.canvas.app import ensure_playwright_on_demand
        ensure_playwright_on_demand()  # Called before browser operations
    """
    app = get_app_instance()
    if app is not None:
        app.ensure_playwright_on_demand()
    else:
        # Fallback: direct check if app not initialized (e.g., Robot runner)
        try:
            from casare_rpa.utils.playwright_setup import ensure_playwright_ready

            ensure_playwright_ready(show_gui=False, parent=None)
        except Exception as e:
            logger.warning(f"Playwright check failed (no app context): {e}")


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

    Business logic delegated to controllers:
    - WorkflowController: New/Open/Save/Template operations
    - ExecutionController: Workflow execution and debugging
    - NodeController: Node type registration (no dependencies)
    - SelectorController: Element selector integration
    - PreferencesController: Settings management
    - AutosaveController: Automatic saving

    Note: Triggers are now visual nodes on the canvas (not a background system).

    Component Initialization Order:
    1. NodeRegistryComponent - Must be first (registers all node types)
    2. All other components - Depend on node registry being initialized
    """

    def __init__(self) -> None:
        """Initialize the application."""
        global _app_instance
        _app_instance = self

        # Setup logging
        setup_logging()
        self._startup_timer = StartupTimer(start_time=IMPORT_START)
        self._startup_timer.mark(
            "import_complete",
            {
                "definition": "module import start -> app init start",
            },
        )

        # Setup Qt application
        self._setup_qt_application()
        self._startup_timer.mark("qt_app_created")

        # PERFORMANCE: Defer Playwright check to first browser node use
        # This is now handled lazily by ensure_playwright_on_demand()
        self._playwright_checked = False

        # Create main window and node graph
        self._create_ui()

        # STARTUP OPTIMIZATION: Show window BEFORE heavy initialization
        # This gives immediate visual feedback while nodes load in background
        self._main_window.setWindowTitle(f"{APP_NAME} - Loading...")
        self._main_window.show()

        # Process pending events to ensure window is displayed
        self._app.processEvents()
        self._startup_timer.mark("window_visible")

        # Initialize components in dependency order (node registration is deferred)
        self._initialize_components()

        # Connect component signals
        self._connect_components()

        # Connect UI signals
        self._connect_ui_signals()

        # Restore window title after initialization
        self._main_window.setWindowTitle(APP_NAME)
        self._startup_timer.mark(
            "interactive_ready",
            {
                "definition": (
                    "window visible + graph widget created + essential nodes "
                    "registered + critical controllers initialized + UI signals wired"
                )
            },
        )

    def _setup_qt_application(self) -> None:
        """Setup Qt application and event loop."""
        # Install custom message handler FIRST to suppress CSS warnings
        qInstallMessageHandler(_qt_message_handler)

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

        # Connect aboutToQuit to ensure async cleanup before event loop terminates
        self._app.aboutToQuit.connect(self._on_about_to_quit)

    def _create_ui(self) -> None:
        """Create main window and central widget."""
        # C3 PERFORMANCE: Lazy import NodeGraphWidget
        from casare_rpa.presentation.canvas.graph.node_graph_widget import (
            NodeGraphWidget,
        )

        # Create main window
        self._main_window = MainWindow()
        self._startup_timer.mark("main_window_created")

        # Create node graph widget
        self._node_graph = NodeGraphWidget()
        self._startup_timer.mark("graph_widget_created")

        # Set node graph as central widget
        self._main_window.set_central_widget(self._node_graph)

        # Create workflow serializer and deserializer
        from .execution.canvas_workflow_runner import CanvasWorkflowRunner
        from .serialization.workflow_deserializer import WorkflowDeserializer
        from .serialization.workflow_serializer import WorkflowSerializer

        self._serializer = WorkflowSerializer(
            self._node_graph.graph,  # NodeGraphQt NodeGraph instance
            self._main_window,
        )

        self._deserializer = WorkflowDeserializer(
            self._node_graph.graph,
            self._main_window,
        )

        # Set as data provider for validation
        self._main_window.set_workflow_data_provider(self._serializer.serialize)

        # Create workflow runner
        from casare_rpa.domain.events import get_event_bus

        self._workflow_runner = CanvasWorkflowRunner(
            self._serializer, get_event_bus(), self._main_window
        )

        logger.debug("Workflow serializer and runner initialized")
        self._startup_timer.mark("graph_stack_ready")

    def _initialize_components(self) -> None:
        """
        Initialize all application controllers in dependency order.

        PERFORMANCE OPTIMIZATION (Phase A/B/C):
        - Phase 1 (sync): Essential nodes only for fast startup
        - Phase 2 (staggered): Controllers initialized with event loop yields
        - Phase 3 (deferred): Full registration after window shows
        - Icon preloading moved to background thread

        C3: Controllers imported lazily here instead of module level (~20-40ms)
        A3: Staggered initialization yields to event loop between batches

        Initialization Order (Critical):
        1. NodeController - MUST be first (registers all node types)
        2. Core controllers (Workflow, Execution) - UI functionality
        3. Support controllers (Selector, Preferences, Autosave) - Less critical

        Raises:
            RuntimeError: If controller initialization fails
        """
        from PySide6.QtCore import QTimer

        # C3 PERFORMANCE: Lazy import controllers (deferred from module level)
        from casare_rpa.presentation.canvas.controllers import (
            AutosaveController,
            ExecutionController,
            NodeController,
            PreferencesController,
            SelectorController,
            WorkflowController,
        )

        # Phase 1: Node registry (essential nodes only for fast startup)
        self._node_controller = NodeController(self._main_window)
        self._node_controller.initialize()
        logger.debug("Essential nodes registered")
        self._startup_timer.mark(
            "node_registration_essential_complete",
            {"phase": "essential"},
        )

        # PERFORMANCE: Defer icon preloading to background
        QTimer.singleShot(500, self._preload_icons_background)

        # Phase 2: Create all controllers (fast - just object creation)
        logger.debug("Phase 2: Creating application controllers...")

        self._workflow_controller = WorkflowController(self._main_window)
        self._execution_controller = ExecutionController(self._main_window)
        self._selector_controller = SelectorController(self._main_window)
        self._preferences_controller = PreferencesController(self._main_window)
        self._autosave_controller = AutosaveController(self._main_window)

        # A3 PERFORMANCE: Initialize controllers in batches with event loop yields
        # Batch 1: Critical controllers (needed for basic UI)
        critical_controllers = [
            self._workflow_controller,
            self._execution_controller,
        ]

        for controller in critical_controllers:
            try:
                controller.initialize()
                logger.debug(f"{controller.__class__.__name__} initialized")
            except Exception as e:
                error_msg = f"Failed to initialize {controller.__class__.__name__}: {e}"
                logger.error(error_msg)
                raise RuntimeError(error_msg) from e
        self._startup_timer.mark("controllers_critical_initialized")

        # Configure execution controller immediately (needed for run button)
        self._execution_controller.set_workflow_runner(self._workflow_runner)

        # Inject critical controllers to make UI functional
        self._main_window.set_controllers(
            workflow_controller=self._workflow_controller,
            execution_controller=self._execution_controller,
            node_controller=self._node_controller,
            selector_controller=self._selector_controller,
        )

        # A3: Defer support controller initialization to next event loop tick
        # This allows the UI to be responsive sooner
        def _init_support_controllers():
            support_controllers = [
                self._selector_controller,
                self._preferences_controller,
                self._autosave_controller,
            ]
            for controller in support_controllers:
                try:
                    controller.initialize()
                    logger.debug(f"{controller.__class__.__name__} initialized (deferred)")
                except Exception as e:
                    logger.error(f"Failed to initialize {controller.__class__.__name__}: {e}")
            self._startup_timer.mark("controllers_support_initialized")

        QTimer.singleShot(0, _init_support_controllers)

        # PERFORMANCE: Defer full node registration until after window is responsive
        QTimer.singleShot(100, self._complete_deferred_initialization)

    def _preload_icons_background(self) -> None:
        """
        Preload node icons in background (non-blocking).

        PERFORMANCE: Moved from synchronous startup to deferred background task.
        Icons are loaded lazily anyway, this just warms the cache.
        """
        try:
            from casare_rpa.presentation.canvas.graph.icon_atlas import (
                get_icon_atlas,
                preload_node_icons,
            )

            get_icon_atlas().initialize()
            preload_node_icons()
            stats = get_icon_atlas().get_stats()
            logger.debug("Icon atlas preloaded in background")
            self._startup_timer.mark(
                "icon_atlas_preload_complete",
                {"icons_loaded": stats.get("icons_loaded")},
            )
        except Exception as e:
            logger.warning(f"Failed to preload icon atlas: {e}")

    def _complete_deferred_initialization(self) -> None:
        """
        Complete deferred initialization after window is shown.

        PERFORMANCE: This runs after the main window is visible and responsive,
        completing the full node registration that was deferred at startup.
        """
        try:
            # Complete full node registration if deferred
            if hasattr(self._node_controller, "complete_node_registration"):
                self._node_controller.complete_node_registration()
                logger.debug("Deferred node registration completed")
        except Exception as e:
            logger.error(f"Failed to complete deferred initialization: {e}")

    def ensure_playwright_on_demand(self) -> None:
        """
        Check Playwright installation on first browser node use.

        PERFORMANCE: Deferred from startup to first actual use.
        Called by browser nodes before execution.
        """
        if self._playwright_checked:
            return

        self._playwright_checked = True

        try:
            from casare_rpa.utils.playwright_setup import ensure_playwright_ready

            ensure_playwright_ready(show_gui=True, parent=self._main_window)
            logger.debug("Playwright check completed on demand")
        except Exception as e:
            logger.warning(f"Playwright check failed: {e}")

    def _connect_components(self) -> None:
        """Connect controller signals for inter-controller communication."""
        # Controllers are already connected to main_window signals and EventBus internally
        # Additional cross-component connections can be added here if needed

        # Connect workflow save/load signals to actual file operations
        self._workflow_controller.workflow_saved.connect(self._on_workflow_save)
        self._workflow_controller.workflow_loaded.connect(self._on_workflow_load)
        self._workflow_controller.workflow_created.connect(self._on_workflow_new)

        # Connect main_window workflow_open signal (emitted from recent files, etc.)
        self._main_window.workflow_open.connect(self._workflow_controller.open_workflow_path)

        # Connect project controller scenario_opened signal to load workflow
        project_controller = self._main_window.get_project_controller()
        if project_controller:
            project_controller.scenario_opened.connect(self._on_scenario_opened)

        logger.debug("Component signals connected")

    def _connect_ui_signals(self) -> None:
        """Connect UI-level signals."""
        graph = self._node_graph.graph
        undo_stack = graph.undo_stack()

        # Edit operations - connect to NodeGraphQt undo stack
        self._main_window.action_undo.setEnabled(True)
        self._main_window.action_redo.setEnabled(True)

        def _undo() -> None:
            log_canvas_event(
                "undo_triggered",
                index=undo_stack.index(),
                clean=undo_stack.isClean(),
            )
            undo_stack.undo()
            log_canvas_event(
                "undo_completed",
                index=undo_stack.index(),
                clean=undo_stack.isClean(),
            )

        def _redo() -> None:
            log_canvas_event(
                "redo_triggered",
                index=undo_stack.index(),
                clean=undo_stack.isClean(),
            )
            undo_stack.redo()
            log_canvas_event(
                "redo_completed",
                index=undo_stack.index(),
                clean=undo_stack.isClean(),
            )

        self._main_window.action_undo.triggered.connect(_undo)
        self._main_window.action_redo.triggered.connect(_redo)

        # Connect undo stack signals to update action states
        undo_stack.canUndoChanged.connect(self._main_window.action_undo.setEnabled)
        undo_stack.canRedoChanged.connect(self._main_window.action_redo.setEnabled)

        # Track modification state using cleanChanged signal
        # cleanChanged(False) = stack is dirty (has unsaved changes)
        # cleanChanged(True) = stack is clean (at saved state)
        undo_stack.cleanChanged.connect(
            lambda is_clean: self._main_window.set_modified(not is_clean)
        )

        # Store reference to mark clean after save
        self._undo_stack = undo_stack

        # Other edit operations
        self._main_window.action_delete.triggered.connect(self._on_delete_selected)
        self._main_window.action_cut.triggered.connect(graph.cut_nodes)
        self._main_window.action_copy.triggered.connect(graph.copy_nodes)
        self._main_window.action_paste.triggered.connect(self._on_paste_nodes)
        self._main_window.action_duplicate.triggered.connect(self._on_duplicate_nodes)
        self._main_window.action_select_all.triggered.connect(graph.select_all)

        logger.debug("UI signals connected")

    def _get_all_controllers(self) -> list:
        """
        Get all initialized controllers.

        Returns:
            List of all controller instances
        """
        return [
            self._node_controller,
            self._workflow_controller,
            self._execution_controller,
            self._selector_controller,
            self._preferences_controller,
            self._autosave_controller,
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

    def _on_paste_nodes(self) -> None:
        """Paste nodes and regenerate IDs to avoid duplicates."""
        import json

        from PySide6.QtWidgets import QApplication

        graph = self._node_graph.graph

        # Validate clipboard data before pasting
        clipboard = QApplication.clipboard()
        cb_text = clipboard.text()
        if not cb_text:
            return

        try:
            data = json.loads(cb_text)
        except json.JSONDecodeError:
            logger.warning("Clipboard does not contain valid JSON data")
            return

        # NodeGraphQt expects a dict with 'nodes' key containing a dict
        if not isinstance(data, dict):
            logger.warning("Clipboard data is not in NodeGraphQt format (expected dict)")
            return

        nodes_data = data.get("nodes")
        if nodes_data is not None and not isinstance(nodes_data, dict):
            logger.warning(
                "Clipboard 'nodes' data is not in NodeGraphQt format "
                f"(expected dict, got {type(nodes_data).__name__})"
            )
            return

        graph.paste_nodes()

        # Regenerate IDs for all pasted nodes (selected after paste)
        pasted_nodes = graph.selected_nodes()
        if pasted_nodes:
            self._regenerate_node_ids(pasted_nodes)

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

        # CRITICAL: Regenerate IDs for pasted nodes to avoid duplicates
        # NodeGraphQt's add_node (used by paste) doesn't emit node_created signal,
        # so the paste hook in node_graph_widget.py doesn't trigger
        self._regenerate_node_ids(pasted_nodes)

        # Calculate bounding box center of pasted nodes
        min_x = min(node.pos()[0] for node in pasted_nodes)
        min_y = min(node.pos()[1] for node in pasted_nodes)
        max_x = max(node.pos()[0] + node.view.boundingRect().width() for node in pasted_nodes)
        max_y = max(node.pos()[1] + node.view.boundingRect().height() for node in pasted_nodes)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Calculate offset to center nodes at cursor position
        offset_x = scene_pos.x() - center_x
        offset_y = scene_pos.y() - center_y

        # Move pasted nodes to cursor position (centered)
        for node in pasted_nodes:
            current_pos = node.pos()
            node.set_pos(current_pos[0] + offset_x, current_pos[1] + offset_y)

    def _regenerate_node_ids(self, nodes: list) -> None:
        """
        Regenerate unique IDs for pasted/duplicated nodes.

        NodeGraphQt's paste uses add_node which doesn't emit node_created signal,
        so this method must be called explicitly after paste operations.

        Args:
            nodes: List of pasted nodes that need new IDs
        """
        from casare_rpa.utils.id_generator import generate_node_id

        for node in nodes:
            # Skip nodes without casare_node (visual-only like comments)
            if not hasattr(node, "get_casare_node"):
                continue

            casare_node = node.get_casare_node()
            if not casare_node:
                # Try to create one if missing
                if hasattr(node, "_auto_create_casare_node"):
                    node._auto_create_casare_node()
                    casare_node = node.get_casare_node()
                if not casare_node:
                    continue

            # Generate new unique ID
            node_type = getattr(casare_node, "node_type", None) or type(casare_node).__name__
            old_id = casare_node.node_id
            new_id = generate_node_id(node_type)

            # Update both casare_node and visual property
            casare_node.node_id = new_id
            node.set_property("node_id", new_id)

            logger.debug(f"Regenerated node ID: {old_id} -> {new_id}")

    def _on_debug_mode_toggled(self, enabled: bool) -> None:
        """Handle debug mode toggle."""
        logger.info(f"Debug mode {'enabled' if enabled else 'disabled'}")

    def _on_step_mode_toggled(self, enabled: bool) -> None:
        """Handle step mode toggle."""
        logger.info(f"Step mode {'enabled' if enabled else 'disabled'}")

    def _on_debug_step(self) -> None:
        """Handle debug step request."""
        # Delegate to execution controller
        if hasattr(self._execution_controller, "_workflow_runner"):
            runner = self._execution_controller._workflow_runner
            if runner and runner.debug_mode:
                runner.step()

    def _on_debug_continue(self) -> None:
        """Handle debug continue request."""
        # Delegate to execution controller
        if hasattr(self._execution_controller, "_workflow_runner"):
            runner = self._execution_controller._workflow_runner
            if runner and runner.debug_mode:
                runner.continue_execution()

    # =========================================================================
    # WORKFLOW SAVE/LOAD HANDLERS
    # =========================================================================

    def _on_workflow_save(self, file_path: str) -> None:
        """
        Handle workflow save - serialize graph and write to file.

        Args:
            file_path: Path to save workflow to
        """
        from PySide6.QtWidgets import QMessageBox

        try:
            logger.info(f"Saving workflow to: {file_path}")

            try:
                path = write_workflow_file(file_path, self._serializer.serialize())
            except PathSecurityError as e:
                logger.error(f"Security violation saving workflow: {e}")
                QMessageBox.critical(
                    self._main_window,
                    "Save Error",
                    f"Cannot save to this location:\n{e}",
                )
                return

            logger.info(f"Workflow saved successfully: {path.name}")
            self._main_window.show_status(f"Saved: {path.name}", 3000)

            # Mark undo stack as clean (at saved state)
            if hasattr(self, "_undo_stack") and self._undo_stack:
                self._undo_stack.setClean()

        except Exception as e:
            logger.exception(f"Failed to save workflow: {e}")
            QMessageBox.critical(
                self._main_window,
                "Save Error",
                f"Failed to save workflow:\n{e}",
            )

    def _on_workflow_load(self, file_path: str) -> None:
        """
        Handle workflow load - read file and deserialize into graph.

        Args:
            file_path: Path to workflow file
        """
        from pathlib import Path

        try:
            logger.info(f"Loading workflow from: {file_path}")

            # Load using deserializer
            success = self._deserializer.load_from_file(file_path)

            if success:
                logger.info("Workflow loaded successfully")
                self._main_window.show_status(f"Loaded: {Path(file_path).name}", 3000)
                # Mark undo stack as clean after load
                if hasattr(self, "_undo_stack") and self._undo_stack:
                    self._undo_stack.setClean()
            else:
                logger.error("Failed to load workflow")
                from PySide6.QtWidgets import QMessageBox

                QMessageBox.warning(
                    self._main_window,
                    "Load Error",
                    f"Failed to load workflow from:\n{file_path}",
                )

        except Exception as e:
            logger.exception(f"Failed to load workflow: {e}")
            from PySide6.QtWidgets import QMessageBox

            QMessageBox.critical(
                self._main_window,
                "Load Error",
                f"Failed to load workflow:\n{e}",
            )

    def _on_workflow_new(self) -> None:
        """Handle new workflow - clear the graph."""
        try:
            logger.info("Creating new workflow")
            self._node_graph.graph.clear_session()
            # Mark undo stack as clean for new workflow
            if hasattr(self, "_undo_stack") and self._undo_stack:
                self._undo_stack.setClean()
            logger.info("Graph cleared for new workflow")
        except Exception as e:
            logger.exception(f"Failed to clear graph: {e}")

    def _on_scenario_opened(self, project_path: str, scenario_path: str) -> None:
        """
        Handle scenario open by routing through standard workflow open.

        Args:
            project_path: Path to project folder
            scenario_path: Path to scenario JSON file
        """
        if self._workflow_controller:
            self._workflow_controller.open_workflow_path(scenario_path)

    # Public API for getting controllers
    def get_workflow_controller(self) -> WorkflowController:
        """Get the workflow controller."""
        return self._workflow_controller

    def get_execution_controller(self) -> ExecutionController:
        """Get the execution controller."""
        return self._execution_controller

    def get_node_controller(self) -> NodeController:
        """Get the node controller."""
        return self._node_controller

    def get_selector_controller(self) -> SelectorController:
        """Get the selector controller."""
        return self._selector_controller

    def get_preferences_controller(self) -> PreferencesController:
        """Get the preferences controller."""
        return self._preferences_controller

    def get_autosave_controller(self) -> AutosaveController:
        """Get the autosave controller."""
        return self._autosave_controller

    def run(self) -> int:
        """
        Run the application.

        Returns:
            Application exit code
        """
        # Window already shown in __init__ for faster perceived startup
        # Just ensure it's visible and start the event loop
        if not self._main_window.isVisible():
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
        # Window already shown in __init__ for faster perceived startup
        if not self._main_window.isVisible():
            self._main_window.show()
        return 0

    def cleanup(self) -> None:
        """Cleanup all controllers."""
        logger.info("Cleaning up application")
        for controller in self._get_all_controllers():
            try:
                controller.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {controller.__class__.__name__}: {e}")

    def _on_about_to_quit(self) -> None:
        """
        Handle application quit - cleanup async resources before event loop terminates.

        This prevents RuntimeWarning from litellm about unawaited coroutines by
        properly closing async HTTP clients before the Qt/asyncio event loop ends.
        """
        logger.debug("Application about to quit - running async cleanup")

        # Cleanup litellm async HTTP clients
        try:
            from litellm.llms.custom_httpx.async_client_cleanup import (
                close_litellm_async_clients,
            )

            # Run the async cleanup synchronously before event loop terminates
            # We need to use the existing event loop since it's still running
            if self._loop.is_running():
                # Schedule cleanup and wait for it
                future = asyncio.run_coroutine_threadsafe(close_litellm_async_clients(), self._loop)
                try:
                    # Wait with a short timeout to avoid blocking shutdown
                    future.result(timeout=2.0)
                    logger.debug("litellm async clients cleaned up")
                except TimeoutError:
                    logger.warning("litellm cleanup timed out")
                except Exception as e:
                    logger.debug(f"litellm cleanup: {e}")
            else:
                # Event loop not running, try direct execution
                try:
                    self._loop.run_until_complete(close_litellm_async_clients())
                    logger.debug("litellm async clients cleaned up (sync)")
                except Exception as e:
                    logger.debug(f"litellm cleanup (sync): {e}")

        except ImportError:
            # litellm not installed or cleanup module not available
            logger.debug("litellm cleanup module not available - skipping")
        except Exception as e:
            # Don't let cleanup errors prevent application exit
            logger.debug(f"litellm cleanup error (non-fatal): {e}")


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

"""
UI Component Initializer for MainWindow.

Handles initialization of panels, docks, debug components, and validation
timers in a structured, tiered loading approach.
"""

from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt, QTimer

from loguru import logger

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMenu

    from ..main_window import MainWindow
    from ..ui.panels import BottomPanelDock
    from ..ui.panels.process_mining_panel import ProcessMiningPanel
    from ..ui.panels.robot_picker_panel import RobotPickerPanel
    from ..ui.widgets.execution_timeline import ExecutionTimeline
    from ..ui.debug_panel import DebugPanel
    from ..controllers.robot_controller import RobotController


class UIComponentInitializer:
    """
    Initializes UI components for MainWindow in a tiered approach.

    Responsibilities:
    - Load NORMAL tier components (panels, docks) after window shown
    - Create debug components (toolbar, panel)
    - Setup validation timer for real-time validation
    - Coordinate with DockCreator for panel creation

    Tiered Loading:
    - CRITICAL: Window setup, actions, menus, toolbar (immediate)
    - NORMAL: Panels, docks, debug components (after showEvent)
    - DEFERRED: Dialogs, heavy features (on first use)

    Attributes:
        _main_window: Reference to parent MainWindow
        _normal_components_loaded: Flag tracking NORMAL tier load status
    """

    def __init__(self, main_window: "MainWindow") -> None:
        """
        Initialize the UI component initializer.

        Args:
            main_window: Parent MainWindow instance
        """
        self._main_window = main_window
        self._normal_components_loaded: bool = False

    @property
    def is_normal_loaded(self) -> bool:
        """Check if NORMAL tier components are loaded."""
        return self._normal_components_loaded

    def ensure_normal_components_loaded(self) -> None:
        """Ensure NORMAL tier components are loaded (idempotent)."""
        if not self._normal_components_loaded:
            self.load_normal_components()

    def load_normal_components(self) -> None:
        """
        Load NORMAL tier components after window is shown.

        Creates:
        - Bottom panel (Variables, Output, Log, Validation)
        - Execution timeline dock
        - Debug components (toolbar, panel)
        - Process mining panel
        - Robot picker panel
        - Validation timer
        """
        if self._normal_components_loaded:
            return

        import time

        start_time = time.perf_counter()
        logger.debug("UIComponentInitializer: Loading normal tier components...")

        mw = self._main_window
        dock_creator = mw._dock_creator

        # Create panels and docks via DockCreator
        mw._bottom_panel = dock_creator.create_bottom_panel()

        # Connect VariableProvider to MainWindow for variable picker integration
        self._connect_variable_provider()

        dock, timeline = dock_creator.create_execution_timeline_dock()
        mw._execution_timeline_dock = dock
        mw._execution_timeline = timeline

        # Create debug components
        self._create_debug_components()

        # Setup validation timer
        self._setup_validation_timer()

        # Create robot picker panel with robot controller
        mw._robot_picker_panel = dock_creator.create_robot_picker_panel(
            mw._robot_controller
        )

        self._normal_components_loaded = True

        # Restore UI state after components created
        if mw._ui_state_controller:
            mw._ui_state_controller.restore_state()

        elapsed = (time.perf_counter() - start_time) * 1000
        logger.info(
            f"UIComponentInitializer: Normal tier components loaded in {elapsed:.2f}ms"
        )

    def _create_debug_components(self) -> None:
        """
        Create debug panel.

        Debug panel provides:
        - Call stack visualization
        - Watch expressions
        - Breakpoints list
        """
        mw = self._main_window

        # Create debug panel (Call Stack, Watch, Breakpoints)
        mw._debug_panel = mw._dock_creator.create_debug_panel()

        # Create process mining panel (AI-powered process discovery)
        mw._process_mining_panel = mw._dock_creator.create_process_mining_panel()

        # Create analytics panel (bottleneck detection, execution analysis)
        mw._analytics_panel = mw._dock_creator.create_analytics_panel()

    def _connect_variable_provider(self) -> None:
        """
        Connect VariableProvider singleton to MainWindow.

        This enables variable picker widgets to access:
        - Workflow variables from the Variables tab
        - Upstream node output variables
        - System variables
        """
        try:
            from ..ui.widgets.variable_picker import VariableProvider

            provider = VariableProvider.get_instance()
            provider.set_main_window(self._main_window)
            logger.debug("VariableProvider connected to MainWindow")
        except Exception as e:
            logger.warning(f"Failed to connect VariableProvider: {e}")

    def _setup_validation_timer(self) -> None:
        """
        Setup validation timer for debounced real-time validation.

        The timer delays validation to avoid running it on every keystroke.
        Default delay: 500ms
        """
        mw = self._main_window
        mw._validation_timer = QTimer(mw)
        mw._validation_timer.setSingleShot(True)
        mw._validation_timer.setInterval(500)
        mw._validation_timer.timeout.connect(mw._do_deferred_validation)

    def _find_view_menu(self) -> Optional["QMenu"]:
        """Get the View menu (stored reference or fallback search)."""
        mw = self._main_window
        # Use stored reference if available
        if hasattr(mw, "_view_menu") and mw._view_menu is not None:
            try:
                _ = mw._view_menu.title()
                return mw._view_menu
            except RuntimeError:
                pass
        # Fallback: search menu bar
        for action in mw.menuBar().actions():
            if action.text() == "&View":
                return action.menu()
        return None

    def schedule_deferred_load(self, delay_ms: int = 100) -> None:
        """
        Schedule NORMAL tier load after a delay.

        Used by showEvent to defer loading until window is visible.

        Args:
            delay_ms: Delay in milliseconds before loading (default: 100)
        """
        if self._normal_components_loaded:
            return
        QTimer.singleShot(delay_ms, self.load_normal_components)

    def cleanup(self) -> None:
        """
        Cleanup initializer resources.

        Stops validation timer if active.
        """
        mw = self._main_window
        if mw._validation_timer:
            mw._validation_timer.stop()
            mw._validation_timer = None
        self._normal_components_loaded = False
        logger.debug("UIComponentInitializer: Cleaned up")

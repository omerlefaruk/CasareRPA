"""
Side Panel Dock for CasareRPA.

Dockable container with tabs for Debug, Process Mining, Robot Picker, and Analytics.
Provides a unified right-side panel for advanced features.
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QDockWidget,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import (
    THEME,
)

if TYPE_CHECKING:
    from ...controllers.robot_controller import RobotController
    from ...debugger.debug_controller import DebugController
    from ..debug_panel import DebugPanel
    from .analytics_panel import AnalyticsPanel
    from .credentials_panel import CredentialsPanel
    from .process_mining_panel import ProcessMiningPanel
    from .robot_picker_panel import RobotPickerPanel

try:
    from casare_rpa.domain.events import (
        NodeCompleted,
        NodeStarted,
        WorkflowStarted,
        get_event_bus,
    )
    from casare_rpa.domain.events.node_events import NodeFailed
    from casare_rpa.presentation.canvas.ui.widgets.profiling_tree import (
        ProfilingTreeWidget,
    )

    HAS_PROFILING = True
except ImportError as e:
    logger.warning(f"Profiling disabled due to missing dependencies: {e}")
    HAS_PROFILING = False


class SidePanelDock(QDockWidget):
    """
    Dockable side panel with tabs for Debug, Process Mining, Robot Picker, Analytics.

    Features:
    - Debug: Call stack, watch expressions, breakpoints, REPL
    - Process Mining: AI-powered process discovery
    - Robot Picker: Select robots for cloud execution
    - Analytics: Bottleneck detection, execution analysis

    Signals:
        navigate_to_node: Emitted when navigation to a node is requested
        select_node: Emitted when a node should be selected in canvas
        step_over_requested: Debug step over
        step_into_requested: Debug step into
        step_out_requested: Debug step out
        continue_requested: Debug continue
    """

    navigate_to_node = Signal(str)
    select_node = Signal(str)
    step_over_requested = Signal()
    step_into_requested = Signal()
    step_out_requested = Signal()
    continue_requested = Signal()

    # Tab indices
    TAB_DEBUG = 0
    TAB_PROCESS_MINING = 1
    TAB_ROBOT_PICKER = 2
    TAB_ANALYTICS = 3
    TAB_PROFILING = 4
    TAB_CREDENTIALS = 5

    def __init__(
        self,
        parent: QWidget | None = None,
        debug_controller: Optional["DebugController"] = None,
        robot_controller: Optional["RobotController"] = None,
    ) -> None:
        """
        Initialize the side panel dock.

        Args:
            parent: Optional parent widget
            debug_controller: Optional debug controller for integration
            robot_controller: Optional robot controller for integration
        """
        super().__init__("Side Panel", parent)
        self.setObjectName("SidePanelDock")

        self._debug_controller = debug_controller
        self._robot_controller = robot_controller

        self._debug_tab: DebugPanel | None = None
        self._process_mining_tab: ProcessMiningPanel | None = None
        self._robot_picker_tab: RobotPickerPanel | None = None
        self._analytics_tab: AnalyticsPanel | None = None
        self._profiling_tab: ProfilingTreeWidget | None = None
        self._credentials_tab: CredentialsPanel | None = None

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._setup_profiling_subscriptions()

        logger.debug("SidePanelDock initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        # Set minimum sizes - allow shrinking but not too small
        self.setMinimumWidth(280)
        self.setMinimumHeight(150)
        # Size policy: can expand horizontally, expand vertically
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def sizeHint(self) -> QSize:
        """Return preferred size for dock widget."""
        return QSize(380, 500)

    def showEvent(self, event) -> None:
        """Handle show event - ensure minimum visible size."""
        super().showEvent(event)
        # Ensure dock has usable size when shown
        if self.width() < 280 or self.height() < 150:
            self.resize(380, 500)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main container widget
        container = QWidget()
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab widget with expanding size policy
        self._tab_widget = QTabWidget()
        self._tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setUsesScrollButtons(True)
        self._tab_widget.setMovable(False)
        self._tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._create_tabs()

        layout.addWidget(self._tab_widget, stretch=1)
        self.setWidget(container)

    def _create_tabs(self) -> None:
        """Create all tab widgets with scroll area wrappers."""
        from ..debug_panel import DebugPanel
        from .analytics_panel import AnalyticsPanel
        from .credentials_panel import CredentialsPanel
        from .process_mining_panel import ProcessMiningPanel
        from .robot_picker_panel import RobotPickerPanel

        # Debug tab - create dock and extract widget
        self._debug_dock = DebugPanel(None, self._debug_controller)
        self._debug_tab = self._debug_dock.widget()
        self._debug_dock.navigate_to_node.connect(self.navigate_to_node.emit)
        self._debug_dock.step_over_requested.connect(self.step_over_requested.emit)
        self._debug_dock.step_into_requested.connect(self.step_into_requested.emit)
        self._debug_dock.step_out_requested.connect(self.step_out_requested.emit)
        self._debug_dock.continue_requested.connect(self.continue_requested.emit)
        debug_scroll = self._wrap_in_scroll_area(self._debug_tab)
        self._tab_widget.addTab(debug_scroll, "Debug")
        self._tab_widget.setTabToolTip(self.TAB_DEBUG, "Debug panel (Ctrl+Shift+D)")

        # Process Mining tab - create dock and extract widget
        self._process_mining_dock = ProcessMiningPanel(None)
        self._process_mining_tab = self._process_mining_dock.widget()
        mining_scroll = self._wrap_in_scroll_area(self._process_mining_tab)
        self._tab_widget.addTab(mining_scroll, "Process Mining")
        self._tab_widget.setTabToolTip(
            self.TAB_PROCESS_MINING, "AI-powered process discovery (Ctrl+Shift+M)"
        )

        # Robot Picker tab - create dock and extract widget
        self._robot_picker_dock = RobotPickerPanel(None)
        self._robot_picker_tab = self._robot_picker_dock.widget()
        if self._robot_controller:
            self._robot_controller.set_panel(self._robot_picker_dock)
        robot_scroll = self._wrap_in_scroll_area(self._robot_picker_tab)
        self._tab_widget.addTab(robot_scroll, "Robots")
        self._tab_widget.setTabToolTip(
            self.TAB_ROBOT_PICKER, "Select robots for execution (Ctrl+Shift+R)"
        )

        # Analytics tab - create dock and extract widget
        self._analytics_dock = AnalyticsPanel(None)
        self._analytics_tab = self._analytics_dock.widget()
        analytics_scroll = self._wrap_in_scroll_area(self._analytics_tab)
        self._tab_widget.addTab(analytics_scroll, "Analytics")
        self._tab_widget.setTabToolTip(
            self.TAB_ANALYTICS, "Bottleneck detection and analysis (Ctrl+Shift+A)"
        )

        # Profiling tab - UiPath-style execution profiling
        if HAS_PROFILING:
            self._profiling_tab = ProfilingTreeWidget()
            # Single click selects and centers node in canvas
            self._profiling_tab.node_clicked.connect(self.navigate_to_node.emit)
            profiling_scroll = self._wrap_in_scroll_area(self._profiling_tab)
            self._tab_widget.addTab(profiling_scroll, "Profiling")
            self._tab_widget.setTabToolTip(
                self.TAB_PROFILING, "Execution profiling and timing analysis"
            )

        # Credentials tab
        self._credentials_dock = CredentialsPanel(None, embedded=True)
        self._credentials_tab = self._credentials_dock
        credentials_scroll = self._wrap_in_scroll_area(self._credentials_tab)
        self._tab_widget.addTab(credentials_scroll, "Credentials")
        self._tab_widget.setTabToolTip(
            self.TAB_CREDENTIALS, "Manage global credentials (Ctrl+Shift+C)"
        )

    def _wrap_in_scroll_area(self, widget: QWidget) -> QScrollArea:
        """Wrap a widget in a scroll area for overflow handling."""
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        # Apply theme-consistent scrollbar styling with ElevenLabs tokens
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {THEME.bg_surface};
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {THEME.bg_surface};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {THEME.bg_hover};
                border-radius: {TOKENS.radius.sm}px;  /* 4px - ElevenLabs radius-sm */
                min-height: 30px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {THEME.border_light};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar:horizontal {{
                background-color: {THEME.bg_surface};
                height: 10px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {THEME.bg_hover};
                border-radius: {TOKENS.radius.sm}px;  /* 4px - ElevenLabs radius-sm */
                min-width: 30px;
                margin: 2px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {THEME.border_light};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
        """)
        return scroll

    def _apply_styles(self) -> None:
        """Apply ElevenLabs-style panel dock styling."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                color: {THEME.dock_title_text};
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
                font-weight: 600;
                font-size: {TOKENS.typography.body_sm}px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {THEME.border_dark};
                font-family: {TOKENS.typography.family};
            }}
            QTabWidget {{
                background-color: {THEME.bg_surface};
                border: none;
            }}
            QTabWidget::pane {{
                background-color: {THEME.bg_surface};
                border: none;
                border-top: 1px solid {THEME.border_dark};
            }}
            QTabBar {{
                background-color: {THEME.bg_header};
                qproperty-drawBase: 0;
            }}
            QTabBar::tab {{
                background-color: {THEME.bg_header};
                color: {THEME.text_muted};
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.lg}px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: {TOKENS.typography.body_sm}px;
                font-weight: 500;
                min-width: 60px;
                font-family: {TOKENS.typography.family};
            }}
            QTabBar::tab:hover {{
                color: {THEME.text_primary};
                background-color: {THEME.bg_hover};
            }}
            QTabBar::tab:selected {{
                color: {THEME.text_primary};
                background-color: {THEME.bg_surface};
                border-bottom: 2px solid {THEME.primary};
            }}
            QTabBar::tab:!selected {{
                border-top: 1px solid {THEME.border_dark};
            }}
            QTabBar::tab:first {{
                margin-left: {TOKENS.spacing.xs}px;
            }}
            QTabBar::scroller {{
                width: 20px;
            }}
            QTabBar QToolButton {{
                background-color: {THEME.bg_header};
                border: none;
                color: {THEME.text_secondary};
            }}
            QTabBar QToolButton:hover {{
                background-color: {THEME.bg_hover};
                color: {THEME.text_primary};
            }}
        """)

    # ==================== Public API ====================

    def get_debug_tab(self) -> Optional["DebugPanel"]:
        """Get the Debug tab widget."""
        return self._debug_tab

    def get_process_mining_tab(self) -> Optional["ProcessMiningPanel"]:
        """Get the Process Mining tab widget."""
        return self._process_mining_tab

    def get_robot_picker_tab(self) -> Optional["RobotPickerPanel"]:
        """Get the Robot Picker tab widget."""
        return self._robot_picker_tab

    def get_analytics_tab(self) -> Optional["AnalyticsPanel"]:
        """Get the Analytics tab widget."""
        return self._analytics_tab

    def show_debug_tab(self) -> None:
        """Show and focus the Debug tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_DEBUG)

    def show_process_mining_tab(self) -> None:
        """Show and focus the Process Mining tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_PROCESS_MINING)

    def show_robot_picker_tab(self) -> None:
        """Show and focus the Robot Picker tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_ROBOT_PICKER)

    def show_analytics_tab(self) -> None:
        """Show and focus the Analytics tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_ANALYTICS)

    def get_credentials_tab(self) -> Optional["CredentialsPanel"]:
        """Get the Credentials tab widget."""
        return self._credentials_tab

    def show_credentials_tab(self) -> None:
        """Toggle the Credentials tab visibility. Hide if already on credentials tab."""
        if self.isVisible() and self._tab_widget.currentIndex() == self.TAB_CREDENTIALS:
            self.hide()
        else:
            self.show()
            self._tab_widget.setCurrentIndex(self.TAB_CREDENTIALS)

    def set_analytics_api_url(self, url: str) -> None:
        """Set the API URL for analytics panel."""
        # Use the dock instance which is the actual AnalyticsPanel class
        if hasattr(self, "_analytics_dock") and self._analytics_dock:
            self._analytics_dock.set_api_url(url)
        # Fallback to tab widget if dock is not available (e.g. legacy/embedded mode)
        elif self._analytics_tab and hasattr(self._analytics_tab, "set_api_url"):
            self._analytics_tab.set_api_url(url)

    def get_profiling_tab(self) -> Optional["ProfilingTreeWidget"]:
        """Get the Profiling tab widget."""
        return self._profiling_tab

    def show_profiling_tab(self) -> None:
        """Show and focus the Profiling tab."""
        self.show()
        self._tab_widget.setCurrentIndex(self.TAB_PROFILING)

    def _setup_profiling_subscriptions(self) -> None:
        """Set up domain EventBus subscriptions for profiling."""
        if not HAS_PROFILING or not self._profiling_tab:
            return

        # Subscribe to domain events (DDD 2025 style)
        self._domain_event_bus = get_event_bus()
        self._domain_event_bus.subscribe(WorkflowStarted, self._on_workflow_started)
        self._domain_event_bus.subscribe(NodeStarted, self._on_node_started)
        self._domain_event_bus.subscribe(NodeCompleted, self._on_node_completed)
        self._domain_event_bus.subscribe(NodeFailed, self._on_node_error)

    def _on_workflow_started(self, event) -> None:
        """Handle workflow started - clear profiling data."""
        if self._profiling_tab:
            self._profiling_tab.clear()

    def _on_node_started(self, event) -> None:
        """Handle node started event."""
        if not self._profiling_tab:
            return
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        node_name = data.get("node_name", "") if isinstance(data, dict) else ""
        node_type = data.get("node_type", "") if isinstance(data, dict) else ""
        parent_id = data.get("parent_id") if isinstance(data, dict) else None

        self._profiling_tab.add_entry(
            node_id=node_id,
            node_name=node_name or node_id[:12],
            node_type=node_type,
            parent_id=parent_id,
        )

    def _on_node_completed(self, event) -> None:
        """Handle node completed event."""
        if not self._profiling_tab:
            return
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        # Support both execution_time (seconds) and duration_ms
        duration_ms = 0
        if isinstance(data, dict):
            if "duration_ms" in data:
                duration_ms = data.get("duration_ms", 0)
            elif "execution_time" in data:
                # execution_time is in seconds, convert to ms
                duration_ms = data.get("execution_time", 0) * 1000

        self._profiling_tab.update_entry(
            node_id=node_id,
            duration_ms=duration_ms,
            status="completed",
        )

    def _on_node_error(self, event) -> None:
        """Handle node error event."""
        if not self._profiling_tab:
            return
        data = event.data if hasattr(event, "data") else event
        node_id = data.get("node_id", "") if isinstance(data, dict) else ""
        duration_ms = 0
        if isinstance(data, dict):
            if "duration_ms" in data:
                duration_ms = data.get("duration_ms", 0)
            elif "execution_time" in data:
                duration_ms = data.get("execution_time", 0) * 1000

        self._profiling_tab.update_entry(
            node_id=node_id,
            duration_ms=duration_ms,
            status="failed",
        )

    def cleanup(self) -> None:
        """Clean up resources."""
        if (
            hasattr(self, "_analytics_dock")
            and self._analytics_dock
            and hasattr(self._analytics_dock, "cleanup")
        ):
            self._analytics_dock.cleanup()
        elif self._analytics_tab and hasattr(self._analytics_tab, "cleanup"):
            self._analytics_tab.cleanup()
        logger.debug("SidePanelDock cleaned up")

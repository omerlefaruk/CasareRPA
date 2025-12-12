"""
Fleet Dashboard Dialog for CasareRPA Canvas.

Comprehensive admin dashboard for robot fleet management with robots, jobs,
schedules, analytics, and API keys tabs. Supports multi-tenant filtering
and real-time updates via WebSocketBridge.
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QLabel,
    QWidget,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from loguru import logger

from PySide6.QtWidgets import QDialog
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs import (
    RobotsTabWidget,
    JobsTabWidget,
    SchedulesTabWidget,
    QueuesTabWidget,
    AnalyticsTabWidget,
    ApiKeysTabWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.tenant_selector import (
    TenantSelectorWidget,
)

if TYPE_CHECKING:
    from casare_rpa.domain.orchestrator.entities.robot import Robot
    from casare_rpa.presentation.canvas.services.websocket_bridge import (
        WebSocketBridge,
        RobotStatusUpdate,
        JobStatusUpdate,
        QueueMetricsUpdate,
    )


class FleetDashboardDialog(QDialog):
    """
    Full admin dashboard for robot fleet management.

    Features:
    - Robots tab: View and manage registered robots
    - Jobs tab: Monitor job queue and history
    - Schedules tab: Manage workflow schedules
    - Queues tab: Transaction queue management (UiPath-style)
    - Analytics tab: Fleet statistics and charts
    - API Keys tab: Manage robot API keys
    - Tenant filtering: Filter by tenant (super admin only)

    Signals:
        robot_selected: Emitted when a robot is selected (robot_id)
        robot_edited: Emitted when a robot is edited (robot_id, robot_data)
        robot_deleted: Emitted when a robot is deleted (robot_id)
        job_cancelled: Emitted when a job is cancelled (job_id)
        job_retried: Emitted when a job is retried (job_id)
        schedule_enabled_changed: Emitted when schedule is toggled (schedule_id, enabled)
        schedule_edited: Emitted when schedule edit requested (schedule_id)
        schedule_deleted: Emitted when schedule is deleted (schedule_id)
        schedule_run_now: Emitted when run now is clicked (schedule_id)
        queue_selected: Emitted when a queue is selected (queue_id)
        queue_created: Emitted when queue is created (queue_data)
        queue_deleted: Emitted when queue is deleted (queue_id)
        queue_item_action: Emitted for queue item actions (queue_id, item_ids, action)
        api_key_generated: Emitted when API key generation requested (config_dict)
        api_key_revoked: Emitted when API key revoked (key_id)
        api_key_rotated: Emitted when API key rotation requested (key_id)
        tenant_changed: Emitted when tenant filter changes (tenant_id or None)
        refresh_requested: Emitted when any tab requests refresh
    """

    robot_selected = Signal(str)
    robot_edited = Signal(str, dict)
    robot_deleted = Signal(str)
    job_cancelled = Signal(str)
    job_retried = Signal(str)
    schedule_enabled_changed = Signal(str, bool)
    schedule_edited = Signal(str)
    schedule_deleted = Signal(str)
    schedule_run_now = Signal(str)
    queue_selected = Signal(str)
    queue_created = Signal(dict)
    queue_deleted = Signal(str)
    queue_item_action = Signal(str, list, str)
    api_key_generated = Signal(dict)
    api_key_revoked = Signal(str)
    api_key_rotated = Signal(str)
    tenant_changed = Signal(object)  # str or None
    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Fleet Dashboard dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Fleet Management Dashboard")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        self.setModal(False)

        self._current_tenant_id: Optional[str] = None
        self._is_super_admin = False
        self._robots: List[Dict[str, Any]] = []

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        logger.debug("FleetDashboardDialog initialized")

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with title and tenant selector
        header_layout = QHBoxLayout()

        title = QLabel("Fleet Management Dashboard")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Tenant selector (hidden by default, shown for super admins)
        self._tenant_selector = TenantSelectorWidget(
            show_all_option=True,
            label_text="Tenant:",
        )
        self._tenant_selector.setVisible(False)
        self._tenant_selector.tenant_changed.connect(self._on_tenant_changed)
        header_layout.addWidget(self._tenant_selector)

        self._connection_status = QLabel("Disconnected")
        self._connection_status.setStyleSheet("color: #F44336;")
        header_layout.addWidget(self._connection_status)

        layout.addLayout(header_layout)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        self._robots_tab = RobotsTabWidget()
        self._tabs.addTab(self._robots_tab, "Robots")

        self._jobs_tab = JobsTabWidget()
        self._tabs.addTab(self._jobs_tab, "Jobs")

        self._schedules_tab = SchedulesTabWidget()
        self._tabs.addTab(self._schedules_tab, "Schedules")

        self._queues_tab = QueuesTabWidget()
        self._tabs.addTab(self._queues_tab, "Queues")

        self._api_keys_tab = ApiKeysTabWidget()
        self._tabs.addTab(self._api_keys_tab, "API Keys")

        self._analytics_tab = AnalyticsTabWidget()
        self._tabs.addTab(self._analytics_tab, "Analytics")

        layout.addWidget(self._tabs)

        # Footer
        footer = QHBoxLayout()

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #888888;")
        footer.addWidget(self._status_label)

        footer.addStretch()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        footer.addWidget(self._close_btn)

        layout.addLayout(footer)

    def _connect_signals(self) -> None:
        """Connect tab signals to dialog signals."""
        # Robots tab
        self._robots_tab.robot_selected.connect(self.robot_selected.emit)
        self._robots_tab.robot_edited.connect(self.robot_edited.emit)
        self._robots_tab.robot_deleted.connect(self.robot_deleted.emit)
        self._robots_tab.refresh_requested.connect(self._on_refresh_robots)

        # Jobs tab
        self._jobs_tab.job_selected.connect(self._on_job_selected)
        self._jobs_tab.job_cancelled.connect(self.job_cancelled.emit)
        self._jobs_tab.job_retried.connect(self.job_retried.emit)
        self._jobs_tab.refresh_requested.connect(self._on_refresh_jobs)

        # Schedules tab
        self._schedules_tab.schedule_selected.connect(self._on_schedule_selected)
        self._schedules_tab.schedule_enabled_changed.connect(
            self.schedule_enabled_changed.emit
        )
        self._schedules_tab.schedule_edited.connect(self.schedule_edited.emit)
        self._schedules_tab.schedule_deleted.connect(self.schedule_deleted.emit)
        self._schedules_tab.schedule_run_now.connect(self.schedule_run_now.emit)
        self._schedules_tab.refresh_requested.connect(self._on_refresh_schedules)

        # Queues tab
        self._queues_tab.queue_selected.connect(self.queue_selected.emit)
        self._queues_tab.queue_created.connect(self.queue_created.emit)
        self._queues_tab.queue_deleted.connect(self.queue_deleted.emit)
        self._queues_tab.items_bulk_action.connect(self.queue_item_action.emit)
        self._queues_tab.refresh_requested.connect(self._on_refresh_queues)

        # API Keys tab
        self._api_keys_tab.key_generated.connect(self.api_key_generated.emit)
        self._api_keys_tab.key_revoked.connect(self.api_key_revoked.emit)
        self._api_keys_tab.key_rotated.connect(self.api_key_rotated.emit)
        self._api_keys_tab.refresh_requested.connect(self._on_refresh_api_keys)

        # Analytics tab
        self._analytics_tab.refresh_requested.connect(self._on_refresh_analytics)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background: #252525;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background: #2a2a2a;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                padding: 10px 20px;
                margin-right: 2px;
                color: #a0a0a0;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #3a3a3a;
                color: #e0e0e0;
                border-bottom-color: #3a3a3a;
            }
            QTabBar::tab:hover:!selected {
                background: #353535;
                color: #c0c0c0;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 8px 20px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #5a8a9a;
            }
            QPushButton:pressed {
                background: #3a3a3a;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def _on_refresh_robots(self) -> None:
        """Handle robots tab refresh request."""
        self._status_label.setText("Refreshing robots...")
        self._robots_tab.set_refreshing(True)
        self.refresh_requested.emit()

    def _on_refresh_jobs(self) -> None:
        """Handle jobs tab refresh request."""
        self._status_label.setText("Refreshing jobs...")
        self._jobs_tab.set_refreshing(True)
        self.refresh_requested.emit()

    def _on_refresh_schedules(self) -> None:
        """Handle schedules tab refresh request."""
        self._status_label.setText("Refreshing schedules...")
        self._schedules_tab.set_refreshing(True)
        self.refresh_requested.emit()

    def _on_refresh_analytics(self) -> None:
        """Handle analytics tab refresh request."""
        self._status_label.setText("Refreshing analytics...")
        self._analytics_tab.set_refreshing(True)
        self.refresh_requested.emit()

    def _on_refresh_api_keys(self) -> None:
        """Handle API keys tab refresh request."""
        self._status_label.setText("Refreshing API keys...")
        self._api_keys_tab.set_refreshing(True)
        self.refresh_requested.emit()

    def _on_refresh_queues(self) -> None:
        """Handle queues tab refresh request."""
        self._status_label.setText("Refreshing queues...")
        self._queues_tab.set_refreshing(True)
        self.refresh_requested.emit()

    def _on_tenant_changed(self, tenant_id: Optional[str]) -> None:
        """Handle tenant selection change."""
        self._current_tenant_id = tenant_id
        self._api_keys_tab.set_tenant(tenant_id)
        self.tenant_changed.emit(tenant_id)
        logger.debug(f"Tenant changed to: {tenant_id}")

    def _on_job_selected(self, job_id: str) -> None:
        """Handle job selection."""
        logger.debug(f"Job selected: {job_id}")

    def _on_schedule_selected(self, schedule_id: str) -> None:
        """Handle schedule selection."""
        logger.debug(f"Schedule selected: {schedule_id}")

    def update_robots(self, robots: List["Robot"]) -> None:
        """
        Update robots tab with new data.

        Args:
            robots: List of Robot entities
        """
        self._robots_tab.update_robots(robots)
        self._robots_tab.set_refreshing(False)
        self._status_label.setText("Ready")

    def update_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """
        Update jobs tab with new data.

        Args:
            jobs: List of job dictionaries
        """
        self._jobs_tab.update_jobs(jobs)
        self._jobs_tab.set_refreshing(False)
        self._status_label.setText("Ready")

    def update_schedules(self, schedules: List[Dict[str, Any]]) -> None:
        """
        Update schedules tab with new data.

        Args:
            schedules: List of schedule dictionaries
        """
        self._schedules_tab.update_schedules(schedules)
        self._schedules_tab.set_refreshing(False)
        self._status_label.setText("Ready")

    def update_analytics(self, analytics: Dict[str, Any]) -> None:
        """
        Update analytics tab with new data.

        Args:
            analytics: Analytics data dictionary
        """
        self._analytics_tab.update_analytics(analytics)
        self._analytics_tab.set_refreshing(False)
        self._status_label.setText("Ready")

    def set_connection_status(self, connected: bool, message: str = "") -> None:
        """
        Set the connection status indicator.

        Args:
            connected: Whether connected to orchestrator
            message: Optional status message
        """
        if connected:
            self._connection_status.setText(message or "Connected")
            self._connection_status.setStyleSheet("color: #4CAF50;")
        else:
            self._connection_status.setText(message or "Disconnected")
            self._connection_status.setStyleSheet("color: #F44336;")

    def set_status(self, message: str) -> None:
        """
        Set status bar message.

        Args:
            message: Status message to display
        """
        self._status_label.setText(message)

    def show_robots_tab(self) -> None:
        """Switch to robots tab."""
        self._tabs.setCurrentWidget(self._robots_tab)

    def show_jobs_tab(self) -> None:
        """Switch to jobs tab."""
        self._tabs.setCurrentWidget(self._jobs_tab)

    def show_schedules_tab(self) -> None:
        """Switch to schedules tab."""
        self._tabs.setCurrentWidget(self._schedules_tab)

    def show_analytics_tab(self) -> None:
        """Switch to analytics tab."""
        self._tabs.setCurrentWidget(self._analytics_tab)

    def show_api_keys_tab(self) -> None:
        """Switch to API keys tab."""
        self._tabs.setCurrentWidget(self._api_keys_tab)

    def show_queues_tab(self) -> None:
        """Switch to queues tab."""
        self._tabs.setCurrentWidget(self._queues_tab)

    def get_selected_job(self) -> Optional[Dict[str, Any]]:
        """Get currently selected job from jobs tab."""
        return self._jobs_tab.get_selected_job()

    # =========================================================================
    # Multi-Tenant Support
    # =========================================================================

    def set_super_admin(self, is_super_admin: bool) -> None:
        """
        Set whether current user is a super admin.

        Super admins can see and switch between all tenants.

        Args:
            is_super_admin: True if user is super admin.
        """
        self._is_super_admin = is_super_admin
        self._tenant_selector.set_super_admin(is_super_admin)
        self._tenant_selector.setVisible(is_super_admin)

    def update_tenants(self, tenants: List[Dict[str, Any]]) -> None:
        """
        Update available tenants list.

        Args:
            tenants: List of tenant dictionaries with 'id' and 'name' keys.
        """
        self._tenant_selector.update_tenants(tenants)

    def set_current_tenant(self, tenant_id: Optional[str]) -> None:
        """
        Set current tenant selection.

        Args:
            tenant_id: Tenant ID or None for "All Tenants".
        """
        self._tenant_selector.set_current_tenant(tenant_id)

    def get_current_tenant_id(self) -> Optional[str]:
        """
        Get currently selected tenant ID.

        Returns:
            Tenant ID or None if "All Tenants" selected.
        """
        return self._tenant_selector.get_current_tenant_id()

    # =========================================================================
    # API Keys Support
    # =========================================================================

    def update_api_keys(self, api_keys: List[Dict[str, Any]]) -> None:
        """
        Update API keys tab with new data.

        Args:
            api_keys: List of API key dictionaries.
        """
        self._api_keys_tab.update_api_keys(api_keys)
        self._api_keys_tab.set_refreshing(False)
        self._status_label.setText("Ready")

    def update_api_keys_robots(self, robots: List[Dict[str, Any]]) -> None:
        """
        Update robots list in API keys tab.

        Args:
            robots: List of robot dictionaries for key generation dropdown.
        """
        self._robots = robots
        self._api_keys_tab.update_robots(robots)

    # =========================================================================
    # Queues Support
    # =========================================================================

    def update_queues(self, queues: List[Dict[str, Any]]) -> None:
        """
        Update queues tab with new data.

        Args:
            queues: List of queue dictionaries.
        """
        self._queues_tab.update_queues(queues)
        self._queues_tab.set_refreshing(False)
        self._status_label.setText("Ready")

    def update_queue_items(self, items: List[Dict[str, Any]]) -> None:
        """
        Update queue items list in queues tab.

        Args:
            items: List of queue item dictionaries.
        """
        self._queues_tab.update_queue_items(items)

    def update_queue_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Update queue statistics in queues tab.

        Args:
            stats: Statistics dictionary with counts.
        """
        self._queues_tab.update_statistics(stats)

    # =========================================================================
    # WebSocket Real-Time Updates
    # =========================================================================

    def connect_websocket_bridge(self, bridge: "WebSocketBridge") -> None:
        """
        Connect to WebSocketBridge for real-time updates.

        Subscribes to robot status, job status, and queue metrics events.

        Args:
            bridge: WebSocketBridge instance
        """
        # Connect bridge signals to tab handlers
        bridge.robot_status_changed.connect(self._on_realtime_robot_status)
        bridge.job_status_changed.connect(self._on_realtime_job_status)
        bridge.queue_metrics_changed.connect(self._on_realtime_queue_metrics)
        bridge.connection_status_changed.connect(self._on_realtime_connection_status)

        # Connect batch signals for efficiency
        bridge.robots_batch_updated.connect(self._on_realtime_robots_batch)
        bridge.jobs_batch_updated.connect(self._on_realtime_jobs_batch)

        logger.info("FleetDashboard connected to WebSocketBridge")

    def disconnect_websocket_bridge(self, bridge: "WebSocketBridge") -> None:
        """
        Disconnect from WebSocketBridge.

        Args:
            bridge: WebSocketBridge instance to disconnect
        """
        try:
            bridge.robot_status_changed.disconnect(self._on_realtime_robot_status)
            bridge.job_status_changed.disconnect(self._on_realtime_job_status)
            bridge.queue_metrics_changed.disconnect(self._on_realtime_queue_metrics)
            bridge.connection_status_changed.disconnect(
                self._on_realtime_connection_status
            )
            bridge.robots_batch_updated.disconnect(self._on_realtime_robots_batch)
            bridge.jobs_batch_updated.disconnect(self._on_realtime_jobs_batch)
        except (RuntimeError, TypeError):
            # Signals may already be disconnected
            pass

        logger.info("FleetDashboard disconnected from WebSocketBridge")

    def _on_realtime_robot_status(self, update: "RobotStatusUpdate") -> None:
        """
        Handle real-time robot status update.

        Args:
            update: RobotStatusUpdate from WebSocket
        """
        self._robots_tab.handle_robot_status_update(update)

    def _on_realtime_job_status(self, update: "JobStatusUpdate") -> None:
        """
        Handle real-time job status update.

        Args:
            update: JobStatusUpdate from WebSocket
        """
        self._jobs_tab.handle_job_status_update(update)

    def _on_realtime_queue_metrics(self, update: "QueueMetricsUpdate") -> None:
        """
        Handle real-time queue metrics update.

        Updates the analytics tab with new queue depth.

        Args:
            update: QueueMetricsUpdate from WebSocket
        """
        # Update analytics with partial queue metrics
        if hasattr(self._analytics_tab, "update_queue_metrics"):
            self._analytics_tab.update_queue_metrics(update)

    def _on_realtime_connection_status(self, connected: bool) -> None:
        """
        Handle WebSocket connection status change.

        Args:
            connected: True if connected
        """
        self.set_connection_status(connected)

    def _on_realtime_robots_batch(self, updates: List["RobotStatusUpdate"]) -> None:
        """
        Handle batch of robot status updates.

        More efficient than individual updates for high-frequency changes.

        Args:
            updates: List of RobotStatusUpdate objects
        """
        self._robots_tab.handle_batch_robot_updates(updates)

    def _on_realtime_jobs_batch(self, updates: List["JobStatusUpdate"]) -> None:
        """
        Handle batch of job status updates.

        More efficient than individual updates for high-frequency changes.

        Args:
            updates: List of JobStatusUpdate objects
        """
        self._jobs_tab.handle_batch_job_updates(updates)

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
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs.constants import (
    DEADLINE_COLORS,
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with title and tenant selector
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)

        title = QLabel("Fleet Management Dashboard")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
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
        self._connection_status.setStyleSheet("color: #F44336; font-weight: bold;")
        header_layout.addWidget(self._connection_status)

        layout.addWidget(header_widget)

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
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)

        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet("color: #AAAAAA;")
        footer_layout.addWidget(self._status_label)

        footer_layout.addStretch()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(self._close_btn)

        layout.addWidget(footer)

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
        self._schedules_tab.refresh_requested.connect(self.refresh_requested.emit)

        # Queues tab
        self._queues_tab.queue_selected.connect(self.queue_selected.emit)

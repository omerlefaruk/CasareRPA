"""
Fleet Dashboard Dialog for CasareRPA Canvas.

Comprehensive admin dashboard for robot fleet management with robots, jobs,
schedules, analytics, and API keys tabs. Supports multi-tenant filtering
and real-time updates via WebSocketBridge.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    margin_comfortable,
    margin_compact,
    margin_standard,
    set_fixed_size,
    set_margins,
    set_min_size,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS
from casare_rpa.presentation.canvas.ui.dialogs.fleet_tabs import (
    AnalyticsTabWidget,
    ApiKeysTabWidget,
    JobsTabWidget,
    QueuesTabWidget,
    RobotsTabWidget,
    SchedulesTabWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.tenant_selector import (
    TenantSelectorWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.toast import ToastNotification

if TYPE_CHECKING:
    from casare_rpa.domain.orchestrator.entities.robot import Robot


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

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the Fleet Dashboard dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Fleet Management Dashboard")
        set_min_size(self, TOKENS.sizes.dialog_width_xl + TOKENS.sizes.dialog_width_md, TOKENS.sizes.dialog_height_lg + TOKENS.sizes.dialog_height_md)
        self.resize(TOKENS.sizes.window_default_width + TOKENS.sizes.dialog_width_md, TOKENS.sizes.window_default_height + TOKENS.sizes.dialog_height_md)
        self.setModal(False)

        self._current_tenant_id: str | None = None
        self._is_super_admin = False
        self._robots: list[dict[str, Any]] = []

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        self._toast = ToastNotification(self)

        logger.debug("FleetDashboardDialog initialized")

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        margin_none(layout)
        set_spacing(layout, TOKENS.spacing.xs)

        # Header with title and tenant selector
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        set_margins(header_layout, TOKENS.margins.panel_header)

        title = QLabel("Fleet Management Dashboard")
        title.setFont(QFont(TOKENS.fonts.ui, TOKENS.fonts.xl))
        font = title.font()
        font.setWeight(QFont.Weight.Bold)
        title.setFont(font)
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
        header_layout.addWidget(self._connection_status)

        layout.addWidget(header_widget)

        # Main content (sidebar + pages)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        margin_none(content_layout)
        set_spacing(content_layout, TOKENS.spacing.xs)

        self._sidebar = QWidget()
        self._sidebar.setObjectName("fleet_sidebar")
        sidebar_layout = QVBoxLayout(self._sidebar)
        set_margins(sidebar_layout, TOKENS.margins.compact)
        set_spacing(sidebar_layout, TOKENS.spacing.sm)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.tabBar().hide()

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

        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: dict[int, QToolButton] = {}
        self._nav_icon_cache: dict[tuple[str, bool], QIcon] = {}

        nav_items = [
            ("Robots", "robot"),
            ("Jobs", "jobs"),
            ("Schedules", "calendar"),
            ("Queues", "queue"),
            ("API Keys", "key"),
            ("Analytics", "chart"),
        ]

        for index, (label, icon_kind) in enumerate(nav_items):
            btn = QToolButton()
            btn.setObjectName("fleet_nav_btn")
            btn.setText(label)
            btn.setCheckable(True)
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            btn.setIcon(self._get_nav_icon(icon_kind, active=False))
            btn.setIconSize(QSize(TOKENS.sizes.icon_lg, TOKENS.sizes.icon_lg))
            btn.clicked.connect(lambda checked, i=index: self._tabs.setCurrentIndex(i))
            self._nav_group.addButton(btn, index)
            self._nav_buttons[index] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        content_layout.addWidget(self._sidebar)
        content_layout.addWidget(self._tabs, 1)

        layout.addWidget(content_widget)

        # Footer
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        set_margins(footer_layout, TOKENS.margins.statusbar)

        self._status_label = QLabel("Ready")
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
        self._schedules_tab.schedule_enabled_changed.connect(self.schedule_enabled_changed.emit)
        self._schedules_tab.schedule_edited.connect(self.schedule_edited.emit)
        self._schedules_tab.schedule_deleted.connect(self.schedule_deleted.emit)
        self._schedules_tab.schedule_run_now.connect(self.schedule_run_now.emit)
        self._schedules_tab.refresh_requested.connect(self.refresh_requested.emit)

        # Queues tab
        self._queues_tab.queue_selected.connect(self.queue_selected.emit)
        self._queues_tab.queue_created.connect(self.queue_created.emit)
        self._queues_tab.queue_deleted.connect(self.queue_deleted.emit)
        self._queues_tab.queue_item_action.connect(self.queue_item_action.emit)
        self._queues_tab.refresh_requested.connect(self.refresh_requested.emit)

        # API Keys tab
        self._api_keys_tab.api_key_generated.connect(self.api_key_generated.emit)
        self._api_keys_tab.api_key_revoked.connect(self.api_key_revoked.emit)
        self._api_keys_tab.api_key_rotated.connect(self.api_key_rotated.emit)
        self._api_keys_tab.refresh_requested.connect(self.refresh_requested.emit)

        # Analytics tab
        self._analytics_tab.refresh_requested.connect(self.refresh_requested.emit)
        self._analytics_tab.drilldown_requested.connect(self._on_analytics_drilldown)

        # Sidebar/tab sync
        self._tabs.currentChanged.connect(self._on_page_changed)
        self._nav_group.button(0).setChecked(True)
        self._on_page_changed(0)

    def _on_analytics_drilldown(self, target: str, payload: object) -> None:
        del payload
        if target == "robots":
            self._tabs.setCurrentWidget(self._robots_tab)
            return
        if target == "jobs":
            self._tabs.setCurrentWidget(self._jobs_tab)
            return
        if target == "queues":
            self._tabs.setCurrentWidget(self._queues_tab)
            return

    def _apply_styles(self) -> None:
        """Apply custom styles to the dialog."""
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {THEME.bg_darkest};
            }}

            QWidget#header {{
                background: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border};
            }}

            QWidget#footer {{
                background: {THEME.bg_header};
                border-top: 1px solid {THEME.border};
            }}

            QLabel {{
                color: {THEME.text_primary};
            }}

            QWidget#fleet_sidebar {{
                background: {THEME.bg_dark};
                border-right: 1px solid {THEME.border};
                min-width: {TOKENS.sizes.sidebar_width_min}px;
                max-width: {TOKENS.sizes.sidebar_width_default}px;
            }}

            QToolButton#fleet_nav_btn {{
                border: 1px solid transparent;
                border-radius: {TOKENS.radii.menu}px;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                color: {THEME.text_secondary};
                text-align: left;
                font-weight: 600;
            }}

            QToolButton#fleet_nav_btn:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.border_light};
                color: {THEME.text_primary};
            }}

            QToolButton#fleet_nav_btn:checked {{
                background: {THEME.bg_selected};
                border-color: {THEME.accent_primary};
                color: {THEME.text_primary};
            }}

            QPushButton {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.menu}px;
                color: {THEME.text_primary};
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
            """
        )

    def _on_page_changed(self, index: int) -> None:
        btn = self._nav_buttons.get(index)
        if btn is not None:
            btn.setChecked(True)

        nav_items = [
            ("robot", 0),
            ("jobs", 1),
            ("calendar", 2),
            ("queue", 3),
            ("key", 4),
            ("chart", 5),
        ]
        for icon_kind, idx in nav_items:
            b = self._nav_buttons.get(idx)
            if b is None:
                continue
            b.setIcon(self._get_nav_icon(icon_kind, active=(idx == index)))

    def _get_nav_icon(self, kind: str, active: bool) -> QIcon:
        cache_key = (kind, active)
        cached = self._nav_icon_cache.get(cache_key)
        if cached is not None:
            return cached

        size = TOKENS.sizes.icon_lg
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(THEME.accent_primary if active else THEME.text_secondary)
        pen = QPen(color, 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        if kind == "robot":
            # Simple robot: head + body + eyes
            painter.drawRoundedRect(4, 3, 10, 7, 2, 2)
            painter.drawRoundedRect(5, 10, 8, 6, 2, 2)
            painter.drawPoint(7, 6)
            painter.drawPoint(11, 6)
            painter.drawLine(9, 1, 9, 3)
        elif kind == "jobs":
            # List icon
            painter.drawLine(4, 5, 14, 5)
            painter.drawLine(4, 9, 14, 9)
            painter.drawLine(4, 13, 14, 13)
            painter.drawPoint(3, 5)
            painter.drawPoint(3, 9)
            painter.drawPoint(3, 13)
        elif kind == "calendar":
            painter.drawRoundedRect(4, 5, 10, 10, 2, 2)
            painter.drawLine(4, 8, 14, 8)
            painter.drawLine(7, 3, 7, 6)
            painter.drawLine(11, 3, 11, 6)
        elif kind == "queue":
            painter.drawRoundedRect(4, 4, 10, 4, 2, 2)
            painter.drawRoundedRect(4, 9, 10, 4, 2, 2)
            painter.drawRoundedRect(4, 14, 10, 2, 1, 1)
        elif kind == "key":
            painter.drawEllipse(4, 6, 6, 6)
            painter.drawLine(9, 9, 14, 9)
            painter.drawLine(12, 9, 12, 11)
            painter.drawLine(13, 9, 13, 10)
        elif kind == "chart":
            painter.drawLine(4, 14, 14, 14)
            painter.drawLine(5, 13, 5, 10)
            painter.drawLine(9, 13, 9, 7)
            painter.drawLine(13, 13, 13, 5)

        painter.end()

        icon = QIcon(pixmap)
        self._nav_icon_cache[cache_key] = icon
        return icon

    def show_toast(self, message: str, level: str = "info", duration_ms: int = 2500) -> None:
        self._toast.show_toast(message, level=level, duration_ms=duration_ms)

    def set_connection_status(self, connected: bool, message: str) -> None:
        self._connection_status.setText(message)
        color = THEME.status_success if connected else THEME.status_error
        self._connection_status.setStyleSheet(f"color: {color}; font-weight: 700;")

    def set_status(self, message: str) -> None:
        self._status_label.setText(message)

    def set_super_admin(self, is_super_admin: bool) -> None:
        self._is_super_admin = is_super_admin
        self._tenant_selector.set_super_admin(is_super_admin)
        self._update_tenant_selector_visibility()

    def update_tenants(self, tenants: list[dict[str, Any]]) -> None:
        self._tenant_selector.update_tenants(tenants)
        self._update_tenant_selector_visibility(tenant_count=len(tenants))

    def _update_tenant_selector_visibility(self, tenant_count: int | None = None) -> None:
        if tenant_count is None:
            tenant_count = 0
        visible = bool(self._is_super_admin and tenant_count > 1)
        self._tenant_selector.setVisible(visible)

    def update_robots(self, robots: list[Robot]) -> None:
        if hasattr(self._robots_tab, "update_robots"):
            self._robots_tab.update_robots(robots)

    def update_jobs(self, jobs: list[dict[str, Any]]) -> None:
        self._jobs_tab.update_jobs(jobs)

    def update_schedules(self, schedules: list[dict[str, Any]]) -> None:
        self._schedules_tab.update_schedules(schedules)

    def update_queues(self, queues: list[dict[str, Any]]) -> None:
        if hasattr(self._queues_tab, "update_queues"):
            self._queues_tab.update_queues(queues)

    def update_analytics(self, analytics: dict[str, Any]) -> None:
        self._analytics_tab.update_analytics(analytics)

    def update_api_keys_robots(self, robots: list[dict[str, Any]]) -> None:
        self._api_keys_tab.update_robots(robots)

    def update_api_keys(self, api_keys: list[dict[str, Any]]) -> None:
        self._api_keys_tab.update_api_keys(api_keys)

    def _on_tenant_changed(self, tenant_id: str | None) -> None:
        """Handle tenant selection change."""
        self._current_tenant_id = tenant_id
        self.tenant_changed.emit(tenant_id)
        self.refresh_requested.emit()

    def _on_refresh_robots(self) -> None:
        self.refresh_requested.emit()

    def _on_job_selected(self, job_id: str) -> None:
        pass

    def _on_refresh_jobs(self) -> None:
        self.refresh_requested.emit()

    def _on_schedule_selected(self, schedule_id: str) -> None:
        pass

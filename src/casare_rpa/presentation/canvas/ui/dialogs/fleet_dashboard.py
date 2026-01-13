"""
Fleet Dashboard Dialog for CasareRPA Canvas.

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.

Comprehensive admin dashboard for robot fleet management with robots, jobs,
schedules, analytics, and API keys tabs. Supports multi-tenant filtering
and real-time updates via WebSocketBridge.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    margin_comfortable,
    margin_compact,
    margin_none,
    margin_standard,
    set_fixed_size,
    set_margins,
    set_min_size,
    set_spacing,
)
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


from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2


class FleetDashboardDialog(BaseDialogV2):
    """
    Full admin dashboard for robot fleet management.

    Migrated to THEME_V2/TOKENS_V2 (Epic 7.x).

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
        super().__init__(
            title="Fleet Management Dashboard",
            parent=parent,
            size=DialogSizeV2.XL,
            resizable=True,
        )

        self._current_tenant_id: str | None = None
        self._is_super_admin = False
        self._robots: list[dict[str, Any]] = []
        self._toast = ToastNotification(self)
        self._robot_controller = None

        # Content widget
        content = QWidget()
        self._setup_content(content)
        self.set_body_widget(content)

        self._connect_signals()
        self._apply_styles()
        self._wire_robot_controller()

        # Hide default footer since this is a dashboard
        self.set_footer_visible(False)

        logger.debug("FleetDashboardDialog initialized")

    def _setup_content(self, content: QWidget) -> None:
        """Set up the dialog content UI with compact styling."""
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with tenant selector (compact toolbar style)
        header_widget = QWidget()
        header_widget.setObjectName("header")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xs,
        )
        header_layout.setSpacing(TOKENS_V2.spacing.sm)

        header_layout.addWidget(QLabel("Tenant:"))

        # Tenant selector (hidden by default, shown for super admins)
        self._tenant_selector = TenantSelectorWidget(
            show_all_option=True,
            label_text="",
        )
        self._tenant_selector.setVisible(False)
        self._tenant_selector.tenant_changed.connect(self._on_tenant_changed)
        header_layout.addWidget(self._tenant_selector)

        header_layout.addStretch()

        self._connection_status = QLabel("Disconnected")
        header_layout.addWidget(self._connection_status)

        layout.addWidget(header_widget)

        # Main content (sidebar + pages)
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._sidebar = QWidget()
        self._sidebar.setObjectName("fleet_sidebar")
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xs,
        )
        sidebar_layout.setSpacing(TOKENS_V2.spacing.xxs)

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
            btn.setIconSize(QSize(TOKENS_V2.sizes.icon_sm, TOKENS_V2.sizes.icon_sm))
            btn.clicked.connect(partial(self._on_nav_clicked, index))
            self._nav_group.addButton(btn, index)
            self._nav_buttons[index] = btn
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        content_layout.addWidget(self._sidebar)
        content_layout.addWidget(self._tabs, 1)

        layout.addWidget(content_widget, 1)

        # Footer (compact status bar style)
        footer = QWidget()
        footer.setObjectName("footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xxs,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xxs,
        )
        footer_layout.setSpacing(TOKENS_V2.spacing.sm)

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
        self.refresh_requested.connect(self._refresh_robots_from_controller)

    @Slot(bool)
    def _on_nav_clicked(self, index: int, checked: bool = False) -> None:
        del checked
        self._tabs.setCurrentIndex(index)

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

    @Slot(bool)
    def _on_nav_clicked(self, index: int, checked: bool) -> None:
        del checked
        self._tabs.setCurrentIndex(index)

    def _apply_styles(self) -> None:
        """Apply custom styles to the dialog using THEME_V2/TOKENS_V2."""
        t = THEME_V2
        tok = TOKENS_V2

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {t.bg_canvas};
            }}

            QWidget#header {{
                background: {t.bg_header};
                border-bottom: 1px solid {t.border};
            }}

            QWidget#footer {{
                background: {t.bg_header};
                border-top: 1px solid {t.border};
            }}

            QLabel {{
                color: {t.text_primary};
                font-size: {tok.typography.body_sm}px;
            }}

            QWidget#fleet_sidebar {{
                background: {t.bg_surface};
                border-right: 1px solid {t.border};
                min-width: {tok.sizes.panel_min_width}px;
                max-width: {tok.sizes.panel_default_width}px;
            }}

            QToolButton#fleet_nav_btn {{
                border: 1px solid transparent;
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
                color: {t.text_secondary};
                text-align: left;
                font-size: {tok.typography.body_sm}px;
                font-weight: {tok.typography.weight_medium};
            }}

            QToolButton#fleet_nav_btn:hover {{
                background: {t.bg_hover};
                border-color: {t.border};
                color: {t.text_primary};
            }}

            QToolButton#fleet_nav_btn:checked {{
                background: {t.bg_selected};
                border-color: {t.primary};
                color: {t.text_primary};
            }}

            QPushButton {{
                background: {t.bg_surface};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                color: {t.text_primary};
                padding: {tok.spacing.xxs}px {tok.spacing.sm}px;
                font-size: {tok.typography.body_sm}px;
                min-height: {tok.sizes.button_sm}px;
            }}

            QPushButton:hover {{
                background: {t.bg_hover};
                border-color: {t.border_light};
            }}

            QLineEdit, QComboBox {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                color: {t.text_primary};
                padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
                font-size: {tok.typography.body_sm}px;
                min-height: {tok.sizes.input_sm}px;
            }}

            QLineEdit:focus, QComboBox:focus {{
                border-color: {t.border_focus};
            }}

            QComboBox::drop-down {{
                border: none;
                width: {tok.sizes.icon_sm}px;
            }}

            QTableWidget {{
                background: {t.bg_surface};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                gridline-color: {t.border};
                font-size: {tok.typography.body_sm}px;
            }}

            QTableWidget::item {{
                padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
                border: none;
            }}

            QTableWidget::item:selected {{
                background: {t.bg_selected};
                color: {t.text_primary};
            }}

            QHeaderView::section {{
                background: {t.bg_component};
                color: {t.text_secondary};
                border: none;
                border-bottom: 1px solid {t.border};
                padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
                font-size: {tok.typography.caption}px;
                font-weight: {tok.typography.weight_semibold};
            }}

            QScrollBar:vertical {{
                background: {t.scrollbar_bg};
                width: {tok.sizes.scrollbar_width}px;
                border: none;
            }}

            QScrollBar::handle:vertical {{
                background: {t.scrollbar_handle};
                border-radius: {tok.radius.xs}px;
                min-height: {tok.sizes.scrollbar_min_height}px;
            }}

            QScrollBar::handle:vertical:hover {{
                background: {t.scrollbar_hover};
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}

            QScrollBar:horizontal {{
                background: {t.scrollbar_bg};
                height: {tok.sizes.scrollbar_width}px;
                border: none;
            }}

            QScrollBar::handle:horizontal {{
                background: {t.scrollbar_handle};
                border-radius: {tok.radius.xs}px;
                min-width: {tok.sizes.scrollbar_min_height}px;
            }}

            QScrollBar::handle:horizontal:hover {{
                background: {t.scrollbar_hover};
            }}

            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}

            QGroupBox {{
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                margin-top: {tok.spacing.sm}px;
                padding-top: {tok.spacing.sm}px;
                font-size: {tok.typography.body_sm}px;
            }}

            QGroupBox::title {{
                color: {t.text_secondary};
                subcontrol-origin: margin;
                left: {tok.spacing.sm}px;
                padding: 0 {tok.spacing.xs}px;
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

        size = TOKENS_V2.sizes.icon_sm
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(THEME_V2.primary if active else THEME_V2.text_secondary)
        pen = QPen(color, 1.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        # Compact 16x16 icon drawings
        if kind == "robot":
            # Simple robot: head + body
            painter.drawRoundedRect(3, 2, 8, 5, 1, 1)
            painter.drawRoundedRect(4, 7, 6, 5, 1, 1)
            painter.drawPoint(5, 4)
            painter.drawPoint(9, 4)
        elif kind == "jobs":
            # List icon
            painter.drawLine(3, 4, 12, 4)
            painter.drawLine(3, 8, 12, 8)
            painter.drawLine(3, 12, 12, 12)
        elif kind == "calendar":
            painter.drawRoundedRect(3, 4, 9, 8, 1, 1)
            painter.drawLine(3, 7, 12, 7)
            painter.drawLine(5, 2, 5, 5)
            painter.drawLine(9, 2, 9, 5)
        elif kind == "queue":
            painter.drawRoundedRect(3, 3, 9, 3, 1, 1)
            painter.drawRoundedRect(3, 7, 9, 3, 1, 1)
            painter.drawRoundedRect(3, 11, 9, 2, 1, 1)
        elif kind == "key":
            painter.drawEllipse(3, 5, 5, 5)
            painter.drawLine(7, 7, 12, 7)
            painter.drawLine(10, 7, 10, 9)
        elif kind == "chart":
            painter.drawLine(3, 12, 12, 12)
            painter.drawLine(4, 11, 4, 8)
            painter.drawLine(7, 11, 7, 5)
            painter.drawLine(10, 11, 10, 4)

        painter.end()

        icon = QIcon(pixmap)
        self._nav_icon_cache[cache_key] = icon
        return icon

    def show_toast(self, message: str, level: str = "info", duration_ms: int = 2500) -> None:
        self._toast.show_toast(message, level=level, duration_ms=duration_ms)

    def set_connection_status(self, connected: bool, message: str) -> None:
        status = "connected" if connected else "disconnected"
        label = message or ("Connected" if connected else "Disconnected")
        self.set_connection_status_detailed(status, label)

    def set_connection_status_detailed(
        self,
        status: str,
        message: str = "",
        url: str = "",
    ) -> None:
        status_config = {
            "connected": (THEME_V2.success, "Connected"),
            "connecting": (THEME_V2.warning, "Connecting..."),
            "disconnected": (THEME_V2.error, "Disconnected"),
            "error": (THEME_V2.error, "Error"),
        }
        color, label = status_config.get(status, (THEME_V2.error, "Unknown"))
        text = message or label
        tooltip = message or label
        if url:
            tooltip = f"{tooltip} ({url})"
        self._connection_status.setText(text)
        self._connection_status.setToolTip(tooltip)
        self._connection_status.setStyleSheet(
            f"color: {color}; font-weight: {TOKENS_V2.typography.weight_semibold};"
        )

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

    def _wire_robot_controller(self) -> None:
        parent = self.parent()
        controller = None
        if parent is not None and hasattr(parent, "get_robot_controller"):
            try:
                controller = parent.get_robot_controller()
            except Exception as exc:
                logger.debug(f"FleetDashboardDialog: controller lookup failed: {exc}")

        if controller is None:
            logger.debug("FleetDashboardDialog: no robot controller available")
            return

        self._robot_controller = controller
        controller.robots_updated.connect(self.update_robots)
        if hasattr(self._robots_tab, "set_refreshing"):
            controller.refreshing_changed.connect(self._robots_tab.set_refreshing)
        controller.connection_status_detailed.connect(self.set_connection_status_detailed)
        controller.connection_status_changed.connect(self._on_connection_changed)

        orchestrator_url = getattr(controller, "orchestrator_url", None)
        if orchestrator_url:
            status = "connected" if getattr(controller, "is_connected", False) else "disconnected"
            self.set_connection_status_detailed(status, "", orchestrator_url)

        self._refresh_robots_from_controller()

    def _on_connection_changed(self, connected: bool) -> None:
        self.set_connection_status(connected, "")

    def _refresh_robots_from_controller(self) -> None:
        if self._robot_controller is None:
            return
        self._schedule_async(self._robot_controller.refresh_robots())

    @staticmethod
    def _schedule_async(coro) -> None:
        try:
            asyncio.create_task(coro)
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.create_task(coro)

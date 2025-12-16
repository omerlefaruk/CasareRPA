"""
Analytics Panel UI Component.

Provides bottleneck detection and execution analysis views
connected to the Orchestrator REST API.
"""

from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QComboBox,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QTabWidget,
    QTextEdit,
    QGroupBox,
    QSpinBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QThread, QObject
from PySide6.QtGui import QColor, QBrush, QFont

from loguru import logger

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)


class ApiWorker(QObject):
    """Worker for background API calls."""

    finished = Signal(object)  # dict or list
    error = Signal(str)

    def __init__(self, url: str, timeout: float = 5.0) -> None:
        """Initialize worker."""
        super().__init__()
        self.url = url
        self.timeout = timeout

    def run(self) -> None:
        """Execute the API call in background thread."""
        try:
            import urllib.request
            import json

            req = urllib.request.Request(self.url, method="GET")
            req.add_header("Accept", "application/json")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    self.finished.emit(data)
                else:
                    self.error.emit(f"API error {response.status}")
        except Exception as e:
            self.error.emit(str(e))


class AnalyticsPanel(QDockWidget):
    """
    Dockable panel for Analytics connected to Orchestrator API.

    Features:
    - Bottleneck Detection: Identify slow/failing nodes
    - Execution Analysis: Trends, patterns, insights
    - Timeline visualization

    Signals:
        workflow_selected: Emitted when workflow is selected (str: workflow_id)
        bottleneck_clicked: Emitted when bottleneck is clicked (dict: bottleneck_data)
        insight_clicked: Emitted when insight is clicked (dict: insight_data)
    """

    workflow_selected = Signal(str)
    bottleneck_clicked = Signal(dict)
    insight_clicked = Signal(dict)

    def __init__(
        self, parent: Optional[QWidget] = None, embedded: bool = False
    ) -> None:
        """Initialize the analytics panel.

        Args:
            parent: Optional parent widget
            embedded: If True, behave as QWidget (for embedding in tab panels)
        """
        self._embedded = embedded
        if embedded:
            QWidget.__init__(self, parent)
        else:
            super().__init__("Analytics", parent)
            self.setObjectName("AnalyticsDock")

        self._api_base_url = self._get_orchestrator_url()
        self._current_workflow: Optional[str] = None
        self._active_workers: List[tuple] = []  # (thread, worker) pairs

        if not embedded:
            self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._setup_refresh_timer()

        logger.debug(f"AnalyticsPanel initialized with API URL: {self._api_base_url}")

    def _get_orchestrator_url(self) -> str:
        """
        Get orchestrator URL from config or environment.

        Priority:
        1. config.yaml orchestrator.url (tunnel URL)
        2. CASARE_API_URL environment variable (tunnel URL)
        3. ORCHESTRATOR_URL environment variable
        4. CLOUDFLARE_TUNNEL_URL environment variable
        5. Default localhost:8000

        Returns:
            Base API URL for orchestrator
        """
        import os

        # Try config.yaml first (has tunnel URL)
        try:
            from casare_rpa.presentation.setup.config_manager import ClientConfigManager

            config_manager = ClientConfigManager()
            if config_manager.config_exists():
                config = config_manager.load()
                url = config.orchestrator.url
                if url:
                    # Config stores WebSocket URL (ws://), convert to HTTP
                    if url.startswith("ws://"):
                        url = url.replace("ws://", "http://")
                    elif url.startswith("wss://"):
                        url = url.replace("wss://", "https://")
                    logger.debug(f"Analytics using orchestrator URL from config: {url}")
                    return f"{url}/api/v1"
        except Exception as e:
            logger.debug(f"Could not read config.yaml for analytics: {e}")

        # Try CASARE_API_URL first (tunnel URL from platform startup)
        casare_api_url = os.getenv("CASARE_API_URL")
        if casare_api_url:
            logger.debug(f"Analytics using CASARE_API_URL: {casare_api_url}")
            return f"{casare_api_url}/api/v1"

        # Try ORCHESTRATOR_URL
        orchestrator_url = os.getenv("ORCHESTRATOR_URL")
        if orchestrator_url:
            logger.debug(f"Analytics using ORCHESTRATOR_URL: {orchestrator_url}")
            return f"{orchestrator_url}/api/v1"

        # Try CLOUDFLARE_TUNNEL_URL
        tunnel_url = os.getenv("CLOUDFLARE_TUNNEL_URL")
        if tunnel_url:
            logger.debug(f"Analytics using CLOUDFLARE_TUNNEL_URL: {tunnel_url}")
            return f"{tunnel_url}/api/v1"

        # Default fallback
        logger.debug("Analytics using default localhost URL")
        return "http://localhost:8000/api/v1"

    def set_api_url(self, url: str) -> None:
        """
        Set the API base URL dynamically.

        Args:
            url: Base URL for orchestrator (e.g., https://tunnel.example.com)
        """
        base = url.replace("ws://", "http://").replace("wss://", "https://").rstrip("/")
        if base.endswith("/ws"):
            base = base[: -len("/ws")]
        if not base.endswith("/api/v1"):
            base = f"{base}/api/v1"
        self._api_base_url = base
        logger.info(f"Analytics API URL updated to: {base}")

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
        self.setMinimumWidth(400)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        if self._embedded:
            main_layout = QVBoxLayout(self)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Header with workflow selector and API settings
        header = self._create_header()
        main_layout.addLayout(header)

        # API connection status
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("API:"))
        self._api_url_label = QLabel(self._api_base_url)
        self._api_url_label.setStyleSheet(f"color: {THEME.text_muted};")
        api_layout.addWidget(self._api_url_label, 1)
        self._api_status = QLabel("O")
        self._api_status.setStyleSheet(f"color: {THEME.text_muted};")
        self._api_status.setToolTip("API connection status")
        api_layout.addWidget(self._api_status)
        main_layout.addLayout(api_layout)

        # Tab widget
        self._tabs = QTabWidget()

        # Bottlenecks tab
        bottlenecks_tab = self._create_bottlenecks_tab()
        self._tabs.addTab(bottlenecks_tab, "Bottlenecks")

        # Execution Analysis tab
        execution_tab = self._create_execution_tab()
        self._tabs.addTab(execution_tab, "Execution")

        # Timeline tab
        timeline_tab = self._create_timeline_tab()
        self._tabs.addTab(timeline_tab, "Timeline")

        main_layout.addWidget(self._tabs)
        if not self._embedded:
            self.setWidget(container)

    def _create_header(self) -> QHBoxLayout:
        """Create header with workflow selector."""
        layout = QHBoxLayout()
        layout.setSpacing(8)

        # Workflow selector
        workflow_label = QLabel("Workflow:")
        self._workflow_combo = QComboBox()
        self._workflow_combo.setMinimumWidth(150)
        self._workflow_combo.addItem("Select workflow...", None)
        self._workflow_combo.currentIndexChanged.connect(self._on_workflow_changed)

        # Days selector
        days_label = QLabel("Days:")
        self._days_spin = QSpinBox()
        self._days_spin.setRange(1, 90)
        self._days_spin.setValue(7)
        self._days_spin.setFixedWidth(60)

        # Analyze button
        self._analyze_btn = QPushButton("Analyze")
        self._analyze_btn.setFixedWidth(70)
        self._analyze_btn.clicked.connect(self._run_analysis)
        self._analyze_btn.setEnabled(False)

        # Refresh workflows button
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(30)
        refresh_btn.setToolTip("Refresh workflow list")
        refresh_btn.clicked.connect(self._load_workflows)

        layout.addWidget(workflow_label)
        layout.addWidget(self._workflow_combo, 1)
        layout.addWidget(days_label)
        layout.addWidget(self._days_spin)
        layout.addWidget(self._analyze_btn)
        layout.addWidget(refresh_btn)

        return layout

    def _create_bottlenecks_tab(self) -> QWidget:
        """Create bottleneck detection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Summary stats
        summary_group = QGroupBox("Analysis Summary")
        summary_layout = QHBoxLayout(summary_group)

        self._exec_count_label = QLabel("0")
        self._exec_count_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        exec_layout = QVBoxLayout()
        exec_layout.addWidget(
            self._exec_count_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        exec_layout.addWidget(
            QLabel("Executions"), alignment=Qt.AlignmentFlag.AlignCenter
        )

        self._bottleneck_count_label = QLabel("0")
        self._bottleneck_count_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        bn_layout = QVBoxLayout()
        bn_layout.addWidget(
            self._bottleneck_count_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        bn_layout.addWidget(
            QLabel("Bottlenecks"), alignment=Qt.AlignmentFlag.AlignCenter
        )

        self._critical_count_label = QLabel("0")
        self._critical_count_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self._critical_count_label.setStyleSheet(f"color: {THEME.status_error};")
        crit_layout = QVBoxLayout()
        crit_layout.addWidget(
            self._critical_count_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        crit_layout.addWidget(
            QLabel("Critical"), alignment=Qt.AlignmentFlag.AlignCenter
        )

        summary_layout.addLayout(exec_layout)
        summary_layout.addLayout(bn_layout)
        summary_layout.addLayout(crit_layout)
        layout.addWidget(summary_group)

        # Bottlenecks table
        self._bottlenecks_table = QTableWidget()
        self._bottlenecks_table.setColumnCount(5)
        self._bottlenecks_table.setHorizontalHeaderLabels(
            ["Node", "Type", "Severity", "Impact", "Frequency"]
        )
        self._bottlenecks_table.setAlternatingRowColors(True)
        self._bottlenecks_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._bottlenecks_table.itemSelectionChanged.connect(
            self._on_bottleneck_selected
        )

        header = self._bottlenecks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._bottlenecks_table)

        # Detail panel
        detail_group = QGroupBox("Bottleneck Details")
        detail_layout = QVBoxLayout(detail_group)
        self._bottleneck_detail = QTextEdit()
        self._bottleneck_detail.setReadOnly(True)
        self._bottleneck_detail.setMaximumHeight(120)
        self._bottleneck_detail.setPlaceholderText("Select a bottleneck for details...")
        detail_layout.addWidget(self._bottleneck_detail)
        layout.addWidget(detail_group)

        return widget

    def _create_execution_tab(self) -> QWidget:
        """Create execution analysis tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Trends summary
        trends_group = QGroupBox("Trends")
        trends_layout = QHBoxLayout(trends_group)

        # Duration trend
        dur_layout = QVBoxLayout()
        self._duration_trend_label = QLabel("—")
        self._duration_trend_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._duration_trend_icon = QLabel("📊")
        self._duration_trend_icon.setFont(QFont("Segoe UI", 18))
        dur_layout.addWidget(
            self._duration_trend_icon, alignment=Qt.AlignmentFlag.AlignCenter
        )
        dur_layout.addWidget(
            self._duration_trend_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        dur_layout.addWidget(QLabel("Duration"), alignment=Qt.AlignmentFlag.AlignCenter)

        # Success trend
        success_layout = QVBoxLayout()
        self._success_trend_label = QLabel("—")
        self._success_trend_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self._success_trend_icon = QLabel("📊")
        self._success_trend_icon.setFont(QFont("Segoe UI", 18))
        success_layout.addWidget(
            self._success_trend_icon, alignment=Qt.AlignmentFlag.AlignCenter
        )
        success_layout.addWidget(
            self._success_trend_label, alignment=Qt.AlignmentFlag.AlignCenter
        )
        success_layout.addWidget(
            QLabel("Success Rate"), alignment=Qt.AlignmentFlag.AlignCenter
        )

        trends_layout.addLayout(dur_layout)
        trends_layout.addLayout(success_layout)
        layout.addWidget(trends_group)

        # Time distribution
        time_group = QGroupBox("Peak Times")
        time_layout = QHBoxLayout(time_group)
        self._peak_hour_label = QLabel("Hour: —")
        self._peak_day_label = QLabel("Day: —")
        time_layout.addWidget(self._peak_hour_label)
        time_layout.addWidget(self._peak_day_label)
        layout.addWidget(time_group)

        # Insights table
        insights_label = QLabel("Execution Insights:")
        layout.addWidget(insights_label)

        self._insights_table = QTableWidget()
        self._insights_table.setColumnCount(3)
        self._insights_table.setHorizontalHeaderLabels(
            ["Insight", "Type", "Significance"]
        )
        self._insights_table.setAlternatingRowColors(True)
        self._insights_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._insights_table.itemSelectionChanged.connect(self._on_insight_selected)

        header = self._insights_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._insights_table)

        # Insight detail
        self._insight_detail = QTextEdit()
        self._insight_detail.setReadOnly(True)
        self._insight_detail.setMaximumHeight(100)
        self._insight_detail.setPlaceholderText("Select an insight for details...")
        layout.addWidget(self._insight_detail)

        return widget

    def _create_timeline_tab(self) -> QWidget:
        """Create timeline visualization tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)

        # Granularity selector
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Granularity:"))
        self._granularity_combo = QComboBox()
        self._granularity_combo.addItems(["hour", "day"])
        self._granularity_combo.currentTextChanged.connect(self._load_timeline)
        header_layout.addWidget(self._granularity_combo)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Timeline table (simple for now, could be chart later)
        self._timeline_table = QTableWidget()
        self._timeline_table.setColumnCount(5)
        self._timeline_table.setHorizontalHeaderLabels(
            ["Time", "Executions", "Success", "Failures", "Avg Duration"]
        )
        self._timeline_table.setAlternatingRowColors(True)

        header = self._timeline_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 5):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._timeline_table)

        return widget

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling using THEME system."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                color: {THEME.dock_title_text};
                padding: 6px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QGroupBox {{
                background-color: {THEME.bg_header};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
                font-weight: 500;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {THEME.text_secondary};
            }}
            {get_panel_table_stylesheet()}
            QTextEdit {{
                background-color: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border_dark};
                font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
            QLabel {{
                color: {THEME.text_primary};
                background: transparent;
            }}
            QPushButton {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: 4px 12px;
                border-radius: 3px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
            QPushButton:pressed {{
                background-color: {THEME.bg_lighter};
            }}
            QPushButton:disabled {{
                background-color: {THEME.bg_medium};
                color: {THEME.text_disabled};
                border-color: {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            QTabWidget {{
                background-color: {THEME.bg_panel};
                border: none;
            }}
            QTabWidget::pane {{
                background-color: {THEME.bg_panel};
                border: none;
                border-top: 1px solid {THEME.border_dark};
            }}
            QTabBar {{
                background-color: {THEME.bg_header};
            }}
            QTabBar::tab {{
                background-color: {THEME.bg_header};
                color: {THEME.text_muted};
                padding: 8px 16px;
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 11px;
                font-weight: 500;
            }}
            QTabBar::tab:hover {{
                color: {THEME.text_primary};
                background-color: {THEME.bg_hover};
            }}
            QTabBar::tab:selected {{
                color: {THEME.text_primary};
                background-color: {THEME.bg_panel};
                border-bottom: 2px solid {THEME.accent_primary};
            }}
        """)

    def _setup_refresh_timer(self) -> None:
        """Setup auto-refresh timer."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.setInterval(60000)  # 1 minute

    def _run_in_background(
        self, url: str, on_success, on_error=None, timeout: float = 5.0
    ) -> None:
        """Run API call in background thread to avoid UI freeze."""
        thread = QThread()
        worker = ApiWorker(url, timeout=timeout)
        worker.moveToThread(thread)

        # Connect signals
        thread.started.connect(worker.run)
        worker.finished.connect(on_success)
        worker.finished.connect(thread.quit)
        if on_error:
            worker.error.connect(on_error)
        worker.error.connect(thread.quit)

        # Cleanup on finish
        def cleanup():
            try:
                self._active_workers.remove((thread, worker))
            except ValueError:
                pass
            thread.deleteLater()
            worker.deleteLater()

        thread.finished.connect(cleanup)

        # Track and start
        self._active_workers.append((thread, worker))
        thread.start()

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self._refresh_timer.start()
        self._check_api_connection()
        self._load_workflows()

    def hideEvent(self, event) -> None:
        """Handle hide event."""
        super().hideEvent(event)
        self._refresh_timer.stop()

    def _check_api_connection(self) -> None:
        """Check if API is reachable (non-blocking)."""
        url = f"{self._api_base_url.replace('/api/v1', '')}/health"

        def on_success(_):
            self._api_status.setText("O")
            self._api_status.setStyleSheet(f"color: {THEME.status_success};")
            self._api_status.setToolTip("API connected")

        def on_error(err):
            logger.debug(f"API health check failed: {err}")
            self._api_status.setText("O")
            self._api_status.setStyleSheet(f"color: {THEME.status_error};")
            self._api_status.setToolTip("API not reachable")

        self._run_in_background(url, on_success, on_error, timeout=2.0)

    def _load_workflows(self) -> None:
        """Load available workflows from API (non-blocking)."""
        url = f"{self._api_base_url}/analytics/process-mining/workflows"

        def on_success(data):
            current_data = self._workflow_combo.currentData()
            self._workflow_combo.blockSignals(True)
            self._workflow_combo.clear()
            self._workflow_combo.addItem("Select workflow...", None)

            for wf in data:
                wf_id = wf.get("workflow_id", "")
                count = wf.get("trace_count", 0)
                self._workflow_combo.addItem(f"{wf_id} ({count} traces)", wf_id)

            # Restore selection
            if current_data:
                for i in range(self._workflow_combo.count()):
                    if self._workflow_combo.itemData(i) == current_data:
                        self._workflow_combo.setCurrentIndex(i)
                        break

            self._workflow_combo.blockSignals(False)

        def on_error(err):
            logger.debug(f"Failed to load workflows: {err}")

        self._run_in_background(url, on_success, on_error, timeout=5.0)

    def _on_workflow_changed(self, index: int) -> None:
        """Handle workflow selection change."""
        workflow_id = self._workflow_combo.currentData()
        self._current_workflow = workflow_id
        self._analyze_btn.setEnabled(workflow_id is not None)

        if workflow_id:
            self.workflow_selected.emit(workflow_id)

    def _run_analysis(self) -> None:
        """Run full analysis for selected workflow."""
        if not self._current_workflow:
            return

        # Load all three tabs
        self._load_bottlenecks()
        self._load_execution_analysis()
        self._load_timeline()

    def _load_bottlenecks(self) -> None:
        """Load bottleneck analysis from API (non-blocking)."""
        if not self._current_workflow:
            return

        days = self._days_spin.value()
        url = f"{self._api_base_url}/analytics/bottlenecks/{self._current_workflow}?days={days}"

        def on_error(err):
            logger.error(f"Failed to load bottlenecks: {err}")
            self._bottleneck_detail.setText(f"Error loading bottlenecks: {err}")

        self._run_in_background(
            url, self._update_bottlenecks_ui, on_error, timeout=15.0
        )

    def _update_bottlenecks_ui(self, data: Dict[str, Any]) -> None:
        """Update bottlenecks UI with API data."""
        # Update summary
        self._exec_count_label.setText(str(data.get("total_executions", 0)))

        bottlenecks = data.get("bottlenecks", [])
        self._bottleneck_count_label.setText(str(len(bottlenecks)))

        critical_count = sum(1 for b in bottlenecks if b.get("severity") == "critical")
        self._critical_count_label.setText(str(critical_count))

        # Update table
        self._bottlenecks_table.setRowCount(0)
        for bn in bottlenecks:
            row = self._bottlenecks_table.rowCount()
            self._bottlenecks_table.insertRow(row)

            # Node
            node_item = QTableWidgetItem(bn.get("location", ""))
            node_item.setData(Qt.ItemDataRole.UserRole, bn)
            self._bottlenecks_table.setItem(row, 0, node_item)

            # Type
            type_item = QTableWidgetItem(bn.get("type", "").replace("_", " ").title())
            self._bottlenecks_table.setItem(row, 1, type_item)

            # Severity
            severity = bn.get("severity", "low")
            severity_item = QTableWidgetItem(severity.upper())
            severity_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if severity == "critical":
                severity_item.setForeground(QBrush(QColor(THEME.status_error)))
            elif severity == "high":
                severity_item.setForeground(QBrush(QColor(THEME.accent_warning)))
            elif severity == "medium":
                severity_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                severity_item.setForeground(QBrush(QColor(THEME.status_success)))
            self._bottlenecks_table.setItem(row, 2, severity_item)

            # Impact
            impact_ms = bn.get("impact_ms", 0)
            impact_item = QTableWidgetItem(f"{impact_ms / 1000:.1f}s")
            impact_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._bottlenecks_table.setItem(row, 3, impact_item)

            # Frequency
            freq = bn.get("frequency", 0) * 100
            freq_item = QTableWidgetItem(f"{freq:.0f}%")
            freq_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._bottlenecks_table.setItem(row, 4, freq_item)

    def _on_bottleneck_selected(self) -> None:
        """Handle bottleneck selection."""
        items = self._bottlenecks_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        node_item = self._bottlenecks_table.item(row, 0)
        bn = node_item.data(Qt.ItemDataRole.UserRole)

        if bn:
            detail = f"**{bn.get('location', 'Unknown')}**\n\n"
            detail += f"Type: {bn.get('type', '').replace('_', ' ').title()}\n"
            detail += f"Severity: {bn.get('severity', 'unknown').upper()}\n\n"
            detail += f"**Description:**\n{bn.get('description', '')}\n\n"
            detail += f"**Recommendation:**\n{bn.get('recommendation', '')}\n"

            self._bottleneck_detail.setText(detail)
            self.bottleneck_clicked.emit(bn)

    def _load_execution_analysis(self) -> None:
        """Load execution analysis from API (non-blocking)."""
        if not self._current_workflow:
            return

        days = self._days_spin.value()
        url = f"{self._api_base_url}/analytics/execution/{self._current_workflow}?days={days}"

        def on_error(err):
            logger.error(f"Failed to load execution analysis: {err}")
            self._insight_detail.setText(f"Error loading analysis: {err}")

        self._run_in_background(url, self._update_execution_ui, on_error, timeout=15.0)

    def _update_execution_ui(self, data: Dict[str, Any]) -> None:
        """Update execution analysis UI."""
        # Update duration trend
        dur_trend = data.get("duration_trend", {})
        direction = dur_trend.get("direction", "stable")
        change = dur_trend.get("change_percent", 0)

        if direction == "improving":
            self._duration_trend_icon.setText("v")
            self._duration_trend_label.setText(f"{change:+.1f}%")
            self._duration_trend_label.setStyleSheet(f"color: {THEME.status_success};")
        elif direction == "degrading":
            self._duration_trend_icon.setText("^")
            self._duration_trend_label.setText(f"{change:+.1f}%")
            self._duration_trend_label.setStyleSheet(f"color: {THEME.status_error};")
        else:
            self._duration_trend_icon.setText("-")
            self._duration_trend_label.setText("Stable")
            self._duration_trend_label.setStyleSheet(f"color: {THEME.status_warning};")

        # Update success trend
        success_trend = data.get("success_rate_trend", {})
        direction = success_trend.get("direction", "stable")
        change = success_trend.get("change_percent", 0)

        if direction == "improving":
            self._success_trend_icon.setText("^")
            self._success_trend_label.setText(f"{change:+.1f}%")
            self._success_trend_label.setStyleSheet(f"color: {THEME.status_success};")
        elif direction == "degrading":
            self._success_trend_icon.setText("v")
            self._success_trend_label.setText(f"{change:+.1f}%")
            self._success_trend_label.setStyleSheet(f"color: {THEME.status_error};")
        else:
            self._success_trend_icon.setText("-")
            self._success_trend_label.setText("Stable")
            self._success_trend_label.setStyleSheet(f"color: {THEME.status_warning};")

        # Update time distribution
        time_dist = data.get("time_distribution", {})
        peak_hour = time_dist.get("peak_hour", 0)
        peak_day = time_dist.get("peak_day", 0)
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self._peak_hour_label.setText(f"Peak Hour: {peak_hour}:00")
        self._peak_day_label.setText(f"Peak Day: {day_names[peak_day]}")

        # Update insights table
        self._insights_table.setRowCount(0)
        for insight in data.get("insights", []):
            row = self._insights_table.rowCount()
            self._insights_table.insertRow(row)

            # Title
            title_item = QTableWidgetItem(insight.get("title", ""))
            title_item.setData(Qt.ItemDataRole.UserRole, insight)
            self._insights_table.setItem(row, 0, title_item)

            # Type
            type_item = QTableWidgetItem(
                insight.get("type", "").replace("_", " ").title()
            )
            self._insights_table.setItem(row, 1, type_item)

            # Significance
            sig = insight.get("significance", 0) * 100
            sig_item = QTableWidgetItem(f"{sig:.0f}%")
            sig_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if sig >= 80:
                sig_item.setForeground(QBrush(QColor(THEME.status_error)))
            elif sig >= 50:
                sig_item.setForeground(QBrush(QColor(THEME.status_warning)))
            else:
                sig_item.setForeground(QBrush(QColor(THEME.status_success)))
            self._insights_table.setItem(row, 2, sig_item)

    def _on_insight_selected(self) -> None:
        """Handle insight selection."""
        items = self._insights_table.selectedItems()
        if not items:
            return

        row = items[0].row()
        title_item = self._insights_table.item(row, 0)
        insight = title_item.data(Qt.ItemDataRole.UserRole)

        if insight:
            detail = f"**{insight.get('title', '')}**\n\n"
            detail += f"{insight.get('description', '')}\n\n"
            if insight.get("recommended_action"):
                detail += (
                    f"**Recommended Action:**\n{insight.get('recommended_action')}\n"
                )

            self._insight_detail.setText(detail)
            self.insight_clicked.emit(insight)

    def _load_timeline(self) -> None:
        """Load timeline data from API (non-blocking)."""
        if not self._current_workflow:
            return

        days = self._days_spin.value()
        granularity = self._granularity_combo.currentText()
        url = f"{self._api_base_url}/analytics/execution/{self._current_workflow}/timeline?days={days}&granularity={granularity}"

        def on_error(err):
            logger.error(f"Failed to load timeline: {err}")

        self._run_in_background(url, self._update_timeline_ui, on_error, timeout=15.0)

    def _update_timeline_ui(self, data: Dict[str, Any]) -> None:
        """Update timeline table."""
        self._timeline_table.setRowCount(0)

        for point in data.get("data_points", []):
            row = self._timeline_table.rowCount()
            self._timeline_table.insertRow(row)

            # Time
            time_item = QTableWidgetItem(point.get("timestamp", ""))
            self._timeline_table.setItem(row, 0, time_item)

            # Executions
            exec_item = QTableWidgetItem(str(point.get("executions", 0)))
            exec_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._timeline_table.setItem(row, 1, exec_item)

            # Success
            success_item = QTableWidgetItem(str(point.get("successes", 0)))
            success_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            success_item.setForeground(QBrush(QColor(THEME.status_success)))
            self._timeline_table.setItem(row, 2, success_item)

            # Failures
            fail_item = QTableWidgetItem(str(point.get("failures", 0)))
            fail_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if point.get("failures", 0) > 0:
                fail_item.setForeground(QBrush(QColor(THEME.status_error)))
            self._timeline_table.setItem(row, 3, fail_item)

            # Avg duration
            duration = point.get("avg_duration_ms", 0) / 1000
            dur_item = QTableWidgetItem(f"{duration:.1f}s")
            dur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._timeline_table.setItem(row, 4, dur_item)

    def _auto_refresh(self) -> None:
        """Auto-refresh data."""
        if self.isVisible() and self._current_workflow:
            self._check_api_connection()
            self._run_analysis()

    def cleanup(self) -> None:
        """Clean up resources."""
        self._refresh_timer.stop()

        # Stop all active workers
        for thread, worker in self._active_workers[:]:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)
            thread.deleteLater()
            worker.deleteLater()
        self._active_workers.clear()

        logger.debug("AnalyticsPanel cleaned up")

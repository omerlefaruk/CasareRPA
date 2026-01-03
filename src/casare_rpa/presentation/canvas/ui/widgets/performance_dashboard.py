"""
Performance Dashboard for CasareRPA Canvas.

Displays real-time performance metrics including:
- System resources (CPU, memory)
- Node execution statistics
- Workflow execution timing
- Connection pool metrics
- Cache hit rates
"""

from datetime import datetime
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.utils.performance.performance_metrics import get_metrics


class MetricCard(QFrame):
    """A card widget displaying a single metric with label and value."""

    def __init__(
        self,
        title: str,
        value: str = "0",
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setMinimumWidth(150)
        self.setMaximumHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.value_label)

        # Subtitle
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(f"color: {THEME.text_disabled}; font-size: 10px;")
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str, subtitle: str = "") -> None:
        """Update the displayed value."""
        self.value_label.setText(value)
        if subtitle:
            self.subtitle_label.setText(subtitle)

    def set_color(self, color: str) -> None:
        """Set the value text color."""
        self.value_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")


class HistogramWidget(QWidget):
    """Widget displaying a histogram with percentile bars."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Percentile labels
        self.percentile_layout = QGridLayout()
        layout.addLayout(self.percentile_layout)

        self._bars: dict[str, QProgressBar] = {}
        self._labels: dict[str, QLabel] = {}

        # Create percentile bars
        percentiles = [("p50", "Median"), ("p90", "p90"), ("p99", "p99")]
        for i, (key, label) in enumerate(percentiles):
            lbl = QLabel(f"{label}:")
            lbl.setStyleSheet("font-size: 11px;")
            self.percentile_layout.addWidget(lbl, i, 0)

            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(100)
            bar.setTextVisible(True)
            bar.setFormat("%v ms")
            bar.setMaximumHeight(20)
            self.percentile_layout.addWidget(bar, i, 1)

            value_lbl = QLabel("0 ms")
            value_lbl.setStyleSheet("font-size: 11px; min-width: 60px;")
            value_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.percentile_layout.addWidget(value_lbl, i, 2)

            self._bars[key] = bar
            self._labels[key] = value_lbl

    def update_data(self, histogram_data: dict[str, Any]) -> None:
        """Update the histogram display."""
        if not histogram_data:
            return

        # Get max value for scaling (handle None values)
        p99 = histogram_data.get("p99") or 0
        max_raw = histogram_data.get("max") or 0
        max_val = max(p99, max_raw, 1)

        for key in ["p50", "p90", "p99"]:
            value = histogram_data.get(key) or 0
            if key in self._bars:
                # Scale to percentage of max
                scaled = int((value / max_val) * 100) if max_val > 0 else 0
                self._bars[key].setValue(scaled)
                self._bars[key].setFormat(f"{value:.1f} ms")
                self._labels[key].setText(f"{value:.1f} ms")


class SystemMetricsPanel(QGroupBox):
    """Panel displaying system resource metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("System Resources", parent)
        layout = QGridLayout(self)

        # CPU card
        self.cpu_card = MetricCard("CPU Usage", "0%", "Process CPU")
        layout.addWidget(self.cpu_card, 0, 0)

        # Memory card
        self.memory_card = MetricCard("Memory", "0 MB", "RSS Memory")
        layout.addWidget(self.memory_card, 0, 1)

        # Threads card
        self.threads_card = MetricCard("Threads", "0", "Active threads")
        layout.addWidget(self.threads_card, 0, 2)

        # GC card
        self.gc_card = MetricCard("GC Objects", "0", "Python objects")
        layout.addWidget(self.gc_card, 0, 3)

        # CPU Progress bar
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setMinimum(0)
        self.cpu_bar.setMaximum(100)
        self.cpu_bar.setTextVisible(True)
        self.cpu_bar.setFormat("CPU: %p%")
        layout.addWidget(self.cpu_bar, 1, 0, 1, 2)

        # Memory Progress bar
        self.memory_bar = QProgressBar()
        self.memory_bar.setMinimum(0)
        self.memory_bar.setMaximum(100)
        self.memory_bar.setTextVisible(True)
        self.memory_bar.setFormat("Memory: %p%")
        layout.addWidget(self.memory_bar, 1, 2, 1, 2)

    def update_metrics(self, system_data: dict[str, Any]) -> None:
        """Update system metrics display."""
        if not system_data:
            return

        current = system_data.get("current", {})

        # CPU
        cpu_percent = current.get("cpu_percent", 0)
        self.cpu_card.set_value(f"{cpu_percent:.1f}%")
        self.cpu_bar.setValue(int(cpu_percent))
        if cpu_percent > 80:
            self.cpu_card.set_color(THEME.error)
        elif cpu_percent > 50:
            self.cpu_card.set_color(THEME.warning)
        else:
            self.cpu_card.set_color(THEME.success)

        # Memory
        memory_mb = current.get("memory_rss_mb", 0)
        self.memory_card.set_value(f"{memory_mb:.0f} MB")
        system_mem_percent = current.get("system_memory_percent", 0)
        self.memory_bar.setValue(int(system_mem_percent))
        self.memory_card.subtitle_label.setText(f"System: {system_mem_percent:.0f}%")

        # Threads
        threads = current.get("cpu_threads", 0)
        self.threads_card.set_value(str(threads))

        # GC
        gc_objects = current.get("gc_objects", 0)
        self.gc_card.set_value(f"{gc_objects:,}")


class NodeMetricsPanel(QGroupBox):
    """Panel displaying node execution metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Node Execution", parent)
        layout = QVBoxLayout(self)

        # Summary cards
        cards_layout = QHBoxLayout()
        self.total_card = MetricCard("Total Nodes", "0", "Executed")
        cards_layout.addWidget(self.total_card)

        self.success_card = MetricCard("Successful", "0", "Completed")
        cards_layout.addWidget(self.success_card)

        self.error_card = MetricCard("Errors", "0", "Failed")
        cards_layout.addWidget(self.error_card)

        self.avg_time_card = MetricCard("Avg Time", "0 ms", "Per node")
        cards_layout.addWidget(self.avg_time_card)

        layout.addLayout(cards_layout)

        # Node table
        self.node_table = QTableWidget()
        self.node_table.setColumnCount(6)
        self.node_table.setHorizontalHeaderLabels(
            ["Node Type", "Count", "Errors", "Avg (ms)", "p90 (ms)", "p99 (ms)"]
        )
        self.node_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.node_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.node_table.setAlternatingRowColors(True)
        self.node_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.node_table)

    def update_metrics(self, node_data: dict[str, Any]) -> None:
        """Update node metrics display."""
        if not node_data:
            return

        # Calculate totals
        total_count = sum(v.get("count", 0) for v in node_data.values())
        total_errors = sum(v.get("errors", 0) for v in node_data.values())

        self.total_card.set_value(str(total_count))
        self.success_card.set_value(str(total_count - total_errors))
        self.error_card.set_value(str(total_errors))
        if total_errors > 0:
            self.error_card.set_color(THEME.error)
        else:
            self.error_card.set_color(THEME.success)

        # Calculate average time
        total_time = 0
        total_with_timing = 0
        for v in node_data.values():
            timing = v.get("timing", {})
            if timing and timing.get("count", 0) > 0:
                total_time += timing.get("sum", 0)
                total_with_timing += timing.get("count", 0)

        avg_time = total_time / total_with_timing if total_with_timing > 0 else 0
        self.avg_time_card.set_value(f"{avg_time:.1f} ms")

        # Update table
        self.node_table.setRowCount(len(node_data))
        for i, (node_type, data) in enumerate(sorted(node_data.items())):
            timing = data.get("timing", {})

            self.node_table.setItem(i, 0, QTableWidgetItem(node_type))
            self.node_table.setItem(i, 1, QTableWidgetItem(str(data.get("count", 0))))

            error_item = QTableWidgetItem(str(data.get("errors", 0)))
            if data.get("errors", 0) > 0:
                error_item.setForeground(QColor(THEME.error))
            self.node_table.setItem(i, 2, error_item)

            self.node_table.setItem(
                i,
                3,
                QTableWidgetItem(f"{timing.get('mean', 0):.1f}" if timing else "-"),
            )
            self.node_table.setItem(
                i, 4, QTableWidgetItem(f"{timing.get('p90', 0):.1f}" if timing else "-")
            )
            self.node_table.setItem(
                i, 5, QTableWidgetItem(f"{timing.get('p99', 0):.1f}" if timing else "-")
            )


class WorkflowMetricsPanel(QGroupBox):
    """Panel displaying workflow execution metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Workflow Execution", parent)
        layout = QVBoxLayout(self)

        # Summary cards
        cards_layout = QHBoxLayout()

        self.started_card = MetricCard("Started", "0", "Workflows")
        cards_layout.addWidget(self.started_card)

        self.completed_card = MetricCard("Completed", "0", "Successful")
        cards_layout.addWidget(self.completed_card)

        self.failed_card = MetricCard("Failed", "0", "With errors")
        cards_layout.addWidget(self.failed_card)

        self.success_rate_card = MetricCard("Success Rate", "0%", "Completion")
        cards_layout.addWidget(self.success_rate_card)

        layout.addLayout(cards_layout)

        # Timing histogram
        timing_group = QGroupBox("Execution Timing")
        timing_layout = QVBoxLayout(timing_group)

        self.histogram_widget = HistogramWidget()
        timing_layout.addWidget(self.histogram_widget)

        # Stats row
        stats_layout = QHBoxLayout()
        self.min_label = QLabel("Min: - ms")
        self.max_label = QLabel("Max: - ms")
        self.mean_label = QLabel("Mean: - ms")
        self.count_label = QLabel("Samples: 0")

        for lbl in [self.min_label, self.max_label, self.mean_label, self.count_label]:
            lbl.setStyleSheet(f"font-size: 11px; color: {THEME.text_disabled};")
            stats_layout.addWidget(lbl)

        timing_layout.addLayout(stats_layout)
        layout.addWidget(timing_group)

    def update_metrics(self, workflow_data: dict[str, Any]) -> None:
        """Update workflow metrics display."""
        if not workflow_data:
            return

        counts = workflow_data.get("counts", {})
        timings = workflow_data.get("timings", {})

        started = counts.get("started", 0)
        completed = counts.get("completed", 0)
        failed = counts.get("failed", 0)

        self.started_card.set_value(str(started))
        self.completed_card.set_value(str(completed))
        self.failed_card.set_value(str(failed))

        if failed > 0:
            self.failed_card.set_color(THEME.error)
        else:
            self.failed_card.set_color(THEME.success)

        # Success rate
        if started > 0:
            rate = (completed / started) * 100
            self.success_rate_card.set_value(f"{rate:.1f}%")
            if rate >= 90:
                self.success_rate_card.set_color(THEME.success)
            elif rate >= 70:
                self.success_rate_card.set_color(THEME.warning)
            else:
                self.success_rate_card.set_color(THEME.error)

        # Update histogram
        if timings:
            self.histogram_widget.update_data(timings)

            self.min_label.setText(f"Min: {timings.get('min') or 0:.1f} ms")
            self.max_label.setText(f"Max: {timings.get('max') or 0:.1f} ms")
            self.mean_label.setText(f"Mean: {timings.get('mean') or 0:.1f} ms")
            self.count_label.setText(f"Samples: {timings.get('count') or 0}")


class PoolMetricsPanel(QGroupBox):
    """Panel displaying connection pool metrics."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Connection Pools", parent)
        layout = QVBoxLayout(self)

        # Pool table
        self.pool_table = QTableWidget()
        self.pool_table.setColumnCount(7)
        self.pool_table.setHorizontalHeaderLabels(
            ["Pool", "Type", "Available", "In Use", "Created", "Closed", "Errors"]
        )
        self.pool_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.pool_table.setAlternatingRowColors(True)
        layout.addWidget(self.pool_table)

    def update_metrics(self, pool_data: dict[str, dict[str, Any]]) -> None:
        """Update pool metrics display."""
        if not pool_data:
            self.pool_table.setRowCount(0)
            return

        self.pool_table.setRowCount(len(pool_data))
        for i, (pool_name, data) in enumerate(pool_data.items()):
            self.pool_table.setItem(i, 0, QTableWidgetItem(pool_name))
            self.pool_table.setItem(
                i, 1, QTableWidgetItem(data.get("db_type", data.get("type", "http")))
            )
            self.pool_table.setItem(i, 2, QTableWidgetItem(str(data.get("available", 0))))
            self.pool_table.setItem(i, 3, QTableWidgetItem(str(data.get("in_use", 0))))
            self.pool_table.setItem(
                i,
                4,
                QTableWidgetItem(
                    str(data.get("connections_created", data.get("sessions_created", 0)))
                ),
            )
            self.pool_table.setItem(
                i,
                5,
                QTableWidgetItem(
                    str(data.get("connections_closed", data.get("sessions_closed", 0)))
                ),
            )
            self.pool_table.setItem(i, 6, QTableWidgetItem(str(data.get("errors", 0))))


class CountersGaugesPanel(QGroupBox):
    """Panel displaying raw counters and gauges."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Counters & Gauges", parent)
        layout = QHBoxLayout(self)

        # Counters table
        counters_group = QGroupBox("Counters")
        counters_layout = QVBoxLayout(counters_group)
        self.counters_table = QTableWidget()
        self.counters_table.setColumnCount(2)
        self.counters_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.counters_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.counters_table.setAlternatingRowColors(True)
        counters_layout.addWidget(self.counters_table)
        layout.addWidget(counters_group)

        # Gauges table
        gauges_group = QGroupBox("Gauges")
        gauges_layout = QVBoxLayout(gauges_group)
        self.gauges_table = QTableWidget()
        self.gauges_table.setColumnCount(2)
        self.gauges_table.setHorizontalHeaderLabels(["Name", "Value"])
        self.gauges_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.gauges_table.setAlternatingRowColors(True)
        gauges_layout.addWidget(self.gauges_table)
        layout.addWidget(gauges_group)

    def update_metrics(self, counters: dict[str, int], gauges: dict[str, float]) -> None:
        """Update counters and gauges display."""
        # Update counters
        self.counters_table.setRowCount(len(counters))
        for i, (name, value) in enumerate(sorted(counters.items())):
            self.counters_table.setItem(i, 0, QTableWidgetItem(name))
            self.counters_table.setItem(i, 1, QTableWidgetItem(str(value)))

        # Update gauges
        self.gauges_table.setRowCount(len(gauges))
        for i, (name, value) in enumerate(sorted(gauges.items())):
            self.gauges_table.setItem(i, 0, QTableWidgetItem(name))
            self.gauges_table.setItem(i, 1, QTableWidgetItem(f"{value:.2f}"))


class PerformanceDashboardDialog(QDialog):
    """
    Performance Dashboard Dialog.

    Displays comprehensive performance metrics with live updates.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Performance Dashboard")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)

        self._metrics = get_metrics()
        self._pool_callbacks: list[Any] = []
        self._refresh_timer: QTimer | None = None

        self._setup_ui()
        self._connect_signals()
        self._start_refresh()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header with controls
        header_layout = QHBoxLayout()

        title = QLabel("Performance Dashboard")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Refresh interval
        header_layout.addWidget(QLabel("Refresh:"))
        self.refresh_combo = QComboBox()
        self.refresh_combo.addItems(["1s", "2s", "5s", "10s", "Manual"])
        self.refresh_combo.setCurrentIndex(1)  # 2s default
        header_layout.addWidget(self.refresh_combo)

        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        header_layout.addWidget(self.auto_scroll_check)

        # Manual refresh button
        self.refresh_btn = QPushButton("Refresh Now")
        header_layout.addWidget(self.refresh_btn)

        # Reset button
        self.reset_btn = QPushButton("Reset Metrics")
        self.reset_btn.setStyleSheet(f"color: {THEME.error};")
        header_layout.addWidget(self.reset_btn)

        layout.addLayout(header_layout)

        # Last updated label
        self.last_updated_label = QLabel("Last updated: Never")
        self.last_updated_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        layout.addWidget(self.last_updated_label)

        # Tab widget for different metric views
        self.tab_widget = QTabWidget()

        # Overview tab
        overview_widget = QWidget()
        overview_layout = QVBoxLayout(overview_widget)

        # System metrics
        self.system_panel = SystemMetricsPanel()
        overview_layout.addWidget(self.system_panel)

        # Workflow metrics
        self.workflow_panel = WorkflowMetricsPanel()
        overview_layout.addWidget(self.workflow_panel)

        self.tab_widget.addTab(overview_widget, "Overview")

        # Nodes tab
        nodes_widget = QWidget()
        nodes_layout = QVBoxLayout(nodes_widget)
        self.nodes_panel = NodeMetricsPanel()
        nodes_layout.addWidget(self.nodes_panel)
        self.tab_widget.addTab(nodes_widget, "Nodes")

        # Pools tab
        pools_widget = QWidget()
        pools_layout = QVBoxLayout(pools_widget)
        self.pools_panel = PoolMetricsPanel()
        pools_layout.addWidget(self.pools_panel)
        self.tab_widget.addTab(pools_widget, "Pools")

        # Raw metrics tab
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        self.raw_panel = CountersGaugesPanel()
        raw_layout.addWidget(self.raw_panel)
        self.tab_widget.addTab(raw_widget, "Raw Metrics")

        layout.addWidget(self.tab_widget)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {THEME.text_secondary};")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        status_layout.addWidget(close_btn)

        layout.addLayout(status_layout)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.refresh_btn.clicked.connect(self._refresh_metrics)
        self.reset_btn.clicked.connect(self._reset_metrics)
        self.refresh_combo.currentTextChanged.connect(self._update_refresh_interval)

    def _start_refresh(self) -> None:
        """Start the auto-refresh timer."""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_metrics)
        self._update_refresh_interval(self.refresh_combo.currentText())
        self._refresh_metrics()  # Initial refresh

    def _update_refresh_interval(self, interval_text: str) -> None:
        """Update the refresh timer interval."""
        if self._refresh_timer is None:
            return

        if interval_text == "Manual":
            self._refresh_timer.stop()
        else:
            interval_ms = {
                "1s": 1000,
                "2s": 2000,
                "5s": 5000,
                "10s": 10000,
            }.get(interval_text, 2000)
            self._refresh_timer.start(interval_ms)

    def _refresh_metrics(self) -> None:
        """Start background refresh of all metrics displays."""
        # Use QTimer.singleShot with a very short delay to run in background
        # This prevents freezing by batching the data collection
        from concurrent.futures import ThreadPoolExecutor

        from PySide6.QtCore import QTimer as QT
        
        self.status_label.setText("Refreshing...")
        
        # Run data collection in thread pool
        def collect_data():
            """Collect all metrics data in background thread."""
            try:
                data = {
                    "summary": self._metrics.get_summary(),
                    "system_stats": self._metrics.get_system_stats(),
                    "node_stats": self._metrics.get_node_stats(),
                    "pool_data": self._collect_pool_metrics(),
                }
                return data
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                return None
        
        def on_data_ready(future):
            """Update UI with collected data (runs in main thread via singleShot)."""
            def update_ui():
                try:
                    data = future.result()
                    if data is None:
                        self.status_label.setText("Error refreshing metrics")
                        return
                    
                    summary = data["summary"]
                    
                    # Update system metrics
                    self.system_panel.update_metrics(data["system_stats"])
                    
                    # Update workflow metrics
                    self.workflow_panel.update_metrics(summary.get("workflows", {}))
                    
                    # Update node metrics
                    self.nodes_panel.update_metrics(data["node_stats"])
                    
                    # Update pool metrics
                    self.pools_panel.update_metrics(data["pool_data"])
                    
                    # Update raw metrics
                    self.raw_panel.update_metrics(
                        summary.get("counters", {}), 
                        summary.get("gauges", {})
                    )
                    
                    # Update timestamp
                    self.last_updated_label.setText(
                        f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    self.status_label.setText("Metrics refreshed")
                    
                except Exception as e:
                    logger.error(f"Error updating metrics UI: {e}")
                    self.status_label.setText(f"Error: {str(e)}")
            
            # Schedule UI update in main thread
            QT.singleShot(0, update_ui)
        
        # Submit to thread pool
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(collect_data)
        future.add_done_callback(on_data_ready)
        # Don't wait for executor - let it run in background
        executor.shutdown(wait=False)

    def _collect_pool_metrics(self) -> dict[str, dict[str, Any]]:
        """Collect metrics from all registered pool sources."""
        pool_data: dict[str, dict[str, Any]] = {}

        # Try to get browser pool stats
        try:
            from ...utils.browser_pool import BrowserPoolManager

            manager = getattr(BrowserPoolManager, "_instance", None)
            if manager and hasattr(manager, "get_all_stats"):
                for name, data in manager.get_all_stats().items():
                    pool_data[f"browser_{name}"] = data
        except Exception:
            pass

        # Try to get database pool stats
        try:
            from ...utils.database_pool import DatabasePoolManager

            manager = getattr(DatabasePoolManager, "_instance", None)
            if manager and hasattr(manager, "get_all_stats"):
                for name, data in manager.get_all_stats().items():
                    pool_data[f"db_{name}"] = data
        except Exception:
            pass

        # Try to get HTTP session pool stats
        try:
            from ...utils.http_session_pool import HttpSessionManager

            manager = getattr(HttpSessionManager, "_instance", None)
            if manager and hasattr(manager, "get_all_stats"):
                for name, data in manager.get_all_stats().items():
                    pool_data[f"http_{name}"] = data
        except Exception:
            pass

        return pool_data

    def _reset_metrics(self) -> None:
        """Reset all metrics."""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "Reset Metrics",
            "Are you sure you want to reset all performance metrics?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._metrics.reset()
            self._refresh_metrics()
            self.status_label.setText("Metrics reset")

    def register_pool_callback(self, callback) -> None:
        """Register a callback for collecting pool metrics."""
        self._pool_callbacks.append(callback)

    def closeEvent(self, event) -> None:
        """Handle dialog close."""
        if self._refresh_timer:
            self._refresh_timer.stop()
        super().closeEvent(event)


def show_performance_dashboard(parent: QWidget | None = None) -> None:
    """Show the performance dashboard dialog."""
    dialog = PerformanceDashboardDialog(parent)
    dialog.exec()


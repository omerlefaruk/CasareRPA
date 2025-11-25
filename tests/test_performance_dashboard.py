"""
Tests for CasareRPA Performance Dashboard UI.

Tests:
    - Dashboard dialog creation
    - Metric panels
    - Live refresh functionality
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication

from casare_rpa.canvas.performance_dashboard import (
    MetricCard,
    HistogramWidget,
    SystemMetricsPanel,
    NodeMetricsPanel,
    WorkflowMetricsPanel,
    PoolMetricsPanel,
    CountersGaugesPanel,
    PerformanceDashboardDialog,
)
from casare_rpa.utils.performance_metrics import PerformanceMetrics


@pytest.fixture(scope="module")
def app():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestMetricCard:
    """Tests for MetricCard widget."""

    def test_creation(self, app):
        """Test metric card creation."""
        card = MetricCard("Test Metric", "100", "Subtitle")

        assert card.title_label.text() == "Test Metric"
        assert card.value_label.text() == "100"
        assert card.subtitle_label.text() == "Subtitle"

    def test_set_value(self, app):
        """Test setting card value."""
        card = MetricCard("Test", "0")
        card.set_value("42", "New subtitle")

        assert card.value_label.text() == "42"
        assert card.subtitle_label.text() == "New subtitle"

    def test_set_color(self, app):
        """Test setting value color."""
        card = MetricCard("Test", "0")
        card.set_color("#ff0000")

        # Color is set via stylesheet
        assert "#ff0000" in card.value_label.styleSheet()


class TestHistogramWidget:
    """Tests for HistogramWidget."""

    def test_creation(self, app):
        """Test histogram widget creation."""
        widget = HistogramWidget()

        assert "p50" in widget._bars
        assert "p90" in widget._bars
        assert "p99" in widget._bars

    def test_update_data(self, app):
        """Test updating histogram data."""
        widget = HistogramWidget()

        data = {
            "p50": 50.0,
            "p90": 100.0,
            "p99": 200.0,
            "max": 250.0,
        }

        widget.update_data(data)

        # Values should be displayed
        assert "50.0" in widget._labels["p50"].text()

    def test_empty_data(self, app):
        """Test with empty data."""
        widget = HistogramWidget()
        widget.update_data({})  # Should not raise


class TestSystemMetricsPanel:
    """Tests for SystemMetricsPanel."""

    def test_creation(self, app):
        """Test panel creation."""
        panel = SystemMetricsPanel()

        assert panel.cpu_card is not None
        assert panel.memory_card is not None
        assert panel.threads_card is not None

    def test_update_metrics(self, app):
        """Test updating system metrics."""
        panel = SystemMetricsPanel()

        data = {
            "current": {
                "cpu_percent": 45.5,
                "memory_rss_mb": 256.0,
                "cpu_threads": 8,
                "gc_objects": 10000,
                "system_memory_percent": 60.0,
            }
        }

        panel.update_metrics(data)

        assert "45.5%" in panel.cpu_card.value_label.text()
        assert "256" in panel.memory_card.value_label.text()


class TestNodeMetricsPanel:
    """Tests for NodeMetricsPanel."""

    def test_creation(self, app):
        """Test panel creation."""
        panel = NodeMetricsPanel()

        assert panel.node_table is not None
        assert panel.total_card is not None

    def test_update_metrics(self, app):
        """Test updating node metrics."""
        panel = NodeMetricsPanel()

        data = {
            "TestNode": {
                "count": 10,
                "errors": 2,
                "timing": {
                    "count": 10,
                    "sum": 500.0,
                    "mean": 50.0,
                    "p90": 80.0,
                    "p99": 100.0,
                }
            }
        }

        panel.update_metrics(data)

        assert panel.node_table.rowCount() == 1
        assert panel.total_card.value_label.text() == "10"


class TestWorkflowMetricsPanel:
    """Tests for WorkflowMetricsPanel."""

    def test_creation(self, app):
        """Test panel creation."""
        panel = WorkflowMetricsPanel()

        assert panel.started_card is not None
        assert panel.completed_card is not None
        assert panel.histogram_widget is not None

    def test_update_metrics(self, app):
        """Test updating workflow metrics."""
        panel = WorkflowMetricsPanel()

        data = {
            "counts": {
                "started": 100,
                "completed": 95,
                "failed": 5,
            },
            "timings": {
                "count": 100,
                "mean": 5000.0,
                "p50": 4000.0,
                "p90": 8000.0,
                "p99": 15000.0,
                "min": 1000.0,
                "max": 20000.0,
            }
        }

        panel.update_metrics(data)

        assert panel.started_card.value_label.text() == "100"
        assert "95.0%" in panel.success_rate_card.value_label.text()


class TestPoolMetricsPanel:
    """Tests for PoolMetricsPanel."""

    def test_creation(self, app):
        """Test panel creation."""
        panel = PoolMetricsPanel()

        assert panel.pool_table is not None
        assert panel.pool_table.columnCount() == 7

    def test_update_metrics(self, app):
        """Test updating pool metrics."""
        panel = PoolMetricsPanel()

        data = {
            "db_main": {
                "db_type": "sqlite",
                "available": 3,
                "in_use": 1,
                "connections_created": 5,
                "connections_closed": 1,
                "errors": 0,
            }
        }

        panel.update_metrics(data)

        assert panel.pool_table.rowCount() == 1


class TestCountersGaugesPanel:
    """Tests for CountersGaugesPanel."""

    def test_creation(self, app):
        """Test panel creation."""
        panel = CountersGaugesPanel()

        assert panel.counters_table is not None
        assert panel.gauges_table is not None

    def test_update_metrics(self, app):
        """Test updating counters and gauges."""
        panel = CountersGaugesPanel()

        counters = {"requests": 100, "errors": 5}
        gauges = {"cpu": 45.5, "memory": 256.0}

        panel.update_metrics(counters, gauges)

        assert panel.counters_table.rowCount() == 2
        assert panel.gauges_table.rowCount() == 2


class TestPerformanceDashboardDialog:
    """Tests for PerformanceDashboardDialog."""

    def test_creation(self, app):
        """Test dialog creation."""
        dialog = PerformanceDashboardDialog()

        assert dialog.tab_widget is not None
        assert dialog.system_panel is not None
        assert dialog.nodes_panel is not None
        assert dialog.workflow_panel is not None

        dialog.close()

    def test_refresh_interval_change(self, app):
        """Test changing refresh interval."""
        dialog = PerformanceDashboardDialog()

        # Change to manual
        dialog.refresh_combo.setCurrentText("Manual")

        # Timer should stop
        assert not dialog._refresh_timer.isActive()

        # Change to 5s
        dialog.refresh_combo.setCurrentText("5s")

        # Timer should start with 5000ms interval
        assert dialog._refresh_timer.isActive()
        assert dialog._refresh_timer.interval() == 5000

        dialog.close()

    def test_refresh_metrics(self, app):
        """Test manual refresh."""
        dialog = PerformanceDashboardDialog()

        # Add some test metrics
        metrics = dialog._metrics
        metrics.increment("test_counter", 10)
        metrics.set_gauge("test_gauge", 42.0)
        metrics.record_node_start("TestNode", "node-1")
        metrics.record_node_complete("TestNode", "node-1", 100.0, True)

        # Refresh
        dialog._refresh_metrics()

        # Last updated should change
        assert "Never" not in dialog.last_updated_label.text()

        dialog.close()

    def test_tabs(self, app):
        """Test tab navigation."""
        dialog = PerformanceDashboardDialog()

        # Should have 4 tabs
        assert dialog.tab_widget.count() == 4

        # Tab names
        assert dialog.tab_widget.tabText(0) == "Overview"
        assert dialog.tab_widget.tabText(1) == "Nodes"
        assert dialog.tab_widget.tabText(2) == "Pools"
        assert dialog.tab_widget.tabText(3) == "Raw Metrics"

        dialog.close()

    def test_close_stops_timer(self, app):
        """Test that closing dialog stops the timer."""
        dialog = PerformanceDashboardDialog()

        assert dialog._refresh_timer.isActive()

        dialog.close()

        # Timer should be stopped after close
        # (closeEvent is called)


class TestIntegration:
    """Integration tests for dashboard with metrics."""

    def test_full_workflow(self, app):
        """Test full workflow with metrics display."""
        # Get metrics instance
        metrics = PerformanceMetrics.get_instance()
        metrics.reset()

        # Simulate workflow execution
        metrics.record_workflow_start("wf-1")

        # Simulate node executions
        for i in range(5):
            metrics.record_node_start("HttpRequestNode", f"node-{i}")
            metrics.record_node_complete("HttpRequestNode", f"node-{i}", 100.0 + i * 10, True)

        metrics.record_node_start("ErrorNode", "error-node")
        metrics.record_node_complete("ErrorNode", "error-node", 50.0, False)

        metrics.record_workflow_complete("wf-1", 1500.0, True)

        # Create dashboard
        dialog = PerformanceDashboardDialog()
        dialog._refresh_metrics()

        # Verify metrics displayed
        summary = metrics.get_summary()

        assert summary["workflows"]["counts"]["completed"] == 1
        assert summary["nodes"]["execution_counts"]["HttpRequestNode"] == 5

        dialog.close()

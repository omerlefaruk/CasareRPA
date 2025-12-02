"""
Tests for LogViewerPanel.

Mock heavy Qt components and WebSocket connections.
Test UI logic, filtering, and export functionality.
Minimal coverage due to Qt/qasync complexity.
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import Mock, MagicMock, patch, AsyncMock

# Skip tests if PySide6 not available
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from casare_rpa.presentation.canvas.ui.panels.log_viewer_panel import (
    LogViewerPanel,
    LogStreamWorker,
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def log_viewer_panel(qapp, qtbot) -> LogViewerPanel:
    """Create LogViewerPanel for testing."""
    panel = LogViewerPanel()
    qtbot.addWidget(panel)
    return panel


@pytest.fixture
def sample_log_data() -> Dict[str, Any]:
    """Create sample log entry data."""
    return {
        "type": "log_entry",
        "robot_id": "robot-123-456",
        "timestamp": "2024-01-15T10:30:00+00:00",
        "level": "INFO",
        "message": "Test log message",
        "source": "test_source",
    }


# ============================================================================
# Panel Initialization Tests
# ============================================================================


class TestLogViewerPanelInit:
    """Tests for LogViewerPanel initialization."""

    def test_panel_created(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Panel is created successfully."""
        assert log_viewer_panel is not None
        assert log_viewer_panel.windowTitle() == "Log Viewer"

    def test_panel_has_table(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Panel has log table."""
        assert log_viewer_panel._table is not None
        assert log_viewer_panel._table.columnCount() == 5

    def test_panel_has_level_filter(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Panel has level filter combo."""
        assert log_viewer_panel._level_combo is not None
        assert log_viewer_panel._level_combo.count() == 7  # All + 6 levels

    def test_panel_has_search_field(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Panel has search field."""
        assert log_viewer_panel._search_edit is not None

    def test_panel_default_state(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Panel has correct default state."""
        assert log_viewer_panel._auto_scroll is True
        assert log_viewer_panel._paused is False
        assert log_viewer_panel._level_filter == "All"
        assert log_viewer_panel._max_entries == 5000


# ============================================================================
# Configuration Tests
# ============================================================================


class TestLogViewerPanelConfiguration:
    """Tests for panel configuration."""

    def test_configure_with_http_url(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Configure converts http to ws."""
        log_viewer_panel.configure(
            orchestrator_url="http://localhost:8000",
            api_secret="test-secret",
        )

        assert log_viewer_panel._orchestrator_url == "ws://localhost:8000"
        assert log_viewer_panel._api_secret == "test-secret"

    def test_configure_with_https_url(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Configure converts https to wss."""
        log_viewer_panel.configure(
            orchestrator_url="https://example.com",
            api_secret="test-secret",
        )

        assert log_viewer_panel._orchestrator_url == "wss://example.com"

    def test_configure_with_ws_url(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Configure preserves ws URL."""
        log_viewer_panel.configure(
            orchestrator_url="ws://localhost:8000",
            api_secret="test-secret",
        )

        assert log_viewer_panel._orchestrator_url == "ws://localhost:8000"

    def test_configure_with_tenant(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Configure sets tenant ID."""
        log_viewer_panel.configure(
            orchestrator_url="ws://localhost",
            api_secret="secret",
            tenant_id="tenant-123",
        )

        assert log_viewer_panel._tenant_edit.text() == "tenant-123"
        assert log_viewer_panel._current_tenant == "tenant-123"


# ============================================================================
# Robot Management Tests
# ============================================================================


class TestLogViewerPanelRobots:
    """Tests for robot management."""

    def test_add_robot(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Add robot to selector."""
        log_viewer_panel.add_robot("robot-123", "Test Robot")

        # Should have 2 items: "All Robots" + added robot
        assert log_viewer_panel._robot_combo.count() == 2
        assert "Test Robot" in log_viewer_panel._robot_combo.itemText(1)

    def test_clear_robots(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Clear robots from selector."""
        log_viewer_panel.add_robot("robot-1", "Robot 1")
        log_viewer_panel.add_robot("robot-2", "Robot 2")
        log_viewer_panel.clear_robots()

        # Should only have "All Robots"
        assert log_viewer_panel._robot_combo.count() == 1
        assert log_viewer_panel._robot_combo.itemText(0) == "All Robots"


# ============================================================================
# Log Entry Addition Tests
# ============================================================================


class TestLogViewerPanelLogEntries:
    """Tests for adding log entries."""

    def test_add_log_entry(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """Add log entry to table."""
        log_viewer_panel._add_log_entry(sample_log_data)

        assert log_viewer_panel._table.rowCount() == 1

    def test_add_log_entry_columns(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """Log entry has correct column values."""
        log_viewer_panel._add_log_entry(sample_log_data)

        # Check level column
        level_item = log_viewer_panel._table.item(0, LogViewerPanel.COL_LEVEL)
        assert level_item.text() == "INFO"

        # Check message column
        msg_item = log_viewer_panel._table.item(0, LogViewerPanel.COL_MESSAGE)
        assert msg_item.text() == "Test log message"

    def test_add_log_entry_updates_count(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """Adding entries updates count label."""
        log_viewer_panel._add_log_entry(sample_log_data)
        log_viewer_panel._add_log_entry(sample_log_data)

        assert "2 entries" in log_viewer_panel._entry_count_label.text()

    def test_buffer_trimmed_at_max(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """Buffer is trimmed when exceeding max entries."""
        log_viewer_panel._max_entries = 3

        for i in range(5):
            log_viewer_panel._add_log_entry(sample_log_data)

        assert log_viewer_panel._table.rowCount() == 3

    def test_add_log_entry_with_z_timestamp(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Handle Z suffix in timestamp."""
        data = {
            "type": "log_entry",
            "robot_id": "robot-123",
            "timestamp": "2024-01-15T10:30:00Z",
            "level": "INFO",
            "message": "Test",
        }
        log_viewer_panel._add_log_entry(data)

        assert log_viewer_panel._table.rowCount() == 1


# ============================================================================
# Filter Tests
# ============================================================================


class TestLogViewerPanelFilters:
    """Tests for log filtering."""

    def test_level_filter_applied_on_add(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Level filter is applied when adding entries."""
        log_viewer_panel._level_filter = "ERROR"

        info_log = {
            "type": "log_entry",
            "robot_id": "robot-123",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "level": "INFO",
            "message": "Info message",
        }
        log_viewer_panel._add_log_entry(info_log)

        # INFO log should not be added when filtering for ERROR
        assert log_viewer_panel._table.rowCount() == 0

    def test_search_filter_applied_on_add(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Search filter is applied when adding entries."""
        log_viewer_panel._search_text = "specific"

        log_data = {
            "type": "log_entry",
            "robot_id": "robot-123",
            "timestamp": "2024-01-15T10:30:00+00:00",
            "level": "INFO",
            "message": "Generic message",
        }
        log_viewer_panel._add_log_entry(log_data)

        # Message doesn't contain "specific"
        assert log_viewer_panel._table.rowCount() == 0

    def test_apply_filters_hides_rows(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """Apply filters hides non-matching rows."""
        # Add some entries first
        log_viewer_panel._add_log_entry(sample_log_data)

        error_log = sample_log_data.copy()
        error_log["level"] = "ERROR"
        error_log["message"] = "Error message"
        log_viewer_panel._add_log_entry(error_log)

        # Apply level filter
        log_viewer_panel._level_filter = "ERROR"
        log_viewer_panel._apply_filters()

        # First row (INFO) should be hidden
        assert log_viewer_panel._table.isRowHidden(0) is True
        assert log_viewer_panel._table.isRowHidden(1) is False


# ============================================================================
# Log Received Handler Tests
# ============================================================================


class TestLogViewerPanelLogReceived:
    """Tests for log received handler."""

    def test_on_log_received_adds_entry(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """On log received adds entry to table."""
        log_viewer_panel._on_log_received(sample_log_data)

        assert log_viewer_panel._table.rowCount() == 1

    def test_on_log_received_ignores_when_paused(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """On log received ignores when paused."""
        log_viewer_panel._paused = True
        log_viewer_panel._on_log_received(sample_log_data)

        assert log_viewer_panel._table.rowCount() == 0

    def test_on_log_received_ignores_unknown_type(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """On log received ignores unknown message types."""
        data = {"type": "unknown", "data": "something"}
        log_viewer_panel._on_log_received(data)

        assert log_viewer_panel._table.rowCount() == 0


# ============================================================================
# Level Color Tests
# ============================================================================


class TestLogViewerPanelColors:
    """Tests for log level colors."""

    def test_get_level_color_info(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """INFO level has green color."""
        color = log_viewer_panel._get_level_color("INFO")
        assert color.name() == "#4ec9b0"

    def test_get_level_color_warning(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """WARNING level has yellow color."""
        color = log_viewer_panel._get_level_color("WARNING")
        assert color.name() == "#cca700"

    def test_get_level_color_error(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """ERROR level has red color."""
        color = log_viewer_panel._get_level_color("ERROR")
        assert color.name() == "#f44747"

    def test_get_level_color_unknown(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Unknown level has default color."""
        color = log_viewer_panel._get_level_color("UNKNOWN")
        assert color.name() == "#d4d4d4"


# ============================================================================
# UI Actions Tests
# ============================================================================


class TestLogViewerPanelActions:
    """Tests for UI actions."""

    def test_clear_clears_table(
        self,
        log_viewer_panel: LogViewerPanel,
        sample_log_data: Dict[str, Any],
    ) -> None:
        """Clear action clears table."""
        log_viewer_panel._add_log_entry(sample_log_data)
        log_viewer_panel.clear()

        assert log_viewer_panel._table.rowCount() == 0
        assert "0 entries" in log_viewer_panel._entry_count_label.text()

    def test_pause_toggle(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Pause button toggles pause state."""
        log_viewer_panel._on_pause_clicked(True)
        assert log_viewer_panel._paused is True
        assert log_viewer_panel._pause_btn.text() == "Resume"

        log_viewer_panel._on_pause_clicked(False)
        assert log_viewer_panel._paused is False
        assert log_viewer_panel._pause_btn.text() == "Pause"

    def test_auto_scroll_toggle(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Auto-scroll checkbox toggles state."""
        log_viewer_panel._on_auto_scroll_changed(Qt.CheckState.Unchecked.value)
        assert log_viewer_panel._auto_scroll is False

        log_viewer_panel._on_auto_scroll_changed(Qt.CheckState.Checked.value)
        assert log_viewer_panel._auto_scroll is True

    def test_level_changed_updates_filter(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Level combo change updates filter."""
        log_viewer_panel._on_level_changed("ERROR")
        assert log_viewer_panel._level_filter == "ERROR"

    def test_search_changed_updates_filter(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Search text change updates filter."""
        log_viewer_panel._on_search_changed("error")
        assert log_viewer_panel._search_text == "error"


# ============================================================================
# Cleanup Tests
# ============================================================================


class TestLogViewerPanelCleanup:
    """Tests for cleanup method."""

    def test_cleanup_disconnects(
        self,
        log_viewer_panel: LogViewerPanel,
    ) -> None:
        """Cleanup disconnects WebSocket."""
        # Setup mock worker
        mock_worker = Mock()
        mock_thread = Mock()
        mock_thread.wait.return_value = True

        log_viewer_panel._worker = mock_worker
        log_viewer_panel._thread = mock_thread

        log_viewer_panel.cleanup()

        # Verify worker stop was called
        mock_worker.stop.assert_called_once()


# ============================================================================
# LogStreamWorker Tests
# ============================================================================


class TestLogStreamWorker:
    """Tests for LogStreamWorker."""

    def test_worker_init(self) -> None:
        """Worker initializes correctly."""
        worker = LogStreamWorker(
            orchestrator_url="ws://localhost:8000",
            api_secret="test-secret",
            robot_id="robot-123",
            tenant_id="tenant-456",
            min_level="INFO",
        )

        assert worker.orchestrator_url == "ws://localhost:8000"
        assert worker.api_secret == "test-secret"
        assert worker.robot_id == "robot-123"
        assert worker.tenant_id == "tenant-456"
        assert worker.min_level == "INFO"

    def test_worker_stop(self) -> None:
        """Worker stop sets running flag."""
        worker = LogStreamWorker(
            orchestrator_url="ws://localhost",
            api_secret="secret",
        )
        worker._running = True

        worker.stop()

        assert worker._running is False

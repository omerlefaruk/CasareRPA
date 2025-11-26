"""
CasareRPA - Canvas Trigger Runner Tests

Comprehensive tests for the CanvasTriggerRunner that manages
trigger lifecycle in the Canvas application.
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure Qt for testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerStatus, TriggerType, TriggerEvent


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_app():
    """Create a mock CanvasApp."""
    app = MagicMock()

    # Mock main window
    main_window = MagicMock()
    main_window.statusBar.return_value = MagicMock()
    app._main_window = main_window

    # Mock bottom panel
    bottom_panel = MagicMock()
    bottom_panel.get_triggers.return_value = []
    bottom_panel.get_triggers_tab.return_value = MagicMock()
    main_window.get_bottom_panel.return_value = bottom_panel

    return app


@pytest.fixture
def trigger_runner(mock_app):
    """Create a CanvasTriggerRunner instance."""
    from casare_rpa.canvas.trigger_runner import CanvasTriggerRunner
    return CanvasTriggerRunner(mock_app)


@pytest.fixture
def sample_trigger_configs():
    """Sample trigger configurations for testing."""
    return [
        {
            "id": "trigger_001",
            "name": "Interval Test",
            "type": "scheduled",
            "enabled": True,
            "priority": 1,
            "cooldown_seconds": 0,
            "config": {
                "frequency": "interval",
                "interval_seconds": 60
            }
        },
        {
            "id": "trigger_002",
            "name": "Daily Test",
            "type": "scheduled",
            "enabled": True,
            "priority": 2,
            "config": {
                "frequency": "daily",
                "time_hour": 9,
                "time_minute": 0
            }
        },
        {
            "id": "trigger_003",
            "name": "Disabled Trigger",
            "type": "scheduled",
            "enabled": False,
            "config": {
                "frequency": "daily",
                "time_hour": 10,
                "time_minute": 0
            }
        }
    ]


# =============================================================================
# Initialization Tests
# =============================================================================

class TestTriggerRunnerInit:
    """Tests for CanvasTriggerRunner initialization."""

    def test_init_basic(self, trigger_runner, mock_app):
        """Test basic initialization."""
        assert trigger_runner._app == mock_app
        assert trigger_runner._active_triggers == {}
        assert trigger_runner._running is False

    def test_is_running_property(self, trigger_runner):
        """Test is_running property."""
        assert trigger_runner.is_running is False

    def test_active_trigger_count_property(self, trigger_runner):
        """Test active_trigger_count property."""
        assert trigger_runner.active_trigger_count == 0


# =============================================================================
# Start Triggers Tests
# =============================================================================

class TestStartTriggers:
    """Tests for starting triggers."""

    @pytest.mark.asyncio
    async def test_start_triggers_empty_list(self, trigger_runner):
        """Test starting with empty trigger list."""
        count = await trigger_runner.start_triggers([])

        assert count == 0
        assert trigger_runner.is_running is False

    @pytest.mark.asyncio
    async def test_start_triggers_single(self, trigger_runner, sample_trigger_configs):
        """Test starting a single trigger."""
        configs = [sample_trigger_configs[0]]

        count = await trigger_runner.start_triggers(configs)

        assert count == 1
        assert trigger_runner.is_running is True
        assert trigger_runner.active_trigger_count == 1

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_start_triggers_multiple(self, trigger_runner, sample_trigger_configs):
        """Test starting multiple triggers."""
        # Only enabled triggers (first two)
        configs = sample_trigger_configs[:2]

        count = await trigger_runner.start_triggers(configs)

        assert count == 2
        assert trigger_runner.is_running is True
        assert trigger_runner.active_trigger_count == 2

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_start_triggers_skips_disabled(self, trigger_runner, sample_trigger_configs):
        """Test that disabled triggers are skipped."""
        count = await trigger_runner.start_triggers(sample_trigger_configs)

        # Should only start 2 (trigger_003 is disabled)
        assert count == 2
        assert trigger_runner.active_trigger_count == 2

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_start_triggers_already_running(self, trigger_runner, sample_trigger_configs):
        """Test starting when already running returns 0."""
        configs = [sample_trigger_configs[0]]

        await trigger_runner.start_triggers(configs)

        # Try to start again
        count = await trigger_runner.start_triggers(configs)

        assert count == 0  # Should not start more

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_start_triggers_invalid_type(self, trigger_runner):
        """Test starting with invalid trigger type."""
        configs = [{
            "id": "invalid",
            "name": "Invalid",
            "type": "nonexistent_type",
            "enabled": True,
            "config": {}
        }]

        count = await trigger_runner.start_triggers(configs)

        assert count == 0

    @pytest.mark.asyncio
    async def test_start_triggers_invalid_config(self, trigger_runner):
        """Test starting with invalid trigger configuration."""
        configs = [{
            "id": "invalid_config",
            "name": "Invalid Config",
            "type": "scheduled",
            "enabled": True,
            "config": {
                "frequency": "invalid_frequency"
            }
        }]

        count = await trigger_runner.start_triggers(configs)

        # Should fail validation and not start
        assert count == 0

    @pytest.mark.asyncio
    async def test_start_triggers_with_max_runs(self, trigger_runner):
        """Test starting trigger with max_runs config."""
        configs = [{
            "id": "max_runs_test",
            "name": "Max Runs Test",
            "type": "scheduled",
            "enabled": True,
            "max_runs": 5,
            "config": {
                "frequency": "interval",
                "interval_seconds": 60
            }
        }]

        count = await trigger_runner.start_triggers(configs)

        assert count == 1

        await trigger_runner.stop_triggers()


# =============================================================================
# Stop Triggers Tests
# =============================================================================

class TestStopTriggers:
    """Tests for stopping triggers."""

    @pytest.mark.asyncio
    async def test_stop_triggers_when_running(self, trigger_runner, sample_trigger_configs):
        """Test stopping running triggers."""
        await trigger_runner.start_triggers([sample_trigger_configs[0]])

        await trigger_runner.stop_triggers()

        assert trigger_runner.is_running is False
        assert trigger_runner.active_trigger_count == 0

    @pytest.mark.asyncio
    async def test_stop_triggers_when_not_running(self, trigger_runner):
        """Test stopping when not running is safe."""
        await trigger_runner.stop_triggers()

        assert trigger_runner.is_running is False
        assert trigger_runner.active_trigger_count == 0

    @pytest.mark.asyncio
    async def test_stop_triggers_clears_active(self, trigger_runner, sample_trigger_configs):
        """Test that stop clears active triggers dict."""
        await trigger_runner.start_triggers(sample_trigger_configs[:2])

        assert len(trigger_runner._active_triggers) == 2

        await trigger_runner.stop_triggers()

        assert len(trigger_runner._active_triggers) == 0

    @pytest.mark.asyncio
    async def test_stop_triggers_multiple_times(self, trigger_runner, sample_trigger_configs):
        """Test stopping multiple times is safe."""
        await trigger_runner.start_triggers([sample_trigger_configs[0]])

        await trigger_runner.stop_triggers()
        await trigger_runner.stop_triggers()
        await trigger_runner.stop_triggers()

        assert trigger_runner.is_running is False


# =============================================================================
# Trigger Event Handling Tests
# =============================================================================

class TestTriggerEventHandling:
    """Tests for trigger event handling."""

    @pytest.mark.asyncio
    async def test_on_trigger_event_stores_event(self, trigger_runner):
        """Test that trigger event is stored."""
        event = TriggerEvent(
            trigger_id="test_trigger",
            trigger_type=TriggerType.SCHEDULED,
            workflow_id="wf",
            scenario_id="sc",
            payload={"test": "data"}
        )

        await trigger_runner._on_trigger_event(event)

        stored = trigger_runner.get_last_trigger_event()
        assert stored == event

    @pytest.mark.asyncio
    async def test_get_last_trigger_event_initial(self, trigger_runner):
        """Test get_last_trigger_event returns None initially."""
        result = trigger_runner.get_last_trigger_event()
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_last_trigger_event(self, trigger_runner):
        """Test clearing last trigger event."""
        event = TriggerEvent(
            trigger_id="test",
            trigger_type=TriggerType.MANUAL,
            workflow_id="wf",
            scenario_id="sc"
        )

        await trigger_runner._on_trigger_event(event)
        trigger_runner.clear_last_trigger_event()

        assert trigger_runner.get_last_trigger_event() is None

    @pytest.mark.asyncio
    async def test_on_trigger_event_invokes_main_window(self, trigger_runner, mock_app):
        """Test that trigger event invokes main window method."""
        event = TriggerEvent(
            trigger_id="test",
            trigger_type=TriggerType.SCHEDULED,
            workflow_id="wf",
            scenario_id="sc"
        )

        with patch('PySide6.QtCore.QMetaObject') as mock_meta:
            await trigger_runner._on_trigger_event(event)

            # Should have called invokeMethod
            mock_meta.invokeMethod.assert_called_once()


# =============================================================================
# Stats Update Tests
# =============================================================================

class TestStatsUpdate:
    """Tests for trigger stats update functionality."""

    def test_update_trigger_stats(self, trigger_runner, mock_app):
        """Test updating trigger stats."""
        # Setup mock triggers tab
        triggers_tab = MagicMock()
        triggers_tab.get_triggers.return_value = [
            {"id": "test_trigger", "trigger_count": 5}
        ]

        mock_app._main_window.get_bottom_panel.return_value.get_triggers_tab.return_value = triggers_tab

        with patch('PySide6.QtCore.QTimer') as mock_timer:
            trigger_runner._update_trigger_stats("test_trigger")

            # Should have scheduled a QTimer.singleShot
            mock_timer.singleShot.assert_called_once()

    def test_update_trigger_stats_no_main_window(self, trigger_runner, mock_app):
        """Test update stats when main window is None."""
        mock_app._main_window = None

        # Should not crash
        trigger_runner._update_trigger_stats("test_trigger")

    def test_update_trigger_stats_no_bottom_panel(self, trigger_runner, mock_app):
        """Test update stats when bottom panel is None."""
        mock_app._main_window.get_bottom_panel.return_value = None

        # Should not crash
        trigger_runner._update_trigger_stats("test_trigger")


# =============================================================================
# Integration Tests
# =============================================================================

class TestTriggerRunnerIntegration:
    """Integration tests for trigger runner."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, trigger_runner, sample_trigger_configs):
        """Test complete trigger lifecycle."""
        # Start
        count = await trigger_runner.start_triggers([sample_trigger_configs[0]])
        assert count == 1
        assert trigger_runner.is_running is True

        # Check state
        assert trigger_runner.active_trigger_count == 1
        assert "trigger_001" in trigger_runner._active_triggers

        # Stop
        await trigger_runner.stop_triggers()
        assert trigger_runner.is_running is False
        assert trigger_runner.active_trigger_count == 0

    @pytest.mark.asyncio
    async def test_restart_after_stop(self, trigger_runner, sample_trigger_configs):
        """Test restarting triggers after stopping."""
        # First run
        await trigger_runner.start_triggers([sample_trigger_configs[0]])
        await trigger_runner.stop_triggers()

        # Restart
        count = await trigger_runner.start_triggers([sample_trigger_configs[1]])

        assert count == 1
        assert trigger_runner.is_running is True

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_multiple_trigger_types(self, trigger_runner):
        """Test starting multiple trigger types."""
        configs = [
            {
                "id": "scheduled_1",
                "name": "Scheduled",
                "type": "scheduled",
                "enabled": True,
                "config": {"frequency": "interval", "interval_seconds": 60}
            },
            # Note: Other trigger types may need different test setup
        ]

        count = await trigger_runner.start_triggers(configs)

        assert count >= 1  # At least scheduled should work

        await trigger_runner.stop_triggers()


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestTriggerRunnerErrorHandling:
    """Error handling tests for trigger runner."""

    @pytest.mark.asyncio
    async def test_start_handles_exception(self, trigger_runner):
        """Test that start handles exceptions gracefully."""
        # Create a trigger config with invalid frequency
        configs = [{
            "id": "error_test",
            "name": "Error Test",
            "type": "scheduled",
            "enabled": True,
            "config": {
                "frequency": "invalid_frequency_type"  # This will fail validation
            }
        }]

        # Should not raise, but return 0 since validation fails
        count = await trigger_runner.start_triggers(configs)

        assert count == 0

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_stop_handles_exception(self, trigger_runner, sample_trigger_configs):
        """Test that stop handles exceptions gracefully."""
        await trigger_runner.start_triggers([sample_trigger_configs[0]])

        # Corrupt the trigger to cause stop to fail
        if trigger_runner._active_triggers:
            trigger_id = list(trigger_runner._active_triggers.keys())[0]
            trigger = trigger_runner._active_triggers[trigger_id]
            trigger.stop = AsyncMock(side_effect=Exception("Stop failed"))

        # Should not raise
        await trigger_runner.stop_triggers()

        # Should still clean up
        assert trigger_runner.is_running is False

    @pytest.mark.asyncio
    async def test_event_handling_exception(self, trigger_runner, mock_app):
        """Test event handling with exception."""
        # Make main window throw exception
        mock_app._main_window = MagicMock()
        mock_app._main_window.get_bottom_panel.side_effect = Exception("Test error")

        event = TriggerEvent(
            trigger_id="test",
            trigger_type=TriggerType.MANUAL,
            workflow_id="wf",
            scenario_id="sc"
        )

        # Should not raise
        await trigger_runner._on_trigger_event(event)


# =============================================================================
# Performance Tests
# =============================================================================

class TestTriggerRunnerPerformance:
    """Performance tests for trigger runner."""

    @pytest.mark.asyncio
    async def test_start_many_triggers(self, trigger_runner):
        """Test starting many triggers."""
        configs = [
            {
                "id": f"trigger_{i}",
                "name": f"Trigger {i}",
                "type": "scheduled",
                "enabled": True,
                "config": {
                    "frequency": "interval",
                    "interval_seconds": 3600  # 1 hour to not fire during test
                }
            }
            for i in range(20)
        ]

        count = await trigger_runner.start_triggers(configs)

        assert count == 20
        assert trigger_runner.active_trigger_count == 20

        await trigger_runner.stop_triggers()

    @pytest.mark.asyncio
    async def test_rapid_start_stop_cycles(self, trigger_runner, sample_trigger_configs):
        """Test rapid start/stop cycles."""
        config = sample_trigger_configs[0]

        for _ in range(10):
            await trigger_runner.start_triggers([config])
            assert trigger_runner.is_running is True
            await trigger_runner.stop_triggers()
            assert trigger_runner.is_running is False

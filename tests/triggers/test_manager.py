"""Tests for TriggerManager.

Tests the central coordinator for all workflow triggers including
lifecycle management, webhook handling, and event routing.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from casare_rpa.triggers.manager import TriggerManager
from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerEvent,
    TriggerType,
    TriggerStatus,
)


@pytest.fixture
def trigger_config():
    """Create a basic trigger config."""
    return BaseTriggerConfig(
        id="test_trigger_1",
        name="Test Trigger",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario_1",
        workflow_id="workflow_1",
        config={"endpoint": "/webhooks/test"},
        enabled=True,
    )


@pytest.fixture
def scheduled_config():
    """Create a scheduled trigger config."""
    return BaseTriggerConfig(
        id="scheduled_1",
        name="Scheduled Test",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario_1",
        workflow_id="workflow_1",
        config={"cron": "0 * * * *"},
        enabled=True,
    )


@pytest.fixture
def mock_trigger():
    """Create a mock trigger."""
    trigger = AsyncMock(spec=BaseTrigger)
    trigger.config = BaseTriggerConfig(
        id="mock_trigger",
        name="Mock Trigger",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario_1",
        workflow_id="workflow_1",
        config={},
        enabled=True,
    )
    trigger.trigger_type = TriggerType.WEBHOOK
    trigger.is_active = True
    # validate_config is sync, returns tuple
    trigger.validate_config = Mock(return_value=(True, None))
    return trigger


@pytest.fixture
def event_callback():
    """Create a mock event callback."""
    return AsyncMock()


class TestTriggerManagerInit:
    """Tests for TriggerManager initialization."""

    def test_init_default_port(self):
        """Test initialization with default port."""
        manager = TriggerManager()

        assert manager._http_port == 8766
        assert manager._running is False
        assert len(manager._triggers) == 0
        assert manager._on_trigger_event is None

    def test_init_custom_port(self):
        """Test initialization with custom port."""
        manager = TriggerManager(http_port=9999)

        assert manager._http_port == 9999

    def test_init_with_callback(self, event_callback):
        """Test initialization with event callback."""
        manager = TriggerManager(on_trigger_event=event_callback)

        assert manager._on_trigger_event is event_callback


class TestTriggerManagerLifecycle:
    """Tests for TriggerManager start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self):
        """Test that start sets running flag."""
        manager = TriggerManager()

        with patch.object(manager, "_start_http_server", new_callable=AsyncMock):
            await manager.start()

        assert manager._running is True

    @pytest.mark.asyncio
    async def test_start_already_running(self):
        """Test that starting when already running logs warning."""
        manager = TriggerManager()
        manager._running = True

        with patch.object(
            manager, "_start_http_server", new_callable=AsyncMock
        ) as mock_start:
            await manager.start()
            mock_start.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self):
        """Test that stop clears running flag."""
        manager = TriggerManager()
        manager._running = True

        with patch.object(manager, "_stop_http_server", new_callable=AsyncMock):
            await manager.stop()

        assert manager._running is False

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test that stop when not running does nothing."""
        manager = TriggerManager()

        with patch.object(
            manager, "_stop_http_server", new_callable=AsyncMock
        ) as mock_stop:
            await manager.stop()
            mock_stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_starts_enabled_triggers(self, mock_trigger):
        """Test that start starts all enabled triggers."""
        manager = TriggerManager()
        manager._triggers["trigger_1"] = mock_trigger

        with patch.object(manager, "_start_http_server", new_callable=AsyncMock):
            await manager.start()

        mock_trigger.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_skips_disabled_triggers(self, mock_trigger):
        """Test that start skips disabled triggers."""
        manager = TriggerManager()
        mock_trigger.config.enabled = False
        manager._triggers["trigger_1"] = mock_trigger

        with patch.object(manager, "_start_http_server", new_callable=AsyncMock):
            await manager.start()

        mock_trigger.start.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_stop_stops_all_triggers(self, mock_trigger):
        """Test that stop stops all triggers."""
        manager = TriggerManager()
        manager._running = True
        manager._triggers["trigger_1"] = mock_trigger

        with patch.object(manager, "_stop_http_server", new_callable=AsyncMock):
            await manager.stop()

        mock_trigger.stop.assert_awaited_once()


class TestTriggerRegistration:
    """Tests for trigger registration."""

    @pytest.mark.asyncio
    async def test_register_trigger_creates_instance(self, trigger_config):
        """Test registering a trigger creates an instance."""
        manager = TriggerManager()
        mock_trigger = AsyncMock()
        mock_trigger.validate_config = Mock(return_value=(True, None))

        with patch.object(
            manager._registry, "create_instance", return_value=mock_trigger
        ):
            result = await manager.register_trigger(trigger_config)

        assert result is mock_trigger
        assert trigger_config.id in manager._triggers

    @pytest.mark.asyncio
    async def test_register_trigger_already_exists(self, trigger_config, mock_trigger):
        """Test registering duplicate trigger returns existing."""
        manager = TriggerManager()
        manager._triggers[trigger_config.id] = mock_trigger

        result = await manager.register_trigger(trigger_config)

        assert result is mock_trigger

    @pytest.mark.asyncio
    async def test_register_trigger_invalid_config(self, trigger_config):
        """Test registering trigger with invalid config fails."""
        manager = TriggerManager()
        mock_trigger = AsyncMock()
        mock_trigger.validate_config = Mock(return_value=(False, "Invalid config"))

        with patch.object(
            manager._registry, "create_instance", return_value=mock_trigger
        ):
            result = await manager.register_trigger(trigger_config)

        assert result is None

    @pytest.mark.asyncio
    async def test_register_trigger_creates_webhook_route(self, trigger_config):
        """Test registering webhook trigger creates route."""
        manager = TriggerManager()
        mock_trigger = AsyncMock()
        mock_trigger.validate_config = Mock(return_value=(True, None))

        with patch.object(
            manager._registry, "create_instance", return_value=mock_trigger
        ):
            await manager.register_trigger(trigger_config)

        assert "/webhooks/test" in manager._webhook_routes
        assert manager._webhook_routes["/webhooks/test"] == trigger_config.id

    @pytest.mark.asyncio
    async def test_register_workflow_call_trigger_creates_callable(self):
        """Test registering workflow call trigger creates callable."""
        manager = TriggerManager()
        config = BaseTriggerConfig(
            id="call_trigger",
            name="Call Trigger",
            trigger_type=TriggerType.WORKFLOW_CALL,
            scenario_id="scenario_1",
            workflow_id="workflow_1",
            config={"call_alias": "my_workflow"},
            enabled=True,
        )
        mock_trigger = AsyncMock()
        mock_trigger.validate_config = Mock(return_value=(True, None))

        with patch.object(
            manager._registry, "create_instance", return_value=mock_trigger
        ):
            await manager.register_trigger(config)

        assert "my_workflow" in manager._callables
        assert manager._callables["my_workflow"] == config.id

    @pytest.mark.asyncio
    async def test_register_starts_trigger_if_running(self, trigger_config):
        """Test registering trigger starts it if manager is running."""
        manager = TriggerManager()
        manager._running = True
        mock_trigger = AsyncMock()
        mock_trigger.validate_config = Mock(return_value=(True, None))

        with patch.object(
            manager._registry, "create_instance", return_value=mock_trigger
        ):
            await manager.register_trigger(trigger_config)

        mock_trigger.start.assert_awaited_once()


class TestTriggerUnregistration:
    """Tests for trigger unregistration."""

    @pytest.mark.asyncio
    async def test_unregister_trigger_stops_and_removes(
        self, mock_trigger, trigger_config
    ):
        """Test unregistering trigger stops and removes it."""
        manager = TriggerManager()
        manager._triggers[trigger_config.id] = mock_trigger
        manager._trigger_configs[trigger_config.id] = trigger_config
        manager._webhook_routes["/webhooks/test"] = trigger_config.id

        result = await manager.unregister_trigger(trigger_config.id)

        assert result is True
        assert trigger_config.id not in manager._triggers
        assert "/webhooks/test" not in manager._webhook_routes
        mock_trigger.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_returns_false(self):
        """Test unregistering nonexistent trigger returns False."""
        manager = TriggerManager()

        result = await manager.unregister_trigger("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_unregister_removes_callable(self):
        """Test unregistering workflow call trigger removes callable."""
        manager = TriggerManager()
        config = BaseTriggerConfig(
            id="call_trigger",
            name="Call Trigger",
            trigger_type=TriggerType.WORKFLOW_CALL,
            scenario_id="scenario_1",
            workflow_id="workflow_1",
            config={"call_alias": "my_workflow"},
            enabled=True,
        )
        mock_trigger = AsyncMock()
        manager._triggers[config.id] = mock_trigger
        manager._trigger_configs[config.id] = config
        manager._callables["my_workflow"] = config.id

        await manager.unregister_trigger(config.id)

        assert "my_workflow" not in manager._callables


class TestTriggerEnableDisable:
    """Tests for enabling/disabling triggers."""

    @pytest.mark.asyncio
    async def test_enable_trigger_starts_if_running(self, mock_trigger):
        """Test enabling trigger starts it if manager is running."""
        manager = TriggerManager()
        manager._running = True
        mock_trigger.config.enabled = False
        manager._triggers["trigger_1"] = mock_trigger

        result = await manager.enable_trigger("trigger_1")

        assert result is True
        assert mock_trigger.config.enabled is True
        mock_trigger.start.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_enable_nonexistent_returns_false(self):
        """Test enabling nonexistent trigger returns False."""
        manager = TriggerManager()

        result = await manager.enable_trigger("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_disable_trigger_stops(self, mock_trigger):
        """Test disabling trigger stops it."""
        manager = TriggerManager()
        manager._triggers["trigger_1"] = mock_trigger

        result = await manager.disable_trigger("trigger_1")

        assert result is True
        assert mock_trigger.config.enabled is False
        mock_trigger.stop.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_disable_nonexistent_returns_false(self):
        """Test disabling nonexistent trigger returns False."""
        manager = TriggerManager()

        result = await manager.disable_trigger("nonexistent")

        assert result is False


class TestFireTrigger:
    """Tests for manually firing triggers."""

    @pytest.mark.asyncio
    async def test_fire_trigger_emits_event(self, mock_trigger):
        """Test firing trigger emits event."""
        manager = TriggerManager()
        manager._triggers["trigger_1"] = mock_trigger
        mock_trigger.emit.return_value = True

        result = await manager.fire_trigger("trigger_1", {"data": "test"})

        assert result is not None
        assert result.startswith("evt_")
        mock_trigger.emit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_fire_nonexistent_returns_none(self):
        """Test firing nonexistent trigger returns None."""
        manager = TriggerManager()

        result = await manager.fire_trigger("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_fire_disabled_returns_none(self, mock_trigger):
        """Test firing disabled trigger returns None."""
        manager = TriggerManager()
        mock_trigger.config.enabled = False
        manager._triggers["trigger_1"] = mock_trigger

        result = await manager.fire_trigger("trigger_1")

        assert result is None

    @pytest.mark.asyncio
    async def test_fire_cooldown_returns_none(self, mock_trigger):
        """Test firing trigger in cooldown returns None."""
        manager = TriggerManager()
        manager._triggers["trigger_1"] = mock_trigger
        mock_trigger.emit.return_value = False  # Indicates cooldown

        result = await manager.fire_trigger("trigger_1")

        assert result is None


class TestCallWorkflow:
    """Tests for callable workflow invocation."""

    @pytest.mark.asyncio
    async def test_call_workflow_fires_trigger(self, mock_trigger):
        """Test calling workflow fires associated trigger."""
        manager = TriggerManager()
        manager._triggers["call_trigger"] = mock_trigger
        manager._callables["my_workflow"] = "call_trigger"
        mock_trigger.emit.return_value = True

        result = await manager.call_workflow("my_workflow", {"param": "value"})

        assert result is not None
        assert "event_id" in result
        assert result["status"] == "submitted"

    @pytest.mark.asyncio
    async def test_call_unknown_alias_returns_none(self):
        """Test calling unknown alias returns None."""
        manager = TriggerManager()

        result = await manager.call_workflow("unknown_alias")

        assert result is None


class TestTriggerQueries:
    """Tests for trigger query methods."""

    def test_get_trigger(self, mock_trigger):
        """Test getting trigger by ID."""
        manager = TriggerManager()
        manager._triggers["trigger_1"] = mock_trigger

        result = manager.get_trigger("trigger_1")

        assert result is mock_trigger

    def test_get_trigger_nonexistent(self):
        """Test getting nonexistent trigger returns None."""
        manager = TriggerManager()

        result = manager.get_trigger("nonexistent")

        assert result is None

    def test_get_all_triggers(self, mock_trigger):
        """Test getting all triggers."""
        manager = TriggerManager()
        manager._triggers["trigger_1"] = mock_trigger
        manager._triggers["trigger_2"] = mock_trigger

        result = manager.get_all_triggers()

        assert len(result) == 2

    def test_get_triggers_by_scenario(self, mock_trigger):
        """Test getting triggers by scenario."""
        manager = TriggerManager()
        mock_trigger.config.scenario_id = "scenario_1"
        manager._triggers["trigger_1"] = mock_trigger

        other_trigger = AsyncMock()
        other_trigger.config = BaseTriggerConfig(
            id="trigger_2",
            name="Other",
            trigger_type=TriggerType.SCHEDULED,
            scenario_id="scenario_2",
            workflow_id="workflow_1",
            config={},
        )
        manager._triggers["trigger_2"] = other_trigger

        result = manager.get_triggers_by_scenario("scenario_1")

        assert len(result) == 1

    def test_get_triggers_by_type(self, mock_trigger):
        """Test getting triggers by type."""
        manager = TriggerManager()
        mock_trigger.trigger_type = TriggerType.WEBHOOK
        manager._triggers["trigger_1"] = mock_trigger

        result = manager.get_triggers_by_type(TriggerType.WEBHOOK)

        assert len(result) == 1

    def test_get_active_triggers(self, mock_trigger):
        """Test getting active triggers."""
        manager = TriggerManager()
        mock_trigger.is_active = True
        manager._triggers["trigger_1"] = mock_trigger

        inactive = AsyncMock()
        inactive.is_active = False
        manager._triggers["trigger_2"] = inactive

        result = manager.get_active_triggers()

        assert len(result) == 1


class TestGetStats:
    """Tests for statistics."""

    def test_get_stats_empty(self):
        """Test stats with no triggers."""
        manager = TriggerManager()

        stats = manager.get_stats()

        assert stats["total_triggers"] == 0
        assert stats["active_triggers"] == 0
        assert stats["http_server_running"] is False

    def test_get_stats_with_triggers(self, mock_trigger):
        """Test stats with triggers."""
        manager = TriggerManager()
        mock_trigger.is_active = True
        mock_trigger.config.enabled = True
        mock_trigger.config.trigger_count = 10
        mock_trigger.config.success_count = 8
        mock_trigger.config.error_count = 2
        manager._triggers["trigger_1"] = mock_trigger

        stats = manager.get_stats()

        assert stats["total_triggers"] == 1
        assert stats["active_triggers"] == 1
        assert stats["enabled_triggers"] == 1
        assert stats["total_fired"] == 10
        assert stats["total_success"] == 8
        assert stats["total_errors"] == 2


class TestEventCallback:
    """Tests for trigger event callback handling."""

    @pytest.mark.asyncio
    async def test_on_trigger_fired_calls_callback(self, event_callback):
        """Test that trigger events invoke the callback."""
        manager = TriggerManager(on_trigger_event=event_callback)

        event = TriggerEvent(
            trigger_id="trigger_1",
            trigger_type=TriggerType.WEBHOOK,
            workflow_id="workflow_1",
            scenario_id="scenario_1",
            payload={"data": "test"},
            metadata={},
        )

        await manager._on_trigger_fired(event)

        event_callback.assert_awaited_once_with(event)

    @pytest.mark.asyncio
    async def test_on_trigger_fired_handles_sync_callback(self):
        """Test that sync callbacks are handled."""
        sync_callback = Mock()
        manager = TriggerManager(on_trigger_event=sync_callback)

        event = TriggerEvent(
            trigger_id="trigger_1",
            trigger_type=TriggerType.WEBHOOK,
            workflow_id="workflow_1",
            scenario_id="scenario_1",
            payload={},
            metadata={},
        )

        await manager._on_trigger_fired(event)

        sync_callback.assert_called_once_with(event)

    @pytest.mark.asyncio
    async def test_on_trigger_fired_no_callback(self):
        """Test that missing callback doesn't raise."""
        manager = TriggerManager()

        event = TriggerEvent(
            trigger_id="trigger_1",
            trigger_type=TriggerType.WEBHOOK,
            workflow_id="workflow_1",
            scenario_id="scenario_1",
            payload={},
            metadata={},
        )

        # Should not raise
        await manager._on_trigger_fired(event)

    @pytest.mark.asyncio
    async def test_on_trigger_fired_callback_error(self, event_callback):
        """Test that callback errors are handled gracefully."""
        event_callback.side_effect = Exception("Callback error")
        manager = TriggerManager(on_trigger_event=event_callback)

        event = TriggerEvent(
            trigger_id="trigger_1",
            trigger_type=TriggerType.WEBHOOK,
            workflow_id="workflow_1",
            scenario_id="scenario_1",
            payload={},
            metadata={},
        )

        # Should not raise
        await manager._on_trigger_fired(event)


class TestProperties:
    """Tests for manager properties."""

    def test_is_running(self):
        """Test is_running property."""
        manager = TriggerManager()

        assert manager.is_running is False

        manager._running = True
        assert manager.is_running is True

    def test_http_port(self):
        """Test http_port property."""
        manager = TriggerManager(http_port=9999)

        assert manager.http_port == 9999

    def test_repr(self):
        """Test string representation."""
        manager = TriggerManager()

        repr_str = repr(manager)

        assert "TriggerManager" in repr_str
        assert "triggers=0" in repr_str
        assert "running=False" in repr_str


class TestUpdateTrigger:
    """Tests for trigger updates."""

    @pytest.mark.asyncio
    async def test_update_trigger_reregisters(self, trigger_config, mock_trigger):
        """Test updating trigger re-registers with new config."""
        manager = TriggerManager()
        manager._triggers[trigger_config.id] = mock_trigger
        manager._trigger_configs[trigger_config.id] = trigger_config

        new_config = BaseTriggerConfig(
            id="new_id",  # Will be overwritten
            name="Updated Trigger",
            trigger_type=TriggerType.WEBHOOK,
            scenario_id="scenario_1",
            workflow_id="workflow_2",
            config={"endpoint": "/webhooks/updated"},
            enabled=True,
        )

        new_trigger = AsyncMock()
        new_trigger.validate_config = Mock(return_value=(True, None))

        with patch.object(
            manager._registry, "create_instance", return_value=new_trigger
        ):
            result = await manager.update_trigger(trigger_config.id, new_config)

        assert result is new_trigger
        # Old trigger should have been stopped
        mock_trigger.stop.assert_awaited_once()

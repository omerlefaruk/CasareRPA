"""Tests for LocalTriggerRepository."""

import pytest
from pathlib import Path
import tempfile

from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
from casare_rpa.infrastructure.orchestrator.persistence import (
    LocalStorageRepository,
    LocalTriggerRepository,
)


@pytest.fixture
def temp_storage_dir():
    """Create temporary storage directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_storage_dir):
    """Create LocalStorageRepository with temp directory."""
    return LocalStorageRepository(storage_dir=temp_storage_dir)


@pytest.fixture
def trigger_repository(storage):
    """Create LocalTriggerRepository."""
    return LocalTriggerRepository(storage)


@pytest.fixture
def sample_trigger():
    """Create sample trigger config."""
    return BaseTriggerConfig(
        id="trig-1",
        name="Test Webhook",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
        enabled=True,
        priority=1,
        cooldown_seconds=30,
        description="Test webhook trigger",
        config={"path": "/webhook/test", "method": "POST"},
    )


@pytest.mark.asyncio
async def test_save_trigger(trigger_repository, sample_trigger):
    """Test saving a trigger."""
    await trigger_repository.save(sample_trigger)

    # Verify trigger was saved
    retrieved = await trigger_repository.get_by_id("trig-1")
    assert retrieved is not None
    assert retrieved.id == "trig-1"
    assert retrieved.name == "Test Webhook"
    assert retrieved.trigger_type == TriggerType.WEBHOOK


@pytest.mark.asyncio
async def test_get_by_id_not_found(trigger_repository):
    """Test getting non-existent trigger returns None."""
    result = await trigger_repository.get_by_id("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_all(trigger_repository):
    """Test getting all triggers."""
    trig1 = BaseTriggerConfig(
        id="trig-1",
        name="Trigger 1",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
        enabled=True,
    )
    trig2 = BaseTriggerConfig(
        id="trig-2",
        name="Trigger 2",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-1",
        workflow_id="wf-2",
        enabled=False,
    )

    await trigger_repository.save(trig1)
    await trigger_repository.save(trig2)

    all_triggers = await trigger_repository.get_all()
    assert len(all_triggers) == 2
    assert {t.id for t in all_triggers} == {"trig-1", "trig-2"}


@pytest.mark.asyncio
async def test_get_enabled(trigger_repository):
    """Test getting only enabled triggers."""
    trig1 = BaseTriggerConfig(
        id="trig-1",
        name="Trigger 1",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
        enabled=True,
    )
    trig2 = BaseTriggerConfig(
        id="trig-2",
        name="Trigger 2",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-1",
        workflow_id="wf-2",
        enabled=False,
    )
    trig3 = BaseTriggerConfig(
        id="trig-3",
        name="Trigger 3",
        trigger_type=TriggerType.FILE_WATCH,
        scenario_id="scenario-2",
        workflow_id="wf-3",
        enabled=True,
    )

    await trigger_repository.save(trig1)
    await trigger_repository.save(trig2)
    await trigger_repository.save(trig3)

    enabled_triggers = await trigger_repository.get_enabled()
    assert len(enabled_triggers) == 2
    assert {t.id for t in enabled_triggers} == {"trig-1", "trig-3"}


@pytest.mark.asyncio
async def test_get_by_scenario(trigger_repository):
    """Test getting triggers by scenario."""
    trig1 = BaseTriggerConfig(
        id="trig-1",
        name="Trigger 1",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
    )
    trig2 = BaseTriggerConfig(
        id="trig-2",
        name="Trigger 2",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-2",
        workflow_id="wf-2",
    )
    trig3 = BaseTriggerConfig(
        id="trig-3",
        name="Trigger 3",
        trigger_type=TriggerType.FILE_WATCH,
        scenario_id="scenario-1",
        workflow_id="wf-3",
    )

    await trigger_repository.save(trig1)
    await trigger_repository.save(trig2)
    await trigger_repository.save(trig3)

    scenario_1_triggers = await trigger_repository.get_by_scenario("scenario-1")
    assert len(scenario_1_triggers) == 2
    assert {t.id for t in scenario_1_triggers} == {"trig-1", "trig-3"}


@pytest.mark.asyncio
async def test_get_by_workflow(trigger_repository):
    """Test getting triggers by workflow."""
    trig1 = BaseTriggerConfig(
        id="trig-1",
        name="Trigger 1",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
    )
    trig2 = BaseTriggerConfig(
        id="trig-2",
        name="Trigger 2",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-2",
        workflow_id="wf-1",
    )
    trig3 = BaseTriggerConfig(
        id="trig-3",
        name="Trigger 3",
        trigger_type=TriggerType.FILE_WATCH,
        scenario_id="scenario-1",
        workflow_id="wf-2",
    )

    await trigger_repository.save(trig1)
    await trigger_repository.save(trig2)
    await trigger_repository.save(trig3)

    wf_1_triggers = await trigger_repository.get_by_workflow("wf-1")
    assert len(wf_1_triggers) == 2
    assert {t.id for t in wf_1_triggers} == {"trig-1", "trig-2"}


@pytest.mark.asyncio
async def test_get_by_type(trigger_repository):
    """Test getting triggers by type."""
    trig1 = BaseTriggerConfig(
        id="trig-1",
        name="Trigger 1",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
    )
    trig2 = BaseTriggerConfig(
        id="trig-2",
        name="Trigger 2",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-2",
        workflow_id="wf-2",
    )
    trig3 = BaseTriggerConfig(
        id="trig-3",
        name="Trigger 3",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-1",
        workflow_id="wf-3",
    )

    await trigger_repository.save(trig1)
    await trigger_repository.save(trig2)
    await trigger_repository.save(trig3)

    webhook_triggers = await trigger_repository.get_by_type(TriggerType.WEBHOOK)
    assert len(webhook_triggers) == 2
    assert {t.id for t in webhook_triggers} == {"trig-1", "trig-2"}


@pytest.mark.asyncio
async def test_update_trigger(trigger_repository, sample_trigger):
    """Test updating a trigger."""
    await trigger_repository.save(sample_trigger)

    # Update trigger
    sample_trigger.enabled = False
    sample_trigger.trigger_count = 10
    sample_trigger.success_count = 8
    await trigger_repository.save(sample_trigger)

    # Verify updates
    updated = await trigger_repository.get_by_id("trig-1")
    assert updated.enabled is False
    assert updated.trigger_count == 10
    assert updated.success_count == 8


@pytest.mark.asyncio
async def test_delete_trigger(trigger_repository, sample_trigger):
    """Test deleting a trigger."""
    await trigger_repository.save(sample_trigger)

    # Verify trigger exists
    assert await trigger_repository.get_by_id("trig-1") is not None

    # Delete trigger
    await trigger_repository.delete("trig-1")

    # Verify trigger is gone
    assert await trigger_repository.get_by_id("trig-1") is None


@pytest.mark.asyncio
async def test_delete_by_scenario(trigger_repository):
    """Test deleting all triggers for a scenario."""
    trig1 = BaseTriggerConfig(
        id="trig-1",
        name="Trigger 1",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
    )
    trig2 = BaseTriggerConfig(
        id="trig-2",
        name="Trigger 2",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-1",
        workflow_id="wf-2",
    )
    trig3 = BaseTriggerConfig(
        id="trig-3",
        name="Trigger 3",
        trigger_type=TriggerType.FILE_WATCH,
        scenario_id="scenario-2",
        workflow_id="wf-3",
    )

    await trigger_repository.save(trig1)
    await trigger_repository.save(trig2)
    await trigger_repository.save(trig3)

    # Delete all triggers for scenario-1
    deleted_count = await trigger_repository.delete_by_scenario("scenario-1")
    assert deleted_count == 2

    # Verify only scenario-2 triggers remain
    all_triggers = await trigger_repository.get_all()
    assert len(all_triggers) == 1
    assert all_triggers[0].id == "trig-3"


@pytest.mark.asyncio
async def test_config_serialization(trigger_repository):
    """Test that trigger config dict is properly serialized."""
    trigger = BaseTriggerConfig(
        id="trig-config",
        name="Config Test",
        trigger_type=TriggerType.WEBHOOK,
        scenario_id="scenario-1",
        workflow_id="wf-1",
        config={
            "path": "/api/hook",
            "method": "POST",
            "headers": {"X-Custom": "value"},
            "timeout": 30,
        },
    )

    await trigger_repository.save(trigger)
    retrieved = await trigger_repository.get_by_id("trig-config")

    assert retrieved.config["path"] == "/api/hook"
    assert retrieved.config["method"] == "POST"
    assert retrieved.config["headers"] == {"X-Custom": "value"}
    assert retrieved.config["timeout"] == 30


@pytest.mark.asyncio
async def test_datetime_serialization(trigger_repository):
    """Test that datetime fields are properly serialized."""
    from datetime import datetime, timezone

    trigger = BaseTriggerConfig(
        id="trig-datetime",
        name="Datetime Test",
        trigger_type=TriggerType.SCHEDULED,
        scenario_id="scenario-1",
        workflow_id="wf-1",
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        last_triggered=datetime(2025, 1, 20, 14, 45, 0, tzinfo=timezone.utc),
    )

    await trigger_repository.save(trigger)
    retrieved = await trigger_repository.get_by_id("trig-datetime")

    # Verify datetimes are preserved (isoformat round-trip)
    assert retrieved.created_at.year == 2025
    assert retrieved.created_at.month == 1
    assert retrieved.created_at.day == 15
    assert retrieved.last_triggered.hour == 14
    assert retrieved.last_triggered.minute == 45


@pytest.mark.asyncio
async def test_trigger_type_serialization(trigger_repository):
    """Test that TriggerType enum is properly serialized."""
    for trigger_type in [
        TriggerType.WEBHOOK,
        TriggerType.SCHEDULED,
        TriggerType.FILE_WATCH,
        TriggerType.EMAIL,
        TriggerType.APP_EVENT,
    ]:
        trigger = BaseTriggerConfig(
            id=f"trig-{trigger_type.value}",
            name=f"Test {trigger_type.value}",
            trigger_type=trigger_type,
            scenario_id="scenario-1",
            workflow_id="wf-1",
        )

        await trigger_repository.save(trigger)
        retrieved = await trigger_repository.get_by_id(f"trig-{trigger_type.value}")

        assert retrieved.trigger_type == trigger_type

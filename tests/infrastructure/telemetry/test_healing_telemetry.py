"""
Tests for Healing Telemetry Service.

Verifies:
- Event recording
- Metrics aggregation
- Fragile selector detection
- Statistics generation
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from casare_rpa.domain.value_objects.selector import SelectorStrategy
from casare_rpa.domain.value_objects.healing_event import (
    HealingEvent,
    HealingTier,
    create_healing_event,
    create_healing_metrics,
)
from casare_rpa.infrastructure.telemetry.healing_telemetry import (
    HealingTelemetryService,
    get_global_telemetry_service,
)


class TestHealingMetrics:
    """Test HealingMetrics value object."""

    def test_create_metrics(self):
        """Test creating healing metrics."""
        metrics = create_healing_metrics(
            selector_id="btn-submit", selector_name="Submit Button"
        )

        assert metrics.selector_id == "btn-submit"
        assert metrics.selector_name == "Submit Button"
        assert metrics.total_uses == 0
        assert metrics.healing_events == 0
        assert metrics.success_rate == 1.0
        assert metrics.fragility_score == 0.0

    def test_record_use(self):
        """Test recording selector use."""
        metrics = create_healing_metrics(selector_id="btn")

        new_metrics = metrics.record_use()

        assert new_metrics.total_uses == 1
        assert new_metrics.healing_events == 0
        assert metrics.total_uses == 0  # Original unchanged

    def test_record_healing_event_tier1_success(self):
        """Test recording tier 1 healing success."""
        metrics = create_healing_metrics(selector_id="btn")

        event = create_healing_event(
            selector_id="btn",
            original_strategy=SelectorStrategy.DATA_TESTID,
            successful_strategy=SelectorStrategy.TEXT,
            tier=HealingTier.TIER_1_HEURISTIC,
            healing_time_ms=50.0,
            workflow_name="Test",
        )

        new_metrics = metrics.record_healing_event(event)

        assert new_metrics.total_uses == 1
        assert new_metrics.healing_events == 1
        assert new_metrics.successful_heals == 1
        assert new_metrics.tier1_successes == 1
        assert new_metrics.success_rate == 1.0
        assert new_metrics.avg_healing_time_ms == 50.0

    def test_record_healing_event_tier2_success(self):
        """Test recording tier 2 healing success."""
        metrics = create_healing_metrics(selector_id="btn")

        event = create_healing_event(
            selector_id="btn",
            original_strategy=SelectorStrategy.DATA_TESTID,
            tier=HealingTier.TIER_2_ANCHOR,
            healing_time_ms=200.0,
            workflow_name="Test",
        )

        new_metrics = metrics.record_healing_event(event)

        assert new_metrics.tier2_successes == 1
        assert new_metrics.successful_heals == 1

    def test_record_healing_event_failure(self):
        """Test recording healing failure."""
        metrics = create_healing_metrics(selector_id="btn")

        event = create_healing_event(
            selector_id="btn",
            original_strategy=SelectorStrategy.DATA_TESTID,
            tier=HealingTier.FAILED,
            healing_time_ms=1000.0,
            workflow_name="Test",
            error_message="All tiers failed",
        )

        new_metrics = metrics.record_healing_event(event)

        assert new_metrics.healing_events == 1
        assert new_metrics.successful_heals == 0
        assert new_metrics.success_rate == 0.0

    def test_fragility_calculation(self):
        """Test fragility score calculation."""
        metrics = create_healing_metrics(selector_id="btn")

        # Record 10 uses, 5 healing events, 4 successes
        for _ in range(5):
            metrics = metrics.record_use()

        # 4 tier 1 successes
        for _ in range(4):
            event = create_healing_event(
                selector_id="btn",
                original_strategy=SelectorStrategy.DATA_TESTID,
                successful_strategy=SelectorStrategy.TEXT,
                tier=HealingTier.TIER_1_HEURISTIC,
                healing_time_ms=50.0,
                workflow_name="Test",
            )
            metrics = metrics.record_healing_event(event)

        # 1 failure
        event = create_healing_event(
            selector_id="btn",
            original_strategy=SelectorStrategy.DATA_TESTID,
            tier=HealingTier.FAILED,
            healing_time_ms=1000.0,
            workflow_name="Test",
        )
        metrics = metrics.record_healing_event(event)

        # healing_frequency = 5/10 = 0.5
        # failure_rate = 1 - 0.8 = 0.2
        # tier_weight = (4 * 0.3) / 4 = 0.3 (all tier 1)
        # fragility = 0.5 * 0.2 * 0.3 = 0.03

        assert metrics.total_uses == 10
        assert metrics.healing_events == 5
        assert metrics.successful_heals == 4
        assert metrics.success_rate == 0.8
        assert metrics.fragility_score < 0.1

    def test_is_fragile(self):
        """Test fragile selector detection."""
        metrics = create_healing_metrics(selector_id="btn")

        # Make it fragile (high healing frequency + tier 3 + some failures)
        for i in range(10):
            if i < 7:
                # 7 tier 3 successes
                event = create_healing_event(
                    selector_id="btn",
                    original_strategy=SelectorStrategy.DATA_TESTID,
                    tier=HealingTier.TIER_3_COMPUTER_VISION,
                    healing_time_ms=500.0,
                    workflow_name="Test",
                )
            else:
                # 3 failures
                event = create_healing_event(
                    selector_id="btn",
                    original_strategy=SelectorStrategy.DATA_TESTID,
                    tier=HealingTier.FAILED,
                    healing_time_ms=1000.0,
                    workflow_name="Test",
                )
            metrics = metrics.record_healing_event(event)

        # fragility should be >= 0.3
        assert metrics.is_fragile(threshold=0.3)


class TestHealingTelemetryService:
    """Test HealingTelemetryService."""

    @pytest.mark.asyncio
    async def test_record_success(self):
        """Test recording successful selector use."""
        service = HealingTelemetryService()

        await service.record_success(
            selector_id="btn-submit", selector_name="Submit Button"
        )

        metrics = await service.get_metrics("btn-submit")

        assert metrics is not None
        assert metrics.total_uses == 1
        assert metrics.healing_events == 0

    @pytest.mark.asyncio
    async def test_record_healing_event(self):
        """Test recording healing event."""
        service = HealingTelemetryService()

        event = create_healing_event(
            selector_id="btn-login",
            selector_name="Login Button",
            original_strategy=SelectorStrategy.DATA_TESTID,
            successful_strategy=SelectorStrategy.TEXT,
            tier=HealingTier.TIER_1_HEURISTIC,
            healing_time_ms=75.5,
            workflow_name="Login Flow",
        )

        await service.record_healing_event(event)

        metrics = await service.get_metrics("btn-login")

        assert metrics is not None
        assert metrics.total_uses == 1
        assert metrics.healing_events == 1
        assert metrics.successful_heals == 1
        assert metrics.avg_healing_time_ms == 75.5

    @pytest.mark.asyncio
    async def test_get_fragile_selectors(self):
        """Test identifying fragile selectors."""
        service = HealingTelemetryService()

        # Create stable selector
        for _ in range(10):
            await service.record_success(selector_id="stable-btn")

        # Create fragile selector
        for i in range(10):
            if i % 2 == 0:
                # Half fail
                event = create_healing_event(
                    selector_id="fragile-btn",
                    original_strategy=SelectorStrategy.DATA_TESTID,
                    tier=HealingTier.FAILED,
                    healing_time_ms=1000.0,
                    workflow_name="Test",
                )
            else:
                # Half succeed with tier 3
                event = create_healing_event(
                    selector_id="fragile-btn",
                    original_strategy=SelectorStrategy.DATA_TESTID,
                    tier=HealingTier.TIER_3_COMPUTER_VISION,
                    healing_time_ms=800.0,
                    workflow_name="Test",
                )

            await service.record_healing_event(event)

        fragile = await service.get_fragile_selectors(threshold=0.3, min_uses=5)

        assert len(fragile) == 1
        assert fragile[0].selector_id == "fragile-btn"

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """Test overall statistics generation."""
        service = HealingTelemetryService()

        # Record some events
        for i in range(5):
            event = create_healing_event(
                selector_id=f"btn-{i}",
                original_strategy=SelectorStrategy.DATA_TESTID,
                successful_strategy=SelectorStrategy.TEXT,
                tier=HealingTier.TIER_1_HEURISTIC,
                healing_time_ms=50.0 + i * 10,
                workflow_name="Test",
            )
            await service.record_healing_event(event)

        stats = await service.get_statistics()

        assert stats["total_selectors"] == 5
        assert stats["total_uses"] == 5
        assert stats["total_healing_events"] == 5
        assert stats["overall_success_rate"] == 1.0
        assert stats["tier_breakdown"]["tier1"] == 5
        assert stats["avg_healing_time_ms"] == 70.0  # (50+60+70+80+90)/5

    @pytest.mark.asyncio
    async def test_export_import_metrics(self):
        """Test exporting and importing metrics."""
        service = HealingTelemetryService()

        # Record some data
        event = create_healing_event(
            selector_id="btn-export",
            original_strategy=SelectorStrategy.DATA_TESTID,
            tier=HealingTier.TIER_1_HEURISTIC,
            healing_time_ms=100.0,
            workflow_name="Test",
        )
        await service.record_healing_event(event)

        # Export
        data = await service.export_metrics()

        assert "metrics" in data
        assert "events" in data
        assert "btn-export" in data["metrics"]

        # Import into new service
        new_service = HealingTelemetryService()
        await new_service.import_metrics(data)

        metrics = await new_service.get_metrics("btn-export")

        assert metrics is not None
        assert metrics.healing_events == 1

    @pytest.mark.asyncio
    async def test_clear_old_events(self):
        """Test clearing old events."""
        service = HealingTelemetryService()

        # Create old event (manually set timestamp)
        old_event = HealingEvent(
            selector_id="btn-old",
            original_strategy=SelectorStrategy.DATA_TESTID,
            tier=HealingTier.TIER_1_HEURISTIC,
            healing_time_ms=50.0,
            workflow_name="Test",
            timestamp=datetime.now() - timedelta(days=60),
        )

        # Create recent event
        recent_event = create_healing_event(
            selector_id="btn-recent",
            original_strategy=SelectorStrategy.DATA_TESTID,
            tier=HealingTier.TIER_1_HEURISTIC,
            healing_time_ms=50.0,
            workflow_name="Test",
        )

        await service.record_healing_event(old_event)
        await service.record_healing_event(recent_event)

        # Clear events older than 30 days
        removed = await service.clear_old_events(days=30)

        assert removed == 1

        # Check recent events
        recent = await service.get_recent_events(hours=24 * 7)
        assert len(recent) == 1
        assert recent[0].selector_id == "btn-recent"

    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test thread-safe concurrent access."""
        service = HealingTelemetryService()

        async def record_events(selector_id: str, count: int):
            for _ in range(count):
                event = create_healing_event(
                    selector_id=selector_id,
                    original_strategy=SelectorStrategy.DATA_TESTID,
                    tier=HealingTier.TIER_1_HEURISTIC,
                    healing_time_ms=50.0,
                    workflow_name="Concurrent Test",
                )
                await service.record_healing_event(event)

        # Run 3 tasks concurrently
        await asyncio.gather(
            record_events("btn-1", 10),
            record_events("btn-2", 15),
            record_events("btn-1", 5),  # Same selector
        )

        metrics1 = await service.get_metrics("btn-1")
        metrics2 = await service.get_metrics("btn-2")

        assert metrics1.healing_events == 15  # 10 + 5
        assert metrics2.healing_events == 15

    def test_global_telemetry_service(self):
        """Test global singleton telemetry service."""
        service1 = get_global_telemetry_service()
        service2 = get_global_telemetry_service()

        assert service1 is service2  # Same instance

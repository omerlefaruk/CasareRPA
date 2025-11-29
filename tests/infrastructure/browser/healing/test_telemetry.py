"""
Tests for Healing Telemetry.

These tests verify the telemetry collection, statistics calculation,
and event tracking for self-healing selectors.
"""

import pytest
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from casare_rpa.infrastructure.browser.healing.telemetry import (
    HealingEvent,
    HealingTelemetry,
    HealingTier,
    SelectorStats,
    get_healing_telemetry,
    reset_healing_telemetry,
)


class TestHealingTier:
    """Tests for HealingTier enum."""

    def test_all_tiers_defined(self) -> None:
        """Verify all expected tiers exist."""
        expected = ["ORIGINAL", "HEURISTIC", "ANCHOR", "CV", "FAILED"]
        for tier in expected:
            assert hasattr(HealingTier, tier)

    def test_tier_values(self) -> None:
        """Verify tier string values."""
        assert HealingTier.ORIGINAL.value == "original"
        assert HealingTier.HEURISTIC.value == "heuristic"
        assert HealingTier.ANCHOR.value == "anchor"
        assert HealingTier.CV.value == "cv"
        assert HealingTier.FAILED.value == "failed"


class TestHealingEvent:
    """Tests for HealingEvent dataclass."""

    def test_event_creation(self) -> None:
        """Verify event creation with required fields."""
        event = HealingEvent(
            timestamp=time.time(),
            selector="#button",
            page_url="https://example.com",
            success=True,
            tier_used=HealingTier.HEURISTIC,
            healing_time_ms=45.5,
            healed_selector='button:has-text("Submit")',
            confidence=0.85,
        )

        assert event.selector == "#button"
        assert event.success is True
        assert event.tier_used == HealingTier.HEURISTIC
        assert event.healing_time_ms == 45.5

    def test_event_serialization(self) -> None:
        """Verify event dict serialization."""
        event = HealingEvent(
            timestamp=1700000000.0,
            selector="#test",
            page_url="https://example.com",
            success=True,
            tier_used=HealingTier.ANCHOR,
            healing_time_ms=50.0,
            tiers_attempted=["original", "heuristic", "anchor"],
        )

        data = event.to_dict()

        assert data["selector"] == "#test"
        assert data["success"] is True
        assert data["tier_used"] == "anchor"
        assert data["healing_time_ms"] == 50.0
        assert "datetime" in data


class TestSelectorStats:
    """Tests for SelectorStats dataclass."""

    def test_success_rate_calculation(self) -> None:
        """Verify success rate calculation."""
        stats = SelectorStats(
            selector="#button",
            total_uses=100,
            original_successes=70,
            healed_successes=20,
            failures=10,
        )

        assert stats.success_rate == 0.9  # 90% success

    def test_healing_rate_calculation(self) -> None:
        """Verify healing rate calculation."""
        stats = SelectorStats(
            selector="#button",
            total_uses=100,
            original_successes=70,
            healed_successes=20,
            failures=10,
        )

        assert stats.healing_rate == 0.3  # 30% needed healing

    def test_healing_success_rate_calculation(self) -> None:
        """Verify healing success rate when healing is attempted."""
        stats = SelectorStats(
            selector="#button",
            total_uses=100,
            original_successes=70,
            healed_successes=20,
            failures=10,
        )

        # 20 healed + 10 failed = 30 healing attempts
        # 20/30 = 66.67% healing success
        assert abs(stats.healing_success_rate - 0.6667) < 0.01

    def test_empty_stats(self) -> None:
        """Verify handling of empty stats."""
        stats = SelectorStats(selector="#button")

        assert stats.success_rate == 0.0
        assert stats.healing_rate == 0.0
        assert stats.healing_success_rate == 0.0


class TestHealingTelemetry:
    """Tests for HealingTelemetry class."""

    def test_initialization(self) -> None:
        """Verify default initialization."""
        telemetry = HealingTelemetry()
        assert telemetry._total_uses == 0
        assert len(telemetry._events) == 0

    def test_record_original_success(self) -> None:
        """Verify recording original selector success."""
        telemetry = HealingTelemetry()

        event = telemetry.record_event(
            selector="#button",
            page_url="https://example.com",
            success=True,
            tier_used=HealingTier.ORIGINAL,
            healing_time_ms=0.0,
        )

        assert event.success is True
        assert event.tier_used == HealingTier.ORIGINAL
        assert telemetry._total_uses == 1
        assert telemetry._total_original_success == 1

    def test_record_healed_success(self) -> None:
        """Verify recording healed selector success."""
        telemetry = HealingTelemetry()

        telemetry.record_event(
            selector="#button",
            page_url="https://example.com",
            success=True,
            tier_used=HealingTier.HEURISTIC,
            healing_time_ms=30.0,
            healed_selector='button:has-text("Submit")',
            confidence=0.8,
        )

        assert telemetry._total_uses == 1
        assert telemetry._total_healed_success == 1
        assert telemetry._tier_successes["heuristic"] == 1

    def test_record_failure(self) -> None:
        """Verify recording healing failure."""
        telemetry = HealingTelemetry()

        telemetry.record_event(
            selector="#broken",
            page_url="https://example.com",
            success=False,
            tier_used=HealingTier.FAILED,
            healing_time_ms=400.0,
            error_message="All tiers failed",
        )

        assert telemetry._total_uses == 1
        assert telemetry._total_failures == 1

    def test_overall_stats(self) -> None:
        """Verify overall statistics calculation."""
        telemetry = HealingTelemetry()

        # Record mix of events
        for _ in range(70):
            telemetry.record_event(
                selector="#btn",
                page_url="https://example.com",
                success=True,
                tier_used=HealingTier.ORIGINAL,
                healing_time_ms=0.0,
            )

        for _ in range(20):
            telemetry.record_event(
                selector="#btn",
                page_url="https://example.com",
                success=True,
                tier_used=HealingTier.HEURISTIC,
                healing_time_ms=50.0,
            )

        for _ in range(10):
            telemetry.record_event(
                selector="#btn",
                page_url="https://example.com",
                success=False,
                tier_used=HealingTier.FAILED,
                healing_time_ms=400.0,
            )

        stats = telemetry.get_overall_stats()

        assert stats["total_uses"] == 100
        assert stats["original_successes"] == 70
        assert stats["healed_successes"] == 20
        assert stats["failures"] == 10
        assert stats["success_rate"] == 90.0

    def test_tier_stats(self) -> None:
        """Verify per-tier statistics."""
        telemetry = HealingTelemetry()

        telemetry.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#b", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#c", "url", True, HealingTier.HEURISTIC, 30.0)
        telemetry.record_event("#d", "url", True, HealingTier.ANCHOR, 60.0)

        tier_stats = telemetry.get_tier_stats()

        assert tier_stats["original"]["count"] == 2
        assert tier_stats["heuristic"]["count"] == 1
        assert tier_stats["anchor"]["count"] == 1

    def test_selector_stats(self) -> None:
        """Verify per-selector statistics tracking."""
        telemetry = HealingTelemetry()

        # Same selector, multiple uses
        telemetry.record_event("#btn", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#btn", "url", True, HealingTier.HEURISTIC, 30.0)
        telemetry.record_event("#btn", "url", False, HealingTier.FAILED, 400.0)

        stats = telemetry.get_selector_stats("#btn")

        assert stats is not None
        assert stats.total_uses == 3
        assert stats.original_successes == 1
        assert stats.healed_successes == 1
        assert stats.failures == 1

    def test_problematic_selectors(self) -> None:
        """Verify identification of problematic selectors."""
        telemetry = HealingTelemetry()

        # Good selector - 100% success
        for _ in range(10):
            telemetry.record_event("#good", "url", True, HealingTier.ORIGINAL, 0.0)

        # Bad selector - 50% success
        for _ in range(5):
            telemetry.record_event("#bad", "url", True, HealingTier.ORIGINAL, 0.0)
        for _ in range(5):
            telemetry.record_event("#bad", "url", False, HealingTier.FAILED, 400.0)

        problematic = telemetry.get_problematic_selectors(
            min_uses=5, max_success_rate=0.8
        )

        assert len(problematic) == 1
        assert problematic[0].selector == "#bad"

    def test_recent_events(self) -> None:
        """Verify getting recent events."""
        telemetry = HealingTelemetry()

        for i in range(10):
            telemetry.record_event(f"#sel{i}", "url", True, HealingTier.ORIGINAL, 0.0)

        recent = telemetry.get_recent_events(limit=5)
        assert len(recent) == 5
        assert recent[0].selector == "#sel5"  # Oldest in the slice

    def test_recent_events_filtered(self) -> None:
        """Verify filtered recent events."""
        telemetry = HealingTelemetry()

        telemetry.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#b", "url", False, HealingTier.FAILED, 400.0)
        telemetry.record_event("#c", "url", True, HealingTier.HEURISTIC, 30.0)

        failures = telemetry.get_recent_events(success_only=False)
        assert len(failures) == 1
        assert failures[0].selector == "#b"

    def test_export_report(self) -> None:
        """Verify report export."""
        telemetry = HealingTelemetry()

        telemetry.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#b", "url", True, HealingTier.ANCHOR, 50.0)

        report = telemetry.export_report()

        assert "generated_at" in report
        assert "overall" in report
        assert "tier_breakdown" in report
        assert report["overall"]["total_uses"] == 2

    def test_reset(self) -> None:
        """Verify telemetry reset."""
        telemetry = HealingTelemetry()

        telemetry.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)
        telemetry.record_event("#b", "url", True, HealingTier.ORIGINAL, 0.0)

        assert telemetry._total_uses == 2

        telemetry.reset()

        assert telemetry._total_uses == 0
        assert len(telemetry._events) == 0
        assert len(telemetry._selector_stats) == 0

    def test_event_limit(self) -> None:
        """Verify event count limit."""
        telemetry = HealingTelemetry(max_events=10)

        for i in range(20):
            telemetry.record_event(f"#sel{i}", "url", True, HealingTier.ORIGINAL, 0.0)

        assert len(telemetry._events) == 10
        # Should have the most recent events
        assert telemetry._events[0].selector == "#sel10"

    def test_persistence(self) -> None:
        """Verify telemetry save and load."""
        with TemporaryDirectory() as tmpdir:
            storage_path = Path(tmpdir) / "telemetry.json"

            # Create and populate telemetry
            telemetry1 = HealingTelemetry(storage_path=storage_path)
            telemetry1.record_event("#a", "url", True, HealingTier.ORIGINAL, 0.0)
            telemetry1.record_event("#b", "url", True, HealingTier.HEURISTIC, 30.0)
            telemetry1.save()

            # Load in new instance
            telemetry2 = HealingTelemetry(storage_path=storage_path)

            assert telemetry2._total_uses == 2
            assert telemetry2._total_original_success == 1
            assert telemetry2._total_healed_success == 1


class TestGlobalTelemetry:
    """Tests for global telemetry instance."""

    def test_get_global_instance(self) -> None:
        """Verify getting global instance."""
        reset_healing_telemetry()

        instance1 = get_healing_telemetry()
        instance2 = get_healing_telemetry()

        assert instance1 is instance2

    def test_reset_global_instance(self) -> None:
        """Verify resetting global instance."""
        instance1 = get_healing_telemetry()
        reset_healing_telemetry()
        instance2 = get_healing_telemetry()

        assert instance1 is not instance2

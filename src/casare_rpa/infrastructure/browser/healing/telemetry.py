"""
Healing Telemetry for Self-Healing Selectors.

Tracks success rates, performance metrics, and healing patterns across all tiers.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger


class HealingTier(Enum):
    """Healing strategy tiers."""

    ORIGINAL = "original"
    """Original selector worked without healing."""

    HEURISTIC = "heuristic"
    """Tier 1: Heuristic-based healing (attribute fallbacks)."""

    ANCHOR = "anchor"
    """Tier 2: Anchor-based spatial healing."""

    CV = "cv"
    """Tier 3: Computer vision fallback (OCR + template matching)."""

    VISION = "vision"
    """Tier 4: Vision AI fallback (GPT-4V/Claude Vision)."""

    FAILED = "failed"
    """All healing attempts failed."""


@dataclass
class HealingEvent:
    """
    Record of a single healing attempt.

    Captures what happened when a selector was used, including
    whether it needed healing and which tier succeeded.
    """

    timestamp: float
    """Unix timestamp of the event."""

    selector: str
    """Original selector that was attempted."""

    page_url: str
    """URL of the page."""

    success: bool
    """Whether element was ultimately found."""

    tier_used: HealingTier
    """Which tier succeeded (or FAILED)."""

    healing_time_ms: float
    """Time spent on healing in milliseconds."""

    healed_selector: str | None = None
    """The selector that worked (if healed)."""

    confidence: float = 1.0
    """Confidence score of the healed selector."""

    tiers_attempted: list[str] = field(default_factory=list)
    """List of tiers that were attempted."""

    error_message: str | None = None
    """Error message if failed."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "selector": self.selector,
            "page_url": self.page_url,
            "success": self.success,
            "tier_used": self.tier_used.value,
            "healing_time_ms": self.healing_time_ms,
            "healed_selector": self.healed_selector,
            "confidence": self.confidence,
            "tiers_attempted": self.tiers_attempted,
            "error_message": self.error_message,
        }


@dataclass
class SelectorStats:
    """
    Aggregated statistics for a specific selector.

    Tracks healing history and patterns for a single selector.
    """

    selector: str
    """The selector string."""

    total_uses: int = 0
    """Total times this selector was used."""

    original_successes: int = 0
    """Times the original selector worked."""

    healed_successes: int = 0
    """Times healing was needed and succeeded."""

    failures: int = 0
    """Times all attempts failed."""

    tier_usage: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    """Count of successes by tier."""

    avg_healing_time_ms: float = 0.0
    """Average healing time when healing was needed."""

    last_healed_selector: str | None = None
    """Most recent healed selector."""

    last_used: float = 0.0
    """Timestamp of last use."""

    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_uses == 0:
            return 0.0
        return (self.original_successes + self.healed_successes) / self.total_uses

    @property
    def healing_rate(self) -> float:
        """Calculate how often healing is needed."""
        if self.total_uses == 0:
            return 0.0
        return (self.healed_successes + self.failures) / self.total_uses

    @property
    def healing_success_rate(self) -> float:
        """Calculate healing success rate when healing is attempted."""
        attempted = self.healed_successes + self.failures
        if attempted == 0:
            return 0.0
        return self.healed_successes / attempted

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "selector": self.selector,
            "total_uses": self.total_uses,
            "original_successes": self.original_successes,
            "healed_successes": self.healed_successes,
            "failures": self.failures,
            "success_rate": round(self.success_rate * 100, 2),
            "healing_rate": round(self.healing_rate * 100, 2),
            "healing_success_rate": round(self.healing_success_rate * 100, 2),
            "tier_usage": dict(self.tier_usage),
            "avg_healing_time_ms": round(self.avg_healing_time_ms, 2),
            "last_healed_selector": self.last_healed_selector,
            "last_used": self.last_used,
        }


class HealingTelemetry:
    """
    Telemetry collector for self-healing selectors.

    Tracks healing events, calculates statistics, and provides insights
    for monitoring and debugging selector health.

    Example:
        telemetry = HealingTelemetry()

        # Record a successful original selector
        telemetry.record_event(
            selector="#submit-btn",
            page_url="https://example.com/form",
            success=True,
            tier_used=HealingTier.ORIGINAL,
            healing_time_ms=0.0
        )

        # Record a healed selector
        telemetry.record_event(
            selector="#submit-btn",
            page_url="https://example.com/form",
            success=True,
            tier_used=HealingTier.ANCHOR,
            healing_time_ms=45.0,
            healed_selector='label:has-text("Submit") >> button'
        )

        # Get statistics
        stats = telemetry.get_overall_stats()
        logger.info(f"Success rate: {stats['success_rate']}%")
    """

    def __init__(
        self,
        storage_path: Path | None = None,
        max_events: int = 10000,
        retention_days: int = 30,
    ) -> None:
        """
        Initialize telemetry collector.

        Args:
            storage_path: Path to persist telemetry data.
            max_events: Maximum events to keep in memory.
            retention_days: Days to retain events.
        """
        self._storage_path = storage_path
        self._max_events = max_events
        self._retention_days = retention_days

        self._events: list[HealingEvent] = []
        self._selector_stats: dict[str, SelectorStats] = {}

        # Aggregate counters
        self._total_uses = 0
        self._total_original_success = 0
        self._total_healed_success = 0
        self._total_failures = 0
        self._tier_successes: dict[str, int] = defaultdict(int)
        self._total_healing_time_ms = 0.0

        if storage_path and storage_path.exists():
            self._load()

    def record_event(
        self,
        selector: str,
        page_url: str,
        success: bool,
        tier_used: HealingTier,
        healing_time_ms: float,
        healed_selector: str | None = None,
        confidence: float = 1.0,
        tiers_attempted: list[str] | None = None,
        error_message: str | None = None,
    ) -> HealingEvent:
        """
        Record a healing event.

        Args:
            selector: Original selector attempted.
            page_url: URL of the page.
            success: Whether element was found.
            tier_used: Which tier succeeded.
            healing_time_ms: Time spent healing.
            healed_selector: Selector that worked (if healed).
            confidence: Confidence of healed selector.
            tiers_attempted: List of attempted tiers.
            error_message: Error if failed.

        Returns:
            The recorded HealingEvent.
        """
        event = HealingEvent(
            timestamp=time.time(),
            selector=selector,
            page_url=page_url,
            success=success,
            tier_used=tier_used,
            healing_time_ms=healing_time_ms,
            healed_selector=healed_selector,
            confidence=confidence,
            tiers_attempted=tiers_attempted or [],
            error_message=error_message,
        )

        self._events.append(event)
        self._update_stats(event)

        # Evict old events if over limit
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

        logger.debug(
            f"Telemetry: {selector} -> {tier_used.value} "
            f"(success={success}, time={healing_time_ms:.1f}ms)"
        )

        return event

    def _update_stats(self, event: HealingEvent) -> None:
        """Update statistics from an event."""
        self._total_uses += 1

        if event.success:
            if event.tier_used == HealingTier.ORIGINAL:
                self._total_original_success += 1
            else:
                self._total_healed_success += 1
                self._total_healing_time_ms += event.healing_time_ms

            self._tier_successes[event.tier_used.value] += 1
        else:
            self._total_failures += 1

        # Update selector-specific stats
        if event.selector not in self._selector_stats:
            self._selector_stats[event.selector] = SelectorStats(selector=event.selector)

        stats = self._selector_stats[event.selector]
        stats.total_uses += 1
        stats.last_used = event.timestamp

        if event.success:
            if event.tier_used == HealingTier.ORIGINAL:
                stats.original_successes += 1
            else:
                stats.healed_successes += 1
                stats.last_healed_selector = event.healed_selector

                # Update average healing time
                healed_count = stats.healed_successes
                old_avg = stats.avg_healing_time_ms
                stats.avg_healing_time_ms = (
                    old_avg * (healed_count - 1) + event.healing_time_ms
                ) / healed_count

            stats.tier_usage[event.tier_used.value] += 1
        else:
            stats.failures += 1

    def get_selector_stats(self, selector: str) -> SelectorStats | None:
        """Get statistics for a specific selector."""
        return self._selector_stats.get(selector)

    def get_overall_stats(self) -> dict[str, Any]:
        """
        Get overall healing statistics.

        Returns:
            Dictionary with aggregate statistics.
        """
        success_rate = 0.0
        healing_rate = 0.0
        healing_success_rate = 0.0
        avg_healing_time = 0.0

        if self._total_uses > 0:
            total_success = self._total_original_success + self._total_healed_success
            success_rate = (total_success / self._total_uses) * 100

            healing_attempts = self._total_healed_success + self._total_failures
            if healing_attempts > 0:
                healing_rate = (healing_attempts / self._total_uses) * 100
                healing_success_rate = (self._total_healed_success / healing_attempts) * 100
                avg_healing_time = self._total_healing_time_ms / max(1, self._total_healed_success)

        return {
            "total_uses": self._total_uses,
            "original_successes": self._total_original_success,
            "healed_successes": self._total_healed_success,
            "failures": self._total_failures,
            "success_rate": round(success_rate, 2),
            "healing_rate": round(healing_rate, 2),
            "healing_success_rate": round(healing_success_rate, 2),
            "avg_healing_time_ms": round(avg_healing_time, 2),
            "tier_breakdown": dict(self._tier_successes),
            "unique_selectors": len(self._selector_stats),
            "events_recorded": len(self._events),
        }

    def get_tier_stats(self) -> dict[str, dict[str, Any]]:
        """
        Get statistics broken down by healing tier.

        Returns:
            Dictionary with per-tier statistics.
        """
        tier_stats: dict[str, dict[str, Any]] = {}

        for tier in HealingTier:
            count = self._tier_successes.get(tier.value, 0)
            tier_stats[tier.value] = {
                "count": count,
                "percentage": round((count / max(1, self._total_uses)) * 100, 2),
            }

        return tier_stats

    def get_problematic_selectors(
        self,
        min_uses: int = 5,
        max_success_rate: float = 0.8,
    ) -> list[SelectorStats]:
        """
        Get selectors that frequently need healing or fail.

        Args:
            min_uses: Minimum uses to be considered.
            max_success_rate: Maximum success rate to be flagged.

        Returns:
            List of problematic selector stats, sorted by failure rate.
        """
        problematic = []

        for stats in self._selector_stats.values():
            if stats.total_uses >= min_uses and stats.success_rate <= max_success_rate:
                problematic.append(stats)

        problematic.sort(key=lambda s: s.success_rate)
        return problematic

    def get_recent_events(
        self,
        limit: int = 100,
        selector: str | None = None,
        success_only: bool | None = None,
    ) -> list[HealingEvent]:
        """
        Get recent healing events.

        Args:
            limit: Maximum events to return.
            selector: Filter by selector.
            success_only: Filter by success status.

        Returns:
            List of recent events.
        """
        events = self._events.copy()

        if selector:
            events = [e for e in events if e.selector == selector]

        if success_only is not None:
            events = [e for e in events if e.success == success_only]

        return events[-limit:]

    def cleanup_old_events(self) -> int:
        """
        Remove events older than retention period.

        Returns:
            Number of events removed.
        """
        cutoff = time.time() - (self._retention_days * 24 * 60 * 60)
        original_count = len(self._events)

        self._events = [e for e in self._events if e.timestamp >= cutoff]

        removed = original_count - len(self._events)
        if removed > 0:
            logger.info(f"Cleaned up {removed} old telemetry events")

        return removed

    def export_report(self) -> dict[str, Any]:
        """
        Export a comprehensive telemetry report.

        Returns:
            Dictionary with full report data.
        """
        problematic = self.get_problematic_selectors()

        return {
            "generated_at": datetime.now().isoformat(),
            "overall": self.get_overall_stats(),
            "tier_breakdown": self.get_tier_stats(),
            "problematic_selectors": [s.to_dict() for s in problematic[:20]],
            "recent_failures": [
                e.to_dict() for e in self.get_recent_events(limit=50, success_only=False)
            ],
        }

    def _load(self) -> None:
        """Load telemetry from storage."""
        if not self._storage_path or not self._storage_path.exists():
            return

        try:
            with open(self._storage_path, encoding="utf-8") as f:
                data = json.load(f)

            self._total_uses = data.get("total_uses", 0)
            self._total_original_success = data.get("total_original_success", 0)
            self._total_healed_success = data.get("total_healed_success", 0)
            self._total_failures = data.get("total_failures", 0)
            self._tier_successes = defaultdict(int, data.get("tier_successes", {}))
            self._total_healing_time_ms = data.get("total_healing_time_ms", 0.0)

            logger.info(f"Loaded telemetry: {self._total_uses} recorded uses")

        except Exception as e:
            logger.warning(f"Failed to load telemetry: {e}")

    def save(self) -> None:
        """Save telemetry to storage."""
        if not self._storage_path:
            return

        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "total_uses": self._total_uses,
                "total_original_success": self._total_original_success,
                "total_healed_success": self._total_healed_success,
                "total_failures": self._total_failures,
                "tier_successes": dict(self._tier_successes),
                "total_healing_time_ms": self._total_healing_time_ms,
                "saved_at": datetime.now().isoformat(),
            }

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved telemetry to {self._storage_path}")

        except Exception as e:
            logger.warning(f"Failed to save telemetry: {e}")

    def reset(self) -> None:
        """Reset all telemetry data."""
        self._events.clear()
        self._selector_stats.clear()
        self._total_uses = 0
        self._total_original_success = 0
        self._total_healed_success = 0
        self._total_failures = 0
        self._tier_successes.clear()
        self._total_healing_time_ms = 0.0
        logger.info("Telemetry reset")


# Global telemetry instance
_global_telemetry: HealingTelemetry | None = None


def get_healing_telemetry(storage_path: Path | None = None) -> HealingTelemetry:
    """Get or create the global telemetry instance."""
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = HealingTelemetry(storage_path=storage_path)
    return _global_telemetry


def reset_healing_telemetry() -> None:
    """Reset the global telemetry instance."""
    global _global_telemetry
    _global_telemetry = None


__all__ = [
    "HealingTier",
    "HealingEvent",
    "SelectorStats",
    "HealingTelemetry",
    "get_healing_telemetry",
    "reset_healing_telemetry",
]

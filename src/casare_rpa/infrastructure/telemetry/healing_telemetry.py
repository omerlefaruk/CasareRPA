"""
CasareRPA - Infrastructure: Healing Telemetry Service

Collects and aggregates selector healing metrics.
Identifies fragile selectors and provides insights for workflow maintenance.
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger

from casare_rpa.domain.value_objects.healing_event import (
    HealingEvent,
    HealingMetrics,
    HealingTier,
    create_healing_metrics,
)
from casare_rpa.domain.value_objects.selector import SelectorStrategy


class HealingTelemetryService:
    """
    Service for collecting and analyzing selector healing telemetry.

    Features:
    - Records healing events
    - Aggregates metrics per selector
    - Identifies fragile selectors
    - Provides healing statistics

    Thread-safe for concurrent workflow execution.
    """

    def __init__(self):
        """Initialize telemetry service."""
        self._metrics: Dict[str, HealingMetrics] = {}
        self._events: List[HealingEvent] = []
        self._lock = asyncio.Lock()

    async def record_success(
        self, selector_id: str, selector_name: Optional[str] = None
    ) -> None:
        """
        Record successful selector use (no healing needed).

        Args:
            selector_id: Selector ID
            selector_name: Selector name (optional)
        """
        async with self._lock:
            if selector_id not in self._metrics:
                self._metrics[selector_id] = create_healing_metrics(
                    selector_id=selector_id, selector_name=selector_name
                )

            # Record use
            self._metrics[selector_id] = self._metrics[selector_id].record_use()

    async def record_healing_event(self, event: HealingEvent) -> None:
        """
        Record a healing event and update metrics.

        Args:
            event: Healing event to record
        """
        async with self._lock:
            # Store event
            self._events.append(event)

            # Initialize metrics if needed
            if event.selector_id not in self._metrics:
                self._metrics[event.selector_id] = create_healing_metrics(
                    selector_id=event.selector_id, selector_name=event.selector_name
                )

            # Update metrics
            self._metrics[event.selector_id] = self._metrics[
                event.selector_id
            ].record_healing_event(event)

            # Log if selector is becoming fragile
            metrics = self._metrics[event.selector_id]
            if metrics.is_fragile():
                logger.warning(
                    f"[Telemetry] Selector '{event.selector_id}' is fragile - "
                    f"fragility score: {metrics.fragility_score:.2f}, "
                    f"success rate: {metrics.success_rate:.1%}"
                )

    async def get_metrics(self, selector_id: str) -> Optional[HealingMetrics]:
        """
        Get metrics for a specific selector.

        Args:
            selector_id: Selector ID

        Returns:
            HealingMetrics or None if not found
        """
        async with self._lock:
            return self._metrics.get(selector_id)

    async def get_all_metrics(self) -> Dict[str, HealingMetrics]:
        """
        Get metrics for all selectors.

        Returns:
            Dictionary of selector_id -> HealingMetrics
        """
        async with self._lock:
            return self._metrics.copy()

    async def get_fragile_selectors(
        self, threshold: float = 0.3, min_uses: int = 5
    ) -> List[HealingMetrics]:
        """
        Get list of fragile selectors.

        Args:
            threshold: Fragility threshold (default 0.3)
            min_uses: Minimum uses to consider (default 5)

        Returns:
            List of HealingMetrics for fragile selectors, sorted by fragility
        """
        async with self._lock:
            fragile = [
                metrics
                for metrics in self._metrics.values()
                if metrics.total_uses >= min_uses and metrics.is_fragile(threshold)
            ]

            # Sort by fragility score descending
            fragile.sort(key=lambda m: m.fragility_score, reverse=True)

            return fragile

    async def get_recent_events(
        self, hours: int = 24, selector_id: Optional[str] = None
    ) -> List[HealingEvent]:
        """
        Get recent healing events.

        Args:
            hours: Number of hours to look back (default 24)
            selector_id: Filter by selector ID (optional)

        Returns:
            List of HealingEvents
        """
        async with self._lock:
            cutoff = datetime.now() - timedelta(hours=hours)

            events = [event for event in self._events if event.timestamp >= cutoff]

            if selector_id:
                events = [e for e in events if e.selector_id == selector_id]

            return events

    async def get_statistics(self) -> Dict:
        """
        Get overall healing statistics.

        Returns:
            Dictionary with statistics:
            - total_selectors: Total unique selectors
            - total_uses: Total selector uses
            - total_healing_events: Total healing events
            - overall_success_rate: Overall healing success rate
            - fragile_selectors_count: Number of fragile selectors
            - tier_breakdown: Successes by tier
            - avg_healing_time_ms: Average healing time
        """
        async with self._lock:
            if not self._metrics:
                return {
                    "total_selectors": 0,
                    "total_uses": 0,
                    "total_healing_events": 0,
                    "overall_success_rate": 0.0,
                    "fragile_selectors_count": 0,
                    "tier_breakdown": {"tier1": 0, "tier2": 0, "tier3": 0},
                    "avg_healing_time_ms": 0.0,
                }

            total_uses = sum(m.total_uses for m in self._metrics.values())
            total_healing_events = sum(m.healing_events for m in self._metrics.values())
            total_successful_heals = sum(
                m.successful_heals for m in self._metrics.values()
            )

            overall_success_rate = (
                total_successful_heals / total_healing_events
                if total_healing_events > 0
                else 1.0
            )

            fragile_count = sum(
                1
                for m in self._metrics.values()
                if m.total_uses >= 5 and m.is_fragile()
            )

            # Tier breakdown
            tier1_total = sum(m.tier1_successes for m in self._metrics.values())
            tier2_total = sum(m.tier2_successes for m in self._metrics.values())
            tier3_total = sum(m.tier3_successes for m in self._metrics.values())

            # Average healing time (weighted by healing events)
            if total_healing_events > 0:
                total_time = sum(
                    m.avg_healing_time_ms * m.healing_events
                    for m in self._metrics.values()
                )
                avg_healing_time = total_time / total_healing_events
            else:
                avg_healing_time = 0.0

            return {
                "total_selectors": len(self._metrics),
                "total_uses": total_uses,
                "total_healing_events": total_healing_events,
                "overall_success_rate": overall_success_rate,
                "fragile_selectors_count": fragile_count,
                "tier_breakdown": {
                    "tier1": tier1_total,
                    "tier2": tier2_total,
                    "tier3": tier3_total,
                },
                "avg_healing_time_ms": avg_healing_time,
            }

    async def export_metrics(self) -> Dict:
        """
        Export all metrics and events for persistence.

        Returns:
            Dictionary with metrics and events
        """
        async with self._lock:
            return {
                "metrics": {
                    selector_id: metrics.to_dict()
                    for selector_id, metrics in self._metrics.items()
                },
                "events": [event.to_dict() for event in self._events],
                "exported_at": datetime.now().isoformat(),
            }

    async def import_metrics(self, data: Dict) -> None:
        """
        Import metrics and events from persistence.

        Args:
            data: Dictionary from export_metrics()
        """
        async with self._lock:
            # Import metrics
            self._metrics = {
                selector_id: HealingMetrics.from_dict(metrics_dict)
                for selector_id, metrics_dict in data.get("metrics", {}).items()
            }

            # Import events
            from casare_rpa.domain.value_objects.healing_event import HealingEvent

            self._events = [
                HealingEvent(**event_dict) for event_dict in data.get("events", [])
            ]

            logger.info(
                f"[Telemetry] Imported {len(self._metrics)} metrics and "
                f"{len(self._events)} events"
            )

    async def clear_old_events(self, days: int = 30) -> int:
        """
        Clear events older than specified days.

        Args:
            days: Number of days to keep (default 30)

        Returns:
            Number of events removed
        """
        async with self._lock:
            cutoff = datetime.now() - timedelta(days=days)
            original_count = len(self._events)

            self._events = [
                event for event in self._events if event.timestamp >= cutoff
            ]

            removed = original_count - len(self._events)

            if removed > 0:
                logger.info(
                    f"[Telemetry] Removed {removed} events older than {days} days"
                )

            return removed


# ============================================================================
# Global Singleton (optional)
# ============================================================================

_global_telemetry_service: Optional[HealingTelemetryService] = None


def get_global_telemetry_service() -> HealingTelemetryService:
    """
    Get global telemetry service singleton.

    Returns:
        Global HealingTelemetryService instance
    """
    global _global_telemetry_service

    if _global_telemetry_service is None:
        _global_telemetry_service = HealingTelemetryService()
        logger.debug("[Telemetry] Initialized global telemetry service")

    return _global_telemetry_service


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "HealingTelemetryService",
    "get_global_telemetry_service",
]

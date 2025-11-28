"""
CasareRPA - Domain Value Object: Healing Event

Events and metrics for selector healing telemetry.
Used to track healing success rates and fragile selectors.

This is PURE domain - no infrastructure dependencies.
"""

from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from .selector import SelectorStrategy


class HealingTier(str, Enum):
    """Healing tier that successfully found the element."""

    TIER_1_HEURISTIC = "tier_1_heuristic"  # Multi-attribute fallback
    TIER_2_ANCHOR = "tier_2_anchor"  # Anchor-based navigation
    TIER_3_COMPUTER_VISION = "tier_3_cv"  # Template matching
    FAILED = "failed"  # All tiers failed


class HealingEvent(BaseModel):
    """
    Event captured when selector healing occurs.

    Used for telemetry and learning which selectors are fragile.

    Example:
        HealingEvent(
            selector_id="btn-submit",
            original_strategy=SelectorStrategy.DATA_TESTID,
            successful_strategy=SelectorStrategy.TEXT,
            tier=HealingTier.TIER_1_HEURISTIC,
            healing_time_ms=45.2,
            workflow_name="Order Processing"
        )
    """

    # Selector identification
    selector_id: str = Field(..., description="ID of healed selector")
    selector_name: Optional[str] = Field(
        None, description="Human-readable selector name"
    )

    # Healing details
    original_strategy: SelectorStrategy = Field(
        ..., description="Strategy that failed (primary)"
    )
    successful_strategy: Optional[SelectorStrategy] = Field(
        None, description="Strategy that succeeded (or None if all failed)"
    )
    tier: HealingTier = Field(..., description="Healing tier that succeeded")

    # Performance
    healing_time_ms: float = Field(..., description="Time taken to heal (milliseconds)")
    attempts: int = Field(default=1, description="Number of healing attempts")

    # Context
    workflow_name: str = Field(..., description="Workflow where healing occurred")
    node_id: Optional[str] = Field(None, description="Node ID that triggered healing")
    url: Optional[str] = Field(None, description="Page URL where healing occurred")

    # Timestamp
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Event timestamp"
    )

    # Error details (if failed)
    error_message: Optional[str] = Field(
        None, description="Error message if healing failed"
    )

    class Config:
        frozen = True  # Immutable event

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode="json")


class HealingMetrics(BaseModel):
    """
    Aggregated metrics for a specific selector.

    Tracks success rates, average healing time, and fragility score.

    Example:
        HealingMetrics(
            selector_id="btn-submit",
            total_uses=100,
            healing_events=15,
            success_rate=0.867,
            avg_healing_time_ms=52.3,
            fragility_score=0.15
        )
    """

    # Selector identification
    selector_id: str = Field(..., description="Selector ID")
    selector_name: Optional[str] = Field(None, description="Selector name")

    # Usage stats
    total_uses: int = Field(default=0, description="Total times selector was used")
    healing_events: int = Field(default=0, description="Times healing was triggered")
    successful_heals: int = Field(default=0, description="Times healing succeeded")

    # Performance metrics
    success_rate: float = Field(
        default=1.0, description="Healing success rate (0.0-1.0)"
    )
    avg_healing_time_ms: float = Field(
        default=0.0, description="Average healing time in milliseconds"
    )

    # Tier breakdown
    tier1_successes: int = Field(default=0, description="Tier 1 successes")
    tier2_successes: int = Field(default=0, description="Tier 2 successes")
    tier3_successes: int = Field(default=0, description="Tier 3 successes")

    # Fragility
    fragility_score: float = Field(
        default=0.0, description="Fragility score (0.0-1.0, higher = more fragile)"
    )

    # Timestamps
    last_used: datetime = Field(
        default_factory=datetime.now, description="Last time selector was used"
    )
    last_healing: Optional[datetime] = Field(
        None, description="Last time healing occurred"
    )

    class Config:
        frozen = False  # Mutable for aggregation
        validate_assignment = True

    def record_use(self) -> "HealingMetrics":
        """
        Record a selector use (no healing needed).

        Returns:
            Updated metrics
        """
        return self.model_copy(
            update={"total_uses": self.total_uses + 1, "last_used": datetime.now()}
        )

    def record_healing_event(self, event: HealingEvent) -> "HealingMetrics":
        """
        Record a healing event and update metrics.

        Args:
            event: Healing event to record

        Returns:
            Updated metrics
        """
        new_total_uses = self.total_uses + 1
        new_healing_events = self.healing_events + 1

        # Update tier counters
        tier1 = self.tier1_successes
        tier2 = self.tier2_successes
        tier3 = self.tier3_successes
        new_successful_heals = self.successful_heals

        if event.tier == HealingTier.TIER_1_HEURISTIC:
            tier1 += 1
            new_successful_heals += 1
        elif event.tier == HealingTier.TIER_2_ANCHOR:
            tier2 += 1
            new_successful_heals += 1
        elif event.tier == HealingTier.TIER_3_COMPUTER_VISION:
            tier3 += 1
            new_successful_heals += 1

        # Calculate new averages
        new_success_rate = (
            new_successful_heals / new_healing_events if new_healing_events > 0 else 1.0
        )

        # Update average healing time
        total_time = self.avg_healing_time_ms * self.healing_events
        new_avg_time = (
            (total_time + event.healing_time_ms) / new_healing_events
            if new_healing_events > 0
            else event.healing_time_ms
        )

        # Calculate fragility score
        # Formula: (healing_events / total_uses) * (1 - success_rate) * tier_weight
        healing_frequency = new_healing_events / new_total_uses
        failure_rate = 1.0 - new_success_rate

        # Weight by which tier succeeded (tier 3 = more fragile)
        tier_weight = 1.0
        if new_successful_heals > 0:
            tier_weight = (
                tier1 * 0.3 + tier2 * 0.6 + tier3 * 1.0
            ) / new_successful_heals

        new_fragility = healing_frequency * failure_rate * tier_weight

        return self.model_copy(
            update={
                "total_uses": new_total_uses,
                "healing_events": new_healing_events,
                "successful_heals": new_successful_heals,
                "success_rate": new_success_rate,
                "avg_healing_time_ms": new_avg_time,
                "tier1_successes": tier1,
                "tier2_successes": tier2,
                "tier3_successes": tier3,
                "fragility_score": new_fragility,
                "last_used": datetime.now(),
                "last_healing": event.timestamp,
            }
        )

    def is_fragile(self, threshold: float = 0.3) -> bool:
        """
        Check if selector is considered fragile.

        Args:
            threshold: Fragility threshold (default 0.3)

        Returns:
            True if fragility score exceeds threshold
        """
        return self.fragility_score > threshold

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, data: dict) -> "HealingMetrics":
        """Deserialize from dictionary."""
        return cls(**data)


# ============================================================================
# Factory Functions
# ============================================================================


def create_healing_event(
    selector_id: str,
    original_strategy: SelectorStrategy,
    tier: HealingTier,
    healing_time_ms: float,
    workflow_name: str,
    successful_strategy: Optional[SelectorStrategy] = None,
    selector_name: Optional[str] = None,
    node_id: Optional[str] = None,
    url: Optional[str] = None,
    error_message: Optional[str] = None,
) -> HealingEvent:
    """
    Create a healing event.

    Args:
        selector_id: Selector ID
        original_strategy: Strategy that failed
        tier: Healing tier that succeeded
        healing_time_ms: Healing time in milliseconds
        workflow_name: Workflow name
        successful_strategy: Strategy that succeeded (optional)
        selector_name: Selector name (optional)
        node_id: Node ID (optional)
        url: Page URL (optional)
        error_message: Error message if failed (optional)

    Returns:
        HealingEvent instance
    """
    return HealingEvent(
        selector_id=selector_id,
        selector_name=selector_name,
        original_strategy=original_strategy,
        successful_strategy=successful_strategy,
        tier=tier,
        healing_time_ms=healing_time_ms,
        workflow_name=workflow_name,
        node_id=node_id,
        url=url,
        error_message=error_message,
    )


def create_healing_metrics(
    selector_id: str, selector_name: Optional[str] = None
) -> HealingMetrics:
    """
    Create initial healing metrics for a selector.

    Args:
        selector_id: Selector ID
        selector_name: Selector name (optional)

    Returns:
        HealingMetrics instance with zero stats
    """
    return HealingMetrics(selector_id=selector_id, selector_name=selector_name)


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "HealingTier",
    "HealingEvent",
    "HealingMetrics",
    "create_healing_event",
    "create_healing_metrics",
]

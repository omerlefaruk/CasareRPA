"""
Self-Healing Selector Infrastructure.

Provides a tiered self-healing system for web automation selectors:

Tier 1 (Heuristic): Multi-attribute fallback using element fingerprints
Tier 2 (Anchor): Spatial relationship-based healing using stable anchors
Tier 3 (CV): Computer vision fallback using OCR and template matching

Usage:
    from casare_rpa.infrastructure.browser.healing import (
        SelectorHealingChain,
        create_healing_chain,
    )

    # Create healing chain with CV fallback enabled
    chain = create_healing_chain(
        healing_budget_ms=400,
        cv_budget_ms=2000,
        enable_cv=True
    )

    # Capture context during recording
    await chain.capture_element_context(page, "#submit-btn")

    # Use during playback
    result = await chain.locate_element(page, "#submit-btn")
    if result.success:
        if result.is_cv_result:
            # CV healing returns coordinates, not element
            coords = result.cv_click_coordinates
            await page.mouse.click(coords[0], coords[1])
        else:
            await result.element.click()

    # Get statistics
    stats = chain.get_stats()
    print(f"Success rate: {stats['success_rate']}%")
"""

from casare_rpa.infrastructure.browser.healing.models import (
    AnchorElement,
    AnchorHealingResult,
    BoundingRect,
    SpatialContext,
    SpatialRelation,
)
from casare_rpa.infrastructure.browser.healing.anchor_healer import (
    AnchorHealer,
)
from casare_rpa.infrastructure.browser.healing.cv_healer import (
    CVContext,
    CVHealer,
    CVHealingResult,
    CVStrategy,
    OCRMatch,
    TemplateMatch,
)
from casare_rpa.infrastructure.browser.healing.telemetry import (
    HealingEvent,
    HealingTelemetry,
    HealingTier,
    SelectorStats,
    get_healing_telemetry,
    reset_healing_telemetry,
)
from casare_rpa.infrastructure.browser.healing.healing_chain import (
    HealingChainResult,
    SelectorHealingChain,
    create_healing_chain,
)


__all__ = [
    # Models
    "AnchorElement",
    "AnchorHealingResult",
    "BoundingRect",
    "SpatialContext",
    "SpatialRelation",
    # Anchor Healer
    "AnchorHealer",
    # CV Healer
    "CVContext",
    "CVHealer",
    "CVHealingResult",
    "CVStrategy",
    "OCRMatch",
    "TemplateMatch",
    # Telemetry
    "HealingEvent",
    "HealingTelemetry",
    "HealingTier",
    "SelectorStats",
    "get_healing_telemetry",
    "reset_healing_telemetry",
    # Healing Chain
    "HealingChainResult",
    "SelectorHealingChain",
    "create_healing_chain",
]

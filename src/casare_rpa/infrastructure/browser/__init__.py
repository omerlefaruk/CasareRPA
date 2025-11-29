"""
Browser infrastructure components.

Contains browser-specific infrastructure including:
- Self-healing selectors (heuristic, anchor-based, CV fallback)
- Browser resource management
"""

from casare_rpa.infrastructure.browser.healing import (
    AnchorHealer,
    HealingTelemetry,
    SelectorHealingChain,
    SpatialRelation,
    AnchorElement,
    AnchorHealingResult,
)

__all__ = [
    "AnchorHealer",
    "HealingTelemetry",
    "SelectorHealingChain",
    "SpatialRelation",
    "AnchorElement",
    "AnchorHealingResult",
]

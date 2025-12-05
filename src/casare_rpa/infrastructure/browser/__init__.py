"""
Browser infrastructure components.

Contains browser-specific infrastructure including:
- Self-healing selectors (heuristic, anchor-based, CV fallback)
- Browser resource management
- Browser action recording
"""

from casare_rpa.infrastructure.browser.healing import (
    AnchorHealer,
    HealingTelemetry,
    SelectorHealingChain,
    SpatialRelation,
    AnchorElement,
    AnchorHealingResult,
)
from casare_rpa.infrastructure.browser.browser_recorder import (
    BrowserActionType,
    BrowserRecordedAction,
    BrowserRecorder,
    BrowserWorkflowGenerator,
)

__all__ = [
    # Healing
    "AnchorHealer",
    "HealingTelemetry",
    "SelectorHealingChain",
    "SpatialRelation",
    "AnchorElement",
    "AnchorHealingResult",
    # Recording
    "BrowserActionType",
    "BrowserRecordedAction",
    "BrowserRecorder",
    "BrowserWorkflowGenerator",
]

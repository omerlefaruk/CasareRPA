"""
Browser infrastructure components.

Contains browser-specific infrastructure including:
- Playwright lifecycle management (PlaywrightManager singleton)
- Self-healing selectors (heuristic, anchor-based, CV fallback)
- Browser resource management
- Browser action recording
"""

from casare_rpa.infrastructure.browser.browser_recorder import (
    BrowserActionType,
    BrowserRecordedAction,
    BrowserRecorder,
    BrowserWorkflowGenerator,
)
from casare_rpa.infrastructure.browser.healing import (
    AnchorElement,
    AnchorHealer,
    AnchorHealingResult,
    HealingTelemetry,
    SelectorHealingChain,
    SpatialRelation,
)
from casare_rpa.infrastructure.browser.playwright_manager import (
    PlaywrightManager,
    get_playwright_singleton,
    shutdown_playwright_singleton,
)

__all__ = [
    # Playwright Manager
    "PlaywrightManager",
    "get_playwright_singleton",
    "shutdown_playwright_singleton",
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

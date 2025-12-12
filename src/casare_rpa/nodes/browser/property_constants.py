"""
Common PropertyDef constants for browser automation nodes.

Provides reusable PropertyDef definitions to ensure consistency
across all browser-related nodes (navigation, interaction, data, wait).

Usage:
    from casare_rpa.nodes.browser.property_constants import (
        BROWSER_TIMEOUT,
        BROWSER_RETRY_COUNT,
        BROWSER_SELECTOR,
    )

    @properties(
        BROWSER_SELECTOR,
        BROWSER_TIMEOUT,
        BROWSER_RETRY_COUNT,
        PropertyDef("custom_prop", PropertyType.STRING, default=""),
    )
    @node(category="browser")
    class MyBrowserNode(BrowserBaseNode):
        ...
"""

from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.decorators import node, properties
from casare_rpa.config import DEFAULT_NODE_TIMEOUT, DEFAULT_PAGE_LOAD_TIMEOUT


# =============================================================================
# Core Timeout and Retry Properties
# =============================================================================

BROWSER_TIMEOUT = PropertyDef(
    "timeout",
    PropertyType.INTEGER,
    default=DEFAULT_NODE_TIMEOUT * 1000,
    label="Timeout (ms)",
    tooltip="Maximum time to wait in milliseconds",
    min_value=0,
)

BROWSER_PAGE_LOAD_TIMEOUT = PropertyDef(
    "timeout",
    PropertyType.INTEGER,
    default=DEFAULT_PAGE_LOAD_TIMEOUT,
    label="Timeout (ms)",
    tooltip="Page load timeout in milliseconds",
    min_value=0,
)

BROWSER_RETRY_COUNT = PropertyDef(
    "retry_count",
    PropertyType.INTEGER,
    default=0,
    label="Retry Count",
    tooltip="Number of retries on failure (0 = no retry)",
    min_value=0,
)

BROWSER_RETRY_INTERVAL = PropertyDef(
    "retry_interval",
    PropertyType.INTEGER,
    default=1000,
    label="Retry Interval (ms)",
    tooltip="Delay between retries in milliseconds",
    min_value=0,
)


# =============================================================================
# Screenshot Properties
# =============================================================================

BROWSER_SCREENSHOT_ON_FAIL = PropertyDef(
    "screenshot_on_fail",
    PropertyType.BOOLEAN,
    default=False,
    label="Screenshot on Fail",
    tooltip="Take screenshot when operation fails",
)

BROWSER_SCREENSHOT_PATH = PropertyDef(
    "screenshot_path",
    PropertyType.FILE_PATH,
    default="",
    label="Screenshot Path",
    tooltip="Path for failure screenshot (auto-generated if empty)",
    placeholder="screenshots/error.png",
)


# =============================================================================
# Selector Properties
# =============================================================================

BROWSER_SELECTOR = PropertyDef(
    "selector",
    PropertyType.SELECTOR,
    default="",
    required=False,
    label="Element Selector",
    tooltip="CSS or XPath selector for the element",
    placeholder="#element-id or //button[@name='submit']",
)

BROWSER_SELECTOR_STRICT = PropertyDef(
    "strict",
    PropertyType.BOOLEAN,
    default=False,
    label="Strict",
    tooltip="Require exactly one matching element",
)


# =============================================================================
# Anchor Properties (for reliable element location)
# =============================================================================

BROWSER_ANCHOR_CONFIG = PropertyDef(
    "anchor_config",
    PropertyType.JSON,
    default="",
    label="Anchor Configuration",
    tooltip="JSON config for anchor-based element location (set via Element Selector dialog)",
    tab="advanced",
)


# =============================================================================
# Navigation Properties
# =============================================================================

BROWSER_WAIT_UNTIL = PropertyDef(
    "wait_until",
    PropertyType.CHOICE,
    default="load",
    choices=["load", "domcontentloaded", "networkidle", "commit"],
    label="Wait Until",
    tooltip="Navigation event to wait for",
)


# =============================================================================
# Action Properties
# =============================================================================

BROWSER_FORCE = PropertyDef(
    "force",
    PropertyType.BOOLEAN,
    default=False,
    label="Force",
    tooltip="Bypass actionability checks",
)

BROWSER_NO_WAIT_AFTER = PropertyDef(
    "no_wait_after",
    PropertyType.BOOLEAN,
    default=False,
    label="No Wait After",
    tooltip="Skip waiting for navigations after action",
)


# =============================================================================
# Visual Feedback Properties
# =============================================================================

BROWSER_HIGHLIGHT = PropertyDef(
    "highlight_before_action",
    PropertyType.BOOLEAN,
    default=False,
    label="Highlight Element",
    tooltip="Briefly highlight element before action (debugging)",
)


# =============================================================================
# Element State Properties (for wait operations)
# =============================================================================

BROWSER_ELEMENT_STATE = PropertyDef(
    "state",
    PropertyType.CHOICE,
    default="visible",
    choices=["visible", "hidden", "attached", "detached"],
    label="State",
    tooltip="Element state to wait for",
)


# =============================================================================
# Helper to create common property groups
# =============================================================================


def get_retry_properties() -> list[PropertyDef]:
    """Get standard retry properties (retry_count, retry_interval)."""
    return [BROWSER_RETRY_COUNT, BROWSER_RETRY_INTERVAL]


def get_screenshot_properties() -> list[PropertyDef]:
    """Get standard screenshot-on-fail properties."""
    return [BROWSER_SCREENSHOT_ON_FAIL, BROWSER_SCREENSHOT_PATH]


def get_selector_properties() -> list[PropertyDef]:
    """Get standard selector properties (selector, strict)."""
    return [BROWSER_SELECTOR, BROWSER_SELECTOR_STRICT]


def get_action_properties() -> list[PropertyDef]:
    """Get standard action properties (force, no_wait_after)."""
    return [BROWSER_FORCE, BROWSER_NO_WAIT_AFTER]

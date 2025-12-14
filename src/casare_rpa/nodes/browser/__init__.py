"""
Browser automation nodes package.

This package provides browser automation nodes built on Playwright:
- Browser lifecycle (launch, close) - imported from browser_nodes
- Tab management (new tab, switch tab)
- Navigation (goto, back, forward, refresh)
- Interaction (click, type, select)
- Data extraction (text, attributes, screenshots)
- Wait operations (element, navigation)

All nodes extend BrowserBaseNode for consistent:
- Page access from context
- Selector normalization
- Retry logic
- Screenshot on failure
- Error handling
"""

from casare_rpa.nodes.browser.browser_base import (
    BrowserBaseNode,
    get_page_from_context,
    take_failure_screenshot,
)
from casare_rpa.nodes.browser.property_constants import (
    # Core properties
    BROWSER_TIMEOUT,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    # Selector properties
    BROWSER_SELECTOR,
    BROWSER_SELECTOR_STRICT,
    # Navigation properties
    BROWSER_WAIT_UNTIL,
    # Action properties
    BROWSER_FORCE,
    BROWSER_NO_WAIT_AFTER,
    # Highlight
    BROWSER_HIGHLIGHT,
)
from casare_rpa.nodes.browser.smart_selector_node import (
    SmartSelectorNode,
    SmartSelectorOptionsNode,
    RefineSelectorNode,
)

# New modules
from casare_rpa.nodes.browser.lifecycle import (
    LaunchBrowserNode,
    CloseBrowserNode,
)
from casare_rpa.nodes.browser.tabs import (
    NewTabNode,
)
from casare_rpa.nodes.browser.navigation import (
    GoToURLNode,
    GoBackNode,
    GoForwardNode,
    RefreshPageNode,
)
from casare_rpa.nodes.browser.interaction import (
    ClickElementNode,
    TypeTextNode,
    SelectDropdownNode,
    ImageClickNode,
    PressKeyNode,
)
from casare_rpa.nodes.browser.extraction_nodes import (
    GetAllImagesNode,
    DownloadFileNode,
)
from casare_rpa.nodes.browser.evaluate_node import BrowserEvaluateNode

__all__ = [
    # Base class
    "BrowserBaseNode",
    # Utility functions
    "get_page_from_context",
    "take_failure_screenshot",
    # Property constants
    "BROWSER_TIMEOUT",
    "BROWSER_RETRY_COUNT",
    "BROWSER_RETRY_INTERVAL",
    "BROWSER_SCREENSHOT_ON_FAIL",
    "BROWSER_SCREENSHOT_PATH",
    "BROWSER_SELECTOR",
    "BROWSER_SELECTOR_STRICT",
    "BROWSER_WAIT_UNTIL",
    "BROWSER_FORCE",
    "BROWSER_NO_WAIT_AFTER",
    "BROWSER_HIGHLIGHT",
    # Smart selector nodes
    "SmartSelectorNode",
    "SmartSelectorOptionsNode",
    "RefineSelectorNode",
    # Lifecycle
    "LaunchBrowserNode",
    "CloseBrowserNode",
    # Tabs
    "NewTabNode",
    # Navigation
    "GoToURLNode",
    "GoBackNode",
    "GoForwardNode",
    "RefreshPageNode",
    # Interaction
    "ClickElementNode",
    "TypeTextNode",
    "SelectDropdownNode",
    "ImageClickNode",
    "PressKeyNode",
    # Extraction
    "GetAllImagesNode",
    "DownloadFileNode",
    # Evaluate
    "BrowserEvaluateNode",
]

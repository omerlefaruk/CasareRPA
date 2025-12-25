"""
Browser automation nodes package.

This package provides browser automation nodes built on Playwright:
- Browser lifecycle (launch, close)
- Tab management (new tab, switch tab)
- Navigation (goto, back, forward, refresh)
- Interaction (click, type, select)
- Data extraction (text, attributes, screenshots)

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
from casare_rpa.nodes.browser.evaluate_node import BrowserEvaluateNode
from casare_rpa.nodes.browser.extraction_nodes import (
    DownloadFileNode,
    GetAllImagesNode,
)
from casare_rpa.nodes.browser.interaction import (
    ClickElementNode,
    ImageClickNode,
    PressKeyNode,
    SelectDropdownNode,
    TypeTextNode,
)

# New modules
from casare_rpa.nodes.browser.lifecycle import (
    CloseBrowserNode,
    LaunchBrowserNode,
)
from casare_rpa.nodes.browser.navigation import (
    GoBackNode,
    GoForwardNode,
    GoToURLNode,
    RefreshPageNode,
)
from casare_rpa.nodes.browser.property_constants import (
    # Action properties
    BROWSER_FORCE,
    # Highlight
    BROWSER_HIGHLIGHT,
    BROWSER_NO_WAIT_AFTER,
    BROWSER_RETRY_COUNT,
    BROWSER_RETRY_INTERVAL,
    BROWSER_SCREENSHOT_ON_FAIL,
    BROWSER_SCREENSHOT_PATH,
    # Selector properties
    BROWSER_SELECTOR,
    BROWSER_SELECTOR_STRICT,
    # Core properties
    BROWSER_TIMEOUT,
    # Navigation properties
    BROWSER_WAIT_UNTIL,
)
from casare_rpa.nodes.browser.smart_selector_node import (
    RefineSelectorNode,
    SmartSelectorNode,
    SmartSelectorOptionsNode,
)
from casare_rpa.nodes.browser.tabs import (
    NewTabNode,
)

# Alert and Cookie management
from casare_rpa.nodes.browser.alert_handle_node import (
    BrowserAlertHandleNode,
)
from casare_rpa.nodes.browser.cookie_management_node import (
    CookieManagementNode,
)

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
    # Alert and Cookie management
    "BrowserAlertHandleNode",
    "CookieManagementNode",
]

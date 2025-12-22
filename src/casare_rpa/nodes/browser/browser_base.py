"""
Base class for browser automation nodes.

Provides shared functionality for all Playwright-based nodes:
- Page access from context (input port or active page)
- Selector normalization (XPath, CSS, ARIA)
- Retry logic with configurable attempts and intervals
- Screenshot capture on failure
- Consistent error handling and logging
- Browser context pool integration for performance

PERFORMANCE: Browser pool integration provides:
- Pre-warmed browser contexts for faster launches
- Context reuse to avoid setup overhead
- Automatic cleanup and resource management
- Pool sizing based on workload

Usage:
    from casare_rpa.nodes.browser.browser_base import BrowserBaseNode

    @properties(BROWSER_SELECTOR, BROWSER_TIMEOUT, ...)
    @node(category="browser")
    class MyBrowserNode(BrowserBaseNode):
        async def execute(self, context: ExecutionContext) -> ExecutionResult:
            page = self.get_page(context)
            selector = self.get_normalized_selector(context)
            # ... node logic ...
"""

import asyncio
import os
from abc import ABC
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, TypeVar, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.config import DEFAULT_NODE_TIMEOUT

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext
    from casare_rpa.utils.pooling.browser_pool import BrowserPoolManager


T = TypeVar("T")

# Resource key for storing BrowserPoolManager in ExecutionContext
BROWSER_POOL_RESOURCE_KEY = "_browser_pool_manager"

# Global healing chain instance (lazy initialized)
_healing_chain = None


# =============================================================================
# Browser Pool Integration
# =============================================================================


async def get_browser_pool_from_context(
    context: "ExecutionContext",
    min_size: int = 1,
    max_size: int = 5,
) -> "BrowserPoolManager":
    """
    Get or create BrowserPoolManager from ExecutionContext resources.

    The pool is stored in context.resources for reuse across all browser nodes
    in the workflow execution. This ensures:
    - Pre-warmed browser contexts for faster launches
    - Context reuse to avoid setup overhead
    - Automatic cleanup at workflow end

    Args:
        context: ExecutionContext for the workflow
        min_size: Minimum number of browser contexts in pool
        max_size: Maximum number of browser contexts in pool

    Returns:
        BrowserPoolManager instance (shared across all browser nodes)
    """
    from casare_rpa.utils.pooling.browser_pool import BrowserPoolManager

    if BROWSER_POOL_RESOURCE_KEY not in context.resources:
        pool = BrowserPoolManager(min_size=min_size, max_size=max_size)
        await pool.initialize()
        context.resources[BROWSER_POOL_RESOURCE_KEY] = pool
        logger.debug(
            f"Created BrowserPoolManager for workflow execution "
            f"(min={min_size}, max={max_size})"
        )

    return context.resources[BROWSER_POOL_RESOURCE_KEY]


async def acquire_browser_context_from_pool(
    context: "ExecutionContext",
    headless: bool = True,
    user_agent: Optional[str] = None,
    viewport: Optional[dict] = None,
    **options: Any,
) -> tuple[Any, str]:
    """
    Acquire a browser context from the pool.

    The context is checked out from the pool and should be released
    back when no longer needed via release_browser_context_to_pool().

    Args:
        context: ExecutionContext for the workflow
        headless: Whether to run browser in headless mode
        user_agent: Custom user agent string
        viewport: Custom viewport size {"width": int, "height": int}
        **options: Additional browser context options

    Returns:
        Tuple of (BrowserContext, context_id) for tracking
    """
    pool = await get_browser_pool_from_context(context)

    browser_context, context_id = await pool.acquire(
        headless=headless,
        user_agent=user_agent,
        viewport=viewport,
        **options,
    )

    logger.debug(f"Acquired browser context from pool: {context_id}")
    return browser_context, context_id


async def release_browser_context_to_pool(
    context: "ExecutionContext",
    context_id: str,
    clean: bool = True,
) -> None:
    """
    Release a browser context back to the pool.

    The context is returned to the pool for reuse. If clean=True,
    the context is cleaned (cookies cleared, storage reset) before reuse.

    Args:
        context: ExecutionContext for the workflow
        context_id: ID of the browser context to release
        clean: Whether to clean the context before returning to pool
    """
    if BROWSER_POOL_RESOURCE_KEY not in context.resources:
        logger.warning("Browser pool not found in context, cannot release")
        return

    pool = context.resources[BROWSER_POOL_RESOURCE_KEY]
    await pool.release(context_id, clean=clean)
    logger.debug(f"Released browser context to pool: {context_id}")


async def close_browser_pool_from_context(context: "ExecutionContext") -> None:
    """
    Close BrowserPoolManager stored in ExecutionContext.

    Called automatically during ExecutionContext.cleanup().

    Args:
        context: ExecutionContext for the workflow
    """
    if BROWSER_POOL_RESOURCE_KEY in context.resources:
        pool = context.resources[BROWSER_POOL_RESOURCE_KEY]
        if pool is not None:
            await pool.shutdown()
            logger.debug("Closed BrowserPoolManager for workflow execution")
        del context.resources[BROWSER_POOL_RESOURCE_KEY]


def get_healing_chain():
    """Get or create the global healing chain instance."""
    global _healing_chain
    if _healing_chain is None:
        try:
            from casare_rpa.infrastructure.browser.healing.healing_chain import (
                SelectorHealingChain,
            )

            _healing_chain = SelectorHealingChain(enable_cv_fallback=True)
            logger.info("Initialized global healing chain with CV fallback")
        except Exception as e:
            logger.warning(f"Failed to initialize healing chain: {e}")
    return _healing_chain


class PlaywrightError(Exception):
    """Base exception for Playwright-related errors in browser nodes."""

    def __init__(
        self,
        message: str,
        selector: Optional[str] = None,
        timeout: Optional[int] = None,
        attempts: int = 1,
    ):
        super().__init__(message)
        self.selector = selector
        self.timeout = timeout
        self.attempts = attempts


class ElementNotFoundError(PlaywrightError):
    """Raised when element cannot be found within timeout."""

    pass


class PageNotAvailableError(PlaywrightError):
    """Raised when no page instance is available."""

    pass


async def get_page_from_context(
    browser_node: "BrowserBaseNode",
    context: "ExecutionContext",
    port_name: str = "page",
) -> Any:
    """
    Get page instance from input port or context.

    Standard pattern for all browser nodes to access the active page.

    Args:
        browser_node: The browser node instance
        context: Execution context
        port_name: Name of the page input port (default: "page")

    Returns:
        Playwright Page instance

    Raises:
        PageNotAvailableError: If no page is available
    """
    page = browser_node.get_input_value(port_name)
    if page is None:
        page = context.get_active_page()

    if page is None:
        raise PageNotAvailableError("No page instance found. Launch browser and navigate first.")

    return page


async def take_failure_screenshot(
    page: Any,
    screenshot_path: str = "",
    prefix: str = "failure",
) -> Optional[str]:
    """
    Take a screenshot on failure for debugging.

    Args:
        page: Playwright Page instance
        screenshot_path: Custom path for screenshot (auto-generated if empty)
        prefix: Prefix for auto-generated filename

    Returns:
        Path where screenshot was saved, or None if failed
    """
    if not page:
        return None

    try:
        if screenshot_path:
            path = screenshot_path
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{prefix}_{timestamp}.png"

        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        await page.screenshot(path=path)
        logger.info(f"Failure screenshot saved: {path}")
        return path

    except Exception as e:
        logger.warning(f"Failed to take screenshot: {e}")
        return None


async def highlight_element(
    page: Any,
    selector: str,
    timeout: int = 5000,
    color: str = "#ff0000",
    duration: float = 0.3,
) -> None:
    """
    Briefly highlight an element before action (for debugging).

    Args:
        page: Playwright Page instance
        selector: Normalized selector for element
        timeout: Max time to wait for element
        color: Highlight outline color
        duration: How long to show highlight in seconds
    """
    try:
        element = await page.wait_for_selector(selector, timeout=timeout)
        if element:
            await element.evaluate(
                f"""
                el => {{
                    const original = el.style.outline;
                    el.style.outline = '3px solid {color}';
                    setTimeout(() => {{ el.style.outline = original; }}, {int(duration * 1000)});
                }}
                """
            )
            await asyncio.sleep(duration)
    except Exception:
        pass  # Ignore highlight errors


@properties()
@node(category="browser")
class BrowserBaseNode(BaseNode, ABC):
    """
    Abstract base class for browser automation nodes.

    Provides common functionality for Playwright-based operations:
    - Page retrieval from context
    - Selector normalization
    - Retry logic
    - Screenshot on failure
    - Standard input/output port patterns

    Subclasses should:
    1. Define ports in _define_ports()
    2. Implement execute() using helper methods
    3. Use @properties with property constants
    """

    # @category: browser
    # @requires: none
    # @ports: none -> none

    def __init__(self, node_id: str, config: Optional[dict] = None, **kwargs: Any) -> None:
        """
        Initialize browser base node.

        Args:
            node_id: Unique identifier for this node
            config: Node configuration (from @properties defaults + user config)
            **kwargs: Additional arguments (name, etc.)
        """
        super().__init__(node_id, config or {})
        self.name = kwargs.get("name", self.__class__.__name__)
        self.node_type = self.__class__.__name__

    # =========================================================================
    # Page Access
    # =========================================================================

    def get_page(self, context: "ExecutionContext") -> Any:
        """
        Get page from input port or context (sync wrapper for common pattern).

        NOTE: For async contexts, prefer using get_page_async().

        Args:
            context: Execution context

        Returns:
            Playwright Page instance

        Raises:
            PageNotAvailableError: If no page is available
        """
        # Debug: Check input port first
        page = self.get_input_value("page")
        logger.debug(
            f"BrowserBaseNode.get_page ({self.__class__.__name__}): "
            f"input_port_page={page is not None}"
        )

        if page is None:
            logger.debug(
                f"BrowserBaseNode.get_page ({self.__class__.__name__}): "
                f"falling back to context.get_active_page(), context_id={id(context)}"
            )
            page = context.get_active_page()

        if page is None:
            logger.error(
                f"BrowserBaseNode.get_page ({self.__class__.__name__}): "
                f"NO PAGE FOUND! context_id={id(context)}, "
                f"context.pages={list(context.pages.keys()) if hasattr(context, 'pages') else 'N/A'}"
            )
            raise PageNotAvailableError(
                "No page instance found. Launch browser and navigate first."
            )

        return page

    async def get_page_async(self, context: "ExecutionContext") -> Any:
        """
        Get page from input port or context (async version).

        Args:
            context: Execution context

        Returns:
            Playwright Page instance

        Raises:
            PageNotAvailableError: If no page is available
        """
        return await get_page_from_context(self, context)

    # =========================================================================
    # Selector Handling
    # =========================================================================

    def get_normalized_selector(
        self,
        context: "ExecutionContext",
        param_name: str = "selector",
    ) -> str:
        """
        Get selector parameter, resolve variables, and normalize for Playwright.

        Uses the unified SelectorFacade for consistent normalization across
        all browser nodes (CSS, XPath, UiPath XML, wildcards, etc.).

        Args:
            context: Execution context (for variable resolution)
            param_name: Parameter name containing selector

        Returns:
            Normalized selector string ready for Playwright

        Raises:
            ValueError: If selector is required but empty
        """
        from casare_rpa.utils.selectors import get_selector_facade

        # Get selector from parameter (auto-resolves variables via get_parameter)
        selector = self.get_parameter(param_name, "")

        if not selector or not str(selector).strip():
            raise ValueError(
                f"Selector parameter '{param_name}' is required but empty. "
                f"Provide a valid CSS, XPath, or text selector."
            )

        # Normalize using unified facade
        return get_selector_facade().normalize(str(selector).strip())

    def get_optional_normalized_selector(
        self,
        context: "ExecutionContext",
        param_name: str = "selector",
    ) -> Optional[str]:
        """
        Get optional selector parameter, resolve variables, and normalize.

        Unlike get_normalized_selector(), returns None if selector is empty.
        Uses the unified SelectorFacade for consistent normalization.

        Args:
            context: Execution context
            param_name: Parameter name containing selector

        Returns:
            Normalized selector string, or None if empty
        """
        from casare_rpa.utils.selectors import get_selector_facade

        # Get selector from parameter (auto-resolves variables via get_parameter)
        selector = self.get_parameter(param_name, "")

        if not selector or not str(selector).strip():
            return None

        # Normalize using unified facade
        return get_selector_facade().normalize(str(selector).strip())

    def get_healing_context(self, param_name: str = "selector") -> Optional[dict]:
        """
        Get healing context for a selector parameter.

        The healing context is stored alongside the selector when captured
        via the Unified Selector Dialog and contains:
        - fingerprint: Element attributes for heuristic matching
        - spatial: Anchor element relationships
        - cv_template: Base64 encoded element screenshot for CV matching

        Args:
            param_name: Parameter name of the selector

        Returns:
            Healing context dict, or None if not available
        """
        healing_key = f"{param_name}_healing_context"
        return self.get_parameter(healing_key, None)

    def get_anchor_config(self):
        """
        Get anchor configuration from node parameters.

        Returns:
            NodeAnchorConfig instance (may have enabled=False if not configured)
        """
        from casare_rpa.nodes.browser.anchor_config import NodeAnchorConfig

        anchor_json = self.get_parameter("anchor_config", "")
        return NodeAnchorConfig.from_json(anchor_json)

    async def find_element_with_anchor(
        self,
        page: Any,
        selector: str,
        anchor_config,
        timeout_ms: int = 5000,
    ) -> Optional[Any]:
        """
        Find element using anchor-based location.

        Uses anchor element as a stable reference point to find the target element.
        Falls back to direct selector if anchor fails.

        Args:
            page: Playwright Page instance
            selector: Target element selector
            anchor_config: NodeAnchorConfig instance
            timeout_ms: Timeout in milliseconds

        Returns:
            ElementHandle if found, None otherwise
        """
        if not anchor_config or not anchor_config.is_valid:
            return None

        try:
            from casare_rpa.utils.selectors.anchor_locator import AnchorLocator

            locator = AnchorLocator()

            # First verify anchor exists
            anchor_element = await page.query_selector(anchor_config.selector)
            if not anchor_element:
                logger.warning(
                    f"Anchor element not found: {anchor_config.selector}, "
                    f"falling back to direct selector"
                )
                return None

            logger.info(
                f"Using anchor '{anchor_config.display_text}' "
                f"(position={anchor_config.position}) to find target"
            )

            # Use anchor to find target
            element = await locator.find_element_with_anchor(
                page=page,
                target_selector=selector,
                anchor_selector=anchor_config.selector,
                position=anchor_config.position,
                offset_x=anchor_config.offset_x,
                offset_y=anchor_config.offset_y,
            )

            if element:
                logger.info(f"Found target element via anchor: {anchor_config.selector}")
                return element

            logger.warning("Could not find target via anchor, falling back to direct selector")
            return None

        except ImportError:
            logger.warning("AnchorLocator not available")
            return None
        except Exception as e:
            logger.warning(f"Anchor-based location failed: {e}")
            return None

    async def find_element_smart(
        self,
        page: Any,
        context: "ExecutionContext",
        selector: str,
        timeout_ms: int = 5000,
        param_name: str = "selector",
    ) -> tuple[Any, str, str]:
        """
        Find element using anchor (if configured) or healing chain.

        This is the preferred method for finding elements as it:
        1. First tries anchor-based location (if anchor_config is set)
        2. Falls back to direct selector
        3. Uses healing chain if direct selector fails

        Args:
            page: Playwright Page instance
            context: Execution context
            selector: Normalized selector string
            timeout_ms: Timeout for selector operations
            param_name: Parameter name to get healing context from

        Returns:
            Tuple of (element, final_selector, method_used)
            - element: Found ElementHandle
            - final_selector: Selector that worked
            - method_used: "anchor", "original", or healing tier name
        """
        # Try anchor-based location first
        anchor_config = self.get_anchor_config()
        if anchor_config and anchor_config.is_valid:
            element = await self.find_element_with_anchor(page, selector, anchor_config, timeout_ms)
            if element:
                return element, selector, "anchor"

        # Fall through to standard healing-aware finder
        return await self.find_element_with_healing(page, selector, timeout_ms, param_name)

    async def find_element_with_healing(
        self,
        page: Any,
        selector: str,
        timeout_ms: int = 5000,
        param_name: str = "selector",
    ) -> tuple[Any, str, str]:
        """
        Find element with self-healing fallback.

        Attempts to find element using:
        1. Primary selector (fast path)
        2. Healing chain (heuristic → anchor → CV) if primary fails

        Args:
            page: Playwright Page instance
            selector: Normalized selector string
            timeout_ms: Timeout for selector operations
            param_name: Parameter name to get healing context from

        Returns:
            Tuple of (element, final_selector, tier_used)
            - element: Found ElementHandle (may be None for CV results)
            - final_selector: Selector that worked (or original)
            - tier_used: "original", "heuristic", "anchor", or "cv"

        Raises:
            ElementNotFoundError: If element cannot be found by any method
        """
        # Fast path: try primary selector first
        try:
            element = await page.wait_for_selector(
                selector,
                timeout=min(timeout_ms, 2000),
                state="attached",
            )
            if element:
                return element, selector, "original"
        except Exception as e:
            logger.debug(f"Primary selector failed: {selector} - {e}")

        # Get healing context from node config
        healing_context = self.get_healing_context(param_name)
        if not healing_context:
            raise ElementNotFoundError(
                f"Element not found and no healing context available: {selector}",
                selector=selector,
                timeout=timeout_ms,
            )

        logger.info(f"Primary selector failed, attempting healing for: {selector}")

        # Get or create healing chain
        healing_chain = get_healing_chain()
        if not healing_chain:
            raise ElementNotFoundError(
                f"Element not found and healing chain unavailable: {selector}",
                selector=selector,
                timeout=timeout_ms,
            )

        # Load healing context into chain
        await self._load_healing_context(healing_chain, selector, healing_context, page)

        # Attempt healing
        result = await healing_chain.locate_element(
            page=page,
            selector=selector,
            timeout_ms=timeout_ms,
        )

        if result.success:
            tier_name = (
                result.tier_used.value
                if hasattr(result.tier_used, "value")
                else str(result.tier_used)
            )
            logger.info(
                f"Healing succeeded for {selector} using {tier_name} tier "
                f"(confidence: {result.confidence:.1%})"
            )
            return result.element, result.final_selector, tier_name

        raise ElementNotFoundError(
            f"Element not found after healing attempts: {selector}",
            selector=selector,
            timeout=timeout_ms,
        )

    async def navigate_label_to_input(
        self,
        page: Any,
        element: Any,
        timeout_ms: int = 5000,
    ) -> tuple[Any, str]:
        """
        Navigate from a label element to its associated input.

        When a selector matches a <label> element but we need an input
        (for fill/type operations), this method finds the associated input.

        Strategy:
        1. Check if element is a <label>
        2. If label has 'for' attribute → find input with that ID
        3. If no 'for' → look for input/textarea/select inside the label
        4. If no child → look for following sibling input
        5. If no sibling → look for input in same parent

        Args:
            page: Playwright Page instance
            element: Element handle (potentially a label)
            timeout_ms: Timeout for finding associated input

        Returns:
            Tuple of (input_element, navigation_method)
            - input_element: The input element (or original if not a label)
            - navigation_method: How we found it ("for_attr", "child", "sibling", "parent", "original")
        """
        try:
            # Check if element is a label
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            if tag_name != "label":
                return element, "original"

            logger.debug("Element is a <label>, attempting to find associated input")

            # Strategy 1: Check 'for' attribute
            for_attr = await element.evaluate("el => el.getAttribute('for')")
            if for_attr:
                try:
                    input_el = await page.wait_for_selector(
                        f"#{for_attr}",
                        timeout=min(timeout_ms, 2000),
                        state="attached",
                    )
                    if input_el:
                        logger.info(f"Found input via label 'for' attribute: #{for_attr}")
                        return input_el, "for_attr"
                except Exception:
                    logger.debug(f"Could not find input with id='{for_attr}'")

            # Strategy 2: Look for input/textarea/select inside the label
            try:
                child_input = await element.query_selector(
                    "input, textarea, select, [contenteditable='true']"
                )
                if child_input:
                    logger.info("Found input as child of label")
                    return child_input, "child"
            except Exception:
                pass

            # Strategy 3: Look for following sibling input
            try:
                sibling_input = await element.evaluate_handle(
                    """el => {
                        let sibling = el.nextElementSibling;
                        while (sibling) {
                            if (sibling.matches('input, textarea, select, [contenteditable="true"]')) {
                                return sibling;
                            }
                            sibling = sibling.nextElementSibling;
                        }
                        return null;
                    }"""
                )
                if sibling_input and await sibling_input.evaluate("el => el !== null"):
                    as_element = sibling_input.as_element()
                    if as_element:
                        logger.info("Found input as sibling of label")
                        return as_element, "sibling"
            except Exception:
                pass

            # Strategy 4: Look for input in same parent container
            try:
                parent_input = await element.evaluate_handle(
                    """el => {
                        const parent = el.parentElement;
                        if (!parent) return null;
                        const input = parent.querySelector('input, textarea, select, [contenteditable="true"]');
                        return input !== el ? input : null;
                    }"""
                )
                if parent_input and await parent_input.evaluate("el => el !== null"):
                    as_element = parent_input.as_element()
                    if as_element:
                        logger.info("Found input in same parent as label")
                        return as_element, "parent"
            except Exception:
                pass

            # No input found, return original element (will likely fail on fill)
            logger.warning("Could not find associated input for label, using original element")
            return element, "original"

        except Exception as e:
            logger.debug(f"Label-to-input navigation failed: {e}")
            return element, "original"

    async def _load_healing_context(
        self,
        healing_chain: Any,
        selector: str,
        healing_context: dict,
        page: Any,
    ) -> None:
        """
        Load stored healing context into the healing chain.

        Reconstructs fingerprint, spatial context, and CV context from
        the stored healing_context dict.

        Args:
            healing_chain: SelectorHealingChain instance
            selector: Original selector
            healing_context: Stored healing context dict
            page: Playwright Page instance
        """
        try:
            # Load fingerprint for heuristic healing
            if "fingerprint" in healing_context:
                from casare_rpa.utils.selectors.selector_healing import (
                    ElementFingerprint,
                )

                fingerprint_data = healing_context["fingerprint"]
                # Reconstruct fingerprint from dict
                if isinstance(fingerprint_data, dict):
                    fingerprint = ElementFingerprint(**fingerprint_data)
                    healing_chain._fingerprints[selector] = fingerprint
                    healing_chain._heuristic_healer.store_fingerprint(selector, fingerprint)
                    logger.debug(f"Loaded fingerprint for healing: {selector}")

            # Load spatial context for anchor healing
            if "spatial" in healing_context:
                from casare_rpa.infrastructure.browser.healing.models import (
                    SpatialContext,
                )

                spatial_data = healing_context["spatial"]
                if isinstance(spatial_data, dict):
                    spatial = SpatialContext(**spatial_data)
                    healing_chain._spatial_contexts[selector] = spatial
                    healing_chain._anchor_healer.store_context(selector, spatial)
                    logger.debug(f"Loaded spatial context for healing: {selector}")

            # Load CV template for CV fallback
            if "cv_template" in healing_context and healing_chain._cv_healer:
                cv_data = healing_context["cv_template"]
                if isinstance(cv_data, dict) and "image_base64" in cv_data:
                    import base64
                    from casare_rpa.infrastructure.browser.healing.cv_healer import (
                        CVContext,
                    )

                    # Decode base64 image
                    image_bytes = base64.b64decode(cv_data["image_base64"])

                    # Create CV context
                    cv_context = CVContext(
                        template_image=image_bytes,
                        text_content="",  # Not stored in cv_template
                        expected_position=None,
                        expected_size=(
                            cv_data.get("width", 0),
                            cv_data.get("height", 0),
                        ),
                        element_type="unknown",
                    )
                    healing_chain._cv_contexts[selector] = cv_context
                    healing_chain._cv_healer.store_context(selector, cv_context)
                    logger.debug(
                        f"Loaded CV template for healing: {selector} " f"({len(image_bytes)} bytes)"
                    )

        except Exception as e:
            logger.warning(f"Failed to load healing context: {e}")

    async def click_with_healing(
        self,
        page: Any,
        selector: str,
        timeout_ms: int = 5000,
        param_name: str = "selector",
        **click_options: Any,
    ) -> tuple[bool, str]:
        """
        Click element with self-healing fallback.

        If the primary selector fails, attempts healing. For CV-based healing,
        performs coordinate-based click since there's no element handle.

        Args:
            page: Playwright Page instance
            selector: Normalized selector string
            timeout_ms: Timeout for selector operations
            param_name: Parameter name to get healing context from
            **click_options: Additional options for page.click()

        Returns:
            Tuple of (success, tier_used)

        Raises:
            ElementNotFoundError: If element cannot be found
        """
        try:
            element, final_selector, tier = await self.find_element_with_healing(
                page, selector, timeout_ms, param_name
            )

            if tier == "cv" and element is None:
                # CV healing returns coordinates, not element
                healing_chain = get_healing_chain()
                if healing_chain:
                    healing_chain._cv_contexts.get(selector)
                    # For CV, we need to click at coordinates
                    # This is a simplified implementation - full impl would use
                    # result.cv_click_coordinates from HealingChainResult
                    logger.warning("CV coordinate-based click not fully implemented")
                    return False, tier

            # Normal click with element
            await element.click(**click_options)
            return True, tier

        except ElementNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Click with healing failed: {e}")
            raise

    # =========================================================================
    # Retry Logic
    # =========================================================================

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "operation",
        retry_count: Optional[int] = None,
        retry_interval: Optional[int] = None,
    ) -> tuple[T, int]:
        """
        Execute an async operation with retry logic.

        Uses retry_count and retry_interval from node config if not provided.

        Args:
            operation: Async callable to execute
            operation_name: Name for logging
            retry_count: Override retry count (default: from config)
            retry_interval: Override retry interval in ms (default: from config)

        Returns:
            Tuple of (result, attempts) where attempts is 1-based count

        Raises:
            Last exception if all attempts fail
        """
        if retry_count is None:
            retry_count = self.get_parameter("retry_count", 0)
        if retry_interval is None:
            retry_interval = self.get_parameter("retry_interval", 1000)

        last_error: Optional[Exception] = None
        attempts = 0
        max_attempts = retry_count + 1

        while attempts < max_attempts:
            attempts += 1
            try:
                if attempts > 1:
                    logger.info(f"Retry attempt {attempts - 1}/{retry_count} for {operation_name}")

                result = await operation()
                return result, attempts

            except Exception as e:
                last_error = e
                if attempts < max_attempts:
                    logger.warning(f"{operation_name} failed (attempt {attempts}): {e}")
                    await asyncio.sleep(retry_interval / 1000)

        if last_error:
            raise last_error
        raise RuntimeError(f"{operation_name} failed without exception")

    # =========================================================================
    # Screenshot on Failure
    # =========================================================================

    async def screenshot_on_failure(
        self,
        page: Any,
        prefix: str = "failure",
    ) -> Optional[str]:
        """
        Take screenshot if screenshot_on_fail is enabled.

        Uses screenshot_on_fail and screenshot_path from node config.

        Args:
            page: Playwright Page instance
            prefix: Prefix for auto-generated filename

        Returns:
            Screenshot path if taken, None otherwise
        """
        if not self.get_parameter("screenshot_on_fail", False):
            return None

        screenshot_path = self.get_parameter("screenshot_path", "")
        return await take_failure_screenshot(page, screenshot_path, prefix)

    # =========================================================================
    # Element Highlighting
    # =========================================================================

    async def highlight_if_enabled(
        self,
        page: Any,
        selector: str,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Highlight element if highlight_before_action is enabled.

        Uses highlight_before_action from node config.

        Args:
            page: Playwright Page instance
            selector: Normalized selector
            timeout: Override timeout (default: from config)
        """
        highlight_enabled = self.get_parameter("highlight_before_action", False)
        # Also check legacy name
        if not highlight_enabled:
            highlight_enabled = self.get_parameter("highlight_before_click", False)
        if not highlight_enabled:
            highlight_enabled = self.get_parameter("highlight_on_find", False)

        if not highlight_enabled:
            return

        if timeout is None:
            timeout = self.get_parameter("timeout", DEFAULT_NODE_TIMEOUT * 1000)

        await highlight_element(page, selector, timeout)

    # =========================================================================
    # Common Port Patterns
    # =========================================================================

    def add_page_input_port(self, required: bool = False) -> None:
        """Add standard page input port."""
        self.add_input_port("page", DataType.PAGE, required=required)

    def add_page_output_port(self) -> None:
        """Add standard page output port."""
        self.add_output_port("page", DataType.PAGE)

    def add_page_passthrough_ports(self, required: bool = False) -> None:
        """Add page input and output ports for passthrough pattern."""
        self.add_page_input_port(required=required)
        self.add_page_output_port()

    def add_selector_input_port(self) -> None:
        """Add standard selector input port."""
        self.add_input_port("selector", DataType.STRING, required=False)

    # =========================================================================
    # Result Building
    # =========================================================================

    def success_result(
        self,
        data: dict[str, Any],
        next_nodes: Optional[list[str]] = None,
    ) -> ExecutionResult:
        """
        Build standard success result.

        Args:
            data: Result data dictionary
            next_nodes: Execution ports to continue (default: ["exec_out"])

        Returns:
            ExecutionResult dictionary
        """
        self.status = NodeStatus.SUCCESS
        return {
            "success": True,
            "data": data,
            "next_nodes": next_nodes or ["exec_out"],
        }

    def error_result(
        self,
        error: str | Exception,
        data: Optional[dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Build standard error result.

        Args:
            error: Error message or exception
            data: Optional additional data

        Returns:
            ExecutionResult dictionary
        """
        self.status = NodeStatus.ERROR
        error_msg = str(error)
        logger.error(f"{self.__class__.__name__} failed: {error_msg}")

        result: dict[str, Any] = {
            "success": False,
            "error": error_msg,
            "next_nodes": [],
        }
        if data:
            result["data"] = data
        return result

    # =========================================================================
    # Default Implementations
    # =========================================================================

    def _validate_config(self) -> tuple[bool, str]:
        """
        Validate node configuration.

        Override in subclass for custom validation.
        Default: always valid (schema handles validation).
        """
        return True, ""

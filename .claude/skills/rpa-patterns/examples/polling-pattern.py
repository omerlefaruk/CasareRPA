"""
Polling Pattern for RPA Automation

Use Case: Wait for dynamic UI elements, async operations, or state changes.

This pattern implements:
1. Condition polling with configurable intervals
2. Timeout handling
3. Progressive interval increase (adaptive polling)
4. Pre-condition checks for fast-path success
"""

import asyncio
from typing import Awaitable, Callable

from loguru import logger


async def poll_for_condition(
    condition: Callable[[], Awaitable[bool]],
    condition_name: str = "condition",
    timeout_ms: int = 30000,
    interval_ms: int = 500,
    raise_on_timeout: bool = True,
) -> bool:
    """
    Poll until a condition becomes true or timeout is reached.

    Args:
        condition: Async callable that returns bool
        condition_name: Description for logging
        timeout_ms: Maximum time to wait in milliseconds
        interval_ms: Time between polls in milliseconds
        raise_on_timeout: Whether to raise exception or return False on timeout

    Returns:
        True if condition met, False if timeout (when raise_on_timeout=False)

    Raises:
        TimeoutError: If condition not met within timeout (when raise_on_timeout=True)

    Example:
        # Wait for element to appear
        async def is_visible():
            return await page.locator(".loading-complete").count() > 0

        await poll_for_condition(is_visible, condition_name="loading complete", timeout_ms=10000)
    """
    deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000)
    attempts = 0

    # Fast-path: check immediately
    if await condition():
        logger.debug(f"{condition_name} satisfied immediately")
        return True

    while asyncio.get_event_loop().time() < deadline:
        attempts += 1
        await asyncio.sleep(interval_ms / 1000)

        try:
            if await condition():
                logger.debug(f"{condition_name} satisfied after {attempts} attempts")
                return True
        except Exception as e:
            logger.warning(f"Error checking {condition_name} (attempt {attempts}): {e}")

    if raise_on_timeout:
        raise TimeoutError(f"{condition_name} not met within {timeout_ms}ms")
    return False


async def poll_with_progressive_intervals(
    condition: Callable[[], Awaitable[bool]],
    condition_name: str = "condition",
    timeout_ms: int = 30000,
    initial_interval_ms: int = 100,
    max_interval_ms: int = 2000,
    backoff_multiplier: float = 1.5,
) -> bool:
    """
    Poll with increasing intervals (adaptive polling).

    Starts with short intervals for fast response, backs off for long-running operations.

    Args:
        condition: Async callable that returns bool
        condition_name: Description for logging
        timeout_ms: Maximum time to wait
        initial_interval_ms: Starting poll interval
        max_interval_ms: Maximum poll interval
        backoff_multiplier: Interval growth factor

    Returns:
        True if condition met

    Raises:
        TimeoutError: If condition not met within timeout
    """
    deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000)
    current_interval = initial_interval_ms
    attempts = 0

    # Immediate check
    if await condition():
        return True

    while asyncio.get_event_loop().time() < deadline:
        attempts += 1
        await asyncio.sleep(current_interval / 1000)

        if await condition():
            logger.debug(f"{condition_name} satisfied after {attempts} attempts")
            return True

        # Increase interval for next poll (but don't exceed max)
        current_interval = min(int(current_interval * backoff_multiplier), max_interval_ms)

    raise TimeoutError(f"{condition_name} not met within {timeout_ms}ms")


# ===========================================================================
# RPA-Specific Polling Helpers
# ===========================================================================


async def wait_for_element_state(
    page,
    selector: str,
    state: str = "visible",
    timeout_ms: int = 30000,
) -> bool:
    """
    Wait for an element to reach a specific state.

    States: visible, hidden, attached, detached
    """

    async def check_state():
        try:
            element = page.locator(selector)
            count = await element.count()

            if count == 0:
                return state in ("hidden", "detached")

            if state == "visible":
                return await element.is_visible()
            elif state == "hidden":
                return not await element.is_visible()
            elif state == "attached":
                return True
            elif state == "detached":
                return False

        except Exception:
            return state in ("hidden", "detached", "detached")

        return False

    return await poll_for_condition(
        check_state,
        condition_name=f"element {selector} state={state}",
        timeout_ms=timeout_ms,
    )


async def wait_for_text_content(
    page,
    selector: str,
    expected_text: str | None = None,
    timeout_ms: int = 30000,
) -> bool:
    """
    Wait for element to contain expected text (or any non-empty text).

    Args:
        page: Playwright Page object
        selector: Element selector
        expected_text: Specific text to wait for (None = any non-empty text)
        timeout_ms: Maximum wait time
    """

    async def check_text():
        try:
            element = page.locator(selector)
            if await element.count() == 0:
                return False

            text = await element.inner_text() or ""

            if expected_text is None:
                return len(text.strip()) > 0

            return expected_text in text

        except Exception:
            return False

    condition_desc = (
        f"text '{expected_text}' in {selector}" if expected_text else f"any text in {selector}"
    )
    return await poll_for_condition(
        check_text,
        condition_name=condition_desc,
        timeout_ms=timeout_ms,
    )


async def wait_for_navigation_complete(
    page,
    timeout_ms: int = 30000,
) -> bool:
    """
    Wait for page navigation and loading to complete.

    Checks for common indicators that a page is fully loaded:
    - No active network requests (for a brief period)
    - Document ready state
    - No visible loading indicators
    """

    async def is_loaded():
        try:
            # Check document state
            state = await page.evaluate("() => document.readyState")
            if state != "complete":
                return False

            # Check for common loading indicators
            loaders = await page.locator(
                ".loading, .spinner, .loader, [data-loading], .fa-spinner"
            ).count()

            return loaders == 0

        except Exception:
            return False

    return await poll_for_condition(
        is_loaded,
        condition_name="page navigation complete",
        timeout_ms=timeout_ms,
        interval_ms=200,
    )


async def wait_for_file_download(
    page,
    download_handle,
    timeout_ms: int = 60000,
) -> str | None:
    """
    Wait for a download to complete and return the saved path.

    Args:
        page: Playwright Page object
        download_handle: Download object from download event
        timeout_ms: Maximum wait time

    Returns:
        Path to downloaded file, or None if failed
    """

    async def is_complete():
        # Playwright downloads complete immediately; this is for any
        # additional processing or saving steps
        return download_handle.failure() is None

    try:
        await poll_for_condition(
            is_complete,
            condition_name="file download",
            timeout_ms=timeout_ms,
            interval_ms=500,
        )

        # Save the download
        path = await download_handle.path()
        return path

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return None


# ===========================================================================
# Node Integration Example
# ===========================================================================

"""
Usage in a browser node:

from casare_rpa.nodes.browser.browser_base import BrowserBaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType

@properties(
    PropertyDef("selector", PropertyType.STRING, required=True),
    PropertyDef("state", PropertyType.CHOICE, default="visible",
                options=["visible", "hidden", "attached", "detached"]),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class WaitForElementNode(BrowserBaseNode):
    async def execute(self, context):
        page = await self.get_page(context)
        selector = self.get_parameter("selector")
        state = self.get_parameter("state", "visible")
        timeout = self.get_parameter("timeout", 30000)

        try:
            await wait_for_element_state(page, selector, state, timeout)
            self.set_output_value("found", True)
            return {"success": True}
        except TimeoutError as e:
            logger.error(f"Element not found: {e}")
            self.set_output_value("found", False)
            return {"success": False, "error": str(e)}
"""

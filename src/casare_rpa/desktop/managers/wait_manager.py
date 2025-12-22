"""
Wait Manager - Wait operations for desktop automation

Handles waiting for elements, windows, and conditions.
All operations are async-first with proper error handling.
"""

import asyncio
import re
import time
from typing import Any, Dict, Optional

import uiautomation as auto
from loguru import logger

from casare_rpa.desktop.element import DesktopElement
from casare_rpa.desktop.selector import find_element as selector_find_element


class WaitManager:
    """
    Handles wait operations for desktop automation.

    Provides async methods for waiting on elements and windows
    to reach specific states.
    Uses asyncio.to_thread() for blocking UIAutomation calls.
    """

    def __init__(self) -> None:
        """Initialize wait manager."""
        logger.debug("Initializing WaitManager")

    async def wait_for_element(
        self,
        selector: Dict[str, Any],
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
        parent: auto.Control = None,
    ) -> Optional[DesktopElement]:
        """
        Wait for an element to reach a specific state.

        Args:
            selector: Element selector dictionary
            timeout: Maximum wait time in seconds
            state: State to wait for - "visible", "hidden", "enabled", "disabled"
            poll_interval: Time between checks in seconds
            parent: Parent control to search within (uses root if None)

        Returns:
            DesktopElement if found (for visible/enabled), None if hidden/disabled

        Raises:
            TimeoutError: If element doesn't reach state within timeout
        """
        valid_states = ["visible", "hidden", "enabled", "disabled"]
        if state.lower() not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Must be one of: {valid_states}")

        state = state.lower()
        logger.debug(f"Waiting for element to be '{state}' (timeout={timeout}s)")

        start_time = time.time()

        def _find_and_check() -> tuple:
            """Find element and check state - runs in thread."""
            try:
                search_parent = parent if parent else auto.GetRootControl()
                element = selector_find_element(search_parent, selector, timeout=0.1)

                if state == "visible":
                    if element and element.exists():
                        return ("found", element)
                elif state == "hidden":
                    if not element or not element.exists():
                        return ("hidden", None)
                elif state == "enabled":
                    if element and element._control.IsEnabled:
                        return ("enabled", element)
                elif state == "disabled":
                    if element and not element._control.IsEnabled:
                        return ("disabled", element)

                return ("not_ready", element)
            except Exception:
                if state == "hidden":
                    return ("hidden", None)
                return ("error", None)

        while time.time() - start_time < timeout:
            result_type, element = await asyncio.to_thread(_find_and_check)

            if result_type in ("found", "enabled", "disabled"):
                logger.info(f"Element is {state}")
                return element
            elif result_type == "hidden":
                logger.info("Element is hidden/not found")
                return None

            await asyncio.sleep(poll_interval)

        elapsed = time.time() - start_time
        raise TimeoutError(
            f"Element did not become '{state}' within {timeout} seconds "
            f"(elapsed: {elapsed:.1f}s)"
        )

    async def wait_for_window(
        self,
        title: str = None,
        title_regex: str = None,
        class_name: str = None,
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
    ) -> Optional[auto.Control]:
        """
        Wait for a window to reach a specific state.

        Args:
            title: Window title (partial match)
            title_regex: Window title regex pattern
            class_name: Window class name
            timeout: Maximum wait time in seconds
            state: State to wait for - "visible", "hidden"
            poll_interval: Time between checks in seconds

        Returns:
            Window control if found (for visible), None if hidden

        Raises:
            TimeoutError: If window doesn't reach state within timeout
            ValueError: If no search criteria provided
        """
        if not title and not title_regex and not class_name:
            raise ValueError("Must provide at least one of: title, title_regex, class_name")

        valid_states = ["visible", "hidden"]
        if state.lower() not in valid_states:
            raise ValueError(f"Invalid state '{state}'. Must be one of: {valid_states}")

        state = state.lower()
        logger.debug(f"Waiting for window to be '{state}' (timeout={timeout}s)")

        start_time = time.time()

        def _search_windows() -> Optional[auto.Control]:
            """Search for window - runs in thread."""
            windows = auto.GetRootControl().GetChildren()

            for win in windows:
                try:
                    win_title = win.Name or ""

                    if title and title.lower() in win_title.lower():
                        return win
                    elif title_regex and re.search(title_regex, win_title):
                        return win
                    elif class_name and win.ClassName == class_name:
                        return win
                except Exception:
                    continue
            return None

        while time.time() - start_time < timeout:
            window_found = await asyncio.to_thread(_search_windows)

            if state == "visible":
                if window_found:
                    logger.info(f"Window found: '{window_found.Name}'")
                    return window_found
            elif state == "hidden":
                if not window_found:
                    logger.info("Window is hidden/closed")
                    return None

            await asyncio.sleep(poll_interval)

        time.time() - start_time
        search_desc = title or title_regex or class_name
        raise TimeoutError(
            f"Window '{search_desc}' did not become '{state}' within {timeout} seconds"
        )

    async def element_exists(
        self,
        selector: Dict[str, Any],
        timeout: float = 0.0,
        parent: auto.Control = None,
    ) -> bool:
        """
        Check if an element exists.

        Args:
            selector: Element selector dictionary
            timeout: Maximum time to search (0 for immediate check)
            parent: Parent control to search within

        Returns:
            True if element exists, False otherwise
        """
        logger.debug(f"Checking if element exists: {selector}")

        def _check_exists() -> bool:
            try:
                search_parent = parent if parent else auto.GetRootControl()
                element = selector_find_element(search_parent, selector, timeout=max(0.1, timeout))
                exists = element is not None and element.exists()
                logger.debug(f"Element exists: {exists}")
                return exists
            except Exception:
                logger.debug("Element does not exist")
                return False

        return await asyncio.to_thread(_check_exists)

    async def verify_element_property(
        self,
        element: DesktopElement,
        property_name: str,
        expected_value: Any,
        comparison: str = "equals",
    ) -> bool:
        """
        Verify an element property has an expected value.

        Args:
            element: DesktopElement to check
            property_name: Name of property to check (Name, ClassName, IsEnabled, etc.)
            expected_value: Expected value of the property
            comparison: Comparison type - "equals", "contains", "startswith", "endswith",
                       "regex", "greater", "less", "not_equals"

        Returns:
            True if verification passes, False otherwise
        """
        valid_comparisons = [
            "equals",
            "contains",
            "startswith",
            "endswith",
            "regex",
            "greater",
            "less",
            "not_equals",
        ]
        if comparison.lower() not in valid_comparisons:
            raise ValueError(
                f"Invalid comparison '{comparison}'. Must be one of: {valid_comparisons}"
            )

        comparison = comparison.lower()
        logger.debug(
            f"Verifying element property '{property_name}' {comparison} '{expected_value}'"
        )

        def _verify() -> bool:
            try:
                control = element._control

                actual_value = getattr(control, property_name, None)

                if actual_value is None:
                    property_map = {
                        "text": control.Name,
                        "name": control.Name,
                        "class": control.ClassName,
                        "classname": control.ClassName,
                        "enabled": control.IsEnabled,
                        "isenabled": control.IsEnabled,
                        "automation_id": control.AutomationId,
                        "automationid": control.AutomationId,
                    }
                    actual_value = property_map.get(property_name.lower())

                if actual_value is None:
                    logger.warning(f"Property '{property_name}' not found on element")
                    return False

                result = False
                actual_str = str(actual_value)
                expected_str = str(expected_value)

                if comparison == "equals":
                    result = actual_value == expected_value or actual_str == expected_str
                elif comparison == "not_equals":
                    result = actual_value != expected_value and actual_str != expected_str
                elif comparison == "contains":
                    result = expected_str.lower() in actual_str.lower()
                elif comparison == "startswith":
                    result = actual_str.lower().startswith(expected_str.lower())
                elif comparison == "endswith":
                    result = actual_str.lower().endswith(expected_str.lower())
                elif comparison == "regex":
                    result = bool(re.search(expected_str, actual_str))
                elif comparison == "greater":
                    try:
                        result = float(actual_value) > float(expected_value)
                    except (ValueError, TypeError):
                        result = actual_str > expected_str
                elif comparison == "less":
                    try:
                        result = float(actual_value) < float(expected_value)
                    except (ValueError, TypeError):
                        result = actual_str < expected_str

                logger.info(
                    f"Property verification: '{property_name}' {comparison} "
                    f"'{expected_value}' -> actual='{actual_value}', result={result}"
                )
                return result

            except Exception as e:
                logger.error(f"Property verification failed: {e}")
                return False

        return await asyncio.to_thread(_verify)

    async def wait_for_condition(
        self,
        condition_fn,
        timeout: float = 10.0,
        poll_interval: float = 0.5,
        error_message: str = "Condition not met",
    ) -> bool:
        """
        Wait for a custom condition to become true.

        Args:
            condition_fn: Callable that returns True when condition is met
            timeout: Maximum wait time in seconds
            poll_interval: Time between checks in seconds
            error_message: Error message for timeout

        Returns:
            True if condition was met

        Raises:
            TimeoutError: If condition is not met within timeout
        """
        logger.debug(f"Waiting for condition (timeout={timeout}s)")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                result = await asyncio.to_thread(condition_fn)
                if result:
                    logger.info("Condition met")
                    return True
            except Exception as e:
                logger.debug(f"Condition check failed: {e}")

            await asyncio.sleep(poll_interval)

        elapsed = time.time() - start_time
        raise TimeoutError(f"{error_message} within {timeout} seconds (elapsed: {elapsed:.1f}s)")

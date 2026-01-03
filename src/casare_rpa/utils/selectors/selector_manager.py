"""
Playwright Integration for Element Selector
Manages injector lifecycle and bidirectional communication
"""

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.utils.selectors.selector_cache import SelectorCache, get_selector_cache
from casare_rpa.utils.selectors.selector_generator import (
    ElementFingerprint,
    SmartSelectorGenerator,
)

# Global callback registry - maps page id to callbacks
# This is needed because Playwright's expose_function persists across SelectorManager instances
_page_callbacks: dict[int, dict[str, Callable]] = {}


def parse_xml_selector(xml_selector: str) -> tuple[str, str]:
    """
    Parse UiPath-style XML selector and convert to XPath. (Backward Compatibility)
    """
    from casare_rpa.application.services.selector_service import SelectorService

    return SelectorService.parse_xml_selector(xml_selector)


def _get_page_callbacks(page) -> dict[str, Callable]:
    """Get callback registry for a page."""
    page_id = id(page)
    if page_id not in _page_callbacks:
        _page_callbacks[page_id] = {}
    return _page_callbacks[page_id]


class SelectorManager:
    """
    Manages the element selector injector lifecycle
    Integrates with Playwright for seamless element picking
    """

    def __init__(self, cache: SelectorCache | None = None):
        self._injector_script: str | None = None
        self._active_page = None
        self._callback_element_selected: Callable | None = None
        self._callback_recording_complete: Callable | None = None
        self._is_active = False
        self._is_recording = False
        self._cache = cache or get_selector_cache()

    def _load_injector_script(self) -> str:
        """Load the JavaScript injector from file"""
        if self._injector_script:
            return self._injector_script

        script_path = Path(__file__).parent / "selector_injector.js"
        with open(script_path, encoding="utf-8") as f:
            self._injector_script = f.read()

        return self._injector_script

    async def inject_into_page(self, page):
        """
        Inject the selector script into a Playwright page
        Sets up bidirectional communication
        """
        self._active_page = page

        # Load script
        script = self._load_injector_script()

        # Add init script for future navigations
        await page.add_init_script(script)

        # Also inject into current page immediately (if already loaded)
        try:
            await page.evaluate(script)
        except Exception as e:
            logger.debug(f"Script already injected or page not ready: {e}")

        # Expose Python functions to JavaScript (only if not already registered)
        try:
            await page.expose_function(
                "__casareRPA_onElementSelected", self._handle_element_selected
            )
            logger.info("Exposed __casareRPA_onElementSelected function to browser")
        except Exception as e:
            if "already registered" not in str(e).lower():
                raise
            logger.debug("__casareRPA_onElementSelected already registered")

        try:
            await page.expose_function(
                "__casareRPA_onRecordingComplete", self._handle_recording_complete
            )
        except Exception as e:
            if "already registered" not in str(e).lower():
                raise

        try:
            await page.expose_function("__casareRPA_onActionRecorded", self._handle_action_recorded)
        except Exception as e:
            if "already registered" not in str(e).lower():
                raise

        logger.info("Selector injector loaded into page")

    async def activate_selector_mode(
        self,
        recording: bool = False,
        on_element_selected: Callable | None = None,
        on_recording_complete: Callable | None = None,
    ):
        """
        Activate selector mode on the current page

        Args:
            recording: If True, enables recording mode for workflow capture
            on_element_selected: Callback when element is selected
            on_recording_complete: Callback when recording is complete
        """
        if not self._active_page:
            raise RuntimeError("No active page. Call inject_into_page first.")

        # Store callbacks both locally and in global registry
        # Global registry is needed because expose_function persists across SelectorManager instances
        self._callback_element_selected = on_element_selected
        self._callback_recording_complete = on_recording_complete

        # Update global registry so any SelectorManager instance can find the current callback
        callbacks = _get_page_callbacks(self._active_page)
        callbacks["on_element_selected"] = on_element_selected
        callbacks["on_recording_complete"] = on_recording_complete
        logger.debug(f"Registered callbacks in global registry for page {id(self._active_page)}")

        self._is_active = True
        self._is_recording = recording

        # Check if injector is loaded, if not re-inject
        is_injected = await self._active_page.evaluate(
            "typeof window.__casareRPA !== 'undefined' && typeof window.__casareRPA.selector !== 'undefined'"
        )

        if not is_injected:
            logger.warning("Injector not found in page, re-injecting...")
            script = self._load_injector_script()
            await self._active_page.evaluate(script)

        # Verify callback is exposed
        callback_exists = await self._active_page.evaluate(
            "typeof window.__casareRPA_onElementSelected === 'function'"
        )
        logger.info(f"Callback __casareRPA_onElementSelected exists in browser: {callback_exists}")

        if not callback_exists:
            logger.warning("Callback not found - attempting to re-expose")
            try:
                await self._active_page.expose_function(
                    "__casareRPA_onElementSelected", self._handle_element_selected
                )
                logger.info("Re-exposed callback successfully")
            except Exception as e:
                logger.debug(f"Could not re-expose (may already exist): {e}")

        # Activate selector mode in browser - use parameterized call
        await self._active_page.evaluate(
            "recording => window.__casareRPA.selector.activate(recording)", recording
        )

        logger.info(f"Selector mode activated (recording={recording})")

    async def deactivate_selector_mode(self):
        """Deactivate selector mode"""
        if not self._active_page or not self._is_active:
            return

        try:
            await self._active_page.evaluate("window.__casareRPA.selector.deactivate()")
        except Exception as e:
            logger.warning(f"Failed to deactivate selector mode: {e}")

        self._is_active = False
        self._is_recording = False
        logger.info("Selector mode deactivated")

    async def _handle_element_selected(self, element_data: dict[str, Any]):
        """
        Handle element selection from browser
        Generates smart selectors and invokes callback
        """
        # ALWAYS check global registry first - it has the most recently activated callback
        # This is needed because expose_function binds to one instance, but multiple
        # dialogs (ElementSelectorDialog, UIExplorer) may share the same page
        callback = None
        if self._active_page:
            callbacks = _get_page_callbacks(self._active_page)
            callback = callbacks.get("on_element_selected")
            logger.debug(f"Retrieved callback from global registry: {callback is not None}")
        # Fall back to instance callback if global not available
        if callback is None:
            callback = self._callback_element_selected

        logger.info(
            f"Element selected from browser: {element_data.get('tagName')} (callback: {callback is not None})"
        )

        # Generate multiple selector strategies
        try:
            fingerprint = SmartSelectorGenerator.generate_selectors(element_data)
            logger.info(
                f"Generated {len(fingerprint.selectors)} selectors for {fingerprint.tag_name}"
            )
        except Exception as e:
            logger.error(f"Failed to generate selectors: {e}")
            return

        # Validate selectors against page
        try:
            await self._validate_selectors(fingerprint)
            logger.info("Selectors validated")
        except Exception as e:
            logger.warning(f"Selector validation failed (non-critical): {e}")

        # Invoke callback
        if callback:
            try:
                logger.info("Invoking element selected callback...")
                if asyncio.iscoroutinefunction(callback):
                    await callback(fingerprint)
                else:
                    callback(fingerprint)
                logger.info("Callback completed successfully")
            except Exception as e:
                logger.error(f"Error in element selected callback: {e}", exc_info=True)
        else:
            logger.warning("No callback registered for element selection")

    async def _handle_action_recorded(self, action: dict[str, Any]):
        """
        Handle individual action being recorded (real-time feedback).

        Args:
            action: Single action data from browser
        """
        logger.debug(f"Action recorded: {action.get('action')} at {action.get('timestamp')}")
        # Could emit events here for real-time UI updates if needed

    async def _handle_recording_complete(self, actions: list[dict[str, Any]]):
        """
        Handle recording completion from browser
        Processes recorded actions and invokes callback
        """
        logger.info(f"Recording complete: {len(actions)} actions captured")

        # Look up callback from global registry first
        callback = self._callback_recording_complete
        if callback is None and self._active_page:
            callbacks = _get_page_callbacks(self._active_page)
            callback = callbacks.get("on_recording_complete")

        # Process each action and generate selectors
        processed_actions = []
        for action_data in actions:
            element_data = action_data.get("element", {})
            fingerprint = SmartSelectorGenerator.generate_selectors(element_data)

            processed_actions.append(
                {
                    "action": action_data.get("action"),
                    "timestamp": action_data.get("timestamp"),
                    "value": action_data.get("value"),
                    "element": fingerprint,
                }
            )

        # Invoke callback
        if callback:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(processed_actions)
                else:
                    callback(processed_actions)
            except Exception as e:
                logger.error(f"Error in recording complete callback: {e}")

    async def _validate_selectors(self, fingerprint: ElementFingerprint):
        """
        Validate selectors against the current page.
        Uses caching to avoid repeated DOM queries for the same selectors.
        """
        if not self._active_page:
            return

        # Get current page URL for cache key
        try:
            page_url = self._active_page.url
        except Exception:
            page_url = "unknown"

        for selector_strategy in fingerprint.selectors:
            try:
                selector_value = selector_strategy.value
                selector_type = selector_strategy.selector_type.value

                # Check cache first
                cached = self._cache.get(selector_value, selector_type, page_url)
                if cached:
                    # Use cached result
                    selector_strategy.is_unique = cached.is_unique
                    selector_strategy.execution_time_ms = cached.execution_time_ms

                    if selector_strategy.is_unique:
                        selector_strategy.score = min(100, selector_strategy.score + 5)
                    else:
                        selector_strategy.score = max(0, selector_strategy.score - 10)

                    logger.debug(
                        f"Validated {selector_type} (cached): unique={selector_strategy.is_unique}"
                    )
                    continue

                # Not in cache - validate against page
                if selector_type in ["xpath", "aria", "data_attr", "text"]:
                    result = await self._active_page.evaluate(
                        """
                        (selector) => {
                            const start = performance.now();
                            const nodes = document.evaluate(
                                selector,
                                document,
                                null,
                                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                                null
                            );
                            const time = performance.now() - start;
                            return { count: nodes.snapshotLength, time };
                        }
                    """,
                        selector_value,
                    )
                else:
                    result = await self._active_page.evaluate(
                        """
                        (selector) => {
                            const start = performance.now();
                            const elements = document.querySelectorAll(selector);
                            const time = performance.now() - start;
                            return { count: elements.length, time };
                        }
                    """,
                        selector_value,
                    )

                # Cache the result
                self._cache.put(
                    selector_value,
                    selector_type,
                    page_url,
                    result["count"],
                    result["time"],
                )

                # Update selector metadata
                selector_strategy.is_unique = result["count"] == 1
                selector_strategy.execution_time_ms = result["time"]

                if selector_strategy.is_unique:
                    selector_strategy.score = min(100, selector_strategy.score + 5)
                else:
                    selector_strategy.score = max(0, selector_strategy.score - 10)

                logger.debug(
                    f"Validated {selector_type}: "
                    f"unique={selector_strategy.is_unique}, "
                    f"time={selector_strategy.execution_time_ms:.2f}ms"
                )

            except Exception as e:
                logger.warning(f"Failed to validate selector: {e}")
                selector_strategy.failure_count += 1
                selector_strategy.score = max(0, selector_strategy.score - 15)

    async def test_selector(
        self, selector_value: str, selector_type: str = "xpath", use_cache: bool = True
    ) -> dict[str, Any]:
        """
        Test a selector against the current page.
        Returns match count and execution time.

        Args:
            selector_value: The selector string
            selector_type: Type of selector (xpath, css, etc.)
            use_cache: Whether to use cached results if available
        """
        if not self._active_page:
            raise RuntimeError("No active page")

        try:
            page_url = self._active_page.url
        except Exception:
            page_url = "unknown"

        # Check cache first if enabled
        if use_cache:
            cached = self._cache.get(selector_value, selector_type, page_url)
            if cached:
                return cached.to_dict()

        try:
            if selector_type in ["xpath", "aria", "data_attr", "text"]:
                result = await self._active_page.evaluate(
                    """
                    (selector) => {
                        const start = performance.now();
                        const nodes = document.evaluate(
                            selector,
                            document,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );
                        const time = performance.now() - start;
                        return {
                            count: nodes.snapshotLength,
                            time,
                            success: true
                        };
                    }
                """,
                    selector_value,
                )
            else:
                result = await self._active_page.evaluate(
                    """
                    (selector) => {
                        const start = performance.now();
                        const elements = document.querySelectorAll(selector);
                        const time = performance.now() - start;
                        return {
                            count: elements.length,
                            time,
                            success: true
                        };
                    }
                """,
                    selector_value,
                )

            # Cache the result
            self._cache.put(
                selector_value, selector_type, page_url, result["count"], result["time"]
            )

            return result
        except Exception as e:
            logger.error(f"Selector test failed: {e}")
            return {"success": False, "error": str(e), "count": 0, "time": 0}

    async def highlight_elements(self, selector_value: str, selector_type: str = "xpath"):
        """
        Highlight all elements matching a selector (for visual validation)
        """
        if not self._active_page:
            return

        try:
            if selector_type in ["xpath", "aria", "data_attr", "text"]:
                # XPath-based selectors - pass selector as parameter to prevent injection
                await self._active_page.evaluate(
                    """
                    (selector) => {
                        // Remove previous highlights
                        document.querySelectorAll('.casare-test-highlight').forEach(el => el.remove());

                        const nodes = document.evaluate(
                            selector,
                            document,
                            null,
                            XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                            null
                        );

                        for (let i = 0; i < nodes.snapshotLength; i++) {
                            const element = nodes.snapshotItem(i);
                            const rect = element.getBoundingClientRect();
                            const highlight = document.createElement('div');
                            highlight.className = 'casare-test-highlight';
                            highlight.style.cssText = `
                                position: absolute;
                                left: ${rect.left + window.pageXOffset}px;
                                top: ${rect.top + window.pageYOffset}px;
                                width: ${rect.width}px;
                                height: ${rect.height}px;
                                border: 3px solid #2196f3;
                                background: rgba(33, 150, 243, 0.2);
                                pointer-events: none;
                                z-index: 2147483647;
                                box-sizing: border-box;
                            `;
                            document.body.appendChild(highlight);
                        }

                        // Auto-remove after 3 seconds
                        setTimeout(() => {
                            document.querySelectorAll('.casare-test-highlight').forEach(el => el.remove());
                        }, 3000);
                    }
                """,
                    selector_value,
                )
            else:
                # CSS selectors - pass selector as parameter to prevent injection
                await self._active_page.evaluate(
                    """
                    (selector) => {
                        // Remove previous highlights
                        document.querySelectorAll('.casare-test-highlight').forEach(el => el.remove());

                        const elements = document.querySelectorAll(selector);

                        elements.forEach(element => {
                            const rect = element.getBoundingClientRect();
                            const highlight = document.createElement('div');
                            highlight.className = 'casare-test-highlight';
                            highlight.style.cssText = `
                                position: absolute;
                                left: ${rect.left + window.pageXOffset}px;
                                top: ${rect.top + window.pageYOffset}px;
                                width: ${rect.width}px;
                                height: ${rect.height}px;
                                border: 3px solid #2196f3;
                                background: rgba(33, 150, 243, 0.2);
                                pointer-events: none;
                                z-index: 2147483647;
                                box-sizing: border-box;
                            `;
                            document.body.appendChild(highlight);
                        });

                        // Auto-remove after 3 seconds
                        setTimeout(() => {
                            document.querySelectorAll('.casare-test-highlight').forEach(el => el.remove());
                        }, 3000);
                    }
                """,
                    selector_value,
                )
        except Exception as e:
            logger.error(f"Failed to highlight elements: {e}")

    @property
    def is_active(self) -> bool:
        """Check if selector mode is active"""
        return self._is_active

    @property
    def is_recording(self) -> bool:
        """Check if recording mode is active"""
        return self._is_recording

    # Cache management methods
    def get_cache_stats(self) -> dict[str, Any]:
        """Get selector cache statistics."""
        return self._cache.get_stats()

    def clear_cache(self, page_url: str | None = None) -> int:
        """
        Clear selector cache.

        Args:
            page_url: If provided, only clear entries for this URL

        Returns:
            Number of entries cleared
        """
        return self._cache.invalidate(page_url)

    def enable_cache(self) -> None:
        """Enable selector caching."""
        self._cache.enable()

    def disable_cache(self) -> None:
        """Disable selector caching."""
        self._cache.disable()

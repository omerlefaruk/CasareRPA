"""
Playwright Integration for Element Selector
Manages injector lifecycle and bidirectional communication
"""

import asyncio
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from loguru import logger

from .selector_generator import SmartSelectorGenerator, ElementFingerprint
from .selector_normalizer import normalize_selector, detect_selector_type


class SelectorManager:
    """
    Manages the element selector injector lifecycle
    Integrates with Playwright for seamless element picking
    """

    def __init__(self):
        self._injector_script: Optional[str] = None
        self._active_page = None
        self._callback_element_selected: Optional[Callable] = None
        self._callback_recording_complete: Optional[Callable] = None
        self._is_active = False
        self._is_recording = False

    def _load_injector_script(self) -> str:
        """Load the JavaScript injector from file"""
        if self._injector_script:
            return self._injector_script

        script_path = Path(__file__).parent / "selector_injector.js"
        with open(script_path, 'r', encoding='utf-8') as f:
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

        # Expose Python functions to JavaScript
        await page.expose_function(
            '__casareRPA_onElementSelected',
            self._handle_element_selected
        )

        await page.expose_function(
            '__casareRPA_onRecordingComplete',
            self._handle_recording_complete
        )

        await page.expose_function(
            '__casareRPA_onActionRecorded',
            self._handle_action_recorded
        )

        logger.info("Selector injector loaded into page")

    async def activate_selector_mode(self, recording: bool = False,
                                    on_element_selected: Optional[Callable] = None,
                                    on_recording_complete: Optional[Callable] = None):
        """
        Activate selector mode on the current page

        Args:
            recording: If True, enables recording mode for workflow capture
            on_element_selected: Callback when element is selected
            on_recording_complete: Callback when recording is complete
        """
        if not self._active_page:
            raise RuntimeError("No active page. Call inject_into_page first.")

        self._callback_element_selected = on_element_selected
        self._callback_recording_complete = on_recording_complete
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

        # Activate selector mode in browser - use parameterized call
        await self._active_page.evaluate(
            "recording => window.__casareRPA.selector.activate(recording)",
            recording
        )

        logger.info(f"Selector mode activated (recording={recording})")

    async def deactivate_selector_mode(self):
        """Deactivate selector mode"""
        if not self._active_page or not self._is_active:
            return

        try:
            await self._active_page.evaluate(
                "window.__casareRPA.selector.deactivate()"
            )
        except Exception as e:
            logger.warning(f"Failed to deactivate selector mode: {e}")

        self._is_active = False
        self._is_recording = False
        logger.info("Selector mode deactivated")

    async def _handle_element_selected(self, element_data: Dict[str, Any]):
        """
        Handle element selection from browser
        Generates smart selectors and invokes callback
        """
        logger.debug(f"Element selected: {element_data.get('tagName')}")

        # Generate multiple selector strategies
        fingerprint = SmartSelectorGenerator.generate_selectors(element_data)

        # Validate selectors against page
        await self._validate_selectors(fingerprint)

        # Invoke callback
        if self._callback_element_selected:
            try:
                if asyncio.iscoroutinefunction(self._callback_element_selected):
                    await self._callback_element_selected(fingerprint)
                else:
                    self._callback_element_selected(fingerprint)
            except Exception as e:
                logger.error(f"Error in element selected callback: {e}")

    async def _handle_action_recorded(self, action: Dict[str, Any]):
        """
        Handle individual action being recorded (real-time feedback).

        Args:
            action: Single action data from browser
        """
        logger.debug(f"Action recorded: {action.get('action')} at {action.get('timestamp')}")
        # Could emit events here for real-time UI updates if needed

    async def _handle_recording_complete(self, actions: List[Dict[str, Any]]):
        """
        Handle recording completion from browser
        Processes recorded actions and invokes callback
        """
        logger.info(f"Recording complete: {len(actions)} actions captured")

        # Process each action and generate selectors
        processed_actions = []
        for action_data in actions:
            element_data = action_data.get('element', {})
            fingerprint = SmartSelectorGenerator.generate_selectors(element_data)

            processed_actions.append({
                'action': action_data.get('action'),
                'timestamp': action_data.get('timestamp'),
                'value': action_data.get('value'),
                'element': fingerprint
            })

        # Invoke callback
        if self._callback_recording_complete:
            try:
                if asyncio.iscoroutinefunction(self._callback_recording_complete):
                    await self._callback_recording_complete(processed_actions)
                else:
                    self._callback_recording_complete(processed_actions)
            except Exception as e:
                logger.error(f"Error in recording complete callback: {e}")

    async def _validate_selectors(self, fingerprint: ElementFingerprint):
        """
        Validate selectors against the current page
        Tests uniqueness and updates scores
        """
        if not self._active_page:
            return

        for selector_strategy in fingerprint.selectors:
            try:
                # Test selector using parameterized evaluate to prevent injection
                selector_value = selector_strategy.value
                selector_type = selector_strategy.selector_type.value

                if selector_type in ['xpath', 'aria', 'data_attr', 'text']:
                    # XPath-based selectors - pass selector as parameter
                    result = await self._active_page.evaluate("""
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
                    """, selector_value)
                else:
                    # CSS selectors - pass selector as parameter
                    result = await self._active_page.evaluate("""
                        (selector) => {
                            const start = performance.now();
                            const elements = document.querySelectorAll(selector);
                            const time = performance.now() - start;
                            return { count: elements.length, time };
                        }
                    """, selector_value)

                # Update selector metadata
                selector_strategy.is_unique = (result['count'] == 1)
                selector_strategy.execution_time_ms = result['time']

                # Boost score for unique selectors
                if selector_strategy.is_unique:
                    selector_strategy.score = min(100, selector_strategy.score + 5)
                else:
                    # Penalty for non-unique selectors
                    selector_strategy.score = max(0, selector_strategy.score - 10)

                logger.debug(
                    f"Validated {selector_strategy.selector_type.value}: "
                    f"unique={selector_strategy.is_unique}, "
                    f"time={selector_strategy.execution_time_ms:.2f}ms"
                )

            except Exception as e:
                logger.warning(f"Failed to validate selector: {e}")
                selector_strategy.failure_count += 1
                selector_strategy.score = max(0, selector_strategy.score - 15)

    async def test_selector(self, selector_value: str,
                           selector_type: str = 'xpath') -> Dict[str, Any]:
        """
        Test a selector against the current page
        Returns match count and execution time
        """
        if not self._active_page:
            raise RuntimeError("No active page")

        try:
            if selector_type in ['xpath', 'aria', 'data_attr', 'text']:
                # XPath-based selectors - pass selector as parameter to prevent injection
                result = await self._active_page.evaluate("""
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
                """, selector_value)
            else:
                # CSS selectors - pass selector as parameter to prevent injection
                result = await self._active_page.evaluate("""
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
                """, selector_value)

            return result
        except Exception as e:
            logger.error(f"Selector test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'count': 0,
                'time': 0
            }

    async def highlight_elements(self, selector_value: str, selector_type: str = 'xpath'):
        """
        Highlight all elements matching a selector (for visual validation)
        """
        if not self._active_page:
            return

        try:
            if selector_type in ['xpath', 'aria', 'data_attr', 'text']:
                # XPath-based selectors - pass selector as parameter to prevent injection
                await self._active_page.evaluate("""
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
                """, selector_value)
            else:
                # CSS selectors - pass selector as parameter to prevent injection
                await self._active_page.evaluate("""
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
                """, selector_value)
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

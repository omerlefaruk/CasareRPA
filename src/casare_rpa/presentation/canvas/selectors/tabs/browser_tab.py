"""
Browser Selector Tab.

Pick elements from browser using CSS, XPath, ARIA, data-testid selectors.
Integrates with SelectorManager and healing chain for context capture.
"""

import asyncio
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)

if TYPE_CHECKING:
    from playwright.async_api import Page


class BrowserSelectorTab(BaseSelectorTab):
    """
    Browser element selector tab.

    Features:
    - Pick element from browser via JS injector
    - Generate CSS, XPath, ARIA, data-testid, text selectors
    - Test and highlight selectors in browser
    - Capture healing context (fingerprint, spatial, CV)
    """

    # Signal emitted when element screenshot is captured (for image matching)
    element_screenshot_captured = Signal(bytes)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._browser_page: Page | None = None
        self._selector_manager = None
        self._healing_chain = None
        self._target_node = None
        self._target_property = "selector"
        self._element_fingerprint = None
        self._pending_capture_task = None  # Track pending capture for await

        self.setup_ui()

    @property
    def tab_name(self) -> str:
        return "Browser"

    @property
    def tab_icon(self) -> str:
        return "\U0001f310"  # Globe emoji

    def setup_ui(self) -> None:
        """Setup tab UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Pick element section
        pick_group = QGroupBox("Pick Element")
        pick_layout = QVBoxLayout(pick_group)

        # Info label
        info = QLabel(
            "Click 'Start Picking' then click any element in the browser.\n" "Press ESC to cancel."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #888;")
        pick_layout.addWidget(info)

        # Pick button
        btn_layout = QHBoxLayout()

        self.pick_btn = QPushButton("Start Picking")
        self.pick_btn.setObjectName("pickButton")
        self.pick_btn.clicked.connect(self._on_pick_clicked)
        self.pick_btn.setStyleSheet("""
            QPushButton#pickButton {
                background: #3b82f6;
                color: white;
                border: 1px solid #2563eb;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#pickButton:hover {
                background: #2563eb;
            }
        """)
        btn_layout.addWidget(self.pick_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)

        btn_layout.addStretch()
        pick_layout.addLayout(btn_layout)

        layout.addWidget(pick_group)

        # Element preview section
        preview_group = QGroupBox("Selected Element")
        preview_layout = QVBoxLayout(preview_group)

        self.element_preview = QLabel("No element selected")
        self.element_preview.setWordWrap(True)
        self.element_preview.setStyleSheet(
            "padding: 12px; background: #1a1a1a; border-radius: 6px; "
            "font-family: Consolas; color: #60a5fa;"
        )
        preview_layout.addWidget(self.element_preview)

        # Element details
        self.element_details = QLabel("")
        self.element_details.setWordWrap(True)
        self.element_details.setStyleSheet("color: #888; font-size: 11px;")
        preview_layout.addWidget(self.element_details)

        layout.addWidget(preview_group)

        # Healing context options
        healing_group = QGroupBox("Healing Context")
        healing_layout = QVBoxLayout(healing_group)

        healing_info = QLabel("Capture additional context for self-healing selectors at runtime.")
        healing_info.setStyleSheet("color: #888; font-size: 11px;")
        healing_layout.addWidget(healing_info)

        self.capture_fingerprint = QCheckBox("Capture element fingerprint")
        self.capture_fingerprint.setChecked(True)
        self.capture_fingerprint.setToolTip("Store element attributes for heuristic healing")
        healing_layout.addWidget(self.capture_fingerprint)

        self.capture_spatial = QCheckBox("Capture spatial context")
        self.capture_spatial.setChecked(True)
        self.capture_spatial.setToolTip("Store relationships with nearby anchor elements")
        healing_layout.addWidget(self.capture_spatial)

        self.capture_cv = QCheckBox("Capture CV template")
        self.capture_cv.setChecked(False)
        self.capture_cv.setToolTip("Store element screenshot for visual matching (slower)")
        healing_layout.addWidget(self.capture_cv)

        layout.addWidget(healing_group)

        layout.addStretch()

    def set_browser_page(self, page: "Page") -> None:
        """Set the browser page."""
        logger.info(f"BrowserSelectorTab.set_browser_page called: page={page is not None}")

        # Check if page changed - if so, we need a new selector manager
        if self._browser_page is not None and self._browser_page != page:
            logger.info("Browser page changed - will create new SelectorManager on next use")
            self._selector_manager = None  # Force new manager for new page

        self._browser_page = page
        self._init_selector_manager()

    def set_target_node(self, node: Any, property_name: str) -> None:
        """Set target node for auto-pasting."""
        self._target_node = node
        self._target_property = property_name

    def _init_selector_manager(self) -> None:
        """Initialize selector manager if page is available."""
        if not self._browser_page:
            return

        # Reuse existing selector manager to avoid callback registration issues
        # (Playwright's expose_function only registers once per page)
        if self._selector_manager is not None:
            logger.debug("Reusing existing SelectorManager instance")
            return

        try:
            from casare_rpa.utils.selectors.selector_manager import SelectorManager

            self._selector_manager = SelectorManager()
            logger.info("Created new SelectorManager instance")

            # Initialize healing chain lazily
            try:
                from casare_rpa.infrastructure.browser.healing.healing_chain import (
                    SelectorHealingChain,
                )

                self._healing_chain = SelectorHealingChain(
                    enable_cv_fallback=self.capture_cv.isChecked()
                )
            except ImportError:
                logger.debug("Healing chain not available")

        except Exception as e:
            logger.error(f"Failed to init selector manager: {e}")

    async def start_picking(self) -> None:
        """Start element picking mode."""
        if not self._browser_page:
            self._emit_status("No browser page available")
            logger.warning("Cannot start picking: no browser page")
            return

        if not self._selector_manager:
            self._init_selector_manager()

        if not self._selector_manager:
            self._emit_status("Selector manager not available")
            return

        try:
            self._emit_status("Picking mode active - click an element...")
            self.pick_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            # Inject and activate
            await self._selector_manager.inject_into_page(self._browser_page)
            await self._selector_manager.activate_selector_mode(
                recording=False,
                on_element_selected=self._on_element_selected,
            )

            logger.info("Browser picking mode started")

        except Exception as e:
            logger.error(f"Failed to start picking: {e}")
            self._emit_status(f"Error: {e}")
            self.pick_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    async def stop_picking(self) -> None:
        """Stop element picking mode."""
        if self._selector_manager:
            try:
                await self._selector_manager.deactivate_selector_mode()
            except Exception as e:
                logger.debug(f"Stop picking error: {e}")

        self.pick_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._emit_status("")

    def get_current_selector(self) -> SelectorResult | None:
        """Get current selector result."""
        return self._current_result

    async def ensure_capture_complete(self) -> None:
        """
        Await pending capture task to ensure healing data is captured.

        Call this before using the result when cv_template is needed
        (e.g., for ImageClickNode).
        """
        if self._pending_capture_task and not self._pending_capture_task.done():
            try:
                await self._pending_capture_task
                logger.debug("Pending capture task completed")
            except Exception as e:
                logger.warning(f"Capture task failed: {e}")
            finally:
                self._pending_capture_task = None

    def get_strategies(self) -> list[SelectorStrategy]:
        """Get generated strategies."""
        return self._strategies

    def _on_pick_clicked(self) -> None:
        """Handle pick button click."""
        asyncio.ensure_future(self.start_picking())

    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        asyncio.ensure_future(self.stop_picking())

    def _on_element_selected(self, fingerprint) -> None:
        """Handle element selection from browser."""
        logger.info(
            f"BrowserSelectorTab._on_element_selected: {fingerprint.tag_name} with {len(fingerprint.selectors)} selectors"
        )

        self._element_fingerprint = fingerprint

        # Update preview
        self.element_preview.setText(f"<{fingerprint.tag_name}>")
        logger.debug(
            f"Emitting selectors_generated signal with {len(fingerprint.selectors)} strategies"
        )

        # Build details
        details = []
        if fingerprint.element_id:
            details.append(f"ID: {fingerprint.element_id}")
        if fingerprint.class_names:
            details.append(f"Classes: {', '.join(fingerprint.class_names[:3])}")
        if fingerprint.text_content:
            text = fingerprint.text_content[:50]
            if len(fingerprint.text_content) > 50:
                text += "..."
            details.append(f"Text: {text}")

        self.element_details.setText(" | ".join(details) if details else "")

        # Convert fingerprint selectors to our SelectorStrategy format
        self._strategies = []
        for sel in fingerprint.selectors:
            strategy = SelectorStrategy(
                value=sel.value,
                selector_type=sel.selector_type.value,
                score=sel.score,
                is_unique=sel.is_unique,
                description=f"{sel.selector_type.value.upper()}: {sel.value[:40]}...",
            )
            self._strategies.append(strategy)

        # Sort by score
        self._strategies.sort(key=lambda s: -s.score)

        # Emit strategies
        logger.info(f"Emitting selectors_generated signal with {len(self._strategies)} strategies")
        self.selectors_generated.emit(self._strategies)
        logger.info("selectors_generated signal emitted")

        # Build result with healing context
        healing_context = {}
        if self._strategies:
            best = self._strategies[0]

            self._current_result = SelectorResult(
                selector_value=best.value,
                selector_type=best.selector_type,
                confidence=best.score / 100.0,
                is_unique=best.is_unique,
                healing_context=healing_context,
                metadata={
                    "tag_name": fingerprint.tag_name,
                    "element_id": fingerprint.element_id,
                    "class_names": fingerprint.class_names,
                    "text_content": fingerprint.text_content,
                },
            )

            # Capture healing context and screenshot together, then update result
            # Store task so we can await it before using result
            self._pending_capture_task = asyncio.ensure_future(
                self._capture_all_healing_data(best.value, fingerprint, healing_context)
            )

        # Stop picking mode
        asyncio.ensure_future(self.stop_picking())

        self._emit_status(
            f"Selected <{fingerprint.tag_name}> - {len(self._strategies)} selectors generated"
        )

    async def _capture_healing_context(self, selector: str, context: dict[str, Any]) -> None:
        """Capture healing context for the selector."""
        if not self._browser_page or not self._healing_chain:
            return

        try:
            # Capture if options are checked
            if self.capture_fingerprint.isChecked():
                fingerprint = await self._healing_chain._heuristic_healer.capture_fingerprint(
                    self._browser_page, selector
                )
                if fingerprint:
                    context["fingerprint"] = fingerprint.__dict__

            if self.capture_spatial.isChecked():
                spatial = await self._healing_chain._anchor_healer.capture_spatial_context(
                    self._browser_page, selector
                )
                if spatial:
                    context["spatial"] = spatial.__dict__

            if self.capture_cv.isChecked() and self._healing_chain._cv_healer:
                cv_ctx = await self._healing_chain._cv_healer.capture_cv_context(
                    self._browser_page, selector
                )
                if cv_ctx:
                    # Don't store binary template in JSON
                    context["cv"] = {
                        "text_content": cv_ctx.text_content,
                        "expected_position": cv_ctx.expected_position,
                        "expected_size": cv_ctx.expected_size,
                        "element_type": cv_ctx.element_type,
                    }

            logger.debug(f"Captured healing context: {list(context.keys())}")

        except Exception as e:
            logger.debug(f"Failed to capture healing context: {e}")

    async def _capture_all_healing_data(
        self, selector: str, fingerprint, context: dict[str, Any]
    ) -> None:
        """
        Capture all healing data including context and screenshot.

        This method ensures both are captured before the result is finalized,
        which is important for ImageClickNode that needs the cv_template.
        """
        # First capture the healing context
        await self._capture_healing_context(selector, context)

        # Then capture the element screenshot (updates self._current_result.healing_context)
        await self._capture_element_screenshot(fingerprint)

        logger.info(f"All healing data captured. cv_template present: {'cv_template' in context}")

    async def _capture_element_screenshot(self, fingerprint) -> None:
        """Capture screenshot of the selected element for image matching and healing."""
        if not self._browser_page:
            logger.debug("No browser page for element screenshot")
            return

        try:
            # Get bounding rect from fingerprint
            rect = getattr(fingerprint, "rect", None)
            if not rect:
                logger.debug("No bounding rect in fingerprint")
                return

            # Extract clip dimensions (rect is a dict with x, y, width, height)
            x = rect.get("x", rect.get("left", 0))
            y = rect.get("y", rect.get("top", 0))
            width = rect.get("width", 0)
            height = rect.get("height", 0)

            if width <= 0 or height <= 0:
                logger.debug(f"Invalid rect dimensions: {width}x{height}")
                return

            # Add small padding around element
            padding = 5
            clip = {
                "x": max(0, x - padding),
                "y": max(0, y - padding),
                "width": width + (padding * 2),
                "height": height + (padding * 2),
            }

            # Capture screenshot of just the element
            screenshot_bytes = await self._browser_page.screenshot(
                type="png",
                clip=clip,
            )

            logger.info(
                f"Captured element screenshot: {len(screenshot_bytes)} bytes, {width}x{height}"
            )

            # Store in current result's healing context for CV fallback at runtime
            import base64

            if self._current_result:
                logger.info(
                    f"Storing cv_template in healing_context (current keys: {list(self._current_result.healing_context.keys())})"
                )
                self._current_result.healing_context["cv_template"] = {
                    "image_base64": base64.b64encode(screenshot_bytes).decode("utf-8"),
                    "width": width,
                    "height": height,
                    "padding": padding,
                }
                logger.info("Stored CV template in healing context")

            # Emit signal for image match tab
            self.element_screenshot_captured.emit(screenshot_bytes)

        except Exception as e:
            logger.debug(f"Failed to capture element screenshot: {e}")

    async def test_selector(self, selector: str, selector_type: str) -> dict[str, Any]:
        """Test selector against browser page."""
        if not self._browser_page:
            return {"success": False, "error": "No browser page"}

        if not self._selector_manager:
            return {"success": False, "error": "Selector manager not initialized"}

        try:
            # Ensure page is injected for test to work
            await self._selector_manager.inject_into_page(self._browser_page)

            result = await self._selector_manager.test_selector(selector, selector_type)
            return {
                "success": True,
                "count": result.get("count", 0),
                "time_ms": result.get("time", 0),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def highlight_selector(self, selector: str, selector_type: str) -> bool:
        """Highlight selector in browser."""
        if not self._browser_page or not self._selector_manager:
            return False

        try:
            # Ensure page is injected for highlight to work
            await self._selector_manager.inject_into_page(self._browser_page)
            await self._selector_manager.highlight_elements(selector, selector_type)
            return True
        except Exception as e:
            logger.error(f"Highlight failed: {e}")
            return False

    def clear(self) -> None:
        """Clear current state."""
        super().clear()
        self._element_fingerprint = None
        self.element_preview.setText("No element selected")
        self.element_details.setText("")

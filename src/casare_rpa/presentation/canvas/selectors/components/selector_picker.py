"""
Selector Picker Component.

Handles all element picking logic across different modes:
- Browser element picking (CSS, XPath, ARIA)
- Desktop element picking (AutomationId, Name, Path)
- OCR text detection
- Image/template matching
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from loguru import logger

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)

if TYPE_CHECKING:
    from playwright.async_api import Page


class SelectorPicker(QObject):
    """
    Manages element picking across different modes.

    Coordinates with tab implementations to perform actual picking
    and emits signals when elements are picked or strategies generated.

    Signals:
        strategies_generated: Emitted when selectors are generated (List[SelectorStrategy])
        status_changed: Emitted when status message changes (str)
        element_screenshot_captured: Emitted when element screenshot is taken (bytes)
        anchor_picked: Emitted when anchor element is picked (Dict)
        picking_started: Emitted when picking mode begins (str mode)
        picking_stopped: Emitted when picking mode ends ()
    """

    strategies_generated = Signal(list)
    status_changed = Signal(str)
    element_screenshot_captured = Signal(bytes)
    anchor_picked = Signal(dict)
    picking_started = Signal(str)
    picking_stopped = Signal()

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)

        self._tabs: Dict[str, BaseSelectorTab] = {}
        self._browser_page: Optional["Page"] = None
        self._current_mode: str = "browser"
        self._is_picking: bool = False
        self._picking_anchor: bool = False
        self._current_result: Optional[SelectorResult] = None
        self._strategies: List[SelectorStrategy] = []

    def register_tab(self, mode: str, tab: BaseSelectorTab) -> None:
        """
        Register a tab for a specific picking mode.

        Args:
            mode: Mode identifier (browser, desktop, ocr, image)
            tab: Tab implementation for this mode
        """
        self._tabs[mode] = tab
        tab.selectors_generated.connect(self._on_tab_strategies_generated)
        tab.status_changed.connect(self._on_tab_status_changed)

        if hasattr(tab, "element_screenshot_captured"):
            tab.element_screenshot_captured.connect(self._on_element_screenshot)

        logger.debug(f"Registered tab for mode: {mode}")

    def set_browser_page(self, page: "Page") -> None:
        """Set the browser page for browser operations."""
        logger.info(f"SelectorPicker.set_browser_page: page={page is not None}")
        self._browser_page = page
        for tab in self._tabs.values():
            tab.set_browser_page(page)

    def set_current_mode(self, mode: str) -> None:
        """Set the current picking mode."""
        if mode in self._tabs:
            # Deactivate previous mode
            for m, tab in self._tabs.items():
                tab.set_active(m == mode)
            self._current_mode = mode
            logger.debug(f"Picker mode changed to: {mode}")

    @property
    def current_mode(self) -> str:
        """Get current picking mode."""
        return self._current_mode

    @property
    def is_picking(self) -> bool:
        """Check if currently in picking mode."""
        return self._is_picking

    @property
    def strategies(self) -> List[SelectorStrategy]:
        """Get last generated strategies."""
        return self._strategies

    @property
    def current_result(self) -> Optional[SelectorResult]:
        """Get current selector result."""
        return self._current_result

    def has_browser_page(self) -> bool:
        """Check if browser page is available."""
        return self._browser_page is not None

    async def start_picking(self, mode: Optional[str] = None) -> bool:
        """
        Start element picking for specified mode.

        Args:
            mode: Optional mode override (uses current_mode if None)

        Returns:
            True if picking started successfully
        """
        pick_mode = mode or self._current_mode

        # Validate browser mode has page
        if pick_mode == "browser" and not self._browser_page:
            self.status_changed.emit("Run a Navigate node first to open browser")
            logger.warning("Cannot start browser picking: no browser page")
            return False

        tab = self._tabs.get(pick_mode)
        if not tab:
            logger.error(f"No tab registered for mode: {pick_mode}")
            return False

        self._is_picking = True
        self.picking_started.emit(pick_mode)

        mode_names = {
            "browser": "Browser",
            "desktop": "Desktop",
            "ocr": "OCR",
            "image": "Image",
        }
        mode_name = mode_names.get(pick_mode, pick_mode)

        if pick_mode == "browser":
            self.status_changed.emit(f"{mode_name} picking active - Ctrl+Click element in browser")
        else:
            self.status_changed.emit(f"{mode_name} picking active...")

        try:
            await tab.start_picking()
            return True
        except Exception as e:
            logger.error(f"Failed to start picking: {e}")
            self.status_changed.emit(f"Error: {e}")
            self._is_picking = False
            self.picking_stopped.emit()
            return False

    async def stop_picking(self) -> None:
        """Stop any active picking mode."""
        self._is_picking = False
        for tab in self._tabs.values():
            try:
                await tab.stop_picking()
            except Exception as e:
                logger.debug(f"Error stopping tab: {e}")
        self.picking_stopped.emit()

    async def start_anchor_picking(self) -> bool:
        """
        Start anchor element picking mode.

        Returns:
            True if anchor picking started successfully
        """
        if self._current_mode == "browser" and not self._browser_page:
            self.status_changed.emit("Run a Navigate node first to open browser")
            return False

        self._picking_anchor = True
        self.status_changed.emit("ANCHOR MODE: Ctrl+Click a reference element...")

        tab = self._tabs.get(self._current_mode)
        if tab:
            try:
                await tab.start_picking()
                return True
            except Exception as e:
                logger.error(f"Failed to start anchor picking: {e}")
                self.status_changed.emit(f"Error: {e}")
                self._picking_anchor = False
                return False
        return False

    async def auto_detect_anchor(self, target_selector: str) -> Optional[Dict[str, Any]]:
        """
        Auto-detect the best anchor for a target element.

        Args:
            target_selector: The target element's selector

        Returns:
            Anchor data dict or None if not found
        """
        if self._current_mode == "browser" and not self._browser_page:
            self.status_changed.emit("No browser open - cannot auto-detect anchor")
            return None

        try:
            from casare_rpa.utils.selectors.anchor_locator import AnchorLocator

            locator = AnchorLocator()
            anchor_data = await locator.auto_detect_anchor(
                self._browser_page,
                target_selector,
            )
            return anchor_data

        except ImportError:
            logger.warning("AnchorLocator not available")
            self.status_changed.emit("Anchor auto-detect not available")
            return None
        except Exception as e:
            logger.error(f"Anchor auto-detection failed: {e}")
            self.status_changed.emit(f"Error: {e}")
            return None

    def get_current_selector_from_tab(self) -> Optional[SelectorResult]:
        """Get current selector from active tab."""
        tab = self._tabs.get(self._current_mode)
        if tab:
            return tab.get_current_selector()
        return None

    def _on_tab_strategies_generated(self, strategies: List[SelectorStrategy]) -> None:
        """Handle strategies generated from a tab."""
        logger.info(f"Picker received {len(strategies)} strategies")

        if self._picking_anchor:
            self._picking_anchor = False
            self._is_picking = False
            self.picking_stopped.emit()

            if strategies:
                best = strategies[0]
                anchor_data = {
                    "selector": best.value,
                    "selector_type": best.selector_type,
                    "score": best.score,
                    "is_unique": best.is_unique,
                }
                self.anchor_picked.emit(anchor_data)
                self.status_changed.emit(f"Anchor set: {best.value[:30]}...")
            else:
                self.status_changed.emit("No anchor element found")
            return

        # Normal picking flow
        self._strategies = strategies
        self._is_picking = False
        self.picking_stopped.emit()

        if strategies:
            best = strategies[0]
            self._current_result = SelectorResult(
                selector_value=best.value,
                selector_type=best.selector_type,
                confidence=best.score / 100.0,
                is_unique=best.is_unique,
            )
            self.status_changed.emit(f"{len(strategies)} selectors generated")
        else:
            self.status_changed.emit("No selectors generated")

        self.strategies_generated.emit(strategies)

    def _on_tab_status_changed(self, message: str) -> None:
        """Forward status from tab."""
        self.status_changed.emit(message)

    def _on_element_screenshot(self, screenshot_bytes: bytes) -> None:
        """Forward element screenshot from tab."""
        self.element_screenshot_captured.emit(screenshot_bytes)

    def update_result_from_strategy(self, strategy: SelectorStrategy) -> None:
        """
        Update current result from a selected strategy.

        Args:
            strategy: The selected strategy
        """
        tab = self._tabs.get(self._current_mode)
        if tab:
            result = tab.get_current_selector()
            if result:
                result.selector_value = strategy.value
                result.selector_type = strategy.selector_type
                result.confidence = strategy.score / 100.0
                result.is_unique = strategy.is_unique
                self._current_result = result
            else:
                self._current_result = SelectorResult(
                    selector_value=strategy.value,
                    selector_type=strategy.selector_type,
                    confidence=strategy.score / 100.0,
                    is_unique=strategy.is_unique,
                )

    def clear(self) -> None:
        """Clear current state."""
        self._current_result = None
        self._strategies = []
        self._is_picking = False
        self._picking_anchor = False

        for tab in self._tabs.values():
            tab.clear()

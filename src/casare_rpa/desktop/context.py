"""
Desktop Context - Main entry point for desktop automation

Manages windows, applications, and provides high-level desktop automation API.

This module provides a backward-compatible API that wraps the new async-first
managers. Both sync and async methods are available:
- Sync methods: find_window(), launch_application(), etc.
- Async methods: Use the managers directly or context_new.DesktopContext

Note: Sync methods use asyncio.run() internally. Prefer async methods when
running within an asyncio event loop to avoid blocking.
"""

import asyncio
from typing import Any, Dict, List, Optional, Union
from loguru import logger
import uiautomation as auto

from casare_rpa.desktop.element import DesktopElement
from casare_rpa.desktop.managers.form_interactor import FormInteractor
from casare_rpa.desktop.managers.keyboard_controller import KeyboardController
from casare_rpa.desktop.managers.mouse_controller import MouseController
from casare_rpa.desktop.managers.screen_capture import ScreenCapture
from casare_rpa.desktop.managers.wait_manager import WaitManager
from casare_rpa.desktop.managers.window_manager import WindowManager
from casare_rpa.desktop.selector import find_element as selector_find_element


def _run_async(coro):
    """Run async coroutine synchronously, handling existing event loops."""
    try:
        loop = asyncio.get_running_loop()
        # If we're in an async context, we can't use asyncio.run()
        # Use a thread pool to run the coroutine
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running event loop, safe to use asyncio.run()
        return asyncio.run(coro)


class DesktopContext:
    """
    Desktop automation context for managing Windows applications and UI elements.

    Provides methods to launch applications, find windows, and interact with desktop UI.
    Both sync and async methods are available for flexibility.

    Example (sync):
        with DesktopContext() as ctx:
            window = ctx.find_window("Notepad")
            ctx.send_keys("Hello!")

    Example (async):
        async with DesktopContext() as ctx:
            window = await ctx.async_find_window("Notepad")
            await ctx.async_send_keys("Hello!")
    """

    def __init__(self):
        """Initialize desktop automation context."""
        logger.debug("Initializing DesktopContext")

        # Initialize managers
        self._window_manager = WindowManager()
        self._mouse_controller = MouseController()
        self._keyboard_controller = KeyboardController()
        self._form_interactor = FormInteractor()
        self._screen_capture = ScreenCapture()
        self._wait_manager = WaitManager()

        # Track launched processes for cleanup
        self._launched_processes = []

    # =========================================================================
    # Window Operations - Sync API (backward compatible)
    # =========================================================================

    def find_window(
        self, title: str, exact: bool = False, timeout: float = 5.0
    ) -> Optional[DesktopElement]:
        """Find a window by its title (sync version)."""
        return _run_async(self._window_manager.find_window(title, exact, timeout))

    async def async_find_window(
        self, title: str, exact: bool = False, timeout: float = 5.0
    ) -> Optional[DesktopElement]:
        """Find a window by its title (async version)."""
        return await self._window_manager.find_window(title, exact, timeout)

    def get_all_windows(self, include_invisible: bool = False) -> List[DesktopElement]:
        """Get all top-level windows (sync version)."""
        return _run_async(self._window_manager.get_all_windows(include_invisible))

    def launch_application(
        self,
        path: str,
        args: str = "",
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None,
    ) -> DesktopElement:
        """Launch an application and return its main window (sync version)."""
        return _run_async(
            self._window_manager.launch_application(
                path, args, working_dir, timeout, window_title
            )
        )

    async def async_launch_application(
        self,
        path: str,
        args: str = "",
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None,
        keep_open: bool = True,
    ) -> DesktopElement:
        """Launch an application and return its main window (async version).

        Args:
            keep_open: If True, the app won't be closed when workflow ends (default: True)
        """
        return await self._window_manager.launch_application(
            path, args, working_dir, timeout, window_title, keep_open=keep_open
        )

    def close_application(
        self,
        window_or_pid: Union[DesktopElement, int, str],
        force: bool = False,
        timeout: float = 5.0,
    ) -> bool:
        """Close an application (sync version)."""
        return _run_async(
            self._window_manager.close_application(window_or_pid, force, timeout)
        )

    async def async_close_application(
        self,
        window_or_pid: Union[DesktopElement, int, str],
        force: bool = False,
        timeout: float = 5.0,
    ) -> bool:
        """Close an application (async version)."""
        return await self._window_manager.close_application(
            window_or_pid, force, timeout
        )

    def resize_window(self, window: DesktopElement, width: int, height: int) -> bool:
        """Resize a window to specified dimensions (sync version)."""
        return _run_async(self._window_manager.resize_window(window, width, height))

    def move_window(self, window: DesktopElement, x: int, y: int) -> bool:
        """Move a window to specified position (sync version)."""
        return _run_async(self._window_manager.move_window(window, x, y))

    def maximize_window(self, window: DesktopElement) -> bool:
        """Maximize a window (sync version)."""
        return _run_async(self._window_manager.maximize_window(window))

    def minimize_window(self, window: DesktopElement) -> bool:
        """Minimize a window (sync version)."""
        return _run_async(self._window_manager.minimize_window(window))

    def restore_window(self, window: DesktopElement) -> bool:
        """Restore a window to normal state (sync version)."""
        return _run_async(self._window_manager.restore_window(window))

    def get_window_properties(self, window: DesktopElement) -> Dict[str, Any]:
        """Get comprehensive properties of a window (sync version)."""
        return _run_async(self._window_manager.get_window_properties(window))

    # =========================================================================
    # Mouse Operations - Sync API
    # =========================================================================

    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """Move mouse cursor to specified position (sync version)."""
        return _run_async(self._mouse_controller.move_mouse(x, y, duration))

    def click_mouse(
        self,
        x: int = None,
        y: int = None,
        button: str = "left",
        click_type: str = "single",
    ) -> bool:
        """Click mouse at specified position (sync version)."""
        return _run_async(self._mouse_controller.click(x, y, button, click_type))

    def get_mouse_position(self) -> tuple:
        """Get current mouse cursor position (sync version)."""
        return _run_async(self._mouse_controller.get_position())

    def drag_mouse(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        duration: float = 0.5,
    ) -> bool:
        """Drag mouse from one position to another (sync version)."""
        return _run_async(
            self._mouse_controller.drag(
                start_x, start_y, end_x, end_y, button, duration
            )
        )

    # =========================================================================
    # Keyboard Operations - Sync API
    # =========================================================================

    def send_keys(self, keys: str, interval: float = 0.0) -> bool:
        """Send keyboard input (sync version)."""
        return _run_async(self._keyboard_controller.send_keys(keys, interval))

    def send_hotkey(self, *keys: str) -> bool:
        """Send a hotkey combination (sync version)."""
        return _run_async(self._keyboard_controller.send_hotkey(*keys))

    # =========================================================================
    # Form Operations - Sync API
    # =========================================================================

    def select_from_dropdown(
        self, element: DesktopElement, value: str, by_text: bool = True
    ) -> bool:
        """Select an item from a dropdown/combobox (sync version)."""
        return _run_async(
            self._form_interactor.select_from_dropdown(element, value, by_text)
        )

    def check_checkbox(self, element: DesktopElement, check: bool = True) -> bool:
        """Check or uncheck a checkbox (sync version)."""
        return _run_async(self._form_interactor.check_checkbox(element, check))

    def select_radio_button(self, element: DesktopElement) -> bool:
        """Select a radio button (sync version)."""
        return _run_async(self._form_interactor.select_radio_button(element))

    def select_tab(
        self,
        tab_control: DesktopElement,
        tab_name: str = None,
        tab_index: int = None,
    ) -> bool:
        """Select a tab in a tab control (sync version)."""
        return _run_async(
            self._form_interactor.select_tab(tab_control, tab_name, tab_index)
        )

    def expand_tree_item(self, element: DesktopElement, expand: bool = True) -> bool:
        """Expand or collapse a tree item (sync version)."""
        return _run_async(self._form_interactor.expand_tree_item(element, expand))

    def scroll_element(
        self,
        element: DesktopElement,
        direction: str = "down",
        amount: Union[float, str] = 0.5,
    ) -> bool:
        """Scroll an element (sync version)."""
        return _run_async(
            self._form_interactor.scroll_element(element, direction, amount)
        )

    # =========================================================================
    # Screenshot & OCR Operations - Sync API
    # =========================================================================

    def capture_screenshot(
        self,
        file_path: str = None,
        region: Dict[str, int] = None,
        format: str = "PNG",
    ) -> Optional[Any]:
        """Capture a screenshot (sync version)."""
        return _run_async(
            self._screen_capture.capture_screenshot(file_path, region, format)
        )

    def capture_element_image(
        self,
        element: DesktopElement,
        file_path: str = None,
        padding: int = 0,
        format: str = "PNG",
    ) -> Optional[Any]:
        """Capture an image of a specific desktop element (sync version)."""
        return _run_async(
            self._screen_capture.capture_element_image(
                element, file_path, padding, format
            )
        )

    def ocr_extract_text(
        self,
        image: Any = None,
        image_path: str = None,
        region: Dict[str, int] = None,
        language: str = "eng",
        config: str = "",
        engine: str = "auto",
    ) -> Optional[str]:
        """Extract text from an image using OCR (sync version)."""
        return _run_async(
            self._screen_capture.ocr_extract_text(
                image, image_path, region, language, config, engine
            )
        )

    def compare_images(
        self,
        image1: Any = None,
        image2: Any = None,
        image1_path: str = None,
        image2_path: str = None,
        method: str = "ssim",
        threshold: float = 0.9,
    ) -> Dict[str, Any]:
        """Compare two images and return similarity metrics (sync version)."""
        return _run_async(
            self._screen_capture.compare_images(
                image1, image2, image1_path, image2_path, method, threshold
            )
        )

    # =========================================================================
    # Wait Operations - Sync API
    # =========================================================================

    def wait_for_element(
        self,
        selector: Dict[str, Any],
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
        parent: auto.Control = None,
    ) -> Optional[DesktopElement]:
        """Wait for an element to reach a specific state (sync version)."""
        return _run_async(
            self._wait_manager.wait_for_element(
                selector, timeout, state, poll_interval, parent
            )
        )

    async def async_wait_for_element(
        self,
        selector: Dict[str, Any],
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
        parent: auto.Control = None,
    ) -> Optional[DesktopElement]:
        """Wait for an element to reach a specific state (async version)."""
        return await self._wait_manager.wait_for_element(
            selector, timeout, state, poll_interval, parent
        )

    def wait_for_window(
        self,
        title: str = None,
        title_regex: str = None,
        class_name: str = None,
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
    ) -> Optional[auto.Control]:
        """Wait for a window to reach a specific state (sync version)."""
        return _run_async(
            self._wait_manager.wait_for_window(
                title, title_regex, class_name, timeout, state, poll_interval
            )
        )

    async def async_wait_for_window(
        self,
        title: str = None,
        title_regex: str = None,
        class_name: str = None,
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
    ) -> Optional[auto.Control]:
        """Wait for a window to reach a specific state (async version)."""
        return await self._wait_manager.wait_for_window(
            title, title_regex, class_name, timeout, state, poll_interval
        )

    def element_exists(
        self,
        selector: Dict[str, Any],
        timeout: float = 0.0,
        parent: auto.Control = None,
    ) -> bool:
        """Check if an element exists (sync version)."""
        return _run_async(self._wait_manager.element_exists(selector, timeout, parent))

    def verify_element_property(
        self,
        element: DesktopElement,
        property_name: str,
        expected_value: Any,
        comparison: str = "equals",
    ) -> bool:
        """Verify an element property has an expected value (sync version)."""
        return _run_async(
            self._wait_manager.verify_element_property(
                element, property_name, expected_value, comparison
            )
        )

    # =========================================================================
    # Element Finding
    # =========================================================================

    def find_element(
        self,
        selector: Dict[str, Any],
        timeout: float = 5.0,
        parent: auto.Control = None,
    ) -> Optional[DesktopElement]:
        """Find an element using selector (sync version)."""
        search_parent = parent if parent else auto.GetRootControl()
        return selector_find_element(search_parent, selector, timeout)

    # =========================================================================
    # Lifecycle Management
    # =========================================================================

    def cleanup(self):
        """Clean up resources and close applications launched by this context."""
        logger.info("Cleaning up DesktopContext")
        self._window_manager.cleanup()
        self._launched_processes.clear()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources."""
        self.cleanup()
        return False

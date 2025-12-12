"""
Window Manager - Desktop window operations

Handles finding, launching, closing, resizing, and managing Windows desktop windows.
All operations are async-first with proper error handling.
"""

import asyncio
import os
import shlex
import subprocess
import time
from typing import Any, Dict, List, Optional, Union

import psutil
import uiautomation as auto
from loguru import logger

from casare_rpa.desktop.element import DesktopElement


class WindowManager:
    """
    Manages Windows desktop window operations.

    Provides async methods for finding, launching, and manipulating windows.
    Uses asyncio.to_thread() for blocking UIAutomation calls.
    """

    def __init__(self) -> None:
        """Initialize window manager."""
        logger.debug("Initializing WindowManager")
        self._launched_processes: List[int] = []
        # PIDs to keep open when cleanup is called
        self._keep_open_processes: set[int] = set()

    async def find_window(
        self, title: str, exact: bool = False, timeout: float = 5.0
    ) -> Optional[DesktopElement]:
        """
        Find a window by its title.

        Args:
            title: Window title to search for
            exact: If True, match exact title; if False, match partial title
            timeout: Maximum time to wait for window (seconds)

        Returns:
            DesktopElement wrapping the window, or None if not found

        Raises:
            ValueError: If window is not found within timeout
        """
        logger.debug(f"Finding window: '{title}' (exact={exact}, timeout={timeout}s)")

        start_time = time.time()
        check_count = 0
        max_quick_checks = 30

        def _search_window() -> Optional[DesktopElement]:
            """Blocking window search - runs in thread."""
            with auto.UIAutomationInitializerInThread():
                try:
                    if exact:
                        window = auto.WindowControl(searchDepth=1, Name=title)
                    else:
                        window = auto.WindowControl(searchDepth=1, SubName=title)

                    if window.Exists(0, 0):
                        return DesktopElement(window)
                except Exception as e:
                    logger.debug(f"Window search attempt failed: {e}")
                return None

        while time.time() - start_time < timeout:
            check_count += 1

            result = await asyncio.to_thread(_search_window)
            if result is not None:
                logger.info(f"Found window: '{result.get_text()}'")
                return result

            if check_count < max_quick_checks:
                await asyncio.sleep(0.1)
            else:
                await asyncio.sleep(0.5)

        error_msg = f"Window not found: '{title}' (exact={exact})"
        logger.error(error_msg)
        raise ValueError(error_msg)

    async def get_all_windows(
        self, include_invisible: bool = False
    ) -> List[DesktopElement]:
        """
        Get all top-level windows.

        Args:
            include_invisible: If True, include invisible/hidden windows

        Returns:
            List of DesktopElement objects representing windows
        """
        logger.debug(f"Getting all windows (include_invisible={include_invisible})")

        def _get_windows() -> List[DesktopElement]:
            with auto.UIAutomationInitializerInThread():
                windows = []
                for window in auto.GetRootControl().GetChildren():
                    if window.ControlTypeName == "WindowControl":
                        if include_invisible or window.IsEnabled:
                            windows.append(DesktopElement(window))
                return windows

        windows = await asyncio.to_thread(_get_windows)
        logger.info(f"Found {len(windows)} windows")
        return windows

    async def launch_application(
        self,
        path: str,
        args: str = "",
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None,
        keep_open: bool = True,
    ) -> DesktopElement:
        """
        Launch an application and return its main window.

        Args:
            path: Path to executable or command name
            args: Command line arguments
            working_dir: Working directory for the process
            timeout: Maximum time to wait for window to appear
            window_title: Expected window title (if None, uses process name)
            keep_open: If True, don't close this app on cleanup (default: True)

        Returns:
            DesktopElement wrapping the application's main window

        Raises:
            RuntimeError: If application fails to launch or window not found
        """
        logger.info(f"Launching application: {path} {args} (keep_open={keep_open})")

        try:
            cmd_list = [path]
            if args:
                try:
                    parsed_args = shlex.split(args)
                    cmd_list.extend(parsed_args)
                except ValueError as e:
                    logger.warning(
                        f"Could not parse args with shlex: {e}, using simple split"
                    )
                    cmd_list.extend(args.split())

            process = subprocess.Popen(cmd_list, cwd=working_dir, shell=False)

            self._launched_processes.append(process.pid)
            if keep_open:
                self._keep_open_processes.add(process.pid)
                logger.debug(
                    f"Process launched with PID: {process.pid} (will keep open)"
                )
            else:
                logger.debug(
                    f"Process launched with PID: {process.pid} (will close on cleanup)"
                )

            await asyncio.sleep(0.5)

            if window_title is None:
                exe_name = os.path.splitext(os.path.basename(path))[0]
                window_title = exe_name

            # Use full timeout for title search as it's more reliable than PID for modern apps
            window_search_timeout = timeout

            try:
                window = await self.find_window(
                    window_title, exact=False, timeout=window_search_timeout
                )
                logger.info(f"Application launched successfully: {window_title}")
                return window
            except ValueError:
                logger.warning(
                    f"Could not find window by title '{window_title}' "
                    f"after {window_search_timeout}s, searching by process..."
                )

                def _search_by_pid() -> Optional[DesktopElement]:
                    """Search for window by PID - runs in thread."""
                    with auto.UIAutomationInitializerInThread():
                        search_start = time.time()
                        max_search_time = 3.0
                        windows_checked = 0

                        try:
                            for window in auto.GetRootControl().GetChildren():
                                if time.time() - search_start > max_search_time:
                                    logger.warning(
                                        f"Process-based window search timed out "
                                        f"after checking {windows_checked} windows"
                                    )
                                    break

                                windows_checked += 1

                                if (
                                    window.ControlTypeName == "WindowControl"
                                    and window.IsEnabled
                                ):
                                    try:
                                        if window.ProcessId == process.pid:
                                            return DesktopElement(window)
                                    except Exception:
                                        continue

                            logger.error(
                                f"No window found for PID {process.pid} "
                                f"after checking {windows_checked} windows"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error during process-based window search: {e}"
                            )
                        return None

                result = await asyncio.to_thread(_search_by_pid)
                if result is not None:
                    window_title_found = result.get_text()
                    logger.info(f"Found window by process ID: {window_title_found}")
                    return result

                raise RuntimeError(f"Failed to find window for application: {path}")

        except Exception as e:
            error_msg = f"Failed to launch application '{path}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    async def close_application(
        self,
        window_or_pid: Union[DesktopElement, int, str],
        force: bool = False,
        timeout: float = 5.0,
    ) -> bool:
        """
        Close an application.

        Args:
            window_or_pid: DesktopElement (window), process ID, or window title
            force: If True, force kill the process; if False, try graceful close
            timeout: Maximum time to wait for graceful close

        Returns:
            True if application was closed successfully

        Raises:
            ValueError: If application not found or failed to close
        """
        logger.debug(f"Closing application (force={force})")

        try:
            if isinstance(window_or_pid, DesktopElement):
                window = window_or_pid
            elif isinstance(window_or_pid, int):

                def _find_by_pid() -> Optional[DesktopElement]:
                    with auto.UIAutomationInitializerInThread():
                        all_windows = []
                        for w in auto.GetRootControl().GetChildren():
                            if w.ControlTypeName == "WindowControl" and w.IsEnabled:
                                all_windows.append(DesktopElement(w))
                        for w in all_windows:
                            try:
                                if w._control.ProcessId == window_or_pid:
                                    return w
                            except Exception:
                                pass
                        return None

                window = await asyncio.to_thread(_find_by_pid)
                if window is None:
                    raise ValueError(f"No window found for PID: {window_or_pid}")
            else:
                window = await self.find_window(window_or_pid)

            pid = window._control.ProcessId

            if force:

                def _force_kill() -> bool:
                    logger.info(f"Force killing process {pid}")
                    try:
                        process = psutil.Process(pid)
                        process.kill()
                        process.wait(timeout=timeout)
                    except psutil.NoSuchProcess:
                        pass
                    return True

                return await asyncio.to_thread(_force_kill)
            else:
                logger.info(f"Attempting graceful close of window: {window.get_text()}")

                def _try_close() -> None:
                    with auto.UIAutomationInitializerInThread():
                        try:
                            window._control.GetWindowPattern().Close()
                        except Exception as e:
                            logger.debug(
                                f"WindowPattern.Close() failed, trying Alt+F4: {e}"
                            )
                            window._control.SetFocus()
                            window._control.SendKeys("{Alt}F4")

                await asyncio.to_thread(_try_close)

                start_time = time.time()
                while time.time() - start_time < timeout:
                    exists = await asyncio.to_thread(
                        lambda: window._control.Exists(0, 0)
                    )
                    if not exists:
                        logger.info("Application closed successfully")
                        return True
                    await asyncio.sleep(0.1)

                logger.warning(f"Graceful close timed out, force killing PID {pid}")

                def _force_kill_fallback() -> None:
                    try:
                        process = psutil.Process(pid)
                        process.kill()
                    except psutil.NoSuchProcess:
                        pass

                await asyncio.to_thread(_force_kill_fallback)
                return True

        except Exception as e:
            error_msg = f"Failed to close application: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    async def resize_window(
        self, window: DesktopElement, width: int, height: int
    ) -> bool:
        """
        Resize a window to specified dimensions.

        Args:
            window: DesktopElement representing the window
            width: New width in pixels
            height: New height in pixels

        Returns:
            True if resize was successful

        Raises:
            ValueError: If window cannot be resized
        """
        logger.debug(f"Resizing window to {width}x{height}")

        def _resize() -> bool:
            with auto.UIAutomationInitializerInThread():
                try:
                    import win32gui

                    hwnd = window._control.NativeWindowHandle
                    rect = window.get_bounding_rect()
                    current_x = rect["left"]
                    current_y = rect["top"]
                    win32gui.MoveWindow(hwnd, current_x, current_y, width, height, True)
                    return True
                except Exception as e:
                    raise ValueError(f"Failed to resize window: {e}")

        result = await asyncio.to_thread(_resize)
        logger.info(f"Resized window to {width}x{height}")
        return result

    async def move_window(self, window: DesktopElement, x: int, y: int) -> bool:
        """
        Move a window to specified position.

        Args:
            window: DesktopElement representing the window
            x: New X position (left edge)
            y: New Y position (top edge)

        Returns:
            True if move was successful

        Raises:
            ValueError: If window cannot be moved
        """
        logger.debug(f"Moving window to ({x}, {y})")

        def _move() -> bool:
            with auto.UIAutomationInitializerInThread():
                try:
                    import win32gui

                    hwnd = window._control.NativeWindowHandle
                    rect = window.get_bounding_rect()
                    current_width = rect["width"]
                    current_height = rect["height"]
                    win32gui.MoveWindow(hwnd, x, y, current_width, current_height, True)
                    return True
                except Exception as e:
                    raise ValueError(f"Failed to move window: {e}")

        result = await asyncio.to_thread(_move)
        logger.info(f"Moved window to ({x}, {y})")
        return result

    async def maximize_window(self, window: DesktopElement) -> bool:
        """
        Maximize a window.

        Args:
            window: DesktopElement representing the window

        Returns:
            True if maximize was successful
        """
        logger.debug("Maximizing window")

        def _maximize() -> bool:
            with auto.UIAutomationInitializerInThread():
                try:
                    import win32con
                    import win32gui

                    hwnd = window._control.NativeWindowHandle
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    return True
                except Exception as e:
                    raise ValueError(f"Failed to maximize window: {e}")

        result = await asyncio.to_thread(_maximize)
        logger.info(f"Maximized window: {window.get_text()}")
        return result

    async def minimize_window(self, window: DesktopElement) -> bool:
        """
        Minimize a window.

        Args:
            window: DesktopElement representing the window

        Returns:
            True if minimize was successful
        """
        logger.debug("Minimizing window")

        def _minimize() -> bool:
            with auto.UIAutomationInitializerInThread():
                try:
                    import win32con
                    import win32gui

                    hwnd = window._control.NativeWindowHandle
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    return True
                except Exception as e:
                    raise ValueError(f"Failed to minimize window: {e}")

        result = await asyncio.to_thread(_minimize)
        logger.info(f"Minimized window: {window.get_text()}")
        return result

    async def restore_window(self, window: DesktopElement) -> bool:
        """
        Restore a window to normal state (from maximized or minimized).

        Args:
            window: DesktopElement representing the window

        Returns:
            True if restore was successful
        """
        logger.debug("Restoring window")

        def _restore() -> bool:
            with auto.UIAutomationInitializerInThread():
                try:
                    import win32con
                    import win32gui

                    hwnd = window._control.NativeWindowHandle
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    return True
                except Exception as e:
                    raise ValueError(f"Failed to restore window: {e}")

        result = await asyncio.to_thread(_restore)
        logger.info(f"Restored window: {window.get_text()}")
        return result

    async def get_window_properties(self, window: DesktopElement) -> Dict[str, Any]:
        """
        Get comprehensive properties of a window.

        Args:
            window: DesktopElement representing the window

        Returns:
            Dictionary with window properties
        """
        logger.debug("Getting window properties")

        def _get_properties() -> Dict[str, Any]:
            with auto.UIAutomationInitializerInThread():
                try:
                    import win32con
                    import win32gui

                    hwnd = window._control.NativeWindowHandle
                    rect = window.get_bounding_rect()
                    placement = win32gui.GetWindowPlacement(hwnd)
                    show_state = placement[1]

                    state_map = {
                        win32con.SW_HIDE: "hidden",
                        win32con.SW_MINIMIZE: "minimized",
                        win32con.SW_MAXIMIZE: "maximized",
                        win32con.SW_RESTORE: "normal",
                        win32con.SW_SHOW: "normal",
                        win32con.SW_SHOWMINIMIZED: "minimized",
                        win32con.SW_SHOWMAXIMIZED: "maximized",
                        win32con.SW_SHOWNOACTIVATE: "normal",
                        win32con.SW_SHOWNORMAL: "normal",
                    }
                    window_state = state_map.get(show_state, "normal")
                    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

                    return {
                        "title": window.get_text(),
                        "process_id": window._control.ProcessId,
                        "handle": hwnd,
                        "automation_id": window.get_property("AutomationId"),
                        "class_name": window._control.ClassName,
                        "control_type": window._control.ControlTypeName,
                        "is_enabled": window.is_enabled(),
                        "is_visible": window.is_visible(),
                        "bounds": rect,
                        "x": rect["left"],
                        "y": rect["top"],
                        "width": rect["width"],
                        "height": rect["height"],
                        "state": window_state,
                        "is_maximized": bool(style & win32con.WS_MAXIMIZE),
                        "is_minimized": bool(style & win32con.WS_MINIMIZE),
                        "is_resizable": bool(style & win32con.WS_THICKFRAME),
                        "has_title_bar": bool(style & win32con.WS_CAPTION),
                    }
                except Exception as e:
                    logger.warning(f"Failed to get full window properties: {e}")
                    rect = window.get_bounding_rect()
                    return {
                        "title": window.get_text(),
                        "process_id": window.get_property("ProcessId"),
                        "is_enabled": window.is_enabled(),
                        "is_visible": window.is_visible(),
                        "bounds": rect,
                        "x": rect["left"],
                        "y": rect["top"],
                        "width": rect["width"],
                        "height": rect["height"],
                        "state": "unknown",
                    }

        properties = await asyncio.to_thread(_get_properties)
        logger.info(f"Got properties for window: {properties['title']}")
        return properties

    def cleanup(self) -> None:
        """Clean up resources and close applications launched by this manager.

        Applications launched with keep_open=True will NOT be terminated.
        """
        logger.info("Cleaning up WindowManager")

        for pid in self._launched_processes:
            # Skip processes marked to keep open
            if pid in self._keep_open_processes:
                logger.debug(f"Keeping process {pid} open (keep_open=True)")
                continue

            try:
                process = psutil.Process(pid)
                if process.is_running():
                    logger.debug(f"Terminating process {pid}")
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        process.kill()
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logger.warning(f"Error cleaning up process {pid}: {e}")

        self._launched_processes.clear()
        self._keep_open_processes.clear()

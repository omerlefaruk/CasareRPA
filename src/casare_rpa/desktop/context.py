"""
Desktop Context - Main entry point for desktop automation

Manages windows, applications, and provides high-level desktop automation API.
"""

import time
import subprocess
import psutil
from typing import Any, Dict, List, Optional, Union
from loguru import logger
import uiautomation as auto

from .element import DesktopElement


class DesktopContext:
    """
    Desktop automation context for managing Windows applications and UI elements.
    
    Provides methods to launch applications, find windows, and interact with desktop UI.
    """
    
    def __init__(self):
        """Initialize desktop automation context."""
        logger.debug("Initializing DesktopContext")
        self._launched_processes = []  # Track processes we launched for cleanup
    
    def find_window(self, title: str, exact: bool = False, timeout: float = 5.0) -> Optional[DesktopElement]:
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
        max_quick_checks = 30  # Check 30 times (3 seconds) before slowing down
        
        while time.time() - start_time < timeout:
            check_count += 1
            try:
                if exact:
                    window = auto.WindowControl(searchDepth=1, Name=title)
                else:
                    window = auto.WindowControl(searchDepth=1, SubName=title)
                
                if window.Exists(0, 0):
                    logger.info(f"Found window: '{window.Name}'")
                    return DesktopElement(window)
            except Exception as e:
                logger.debug(f"Window search attempt failed: {e}")
            
            # Quick checks for first 3 seconds, then slow down
            if check_count < max_quick_checks:
                time.sleep(0.1)  # Check every 100ms for first 3 seconds
            else:
                time.sleep(0.5)  # Then check every 500ms to avoid wasting CPU
        
        error_msg = f"Window not found: '{title}' (exact={exact})"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def get_all_windows(self, include_invisible: bool = False) -> List[DesktopElement]:
        """
        Get all top-level windows.
        
        Args:
            include_invisible: If True, include invisible/hidden windows
            
        Returns:
            List of DesktopElement objects representing windows
        """
        logger.debug(f"Getting all windows (include_invisible={include_invisible})")
        
        windows = []
        for window in auto.GetRootControl().GetChildren():
            if window.ControlTypeName == 'WindowControl':
                if include_invisible or window.IsEnabled:
                    windows.append(DesktopElement(window))
        
        logger.info(f"Found {len(windows)} windows")
        return windows
    
    def launch_application(
        self, 
        path: str, 
        args: str = "", 
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None
    ) -> DesktopElement:
        """
        Launch an application and return its main window.
        
        Args:
            path: Path to executable or command name
            args: Command line arguments
            working_dir: Working directory for the process
            timeout: Maximum time to wait for window to appear
            window_title: Expected window title (if None, uses process name)
            
        Returns:
            DesktopElement wrapping the application's main window
            
        Raises:
            RuntimeError: If application fails to launch or window not found
        """
        logger.info(f"Launching application: {path} {args}")
        
        try:
            # Build command
            command = f'"{path}"' if ' ' in path else path
            if args:
                command += f" {args}"
            
            # Launch process
            process = subprocess.Popen(
                command,
                cwd=working_dir,
                shell=True
            )
            
            self._launched_processes.append(process.pid)
            logger.debug(f"Process launched with PID: {process.pid}")
            
            # Wait a moment for window to initialize
            time.sleep(0.5)
            
            # Try to find the window
            if window_title is None:
                # Extract executable name from path
                import os
                exe_name = os.path.splitext(os.path.basename(path))[0]
                window_title = exe_name
            
            # Use a shorter timeout for window search (3 seconds should be enough)
            # Most apps show a window within 1-2 seconds
            window_search_timeout = min(timeout, 3.0)
            
            try:
                window = self.find_window(window_title, exact=False, timeout=window_search_timeout)
                logger.info(f"Application launched successfully: {window_title}")
                return window
            except ValueError:
                # If we can't find by title, try to find by process ID
                logger.warning(f"Could not find window by title '{window_title}' after {window_search_timeout}s, searching by process...")
                
                # No additional sleep - go straight to process-based search
                # time.sleep(1.0)  # Removed - unnecessary delay
                
                # Try to find any window from this process (with timeout)
                logger.debug(f"Searching for windows from PID {process.pid}...")
                search_start = time.time()
                max_search_time = 3.0  # Maximum 3 seconds for process-based search
                windows_checked = 0
                
                try:
                    for window in auto.GetRootControl().GetChildren():
                        # Check timeout
                        if time.time() - search_start > max_search_time:
                            logger.warning(f"Process-based window search timed out after checking {windows_checked} windows")
                            break
                        
                        windows_checked += 1
                        
                        # Only check window controls
                        if window.ControlTypeName == 'WindowControl' and window.IsEnabled:
                            try:
                                if window.ProcessId == process.pid:
                                    window_elem = DesktopElement(window)
                                    window_title_found = window_elem.get_text()
                                    logger.info(f"Found window by process ID: {window_title_found}")
                                    return window_elem
                            except Exception as e:
                                logger.debug(f"Error checking window: {e}")
                                continue
                    
                    logger.error(f"No window found for PID {process.pid} after checking {windows_checked} windows")
                except Exception as e:
                    logger.error(f"Error during process-based window search: {e}")
                
                raise RuntimeError(f"Failed to find window for application: {path}")
                
        except Exception as e:
            error_msg = f"Failed to launch application '{path}': {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def close_application(
        self, 
        window_or_pid: Union[DesktopElement, int, str],
        force: bool = False,
        timeout: float = 5.0
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
            # Get window element
            if isinstance(window_or_pid, DesktopElement):
                window = window_or_pid
            elif isinstance(window_or_pid, int):
                # Find window by process ID
                for w in self.get_all_windows():
                    try:
                        if w._control.ProcessId == window_or_pid:
                            window = w
                            break
                    except:
                        pass
                else:
                    raise ValueError(f"No window found for PID: {window_or_pid}")
            else:
                # Find window by title
                window = self.find_window(window_or_pid)
            
            # Get process ID
            pid = window._control.ProcessId
            
            if force:
                # Force kill
                logger.info(f"Force killing process {pid}")
                try:
                    process = psutil.Process(pid)
                    process.kill()
                    process.wait(timeout=timeout)
                except psutil.NoSuchProcess:
                    pass  # Already dead
                return True
            else:
                # Try graceful close
                logger.info(f"Attempting graceful close of window: {window.get_text()}")
                
                # Try to close window using WindowPattern
                try:
                    window._control.GetWindowPattern().Close()
                except:
                    # Fallback: send Alt+F4
                    logger.debug("WindowPattern.Close() failed, trying Alt+F4")
                    window._control.SetFocus()
                    window._control.SendKeys('{Alt}F4')
                
                # Wait for window to close
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if not window._control.Exists(0, 0):
                        logger.info("Application closed successfully")
                        return True
                    time.sleep(0.1)
                
                # Timeout - force kill
                logger.warning(f"Graceful close timed out, force killing PID {pid}")
                try:
                    process = psutil.Process(pid)
                    process.kill()
                except psutil.NoSuchProcess:
                    pass
                
                return True
                
        except Exception as e:
            error_msg = f"Failed to close application: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def cleanup(self):
        """
        Clean up resources and close applications launched by this context.
        """
        logger.info("Cleaning up DesktopContext")
        
        for pid in self._launched_processes:
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
                pass  # Already terminated
            except Exception as e:
                logger.warning(f"Error cleaning up process {pid}: {e}")
        
        self._launched_processes.clear()
    
    def resize_window(
        self,
        window: DesktopElement,
        width: int,
        height: int
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

        try:
            import win32gui
            import win32con

            hwnd = window._control.NativeWindowHandle

            # Get current position to preserve it
            rect = window.get_bounding_rect()
            current_x = rect['left']
            current_y = rect['top']

            # Resize window
            win32gui.MoveWindow(hwnd, current_x, current_y, width, height, True)

            logger.info(f"Resized window to {width}x{height}")
            return True

        except Exception as e:
            error_msg = f"Failed to resize window: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def move_window(
        self,
        window: DesktopElement,
        x: int,
        y: int
    ) -> bool:
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

        try:
            import win32gui

            hwnd = window._control.NativeWindowHandle

            # Get current size to preserve it
            rect = window.get_bounding_rect()
            current_width = rect['width']
            current_height = rect['height']

            # Move window
            win32gui.MoveWindow(hwnd, x, y, current_width, current_height, True)

            logger.info(f"Moved window to ({x}, {y})")
            return True

        except Exception as e:
            error_msg = f"Failed to move window: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def maximize_window(self, window: DesktopElement) -> bool:
        """
        Maximize a window.

        Args:
            window: DesktopElement representing the window

        Returns:
            True if maximize was successful
        """
        logger.debug("Maximizing window")

        try:
            import win32gui
            import win32con

            hwnd = window._control.NativeWindowHandle
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

            logger.info(f"Maximized window: {window.get_text()}")
            return True

        except Exception as e:
            error_msg = f"Failed to maximize window: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def minimize_window(self, window: DesktopElement) -> bool:
        """
        Minimize a window.

        Args:
            window: DesktopElement representing the window

        Returns:
            True if minimize was successful
        """
        logger.debug("Minimizing window")

        try:
            import win32gui
            import win32con

            hwnd = window._control.NativeWindowHandle
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

            logger.info(f"Minimized window: {window.get_text()}")
            return True

        except Exception as e:
            error_msg = f"Failed to minimize window: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def restore_window(self, window: DesktopElement) -> bool:
        """
        Restore a window to normal state (from maximized or minimized).

        Args:
            window: DesktopElement representing the window

        Returns:
            True if restore was successful
        """
        logger.debug("Restoring window")

        try:
            import win32gui
            import win32con

            hwnd = window._control.NativeWindowHandle
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            logger.info(f"Restored window: {window.get_text()}")
            return True

        except Exception as e:
            error_msg = f"Failed to restore window: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def get_window_properties(self, window: DesktopElement) -> Dict[str, Any]:
        """
        Get comprehensive properties of a window.

        Args:
            window: DesktopElement representing the window

        Returns:
            Dictionary with window properties
        """
        logger.debug("Getting window properties")

        try:
            import win32gui
            import win32con

            hwnd = window._control.NativeWindowHandle

            # Get window rect
            rect = window.get_bounding_rect()

            # Get window state
            placement = win32gui.GetWindowPlacement(hwnd)
            show_state = placement[1]

            state_map = {
                win32con.SW_HIDE: 'hidden',
                win32con.SW_MINIMIZE: 'minimized',
                win32con.SW_MAXIMIZE: 'maximized',
                win32con.SW_RESTORE: 'normal',
                win32con.SW_SHOW: 'normal',
                win32con.SW_SHOWMINIMIZED: 'minimized',
                win32con.SW_SHOWMAXIMIZED: 'maximized',
                win32con.SW_SHOWNOACTIVATE: 'normal',
                win32con.SW_SHOWNORMAL: 'normal',
            }
            window_state = state_map.get(show_state, 'normal')

            # Get window style
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

            properties = {
                'title': window.get_text(),
                'process_id': window._control.ProcessId,
                'handle': hwnd,
                'automation_id': window.get_property('AutomationId'),
                'class_name': window._control.ClassName,
                'control_type': window._control.ControlTypeName,
                'is_enabled': window.is_enabled(),
                'is_visible': window.is_visible(),
                'bounds': rect,
                'x': rect['left'],
                'y': rect['top'],
                'width': rect['width'],
                'height': rect['height'],
                'state': window_state,
                'is_maximized': bool(style & win32con.WS_MAXIMIZE),
                'is_minimized': bool(style & win32con.WS_MINIMIZE),
                'is_resizable': bool(style & win32con.WS_THICKFRAME),
                'has_title_bar': bool(style & win32con.WS_CAPTION),
            }

            logger.info(f"Got properties for window: {properties['title']}")
            return properties

        except Exception as e:
            error_msg = f"Failed to get window properties: {e}"
            logger.error(error_msg)
            # Return basic properties if win32 fails
            rect = window.get_bounding_rect()
            return {
                'title': window.get_text(),
                'process_id': window.get_property('ProcessId'),
                'is_enabled': window.is_enabled(),
                'is_visible': window.is_visible(),
                'bounds': rect,
                'x': rect['left'],
                'y': rect['top'],
                'width': rect['width'],
                'height': rect['height'],
                'state': 'unknown',
            }

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False

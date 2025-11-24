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

    # =========================================================================
    # Advanced Interaction Methods (Bite 6)
    # =========================================================================

    def select_from_dropdown(
        self,
        element: DesktopElement,
        value: str,
        by_text: bool = True
    ) -> bool:
        """
        Select an item from a dropdown/combobox.

        Args:
            element: DesktopElement representing the dropdown/combobox
            value: Value to select (text or index)
            by_text: If True, match by text; if False, treat value as index

        Returns:
            True if selection was successful

        Raises:
            ValueError: If item not found or selection fails
        """
        logger.debug(f"Selecting '{value}' from dropdown (by_text={by_text})")

        try:
            control = element._control

            # Try ExpandCollapsePattern to open dropdown first
            try:
                expand_pattern = control.GetExpandCollapsePattern()
                if expand_pattern:
                    expand_state = expand_pattern.ExpandCollapseState
                    if expand_state == auto.ExpandCollapseState.Collapsed:
                        expand_pattern.Expand()
                        time.sleep(0.2)  # Wait for dropdown to open
            except Exception as e:
                logger.debug(f"Could not expand dropdown: {e}")

            # Try SelectionPattern (for ComboBox controls)
            try:
                selection_pattern = control.GetSelectionPattern()
                if selection_pattern:
                    # Find the item in the dropdown list
                    items = control.GetChildren()
                    for item in items:
                        if item.ControlTypeName == 'ListItemControl':
                            if by_text:
                                if item.Name == value or value.lower() in item.Name.lower():
                                    # Select this item
                                    try:
                                        sel_item_pattern = item.GetSelectionItemPattern()
                                        if sel_item_pattern:
                                            sel_item_pattern.Select()
                                            logger.info(f"Selected '{item.Name}' from dropdown")
                                            return True
                                    except:
                                        # Fallback: click the item
                                        item.Click()
                                        logger.info(f"Clicked '{item.Name}' in dropdown")
                                        return True
            except Exception as e:
                logger.debug(f"SelectionPattern failed: {e}")

            # Try ValuePattern (for editable comboboxes)
            try:
                value_pattern = control.GetValuePattern()
                if value_pattern and not value_pattern.IsReadOnly:
                    value_pattern.SetValue(value)
                    logger.info(f"Set dropdown value using ValuePattern: '{value}'")
                    return True
            except Exception as e:
                logger.debug(f"ValuePattern failed: {e}")

            # Fallback: click to open and search for item
            control.Click()
            time.sleep(0.3)  # Wait for dropdown to open

            # Search in list items
            list_control = None
            for child in auto.GetRootControl().GetChildren():
                if child.ControlTypeName in ['ListControl', 'MenuControl', 'PopupControl']:
                    if child.BoundingRectangle.width() > 0:
                        list_control = child
                        break

            if list_control:
                for item in list_control.GetChildren():
                    item_text = item.Name or ""
                    if by_text and (item_text == value or value.lower() in item_text.lower()):
                        item.Click()
                        logger.info(f"Selected '{item_text}' from dropdown list")
                        return True
                    elif not by_text:
                        try:
                            idx = int(value)
                            items = list(list_control.GetChildren())
                            if 0 <= idx < len(items):
                                items[idx].Click()
                                logger.info(f"Selected item at index {idx}")
                                return True
                        except ValueError:
                            pass

            raise ValueError(f"Could not find item '{value}' in dropdown")

        except Exception as e:
            error_msg = f"Failed to select from dropdown: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def check_checkbox(
        self,
        element: DesktopElement,
        check: bool = True
    ) -> bool:
        """
        Check or uncheck a checkbox.

        Args:
            element: DesktopElement representing the checkbox
            check: True to check, False to uncheck

        Returns:
            True if operation was successful

        Raises:
            ValueError: If checkbox cannot be toggled
        """
        logger.debug(f"Setting checkbox to {'checked' if check else 'unchecked'}")

        try:
            control = element._control

            # Try TogglePattern
            try:
                toggle_pattern = control.GetTogglePattern()
                if toggle_pattern:
                    current_state = toggle_pattern.ToggleState
                    # ToggleState: 0=Off, 1=On, 2=Indeterminate
                    is_checked = current_state == auto.ToggleState.On

                    if check and not is_checked:
                        toggle_pattern.Toggle()
                        # If it went to Indeterminate, toggle again to get to On
                        if toggle_pattern.ToggleState == auto.ToggleState.Indeterminate:
                            toggle_pattern.Toggle()
                        logger.info("Checkbox checked")
                    elif not check and is_checked:
                        toggle_pattern.Toggle()
                        logger.info("Checkbox unchecked")
                    else:
                        logger.info(f"Checkbox already {'checked' if check else 'unchecked'}")

                    return True
            except Exception as e:
                logger.debug(f"TogglePattern failed: {e}")

            # Fallback: click the checkbox
            current_text = element.get_text().lower()
            is_checked = "checked" in current_text or "true" in current_text

            if (check and not is_checked) or (not check and is_checked):
                element.click()
                logger.info(f"Clicked checkbox to {'check' if check else 'uncheck'}")

            return True

        except Exception as e:
            error_msg = f"Failed to toggle checkbox: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def select_radio_button(
        self,
        element: DesktopElement
    ) -> bool:
        """
        Select a radio button.

        Args:
            element: DesktopElement representing the radio button

        Returns:
            True if selection was successful

        Raises:
            ValueError: If radio button cannot be selected
        """
        logger.debug("Selecting radio button")

        try:
            control = element._control

            # Try SelectionItemPattern
            try:
                sel_item_pattern = control.GetSelectionItemPattern()
                if sel_item_pattern:
                    sel_item_pattern.Select()
                    logger.info(f"Selected radio button: {control.Name}")
                    return True
            except Exception as e:
                logger.debug(f"SelectionItemPattern failed: {e}")

            # Fallback: click the radio button
            element.click()
            logger.info(f"Clicked radio button: {control.Name}")
            return True

        except Exception as e:
            error_msg = f"Failed to select radio button: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def select_tab(
        self,
        tab_control: DesktopElement,
        tab_name: str = None,
        tab_index: int = None
    ) -> bool:
        """
        Select a tab in a tab control.

        Args:
            tab_control: DesktopElement representing the tab control
            tab_name: Name of tab to select (partial match supported)
            tab_index: Index of tab to select (0-based)

        Returns:
            True if selection was successful

        Raises:
            ValueError: If tab not found or cannot be selected
        """
        if tab_name is None and tab_index is None:
            raise ValueError("Must provide either tab_name or tab_index")

        logger.debug(f"Selecting tab: name='{tab_name}', index={tab_index}")

        try:
            control = tab_control._control

            # Get tab items
            tab_items = []
            for child in control.GetChildren():
                if child.ControlTypeName == 'TabItemControl':
                    tab_items.append(child)

            if not tab_items:
                # Try deeper search
                for child in control.GetChildren():
                    for subchild in child.GetChildren():
                        if subchild.ControlTypeName == 'TabItemControl':
                            tab_items.append(subchild)

            logger.debug(f"Found {len(tab_items)} tab items")

            target_tab = None

            if tab_index is not None:
                if 0 <= tab_index < len(tab_items):
                    target_tab = tab_items[tab_index]
                else:
                    raise ValueError(f"Tab index {tab_index} out of range (0-{len(tab_items)-1})")

            elif tab_name is not None:
                for tab in tab_items:
                    if tab.Name == tab_name or tab_name.lower() in tab.Name.lower():
                        target_tab = tab
                        break

                if not target_tab:
                    tab_names = [t.Name for t in tab_items]
                    raise ValueError(f"Tab '{tab_name}' not found. Available tabs: {tab_names}")

            # Select the tab
            try:
                sel_item_pattern = target_tab.GetSelectionItemPattern()
                if sel_item_pattern:
                    sel_item_pattern.Select()
                    logger.info(f"Selected tab: {target_tab.Name}")
                    return True
            except Exception as e:
                logger.debug(f"SelectionItemPattern failed: {e}")

            # Fallback: click the tab
            target_tab.Click()
            logger.info(f"Clicked tab: {target_tab.Name}")
            return True

        except Exception as e:
            error_msg = f"Failed to select tab: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def expand_tree_item(
        self,
        element: DesktopElement,
        expand: bool = True
    ) -> bool:
        """
        Expand or collapse a tree item.

        Args:
            element: DesktopElement representing the tree item
            expand: True to expand, False to collapse

        Returns:
            True if operation was successful

        Raises:
            ValueError: If tree item cannot be expanded/collapsed
        """
        action = "expand" if expand else "collapse"
        logger.debug(f"Attempting to {action} tree item")

        try:
            control = element._control

            # Try ExpandCollapsePattern
            try:
                expand_pattern = control.GetExpandCollapsePattern()
                if expand_pattern:
                    current_state = expand_pattern.ExpandCollapseState

                    if expand and current_state == auto.ExpandCollapseState.Collapsed:
                        expand_pattern.Expand()
                        logger.info(f"Expanded tree item: {control.Name}")
                    elif not expand and current_state == auto.ExpandCollapseState.Expanded:
                        expand_pattern.Collapse()
                        logger.info(f"Collapsed tree item: {control.Name}")
                    else:
                        state_name = "expanded" if current_state == auto.ExpandCollapseState.Expanded else "collapsed"
                        logger.info(f"Tree item already {state_name}")

                    return True
            except Exception as e:
                logger.debug(f"ExpandCollapsePattern failed: {e}")

            # Fallback: double-click the tree item
            rect = control.BoundingRectangle
            center_x = rect.left + rect.width() // 2
            center_y = rect.top + rect.height() // 2
            control.DoubleClick(x=center_x, y=center_y)
            logger.info(f"Double-clicked tree item to {action}: {control.Name}")
            return True

        except Exception as e:
            error_msg = f"Failed to {action} tree item: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def scroll_element(
        self,
        element: DesktopElement,
        direction: str = "down",
        amount: float = 0.5
    ) -> bool:
        """
        Scroll an element (scrollbar, list, window, etc.).

        Args:
            element: DesktopElement to scroll
            direction: Scroll direction - "up", "down", "left", "right"
            amount: Scroll amount as percentage (0.0 to 1.0) or "page" for page scroll

        Returns:
            True if scroll was successful

        Raises:
            ValueError: If element cannot be scrolled
        """
        logger.debug(f"Scrolling element {direction} by {amount}")

        valid_directions = ["up", "down", "left", "right"]
        if direction.lower() not in valid_directions:
            raise ValueError(f"Invalid direction '{direction}'. Must be one of: {valid_directions}")

        direction = direction.lower()

        try:
            control = element._control

            # Try ScrollPattern
            try:
                scroll_pattern = control.GetScrollPattern()
                if scroll_pattern:
                    # Get current scroll position
                    h_scroll = scroll_pattern.HorizontalScrollPercent
                    v_scroll = scroll_pattern.VerticalScrollPercent

                    # Calculate scroll amount
                    if isinstance(amount, str) and amount.lower() == "page":
                        scroll_amount = 100  # Full page
                    else:
                        scroll_amount = float(amount) * 100  # Convert to percentage

                    if direction == "down":
                        new_v = min(100, v_scroll + scroll_amount)
                        scroll_pattern.SetScrollPercent(h_scroll, new_v)
                    elif direction == "up":
                        new_v = max(0, v_scroll - scroll_amount)
                        scroll_pattern.SetScrollPercent(h_scroll, new_v)
                    elif direction == "right":
                        new_h = min(100, h_scroll + scroll_amount)
                        scroll_pattern.SetScrollPercent(new_h, v_scroll)
                    elif direction == "left":
                        new_h = max(0, h_scroll - scroll_amount)
                        scroll_pattern.SetScrollPercent(new_h, v_scroll)

                    logger.info(f"Scrolled {direction} by {scroll_amount}%")
                    return True
            except Exception as e:
                logger.debug(f"ScrollPattern failed: {e}")

            # Fallback: use mouse wheel or keyboard
            control.SetFocus()
            time.sleep(0.1)

            if direction in ["up", "down"]:
                # Use mouse wheel
                rect = control.BoundingRectangle
                center_x = rect.left + rect.width() // 2
                center_y = rect.top + rect.height() // 2

                # Calculate wheel delta
                wheel_delta = 3 if isinstance(amount, str) else max(1, int(amount * 5))

                if direction == "down":
                    auto.WheelDown(center_x, center_y, wheelTimes=wheel_delta)
                else:
                    auto.WheelUp(center_x, center_y, wheelTimes=wheel_delta)

                logger.info(f"Scrolled {direction} using mouse wheel")
                return True
            else:
                # Use keyboard for horizontal scroll
                key = '{Right}' if direction == "right" else '{Left}'
                times = 5 if isinstance(amount, str) else max(1, int(amount * 10))
                for _ in range(times):
                    control.SendKeys(key)

                logger.info(f"Scrolled {direction} using keyboard")
                return True

        except Exception as e:
            error_msg = f"Failed to scroll element: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    # =========================================================================
    # Mouse & Keyboard Control Methods (Bite 7)
    # =========================================================================

    def move_mouse(
        self,
        x: int,
        y: int,
        duration: float = 0.0
    ) -> bool:
        """
        Move mouse cursor to specified position.

        Args:
            x: Target X coordinate
            y: Target Y coordinate
            duration: Time in seconds to move (0 for instant)

        Returns:
            True if successful

        Raises:
            ValueError: If move fails
        """
        logger.debug(f"Moving mouse to ({x}, {y}) over {duration}s")

        try:
            if duration > 0:
                # Animated move
                import ctypes
                start_x, start_y = self.get_mouse_position()
                steps = max(10, int(duration * 60))  # ~60 fps

                for i in range(steps + 1):
                    progress = i / steps
                    # Ease-out quadratic
                    ease = 1 - (1 - progress) ** 2
                    current_x = int(start_x + (x - start_x) * ease)
                    current_y = int(start_y + (y - start_y) * ease)
                    ctypes.windll.user32.SetCursorPos(current_x, current_y)
                    time.sleep(duration / steps)
            else:
                # Instant move
                import ctypes
                ctypes.windll.user32.SetCursorPos(x, y)

            logger.info(f"Moved mouse to ({x}, {y})")
            return True

        except Exception as e:
            error_msg = f"Failed to move mouse: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def click_mouse(
        self,
        x: int = None,
        y: int = None,
        button: str = "left",
        click_type: str = "single"
    ) -> bool:
        """
        Click mouse at specified position or current position.

        Args:
            x: X coordinate (None for current position)
            y: Y coordinate (None for current position)
            button: Mouse button - "left", "right", "middle"
            click_type: Click type - "single", "double", "triple"

        Returns:
            True if successful

        Raises:
            ValueError: If click fails
        """
        logger.debug(f"Clicking {button} {click_type} at ({x}, {y})")

        valid_buttons = ["left", "right", "middle"]
        if button.lower() not in valid_buttons:
            raise ValueError(f"Invalid button '{button}'. Must be one of: {valid_buttons}")

        valid_types = ["single", "double", "triple"]
        if click_type.lower() not in valid_types:
            raise ValueError(f"Invalid click_type '{click_type}'. Must be one of: {valid_types}")

        button = button.lower()
        click_type = click_type.lower()

        try:
            # Move to position if specified
            if x is not None and y is not None:
                self.move_mouse(x, y)
            else:
                x, y = self.get_mouse_position()

            # Determine click count
            clicks = {"single": 1, "double": 2, "triple": 3}[click_type]

            # Use uiautomation for clicking
            for _ in range(clicks):
                if button == "left":
                    auto.Click(x, y)
                elif button == "right":
                    auto.RightClick(x, y)
                elif button == "middle":
                    auto.MiddleClick(x, y)
                if clicks > 1:
                    time.sleep(0.05)  # Small delay between clicks

            logger.info(f"Clicked {button} {click_type} at ({x}, {y})")
            return True

        except Exception as e:
            error_msg = f"Failed to click mouse: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def get_mouse_position(self) -> tuple:
        """
        Get current mouse cursor position.

        Returns:
            Tuple of (x, y) coordinates
        """
        try:
            import ctypes

            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            point = POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(point))

            logger.debug(f"Mouse position: ({point.x}, {point.y})")
            return (point.x, point.y)

        except Exception as e:
            error_msg = f"Failed to get mouse position: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def send_keys(
        self,
        keys: str,
        interval: float = 0.0
    ) -> bool:
        """
        Send keyboard input.

        Args:
            keys: Keys to send. Supports special keys in braces:
                  {Enter}, {Tab}, {Escape}, {Backspace}, {Delete},
                  {Up}, {Down}, {Left}, {Right}, {Home}, {End},
                  {PageUp}, {PageDown}, {F1}-{F12}, {Ctrl}, {Alt}, {Shift}
            interval: Delay between keys in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If send fails
        """
        logger.debug(f"Sending keys: '{keys[:50]}...' (interval={interval}s)")

        try:
            # Use uiautomation's SendKeys
            auto.SendKeys(keys, interval=interval)

            logger.info(f"Sent keys: '{keys[:50]}...'")
            return True

        except Exception as e:
            error_msg = f"Failed to send keys: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def send_hotkey(
        self,
        *keys: str
    ) -> bool:
        """
        Send a hotkey combination (e.g., Ctrl+C, Alt+Tab).

        Args:
            *keys: Keys in the combination (e.g., "ctrl", "c")
                   Supported modifiers: ctrl, alt, shift, win

        Returns:
            True if successful

        Raises:
            ValueError: If send fails
        """
        logger.debug(f"Sending hotkey: {'+'.join(keys)}")

        try:
            # Build the hotkey string for uiautomation
            # Format: {Ctrl}{Alt}{Shift}key
            modifiers = {
                "ctrl": "{Ctrl}",
                "control": "{Ctrl}",
                "alt": "{Alt}",
                "shift": "{Shift}",
                "win": "{Win}",
                "windows": "{Win}"
            }

            hotkey_str = ""
            regular_keys = []

            for key in keys:
                key_lower = key.lower()
                if key_lower in modifiers:
                    hotkey_str += modifiers[key_lower]
                else:
                    regular_keys.append(key)

            # Add regular keys
            for key in regular_keys:
                if len(key) == 1:
                    hotkey_str += key
                else:
                    # Special key like Enter, Tab, etc.
                    hotkey_str += "{" + key.capitalize() + "}"

            # Send the hotkey
            auto.SendKeys(hotkey_str, interval=0)

            logger.info(f"Sent hotkey: {'+'.join(keys)}")
            return True

        except Exception as e:
            error_msg = f"Failed to send hotkey: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def drag_mouse(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        duration: float = 0.5
    ) -> bool:
        """
        Drag mouse from one position to another.

        Args:
            start_x: Starting X coordinate
            start_y: Starting Y coordinate
            end_x: Ending X coordinate
            end_y: Ending Y coordinate
            button: Mouse button to hold - "left", "right"
            duration: Time for drag operation in seconds

        Returns:
            True if successful

        Raises:
            ValueError: If drag fails
        """
        logger.debug(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")

        valid_buttons = ["left", "right"]
        if button.lower() not in valid_buttons:
            raise ValueError(f"Invalid button '{button}'. Must be one of: {valid_buttons}")

        button = button.lower()

        try:
            # Move to start position
            self.move_mouse(start_x, start_y)
            time.sleep(0.1)

            # Use win32api for drag operation
            import ctypes
            from ctypes import wintypes

            # Mouse event constants
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            MOUSEEVENTF_ABSOLUTE = 0x8000
            MOUSEEVENTF_MOVE = 0x0001

            if button == "left":
                down_flag = MOUSEEVENTF_LEFTDOWN
                up_flag = MOUSEEVENTF_LEFTUP
            else:
                down_flag = MOUSEEVENTF_RIGHTDOWN
                up_flag = MOUSEEVENTF_RIGHTUP

            # Press button down
            ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
            time.sleep(0.05)

            # Move to end position with animation
            self.move_mouse(end_x, end_y, duration=duration)
            time.sleep(0.05)

            # Release button
            ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)

            logger.info(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            return True

        except Exception as e:
            error_msg = f"Failed to drag mouse: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    # =========================================================================
    # Wait & Verification Methods (Bite 8)
    # =========================================================================

    def wait_for_element(
        self,
        selector: dict,
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
        parent: auto.Control = None
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
        last_element = None

        while time.time() - start_time < timeout:
            try:
                element = self.find_element(selector, timeout=0.1, parent=parent)
                last_element = element

                if state == "visible":
                    # Element found and should be visible
                    if element and element.exists():
                        logger.info(f"Element is visible")
                        return element
                elif state == "hidden":
                    # Element should not exist or not be visible
                    if not element or not element.exists():
                        logger.info(f"Element is hidden/not found")
                        return None
                elif state == "enabled":
                    # Element should be enabled
                    if element and element._control.IsEnabled:
                        logger.info(f"Element is enabled")
                        return element
                elif state == "disabled":
                    # Element should be disabled
                    if element and not element._control.IsEnabled:
                        logger.info(f"Element is disabled")
                        return element

            except Exception:
                # Element not found
                if state == "hidden":
                    logger.info(f"Element is hidden (not found)")
                    return None

            time.sleep(poll_interval)

        # Timeout reached
        elapsed = time.time() - start_time
        raise TimeoutError(
            f"Element did not become '{state}' within {timeout} seconds (elapsed: {elapsed:.1f}s)"
        )

    def wait_for_window(
        self,
        title: str = None,
        title_regex: str = None,
        class_name: str = None,
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5
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

        import re
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Get all windows
            windows = auto.GetRootControl().GetChildren()
            window_found = None

            for win in windows:
                try:
                    win_title = win.Name or ""

                    # Check title match
                    if title and title.lower() in win_title.lower():
                        window_found = win
                        break
                    elif title_regex and re.search(title_regex, win_title):
                        window_found = win
                        break
                    elif class_name and win.ClassName == class_name:
                        window_found = win
                        break
                except Exception:
                    continue

            if state == "visible":
                if window_found:
                    logger.info(f"Window found: '{window_found.Name}'")
                    return window_found
            elif state == "hidden":
                if not window_found:
                    logger.info(f"Window is hidden/closed")
                    return None

            time.sleep(poll_interval)

        # Timeout reached
        elapsed = time.time() - start_time
        search_desc = title or title_regex or class_name
        raise TimeoutError(
            f"Window '{search_desc}' did not become '{state}' within {timeout} seconds"
        )

    def element_exists(
        self,
        selector: dict,
        timeout: float = 0.0,
        parent: auto.Control = None
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

        try:
            element = self.find_element(selector, timeout=max(0.1, timeout), parent=parent)
            exists = element is not None and element.exists()
            logger.debug(f"Element exists: {exists}")
            return exists
        except Exception:
            logger.debug(f"Element does not exist")
            return False

    def verify_element_property(
        self,
        element: DesktopElement,
        property_name: str,
        expected_value: any,
        comparison: str = "equals"
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
            "equals", "contains", "startswith", "endswith",
            "regex", "greater", "less", "not_equals"
        ]
        if comparison.lower() not in valid_comparisons:
            raise ValueError(f"Invalid comparison '{comparison}'. Must be one of: {valid_comparisons}")

        comparison = comparison.lower()
        logger.debug(f"Verifying element property '{property_name}' {comparison} '{expected_value}'")

        try:
            control = element._control

            # Get the property value
            actual_value = getattr(control, property_name, None)

            # If property doesn't exist, try common patterns
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

            # Perform comparison
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
                import re
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
                f"Property verification: '{property_name}' {comparison} '{expected_value}' -> "
                f"actual='{actual_value}', result={result}"
            )
            return result

        except Exception as e:
            logger.error(f"Property verification failed: {e}")
            return False

    # ============================================================
    # Bite 9: Screenshot & OCR Methods
    # ============================================================

    def capture_screenshot(
        self,
        file_path: str = None,
        region: dict = None,
        format: str = "PNG"
    ) -> Optional[any]:
        """
        Capture a screenshot of the screen or a specific region.

        Args:
            file_path: Path to save the screenshot (optional)
            region: Dict with x, y, width, height for specific region (optional)
            format: Image format (PNG, JPEG, BMP)

        Returns:
            PIL Image object if successful, None otherwise
        """
        try:
            from PIL import ImageGrab, Image

            if region:
                # Capture specific region
                x = region.get("x", 0)
                y = region.get("y", 0)
                width = region.get("width", 100)
                height = region.get("height", 100)
                bbox = (x, y, x + width, y + height)
                screenshot = ImageGrab.grab(bbox=bbox)
                logger.info(f"Captured screenshot region: {bbox}")
            else:
                # Capture full screen
                screenshot = ImageGrab.grab()
                logger.info("Captured full screen screenshot")

            # Save to file if path provided
            if file_path:
                screenshot.save(file_path, format=format)
                logger.info(f"Screenshot saved to: {file_path}")

            return screenshot

        except ImportError:
            logger.error("PIL/Pillow not installed. Run: pip install Pillow")
            return None
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None

    def capture_element_image(
        self,
        element: DesktopElement,
        file_path: str = None,
        padding: int = 0,
        format: str = "PNG"
    ) -> Optional[any]:
        """
        Capture an image of a specific desktop element.

        Args:
            element: DesktopElement to capture
            file_path: Path to save the image (optional)
            padding: Extra pixels around element bounds
            format: Image format (PNG, JPEG, BMP)

        Returns:
            PIL Image object if successful, None otherwise
        """
        try:
            from PIL import ImageGrab

            # Get element bounding rectangle
            control = element._control
            rect = control.BoundingRectangle

            if not rect:
                logger.error("Could not get element bounding rectangle")
                return None

            # Calculate capture region with padding
            x = max(0, rect.left - padding)
            y = max(0, rect.top - padding)
            right = rect.right + padding
            bottom = rect.bottom + padding
            bbox = (x, y, right, bottom)

            # Capture the region
            screenshot = ImageGrab.grab(bbox=bbox)
            logger.info(f"Captured element image: {bbox}")

            # Save to file if path provided
            if file_path:
                screenshot.save(file_path, format=format)
                logger.info(f"Element image saved to: {file_path}")

            return screenshot

        except ImportError:
            logger.error("PIL/Pillow not installed. Run: pip install Pillow")
            return None
        except Exception as e:
            logger.error(f"Element image capture failed: {e}")
            return None

    def ocr_extract_text(
        self,
        image: any = None,
        image_path: str = None,
        region: dict = None,
        language: str = "eng",
        config: str = ""
    ) -> Optional[str]:
        """
        Extract text from an image using OCR.

        Args:
            image: PIL Image object (optional)
            image_path: Path to image file (optional)
            region: Dict with x, y, width, height to extract from specific region
            language: Tesseract language code (default: eng)
            config: Additional Tesseract config options

        Returns:
            Extracted text string if successful, None otherwise
        """
        try:
            from PIL import Image

            # Load image from path if needed
            if image is None and image_path:
                image = Image.open(image_path)
            elif image is None:
                # Capture screen if no image provided
                image = self.capture_screenshot(region=region)

            if image is None:
                logger.error("No image provided for OCR")
                return None

            # Crop to region if specified and image wasn't already captured with region
            if region and image_path:
                x = region.get("x", 0)
                y = region.get("y", 0)
                width = region.get("width", image.width)
                height = region.get("height", image.height)
                image = image.crop((x, y, x + width, y + height))

            # Try using pytesseract for OCR
            try:
                import pytesseract
                text = pytesseract.image_to_string(image, lang=language, config=config)
                text = text.strip()
                logger.info(f"OCR extracted {len(text)} characters")
                return text
            except ImportError:
                logger.warning("pytesseract not installed, trying Windows OCR")

            # Fallback: Try Windows built-in OCR (requires windows-ocr package)
            try:
                import winocr
                import asyncio

                async def do_ocr():
                    result = await winocr.recognize_pil(image, lang=language)
                    return result.text

                loop = asyncio.get_event_loop()
                text = loop.run_until_complete(do_ocr())
                logger.info(f"Windows OCR extracted {len(text)} characters")
                return text.strip()
            except ImportError:
                logger.error("No OCR engine available. Install pytesseract or winocr")
                return None

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return None

    def compare_images(
        self,
        image1: any = None,
        image2: any = None,
        image1_path: str = None,
        image2_path: str = None,
        method: str = "ssim",
        threshold: float = 0.9
    ) -> dict:
        """
        Compare two images and return similarity metrics.

        Args:
            image1: First PIL Image object
            image2: Second PIL Image object
            image1_path: Path to first image file
            image2_path: Path to second image file
            method: Comparison method ('ssim', 'histogram', 'pixel')
            threshold: Similarity threshold for match (0.0 to 1.0)

        Returns:
            Dict with similarity score, is_match, and method used
        """
        try:
            from PIL import Image
            import numpy as np

            # Load images from paths if needed
            if image1 is None and image1_path:
                image1 = Image.open(image1_path)
            if image2 is None and image2_path:
                image2 = Image.open(image2_path)

            if image1 is None or image2 is None:
                logger.error("Both images required for comparison")
                return {"similarity": 0.0, "is_match": False, "method": method, "error": "Missing images"}

            # Resize images to same size for comparison
            if image1.size != image2.size:
                image2 = image2.resize(image1.size, Image.LANCZOS)

            # Convert to same mode
            if image1.mode != image2.mode:
                image2 = image2.convert(image1.mode)

            # Convert to numpy arrays
            arr1 = np.array(image1)
            arr2 = np.array(image2)

            similarity = 0.0

            if method == "ssim":
                # Structural Similarity Index
                try:
                    from skimage.metrics import structural_similarity as ssim
                    # Convert to grayscale for SSIM
                    if len(arr1.shape) == 3:
                        gray1 = np.mean(arr1, axis=2)
                        gray2 = np.mean(arr2, axis=2)
                    else:
                        gray1, gray2 = arr1, arr2
                    similarity = ssim(gray1, gray2, data_range=255)
                except ImportError:
                    # Fallback to histogram if skimage not available
                    method = "histogram"
                    logger.warning("skimage not available, using histogram method")

            if method == "histogram":
                # Histogram comparison
                hist1 = image1.histogram()
                hist2 = image2.histogram()
                # Normalized correlation
                h1 = np.array(hist1, dtype=np.float64)
                h2 = np.array(hist2, dtype=np.float64)
                h1 = h1 / (h1.sum() + 1e-10)
                h2 = h2 / (h2.sum() + 1e-10)
                similarity = np.sum(np.minimum(h1, h2))

            elif method == "pixel":
                # Pixel-by-pixel comparison
                diff = np.abs(arr1.astype(np.float64) - arr2.astype(np.float64))
                max_diff = 255.0 * arr1.size
                actual_diff = np.sum(diff)
                similarity = 1.0 - (actual_diff / max_diff)

            is_match = similarity >= threshold
            logger.info(f"Image comparison ({method}): similarity={similarity:.4f}, threshold={threshold}, match={is_match}")

            return {
                "similarity": float(similarity),
                "is_match": is_match,
                "method": method,
                "threshold": threshold
            }

        except ImportError as e:
            logger.error(f"Required library not installed: {e}")
            return {"similarity": 0.0, "is_match": False, "method": method, "error": str(e)}
        except Exception as e:
            logger.error(f"Image comparison failed: {e}")
            return {"similarity": 0.0, "is_match": False, "method": method, "error": str(e)}

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False

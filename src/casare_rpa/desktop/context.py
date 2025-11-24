"""
Desktop Context - Main entry point for desktop automation

Manages windows, applications, and provides high-level desktop automation API.
"""

import time
import subprocess
import psutil
from typing import List, Optional, Union
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
        while time.time() - start_time < timeout:
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
            
            time.sleep(0.1)
        
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
            
            try:
                window = self.find_window(window_title, exact=False, timeout=timeout)
                logger.info(f"Application launched successfully: {window_title}")
                return window
            except ValueError:
                # If we can't find by title, try to find by process ID
                logger.warning(f"Could not find window by title '{window_title}', searching by process...")
                
                # Give more time for window to appear
                time.sleep(1.0)
                
                # Try to find any window from this process
                for window_elem in self.get_all_windows():
                    try:
                        # This is a best-effort attempt
                        if window_elem._control.ProcessId == process.pid:
                            logger.info(f"Found window by process ID: {window_elem.get_text()}")
                            return window_elem
                    except:
                        pass
                
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
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        self.cleanup()
        return False

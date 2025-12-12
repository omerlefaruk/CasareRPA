"""
Desktop Application Management Nodes

Nodes for launching, closing, and managing Windows desktop applications.
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.value_objects.types import NodeStatus, DataType

from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    APPLICATION_PATH_PROP,
    ARGUMENTS_PROP,
    WORKING_DIRECTORY_PROP,
    TIMEOUT_LONG_PROP,
    WINDOW_TITLE_HINT_PROP,
    WINDOW_STATE_PROP,
    KEEP_OPEN_PROP,
    FORCE_CLOSE_PROP,
    TIMEOUT_PROP,
    MATCH_PARTIAL_PROP,
    INCLUDE_INVISIBLE_PROP,
    FILTER_TITLE_PROP,
)


@node(category="desktop")
@properties(
    APPLICATION_PATH_PROP,
    ARGUMENTS_PROP,
    WORKING_DIRECTORY_PROP,
    TIMEOUT_LONG_PROP,
    WINDOW_TITLE_HINT_PROP,
    WINDOW_STATE_PROP,
    KEEP_OPEN_PROP,
)
class LaunchApplicationNode(DesktopNodeBase):
    """
    Launch a Windows desktop application.

    Launches an application and returns its main window for further automation.

    Config (via @properties):
        application_path: Full path to the executable (required)
        arguments: Command line arguments (default: "")
        working_directory: Starting directory (default: "")
        timeout: Maximum time to wait for window (default: 10.0 seconds)
        window_title_hint: Expected window title (default: "")
        window_state: Initial window state - normal/maximized/minimized (default: "normal")
        keep_open: Keep application open when workflow ends (default: True)

    Outputs:
        window: Desktop window object for automation
        process_id: Process ID of the launched application
        window_title: Title of the application window
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: application_path, arguments, working_directory -> window, process_id, window_title

    NODE_NAME = "Launch Application"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Launch Application",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "LaunchApplicationNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("application_path", DataType.STRING)
        # arguments and working_directory are optional
        self.add_input_port("arguments", DataType.STRING, required=False)
        self.add_input_port("working_directory", DataType.STRING, required=False)
        self.add_output_port("window", DataType.ANY)
        self.add_output_port("process_id", DataType.INTEGER)
        self.add_output_port("window_title", DataType.STRING)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - launch application."""
        app_path = self.get_parameter("application_path", context)
        arguments = self.get_parameter("arguments", context)
        working_dir = self.get_parameter("working_directory", context) or None
        timeout = self.get_parameter("timeout", context)
        window_title_hint = self.get_parameter("window_title_hint", context)
        window_state = self.get_parameter("window_state", context)
        keep_open = self.get_parameter("keep_open", context)

        if not app_path:
            error_msg = "Application path is required. Please enter the full path to the executable."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        # If no hint provided, try to guess from app name
        if not window_title_hint:
            import os

            app_name = os.path.splitext(os.path.basename(app_path))[0].lower()
            title_map = {
                "calc": "Calculator",
                "notepad": "Untitled - Notepad",
                "explorer": "File Explorer",
                "chrome": "Chrome",
                "firefox": "Firefox",
                "msedge": "Edge",
            }
            window_title_hint = title_map.get(app_name, app_name)

        logger.info(f"[{self.name}] Launching application: {app_path}")
        logger.debug(f"[{self.name}] Arguments: {arguments}")
        logger.debug(f"[{self.name}] Working directory: {working_dir}")
        logger.debug(f"[{self.name}] Window title hint: {window_title_hint}")
        logger.debug(f"[{self.name}] Timeout: {timeout}s")

        desktop_ctx = self.get_desktop_context(context)

        try:
            logger.info(
                f"[{self.name}] Calling desktop_ctx.async_launch_application..."
            )
            window = await desktop_ctx.async_launch_application(
                path=app_path,
                args=arguments,
                working_dir=working_dir,
                timeout=timeout,
                window_title=window_title_hint,
                keep_open=keep_open,
            )

            process_id = window._control.ProcessId
            window_title = window.get_text()

            logger.info(
                f"[{self.name}] Successfully got window: '{window_title}' (PID: {process_id})"
            )

            # Apply window state if needed
            if window_state == "maximized":
                try:
                    window._control.GetWindowPattern().SetWindowVisualState(1)
                    logger.debug(f"[{self.name}] Maximized window")
                except Exception as ex:
                    logger.warning(f"[{self.name}] Could not maximize window: {ex}")
            elif window_state == "minimized":
                try:
                    window._control.GetWindowPattern().SetWindowVisualState(2)
                    logger.debug(f"[{self.name}] Minimized window")
                except Exception as ex:
                    logger.warning(f"[{self.name}] Could not minimize window: {ex}")

            logger.info(
                f"[{self.name}] Application launched successfully: {window_title} (PID: {process_id})"
            )

            return self.success_result(
                window=window,
                process_id=process_id,
                window_title=window_title,
            )

        except FileNotFoundError:
            error_msg = f"Application not found: '{app_path}'. Please check the path is correct."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)
        except TimeoutError:
            error_msg = (
                f"Timeout waiting for window after launching '{app_path}'. "
                f"Window title hint was '{window_title_hint}'. "
                "Try increasing timeout or providing a more specific window title hint."
            )
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)
        except Exception as e:
            self.handle_error(e, f"launch application '{app_path}'")
            return {"success": False, "data": {}, "next_nodes": []}


@node(category="desktop")
@properties(
    FORCE_CLOSE_PROP,
    TIMEOUT_PROP,
)
class CloseApplicationNode(DesktopNodeBase):
    """
    Close a Windows desktop application.

    Closes an application gracefully or forcefully.

    Config (via @properties):
        force_close: Forcefully terminate if graceful close fails (default: False)
        timeout: Maximum time to wait for close (default: 5.0 seconds)

    Inputs:
        window: Desktop window object (from Launch Application)
        process_id: Process ID to close
        window_title: Window title to match

    Outputs:
        success: Whether the close operation succeeded
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: window, process_id, window_title -> success

    NODE_NAME = "Close Application"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Close Application",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "CloseApplicationNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Can identify app by window, process_id, or window_title - any one is sufficient
        self.add_input_port("window", DataType.ANY, required=False)
        self.add_input_port("process_id", DataType.INTEGER, required=False)
        self.add_input_port("window_title", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - close application."""
        window = self.get_input_value("window")
        process_id = self.get_input_value("process_id")
        window_title = self.get_input_value("window_title")

        force_close = self.get_parameter("force_close", context)
        timeout = self.get_parameter("timeout", context)

        if not window and not process_id and not window_title:
            raise ValueError(
                "Must provide either 'window', 'process_id', or 'window_title'"
            )

        logger.info(f"[{self.name}] Closing application (force={force_close})")

        desktop_ctx = self.get_desktop_context(context)

        try:
            target = window if window else (process_id if process_id else window_title)

            success = await desktop_ctx.async_close_application(
                window_or_pid=target, force=force_close, timeout=timeout
            )

            logger.info(f"[{self.name}] Application closed successfully")
            return self.success_result()

        except Exception as e:
            self.handle_error(e, "close application")
            return {"success": False, "data": {}, "next_nodes": []}


@node(category="desktop")
@properties(
    MATCH_PARTIAL_PROP,
    TIMEOUT_PROP,
)
class ActivateWindowNode(DesktopNodeBase):
    """
    Activate (bring to foreground) a Windows desktop window.

    Makes a window active and brings it to the foreground.

    Config (via @properties):
        match_partial: Allow partial title matching (default: True)
        timeout: Maximum time to wait for window (default: 5.0 seconds)

    Inputs:
        window: Desktop window object (from Launch Application)
        window_title: Window title to match

    Outputs:
        success: Whether the activation succeeded
        window: The activated window object
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: window, window_title -> success, window

    NODE_NAME = "Activate Window"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Activate Window",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "ActivateWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Can identify window by either window handle or title - one is required
        self.add_input_port("window", DataType.ANY, required=False)
        self.add_input_port("window_title", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("window", DataType.ANY)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - activate window."""
        window = self.get_input_value("window")
        window_title = self.get_input_value("window_title")

        match_partial = self.get_parameter("match_partial", context)
        timeout = self.get_parameter("timeout", context)

        if not window and not window_title:
            raise ValueError("Must provide either 'window' or 'window_title'")

        logger.info(f"[{self.name}] Activating window")

        desktop_ctx = self.get_desktop_context(context)

        try:
            # Find window if title provided
            if not window:
                window = await desktop_ctx.async_find_window(
                    title=window_title, exact=not match_partial, timeout=timeout
                )

            # Activate window
            window._control.SetFocus()

            # Try to bring to foreground
            try:
                import win32gui
                import win32con

                hwnd = window._control.NativeWindowHandle
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
            except Exception as e:
                logger.debug(f"Win32 foreground failed, using SetFocus: {e}")

            logger.info(f"[{self.name}] Window activated: {window.get_text()}")
            return self.success_result(window=window)

        except Exception as e:
            self.handle_error(e, "activate window")
            return {"success": False, "data": {}, "next_nodes": []}


@node(category="desktop")
@properties(
    INCLUDE_INVISIBLE_PROP,
    FILTER_TITLE_PROP,
)
class GetWindowListNode(DesktopNodeBase):
    """
    Get a list of all open Windows desktop windows.

    Returns information about all currently open windows.

    Config (via @properties):
        include_invisible: Include invisible windows (default: False)
        filter_title: Filter windows by title (default: "")

    Outputs:
        window_list: List of window information dictionaries
        window_count: Number of windows found
    """

    # @category: desktop
    # @requires: pywin32
    # @ports: none -> window_list, window_count

    NODE_NAME = "Get Window List"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "Get Window List",
    ):
        super().__init__(node_id, config, name)
        self.node_type = "GetWindowListNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_output_port("window_list", DataType.LIST)
        self.add_output_port("window_count", DataType.INTEGER)

    async def execute(self, context: Any) -> Dict[str, Any]:
        """Execute the node - get window list."""
        include_invisible = self.get_parameter("include_invisible", context)
        filter_title = self.get_parameter("filter_title", context)

        logger.info(f"[{self.name}] Getting window list")

        desktop_ctx = self.get_desktop_context(context)

        try:
            windows = desktop_ctx.get_all_windows(include_invisible=include_invisible)

            window_list = []
            for window in windows:
                window_info = {
                    "window": window,
                    "title": window.get_text(),
                    "process_id": window.get_property("ProcessId"),
                    "automation_id": window.get_property("AutomationId"),
                    "is_enabled": window.is_enabled(),
                    "is_visible": window.is_visible(),
                    "bounds": window.get_bounding_rect(),
                }

                # Apply filter if specified
                if (
                    filter_title
                    and filter_title.lower() not in window_info["title"].lower()
                ):
                    continue

                window_list.append(window_info)

            logger.info(f"[{self.name}] Found {len(window_list)} windows")

            return self.success_result(
                window_list=window_list,
                window_count=len(window_list),
            )

        except Exception as e:
            self.handle_error(e, "get window list")
            return {"success": False, "data": {}, "next_nodes": []}

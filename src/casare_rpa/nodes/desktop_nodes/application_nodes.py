"""
Desktop Application Management Nodes

Nodes for launching, closing, and managing Windows desktop applications.
"""

from typing import Any, Dict
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode as Node
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.nodes.utils.type_converters import safe_int
from ...domain.value_objects.types import NodeStatus, PortType, DataType
from ...desktop import DesktopContext


@executable_node
@node_schema(
    PropertyDef(
        "application_path",
        PropertyType.STRING,
        required=True,
        label="Application Path",
        tooltip="Full path to the executable",
        placeholder="C:\\Program Files\\App\\app.exe",
    ),
    PropertyDef(
        "arguments",
        PropertyType.STRING,
        default="",
        label="Arguments",
        tooltip="Command line arguments",
    ),
    PropertyDef(
        "working_directory",
        PropertyType.STRING,
        default="",
        label="Working Directory",
        tooltip="Starting directory for the application",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=10.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for application window",
    ),
    PropertyDef(
        "window_title_hint",
        PropertyType.STRING,
        default="",
        label="Window Title Hint",
        tooltip="Expected window title to identify the application window",
    ),
    PropertyDef(
        "window_state",
        PropertyType.CHOICE,
        default="normal",
        choices=["normal", "maximized", "minimized"],
        label="Window State",
        tooltip="Initial window state after launch",
    ),
)
class LaunchApplicationNode(Node):
    """
    Launch a Windows desktop application.

    Launches an application and returns its main window for further automation.

    Config (via @node_schema):
        application_path: Full path to the executable (required)
        arguments: Command line arguments (default: "")
        working_directory: Starting directory (default: "")
        timeout: Maximum time to wait for window (default: 10.0 seconds)
        window_title_hint: Expected window title (default: "")
        window_state: Initial window state - normal/maximized/minimized (default: "normal")

    Outputs:
        window: Desktop window object for automation
        process_id: Process ID of the launched application
        window_title: Title of the application window
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Launch Application"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Launch Application",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LaunchApplicationNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("application_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("arguments", PortType.INPUT, DataType.STRING)
        self.add_input_port("working_directory", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("window", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("process_id", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("window_title", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - launch application.

        Args:
            context: Execution context

        Returns:
            Dictionary with window, process_id, and window_title
        """
        # Get parameters using new unified method
        app_path = self.get_parameter("application_path", context)
        arguments = self.get_parameter("arguments", context)
        working_dir = self.get_parameter("working_directory", context) or None
        timeout = self.get_parameter("timeout", context)
        window_title_hint = self.get_parameter("window_title_hint", context)
        window_state = self.get_parameter("window_state", context)

        if not app_path:
            error_msg = "Application path is required. Please enter the full path to the executable."
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)

        # If no hint provided, try to guess from app name
        if not window_title_hint:
            import os

            app_name = os.path.splitext(os.path.basename(app_path))[0].lower()
            # Map common apps to their window titles
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

        # Get or create desktop context
        if not hasattr(context, "desktop_context"):
            context.desktop_context = DesktopContext()
            logger.debug(f"[{self.name}] Created new DesktopContext")

        desktop_ctx = context.desktop_context

        try:
            # Launch application using async method to avoid blocking event loop
            logger.info(
                f"[{self.name}] Calling desktop_ctx.async_launch_application..."
            )
            window = await desktop_ctx.async_launch_application(
                path=app_path,
                args=arguments,
                working_dir=working_dir,
                timeout=timeout,
                window_title=window_title_hint,
            )

            # Get process ID
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

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "window": window,
                "process_id": process_id,
                "window_title": window_title,
                "next_nodes": ["exec_out"],
            }

        except FileNotFoundError as e:
            error_msg = f"Application not found: '{app_path}'. Please check the path is correct."
            logger.error(f"[{self.name}] {error_msg}")
            logger.exception(e)
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)
        except TimeoutError as e:
            error_msg = f"Timeout waiting for window after launching '{app_path}'. Window title hint was '{window_title_hint}'. Try increasing timeout or providing a more specific window title hint."
            logger.error(f"[{self.name}] {error_msg}")
            logger.exception(e)
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = (
                f"Failed to launch application '{app_path}': {type(e).__name__}: {e}"
            )
            logger.error(f"[{self.name}] {error_msg}")
            logger.exception(e)
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "force_close",
        PropertyType.BOOLEAN,
        default=False,
        label="Force Close",
        tooltip="Forcefully terminate the application if graceful close fails",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait for application to close",
    ),
)
class CloseApplicationNode(Node):
    """
    Close a Windows desktop application.

    Closes an application gracefully or forcefully.

    Config (via @node_schema):
        force_close: Forcefully terminate if graceful close fails (default: False)
        timeout: Maximum time to wait for close (default: 5.0 seconds)

    Inputs:
        window: Desktop window object (from Launch Application)
        process_id: Process ID to close
        window_title: Window title to match

    Outputs:
        success: Whether the close operation succeeded
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Close Application"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Close Application",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CloseApplicationNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("process_id", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("window_title", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - close application.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status
        """
        # Get inputs
        window = self.get_input_value("window")
        process_id = self.get_input_value("process_id")
        window_title = self.get_input_value("window_title")

        # Get configuration
        force_close = self.get_parameter("force_close", context)
        timeout = self.get_parameter("timeout", context)

        # Validate inputs
        if not window and not process_id and not window_title:
            raise ValueError(
                "Must provide either 'window', 'process_id', or 'window_title'"
            )

        logger.info(f"[{self.name}] Closing application (force={force_close})")

        # Get desktop context
        if not hasattr(context, "desktop_context"):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            # Determine what to close
            target = window if window else (process_id if process_id else window_title)

            # Close application using async method to avoid blocking event loop
            success = await desktop_ctx.async_close_application(
                window_or_pid=target, force=force_close, timeout=timeout
            )

            logger.info(f"[{self.name}] Application closed successfully")

            self.status = NodeStatus.SUCCESS
            return {"success": success, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"Failed to close application: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "match_partial",
        PropertyType.BOOLEAN,
        default=True,
        label="Match Partial",
        tooltip="Allow partial title matching",
    ),
    PropertyDef(
        "timeout",
        PropertyType.FLOAT,
        default=5.0,
        min_value=0.1,
        label="Timeout (seconds)",
        tooltip="Maximum time to wait to find window",
    ),
)
class ActivateWindowNode(Node):
    """
    Activate (bring to foreground) a Windows desktop window.

    Makes a window active and brings it to the foreground.

    Config (via @node_schema):
        match_partial: Allow partial title matching (default: True)
        timeout: Maximum time to wait for window (default: 5.0 seconds)

    Inputs:
        window: Desktop window object (from Launch Application)
        window_title: Window title to match

    Outputs:
        success: Whether the activation succeeded
        window: The activated window object
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Activate Window"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Activate Window",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ActivateWindowNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Input ports
        self.add_input_port("window", PortType.INPUT, DataType.ANY)
        self.add_input_port("window_title", PortType.INPUT, DataType.STRING)

        # Output ports
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("window", PortType.OUTPUT, DataType.ANY)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - activate window.

        Args:
            context: Execution context

        Returns:
            Dictionary with success status and window
        """
        # Get inputs
        window = self.get_input_value("window")
        window_title = self.get_input_value("window_title")

        # Get configuration
        match_partial = self.get_parameter("match_partial", context)
        timeout = self.get_parameter("timeout", context)

        # Validate inputs
        if not window and not window_title:
            raise ValueError("Must provide either 'window' or 'window_title'")

        logger.info(f"[{self.name}] Activating window")

        # Get desktop context
        if not hasattr(context, "desktop_context"):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            # Find window if title provided (use async to avoid blocking)
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
                # Fallback - just set focus
                logger.debug(f"Win32 foreground failed, using SetFocus: {e}")

            logger.info(f"[{self.name}] Window activated: {window.get_text()}")

            self.status = NodeStatus.SUCCESS
            return {"success": True, "window": window, "next_nodes": ["exec_out"]}

        except Exception as e:
            error_msg = f"Failed to activate window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


@executable_node
@node_schema(
    PropertyDef(
        "include_invisible",
        PropertyType.BOOLEAN,
        default=False,
        label="Include Invisible",
        tooltip="Include invisible windows in the list",
    ),
    PropertyDef(
        "filter_title",
        PropertyType.STRING,
        default="",
        label="Filter Title",
        tooltip="Filter windows by title (partial match)",
    ),
)
class GetWindowListNode(Node):
    """
    Get a list of all open Windows desktop windows.

    Returns information about all currently open windows.

    Config (via @node_schema):
        include_invisible: Include invisible windows (default: False)
        filter_title: Filter windows by title (default: "")

    Outputs:
        window_list: List of window information dictionaries
        window_count: Number of windows found
    """

    __identifier__ = "casare_rpa.nodes.desktop"
    NODE_NAME = "Get Window List"

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Get Window List",
    ):
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetWindowListNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        # Output ports
        self.add_output_port("window_list", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("window_count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - get window list.

        Args:
            context: Execution context

        Returns:
            Dictionary with window_list and window_count
        """
        # Get configuration
        include_invisible = self.get_parameter("include_invisible", context)
        filter_title = self.get_parameter("filter_title", context)

        logger.info(f"[{self.name}] Getting window list")

        # Get desktop context
        if not hasattr(context, "desktop_context"):
            context.desktop_context = DesktopContext()

        desktop_ctx = context.desktop_context

        try:
            # Get all windows
            windows = desktop_ctx.get_all_windows(include_invisible=include_invisible)

            # Build window information list
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

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "window_list": window_list,
                "window_count": len(window_list),
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = f"Failed to get window list: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)

"""
Desktop Application Management Nodes

Nodes for launching, closing, and managing Windows desktop applications.
"""

from typing import Any, Dict, Optional
from loguru import logger

from ...core.base_node import BaseNode as Node
from ...core.types import NodeStatus
from ...desktop import DesktopContext


class LaunchApplicationNode(Node):
    """
    Launch a Windows desktop application.
    
    Launches an application and returns its main window for further automation.
    """
    
    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Launch Application'
    
    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Launch Application"):
        """
        Initialize Launch Application node.
        
        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "timeout": 10.0,
                "window_title_hint": "",
                "window_state": "normal"
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "LaunchApplicationNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        from casare_rpa.core.types import PortType, DataType
        
        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("application_path", PortType.INPUT, DataType.STRING)
        self.add_input_port("arguments", PortType.INPUT, DataType.STRING)
        self.add_input_port("working_directory", PortType.INPUT, DataType.STRING)
        
        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("window", PortType.OUTPUT, DataType.ANY)  # Desktop window object
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
        # Get inputs - try input ports first, then fall back to config (for GUI widgets)
        app_path = self.get_input_value('application_path') or self.config.get('application_path', '')
        arguments = self.get_input_value('arguments') or self.config.get('arguments', '')
        working_dir = self.get_input_value('working_directory') or self.config.get('working_directory') or None
        
        if not app_path:
            error_msg = "Application path is required. Please enter the full path to the executable."
            logger.error(f"[{self.name}] {error_msg}")
            logger.error(f"[{self.name}] Input value: {self.get_input_value('application_path')}")
            logger.error(f"[{self.name}] Config value: {self.config.get('application_path')}")
            logger.error(f"[{self.name}] Full config: {self.config}")
            self.status = NodeStatus.ERROR
            raise ValueError(error_msg)
        
        # Get configuration
        timeout = self.config.get('timeout', 10.0)
        window_title_hint = self.get_input_value('window_title_hint') or self.config.get('window_title_hint', '')
        # If no hint provided, try to guess from app name
        if not window_title_hint:
            import os
            app_name = os.path.splitext(os.path.basename(app_path))[0].lower()
            # Map common apps to their window titles
            title_map = {
                'calc': 'Calculator',
                'notepad': 'Untitled - Notepad',
                'explorer': 'File Explorer',
                'chrome': 'Chrome',  # Will match "Google Chrome" or any Chrome window
                'firefox': 'Firefox',
                'msedge': 'Edge'
            }
            window_title_hint = title_map.get(app_name, app_name)
        
        window_state = self.config.get('window_state', 'normal')
        
        logger.info(f"[{self.name}] Launching application: {app_path}")
        logger.debug(f"[{self.name}] Arguments: {arguments}")
        logger.debug(f"[{self.name}] Working directory: {working_dir}")
        logger.debug(f"[{self.name}] Window title hint: {window_title_hint}")
        logger.debug(f"[{self.name}] Timeout: {timeout}s")
        
        # Get or create desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()
            logger.debug(f"[{self.name}] Created new DesktopContext")
        
        desktop_ctx = context.desktop_context
        
        try:
            # Launch application
            logger.info(f"[{self.name}] Calling desktop_ctx.launch_application...")
            window = desktop_ctx.launch_application(
                path=app_path,
                args=arguments,
                working_dir=working_dir,
                timeout=timeout,
                window_title=window_title_hint
            )
            
            # Get process ID
            process_id = window._control.ProcessId
            window_title = window.get_text()
            
            logger.info(f"[{self.name}] Successfully got window: '{window_title}' (PID: {process_id})")
            
            # Apply window state if needed
            if window_state == 'maximized':
                try:
                    window._control.GetWindowPattern().SetWindowVisualState(1)  # Maximized
                    logger.debug(f"[{self.name}] Maximized window")
                except Exception as ex:
                    logger.warning(f"[{self.name}] Could not maximize window: {ex}")
            elif window_state == 'minimized':
                try:
                    window._control.GetWindowPattern().SetWindowVisualState(2)  # Minimized
                    logger.debug(f"[{self.name}] Minimized window")
                except Exception as ex:
                    logger.warning(f"[{self.name}] Could not minimize window: {ex}")
            
            logger.info(f"[{self.name}] Application launched successfully: {window_title} (PID: {process_id})")
            
            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'window': window,
                'process_id': process_id,
                'window_title': window_title,
                'next_nodes': ['exec_out']
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
            error_msg = f"Failed to launch application '{app_path}': {type(e).__name__}: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            logger.exception(e)
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class CloseApplicationNode(Node):
    """
    Close a Windows desktop application.
    
    Closes an application gracefully or forcefully.
    """
    
    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Close Application'
    
    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Close Application"):
        """
        Initialize Close Application node.
        
        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "force_close": False,
                "timeout": 5.0
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CloseApplicationNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        from casare_rpa.core.types import PortType, DataType
        
        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object
        self.add_input_port("process_id", PortType.INPUT, DataType.INTEGER)
        self.add_input_port("window_title", PortType.INPUT, DataType.STRING)
        
        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        window = self.get_input_value('window')
        process_id = self.get_input_value('process_id')
        window_title = self.get_input_value('window_title')
        
        # Get configuration
        force_close = self.config.get('force_close', False)
        timeout = self.config.get('timeout', 5.0)
        
        # Validate inputs
        if not window and not process_id and not window_title:
            raise ValueError("Must provide either 'window', 'process_id', or 'window_title'")
        
        logger.info(f"[{self.name}] Closing application (force={force_close})")
        
        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()
        
        desktop_ctx = context.desktop_context
        
        try:
            # Determine what to close
            target = window if window else (process_id if process_id else window_title)
            
            # Close application
            success = desktop_ctx.close_application(
                window_or_pid=target,
                force=force_close,
                timeout=timeout
            )
            
            logger.info(f"[{self.name}] Application closed successfully")
            
            self.status = NodeStatus.SUCCESS
            return {
                'success': success,
                'next_nodes': ['exec_out']
            }
            
        except Exception as e:
            error_msg = f"Failed to close application: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class ActivateWindowNode(Node):
    """
    Activate (bring to foreground) a Windows desktop window.
    
    Makes a window active and brings it to the foreground.
    """
    
    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Activate Window'
    
    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Activate Window"):
        """
        Initialize Activate Window node.
        
        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "match_partial": True,
                "timeout": 5.0
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ActivateWindowNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        from casare_rpa.core.types import PortType, DataType
        
        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("window", PortType.INPUT, DataType.ANY)  # Desktop window object
        self.add_input_port("window_title", PortType.INPUT, DataType.STRING)
        
        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("window", PortType.OUTPUT, DataType.ANY)  # Desktop window object
    
    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute the node - activate window.
        
        Args:
            context: Execution context
            
        Returns:
            Dictionary with success status and window
        """
        # Get inputs
        window = self.get_input_value('window')
        window_title = self.get_input_value('window_title')
        
        # Get configuration
        match_partial = self.config.get('match_partial', True)
        timeout = self.config.get('timeout', 5.0)
        
        # Validate inputs
        if not window and not window_title:
            raise ValueError("Must provide either 'window' or 'window_title'")
        
        logger.info(f"[{self.name}] Activating window")
        
        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()
        
        desktop_ctx = context.desktop_context
        
        try:
            # Find window if title provided
            if not window:
                window = desktop_ctx.find_window(
                    title=window_title,
                    exact=not match_partial,
                    timeout=timeout
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
            return {
                'success': True,
                'window': window,
                'next_nodes': ['exec_out']
            }
            
        except Exception as e:
            error_msg = f"Failed to activate window: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)


class GetWindowListNode(Node):
    """
    Get a list of all open Windows desktop windows.
    
    Returns information about all currently open windows.
    """
    
    # Node metadata
    __identifier__ = 'casare_rpa.nodes.desktop'
    NODE_NAME = 'Get Window List'
    
    def __init__(self, node_id: str = None, config: Dict[str, Any] = None, name: str = "Get Window List"):
        """
        Initialize Get Window List node.
        
        Args:
            node_id: Unique node identifier
            config: Node configuration
            name: Display name for the node
        """
        if config is None:
            config = {
                "include_invisible": False,
                "filter_title": ""
            }
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetWindowListNode"
    
    def _define_ports(self) -> None:
        """Define node ports."""
        from casare_rpa.core.types import PortType, DataType
        
        # Input ports
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        
        # Output ports
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
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
        include_invisible = self.config.get('include_invisible', False)
        filter_title = self.config.get('filter_title', '')
        
        logger.info(f"[{self.name}] Getting window list")
        
        # Get desktop context
        if not hasattr(context, 'desktop_context'):
            context.desktop_context = DesktopContext()
        
        desktop_ctx = context.desktop_context
        
        try:
            # Get all windows
            windows = desktop_ctx.get_all_windows(include_invisible=include_invisible)
            
            # Build window information list
            window_list = []
            for window in windows:
                window_info = {
                    'window': window,
                    'title': window.get_text(),
                    'process_id': window.get_property('ProcessId'),
                    'automation_id': window.get_property('AutomationId'),
                    'is_enabled': window.is_enabled(),
                    'is_visible': window.is_visible(),
                    'bounds': window.get_bounding_rect()
                }
                
                # Apply filter if specified
                if filter_title and filter_title.lower() not in window_info['title'].lower():
                    continue
                
                window_list.append(window_info)
            
            logger.info(f"[{self.name}] Found {len(window_list)} windows")
            
            self.status = NodeStatus.SUCCESS
            return {
                'success': True,
                'window_list': window_list,
                'window_count': len(window_list),
                'next_nodes': ['exec_out']
            }
            
        except Exception as e:
            error_msg = f"Failed to get window list: {e}"
            logger.error(f"[{self.name}] {error_msg}")
            self.status = NodeStatus.ERROR
            raise RuntimeError(error_msg)

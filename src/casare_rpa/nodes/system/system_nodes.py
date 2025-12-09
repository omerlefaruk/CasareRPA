"""
System Nodes for CasareRPA

System-level operations including screen region selection, volume control,
process management, environment variables, and system information.
"""

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Select Screen Region",
        label="Title",
        tooltip="Window title for region picker",
    ),
    PropertyDef(
        "show_coordinates",
        PropertyType.BOOLEAN,
        default=True,
        label="Show Coordinates",
        tooltip="Display real-time coordinates while selecting",
    ),
)
@executable_node
class ScreenRegionPickerNode(BaseNode):
    """
    Allow user to select a screen region using mouse.

    Config (via @node_schema):
        title: Window title (default: 'Select Screen Region')
        show_coordinates: Show coordinates while selecting (default: True)

    Outputs:
        x: X coordinate of top-left corner
        y: Y coordinate of top-left corner
        width: Width of selected region
        height: Height of selected region
        confirmed: True if selection was completed
    """

    # @category: system
    # @requires: uiautomation
    # @ports: none -> x, y, width, height, confirmed

    def __init__(
        self, node_id: str, name: str = "Screen Region Picker", **kwargs
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ScreenRegionPickerNode"

    def _define_ports(self) -> None:
        self.add_output_port("x", DataType.INTEGER)
        self.add_output_port("y", DataType.INTEGER)
        self.add_output_port("width", DataType.INTEGER)
        self.add_output_port("height", DataType.INTEGER)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Select Screen Region")
            show_coordinates = self.get_parameter("show_coordinates", True)

            title = context.resolve_value(title)

            try:
                from PySide6.QtWidgets import QApplication, QWidget, QLabel, QRubberBand
                from PySide6.QtCore import Qt, QPoint, QRect
                from PySide6.QtGui import (
                    QScreen,
                    QGuiApplication,
                    QPainter,
                    QColor,
                    QPen,
                )

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                # Get primary screen
                screen = QGuiApplication.primaryScreen()
                screen_geometry = screen.geometry()

                future = asyncio.get_event_loop().create_future()

                # Create transparent overlay window
                class SelectionOverlay(QWidget):
                    def __init__(self, result_future):
                        super().__init__()
                        self._future = result_future
                        self.setWindowFlags(
                            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                        )
                        self.setAttribute(Qt.WA_TranslucentBackground)
                        self.setAttribute(Qt.WA_DeleteOnClose)
                        self.setGeometry(screen_geometry)
                        self.setMouseTracking(True)
                        self.setCursor(Qt.CrossCursor)

                        self.start_pos = None
                        self.current_pos = None
                        self.selection_rect = QRect()
                        self.completed = False

                        self.coord_label = None
                        if show_coordinates:
                            self.coord_label = QLabel(self)
                            self.coord_label.setStyleSheet(
                                "background: rgba(0,0,0,180); color: white; padding: 4px; border-radius: 3px;"
                            )
                            self.coord_label.hide()

                    def paintEvent(self, event):
                        painter = QPainter(self)
                        # Semi-transparent overlay
                        painter.fillRect(self.rect(), QColor(0, 0, 0, 50))

                        if not self.selection_rect.isNull():
                            # Clear the selection area
                            painter.setCompositionMode(QPainter.CompositionMode_Clear)
                            painter.fillRect(
                                self.selection_rect.normalized(), Qt.transparent
                            )

                            # Draw selection border
                            painter.setCompositionMode(
                                QPainter.CompositionMode_SourceOver
                            )
                            pen = QPen(QColor(33, 150, 243), 2)
                            painter.setPen(pen)
                            painter.drawRect(self.selection_rect.normalized())

                    def mousePressEvent(self, event):
                        if event.button() == Qt.LeftButton:
                            self.start_pos = event.globalPosition().toPoint()
                            self.current_pos = self.start_pos
                            self.selection_rect = QRect(self.start_pos, self.start_pos)

                    def mouseMoveEvent(self, event):
                        if self.start_pos:
                            self.current_pos = event.globalPosition().toPoint()
                            self.selection_rect = QRect(
                                self.start_pos, self.current_pos
                            )
                            self.update()

                            if self.coord_label:
                                rect = self.selection_rect.normalized()
                                self.coord_label.setText(
                                    f"X: {rect.x()}, Y: {rect.y()}, W: {rect.width()}, H: {rect.height()}"
                                )
                                label_pos = self.mapFromGlobal(
                                    self.current_pos
                                ) + QPoint(15, 15)
                                self.coord_label.move(label_pos)
                                self.coord_label.adjustSize()
                                self.coord_label.show()

                    def mouseReleaseEvent(self, event):
                        if event.button() == Qt.LeftButton and self.start_pos:
                            self.completed = True
                            self._set_result()
                            self.close()

                    def keyPressEvent(self, event):
                        if event.key() == Qt.Key_Escape:
                            self.selection_rect = QRect()
                            self._set_result()
                            self.close()

                    def _set_result(self):
                        if not self._future.done():
                            if self.completed and not self.selection_rect.isNull():
                                rect = self.selection_rect.normalized()
                                self._future.set_result(
                                    (
                                        rect.x(),
                                        rect.y(),
                                        rect.width(),
                                        rect.height(),
                                        True,
                                    )
                                )
                            else:
                                self._future.set_result((0, 0, 0, 0, False))

                    def closeEvent(self, event):
                        self._set_result()
                        super().closeEvent(event)

                overlay = SelectionOverlay(future)
                overlay.show()
                overlay.activateWindow()

                x, y, width, height, confirmed = await future

            except ImportError:
                x, y, width, height, confirmed = 0, 0, 0, 0, False

            self.set_output_value("x", x)
            self.set_output_value("y", y)
            self.set_output_value("width", width)
            self.set_output_value("height", height)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"x": x, "y": y, "width": width, "height": height},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"ScreenRegionPickerNode error: {e}")
            self.set_output_value("x", 0)
            self.set_output_value("y", 0)
            self.set_output_value("width", 0)
            self.set_output_value("height", 0)
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default="get",
        choices=["get", "set", "mute", "unmute"],
        label="Action",
        tooltip="Volume action to perform",
    ),
    PropertyDef(
        "level",
        PropertyType.INTEGER,
        default=50,
        min_value=0,
        max_value=100,
        label="Volume Level",
        tooltip="Volume level (0-100) for set action",
    ),
)
@executable_node
class VolumeControlNode(BaseNode):
    """
    Get or set system volume.

    Config (via @node_schema):
        action: get/set/mute/unmute (default: 'get')
        level: Volume level 0-100 for set action (default: 50)

    Outputs:
        volume: Current volume level (0-100)
        muted: True if system is muted
        success: True if operation succeeded
    """

    # @category: system
    # @requires: uiautomation
    # @ports: level -> volume, muted, success

    def __init__(self, node_id: str, name: str = "Volume Control", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "VolumeControlNode"

    def _define_ports(self) -> None:
        self.add_input_port("level", DataType.INTEGER, required=False)
        self.add_output_port("volume", DataType.INTEGER)
        self.add_output_port("muted", DataType.BOOLEAN)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            action = self.get_parameter("action", "get")
            level_input = self.get_input_value("level")
            if level_input is None:
                level = int(self.get_parameter("level", 50) or 50)
            else:
                level = int(level_input)

            level = max(0, min(100, level))
            volume = 0
            muted = False
            success = False

            try:
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
                )
                volume_interface = cast(interface, POINTER(IAudioEndpointVolume))

                if action == "get":
                    volume = int(volume_interface.GetMasterVolumeLevelScalar() * 100)
                    muted = bool(volume_interface.GetMute())
                    success = True

                elif action == "set":
                    volume_interface.SetMasterVolumeLevelScalar(level / 100.0, None)
                    volume = level
                    muted = bool(volume_interface.GetMute())
                    success = True

                elif action == "mute":
                    volume_interface.SetMute(True, None)
                    volume = int(volume_interface.GetMasterVolumeLevelScalar() * 100)
                    muted = True
                    success = True

                elif action == "unmute":
                    volume_interface.SetMute(False, None)
                    volume = int(volume_interface.GetMasterVolumeLevelScalar() * 100)
                    muted = False
                    success = True

            except ImportError:
                logger.warning("pycaw not installed, volume control unavailable")
            except Exception as e:
                logger.error(f"Volume control error: {e}")

            self.set_output_value("volume", volume)
            self.set_output_value("muted", muted)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"volume": volume, "muted": muted},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"VolumeControlNode error: {e}")
            self.set_output_value("volume", 0)
            self.set_output_value("muted", False)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "filter_name",
        PropertyType.STRING,
        default="",
        label="Filter Name",
        tooltip="Filter processes by name (partial match)",
    ),
    PropertyDef(
        "include_details",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Details",
        tooltip="Include CPU, memory, and other details",
    ),
)
@executable_node
class ProcessListNode(BaseNode):
    """
    List running processes.

    Config (via @node_schema):
        filter_name: Filter by process name (default: '' = all)
        include_details: Include CPU/memory info (default: True)

    Outputs:
        processes: List of process dictionaries
        count: Number of processes found
    """

    # @category: system
    # @requires: uiautomation
    # @ports: filter_name -> processes, count

    def __init__(self, node_id: str, name: str = "Process List", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ProcessListNode"

    def _define_ports(self) -> None:
        self.add_input_port("filter_name", DataType.STRING, required=False)
        self.add_output_port("processes", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            filter_input = self.get_input_value("filter_name")
            if filter_input is None:
                filter_name = self.get_parameter("filter_name", "")
            else:
                filter_name = str(filter_input)

            filter_name = context.resolve_value(filter_name).lower()
            include_details = self.get_parameter("include_details", True)

            processes = []

            try:
                import psutil

                # Collect process list without blocking cpu_percent call
                for proc in psutil.process_iter(["pid", "name", "status"]):
                    try:
                        proc_info = proc.info
                        proc_name = proc_info.get("name", "").lower()

                        if filter_name and filter_name not in proc_name:
                            continue

                        process_data = {
                            "pid": proc_info["pid"],
                            "name": proc_info.get("name", "Unknown"),
                            "status": proc_info.get("status", "unknown"),
                        }

                        if include_details:
                            try:
                                # Don't use interval for cpu_percent - it blocks!
                                process_data["cpu_percent"] = proc.cpu_percent(
                                    interval=None
                                )
                                mem_info = proc.memory_info()
                                process_data["memory_mb"] = round(
                                    mem_info.rss / (1024 * 1024), 2
                                )
                                process_data["username"] = proc.username()
                                process_data["create_time"] = proc.create_time()
                            except (psutil.AccessDenied, psutil.NoSuchProcess):
                                process_data["cpu_percent"] = 0
                                process_data["memory_mb"] = 0
                                process_data["username"] = "N/A"

                        processes.append(process_data)

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            except ImportError:
                logger.warning("psutil not installed, process listing unavailable")

            self.set_output_value("processes", processes)
            self.set_output_value("count", len(processes))
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(processes)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"ProcessListNode error: {e}")
            self.set_output_value("processes", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "pid_or_name",
        PropertyType.STRING,
        default="",
        label="PID or Name",
        tooltip="Process ID (number) or name to kill",
        essential=True,
    ),
    PropertyDef(
        "force",
        PropertyType.BOOLEAN,
        default=False,
        label="Force Kill",
        tooltip="Force kill (SIGKILL) instead of graceful terminate",
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=5,
        min_value=1,
        max_value=60,
        label="Timeout (s)",
        tooltip="Timeout in seconds for graceful termination",
    ),
)
@executable_node
class ProcessKillNode(BaseNode):
    """
    Kill a process by PID or name.

    Config (via @node_schema):
        pid_or_name: Process ID or name (essential)
        force: Force kill (default: False)
        timeout: Graceful termination timeout (default: 5s)

    Inputs:
        pid_or_name: Optional - overrides config if connected

    Outputs:
        killed_count: Number of processes killed
        success: True if at least one process was killed
    """

    # @category: system
    # @requires: uiautomation
    # @ports: pid_or_name -> killed_count, success

    def __init__(self, node_id: str, name: str = "Process Kill", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ProcessKillNode"

    def _define_ports(self) -> None:
        self.add_input_port("pid_or_name", DataType.STRING, required=False)
        self.add_output_port("killed_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            pid_or_name = self.get_input_value("pid_or_name")
            if pid_or_name is None:
                pid_or_name = self.get_parameter("pid_or_name", "")
            pid_or_name = context.resolve_value(str(pid_or_name))

            force = self.get_parameter("force", False)
            timeout = int(self.get_parameter("timeout", 5) or 5)

            if not pid_or_name:
                self.set_output_value("killed_count", 0)
                self.set_output_value("success", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"error": "No PID or name provided"},
                    "next_nodes": ["exec_out"],
                }

            killed_count = 0

            try:
                import psutil

                # Check if it's a PID (numeric)
                try:
                    pid = int(pid_or_name)
                    procs = [psutil.Process(pid)]
                except ValueError:
                    # It's a name, find all matching processes
                    name_lower = pid_or_name.lower()
                    procs = [
                        p
                        for p in psutil.process_iter(["pid", "name"])
                        if name_lower in p.info.get("name", "").lower()
                    ]

                for proc in procs:
                    try:
                        if force:
                            proc.kill()
                        else:
                            proc.terminate()

                        try:
                            proc.wait(timeout=timeout)
                        except psutil.TimeoutExpired:
                            if not force:
                                proc.kill()
                                proc.wait(timeout=2)

                        killed_count += 1
                        logger.info(f"Killed process: {proc.pid}")

                    except psutil.NoSuchProcess:
                        logger.debug(f"Process {proc.pid} already terminated")
                    except psutil.AccessDenied:
                        logger.warning(f"Access denied killing process {proc.pid}")
                    except Exception as e:
                        logger.error(f"Error killing process {proc.pid}: {e}")

            except ImportError:
                logger.warning("psutil not installed, process kill unavailable")

            success = killed_count > 0
            self.set_output_value("killed_count", killed_count)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"killed_count": killed_count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"ProcessKillNode error: {e}")
            self.set_output_value("killed_count", 0)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "action",
        PropertyType.CHOICE,
        default="get",
        choices=["get", "set"],
        label="Action",
        tooltip="Get or set environment variable",
    ),
    PropertyDef(
        "var_name",
        PropertyType.STRING,
        default="",
        label="Variable Name",
        tooltip="Environment variable name",
        essential=True,
    ),
    PropertyDef(
        "value",
        PropertyType.STRING,
        default="",
        label="Value",
        tooltip="Value to set (for set action)",
    ),
    PropertyDef(
        "scope",
        PropertyType.CHOICE,
        default="process",
        choices=["process", "user", "system"],
        label="Scope",
        tooltip="Variable scope (process=current only, user/system=persistent)",
    ),
)
@executable_node
class EnvironmentVariableNode(BaseNode):
    """
    Get or set environment variables.

    Config (via @node_schema):
        action: get/set (default: 'get')
        name: Variable name (essential)
        value: Value to set (default: '')
        scope: process/user/system (default: 'process')

    Inputs:
        name: Optional - overrides config if connected
        value: Optional - overrides config if connected

    Outputs:
        value: Variable value (empty if not found)
        exists: True if variable exists
        success: True if operation succeeded
    """

    # @category: system
    # @requires: uiautomation
    # @ports: var_name, value -> result_value, exists, success

    def __init__(
        self, node_id: str, name: str = "Environment Variable", **kwargs
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "EnvironmentVariableNode"

    def _define_ports(self) -> None:
        self.add_input_port("var_name", DataType.STRING, required=False)
        self.add_input_port("value", DataType.STRING, required=False)
        self.add_output_port("result_value", DataType.STRING)
        self.add_output_port("exists", DataType.BOOLEAN)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import os

            action = self.get_parameter("action", "get")

            var_name = self.get_input_value("var_name")
            if var_name is None:
                var_name = self.get_parameter("var_name", "")
            var_name = context.resolve_value(str(var_name))

            var_value = self.get_input_value("value")
            if var_value is None:
                var_value = self.get_parameter("value", "")
            var_value = context.resolve_value(str(var_value))

            scope = self.get_parameter("scope", "process")

            if not var_name:
                self.set_output_value("result_value", "")
                self.set_output_value("exists", False)
                self.set_output_value("success", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"error": "No variable name"},
                    "next_nodes": ["exec_out"],
                }

            result_value = ""
            exists = False
            success = False

            if action == "get":
                result_value = os.environ.get(var_name, "")
                exists = var_name in os.environ
                success = True

            elif action == "set":
                if scope == "process":
                    os.environ[var_name] = var_value
                    result_value = var_value
                    exists = True
                    success = True
                else:
                    # Persistent environment variables (Windows registry)
                    try:
                        import winreg

                        if scope == "user":
                            key = winreg.OpenKey(
                                winreg.HKEY_CURRENT_USER,
                                r"Environment",
                                0,
                                winreg.KEY_SET_VALUE,
                            )
                        else:  # system
                            key = winreg.OpenKey(
                                winreg.HKEY_LOCAL_MACHINE,
                                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                                0,
                                winreg.KEY_SET_VALUE,
                            )

                        winreg.SetValueEx(key, var_name, 0, winreg.REG_SZ, var_value)
                        winreg.CloseKey(key)

                        # Also set in current process
                        os.environ[var_name] = var_value
                        result_value = var_value
                        exists = True
                        success = True

                        logger.info(f"Set {scope} environment variable: {var_name}")

                    except PermissionError:
                        logger.error(
                            f"Permission denied setting {scope} environment variable"
                        )
                    except Exception as e:
                        logger.error(f"Error setting environment variable: {e}")

            self.set_output_value("result_value", result_value)
            self.set_output_value("exists", exists)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result_value": result_value, "exists": exists},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"EnvironmentVariableNode error: {e}")
            self.set_output_value("result_value", "")
            self.set_output_value("exists", False)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "info_type",
        PropertyType.CHOICE,
        default="all",
        choices=["os", "cpu", "ram", "disk", "network", "all"],
        label="Info Type",
        tooltip="Type of system information to retrieve",
    ),
)
@executable_node
class SystemInfoNode(BaseNode):
    """
    Get system information.

    Config (via @node_schema):
        info_type: os/cpu/ram/disk/network/all (default: 'all')

    Outputs:
        info: Dictionary of system information
        os_name: Operating system name
        cpu_percent: Current CPU usage
        ram_percent: Current RAM usage
        disk_percent: Current disk usage
    """

    # @category: system
    # @requires: uiautomation
    # @ports: none -> info, os_name, cpu_percent, ram_percent, disk_percent

    def __init__(self, node_id: str, name: str = "System Info", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SystemInfoNode"

    def _define_ports(self) -> None:
        self.add_output_port("info", DataType.DICT)
        self.add_output_port("os_name", DataType.STRING)
        self.add_output_port("cpu_percent", DataType.FLOAT)
        self.add_output_port("ram_percent", DataType.FLOAT)
        self.add_output_port("disk_percent", DataType.FLOAT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import platform
            import os

            info_type = self.get_parameter("info_type", "all")
            info = {}

            # OS Info
            if info_type in ["os", "all"]:
                info["os"] = {
                    "system": platform.system(),
                    "release": platform.release(),
                    "version": platform.version(),
                    "machine": platform.machine(),
                    "processor": platform.processor(),
                    "hostname": platform.node(),
                    "python_version": platform.python_version(),
                }

            try:
                import psutil

                # CPU Info
                if info_type in ["cpu", "all"]:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    cpu_count = psutil.cpu_count()
                    cpu_count_logical = psutil.cpu_count(logical=True)
                    cpu_freq = psutil.cpu_freq()

                    info["cpu"] = {
                        "percent": cpu_percent,
                        "cores_physical": cpu_count,
                        "cores_logical": cpu_count_logical,
                        "frequency_mhz": cpu_freq.current if cpu_freq else 0,
                    }

                # RAM Info
                if info_type in ["ram", "all"]:
                    mem = psutil.virtual_memory()
                    info["ram"] = {
                        "total_gb": round(mem.total / (1024**3), 2),
                        "available_gb": round(mem.available / (1024**3), 2),
                        "used_gb": round(mem.used / (1024**3), 2),
                        "percent": mem.percent,
                    }

                # Disk Info
                if info_type in ["disk", "all"]:
                    partitions = []
                    for part in psutil.disk_partitions():
                        try:
                            usage = psutil.disk_usage(part.mountpoint)
                            partitions.append(
                                {
                                    "device": part.device,
                                    "mountpoint": part.mountpoint,
                                    "fstype": part.fstype,
                                    "total_gb": round(usage.total / (1024**3), 2),
                                    "used_gb": round(usage.used / (1024**3), 2),
                                    "free_gb": round(usage.free / (1024**3), 2),
                                    "percent": usage.percent,
                                }
                            )
                        except PermissionError:
                            continue
                    info["disk"] = partitions

                # Network Info
                if info_type in ["network", "all"]:
                    net_io = psutil.net_io_counters()
                    net_addrs = psutil.net_if_addrs()

                    interfaces = []
                    for iface, addrs in net_addrs.items():
                        iface_info = {"name": iface, "addresses": []}
                        for addr in addrs:
                            iface_info["addresses"].append(
                                {
                                    "family": str(addr.family),
                                    "address": addr.address,
                                }
                            )
                        interfaces.append(iface_info)

                    info["network"] = {
                        "bytes_sent": net_io.bytes_sent,
                        "bytes_recv": net_io.bytes_recv,
                        "interfaces": interfaces,
                    }

            except ImportError:
                logger.warning("psutil not installed, limited system info available")
                info["cpu"] = {"percent": 0}
                info["ram"] = {"percent": 0}
                info["disk"] = []

            # Extract key values
            os_name = f"{platform.system()} {platform.release()}"
            cpu_percent = info.get("cpu", {}).get("percent", 0)
            ram_percent = info.get("ram", {}).get("percent", 0)

            # Get primary disk usage
            disk_percent = 0
            disk_info = info.get("disk", [])
            if disk_info:
                disk_percent = disk_info[0].get("percent", 0)

            self.set_output_value("info", info)
            self.set_output_value("os_name", os_name)
            self.set_output_value("cpu_percent", cpu_percent)
            self.set_output_value("ram_percent", ram_percent)
            self.set_output_value("disk_percent", disk_percent)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": info,
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            logger.error(f"SystemInfoNode error: {e}")
            self.set_output_value("info", {})
            self.set_output_value("os_name", "")
            self.set_output_value("cpu_percent", 0)
            self.set_output_value("ram_percent", 0)
            self.set_output_value("disk_percent", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

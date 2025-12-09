"""
Windows Services management nodes for CasareRPA.

This module provides nodes for managing Windows services:
- Get service status
- Start/Stop/Restart services
- List services
"""

import json
import subprocess
import sys

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@executable_node
class GetServiceStatusNode(BaseNode):
    """
    Get the status of a Windows service.

    Inputs:
        service_name: Name of the service

    Outputs:
        status: Service status ('running', 'stopped', 'paused', 'starting', 'stopping', 'unknown')
        display_name: Service display name
        exists: Whether service exists
    """

    # @category: system
    # @requires: none
    # @ports: service_name -> status, display_name, exists

    def __init__(
        self, node_id: str, name: str = "Get Service Status", **kwargs
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetServiceStatusNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("status", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("display_name", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("exists", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            result = subprocess.run(
                ["sc", "query", service_name], capture_output=True, text=True
            )

            if (
                "FAILED 1060" in result.stderr
                or "does not exist" in result.stderr.lower()
            ):
                self.set_output_value("status", "not_found")
                self.set_output_value("display_name", "")
                self.set_output_value("exists", False)
            else:
                # Parse status from output
                output = result.stdout
                status = "unknown"

                if "RUNNING" in output:
                    status = "running"
                elif "STOPPED" in output:
                    status = "stopped"
                elif "PAUSED" in output:
                    status = "paused"
                elif "START_PENDING" in output:
                    status = "starting"
                elif "STOP_PENDING" in output:
                    status = "stopping"

                # Get display name
                display_result = subprocess.run(
                    ["sc", "GetDisplayName", service_name],
                    capture_output=True,
                    text=True,
                )
                display_name = ""
                if "=" in display_result.stdout:
                    display_name = display_result.stdout.split("=")[-1].strip()

                self.set_output_value("status", status)
                self.set_output_value("display_name", display_name)
                self.set_output_value("exists", True)

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"status": self.get_output_value("status")},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("status", "error")
            self.set_output_value("exists", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class StartServiceNode(BaseNode):
    """
    Start a Windows service.

    Inputs:
        service_name: Name of the service

    Outputs:
        success: Whether service was started
        message: Status message
    """

    # @category: system
    # @requires: none
    # @ports: service_name -> success, message

    def __init__(self, node_id: str, name: str = "Start Service", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "StartServiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            result = subprocess.run(
                ["sc", "start", service_name], capture_output=True, text=True
            )

            success = (
                result.returncode == 0 or "already running" in result.stderr.lower()
            )
            message = result.stdout if success else result.stderr

            self.set_output_value("success", success)
            self.set_output_value("message", message.strip())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@executable_node
class StopServiceNode(BaseNode):
    """
    Stop a Windows service.

    Inputs:
        service_name: Name of the service

    Outputs:
        success: Whether service was stopped
        message: Status message
    """

    # @category: system
    # @requires: none
    # @ports: service_name -> success, message

    def __init__(self, node_id: str, name: str = "Stop Service", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "StopServiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            result = subprocess.run(
                ["sc", "stop", service_name], capture_output=True, text=True
            )

            success = result.returncode == 0 or "not started" in result.stderr.lower()
            message = result.stdout if success else result.stderr

            self.set_output_value("success", success)
            self.set_output_value("message", message.strip())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "wait_time",
        PropertyType.INTEGER,
        default=2,
        min_value=0,
        label="Wait Time (seconds)",
        tooltip="Seconds to wait between stop and start",
    ),
)
@executable_node
class RestartServiceNode(BaseNode):
    """
    Restart a Windows service.

    Config (via @node_schema):
        wait_time: Seconds to wait between stop and start (default: 2)

    Inputs:
        service_name: Name of the service

    Outputs:
        success: Whether service was restarted
        message: Status message
    """

    # @category: system
    # @requires: none
    # @ports: service_name -> success, message

    def __init__(self, node_id: str, name: str = "Restart Service", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RestartServiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        import asyncio

        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")
            wait_time = self.get_parameter("wait_time", 2)

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            # Stop service
            subprocess.run(["sc", "stop", service_name], capture_output=True)

            # Wait
            await asyncio.sleep(wait_time)

            # Start service
            result = subprocess.run(
                ["sc", "start", service_name], capture_output=True, text=True
            )

            success = result.returncode == 0
            message = result.stdout if success else result.stderr

            self.set_output_value("success", success)
            self.set_output_value("message", message.strip())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "state_filter",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "running", "stopped"],
        label="State Filter",
        tooltip="Filter services by state",
    ),
)
@executable_node
class ListServicesNode(BaseNode):
    """
    List all Windows services.

    Config (via @node_schema):
        state_filter: 'all', 'running', 'stopped' (default: all)

    Outputs:
        services: List of service info dicts
        count: Number of services
    """

    # @category: system
    # @requires: none
    # @ports: none -> services, count

    def __init__(self, node_id: str, name: str = "List Services", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListServicesNode"

    def _define_ports(self) -> None:
        self.add_output_port("services", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            state_filter = self.get_parameter("state_filter", "all")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            # Use PowerShell to get services as it provides better output
            ps_cmd = (
                "Get-Service | Select-Object Name, DisplayName, Status | ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd], capture_output=True, text=True
            )

            services = []
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict):
                        data = [data]

                    for svc in data:
                        status = str(svc.get("Status", "")).lower()
                        if status == "4":
                            status = "running"
                        elif status == "1":
                            status = "stopped"

                        # Apply filter
                        if state_filter == "running" and status != "running":
                            continue
                        if state_filter == "stopped" and status != "stopped":
                            continue

                        services.append(
                            {
                                "name": svc.get("Name", ""),
                                "display_name": svc.get("DisplayName", ""),
                                "status": status,
                            }
                        )
                except json.JSONDecodeError:
                    pass

            self.set_output_value("services", services)
            self.set_output_value("count", len(services))
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(services)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("services", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

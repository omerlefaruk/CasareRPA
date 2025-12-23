"""
CallSubworkflowNode - Invokes subworkflows with sync/async execution modes.

This node provides visual workflow-level orchestration, allowing one workflow
to call another subworkflow as an atomic operation. Unlike SubflowNode (which
embeds subflow content inline), CallSubworkflowNode references an external
subworkflow by ID and supports both synchronous and asynchronous execution.

Key Features:
- Sync mode: Blocks until subworkflow completes
- Async mode: Returns immediately with job_id for later status check
- Dynamic ports: Input/output ports match selected subworkflow interface
- Timeout handling: Configurable timeout with proper cleanup
- Recursion prevention: Tracks call depth to prevent infinite loops
"""

import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.subflow import Subflow
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext


MAX_CALL_DEPTH = 10


@properties(
    PropertyDef(
        "subworkflow_id",
        PropertyType.STRING,
        default="",
        label="Subworkflow ID",
        tooltip="ID of the subworkflow to call",
    ),
    PropertyDef(
        "execution_mode",
        PropertyType.CHOICE,
        default="sync",
        label="Execution Mode",
        tooltip="sync: wait for completion; async: return immediately with job_id",
        choices=["sync", "async"],
    ),
    PropertyDef(
        "timeout_seconds",
        PropertyType.INTEGER,
        default=300,
        label="Timeout (seconds)",
        tooltip="Maximum execution time (sync mode only)",
        min_value=1,
        max_value=86400,
    ),
    PropertyDef(
        "wait_for_result",
        PropertyType.BOOLEAN,
        default=True,
        label="Wait for Result",
        tooltip="In async mode, whether to poll for completion",
    ),
    PropertyDef(
        "poll_interval",
        PropertyType.INTEGER,
        default=5,
        label="Poll Interval (seconds)",
        tooltip="Interval between status checks when waiting for async result",
        min_value=1,
        max_value=60,
    ),
)
@node(category="workflow", exec_outputs=["exec_out", "error"])
class CallSubworkflowNode(BaseNode):
    """
    Calls a subworkflow by reference with sync or async execution.

    This node differs from SubflowNode in that it:
    - References subworkflows by ID (not embedded)
    - Supports async execution (fire-and-forget or poll-for-result)
    - Provides job_id output for external tracking
    - Integrates with the orchestrator for distributed execution

    Execution Modes:
    - sync: Executes subworkflow and blocks until completion or timeout
    - async: Submits subworkflow to job queue and returns job_id

    Ports:
    - exec_in: Execution input
    - exec_out: Execution continues (success path)
    - error: Execution failed
    - job_id (output): Job ID for async tracking
    - Dynamic input/output ports based on selected subworkflow

    @category: workflow
    @requires: none
    """

    def __init__(
        self,
        node_id: str,
        config: Optional[Dict] = None,
        **kwargs,
    ) -> None:
        """
        Initialize CallSubworkflowNode.

        Args:
            node_id: Unique node identifier
            config: Node configuration
        """
        config = config or {}
        super().__init__(node_id, config)
        self.node_type = "CallSubworkflowNode"
        self.category = "Workflow"

        self._subworkflow: Optional[Subflow] = None
        self._dynamic_inputs: List[str] = []
        self._dynamic_outputs: List[str] = []

    def _define_ports(self) -> None:
        """Define default ports. Dynamic ports added via configure_from_subworkflow."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("error")

        self.add_output_port("job_id", DataType.STRING, "Job ID", required=False)
        self.add_output_port("success", DataType.BOOLEAN, "Success", required=False)
        self.add_output_port(
            "execution_time_ms", DataType.INTEGER, "Execution Time (ms)", required=False
        )

    def configure_from_subworkflow(self, subworkflow: Subflow) -> None:
        """
        Configure dynamic ports based on subworkflow interface.

        Args:
            subworkflow: Subworkflow to extract interface from
        """
        self._subworkflow = subworkflow
        self.config["subworkflow_id"] = subworkflow.id
        self.config["subworkflow_name"] = subworkflow.name

        # Clear previous dynamic ports
        for port_name in self._dynamic_inputs:
            if port_name in self.input_ports:
                del self.input_ports[port_name]
        for port_name in self._dynamic_outputs:
            if port_name in self.output_ports:
                del self.output_ports[port_name]

        self._dynamic_inputs.clear()
        self._dynamic_outputs.clear()

        # Add input ports from subworkflow
        for port in subworkflow.inputs:
            data_type = self._normalize_data_type(port.data_type)
            self.add_input_port(
                port.name,
                data_type,
                port.description or port.name,
                required=port.required,
            )
            self._dynamic_inputs.append(port.name)

        # Add output ports from subworkflow
        for port in subworkflow.outputs:
            data_type = self._normalize_data_type(port.data_type)
            self.add_output_port(
                port.name,
                data_type,
                port.description or port.name,
                required=False,
            )
            self._dynamic_outputs.append(port.name)

        logger.debug(
            f"Configured CallSubworkflowNode from '{subworkflow.name}': "
            f"{len(self._dynamic_inputs)} inputs, {len(self._dynamic_outputs)} outputs"
        )

    def _normalize_data_type(self, data_type: Any) -> DataType:
        """Normalize data type to DataType enum."""
        if isinstance(data_type, DataType):
            return data_type
        if not data_type:
            return DataType.ANY
        if isinstance(data_type, str):
            type_map = {
                "STRING": DataType.STRING,
                "INTEGER": DataType.INTEGER,
                "FLOAT": DataType.FLOAT,
                "BOOLEAN": DataType.BOOLEAN,
                "LIST": DataType.LIST,
                "DICT": DataType.DICT,
                "OBJECT": DataType.OBJECT,
                "ANY": DataType.ANY,
                "PAGE": DataType.PAGE,
                "ELEMENT": DataType.ELEMENT,
            }
            return type_map.get(data_type.upper(), DataType.ANY)
        return DataType.ANY

    async def execute(self, context: "ExecutionContext") -> ExecutionResult:
        """
        Execute the subworkflow call.

        Args:
            context: Execution context

        Returns:
            ExecutionResult with outputs or error
        """
        import time

        self.status = NodeStatus.RUNNING
        start_time = time.time()

        try:
            subworkflow_id = self.get_parameter("subworkflow_id", "")
            execution_mode = self.get_parameter("execution_mode", "sync")
            timeout_seconds = self.get_parameter("timeout_seconds", 300)
            wait_for_result = self.get_parameter("wait_for_result", True)
            poll_interval = self.get_parameter("poll_interval", 5)

            if not subworkflow_id:
                return self._error_result("Subworkflow ID not configured")

            # Check call depth to prevent infinite recursion
            call_depth = context.get_variable("_subworkflow_call_depth", 0)
            if call_depth >= MAX_CALL_DEPTH:
                return self._error_result(
                    f"Maximum call depth ({MAX_CALL_DEPTH}) exceeded - "
                    "possible infinite recursion"
                )

            # Load subworkflow
            subworkflow = await self._load_subworkflow(subworkflow_id)
            if not subworkflow:
                return self._error_result(f"Subworkflow '{subworkflow_id}' not found")

            # Collect input values
            inputs = self._collect_inputs()

            logger.info(
                f"Calling subworkflow '{subworkflow.name}' "
                f"(mode={execution_mode}, timeout={timeout_seconds}s)"
            )

            if execution_mode == "async":
                result = await self._execute_async(
                    subworkflow,
                    inputs,
                    context,
                    wait_for_result,
                    poll_interval,
                    timeout_seconds,
                    call_depth,
                )
            else:
                result = await self._execute_sync(
                    subworkflow,
                    inputs,
                    context,
                    timeout_seconds,
                    call_depth,
                )

            execution_time_ms = int((time.time() - start_time) * 1000)

            if result.get("success"):
                self.status = NodeStatus.SUCCESS
                self.set_output_value("success", True)
                self.set_output_value("execution_time_ms", execution_time_ms)
                if "job_id" in result:
                    self.set_output_value("job_id", result["job_id"])

                # Map subworkflow outputs to node outputs
                outputs = result.get("data", {})
                for port_name in self._dynamic_outputs:
                    if port_name in outputs:
                        self.set_output_value(port_name, outputs[port_name])

                return {
                    "success": True,
                    "data": {
                        **outputs,
                        "execution_time_ms": execution_time_ms,
                        "job_id": result.get("job_id"),
                    },
                    "next_nodes": ["exec_out"],
                }
            else:
                return self._error_result(
                    result.get("error", "Subworkflow execution failed"),
                    execution_time_ms=execution_time_ms,
                )

        except asyncio.TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return self._error_result(
                f"Subworkflow execution timed out after {timeout_seconds}s",
                execution_time_ms=execution_time_ms,
            )
        except Exception as e:
            logger.exception(f"CallSubworkflowNode execution failed: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)
            return self._error_result(str(e), execution_time_ms=execution_time_ms)

    async def _execute_sync(
        self,
        subworkflow: Subflow,
        inputs: Dict[str, Any],
        context: "ExecutionContext",
        timeout_seconds: int,
        call_depth: int,
    ) -> Dict[str, Any]:
        """Execute subworkflow synchronously."""
        try:
            from casare_rpa.infrastructure.execution.subworkflow_executor import (
                SubworkflowExecutor,
            )

            executor = SubworkflowExecutor()
            result = await asyncio.wait_for(
                executor.execute(
                    subworkflow=subworkflow,
                    inputs=inputs,
                    parent_context=context,
                    call_depth=call_depth + 1,
                ),
                timeout=timeout_seconds,
            )

            return {
                "success": result.success,
                "data": result.outputs,
                "error": result.error,
            }
        except ImportError:
            # Fallback to application layer executor
            from casare_rpa.application.use_cases.subflow_executor import (
                SubflowExecutor,
            )

            executor = SubflowExecutor()
            result = await asyncio.wait_for(
                executor.execute(
                    subflow=self._create_subflow_data(subworkflow),
                    inputs=inputs,
                    context=context.clone_for_branch(f"call_{subworkflow.id}"),
                ),
                timeout=timeout_seconds,
            )

            return {
                "success": result.success,
                "data": result.outputs,
                "error": result.error,
            }

    async def _execute_async(
        self,
        subworkflow: Subflow,
        inputs: Dict[str, Any],
        context: "ExecutionContext",
        wait_for_result: bool,
        poll_interval: int,
        timeout_seconds: int,
        call_depth: int,
    ) -> Dict[str, Any]:
        """Execute subworkflow asynchronously via job queue."""
        import uuid

        job_id = str(uuid.uuid4())

        try:
            # Try to submit to orchestrator job queue
            from casare_rpa.application.services.orchestrator_client import (
                OrchestratorClient,
            )

            client = context.resources.get("orchestrator_client")
            if client is None:
                client = OrchestratorClient()
                context.resources["orchestrator_client"] = client

            # Submit job
            await client.submit_job(
                job_id=job_id,
                workflow_id=subworkflow.id,
                workflow_name=subworkflow.name,
                inputs=inputs,
                metadata={
                    "parent_workflow": context.workflow_name,
                    "call_depth": call_depth + 1,
                },
            )

            if not wait_for_result:
                return {"success": True, "job_id": job_id, "data": {}}

            # Poll for completion
            elapsed = 0
            while elapsed < timeout_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                status = await client.get_job_status(job_id)
                if status.get("completed"):
                    if status.get("success"):
                        return {
                            "success": True,
                            "job_id": job_id,
                            "data": status.get("result", {}),
                        }
                    else:
                        return {
                            "success": False,
                            "job_id": job_id,
                            "error": status.get("error", "Job failed"),
                        }

            return {
                "success": False,
                "job_id": job_id,
                "error": f"Job did not complete within {timeout_seconds}s",
            }

        except ImportError:
            # Orchestrator not available - fall back to sync execution
            logger.warning("Orchestrator client not available, falling back to sync execution")
            result = await self._execute_sync(
                subworkflow, inputs, context, timeout_seconds, call_depth
            )
            result["job_id"] = job_id
            return result

    def _collect_inputs(self) -> Dict[str, Any]:
        """Collect input values from dynamic input ports."""
        inputs = {}
        for port_name in self._dynamic_inputs:
            value = self.get_input_value(port_name)
            if value is not None:
                inputs[port_name] = value
            else:
                # Check config for default using dual-source accessor
                value = self.get_parameter(port_name)
                if value is not None:
                    inputs[port_name] = value
        return inputs

    async def _load_subworkflow(self, subworkflow_id: str) -> Optional[Subflow]:
        """Load subworkflow by ID."""
        if self._subworkflow and self._subworkflow.id == subworkflow_id:
            return self._subworkflow

        try:
            from casare_rpa.infrastructure.repositories.subflow_repository import (
                SubflowRepository,
            )

            repo = SubflowRepository()
            subworkflow = await repo.get_by_id(subworkflow_id)
            if subworkflow:
                self._subworkflow = subworkflow
            return subworkflow
        except ImportError:
            # Try loading from file path in config
            subworkflow_path = self.get_parameter("subworkflow_path", "")
            if subworkflow_path:
                try:
                    subworkflow = Subflow.load_from_file(subworkflow_path)
                    if subworkflow.id == subworkflow_id:
                        self._subworkflow = subworkflow
                        return subworkflow
                except Exception as e:
                    logger.error(f"Failed to load subworkflow from file: {e}")
            return None

    def _create_subflow_data(self, subworkflow: Subflow) -> Any:
        """Create SubflowData for application layer executor."""
        from casare_rpa.application.use_cases.subflow_executor import (
            Subflow as SubflowData,
            SubflowInputDefinition,
            SubflowOutputDefinition,
        )
        from casare_rpa.domain.entities.workflow import WorkflowSchema

        workflow_schema = WorkflowSchema()
        workflow_schema.nodes = subworkflow.nodes
        workflow_schema.connections = []

        input_defs = [
            SubflowInputDefinition(
                name=p.name,
                data_type=str(p.data_type.name)
                if hasattr(p.data_type, "name")
                else str(p.data_type),
                required=p.required,
            )
            for p in subworkflow.inputs
        ]

        output_defs = [
            SubflowOutputDefinition(
                name=p.name,
                data_type=str(p.data_type.name)
                if hasattr(p.data_type, "name")
                else str(p.data_type),
            )
            for p in subworkflow.outputs
        ]

        return SubflowData(
            workflow=workflow_schema,
            inputs=input_defs,
            outputs=output_defs,
            name=subworkflow.name,
        )

    def _error_result(self, error: str, execution_time_ms: int = 0) -> ExecutionResult:
        """Create error result."""
        self.status = NodeStatus.ERROR
        self.set_output_value("success", False)
        self.set_output_value("execution_time_ms", execution_time_ms)
        return {
            "success": False,
            "error": error,
            "error_code": "SUBWORKFLOW_CALL_ERROR",
            "data": {"execution_time_ms": execution_time_ms},
            "next_nodes": ["error"],
        }

    def __repr__(self) -> str:
        subworkflow_name = self._subworkflow.name if self._subworkflow else "not configured"
        return f"CallSubworkflowNode(id='{self.node_id}', subworkflow='{subworkflow_name}')"

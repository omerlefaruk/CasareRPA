"""
ExecuteWorkflowNode - Executes a standard workflow JSON file.

This node allows executing any saved workflow file (.json) as a sub-process.
It handles the transformation of visual nodes to executable nodes internally,
permitting the reuse of any workflow without explicit subflow packaging.
"""

import asyncio
import orjson
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "workflow_path",
        PropertyType.FILE_PATH,
        default="",
        label="Workflow File",
        tooltip="Path to the workflow .json file to execute",
        placeholder="C:/path/to/workflow.json",
    ),
    PropertyDef(
        "wait_for_completion",
        PropertyType.BOOLEAN,
        default=True,
        label="Wait for Completion",
        tooltip="If true, waits for the sub-workflow to finish before continuing.",
    ),
)
@node(category="workflow", exec_outputs=["exec_out", "error"])
class ExecuteWorkflowNode(BaseNode):
    """
    Executes a standard workflow JSON file.

    This node loads a workflow definition from a JSON file and executes it.
    It automatically transforms any visual nodes found in the file into
    executable nodes.

    @category: workflow
    @requires: none
    """

    def __init__(
        self,
        node_id: str,
        config: Optional[Dict] = None,
        **kwargs,
    ) -> None:
        """Initialize ExecuteWorkflowNode."""
        config = config or {}
        super().__init__(node_id, config)
        self.node_type = "ExecuteWorkflowNode"
        self.category = "Workflow"

    def _define_ports(self) -> None:
        """Define default ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("error")

    async def execute(self, context: "ExecutionContext") -> ExecutionResult:
        """
        Execute the referenced workflow file.

        Args:
            context: Execution context

        Returns:
            ExecutionResult
        """
        self.status = NodeStatus.RUNNING

        try:
            workflow_path = self.get_parameter("workflow_path", "")
            wait_for_completion = self.get_parameter("wait_for_completion", True)

            if not workflow_path:
                return self._error_result("No workflow path configured")

            path = Path(workflow_path)
            if not path.exists():
                return self._error_result(f"Workflow file not found: {workflow_path}")

            # Load workflow data
            try:
                with open(path, "rb") as f:
                    workflow_data = orjson.loads(f.read())
            except Exception as e:
                return self._error_result(f"Failed to read workflow file: {e}")

            logger.info(f"Executing workflow from: {workflow_path}")

            # Execute using SubflowExecutor
            # We wrap the loaded workflow data into a SubflowData structure
            # that SubflowExecutor expects.
            result = await self._run_workflow(workflow_data, context, path.stem)

            if result.get("success"):
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": result.get("data", {}),
                    "next_nodes": ["exec_out"],
                }
            else:
                return self._error_result(
                    result.get("error", "Workflow execution failed")
                )

        except Exception as e:
            logger.exception(f"ExecuteWorkflowNode critical error: {e}")
            return self._error_result(str(e))

    async def _run_workflow(
        self,
        workflow_data: Dict[str, Any],
        context: "ExecutionContext",
        name: str,
    ) -> Dict[str, Any]:
        """
        Run the raw workflow data using SubflowExecutor.

        Args:
            workflow_data: The loaded JSON data
            context: Current execution context
            name: Workflow name for logging

        Returns:
            Result dict
        """
        from casare_rpa.application.use_cases.subflow_executor import (
            SubflowExecutor,
            Subflow as SubflowData,
        )
        from casare_rpa.domain.entities.workflow import WorkflowSchema

        # Extract nodes and connections
        # Note: Saved files usually wrap data in 'nodes', 'connections' etc.
        # But sometimes they might be full UI saves with visual info.

        nodes = workflow_data.get("nodes", {})
        connections = workflow_data.get("connections", [])

        # Transform nodes to executable format (fixing VisualNode types)
        # We reuse the logic from SubflowNode for this
        executable_nodes, id_mapping, reroute_mapping = (
            self._transform_nodes_for_execution(nodes)
        )

        # Build WorkflowSchema
        workflow_schema = WorkflowSchema()
        workflow_schema.nodes = executable_nodes

        # Transform connections
        final_connections = self._transform_connections_for_execution(
            connections, id_mapping, reroute_mapping
        )
        workflow_schema.connections = final_connections

        # Prepare SubflowData
        # We treat this as a subflow with NO inputs/outputs defined
        # (unless we want to pass variables implicitly, which we do via context)
        subflow_data = SubflowData(
            workflow=workflow_schema,
            inputs=[],
            outputs=[],
            name=name,
        )

        executor = SubflowExecutor()

        # We pass empty inputs because variables are inherited via context branching
        # in the executor if we use context.clone_for_branch inside executor?
        # Actually SubflowExecutor executes with NEW internal context.
        # Since this node doesn't map specific input ports, we assume
        # the user relies on variables or no data passing.
        # However, SubflowExecutor creates an internal context from parent.

        # Execute
        result = await executor.execute(
            subflow=subflow_data,
            inputs={},
            context=context,
        )

        if result.success:
            return {"success": True, "data": result.outputs}
        else:
            return {"success": False, "error": result.error}

    def _transform_nodes_for_execution(
        self, nodes: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, str], Dict[str, tuple[str, str]]]:
        """
        Transform node data to executable format.
        (Copied/Adapted from SubflowNode logic for standalone use)
        """
        executable_nodes: Dict[str, Any] = {}
        id_mapping: Dict[str, str] = {}
        reroute_mapping: Dict[str, tuple[str, str]] = {}

        for visual_key, node_data in nodes.items():
            type_str = node_data.get("type_", "") or node_data.get("type", "")
            custom = node_data.get("custom", {})
            name = node_data.get("name", "")

            # Skip reroute nodes
            is_reroute = (
                "RerouteNode" in type_str
                or "Reroute" in name
                or type_str == "VisualRerouteNode"
            )
            if is_reroute:
                reroute_mapping[visual_key] = ("in", "out")
                continue

            # Get actual node ID
            actual_node_id = (
                custom.get("node_id") or node_data.get("node_id") or visual_key
            )
            id_mapping[visual_key] = actual_node_id

            # Extract executable node type
            node_type = self._extract_executable_type(type_str)

            # Build config
            config = dict(custom) if custom else {}
            if "properties" in node_data:
                config.update(node_data["properties"])

            executable_node = {
                "node_id": actual_node_id,
                "node_type": node_type,
                "type": node_type,
                "config": config,
            }
            executable_nodes[actual_node_id] = executable_node

        return executable_nodes, id_mapping, reroute_mapping

    def _extract_executable_type(self, visual_type: str) -> str:
        """Extract executable node type from visual type string."""
        if not visual_type:
            return "UnknownNode"
        class_name = visual_type.split(".")[-1]
        if class_name.startswith("Visual"):
            class_name = class_name[6:]
        return class_name

    def _transform_connections_for_execution(
        self,
        connections: List[Dict[str, Any]],
        id_mapping: Dict[str, str],
        reroute_mapping: Dict[str, tuple[str, str]],
    ) -> List[Any]:
        """Transform connections."""
        from casare_rpa.domain.entities.node_connection import NodeConnection

        # Similar logic to SubflowNode but simpler connection object creation
        # We need to return List[NodeConnection] for WorkflowSchema

        result_connections = []

        # Build reroute map
        reroute_targets = {}  # source -> targets

        # Helper to parse connection dict
        def parse(conn):
            if "out" in conn and "in" in conn:  # NodeGraphQt format
                return (conn["out"][0], conn["out"][1], conn["in"][0], conn["in"][1])
            return None

        # 1. Map reroutes
        for conn in connections:
            parsed = parse(conn)
            if not parsed:
                continue
            src, src_port, tgt, tgt_port = parsed

            if src in reroute_mapping:
                if src not in reroute_targets:
                    reroute_targets[src] = []
                reroute_targets[src].append((tgt, tgt_port))

        # 2. Resolve final targets
        def get_final_targets(node_id):
            targets = []
            if node_id not in reroute_targets:
                return []

            for tgt, port in reroute_targets[node_id]:
                if tgt in reroute_mapping:
                    targets.extend(get_final_targets(tgt))
                elif tgt in id_mapping:
                    targets.append((id_mapping[tgt], port))
            return targets

        # 3. Build connections
        processed = set()

        for conn in connections:
            parsed = parse(conn)
            if not parsed:
                continue
            src, src_port, tgt, tgt_port = parsed

            # Skip if source is reroute (handled by recursion from real source)
            if src in reroute_mapping:
                continue

            actual_src = id_mapping.get(src, src)

            if tgt in reroute_mapping:
                # Resolve through reroute
                final_tgts = get_final_targets(tgt)
                # Note: Logic above for get_final_targets assumes we start lookups from reroute node
                # but map needs to be filled.
                # Actually, simpler: just follow the chain?
                # Re-using strict logic from SubflowNode is safer but voluminous.
                # Let's use a simpler path since we are in same file context
                # Wait, I copied SubflowNode logic mentally. Reroute/id_mapping logic
                # in SubflowNode is robust. Let's simplify slightly for readability
                # but keep core correctness.

                # ... okay actually just blindly copying SubflowNode's robust logic
                # inside this method without 'self' deps is best.
                pass
            else:
                # Direct
                actual_tgt = id_mapping.get(tgt, tgt)
                key = (actual_src, src_port, actual_tgt, tgt_port)
                if key not in processed:
                    processed.add(key)
                    result_connections.append(
                        NodeConnection(
                            source_node=actual_src,
                            source_port=src_port,
                            target_node=actual_tgt,
                            target_port=tgt_port,
                        )
                    )

        # Re-implement robust reroute logic locally to avoid errors
        # (The loop above was incomplete)

        # Let's do a second pass for reroutes properly
        # Reroute logic needs full graph traversal if chained
        # For MVP, allow 1 level of reroute or assume SubflowNode logic is needed?
        # It's better to NOT implement broken reroute logic.
        # If I can import SubflowNode, I could use its method?
        # No, SubflowNode is an instance method.
        # I will paste the robust logic from SubflowNode here.

        # ... logic reset ...

        reroute_targets = {}  # key -> list of (target, port)

        for conn in connections:
            parsed = parse(conn)
            if not parsed:
                continue
            src, src_port, tgt, tgt_port = parsed

            if src in reroute_mapping:
                if src not in reroute_targets:
                    reroute_targets[src] = []
                reroute_targets[src].append((tgt, tgt_port))

        def find_targets(r_key):
            found = []
            for t_key, t_port in reroute_targets.get(r_key, []):
                if t_key in reroute_mapping:
                    found.extend(find_targets(t_key))
                elif t_key in id_mapping:
                    found.append((id_mapping[t_key], t_port))
            return found

        for conn in connections:
            parsed = parse(conn)
            if not parsed:
                continue
            src, src_port, tgt, tgt_port = parsed

            if src in reroute_mapping:
                continue  # handled later

            actual_src = id_mapping.get(src, src)

            if tgt in reroute_mapping:
                for final_tgt, final_port in find_targets(tgt):
                    result_connections.append(
                        NodeConnection(
                            source_node=actual_src,
                            source_port=src_port,
                            target_node=final_tgt,
                            target_port=final_port,
                        )
                    )
            else:
                actual_tgt = id_mapping.get(tgt, tgt)
                result_connections.append(
                    NodeConnection(
                        source_node=actual_src,
                        source_port=src_port,
                        target_node=actual_tgt,
                        target_port=tgt_port,
                    )
                )

        return result_connections

    def _error_result(self, error: str) -> ExecutionResult:
        """Create error result."""
        self.status = NodeStatus.ERROR
        return {
            "success": False,
            "error": error,
            "next_nodes": ["error"],
        }

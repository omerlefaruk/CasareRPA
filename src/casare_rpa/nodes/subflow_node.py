"""
SubflowNode for CasareRPA.

Executes a subflow (reusable workflow fragment) within a parent workflow.
The subflow's internal nodes are executed as a unit, with inputs/outputs
mapped to the SubflowNode's ports.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.entities.subflow import Subflow
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
    PropertyDef(
        "subflow_id",
        PropertyType.STRING,
        default="",
        label="Subflow ID",
        tooltip="ID of the subflow to execute",
    ),
    PropertyDef(
        "subflow_path",
        PropertyType.FILE_PATH,
        default="",
        label="Subflow Path",
        tooltip="Path to subflow definition file",
        placeholder="workflows/subflows/my_subflow.json",
    ),
)
@node(exec_outputs=["exec_out", "error"])
class SubflowNode(BaseNode):
    """
    Executes a subflow (reusable workflow fragment).

    A SubflowNode encapsulates a group of nodes that have been grouped into
    a reusable unit. The subflow's inputs become the node's input ports,
    and the subflow's outputs become the node's output ports.

    During execution:
    1. Input port values are passed to the subflow's entry points
    2. The subflow's internal nodes are executed
    3. Output port values are collected from the subflow's exit points
    """

    # @category: control_flow
    # @requires: none
    # @ports: exec_in -> exec_out, error

    def __init__(
        self,
        node_id: str,
        config: dict | None = None,
        name: str = "Subflow",
        **kwargs,
    ) -> None:
        """
        Initialize SubflowNode.

        Args:
            node_id: Unique identifier for this node
            config: Node configuration containing subflow_id and/or subflow_path
            name: Display name for the node
        """
        config = config or {}
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SubflowNode"
        self._subflow: Subflow | None = None
        self._subflow_loaded = False

    def _define_ports(self) -> None:
        """
        Define node ports based on subflow definition.

        Default ports are created initially, then updated when subflow is loaded.
        """
        # Default exec ports - always present
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_exec_output("error")

        # Dynamic ports will be added when subflow is loaded
        # via configure_from_subflow()

    def configure_from_subflow(self, subflow: Subflow) -> None:
        """
        Configure node ports based on subflow definition.

        Creates input/output ports matching the subflow's interface.
        Works with both old-style (string data_type) and new-style (DataType enum) ports.
        Also builds property definitions from promoted parameters.

        Args:
            subflow: The subflow entity to configure from
        """
        self._subflow = subflow
        self._subflow_loaded = True
        self.name = f"Subflow: {subflow.name}"

        # Store subflow info in config
        self.config["subflow_id"] = subflow.id
        self.config["subflow_name"] = subflow.name

        # Clear existing data ports (keep exec ports)
        # Note: In practice, this is called during node creation
        # so there shouldn't be existing data ports to clear

        # Add input ports from subflow
        for port in subflow.inputs:
            # SubflowPort now uses DataType enum directly
            data_type = self._normalize_data_type(port.data_type)
            self.add_input_port(port.name, data_type)

        # Add output ports from subflow
        for port in subflow.outputs:
            # SubflowPort now uses DataType enum directly
            data_type = self._normalize_data_type(port.data_type)
            self.add_output_port(port.name, data_type)

        # Generate PropertyDefs from promoted parameters
        self._promoted_property_defs: list[PropertyDef] = []
        if hasattr(subflow, "parameters") and subflow.parameters:
            for param in subflow.parameters:
                prop_def = param.to_property_def()
                self._promoted_property_defs.append(prop_def)

                # Store default in config if not already set
                if param.name not in self.config:
                    self.config[param.name] = param.default_value

    def get_promoted_properties(self) -> list[PropertyDef]:
        """
        Get list of promoted property definitions for widget generation.

        Returns:
            List of PropertyDef objects for promoted parameters
        """
        return getattr(self, "_promoted_property_defs", [])

    def _normalize_data_type(self, data_type) -> DataType:
        """
        Normalize data type to DataType enum.

        Handles both DataType enum values and legacy string formats.

        Args:
            data_type: DataType enum, string like "STRING", or None

        Returns:
            Corresponding DataType enum value
        """
        # Already a DataType enum
        if isinstance(data_type, DataType):
            return data_type

        # None or empty - default to ANY
        if not data_type:
            return DataType.ANY

        # Legacy string format
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
                "BROWSER": DataType.BROWSER,
            }
            return type_map.get(data_type.upper(), DataType.ANY)

        return DataType.ANY

    def _parse_data_type(self, type_str: str | None) -> DataType:
        """
        Parse data type string to DataType enum.

        DEPRECATED: Use _normalize_data_type() instead.
        Kept for backward compatibility.

        Args:
            type_str: Type string like "STRING", "INTEGER", etc.

        Returns:
            Corresponding DataType enum value
        """
        return self._normalize_data_type(type_str)

    def _legacy_parse_data_type(self, type_str: str | None) -> DataType:
        """Legacy parser for old string-based data types."""
        if not type_str:
            return DataType.ANY

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
            "BROWSER": DataType.BROWSER,
        }

        return type_map.get(type_str.upper(), DataType.ANY)

    def _load_subflow(self) -> Subflow | None:
        """
        Load subflow from file or cache.

        Returns:
            Loaded Subflow or None if loading failed
        """
        if self._subflow_loaded and self._subflow:
            return self._subflow

        subflow_path = self.get_parameter("subflow_path", "")

        if not subflow_path:
            logger.error("SubflowNode: No subflow path configured")
            return None

        try:
            path = Path(subflow_path)
            if not path.exists():
                logger.error(f"SubflowNode: Subflow file not found: {subflow_path}")
                return None

            self._subflow = Subflow.load_from_file(str(path))
            self._subflow_loaded = True
            return self._subflow

        except Exception as e:
            logger.error(f"SubflowNode: Failed to load subflow: {e}")
            return None

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute the subflow.

        This method:
        1. Loads the subflow definition if not already loaded
        2. Creates a sub-context for subflow execution
        3. Maps input port values to subflow entry points
        4. Executes the subflow's internal nodes
        5. Maps subflow output values to output ports

        Args:
            context: Execution context from parent workflow

        Returns:
            ExecutionResult with subflow outputs
        """
        self.status = NodeStatus.RUNNING

        try:
            # Load subflow if needed
            subflow = self._load_subflow()
            if not subflow:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Subflow not loaded",
                    "error_code": "SUBFLOW_NOT_LOADED",
                    "next_nodes": ["error"],
                }

            logger.info(f"Executing subflow: {subflow.name} ({subflow.id})")

            # Create sub-context for subflow execution using clone_for_branch
            # This copies parent variables and shares browser resources
            subflow_context = context.clone_for_branch(f"subflow_{subflow.id}")

            # Map input port values to subflow context
            for input_port in subflow.inputs:
                # Skip exec ports - check by data_type or name pattern
                if input_port.data_type == DataType.EXECUTION or "exec" in input_port.name.lower():
                    continue

                port_name = input_port.name
                input_value = self.get_input_value(port_name)
                if input_value is not None:
                    # Store as variable in subflow context
                    subflow_context.variables[port_name] = input_value

            # Execute subflow nodes
            # Note: This requires the execution engine to handle subflow execution
            # For now, we delegate to the subflow executor if available
            result = await self._execute_subflow_nodes(subflow, subflow_context)

            if not result.get("success", False):
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": result.get("error", "Subflow execution failed"),
                    "error_code": result.get("error_code", "SUBFLOW_EXECUTION_FAILED"),
                    "next_nodes": ["error"],
                }

            # Map subflow outputs to node output ports
            output_data = {}
            for output_port in subflow.outputs:
                # Skip exec ports - check by data_type or name pattern
                if (
                    output_port.data_type == DataType.EXECUTION
                    or "exec" in output_port.name.lower()
                ):
                    continue

                port_name = output_port.name
                # Get value from subflow context
                output_value = subflow_context.variables.get(port_name)
                if output_value is not None:
                    self.set_output_value(port_name, output_value)
                    output_data[port_name] = output_value

            self.status = NodeStatus.SUCCESS
            logger.info(f"Subflow '{subflow.name}' completed successfully")

            return {
                "success": True,
                "data": output_data,
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"SubflowNode execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "SUBFLOW_ERROR",
                "next_nodes": ["error"],
            }

    async def _execute_subflow_nodes(
        self, subflow: Subflow, context: ExecutionContext
    ) -> dict[str, Any]:
        """
        Execute the internal nodes of a subflow.

        Uses SubflowExecutor for proper node execution with full lifecycle management.

        Args:
            subflow: The subflow to execute
            context: Execution context for the subflow

        Returns:
            Execution result dictionary
        """
        try:
            from casare_rpa.application.use_cases.subflow_executor import (
                Subflow as SubflowData,
            )
            from casare_rpa.application.use_cases.subflow_executor import (
                SubflowExecutor,
                SubflowInputDefinition,
                SubflowOutputDefinition,
            )
            from casare_rpa.domain.entities.workflow import WorkflowSchema

            # Transform NodeGraphQt format to executable format
            executable_nodes, id_mapping, reroute_mapping = self._transform_nodes_for_execution(
                subflow.nodes
            )

            # Build WorkflowSchema from transformed data
            workflow_schema = WorkflowSchema()
            workflow_schema.nodes = executable_nodes

            # Convert connections, remapping IDs and resolving reroutes
            connections = self._transform_connections_for_execution(
                subflow.connections, id_mapping, reroute_mapping
            )
            workflow_schema.connections = connections

            # Build input/output definitions
            input_defs = [
                SubflowInputDefinition(
                    name=port.name,
                    data_type=str(port.data_type.value)
                    if hasattr(port.data_type, "value")
                    else str(port.data_type),
                    required=port.required if hasattr(port, "required") else False,
                )
                for port in subflow.inputs
                if port.data_type != DataType.EXECUTION and "exec" not in port.name.lower()
            ]

            output_defs = [
                SubflowOutputDefinition(
                    name=port.name,
                    data_type=str(port.data_type.value)
                    if hasattr(port.data_type, "value")
                    else str(port.data_type),
                )
                for port in subflow.outputs
                if port.data_type != DataType.EXECUTION and "exec" not in port.name.lower()
            ]

            # Create SubflowData for executor
            subflow_data = SubflowData(
                workflow=workflow_schema,
                inputs=input_defs,
                outputs=output_defs,
                name=subflow.name,
            )

            # Collect input values from context
            inputs = {}
            for input_def in input_defs:
                value = context.variables.get(input_def.name)
                if value is not None:
                    inputs[input_def.name] = value

            # Collect promoted parameter values from config
            param_values = {}
            if hasattr(subflow, "parameters") and subflow.parameters:
                for param in subflow.parameters:
                    if param.name in self.config:
                        param_values[param.name] = self.config[param.name]

            # Execute with SubflowExecutor, passing promoted parameter values
            executor = SubflowExecutor()
            result = await executor.execute(
                subflow_data,
                inputs,
                context,
                param_values=param_values if param_values else None,
            )

            if result.success:
                # Store outputs in context
                for name, value in result.outputs.items():
                    context.variables[name] = value
                return {"success": True, "data": result.outputs}
            else:
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.error(f"Subflow node execution error: {e}")
            return {"success": False, "error": str(e)}

    def _transform_nodes_for_execution(
        self, nodes: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, str], dict[str, tuple[str, str]]]:
        """
        Transform node data to executable format.

        Handles TWO formats:
        1. NodeGraphQt format: type_ with visual class, custom.node_id
        2. Create-subflow format: type with executable class, node_id directly

        Args:
            nodes: Dict of nodes in either format

        Returns:
            Tuple of:
            - executable_nodes: Dict of nodes ready for execution
            - id_mapping: Maps visual_key -> actual_node_id
            - reroute_mapping: Maps reroute visual_key -> (input_key, output_key) for bypass
        """
        executable_nodes: dict[str, Any] = {}
        id_mapping: dict[str, str] = {}
        reroute_mapping: dict[str, tuple[str, str]] = {}

        for visual_key, node_data in nodes.items():
            # Handle both formats: "type_" (NodeGraphQt) and "type" (create_subflow)
            type_str = node_data.get("type_", "") or node_data.get("type", "")
            custom = node_data.get("custom", {})
            name = node_data.get("name", "")

            # Skip reroute nodes - they're visual-only
            # Check type string, name, and also check if it's a reroute by class pattern
            is_reroute = (
                "RerouteNode" in type_str or "Reroute" in name or type_str == "VisualRerouteNode"
            )
            if is_reroute:
                reroute_mapping[visual_key] = ("in", "out")
                logger.debug(f"Skipping reroute node: {visual_key} (type={type_str})")
                continue

            # Get actual node ID - handle both formats
            # Format 1 (NodeGraphQt): custom.node_id
            # Format 2 (create_subflow): node_id directly
            actual_node_id = custom.get("node_id") or node_data.get("node_id") or visual_key
            id_mapping[visual_key] = actual_node_id

            # Extract executable node type
            # Format 1: "casare_rpa.system.VisualMessageBoxNode" -> "MessageBoxNode"
            # Format 2: Already "MessageBoxNode"
            node_type = self._extract_executable_type(type_str)

            # Build config - merge custom with properties if available
            config = dict(custom) if custom else {}
            if "properties" in node_data:
                config.update(node_data["properties"])

            # Build executable node format
            executable_node = {
                "node_id": actual_node_id,
                "node_type": node_type,
                "type": node_type,
                "config": config,
            }

            executable_nodes[actual_node_id] = executable_node

        logger.debug(
            f"Transformed {len(executable_nodes)} nodes, "
            f"skipped {len(reroute_mapping)} reroute nodes"
        )
        return executable_nodes, id_mapping, reroute_mapping

    def _extract_executable_type(self, visual_type: str) -> str:
        """
        Extract executable node type from visual type string.

        Args:
            visual_type: Full visual type like "casare_rpa.system.VisualMessageBoxNode"

        Returns:
            Executable type like "MessageBoxNode"
        """
        if not visual_type:
            return "UnknownNode"

        # Get the class name (last part after the dot)
        class_name = visual_type.split(".")[-1]

        # Remove "Visual" prefix if present
        if class_name.startswith("Visual"):
            class_name = class_name[6:]  # Remove "Visual" prefix

        return class_name

    def _transform_connections_for_execution(
        self,
        connections: list,
        id_mapping: dict[str, str],
        reroute_mapping: dict[str, tuple[str, str]],
    ) -> list:
        """
        Transform connections, remapping IDs and resolving reroute passthrough.

        Handles TWO formats:
        1. NodeGraphQt: {"out": ["node_id", "port"], "in": ["node_id", "port"]}
        2. Create-subflow: {"source_node": "...", "source_port": "...", ...}

        Args:
            connections: List of connection dicts
            id_mapping: Maps visual_key -> actual_node_id
            reroute_mapping: Maps reroute visual_key -> (in_port, out_port)

        Returns:
            List of NodeConnection objects with resolved IDs
        """
        from casare_rpa.domain.entities.node_connection import NodeConnection

        def parse_connection(conn: dict) -> tuple:
            """Parse connection dict to (source_key, source_port, target_key, target_port)."""
            # Format 1: NodeGraphQt {"out": [...], "in": [...]}
            if "out" in conn and "in" in conn:
                out_info = conn.get("out", [])
                in_info = conn.get("in", [])
                if len(out_info) >= 2 and len(in_info) >= 2:
                    return (out_info[0], out_info[1], in_info[0], in_info[1])
                return None
            # Format 2: Create-subflow {"source_node": ..., "target_node": ...}
            elif "source_node" in conn and "target_node" in conn:
                return (
                    conn.get("source_node", ""),
                    conn.get("source_port", ""),
                    conn.get("target_node", ""),
                    conn.get("target_port", ""),
                )
            return None

        # First, build reroute resolution map (source -> target through reroutes)
        reroute_sources: dict[str, tuple[str, str]] = {}
        reroute_targets: dict[str, list] = {}

        for conn in connections:
            parsed = parse_connection(conn)
            if not parsed:
                continue

            source_key, source_port, target_key, target_port = parsed

            # Track reroute connections
            if target_key in reroute_mapping:
                reroute_sources[target_key] = (source_key, source_port)
            if source_key in reroute_mapping:
                if source_key not in reroute_targets:
                    reroute_targets[source_key] = []
                reroute_targets[source_key].append((target_key, target_port))

        # Build final connections, bypassing reroutes
        result_connections = []
        processed = set()

        def find_final_targets(reroute_key: str) -> list:
            """Recursively find non-reroute targets."""
            targets = []
            for t_key, t_port in reroute_targets.get(reroute_key, []):
                if t_key in reroute_mapping:
                    targets.extend(find_final_targets(t_key))
                elif t_key in id_mapping:
                    targets.append((id_mapping[t_key], t_port))
            return targets

        for conn in connections:
            parsed = parse_connection(conn)
            if not parsed:
                continue

            source_key, source_port, target_key, target_port = parsed

            # Skip if source is reroute (handled when processing its input)
            if source_key in reroute_mapping:
                continue

            # Resolve source node ID
            actual_source = id_mapping.get(source_key, source_key)

            # Skip if target is reroute (resolve through it)
            if target_key in reroute_mapping:
                for actual_target, actual_target_port in find_final_targets(target_key):
                    conn_key = (
                        actual_source,
                        source_port,
                        actual_target,
                        actual_target_port,
                    )
                    if conn_key not in processed:
                        processed.add(conn_key)
                        result_connections.append(
                            NodeConnection(
                                source_node=actual_source,
                                source_port=source_port,
                                target_node=actual_target,
                                target_port=actual_target_port,
                            )
                        )
            else:
                # Direct connection (no reroutes)
                actual_target = id_mapping.get(target_key, target_key)

                conn_key = (actual_source, source_port, actual_target, target_port)
                if conn_key not in processed:
                    processed.add(conn_key)
                    result_connections.append(
                        NodeConnection(
                            source_node=actual_source,
                            source_port=source_port,
                            target_node=actual_target,
                            target_port=target_port,
                        )
                    )

        logger.debug(f"Transformed {len(connections)} connections to {len(result_connections)}")
        return result_connections

    def get_subflow(self) -> Subflow | None:
        """
        Get the loaded subflow.

        Returns:
            The Subflow instance or None
        """
        if not self._subflow_loaded:
            self._load_subflow()
        return self._subflow

    def __repr__(self) -> str:
        """String representation."""
        subflow_name = self._subflow.name if self._subflow else "not loaded"
        return f"SubflowNode(id='{self.node_id}', subflow='{subflow_name}')"

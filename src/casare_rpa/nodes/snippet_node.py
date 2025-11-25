"""
CasareRPA - Snippet Node
Container node that executes snippet subgraphs with parameter binding and variable scoping.
"""

from typing import Any, Dict, Optional
from loguru import logger

from ..core.base_node import BaseNode
from ..core.types import DataType, ExecutionResult, NodeId
from ..core.execution_context import ExecutionContext
from ..core.snippet_definition import SnippetDefinition, ParameterMapping
from ..runner.subgraph_runner import SubgraphRunner


class SnippetNode(BaseNode):
    """
    Container node for executing snippet subgraphs.

    Features:
    - Dynamic port creation based on snippet parameters
    - Isolated execution context for subgraph
    - Parameter binding to internal node configurations
    - Variable scope management (inheritance and export)
    - Support for both collapsed and expanded modes
    """

    def __init__(self, node_id: NodeId, config: Optional[Dict[str, Any]] = None):
        """
        Initialize snippet node.

        Args:
            node_id: Unique node identifier
            config: Node configuration including snippet_id
        """
        # Initialize with empty snippet_definition first
        self.snippet_definition: Optional[SnippetDefinition] = None
        self.is_collapsed: bool = True

        # Call parent constructor
        super().__init__(node_id, config)

        # Override metadata
        self.category = "Snippets"
        self.description = "Reusable snippet container"

        logger.debug(f"SnippetNode {node_id} initialized")

    def _define_ports(self) -> None:
        """
        Dynamically create ports based on snippet parameters.

        Called during __init__ and when snippet_definition changes.
        """
        # Clear existing ports (for when snippet definition changes)
        self.input_ports.clear()
        self.output_ports.clear()

        # Always add execution ports
        self.add_input_port("exec_in", DataType.ANY, "Execution Input", required=False)
        self.add_output_port("exec_out", DataType.ANY, "Execution Output")

        # Add parameter ports if snippet is loaded
        if self.snippet_definition:
            for param in self.snippet_definition.parameters:
                self.add_input_port(
                    param.snippet_param_name,
                    param.param_type,
                    label=param.description,
                    required=param.required,
                )

            # Update description
            self.description = self.snippet_definition.description or "Reusable snippet"

            logger.debug(
                f"Created {len(self.snippet_definition.parameters)} parameter ports "
                f"for snippet '{self.snippet_definition.name}'"
            )

    def set_snippet_definition(self, definition: SnippetDefinition):
        """
        Set or update the snippet definition.

        This will recreate ports based on the new definition.

        Args:
            definition: SnippetDefinition to use
        """
        self.snippet_definition = definition

        # Recreate ports
        self._define_ports()

        # Store snippet_id in config for serialization
        self.config["snippet_id"] = definition.snippet_id
        self.config["snippet_name"] = definition.name

        logger.info(f"Snippet definition set: {definition.name} (v{definition.version})")

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute snippet subgraph with isolated context.

        Process:
        1. Create child execution context
        2. Instantiate internal nodes
        3. Bind parameters to internal node configs
        4. Execute subgraph using SubgraphRunner
        5. Export variables based on scope config

        Args:
            context: Parent execution context

        Returns:
            Execution result dictionary
        """
        if not self.snippet_definition:
            error = "No snippet definition loaded"
            logger.error(f"SnippetNode {self.node_id}: {error}")
            return {"success": False, "error": error}

        logger.info(
            f"Executing snippet '{self.snippet_definition.name}' "
            f"with {len(self.snippet_definition.nodes)} internal nodes"
        )

        try:
            # 1. Create child execution context
            child_context = self._create_child_context(context)

            # 2. Instantiate internal nodes
            internal_nodes = self._instantiate_internal_nodes()

            # 3. Bind parameters to internal node configs
            self._bind_parameters(internal_nodes)

            # 4. Execute subgraph
            runner = SubgraphRunner(
                nodes=internal_nodes,
                connections=self.snippet_definition.connections,
                entry_nodes=self.snippet_definition.entry_node_ids,
                exit_nodes=self.snippet_definition.exit_node_ids,
            )

            result = await runner.execute(child_context)

            # 5. Export variables back to parent context
            self._export_variables(context, child_context)

            # Return execution result
            if result.success:
                logger.info(
                    f"Snippet '{self.snippet_definition.name}' executed successfully"
                )
                return {
                    "success": True,
                    "data": result.exit_node_results,
                    "next_nodes": ["exec_out"],
                }
            else:
                logger.error(
                    f"Snippet '{self.snippet_definition.name}' execution failed: {result.error}"
                )
                return {"success": False, "error": result.error}

        except Exception as e:
            logger.exception(
                f"Exception in snippet '{self.snippet_definition.name}': {e}"
            )
            return {"success": False, "error": str(e)}

    def _create_child_context(self, parent_context: ExecutionContext) -> ExecutionContext:
        """
        Create child execution context based on variable scope configuration.

        Args:
            parent_context: Parent workflow context

        Returns:
            New child context with appropriate variable inheritance
        """
        scope = self.snippet_definition.variable_scope

        # Determine initial variables for child context
        if scope.inherit_parent_scope:
            # Copy parent variables
            initial_vars = parent_context.variables.copy()
        else:
            # Start with empty variables
            initial_vars = {}

        # Apply input mappings (parent var -> snippet var)
        for parent_var, snippet_var in scope.input_mappings.items():
            if parent_context.has_variable(parent_var):
                initial_vars[snippet_var] = parent_context.get_variable(parent_var)

        # Create child context
        child_context = ExecutionContext(
            workflow_name=f"Snippet: {self.snippet_definition.name}",
            mode=parent_context.mode,
            initial_variables=initial_vars,
        )

        # Share browser resources (not isolated)
        child_context.browser = parent_context.browser
        child_context.browser_contexts = parent_context.browser_contexts
        child_context.pages = parent_context.pages
        child_context.active_page = parent_context.active_page

        logger.debug(
            f"Created child context with {len(initial_vars)} initial variables"
        )

        return child_context

    def _instantiate_internal_nodes(self) -> Dict[NodeId, BaseNode]:
        """
        Instantiate internal node instances from serialized data.

        Returns:
            Dictionary mapping node_id to BaseNode instance
        """
        # Import here to avoid circular dependency
        from ..utils.workflow_loader import NODE_TYPE_MAP

        nodes = {}

        for node_id, node_data in self.snippet_definition.nodes.items():
            node_type = node_data.get("node_type")
            config = node_data.get("config", {})

            # Get node class from registry
            node_class = NODE_TYPE_MAP.get(node_type)

            if not node_class:
                logger.warning(
                    f"Unknown node type '{node_type}' in snippet, skipping"
                )
                continue

            # Create node instance
            try:
                node_instance = node_class(node_id, config=config)
                nodes[node_id] = node_instance
                logger.debug(f"Instantiated internal node: {node_id} ({node_type})")
            except Exception as e:
                logger.error(f"Failed to instantiate node {node_id}: {e}")

        logger.info(
            f"Instantiated {len(nodes)} internal nodes for snippet '{self.snippet_definition.name}'"
        )

        return nodes

    def _bind_parameters(self, internal_nodes: Dict[NodeId, BaseNode]):
        """
        Apply parameter values to internal node configurations.

        Reads values from snippet's input ports and writes them to
        internal node configs based on parameter mappings.

        Args:
            internal_nodes: Dictionary of internal node instances
        """
        for param in self.snippet_definition.parameters:
            # Get value from input port or use default
            value = self.get_input_value(param.snippet_param_name)

            if value is None:
                value = param.default_value

            # Apply to target node's config
            target_node = internal_nodes.get(param.target_node_id)

            if target_node:
                target_node.config[param.target_config_key] = value
                logger.debug(
                    f"Parameter binding: {param.snippet_param_name}={value} -> "
                    f"{param.target_node_id}.config['{param.target_config_key}']"
                )
            else:
                logger.warning(
                    f"Target node '{param.target_node_id}' not found for parameter '{param.snippet_param_name}'"
                )

    def _export_variables(
        self, parent_context: ExecutionContext, child_context: ExecutionContext
    ):
        """
        Export variables from child context back to parent based on scope config.

        Args:
            parent_context: Parent workflow context
            child_context: Child snippet context
        """
        scope = self.snippet_definition.variable_scope

        if scope.export_local_vars:
            # Export all variables (except isolated ones)
            for var_name, var_value in child_context.variables.items():
                if var_name not in scope.isolated_vars:
                    parent_context.set_variable(var_name, var_value)
                    logger.debug(f"Exported variable: {var_name}")

        # Apply output mappings (snippet var -> parent var)
        for snippet_var, parent_var in scope.output_mappings.items():
            if child_context.has_variable(snippet_var):
                value = child_context.get_variable(snippet_var)
                parent_context.set_variable(parent_var, value)
                logger.debug(
                    f"Output mapping: {snippet_var} -> {parent_var} = {value}"
                )

    def _validate_config(self) -> tuple[bool, Optional[str]]:
        """
        Validate snippet node configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if snippet_id is in config
        if "snippet_id" not in self.config:
            return False, "Snippet ID not specified in config"

        # Check if snippet definition is loaded
        if not self.snippet_definition:
            return False, "Snippet definition not loaded"

        # Validate that entry and exit nodes exist
        for entry_id in self.snippet_definition.entry_node_ids:
            if entry_id not in self.snippet_definition.nodes:
                return False, f"Entry node '{entry_id}' not found in snippet"

        for exit_id in self.snippet_definition.exit_node_ids:
            if exit_id not in self.snippet_definition.nodes:
                return False, f"Exit node '{exit_id}' not found in snippet"

        return True, None

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize snippet node to dictionary.

        Returns:
            Dictionary containing node data
        """
        data = super().serialize()

        # Add snippet-specific data
        if self.snippet_definition:
            data["snippet_id"] = self.snippet_definition.snippet_id
            data["snippet_name"] = self.snippet_definition.name
            data["snippet_version"] = self.snippet_definition.version

        data["is_collapsed"] = self.is_collapsed

        return data

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "SnippetNode":
        """
        Create snippet node from serialized data.

        Note: This creates the node but does not load the snippet definition.
        The snippet definition must be loaded separately using set_snippet_definition().

        Args:
            data: Serialized node dictionary

        Returns:
            SnippetNode instance
        """
        node_id = data["node_id"]
        config = data.get("config", {})

        node = cls(node_id, config)
        node.is_collapsed = data.get("is_collapsed", True)

        # Note: Snippet definition must be loaded separately
        # This is typically done by the workflow loader or canvas

        return node

    def __repr__(self) -> str:
        """String representation."""
        snippet_name = (
            self.snippet_definition.name if self.snippet_definition else "Not Loaded"
        )
        return (
            f"SnippetNode(id='{self.node_id}', snippet='{snippet_name}', "
            f"collapsed={self.is_collapsed})"
        )

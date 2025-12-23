"""
CasareRPA - Qt-Based Workflow Validation Service.

Validates workflows against actual Qt visual node definitions to ensure:
- All node types exist and are registered
- All port names match the actual node port definitions
- All connections are valid (source port exists, target port exists, types match)
- Loop structures are properly connected (ForLoop, WhileLoop, Try/Catch/Finally)

This validator uses the actual visual node classes to validate port names,
ensuring AI-generated workflows will work correctly when loaded.

Usage:
    from casare_rpa.domain.services.workflow_validator import (
        WorkflowValidator,
        validate_workflow_with_qt,
    )

    validator = WorkflowValidator()
    result = validator.validate(workflow_dict)

    if not result.is_valid:
        for error in result.errors:
            print(f"ERROR: {error}")
"""

from __future__ import annotations

import re
import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    pass


# =============================================================================
# VALIDATION RESULT
# =============================================================================


@dataclass
class ValidationIssue:
    """A single validation issue (error or warning)."""

    code: str
    message: str
    location: str | None = None
    suggestion: str | None = None
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        loc = f" at {self.location}" if self.location else ""
        sug = f" (Suggestion: {self.suggestion})" if self.suggestion else ""
        return f"[{self.code}]{loc}: {self.message}{sug}"


@dataclass
class ValidationResult:
    """Result of workflow validation."""

    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    node_count: int = 0
    connection_count: int = 0
    validated_nodes: set[str] = field(default_factory=set)

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def add_error(
        self,
        code: str,
        message: str,
        location: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add an error."""
        self.errors.append(ValidationIssue(code, message, location, suggestion, "error"))

    def add_warning(
        self,
        code: str,
        message: str,
        location: str | None = None,
        suggestion: str | None = None,
    ) -> None:
        """Add a warning."""
        self.warnings.append(ValidationIssue(code, message, location, suggestion, "warning"))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [str(e) for e in self.errors],
            "warnings": [str(w) for w in self.warnings],
            "node_count": self.node_count,
            "connection_count": self.connection_count,
        }


# =============================================================================
# PORT DEFINITIONS FROM VISUAL NODES
# =============================================================================


# Known port definitions for control flow nodes
# These are extracted from the actual visual node classes
CONTROL_FLOW_PORTS = {
    "IfNode": {
        "inputs": ["exec_in", "condition"],
        "outputs": ["true", "false"],
    },
    "TryNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out", "try_body"],
    },
    "CatchNode": {
        "inputs": ["exec_in"],
        "outputs": ["catch_body", "error_message", "error_type", "stack_trace"],
    },
    "FinallyNode": {
        "inputs": ["exec_in"],
        "outputs": ["finally_body", "had_error"],
    },
    "ForLoopStartNode": {
        "inputs": ["exec_in", "items", "end"],
        "outputs": [
            "body",
            "completed",
            "current_item",
            "current_index",
            "current_key",
        ],
    },
    "ForLoopEndNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out"],
    },
    "WhileLoopStartNode": {
        "inputs": ["exec_in", "condition"],
        "outputs": ["body", "completed", "current_iteration"],
    },
    "WhileLoopEndNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out"],
    },
    "ForkNode": {
        "inputs": ["exec_in"],
        "outputs": ["branch_1", "branch_2", "branch_3", "branch_4"],
    },
    "JoinNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out", "results", "branch_count"],
    },
    "MergeNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out"],
    },
    "SwitchNode": {
        "inputs": ["exec_in", "value"],
        "outputs": ["default", "case_0", "case_1", "case_2", "case_3", "case_4", "case_5"],
    },
    "ComparisonNode": {
        "inputs": ["exec_in", "a", "b"],
        "outputs": ["exec_out", "result"],
    },
    "CreateListNode": {
        "inputs": ["exec_in", "item_1", "item_2", "item_3"],
        "outputs": ["exec_out", "list"],
    },
    "JsonParseNode": {
        "inputs": ["exec_in", "json_string"],
        "outputs": ["exec_out", "data"],
    },
    "BreakNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out"],
    },
    "ContinueNode": {
        "inputs": ["exec_in"],
        "outputs": ["exec_out"],
    },
}

# Standard node ports (most nodes follow this pattern)
STANDARD_PORTS = {
    "inputs": ["exec_in"],
    "outputs": ["exec_out"],
}

# Nodes with additional data ports
DATA_OUTPUT_NODES = {
    "WaitForElementNode": ["page", "element", "found"],
    "ExtractTextNode": ["text", "page"],
    "ExtractAttributeNode": ["value", "page"],
    "GetVariableNode": ["value"],
    "ReadFileNode": ["content"],
    "HttpRequestNode": ["response", "status_code", "headers"],
    "ScreenshotNode": ["screenshot_path", "page"],
    "NavigateNode": ["page"],
    "GoToURLNode": ["page"],
    "LaunchBrowserNode": ["page", "browser"],
    "CloseBrowserNode": [],
    "TooltipNode": [],
    "ComparisonNode": ["result"],
    "CreateListNode": ["list"],
    "ListGetItemNode": ["item"],
    "JsonParseNode": ["data"],
    "RandomNumberNode": ["number"],
    "RandomChoiceNode": ["choice"],
    "RandomStringNode": ["string"],
    "RandomUUIDNode": ["uuid"],
}

# Nodes with additional data inputs
DATA_INPUT_NODES = {
    "TypeTextNode": ["page", "element"],
    "ClickElementNode": ["page", "element"],
    "WaitForElementNode": ["page"],
    "SetVariableNode": ["value"],
    "WriteFileNode": ["content"],
    "IfNode": ["condition"],  # Note: VisualIfNode uses "condition" input
    "GoToURLNode": ["page"],  # Can accept page as input
    "ExtractTextNode": ["page"],  # Can accept page as input
    "ScreenshotNode": ["page"],  # Can accept page as input
    "TooltipNode": ["message"],  # Message input for dynamic content
    "CloseBrowserNode": ["page"],  # Browser page to close
    "ComparisonNode": ["a", "b"],
    "CreateListNode": ["item_1", "item_2", "item_3"],
    "ListGetItemNode": ["list", "index"],
    "JsonParseNode": ["json_string"],
    "RandomNumberNode": ["min", "max"],
    "RandomChoiceNode": ["items"],
    "RandomStringNode": ["length", "charset"],
    "RandomUUIDNode": [],
}

# =============================================================================
# DATA-ONLY NODES (no exec_in/exec_out ports)
# =============================================================================
# These nodes are pure data transformers without execution flow ports.
# They receive data through typed input ports and produce results on typed outputs.
# The execution engine handles them specially - they execute when their outputs
# are needed by downstream nodes.

DATA_ONLY_NODES = {
    # JSON/Dict operations
    "GetPropertyNode": {
        "inputs": ["object", "property_path"],
        "outputs": ["value"],
    },
}


# =============================================================================
# WORKFLOW VALIDATOR
# =============================================================================


class WorkflowValidator:
    """
    Validates workflows against actual Qt visual node definitions.

    This validator ensures that:
    1. All node types are valid and registered
    2. All port names match the actual node definitions
    3. All connections are valid
    4. Loop structures are properly connected
    """

    def __init__(self) -> None:
        """Initialize the validator."""
        self._visual_node_registry: dict[str, type] | None = None
        self._port_cache: dict[str, dict[str, list[str]]] = {}
        logger.debug("WorkflowValidator initialized")

    def _load_visual_node_registry(self) -> dict[str, type]:
        """Load the visual node registry."""
        if self._visual_node_registry is not None:
            return self._visual_node_registry

        try:
            from casare_rpa.presentation.canvas.graph.node_registry import (
                get_all_node_types,
                get_visual_class_for_type,
            )

            # Build registry by fetching visual class for each node type
            self._visual_node_registry = {}
            for node_type in get_all_node_types():
                visual_class = get_visual_class_for_type(node_type)
                if visual_class is not None:
                    self._visual_node_registry[node_type] = visual_class

            logger.debug(
                f"Loaded visual node registry with {len(self._visual_node_registry)} nodes"
            )
        except ImportError as e:
            logger.warning(f"Could not load visual node registry: {e}")
            self._visual_node_registry = {}
        except Exception as e:
            logger.error(f"Error loading visual node registry: {e}")
            self._visual_node_registry = {}

        return self._visual_node_registry

    def _get_node_ports(self, node_type: str) -> dict[str, list[str]]:
        """
        Get the valid input and output ports for a node type.

        Args:
            node_type: The node type (e.g., "IfNode", "TryNode")

        Returns:
            Dict with "inputs" and "outputs" lists
        """
        # Check cache first
        if node_type in self._port_cache:
            return self._port_cache[node_type]

        # Check control flow special ports
        if node_type in CONTROL_FLOW_PORTS:
            ports = CONTROL_FLOW_PORTS[node_type]
            self._port_cache[node_type] = ports
            return ports

        # Check data-only nodes (no exec_in/exec_out ports)
        if node_type in DATA_ONLY_NODES:
            ports = DATA_ONLY_NODES[node_type]
            self._port_cache[node_type] = ports
            return ports

        # Try to get ports from actual visual node class
        registry = self._load_visual_node_registry()
        if node_type in registry:
            try:
                node_class = registry[node_type]
                ports = self._extract_ports_from_class(node_class)
                self._port_cache[node_type] = ports
                return ports
            except Exception as e:
                logger.debug(f"Could not extract ports from {node_type}: {e}")

        # Build standard ports with known additions
        inputs = list(STANDARD_PORTS["inputs"])
        outputs = list(STANDARD_PORTS["outputs"])

        # Try to get ports from backend node class (schema-driven)
        backend_ports = self._extract_ports_from_backend_node(node_type)
        if backend_ports:
            # Merge with standard ports
            for inp in backend_ports.get("inputs", []):
                if inp not in inputs:
                    inputs.append(inp)
            for out in backend_ports.get("outputs", []):
                if out not in outputs:
                    outputs.append(out)
            ports = {"inputs": inputs, "outputs": outputs}
            self._port_cache[node_type] = ports
            return ports

        # Add known data outputs
        if node_type in DATA_OUTPUT_NODES:
            outputs.extend(DATA_OUTPUT_NODES[node_type])

        # Add known data inputs
        if node_type in DATA_INPUT_NODES:
            inputs.extend(DATA_INPUT_NODES[node_type])

        ports = {"inputs": inputs, "outputs": outputs}
        self._port_cache[node_type] = ports
        return ports

    def _extract_ports_from_backend_node(self, node_type: str) -> dict[str, list[str]] | None:
        """
        Extract port definitions from backend node class using live instantiation.

        This is the most reliable method as it uses the actual node's _define_ports().
        Also extracts property names from @properties schema for dual-source validation.

        Args:
            node_type: The node type (e.g., "ClickElementNode")

        Returns:
            Dict with "inputs", "outputs", and "properties" lists, or None if failed
        """
        try:
            # Import the node class from registry
            import importlib

            from casare_rpa.nodes.registry_data import NODE_REGISTRY

            if node_type not in NODE_REGISTRY:
                return None

            module_info = NODE_REGISTRY[node_type]
            if isinstance(module_info, tuple):
                module_path, class_alias = module_info
            else:
                module_path = module_info
                class_alias = node_type

            full_module = f"casare_rpa.nodes.{module_path}"
            module = importlib.import_module(full_module)
            node_class = getattr(module, class_alias, None)

            if node_class is None:
                return None

            # Instantiate to get ports
            instance = node_class(node_id="__validator_temp")

            inputs = []
            outputs = []

            for name, _port in instance.input_ports.items():
                inputs.append(name)

            for name, _port in instance.output_ports.items():
                outputs.append(name)

            # Also get property names from schema (for dual-source validation)
            properties = []
            schema = getattr(node_class, "__node_schema__", None)
            if schema:
                properties = [p.name for p in schema.properties]

            return {
                "inputs": inputs,
                "outputs": outputs,
                "properties": properties,
            }

        except Exception as e:
            logger.debug(f"Could not extract ports from backend node {node_type}: {e}")
            return None

    def _extract_ports_from_class(self, node_class: type) -> dict[str, list[str]]:
        """
        Extract port definitions from node class without instantiating.

        Analyzes the setup_ports method source code to extract port names.

        Args:
            node_class: The visual node class

        Returns:
            Dict with "inputs" and "outputs" lists
        """
        try:
            import inspect
            import re

            # Try to get the setup_ports method source
            if hasattr(node_class, "setup_ports"):
                source = inspect.getsource(node_class.setup_ports)

                inputs = []
                outputs = []

                # Parse add_exec_input/add_typed_input calls WITH explicit arguments
                input_patterns = [
                    r'add_exec_input\(["\'](\w+)["\']',
                    r'add_typed_input\(["\'](\w+)["\']',
                    r'add_input\(["\'](\w+)["\']',
                ]
                for pattern in input_patterns:
                    inputs.extend(re.findall(pattern, source))

                # Parse add_exec_output/add_typed_output calls WITH explicit arguments
                output_patterns = [
                    r'add_exec_output\(["\'](\w+)["\']',
                    r'add_typed_output\(["\'](\w+)["\']',
                    r'add_output\(["\'](\w+)["\']',
                ]
                for pattern in output_patterns:
                    outputs.extend(re.findall(pattern, source))

                # CRITICAL: Detect add_exec_input() and add_exec_output() WITHOUT arguments
                # These use default port names "exec_in" and "exec_out"
                # Match add_exec_input( ) or add_exec_input() - no string argument inside parens
                if re.search(r"add_exec_input\s*\(\s*\)", source):
                    if "exec_in" not in inputs:
                        inputs.append("exec_in")

                if re.search(r"add_exec_output\s*\(\s*\)", source):
                    if "exec_out" not in outputs:
                        outputs.append("exec_out")

                if inputs or outputs:
                    return {"inputs": inputs, "outputs": outputs}

            # Fallback to default ports
            return {"inputs": ["exec_in"], "outputs": ["exec_out"]}

        except Exception as e:
            logger.debug(f"Could not extract ports from class: {e}")
            return {"inputs": ["exec_in"], "outputs": ["exec_out"]}

    def validate(self, workflow_dict: dict[str, Any]) -> ValidationResult:
        """
        Validate a workflow dictionary.

        Args:
            workflow_dict: The workflow dictionary to validate

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()
        logger.debug("Starting workflow validation...")

        try:
            # Validate basic structure
            self._validate_structure(workflow_dict, result)

            if result.errors:
                # Don't continue if structure is invalid
                return result

            nodes = workflow_dict.get("nodes", {})
            connections = workflow_dict.get("connections", [])

            result.node_count = len(nodes)
            result.connection_count = len(connections)

            # Validate each node
            for node_id, node_data in nodes.items():
                self._validate_node(node_id, node_data, result)

            # Validate each connection
            for idx, conn in enumerate(connections):
                self._validate_connection(idx, conn, nodes, result)

            # Validate loop structures
            self._validate_loop_structures(nodes, connections, result)

            # Validate Try/Catch/Finally structures
            self._validate_try_catch_structures(nodes, connections, result)

            logger.debug(
                f"Validation complete: {len(result.errors)} errors, "
                f"{len(result.warnings)} warnings"
            )

        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            logger.debug(traceback.format_exc())
            result.add_error(
                "VALIDATION_EXCEPTION",
                f"Validation failed: {e}",
                suggestion="Check workflow structure",
            )

        return result

    def _validate_structure(self, workflow_dict: dict[str, Any], result: ValidationResult) -> None:
        """Validate basic workflow structure."""
        if not isinstance(workflow_dict, dict):
            result.add_error(
                "INVALID_STRUCTURE",
                "Workflow must be a dictionary",
            )
            return

        if "nodes" not in workflow_dict:
            result.add_error(
                "MISSING_NODES",
                "Workflow must have a 'nodes' field",
            )

        if "connections" not in workflow_dict:
            result.add_warning(
                "MISSING_CONNECTIONS",
                "Workflow has no 'connections' field",
                suggestion="Add connections to link nodes",
            )

    def _validate_node(
        self,
        node_id: str,
        node_data: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate a single node."""
        # Check node_id matches key
        if node_data.get("node_id") != node_id:
            result.add_error(
                "NODE_ID_MISMATCH",
                f"Node ID in data ({node_data.get('node_id')}) doesn't match key ({node_id})",
                location=f"node:{node_id}",
                suggestion="Ensure node_id field matches the dictionary key",
            )

        # Check node_type
        node_type = node_data.get("node_type")
        if not node_type:
            result.add_error(
                "MISSING_NODE_TYPE",
                "Node is missing node_type",
                location=f"node:{node_id}",
            )
            return

        # Validate node_type format
        if not re.match(r"^[A-Z][a-zA-Z0-9]*Node$", node_type):
            result.add_warning(
                "INVALID_NODE_TYPE_FORMAT",
                f"Node type '{node_type}' should be PascalCase ending with 'Node'",
                location=f"node:{node_id}",
            )

        result.validated_nodes.add(node_id)

    def _validate_connection(
        self,
        idx: int,
        conn: dict[str, Any],
        nodes: dict[str, Any],
        result: ValidationResult,
    ) -> None:
        """Validate a single connection."""
        source_node = conn.get("source_node")
        source_port = conn.get("source_port")
        target_node = conn.get("target_node")
        target_port = conn.get("target_port")

        location = f"connection:{idx}"

        # Check source node exists
        if source_node not in nodes:
            result.add_error(
                "INVALID_SOURCE_NODE",
                f"Source node '{source_node}' does not exist",
                location=location,
                suggestion=f"Add node '{source_node}' or fix the connection",
            )
            return

        # Check target node exists
        if target_node not in nodes:
            result.add_error(
                "INVALID_TARGET_NODE",
                f"Target node '{target_node}' does not exist",
                location=location,
                suggestion=f"Add node '{target_node}' or fix the connection",
            )
            return

        # Get node types
        source_type = nodes[source_node].get("node_type", "")
        target_type = nodes[target_node].get("node_type", "")

        # Validate source port
        if source_port:
            source_ports = self._get_node_ports(source_type)
            valid_outputs = source_ports.get("outputs", [])

            if valid_outputs and source_port not in valid_outputs:
                result.add_error(
                    "INVALID_SOURCE_PORT",
                    f"Port '{source_port}' is not a valid output of {source_type}",
                    location=f"{location} ({source_node}.{source_port})",
                    suggestion=f"Valid outputs: {', '.join(valid_outputs)}",
                )

        # Validate target port
        if target_port:
            target_ports = self._get_node_ports(target_type)
            valid_inputs = target_ports.get("inputs", [])

            if valid_inputs and target_port not in valid_inputs:
                result.add_error(
                    "INVALID_TARGET_PORT",
                    f"Port '{target_port}' is not a valid input of {target_type}",
                    location=f"{location} ({target_node}.{target_port})",
                    suggestion=f"Valid inputs: {', '.join(valid_inputs)}",
                )

    def _validate_loop_structures(
        self,
        nodes: dict[str, Any],
        connections: list[dict[str, Any]],
        result: ValidationResult,
    ) -> None:
        """Validate loop structures (ForLoop, WhileLoop)."""
        # Find ForLoopStart nodes
        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type", "")

            if node_type == "ForLoopStartNode":
                # Check that 'body' output is connected
                body_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "body"
                    for c in connections
                )

                if not body_connected:
                    result.add_warning(
                        "LOOP_BODY_NOT_CONNECTED",
                        f"ForLoopStartNode '{node_id}' has no 'body' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'body' output to the loop body nodes",
                    )

            elif node_type == "WhileLoopStartNode":
                body_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "body"
                    for c in connections
                )

                if not body_connected:
                    result.add_warning(
                        "LOOP_BODY_NOT_CONNECTED",
                        f"WhileLoopStartNode '{node_id}' has no 'body' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'body' output to the loop body nodes",
                    )

    def _validate_try_catch_structures(
        self,
        nodes: dict[str, Any],
        connections: list[dict[str, Any]],
        result: ValidationResult,
    ) -> None:
        """Validate Try/Catch/Finally structures."""
        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type", "")

            if node_type == "TryNode":
                # Check that 'try_body' output is connected
                try_body_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "try_body"
                    for c in connections
                )

                if not try_body_connected:
                    result.add_warning(
                        "TRY_BODY_NOT_CONNECTED",
                        f"TryNode '{node_id}' has no 'try_body' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'try_body' to the operations that should be tried",
                    )

            elif node_type == "CatchNode":
                # Check that 'catch_body' output is connected
                catch_body_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "catch_body"
                    for c in connections
                )

                if not catch_body_connected:
                    result.add_warning(
                        "CATCH_BODY_NOT_CONNECTED",
                        f"CatchNode '{node_id}' has no 'catch_body' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'catch_body' to error handling operations",
                    )

            elif node_type == "FinallyNode":
                # Check that 'finally_body' output is connected
                finally_body_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "finally_body"
                    for c in connections
                )

                if not finally_body_connected:
                    result.add_warning(
                        "FINALLY_BODY_NOT_CONNECTED",
                        f"FinallyNode '{node_id}' has no 'finally_body' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'finally_body' to cleanup operations",
                    )

            elif node_type == "IfNode":
                # Check that both 'true' and 'false' outputs are connected
                true_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "true"
                    for c in connections
                )
                false_connected = any(
                    c.get("source_node") == node_id and c.get("source_port") == "false"
                    for c in connections
                )

                if not true_connected:
                    result.add_warning(
                        "IF_TRUE_NOT_CONNECTED",
                        f"IfNode '{node_id}' has no 'true' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'true' output to the true branch",
                    )

                if not false_connected:
                    result.add_warning(
                        "IF_FALSE_NOT_CONNECTED",
                        f"IfNode '{node_id}' has no 'false' output connection",
                        location=f"node:{node_id}",
                        suggestion="Connect 'false' output to the false branch or a Merge node",
                    )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def validate_workflow_with_qt(workflow_dict: dict[str, Any]) -> ValidationResult:
    """
    Validate a workflow dictionary using Qt visual node definitions.

    Args:
        workflow_dict: The workflow dictionary to validate

    Returns:
        ValidationResult with any issues found
    """
    validator = WorkflowValidator()
    return validator.validate(workflow_dict)


def get_valid_ports_for_node(node_type: str) -> dict[str, list[str]]:
    """
    Get the valid input and output ports for a node type.

    Args:
        node_type: The node type (e.g., "IfNode", "TryNode")

    Returns:
        Dict with "inputs" and "outputs" lists
    """
    validator = WorkflowValidator()
    return validator._get_node_ports(node_type)


__all__ = [
    "WorkflowValidator",
    "ValidationResult",
    "ValidationIssue",
    "validate_workflow_with_qt",
    "get_valid_ports_for_node",
]

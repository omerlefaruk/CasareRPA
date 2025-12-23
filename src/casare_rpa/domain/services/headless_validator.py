"""
Headless Workflow Sandbox for validating AI-generated workflow JSON.

This module provides validation of workflow JSON without rendering UI,
using existing node registries to verify node types, configs, and connections.

Entry Points:
    - HeadlessWorkflowSandbox: Main validator class
    - WorkflowValidationResult: Validation outcome with errors/warnings
    - WorkflowValidationError: Structured error information

Key Patterns:
    - Uses NODE_REGISTRY for node type validation
    - Uses _VISUAL_NODE_REGISTRY for visual node validation
    - Uses WorkflowAISchema for schema validation
    - Provides LLM-friendly error messages with suggestions

Related:
    - casare_rpa.nodes.registry_data.NODE_REGISTRY: Executable node registry
    - casare_rpa.presentation.canvas.visual_nodes._VISUAL_NODE_REGISTRY: Visual registry
    - casare_rpa.domain.schemas.workflow_ai.WorkflowAISchema: Schema validation
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from loguru import logger


@dataclass
class WorkflowValidationError:
    """Structured validation error with LLM-friendly suggestions."""

    error_type: str  # REGISTRY_ERROR, INIT_ERROR, PORT_ERROR, TYPE_MISMATCH
    node_id: str
    message: str
    suggestion: str

    def __str__(self) -> str:
        return f"[{self.error_type}] {self.node_id}: {self.message}"


@dataclass
class WorkflowValidationResult:
    """Result of headless workflow validation."""

    success: bool
    errors: List[WorkflowValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_nodes: int = 0
    validated_connections: int = 0

    def add_error(
        self,
        error_type: str,
        node_id: str,
        message: str,
        suggestion: str = "",
    ) -> None:
        """Add a validation error."""
        self.errors.append(
            WorkflowValidationError(
                error_type=error_type,
                node_id=node_id,
                message=message,
                suggestion=suggestion,
            )
        )
        self.success = False

    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)


class HeadlessWorkflowSandbox:
    """
    Validates workflow JSON without rendering UI.

    Uses existing node registries to validate:
    1. Node types exist in registry
    2. Node configs have required parameters
    3. Connections reference valid ports
    4. Port type compatibility

    Example:
        validator = HeadlessWorkflowSandbox()
        result = validator.validate_workflow(workflow_json)
        if not result.success:
            for error in result.errors:
                print(f"{error.error_type}: {error.message}")
                print(f"  Suggestion: {error.suggestion}")
    """

    def __init__(self) -> None:
        """Initialize validator with node registries."""
        self._node_registry: Optional[Dict[str, Any]] = None
        self._visual_registry: Optional[Dict[str, str]] = None
        self._node_classes_cache: Dict[str, Type] = {}
        self._node_ports_cache: Dict[str, Dict[str, Any]] = {}

    def _get_node_registry(self) -> Dict[str, Any]:
        """Lazy load node registry."""
        if self._node_registry is None:
            try:
                from casare_rpa.nodes.registry_data import NODE_REGISTRY

                self._node_registry = NODE_REGISTRY
            except ImportError as e:
                logger.warning(f"Could not import node registry: {e}")
                self._node_registry = {}
        return self._node_registry

    def _get_visual_registry(self) -> Dict[str, str]:
        """Lazy load visual node registry."""
        if self._visual_registry is None:
            try:
                from casare_rpa.presentation.canvas.visual_nodes import (
                    _VISUAL_NODE_REGISTRY,
                )

                self._visual_registry = _VISUAL_NODE_REGISTRY
            except ImportError as e:
                logger.warning(f"Could not import visual node registry: {e}")
                self._visual_registry = {}
        return self._visual_registry

    def _get_node_class(self, node_type: str) -> Optional[Type]:
        """Get node class from registry with caching."""
        if node_type in self._node_classes_cache:
            return self._node_classes_cache[node_type]

        registry = self._get_node_registry()
        if node_type not in registry:
            return None

        try:
            from casare_rpa.nodes import get_node_class

            cls = get_node_class(node_type)
            self._node_classes_cache[node_type] = cls
            return cls
        except Exception as e:
            logger.debug(f"Could not load node class {node_type}: {e}")
            return None

    def _get_node_ports(self, node_type: str) -> Dict[str, Any]:
        """
        Get port definitions for a node type.

        Returns dict with:
            - input_ports: Dict[name, port_info]
            - output_ports: Dict[name, port_info]
        """
        if node_type in self._node_ports_cache:
            return self._node_ports_cache[node_type]

        ports = {"input_ports": {}, "output_ports": {}}

        node_cls = self._get_node_class(node_type)
        if node_cls is None:
            return ports

        try:
            # Create temporary instance to get port definitions
            temp_node = node_cls(node_id="__temp__", config={})
            ports["input_ports"] = {
                name: {
                    "port_type": str(port.port_type),
                    "data_type": str(port.data_type),
                }
                for name, port in temp_node.input_ports.items()
            }
            ports["output_ports"] = {
                name: {
                    "port_type": str(port.port_type),
                    "data_type": str(port.data_type),
                }
                for name, port in temp_node.output_ports.items()
            }
        except Exception as e:
            logger.debug(f"Could not instantiate {node_type} for port info: {e}")

        self._node_ports_cache[node_type] = ports
        return ports

    def _get_nodes_by_category(self) -> Dict[str, List[str]]:
        """Group node types by category for suggestions."""
        registry = self._get_node_registry()
        categories: Dict[str, List[str]] = {}

        for node_type, module_path in registry.items():
            if isinstance(module_path, tuple):
                module_path = module_path[0]

            # Extract category from module path
            if "." in module_path:
                category = module_path.split(".")[0]
            else:
                category = module_path.replace("_nodes", "")

            # Normalize category names
            category_map = {
                "basic": "basic",
                "browser": "browser",
                "navigation": "browser",
                "interaction": "browser",
                "data": "browser",
                "wait": "browser",
                "control_flow": "control_flow",
                "parallel": "control_flow",
                "error_handling": "error_handling",
                "data_operation": "data_operation",
                "utility": "utility",
                "file": "file",
                "email": "email",
                "http": "http",
                "database": "database",
                "random": "utility",
                "datetime": "utility",
                "text": "text",
                "system": "system",
                "script": "script",
                "xml": "xml",
                "pdf": "pdf",
                "ftp": "ftp",
                "llm": "ai",
                "document": "document",
                "trigger": "trigger",
                "google": "google",
                "messaging": "messaging",
                "desktop": "desktop",
            }

            normalized = category_map.get(category, category)
            if normalized not in categories:
                categories[normalized] = []
            categories[normalized].append(node_type)

        return categories

    def _suggest_similar_nodes(self, invalid_type: str) -> str:
        """Generate suggestion for invalid node type."""
        registry = self._get_node_registry()

        # Try to find similar node names
        invalid_lower = invalid_type.lower()
        similar = []

        for node_type in registry.keys():
            node_lower = node_type.lower()
            # Check for substring matches
            if invalid_lower in node_lower or node_lower in invalid_lower:
                similar.append(node_type)
            # Check for common prefix/suffix
            elif (
                invalid_lower.replace("node", "") in node_lower
                or node_lower.replace("node", "") in invalid_lower
            ):
                similar.append(node_type)

        if similar:
            return f"Did you mean: {', '.join(similar[:5])}?"

        # No similar nodes found, suggest by category
        categories = self._get_nodes_by_category()

        # Try to guess category from name
        category_hints = {
            "click": "browser",
            "type": "browser",
            "navigate": "browser",
            "browser": "browser",
            "page": "browser",
            "if": "control_flow",
            "loop": "control_flow",
            "for": "control_flow",
            "while": "control_flow",
            "file": "file",
            "read": "file",
            "write": "file",
            "http": "http",
            "api": "http",
            "email": "email",
            "database": "database",
            "sql": "database",
        }

        for hint, category in category_hints.items():
            if hint in invalid_lower:
                nodes = categories.get(category, [])[:5]
                if nodes:
                    return f"Available {category} nodes: {', '.join(nodes)}..."
                break

        return "Check available node types in the node registry."

    def _suggest_port_names(self, node_type: str, invalid_port: str) -> str:
        """Generate suggestion for invalid port name."""
        ports = self._get_node_ports(node_type)
        all_ports = list(ports["input_ports"].keys()) + list(ports["output_ports"].keys())

        if all_ports:
            return f"Valid ports for {node_type}: {', '.join(all_ports)}"
        return f"Could not determine valid ports for {node_type}."

    def validate_workflow(self, workflow_json: Dict[str, Any]) -> WorkflowValidationResult:
        """
        Validate workflow JSON structure and contents.

        Args:
            workflow_json: Workflow dictionary to validate

        Returns:
            WorkflowValidationResult with errors, warnings, and statistics
        """
        result = WorkflowValidationResult(success=True)

        # Step 0: Schema validation
        schema_errors = self._validate_schema(workflow_json, result)
        if schema_errors:
            return result

        # Extract nodes and connections
        nodes = workflow_json.get("nodes", {})
        connections = workflow_json.get("connections", [])

        # Step 1: Validate node types exist
        self._validate_node_types(nodes, result)

        # Step 2: Validate node configs
        self._validate_node_configs(nodes, result)

        # Step 3: Validate connections reference valid ports
        self._validate_connection_ports(nodes, connections, result)

        # Step 4: Validate port type compatibility
        self._validate_port_compatibility(nodes, connections, result)

        # Update statistics
        result.validated_nodes = len(nodes)
        result.validated_connections = len(connections)

        return result

    def _validate_schema(
        self, workflow_json: Dict[str, Any], result: WorkflowValidationResult
    ) -> bool:
        """
        Validate workflow against Pydantic schema.

        Returns True if there are errors, False if valid.
        """
        try:
            from casare_rpa.domain.schemas.workflow_ai import WorkflowAISchema

            is_valid, error_msg = WorkflowAISchema.validate_ai_output(workflow_json)
            if not is_valid:
                result.add_error(
                    error_type="SCHEMA_ERROR",
                    node_id="workflow",
                    message=f"Schema validation failed: {error_msg}",
                    suggestion="Ensure workflow follows WorkflowAISchema structure.",
                )
                return True
        except ImportError:
            result.add_warning("Could not import WorkflowAISchema for validation")
        except Exception as e:
            result.add_error(
                error_type="SCHEMA_ERROR",
                node_id="workflow",
                message=f"Schema validation error: {e}",
                suggestion="Check workflow JSON structure.",
            )
            return True
        return False

    def _validate_node_types(self, nodes: Dict[str, Any], result: WorkflowValidationResult) -> None:
        """Validate all node types exist in registry."""
        registry = self._get_node_registry()

        for node_id, node_data in nodes.items():
            # Handle both dict and object formats
            if isinstance(node_data, dict):
                node_type = node_data.get("node_type", "")
            else:
                node_type = getattr(node_data, "node_type", "")

            if not node_type:
                result.add_error(
                    error_type="REGISTRY_ERROR",
                    node_id=node_id,
                    message="Node type not specified",
                    suggestion="Each node must have a 'node_type' field.",
                )
                continue

            if node_type not in registry:
                suggestion = self._suggest_similar_nodes(node_type)
                result.add_error(
                    error_type="REGISTRY_ERROR",
                    node_id=node_id,
                    message=f"Node type '{node_type}' not found in registry",
                    suggestion=suggestion,
                )

    def _validate_node_configs(
        self, nodes: Dict[str, Any], result: WorkflowValidationResult
    ) -> None:
        """Validate node configs can initialize nodes."""
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                node_type = node_data.get("node_type", "")
                config = node_data.get("config", {})
            else:
                node_type = getattr(node_data, "node_type", "")
                config = getattr(node_data, "config", {})

            node_cls = self._get_node_class(node_type)
            if node_cls is None:
                continue  # Already reported in type validation

            try:
                # Try to instantiate node with config
                test_node = node_cls(node_id=node_id, config=config)
                # Run node's own validation
                is_valid, error_msg = test_node.validate()
                if not is_valid:
                    result.add_error(
                        error_type="INIT_ERROR",
                        node_id=node_id,
                        message=f"Node validation failed: {error_msg}",
                        suggestion="Check required config parameters for this node type.",
                    )
            except TypeError as e:
                result.add_error(
                    error_type="INIT_ERROR",
                    node_id=node_id,
                    message=f"Invalid config for {node_type}: {e}",
                    suggestion="Check constructor parameters for this node type.",
                )
            except Exception as e:
                result.add_error(
                    error_type="INIT_ERROR",
                    node_id=node_id,
                    message=f"Could not initialize {node_type}: {e}",
                    suggestion="Verify node config matches expected schema.",
                )

    def _validate_connection_ports(
        self,
        nodes: Dict[str, Any],
        connections: List[Dict[str, str]],
        result: WorkflowValidationResult,
    ) -> None:
        """Validate connections reference valid ports."""
        node_types = {}
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                node_types[node_id] = node_data.get("node_type", "")
            else:
                node_types[node_id] = getattr(node_data, "node_type", "")

        for idx, conn in enumerate(connections):
            if isinstance(conn, dict):
                source_node = conn.get("source_node", "")
                source_port = conn.get("source_port", "")
                target_node = conn.get("target_node", "")
                target_port = conn.get("target_port", "")
            else:
                source_node = getattr(conn, "source_node", "")
                source_port = getattr(conn, "source_port", "")
                target_node = getattr(conn, "target_node", "")
                target_port = getattr(conn, "target_port", "")

            conn_id = f"connection_{idx}"

            # Validate source port
            if source_node in node_types:
                source_type = node_types[source_node]
                ports = self._get_node_ports(source_type)
                if source_port not in ports["output_ports"]:
                    suggestion = self._suggest_port_names(source_type, source_port)
                    result.add_error(
                        error_type="PORT_ERROR",
                        node_id=conn_id,
                        message=(
                            f"Output port '{source_port}' not found on "
                            f"{source_type} ({source_node})"
                        ),
                        suggestion=suggestion,
                    )

            # Validate target port
            if target_node in node_types:
                target_type = node_types[target_node]
                ports = self._get_node_ports(target_type)
                if target_port not in ports["input_ports"]:
                    suggestion = self._suggest_port_names(target_type, target_port)
                    result.add_error(
                        error_type="PORT_ERROR",
                        node_id=conn_id,
                        message=(
                            f"Input port '{target_port}' not found on "
                            f"{target_type} ({target_node})"
                        ),
                        suggestion=suggestion,
                    )

    def _validate_port_compatibility(
        self,
        nodes: Dict[str, Any],
        connections: List[Dict[str, str]],
        result: WorkflowValidationResult,
    ) -> None:
        """Validate port type compatibility for connections."""
        node_types = {}
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                node_types[node_id] = node_data.get("node_type", "")
            else:
                node_types[node_id] = getattr(node_data, "node_type", "")

        for idx, conn in enumerate(connections):
            if isinstance(conn, dict):
                source_node = conn.get("source_node", "")
                source_port = conn.get("source_port", "")
                target_node = conn.get("target_node", "")
                target_port = conn.get("target_port", "")
            else:
                source_node = getattr(conn, "source_node", "")
                source_port = getattr(conn, "source_port", "")
                target_node = getattr(conn, "target_node", "")
                target_port = getattr(conn, "target_port", "")

            conn_id = f"connection_{idx}"

            source_type = node_types.get(source_node, "")
            target_type = node_types.get(target_node, "")

            if not source_type or not target_type:
                continue

            source_ports = self._get_node_ports(source_type)
            target_ports = self._get_node_ports(target_type)

            source_info = source_ports["output_ports"].get(source_port, {})
            target_info = target_ports["input_ports"].get(target_port, {})

            if not source_info or not target_info:
                continue

            source_port_type = source_info.get("port_type", "")
            target_port_type = target_info.get("port_type", "")

            # Check exec port compatibility
            is_source_exec = "EXEC" in source_port_type.upper()
            is_target_exec = "EXEC" in target_port_type.upper()

            if is_source_exec != is_target_exec:
                result.add_error(
                    error_type="TYPE_MISMATCH",
                    node_id=conn_id,
                    message=(
                        f"Port type mismatch: {source_port} ({source_port_type}) -> "
                        f"{target_port} ({target_port_type})"
                    ),
                    suggestion=(
                        "Connect exec_out to exec_in for flow control, "
                        "and data ports to data ports for values."
                    ),
                )

    def get_available_node_types(self) -> List[str]:
        """Get list of all available node types."""
        return list(self._get_node_registry().keys())

    def get_node_port_info(self, node_type: str) -> Dict[str, Any]:
        """Get port information for a specific node type."""
        return self._get_node_ports(node_type)

    def get_nodes_by_category(self) -> Dict[str, List[str]]:
        """Get node types grouped by category."""
        return self._get_nodes_by_category()


__all__ = [
    "HeadlessWorkflowSandbox",
    "WorkflowValidationResult",
    "WorkflowValidationError",
]

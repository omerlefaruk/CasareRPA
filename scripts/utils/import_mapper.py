"""
Import mapping configuration for v2.x to v3.0 migration.

This module provides the ImportMapper class that maps deprecated import paths
from the v2.x compatibility layer (core/, visual_nodes.py) to their new
canonical locations in the domain, infrastructure, and presentation layers.

Usage:
    from scripts.utils.import_mapper import ImportMapper

    # Map a module path
    new_path = ImportMapper.map_module("casare_rpa.core.types")
    # Returns: "casare_rpa.domain.value_objects.types"

    # Map a specific name from a module
    new_module, new_name = ImportMapper.map_name("casare_rpa.core.base_node", "Port")
    # Returns: ("casare_rpa.domain.value_objects.port", "Port")
"""

from typing import Dict, List, Optional, Set, Tuple


class ImportMapper:
    """
    Maps deprecated v2.x imports to their v3.0 canonical locations.

    Provides both module-level mappings (for entire module redirects) and
    name-specific mappings (for ambiguous names that need special handling).
    """

    # Module-level mappings: old_module -> new_module
    # These handle the common case where an entire module is relocated
    MODULE_MAPPINGS: Dict[str, str] = {
        # Core types -> Domain value objects
        "casare_rpa.core.types": "casare_rpa.domain.value_objects.types",
        # Core base_node -> Domain entities (most symbols)
        # Note: Port is handled specially in NAME_MAPPINGS
        "casare_rpa.core.base_node": "casare_rpa.domain.entities.base_node",
        # Core workflow_schema -> Domain entities
        "casare_rpa.core.workflow_schema": "casare_rpa.domain.entities.workflow",
        # Core execution_context -> Infrastructure (facade remains in core for now)
        "casare_rpa.core.execution_context": "casare_rpa.core.execution_context",
        # Core package root -> Domain root (fallback for direct core imports)
        "casare_rpa.core": "casare_rpa.domain",
        # Visual nodes monolith (if it exists) -> organized visual_nodes package
        "casare_rpa.presentation.canvas.visual_nodes.visual_nodes": (
            "casare_rpa.presentation.canvas.visual_nodes"
        ),
        # Legacy node wrapper modules (re-export wrappers)
        "casare_rpa.nodes.file_nodes": "casare_rpa.nodes.file",
        "casare_rpa.nodes.http_nodes": "casare_rpa.nodes.http",
        "casare_rpa.nodes.database_nodes": "casare_rpa.nodes.database",
    }

    # Name-specific mappings: (old_module, name) -> (new_module, new_name)
    # Used for names that exist in multiple locations or need special routing
    NAME_MAPPINGS: Dict[Tuple[str, str], Tuple[str, str]] = {
        # Port class is in domain.value_objects.port, not domain.entities.base_node
        ("casare_rpa.core", "Port"): (
            "casare_rpa.domain.value_objects.port",
            "Port",
        ),
        ("casare_rpa.core.base_node", "Port"): (
            "casare_rpa.domain.value_objects.port",
            "Port",
        ),
        # BaseNode stays in domain.entities.base_node but accessed from core
        ("casare_rpa.core", "BaseNode"): (
            "casare_rpa.domain.entities.base_node",
            "BaseNode",
        ),
        # WorkflowSchema and related from core root
        ("casare_rpa.core", "WorkflowSchema"): (
            "casare_rpa.domain.entities.workflow",
            "WorkflowSchema",
        ),
        ("casare_rpa.core", "WorkflowMetadata"): (
            "casare_rpa.domain.entities.workflow_metadata",
            "WorkflowMetadata",
        ),
        ("casare_rpa.core", "NodeConnection"): (
            "casare_rpa.domain.entities.node_connection",
            "NodeConnection",
        ),
        ("casare_rpa.core", "VariableDefinition"): (
            "casare_rpa.domain.entities.workflow",
            "VariableDefinition",
        ),
        # workflow_schema module special cases
        ("casare_rpa.core.workflow_schema", "WorkflowMetadata"): (
            "casare_rpa.domain.entities.workflow_metadata",
            "WorkflowMetadata",
        ),
        ("casare_rpa.core.workflow_schema", "NodeConnection"): (
            "casare_rpa.domain.entities.node_connection",
            "NodeConnection",
        ),
        ("casare_rpa.core.workflow_schema", "VariableDefinition"): (
            "casare_rpa.domain.entities.workflow",
            "VariableDefinition",
        ),
        # Type aliases and enums from core root -> domain.value_objects.types
        ("casare_rpa.core", "DataType"): (
            "casare_rpa.domain.value_objects.types",
            "DataType",
        ),
        ("casare_rpa.core", "NodeStatus"): (
            "casare_rpa.domain.value_objects.types",
            "NodeStatus",
        ),
        ("casare_rpa.core", "PortType"): (
            "casare_rpa.domain.value_objects.types",
            "PortType",
        ),
        ("casare_rpa.core", "ExecutionMode"): (
            "casare_rpa.domain.value_objects.types",
            "ExecutionMode",
        ),
        ("casare_rpa.core", "EventType"): (
            "casare_rpa.domain.value_objects.types",
            "EventType",
        ),
        ("casare_rpa.core", "ErrorCode"): (
            "casare_rpa.domain.value_objects.types",
            "ErrorCode",
        ),
        ("casare_rpa.core", "NodeId"): (
            "casare_rpa.domain.value_objects.types",
            "NodeId",
        ),
        ("casare_rpa.core", "PortId"): (
            "casare_rpa.domain.value_objects.types",
            "PortId",
        ),
        ("casare_rpa.core", "Connection"): (
            "casare_rpa.domain.value_objects.types",
            "Connection",
        ),
        ("casare_rpa.core", "NodeConfig"): (
            "casare_rpa.domain.value_objects.types",
            "NodeConfig",
        ),
        ("casare_rpa.core", "ExecutionResult"): (
            "casare_rpa.domain.value_objects.types",
            "ExecutionResult",
        ),
        ("casare_rpa.core", "SerializedNode"): (
            "casare_rpa.domain.value_objects.types",
            "SerializedNode",
        ),
        ("casare_rpa.core", "SerializedWorkflow"): (
            "casare_rpa.domain.value_objects.types",
            "SerializedWorkflow",
        ),
        ("casare_rpa.core", "SCHEMA_VERSION"): (
            "casare_rpa.domain.value_objects.types",
            "SCHEMA_VERSION",
        ),
        # ExecutionContext stays in core for now (facade pattern)
        ("casare_rpa.core", "ExecutionContext"): (
            "casare_rpa.core.execution_context",
            "ExecutionContext",
        ),
        # Event system stays in core (not yet migrated to domain)
        ("casare_rpa.core", "Event"): (
            "casare_rpa.core.events",
            "Event",
        ),
        ("casare_rpa.core", "EventBus"): (
            "casare_rpa.core.events",
            "EventBus",
        ),
        ("casare_rpa.core", "get_event_bus"): (
            "casare_rpa.core.events",
            "get_event_bus",
        ),
        # Validation stays in core (not yet migrated)
        ("casare_rpa.core", "ValidationResult"): (
            "casare_rpa.core.validation",
            "ValidationResult",
        ),
        ("casare_rpa.core", "validate_workflow"): (
            "casare_rpa.core.validation",
            "validate_workflow",
        ),
    }

    # Names that are known to exist in deprecated modules
    # Used for validation and star import expansion
    DEPRECATED_MODULE_EXPORTS: Dict[str, Set[str]] = {
        "casare_rpa.core.types": {
            "DataType",
            "NodeStatus",
            "PortType",
            "ExecutionMode",
            "EventType",
            "ErrorCode",
            "NodeId",
            "PortId",
            "Connection",
            "NodeConfig",
            "ExecutionResult",
            "PortDefinition",
            "SerializedNode",
            "SerializedFrame",
            "SerializedWorkflow",
            "EventData",
            "SCHEMA_VERSION",
            "DEFAULT_TIMEOUT",
            "MAX_RETRIES",
            "EXEC_IN_PORT",
            "EXEC_OUT_PORT",
        },
        "casare_rpa.core.base_node": {
            "BaseNode",
            "Port",
        },
        "casare_rpa.core.workflow_schema": {
            "WorkflowSchema",
            "WorkflowMetadata",
            "NodeConnection",
            "VariableDefinition",
            "SCHEMA_VERSION",
        },
        "casare_rpa.core": {
            "DataType",
            "NodeStatus",
            "PortType",
            "ExecutionMode",
            "EventType",
            "NodeId",
            "PortId",
            "Connection",
            "NodeConfig",
            "ExecutionResult",
            "SerializedNode",
            "SerializedWorkflow",
            "SCHEMA_VERSION",
            "BaseNode",
            "Port",
            "WorkflowSchema",
            "WorkflowMetadata",
            "NodeConnection",
            "ExecutionContext",
            "Event",
            "EventBus",
            "get_event_bus",
            "reset_event_bus",
            "ValidationResult",
            "ValidationIssue",
            "ValidationSeverity",
            "validate_workflow",
            "validate_node",
            "validate_connections",
            "quick_validate",
        },
    }

    @classmethod
    def map_module(cls, old_module: str) -> str:
        """
        Map a deprecated module path to its new location.

        Args:
            old_module: The deprecated module path (e.g., "casare_rpa.core.types")

        Returns:
            The new module path, or the original if no mapping exists

        Examples:
            >>> ImportMapper.map_module("casare_rpa.core.types")
            "casare_rpa.domain.value_objects.types"

            >>> ImportMapper.map_module("casare_rpa.nodes.browser")
            "casare_rpa.nodes.browser"  # No change needed
        """
        # Exact match first (most specific)
        if old_module in cls.MODULE_MAPPINGS:
            return cls.MODULE_MAPPINGS[old_module]

        # Prefix match for submodules (e.g., casare_rpa.core.types.extra)
        for old_prefix, new_prefix in sorted(
            cls.MODULE_MAPPINGS.items(),
            key=lambda x: len(x[0]),
            reverse=True,  # Longest prefix first
        ):
            if old_module.startswith(old_prefix + "."):
                suffix = old_module[len(old_prefix) :]
                return new_prefix + suffix

        # No mapping found - return unchanged
        return old_module

    @classmethod
    def map_name(cls, old_module: str, name: str) -> Tuple[str, str]:
        """
        Map a specific name import to its new location.

        Handles cases where a name needs to go to a different module than
        the default module mapping would suggest (e.g., Port from base_node
        goes to value_objects.port, not entities.base_node).

        Args:
            old_module: The deprecated module path
            name: The name being imported

        Returns:
            Tuple of (new_module, new_name). Name is usually unchanged.

        Examples:
            >>> ImportMapper.map_name("casare_rpa.core.base_node", "Port")
            ("casare_rpa.domain.value_objects.port", "Port")

            >>> ImportMapper.map_name("casare_rpa.core.base_node", "BaseNode")
            ("casare_rpa.domain.entities.base_node", "BaseNode")
        """
        key = (old_module, name)

        # Check for specific name mapping
        if key in cls.NAME_MAPPINGS:
            return cls.NAME_MAPPINGS[key]

        # Fall back to module mapping with same name
        new_module = cls.map_module(old_module)
        return (new_module, name)

    @classmethod
    def is_deprecated_module(cls, module: str) -> bool:
        """
        Check if a module path is deprecated.

        Args:
            module: Module path to check

        Returns:
            True if module should be migrated

        Examples:
            >>> ImportMapper.is_deprecated_module("casare_rpa.core.types")
            True

            >>> ImportMapper.is_deprecated_module("casare_rpa.domain.value_objects.types")
            False
        """
        deprecated_prefixes = (
            "casare_rpa.core",
            "casare_rpa.presentation.canvas.visual_nodes.visual_nodes",
            "casare_rpa.nodes.file_nodes",
            "casare_rpa.nodes.http_nodes",
            "casare_rpa.nodes.database_nodes",
        )
        return any(module.startswith(prefix) for prefix in deprecated_prefixes)

    @classmethod
    def get_module_exports(cls, module: str) -> Set[str]:
        """
        Get known exports for a deprecated module (for star import expansion).

        Args:
            module: Deprecated module path

        Returns:
            Set of known export names, empty if module unknown

        Examples:
            >>> ImportMapper.get_module_exports("casare_rpa.core.types")
            {"DataType", "NodeStatus", "PortType", ...}
        """
        return cls.DEPRECATED_MODULE_EXPORTS.get(module, set())

    @classmethod
    def validate_mappings(cls) -> List[str]:
        """
        Validate internal consistency of mappings.

        Returns:
            List of validation errors (empty if valid)
        """
        errors: List[str] = []

        # Check that all NAME_MAPPINGS modules exist in MODULE_MAPPINGS
        # or are the new canonical modules
        for (old_mod, name), (new_mod, _) in cls.NAME_MAPPINGS.items():
            if not cls.is_deprecated_module(old_mod):
                errors.append(
                    f"NAME_MAPPINGS key ({old_mod}, {name}) "
                    f"is not from a deprecated module"
                )

        # Check for duplicate mappings that might cause confusion
        seen_targets: Dict[Tuple[str, str], Tuple[str, str]] = {}
        for key, value in cls.NAME_MAPPINGS.items():
            if value in seen_targets.values():
                for other_key, other_value in seen_targets.items():
                    if other_value == value and other_key != key:
                        # This is OK - multiple old locations can map to same new location
                        pass

        return errors


def test_import_mapper() -> None:
    """
    Run basic tests on ImportMapper.

    This function can be run directly to verify mappings:
        python scripts/utils/import_mapper.py
    """
    print("Testing ImportMapper...")

    # Test module mappings
    test_cases = [
        ("casare_rpa.core.types", "casare_rpa.domain.value_objects.types"),
        ("casare_rpa.core.base_node", "casare_rpa.domain.entities.base_node"),
        ("casare_rpa.core.workflow_schema", "casare_rpa.domain.entities.workflow"),
        ("casare_rpa.core", "casare_rpa.domain"),
        ("casare_rpa.nodes.file_nodes", "casare_rpa.nodes.file"),
        ("casare_rpa.nodes.browser", "casare_rpa.nodes.browser"),  # No change
    ]

    print("\n1. Module Mappings:")
    for old, expected in test_cases:
        result = ImportMapper.map_module(old)
        status = "OK" if result == expected else "FAIL"
        print(f"   [{status}] {old} -> {result}")
        if result != expected:
            print(f"        Expected: {expected}")

    # Test name mappings
    name_cases = [
        (
            ("casare_rpa.core.base_node", "Port"),
            ("casare_rpa.domain.value_objects.port", "Port"),
        ),
        (
            ("casare_rpa.core.base_node", "BaseNode"),
            ("casare_rpa.domain.entities.base_node", "BaseNode"),
        ),
        (
            ("casare_rpa.core", "DataType"),
            ("casare_rpa.domain.value_objects.types", "DataType"),
        ),
        (
            ("casare_rpa.core.workflow_schema", "WorkflowMetadata"),
            ("casare_rpa.domain.entities.workflow_metadata", "WorkflowMetadata"),
        ),
    ]

    print("\n2. Name Mappings:")
    for (old_mod, name), (exp_mod, exp_name) in name_cases:
        result = ImportMapper.map_name(old_mod, name)
        status = "OK" if result == (exp_mod, exp_name) else "FAIL"
        print(f"   [{status}] ({old_mod}, {name}) -> {result}")
        if result != (exp_mod, exp_name):
            print(f"        Expected: ({exp_mod}, {exp_name})")

    # Test deprecated module detection
    print("\n3. Deprecated Module Detection:")
    deprecated_cases = [
        ("casare_rpa.core.types", True),
        ("casare_rpa.core", True),
        ("casare_rpa.domain.value_objects.types", False),
        ("casare_rpa.nodes.file_nodes", True),
        ("casare_rpa.nodes.file", False),
    ]
    for mod, expected in deprecated_cases:
        result = ImportMapper.is_deprecated_module(mod)
        status = "OK" if result == expected else "FAIL"
        print(f"   [{status}] {mod} -> {result}")

    # Validate internal consistency
    print("\n4. Internal Validation:")
    errors = ImportMapper.validate_mappings()
    if errors:
        for err in errors:
            print(f"   [FAIL] {err}")
    else:
        print("   [OK] All mappings are internally consistent")

    print("\nDone.")


if __name__ == "__main__":
    test_import_mapper()

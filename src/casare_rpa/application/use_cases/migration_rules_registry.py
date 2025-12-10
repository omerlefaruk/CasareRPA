"""
CasareRPA - Migration Rules Registry
Handles registration and retrieval of node migration rules/transformers.
"""

import threading
from typing import Callable, Dict, List, Optional, Tuple, Union
from loguru import logger

from casare_rpa.domain.workflow.versioning import SemanticVersion, WorkflowVersion

# Type aliases
JsonValue = Union[
    str, int, float, bool, None, List["JsonValue"], Dict[str, "JsonValue"]
]
WorkflowData = Dict[str, JsonValue]
NodeData = Dict[str, JsonValue]


class NodeMigrationRule:
    """
    Rule for migrating a specific node type between versions.

    Used to define how nodes should be transformed when their
    schema changes between versions.
    """

    def __init__(
        self,
        node_type: str,
        from_version_range: Tuple[str, str],  # (min, max) inclusive
        to_version_range: Tuple[str, str],
        transformer: Callable[[NodeData], NodeData],
        description: str = "",
    ) -> None:
        """
        Initialize migration rule.

        Args:
            node_type: Type of node this rule applies to
            from_version_range: (min_version, max_version) for source
            to_version_range: (min_version, max_version) for target
            transformer: Function to transform node data
            description: Human-readable description
        """
        self.node_type = node_type
        self.from_min = SemanticVersion.parse(from_version_range[0])
        self.from_max = SemanticVersion.parse(from_version_range[1])
        self.to_min = SemanticVersion.parse(to_version_range[0])
        self.to_max = SemanticVersion.parse(to_version_range[1])
        self.transformer = transformer
        self.description = description

    def applies_to(
        self, node_type: str, from_version: SemanticVersion, to_version: SemanticVersion
    ) -> bool:
        """Check if this rule applies to the given migration."""
        if node_type != self.node_type:
            return False
        if not (self.from_min <= from_version <= self.from_max):
            return False
        if not (self.to_min <= to_version <= self.to_max):
            return False
        return True


class MigrationRuleRegistry:
    """Registry of node migration rules."""

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._rules: List[NodeMigrationRule] = []

    def register(self, rule: NodeMigrationRule) -> None:
        """Register a migration rule."""
        self._rules.append(rule)
        logger.debug(
            f"Registered migration rule for {rule.node_type}: {rule.description}"
        )

    def find_rules(
        self, node_type: str, from_version: SemanticVersion, to_version: SemanticVersion
    ) -> List[NodeMigrationRule]:
        """Find all applicable rules for a migration."""
        return [
            r for r in self._rules if r.applies_to(node_type, from_version, to_version)
        ]


# Module-level singleton with thread-safe lazy initialization
_rule_registry_instance: Optional[MigrationRuleRegistry] = None
_rule_registry_lock = threading.Lock()


def _get_registry_singleton() -> MigrationRuleRegistry:
    """Get or create the registry singleton with double-checked locking."""
    _local_instance = _rule_registry_instance
    if _local_instance is None:
        with _rule_registry_lock:
            _local_instance = _rule_registry_instance
            if _local_instance is None:
                _local_instance = MigrationRuleRegistry()
                globals()["_rule_registry_instance"] = _local_instance
    return _local_instance


def get_rule_registry() -> MigrationRuleRegistry:
    """Get the migration rule registry."""
    return _get_registry_singleton()


def reset_rule_registry() -> None:
    """
    Reset the migration rule registry (for testing).

    Clears the singleton so it will be recreated on next access.
    """
    with _rule_registry_lock:
        globals()["_rule_registry_instance"] = None


def register_migration_rule(
    node_type: str,
    from_version_range: Tuple[str, str],
    to_version_range: Tuple[str, str],
    description: str = "",
) -> Callable:
    """
    Decorator to register a node migration rule.

    Example:
        @register_migration_rule("NavigateNode", ("1.0.0", "1.9.9"), ("2.0.0", "2.9.9"))
        def migrate_navigate_v1_to_v2(node_data: NodeData) -> NodeData:
            # Transform node data
            return transformed_data
    """

    def decorator(
        func: Callable[[NodeData], NodeData],
    ) -> Callable[[NodeData], NodeData]:
        rule = NodeMigrationRule(
            node_type=node_type,
            from_version_range=from_version_range,
            to_version_range=to_version_range,
            transformer=func,
            description=description,
        )
        get_rule_registry().register(rule)
        return func

    return decorator

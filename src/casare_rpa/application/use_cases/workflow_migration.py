"""
CasareRPA - Application Use Case: Workflow Migration
Handles version migration, compatibility checking, and rollback operations.

Coordinates:
- Domain: VersionHistory, WorkflowVersion, VersionDiff
- Domain: Breaking change detection and compatibility validation
- Infrastructure: Database persistence for versions
- Application: Event emission for migration progress
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
import copy

# Type aliases for workflow migration
JsonValue = Union[
    str, int, float, bool, None, List["JsonValue"], Dict[str, "JsonValue"]
]
WorkflowData = Dict[str, JsonValue]
NodeData = Dict[str, JsonValue]

from loguru import logger

from casare_rpa.domain.workflow.versioning import (
    SemanticVersion,
    WorkflowVersion,
    VersionHistory,
    VersionDiff,
    CompatibilityResult,
)
from casare_rpa.domain.events import EventBus, Event
from casare_rpa.domain.value_objects.types import EventType


class MigrationStatus(Enum):
    """Status of a migration operation."""

    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    ROLLED_BACK = auto()


@dataclass
class MigrationStep:
    """Represents a single step in the migration process."""

    name: str
    description: str
    action: Callable[["MigrationContext"], bool]
    rollback_action: Optional[Callable[["MigrationContext"], bool]] = None
    completed: bool = False
    error: Optional[str] = None


@dataclass
class MigrationContext:
    """Context passed to migration steps."""

    workflow_id: str
    from_version: WorkflowVersion
    to_version: WorkflowVersion
    diff: VersionDiff
    compatibility: CompatibilityResult
    workflow_data: WorkflowData  # Mutable copy being transformed
    variables: Dict[str, JsonValue] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    success: bool
    workflow_id: str
    from_version: str
    to_version: str
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    steps_completed: int = 0
    total_steps: int = 0
    breaking_changes_resolved: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    migrated_data: Optional[WorkflowData] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "workflow_id": self.workflow_id,
            "from_version": self.from_version,
            "to_version": self.to_version,
            "status": self.status.name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "steps_completed": self.steps_completed,
            "total_steps": self.total_steps,
            "breaking_changes_resolved": self.breaking_changes_resolved,
            "errors": self.errors,
            "warnings": self.warnings,
        }


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


# Global rule registry
_rule_registry = MigrationRuleRegistry()


def get_rule_registry() -> MigrationRuleRegistry:
    """Get the global migration rule registry."""
    return _rule_registry


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
        _rule_registry.register(rule)
        return func

    return decorator


class WorkflowMigrationUseCase:
    """
    Application use case for migrating workflows between versions.

    Provides:
    - Automatic migration with registered rules
    - Breaking change resolution
    - Rollback support
    - Progress tracking via events
    """

    def __init__(
        self,
        version_history: VersionHistory,
        event_bus: Optional[EventBus] = None,
        rule_registry: Optional[MigrationRuleRegistry] = None,
    ) -> None:
        """
        Initialize migration use case.

        Args:
            version_history: VersionHistory for the workflow
            event_bus: Optional event bus for progress updates
            rule_registry: Optional custom rule registry
        """
        self.version_history = version_history
        self.event_bus = event_bus
        self.rule_registry = rule_registry or get_rule_registry()
        self._migration_steps: List[MigrationStep] = []
        self._current_context: Optional[MigrationContext] = None

    def _emit_event(self, event_type: EventType, data: Dict[str, JsonValue]) -> None:
        """Emit migration event."""
        if self.event_bus:
            event = Event(event_type=event_type, data=data)
            self.event_bus.publish(event)

    def check_migration_feasibility(
        self, from_version: str, to_version: str
    ) -> Tuple[bool, CompatibilityResult, str]:
        """
        Check if migration between versions is feasible.

        Args:
            from_version: Source version string
            to_version: Target version string

        Returns:
            Tuple of (feasible, compatibility_result, reason)
        """
        from_ver = self.version_history.get_version(from_version)
        to_ver = self.version_history.get_version(to_version)

        if not from_ver:
            return (
                False,
                CompatibilityResult(is_compatible=False),
                f"Source version {from_version} not found",
            )

        if not to_ver:
            return (
                False,
                CompatibilityResult(is_compatible=False),
                f"Target version {to_version} not found",
            )

        # Check compatibility
        compatibility = self.version_history.check_compatibility(
            from_version, to_version
        )

        if not compatibility.is_compatible and not compatibility.auto_migratable:
            return (
                False,
                compatibility,
                f"Migration requires manual intervention: {len(compatibility.breaking_changes)} breaking changes",
            )

        return True, compatibility, "Migration is feasible"

    async def migrate(
        self,
        from_version: str,
        to_version: str,
        dry_run: bool = False,
    ) -> MigrationResult:
        """
        Execute migration from one version to another.

        Args:
            from_version: Source version string
            to_version: Target version string
            dry_run: If True, simulate migration without persisting

        Returns:
            MigrationResult with outcome details
        """
        started_at = datetime.now()
        workflow_id = self.version_history.workflow_id

        logger.info(
            f"Starting migration for {workflow_id}: {from_version} -> {to_version}"
        )

        # Initialize result
        result = MigrationResult(
            success=False,
            workflow_id=workflow_id,
            from_version=from_version,
            to_version=to_version,
            status=MigrationStatus.PENDING,
            started_at=started_at,
        )

        try:
            # Check feasibility
            feasible, compatibility, reason = self.check_migration_feasibility(
                from_version, to_version
            )

            if not feasible:
                result.status = MigrationStatus.FAILED
                result.errors.append(reason)
                logger.error(f"Migration not feasible: {reason}")
                return result

            # Get versions
            from_ver = self.version_history.get_version(from_version)
            to_ver = self.version_history.get_version(to_version)

            if not from_ver or not to_ver:
                result.status = MigrationStatus.FAILED
                result.errors.append("Version not found")
                return result

            # Generate diff
            diff = self.version_history.generate_diff(from_version, to_version)
            if not diff:
                result.status = MigrationStatus.FAILED
                result.errors.append("Failed to generate version diff")
                return result

            # Create migration context
            context = MigrationContext(
                workflow_id=workflow_id,
                from_version=from_ver,
                to_version=to_ver,
                diff=diff,
                compatibility=compatibility,
                workflow_data=copy.deepcopy(from_ver.workflow_data),
            )
            self._current_context = context

            # Build migration steps
            self._build_migration_steps(context)
            result.total_steps = len(self._migration_steps)

            # Emit start event
            self._emit_event(
                EventType.WORKFLOW_STARTED,
                {
                    "operation": "migration",
                    "workflow_id": workflow_id,
                    "from_version": from_version,
                    "to_version": to_version,
                    "total_steps": result.total_steps,
                },
            )

            result.status = MigrationStatus.IN_PROGRESS

            # Execute migration steps
            for i, step in enumerate(self._migration_steps):
                logger.debug(
                    f"Executing migration step {i + 1}/{result.total_steps}: {step.name}"
                )

                try:
                    success = step.action(context)

                    if success:
                        step.completed = True
                        result.steps_completed += 1
                    else:
                        step.error = (
                            context.errors[-1] if context.errors else "Step failed"
                        )
                        result.errors.append(f"Step '{step.name}' failed: {step.error}")
                        break

                except Exception as e:
                    step.error = str(e)
                    result.errors.append(f"Step '{step.name}' raised exception: {e}")
                    logger.exception(f"Migration step '{step.name}' failed")
                    break

            # Check if all steps completed
            if result.steps_completed == result.total_steps:
                result.success = True
                result.status = MigrationStatus.COMPLETED
                result.migrated_data = context.workflow_data
                result.breaking_changes_resolved = sum(
                    1 for bc in compatibility.breaking_changes if bc.severity != "error"
                )

                if not dry_run:
                    # Create new version with migrated data
                    new_version = self.version_history.create_new_version(
                        workflow_data=context.workflow_data,
                        bump_type=self._determine_version_bump(compatibility),
                        change_summary=f"Migrated from {from_version}",
                    )
                    logger.info(f"Created migrated version: {new_version.version}")

            else:
                result.status = MigrationStatus.FAILED

                # Attempt rollback if not dry run
                if not dry_run:
                    await self._rollback_migration(context, result)

            # Add warnings
            result.warnings.extend(context.warnings)

            # Calculate duration
            result.completed_at = datetime.now()
            result.duration_ms = (
                result.completed_at - started_at
            ).total_seconds() * 1000

            # Emit completion event
            self._emit_event(
                EventType.WORKFLOW_COMPLETED
                if result.success
                else EventType.WORKFLOW_ERROR,
                {
                    "operation": "migration",
                    "workflow_id": workflow_id,
                    "success": result.success,
                    "duration_ms": result.duration_ms,
                },
            )

            logger.info(
                f"Migration {'completed' if result.success else 'failed'}: "
                f"{result.steps_completed}/{result.total_steps} steps, "
                f"{result.duration_ms:.2f}ms"
            )

            return result

        except Exception as e:
            result.status = MigrationStatus.FAILED
            result.errors.append(f"Migration failed with exception: {e}")
            result.completed_at = datetime.now()
            result.duration_ms = (
                result.completed_at - started_at
            ).total_seconds() * 1000
            logger.exception("Migration failed with unexpected exception")
            return result

        finally:
            self._current_context = None
            self._migration_steps.clear()

    def _build_migration_steps(self, context: MigrationContext) -> None:
        """Build the list of migration steps based on diff and compatibility."""
        self._migration_steps.clear()

        # Step 1: Migrate modified nodes
        if context.diff.nodes_modified:
            self._migration_steps.append(
                MigrationStep(
                    name="migrate_modified_nodes",
                    description="Apply transformation rules to modified nodes",
                    action=self._step_migrate_nodes,
                )
            )

        # Step 2: Update connections for node changes
        if context.diff.connections_removed or context.diff.connections_added:
            self._migration_steps.append(
                MigrationStep(
                    name="update_connections",
                    description="Update connection graph for node changes",
                    action=self._step_update_connections,
                )
            )

        # Step 3: Migrate variables
        if context.diff.variables_modified or context.diff.variables_removed:
            self._migration_steps.append(
                MigrationStep(
                    name="migrate_variables",
                    description="Transform and validate workflow variables",
                    action=self._step_migrate_variables,
                )
            )

        # Step 4: Update settings
        if context.diff.settings_changed:
            self._migration_steps.append(
                MigrationStep(
                    name="update_settings",
                    description="Migrate workflow settings",
                    action=self._step_update_settings,
                )
            )

        # Step 5: Validate migrated workflow
        self._migration_steps.append(
            MigrationStep(
                name="validate_result",
                description="Validate migrated workflow structure",
                action=self._step_validate_result,
            )
        )

    def _step_migrate_nodes(self, context: MigrationContext) -> bool:
        """Migration step: Transform modified nodes using registered rules."""
        from_version = context.from_version.version
        to_version = context.to_version.version
        nodes = context.workflow_data.get("nodes", {})

        for node_id in context.diff.nodes_modified:
            if node_id not in nodes:
                continue

            node_data = nodes[node_id]
            node_type = node_data.get("node_type", "")

            # Find applicable migration rules
            rules = self.rule_registry.find_rules(node_type, from_version, to_version)

            if rules:
                for rule in rules:
                    try:
                        transformed = rule.transformer(copy.deepcopy(node_data))
                        nodes[node_id] = transformed
                        logger.debug(
                            f"Applied migration rule to {node_id}: {rule.description}"
                        )
                    except Exception as e:
                        context.errors.append(f"Failed to apply rule to {node_id}: {e}")
                        return False
            else:
                # No rules - apply default transformation (preserve data)
                context.warnings.append(
                    f"No migration rules for {node_type} - node preserved as-is"
                )

        return True

    def _step_update_connections(self, context: MigrationContext) -> bool:
        """Migration step: Update connections for node changes."""
        # Remove connections to/from removed nodes
        removed_nodes = context.diff.nodes_removed
        connections = context.workflow_data.get("connections", [])

        updated_connections = [
            conn
            for conn in connections
            if conn.get("source_node") not in removed_nodes
            and conn.get("target_node") not in removed_nodes
        ]

        # Check for broken connections (ports that no longer exist)
        nodes = context.workflow_data.get("nodes", {})
        valid_connections = []

        for conn in updated_connections:
            source_node = nodes.get(conn.get("source_node"))
            target_node = nodes.get(conn.get("target_node"))

            if not source_node or not target_node:
                context.warnings.append(
                    f"Removing connection: node not found ({conn.get('source_node')} -> {conn.get('target_node')})"
                )
                continue

            # Check if ports exist (relaxed validation)
            valid_connections.append(conn)

        context.workflow_data["connections"] = valid_connections

        removed_count = len(connections) - len(valid_connections)
        if removed_count > 0:
            context.warnings.append(f"Removed {removed_count} invalid connections")

        return True

    def _step_migrate_variables(self, context: MigrationContext) -> bool:
        """Migration step: Migrate workflow variables."""
        variables = context.workflow_data.get("variables", {})
        to_variables = context.to_version.workflow_data.get("variables", {})

        # Remove deleted variables
        for var_name in context.diff.variables_removed:
            if var_name in variables:
                del variables[var_name]
                context.warnings.append(f"Removed variable: {var_name}")

        # Update modified variables (preserve values where possible)
        for var_name in context.diff.variables_modified:
            if var_name in variables and var_name in to_variables:
                old_var = variables[var_name]
                new_var = to_variables[var_name]

                # Attempt type coercion if types changed
                old_type = (
                    old_var.get("type")
                    if isinstance(old_var, dict)
                    else type(old_var).__name__
                )
                new_type = (
                    new_var.get("type")
                    if isinstance(new_var, dict)
                    else type(new_var).__name__
                )

                if old_type != new_type:
                    context.warnings.append(
                        f"Variable '{var_name}' type changed from {old_type} to {new_type}"
                    )
                    # Use new default value since type changed
                    variables[var_name] = new_var
                else:
                    # Preserve existing value, update structure
                    if isinstance(new_var, dict) and isinstance(old_var, dict):
                        merged = {
                            **new_var,
                            "default_value": old_var.get("default_value"),
                        }
                        variables[var_name] = merged

        # Add new variables
        for var_name in context.diff.variables_added:
            if var_name in to_variables:
                variables[var_name] = to_variables[var_name]

        context.workflow_data["variables"] = variables
        return True

    def _step_update_settings(self, context: MigrationContext) -> bool:
        """Migration step: Update workflow settings."""
        settings = context.workflow_data.get("settings", {})
        to_settings = context.to_version.workflow_data.get("settings", {})

        for key, (old_val, new_val) in context.diff.settings_changed.items():
            if new_val is None:
                # Setting removed
                if key in settings:
                    del settings[key]
                    context.warnings.append(f"Removed setting: {key}")
            else:
                # Setting added or changed
                settings[key] = new_val
                if old_val is not None:
                    context.warnings.append(
                        f"Updated setting '{key}': {old_val} -> {new_val}"
                    )

        context.workflow_data["settings"] = settings
        return True

    def _step_validate_result(self, context: MigrationContext) -> bool:
        """Migration step: Validate the migrated workflow."""
        workflow_data = context.workflow_data

        # Basic structure validation
        if "nodes" not in workflow_data:
            context.errors.append("Migrated workflow missing 'nodes' key")
            return False

        if "connections" not in workflow_data:
            workflow_data["connections"] = []

        # Validate node references in connections
        nodes = workflow_data.get("nodes", {})
        connections = workflow_data.get("connections", [])

        for conn in connections:
            source_node = conn.get("source_node")
            target_node = conn.get("target_node")

            if source_node not in nodes:
                context.errors.append(
                    f"Connection references missing source node: {source_node}"
                )
                return False

            if target_node not in nodes:
                context.errors.append(
                    f"Connection references missing target node: {target_node}"
                )
                return False

        # Check for orphaned nodes (no connections) - warning only
        connected_nodes: Set[str] = set()
        for conn in connections:
            connected_nodes.add(conn.get("source_node", ""))
            connected_nodes.add(conn.get("target_node", ""))

        for node_id in nodes:
            if node_id not in connected_nodes:
                node_type = nodes[node_id].get("node_type", "")
                if node_type not in ("StartNode", "EndNode"):
                    context.warnings.append(
                        f"Orphaned node detected: {node_id} ({node_type})"
                    )

        return True

    async def _rollback_migration(
        self, context: MigrationContext, result: MigrationResult
    ) -> None:
        """Attempt to rollback failed migration steps."""
        logger.warning("Attempting migration rollback...")

        # Execute rollback actions in reverse order
        for step in reversed(self._migration_steps):
            if step.completed and step.rollback_action:
                try:
                    step.rollback_action(context)
                    logger.debug(f"Rolled back step: {step.name}")
                except Exception as e:
                    logger.error(f"Rollback failed for step {step.name}: {e}")

        result.status = MigrationStatus.ROLLED_BACK

    def _determine_version_bump(self, compatibility: CompatibilityResult) -> str:
        """Determine appropriate version bump based on compatibility."""
        if compatibility.has_breaking_changes:
            return "major"
        elif compatibility.migration_required:
            return "minor"
        return "patch"

    async def validate_running_jobs(
        self, target_version: str, running_job_ids: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that migration is safe for running jobs.

        Args:
            target_version: Version to migrate to
            running_job_ids: List of currently running job IDs

        Returns:
            Tuple of (safe_to_migrate, conflicting_job_ids)
        """
        # This would integrate with the job scheduler to check
        # if any running jobs are using a version incompatible with target
        conflicting_jobs: List[str] = []

        # For now, return empty conflicts (implementation depends on job scheduler)
        return len(conflicting_jobs) == 0, conflicting_jobs


class VersionPinManager:
    """
    Manages version pinning for scheduled jobs.

    Allows jobs to be pinned to specific workflow versions,
    preventing automatic updates that could break scheduled executions.
    """

    def __init__(self, version_history: VersionHistory) -> None:
        """
        Initialize pin manager.

        Args:
            version_history: VersionHistory for the workflow
        """
        self.version_history = version_history
        self._pins: Dict[str, str] = {}  # job_id -> version_string

    def pin_job(self, job_id: str, version_str: str, reason: str = "") -> bool:
        """
        Pin a job to a specific version.

        Args:
            job_id: Job identifier
            version_str: Version to pin to
            reason: Reason for pinning

        Returns:
            True if pinning succeeded
        """
        version = self.version_history.get_version(version_str)
        if not version:
            logger.error(f"Cannot pin job {job_id}: version {version_str} not found")
            return False

        if not version.can_execute():
            logger.error(
                f"Cannot pin job {job_id}: version {version_str} is not executable"
            )
            return False

        self._pins[job_id] = version_str
        logger.info(f"Pinned job {job_id} to version {version_str}: {reason}")
        return True

    def unpin_job(self, job_id: str) -> bool:
        """
        Remove version pin from a job.

        Args:
            job_id: Job identifier

        Returns:
            True if job was unpinned
        """
        if job_id in self._pins:
            del self._pins[job_id]
            logger.info(f"Unpinned job {job_id}")
            return True
        return False

    def get_pinned_version(self, job_id: str) -> Optional[str]:
        """Get pinned version for a job, or None if not pinned."""
        return self._pins.get(job_id)

    def get_execution_version(self, job_id: str) -> Optional[WorkflowVersion]:
        """
        Get the workflow version that should be used for job execution.

        Returns pinned version if set, otherwise active version.

        Args:
            job_id: Job identifier

        Returns:
            WorkflowVersion to use for execution
        """
        pinned = self._pins.get(job_id)
        if pinned:
            return self.version_history.get_version(pinned)
        return self.version_history.active_version

    def get_jobs_pinned_to_version(self, version_str: str) -> List[str]:
        """Get all job IDs pinned to a specific version."""
        return [job_id for job_id, ver in self._pins.items() if ver == version_str]

    def validate_pins(self) -> List[Tuple[str, str]]:
        """
        Validate all pins and return invalid ones.

        Returns:
            List of (job_id, reason) for invalid pins
        """
        invalid: List[Tuple[str, str]] = []

        for job_id, version_str in self._pins.items():
            version = self.version_history.get_version(version_str)
            if not version:
                invalid.append((job_id, f"Version {version_str} no longer exists"))
            elif not version.can_execute():
                invalid.append(
                    (job_id, f"Version {version_str} is {version.status.name}")
                )

        return invalid

    def to_dict(self) -> Dict[str, Any]:
        """Serialize pins to dictionary."""
        return {"pins": dict(self._pins)}

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], version_history: VersionHistory
    ) -> "VersionPinManager":
        """Create instance from dictionary."""
        manager = cls(version_history)
        manager._pins = dict(data.get("pins", {}))
        return manager


class AutoMigrationPolicy:
    """
    Policy for automatic workflow version migrations.

    Defines rules for when and how to automatically migrate
    workflows to newer versions.
    """

    def __init__(
        self,
        auto_patch_updates: bool = True,
        auto_minor_updates: bool = False,
        auto_major_updates: bool = False,
        require_passing_validation: bool = True,
        max_breaking_changes: int = 0,
    ) -> None:
        """
        Initialize migration policy.

        Args:
            auto_patch_updates: Auto-migrate for patch version bumps
            auto_minor_updates: Auto-migrate for minor version bumps
            auto_major_updates: Auto-migrate for major version bumps
            require_passing_validation: Require validation pass before migration
            max_breaking_changes: Max allowed breaking changes for auto-migration
        """
        self.auto_patch_updates = auto_patch_updates
        self.auto_minor_updates = auto_minor_updates
        self.auto_major_updates = auto_major_updates
        self.require_passing_validation = require_passing_validation
        self.max_breaking_changes = max_breaking_changes

    def should_auto_migrate(
        self,
        from_version: SemanticVersion,
        to_version: SemanticVersion,
        compatibility: CompatibilityResult,
    ) -> Tuple[bool, str]:
        """
        Check if auto-migration should proceed.

        Args:
            from_version: Current version
            to_version: Target version
            compatibility: Compatibility check result

        Returns:
            Tuple of (should_migrate, reason)
        """
        # Check breaking changes limit
        if len(compatibility.breaking_changes) > self.max_breaking_changes:
            return (
                False,
                f"Too many breaking changes: {len(compatibility.breaking_changes)} > {self.max_breaking_changes}",
            )

        # Check if migration is possible
        if not compatibility.auto_migratable:
            return False, "Migration requires manual intervention"

        # Check version bump type
        if from_version.major != to_version.major:
            if not self.auto_major_updates:
                return False, "Major version updates require manual approval"
            return True, "Auto-major update enabled"

        if from_version.minor != to_version.minor:
            if not self.auto_minor_updates:
                return False, "Minor version updates require manual approval"
            return True, "Auto-minor update enabled"

        if from_version.patch != to_version.patch:
            if not self.auto_patch_updates:
                return False, "Patch version updates require manual approval"
            return True, "Auto-patch update enabled"

        return False, "No version change detected"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize policy to dictionary."""
        return {
            "auto_patch_updates": self.auto_patch_updates,
            "auto_minor_updates": self.auto_minor_updates,
            "auto_major_updates": self.auto_major_updates,
            "require_passing_validation": self.require_passing_validation,
            "max_breaking_changes": self.max_breaking_changes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutoMigrationPolicy":
        """Create instance from dictionary."""
        return cls(
            auto_patch_updates=data.get("auto_patch_updates", True),
            auto_minor_updates=data.get("auto_minor_updates", False),
            auto_major_updates=data.get("auto_major_updates", False),
            require_passing_validation=data.get("require_passing_validation", True),
            max_breaking_changes=data.get("max_breaking_changes", 0),
        )

    @classmethod
    def permissive(cls) -> "AutoMigrationPolicy":
        """Create a permissive policy (auto-migrate most changes)."""
        return cls(
            auto_patch_updates=True,
            auto_minor_updates=True,
            auto_major_updates=False,
            max_breaking_changes=5,
        )

    @classmethod
    def strict(cls) -> "AutoMigrationPolicy":
        """Create a strict policy (minimal auto-migration)."""
        return cls(
            auto_patch_updates=True,
            auto_minor_updates=False,
            auto_major_updates=False,
            max_breaking_changes=0,
        )

    @classmethod
    def manual(cls) -> "AutoMigrationPolicy":
        """Create a manual-only policy (no auto-migration)."""
        return cls(
            auto_patch_updates=False,
            auto_minor_updates=False,
            auto_major_updates=False,
            max_breaking_changes=0,
        )

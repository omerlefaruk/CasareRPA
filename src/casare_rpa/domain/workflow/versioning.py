"""
CasareRPA - Domain: Workflow Versioning
Semantic versioning and version management for enterprise workflows.

Provides:
- Semantic versioning (major.minor.patch)
- Version status lifecycle (draft, active, deprecated, archived)
- Breaking change detection
- Diff generation between versions
- Backward compatibility validation
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
import re

import logging

logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """Workflow version lifecycle status."""

    DRAFT = auto()  # Work in progress, not deployable
    ACTIVE = auto()  # Production-ready, can be executed
    DEPRECATED = auto()  # Still functional but scheduled for removal
    ARCHIVED = auto()  # No longer usable, kept for history


class BreakingChangeType(Enum):
    """Types of breaking changes between workflow versions."""

    NODE_REMOVED = auto()  # A node was deleted
    NODE_TYPE_CHANGED = auto()  # Node type was modified
    PORT_REMOVED = auto()  # Input/output port was removed
    PORT_TYPE_CHANGED = auto()  # Port data type was changed
    REQUIRED_PORT_ADDED = auto()  # New required input port added
    CONNECTION_BROKEN = auto()  # Connection path no longer valid
    VARIABLE_REMOVED = auto()  # Global variable removed
    VARIABLE_TYPE_CHANGED = auto()  # Variable type changed
    SETTING_REMOVED = auto()  # Workflow setting removed


@dataclass(frozen=True)
class SemanticVersion:
    """
    Immutable semantic version following semver.org specification.

    Version format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
    - MAJOR: Incremented for breaking changes
    - MINOR: Incremented for backward-compatible features
    - PATCH: Incremented for backward-compatible bug fixes
    """

    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    build: Optional[str] = None

    SEMVER_PATTERN = re.compile(
        r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
        r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    )

    def __post_init__(self) -> None:
        """Validate version components."""
        if self.major < 0:
            raise ValueError(f"Major version must be non-negative: {self.major}")
        if self.minor < 0:
            raise ValueError(f"Minor version must be non-negative: {self.minor}")
        if self.patch < 0:
            raise ValueError(f"Patch version must be non-negative: {self.patch}")

    @classmethod
    def parse(cls, version_string: str) -> "SemanticVersion":
        """
        Parse a version string into SemanticVersion.

        Args:
            version_string: Version string (e.g., "1.2.3", "2.0.0-beta.1+build.123")

        Returns:
            SemanticVersion instance

        Raises:
            ValueError: If version string is invalid
        """
        match = cls.SEMVER_PATTERN.match(version_string.strip())
        if not match:
            raise ValueError(f"Invalid semantic version: '{version_string}'")

        groups = match.groupdict()
        return cls(
            major=int(groups["major"]),
            minor=int(groups["minor"]),
            patch=int(groups["patch"]),
            prerelease=groups.get("prerelease"),
            build=groups.get("build"),
        )

    @classmethod
    def initial(cls) -> "SemanticVersion":
        """Create initial version 1.0.0."""
        return cls(major=1, minor=0, patch=0)

    def bump_major(self) -> "SemanticVersion":
        """Increment major version, reset minor and patch."""
        return SemanticVersion(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> "SemanticVersion":
        """Increment minor version, reset patch."""
        return SemanticVersion(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> "SemanticVersion":
        """Increment patch version."""
        return SemanticVersion(major=self.major, minor=self.minor, patch=self.patch + 1)

    def with_prerelease(self, prerelease: str) -> "SemanticVersion":
        """Create version with prerelease tag."""
        return SemanticVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=prerelease,
            build=self.build,
        )

    def with_build(self, build: str) -> "SemanticVersion":
        """Create version with build metadata."""
        return SemanticVersion(
            major=self.major,
            minor=self.minor,
            patch=self.patch,
            prerelease=self.prerelease,
            build=build,
        )

    def is_compatible_with(self, other: "SemanticVersion") -> bool:
        """
        Check if this version is backward compatible with another.

        Per semver, versions with same major version should be compatible
        (assuming proper versioning practices).

        Args:
            other: Version to check compatibility against

        Returns:
            True if versions are compatible
        """
        if self.major == 0 and other.major == 0:
            # Pre-1.0 versions: minor version changes may be breaking
            return self.major == other.major and self.minor == other.minor
        return self.major == other.major

    def is_prerelease(self) -> bool:
        """Check if this is a prerelease version."""
        return self.prerelease is not None

    def __str__(self) -> str:
        """Format as version string."""
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        if self.build:
            version += f"+{self.build}"
        return version

    def __lt__(self, other: "SemanticVersion") -> bool:
        """Compare versions for ordering."""
        if not isinstance(other, SemanticVersion):
            return NotImplemented

        # Compare major.minor.patch
        self_tuple = (self.major, self.minor, self.patch)
        other_tuple = (other.major, other.minor, other.patch)

        if self_tuple != other_tuple:
            return self_tuple < other_tuple

        # Prerelease versions have lower precedence
        if self.prerelease is None and other.prerelease is None:
            return False
        if self.prerelease is None:
            return False  # Release > prerelease
        if other.prerelease is None:
            return True  # Prerelease < release

        # Compare prerelease strings
        return self.prerelease < other.prerelease

    def __le__(self, other: "SemanticVersion") -> bool:
        return self == other or self < other

    def __gt__(self, other: "SemanticVersion") -> bool:
        return not self <= other

    def __ge__(self, other: "SemanticVersion") -> bool:
        return not self < other


@dataclass
class BreakingChange:
    """Represents a breaking change between workflow versions."""

    change_type: BreakingChangeType
    element_id: str  # ID of affected element (node_id, variable name, etc.)
    description: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    severity: str = "error"  # error, warning

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "change_type": self.change_type.name,
            "element_id": self.element_id,
            "description": self.description,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "severity": self.severity,
        }


@dataclass
class CompatibilityResult:
    """Result of compatibility check between workflow versions."""

    is_compatible: bool
    breaking_changes: List[BreakingChange] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    migration_required: bool = False
    auto_migratable: bool = True

    @property
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return len(self.breaking_changes) > 0

    @property
    def error_count(self) -> int:
        """Count breaking changes with error severity."""
        return sum(1 for bc in self.breaking_changes if bc.severity == "error")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "is_compatible": self.is_compatible,
            "breaking_changes": [bc.to_dict() for bc in self.breaking_changes],
            "warnings": self.warnings,
            "migration_required": self.migration_required,
            "auto_migratable": self.auto_migratable,
        }


@dataclass
class VersionDiff:
    """Represents differences between two workflow versions."""

    from_version: str
    to_version: str
    nodes_added: Set[str] = field(default_factory=set)
    nodes_removed: Set[str] = field(default_factory=set)
    nodes_modified: Set[str] = field(default_factory=set)
    connections_added: List[Dict[str, str]] = field(default_factory=list)
    connections_removed: List[Dict[str, str]] = field(default_factory=list)
    variables_added: Set[str] = field(default_factory=set)
    variables_removed: Set[str] = field(default_factory=set)
    variables_modified: Set[str] = field(default_factory=set)
    settings_changed: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    metadata_changed: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return (
            bool(self.nodes_added)
            or bool(self.nodes_removed)
            or bool(self.nodes_modified)
            or bool(self.connections_added)
            or bool(self.connections_removed)
            or bool(self.variables_added)
            or bool(self.variables_removed)
            or bool(self.variables_modified)
            or bool(self.settings_changed)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "nodes_added": list(self.nodes_added),
            "nodes_removed": list(self.nodes_removed),
            "nodes_modified": list(self.nodes_modified),
            "connections_added": self.connections_added,
            "connections_removed": self.connections_removed,
            "variables_added": list(self.variables_added),
            "variables_removed": list(self.variables_removed),
            "variables_modified": list(self.variables_modified),
            "settings_changed": {
                k: {"old": v[0], "new": v[1]} for k, v in self.settings_changed.items()
            },
            "metadata_changed": {
                k: {"old": v[0], "new": v[1]} for k, v in self.metadata_changed.items()
            },
        }


@dataclass
class WorkflowVersion:
    """
    Represents a specific version of a workflow.

    Captures the complete workflow state at a point in time,
    including schema, metadata, and version information.
    """

    workflow_id: str  # UUID of the workflow
    version: SemanticVersion
    status: VersionStatus
    workflow_data: Dict[str, Any]  # Complete serialized workflow
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    parent_version: Optional[str] = None  # Version string of parent
    change_summary: str = ""
    tags: List[str] = field(default_factory=list)

    # Computed fields
    node_count: int = 0
    connection_count: int = 0
    checksum: str = ""

    def __post_init__(self) -> None:
        """Compute derived fields."""
        if self.workflow_data:
            self.node_count = len(self.workflow_data.get("nodes", {}))
            self.connection_count = len(self.workflow_data.get("connections", []))
            self._compute_checksum()

    def _compute_checksum(self) -> None:
        """Compute content checksum for integrity verification."""
        import hashlib
        import orjson

        # Exclude volatile fields from checksum
        data_for_hash = {
            "nodes": self.workflow_data.get("nodes", {}),
            "connections": self.workflow_data.get("connections", []),
            "variables": self.workflow_data.get("variables", {}),
            "settings": self.workflow_data.get("settings", {}),
        }
        json_bytes = orjson.dumps(data_for_hash, option=orjson.OPT_SORT_KEYS)
        self.checksum = hashlib.sha256(json_bytes).hexdigest()[:16]

    def is_draft(self) -> bool:
        """Check if version is in draft status."""
        return self.status == VersionStatus.DRAFT

    def is_active(self) -> bool:
        """Check if version is active."""
        return self.status == VersionStatus.ACTIVE

    def is_deprecated(self) -> bool:
        """Check if version is deprecated."""
        return self.status == VersionStatus.DEPRECATED

    def is_archived(self) -> bool:
        """Check if version is archived."""
        return self.status == VersionStatus.ARCHIVED

    def can_execute(self) -> bool:
        """Check if this version can be executed."""
        return self.status in (VersionStatus.ACTIVE, VersionStatus.DEPRECATED)

    def can_modify(self) -> bool:
        """Check if this version can be modified."""
        return self.status == VersionStatus.DRAFT

    def transition_to(self, new_status: VersionStatus) -> bool:
        """
        Attempt to transition to a new status.

        Valid transitions:
        - DRAFT -> ACTIVE
        - ACTIVE -> DEPRECATED
        - DEPRECATED -> ARCHIVED
        - DEPRECATED -> ACTIVE (reactivation)

        Args:
            new_status: Target status

        Returns:
            True if transition was valid and executed
        """
        valid_transitions = {
            VersionStatus.DRAFT: {VersionStatus.ACTIVE},
            VersionStatus.ACTIVE: {VersionStatus.DEPRECATED},
            VersionStatus.DEPRECATED: {VersionStatus.ARCHIVED, VersionStatus.ACTIVE},
            VersionStatus.ARCHIVED: set(),  # No transitions from archived
        }

        if new_status in valid_transitions.get(self.status, set()):
            logger.info(
                f"Workflow {self.workflow_id} version {self.version}: "
                f"{self.status.name} -> {new_status.name}"
            )
            self.status = new_status
            return True

        logger.warning(f"Invalid status transition: {self.status.name} -> {new_status.name}")
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "workflow_id": self.workflow_id,
            "version": str(self.version),
            "status": self.status.name,
            "workflow_data": self.workflow_data,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_version": self.parent_version,
            "change_summary": self.change_summary,
            "tags": self.tags,
            "node_count": self.node_count,
            "connection_count": self.connection_count,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowVersion":
        """Create instance from dictionary."""
        return cls(
            workflow_id=data["workflow_id"],
            version=SemanticVersion.parse(data["version"]),
            status=VersionStatus[data["status"]],
            workflow_data=data["workflow_data"],
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=data.get("created_by"),
            parent_version=data.get("parent_version"),
            change_summary=data.get("change_summary", ""),
            tags=data.get("tags", []),
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"WorkflowVersion(workflow_id={self.workflow_id}, "
            f"version={self.version}, status={self.status.name})"
        )


class VersionHistory:
    """
    Manages version history for a workflow.

    Provides:
    - Version creation and tracking
    - Diff generation between versions
    - Breaking change detection
    - Rollback support
    """

    def __init__(self, workflow_id: str) -> None:
        """
        Initialize version history.

        Args:
            workflow_id: UUID of the workflow
        """
        self.workflow_id = workflow_id
        self.versions: Dict[str, WorkflowVersion] = {}  # version string -> WorkflowVersion
        self._version_order: List[str] = []  # Ordered list of version strings
        self._active_version: Optional[str] = None

    @property
    def active_version(self) -> Optional[WorkflowVersion]:
        """Get the currently active version."""
        if self._active_version:
            return self.versions.get(self._active_version)
        return None

    @property
    def latest_version(self) -> Optional[WorkflowVersion]:
        """Get the most recent version (regardless of status)."""
        if self._version_order:
            return self.versions.get(self._version_order[-1])
        return None

    @property
    def version_count(self) -> int:
        """Get total number of versions."""
        return len(self.versions)

    def add_version(self, version: WorkflowVersion) -> None:
        """
        Add a version to history.

        Args:
            version: WorkflowVersion to add

        Raises:
            ValueError: If version already exists
        """
        version_str = str(version.version)

        if version_str in self.versions:
            raise ValueError(f"Version {version_str} already exists")

        self.versions[version_str] = version
        self._version_order.append(version_str)
        self._version_order.sort(key=lambda v: SemanticVersion.parse(v))

        if version.is_active():
            self._set_active_version(version_str)

        logger.debug(f"Added version {version_str} to history for {self.workflow_id}")

    def get_version(self, version_str: str) -> Optional[WorkflowVersion]:
        """Get a specific version."""
        return self.versions.get(version_str)

    def _set_active_version(self, version_str: str) -> None:
        """
        Set a version as active (deactivating any current active version).

        Args:
            version_str: Version to activate
        """
        # Deprecate current active version
        if self._active_version and self._active_version != version_str:
            current_active = self.versions.get(self._active_version)
            if current_active and current_active.is_active():
                current_active.transition_to(VersionStatus.DEPRECATED)

        self._active_version = version_str
        logger.info(f"Active version set to {version_str} for {self.workflow_id}")

    def activate_version(self, version_str: str) -> bool:
        """
        Activate a specific version.

        Args:
            version_str: Version to activate

        Returns:
            True if activation succeeded
        """
        version = self.versions.get(version_str)
        if not version:
            logger.error(f"Version {version_str} not found")
            return False

        if version.transition_to(VersionStatus.ACTIVE):
            self._set_active_version(version_str)
            return True
        return False

    def create_new_version(
        self,
        workflow_data: Dict[str, Any],
        bump_type: str = "patch",
        change_summary: str = "",
        created_by: Optional[str] = None,
    ) -> WorkflowVersion:
        """
        Create a new version based on the latest version.

        Args:
            workflow_data: New workflow data
            bump_type: Version bump type ("major", "minor", "patch")
            change_summary: Description of changes
            created_by: User who created this version

        Returns:
            New WorkflowVersion instance
        """
        # Determine new version number
        if self.latest_version:
            base_version = self.latest_version.version
            if bump_type == "major":
                new_version = base_version.bump_major()
            elif bump_type == "minor":
                new_version = base_version.bump_minor()
            else:
                new_version = base_version.bump_patch()
            parent_version = str(base_version)
        else:
            new_version = SemanticVersion.initial()
            parent_version = None

        version = WorkflowVersion(
            workflow_id=self.workflow_id,
            version=new_version,
            status=VersionStatus.DRAFT,
            workflow_data=workflow_data,
            created_by=created_by,
            parent_version=parent_version,
            change_summary=change_summary,
        )

        self.add_version(version)
        return version

    def generate_diff(self, from_version: str, to_version: str) -> Optional[VersionDiff]:
        """
        Generate diff between two versions.

        Args:
            from_version: Source version string
            to_version: Target version string

        Returns:
            VersionDiff or None if versions not found
        """
        from_ver = self.versions.get(from_version)
        to_ver = self.versions.get(to_version)

        if not from_ver or not to_ver:
            logger.error(f"Cannot diff: version not found ({from_version} or {to_version})")
            return None

        diff = VersionDiff(from_version=from_version, to_version=to_version)

        from_data = from_ver.workflow_data
        to_data = to_ver.workflow_data

        # Compare nodes
        from_nodes = set(from_data.get("nodes", {}).keys())
        to_nodes = set(to_data.get("nodes", {}).keys())

        diff.nodes_added = to_nodes - from_nodes
        diff.nodes_removed = from_nodes - to_nodes

        # Find modified nodes
        common_nodes = from_nodes & to_nodes
        for node_id in common_nodes:
            from_node = from_data["nodes"][node_id]
            to_node = to_data["nodes"][node_id]
            if from_node != to_node:
                diff.nodes_modified.add(node_id)

        # Compare connections
        from_conns = {
            (c["source_node"], c["source_port"], c["target_node"], c["target_port"])
            for c in from_data.get("connections", [])
        }
        to_conns = {
            (c["source_node"], c["source_port"], c["target_node"], c["target_port"])
            for c in to_data.get("connections", [])
        }

        for conn in to_conns - from_conns:
            diff.connections_added.append(
                {
                    "source_node": conn[0],
                    "source_port": conn[1],
                    "target_node": conn[2],
                    "target_port": conn[3],
                }
            )

        for conn in from_conns - to_conns:
            diff.connections_removed.append(
                {
                    "source_node": conn[0],
                    "source_port": conn[1],
                    "target_node": conn[2],
                    "target_port": conn[3],
                }
            )

        # Compare variables
        from_vars = set(from_data.get("variables", {}).keys())
        to_vars = set(to_data.get("variables", {}).keys())

        diff.variables_added = to_vars - from_vars
        diff.variables_removed = from_vars - to_vars

        common_vars = from_vars & to_vars
        for var_name in common_vars:
            from_var = from_data["variables"][var_name]
            to_var = to_data["variables"][var_name]
            if from_var != to_var:
                diff.variables_modified.add(var_name)

        # Compare settings
        from_settings = from_data.get("settings", {})
        to_settings = to_data.get("settings", {})

        all_setting_keys = set(from_settings.keys()) | set(to_settings.keys())
        for key in all_setting_keys:
            from_val = from_settings.get(key)
            to_val = to_settings.get(key)
            if from_val != to_val:
                diff.settings_changed[key] = (from_val, to_val)

        return diff

    def check_compatibility(self, from_version: str, to_version: str) -> CompatibilityResult:
        """
        Check backward compatibility between versions.

        Args:
            from_version: Base version to compare against
            to_version: New version to check

        Returns:
            CompatibilityResult with breaking changes
        """
        result = CompatibilityResult(is_compatible=True)

        diff = self.generate_diff(from_version, to_version)
        if not diff:
            result.is_compatible = False
            result.warnings.append("Could not generate diff between versions")
            return result

        from_ver = self.versions.get(from_version)
        to_ver = self.versions.get(to_version)

        if not from_ver or not to_ver:
            result.is_compatible = False
            return result

        from_data = from_ver.workflow_data
        to_data = to_ver.workflow_data

        # Check for removed nodes (breaking)
        for node_id in diff.nodes_removed:
            node_data = from_data["nodes"][node_id]
            result.breaking_changes.append(
                BreakingChange(
                    change_type=BreakingChangeType.NODE_REMOVED,
                    element_id=node_id,
                    description=f"Node '{node_data.get('node_type', 'unknown')}' was removed",
                    old_value=node_data.get("node_type"),
                )
            )

        # Check for modified nodes - look for type changes
        for node_id in diff.nodes_modified:
            from_node = from_data["nodes"][node_id]
            to_node = to_data["nodes"][node_id]

            if from_node.get("node_type") != to_node.get("node_type"):
                result.breaking_changes.append(
                    BreakingChange(
                        change_type=BreakingChangeType.NODE_TYPE_CHANGED,
                        element_id=node_id,
                        description="Node type was changed",
                        old_value=from_node.get("node_type"),
                        new_value=to_node.get("node_type"),
                    )
                )

            # Check for removed ports
            from_inputs = set(from_node.get("input_ports", {}).keys())
            to_inputs = set(to_node.get("input_ports", {}).keys())
            removed_inputs = from_inputs - to_inputs

            for port_name in removed_inputs:
                result.breaking_changes.append(
                    BreakingChange(
                        change_type=BreakingChangeType.PORT_REMOVED,
                        element_id=f"{node_id}.{port_name}",
                        description=f"Input port '{port_name}' was removed from node",
                    )
                )

        # Check for removed variables (breaking if used)
        for var_name in diff.variables_removed:
            result.breaking_changes.append(
                BreakingChange(
                    change_type=BreakingChangeType.VARIABLE_REMOVED,
                    element_id=var_name,
                    description=f"Variable '{var_name}' was removed",
                    severity="warning",  # May not be breaking if unused
                )
            )

        # Check for variable type changes
        for var_name in diff.variables_modified:
            from_var = from_data["variables"][var_name]
            to_var = to_data["variables"][var_name]

            from_type = (
                from_var.get("type") if isinstance(from_var, dict) else type(from_var).__name__
            )
            to_type = to_var.get("type") if isinstance(to_var, dict) else type(to_var).__name__

            if from_type != to_type:
                result.breaking_changes.append(
                    BreakingChange(
                        change_type=BreakingChangeType.VARIABLE_TYPE_CHANGED,
                        element_id=var_name,
                        description=f"Variable type changed from {from_type} to {to_type}",
                        old_value=from_type,
                        new_value=to_type,
                    )
                )

        # Check removed connections - may break execution flow
        for conn in diff.connections_removed:
            result.breaking_changes.append(
                BreakingChange(
                    change_type=BreakingChangeType.CONNECTION_BROKEN,
                    element_id=f"{conn['source_node']}.{conn['source_port']}",
                    description=f"Connection from {conn['source_node']} to {conn['target_node']} was removed",
                    severity="warning",
                )
            )

        # Determine overall compatibility
        error_changes = [bc for bc in result.breaking_changes if bc.severity == "error"]
        result.is_compatible = len(error_changes) == 0
        result.migration_required = diff.has_changes

        # Check if auto-migration is possible
        result.auto_migratable = all(
            bc.change_type
            not in (
                BreakingChangeType.NODE_REMOVED,
                BreakingChangeType.NODE_TYPE_CHANGED,
            )
            for bc in result.breaking_changes
        )

        return result

    def can_rollback_to(self, version_str: str) -> Tuple[bool, str]:
        """
        Check if rollback to a version is safe.

        Args:
            version_str: Target rollback version

        Returns:
            Tuple of (can_rollback, reason)
        """
        version = self.versions.get(version_str)
        if not version:
            return False, f"Version {version_str} not found"

        if version.is_archived():
            return False, "Cannot rollback to archived version"

        # Check compatibility with current active version
        if self._active_version:
            compat = self.check_compatibility(version_str, self._active_version)
            if compat.has_breaking_changes:
                return (
                    False,
                    f"Rollback would cause {len(compat.breaking_changes)} breaking changes",
                )

        return True, "Rollback is safe"

    def get_versions_by_status(self, status: VersionStatus) -> List[WorkflowVersion]:
        """Get all versions with a specific status."""
        return [v for v in self.versions.values() if v.status == status]

    def get_version_timeline(self) -> List[Dict[str, Any]]:
        """Get ordered timeline of all versions."""
        return [
            {
                "version": v_str,
                "status": self.versions[v_str].status.name,
                "created_at": self.versions[v_str].created_at.isoformat(),
                "created_by": self.versions[v_str].created_by,
                "change_summary": self.versions[v_str].change_summary,
            }
            for v_str in self._version_order
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize version history."""
        return {
            "workflow_id": self.workflow_id,
            "versions": {k: v.to_dict() for k, v in self.versions.items()},
            "version_order": self._version_order,
            "active_version": self._active_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionHistory":
        """Create instance from dictionary."""
        history = cls(workflow_id=data["workflow_id"])
        history._version_order = data.get("version_order", [])
        history._active_version = data.get("active_version")

        for v_str, v_data in data.get("versions", {}).items():
            history.versions[v_str] = WorkflowVersion.from_dict(v_data)

        return history

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"VersionHistory(workflow_id={self.workflow_id}, "
            f"versions={self.version_count}, "
            f"active={self._active_version})"
        )

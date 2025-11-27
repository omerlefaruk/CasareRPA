"""
CasareRPA - Domain Entities: Project and Scenario
Represents project hierarchy and organization in the domain layer.

These are pure domain entities moved from core.project_schema.
For backward compatibility, core.project_schema re-exports these classes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


# ============================================================================
# CONSTANTS
# ============================================================================

PROJECT_SCHEMA_VERSION: str = "1.0.0"


def generate_project_id() -> str:
    """Generate unique project ID."""
    return f"proj_{uuid.uuid4().hex[:8]}"


def generate_scenario_id() -> str:
    """Generate unique scenario ID."""
    return f"scen_{uuid.uuid4().hex[:8]}"


# ============================================================================
# ENUMS
# ============================================================================


class VariableScope(Enum):
    """Scope for variable storage."""
    GLOBAL = "global"
    PROJECT = "project"
    SCENARIO = "scenario"


class VariableType(Enum):
    """Supported variable data types."""
    STRING = "String"
    INTEGER = "Integer"
    FLOAT = "Float"
    BOOLEAN = "Boolean"
    LIST = "List"
    DICT = "Dict"
    DATATABLE = "DataTable"


# ============================================================================
# PROJECT VARIABLE
# ============================================================================


@dataclass
class ProjectVariable:
    """
    A variable definition with metadata for project/global scope.

    Domain entity representing a typed variable with metadata.

    Attributes:
        name: Variable name (must be valid Python identifier)
        type: Variable type (String, Integer, Float, Boolean, List, Dict, DataTable)
        default_value: Default value for the variable
        description: Optional description
        sensitive: If True, value should be masked in UI
        readonly: If True, cannot be modified at runtime
    """
    name: str
    type: str = "String"
    default_value: Any = ""
    description: str = ""
    sensitive: bool = False
    readonly: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "default_value": self.default_value,
            "description": self.description,
            "sensitive": self.sensitive,
            "readonly": self.readonly,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectVariable":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            type=data.get("type", "String"),
            default_value=data.get("default_value", ""),
            description=data.get("description", ""),
            sensitive=data.get("sensitive", False),
            readonly=data.get("readonly", False),
        )


# ============================================================================
# VARIABLES FILE
# ============================================================================


@dataclass
class VariablesFile:
    """
    Container for variables stored in variables.json files.
    Used for both project and global variable storage.
    """
    scope: VariableScope = VariableScope.PROJECT
    variables: Dict[str, ProjectVariable] = field(default_factory=dict)
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "scope": self.scope.value,
            "variables": {name: var.to_dict() for name, var in self.variables.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VariablesFile":
        """Create from dictionary."""
        scope_str = data.get("scope", "project")
        variables_data = data.get("variables", {})

        variables = {
            name: ProjectVariable.from_dict(var_data)
            for name, var_data in variables_data.items()
        }

        return cls(
            scope=VariableScope(scope_str),
            variables=variables,
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    def get_variable(self, name: str) -> Optional[ProjectVariable]:
        """Get variable by name."""
        return self.variables.get(name)

    def set_variable(self, variable: ProjectVariable) -> None:
        """Add or update a variable."""
        self.variables[variable.name] = variable

    def remove_variable(self, name: str) -> bool:
        """Remove a variable. Returns True if removed."""
        if name in self.variables:
            del self.variables[name]
            return True
        return False

    def get_default_values(self) -> Dict[str, Any]:
        """Get dictionary of variable names to their default values."""
        return {name: var.default_value for name, var in self.variables.items()}


# ============================================================================
# CREDENTIAL BINDING
# ============================================================================


@dataclass
class CredentialBinding:
    """
    Maps a local alias to a Vault credential path.

    Domain entity for credential reference management.

    Attributes:
        alias: Local name used in workflows (e.g., "erp_login")
        vault_path: Path in HashiCorp Vault (e.g., "projects/proj_123/erp_creds")
        credential_type: Type of credential (username_password, api_key, etc.)
        description: Description of what this credential is for
        required: If True, workflow execution fails if credential is missing
    """
    alias: str
    vault_path: str
    credential_type: str = "username_password"
    description: str = ""
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "alias": self.alias,
            "vault_path": self.vault_path,
            "credential_type": self.credential_type,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CredentialBinding":
        """Create from dictionary."""
        return cls(
            alias=data.get("alias", ""),
            vault_path=data.get("vault_path", ""),
            credential_type=data.get("credential_type", "username_password"),
            description=data.get("description", ""),
            required=data.get("required", True),
        )


# ============================================================================
# CREDENTIAL BINDINGS FILE
# ============================================================================


@dataclass
class CredentialBindingsFile:
    """Container for credential bindings in credentials.json files."""
    scope: str = "project"
    bindings: Dict[str, CredentialBinding] = field(default_factory=dict)
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "scope": self.scope,
            "bindings": {
                alias: binding.to_dict() for alias, binding in self.bindings.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CredentialBindingsFile":
        """Create from dictionary."""
        bindings_data = data.get("bindings", {})

        bindings = {
            alias: CredentialBinding.from_dict(binding_data)
            for alias, binding_data in bindings_data.items()
        }

        return cls(
            scope=data.get("scope", "project"),
            bindings=bindings,
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    def get_binding(self, alias: str) -> Optional[CredentialBinding]:
        """Get binding by alias."""
        return self.bindings.get(alias)

    def set_binding(self, binding: CredentialBinding) -> None:
        """Add or update a binding."""
        self.bindings[binding.alias] = binding

    def remove_binding(self, alias: str) -> bool:
        """Remove a binding. Returns True if removed."""
        if alias in self.bindings:
            del self.bindings[alias]
            return True
        return False

    def resolve_vault_path(self, alias: str) -> Optional[str]:
        """Get the Vault path for an alias."""
        binding = self.bindings.get(alias)
        return binding.vault_path if binding else None


# ============================================================================
# PROJECT SETTINGS
# ============================================================================


@dataclass
class ProjectSettings:
    """
    Project-level execution and behavior settings.

    Domain value object for project configuration.
    """
    default_browser: str = "chromium"
    stop_on_error: bool = True
    timeout_seconds: int = 30
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "default_browser": self.default_browser,
            "stop_on_error": self.stop_on_error,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectSettings":
        """Create from dictionary."""
        return cls(
            default_browser=data.get("default_browser", "chromium"),
            stop_on_error=data.get("stop_on_error", True),
            timeout_seconds=data.get("timeout_seconds", 30),
            retry_count=data.get("retry_count", 0),
        )


# ============================================================================
# PROJECT
# ============================================================================


@dataclass
class Project:
    """
    Domain entity representing a CasareRPA project.

    A project is a folder containing workflows, scenarios, variables,
    and credential bindings organized for a specific automation goal.

    Attributes:
        id: Unique project identifier (proj_uuid8)
        name: Human-readable project name
        description: Project description
        author: Project creator
        created_at: Creation timestamp
        modified_at: Last modification timestamp
        tags: List of tags for categorization
        settings: Project-level execution settings
    """
    id: str
    name: str
    description: str = ""
    author: str = ""
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    schema_version: str = PROJECT_SCHEMA_VERSION

    # Runtime properties (not serialized)
    _path: Optional[Path] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    @property
    def path(self) -> Optional[Path]:
        """Get project folder path."""
        return self._path

    @path.setter
    def path(self, value: Path) -> None:
        """Set project folder path."""
        self._path = value

    @property
    def scenarios_dir(self) -> Optional[Path]:
        """Get scenarios directory path."""
        if self._path:
            return self._path / "scenarios"
        return None

    @property
    def project_file(self) -> Optional[Path]:
        """Get project.json file path."""
        if self._path:
            return self._path / "project.json"
        return None

    @property
    def variables_file(self) -> Optional[Path]:
        """Get variables.json file path."""
        if self._path:
            return self._path / "variables.json"
        return None

    @property
    def credentials_file(self) -> Optional[Path]:
        """Get credentials.json file path."""
        if self._path:
            return self._path / "credentials.json"
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for project.json."""
        return {
            "$schema_version": self.schema_version,
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "tags": self.tags,
            "settings": self.settings.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Project":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        return cls(
            id=data.get("id", generate_project_id()),
            name=data.get("name", "Untitled Project"),
            description=data.get("description", ""),
            author=data.get("author", ""),
            created_at=created_at,
            modified_at=modified_at,
            tags=data.get("tags", []),
            settings=ProjectSettings.from_dict(data.get("settings", {})),
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    @classmethod
    def create_new(cls, name: str, path: Path, **kwargs: Any) -> "Project":
        """
        Factory method to create a new project.

        Args:
            name: Project name
            path: Path where project will be stored
            **kwargs: Additional project attributes

        Returns:
            New Project instance with generated ID
        """
        project = cls(id=generate_project_id(), name=name, **kwargs)
        project._path = path
        return project

    def touch_modified(self) -> None:
        """Update modified timestamp to current time."""
        self.modified_at = datetime.now()

    def __repr__(self) -> str:
        """String representation."""
        return f"Project(id='{self.id}', name='{self.name}')"


# ============================================================================
# SCENARIO EXECUTION SETTINGS
# ============================================================================


@dataclass
class ScenarioExecutionSettings:
    """
    Execution-time overrides for a scenario.

    Domain value object for scenario execution configuration.
    """
    priority: str = "normal"  # low, normal, high, critical
    timeout_override: Optional[int] = None
    environment_override: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "priority": self.priority,
            "timeout_override": self.timeout_override,
            "environment_override": self.environment_override,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioExecutionSettings":
        """Create from dictionary."""
        return cls(
            priority=data.get("priority", "normal"),
            timeout_override=data.get("timeout_override"),
            environment_override=data.get("environment_override"),
        )


# ============================================================================
# SCENARIO
# ============================================================================


@dataclass
class Scenario:
    """
    Domain entity representing a scenario: a workflow + data bundle.

    Scenarios embed the full workflow JSON and include specific
    variable values and credential bindings for execution.

    Attributes:
        id: Unique scenario identifier (scen_uuid8)
        name: Human-readable scenario name
        project_id: Parent project ID
        description: Scenario description
        workflow: Embedded workflow (full WorkflowSchema dict)
        variable_values: Variable values for this scenario
        credential_bindings: Credential alias -> binding alias mappings
        execution_settings: Execution overrides
    """
    id: str
    name: str
    project_id: str
    description: str = ""
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    # Embedded workflow (full WorkflowSchema serialized)
    workflow: Dict[str, Any] = field(default_factory=dict)

    # Variable values for this scenario (overrides defaults)
    variable_values: Dict[str, Any] = field(default_factory=dict)

    # Credential alias -> vault path mappings for this scenario
    credential_bindings: Dict[str, str] = field(default_factory=dict)

    # Execution settings
    execution_settings: ScenarioExecutionSettings = field(
        default_factory=ScenarioExecutionSettings
    )

    # Triggers for this scenario
    triggers: List[Dict[str, Any]] = field(default_factory=list)

    schema_version: str = PROJECT_SCHEMA_VERSION

    # Runtime properties
    _file_path: Optional[Path] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    @property
    def file_path(self) -> Optional[Path]:
        """Get scenario file path."""
        return self._file_path

    @file_path.setter
    def file_path(self, value: Path) -> None:
        """Set scenario file path."""
        self._file_path = value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for scenario JSON file."""
        return {
            "$schema_version": self.schema_version,
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "tags": self.tags,
            "workflow": self.workflow,
            "variable_values": self.variable_values,
            "credential_bindings": self.credential_bindings,
            "execution_settings": self.execution_settings.to_dict(),
            "triggers": self.triggers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        return cls(
            id=data.get("id", generate_scenario_id()),
            name=data.get("name", "Untitled Scenario"),
            project_id=data.get("project_id", ""),
            description=data.get("description", ""),
            created_at=created_at,
            modified_at=modified_at,
            tags=data.get("tags", []),
            workflow=data.get("workflow", {}),
            variable_values=data.get("variable_values", {}),
            credential_bindings=data.get("credential_bindings", {}),
            execution_settings=ScenarioExecutionSettings.from_dict(
                data.get("execution_settings", {})
            ),
            triggers=data.get("triggers", []),
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    @classmethod
    def create_new(
        cls,
        name: str,
        project_id: str,
        workflow: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "Scenario":
        """
        Factory method to create a new scenario.

        Args:
            name: Scenario name
            project_id: Parent project ID
            workflow: Optional workflow definition
            **kwargs: Additional scenario attributes

        Returns:
            New Scenario instance with generated ID
        """
        return cls(
            id=generate_scenario_id(),
            name=name,
            project_id=project_id,
            workflow=workflow or {},
            **kwargs,
        )

    def touch_modified(self) -> None:
        """Update modified timestamp to current time."""
        self.modified_at = datetime.now()

    def get_variable_value(self, name: str, default: Any = None) -> Any:
        """
        Get a variable value, with optional default.

        Args:
            name: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self.variable_values.get(name, default)

    def set_variable_value(self, name: str, value: Any) -> None:
        """
        Set a variable value.

        Args:
            name: Variable name
            value: Value to set
        """
        self.variable_values[name] = value

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Scenario(id='{self.id}', name='{self.name}', project='{self.project_id}')"
        )


# ============================================================================
# PROJECTS INDEX
# ============================================================================


@dataclass
class ProjectIndexEntry:
    """
    Entry in the projects index for quick project lookup.

    Domain value object for project registry tracking.
    """
    id: str
    name: str
    path: str
    last_opened: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "path": self.path,
            "last_opened": self.last_opened.isoformat() if self.last_opened else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectIndexEntry":
        """Create from dictionary."""
        last_opened = None
        if data.get("last_opened"):
            last_opened = datetime.fromisoformat(data["last_opened"])

        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            path=data.get("path", ""),
            last_opened=last_opened,
        )


@dataclass
class ProjectsIndex:
    """
    Index of all known projects for the application.

    Domain entity managing the project registry.
    Stored in CONFIG_DIR/projects_index.json
    """
    projects: List[ProjectIndexEntry] = field(default_factory=list)
    recent_limit: int = 10
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "projects": [p.to_dict() for p in self.projects],
            "recent_limit": self.recent_limit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectsIndex":
        """Create from dictionary."""
        projects = [ProjectIndexEntry.from_dict(p) for p in data.get("projects", [])]
        return cls(
            projects=projects,
            recent_limit=data.get("recent_limit", 10),
            schema_version=data.get("$schema_version", PROJECT_SCHEMA_VERSION),
        )

    def add_project(self, project: Project) -> None:
        """
        Add or update a project in the index.

        Args:
            project: Project to add
        """
        # Remove existing entry if present
        self.projects = [p for p in self.projects if p.id != project.id]

        # Add new entry at the beginning
        entry = ProjectIndexEntry(
            id=project.id,
            name=project.name,
            path=str(project.path) if project.path else "",
            last_opened=datetime.now(),
        )
        self.projects.insert(0, entry)

        # Trim to recent_limit
        self.projects = self.projects[: self.recent_limit]

    def remove_project(self, project_id: str) -> bool:
        """
        Remove a project from the index.

        Args:
            project_id: ID of project to remove

        Returns:
            True if project was removed
        """
        original_len = len(self.projects)
        self.projects = [p for p in self.projects if p.id != project_id]
        return len(self.projects) < original_len

    def get_project(self, project_id: str) -> Optional[ProjectIndexEntry]:
        """
        Get a project entry by ID.

        Args:
            project_id: Project ID to find

        Returns:
            ProjectIndexEntry if found, None otherwise
        """
        for p in self.projects:
            if p.id == project_id:
                return p
        return None

    def get_recent_projects(
        self, limit: Optional[int] = None
    ) -> List[ProjectIndexEntry]:
        """
        Get recently opened projects.

        Args:
            limit: Max number of projects to return

        Returns:
            List of recent project entries
        """
        limit = limit or self.recent_limit
        return self.projects[:limit]

    def update_last_opened(self, project_id: str) -> None:
        """
        Update the last_opened timestamp for a project.

        Args:
            project_id: ID of project to update
        """
        for p in self.projects:
            if p.id == project_id:
                p.last_opened = datetime.now()
                # Move to front of list
                self.projects.remove(p)
                self.projects.insert(0, p)
                break

"""
CasareRPA - Scenario Entity

Scenario domain entity - a workflow + data bundle.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from casare_rpa.domain.entities.project.base import (
    PROJECT_SCHEMA_VERSION,
    generate_scenario_id,
)
from casare_rpa.domain.entities.project.settings import ScenarioExecutionSettings


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
    created_at: datetime | None = None
    modified_at: datetime | None = None
    tags: list[str] = field(default_factory=list)

    # Embedded workflow (full WorkflowSchema serialized)
    workflow: dict[str, Any] = field(default_factory=dict)

    # Variable values for this scenario (overrides defaults)
    variable_values: dict[str, Any] = field(default_factory=dict)

    # Credential alias -> vault path mappings for this scenario
    credential_bindings: dict[str, str] = field(default_factory=dict)

    # Execution settings
    execution_settings: ScenarioExecutionSettings = field(default_factory=ScenarioExecutionSettings)

    # Triggers for this scenario
    triggers: list[dict[str, Any]] = field(default_factory=list)

    schema_version: str = PROJECT_SCHEMA_VERSION

    # Runtime properties
    _file_path: Path | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize timestamps and validate required fields."""
        # Validation
        self._validate_required_fields()

        # Initialize timestamps
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    def _validate_required_fields(self) -> None:
        """Validate required scenario fields."""
        if not self.id or not self.id.strip():
            raise ValueError("Scenario id cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Scenario name cannot be empty")
        if not self.project_id or not self.project_id.strip():
            raise ValueError("Scenario project_id cannot be empty")
        if len(self.name) > 255:
            raise ValueError(f"Scenario name too long: {len(self.name)} chars (max 255)")

    @property
    def file_path(self) -> Path | None:
        """Get scenario file path."""
        return self._file_path

    @file_path.setter
    def file_path(self, value: Path) -> None:
        """Set scenario file path."""
        self._file_path = value

    def to_dict(self) -> dict[str, Any]:
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
    def from_dict(cls, data: dict[str, Any]) -> "Scenario":
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
        workflow: dict[str, Any] | None = None,
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
        return f"Scenario(id='{self.id}', name='{self.name}', project='{self.project_id}')"

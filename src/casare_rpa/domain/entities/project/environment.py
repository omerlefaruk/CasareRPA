"""
CasareRPA - Environment Entity

Environment configuration for dev/staging/prod with variable inheritance.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EnvironmentType(Enum):
    """Standard environment types with inheritance order."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    CUSTOM = "custom"


# Inheritance chain: development -> staging -> production
ENVIRONMENT_INHERITANCE = {
    EnvironmentType.STAGING: EnvironmentType.DEVELOPMENT,
    EnvironmentType.PRODUCTION: EnvironmentType.STAGING,
}


def generate_environment_id() -> str:
    """Generate unique environment ID."""
    return f"env_{uuid.uuid4().hex[:8]}"


@dataclass
class EnvironmentSettings:
    """
    Environment-specific execution settings.

    Overrides project-level settings when environment is active.
    """

    api_base_urls: dict[str, str] = field(default_factory=dict)
    timeout_override: int | None = None
    retry_count_override: int | None = None
    feature_flags: dict[str, bool] = field(default_factory=dict)
    headless_browser: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "api_base_urls": self.api_base_urls,
            "timeout_override": self.timeout_override,
            "retry_count_override": self.retry_count_override,
            "feature_flags": self.feature_flags,
            "headless_browser": self.headless_browser,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EnvironmentSettings":
        """Create from dictionary."""
        return cls(
            api_base_urls=data.get("api_base_urls", {}),
            timeout_override=data.get("timeout_override"),
            retry_count_override=data.get("retry_count_override"),
            feature_flags=data.get("feature_flags", {}),
            headless_browser=data.get("headless_browser"),
        )


@dataclass
class Environment:
    """
    Domain entity representing an execution environment.

    Environments allow different configurations for dev/staging/prod.
    Supports variable inheritance: staging inherits from dev, prod from staging.

    Attributes:
        id: Unique environment identifier (env_uuid8)
        name: Display name (e.g., "Development", "Staging", "Production")
        env_type: Environment type for inheritance chain
        description: Environment description
        variables: Environment-specific variable overrides
        credential_overrides: Map of alias -> credential_id per environment
        settings: Environment-specific execution settings
        is_default: Whether this is the default environment
        color: Hex color for UI display
        icon: Icon name for UI
        created_at: Creation timestamp
        modified_at: Last modification timestamp
    """

    id: str
    name: str
    env_type: EnvironmentType = EnvironmentType.DEVELOPMENT
    description: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    credential_overrides: dict[str, str] = field(default_factory=dict)
    settings: EnvironmentSettings = field(default_factory=EnvironmentSettings)
    is_default: bool = False
    color: str = "#4CAF50"  # Green for dev
    icon: str = "environment"
    created_at: datetime | None = None
    modified_at: datetime | None = None

    def __post_init__(self) -> None:
        """Initialize timestamps and set default color by type."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

        # Set default colors by environment type
        if self.color == "#4CAF50":  # Only if using default
            self.color = self._get_default_color()

    def _get_default_color(self) -> str:
        """Get default color based on environment type."""
        colors = {
            EnvironmentType.DEVELOPMENT: "#4CAF50",  # Green
            EnvironmentType.STAGING: "#FF9800",  # Orange
            EnvironmentType.PRODUCTION: "#F44336",  # Red
            EnvironmentType.CUSTOM: "#9C27B0",  # Purple
        }
        return colors.get(self.env_type, "#607D8B")

    def get_parent_type(self) -> EnvironmentType | None:
        """Get parent environment type for inheritance."""
        return ENVIRONMENT_INHERITANCE.get(self.env_type)

    def resolve_variables(self, parent_variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Resolve variables with inheritance from parent environment.

        Args:
            parent_variables: Variables from parent environment (if any)

        Returns:
            Merged variables with this environment's overrides taking precedence
        """
        if parent_variables is None:
            return self.variables.copy()

        # Parent variables as base, override with this environment's variables
        resolved = parent_variables.copy()
        resolved.update(self.variables)
        return resolved

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "env_type": self.env_type.value,
            "description": self.description,
            "variables": self.variables,
            "credential_overrides": self.credential_overrides,
            "settings": self.settings.to_dict(),
            "is_default": self.is_default,
            "color": self.color,
            "icon": self.icon,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Environment":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        env_type_str = data.get("env_type", "development")
        try:
            env_type = EnvironmentType(env_type_str)
        except ValueError:
            env_type = EnvironmentType.CUSTOM

        return cls(
            id=data.get("id", generate_environment_id()),
            name=data.get("name", "Unnamed Environment"),
            env_type=env_type,
            description=data.get("description", ""),
            variables=data.get("variables", {}),
            credential_overrides=data.get("credential_overrides", {}),
            settings=EnvironmentSettings.from_dict(data.get("settings", {})),
            is_default=data.get("is_default", False),
            color=data.get("color", "#4CAF50"),
            icon=data.get("icon", "environment"),
            created_at=created_at,
            modified_at=modified_at,
        )

    @classmethod
    def create_default_environments(cls) -> list["Environment"]:
        """
        Factory method to create default dev/staging/prod environments.

        Returns:
            List of three Environment instances
        """
        return [
            cls(
                id=generate_environment_id(),
                name="Development",
                env_type=EnvironmentType.DEVELOPMENT,
                description="Local development environment",
                is_default=True,
                color="#4CAF50",
            ),
            cls(
                id=generate_environment_id(),
                name="Staging",
                env_type=EnvironmentType.STAGING,
                description="Pre-production testing environment",
                is_default=False,
                color="#FF9800",
            ),
            cls(
                id=generate_environment_id(),
                name="Production",
                env_type=EnvironmentType.PRODUCTION,
                description="Live production environment",
                is_default=False,
                color="#F44336",
            ),
        ]

    def touch_modified(self) -> None:
        """Update modified timestamp to current time."""
        self.modified_at = datetime.now()

    def __repr__(self) -> str:
        """String representation."""
        return f"Environment(id='{self.id}', name='{self.name}', type={self.env_type.value})"

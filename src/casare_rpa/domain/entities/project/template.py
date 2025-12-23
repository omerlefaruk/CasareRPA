"""
CasareRPA - Project Template Entity

Project templates for quick-start workflows.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from casare_rpa.domain.entities.project.settings import ProjectSettings


class TemplateDifficulty(Enum):
    """Template difficulty levels."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TemplateCategory(Enum):
    """Template categories."""

    WEB_SCRAPING = "Web Scraping"
    GOOGLE_WORKSPACE = "Google Workspace"
    DESKTOP_AUTOMATION = "Desktop Automation"
    DATA_ETL = "Data ETL"
    EMAIL_DOCUMENTS = "Email & Documents"
    API_WEBHOOKS = "API & Webhooks"
    NOTIFICATIONS = "Notifications"
    OFFICE_AUTOMATION = "Office Automation"
    CUSTOM = "Custom"


def generate_template_id() -> str:
    """Generate unique template ID."""
    return f"tmpl_{uuid.uuid4().hex[:8]}"


@dataclass
class TemplateVariable:
    """Variable definition for templates."""

    name: str
    data_type: str = "String"
    default_value: Any = ""
    description: str = ""
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "default_value": self.default_value,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateVariable":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            data_type=data.get("data_type", "String"),
            default_value=data.get("default_value", ""),
            description=data.get("description", ""),
            required=data.get("required", False),
        )


@dataclass
class TemplateCredential:
    """Credential requirement for templates."""

    alias: str
    credential_type: str = "username_password"
    description: str = ""
    required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "alias": self.alias,
            "credential_type": self.credential_type,
            "description": self.description,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateCredential":
        """Create from dictionary."""
        return cls(
            alias=data.get("alias", ""),
            credential_type=data.get("credential_type", "username_password"),
            description=data.get("description", ""),
            required=data.get("required", False),
        )


@dataclass
class ProjectTemplate:
    """
    Domain entity representing a project template.

    Templates provide quick-start workflows with pre-configured nodes,
    variables, and credential requirements.

    Attributes:
        id: Unique template identifier (tmpl_uuid8)
        name: Template display name
        description: Template description
        category: Template category for organization
        icon: Icon name for UI
        color: Hex color for UI display
        tags: List of tags for filtering

        base_workflow: Starter workflow JSON structure
        default_variables: Variables to create in new project
        default_credentials: Credential requirements
        default_settings: Project settings

        version: Template version
        author: Template creator
        difficulty: Difficulty level
        estimated_nodes: Approximate node count
        is_builtin: Whether this is a built-in template
        is_public: Whether template is shared

        created_at: Creation timestamp
        modified_at: Last modification timestamp
    """

    id: str
    name: str
    description: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    icon: str = "template"
    color: str = "#2196F3"
    tags: List[str] = field(default_factory=list)

    # Template content
    base_workflow: Dict[str, Any] = field(default_factory=dict)
    default_variables: List[TemplateVariable] = field(default_factory=list)
    default_credentials: List[TemplateCredential] = field(default_factory=list)
    default_settings: ProjectSettings = field(default_factory=ProjectSettings)

    # Metadata
    version: str = "1.0.0"
    author: str = "CasareRPA"
    difficulty: TemplateDifficulty = TemplateDifficulty.BEGINNER
    estimated_nodes: int = 0
    is_builtin: bool = False
    is_public: bool = True

    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "icon": self.icon,
            "color": self.color,
            "tags": self.tags,
            "base_workflow": self.base_workflow,
            "default_variables": [v.to_dict() for v in self.default_variables],
            "default_credentials": [c.to_dict() for c in self.default_credentials],
            "default_settings": self.default_settings.to_dict(),
            "version": self.version,
            "author": self.author,
            "difficulty": self.difficulty.value,
            "estimated_nodes": self.estimated_nodes,
            "is_builtin": self.is_builtin,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectTemplate":
        """Create from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        # Parse category
        category_str = data.get("category", "Custom")
        try:
            category = TemplateCategory(category_str)
        except ValueError:
            category = TemplateCategory.CUSTOM

        # Parse difficulty
        difficulty_str = data.get("difficulty", "beginner")
        try:
            difficulty = TemplateDifficulty(difficulty_str)
        except ValueError:
            difficulty = TemplateDifficulty.BEGINNER

        return cls(
            id=data.get("id", generate_template_id()),
            name=data.get("name", "Unnamed Template"),
            description=data.get("description", ""),
            category=category,
            icon=data.get("icon", "template"),
            color=data.get("color", "#2196F3"),
            tags=data.get("tags", []),
            base_workflow=data.get("base_workflow", {}),
            default_variables=[
                TemplateVariable.from_dict(v) for v in data.get("default_variables", [])
            ],
            default_credentials=[
                TemplateCredential.from_dict(c) for c in data.get("default_credentials", [])
            ],
            default_settings=ProjectSettings.from_dict(data.get("default_settings", {})),
            version=data.get("version", "1.0.0"),
            author=data.get("author", "CasareRPA"),
            difficulty=difficulty,
            estimated_nodes=data.get("estimated_nodes", 0),
            is_builtin=data.get("is_builtin", False),
            is_public=data.get("is_public", True),
            created_at=created_at,
            modified_at=modified_at,
        )

    @classmethod
    def create_new(cls, name: str, category: TemplateCategory, **kwargs: Any) -> "ProjectTemplate":
        """
        Factory method to create a new template.

        Args:
            name: Template name
            category: Template category
            **kwargs: Additional template attributes

        Returns:
            New ProjectTemplate instance with generated ID
        """
        return cls(
            id=generate_template_id(),
            name=name,
            category=category,
            **kwargs,
        )

    def touch_modified(self) -> None:
        """Update modified timestamp to current time."""
        self.modified_at = datetime.now()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ProjectTemplate(id='{self.id}', name='{self.name}', category={self.category.value})"
        )


@dataclass
class TemplatesFile:
    """
    Container for templates stored in templates.json.

    Can store both built-in and user-created templates.
    """

    templates: Dict[str, ProjectTemplate] = field(default_factory=dict)
    schema_version: str = "2.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "$schema_version": self.schema_version,
            "templates": {tmpl_id: tmpl.to_dict() for tmpl_id, tmpl in self.templates.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplatesFile":
        """Create from dictionary."""
        templates_data = data.get("templates", {})

        templates = {
            tmpl_id: ProjectTemplate.from_dict(tmpl_data)
            for tmpl_id, tmpl_data in templates_data.items()
        }

        return cls(
            templates=templates,
            schema_version=data.get("$schema_version", "2.0.0"),
        )

    def get_template(self, template_id: str) -> Optional[ProjectTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)

    def add_template(self, template: ProjectTemplate) -> None:
        """Add or update a template."""
        self.templates[template.id] = template

    def remove_template(self, template_id: str) -> bool:
        """Remove a template. Returns True if removed."""
        if template_id in self.templates:
            del self.templates[template_id]
            return True
        return False

    def get_by_category(self, category: TemplateCategory) -> List[ProjectTemplate]:
        """Get all templates in a category."""
        return [t for t in self.templates.values() if t.category == category]

    def get_builtin(self) -> List[ProjectTemplate]:
        """Get all built-in templates."""
        return [t for t in self.templates.values() if t.is_builtin]

    def get_public(self) -> List[ProjectTemplate]:
        """Get all public templates."""
        return [t for t in self.templates.values() if t.is_public]

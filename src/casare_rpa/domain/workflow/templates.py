"""
CasareRPA - Domain Model: Workflow Templates

Template models for rapid workflow creation with parameterized configurations.
Templates define reusable workflow patterns that can be instantiated with
custom parameter values.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import re
import uuid

from loguru import logger


class ReviewStatus(Enum):
    """Status of a template review."""

    PENDING = "pending"
    PUBLISHED = "published"
    HIDDEN = "hidden"
    REMOVED = "removed"


class TemplateCategory(Enum):
    """Categories for organizing workflow templates."""

    WEB_SCRAPING = "web_scraping"
    DATA_ENTRY = "data_entry"
    REPORT_GENERATION = "report_generation"
    API_INTEGRATION = "api_integration"
    FILE_OPERATIONS = "file_operations"
    EMAIL_PROCESSING = "email_processing"
    DATABASE_OPERATIONS = "database_operations"
    DESKTOP_AUTOMATION = "desktop_automation"
    PDF_PROCESSING = "pdf_processing"
    EXCEL_AUTOMATION = "excel_automation"
    GENERAL = "general"
    CUSTOM = "custom"

    @classmethod
    def from_string(cls, value: str) -> "TemplateCategory":
        """
        Convert string to TemplateCategory.

        Args:
            value: Category string value

        Returns:
            TemplateCategory enum value

        Raises:
            ValueError: If value is not a valid category
        """
        try:
            return cls(value.lower())
        except ValueError:
            logger.warning(
                f"Unknown template category '{value}', defaulting to GENERAL"
            )
            return cls.GENERAL


class TemplateParameterType(Enum):
    """Types of template parameters."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    FILE_PATH = "file_path"
    DIRECTORY_PATH = "directory_path"
    URL = "url"
    EMAIL = "email"
    SELECTOR = "selector"
    CREDENTIAL = "credential"
    CHOICE = "choice"
    LIST = "list"
    JSON = "json"

    def validate_value(
        self, value: Any, constraints: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this parameter type.

        Args:
            value: Value to validate
            constraints: Optional validation constraints (min, max, choices, pattern, etc.)

        Returns:
            Tuple of (is_valid, error_message)
        """
        constraints = constraints or {}

        if self == TemplateParameterType.STRING:
            if not isinstance(value, str):
                return False, f"Expected string, got {type(value).__name__}"
            if "min_length" in constraints and len(value) < constraints["min_length"]:
                return False, f"String too short (min: {constraints['min_length']})"
            if "max_length" in constraints and len(value) > constraints["max_length"]:
                return False, f"String too long (max: {constraints['max_length']})"
            if "pattern" in constraints:
                if not re.match(constraints["pattern"], value):
                    return (
                        False,
                        f"Value does not match pattern: {constraints['pattern']}",
                    )
            return True, None

        elif self == TemplateParameterType.INTEGER:
            if not isinstance(value, int) or isinstance(value, bool):
                return False, f"Expected integer, got {type(value).__name__}"
            if "min" in constraints and value < constraints["min"]:
                return False, f"Value too small (min: {constraints['min']})"
            if "max" in constraints and value > constraints["max"]:
                return False, f"Value too large (max: {constraints['max']})"
            return True, None

        elif self == TemplateParameterType.FLOAT:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                return False, f"Expected number, got {type(value).__name__}"
            if "min" in constraints and value < constraints["min"]:
                return False, f"Value too small (min: {constraints['min']})"
            if "max" in constraints and value > constraints["max"]:
                return False, f"Value too large (max: {constraints['max']})"
            return True, None

        elif self == TemplateParameterType.BOOLEAN:
            if not isinstance(value, bool):
                return False, f"Expected boolean, got {type(value).__name__}"
            return True, None

        elif self == TemplateParameterType.URL:
            if not isinstance(value, str):
                return False, f"Expected string URL, got {type(value).__name__}"
            url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
            if not re.match(url_pattern, value, re.IGNORECASE):
                return False, "Invalid URL format"
            return True, None

        elif self == TemplateParameterType.EMAIL:
            if not isinstance(value, str):
                return False, f"Expected string email, got {type(value).__name__}"
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, value):
                return False, "Invalid email format"
            return True, None

        elif self in (
            TemplateParameterType.FILE_PATH,
            TemplateParameterType.DIRECTORY_PATH,
        ):
            if not isinstance(value, str):
                return False, f"Expected string path, got {type(value).__name__}"
            return True, None

        elif self == TemplateParameterType.SELECTOR:
            if not isinstance(value, str):
                return False, f"Expected string selector, got {type(value).__name__}"
            if not value.strip():
                return False, "Selector cannot be empty"
            return True, None

        elif self == TemplateParameterType.CREDENTIAL:
            if not isinstance(value, str):
                return (
                    False,
                    f"Expected credential reference, got {type(value).__name__}",
                )
            return True, None

        elif self == TemplateParameterType.CHOICE:
            if "choices" not in constraints:
                return False, "CHOICE type requires 'choices' constraint"
            if value not in constraints["choices"]:
                return False, f"Value must be one of: {constraints['choices']}"
            return True, None

        elif self == TemplateParameterType.LIST:
            if not isinstance(value, list):
                return False, f"Expected list, got {type(value).__name__}"
            if "min_items" in constraints and len(value) < constraints["min_items"]:
                return False, f"List too short (min: {constraints['min_items']} items)"
            if "max_items" in constraints and len(value) > constraints["max_items"]:
                return False, f"List too long (max: {constraints['max_items']} items)"
            return True, None

        elif self == TemplateParameterType.JSON:
            if not isinstance(value, (dict, list)):
                return False, f"Expected JSON object/array, got {type(value).__name__}"
            return True, None

        return True, None


@dataclass
class TemplateParameter:
    """
    A configurable parameter within a workflow template.

    Parameters define variable parts of a template that users must provide
    values for when instantiating the template into a workflow.

    Attributes:
        name: Parameter identifier (used in placeholder: {{param_name}})
        display_name: Human-readable name for UI
        description: Explanation of what this parameter controls
        param_type: Type of the parameter value
        default_value: Optional default value
        required: Whether the parameter must be provided
        constraints: Type-specific validation constraints
        group: Optional grouping for UI organization
        order: Display order within group
    """

    name: str
    display_name: str
    description: str
    param_type: TemplateParameterType
    default_value: Optional[Any] = None
    required: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)
    group: str = "General"
    order: int = 0

    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """
        Validate a value against this parameter's type and constraints.

        Args:
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            if self.required and self.default_value is None:
                return False, f"Required parameter '{self.display_name}' is missing"
            return True, None

        return self.param_type.validate_value(value, self.constraints)

    def get_effective_value(self, provided_value: Optional[Any]) -> Any:
        """
        Get the effective value considering defaults.

        Args:
            provided_value: User-provided value or None

        Returns:
            Effective value (provided or default)
        """
        if provided_value is not None:
            return provided_value
        return self.default_value

    def to_dict(self) -> Dict[str, Any]:
        """Serialize parameter to dictionary."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "param_type": self.param_type.value,
            "default_value": self.default_value,
            "required": self.required,
            "constraints": self.constraints,
            "group": self.group,
            "order": self.order,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateParameter":
        """Create parameter from dictionary."""
        return cls(
            name=data["name"],
            display_name=data.get("display_name", data["name"]),
            description=data.get("description", ""),
            param_type=TemplateParameterType(data.get("param_type", "string")),
            default_value=data.get("default_value"),
            required=data.get("required", True),
            constraints=data.get("constraints", {}),
            group=data.get("group", "General"),
            order=data.get("order", 0),
        )


@dataclass
class TemplateUsageStats:
    """
    Usage statistics for a workflow template.

    Tracks how templates are used for analytics and optimization.
    """

    total_uses: int = 0
    last_used: Optional[datetime] = None
    successful_instantiations: int = 0
    failed_instantiations: int = 0
    average_rating: Optional[float] = None
    rating_count: int = 0

    def record_use(self, success: bool) -> None:
        """
        Record a template usage.

        Args:
            success: Whether instantiation was successful
        """
        self.total_uses += 1
        self.last_used = datetime.now()
        if success:
            self.successful_instantiations += 1
        else:
            self.failed_instantiations += 1

    def add_rating(self, rating: float) -> None:
        """
        Add a user rating (1-5 scale).

        Args:
            rating: Rating value between 1 and 5

        Raises:
            ValueError: If rating is out of range
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        if self.average_rating is None:
            self.average_rating = rating
            self.rating_count = 1
        else:
            total = self.average_rating * self.rating_count
            self.rating_count += 1
            self.average_rating = (total + rating) / self.rating_count

    @property
    def success_rate(self) -> Optional[float]:
        """Calculate success rate as percentage."""
        if self.total_uses == 0:
            return None
        return (self.successful_instantiations / self.total_uses) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Serialize stats to dictionary."""
        return {
            "total_uses": self.total_uses,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "successful_instantiations": self.successful_instantiations,
            "failed_instantiations": self.failed_instantiations,
            "average_rating": self.average_rating,
            "rating_count": self.rating_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateUsageStats":
        """Create stats from dictionary."""
        last_used = None
        if data.get("last_used"):
            last_used = datetime.fromisoformat(data["last_used"])

        return cls(
            total_uses=data.get("total_uses", 0),
            last_used=last_used,
            successful_instantiations=data.get("successful_instantiations", 0),
            failed_instantiations=data.get("failed_instantiations", 0),
            average_rating=data.get("average_rating"),
            rating_count=data.get("rating_count", 0),
        )


@dataclass
class TemplateMetadata:
    """
    Metadata for a workflow template.

    Contains descriptive and organizational information.
    """

    name: str
    description: str
    category: TemplateCategory
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    icon: str = ""
    preview_image: str = ""
    difficulty: str = "intermediate"
    estimated_duration: Optional[str] = None
    requirements: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.modified_at is None:
            self.modified_at = datetime.now()

    def touch_modified(self) -> None:
        """Update modified timestamp."""
        self.modified_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "icon": self.icon,
            "preview_image": self.preview_image,
            "difficulty": self.difficulty,
            "estimated_duration": self.estimated_duration,
            "requirements": self.requirements,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateMetadata":
        """Create metadata from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        modified_at = None
        if data.get("modified_at"):
            modified_at = datetime.fromisoformat(data["modified_at"])

        return cls(
            name=data.get("name", "Untitled Template"),
            description=data.get("description", ""),
            category=TemplateCategory.from_string(data.get("category", "general")),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            tags=data.get("tags", []),
            created_at=created_at,
            modified_at=modified_at,
            icon=data.get("icon", ""),
            preview_image=data.get("preview_image", ""),
            difficulty=data.get("difficulty", "intermediate"),
            estimated_duration=data.get("estimated_duration"),
            requirements=data.get("requirements", []),
        )


@dataclass
class TemplateReview:
    """
    A user review and rating for a workflow template.

    Reviews help users evaluate templates before using them and provide
    feedback to template authors.

    Attributes:
        id: Unique review identifier
        template_id: ID of the reviewed template
        rating: Rating from 1-5
        title: Short review title
        review_text: Detailed review content
        reviewer_id: ID of the reviewer (if authenticated)
        reviewer_name: Display name of the reviewer
        verified_use: Whether the reviewer actually used the template
        template_version: Version of template when reviewed
        helpful_count: Number of users who found this helpful
        not_helpful_count: Number of users who found this not helpful
        status: Review moderation status
        created_at: When the review was created
        updated_at: When the review was last updated
    """

    id: str
    template_id: str
    rating: int
    title: str = ""
    review_text: str = ""
    reviewer_id: Optional[str] = None
    reviewer_name: str = "Anonymous"
    verified_use: bool = False
    template_version: Optional[str] = None
    helpful_count: int = 0
    not_helpful_count: int = 0
    status: ReviewStatus = ReviewStatus.PUBLISHED
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamps and validate rating."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

        # Validate rating
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

    @classmethod
    def create_new(
        cls,
        template_id: str,
        rating: int,
        reviewer_name: str = "Anonymous",
        reviewer_id: Optional[str] = None,
        title: str = "",
        review_text: str = "",
        template_version: Optional[str] = None,
    ) -> "TemplateReview":
        """
        Factory method to create a new review.

        Args:
            template_id: ID of the template being reviewed
            rating: Rating from 1-5
            reviewer_name: Display name of the reviewer
            reviewer_id: Optional ID of the reviewer
            title: Optional short title
            review_text: Optional detailed review
            template_version: Optional version being reviewed

        Returns:
            New TemplateReview instance

        Raises:
            ValueError: If rating is out of range
        """
        return cls(
            id=f"rev_{uuid.uuid4().hex[:12]}",
            template_id=template_id,
            rating=rating,
            title=title,
            review_text=review_text,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            template_version=template_version,
        )

    def mark_helpful(self, helpful: bool = True) -> None:
        """
        Mark this review as helpful or not helpful.

        Args:
            helpful: True if helpful, False if not helpful
        """
        if helpful:
            self.helpful_count += 1
        else:
            self.not_helpful_count += 1

    @property
    def helpfulness_score(self) -> float:
        """
        Calculate helpfulness score as percentage.

        Returns:
            Percentage of helpful votes, or 0 if no votes
        """
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0.0
        return (self.helpful_count / total) * 100

    def update(
        self,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        review_text: Optional[str] = None,
    ) -> None:
        """
        Update the review content.

        Args:
            rating: New rating (1-5)
            title: New title
            review_text: New review text

        Raises:
            ValueError: If rating is out of range
        """
        if rating is not None:
            if not 1 <= rating <= 5:
                raise ValueError("Rating must be between 1 and 5")
            self.rating = rating
        if title is not None:
            self.title = title
        if review_text is not None:
            self.review_text = review_text
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize review to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "rating": self.rating,
            "title": self.title,
            "review_text": self.review_text,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer_name,
            "verified_use": self.verified_use,
            "template_version": self.template_version,
            "helpful_count": self.helpful_count,
            "not_helpful_count": self.not_helpful_count,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateReview":
        """Create review from dictionary."""
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"])

        status = ReviewStatus.PUBLISHED
        if data.get("status"):
            try:
                status = ReviewStatus(data["status"])
            except ValueError:
                pass

        return cls(
            id=data.get("id", f"rev_{uuid.uuid4().hex[:12]}"),
            template_id=data["template_id"],
            rating=data["rating"],
            title=data.get("title", ""),
            review_text=data.get("review_text", ""),
            reviewer_id=data.get("reviewer_id"),
            reviewer_name=data.get("reviewer_name", "Anonymous"),
            verified_use=data.get("verified_use", False),
            template_version=data.get("template_version"),
            helpful_count=data.get("helpful_count", 0),
            not_helpful_count=data.get("not_helpful_count", 0),
            status=status,
            created_at=created_at,
            updated_at=updated_at,
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TemplateReview(id='{self.id}', "
            f"template_id='{self.template_id}', "
            f"rating={self.rating}, "
            f"reviewer='{self.reviewer_name}')"
        )


@dataclass
class TemplateVersion:
    """
    A specific version of a workflow template.

    Tracks template changes over time for version history and rollback.

    Attributes:
        id: Unique version identifier
        template_id: ID of the parent template
        version: Semantic version string
        version_number: Sequential version number
        change_summary: Description of changes
        breaking_changes: Whether this version has breaking changes
        workflow_definition: Full template snapshot
        parameters: Parameter definitions snapshot
        status: Version status
        published_at: When this version was published
        published_by: Who published this version
        created_at: When this version was created
    """

    id: str
    template_id: str
    version: str
    version_number: int = 1
    change_summary: str = ""
    breaking_changes: bool = False
    workflow_definition: Dict[str, Any] = field(default_factory=dict)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    published_at: Optional[datetime] = None
    published_by: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Initialize timestamps."""
        if self.created_at is None:
            self.created_at = datetime.now()

    @classmethod
    def create_from_template(
        cls,
        template: "WorkflowTemplate",
        version: str,
        change_summary: str,
        breaking_changes: bool = False,
    ) -> "TemplateVersion":
        """
        Create a version snapshot from a template.

        Args:
            template: Template to snapshot
            version: Version string
            change_summary: Description of changes
            breaking_changes: Whether this is a breaking change

        Returns:
            New TemplateVersion instance
        """
        return cls(
            id=f"ver_{uuid.uuid4().hex[:12]}",
            template_id=template.id,
            version=version,
            change_summary=change_summary,
            breaking_changes=breaking_changes,
            workflow_definition=template.workflow_definition.copy(),
            parameters=[p.to_dict() for p in template.parameters],
        )

    def publish(self, published_by: Optional[str] = None) -> None:
        """
        Publish this version.

        Args:
            published_by: ID of the publisher
        """
        self.status = "published"
        self.published_at = datetime.now()
        self.published_by = published_by

    def to_dict(self) -> Dict[str, Any]:
        """Serialize version to dictionary."""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "version": self.version,
            "version_number": self.version_number,
            "change_summary": self.change_summary,
            "breaking_changes": self.breaking_changes,
            "workflow_definition": self.workflow_definition,
            "parameters": self.parameters,
            "status": self.status,
            "published_at": self.published_at.isoformat()
            if self.published_at
            else None,
            "published_by": self.published_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TemplateVersion":
        """Create version from dictionary."""
        published_at = None
        if data.get("published_at"):
            published_at = datetime.fromisoformat(data["published_at"])

        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])

        return cls(
            id=data.get("id", f"ver_{uuid.uuid4().hex[:12]}"),
            template_id=data["template_id"],
            version=data["version"],
            version_number=data.get("version_number", 1),
            change_summary=data.get("change_summary", ""),
            breaking_changes=data.get("breaking_changes", False),
            workflow_definition=data.get("workflow_definition", {}),
            parameters=data.get("parameters", []),
            status=data.get("status", "draft"),
            published_at=published_at,
            published_by=data.get("published_by"),
            created_at=created_at,
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"TemplateVersion(template_id='{self.template_id}', "
            f"version='{self.version}', "
            f"status='{self.status}')"
        )


@dataclass
class WorkflowTemplate:
    """
    A reusable workflow template with parameterized configuration.

    Templates contain a workflow definition with placeholder values that
    can be replaced with actual values when instantiating the template.

    Placeholder syntax: {{parameter_name}}

    Attributes:
        id: Unique template identifier
        metadata: Template descriptive metadata
        parameters: List of configurable parameters
        workflow_definition: The workflow JSON with placeholders
        usage_stats: Usage statistics
        is_builtin: Whether this is a built-in system template
        source: Template source (builtin, user, marketplace)
        marketplace_id: Optional marketplace identifier
    """

    id: str
    metadata: TemplateMetadata
    parameters: List[TemplateParameter] = field(default_factory=list)
    workflow_definition: Dict[str, Any] = field(default_factory=dict)
    usage_stats: TemplateUsageStats = field(default_factory=TemplateUsageStats)
    is_builtin: bool = False
    source: str = "user"
    marketplace_id: Optional[str] = None
    _file_path: Optional[Path] = field(default=None, repr=False)

    @classmethod
    def create_new(
        cls,
        name: str,
        description: str,
        category: TemplateCategory,
        workflow_definition: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> "WorkflowTemplate":
        """
        Factory method to create a new template.

        Args:
            name: Template name
            description: Template description
            category: Template category
            workflow_definition: Optional workflow JSON
            **kwargs: Additional template attributes

        Returns:
            New WorkflowTemplate instance
        """
        template_id = f"tmpl_{uuid.uuid4().hex[:12]}"
        metadata = TemplateMetadata(
            name=name,
            description=description,
            category=category,
            **{k: v for k, v in kwargs.items() if hasattr(TemplateMetadata, k)},
        )

        return cls(
            id=template_id,
            metadata=metadata,
            workflow_definition=workflow_definition or {},
            **{k: v for k, v in kwargs.items() if hasattr(cls, k) and k != "metadata"},
        )

    @property
    def file_path(self) -> Optional[Path]:
        """Get template file path."""
        return self._file_path

    @file_path.setter
    def file_path(self, value: Path) -> None:
        """Set template file path."""
        self._file_path = value

    @property
    def name(self) -> str:
        """Get template name."""
        return self.metadata.name

    @property
    def category(self) -> TemplateCategory:
        """Get template category."""
        return self.metadata.category

    def add_parameter(self, parameter: TemplateParameter) -> None:
        """
        Add a parameter to the template.

        Args:
            parameter: Parameter to add

        Raises:
            ValueError: If parameter name already exists
        """
        if any(p.name == parameter.name for p in self.parameters):
            raise ValueError(f"Parameter '{parameter.name}' already exists")
        self.parameters.append(parameter)
        self.metadata.touch_modified()

    def remove_parameter(self, name: str) -> bool:
        """
        Remove a parameter by name.

        Args:
            name: Parameter name to remove

        Returns:
            True if parameter was removed, False if not found
        """
        original_count = len(self.parameters)
        self.parameters = [p for p in self.parameters if p.name != name]
        if len(self.parameters) < original_count:
            self.metadata.touch_modified()
            return True
        return False

    def get_parameter(self, name: str) -> Optional[TemplateParameter]:
        """
        Get a parameter by name.

        Args:
            name: Parameter name

        Returns:
            TemplateParameter or None if not found
        """
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def get_required_parameters(self) -> List[TemplateParameter]:
        """Get list of required parameters without defaults."""
        return [p for p in self.parameters if p.required and p.default_value is None]

    def get_parameters_by_group(self) -> Dict[str, List[TemplateParameter]]:
        """
        Group parameters by their group attribute.

        Returns:
            Dictionary mapping group names to parameter lists
        """
        groups: Dict[str, List[TemplateParameter]] = {}
        for param in sorted(self.parameters, key=lambda p: p.order):
            if param.group not in groups:
                groups[param.group] = []
            groups[param.group].append(param)
        return groups

    def find_placeholders(self) -> Set[str]:
        """
        Find all placeholders in the workflow definition.

        Returns:
            Set of placeholder names found in the template
        """
        placeholders: Set[str] = set()
        self._find_placeholders_recursive(self.workflow_definition, placeholders)
        return placeholders

    def _find_placeholders_recursive(
        self,
        obj: Any,
        placeholders: Set[str],
    ) -> None:
        """Recursively find placeholders in nested structure."""
        if isinstance(obj, str):
            matches = re.findall(r"\{\{(\w+)\}\}", obj)
            placeholders.update(matches)
        elif isinstance(obj, dict):
            for value in obj.values():
                self._find_placeholders_recursive(value, placeholders)
        elif isinstance(obj, list):
            for item in obj:
                self._find_placeholders_recursive(item, placeholders)

    def validate_parameters(
        self,
        values: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """
        Validate provided parameter values.

        Args:
            values: Dictionary of parameter values

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: List[str] = []

        for param in self.parameters:
            value = values.get(param.name)
            is_valid, error = param.validate_value(value)
            if not is_valid:
                errors.append(f"{param.display_name}: {error}")

        # Check for unknown parameters
        known_params = {p.name for p in self.parameters}
        unknown = set(values.keys()) - known_params
        if unknown:
            errors.append(f"Unknown parameters: {', '.join(unknown)}")

        return len(errors) == 0, errors

    def instantiate(
        self,
        values: Dict[str, Any],
        validate: bool = True,
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        Instantiate the template with provided parameter values.

        Creates a new workflow definition with placeholders replaced
        by actual values.

        Args:
            values: Dictionary of parameter values
            validate: Whether to validate parameters before instantiation

        Returns:
            Tuple of (workflow_definition, list of warnings)

        Raises:
            ValueError: If validation fails and validate=True
        """
        warnings: List[str] = []

        if validate:
            is_valid, errors = self.validate_parameters(values)
            if not is_valid:
                raise ValueError(f"Parameter validation failed: {'; '.join(errors)}")

        # Build effective values dict with defaults
        effective_values: Dict[str, Any] = {}
        for param in self.parameters:
            provided = values.get(param.name)
            effective = param.get_effective_value(provided)
            if effective is None and param.required:
                warnings.append(
                    f"Required parameter '{param.display_name}' has no value"
                )
            effective_values[param.name] = effective

        # Deep copy and substitute placeholders
        import copy

        workflow = copy.deepcopy(self.workflow_definition)
        self._substitute_placeholders(workflow, effective_values)

        # Record usage
        self.usage_stats.record_use(success=True)

        return workflow, warnings

    def _substitute_placeholders(
        self,
        obj: Any,
        values: Dict[str, Any],
    ) -> Any:
        """
        Recursively substitute placeholders with values.

        Args:
            obj: Object to process (modified in place for dicts/lists)
            values: Parameter values

        Returns:
            Processed object
        """
        if isinstance(obj, str):
            result = obj
            for name, value in values.items():
                placeholder = f"{{{{{name}}}}}"
                if placeholder in result:
                    if result == placeholder:
                        # Entire string is placeholder - return typed value
                        return value
                    else:
                        # Placeholder within string - convert value to string
                        result = result.replace(
                            placeholder, str(value) if value is not None else ""
                        )
            return result
        elif isinstance(obj, dict):
            for key in list(obj.keys()):
                obj[key] = self._substitute_placeholders(obj[key], values)
            return obj
        elif isinstance(obj, list):
            for i in range(len(obj)):
                obj[i] = self._substitute_placeholders(obj[i], values)
            return obj
        return obj

    def get_missing_parameters(self, values: Dict[str, Any]) -> List[str]:
        """
        Get list of required parameters not provided.

        Args:
            values: Provided parameter values

        Returns:
            List of missing parameter names
        """
        missing = []
        for param in self.parameters:
            if param.required and param.default_value is None:
                if param.name not in values or values[param.name] is None:
                    missing.append(param.name)
        return missing

    def to_dict(self) -> Dict[str, Any]:
        """Serialize template to dictionary."""
        return {
            "$schema": "casare_rpa/workflow_template/1.0",
            "id": self.id,
            "metadata": self.metadata.to_dict(),
            "parameters": [p.to_dict() for p in self.parameters],
            "workflow_definition": self.workflow_definition,
            "usage_stats": self.usage_stats.to_dict(),
            "is_builtin": self.is_builtin,
            "source": self.source,
            "marketplace_id": self.marketplace_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowTemplate":
        """Create template from dictionary."""
        parameters = [
            TemplateParameter.from_dict(p) for p in data.get("parameters", [])
        ]

        return cls(
            id=data.get("id", f"tmpl_{uuid.uuid4().hex[:12]}"),
            metadata=TemplateMetadata.from_dict(data.get("metadata", {})),
            parameters=parameters,
            workflow_definition=data.get("workflow_definition", {}),
            usage_stats=TemplateUsageStats.from_dict(data.get("usage_stats", {})),
            is_builtin=data.get("is_builtin", False),
            source=data.get("source", "user"),
            marketplace_id=data.get("marketplace_id"),
        )

    def export_json(self) -> bytes:
        """
        Export template as JSON bytes.

        Returns:
            JSON-encoded template data
        """
        import orjson

        return orjson.dumps(
            self.to_dict(),
            option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
        )

    @classmethod
    def import_json(cls, json_data: bytes) -> "WorkflowTemplate":
        """
        Import template from JSON bytes.

        Args:
            json_data: JSON-encoded template data

        Returns:
            WorkflowTemplate instance

        Raises:
            ValueError: If JSON is invalid
        """
        import orjson

        try:
            data = orjson.loads(json_data)
            return cls.from_dict(data)
        except orjson.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}") from e

    def clone(self, new_name: Optional[str] = None) -> "WorkflowTemplate":
        """
        Create a copy of this template.

        Args:
            new_name: Optional new name for the clone

        Returns:
            New WorkflowTemplate instance
        """
        import copy

        data = self.to_dict()
        data["id"] = f"tmpl_{uuid.uuid4().hex[:12]}"
        data["is_builtin"] = False
        data["source"] = "user"
        data["marketplace_id"] = None
        data["usage_stats"] = {}

        if new_name:
            data["metadata"]["name"] = new_name
        else:
            data["metadata"]["name"] = f"{self.metadata.name} (Copy)"

        data["metadata"]["created_at"] = datetime.now().isoformat()
        data["metadata"]["modified_at"] = datetime.now().isoformat()

        return cls.from_dict(data)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"WorkflowTemplate(id='{self.id}', "
            f"name='{self.metadata.name}', "
            f"category={self.metadata.category.value}, "
            f"params={len(self.parameters)})"
        )

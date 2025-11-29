"""
CasareRPA - Application Use Cases: Template Management

Use cases for managing workflow templates including CRUD operations,
search, filtering, instantiation, and import/export functionality.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol
import uuid

from loguru import logger
import orjson

from casare_rpa.domain.workflow.templates import (
    TemplateCategory,
    TemplateParameter,
    WorkflowTemplate,
    TemplateMetadata,
)


class TemplateRepository(Protocol):
    """
    Repository interface for template persistence.

    Implementations must provide all methods for template storage/retrieval.
    """

    async def get_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Get template by ID."""
        ...

    async def get_all(self) -> List[WorkflowTemplate]:
        """Get all templates."""
        ...

    async def get_by_category(
        self, category: TemplateCategory
    ) -> List[WorkflowTemplate]:
        """Get templates by category."""
        ...

    async def search(
        self,
        query: str,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[WorkflowTemplate]:
        """Search templates."""
        ...

    async def save(self, template: WorkflowTemplate) -> None:
        """Save or update template."""
        ...

    async def delete(self, template_id: str) -> bool:
        """Delete template by ID."""
        ...

    async def exists(self, template_id: str) -> bool:
        """Check if template exists."""
        ...


@dataclass
class TemplateSearchCriteria:
    """Criteria for searching templates."""

    query: str = ""
    category: Optional[TemplateCategory] = None
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    is_builtin: Optional[bool] = None
    difficulty: Optional[str] = None
    min_rating: Optional[float] = None
    sort_by: str = "name"
    sort_desc: bool = False
    limit: int = 50
    offset: int = 0


@dataclass
class TemplateSearchResult:
    """Result of template search."""

    templates: List[WorkflowTemplate]
    total_count: int
    has_more: bool


@dataclass
class TemplateInstantiationResult:
    """Result of template instantiation."""

    success: bool
    workflow: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class CreateTemplateUseCase:
    """
    Use case for creating a new workflow template.

    Creates templates from scratch or from existing workflows.
    """

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository for persistence
        """
        self.repository = repository

    async def execute(
        self,
        name: str,
        description: str,
        category: TemplateCategory,
        workflow_definition: Dict[str, Any],
        parameters: Optional[List[Dict[str, Any]]] = None,
        author: str = "",
        tags: Optional[List[str]] = None,
        difficulty: str = "intermediate",
        requirements: Optional[List[str]] = None,
    ) -> WorkflowTemplate:
        """
        Create a new workflow template.

        Args:
            name: Template name
            description: Template description
            category: Template category
            workflow_definition: The workflow JSON to use as template base
            parameters: List of parameter definitions
            author: Template author
            tags: Optional tags for categorization
            difficulty: Difficulty level (beginner, intermediate, advanced)
            requirements: List of requirements/dependencies

        Returns:
            Created WorkflowTemplate

        Raises:
            ValueError: If template creation fails validation
        """
        logger.info(f"Creating new template: {name}")

        # Create metadata
        metadata = TemplateMetadata(
            name=name,
            description=description,
            category=category,
            author=author,
            tags=tags or [],
            difficulty=difficulty,
            requirements=requirements or [],
        )

        # Create template
        template = WorkflowTemplate(
            id=f"tmpl_{uuid.uuid4().hex[:12]}",
            metadata=metadata,
            workflow_definition=workflow_definition,
            is_builtin=False,
            source="user",
        )

        # Add parameters if provided
        if parameters:
            for param_data in parameters:
                param = TemplateParameter.from_dict(param_data)
                template.add_parameter(param)

        # Validate placeholders match parameters
        placeholders = template.find_placeholders()
        param_names = {p.name for p in template.parameters}
        undefined_placeholders = placeholders - param_names

        if undefined_placeholders:
            logger.warning(
                f"Template has undefined placeholders: {undefined_placeholders}. "
                "Creating parameters with default settings."
            )
            for placeholder in undefined_placeholders:
                template.add_parameter(
                    TemplateParameter(
                        name=placeholder,
                        display_name=placeholder.replace("_", " ").title(),
                        description=f"Parameter: {placeholder}",
                        param_type=TemplateParameter.__dataclass_fields__[
                            "param_type"
                        ].default,
                    )
                )

        # Save template
        await self.repository.save(template)

        logger.info(f"Template created successfully: {template.id}")
        return template

    async def from_workflow(
        self,
        workflow_data: Dict[str, Any],
        name: str,
        description: str,
        category: TemplateCategory,
        extract_variables: bool = True,
    ) -> WorkflowTemplate:
        """
        Create a template from an existing workflow.

        Args:
            workflow_data: Existing workflow JSON
            name: Template name
            description: Template description
            category: Template category
            extract_variables: Whether to extract workflow variables as parameters

        Returns:
            Created WorkflowTemplate
        """
        logger.info(f"Creating template from workflow: {name}")

        parameters: List[Dict[str, Any]] = []

        # Extract variables as parameters if requested
        if extract_variables:
            workflow_vars = workflow_data.get("variables", {})
            for var_name, var_def in workflow_vars.items():
                param_type = self._map_variable_type(var_def.get("type", "String"))
                parameters.append(
                    {
                        "name": var_name,
                        "display_name": var_name.replace("_", " ").title(),
                        "description": var_def.get("description", ""),
                        "param_type": param_type,
                        "default_value": var_def.get("default_value"),
                        "required": True,
                    }
                )

        return await self.execute(
            name=name,
            description=description,
            category=category,
            workflow_definition=workflow_data,
            parameters=parameters,
        )

    def _map_variable_type(self, var_type: str) -> str:
        """Map workflow variable type to parameter type."""
        mapping = {
            "String": "string",
            "Integer": "integer",
            "Float": "float",
            "Boolean": "boolean",
            "List": "list",
            "Dict": "json",
        }
        return mapping.get(var_type, "string")


class GetTemplateUseCase:
    """Use case for retrieving templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            WorkflowTemplate or None if not found
        """
        template = await self.repository.get_by_id(template_id)
        if template:
            logger.debug(f"Retrieved template: {template_id}")
        else:
            logger.debug(f"Template not found: {template_id}")
        return template

    async def all(self) -> List[WorkflowTemplate]:
        """
        Get all templates.

        Returns:
            List of all templates
        """
        templates = await self.repository.get_all()
        logger.debug(f"Retrieved {len(templates)} templates")
        return templates

    async def by_category(self, category: TemplateCategory) -> List[WorkflowTemplate]:
        """
        Get templates by category.

        Args:
            category: Template category

        Returns:
            List of templates in category
        """
        templates = await self.repository.get_by_category(category)
        logger.debug(
            f"Retrieved {len(templates)} templates for category {category.value}"
        )
        return templates

    async def builtin(self) -> List[WorkflowTemplate]:
        """
        Get all built-in templates.

        Returns:
            List of built-in templates
        """
        all_templates = await self.repository.get_all()
        builtin = [t for t in all_templates if t.is_builtin]
        logger.debug(f"Retrieved {len(builtin)} built-in templates")
        return builtin

    async def user_created(self) -> List[WorkflowTemplate]:
        """
        Get all user-created templates.

        Returns:
            List of user templates
        """
        all_templates = await self.repository.get_all()
        user_templates = [t for t in all_templates if not t.is_builtin]
        logger.debug(f"Retrieved {len(user_templates)} user templates")
        return user_templates


class SearchTemplatesUseCase:
    """Use case for searching and filtering templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(
        self,
        criteria: TemplateSearchCriteria,
    ) -> TemplateSearchResult:
        """
        Search templates with criteria.

        Args:
            criteria: Search criteria

        Returns:
            TemplateSearchResult with matching templates
        """
        logger.debug(f"Searching templates with query: '{criteria.query}'")

        # Get candidates from repository
        if criteria.category:
            templates = await self.repository.get_by_category(criteria.category)
        else:
            templates = await self.repository.get_all()

        # Apply filters
        filtered = self._apply_filters(templates, criteria)

        # Sort results
        sorted_templates = self._sort_templates(filtered, criteria)

        # Apply pagination
        total = len(sorted_templates)
        paginated = sorted_templates[criteria.offset : criteria.offset + criteria.limit]
        has_more = criteria.offset + len(paginated) < total

        return TemplateSearchResult(
            templates=paginated,
            total_count=total,
            has_more=has_more,
        )

    def _apply_filters(
        self,
        templates: List[WorkflowTemplate],
        criteria: TemplateSearchCriteria,
    ) -> List[WorkflowTemplate]:
        """Apply search criteria filters."""
        result = templates

        # Text query filter
        if criteria.query:
            query_lower = criteria.query.lower()
            result = [
                t
                for t in result
                if (
                    query_lower in t.metadata.name.lower()
                    or query_lower in t.metadata.description.lower()
                    or any(query_lower in tag.lower() for tag in t.metadata.tags)
                )
            ]

        # Tags filter
        if criteria.tags:
            criteria_tags = set(tag.lower() for tag in criteria.tags)
            result = [
                t
                for t in result
                if criteria_tags.intersection(tag.lower() for tag in t.metadata.tags)
            ]

        # Author filter
        if criteria.author:
            author_lower = criteria.author.lower()
            result = [t for t in result if author_lower in t.metadata.author.lower()]

        # Builtin filter
        if criteria.is_builtin is not None:
            result = [t for t in result if t.is_builtin == criteria.is_builtin]

        # Difficulty filter
        if criteria.difficulty:
            result = [t for t in result if t.metadata.difficulty == criteria.difficulty]

        # Rating filter
        if criteria.min_rating is not None:
            result = [
                t
                for t in result
                if (
                    t.usage_stats.average_rating is not None
                    and t.usage_stats.average_rating >= criteria.min_rating
                )
            ]

        return result

    def _sort_templates(
        self,
        templates: List[WorkflowTemplate],
        criteria: TemplateSearchCriteria,
    ) -> List[WorkflowTemplate]:
        """Sort templates by specified field."""
        sort_key_map = {
            "name": lambda t: t.metadata.name.lower(),
            "created": lambda t: t.metadata.created_at or datetime.min,
            "modified": lambda t: t.metadata.modified_at or datetime.min,
            "uses": lambda t: t.usage_stats.total_uses,
            "rating": lambda t: t.usage_stats.average_rating or 0,
            "category": lambda t: t.metadata.category.value,
        }

        sort_key = sort_key_map.get(criteria.sort_by, sort_key_map["name"])
        return sorted(templates, key=sort_key, reverse=criteria.sort_desc)


class UpdateTemplateUseCase:
    """Use case for updating existing templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(
        self,
        template_id: str,
        updates: Dict[str, Any],
    ) -> Optional[WorkflowTemplate]:
        """
        Update an existing template.

        Args:
            template_id: Template to update
            updates: Dictionary of fields to update

        Returns:
            Updated template or None if not found

        Raises:
            ValueError: If update contains invalid data
        """
        logger.info(f"Updating template: {template_id}")

        template = await self.repository.get_by_id(template_id)
        if not template:
            logger.warning(f"Template not found for update: {template_id}")
            return None

        if template.is_builtin:
            raise ValueError("Cannot modify built-in templates")

        # Update metadata fields
        if "name" in updates:
            template.metadata.name = updates["name"]
        if "description" in updates:
            template.metadata.description = updates["description"]
        if "category" in updates:
            template.metadata.category = TemplateCategory.from_string(
                updates["category"]
            )
        if "tags" in updates:
            template.metadata.tags = updates["tags"]
        if "author" in updates:
            template.metadata.author = updates["author"]
        if "difficulty" in updates:
            template.metadata.difficulty = updates["difficulty"]
        if "requirements" in updates:
            template.metadata.requirements = updates["requirements"]

        # Update workflow definition
        if "workflow_definition" in updates:
            template.workflow_definition = updates["workflow_definition"]

        # Update parameters
        if "parameters" in updates:
            template.parameters = [
                TemplateParameter.from_dict(p) for p in updates["parameters"]
            ]

        # Touch modified timestamp
        template.metadata.touch_modified()

        # Save changes
        await self.repository.save(template)

        logger.info(f"Template updated: {template_id}")
        return template


class DeleteTemplateUseCase:
    """Use case for deleting templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(self, template_id: str) -> bool:
        """
        Delete a template.

        Args:
            template_id: Template to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If attempting to delete built-in template
        """
        logger.info(f"Deleting template: {template_id}")

        template = await self.repository.get_by_id(template_id)
        if not template:
            logger.warning(f"Template not found for deletion: {template_id}")
            return False

        if template.is_builtin:
            raise ValueError("Cannot delete built-in templates")

        result = await self.repository.delete(template_id)
        if result:
            logger.info(f"Template deleted: {template_id}")
        return result


class InstantiateTemplateUseCase:
    """Use case for instantiating templates into workflows."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(
        self,
        template_id: str,
        parameter_values: Dict[str, Any],
        workflow_name: Optional[str] = None,
    ) -> TemplateInstantiationResult:
        """
        Instantiate a template with parameter values.

        Args:
            template_id: Template to instantiate
            parameter_values: Values for template parameters
            workflow_name: Optional name for the resulting workflow

        Returns:
            TemplateInstantiationResult with workflow and any warnings/errors
        """
        logger.info(f"Instantiating template: {template_id}")

        template = await self.repository.get_by_id(template_id)
        if not template:
            return TemplateInstantiationResult(
                success=False,
                errors=[f"Template not found: {template_id}"],
            )

        # Check for missing required parameters
        missing = template.get_missing_parameters(parameter_values)
        if missing:
            return TemplateInstantiationResult(
                success=False,
                errors=[f"Missing required parameters: {', '.join(missing)}"],
            )

        try:
            workflow, warnings = template.instantiate(parameter_values, validate=True)

            # Update workflow metadata if name provided
            if workflow_name:
                if "metadata" not in workflow:
                    workflow["metadata"] = {}
                workflow["metadata"]["name"] = workflow_name
                workflow["metadata"]["created_at"] = datetime.now().isoformat()
                workflow["metadata"]["modified_at"] = datetime.now().isoformat()
                workflow["metadata"]["template_id"] = template_id
                workflow["metadata"]["template_name"] = template.metadata.name

            # Save updated usage stats
            await self.repository.save(template)

            logger.info(f"Template instantiated successfully: {template_id}")
            return TemplateInstantiationResult(
                success=True,
                workflow=workflow,
                warnings=warnings,
            )

        except ValueError as e:
            logger.error(f"Template instantiation failed: {e}")
            template.usage_stats.record_use(success=False)
            await self.repository.save(template)

            return TemplateInstantiationResult(
                success=False,
                errors=[str(e)],
            )


class ExportTemplateUseCase:
    """Use case for exporting templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def to_json(self, template_id: str) -> Optional[bytes]:
        """
        Export template to JSON bytes.

        Args:
            template_id: Template to export

        Returns:
            JSON bytes or None if not found
        """
        template = await self.repository.get_by_id(template_id)
        if not template:
            logger.warning(f"Template not found for export: {template_id}")
            return None

        logger.info(f"Exporting template: {template_id}")
        return template.export_json()

    async def to_file(
        self,
        template_id: str,
        file_path: Path,
    ) -> bool:
        """
        Export template to file.

        Args:
            template_id: Template to export
            file_path: Destination file path

        Returns:
            True if exported successfully
        """
        json_data = await self.to_json(template_id)
        if not json_data:
            return False

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(json_data)
            logger.info(f"Template exported to: {file_path}")
            return True
        except OSError as e:
            logger.error(f"Failed to export template to {file_path}: {e}")
            return False


class ImportTemplateUseCase:
    """Use case for importing templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def from_json(
        self,
        json_data: bytes,
        overwrite: bool = False,
    ) -> WorkflowTemplate:
        """
        Import template from JSON bytes.

        Args:
            json_data: JSON template data
            overwrite: Whether to overwrite existing template with same ID

        Returns:
            Imported WorkflowTemplate

        Raises:
            ValueError: If import fails or template exists and overwrite=False
        """
        template = WorkflowTemplate.import_json(json_data)

        # Check for existing template
        existing = await self.repository.get_by_id(template.id)
        if existing and not overwrite:
            raise ValueError(
                f"Template with ID {template.id} already exists. "
                "Set overwrite=True to replace."
            )

        # Mark as user template (imported templates are not builtin)
        template.is_builtin = False
        template.source = "imported"

        # Reset usage stats for imported template
        template.usage_stats.total_uses = 0
        template.usage_stats.successful_instantiations = 0
        template.usage_stats.failed_instantiations = 0
        template.usage_stats.last_used = None

        await self.repository.save(template)

        logger.info(f"Template imported: {template.id}")
        return template

    async def from_file(
        self,
        file_path: Path,
        overwrite: bool = False,
    ) -> WorkflowTemplate:
        """
        Import template from file.

        Args:
            file_path: Path to template JSON file
            overwrite: Whether to overwrite existing template

        Returns:
            Imported WorkflowTemplate

        Raises:
            ValueError: If import fails
            FileNotFoundError: If file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Template file not found: {file_path}")

        try:
            json_data = file_path.read_bytes()
            template = await self.from_json(json_data, overwrite)
            template.file_path = file_path
            logger.info(f"Template imported from file: {file_path}")
            return template
        except OSError as e:
            raise ValueError(f"Failed to read template file: {e}") from e


class CloneTemplateUseCase:
    """Use case for cloning templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(
        self,
        template_id: str,
        new_name: Optional[str] = None,
    ) -> Optional[WorkflowTemplate]:
        """
        Clone an existing template.

        Args:
            template_id: Template to clone
            new_name: Optional name for the clone

        Returns:
            Cloned template or None if source not found
        """
        template = await self.repository.get_by_id(template_id)
        if not template:
            logger.warning(f"Template not found for cloning: {template_id}")
            return None

        cloned = template.clone(new_name)
        await self.repository.save(cloned)

        logger.info(f"Template cloned: {template_id} -> {cloned.id}")
        return cloned


class RateTemplateUseCase:
    """Use case for rating templates."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(
        self,
        template_id: str,
        rating: float,
    ) -> bool:
        """
        Rate a template.

        Args:
            template_id: Template to rate
            rating: Rating value (1-5)

        Returns:
            True if rating was recorded

        Raises:
            ValueError: If rating is out of range
        """
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        template = await self.repository.get_by_id(template_id)
        if not template:
            logger.warning(f"Template not found for rating: {template_id}")
            return False

        template.usage_stats.add_rating(rating)
        await self.repository.save(template)

        logger.info(f"Template {template_id} rated: {rating}")
        return True


class GetTemplateCategoriesUseCase:
    """Use case for retrieving template categories with counts."""

    def __init__(self, repository: TemplateRepository) -> None:
        """
        Initialize use case.

        Args:
            repository: Template repository
        """
        self.repository = repository

    async def execute(self) -> Dict[str, int]:
        """
        Get all categories with template counts.

        Returns:
            Dictionary mapping category names to template counts
        """
        all_templates = await self.repository.get_all()

        counts: Dict[str, int] = {cat.value: 0 for cat in TemplateCategory}

        for template in all_templates:
            counts[template.metadata.category.value] += 1

        # Filter out empty categories
        return {k: v for k, v in counts.items() if v > 0}

"""
CasareRPA - Infrastructure: Template Storage
File-based repository implementation for workflow templates.

Provides persistence for workflow templates using both:
- Built-in templates (shipped with the application)
- User templates (saved locally)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import orjson
from loguru import logger

from ...domain.workflow.templates import (
    TemplateCategory,
    WorkflowTemplate,
)


class TemplateStorage:
    """
    File-based storage adapter for workflow templates.

    Manages templates stored as JSON files in two locations:
    - Built-in templates: Application templates/ directory (read-only)
    - User templates: User config directory (read-write)

    Attributes:
        builtin_dir: Path to built-in templates directory
        user_dir: Path to user templates directory
    """

    def __init__(
        self,
        builtin_dir: Path,
        user_dir: Path,
    ) -> None:
        """
        Initialize template storage.

        Args:
            builtin_dir: Path to built-in templates directory
            user_dir: Path to user templates directory
        """
        self.builtin_dir = builtin_dir
        self.user_dir = user_dir
        self._ensure_directories()
        self._cache: Dict[str, WorkflowTemplate] = {}
        self._cache_valid = False

    def _ensure_directories(self) -> None:
        """Ensure storage directories exist."""
        try:
            self.user_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Template user directory: {self.user_dir}")
        except OSError as e:
            logger.error(f"Failed to create user templates directory: {e}")
            raise

    def _invalidate_cache(self) -> None:
        """Invalidate the template cache."""
        self._cache_valid = False
        self._cache.clear()

    def _load_template_file(self, file_path: Path) -> Optional[WorkflowTemplate]:
        """
        Load a template from a JSON file.

        Args:
            file_path: Path to template JSON file

        Returns:
            WorkflowTemplate or None if loading fails
        """
        try:
            json_data = file_path.read_bytes()
            data = orjson.loads(json_data)
            template = WorkflowTemplate.from_dict(data)
            template.file_path = file_path
            return template
        except orjson.JSONDecodeError as e:
            logger.error(f"Invalid JSON in template file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load template from {file_path}: {e}")
            return None

    def _scan_directory(
        self,
        directory: Path,
        is_builtin: bool = False,
    ) -> List[WorkflowTemplate]:
        """
        Scan a directory for template files.

        Args:
            directory: Directory to scan
            is_builtin: Whether these are built-in templates

        Returns:
            List of loaded templates
        """
        templates = []

        if not directory.exists():
            return templates

        try:
            for file_path in directory.glob("*.json"):
                template = self._load_template_file(file_path)
                if template:
                    template.is_builtin = is_builtin
                    if is_builtin:
                        template.source = "builtin"
                    templates.append(template)
        except OSError as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return templates

    def _load_all_templates(self) -> None:
        """Load all templates into cache."""
        if self._cache_valid:
            return

        self._cache.clear()

        # Load built-in templates first
        builtin_templates = self._scan_directory(self.builtin_dir, is_builtin=True)
        for template in builtin_templates:
            self._cache[template.id] = template
            logger.debug(f"Loaded built-in template: {template.name}")

        # Load user templates (can override built-in IDs)
        user_templates = self._scan_directory(self.user_dir, is_builtin=False)
        for template in user_templates:
            if template.id in self._cache and self._cache[template.id].is_builtin:
                logger.warning(f"User template {template.id} shadows built-in template")
            self._cache[template.id] = template
            logger.debug(f"Loaded user template: {template.name}")

        self._cache_valid = True
        logger.info(
            f"Loaded {len(self._cache)} templates "
            f"({len(builtin_templates)} built-in, {len(user_templates)} user)"
        )

    async def get_by_id(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            WorkflowTemplate or None if not found
        """
        self._load_all_templates()
        return self._cache.get(template_id)

    async def get_all(self) -> List[WorkflowTemplate]:
        """
        Get all templates.

        Returns:
            List of all templates (built-in and user)
        """
        self._load_all_templates()
        return list(self._cache.values())

    async def get_by_category(
        self,
        category: TemplateCategory,
    ) -> List[WorkflowTemplate]:
        """
        Get templates by category.

        Args:
            category: Template category to filter by

        Returns:
            List of templates in the category
        """
        self._load_all_templates()
        return [t for t in self._cache.values() if t.metadata.category == category]

    async def search(
        self,
        query: str,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[WorkflowTemplate]:
        """
        Search templates by query, category, and tags.

        Args:
            query: Search query string
            category: Optional category filter
            tags: Optional tags filter

        Returns:
            List of matching templates
        """
        self._load_all_templates()
        results = list(self._cache.values())

        # Filter by category
        if category:
            results = [t for t in results if t.metadata.category == category]

        # Filter by query (name, description)
        if query:
            query_lower = query.lower()
            results = [
                t
                for t in results
                if (
                    query_lower in t.metadata.name.lower()
                    or query_lower in t.metadata.description.lower()
                    or any(query_lower in tag.lower() for tag in t.metadata.tags)
                )
            ]

        # Filter by tags
        if tags:
            tag_set = set(tag.lower() for tag in tags)
            results = [
                t
                for t in results
                if tag_set.intersection(tag.lower() for tag in t.metadata.tags)
            ]

        return results

    async def save(self, template: WorkflowTemplate) -> None:
        """
        Save or update a template.

        Built-in templates cannot be modified directly; they must be cloned.

        Args:
            template: Template to save

        Raises:
            ValueError: If attempting to overwrite a built-in template
        """
        # Check if this would overwrite a built-in template
        existing = self._cache.get(template.id)
        if existing and existing.is_builtin and template.source != "builtin":
            raise ValueError(
                f"Cannot overwrite built-in template {template.id}. "
                "Clone the template first."
            )

        # Determine save path
        if template.is_builtin:
            # Built-in templates are read-only in normal operation
            # This code path is only for initial template creation
            save_dir = self.builtin_dir
        else:
            save_dir = self.user_dir

        # Generate filename from template ID
        filename = f"{template.id}.json"
        file_path = save_dir / filename

        try:
            json_data = orjson.dumps(
                template.to_dict(),
                option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS,
            )
            file_path.write_bytes(json_data)
            template.file_path = file_path

            # Update cache
            self._cache[template.id] = template
            logger.info(f"Saved template {template.id} to {file_path}")

        except OSError as e:
            logger.error(f"Failed to save template {template.id}: {e}")
            raise

    async def delete(self, template_id: str) -> bool:
        """
        Delete a template by ID.

        Built-in templates cannot be deleted.

        Args:
            template_id: Template to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If attempting to delete a built-in template
        """
        template = self._cache.get(template_id)
        if not template:
            return False

        if template.is_builtin:
            raise ValueError("Cannot delete built-in templates")

        # Delete file
        if template.file_path and template.file_path.exists():
            try:
                template.file_path.unlink()
                logger.info(f"Deleted template file: {template.file_path}")
            except OSError as e:
                logger.error(f"Failed to delete template file: {e}")
                raise

        # Remove from cache
        del self._cache[template_id]
        return True

    async def exists(self, template_id: str) -> bool:
        """
        Check if a template exists.

        Args:
            template_id: Template identifier

        Returns:
            True if template exists
        """
        self._load_all_templates()
        return template_id in self._cache

    def reload(self) -> None:
        """Force reload all templates from disk."""
        self._invalidate_cache()
        self._load_all_templates()

    async def get_builtin(self) -> List[WorkflowTemplate]:
        """
        Get all built-in templates.

        Returns:
            List of built-in templates
        """
        self._load_all_templates()
        return [t for t in self._cache.values() if t.is_builtin]

    async def get_user_templates(self) -> List[WorkflowTemplate]:
        """
        Get all user-created templates.

        Returns:
            List of user templates
        """
        self._load_all_templates()
        return [t for t in self._cache.values() if not t.is_builtin]

    async def get_category_counts(self) -> Dict[str, int]:
        """
        Get template counts by category.

        Returns:
            Dictionary mapping category names to counts
        """
        self._load_all_templates()
        counts: Dict[str, int] = {}

        for template in self._cache.values():
            cat = template.metadata.category.value
            counts[cat] = counts.get(cat, 0) + 1

        return counts

    async def import_template(
        self,
        json_data: bytes,
        overwrite: bool = False,
    ) -> WorkflowTemplate:
        """
        Import a template from JSON data.

        Args:
            json_data: JSON template data
            overwrite: Whether to overwrite existing template

        Returns:
            Imported template

        Raises:
            ValueError: If import fails or template exists without overwrite
        """
        try:
            data = orjson.loads(json_data)
            template = WorkflowTemplate.from_dict(data)
        except orjson.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON data: {e}") from e

        # Check for existing
        existing = await self.get_by_id(template.id)
        if existing:
            if existing.is_builtin:
                raise ValueError("Cannot overwrite built-in templates")
            if not overwrite:
                raise ValueError(
                    f"Template {template.id} already exists. "
                    "Use overwrite=True to replace."
                )

        # Mark as imported user template
        template.is_builtin = False
        template.source = "imported"

        # Save
        await self.save(template)
        return template

    async def export_template(self, template_id: str) -> Optional[bytes]:
        """
        Export a template to JSON bytes.

        Args:
            template_id: Template to export

        Returns:
            JSON bytes or None if not found
        """
        template = await self.get_by_id(template_id)
        if not template:
            return None

        return template.export_json()


class TemplateStorageFactory:
    """Factory for creating TemplateStorage instances."""

    @staticmethod
    def create_default() -> TemplateStorage:
        """
        Create TemplateStorage with default paths.

        Returns:
            Configured TemplateStorage instance
        """
        from ...utils.config import CONFIG_DIR

        # Built-in templates in application directory
        import casare_rpa

        app_dir = Path(casare_rpa.__file__).parent.parent.parent
        builtin_dir = app_dir / "templates"

        # User templates in config directory
        user_dir = CONFIG_DIR / "templates"

        return TemplateStorage(
            builtin_dir=builtin_dir,
            user_dir=user_dir,
        )

    @staticmethod
    def create_for_project(project_path: Path) -> TemplateStorage:
        """
        Create TemplateStorage for a specific project.

        Args:
            project_path: Path to project directory

        Returns:
            TemplateStorage with project-specific user templates
        """
        from ...utils.config import CONFIG_DIR

        import casare_rpa

        app_dir = Path(casare_rpa.__file__).parent.parent.parent
        builtin_dir = app_dir / "templates"

        # Project-local templates
        user_dir = project_path / "templates"

        return TemplateStorage(
            builtin_dir=builtin_dir,
            user_dir=user_dir,
        )

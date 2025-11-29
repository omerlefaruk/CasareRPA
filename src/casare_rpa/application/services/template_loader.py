"""
CasareRPA - Application Service: Template Loader
Service for loading and initializing workflow templates.

Handles loading built-in templates from the application directory
and provides access to the template library.
"""

from pathlib import Path
from typing import Dict, List, Optional
import orjson
from loguru import logger

from ...domain.workflow.templates import (
    TemplateCategory,
    WorkflowTemplate,
)


class TemplateLoader:
    """
    Service for loading and managing workflow templates.

    Provides a high-level interface for template operations including:
    - Loading built-in templates from disk
    - Filtering templates by category
    - Searching templates by name/tags
    - Getting template statistics

    Attributes:
        templates_dir: Path to templates directory
        templates: Dictionary of loaded templates by ID
    """

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        """
        Initialize template loader.

        Args:
            templates_dir: Path to templates directory. If None, uses default.
        """
        if templates_dir is None:
            templates_dir = self._get_default_templates_dir()

        self.templates_dir = templates_dir
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._loaded = False

    @staticmethod
    def _get_default_templates_dir() -> Path:
        """
        Get the default templates directory path.

        Returns:
            Path to templates directory
        """
        import casare_rpa

        app_dir = Path(casare_rpa.__file__).parent.parent.parent
        return app_dir / "templates"

    def load_templates(self, force_reload: bool = False) -> int:
        """
        Load all templates from disk.

        Args:
            force_reload: If True, reload even if already loaded

        Returns:
            Number of templates loaded
        """
        if self._loaded and not force_reload:
            return len(self.templates)

        self.templates.clear()

        if not self.templates_dir.exists():
            logger.warning(f"Templates directory not found: {self.templates_dir}")
            return 0

        loaded_count = 0
        error_count = 0

        for file_path in self.templates_dir.glob("*.json"):
            try:
                template = self._load_template_file(file_path)
                if template:
                    self.templates[template.id] = template
                    loaded_count += 1
                    logger.debug(f"Loaded template: {template.name} ({template.id})")
            except Exception as e:
                logger.error(f"Failed to load template from {file_path}: {e}")
                error_count += 1

        self._loaded = True
        logger.info(
            f"Loaded {loaded_count} templates from {self.templates_dir} "
            f"({error_count} errors)"
        )
        return loaded_count

    def _load_template_file(self, file_path: Path) -> Optional[WorkflowTemplate]:
        """
        Load a single template from a JSON file.

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
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return None
        except KeyError as e:
            logger.error(f"Missing required field in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get a template by ID.

        Args:
            template_id: Template identifier

        Returns:
            WorkflowTemplate or None if not found
        """
        if not self._loaded:
            self.load_templates()
        return self.templates.get(template_id)

    def get_all_templates(self) -> List[WorkflowTemplate]:
        """
        Get all loaded templates.

        Returns:
            List of all templates
        """
        if not self._loaded:
            self.load_templates()
        return list(self.templates.values())

    def get_templates_by_category(
        self,
        category: TemplateCategory,
    ) -> List[WorkflowTemplate]:
        """
        Get templates filtered by category.

        Args:
            category: Category to filter by

        Returns:
            List of templates in the category
        """
        if not self._loaded:
            self.load_templates()
        return [t for t in self.templates.values() if t.metadata.category == category]

    def search_templates(
        self,
        query: str,
        category: Optional[TemplateCategory] = None,
        tags: Optional[List[str]] = None,
    ) -> List[WorkflowTemplate]:
        """
        Search templates by query string.

        Searches template name, description, and tags.

        Args:
            query: Search query string
            category: Optional category filter
            tags: Optional tags filter

        Returns:
            List of matching templates
        """
        if not self._loaded:
            self.load_templates()

        results = list(self.templates.values())

        # Filter by category
        if category:
            results = [t for t in results if t.metadata.category == category]

        # Filter by query
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

    def get_categories_with_counts(self) -> Dict[str, int]:
        """
        Get all categories with template counts.

        Returns:
            Dictionary mapping category names to counts
        """
        if not self._loaded:
            self.load_templates()

        counts: Dict[str, int] = {}
        for template in self.templates.values():
            cat = template.metadata.category.value
            counts[cat] = counts.get(cat, 0) + 1

        return counts

    def get_popular_templates(self, limit: int = 10) -> List[WorkflowTemplate]:
        """
        Get most popular templates by usage.

        Args:
            limit: Maximum number of templates to return

        Returns:
            List of popular templates sorted by usage
        """
        if not self._loaded:
            self.load_templates()

        sorted_templates = sorted(
            self.templates.values(),
            key=lambda t: t.usage_stats.total_uses,
            reverse=True,
        )
        return sorted_templates[:limit]

    def get_top_rated_templates(
        self,
        limit: int = 10,
        min_ratings: int = 1,
    ) -> List[WorkflowTemplate]:
        """
        Get highest rated templates.

        Args:
            limit: Maximum number of templates to return
            min_ratings: Minimum number of ratings required

        Returns:
            List of top-rated templates
        """
        if not self._loaded:
            self.load_templates()

        rated_templates = [
            t
            for t in self.templates.values()
            if (
                t.usage_stats.average_rating is not None
                and t.usage_stats.rating_count >= min_ratings
            )
        ]

        sorted_templates = sorted(
            rated_templates,
            key=lambda t: t.usage_stats.average_rating or 0,
            reverse=True,
        )
        return sorted_templates[:limit]

    def get_templates_by_difficulty(
        self,
        difficulty: str,
    ) -> List[WorkflowTemplate]:
        """
        Get templates filtered by difficulty level.

        Args:
            difficulty: Difficulty level (beginner, intermediate, advanced)

        Returns:
            List of templates with the specified difficulty
        """
        if not self._loaded:
            self.load_templates()

        return [
            t for t in self.templates.values() if t.metadata.difficulty == difficulty
        ]

    def get_template_statistics(self) -> Dict[str, any]:
        """
        Get overall template library statistics.

        Returns:
            Dictionary with statistics
        """
        if not self._loaded:
            self.load_templates()

        templates = list(self.templates.values())
        total = len(templates)

        if total == 0:
            return {
                "total_templates": 0,
                "categories": {},
                "difficulties": {},
                "total_uses": 0,
                "average_rating": None,
            }

        # Calculate statistics
        categories = self.get_categories_with_counts()

        difficulties: Dict[str, int] = {}
        for t in templates:
            diff = t.metadata.difficulty
            difficulties[diff] = difficulties.get(diff, 0) + 1

        total_uses = sum(t.usage_stats.total_uses for t in templates)

        ratings = [
            t.usage_stats.average_rating
            for t in templates
            if t.usage_stats.average_rating is not None
        ]
        avg_rating = sum(ratings) / len(ratings) if ratings else None

        return {
            "total_templates": total,
            "categories": categories,
            "difficulties": difficulties,
            "total_uses": total_uses,
            "average_rating": avg_rating,
            "builtin_count": sum(1 for t in templates if t.is_builtin),
        }

    def reload(self) -> int:
        """
        Force reload all templates from disk.

        Returns:
            Number of templates loaded
        """
        return self.load_templates(force_reload=True)


class TemplateLibraryService:
    """
    High-level service for the template library.

    Combines template loading with repository operations for a complete
    template management solution.
    """

    def __init__(
        self,
        loader: Optional[TemplateLoader] = None,
    ) -> None:
        """
        Initialize template library service.

        Args:
            loader: Template loader (creates default if None)
        """
        self.loader = loader or TemplateLoader()

    def initialize(self) -> None:
        """Initialize the template library by loading all templates."""
        self.loader.load_templates()
        stats = self.loader.get_template_statistics()
        logger.info(
            f"Template library initialized: "
            f"{stats['total_templates']} templates in "
            f"{len(stats['categories'])} categories"
        )

    def get_template_for_instantiation(
        self,
        template_id: str,
    ) -> Optional[WorkflowTemplate]:
        """
        Get a template ready for instantiation.

        Args:
            template_id: Template identifier

        Returns:
            WorkflowTemplate or None if not found
        """
        return self.loader.get_template(template_id)

    def browse_templates(
        self,
        category: Optional[TemplateCategory] = None,
        difficulty: Optional[str] = None,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "name",
        limit: int = 50,
    ) -> List[WorkflowTemplate]:
        """
        Browse templates with various filters.

        Args:
            category: Optional category filter
            difficulty: Optional difficulty filter
            query: Optional search query
            tags: Optional tags filter
            sort_by: Sort field (name, rating, uses, date)
            limit: Maximum results

        Returns:
            List of matching templates
        """
        results = self.loader.get_all_templates()

        # Apply filters
        if category:
            results = [t for t in results if t.metadata.category == category]

        if difficulty:
            results = [t for t in results if t.metadata.difficulty == difficulty]

        if query:
            query_lower = query.lower()
            results = [
                t
                for t in results
                if (
                    query_lower in t.metadata.name.lower()
                    or query_lower in t.metadata.description.lower()
                )
            ]

        if tags:
            tag_set = set(tag.lower() for tag in tags)
            results = [
                t
                for t in results
                if tag_set.intersection(tag.lower() for tag in t.metadata.tags)
            ]

        # Sort results
        sort_keys = {
            "name": lambda t: t.metadata.name.lower(),
            "rating": lambda t: -(t.usage_stats.average_rating or 0),
            "uses": lambda t: -t.usage_stats.total_uses,
            "date": lambda t: t.metadata.created_at or "",
        }
        sort_key = sort_keys.get(sort_by, sort_keys["name"])
        results.sort(key=sort_key)

        return results[:limit]

    def get_featured_templates(self) -> List[WorkflowTemplate]:
        """
        Get featured/recommended templates.

        Returns templates that are popular, well-rated, or hand-picked.

        Returns:
            List of featured templates
        """
        # Combine popular and top-rated
        popular = self.loader.get_popular_templates(limit=5)
        top_rated = self.loader.get_top_rated_templates(limit=5)

        # Deduplicate while preserving order
        seen = set()
        featured = []
        for t in popular + top_rated:
            if t.id not in seen:
                seen.add(t.id)
                featured.append(t)

        return featured

    def get_templates_for_category_page(
        self,
        category: TemplateCategory,
    ) -> Dict[str, any]:
        """
        Get data for a category page.

        Args:
            category: Category to display

        Returns:
            Dictionary with templates and metadata
        """
        templates = self.loader.get_templates_by_category(category)

        # Group by difficulty
        by_difficulty: Dict[str, List[WorkflowTemplate]] = {
            "beginner": [],
            "intermediate": [],
            "advanced": [],
        }
        for t in templates:
            diff = t.metadata.difficulty
            if diff in by_difficulty:
                by_difficulty[diff].append(t)

        return {
            "category": category.value,
            "total": len(templates),
            "templates": templates,
            "by_difficulty": by_difficulty,
        }

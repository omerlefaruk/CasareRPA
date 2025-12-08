"""
CasareRPA - Template Storage

Infrastructure service for loading and managing project templates.
"""

import orjson
from loguru import logger
from pathlib import Path
from typing import Dict, List, Optional

from casare_rpa.domain.entities.project.template import (
    ProjectTemplate,
    TemplateCategory,
    TemplatesFile,
)
from casare_rpa.resources import TEMPLATES_DIR


class TemplateStorage:
    """
    Static adapter for template file operations.

    Loads built-in templates from resources and user templates from config.
    """

    @staticmethod
    def load_builtin_templates() -> List[ProjectTemplate]:
        """
        Load all built-in templates from resources/templates directory.

        Returns:
            List of ProjectTemplate instances
        """
        templates = []

        if not TEMPLATES_DIR.exists():
            return templates

        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                data = orjson.loads(template_file.read_bytes())
                template = ProjectTemplate.from_dict(data)
                template.is_builtin = True
                templates.append(template)
            except Exception as e:
                # Log error but continue loading other templates
                logger.warning(f"Error loading template {template_file}: {e}")

        return templates

    @staticmethod
    def load_template(template_id: str) -> Optional[ProjectTemplate]:
        """
        Load a specific template by ID.

        Args:
            template_id: Template identifier

        Returns:
            ProjectTemplate if found, None otherwise
        """
        # First check built-in templates
        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                data = orjson.loads(template_file.read_bytes())
                if data.get("id") == template_id:
                    template = ProjectTemplate.from_dict(data)
                    template.is_builtin = True
                    return template
            except Exception:
                continue

        return None

    @staticmethod
    def get_templates_by_category(category: TemplateCategory) -> List[ProjectTemplate]:
        """
        Get all templates in a specific category.

        Args:
            category: Template category to filter

        Returns:
            List of matching templates
        """
        all_templates = TemplateStorage.load_builtin_templates()
        return [t for t in all_templates if t.category == category]

    @staticmethod
    def save_user_template(template: ProjectTemplate, templates_dir: Path) -> None:
        """
        Save a user-created template.

        Args:
            template: Template to save
            templates_dir: Directory to save template in
        """
        templates_dir.mkdir(parents=True, exist_ok=True)

        template_file = templates_dir / f"{template.id}.json"
        template_data = template.to_dict()

        template_file.write_bytes(
            orjson.dumps(template_data, option=orjson.OPT_INDENT_2)
        )

    @staticmethod
    def load_user_templates(templates_dir: Path) -> List[ProjectTemplate]:
        """
        Load user-created templates from a directory.

        Args:
            templates_dir: Directory containing user templates

        Returns:
            List of user templates
        """
        templates = []

        if not templates_dir.exists():
            return templates

        for template_file in templates_dir.glob("*.json"):
            try:
                data = orjson.loads(template_file.read_bytes())
                template = ProjectTemplate.from_dict(data)
                template.is_builtin = False
                templates.append(template)
            except Exception as e:
                logger.warning(f"Error loading user template {template_file}: {e}")

        return templates

    @staticmethod
    def delete_user_template(template_id: str, templates_dir: Path) -> bool:
        """
        Delete a user-created template.

        Args:
            template_id: Template to delete
            templates_dir: Directory containing user templates

        Returns:
            True if deleted, False if not found
        """
        template_file = templates_dir / f"{template_id}.json"

        if template_file.exists():
            template_file.unlink()
            return True

        return False

    @staticmethod
    def get_all_templates(
        user_templates_dir: Optional[Path] = None,
    ) -> List[ProjectTemplate]:
        """
        Get all templates (built-in + user).

        Args:
            user_templates_dir: Optional directory for user templates

        Returns:
            Combined list of all templates
        """
        templates = TemplateStorage.load_builtin_templates()

        if user_templates_dir and user_templates_dir.exists():
            templates.extend(TemplateStorage.load_user_templates(user_templates_dir))

        return templates

    @staticmethod
    def save_templates_file(templates_file: TemplatesFile, file_path: Path) -> None:
        """
        Save a templates file (index of templates).

        Args:
            templates_file: Templates container
            file_path: Path to save
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(
            orjson.dumps(templates_file.to_dict(), option=orjson.OPT_INDENT_2)
        )

    @staticmethod
    def load_templates_file(file_path: Path) -> TemplatesFile:
        """
        Load a templates file.

        Args:
            file_path: Path to templates file

        Returns:
            TemplatesFile instance
        """
        if not file_path.exists():
            return TemplatesFile()

        data = orjson.loads(file_path.read_bytes())
        return TemplatesFile.from_dict(data)

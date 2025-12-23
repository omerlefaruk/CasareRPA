"""
CasareRPA - Template Storage

Infrastructure service for loading and managing project templates.

Result Pattern:
    This module uses Result[T, E] for explicit error handling instead of
    returning None or silently failing. Methods that can fail return:
    - Ok(value) on success
    - Err(FileSystemError) on failure

    Callers MUST check result.is_ok() before unwrapping:
        result = TemplateStorage.load_template_safe("my-template")
        if result.is_ok():
            template = result.unwrap()
        else:
            error = result.error  # FileSystemError with context
"""

from pathlib import Path
from typing import List, Optional

import orjson
from loguru import logger

from casare_rpa.domain.entities.project.template import (
    ProjectTemplate,
    TemplateCategory,
    TemplatesFile,
)
from casare_rpa.domain.errors import (
    Err,
    ErrorContext,
    FileSystemError,
    Ok,
    Result,
)
from casare_rpa.resources import TEMPLATES_DIR


class TemplateStorage:
    """
    Static adapter for template file operations.

    Loads built-in templates from resources and user templates from config.
    """

    @staticmethod
    def load_builtin_templates() -> list[ProjectTemplate]:
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
    def load_builtin_templates_safe() -> Result[list[ProjectTemplate], FileSystemError]:
        """
        Load all built-in templates with explicit error handling.

        Uses Result pattern - returns Ok(List[ProjectTemplate]) on success.
        Individual template load failures are logged but don't fail the entire operation.

        Returns:
            Ok(list of templates) - always succeeds, may be empty on errors
        """
        templates = []
        errors = []

        if not TEMPLATES_DIR.exists():
            return Ok(templates)

        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                data = orjson.loads(template_file.read_bytes())
                template = ProjectTemplate.from_dict(data)
                template.is_builtin = True
                templates.append(template)
            except Exception as e:
                errors.append(f"{template_file.name}: {e}")
                logger.warning(f"Error loading template {template_file}: {e}")

        if errors and not templates:
            # All templates failed - return error
            return Err(
                FileSystemError(
                    message=f"Failed to load any templates: {', '.join(errors)}",
                    path=str(TEMPLATES_DIR),
                    context=ErrorContext(
                        component="TemplateStorage",
                        operation="load_builtin_templates_safe",
                        details={"errors": errors},
                    ),
                )
            )

        return Ok(templates)

    @staticmethod
    def load_template(template_id: str) -> ProjectTemplate | None:
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
    def load_template_safe(
        template_id: str,
    ) -> Result[ProjectTemplate, FileSystemError]:
        """
        Load a specific template by ID with explicit error handling.

        Uses Result pattern - returns Ok(ProjectTemplate) on success,
        Err(FileSystemError) if not found or on I/O failure.

        Args:
            template_id: Template identifier

        Returns:
            Ok(ProjectTemplate) on success, Err(FileSystemError) on failure
        """
        if not TEMPLATES_DIR.exists():
            return Err(
                FileSystemError(
                    message="Templates directory not found",
                    path=str(TEMPLATES_DIR),
                    context=ErrorContext(
                        component="TemplateStorage",
                        operation="load_template_safe",
                        details={"template_id": template_id},
                    ),
                )
            )

        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                data = orjson.loads(template_file.read_bytes())
                if data.get("id") == template_id:
                    template = ProjectTemplate.from_dict(data)
                    template.is_builtin = True
                    return Ok(template)
            except orjson.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {template_file}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error loading template {template_file}: {e}")
                continue

        return Err(
            FileSystemError(
                message=f"Template not found: {template_id}",
                path=str(TEMPLATES_DIR),
                context=ErrorContext(
                    component="TemplateStorage",
                    operation="load_template_safe",
                    details={"template_id": template_id},
                ),
            )
        )

    @staticmethod
    def get_templates_by_category(category: TemplateCategory) -> list[ProjectTemplate]:
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

        template_file.write_bytes(orjson.dumps(template_data, option=orjson.OPT_INDENT_2))

    @staticmethod
    def save_user_template_safe(
        template: ProjectTemplate, templates_dir: Path
    ) -> Result[None, FileSystemError]:
        """
        Save a user-created template with explicit error handling.

        Uses Result pattern - returns Ok(None) on success, Err on failure.

        Args:
            template: Template to save
            templates_dir: Directory to save template in

        Returns:
            Ok(None) on success, Err(FileSystemError) on failure
        """
        try:
            templates_dir.mkdir(parents=True, exist_ok=True)
            template_file = templates_dir / f"{template.id}.json"
            template_data = template.to_dict()
            template_file.write_bytes(orjson.dumps(template_data, option=orjson.OPT_INDENT_2))
            return Ok(None)
        except Exception as e:
            logger.error(f"Failed to save user template {template.id}: {e}")
            return Err(
                FileSystemError(
                    message=f"Failed to save template '{template.id}': {e}",
                    path=str(templates_dir / f"{template.id}.json"),
                    context=ErrorContext(
                        component="TemplateStorage",
                        operation="save_user_template_safe",
                        details={
                            "template_id": template.id,
                            "template_name": template.name,
                        },
                    ),
                    original_error=e,
                )
            )

    @staticmethod
    def load_user_templates(templates_dir: Path) -> list[ProjectTemplate]:
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
    def load_user_templates_safe(
        templates_dir: Path,
    ) -> Result[list[ProjectTemplate], FileSystemError]:
        """
        Load user-created templates with explicit error handling.

        Uses Result pattern - returns Ok(List[ProjectTemplate]) on success.
        Individual template load failures are logged but don't fail the entire operation.

        Args:
            templates_dir: Directory containing user templates

        Returns:
            Ok(list of templates) on success, Err on critical failure
        """
        templates = []
        errors = []

        if not templates_dir.exists():
            return Ok(templates)

        for template_file in templates_dir.glob("*.json"):
            try:
                data = orjson.loads(template_file.read_bytes())
                template = ProjectTemplate.from_dict(data)
                template.is_builtin = False
                templates.append(template)
            except Exception as e:
                errors.append(f"{template_file.name}: {e}")
                logger.warning(f"Error loading user template {template_file}: {e}")

        if errors and not templates:
            # All templates failed - return error
            return Err(
                FileSystemError(
                    message=f"Failed to load any user templates: {', '.join(errors)}",
                    path=str(templates_dir),
                    context=ErrorContext(
                        component="TemplateStorage",
                        operation="load_user_templates_safe",
                        details={"errors": errors},
                    ),
                )
            )

        return Ok(templates)

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
    def delete_user_template_safe(
        template_id: str, templates_dir: Path
    ) -> Result[bool, FileSystemError]:
        """
        Delete a user-created template with explicit error handling.

        Uses Result pattern - returns Ok(True) if deleted, Ok(False) if not found,
        Err on I/O failure.

        Args:
            template_id: Template to delete
            templates_dir: Directory containing user templates

        Returns:
            Ok(True) if deleted, Ok(False) if not found, Err on failure
        """
        template_file = templates_dir / f"{template_id}.json"

        if not template_file.exists():
            return Ok(False)

        try:
            template_file.unlink()
            return Ok(True)
        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return Err(
                FileSystemError(
                    message=f"Failed to delete template '{template_id}': {e}",
                    path=str(template_file),
                    context=ErrorContext(
                        component="TemplateStorage",
                        operation="delete_user_template_safe",
                        details={"template_id": template_id},
                    ),
                    original_error=e,
                )
            )

    @staticmethod
    def get_all_templates(
        user_templates_dir: Path | None = None,
    ) -> list[ProjectTemplate]:
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
        file_path.write_bytes(orjson.dumps(templates_file.to_dict(), option=orjson.OPT_INDENT_2))

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

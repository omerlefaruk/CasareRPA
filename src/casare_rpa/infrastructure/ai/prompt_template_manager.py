"""
CasareRPA - Infrastructure: Prompt Template Manager

Manages prompt templates with file persistence and runtime rendering.
Bridges domain templates with infrastructure storage.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.ai.prompt_templates import (
    BUILTIN_TEMPLATES,
    FewShotExample,
    PromptTemplate,
    TemplateCategory,
    TemplateVariable,
)


class PromptTemplateManager:
    """
    Manages prompt templates with file system persistence.

    Features:
    - Built-in templates from domain layer
    - Custom template storage in user directory
    - Template rendering with variable substitution
    - Template validation and versioning
    - Export/import capabilities
    """

    TEMPLATES_DIR = "prompts"
    TEMPLATE_EXTENSION = ".json"

    def __init__(self, storage_path: str | None = None) -> None:
        """
        Initialize template manager.

        Args:
            storage_path: Base directory for template storage
        """
        if storage_path:
            self._storage_path = Path(storage_path)
        else:
            self._storage_path = Path.home() / ".casare_rpa" / self.TEMPLATES_DIR

        self._custom_templates: dict[str, PromptTemplate] = {}
        self._loaded = False

    def _ensure_storage_dir(self) -> Path:
        """Ensure storage directory exists."""
        self._storage_path.mkdir(parents=True, exist_ok=True)
        return self._storage_path

    def _template_to_dict(self, template: PromptTemplate) -> dict[str, Any]:
        """Convert template to serializable dictionary."""
        return {
            "id": template.id,
            "name": template.name,
            "category": template.category.value,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt_template": template.user_prompt_template,
            "output_format": template.output_format,
            "version": template.version,
            "tags": template.tags,
            "variables": [
                {
                    "name": v.name,
                    "description": v.description,
                    "data_type": v.data_type,
                    "required": v.required,
                    "default": v.default,
                    "examples": list(v.examples),
                }
                for v in template.variables
            ],
            "examples": [
                {
                    "input_text": e.input_text,
                    "expected_output": e.expected_output,
                    "explanation": e.explanation,
                }
                for e in template.examples
            ],
        }

    def _dict_to_template(self, data: dict[str, Any]) -> PromptTemplate:
        """Convert dictionary to PromptTemplate."""
        variables = [
            TemplateVariable(
                name=v["name"],
                description=v.get("description", ""),
                data_type=v.get("data_type", "string"),
                required=v.get("required", True),
                default=v.get("default"),
                examples=v.get("examples", []),
            )
            for v in data.get("variables", [])
        ]

        examples = [
            FewShotExample(
                input_text=e["input_text"],
                expected_output=e["expected_output"],
                explanation=e.get("explanation"),
            )
            for e in data.get("examples", [])
        ]

        return PromptTemplate(
            id=data["id"],
            name=data["name"],
            category=TemplateCategory(data.get("category", "generation")),
            description=data.get("description", ""),
            system_prompt=data["system_prompt"],
            user_prompt_template=data["user_prompt_template"],
            output_format=data.get("output_format"),
            version=data.get("version", "1.0"),
            tags=data.get("tags", []),
            variables=variables,
            examples=examples,
        )

    def _load_custom_templates(self) -> None:
        """Load custom templates from storage."""
        if self._loaded:
            return

        storage = self._ensure_storage_dir()

        for file_path in storage.glob(f"*{self.TEMPLATE_EXTENSION}"):
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)

                template = self._dict_to_template(data)
                self._custom_templates[template.id] = template
                logger.debug(f"Loaded custom template: {template.id}")

            except Exception as e:
                logger.warning(f"Failed to load template {file_path}: {e}")

        self._loaded = True
        logger.debug(f"Loaded {len(self._custom_templates)} custom templates")

    def get_template(self, template_id: str) -> PromptTemplate | None:
        """
        Get a template by ID.

        Checks custom templates first, then built-in.
        """
        self._load_custom_templates()

        # Check custom first (allows overriding built-in)
        if template_id in self._custom_templates:
            return self._custom_templates[template_id]

        # Check built-in
        return BUILTIN_TEMPLATES.get(template_id)

    def list_templates(
        self,
        category: TemplateCategory | None = None,
        include_builtin: bool = True,
    ) -> list[dict[str, Any]]:
        """
        List all available templates.

        Args:
            category: Filter by category
            include_builtin: Include built-in templates

        Returns:
            List of template metadata dictionaries
        """
        self._load_custom_templates()

        result = []

        # Add built-in templates
        if include_builtin:
            for template in BUILTIN_TEMPLATES.values():
                if category is None or template.category == category:
                    result.append(
                        {
                            "id": template.id,
                            "name": template.name,
                            "category": template.category.value,
                            "description": template.description,
                            "builtin": True,
                            "variables": [v.name for v in template.variables],
                            "tags": template.tags,
                        }
                    )

        # Add custom templates
        for template in self._custom_templates.values():
            if category is None or template.category == category:
                result.append(
                    {
                        "id": template.id,
                        "name": template.name,
                        "category": template.category.value,
                        "description": template.description,
                        "builtin": False,
                        "variables": [v.name for v in template.variables],
                        "tags": template.tags,
                    }
                )

        return result

    def save_template(self, template: PromptTemplate) -> bool:
        """
        Save a custom template to storage.

        Args:
            template: Template to save

        Returns:
            True if saved successfully
        """
        storage = self._ensure_storage_dir()
        file_path = storage / f"{template.id}{self.TEMPLATE_EXTENSION}"

        try:
            data = self._template_to_dict(template)
            data["saved_at"] = time.time()

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._custom_templates[template.id] = template
            logger.debug(f"Saved template: {template.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save template {template.id}: {e}")
            return False

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a custom template.

        Cannot delete built-in templates.
        """
        if template_id in BUILTIN_TEMPLATES:
            logger.warning(f"Cannot delete built-in template: {template_id}")
            return False

        storage = self._ensure_storage_dir()
        file_path = storage / f"{template_id}{self.TEMPLATE_EXTENSION}"

        try:
            if file_path.exists():
                file_path.unlink()

            if template_id in self._custom_templates:
                del self._custom_templates[template_id]

            logger.debug(f"Deleted template: {template_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete template {template_id}: {e}")
            return False

    def render_template(
        self,
        template_id: str,
        inputs: dict[str, Any],
    ) -> dict[str, str]:
        """
        Render a template with inputs.

        Args:
            template_id: Template ID
            inputs: Variable values

        Returns:
            Dict with 'system' and 'user' prompts

        Raises:
            ValueError: If template not found or validation fails
        """
        template = self.get_template(template_id)
        if template is None:
            raise ValueError(f"Template not found: {template_id}")

        return template.render_full_prompt(inputs)

    def validate_inputs(
        self,
        template_id: str,
        inputs: dict[str, Any],
    ) -> list[str]:
        """
        Validate inputs against template requirements.

        Returns list of validation errors.
        """
        template = self.get_template(template_id)
        if template is None:
            return [f"Template not found: {template_id}"]

        return template.validate_inputs(inputs)

    def create_template(
        self,
        template_id: str,
        name: str,
        category: str,
        system_prompt: str,
        user_prompt_template: str,
        variables: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> PromptTemplate:
        """
        Create a new template.

        Args:
            template_id: Unique template ID
            name: Display name
            category: Category string (extraction, generation, etc.)
            system_prompt: System prompt text
            user_prompt_template: User prompt with {placeholders}
            variables: Variable definitions
            **kwargs: Additional template fields

        Returns:
            Created PromptTemplate
        """
        vars_list = []
        if variables:
            for v in variables:
                vars_list.append(
                    TemplateVariable(
                        name=v["name"],
                        description=v.get("description", ""),
                        data_type=v.get("data_type", "string"),
                        required=v.get("required", True),
                        default=v.get("default"),
                        examples=v.get("examples", []),
                    )
                )

        template = PromptTemplate(
            id=template_id,
            name=name,
            category=TemplateCategory(category),
            system_prompt=system_prompt,
            user_prompt_template=user_prompt_template,
            variables=vars_list,
            description=kwargs.get("description", ""),
            output_format=kwargs.get("output_format"),
            version=kwargs.get("version", "1.0"),
            tags=kwargs.get("tags", []),
        )

        return template

    def export_template(self, template_id: str) -> str | None:
        """Export a template to JSON string."""
        template = self.get_template(template_id)
        if template is None:
            return None

        data = self._template_to_dict(template)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def import_template(self, json_str: str, overwrite: bool = False) -> bool:
        """
        Import a template from JSON string.

        Args:
            json_str: JSON template data
            overwrite: Allow overwriting existing templates

        Returns:
            True if imported successfully
        """
        try:
            data = json.loads(json_str)
            template = self._dict_to_template(data)

            # Check for existing
            existing = self.get_template(template.id)
            if existing and not overwrite:
                logger.warning(f"Template already exists: {template.id}")
                return False

            return self.save_template(template)

        except Exception as e:
            logger.error(f"Failed to import template: {e}")
            return False

    def get_template_variables(
        self,
        template_id: str,
    ) -> list[dict[str, Any]]:
        """Get variable definitions for a template."""
        template = self.get_template(template_id)
        if template is None:
            return []

        return [
            {
                "name": v.name,
                "description": v.description,
                "data_type": v.data_type,
                "required": v.required,
                "default": v.default,
                "examples": v.examples,
            }
            for v in template.variables
        ]

    def search_templates(
        self,
        query: str,
        include_builtin: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query
            include_builtin: Include built-in templates

        Returns:
            Matching template metadata
        """
        query_lower = query.lower()
        results = []

        for template_meta in self.list_templates(include_builtin=include_builtin):
            # Search in name, description, and tags
            searchable = (
                template_meta["name"].lower()
                + " "
                + template_meta.get("description", "").lower()
                + " "
                + " ".join(template_meta.get("tags", []))
            )

            if query_lower in searchable:
                results.append(template_meta)

        return results

    @property
    def storage_path(self) -> Path:
        """Get storage path."""
        return self._storage_path

    @property
    def custom_template_count(self) -> int:
        """Get number of custom templates."""
        self._load_custom_templates()
        return len(self._custom_templates)

    @property
    def total_template_count(self) -> int:
        """Get total number of templates."""
        self._load_custom_templates()
        return len(BUILTIN_TEMPLATES) + len(self._custom_templates)


# Module-level singleton
_default_manager: PromptTemplateManager | None = None


def get_prompt_template_manager() -> PromptTemplateManager:
    """Get or create the default template manager."""
    global _default_manager
    if _default_manager is None:
        _default_manager = PromptTemplateManager()
    return _default_manager


__all__ = [
    "PromptTemplateManager",
    "get_prompt_template_manager",
]

"""
CasareRPA - Prompt Template Node

Node for using reusable prompt templates with LLM operations.
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.llm.llm_base import LLMBaseNode


@properties(
    PropertyDef(
        "template_id",
        PropertyType.STRING,
        default="",
        label="Template ID",
        placeholder="my_template",
        tooltip="ID of the prompt template to use",
        essential=True,
    ),
    PropertyDef(
        "variables",
        PropertyType.JSON,
        default={},
        label="Variables",
        tooltip="Template variables as key-value pairs",
    ),
    PropertyDef(
        "execute",
        PropertyType.BOOLEAN,
        default=True,
        label="Execute with LLM",
        tooltip="Execute the rendered prompt with LLM (or just render)",
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o-mini",
        label="Model",
        tooltip="LLM model to use",
    ),
    PropertyDef(
        "temperature",
        PropertyType.FLOAT,
        default=0.7,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Creativity/randomness (0-2)",
    ),
    PropertyDef(
        "max_tokens",
        PropertyType.INTEGER,
        default=1000,
        min_value=1,
        label="Max Tokens",
        tooltip="Maximum response length",
    ),
)
@node(category="llm")
class PromptTemplateNode(LLMBaseNode):
    """
    Execute a prompt template with LLM.

    Selects a built-in or custom template, fills in variables,
    and optionally executes with an LLM.
    """

    NODE_NAME = "Prompt Template"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Use reusable prompt templates for AI tasks"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("template_id", DataType.STRING)
        self.add_input_port("variables", DataType.DICT)
        self.add_input_port("execute", DataType.BOOLEAN, required=False)
        self._define_common_input_ports()

        # Outputs
        self.add_output_port("rendered_prompt", DataType.STRING)
        self.add_output_port("system_prompt", DataType.STRING)
        self.add_output_port("response", DataType.STRING)
        self.add_output_port("parsed_response", DataType.DICT)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute prompt template."""
        from casare_rpa.infrastructure.ai.prompt_template_manager import (
            get_prompt_template_manager,
        )

        template_id = self.get_parameter("template_id")
        variables = self.get_parameter("variables") or {}
        should_execute = self.get_parameter("execute")

        if hasattr(context, "resolve_value"):
            template_id = context.resolve_value(template_id)

        if not template_id:
            self.set_output_value("success", False)
            self.set_output_value("error", "Template ID is required")
            return {"success": False, "error": "Template ID required", "next_nodes": []}

        # Parse variables if string
        if isinstance(variables, str):
            try:
                variables = json.loads(variables)
            except json.JSONDecodeError as e:
                self.set_output_value("success", False)
                self.set_output_value("error", f"Invalid variables JSON: {e}")
                return {"success": False, "error": str(e), "next_nodes": []}

        # Resolve variable values from context if needed
        if hasattr(context, "resolve_value"):
            resolved_vars = {}
            for key, value in variables.items():
                if isinstance(value, str):
                    resolved_vars[key] = context.resolve_value(value)
                else:
                    resolved_vars[key] = value
            variables = resolved_vars

        try:
            template_manager = get_prompt_template_manager()

            # Validate inputs
            errors = template_manager.validate_inputs(template_id, variables)
            if errors:
                error_msg = "; ".join(errors)
                self.set_output_value("success", False)
                self.set_output_value("error", error_msg)
                return {"success": False, "error": error_msg, "next_nodes": []}

            # Render template
            prompts = template_manager.render_template(template_id, variables)
            rendered_prompt = prompts["user"]
            system_prompt = prompts["system"]

            self.set_output_value("rendered_prompt", rendered_prompt)
            self.set_output_value("system_prompt", system_prompt)

            # Execute with LLM if requested
            if should_execute:
                model = self.get_parameter("model") or self.DEFAULT_MODEL
                temperature = self.get_parameter("temperature") or 0.7
                max_tokens = self.get_parameter("max_tokens") or 1000

                if hasattr(context, "resolve_value"):
                    model = context.resolve_value(model)

                llm_manager = await self._get_llm_manager(context)

                response = await llm_manager.completion(
                    prompt=rendered_prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=float(temperature),
                    max_tokens=int(max_tokens),
                )

                response_text = response.content

                # Try to parse JSON response
                parsed = {}
                try:
                    # Remove markdown code blocks if present
                    clean = response_text.strip()
                    if clean.startswith("```"):
                        lines = clean.split("\n")
                        clean = "\n".join(
                            lines[1:-1] if lines[-1] == "```" else lines[1:]
                        )
                    parsed = json.loads(clean)
                except (json.JSONDecodeError, ValueError):
                    pass

                self.set_output_value("response", response_text)
                self.set_output_value("parsed_response", parsed)
                self.set_output_value("tokens_used", response.total_tokens)
                self.set_output_value("success", True)
                self.set_output_value("error", "")

                logger.info(
                    f"Prompt template executed: {template_id}, "
                    f"tokens={response.total_tokens}"
                )

                return {
                    "success": True,
                    "data": {
                        "response": response_text,
                        "parsed": parsed,
                        "template": template_id,
                    },
                    "next_nodes": ["exec_out"],
                }

            else:
                # Just render, don't execute
                self.set_output_value("response", "")
                self.set_output_value("parsed_response", {})
                self.set_output_value("tokens_used", 0)
                self.set_output_value("success", True)
                self.set_output_value("error", "")

                logger.info(f"Prompt template rendered: {template_id}")

                return {
                    "success": True,
                    "data": {
                        "rendered_prompt": rendered_prompt,
                        "template": template_id,
                    },
                    "next_nodes": ["exec_out"],
                }

        except ValueError as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "category",
        PropertyType.STRING,
        default="",
        label="Category",
        placeholder="extraction, generation, analysis",
        tooltip="Filter by template category (optional)",
    ),
    PropertyDef(
        "search",
        PropertyType.STRING,
        default="",
        label="Search",
        placeholder="Search term...",
        tooltip="Search templates by name/description",
    ),
    PropertyDef(
        "include_builtin",
        PropertyType.BOOLEAN,
        default=True,
        label="Include Built-in",
        tooltip="Include built-in templates in results",
    ),
)
@node(category="llm")
class ListTemplatesNode(LLMBaseNode):
    """
    List available prompt templates.

    Returns metadata about built-in and custom templates.
    """

    NODE_NAME = "List Templates"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "List available prompt templates"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("category", DataType.STRING, required=False)
        self.add_input_port("search", DataType.STRING, required=False)
        self.add_input_port("include_builtin", DataType.BOOLEAN, required=False)

        # Outputs
        self.add_output_port("templates", DataType.LIST)
        self.add_output_port("count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute template listing."""
        from casare_rpa.domain.ai.prompt_templates import TemplateCategory
        from casare_rpa.infrastructure.ai.prompt_template_manager import (
            get_prompt_template_manager,
        )

        category = self.get_parameter("category")
        search = self.get_parameter("search")
        include_builtin = self.get_parameter("include_builtin")

        if include_builtin is None:
            include_builtin = True

        if hasattr(context, "resolve_value"):
            if category:
                category = context.resolve_value(category)
            if search:
                search = context.resolve_value(search)

        try:
            template_manager = get_prompt_template_manager()

            # Parse category
            cat_enum = None
            if category:
                try:
                    cat_enum = TemplateCategory(category.lower())
                except ValueError:
                    pass

            if search:
                templates = template_manager.search_templates(
                    search, include_builtin=include_builtin
                )
            else:
                templates = template_manager.list_templates(
                    category=cat_enum, include_builtin=include_builtin
                )

            self.set_output_value("templates", templates)
            self.set_output_value("count", len(templates))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug(f"Listed {len(templates)} templates")

            return {
                "success": True,
                "data": {"templates": templates, "count": len(templates)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("templates", [])
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "template_id",
        PropertyType.STRING,
        default="",
        label="Template ID",
        placeholder="my_template",
        tooltip="ID of the template to get info for",
        essential=True,
    ),
)
@node(category="llm")
class GetTemplateInfoNode(LLMBaseNode):
    """
    Get detailed information about a prompt template.

    Returns template metadata, variables, and examples.
    """

    NODE_NAME = "Get Template Info"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Get details about a prompt template"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("template_id", DataType.STRING)

        # Outputs
        self.add_output_port("template_info", DataType.DICT)
        self.add_output_port("variables", DataType.LIST)
        self.add_output_port("system_prompt", DataType.STRING)
        self.add_output_port("found", DataType.BOOLEAN)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute template info retrieval."""
        from casare_rpa.infrastructure.ai.prompt_template_manager import (
            get_prompt_template_manager,
        )

        template_id = self.get_parameter("template_id")
        if hasattr(context, "resolve_value"):
            template_id = context.resolve_value(template_id)

        if not template_id:
            self.set_output_value("success", False)
            self.set_output_value("error", "Template ID is required")
            self.set_output_value("found", False)
            return {"success": False, "error": "Template ID required", "next_nodes": []}

        try:
            template_manager = get_prompt_template_manager()
            template = template_manager.get_template(template_id)

            if template is None:
                self.set_output_value("found", False)
                self.set_output_value("template_info", {})
                self.set_output_value("variables", [])
                self.set_output_value("system_prompt", "")
                self.set_output_value("success", True)
                self.set_output_value("error", "")

                return {
                    "success": True,
                    "data": {"found": False},
                    "next_nodes": ["exec_out"],
                }

            # Build info dict
            template_info = {
                "id": template.id,
                "name": template.name,
                "category": template.category.value,
                "description": template.description,
                "version": template.version,
                "tags": template.tags,
                "output_format": template.output_format,
            }

            variables = template_manager.get_template_variables(template_id)

            self.set_output_value("template_info", template_info)
            self.set_output_value("variables", variables)
            self.set_output_value("system_prompt", template.system_prompt)
            self.set_output_value("found", True)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.debug(f"Retrieved template info: {template_id}")

            return {
                "success": True,
                "data": {"template_info": template_info, "found": True},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("found", False)
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "PromptTemplateNode",
    "ListTemplatesNode",
    "GetTemplateInfoNode",
]

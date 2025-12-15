"""
CasareRPA - LLM Nodes

Concrete LLM node implementations for various AI operations.
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
from casare_rpa.infrastructure.resources.llm_resource_manager import LLMResourceManager
from casare_rpa.nodes.llm.llm_base import LLMBaseNode
from casare_rpa.nodes.llm.property_constants import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_TEMPERATURE_LOW,
    LLM_TEMPERATURE_MEDIUM,
    LLM_TEMPERATURE_TRANSLATION,
    LLM_MAX_TOKENS,
    LLM_SYSTEM_PROMPT,
    LLM_PROMPT,
    LLM_MESSAGE,
    LLM_CONVERSATION_ID,
    LLM_SCHEMA,
    LLM_MAX_LENGTH,
    LLM_SUMMARY_STYLE,
    LLM_CATEGORIES,
    LLM_MULTI_LABEL,
    LLM_TARGET_LANGUAGE,
    LLM_SOURCE_LANGUAGE,
)


@properties(
    LLM_PROMPT,
    LLM_MODEL,
    LLM_SYSTEM_PROMPT,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)
@node(category="llm")
class LLMCompletionNode(LLMBaseNode):
    """
    Generate text completion from a prompt.

    Simple prompt-to-response node for single-turn interactions.
    """

    # @category: integration
    # @requires: none
    # @ports: prompt -> none

    NODE_NAME = "LLM Completion"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Generate text using an LLM from a prompt"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("prompt", DataType.STRING)
        self._define_common_input_ports()

        # Outputs
        self._define_common_output_ports()

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute completion request."""
        # Get parameters
        prompt = self.get_parameter("prompt")
        if hasattr(context, "resolve_value"):
            prompt = context.resolve_value(prompt)

        if not prompt:
            self._set_error_outputs("Prompt is required")
            return {"success": False, "error": "Prompt is required", "next_nodes": []}

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or self.DEFAULT_TEMPERATURE
        max_tokens = self.get_parameter("max_tokens") or self.DEFAULT_MAX_TOKENS
        system_prompt = self.get_parameter("system_prompt")

        if hasattr(context, "resolve_value"):
            model = context.resolve_value(model)
            system_prompt = (
                context.resolve_value(system_prompt) if system_prompt else None
            )

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt=system_prompt,
                temperature=float(temperature),
                max_tokens=int(max_tokens),
            )

            self._set_success_outputs(
                response=response.content,
                tokens_used=response.total_tokens,
                model_used=response.model,
            )

            logger.info(f"LLM completion: {response.total_tokens} tokens used")

            return {
                "success": True,
                "data": {
                    "response": response.content,
                    "tokens": response.total_tokens,
                    "model": response.model,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self._set_error_outputs(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "message",
        PropertyType.TEXT,
        default="",
        label="Message",
        placeholder="Enter your message...",
        tooltip="The message to send to the LLM",
        essential=True,
    ),
    PropertyDef(
        "conversation_id",
        PropertyType.STRING,
        default="",
        label="Conversation ID",
        tooltip="Optional ID to continue a conversation",
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o-mini",
        label="Model",
        tooltip="LLM model to use",
    ),
    PropertyDef(
        "system_prompt",
        PropertyType.TEXT,
        default="",
        label="System Prompt",
        tooltip="Optional system prompt for context",
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
class LLMChatNode(LLMBaseNode):
    """
    Multi-turn chat conversation with an LLM.

    Maintains conversation history across multiple messages.
    """

    NODE_NAME = "LLM Chat"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Chat with an LLM maintaining conversation history"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("message", DataType.STRING)
        self.add_input_port("conversation_id", DataType.STRING, required=False)
        self._define_common_input_ports()

        # Outputs
        self._define_common_output_ports()
        self.add_output_port("conversation_id", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute chat message."""
        # Get parameters
        message = self.get_parameter("message")
        if hasattr(context, "resolve_value"):
            message = context.resolve_value(message)

        if not message:
            self._set_error_outputs("Message is required")
            return {"success": False, "error": "Message is required", "next_nodes": []}

        conversation_id = self.get_parameter("conversation_id")
        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or self.DEFAULT_TEMPERATURE
        max_tokens = self.get_parameter("max_tokens") or self.DEFAULT_MAX_TOKENS
        system_prompt = self.get_parameter("system_prompt")

        if hasattr(context, "resolve_value"):
            conversation_id = (
                context.resolve_value(conversation_id) if conversation_id else None
            )
            model = context.resolve_value(model)
            system_prompt = (
                context.resolve_value(system_prompt) if system_prompt else None
            )

        try:
            response, conv_id = await manager.chat(
                message=message,
                conversation_id=conversation_id,
                model=model,
                system_prompt=system_prompt,
                temperature=float(temperature),
                max_tokens=int(max_tokens),
            )

            self._set_success_outputs(
                response=response.content,
                tokens_used=response.total_tokens,
                model_used=response.model,
            )
            self.set_output_value("conversation_id", conv_id)

            logger.info(f"LLM chat: conv={conv_id}, {response.total_tokens} tokens")

            return {
                "success": True,
                "data": {
                    "response": response.content,
                    "conversation_id": conv_id,
                    "tokens": response.total_tokens,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self._set_error_outputs(error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        label="Text",
        placeholder="Text to extract data from...",
        tooltip="The unstructured text to parse",
        essential=True,
    ),
    PropertyDef(
        "schema",
        PropertyType.TEXT,
        default="",
        label="JSON Schema",
        placeholder='{"name": "string", "age": "integer"}',
        tooltip="JSON schema defining the structure to extract",
        essential=True,
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
        default=0.0,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Low temperature recommended for extraction",
    ),
)
@node(category="llm")
class LLMExtractDataNode(LLMBaseNode):
    """
    Extract structured data from text using JSON schema.

    Uses LLM to parse unstructured text into structured JSON.
    """

    NODE_NAME = "LLM Extract Data"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Extract structured data from text using AI"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("schema", DataType.DICT)
        self.add_input_port("model", DataType.STRING, required=False)
        self.add_input_port("temperature", DataType.FLOAT, required=False)

        # Outputs
        self.add_output_port("extracted_data", DataType.DICT)
        self.add_output_port("raw_response", DataType.STRING)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute data extraction."""
        # Get parameters
        text = self.get_parameter("text")
        schema = self.get_parameter("schema")

        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self.set_output_value("success", False)
            self.set_output_value("error", "Text is required")
            self.set_output_value("extracted_data", {})
            return {"success": False, "error": "Text is required", "next_nodes": []}

        if not schema:
            self.set_output_value("success", False)
            self.set_output_value("error", "Schema is required")
            self.set_output_value("extracted_data", {})
            return {"success": False, "error": "Schema is required", "next_nodes": []}

        # Parse schema if string
        if isinstance(schema, str):
            try:
                schema = json.loads(schema)
            except json.JSONDecodeError as e:
                self.set_output_value("success", False)
                self.set_output_value("error", f"Invalid schema JSON: {e}")
                self.set_output_value("extracted_data", {})
                return {
                    "success": False,
                    "error": f"Invalid schema: {e}",
                    "next_nodes": [],
                }

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.0  # Low for extraction

        try:
            extracted = await manager.extract_structured(
                text=text,
                schema=schema,
                model=model,
                temperature=float(temperature),
            )

            self.set_output_value("extracted_data", extracted)
            self.set_output_value("raw_response", json.dumps(extracted))
            self.set_output_value("tokens_used", manager.metrics.total_tokens)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"LLM extraction: {len(extracted)} fields extracted")

            return {
                "success": True,
                "data": {"extracted_data": extracted},
                "next_nodes": ["exec_out"],
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response as JSON: {e}"
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("extracted_data", {})
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("extracted_data", {})
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        label="Text",
        placeholder="Text to summarize...",
        tooltip="The text to summarize",
        essential=True,
    ),
    PropertyDef(
        "max_length",
        PropertyType.INTEGER,
        default=200,
        min_value=10,
        label="Max Length (words)",
        tooltip="Maximum length of summary in words",
    ),
    PropertyDef(
        "style",
        PropertyType.CHOICE,
        default="paragraph",
        choices=["paragraph", "bullet_points", "key_points"],
        label="Style",
        tooltip="Summarization style",
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
        default=0.5,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Creativity/randomness (0-2)",
    ),
)
@node(category="llm")
class LLMSummarizeNode(LLMBaseNode):
    """
    Summarize text using an LLM.

    Supports different summarization styles (bullet points, paragraph, key points).
    """

    NODE_NAME = "LLM Summarize"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Summarize text using AI"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("max_length", DataType.INTEGER, required=False)
        self.add_input_port("style", DataType.STRING, required=False)
        self.add_input_port("model", DataType.STRING, required=False)
        self.add_input_port("temperature", DataType.FLOAT, required=False)

        # Outputs
        self.add_output_port("summary", DataType.STRING)
        self.add_output_port("original_length", DataType.INTEGER)
        self.add_output_port("summary_length", DataType.INTEGER)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute summarization."""
        # Get parameters
        text = self.get_parameter("text")
        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self.set_output_value("success", False)
            self.set_output_value("error", "Text is required")
            return {"success": False, "error": "Text is required", "next_nodes": []}

        max_length = self.get_parameter("max_length") or 200
        style = self.get_parameter("style") or "paragraph"
        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.5

        # Build summarization prompt
        style_instructions = {
            "bullet_points": "Summarize the text as bullet points, with each key point on a new line starting with '-'.",
            "paragraph": "Summarize the text in a concise paragraph.",
            "key_points": "Extract and list the key points from the text, numbered 1, 2, 3, etc.",
        }

        style_instruction = style_instructions.get(
            style, style_instructions["paragraph"]
        )

        prompt = f"""{style_instruction}

Keep the summary under {max_length} words.

Text to summarize:
{text}"""

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt="You are a summarization assistant. Provide clear, concise summaries.",
                temperature=float(temperature),
                max_tokens=int(max_length) * 2,  # Rough word-to-token ratio
            )

            summary = response.content.strip()

            self.set_output_value("summary", summary)
            self.set_output_value("original_length", len(text))
            self.set_output_value("summary_length", len(summary))
            self.set_output_value("tokens_used", response.total_tokens)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(
                f"LLM summarization: {len(text)} -> {len(summary)} chars, "
                f"{response.total_tokens} tokens"
            )

            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "compression_ratio": len(summary) / len(text) if text else 0,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("summary", "")
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        label="Text",
        placeholder="Text to classify...",
        tooltip="The text to classify",
        essential=True,
    ),
    PropertyDef(
        "categories",
        PropertyType.STRING,
        default="",
        label="Categories",
        placeholder="positive, negative, neutral",
        tooltip="Comma-separated list of categories",
        essential=True,
    ),
    PropertyDef(
        "multi_label",
        PropertyType.BOOLEAN,
        default=False,
        label="Multi-label",
        tooltip="Allow multiple categories per text",
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
        default=0.0,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Low temperature recommended for classification",
    ),
)
@node(category="llm")
class LLMClassifyNode(LLMBaseNode):
    """
    Classify text into categories using an LLM.

    Supports single-label and multi-label classification.
    """

    NODE_NAME = "LLM Classify"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Classify text into categories using AI"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("categories", DataType.LIST)
        self.add_input_port("multi_label", DataType.BOOLEAN, required=False)
        self.add_input_port("model", DataType.STRING, required=False)
        self.add_input_port("temperature", DataType.FLOAT, required=False)

        # Outputs
        self.add_output_port("classification", DataType.STRING)
        self.add_output_port("classifications", DataType.LIST)
        self.add_output_port("confidence", DataType.DICT)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute classification."""
        # Get parameters
        text = self.get_parameter("text")
        categories = self.get_parameter("categories")

        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)

        if not text:
            self.set_output_value("success", False)
            self.set_output_value("error", "Text is required")
            return {"success": False, "error": "Text is required", "next_nodes": []}

        if not categories:
            self.set_output_value("success", False)
            self.set_output_value("error", "Categories are required")
            return {
                "success": False,
                "error": "Categories are required",
                "next_nodes": [],
            }

        # Parse categories if string
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError:
                categories = [c.strip() for c in categories.split(",")]

        multi_label = self.get_parameter("multi_label") or False
        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.0

        # Build classification prompt
        categories_str = ", ".join(categories)

        if multi_label:
            prompt = f"""Classify the following text into one or more of these categories: {categories_str}

Return your answer as a JSON object with this format:
{{"categories": ["category1", "category2"], "confidence": {{"category1": 0.9, "category2": 0.7}}}}

Text to classify:
{text}

Return ONLY the JSON, no other text."""
        else:
            prompt = f"""Classify the following text into exactly one of these categories: {categories_str}

Return your answer as a JSON object with this format:
{{"category": "the_category", "confidence": 0.95}}

Text to classify:
{text}

Return ONLY the JSON, no other text."""

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt="You are a text classification assistant. Classify text accurately.",
                temperature=float(temperature),
                max_tokens=200,
            )

            # Parse response
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result = json.loads(content)

            if multi_label:
                classifications = result.get("categories", [])
                classification = classifications[0] if classifications else ""
                confidence = result.get("confidence", {})
            else:
                classification = result.get("category", "")
                classifications = [classification] if classification else []
                confidence = {"primary": result.get("confidence", 0.0)}

            self.set_output_value("classification", classification)
            self.set_output_value("classifications", classifications)
            self.set_output_value("confidence", confidence)
            self.set_output_value("tokens_used", response.total_tokens)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"LLM classification: {classification}")

            return {
                "success": True,
                "data": {
                    "classification": classification,
                    "classifications": classifications,
                    "confidence": confidence,
                },
                "next_nodes": ["exec_out"],
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse classification response: {e}"
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
        "text",
        PropertyType.TEXT,
        default="",
        label="Text",
        placeholder="Text to translate...",
        tooltip="The text to translate",
        essential=True,
    ),
    PropertyDef(
        "target_language",
        PropertyType.STRING,
        default="",
        label="Target Language",
        placeholder="Spanish, French, German...",
        tooltip="Language to translate to",
        essential=True,
    ),
    PropertyDef(
        "source_language",
        PropertyType.STRING,
        default="",
        label="Source Language",
        placeholder="Auto-detect if empty",
        tooltip="Optional source language (auto-detect if empty)",
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
        default=0.3,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Low temperature for accurate translation",
    ),
)
@node(category="llm")
class LLMTranslateNode(LLMBaseNode):
    """
    Translate text to another language using an LLM.

    Supports automatic source language detection.
    """

    NODE_NAME = "LLM Translate"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Translate text to another language using AI"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("target_language", DataType.STRING)
        self.add_input_port("source_language", DataType.STRING, required=False)
        self.add_input_port("model", DataType.STRING, required=False)
        self.add_input_port("temperature", DataType.FLOAT, required=False)

        # Outputs
        self.add_output_port("translated_text", DataType.STRING)
        self.add_output_port("detected_language", DataType.STRING)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: LLMResourceManager,
    ) -> ExecutionResult:
        """Execute translation."""
        # Get parameters
        text = self.get_parameter("text")
        target_language = self.get_parameter("target_language")

        if hasattr(context, "resolve_value"):
            text = context.resolve_value(text)
            target_language = context.resolve_value(target_language)

        if not text:
            self.set_output_value("success", False)
            self.set_output_value("error", "Text is required")
            return {"success": False, "error": "Text is required", "next_nodes": []}

        if not target_language:
            self.set_output_value("success", False)
            self.set_output_value("error", "Target language is required")
            return {
                "success": False,
                "error": "Target language is required",
                "next_nodes": [],
            }

        source_language = self.get_parameter("source_language")
        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.3

        if hasattr(context, "resolve_value") and source_language:
            source_language = context.resolve_value(source_language)

        # Build translation prompt
        if source_language:
            prompt = f"""Translate the following text from {source_language} to {target_language}.

Return your response as JSON:
{{"translated_text": "the translation", "detected_language": "{source_language}"}}

Text to translate:
{text}

Return ONLY the JSON, no other text."""
        else:
            prompt = f"""Translate the following text to {target_language}. First detect the source language.

Return your response as JSON:
{{"translated_text": "the translation", "detected_language": "detected source language"}}

Text to translate:
{text}

Return ONLY the JSON, no other text."""

        try:
            response = await manager.completion(
                prompt=prompt,
                model=model,
                system_prompt="You are a professional translator. Provide accurate, natural translations.",
                temperature=float(temperature),
                max_tokens=len(text) * 3,  # Allow for longer translations
            )

            # Parse response
            content = response.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            result = json.loads(content)

            translated = result.get("translated_text", "")
            detected = result.get("detected_language", source_language or "unknown")

            self.set_output_value("translated_text", translated)
            self.set_output_value("detected_language", detected)
            self.set_output_value("tokens_used", response.total_tokens)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"LLM translation: {detected} -> {target_language}")

            return {
                "success": True,
                "data": {
                    "translated_text": translated,
                    "source_language": detected,
                    "target_language": target_language,
                },
                "next_nodes": ["exec_out"],
            }

        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse translation response: {e}"
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "LLMCompletionNode",
    "LLMChatNode",
    "LLMExtractDataNode",
    "LLMSummarizeNode",
    "LLMClassifyNode",
    "LLMTranslateNode",
]

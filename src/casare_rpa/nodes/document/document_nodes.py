"""
CasareRPA - Document Processing Nodes

Nodes for intelligent document processing using LLM vision models.
"""

import json
from abc import abstractmethod
from typing import Any, Optional

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    PortType,
)
from casare_rpa.infrastructure.resources.document_ai_manager import (
    DocumentAIManager,
)
from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMConfig,
    LLMProvider,
)


class DocumentBaseNode(BaseNode):
    """Base class for document processing nodes."""

    NODE_CATEGORY = "Document AI"
    DEFAULT_MODEL = "gpt-4o"

    def __init__(
        self, node_id: str, name: str = "Document Node", **kwargs: Any
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name

    def _get_document_manager(self, context: Any) -> DocumentAIManager:
        """Get or create document AI manager."""
        # Check if manager exists in context
        if hasattr(context, "resources") and "document_ai" in context.resources:
            return context.resources["document_ai"]

        # Create new manager
        manager = DocumentAIManager()

        # Configure from context variables or environment
        api_key = self._get_api_key(context)
        provider = self._get_provider(context)

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        model = (
            context.resolve_value(model) if hasattr(context, "resolve_value") else model
        )

        config = LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
        )
        manager.configure(config)

        return manager

    def _get_api_key(self, context: Any) -> Optional[str]:
        """Get API key from context or environment."""
        import os

        # Check context variables
        if hasattr(context, "get_variable"):
            key = context.get_variable("OPENAI_API_KEY")
            if key:
                return key
            key = context.get_variable("ANTHROPIC_API_KEY")
            if key:
                return key

        # Fallback to environment
        return os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    def _get_provider(self, context: Any) -> LLMProvider:
        """Determine LLM provider from context or model name."""
        import os

        model = self.get_parameter("model") or self.DEFAULT_MODEL

        # Check for explicit provider in context
        if hasattr(context, "get_variable"):
            provider_str = context.get_variable("LLM_PROVIDER")
            if provider_str:
                try:
                    return LLMProvider(provider_str.lower())
                except ValueError:
                    pass

        # Infer from model name
        model_lower = model.lower()
        if "claude" in model_lower:
            return LLMProvider.ANTHROPIC
        elif "ollama" in model_lower or "llama" in model_lower:
            return LLMProvider.OLLAMA
        elif "azure" in model_lower:
            return LLMProvider.AZURE

        # Check environment for API keys
        if os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
            return LLMProvider.ANTHROPIC

        return LLMProvider.OPENAI

    async def execute(self, context: Any) -> ExecutionResult:
        """Execute the document node."""
        try:
            manager = self._get_document_manager(context)
            return await self._execute_document(context, manager)
        except Exception as e:
            logger.error(f"Document node execution failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e), "next_nodes": []}

    @abstractmethod
    async def _execute_document(
        self,
        context: Any,
        manager: DocumentAIManager,
    ) -> ExecutionResult:
        """Execute document-specific logic. Override in subclasses."""
        pass


class ClassifyDocumentNode(DocumentBaseNode):
    """Node that classifies documents into predefined categories."""

    NODE_NAME = "Classify Document"
    NODE_DESCRIPTION = (
        "Classify a document into categories (invoice, receipt, form, etc.)"
    )

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("document", PortType.INPUT, DataType.STRING)
        self.add_input_port("categories", PortType.INPUT, DataType.LIST, required=False)
        self.add_input_port("model", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("document_type", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("confidence", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("all_scores", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_document(
        self,
        context: Any,
        manager: DocumentAIManager,
    ) -> ExecutionResult:
        """Execute document classification."""
        document = self.get_parameter("document")

        if hasattr(context, "resolve_value"):
            document = context.resolve_value(document)

        if not document:
            self.set_output_value("success", False)
            self.set_output_value("error", "Document is required")
            return {"success": False, "error": "Document is required", "next_nodes": []}

        categories = self.get_parameter("categories")
        model = self.get_parameter("model")

        # Parse categories if string
        if isinstance(categories, str):
            try:
                categories = json.loads(categories)
            except json.JSONDecodeError:
                categories = [c.strip() for c in categories.split(",")]

        try:
            result = await manager.classify_document(
                document=document,
                categories=categories,
                model=model,
            )

            self.set_output_value("document_type", result.document_type.value)
            self.set_output_value("confidence", result.confidence)
            self.set_output_value("all_scores", result.all_scores)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {
                "success": True,
                "document_type": result.document_type.value,
                "confidence": result.confidence,
                "next_nodes": [],
            }

        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e), "next_nodes": []}


class ExtractInvoiceNode(DocumentBaseNode):
    """Node that extracts structured data from invoices."""

    NODE_NAME = "Extract Invoice"
    NODE_DESCRIPTION = "Extract vendor, amounts, dates, and line items from invoices"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("document", PortType.INPUT, DataType.STRING)
        self.add_input_port(
            "custom_fields", PortType.INPUT, DataType.LIST, required=False
        )
        self.add_input_port("model", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("vendor_name", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("invoice_number", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("invoice_date", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("due_date", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("total_amount", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("currency", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("subtotal", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("tax_amount", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("line_items", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("raw_extraction", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("confidence", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("needs_review", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_document(
        self,
        context: Any,
        manager: DocumentAIManager,
    ) -> ExecutionResult:
        """Execute invoice extraction."""
        document = self.get_parameter("document")

        if hasattr(context, "resolve_value"):
            document = context.resolve_value(document)

        if not document:
            self.set_output_value("success", False)
            self.set_output_value("error", "Document is required")
            return {"success": False, "error": "Document is required", "next_nodes": []}

        custom_fields = self.get_parameter("custom_fields")
        model = self.get_parameter("model")

        # Parse custom_fields if string
        if isinstance(custom_fields, str):
            try:
                custom_fields = json.loads(custom_fields)
            except json.JSONDecodeError:
                custom_fields = [f.strip() for f in custom_fields.split(",")]

        try:
            result = await manager.extract_invoice(
                document=document,
                custom_fields=custom_fields,
                model=model,
            )

            fields = result.fields

            # Set individual field outputs
            self.set_output_value("vendor_name", fields.get("vendor_name", ""))
            self.set_output_value("invoice_number", fields.get("invoice_number", ""))
            self.set_output_value("invoice_date", fields.get("invoice_date", ""))
            self.set_output_value("due_date", fields.get("due_date", ""))
            self.set_output_value("total_amount", fields.get("total_amount", 0.0))
            self.set_output_value("currency", fields.get("currency", ""))
            self.set_output_value("subtotal", fields.get("subtotal", 0.0))
            self.set_output_value("tax_amount", fields.get("tax_amount", 0.0))
            self.set_output_value("line_items", fields.get("line_items", []))
            self.set_output_value("raw_extraction", fields)
            self.set_output_value("confidence", result.confidence)
            self.set_output_value("needs_review", result.needs_review)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {
                "success": True,
                "vendor_name": fields.get("vendor_name"),
                "total_amount": fields.get("total_amount"),
                "confidence": result.confidence,
                "next_nodes": [],
            }

        except Exception as e:
            logger.error(f"Invoice extraction failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e), "next_nodes": []}


class ExtractFormNode(DocumentBaseNode):
    """Node that extracts fields from form documents."""

    NODE_NAME = "Extract Form"
    NODE_DESCRIPTION = "Extract fields from forms using a custom schema"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("document", PortType.INPUT, DataType.STRING)
        self.add_input_port("field_schema", PortType.INPUT, DataType.DICT)
        self.add_input_port(
            "fuzzy_match", PortType.INPUT, DataType.BOOLEAN, required=False
        )
        self.add_input_port("model", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("extracted_fields", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("unmatched_fields", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("confidence", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("needs_review", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_document(
        self,
        context: Any,
        manager: DocumentAIManager,
    ) -> ExecutionResult:
        """Execute form extraction."""
        document = self.get_parameter("document")
        field_schema = self.get_parameter("field_schema")

        if hasattr(context, "resolve_value"):
            document = context.resolve_value(document)

        if not document:
            self.set_output_value("success", False)
            self.set_output_value("error", "Document is required")
            return {"success": False, "error": "Document is required", "next_nodes": []}

        if not field_schema:
            self.set_output_value("success", False)
            self.set_output_value("error", "Field schema is required")
            return {
                "success": False,
                "error": "Field schema is required",
                "next_nodes": [],
            }

        # Parse schema if string
        if isinstance(field_schema, str):
            try:
                field_schema = json.loads(field_schema)
            except json.JSONDecodeError as e:
                self.set_output_value("success", False)
                self.set_output_value("error", f"Invalid schema JSON: {e}")
                return {
                    "success": False,
                    "error": f"Invalid schema: {e}",
                    "next_nodes": [],
                }

        fuzzy_match = self.get_parameter("fuzzy_match")
        if fuzzy_match is None:
            fuzzy_match = True
        model = self.get_parameter("model")

        try:
            result = await manager.extract_form(
                document=document,
                field_schema=field_schema,
                fuzzy_match=fuzzy_match,
                model=model,
            )

            self.set_output_value("extracted_fields", result.fields)
            self.set_output_value("unmatched_fields", result.validation_errors)
            self.set_output_value("confidence", result.confidence)
            self.set_output_value("needs_review", result.needs_review)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {
                "success": True,
                "extracted_fields": result.fields,
                "confidence": result.confidence,
                "next_nodes": [],
            }

        except Exception as e:
            logger.error(f"Form extraction failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e), "next_nodes": []}


class ExtractTableNode(DocumentBaseNode):
    """Node that extracts table data from documents."""

    NODE_NAME = "Extract Table"
    NODE_DESCRIPTION = "Extract tabular data from documents"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("document", PortType.INPUT, DataType.STRING)
        self.add_input_port(
            "table_hint", PortType.INPUT, DataType.STRING, required=False
        )
        self.add_input_port("model", PortType.INPUT, DataType.STRING, required=False)

        # Outputs
        self.add_output_port("tables", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("row_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("column_count", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("confidence", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def _execute_document(
        self,
        context: Any,
        manager: DocumentAIManager,
    ) -> ExecutionResult:
        """Execute table extraction."""
        document = self.get_parameter("document")

        if hasattr(context, "resolve_value"):
            document = context.resolve_value(document)

        if not document:
            self.set_output_value("success", False)
            self.set_output_value("error", "Document is required")
            return {"success": False, "error": "Document is required", "next_nodes": []}

        table_hint = self.get_parameter("table_hint")
        model = self.get_parameter("model")

        if hasattr(context, "resolve_value") and table_hint:
            table_hint = context.resolve_value(table_hint)

        try:
            result = await manager.extract_table(
                document=document,
                table_hint=table_hint,
                model=model,
            )

            self.set_output_value("tables", result.tables)
            self.set_output_value("row_count", result.row_count)
            self.set_output_value("column_count", result.column_count)
            self.set_output_value("confidence", result.confidence)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {
                "success": True,
                "tables": result.tables,
                "row_count": result.row_count,
                "column_count": result.column_count,
                "next_nodes": [],
            }

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e), "next_nodes": []}


class ValidateExtractionNode(BaseNode):
    """Node that validates extracted document data."""

    NODE_NAME = "Validate Extraction"
    NODE_DESCRIPTION = "Validate extracted data and flag for human review"
    NODE_CATEGORY = "Document AI"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = self.NODE_NAME
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("extraction", PortType.INPUT, DataType.DICT)
        self.add_input_port("required_fields", PortType.INPUT, DataType.LIST)
        self.add_input_port(
            "confidence_threshold", PortType.INPUT, DataType.FLOAT, required=False
        )
        self.add_input_port(
            "validation_rules", PortType.INPUT, DataType.DICT, required=False
        )

        # Outputs
        self.add_output_port("is_valid", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("needs_review", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("confidence_score", PortType.OUTPUT, DataType.FLOAT)
        self.add_output_port("validation_errors", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("field_status", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("error", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: Any) -> ExecutionResult:
        """Execute validation."""
        extraction = self.get_parameter("extraction")
        required_fields = self.get_parameter("required_fields")

        if not extraction:
            self.set_output_value("success", False)
            self.set_output_value("error", "Extraction data is required")
            return {
                "success": False,
                "error": "Extraction data is required",
                "next_nodes": [],
            }

        if not required_fields:
            self.set_output_value("success", False)
            self.set_output_value("error", "Required fields list is required")
            return {
                "success": False,
                "error": "Required fields list is required",
                "next_nodes": [],
            }

        # Parse inputs if strings
        if isinstance(extraction, str):
            try:
                extraction = json.loads(extraction)
            except json.JSONDecodeError as e:
                self.set_output_value("success", False)
                self.set_output_value("error", f"Invalid extraction JSON: {e}")
                return {
                    "success": False,
                    "error": f"Invalid extraction: {e}",
                    "next_nodes": [],
                }

        if isinstance(required_fields, str):
            try:
                required_fields = json.loads(required_fields)
            except json.JSONDecodeError:
                required_fields = [f.strip() for f in required_fields.split(",")]

        confidence_threshold = self.get_parameter("confidence_threshold")
        if confidence_threshold is None:
            confidence_threshold = 0.8

        validation_rules = self.get_parameter("validation_rules")
        if isinstance(validation_rules, str):
            try:
                validation_rules = json.loads(validation_rules)
            except json.JSONDecodeError:
                validation_rules = None

        try:
            # Use DocumentAIManager for validation
            manager = DocumentAIManager()
            result = manager.validate_extraction(
                extraction=extraction,
                required_fields=required_fields,
                confidence_threshold=float(confidence_threshold),
                validation_rules=validation_rules,
            )

            self.set_output_value("is_valid", result.is_valid)
            self.set_output_value("needs_review", result.needs_review)
            self.set_output_value("confidence_score", result.confidence_score)
            self.set_output_value("validation_errors", result.validation_errors)
            self.set_output_value("field_status", result.field_status)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            return {
                "success": True,
                "is_valid": result.is_valid,
                "needs_review": result.needs_review,
                "confidence_score": result.confidence_score,
                "next_nodes": [],
            }

        except Exception as e:
            logger.error(f"Validation failed: {e}")
            self.set_output_value("success", False)
            self.set_output_value("error", str(e))
            return {"success": False, "error": str(e), "next_nodes": []}

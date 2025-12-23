"""
CasareRPA - Document AI Manager

Coordinates LLM vision models for intelligent document processing.
Handles document preprocessing, extraction, and confidence scoring.
"""

import base64
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from casare_rpa.infrastructure.resources.llm_resource_manager import (
    ImageContent,
    LLMConfig,
    LLMResourceManager,
)


class DocumentType(Enum):
    """Supported document types."""

    INVOICE = "invoice"
    RECEIPT = "receipt"
    FORM = "form"
    CONTRACT = "contract"
    LETTER = "letter"
    REPORT = "report"
    TABLE = "table"
    OTHER = "other"


@dataclass
class DocumentClassification:
    """Result of document classification."""

    document_type: DocumentType
    confidence: float
    all_scores: dict[str, float]
    raw_response: str | None = None


@dataclass
class ExtractionResult:
    """Result of document extraction."""

    fields: dict[str, Any]
    confidence: float
    field_confidences: dict[str, float] = field(default_factory=dict)
    raw_response: str | None = None
    needs_review: bool = False
    validation_errors: list[str] = field(default_factory=list)


@dataclass
class TableExtractionResult:
    """Result of table extraction."""

    tables: list[dict[str, Any]]
    row_count: int
    column_count: int
    confidence: float
    raw_response: str | None = None


@dataclass
class ValidationResult:
    """Result of extraction validation."""

    is_valid: bool
    needs_review: bool
    confidence_score: float
    validation_errors: list[str]
    field_status: dict[str, str]  # field -> "valid" | "invalid" | "missing"


class DocumentAIManager:
    """
    Manager for AI-powered document processing.

    Coordinates LLM vision models for:
    - Document classification
    - Field extraction (invoices, forms)
    - Table extraction
    - Validation and confidence scoring
    """

    # Default models for vision tasks
    DEFAULT_VISION_MODEL = "gpt-4o"
    FALLBACK_VISION_MODEL = "gpt-4o-mini"

    # Invoice field schema
    INVOICE_SCHEMA = {
        "vendor_name": "string",
        "invoice_number": "string",
        "invoice_date": "string (YYYY-MM-DD)",
        "due_date": "string (YYYY-MM-DD)",
        "total_amount": "number",
        "currency": "string (3-letter code)",
        "subtotal": "number",
        "tax_amount": "number",
        "line_items": "array of {description, quantity, unit_price, amount}",
    }

    def __init__(self) -> None:
        """Initialize the document AI manager."""
        self._llm_manager: LLMResourceManager | None = None
        self._config: LLMConfig | None = None
        logger.debug("DocumentAIManager initialized")

    def configure(self, config: LLMConfig) -> None:
        """Configure the underlying LLM manager."""
        self._config = config
        self._llm_manager = LLMResourceManager()
        self._llm_manager.configure(config)
        logger.debug(f"DocumentAIManager configured with {config.provider.value}")

    def _get_llm_manager(self) -> LLMResourceManager:
        """Get or create LLM manager."""
        if self._llm_manager is None:
            self._llm_manager = LLMResourceManager()
            if self._config:
                self._llm_manager.configure(self._config)
        return self._llm_manager

    async def _encode_document(self, document: str | bytes) -> tuple[str, str]:
        """
        Encode document for vision API.

        Args:
            document: File path or base64 encoded bytes

        Returns:
            Tuple of (base64_data, media_type)
        """
        if isinstance(document, bytes):
            # Already bytes, encode to base64
            return base64.b64encode(document).decode("utf-8"), "image/png"

        # Assume it's a file path
        path = Path(document)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {document}")

        # Determine media type from extension
        ext = path.suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }
        media_type = media_types.get(ext, "image/png")

        # Read and encode file
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")

        return data, media_type

    async def classify_document(
        self,
        document: str | bytes,
        categories: list[str] | None = None,
        model: str | None = None,
    ) -> DocumentClassification:
        """
        Classify a document into predefined categories.

        Args:
            document: File path or bytes of the document
            categories: List of category names (default: standard document types)
            model: Vision model to use

        Returns:
            DocumentClassification with type and confidence
        """
        manager = self._get_llm_manager()

        if categories is None:
            categories = [dt.value for dt in DocumentType]

        model = model or self.DEFAULT_VISION_MODEL
        base64_data, media_type = await self._encode_document(document)

        prompt = f"""Analyze this document image and classify it into one of these categories:
{json.dumps(categories, indent=2)}

Respond with a JSON object containing:
- "document_type": the most likely category (must be one from the list)
- "confidence": confidence score between 0 and 1
- "all_scores": dict mapping each category to its confidence score

Example response:
{{"document_type": "invoice", "confidence": 0.95, "all_scores": {{"invoice": 0.95, "receipt": 0.03, "form": 0.02}}}}

Only return the JSON, no other text."""

        # Create image content for vision API
        image = ImageContent(base64_data=base64_data, media_type=media_type)

        try:
            response = await manager.vision_completion(
                prompt=prompt,
                images=[image],
                model=model,
                temperature=0.0,
                max_tokens=500,
            )

            # Parse response
            result = json.loads(response.content)

            doc_type_str = result.get("document_type", "other").lower()
            try:
                doc_type = DocumentType(doc_type_str)
            except ValueError:
                doc_type = DocumentType.OTHER

            return DocumentClassification(
                document_type=doc_type,
                confidence=float(result.get("confidence", 0.0)),
                all_scores=result.get("all_scores", {}),
                raw_response=response.content,
            )

        except Exception as e:
            logger.error(f"Document classification failed: {e}")
            return DocumentClassification(
                document_type=DocumentType.OTHER,
                confidence=0.0,
                all_scores={},
                raw_response=str(e),
            )

    async def extract_invoice(
        self,
        document: str | bytes,
        custom_fields: list[str] | None = None,
        model: str | None = None,
    ) -> ExtractionResult:
        """
        Extract structured data from an invoice.

        Args:
            document: File path or bytes of the invoice
            custom_fields: Additional fields to extract
            model: Vision model to use

        Returns:
            ExtractionResult with invoice fields
        """
        manager = self._get_llm_manager()
        model = model or self.DEFAULT_VISION_MODEL

        # Build schema with custom fields
        schema = dict(self.INVOICE_SCHEMA)
        if custom_fields:
            for field_name in custom_fields:
                schema[field_name] = "string"

        base64_data, media_type = await self._encode_document(document)

        prompt = f"""Extract invoice data from this document image.

Extract these fields:
{json.dumps(schema, indent=2)}

Rules:
- For dates, use YYYY-MM-DD format
- For currency, use 3-letter ISO code (USD, EUR, etc.)
- For amounts, return numbers without currency symbols
- For line_items, extract each line as a separate object
- If a field is not found, return null

Respond with a JSON object containing:
- "fields": the extracted data matching the schema
- "confidence": overall confidence score (0-1)
- "field_confidences": dict mapping each field to its confidence

Only return the JSON, no other text."""

        # Create image content for vision API
        image = ImageContent(base64_data=base64_data, media_type=media_type)

        try:
            response = await manager.vision_completion(
                prompt=prompt,
                images=[image],
                model=model,
                temperature=0.0,
                max_tokens=2000,
            )

            result = json.loads(response.content)

            return ExtractionResult(
                fields=result.get("fields", {}),
                confidence=float(result.get("confidence", 0.0)),
                field_confidences=result.get("field_confidences", {}),
                raw_response=response.content,
                needs_review=result.get("confidence", 0.0) < 0.8,
            )

        except Exception as e:
            logger.error(f"Invoice extraction failed: {e}")
            return ExtractionResult(
                fields={},
                confidence=0.0,
                raw_response=str(e),
                needs_review=True,
                validation_errors=[str(e)],
            )

    async def extract_form(
        self,
        document: str | bytes,
        field_schema: dict[str, str],
        fuzzy_match: bool = True,
        model: str | None = None,
    ) -> ExtractionResult:
        """
        Extract fields from a form document.

        Args:
            document: File path or bytes of the form
            field_schema: Dict mapping field names to expected types
            fuzzy_match: Whether to use fuzzy matching for field names
            model: Vision model to use

        Returns:
            ExtractionResult with form fields
        """
        manager = self._get_llm_manager()
        model = model or self.DEFAULT_VISION_MODEL
        base64_data, media_type = await self._encode_document(document)

        fuzzy_instruction = ""
        if fuzzy_match:
            fuzzy_instruction = """
Use fuzzy matching for field names - if a label is similar to a schema field,
map it to that field. For example, "Full Name" should map to "name" if that's in the schema."""

        prompt = f"""Extract form data from this document image.

Expected fields and types:
{json.dumps(field_schema, indent=2)}
{fuzzy_instruction}

Rules:
- Extract values for each field in the schema
- If a field is not found, return null
- Match form labels to schema fields intelligently

Respond with a JSON object containing:
- "fields": the extracted data matching the schema
- "confidence": overall confidence score (0-1)
- "field_confidences": dict mapping each field to its confidence
- "unmatched_fields": list of fields found in document but not in schema

Only return the JSON, no other text."""

        # Create image content for vision API
        image = ImageContent(base64_data=base64_data, media_type=media_type)

        try:
            response = await manager.vision_completion(
                prompt=prompt,
                images=[image],
                model=model,
                temperature=0.0,
                max_tokens=2000,
            )

            result = json.loads(response.content)

            return ExtractionResult(
                fields=result.get("fields", {}),
                confidence=float(result.get("confidence", 0.0)),
                field_confidences=result.get("field_confidences", {}),
                raw_response=response.content,
                needs_review=result.get("confidence", 0.0) < 0.8,
                validation_errors=result.get("unmatched_fields", []),
            )

        except Exception as e:
            logger.error(f"Form extraction failed: {e}")
            return ExtractionResult(
                fields={},
                confidence=0.0,
                raw_response=str(e),
                needs_review=True,
                validation_errors=[str(e)],
            )

    async def extract_table(
        self,
        document: str | bytes,
        table_hint: str | None = None,
        model: str | None = None,
    ) -> TableExtractionResult:
        """
        Extract table data from a document.

        Args:
            document: File path or bytes of the document
            table_hint: Description of expected table structure
            model: Vision model to use

        Returns:
            TableExtractionResult with table data
        """
        manager = self._get_llm_manager()
        model = model or self.DEFAULT_VISION_MODEL
        base64_data, media_type = await self._encode_document(document)

        hint_text = ""
        if table_hint:
            hint_text = f"\nHint about the table: {table_hint}"

        prompt = f"""Extract all tables from this document image.{hint_text}

For each table found, extract:
- Headers (column names)
- All rows of data

Respond with a JSON object containing:
- "tables": array of tables, each with "headers" and "rows"
- "row_count": total number of data rows across all tables
- "column_count": maximum number of columns
- "confidence": overall confidence score (0-1)

Example format:
{{
    "tables": [
        {{
            "headers": ["Item", "Qty", "Price"],
            "rows": [
                ["Widget A", 5, 10.00],
                ["Widget B", 3, 15.00]
            ]
        }}
    ],
    "row_count": 2,
    "column_count": 3,
    "confidence": 0.92
}}

Only return the JSON, no other text."""

        # Create image content for vision API
        image = ImageContent(base64_data=base64_data, media_type=media_type)

        try:
            response = await manager.vision_completion(
                prompt=prompt,
                images=[image],
                model=model,
                temperature=0.0,
                max_tokens=4000,
            )

            result = json.loads(response.content)

            return TableExtractionResult(
                tables=result.get("tables", []),
                row_count=int(result.get("row_count", 0)),
                column_count=int(result.get("column_count", 0)),
                confidence=float(result.get("confidence", 0.0)),
                raw_response=response.content,
            )

        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return TableExtractionResult(
                tables=[],
                row_count=0,
                column_count=0,
                confidence=0.0,
                raw_response=str(e),
            )

    def validate_extraction(
        self,
        extraction: dict[str, Any],
        required_fields: list[str],
        confidence_threshold: float = 0.8,
        validation_rules: dict[str, Any] | None = None,
    ) -> ValidationResult:
        """
        Validate extracted data against requirements.

        Args:
            extraction: Extracted field data
            required_fields: Fields that must be present
            confidence_threshold: Minimum confidence for auto-approval
            validation_rules: Optional validation rules per field

        Returns:
            ValidationResult with validation status
        """
        errors = []
        field_status = {}

        # Check required fields
        for field_name in required_fields:
            if field_name not in extraction or extraction[field_name] is None:
                errors.append(f"Required field '{field_name}' is missing")
                field_status[field_name] = "missing"
            else:
                field_status[field_name] = "valid"

        # Apply validation rules if provided
        if validation_rules:
            for field_name, rules in validation_rules.items():
                if field_name not in extraction:
                    continue

                value = extraction[field_name]

                # Type validation
                if "type" in rules:
                    expected_type = rules["type"]
                    if expected_type == "number" and not isinstance(value, (int, float)):
                        errors.append(f"Field '{field_name}' should be a number")
                        field_status[field_name] = "invalid"
                    elif expected_type == "string" and not isinstance(value, str):
                        errors.append(f"Field '{field_name}' should be a string")
                        field_status[field_name] = "invalid"

                # Min/max for numbers
                if isinstance(value, (int, float)):
                    if "min" in rules and value < rules["min"]:
                        errors.append(f"Field '{field_name}' is below minimum ({rules['min']})")
                        field_status[field_name] = "invalid"
                    if "max" in rules and value > rules["max"]:
                        errors.append(f"Field '{field_name}' exceeds maximum ({rules['max']})")
                        field_status[field_name] = "invalid"

                # Pattern matching for strings
                if isinstance(value, str) and "pattern" in rules:
                    import re

                    if not re.match(rules["pattern"], value):
                        errors.append(f"Field '{field_name}' doesn't match expected pattern")
                        field_status[field_name] = "invalid"

        # Calculate confidence
        valid_count = sum(1 for s in field_status.values() if s == "valid")
        total_count = len(field_status) if field_status else 1
        confidence_score = valid_count / total_count

        is_valid = len(errors) == 0
        needs_review = confidence_score < confidence_threshold or not is_valid

        return ValidationResult(
            is_valid=is_valid,
            needs_review=needs_review,
            confidence_score=confidence_score,
            validation_errors=errors,
            field_status=field_status,
        )

    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self._llm_manager:
            await self._llm_manager.cleanup()
            self._llm_manager = None
        logger.debug("DocumentAIManager cleaned up")

    def __repr__(self) -> str:
        """String representation."""
        if self._config:
            return f"DocumentAIManager(provider={self._config.provider.value})"
        return "DocumentAIManager(not configured)"

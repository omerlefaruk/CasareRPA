"""Tests for Document AI Manager."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.infrastructure.resources.document_ai_manager import (
    DocumentAIManager,
    DocumentType,
    DocumentClassification,
    ExtractionResult,
    TableExtractionResult,
    ValidationResult,
)
from casare_rpa.infrastructure.resources.llm_resource_manager import (
    LLMConfig,
    LLMProvider,
)


class TestDocumentType:
    """Tests for DocumentType enum."""

    def test_document_types(self):
        """Test all document types exist."""
        assert DocumentType.INVOICE.value == "invoice"
        assert DocumentType.RECEIPT.value == "receipt"
        assert DocumentType.FORM.value == "form"
        assert DocumentType.CONTRACT.value == "contract"
        assert DocumentType.OTHER.value == "other"


class TestDocumentClassification:
    """Tests for DocumentClassification dataclass."""

    def test_create_classification(self):
        """Test creating a classification result."""
        result = DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.95,
            all_scores={"invoice": 0.95, "receipt": 0.03, "form": 0.02},
        )
        assert result.document_type == DocumentType.INVOICE
        assert result.confidence == 0.95
        assert result.all_scores["invoice"] == 0.95


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_create_extraction_result(self):
        """Test creating an extraction result."""
        result = ExtractionResult(
            fields={"vendor_name": "Acme Corp", "total_amount": 100.00},
            confidence=0.90,
            needs_review=False,
        )
        assert result.fields["vendor_name"] == "Acme Corp"
        assert result.confidence == 0.90
        assert result.needs_review is False

    def test_extraction_with_errors(self):
        """Test extraction result with validation errors."""
        result = ExtractionResult(
            fields={},
            confidence=0.0,
            needs_review=True,
            validation_errors=["Failed to parse document"],
        )
        assert len(result.validation_errors) == 1
        assert result.needs_review is True


class TestTableExtractionResult:
    """Tests for TableExtractionResult dataclass."""

    def test_create_table_result(self):
        """Test creating a table extraction result."""
        result = TableExtractionResult(
            tables=[
                {
                    "headers": ["Item", "Qty", "Price"],
                    "rows": [["Widget", 5, 10.00]],
                }
            ],
            row_count=1,
            column_count=3,
            confidence=0.88,
        )
        assert len(result.tables) == 1
        assert result.row_count == 1
        assert result.column_count == 3


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_create_valid_result(self):
        """Test creating a valid validation result."""
        result = ValidationResult(
            is_valid=True,
            needs_review=False,
            confidence_score=0.95,
            validation_errors=[],
            field_status={"vendor_name": "valid", "total_amount": "valid"},
        )
        assert result.is_valid is True
        assert result.needs_review is False
        assert len(result.validation_errors) == 0

    def test_create_invalid_result(self):
        """Test creating an invalid validation result."""
        result = ValidationResult(
            is_valid=False,
            needs_review=True,
            confidence_score=0.5,
            validation_errors=["Required field 'total_amount' is missing"],
            field_status={"vendor_name": "valid", "total_amount": "missing"},
        )
        assert result.is_valid is False
        assert result.needs_review is True
        assert len(result.validation_errors) == 1


class TestDocumentAIManager:
    """Tests for DocumentAIManager."""

    def test_init(self):
        """Test initialization."""
        manager = DocumentAIManager()
        assert manager._llm_manager is None
        assert manager._config is None

    def test_configure(self):
        """Test configuration."""
        manager = DocumentAIManager()
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o",
            api_key="test-key",
        )
        manager.configure(config)

        assert manager._config == config
        assert manager._llm_manager is not None

    def test_repr_not_configured(self):
        """Test string representation when not configured."""
        manager = DocumentAIManager()
        assert "not configured" in repr(manager)

    def test_repr_configured(self):
        """Test string representation when configured."""
        manager = DocumentAIManager()
        manager.configure(LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o"))
        assert "openai" in repr(manager)


class TestDocumentAIManagerValidation:
    """Tests for DocumentAIManager validation methods."""

    def test_validate_extraction_success(self):
        """Test successful validation."""
        manager = DocumentAIManager()

        extraction = {
            "vendor_name": "Acme Corp",
            "total_amount": 100.00,
            "invoice_date": "2024-01-15",
        }
        required_fields = ["vendor_name", "total_amount"]

        result = manager.validate_extraction(
            extraction=extraction,
            required_fields=required_fields,
        )

        assert result.is_valid is True
        assert result.needs_review is False
        assert len(result.validation_errors) == 0

    def test_validate_extraction_missing_field(self):
        """Test validation with missing required field."""
        manager = DocumentAIManager()

        extraction = {"vendor_name": "Acme Corp"}
        required_fields = ["vendor_name", "total_amount"]

        result = manager.validate_extraction(
            extraction=extraction,
            required_fields=required_fields,
        )

        assert result.is_valid is False
        assert result.needs_review is True
        assert "total_amount" in result.validation_errors[0]

    def test_validate_extraction_with_rules(self):
        """Test validation with custom rules."""
        manager = DocumentAIManager()

        extraction = {
            "vendor_name": "Acme Corp",
            "total_amount": -50.00,  # Invalid: negative
        }
        required_fields = ["vendor_name", "total_amount"]
        validation_rules = {
            "total_amount": {"type": "number", "min": 0},
        }

        result = manager.validate_extraction(
            extraction=extraction,
            required_fields=required_fields,
            validation_rules=validation_rules,
        )

        assert result.is_valid is False
        assert "below minimum" in result.validation_errors[0]

    def test_validate_extraction_confidence_threshold(self):
        """Test validation with low confidence triggers review."""
        manager = DocumentAIManager()

        extraction = {"vendor_name": "Acme"}  # Only 1 of 2 fields
        required_fields = ["vendor_name", "total_amount"]

        result = manager.validate_extraction(
            extraction=extraction,
            required_fields=required_fields,
            confidence_threshold=0.9,
        )

        assert result.needs_review is True  # Missing field = low confidence

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup."""
        manager = DocumentAIManager()
        manager.configure(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test")
        )

        await manager.cleanup()
        assert manager._llm_manager is None


class TestDocumentAIManagerClassification:
    """Tests for document classification."""

    @pytest.mark.asyncio
    async def test_classify_document_success(self):
        """Test successful document classification."""
        manager = DocumentAIManager()
        manager.configure(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test")
        )

        mock_response = MagicMock()
        mock_response.content = '{"document_type": "invoice", "confidence": 0.95, "all_scores": {"invoice": 0.95}}'

        with patch.object(
            manager._llm_manager, "completion", new_callable=AsyncMock
        ) as mock_completion:
            mock_completion.return_value = mock_response

            # Mock file reading
            with patch("builtins.open", MagicMock()):
                with patch("pathlib.Path.exists", return_value=True):
                    with patch(
                        "casare_rpa.infrastructure.resources.document_ai_manager.DocumentAIManager._encode_document",
                        new_callable=AsyncMock,
                    ) as mock_encode:
                        mock_encode.return_value = ("base64data", "image/png")

                        result = await manager.classify_document(
                            document="test.png",
                        )

        assert result.document_type == DocumentType.INVOICE
        assert result.confidence == 0.95


class TestDocumentAIManagerExtraction:
    """Tests for document extraction."""

    @pytest.mark.asyncio
    async def test_extract_invoice_success(self):
        """Test successful invoice extraction."""
        manager = DocumentAIManager()
        manager.configure(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test")
        )

        mock_response = MagicMock()
        mock_response.content = """{
            "fields": {
                "vendor_name": "Acme Corp",
                "invoice_number": "INV-001",
                "total_amount": 100.00
            },
            "confidence": 0.92,
            "field_confidences": {"vendor_name": 0.95, "total_amount": 0.90}
        }"""

        with patch.object(
            manager._llm_manager, "completion", new_callable=AsyncMock
        ) as mock_completion:
            mock_completion.return_value = mock_response

            with patch(
                "casare_rpa.infrastructure.resources.document_ai_manager.DocumentAIManager._encode_document",
                new_callable=AsyncMock,
            ) as mock_encode:
                mock_encode.return_value = ("base64data", "image/png")

                result = await manager.extract_invoice(document="invoice.png")

        assert result.fields["vendor_name"] == "Acme Corp"
        assert result.confidence == 0.92
        assert result.needs_review is False  # Confidence > 0.8

    @pytest.mark.asyncio
    async def test_extract_form_success(self):
        """Test successful form extraction."""
        manager = DocumentAIManager()
        manager.configure(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test")
        )

        mock_response = MagicMock()
        mock_response.content = """{
            "fields": {"name": "John Doe", "email": "john@example.com"},
            "confidence": 0.88,
            "field_confidences": {"name": 0.95, "email": 0.80},
            "unmatched_fields": ["phone"]
        }"""

        with patch.object(
            manager._llm_manager, "completion", new_callable=AsyncMock
        ) as mock_completion:
            mock_completion.return_value = mock_response

            with patch(
                "casare_rpa.infrastructure.resources.document_ai_manager.DocumentAIManager._encode_document",
                new_callable=AsyncMock,
            ) as mock_encode:
                mock_encode.return_value = ("base64data", "image/png")

                result = await manager.extract_form(
                    document="form.png",
                    field_schema={"name": "string", "email": "string"},
                )

        assert result.fields["name"] == "John Doe"
        assert result.confidence == 0.88

    @pytest.mark.asyncio
    async def test_extract_table_success(self):
        """Test successful table extraction."""
        manager = DocumentAIManager()
        manager.configure(
            LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4o", api_key="test")
        )

        mock_response = MagicMock()
        mock_response.content = """{
            "tables": [
                {
                    "headers": ["Item", "Qty", "Price"],
                    "rows": [["Widget A", 5, 10.00], ["Widget B", 3, 15.00]]
                }
            ],
            "row_count": 2,
            "column_count": 3,
            "confidence": 0.91
        }"""

        with patch.object(
            manager._llm_manager, "completion", new_callable=AsyncMock
        ) as mock_completion:
            mock_completion.return_value = mock_response

            with patch(
                "casare_rpa.infrastructure.resources.document_ai_manager.DocumentAIManager._encode_document",
                new_callable=AsyncMock,
            ) as mock_encode:
                mock_encode.return_value = ("base64data", "image/png")

                result = await manager.extract_table(document="table.png")

        assert len(result.tables) == 1
        assert result.row_count == 2
        assert result.column_count == 3
        assert result.confidence == 0.91

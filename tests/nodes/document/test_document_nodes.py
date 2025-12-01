"""Tests for Document Processing Nodes."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from casare_rpa.nodes.document.document_nodes import (
    ClassifyDocumentNode,
    ExtractInvoiceNode,
    ExtractFormNode,
    ExtractTableNode,
    ValidateExtractionNode,
)
from casare_rpa.infrastructure.resources.document_ai_manager import (
    DocumentAIManager,
    DocumentType,
    DocumentClassification,
    ExtractionResult,
    TableExtractionResult,
)


@pytest.fixture
def mock_execution_context():
    """Create mock execution context."""
    context = MagicMock()
    context.resources = {}
    context.resolve_value = lambda x: x
    context.get_variable = MagicMock(return_value=None)
    return context


@pytest.fixture
def mock_document_manager():
    """Create mock document AI manager."""
    manager = MagicMock(spec=DocumentAIManager)
    return manager


class TestClassifyDocumentNode:
    """Tests for ClassifyDocumentNode."""

    def test_init(self):
        """Test node initialization."""
        node = ClassifyDocumentNode("test-node")
        assert node.name == "Classify Document"
        assert node.NODE_CATEGORY == "Document AI"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = ClassifyDocumentNode("test-node")

        # Check input ports
        assert "document" in node.input_ports
        assert "categories" in node.input_ports
        assert "model" in node.input_ports

        # Check output ports
        assert "document_type" in node.output_ports
        assert "confidence" in node.output_ports
        assert "all_scores" in node.output_ports
        assert "success" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_document(self, mock_execution_context):
        """Test execution fails without document."""
        node = ClassifyDocumentNode("test-node", config={"document": ""})

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_execution_context, mock_document_manager):
        """Test successful classification."""
        node = ClassifyDocumentNode("test-node", config={"document": "test.png"})

        mock_classification = DocumentClassification(
            document_type=DocumentType.INVOICE,
            confidence=0.95,
            all_scores={"invoice": 0.95, "receipt": 0.03},
        )
        mock_document_manager.classify_document = AsyncMock(
            return_value=mock_classification
        )

        with patch.object(
            node, "_get_document_manager", return_value=mock_document_manager
        ):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("document_type") == "invoice"
        assert node.get_output_value("confidence") == 0.95


class TestExtractInvoiceNode:
    """Tests for ExtractInvoiceNode."""

    def test_init(self):
        """Test node initialization."""
        node = ExtractInvoiceNode("test-node")
        assert node.name == "Extract Invoice"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = ExtractInvoiceNode("test-node")

        # Check input ports
        assert "document" in node.input_ports
        assert "custom_fields" in node.input_ports

        # Check output ports
        assert "vendor_name" in node.output_ports
        assert "invoice_number" in node.output_ports
        assert "total_amount" in node.output_ports
        assert "line_items" in node.output_ports
        assert "confidence" in node.output_ports
        assert "needs_review" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_document(self, mock_execution_context):
        """Test execution fails without document."""
        node = ExtractInvoiceNode("test-node", config={"document": ""})

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_execution_context, mock_document_manager):
        """Test successful invoice extraction."""
        node = ExtractInvoiceNode("test-node", config={"document": "invoice.png"})

        mock_extraction = ExtractionResult(
            fields={
                "vendor_name": "Acme Corp",
                "invoice_number": "INV-001",
                "total_amount": 100.00,
                "currency": "USD",
                "line_items": [{"description": "Widget", "amount": 100.00}],
            },
            confidence=0.92,
            needs_review=False,
        )
        mock_document_manager.extract_invoice = AsyncMock(return_value=mock_extraction)

        with patch.object(
            node, "_get_document_manager", return_value=mock_document_manager
        ):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("vendor_name") == "Acme Corp"
        assert node.get_output_value("total_amount") == 100.00
        assert node.get_output_value("confidence") == 0.92


class TestExtractFormNode:
    """Tests for ExtractFormNode."""

    def test_init(self):
        """Test node initialization."""
        node = ExtractFormNode("test-node")
        assert node.name == "Extract Form"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = ExtractFormNode("test-node")

        assert "document" in node.input_ports
        assert "field_schema" in node.input_ports
        assert "fuzzy_match" in node.input_ports

        assert "extracted_fields" in node.output_ports
        assert "unmatched_fields" in node.output_ports
        assert "confidence" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_document(self, mock_execution_context):
        """Test execution fails without document."""
        node = ExtractFormNode(
            "test-node",
            config={"document": "", "field_schema": {"name": "string"}},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_missing_schema(self, mock_execution_context):
        """Test execution fails without schema."""
        node = ExtractFormNode(
            "test-node",
            config={"document": "form.png", "field_schema": None},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_execution_context, mock_document_manager):
        """Test successful form extraction."""
        node = ExtractFormNode(
            "test-node",
            config={
                "document": "form.png",
                "field_schema": {"name": "string", "email": "string"},
            },
        )

        mock_extraction = ExtractionResult(
            fields={"name": "John Doe", "email": "john@example.com"},
            confidence=0.88,
            needs_review=False,
        )
        mock_document_manager.extract_form = AsyncMock(return_value=mock_extraction)

        with patch.object(
            node, "_get_document_manager", return_value=mock_document_manager
        ):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("extracted_fields")["name"] == "John Doe"


class TestExtractTableNode:
    """Tests for ExtractTableNode."""

    def test_init(self):
        """Test node initialization."""
        node = ExtractTableNode("test-node")
        assert node.name == "Extract Table"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = ExtractTableNode("test-node")

        assert "document" in node.input_ports
        assert "table_hint" in node.input_ports

        assert "tables" in node.output_ports
        assert "row_count" in node.output_ports
        assert "column_count" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_document(self, mock_execution_context):
        """Test execution fails without document."""
        node = ExtractTableNode("test-node", config={"document": ""})

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_success(self, mock_execution_context, mock_document_manager):
        """Test successful table extraction."""
        node = ExtractTableNode("test-node", config={"document": "table.png"})

        mock_result = TableExtractionResult(
            tables=[
                {
                    "headers": ["Item", "Qty", "Price"],
                    "rows": [["Widget A", 5, 10.00]],
                }
            ],
            row_count=1,
            column_count=3,
            confidence=0.91,
        )
        mock_document_manager.extract_table = AsyncMock(return_value=mock_result)

        with patch.object(
            node, "_get_document_manager", return_value=mock_document_manager
        ):
            result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("row_count") == 1
        assert node.get_output_value("column_count") == 3


class TestValidateExtractionNode:
    """Tests for ValidateExtractionNode."""

    def test_init(self):
        """Test node initialization."""
        node = ValidateExtractionNode("test-node")
        assert node.name == "Validate Extraction"
        assert node.NODE_CATEGORY == "Document AI"

    def test_has_required_ports(self):
        """Test node has required ports."""
        node = ValidateExtractionNode("test-node")

        assert "extraction" in node.input_ports
        assert "required_fields" in node.input_ports
        assert "confidence_threshold" in node.input_ports

        assert "is_valid" in node.output_ports
        assert "needs_review" in node.output_ports
        assert "validation_errors" in node.output_ports

    @pytest.mark.asyncio
    async def test_execute_missing_extraction(self, mock_execution_context):
        """Test execution fails without extraction data."""
        node = ValidateExtractionNode(
            "test-node",
            config={"extraction": None, "required_fields": ["vendor_name"]},
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_missing_required_fields(self, mock_execution_context):
        """Test execution fails without required_fields."""
        node = ValidateExtractionNode(
            "test-node",
            config={
                "extraction": {"vendor_name": "Acme"},
                "required_fields": None,
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_execute_valid_extraction(self, mock_execution_context):
        """Test validation of valid extraction."""
        node = ValidateExtractionNode(
            "test-node",
            config={
                "extraction": {
                    "vendor_name": "Acme Corp",
                    "total_amount": 100.00,
                },
                "required_fields": ["vendor_name", "total_amount"],
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_valid") is True
        assert node.get_output_value("needs_review") is False

    @pytest.mark.asyncio
    async def test_execute_invalid_extraction(self, mock_execution_context):
        """Test validation of invalid extraction (missing field)."""
        node = ValidateExtractionNode(
            "test-node",
            config={
                "extraction": {"vendor_name": "Acme Corp"},
                "required_fields": ["vendor_name", "total_amount"],
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True  # Validation succeeded, but data is invalid
        assert node.get_output_value("is_valid") is False
        assert node.get_output_value("needs_review") is True
        assert len(node.get_output_value("validation_errors")) > 0

    @pytest.mark.asyncio
    async def test_execute_with_validation_rules(self, mock_execution_context):
        """Test validation with custom rules."""
        node = ValidateExtractionNode(
            "test-node",
            config={
                "extraction": {
                    "vendor_name": "Acme Corp",
                    "total_amount": -50.00,  # Invalid
                },
                "required_fields": ["vendor_name", "total_amount"],
                "validation_rules": {
                    "total_amount": {"type": "number", "min": 0},
                },
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_valid") is False
        assert "below minimum" in node.get_output_value("validation_errors")[0]

    @pytest.mark.asyncio
    async def test_execute_with_string_inputs(self, mock_execution_context):
        """Test validation with JSON string inputs."""
        node = ValidateExtractionNode(
            "test-node",
            config={
                "extraction": '{"vendor_name": "Acme Corp", "total_amount": 100}',
                "required_fields": '["vendor_name", "total_amount"]',
            },
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert node.get_output_value("is_valid") is True

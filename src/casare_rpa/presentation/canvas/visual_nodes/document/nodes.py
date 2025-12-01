"""Visual nodes for Document AI category.

Provides visual node wrappers for document processing operations including:
- Document classification
- Invoice extraction
- Form extraction
- Table extraction
- Extraction validation
"""

from typing import List, Tuple

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


def get_llm_credentials() -> List[Tuple[str, str]]:
    """Get available LLM credentials for dropdown.

    Returns:
        List of (id, display_name) tuples, with "Auto-detect" as first option.
    """
    credentials = [("auto", "Auto-detect from model")]

    try:
        from casare_rpa.infrastructure.security.credential_store import (
            get_credential_store,
        )

        store = get_credential_store()
        for cred in store.list_credentials(category="llm"):
            credentials.append((cred["id"], cred["name"]))
    except ImportError:
        pass

    return credentials


# Vision-capable models for document processing
VISION_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "claude-3-5-sonnet-latest",
    "claude-3-5-haiku-latest",
    "claude-3-opus-latest",
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-2.0-flash-exp",
]

# Document types for classification
DOCUMENT_TYPES = [
    "invoice",
    "receipt",
    "form",
    "contract",
    "letter",
    "report",
    "id_document",
    "bank_statement",
    "medical_record",
    "other",
]


class VisualClassifyDocumentNode(VisualNode):
    """Visual representation of ClassifyDocumentNode.

    Classify documents into categories (invoice, receipt, form, etc.)
    """

    __identifier__ = "casare_rpa.document"
    NODE_NAME = "Classify Document"
    NODE_CATEGORY = "document"

    def __init__(self) -> None:
        """Initialize classify document node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "document", "Document", placeholder_text="Path or base64 image..."
        )
        self.add_text_input(
            "categories",
            "Categories",
            placeholder_text="invoice, receipt, form (comma-separated)",
        )
        self.add_combo_menu("model", "Model", items=VISION_MODELS)
        self.set_property("model", "gpt-4o")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("document", DataType.STRING)
        self.add_typed_input("categories", DataType.LIST)
        self.add_typed_input("model", DataType.STRING)

        # Data outputs
        self.add_typed_output("document_type", DataType.STRING)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("all_scores", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualExtractInvoiceNode(VisualNode):
    """Visual representation of ExtractInvoiceNode.

    Extract vendor, amounts, dates, and line items from invoices.
    """

    __identifier__ = "casare_rpa.document"
    NODE_NAME = "Extract Invoice"
    NODE_CATEGORY = "document"

    def __init__(self) -> None:
        """Initialize extract invoice node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "document", "Document", placeholder_text="Path or base64 image..."
        )
        self.add_text_input(
            "custom_fields",
            "Custom Fields",
            placeholder_text="Additional fields (comma-separated)",
        )
        self.add_combo_menu("model", "Model", items=VISION_MODELS)
        self.set_property("model", "gpt-4o")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("document", DataType.STRING)
        self.add_typed_input("custom_fields", DataType.LIST)
        self.add_typed_input("model", DataType.STRING)

        # Data outputs
        self.add_typed_output("vendor_name", DataType.STRING)
        self.add_typed_output("invoice_number", DataType.STRING)
        self.add_typed_output("invoice_date", DataType.STRING)
        self.add_typed_output("due_date", DataType.STRING)
        self.add_typed_output("total_amount", DataType.FLOAT)
        self.add_typed_output("currency", DataType.STRING)
        self.add_typed_output("subtotal", DataType.FLOAT)
        self.add_typed_output("tax_amount", DataType.FLOAT)
        self.add_typed_output("line_items", DataType.LIST)
        self.add_typed_output("raw_extraction", DataType.DICT)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("needs_review", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualExtractFormNode(VisualNode):
    """Visual representation of ExtractFormNode.

    Extract fields from forms using a custom schema.
    """

    __identifier__ = "casare_rpa.document"
    NODE_NAME = "Extract Form"
    NODE_CATEGORY = "document"

    def __init__(self) -> None:
        """Initialize extract form node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "document", "Document", placeholder_text="Path or base64 image..."
        )
        self.add_text_input(
            "field_schema",
            "Field Schema",
            placeholder_text='{"name": "string", "email": "string", "date": "date"}',
        )
        self.add_checkbox("fuzzy_match", "Fuzzy Match", state=True)
        self.add_combo_menu("model", "Model", items=VISION_MODELS)
        self.set_property("model", "gpt-4o")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("document", DataType.STRING)
        self.add_typed_input("field_schema", DataType.DICT)
        self.add_typed_input("fuzzy_match", DataType.BOOLEAN)
        self.add_typed_input("model", DataType.STRING)

        # Data outputs
        self.add_typed_output("extracted_fields", DataType.DICT)
        self.add_typed_output("unmatched_fields", DataType.LIST)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("needs_review", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualExtractTableNode(VisualNode):
    """Visual representation of ExtractTableNode.

    Extract tabular data from documents.
    """

    __identifier__ = "casare_rpa.document"
    NODE_NAME = "Extract Table"
    NODE_CATEGORY = "document"

    def __init__(self) -> None:
        """Initialize extract table node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Credential selector
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_text_input(
            "document", "Document", placeholder_text="Path or base64 image..."
        )
        self.add_text_input(
            "table_hint",
            "Table Hint",
            placeholder_text="Optional: describe which table to extract",
        )
        self.add_combo_menu("model", "Model", items=VISION_MODELS)
        self.set_property("model", "gpt-4o")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("document", DataType.STRING)
        self.add_typed_input("table_hint", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)

        # Data outputs
        self.add_typed_output("tables", DataType.LIST)
        self.add_typed_output("row_count", DataType.INTEGER)
        self.add_typed_output("column_count", DataType.INTEGER)
        self.add_typed_output("confidence", DataType.FLOAT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualValidateExtractionNode(VisualNode):
    """Visual representation of ValidateExtractionNode.

    Validate extracted data and flag for human review.
    """

    __identifier__ = "casare_rpa.document"
    NODE_NAME = "Validate Extraction"
    NODE_CATEGORY = "document"

    def __init__(self) -> None:
        """Initialize validate extraction node."""
        super().__init__()
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        self.add_text_input(
            "extraction",
            "Extraction",
            placeholder_text="Extraction data (JSON or from previous node)",
        )
        self.add_text_input(
            "required_fields",
            "Required Fields",
            placeholder_text="vendor_name, total_amount (comma-separated)",
        )
        self.add_text_input("confidence_threshold", "Confidence Threshold", text="0.8")
        self.add_text_input(
            "validation_rules",
            "Validation Rules",
            placeholder_text='{"total_amount": {"min": 0, "max": 1000000}}',
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("extraction", DataType.DICT)
        self.add_typed_input("required_fields", DataType.LIST)
        self.add_typed_input("confidence_threshold", DataType.FLOAT)
        self.add_typed_input("validation_rules", DataType.DICT)

        # Data outputs
        self.add_typed_output("is_valid", DataType.BOOLEAN)
        self.add_typed_output("needs_review", DataType.BOOLEAN)
        self.add_typed_output("confidence_score", DataType.FLOAT)
        self.add_typed_output("validation_errors", DataType.LIST)
        self.add_typed_output("field_status", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

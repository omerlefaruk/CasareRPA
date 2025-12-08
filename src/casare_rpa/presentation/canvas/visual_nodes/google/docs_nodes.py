"""Visual nodes for Google Docs operations.

All nodes use Google credential picker for OAuth authentication.
Document operations also use Drive file picker filtered for Google Docs.
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeGoogleCredentialWidget,
    NodeGoogleDriveFileWidget,
)

# Google Docs API scope
DOCS_SCOPE = ["https://www.googleapis.com/auth/documents"]
# Additional Drive scope for document listing
DOCS_WITH_DRIVE_SCOPE = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.readonly",
]

# MIME type for Google Docs documents
GOOGLE_DOCS_MIME_TYPE = ["application/vnd.google-apps.document"]


class VisualGoogleDocsBaseNode(VisualNode):
    """Base class for Google Docs visual nodes with credential picker integration."""

    REQUIRED_SCOPES = DOCS_WITH_DRIVE_SCOPE

    def __init__(self, qgraphics_item=None) -> None:
        super().__init__(qgraphics_item)

    def setup_widgets(self) -> None:
        """Setup credential picker widget."""
        self._cred_widget = NodeGoogleCredentialWidget(
            name="credential_id",
            label="Google Account",
            scopes=self.REQUIRED_SCOPES,
        )
        if self._cred_widget:
            self.add_custom_widget(self._cred_widget)
            self._cred_widget.setParentItem(self.view)

    def setup_document_widget(self) -> None:
        """Setup Drive file picker widget filtered for Google Docs."""
        self._document_widget = NodeGoogleDriveFileWidget(
            name="document_id",
            label="Document",
            credential_widget=self._cred_widget,
            mime_types=GOOGLE_DOCS_MIME_TYPE,
        )
        if self._document_widget:
            self.add_custom_widget(self._document_widget)
            self._document_widget.setParentItem(self.view)


# =============================================================================
# Document Operations
# =============================================================================


class VisualDocsCreateDocumentNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsCreateDocumentNode.

    Creates a new Google Doc. Only needs credential picker since
    no existing document is required.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Create Document"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsCreateDocumentNode"
    REQUIRED_SCOPES = DOCS_SCOPE

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("title", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("document_id", DataType.STRING)
        self.add_typed_output("document_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsGetDocumentNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsGetDocumentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Get Document"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsGetDocumentNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("body", DataType.OBJECT)
        self.add_typed_output("revision_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


class VisualDocsGetContentNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsGetTextNode (gets document content)."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Get Content"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsGetTextNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("word_count", DataType.INTEGER)
        self.add_typed_output("character_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


# =============================================================================
# Text Operations
# =============================================================================


class VisualDocsInsertTextNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsInsertTextNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Text"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertTextNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


class VisualDocsDeleteContentNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsDeleteContentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Delete Content"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsDeleteContentNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


class VisualDocsReplaceTextNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsReplaceTextNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Replace Text"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsReplaceTextNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("find_text", DataType.STRING)
        self.add_typed_input("replace_text", DataType.STRING)
        self.add_typed_input("match_case", DataType.BOOLEAN)
        self.add_exec_output("exec_out")
        self.add_typed_output("occurrences_changed", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


# =============================================================================
# Formatting Operations
# =============================================================================


class VisualDocsInsertTableNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsInsertTableNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Table"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertTableNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("rows", DataType.INTEGER)
        self.add_typed_input("columns", DataType.INTEGER)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


class VisualDocsInsertImageNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsInsertImageNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Image"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertImageNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("image_uri", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_typed_input("image_width", DataType.FLOAT)
        self.add_typed_input("image_height", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


class VisualDocsUpdateStyleNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsApplyStyleNode (updates text styling)."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Update Style"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsApplyStyleNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()


class VisualDocsBatchUpdateNode(VisualGoogleDocsBaseNode):
    """Visual representation of DocsBatchUpdateNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Batch Update"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsBatchUpdateNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("requests", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("replies", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self.setup_document_widget()

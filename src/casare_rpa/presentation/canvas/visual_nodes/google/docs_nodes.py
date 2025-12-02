"""Visual nodes for Google Docs operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Document Operations
# =============================================================================


class VisualDocsCreateDocumentNode(VisualNode):
    """Visual representation of DocsCreateDocumentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Create Document"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsCreateDocumentNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "title",
            "Title",
            text="New Document",
            tab="properties",
            placeholder_text="Document title",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("title", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("document_id", DataType.STRING)
        self.add_typed_output("document_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsGetDocumentNode(VisualNode):
    """Visual representation of DocsGetDocumentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Get Document"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsGetDocumentNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "document_id",
            "Document ID",
            text="",
            tab="properties",
            placeholder_text="1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("body", DataType.OBJECT)
        self.add_typed_output("revision_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsGetContentNode(VisualNode):
    """Visual representation of DocsGetContentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Get Content"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsGetContentNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("word_count", DataType.INTEGER)
        self.add_typed_output("character_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Text Operations
# =============================================================================


class VisualDocsInsertTextNode(VisualNode):
    """Visual representation of DocsInsertTextNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Text"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertTextNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")
        self.add_text_input("text", "Text", text="", tab="properties")
        self.add_text_input(
            "index",
            "Index (1=start)",
            text="1",
            tab="properties",
            placeholder_text="Insert position",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsDeleteContentNode(VisualNode):
    """Visual representation of DocsDeleteContentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Delete Content"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsDeleteContentNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")
        self.add_text_input("start_index", "Start Index", text="1", tab="properties")
        self.add_text_input("end_index", "End Index", text="2", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsReplaceTextNode(VisualNode):
    """Visual representation of DocsReplaceTextNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Replace Text"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsReplaceTextNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")
        self.add_text_input(
            "find_text",
            "Find Text",
            text="",
            tab="properties",
            placeholder_text="Text to find",
        )
        self.add_text_input(
            "replace_text",
            "Replace With",
            text="",
            tab="properties",
            placeholder_text="Replacement text",
        )
        self.add_checkbox("match_case", "Match Case", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("find_text", DataType.STRING)
        self.add_typed_input("replace_text", DataType.STRING)
        self.add_typed_input("match_case", DataType.BOOLEAN)
        self.add_exec_output("exec_out")
        self.add_typed_output("occurrences_changed", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Formatting Operations
# =============================================================================


class VisualDocsInsertTableNode(VisualNode):
    """Visual representation of DocsInsertTableNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Table"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertTableNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")
        self.add_text_input("rows", "Rows", text="3", tab="properties")
        self.add_text_input("columns", "Columns", text="3", tab="properties")
        self.add_text_input("index", "Insert Index", text="1", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("rows", DataType.INTEGER)
        self.add_typed_input("columns", DataType.INTEGER)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsInsertImageNode(VisualNode):
    """Visual representation of DocsInsertImageNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Image"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertImageNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")
        self.add_text_input(
            "image_uri",
            "Image URL",
            text="",
            tab="properties",
            placeholder_text="https://example.com/image.png",
        )
        self.add_text_input("index", "Insert Index", text="1", tab="properties")
        self.add_text_input(
            "width", "Width (points, 0=auto)", text="0", tab="properties"
        )
        self.add_text_input(
            "height", "Height (points, 0=auto)", text="0", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("image_uri", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_typed_input("width", DataType.FLOAT)
        self.add_typed_input("height", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsUpdateStyleNode(VisualNode):
    """Visual representation of DocsUpdateStyleNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Update Style"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsUpdateStyleNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")
        self.add_text_input("start_index", "Start Index", text="1", tab="properties")
        self.add_text_input("end_index", "End Index", text="10", tab="properties")
        # Style options
        self.add_checkbox("bold", "Bold", state=False, tab="formatting")
        self.add_checkbox("italic", "Italic", state=False, tab="formatting")
        self.add_checkbox("underline", "Underline", state=False, tab="formatting")
        self.add_text_input(
            "font_size", "Font Size (points)", text="0", tab="formatting"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsBatchUpdateNode(VisualNode):
    """Visual representation of DocsBatchUpdateNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Batch Update"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsBatchUpdateNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("document_id", "Document ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("requests", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("replies", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

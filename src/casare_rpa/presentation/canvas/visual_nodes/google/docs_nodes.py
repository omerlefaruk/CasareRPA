"""Visual nodes for Google Docs operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Document Operations
# =============================================================================


class VisualDocsCreateDocumentNode(VisualNode):
    """Visual representation of DocsCreateDocumentNode.

    Widgets are auto-generated from DocsCreateDocumentNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Create Document"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsCreateDocumentNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("title", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("document_id", DataType.STRING)
        self.add_typed_output("document_url", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsGetDocumentNode(VisualNode):
    """Visual representation of DocsGetDocumentNode.

    Widgets are auto-generated from DocsGetDocumentNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Get Document"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsGetDocumentNode"

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
    """Visual representation of DocsGetTextNode (gets document content).

    Widgets are auto-generated from DocsGetTextNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Get Content"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsGetTextNode"

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
    """Visual representation of DocsInsertTextNode.

    Widgets are auto-generated from DocsInsertTextNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Text"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertTextNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsDeleteContentNode(VisualNode):
    """Visual representation of DocsDeleteContentNode.

    Widgets are auto-generated from DocsDeleteContentNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Delete Content"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsDeleteContentNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsReplaceTextNode(VisualNode):
    """Visual representation of DocsReplaceTextNode.

    Widgets are auto-generated from DocsReplaceTextNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Replace Text"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsReplaceTextNode"

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
    """Visual representation of DocsInsertTableNode.

    Widgets are auto-generated from DocsInsertTableNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Table"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertTableNode"

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
    """Visual representation of DocsInsertImageNode.

    Widgets are auto-generated from DocsInsertImageNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Insert Image"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsInsertImageNode"

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
    """Visual representation of DocsApplyStyleNode (updates text styling).

    Widgets are auto-generated from DocsApplyStyleNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Update Style"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsApplyStyleNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("start_index", DataType.INTEGER)
        self.add_typed_input("end_index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualDocsBatchUpdateNode(VisualNode):
    """Visual representation of DocsBatchUpdateNode.

    Widgets are auto-generated from DocsBatchUpdateNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Docs: Batch Update"
    NODE_CATEGORY = "google/docs"
    CASARE_NODE_CLASS = "DocsBatchUpdateNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("document_id", DataType.STRING)
        self.add_typed_input("requests", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("replies", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

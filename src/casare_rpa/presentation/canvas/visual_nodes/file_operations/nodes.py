"""Visual nodes for file_operations category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
)


def _replace_widget(node: VisualNode, widget) -> None:
    """
    Replace auto-generated widget with custom widget.

    If a property already exists (from @node_schema auto-generation),
    remove it first to avoid NodePropertyError conflicts.

    Args:
        node: The visual node
        widget: The custom widget to add (NodeFilePathWidget or NodeDirectoryPathWidget)
    """
    prop_name = widget._name  # NodeBaseWidget stores name as _name
    # Remove existing property if it was auto-generated from schema
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        # Also remove from widgets dict if present
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]
    # Now safely add our custom widget
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)


# Import logic layer nodes
from casare_rpa.nodes.file import (
    ReadFileNode,
    WriteFileNode,
    AppendFileNode,
    DeleteFileNode,
    CopyFileNode,
    MoveFileNode,
    FileExistsNode,
    GetFileSizeNode,
    GetFileInfoNode,
    ListFilesNode,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    ZipFilesNode,
    UnzipFilesNode,
)


# =============================================================================
# Basic File Operations
# =============================================================================


class VisualReadFileNode(VisualNode):
    """Visual representation of ReadFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read File"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "ReadFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File Path",
                file_filter="All Files (*.*)",
                placeholder="Select file to read...",
            ),
        )

    def get_node_class(self) -> type:
        return ReadFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("content", DataType.STRING)
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWriteFileNode(VisualNode):
    """Visual representation of WriteFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write File"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "WriteFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File Path",
                file_filter="All Files (*.*)",
                placeholder="Select file to write...",
            ),
        )

    def get_node_class(self) -> type:
        return WriteFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("content", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("bytes_written", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualAppendFileNode(VisualNode):
    """Visual representation of AppendFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Append File"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "AppendFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File Path",
                file_filter="All Files (*.*)",
                placeholder="Select file to append...",
            ),
        )

    def get_node_class(self) -> type:
        return AppendFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("content", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("bytes_written", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualDeleteFileNode(VisualNode):
    """Visual representation of DeleteFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Delete File"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "DeleteFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File Path",
                file_filter="All Files (*.*)",
                placeholder="Select file to delete...",
            ),
        )

    def get_node_class(self) -> type:
        return DeleteFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualCopyFileNode(VisualNode):
    """Visual representation of CopyFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Copy File"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "CopyFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="source_path",
                label="Source File",
                file_filter="All Files (*.*)",
                placeholder="Select source file...",
            ),
        )
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="dest_path",
                label="Destination",
                file_filter="All Files (*.*)",
                placeholder="Select destination...",
            ),
        )

    def get_node_class(self) -> type:
        return CopyFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("source_path", DataType.STRING)
        self.add_typed_input("dest_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("dest_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMoveFileNode(VisualNode):
    """Visual representation of MoveFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Move File"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "MoveFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="source_path",
                label="Source File",
                file_filter="All Files (*.*)",
                placeholder="Select source file...",
            ),
        )
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="dest_path",
                label="Destination",
                file_filter="All Files (*.*)",
                placeholder="Select destination...",
            ),
        )

    def get_node_class(self) -> type:
        return MoveFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("source_path", DataType.STRING)
        self.add_typed_input("dest_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("dest_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualFileExistsNode(VisualNode):
    """Visual representation of FileExistsNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "File Exists"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "FileExistsNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="path",
                label="Path",
                file_filter="All Files (*.*)",
                placeholder="Select file or folder...",
            ),
        )

    def get_node_class(self) -> type:
        return FileExistsNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("exists", DataType.BOOLEAN)
        self.add_typed_output("is_file", DataType.BOOLEAN)
        self.add_typed_output("is_dir", DataType.BOOLEAN)


class VisualGetFileSizeNode(VisualNode):
    """Visual representation of GetFileSizeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get File Size"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "GetFileSizeNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File Path",
                file_filter="All Files (*.*)",
                placeholder="Select file...",
            ),
        )

    def get_node_class(self) -> type:
        return GetFileSizeNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetFileInfoNode(VisualNode):
    """Visual representation of GetFileInfoNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get File Info"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "GetFileInfoNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="File Path",
                file_filter="All Files (*.*)",
                placeholder="Select file...",
            ),
        )

    def get_node_class(self) -> type:
        return GetFileInfoNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("created", DataType.STRING)
        self.add_typed_output("modified", DataType.STRING)
        self.add_typed_output("extension", DataType.STRING)
        self.add_typed_output("name", DataType.STRING)
        self.add_typed_output("parent", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualListFilesNode(VisualNode):
    """Visual representation of ListFilesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "List Files"
    NODE_CATEGORY = "file_operations/basic"
    CASARE_NODE_CLASS = "ListFilesNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeDirectoryPathWidget(
                name="directory_path",
                label="Directory",
                placeholder="Select directory...",
            ),
        )

    def get_node_class(self) -> type:
        return ListFilesNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("directory_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("files", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# CSV Operations
# =============================================================================


class VisualReadCsvNode(VisualNode):
    """Visual representation of ReadCSVNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read CSV"
    NODE_CATEGORY = "file_operations/csv"
    CASARE_NODE_CLASS = "ReadCSVNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="CSV File",
                file_filter="CSV Files (*.csv);;All Files (*.*)",
                placeholder="Select CSV file...",
            ),
        )

    def get_node_class(self) -> type:
        return ReadCSVNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("data", DataType.LIST)
        self.add_typed_output("headers", DataType.LIST)
        self.add_typed_output("row_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWriteCsvNode(VisualNode):
    """Visual representation of WriteCSVNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write CSV"
    NODE_CATEGORY = "file_operations/csv"
    CASARE_NODE_CLASS = "WriteCSVNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="CSV File",
                file_filter="CSV Files (*.csv);;All Files (*.*)",
                placeholder="Select CSV file...",
            ),
        )

    def get_node_class(self) -> type:
        return WriteCSVNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("data", DataType.LIST)
        self.add_typed_input("headers", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("rows_written", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# JSON Operations
# =============================================================================


class VisualReadJsonNode(VisualNode):
    """Visual representation of ReadJSONFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read JSON"
    NODE_CATEGORY = "file_operations/json"
    CASARE_NODE_CLASS = "ReadJSONFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="JSON File",
                file_filter="JSON Files (*.json);;All Files (*.*)",
                placeholder="Select JSON file...",
            ),
        )

    def get_node_class(self) -> type:
        return ReadJSONFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("data", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWriteJsonNode(VisualNode):
    """Visual representation of WriteJSONFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write JSON"
    NODE_CATEGORY = "file_operations/json"
    CASARE_NODE_CLASS = "WriteJSONFileNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="JSON File",
                file_filter="JSON Files (*.json);;All Files (*.*)",
                placeholder="Select JSON file...",
            ),
        )

    def get_node_class(self) -> type:
        return WriteJSONFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("data", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# ZIP Operations
# =============================================================================


class VisualZipFilesNode(VisualNode):
    """Visual representation of ZipFilesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Zip Files"
    NODE_CATEGORY = "file_operations/archive"
    CASARE_NODE_CLASS = "ZipFilesNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="zip_path",
                label="ZIP File",
                file_filter="ZIP Files (*.zip);;All Files (*.*)",
                placeholder="Select ZIP file path...",
            ),
        )

    def get_node_class(self) -> type:
        return ZipFilesNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("zip_path", DataType.STRING)
        self.add_typed_input("files", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("zip_path", DataType.STRING)
        self.add_typed_output("file_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualUnzipFileNode(VisualNode):
    """Visual representation of UnzipFilesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Unzip File"
    NODE_CATEGORY = "file_operations/archive"
    CASARE_NODE_CLASS = "UnzipFilesNode"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="zip_path",
                label="ZIP File",
                file_filter="ZIP Files (*.zip);;All Files (*.*)",
                placeholder="Select ZIP file...",
            ),
        )
        _replace_widget(
            self,
            NodeDirectoryPathWidget(
                name="extract_to",
                label="Extract To",
                placeholder="Select extraction folder...",
            ),
        )

    def get_node_class(self) -> type:
        return UnzipFilesNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("zip_path", DataType.STRING)
        self.add_typed_input("extract_to", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("extract_to", DataType.STRING)
        self.add_typed_output("files", DataType.LIST)
        self.add_typed_output("file_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# XML Operations
# =============================================================================


class VisualParseXMLNode(VisualNode):
    """Visual representation of ParseXMLNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Parse XML"
    NODE_CATEGORY = "file_operations/xml"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("root_tag", DataType.STRING)
        self.add_typed_output("child_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualReadXMLFileNode(VisualNode):
    """Visual representation of ReadXMLFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read XML File"
    NODE_CATEGORY = "file_operations/xml"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="XML File",
                file_filter="XML Files (*.xml);;All Files (*.*)",
                placeholder="Select XML file...",
            ),
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("xml_string", DataType.STRING)
        self.add_typed_output("root_tag", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWriteXMLFileNode(VisualNode):
    """Visual representation of WriteXMLFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write XML File"
    NODE_CATEGORY = "file_operations/xml"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="XML File",
                file_filter="XML Files (*.xml);;All Files (*.*)",
                placeholder="Select XML file...",
            ),
        )
        self.add_checkbox("pretty_print", "Pretty Print", state=True, tab="properties")
        self.add_checkbox(
            "xml_declaration", "XML Declaration", state=True, tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualXPathQueryNode(VisualNode):
    """Visual representation of XPathQueryNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "XPath Query"
    NODE_CATEGORY = "file_operations/xml"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_typed_input("xpath", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("first_text", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetXMLElementNode(VisualNode):
    """Visual representation of GetXMLElementNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get XML Element"
    NODE_CATEGORY = "file_operations/xml"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_typed_input("tag_name", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("tag", DataType.STRING)
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("attributes", DataType.DICT)
        self.add_typed_output("child_count", DataType.INTEGER)
        self.add_typed_output("found", DataType.BOOLEAN)


class VisualGetXMLAttributeNode(VisualNode):
    """Visual representation of GetXMLAttributeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get XML Attribute"
    NODE_CATEGORY = "file_operations/xml"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_typed_input("xpath", DataType.STRING)
        self.add_typed_input("attribute_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("found", DataType.BOOLEAN)


class VisualXMLToJsonNode(VisualNode):
    """Visual representation of XMLToJsonNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "XML To JSON"
    NODE_CATEGORY = "file_operations/xml"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox(
            "include_attributes", "Include Attributes", state=True, tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("json_data", DataType.DICT)
        self.add_typed_output("json_string", DataType.STRING)


class VisualJsonToXMLNode(VisualNode):
    """Visual representation of JsonToXMLNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "JSON To XML"
    NODE_CATEGORY = "file_operations/xml"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("root_tag", "Root Tag", text="root", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("json_data", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("xml_string", DataType.STRING)


# =============================================================================
# PDF Operations
# =============================================================================


class VisualReadPDFTextNode(VisualNode):
    """Visual representation of ReadPDFTextNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read PDF Text"
    NODE_CATEGORY = "file_operations/pdf"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="PDF File",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select PDF file...",
            ),
        )
        self.add_text_input("start_page", "Start Page", text="", tab="properties")
        self.add_text_input("end_page", "End Page", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("pages", DataType.LIST)
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetPDFInfoNode(VisualNode):
    """Visual representation of GetPDFInfoNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get PDF Info"
    NODE_CATEGORY = "file_operations/pdf"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="PDF File",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select PDF file...",
            ),
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("author", DataType.STRING)
        self.add_typed_output("subject", DataType.STRING)
        self.add_typed_output("creator", DataType.STRING)
        self.add_typed_output("metadata", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMergePDFsNode(VisualNode):
    """Visual representation of MergePDFsNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Merge PDFs"
    NODE_CATEGORY = "file_operations/pdf"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="output_path",
                label="Output PDF",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select output file...",
            ),
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("input_files", DataType.LIST)
        self.add_typed_input("output_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_path", DataType.STRING)
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSplitPDFNode(VisualNode):
    """Visual representation of SplitPDFNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Split PDF"
    NODE_CATEGORY = "file_operations/pdf"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="PDF File",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select PDF file...",
            ),
        )
        _replace_widget(
            self,
            NodeDirectoryPathWidget(
                name="output_dir",
                label="Output Directory",
                placeholder="Select output folder...",
            ),
        )
        self.add_text_input(
            "pages_per_file", "Pages Per File", text="1", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("output_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_files", DataType.LIST)
        self.add_typed_output("file_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualExtractPDFPagesNode(VisualNode):
    """Visual representation of ExtractPDFPagesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Extract PDF Pages"
    NODE_CATEGORY = "file_operations/pdf"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="Input PDF",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select PDF file...",
            ),
        )
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="output_path",
                label="Output PDF",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select output file...",
            ),
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("pages", DataType.LIST)
        self.add_typed_input("output_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_path", DataType.STRING)
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualPDFToImagesNode(VisualNode):
    """Visual representation of PDFToImagesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "PDF To Images"
    NODE_CATEGORY = "file_operations/pdf"

    def __init__(self) -> None:
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="PDF File",
                file_filter="PDF Files (*.pdf);;All Files (*.*)",
                placeholder="Select PDF file...",
            ),
        )
        _replace_widget(
            self,
            NodeDirectoryPathWidget(
                name="output_dir",
                label="Output Directory",
                placeholder="Select output folder...",
            ),
        )
        self.add_combo_menu(
            "format", "Format", items=["png", "jpeg", "jpg"], tab="properties"
        )
        self.add_text_input("dpi", "DPI", text="200", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("output_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("image_paths", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# FTP Operations
# =============================================================================


class VisualFTPConnectNode(VisualNode):
    """Visual representation of FTPConnectNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Connect"
    NODE_CATEGORY = "file_operations/ftp"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("passive", "Passive Mode", state=True, tab="properties")
        self.add_checkbox("use_tls", "Use TLS", state=False, tab="properties")
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_interval",
            "Retry Interval (s)",
            placeholder_text="2.0",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("host", DataType.STRING)
        self.add_typed_input("port", DataType.INTEGER)
        self.add_typed_input("username", DataType.STRING)
        self.add_typed_input("password", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("connected", DataType.BOOLEAN)
        self.add_typed_output("server_message", DataType.STRING)


class VisualFTPUploadNode(VisualNode):
    """Visual representation of FTPUploadNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Upload"
    NODE_CATEGORY = "file_operations/ftp"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("binary_mode", "Binary Mode", state=True, tab="properties")
        self.add_checkbox("create_dirs", "Create Dirs", state=False, tab="properties")
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_interval",
            "Retry Interval (s)",
            placeholder_text="2.0",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("local_path", DataType.STRING)
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("uploaded", DataType.BOOLEAN)
        self.add_typed_output("bytes_sent", DataType.INTEGER)


class VisualFTPDownloadNode(VisualNode):
    """Visual representation of FTPDownloadNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Download"
    NODE_CATEGORY = "file_operations/ftp"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("binary_mode", "Binary Mode", state=True, tab="properties")
        self.add_checkbox("overwrite", "Overwrite", state=False, tab="properties")
        self.add_text_input(
            "retry_count", "Retry Count", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "retry_interval",
            "Retry Interval (s)",
            placeholder_text="2.0",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_typed_input("local_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("downloaded", DataType.BOOLEAN)
        self.add_typed_output("bytes_received", DataType.INTEGER)


class VisualFTPListNode(VisualNode):
    """Visual representation of FTPListNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP List"
    NODE_CATEGORY = "file_operations/ftp"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("detailed", "Detailed", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("items", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualFTPDeleteNode(VisualNode):
    """Visual representation of FTPDeleteNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Delete"
    NODE_CATEGORY = "file_operations/ftp"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted", DataType.BOOLEAN)


class VisualFTPMakeDirNode(VisualNode):
    """Visual representation of FTPMakeDirNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Make Dir"
    NODE_CATEGORY = "file_operations/ftp"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("parents", "Create Parents", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("created", DataType.BOOLEAN)


class VisualFTPRemoveDirNode(VisualNode):
    """Visual representation of FTPRemoveDirNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Remove Dir"
    NODE_CATEGORY = "file_operations/ftp"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("removed", DataType.BOOLEAN)


class VisualFTPRenameNode(VisualNode):
    """Visual representation of FTPRenameNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Rename"
    NODE_CATEGORY = "file_operations/ftp"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("old_path", DataType.STRING)
        self.add_typed_input("new_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("renamed", DataType.BOOLEAN)


class VisualFTPDisconnectNode(VisualNode):
    """Visual representation of FTPDisconnectNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Disconnect"
    NODE_CATEGORY = "file_operations/ftp"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("disconnected", DataType.BOOLEAN)


class VisualFTPGetSizeNode(VisualNode):
    """Visual representation of FTPGetSizeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Get Size"
    NODE_CATEGORY = "file_operations/ftp"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("found", DataType.BOOLEAN)

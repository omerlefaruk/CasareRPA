"""Visual nodes for file_operations category.

NOTE: Basic file operations, CSV, JSON, ZIP, and Image nodes have been
consolidated into Super Nodes (FileSystemSuperNode, StructuredDataSuperNode).
Old workflows will be automatically migrated via NODE_TYPE_ALIASES in workflow_loader.

This file now contains only XML, PDF, and FTP visual nodes which are not yet consolidated.
"""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
)


def _replace_widget(node: VisualNode, widget) -> None:
    """
    Replace auto-generated widget with custom widget.

    If a property already exists (from @properties auto-generation),
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
        self.add_checkbox(
            "pretty_print", label="", text="Pretty Print", state=True, tab="properties"
        )
        self.add_checkbox(
            "xml_declaration",
            label="",
            text="XML Declaration",
            state=True,
            tab="properties",
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
        self.add_checkbox(
            "passive", label="", text="Passive Mode", state=True, tab="properties"
        )
        self.add_checkbox(
            "use_tls", label="", text="Use TLS", state=False, tab="properties"
        )
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
        self.add_checkbox(
            "binary_mode", label="", text="Binary Mode", state=True, tab="properties"
        )
        self.add_checkbox(
            "create_dirs", label="", text="Create Dirs", state=False, tab="properties"
        )
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
        self.add_checkbox(
            "binary_mode", label="", text="Binary Mode", state=True, tab="properties"
        )
        self.add_checkbox(
            "overwrite", label="", text="Overwrite", state=False, tab="properties"
        )
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
        self.add_checkbox(
            "detailed", label="", text="Detailed", state=False, tab="properties"
        )

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
        self.add_checkbox(
            "parents", label="", text="Create Parents", state=False, tab="properties"
        )

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

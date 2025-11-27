"""Visual nodes for file_operations category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.core.types import DataType

# Import logic layer nodes
from casare_rpa.nodes.file_nodes import (
    GetFileSizeNode,
    ListFilesNode,
    ReadCSVNode,
    WriteCSVNode,
    ReadJSONFileNode,
    WriteJSONFileNode,
    UnzipFilesNode,
)


# =============================================================================
# Basic File Operations
# =============================================================================


class VisualReadFileNode(VisualNode):
    """Visual representation of ReadFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.create_property("binary_mode", False, widget_type=1, tab="config")
        self.add_combo_menu(
            "errors",
            "Error Handling",
            items=["strict", "ignore", "replace", "backslashreplace"],
            tab="advanced",
        )
        self.add_text_input(
            "max_size",
            "Max Size (bytes)",
            placeholder_text="0 = unlimited",
            tab="advanced",
        )

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("content")
        self.add_output("size")
        self.add_output("success")


class VisualWriteFileNode(VisualNode):
    """Visual representation of WriteFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("content", "Content", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.create_property("create_dirs", True, widget_type=1, tab="config")
        self.add_combo_menu(
            "errors",
            "Error Handling",
            items=["strict", "ignore", "replace", "backslashreplace"],
            tab="advanced",
        )
        self.create_property("append_mode", False, widget_type=1, tab="advanced")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("content")
        self.add_output("exec_out")
        self.add_output("bytes_written")
        self.add_output("success")


class VisualAppendFileNode(VisualNode):
    """Visual representation of AppendFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Append File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("content", "Content", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("content")
        self.add_output("exec_out")
        self.add_output("bytes_written")
        self.add_output("success")


class VisualDeleteFileNode(VisualNode):
    """Visual representation of DeleteFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Delete File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("ignore_errors", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("success")


class VisualCopyFileNode(VisualNode):
    """Visual representation of CopyFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Copy File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("source_path", "Source Path", text="", tab="inputs")
        self.add_text_input("dest_path", "Destination Path", text="", tab="inputs")
        self.create_property("overwrite", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("source_path")
        self.add_input("dest_path")
        self.add_output("exec_out")
        self.add_output("dest_path")
        self.add_output("success")


class VisualMoveFileNode(VisualNode):
    """Visual representation of MoveFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Move File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("source_path", "Source Path", text="", tab="inputs")
        self.add_text_input("dest_path", "Destination Path", text="", tab="inputs")
        self.create_property("overwrite", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("source_path")
        self.add_input("dest_path")
        self.add_output("exec_out")
        self.add_output("dest_path")
        self.add_output("success")


class VisualFileExistsNode(VisualNode):
    """Visual representation of FileExistsNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "File Exists"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("exists")
        self.add_output("is_file")
        self.add_output("is_dir")


class VisualGetFileSizeNode(VisualNode):
    """Visual representation of GetFileSizeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get File Size"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "GetFileSizeNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

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
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("size")
        self.add_output("created")
        self.add_output("modified")
        self.add_output("extension")
        self.add_output("name")
        self.add_output("parent")
        self.add_output("success")


class VisualListFilesNode(VisualNode):
    """Visual representation of ListFilesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "List Files"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "ListFilesNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("directory_path", "Directory Path", text=".", tab="inputs")
        self.add_text_input("pattern", "Pattern", text="*", tab="config")
        self.create_property("recursive", False, widget_type=1, tab="config")

    def get_node_class(self) -> type:
        return ListFilesNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("directory_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("files", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


# =============================================================================
# CSV Operations
# =============================================================================


class VisualReadCsvNode(VisualNode):
    """Visual representation of ReadCSVNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read CSV"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "ReadCSVNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("has_header", True, widget_type=1, tab="config")
        self.add_text_input("delimiter", "Delimiter", text=",", tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.add_text_input("quotechar", "Quote Char", text='"', tab="advanced")
        self.add_text_input(
            "skip_rows", "Skip Rows", placeholder_text="0", tab="advanced"
        )
        self.add_text_input(
            "max_rows", "Max Rows", placeholder_text="0 = unlimited", tab="advanced"
        )

    def get_node_class(self) -> type:
        return ReadCSVNode

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("headers")
        self.add_output("row_count")
        self.add_output("success")


class VisualWriteCsvNode(VisualNode):
    """Visual representation of WriteCSVNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write CSV"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "WriteCSVNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("write_header", True, widget_type=1, tab="config")
        self.add_text_input("delimiter", "Delimiter", text=",", tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def get_node_class(self) -> type:
        return WriteCSVNode

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("data")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("rows_written")
        self.add_output("success")


# =============================================================================
# JSON Operations
# =============================================================================


class VisualReadJsonNode(VisualNode):
    """Visual representation of ReadJSONFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read JSON"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "ReadJSONFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def get_node_class(self) -> type:
        return ReadJSONFileNode

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("success")


class VisualWriteJsonNode(VisualNode):
    """Visual representation of WriteJSONFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write JSON"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "WriteJSONFileNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("indent", 2, widget_type=2, tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def get_node_class(self) -> type:
        return WriteJSONFileNode

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("data")
        self.add_output("exec_out")
        self.add_output("success")


# =============================================================================
# ZIP Operations
# =============================================================================


class VisualZipFilesNode(VisualNode):
    """Visual representation of ZipFilesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Zip Files"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("zip_path", "ZIP Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("zip_path")
        self.add_input("files")
        self.add_output("exec_out")
        self.add_output("zip_path")
        self.add_output("file_count")
        self.add_output("success")


class VisualUnzipFileNode(VisualNode):
    """Visual representation of UnzipFilesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Unzip File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_CLASS = "UnzipFilesNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("zip_path", "ZIP Path", text="", tab="inputs")
        self.add_text_input("extract_to", "Extract To", text="", tab="inputs")

    def get_node_class(self) -> type:
        return UnzipFilesNode

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("zip_path")
        self.add_input("extract_to")
        self.add_output("exec_out")
        self.add_output("extract_to")
        self.add_output("files")
        self.add_output("file_count")
        self.add_output("success")


# =============================================================================
# XML Operations
# =============================================================================


class VisualParseXMLNode(VisualNode):
    """Visual representation of ParseXMLNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Parse XML"
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted", DataType.BOOLEAN)


class VisualFTPMakeDirNode(VisualNode):
    """Visual representation of FTPMakeDirNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Make Dir"
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("removed", DataType.BOOLEAN)


class VisualFTPRenameNode(VisualNode):
    """Visual representation of FTPRenameNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Rename"
    NODE_CATEGORY = "file_operations"

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
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("disconnected", DataType.BOOLEAN)


class VisualFTPGetSizeNode(VisualNode):
    """Visual representation of FTPGetSizeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Get Size"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("found", DataType.BOOLEAN)

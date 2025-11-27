"""Visual nodes for file_operations category."""
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

class VisualReadFileNode(VisualNode):
    """Visual representation of ReadFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Read File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.create_property("binary_mode", False, widget_type=1, tab="config")
        # Advanced options
        self.add_combo_menu("errors", "Error Handling", items=["strict", "ignore", "replace", "backslashreplace"], tab="advanced")
        self.add_text_input("max_size", "Max Size (bytes)", placeholder_text="0 = unlimited", tab="advanced")
        self.add_combo_menu("newline", "Newline Mode", items=["", "\\n", "\\r\\n", "\\r"], tab="advanced")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("content")
        self.add_output("size")
        self.add_output("success")

class VisualWriteFileNode(VisualNode):
    """Visual representation of WriteFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Write File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Write File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("content", "Content", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.create_property("create_dirs", True, widget_type=1, tab="config")
        # Advanced options
        self.add_combo_menu("errors", "Error Handling", items=["strict", "ignore", "replace", "backslashreplace"], tab="advanced")
        self.add_combo_menu("newline", "Newline Mode", items=["", "\\n", "\\r\\n", "\\r"], tab="advanced")
        self.create_property("append_mode", False, widget_type=1, tab="advanced")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("content")
        self.add_output("exec_out")
        self.add_output("bytes_written")
        self.add_output("success")

class VisualAppendFileNode(VisualNode):
    """Visual representation of AppendFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Append File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Append File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("content", "Content", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("content")
        self.add_output("exec_out")
        self.add_output("bytes_written")
        self.add_output("success")

class VisualDeleteFileNode(VisualNode):
    """Visual representation of DeleteFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Delete File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Delete File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("ignore_errors", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("success")

class VisualCopyFileNode(VisualNode):
    """Visual representation of CopyFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Copy File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Copy File node."""
        super().__init__()
        self.add_text_input("source_path", "Source Path", text="", tab="inputs")
        self.add_text_input("dest_path", "Destination Path", text="", tab="inputs")
        self.create_property("overwrite", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("source_path")
        self.add_input("dest_path")
        self.add_output("exec_out")
        self.add_output("dest_path")
        self.add_output("success")

class VisualMoveFileNode(VisualNode):
    """Visual representation of MoveFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Move File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Move File node."""
        super().__init__()
        self.add_text_input("source_path", "Source Path", text="", tab="inputs")
        self.add_text_input("dest_path", "Destination Path", text="", tab="inputs")
        self.create_property("overwrite", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("source_path")
        self.add_input("dest_path")
        self.add_output("exec_out")
        self.add_output("dest_path")
        self.add_output("success")

class VisualCreateDirectoryNode(VisualNode):
    """Visual representation of CreateDirectoryNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Create Directory"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Create Directory node."""
        super().__init__()
        self.add_text_input("directory_path", "Directory Path", text="", tab="inputs")
        self.create_property("parents", True, widget_type=1, tab="config")
        self.create_property("exist_ok", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("directory_path")
        self.add_output("exec_out")
        self.add_output("directory_path")
        self.add_output("success")

class VisualListDirectoryNode(VisualNode):
    """Visual representation of ListDirectoryNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "List Directory"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize List Directory node."""
        super().__init__()
        self.add_text_input("directory_path", "Directory Path", text=".", tab="inputs")
        self.add_text_input("pattern", "Pattern", text="*", tab="config")
        self.create_property("recursive", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("directory_path")
        self.add_output("exec_out")
        self.add_output("files")
        self.add_output("count")
        self.add_output("success")

class VisualFileExistsNode(VisualNode):
    """Visual representation of FileExistsNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "File Exists"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize File Exists node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("exists")
        self.add_output("is_file")
        self.add_output("is_dir")

class VisualGetFileInfoNode(VisualNode):
    """Visual representation of GetFileInfoNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Get File Info"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Get File Info node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
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

class VisualReadCSVNode(VisualNode):
    """Visual representation of ReadCSVNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read CSV"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Read CSV node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("has_header", True, widget_type=1, tab="config")
        self.add_text_input("delimiter", "Delimiter", text=",", tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        # Advanced options
        self.add_text_input("quotechar", "Quote Char", text="\"", tab="advanced")
        self.add_text_input("skip_rows", "Skip Rows", placeholder_text="0", tab="advanced")
        self.add_text_input("max_rows", "Max Rows", placeholder_text="0 = unlimited", tab="advanced")
        self.create_property("strict", False, widget_type=1, tab="advanced")
        self.create_property("doublequote", True, widget_type=1, tab="advanced")
        self.add_text_input("escapechar", "Escape Char", placeholder_text="Optional", tab="advanced")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("headers")
        self.add_output("row_count")
        self.add_output("success")

class VisualWriteCSVNode(VisualNode):
    """Visual representation of WriteCSVNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Write CSV"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Write CSV node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("write_header", True, widget_type=1, tab="config")
        self.add_text_input("delimiter", "Delimiter", text=",", tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("data")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("rows_written")
        self.add_output("success")

class VisualReadJSONFileNode(VisualNode):
    """Visual representation of ReadJSONFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read JSON File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Read JSON File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("success")

class VisualWriteJSONFileNode(VisualNode):
    """Visual representation of WriteJSONFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Write JSON File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Write JSON File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("indent", 2, widget_type=2, tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("data")
        self.add_output("exec_out")
        self.add_output("success")

class VisualZipFilesNode(VisualNode):
    """Visual representation of ZipFilesNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Zip Files"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Zip Files node."""
        super().__init__()
        self.add_text_input("zip_path", "ZIP Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("zip_path")
        self.add_input("files")
        self.add_output("exec_out")
        self.add_output("zip_path")
        self.add_output("file_count")
        self.add_output("success")

class VisualUnzipFilesNode(VisualNode):
    """Visual representation of UnzipFilesNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Unzip Files"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Unzip Files node."""
        super().__init__()
        self.add_text_input("zip_path", "ZIP Path", text="", tab="inputs")
        self.add_text_input("extract_to", "Extract To", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("zip_path")
        self.add_input("extract_to")
        self.add_output("exec_out")
        self.add_output("extract_to")
        self.add_output("files")
        self.add_output("file_count")
        self.add_output("success")


# =============================================================================
# Email Nodes
# =============================================================================


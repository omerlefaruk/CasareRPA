"""Visual nodes for office_automation category."""
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

class VisualExcelOpenNode(VisualNode):
    """Visual representation of ExcelOpenNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Open"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Open node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("show_window", True, widget_type=1, tab="config")
        self.create_property("read_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("workbook")
        self.add_output("success")

class VisualExcelReadCellNode(VisualNode):
    """Visual representation of ExcelReadCellNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Read Cell"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Read Cell node."""
        super().__init__()
        self.add_text_input("cell_address", "Cell Address", text="A1", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_input("cell_address")
        self.add_input("sheet_name")
        self.add_output("exec_out")
        self.add_output("value")
        self.add_output("success")

class VisualExcelWriteCellNode(VisualNode):
    """Visual representation of ExcelWriteCellNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Write Cell"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Write Cell node."""
        super().__init__()
        self.add_text_input("cell_address", "Cell Address", text="A1", tab="inputs")
        self.add_text_input("value", "Value", text="", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_input("cell_address")
        self.add_input("value")
        self.add_input("sheet_name")
        self.add_output("exec_out")
        self.add_output("success")

class VisualExcelGetRangeNode(VisualNode):
    """Visual representation of ExcelGetRangeNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Get Range"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Get Range node."""
        super().__init__()
        self.add_text_input("range_address", "Range Address", text="A1:B10", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_input("range_address")
        self.add_input("sheet_name")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("success")

class VisualExcelCloseNode(VisualNode):
    """Visual representation of ExcelCloseNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Close"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Close node."""
        super().__init__()
        self.create_property("save_changes", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_output("exec_out")
        self.add_output("success")

class VisualWordOpenNode(VisualNode):
    """Visual representation of WordOpenNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Open"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Open node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("show_window", True, widget_type=1, tab="config")
        self.create_property("read_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("document")
        self.add_output("success")

class VisualWordGetTextNode(VisualNode):
    """Visual representation of WordGetTextNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Get Text"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("document")
        self.add_output("exec_out")
        self.add_output("text")
        self.add_output("success")

class VisualWordReplaceTextNode(VisualNode):
    """Visual representation of WordReplaceTextNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Replace Text"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Replace Text node."""
        super().__init__()
        self.add_text_input("find_text", "Find Text", text="", tab="inputs")
        self.add_text_input("replace_text", "Replace Text", text="", tab="inputs")
        self.create_property("match_case", False, widget_type=1, tab="config")
        self.create_property("whole_word", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("document")
        self.add_input("find_text")
        self.add_input("replace_text")
        self.add_output("exec_out")
        self.add_output("replacements")
        self.add_output("success")

class VisualWordCloseNode(VisualNode):
    """Visual representation of WordCloseNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Close"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Close node."""
        super().__init__()
        self.create_property("save_changes", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("document")
        self.add_output("exec_out")
        self.add_output("success")

class VisualOutlookSendEmailNode(VisualNode):
    """Visual representation of OutlookSendEmailNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Send Email"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Send Email node."""
        super().__init__()
        self.add_text_input("to", "To", text="", tab="inputs")
        self.add_text_input("subject", "Subject", text="", tab="inputs")
        self.add_text_input("body", "Body", text="", tab="inputs")
        self.add_text_input("cc", "CC", text="", tab="inputs")
        self.add_text_input("bcc", "BCC", text="", tab="inputs")
        self.create_property("is_html", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("to")
        self.add_input("subject")
        self.add_input("body")
        self.add_input("attachments")
        self.add_output("exec_out")
        self.add_output("success")

class VisualOutlookReadEmailsNode(VisualNode):
    """Visual representation of OutlookReadEmailsNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Read Emails"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Read Emails node."""
        super().__init__()
        self.add_text_input("folder", "Folder", text="Inbox", tab="inputs")
        self.create_property("count", 10, widget_type=2, tab="config")
        self.create_property("unread_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("folder")
        self.add_output("exec_out")
        self.add_output("emails")
        self.add_output("count")
        self.add_output("success")

class VisualOutlookGetInboxCountNode(VisualNode):
    """Visual representation of OutlookGetInboxCountNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Get Inbox Count"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Get Inbox Count node."""
        super().__init__()
        self.create_property("unread_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")
        self.add_output("total_count")
        self.add_output("unread_count")
        self.add_output("success")


# Database Nodes


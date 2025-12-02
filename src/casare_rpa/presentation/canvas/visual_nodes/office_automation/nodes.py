"""Visual nodes for office_automation category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualExcelOpenNode(VisualNode):
    """Visual representation of ExcelOpenNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Open"
    NODE_CATEGORY = "office_automation/excel"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Open node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("show_window", True, widget_type=1, tab="config")
        self.create_property("read_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("workbook", DataType.WORKBOOK)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualExcelReadCellNode(VisualNode):
    """Visual representation of ExcelReadCellNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Read Cell"
    NODE_CATEGORY = "office_automation/excel"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Read Cell node."""
        super().__init__()
        self.add_text_input("cell_address", "Cell Address", text="A1", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("workbook", DataType.WORKBOOK)
        self.add_typed_input("cell_address", DataType.STRING)
        self.add_typed_input("sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualExcelWriteCellNode(VisualNode):
    """Visual representation of ExcelWriteCellNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Write Cell"
    NODE_CATEGORY = "office_automation/excel"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Write Cell node."""
        super().__init__()
        self.add_text_input("cell_address", "Cell Address", text="A1", tab="inputs")
        self.add_text_input("value", "Value", text="", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("workbook", DataType.WORKBOOK)
        self.add_typed_input("cell_address", DataType.STRING)
        self.add_typed_input("value", DataType.STRING)
        self.add_typed_input("sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualExcelGetRangeNode(VisualNode):
    """Visual representation of ExcelGetRangeNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Get Range"
    NODE_CATEGORY = "office_automation/excel"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Get Range node."""
        super().__init__()
        self.add_text_input(
            "range_address", "Range Address", text="A1:B10", tab="inputs"
        )
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("workbook", DataType.WORKBOOK)
        self.add_typed_input("range_address", DataType.STRING)
        self.add_typed_input("sheet_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("data", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualExcelCloseNode(VisualNode):
    """Visual representation of ExcelCloseNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Close"
    NODE_CATEGORY = "office_automation/excel"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Close node."""
        super().__init__()
        self.create_property("save_changes", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("workbook", DataType.WORKBOOK)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWordOpenNode(VisualNode):
    """Visual representation of WordOpenNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Open"
    NODE_CATEGORY = "office_automation/word"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Open node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("show_window", True, widget_type=1, tab="config")
        self.create_property("read_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("document", DataType.DOCUMENT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWordGetTextNode(VisualNode):
    """Visual representation of WordGetTextNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Get Text"
    NODE_CATEGORY = "office_automation/word"
    CASARE_NODE_MODULE = "office"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("document", DataType.DOCUMENT)
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWordReplaceTextNode(VisualNode):
    """Visual representation of WordReplaceTextNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Replace Text"
    NODE_CATEGORY = "office_automation/word"
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
        self.add_exec_input("exec_in")
        self.add_typed_input("document", DataType.DOCUMENT)
        self.add_typed_input("find_text", DataType.STRING)
        self.add_typed_input("replace_text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("replacements", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWordCloseNode(VisualNode):
    """Visual representation of WordCloseNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Close"
    NODE_CATEGORY = "office_automation/word"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Close node."""
        super().__init__()
        self.create_property("save_changes", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("document", DataType.DOCUMENT)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualOutlookSendEmailNode(VisualNode):
    """Visual representation of OutlookSendEmailNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Send Email"
    NODE_CATEGORY = "office_automation/outlook"
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
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("attachments", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualOutlookReadEmailsNode(VisualNode):
    """Visual representation of OutlookReadEmailsNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Read Emails"
    NODE_CATEGORY = "office_automation/outlook"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Read Emails node."""
        super().__init__()
        self.add_text_input("folder", "Folder", text="Inbox", tab="inputs")
        self.create_property("count", 10, widget_type=2, tab="config")
        self.create_property("unread_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("folder", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("emails", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualOutlookGetInboxCountNode(VisualNode):
    """Visual representation of OutlookGetInboxCountNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Get Inbox Count"
    NODE_CATEGORY = "office_automation/outlook"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Get Inbox Count node."""
        super().__init__()
        self.create_property("unread_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("total_count", DataType.INTEGER)
        self.add_typed_output("unread_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# Database Nodes

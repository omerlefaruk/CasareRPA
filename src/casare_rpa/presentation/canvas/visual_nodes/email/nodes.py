"""Visual nodes for email category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.nodes.email import (
    SendEmailNode,
    ReadEmailsNode,
    GetEmailContentNode,
    SaveAttachmentNode,
    FilterEmailsNode,
    MarkEmailNode,
    DeleteEmailNode,
    MoveEmailNode,
)


class VisualSendEmailNode(VisualNode):
    """Visual representation of SendEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Send Email"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "SendEmailNode"

    def __init__(self) -> None:
        """Initialize Send Email node."""
        super().__init__()
        # Widgets auto-generated from @node_schema on SendEmailNode
        # Add attachments widget manually (not in schema, supports {{variable}} syntax)
        self.add_text_input(
            "attachments",
            "Attachments",
            tab="properties",
            placeholder_text="{{zip_path}} or C:\\path\\to\\file.pdf",
        )

    def get_node_class(self) -> type:
        return SendEmailNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("to_email", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("attachments", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("message_id", DataType.STRING)


class VisualReadEmailsNode(VisualNode):
    """Visual representation of ReadEmailsNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Read Emails"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "ReadEmailsNode"

    def get_node_class(self) -> type:
        return ReadEmailsNode

    def __init__(self) -> None:
        """Initialize Read Emails node."""
        super().__init__()
        self.add_text_input(
            "imap_server", "IMAP Server", text="imap.gmail.com", tab="connection"
        )
        self.add_text_input("imap_port", "IMAP Port", text="993", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self.add_text_input("limit", "Limit", text="10", tab="config")
        self.add_combo_menu(
            "search_criteria",
            "Search",
            items=["ALL", "UNSEEN", "SEEN", "RECENT", "FLAGGED"],
            tab="config",
        )
        # Advanced options
        self.add_text_input(
            "timeout", "Timeout (s)", placeholder_text="30", tab="advanced"
        )
        self._safe_create_property("mark_as_read", False, widget_type=1, tab="advanced")
        self._safe_create_property("include_body", True, widget_type=1, tab="advanced")
        self._safe_create_property("newest_first", True, widget_type=1, tab="advanced")
        # Retry options
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
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("folder", DataType.STRING)
        self.add_typed_input("limit", DataType.INTEGER)
        self.add_typed_input("search_criteria", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("emails", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualGetEmailContentNode(VisualNode):
    """Visual representation of GetEmailContentNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Get Email Content"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "GetEmailContentNode"

    def get_node_class(self) -> type:
        return GetEmailContentNode

    def __init__(self) -> None:
        """Initialize Get Email Content node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("email", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("subject", DataType.STRING)
        self.add_typed_output("from", DataType.STRING)
        self.add_typed_output("to", DataType.STRING)
        self.add_typed_output("date", DataType.STRING)
        self.add_typed_output("body_text", DataType.STRING)
        self.add_typed_output("body_html", DataType.STRING)
        self.add_typed_output("attachments", DataType.LIST)


class VisualSaveAttachmentNode(VisualNode):
    """Visual representation of SaveAttachmentNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Save Attachment"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "SaveAttachmentNode"

    def get_node_class(self) -> type:
        return SaveAttachmentNode

    def __init__(self) -> None:
        """Initialize Save Attachment node."""
        super().__init__()
        self.add_text_input(
            "imap_server", "IMAP Server", text="imap.gmail.com", tab="connection"
        )
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("save_path", "Save Path", text=".", tab="config")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("email_uid", DataType.STRING)
        self.add_typed_input("save_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("saved_files", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualFilterEmailsNode(VisualNode):
    """Visual representation of FilterEmailsNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Filter Emails"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "FilterEmailsNode"

    def get_node_class(self) -> type:
        return FilterEmailsNode

    def __init__(self) -> None:
        """Initialize Filter Emails node."""
        super().__init__()
        self.add_text_input(
            "subject_contains", "Subject Contains", text="", tab="filters"
        )
        self.add_text_input("from_contains", "From Contains", text="", tab="filters")
        self._safe_create_property(
            "has_attachments", False, widget_type=1, tab="filters"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("emails", DataType.LIST)
        self.add_typed_input("subject_contains", DataType.STRING)
        self.add_typed_input("from_contains", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("filtered", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualMarkEmailNode(VisualNode):
    """Visual representation of MarkEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Mark Email"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "MarkEmailNode"

    def get_node_class(self) -> type:
        return MarkEmailNode

    def __init__(self) -> None:
        """Initialize Mark Email node."""
        super().__init__()
        self.add_text_input(
            "imap_server", "IMAP Server", text="imap.gmail.com", tab="connection"
        )
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self.add_combo_menu(
            "mark_as",
            "Mark As",
            items=["read", "unread", "flagged", "unflagged"],
            tab="config",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("email_uid", DataType.STRING)
        self.add_typed_input("mark_as", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualDeleteEmailNode(VisualNode):
    """Visual representation of DeleteEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Delete Email"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "DeleteEmailNode"

    def get_node_class(self) -> type:
        return DeleteEmailNode

    def __init__(self) -> None:
        """Initialize Delete Email node."""
        super().__init__()
        self.add_text_input(
            "imap_server", "IMAP Server", text="imap.gmail.com", tab="connection"
        )
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self._safe_create_property("permanent", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("email_uid", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMoveEmailNode(VisualNode):
    """Visual representation of MoveEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Move Email"
    NODE_CATEGORY = "email"
    CASARE_NODE_CLASS = "MoveEmailNode"

    def get_node_class(self) -> type:
        return MoveEmailNode

    def __init__(self) -> None:
        """Initialize Move Email node."""
        super().__init__()
        self.add_text_input(
            "imap_server", "IMAP Server", text="imap.gmail.com", tab="connection"
        )
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input(
            "source_folder", "Source Folder", text="INBOX", tab="config"
        )
        self.add_text_input("target_folder", "Target Folder", text="", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("email_uid", DataType.STRING)
        self.add_typed_input("target_folder", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# Utility Nodes
# =============================================================================

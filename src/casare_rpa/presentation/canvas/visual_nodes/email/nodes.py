"""Visual nodes for email category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


class VisualSendEmailNode(VisualNode):
    """Visual representation of SendEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Send Email"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Send Email node."""
        super().__init__()
        self.add_text_input(
            "smtp_server", "SMTP Server", text="smtp.gmail.com", tab="connection"
        )
        self.add_text_input("smtp_port", "SMTP Port", text="587", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("from_email", "From Email", text="", tab="email")
        self.add_text_input("to_email", "To Email", text="", tab="email")
        self.add_text_input("subject", "Subject", text="", tab="email")
        self.add_text_input("cc", "CC", text="", tab="email")
        self.add_text_input("bcc", "BCC", text="", tab="email")
        self.create_property("use_tls", True, widget_type=1, tab="config")
        self.create_property("is_html", False, widget_type=1, tab="config")
        # Advanced options
        self.add_text_input(
            "timeout", "Timeout (s)", placeholder_text="30", tab="advanced"
        )
        self.add_text_input(
            "reply_to", "Reply-To", placeholder_text="Optional", tab="advanced"
        )
        self.add_combo_menu(
            "priority", "Priority", items=["normal", "high", "low"], tab="advanced"
        )
        self.create_property("read_receipt", False, widget_type=1, tab="advanced")
        self.add_text_input(
            "sender_name", "Sender Name", placeholder_text="Optional", tab="advanced"
        )
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
        self.add_input("exec_in")
        self.add_input("to_email")
        self.add_input("subject")
        self.add_input("body")
        self.add_input("attachments")
        self.add_output("exec_out")
        self.add_output("success")
        self.add_output("message_id")


class VisualReadEmailsNode(VisualNode):
    """Visual representation of ReadEmailsNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Read Emails"
    NODE_CATEGORY = "email"

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
        self.create_property("mark_as_read", False, widget_type=1, tab="advanced")
        self.create_property("include_body", True, widget_type=1, tab="advanced")
        self.create_property("newest_first", True, widget_type=1, tab="advanced")
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
        self.add_input("exec_in")
        self.add_input("folder")
        self.add_input("limit")
        self.add_input("search_criteria")
        self.add_output("exec_out")
        self.add_output("emails")
        self.add_output("count")


class VisualGetEmailContentNode(VisualNode):
    """Visual representation of GetEmailContentNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Get Email Content"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Get Email Content node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email")
        self.add_output("exec_out")
        self.add_output("subject")
        self.add_output("from")
        self.add_output("to")
        self.add_output("date")
        self.add_output("body_text")
        self.add_output("body_html")
        self.add_output("attachments")


class VisualSaveAttachmentNode(VisualNode):
    """Visual representation of SaveAttachmentNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Save Attachment"
    NODE_CATEGORY = "email"

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
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_input("save_path")
        self.add_output("exec_out")
        self.add_output("saved_files")
        self.add_output("count")


class VisualFilterEmailsNode(VisualNode):
    """Visual representation of FilterEmailsNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Filter Emails"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Filter Emails node."""
        super().__init__()
        self.add_text_input(
            "subject_contains", "Subject Contains", text="", tab="filters"
        )
        self.add_text_input("from_contains", "From Contains", text="", tab="filters")
        self.create_property("has_attachments", False, widget_type=1, tab="filters")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("emails")
        self.add_input("subject_contains")
        self.add_input("from_contains")
        self.add_output("exec_out")
        self.add_output("filtered")
        self.add_output("count")


class VisualMarkEmailNode(VisualNode):
    """Visual representation of MarkEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Mark Email"
    NODE_CATEGORY = "email"

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
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_input("mark_as")
        self.add_output("exec_out")
        self.add_output("success")


class VisualDeleteEmailNode(VisualNode):
    """Visual representation of DeleteEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Delete Email"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Delete Email node."""
        super().__init__()
        self.add_text_input(
            "imap_server", "IMAP Server", text="imap.gmail.com", tab="connection"
        )
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self.create_property("permanent", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_output("exec_out")
        self.add_output("success")


class VisualMoveEmailNode(VisualNode):
    """Visual representation of MoveEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Move Email"
    NODE_CATEGORY = "email"

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
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_input("target_folder")
        self.add_output("exec_out")
        self.add_output("success")


# =============================================================================
# Utility Nodes
# =============================================================================

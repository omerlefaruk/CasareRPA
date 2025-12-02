"""Visual nodes for Gmail operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Send Operations
# =============================================================================


class VisualGmailSendEmailNode(VisualNode):
    """Visual representation of GmailSendEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendEmailNode"

    def __init__(self) -> None:
        super().__init__()
        # Connection tab
        self.add_text_input(
            "credential_name",
            "Credential",
            text="google",
            tab="connection",
            placeholder_text="OAuth credential name",
        )
        # Properties tab
        self.add_text_input(
            "to",
            "To",
            text="",
            tab="properties",
            placeholder_text="recipient@example.com",
        )
        self.add_text_input(
            "cc", "CC", text="", tab="properties", placeholder_text="cc@example.com"
        )
        self.add_text_input(
            "bcc", "BCC", text="", tab="properties", placeholder_text="bcc@example.com"
        )
        self.add_text_input(
            "subject",
            "Subject",
            text="",
            tab="properties",
            placeholder_text="Email subject",
        )
        self.add_text_input(
            "body",
            "Body",
            text="",
            tab="properties",
            placeholder_text="Email body content",
        )
        self.add_combo_menu(
            "body_type", "Body Type", items=["text", "html"], tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailSendWithAttachmentNode(VisualNode):
    """Visual representation of GmailSendWithAttachmentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send With Attachment"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendWithAttachmentNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "to",
            "To",
            text="",
            tab="properties",
            placeholder_text="recipient@example.com",
        )
        self.add_text_input("subject", "Subject", text="", tab="properties")
        self.add_text_input("body", "Body", text="", tab="properties")
        self.add_combo_menu(
            "body_type", "Body Type", items=["text", "html"], tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("attachments", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailReplyToEmailNode(VisualNode):
    """Visual representation of GmailReplyToEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Reply To Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailReplyToEmailNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "message_id", "Original Message ID", text="", tab="properties"
        )
        self.add_text_input("body", "Reply Body", text="", tab="properties")
        self.add_combo_menu(
            "body_type", "Body Type", items=["text", "html"], tab="properties"
        )
        self.add_checkbox("reply_all", "Reply All", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailForwardEmailNode(VisualNode):
    """Visual representation of GmailForwardEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Forward Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailForwardEmailNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")
        self.add_text_input(
            "to",
            "Forward To",
            text="",
            tab="properties",
            placeholder_text="forward@example.com",
        )
        self.add_text_input(
            "additional_text", "Additional Text", text="", tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("to", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_message_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailCreateDraftNode(VisualNode):
    """Visual representation of GmailCreateDraftNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Create Draft"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailCreateDraftNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("to", "To", text="", tab="properties")
        self.add_text_input("subject", "Subject", text="", tab="properties")
        self.add_text_input("body", "Body", text="", tab="properties")
        self.add_combo_menu(
            "body_type", "Body Type", items=["text", "html"], tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("draft_id", DataType.STRING)
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailSendDraftNode(VisualNode):
    """Visual representation of GmailSendDraftNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send Draft"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendDraftNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("draft_id", "Draft ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("draft_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Read Operations
# =============================================================================


class VisualGmailGetEmailNode(VisualNode):
    """Visual representation of GmailGetEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetEmailNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")
        self.add_combo_menu(
            "format", "Format", items=["full", "metadata", "minimal"], tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("subject", DataType.STRING)
        self.add_typed_output("from", DataType.STRING)
        self.add_typed_output("to", DataType.STRING)
        self.add_typed_output("date", DataType.STRING)
        self.add_typed_output("body", DataType.STRING)
        self.add_typed_output("snippet", DataType.STRING)
        self.add_typed_output("labels", DataType.ARRAY)
        self.add_typed_output("attachments", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailListEmailsNode(VisualNode):
    """Visual representation of GmailListEmailsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: List Emails"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailListEmailsNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("max_results", "Max Results", text="10", tab="properties")
        self.add_text_input(
            "label_ids",
            "Label IDs",
            text="INBOX",
            tab="properties",
            placeholder_text="INBOX, UNREAD",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_typed_input("label_ids", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("messages", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailSearchEmailsNode(VisualNode):
    """Visual representation of GmailSearchEmailsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Search Emails"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSearchEmailsNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input(
            "query",
            "Query",
            text="",
            tab="properties",
            placeholder_text="from:example@gmail.com subject:test",
        )
        self.add_text_input("max_results", "Max Results", text="10", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("query", DataType.STRING)
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("messages", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailGetThreadNode(VisualNode):
    """Visual representation of GmailGetThreadNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Thread"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetThreadNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("thread_id", "Thread ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("thread_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("messages", DataType.ARRAY)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("snippet", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailGetAttachmentNode(VisualNode):
    """Visual representation of GmailGetAttachmentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Attachment"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetAttachmentNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")
        self.add_text_input("attachment_id", "Attachment ID", text="", tab="properties")
        self.add_text_input(
            "save_path",
            "Save Path",
            text="",
            tab="properties",
            placeholder_text="C:/Downloads/attachment.pdf",
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("attachment_id", DataType.STRING)
        self.add_typed_input("save_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("file_size", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Management Operations
# =============================================================================


class VisualGmailModifyLabelsNode(VisualNode):
    """Visual representation of GmailModifyLabelsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Modify Labels"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailModifyLabelsNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("add_labels", DataType.ARRAY)
        self.add_typed_input("remove_labels", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("labels", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailMoveToTrashNode(VisualNode):
    """Visual representation of GmailMoveToTrashNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Move to Trash"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailMoveToTrashNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailMarkAsReadNode(VisualNode):
    """Visual representation of GmailMarkAsReadNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Mark as Read"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailMarkAsReadNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailMarkAsUnreadNode(VisualNode):
    """Visual representation of GmailMarkAsUnreadNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Mark as Unread"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailMarkAsUnreadNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailStarEmailNode(VisualNode):
    """Visual representation of GmailStarEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Star Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailStarEmailNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")
        self.add_checkbox(
            "star", "Star (uncheck to unstar)", state=True, tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("star", DataType.BOOLEAN)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailArchiveEmailNode(VisualNode):
    """Visual representation of GmailArchiveEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Archive Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailArchiveEmailNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailDeleteEmailNode(VisualNode):
    """Visual representation of GmailDeleteEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Delete Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailDeleteEmailNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )
        self.add_text_input("message_id", "Message ID", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Batch Operations
# =============================================================================


class VisualGmailBatchSendNode(VisualNode):
    """Visual representation of GmailBatchSendNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Send"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchSendNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("emails", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("results", DataType.ARRAY)
        self.add_typed_output("sent_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailBatchModifyNode(VisualNode):
    """Visual representation of GmailBatchModifyNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Modify"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchModifyNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_ids", DataType.ARRAY)
        self.add_typed_input("add_labels", DataType.ARRAY)
        self.add_typed_input("remove_labels", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("modified_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailBatchDeleteNode(VisualNode):
    """Visual representation of GmailBatchDeleteNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Delete"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchDeleteNode"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "credential_name", "Credential", text="google", tab="connection"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_ids", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

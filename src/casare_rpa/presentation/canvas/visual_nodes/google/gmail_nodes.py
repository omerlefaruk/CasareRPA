"""Visual nodes for Gmail operations.

All nodes use Google credential picker for OAuth authentication.
"""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeGoogleCredentialWidget,
)

# Gmail API scope
GMAIL_SCOPE = ["https://www.googleapis.com/auth/gmail.modify"]


class VisualGmailBaseNode(VisualNode):
    """Base class for Gmail visual nodes with credential picker integration."""

    REQUIRED_SCOPES = GMAIL_SCOPE
    SKIP_SCHEMA_WIDGETS = True  # Use manual widgets, not schema-generated ones

    def __init__(self, qgraphics_item=None) -> None:
        super().__init__(qgraphics_item)

    def _remove_property_if_exists(self, prop_name: str) -> None:
        """Remove existing property if it was auto-generated from schema."""
        if hasattr(self, "model") and prop_name in self.model.custom_properties:
            del self.model.custom_properties[prop_name]
            # Also remove from widgets dict if present
            if hasattr(self, "_widgets") and prop_name in self._widgets:
                del self._widgets[prop_name]

    def _safe_add_text_input(self, name: str, label: str = "", **kwargs) -> None:
        """Safely add a text input widget, removing any existing property first."""
        self._remove_property_if_exists(name)
        self.add_text_input(name, label, **kwargs)

    def _safe_add_combo_menu(
        self, name: str, label: str = "", items: list = None, **kwargs
    ) -> None:
        """Safely add a combo menu widget, removing any existing property first."""
        self._remove_property_if_exists(name)
        self.add_combo_menu(name, label, items=items or [], **kwargs)

    def setup_widgets(self) -> None:
        """Setup credential picker widget."""
        self._cred_widget = NodeGoogleCredentialWidget(
            name="credential_id",
            label="Google Account",
            scopes=self.REQUIRED_SCOPES,
        )
        if self._cred_widget:
            self.add_custom_widget(self._cred_widget)
            self._cred_widget.setParentItem(self.view)


# =============================================================================
# Send Operations
# =============================================================================


class VisualGmailSendEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailSendEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("cc", DataType.STRING)
        self.add_typed_input("bcc", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("body_type", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._safe_add_text_input("to", "To", placeholder_text="recipient@example.com")
        self._safe_add_text_input("cc", "CC", placeholder_text="cc@example.com")
        self._safe_add_text_input("bcc", "BCC", placeholder_text="bcc@example.com")
        self._safe_add_text_input("subject", "Subject", placeholder_text="Email subject")
        self._safe_add_text_input("body", "Body", placeholder_text="Email body...")
        self._safe_add_combo_menu("body_type", "Body Type", items=["plain", "html"])


class VisualGmailSendWithAttachmentNode(VisualGmailBaseNode):
    """Visual representation of GmailSendWithAttachmentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send With Attachment"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendWithAttachmentNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("cc", DataType.STRING)
        self.add_typed_input("bcc", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("body_type", DataType.STRING)
        self.add_typed_input("attachments", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._safe_add_text_input("to", "To", placeholder_text="recipient@example.com")
        self._safe_add_text_input("cc", "CC", placeholder_text="cc@example.com")
        self._safe_add_text_input("bcc", "BCC", placeholder_text="bcc@example.com")
        self._safe_add_text_input("subject", "Subject", placeholder_text="Email subject")
        self._safe_add_text_input("body", "Body", placeholder_text="Email body...")
        self._safe_add_combo_menu("body_type", "Body Type", items=["plain", "html"])
        self._safe_add_text_input(
            "attachments",
            "Attachments",
            placeholder_text="C:\\file1.pdf, C:\\file2.pdf",
        )


class VisualGmailReplyToEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailReplyToEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Reply To Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailReplyToEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("thread_id", DataType.STRING)
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("body_type", DataType.STRING)
        self.add_typed_input("cc", DataType.STRING)
        self.add_typed_input("bcc", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._safe_add_text_input("thread_id", "Thread ID", placeholder_text="18a5b7c8d9e0f1g2")
        self._safe_add_text_input("message_id", "Message ID", placeholder_text="18a5b7c8d9e0f1g2")
        self._safe_add_text_input("body", "Reply Body", placeholder_text="Your reply...")
        self._safe_add_combo_menu("body_type", "Body Type", items=["plain", "html"])
        self._safe_add_text_input("cc", "CC", placeholder_text="cc@example.com")
        self._safe_add_text_input("bcc", "BCC", placeholder_text="bcc@example.com")


class VisualGmailForwardEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailForwardEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Forward Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailForwardEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("cc", DataType.STRING)
        self.add_typed_input("bcc", DataType.STRING)
        self.add_typed_input("additional_body", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_message_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._safe_add_text_input("message_id", "Message ID", placeholder_text="18a5b7c8d9e0f1g2")
        self._safe_add_text_input("to", "To", placeholder_text="forward@example.com")
        self._safe_add_text_input("cc", "CC", placeholder_text="cc@example.com")
        self._safe_add_text_input("bcc", "BCC", placeholder_text="bcc@example.com")
        self._safe_add_text_input(
            "additional_body",
            "Additional Text",
            placeholder_text="Adding my comments...",
        )


class VisualGmailCreateDraftNode(VisualGmailBaseNode):
    """Visual representation of GmailCreateDraftNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Create Draft"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailCreateDraftNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("cc", DataType.STRING)
        self.add_typed_input("bcc", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("body_type", DataType.STRING)
        self.add_typed_input("attachments", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("draft_id", DataType.STRING)
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._safe_add_text_input("to", "To", placeholder_text="recipient@example.com")
        self._safe_add_text_input("cc", "CC", placeholder_text="cc@example.com")
        self._safe_add_text_input("bcc", "BCC", placeholder_text="bcc@example.com")
        self._safe_add_text_input("subject", "Subject", placeholder_text="Email subject")
        self._safe_add_text_input("body", "Body", placeholder_text="Email body...")
        self._safe_add_combo_menu("body_type", "Body Type", items=["plain", "html"])
        self._safe_add_text_input(
            "attachments",
            "Attachments",
            placeholder_text="C:\\file1.pdf, C:\\file2.pdf",
        )


class VisualGmailSendDraftNode(VisualGmailBaseNode):
    """Visual representation of GmailSendDraftNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send Draft"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendDraftNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("draft_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

    def setup_widgets(self) -> None:
        super().setup_widgets()
        self._safe_add_text_input("draft_id", "Draft ID", placeholder_text="r1234567890abcdef")


# =============================================================================
# Read Operations
# =============================================================================


class VisualGmailGetEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailGetEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetEmailNode"

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
        self.add_typed_output("labels", DataType.LIST)
        self.add_typed_output("attachments", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailListEmailsNode(VisualGmailBaseNode):
    """Visual representation of GmailListEmailsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: List Emails"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailListEmailsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_typed_input("label_ids", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("messages", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailSearchEmailsNode(VisualGmailBaseNode):
    """Visual representation of GmailSearchEmailsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Search Emails"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSearchEmailsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("query", DataType.STRING)
        self.add_typed_input("max_results", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("messages", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("next_page_token", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailGetThreadNode(VisualGmailBaseNode):
    """Visual representation of GmailGetThreadNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Thread"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetThreadNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("thread_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("messages", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("snippet", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailGetAttachmentNode(VisualGmailBaseNode):
    """Visual representation of GmailGetAttachmentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Attachment"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetAttachmentNode"

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


class VisualGmailModifyLabelsNode(VisualGmailBaseNode):
    """Visual representation of GmailModifyLabelsNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Modify Labels"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailModifyLabelsNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("add_labels", DataType.LIST)
        self.add_typed_input("remove_labels", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("labels", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailMoveToTrashNode(VisualGmailBaseNode):
    """Visual representation of GmailMoveToTrashNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Move to Trash"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailMoveToTrashNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailMarkAsReadNode(VisualGmailBaseNode):
    """Visual representation of GmailMarkAsReadNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Mark as Read"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailMarkAsReadNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailMarkAsUnreadNode(VisualGmailBaseNode):
    """Visual representation of GmailMarkAsUnreadNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Mark as Unread"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailMarkAsUnreadNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailStarEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailStarEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Star Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailStarEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("star", DataType.BOOLEAN)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailArchiveEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailArchiveEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Archive Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailArchiveEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailDeleteEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailDeleteEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Delete Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailDeleteEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


# =============================================================================
# Batch Operations
# =============================================================================


class VisualGmailBatchSendNode(VisualGmailBaseNode):
    """Visual representation of GmailBatchSendNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Send"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchSendNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("emails", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("sent_count", DataType.INTEGER)
        self.add_typed_output("failed_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailBatchModifyNode(VisualGmailBaseNode):
    """Visual representation of GmailBatchModifyNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Modify"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchModifyNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_ids", DataType.LIST)
        self.add_typed_input("add_labels", DataType.LIST)
        self.add_typed_input("remove_labels", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("modified_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailBatchDeleteNode(VisualGmailBaseNode):
    """Visual representation of GmailBatchDeleteNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Delete"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchDeleteNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_ids", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

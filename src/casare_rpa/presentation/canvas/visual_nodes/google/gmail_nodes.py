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

    def __init__(self, qgraphics_item=None) -> None:
        super().__init__(qgraphics_item)

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
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailSendWithAttachmentNode(VisualGmailBaseNode):
    """Visual representation of GmailSendWithAttachmentNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send With Attachment"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendWithAttachmentNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("to", DataType.STRING)
        self.add_typed_input("subject", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_typed_input("attachments", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailReplyToEmailNode(VisualGmailBaseNode):
    """Visual representation of GmailReplyToEmailNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Reply To Email"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailReplyToEmailNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_id", DataType.STRING)
        self.add_typed_input("body", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("new_message_id", DataType.STRING)
        self.add_typed_output("thread_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


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
        self.add_exec_output("exec_out")
        self.add_typed_output("new_message_id", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailCreateDraftNode(VisualGmailBaseNode):
    """Visual representation of GmailCreateDraftNode."""

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Create Draft"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailCreateDraftNode"

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

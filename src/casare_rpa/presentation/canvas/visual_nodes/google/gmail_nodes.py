"""Visual nodes for Gmail operations."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode


# =============================================================================
# Send Operations
# =============================================================================


class VisualGmailSendEmailNode(VisualNode):
    """Visual representation of GmailSendEmailNode.

    Widgets are auto-generated from GmailSendEmailNode's @node_schema decorator.
    """

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


class VisualGmailSendWithAttachmentNode(VisualNode):
    """Visual representation of GmailSendWithAttachmentNode.

    Widgets are auto-generated from GmailSendWithAttachmentNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Send With Attachment"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSendWithAttachmentNode"

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
    """Visual representation of GmailReplyToEmailNode.

    Widgets are auto-generated from GmailReplyToEmailNode's @node_schema decorator.
    """

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


class VisualGmailForwardEmailNode(VisualNode):
    """Visual representation of GmailForwardEmailNode.

    Widgets are auto-generated from GmailForwardEmailNode's @node_schema decorator.
    """

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


class VisualGmailCreateDraftNode(VisualNode):
    """Visual representation of GmailCreateDraftNode.

    Widgets are auto-generated from GmailCreateDraftNode's @node_schema decorator.
    """

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


class VisualGmailSendDraftNode(VisualNode):
    """Visual representation of GmailSendDraftNode.

    Widgets are auto-generated from GmailSendDraftNode's @node_schema decorator.
    """

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


class VisualGmailGetEmailNode(VisualNode):
    """Visual representation of GmailGetEmailNode.

    Widgets are auto-generated from GmailGetEmailNode's @node_schema decorator.
    """

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
        self.add_typed_output("labels", DataType.ARRAY)
        self.add_typed_output("attachments", DataType.ARRAY)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)


class VisualGmailListEmailsNode(VisualNode):
    """Visual representation of GmailListEmailsNode.

    Widgets are auto-generated from GmailListEmailsNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: List Emails"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailListEmailsNode"

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
    """Visual representation of GmailSearchEmailsNode.

    Widgets are auto-generated from GmailSearchEmailsNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Search Emails"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailSearchEmailsNode"

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
    """Visual representation of GmailGetThreadNode.

    Widgets are auto-generated from GmailGetThreadNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Get Thread"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailGetThreadNode"

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
    """Visual representation of GmailGetAttachmentNode.

    Widgets are auto-generated from GmailGetAttachmentNode's @node_schema decorator.
    """

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


class VisualGmailModifyLabelsNode(VisualNode):
    """Visual representation of GmailModifyLabelsNode.

    Widgets are auto-generated from GmailModifyLabelsNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Modify Labels"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailModifyLabelsNode"

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
    """Visual representation of GmailMoveToTrashNode.

    Widgets are auto-generated from GmailMoveToTrashNode's @node_schema decorator.
    """

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


class VisualGmailMarkAsReadNode(VisualNode):
    """Visual representation of GmailMarkAsReadNode.

    Widgets are auto-generated from GmailMarkAsReadNode's @node_schema decorator.
    """

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


class VisualGmailMarkAsUnreadNode(VisualNode):
    """Visual representation of GmailMarkAsUnreadNode.

    Widgets are auto-generated from GmailMarkAsUnreadNode's @node_schema decorator.
    """

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


class VisualGmailStarEmailNode(VisualNode):
    """Visual representation of GmailStarEmailNode.

    Widgets are auto-generated from GmailStarEmailNode's @node_schema decorator.
    """

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


class VisualGmailArchiveEmailNode(VisualNode):
    """Visual representation of GmailArchiveEmailNode.

    Widgets are auto-generated from GmailArchiveEmailNode's @node_schema decorator.
    """

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


class VisualGmailDeleteEmailNode(VisualNode):
    """Visual representation of GmailDeleteEmailNode.

    Widgets are auto-generated from GmailDeleteEmailNode's @node_schema decorator.
    """

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


class VisualGmailBatchSendNode(VisualNode):
    """Visual representation of GmailBatchSendNode.

    Widgets are auto-generated from GmailBatchSendNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Send"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchSendNode"

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
    """Visual representation of GmailBatchModifyNode.

    Widgets are auto-generated from GmailBatchModifyNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Modify"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchModifyNode"

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
    """Visual representation of GmailBatchDeleteNode.

    Widgets are auto-generated from GmailBatchDeleteNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.google"
    NODE_NAME = "Gmail: Batch Delete"
    NODE_CATEGORY = "google/gmail"
    CASARE_NODE_CLASS = "GmailBatchDeleteNode"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message_ids", DataType.ARRAY)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)

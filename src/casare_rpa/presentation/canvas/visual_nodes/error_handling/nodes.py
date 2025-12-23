"""Visual nodes for error_handling category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

# NOTE: VisualTryNode has been moved to control_flow/nodes.py
# as part of the Try/Catch/Finally composite pattern.
# Use VisualTryCatchFinallyNode from control_flow instead.


class VisualRetryNode(VisualNode):
    """Visual representation of RetryNode.

    Widgets are auto-generated from RetryNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Retry"
    NODE_CATEGORY = "error_handling/retry"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("retry_body")
        self.add_exec_output("success")
        self.add_exec_output("failed")
        self.add_typed_output("attempt", DataType.INTEGER)
        self.add_typed_output("last_error", DataType.ANY)


class VisualRetrySuccessNode(VisualNode):
    """Visual representation of RetrySuccessNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Retry Success"
    NODE_CATEGORY = "error_handling/retry"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")


class VisualRetryFailNode(VisualNode):
    """Visual representation of RetryFailNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Retry Fail"
    NODE_CATEGORY = "error_handling/retry"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("error_message", DataType.STRING)
        self.add_exec_output("exec_out")


class VisualThrowErrorNode(VisualNode):
    """Visual representation of ThrowErrorNode.

    Widgets are auto-generated from ThrowErrorNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Throw Error"
    NODE_CATEGORY = "error_handling/try_catch"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("error_message", DataType.STRING)
        self.add_exec_output("exec_out")


class VisualWebhookNotifyNode(VisualNode):
    """Visual representation of WebhookNotifyNode.

    Widgets are auto-generated from WebhookNotifyNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Webhook Notify"
    NODE_CATEGORY = "error_handling/logging"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("webhook_url", DataType.STRING)
        self.add_typed_input("message", DataType.STRING)
        self.add_typed_input("error_details", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("response", DataType.ANY)


class VisualOnErrorNode(VisualNode):
    """Visual representation of OnErrorNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "On Error"
    NODE_CATEGORY = "error_handling/try_catch"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_exec_output("protected_body")
        self.add_exec_output("on_error")
        self.add_exec_output("finally")
        self.add_typed_output("error_message", DataType.STRING)
        self.add_typed_output("error_type", DataType.STRING)
        self.add_typed_output("error_node", DataType.STRING)
        self.add_typed_output("stack_trace", DataType.STRING)


class VisualErrorRecoveryNode(VisualNode):
    """Visual representation of ErrorRecoveryNode.

    Widgets are auto-generated from ErrorRecoveryNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Error Recovery"
    NODE_CATEGORY = "error_handling/retry"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("strategy", DataType.STRING)
        self.add_typed_input("max_retries", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_exec_output("fallback")


class VisualLogErrorNode(VisualNode):
    """Visual representation of LogErrorNode.

    Widgets auto-generated from LogErrorNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Log Error"
    NODE_CATEGORY = "error_handling/logging"

    def get_node_class(self):
        """Return the CasareRPA node class for schema lookup."""
        from casare_rpa.nodes.error_handling_nodes import LogErrorNode

        return LogErrorNode

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("error_message", DataType.STRING)
        self.add_typed_input("error_type", DataType.STRING)
        self.add_typed_input("context", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("log_entry", DataType.STRING)


class VisualAssertNode(VisualNode):
    """Visual representation of AssertNode.

    Widgets are auto-generated from AssertNode's @properties decorator.
    """

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Assert"
    NODE_CATEGORY = "error_handling/try_catch"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input("exec_in")
        self.add_typed_input("condition", DataType.BOOLEAN)
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("passed", DataType.BOOLEAN)


# Desktop Automation Nodes

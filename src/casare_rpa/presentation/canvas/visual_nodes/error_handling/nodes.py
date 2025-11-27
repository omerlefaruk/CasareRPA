"""Visual nodes for error_handling category."""
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

class VisualTryNode(VisualNode):
    """Visual representation of TryNode."""
    
    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Try"
    NODE_CATEGORY = "error_handling"
    
    def __init__(self) -> None:
        """Initialize Try node."""
        super().__init__()
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("try_body")
        self.add_output("success")
        self.add_output("catch")
        self.add_output("error_message")
        self.add_output("error_type")

class VisualRetryNode(VisualNode):
    """Visual representation of RetryNode."""
    
    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Retry"
    NODE_CATEGORY = "error_handling"
    
    def __init__(self) -> None:
        """Initialize Retry node."""
        super().__init__()
        self.add_text_input("max_attempts", "Max Attempts", text="3", tab="properties")
        self.add_text_input("initial_delay", "Initial Delay (s)", text="1.0", tab="properties")
        self.add_text_input("backoff_multiplier", "Backoff Multiplier", text="2.0", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("retry_body")
        self.add_output("success")
        self.add_output("failed")
        self.add_output("attempt")
        self.add_output("last_error")

class VisualRetrySuccessNode(VisualNode):
    """Visual representation of RetrySuccessNode."""
    
    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Retry Success"
    NODE_CATEGORY = "error_handling"
    
    def __init__(self) -> None:
        """Initialize RetrySuccess node."""
        super().__init__()
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")

class VisualRetryFailNode(VisualNode):
    """Visual representation of RetryFailNode."""
    
    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Retry Fail"
    NODE_CATEGORY = "error_handling"
    
    def __init__(self) -> None:
        """Initialize RetryFail node."""
        super().__init__()
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("error_message")
        self.add_output("exec_out")

class VisualThrowErrorNode(VisualNode):
    """Visual representation of ThrowErrorNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Throw Error"
    NODE_CATEGORY = "error_handling"

    def __init__(self) -> None:
        """Initialize ThrowError node."""
        super().__init__()
        self.add_text_input("error_message", "Error Message", text="Custom error", tab="properties")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("error_message")
        self.add_output("exec_out")

class VisualWebhookNotifyNode(VisualNode):
    """Visual representation of WebhookNotifyNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Webhook Notify"
    NODE_CATEGORY = "error_handling"

    def __init__(self) -> None:
        """Initialize Webhook Notify node."""
        super().__init__()
        self.add_text_input("webhook_url", "Webhook URL", text="", tab="inputs")
        self.add_text_input("message", "Message", text="Error notification from CasareRPA", tab="inputs")
        self.create_property("format", "generic",
                           items=["generic", "slack", "discord", "teams"],
                           widget_type=3, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("webhook_url")
        self.add_input("message")
        self.add_input("error_details")
        self.add_output("exec_out")
        self.add_output("success")
        self.add_output("response")

class VisualOnErrorNode(VisualNode):
    """Visual representation of OnErrorNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "On Error"
    NODE_CATEGORY = "error_handling"

    def __init__(self) -> None:
        """Initialize On Error node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("protected_body")
        self.add_output("on_error")
        self.add_output("finally")
        self.add_output("error_message")
        self.add_output("error_type")
        self.add_output("error_node")
        self.add_output("stack_trace")

class VisualErrorRecoveryNode(VisualNode):
    """Visual representation of ErrorRecoveryNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Error Recovery"
    NODE_CATEGORY = "error_handling"

    def __init__(self) -> None:
        """Initialize Error Recovery node."""
        super().__init__()
        self.create_property("strategy", "stop",
                           items=["stop", "continue", "retry", "restart", "fallback"],
                           widget_type=3, tab="config")
        self.add_text_input("max_retries", "Max Retries", text="3", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("strategy")
        self.add_input("max_retries")
        self.add_output("exec_out")
        self.add_output("fallback")

class VisualLogErrorNode(VisualNode):
    """Visual representation of LogErrorNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Log Error"
    NODE_CATEGORY = "error_handling"

    def __init__(self) -> None:
        """Initialize Log Error node."""
        super().__init__()
        self.create_property("level", "error",
                           items=["debug", "info", "warning", "error", "critical"],
                           widget_type=3, tab="config")
        self.create_property("include_stack_trace", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("error_message")
        self.add_input("error_type")
        self.add_input("context")
        self.add_output("exec_out")
        self.add_output("log_entry")

class VisualAssertNode(VisualNode):
    """Visual representation of AssertNode."""

    __identifier__ = "casare_rpa.error_handling"
    NODE_NAME = "Assert"
    NODE_CATEGORY = "error_handling"

    def __init__(self) -> None:
        """Initialize Assert node."""
        super().__init__()
        self.add_text_input("message", "Assertion Message", text="Assertion failed", tab="properties")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("condition")
        self.add_input("message")
        self.add_output("exec_out")
        self.add_output("passed")


# Desktop Automation Nodes


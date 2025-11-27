"""Visual nodes for utility category."""
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

class VisualHttpRequestNode(VisualNode):
    """Visual representation of HttpRequestNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "HTTP Request"
    NODE_CATEGORY = "utility"
    CASARE_NODE_MODULE = "utility"

    def __init__(self) -> None:
        """Initialize HTTP Request node."""
        super().__init__()
        self.add_text_input("url", "URL", placeholder_text="https://api.example.com", tab="inputs")
        self.add_combo_menu("method", "Method", items=[
            "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"
        ], tab="inputs")
        self.add_text_input("headers", "Headers (JSON)", text="{}", tab="inputs")
        self.add_text_input("body", "Body", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        self.create_property("follow_redirects", True, widget_type=1, tab="config")
        # Advanced options
        self.add_text_input("proxy", "Proxy URL", placeholder_text="http://proxy:port", tab="advanced")
        self.add_text_input("retry_count", "Retry Count", placeholder_text="0", tab="advanced")
        self.add_text_input("retry_delay", "Retry Delay (s)", placeholder_text="1.0", tab="advanced")
        self.add_text_input("max_redirects", "Max Redirects", placeholder_text="10", tab="advanced")
        self.add_combo_menu("response_encoding", "Response Encoding", items=["utf-8", "latin-1", "ascii", "auto"], tab="advanced")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("headers")
        self.add_input("body")
        self.add_output("exec_out")
        self.add_output("response")
        self.add_output("status_code")
        self.add_output("headers")
        self.add_output("success")

class VisualValidateNode(VisualNode):
    """Visual representation of ValidateNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Validate"
    NODE_CATEGORY = "utility"
    CASARE_NODE_MODULE = "utility"

    def __init__(self) -> None:
        """Initialize Validate node."""
        super().__init__()
        self.add_combo_menu("validation_type", "Validation Type", items=[
            "not_empty", "is_numeric", "is_integer", "min_length", "max_length",
            "min_value", "max_value", "in_list", "is_email", "is_url"
        ], tab="inputs")
        self.add_text_input("validation_param", "Parameter", text="", tab="inputs")
        self.add_text_input("error_message", "Error Message", text="Validation failed", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("value")
        self.add_output("exec_out")
        self.add_output("is_valid")
        self.add_output("error_message")

class VisualTransformNode(VisualNode):
    """Visual representation of TransformNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Transform"
    NODE_CATEGORY = "utility"
    CASARE_NODE_MODULE = "utility"

    def __init__(self) -> None:
        """Initialize Transform node."""
        super().__init__()
        self.add_combo_menu("transform_type", "Transform Type", items=[
            "uppercase", "lowercase", "trim", "strip", "replace",
            "split", "join", "to_int", "to_float", "to_string", "to_bool"
        ], tab="inputs")
        self.add_text_input("transform_param", "Parameter", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("value")
        self.add_output("exec_out")
        self.add_output("result")
        self.add_output("success")

class VisualLogNode(VisualNode):
    """Visual representation of LogNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Log"
    NODE_CATEGORY = "utility"
    CASARE_NODE_MODULE = "utility"

    def __init__(self) -> None:
        """Initialize Log node."""
        super().__init__()
        self.add_text_input("message", "Message", text="", tab="inputs")
        self.add_combo_menu("level", "Level", items=[
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        ], tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("message")
        self.add_input("data")
        self.add_output("exec_out")


# =============================================================================
# Office Automation Nodes
# =============================================================================


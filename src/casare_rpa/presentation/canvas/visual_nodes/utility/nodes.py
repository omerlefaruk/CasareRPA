"""Visual nodes for utility category."""
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

# NOTE: VisualHttpRequestNode was removed - it's a duplicate of rest_api.VisualHttpRequestNode
# Use: from casare_rpa.presentation.canvas.visual_nodes.rest_api import VisualHttpRequestNode

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


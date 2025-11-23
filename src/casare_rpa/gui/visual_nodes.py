"""
NodeGraphQt integration for CasareRPA nodes.

This module provides visual node classes that bridge CasareRPA's BaseNode
with NodeGraphQt's visual representation.
"""

from typing import Type, Optional, Any, Dict
from NodeGraphQt import BaseNode as NodeGraphQtBaseNode
from PySide6.QtGui import QColor

from ..core.base_node import BaseNode as CasareBaseNode
from ..core.types import PortType, DataType
from loguru import logger


# Unified color scheme for all nodes matching the image colors
# Using dark teal/gray with cyan accent border (matches reference image)
UNIFIED_NODE_COLOR = QColor(52, 58, 64)  # Dark gray node body - #343a40

# Legacy color scheme (kept for reference but not used)
NODE_COLORS = {
    "basic": UNIFIED_NODE_COLOR,
    "browser": UNIFIED_NODE_COLOR,
    "navigation": UNIFIED_NODE_COLOR,
    "interaction": UNIFIED_NODE_COLOR,
    "data": UNIFIED_NODE_COLOR,
    "wait": UNIFIED_NODE_COLOR,
    "variable": UNIFIED_NODE_COLOR,
}


class VisualNode(NodeGraphQtBaseNode):
    """
    Base class for visual nodes in NodeGraphQt.
    
    Bridges CasareRPA BaseNode with NodeGraphQt visual representation.
    """
    
    # Class attributes for node metadata
    __identifier__ = "casare_rpa"
    NODE_NAME = "Visual Node"
    NODE_CATEGORY = "basic"
    
    def __init__(self) -> None:
        """Initialize visual node."""
        super().__init__()
        
        # Reference to the underlying CasareRPA node
        self._casare_node: Optional[CasareBaseNode] = None
        
        # Set node color based on category
        color = NODE_COLORS.get(self.NODE_CATEGORY, QColor(100, 100, 100))
        self.set_color(color.red(), color.green(), color.blue())
        
        # Create and initialize node properties
        self.create_property("node_id", "")
        self.create_property("status", "idle")
        
        # Auto-create linked CasareRPA node
        # This ensures every visual node has a CasareRPA node regardless of how it was created
        self._auto_create_casare_node()
        
        # Setup ports for this node type
        self.setup_ports()
    
    def setup_ports(self) -> None:
        """
        Setup node ports.
        
        Override this method in subclasses to define ports.
        """
        pass
    
    def get_casare_node(self) -> Optional[CasareBaseNode]:
        """
        Get the underlying CasareRPA node instance.
        
        Returns:
            CasareRPA node instance or None
        """
        return self._casare_node
    
    def set_casare_node(self, node: CasareBaseNode) -> None:
        """
        Set the underlying CasareRPA node instance.
        
        Args:
            node: CasareRPA node instance
        """
        self._casare_node = node
        self.set_property("node_id", node.node_id)
    
    def _auto_create_casare_node(self) -> None:
        """
        Automatically create and link CasareRPA node.
        Called during __init__ to ensure every visual node has a backing CasareRPA node.
        Handles all creation scenarios: menu, copy/paste, undo/redo, workflow loading.
        """
        if self._casare_node is not None:
            return  # Already has a node
        
        try:
            # Import here to avoid circular dependency
            from .node_registry import get_node_factory
            factory = get_node_factory()
            
            # Create the CasareRPA node
            casare_node = factory.create_casare_node(self)
            if casare_node:
                # Node is already linked via factory.create_casare_node -> set_casare_node
                pass
        except Exception:
            # Silently fail during initialization - node will be created later if needed
            # This handles cases where factory isn't ready yet (e.g., during testing)
            pass
    
    def ensure_casare_node(self) -> Optional[CasareBaseNode]:
        """
        Ensure this visual node has a CasareRPA node, creating one if necessary.
        Use this before any operation that requires the CasareRPA node.
        
        Returns:
            The CasareRPA node instance, or None if creation failed
        """
        if self._casare_node is None:
            self._auto_create_casare_node()
        return self._casare_node
    
    def update_status(self, status: str) -> None:
        """
        Update node visual status.
        
        Args:
            status: Node status (idle, running, success, error)
        """
        self.set_property("status", status)
        
        # Update node color based on status
        if status == "running":
            self.set_color(255, 165, 0)  # Orange
        elif status == "success":
            self.set_color(76, 175, 80)  # Green
        elif status == "error":
            self.set_color(244, 67, 54)  # Red
        else:  # idle
            color = NODE_COLORS.get(self.NODE_CATEGORY, QColor(100, 100, 100))
            self.set_color(color.red(), color.green(), color.blue())


# Basic Nodes

class VisualStartNode(VisualNode):
    """Visual representation of StartNode."""
    
    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "Start"
    NODE_CATEGORY = "basic"
    
    def setup_ports(self) -> None:
        """Setup ports for start node."""
        self.add_output("exec_out")


class VisualEndNode(VisualNode):
    """Visual representation of EndNode."""
    
    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "End"
    NODE_CATEGORY = "basic"
    
    def setup_ports(self) -> None:
        """Setup ports for end node."""
        self.add_input("exec_in")


class VisualCommentNode(VisualNode):
    """Visual representation of CommentNode."""
    
    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "Comment"
    NODE_CATEGORY = "basic"
    
    def __init__(self) -> None:
        """Initialize comment node."""
        super().__init__()
        self.add_text_input("comment", "Comment", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports for comment node."""
        pass  # No ports for comment node


# Browser Control Nodes

class VisualLaunchBrowserNode(VisualNode):
    """Visual representation of LaunchBrowserNode."""
    
    __identifier__ = "casare_rpa.browser"
    NODE_NAME = "Launch Browser"
    NODE_CATEGORY = "browser"
    
    def __init__(self) -> None:
        """Initialize launch browser node."""
        super().__init__()
        self.add_text_input("url", "URL", placeholder_text="https://example.com", tab="properties")
        self.add_combo_menu("browser_type", "Browser", items=["chromium", "firefox", "webkit"], tab="properties")
        self.add_checkbox("headless", "Headless", state=False, tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_output("exec_out")
        self.add_output("browser")
        self.add_output("page")


class VisualCloseBrowserNode(VisualNode):
    """Visual representation of CloseBrowserNode."""
    
    __identifier__ = "casare_rpa.browser"
    NODE_NAME = "Close Browser"
    NODE_CATEGORY = "browser"
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("browser")
        self.add_output("exec_out")


class VisualNewTabNode(VisualNode):
    """Visual representation of NewTabNode."""
    
    __identifier__ = "casare_rpa.browser"
    NODE_NAME = "New Tab"
    NODE_CATEGORY = "browser"
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("browser")
        self.add_output("exec_out")
        self.add_output("page")


# Navigation Nodes

class VisualGoToURLNode(VisualNode):
    """Visual representation of GoToURLNode."""
    
    __identifier__ = "casare_rpa.navigation"
    NODE_NAME = "Go To URL"
    NODE_CATEGORY = "navigation"
    
    def __init__(self) -> None:
        """Initialize go to URL node."""
        super().__init__()
        self.add_text_input("url", "URL", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("url")
        self.add_output("exec_out")
        self.add_output("page")


class VisualGoBackNode(VisualNode):
    """Visual representation of GoBackNode."""
    
    __identifier__ = "casare_rpa.navigation"
    NODE_NAME = "Go Back"
    NODE_CATEGORY = "navigation"
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_output("exec_out")
        self.add_output("page")


class VisualGoForwardNode(VisualNode):
    """Visual representation of GoForwardNode."""
    
    __identifier__ = "casare_rpa.navigation"
    NODE_NAME = "Go Forward"
    NODE_CATEGORY = "navigation"
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_output("exec_out")
        self.add_output("page")


class VisualRefreshPageNode(VisualNode):
    """Visual representation of RefreshPageNode."""
    
    __identifier__ = "casare_rpa.navigation"
    NODE_NAME = "Refresh Page"
    NODE_CATEGORY = "navigation"
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_output("exec_out")
        self.add_output("page")


# Interaction Nodes

class VisualClickElementNode(VisualNode):
    """Visual representation of ClickElementNode."""
    
    __identifier__ = "casare_rpa.interaction"
    NODE_NAME = "Click Element"
    NODE_CATEGORY = "interaction"
    
    def __init__(self) -> None:
        """Initialize click element node."""
        super().__init__()
        self.add_text_input("selector", "Selector", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("selector")
        self.add_output("exec_out")
        self.add_output("page")


class VisualTypeTextNode(VisualNode):
    """Visual representation of TypeTextNode."""
    
    __identifier__ = "casare_rpa.interaction"
    NODE_NAME = "Type Text"
    NODE_CATEGORY = "interaction"
    
    def __init__(self) -> None:
        """Initialize type text node."""
        super().__init__()
        self.add_text_input("selector", "Selector", tab="properties")
        self.add_text_input("text", "Text", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("selector")
        self.add_input("text")
        self.add_output("exec_out")
        self.add_output("page")


class VisualSelectDropdownNode(VisualNode):
    """Visual representation of SelectDropdownNode."""
    
    __identifier__ = "casare_rpa.interaction"
    NODE_NAME = "Select Dropdown"
    NODE_CATEGORY = "interaction"
    
    def __init__(self) -> None:
        """Initialize select dropdown node."""
        super().__init__()
        self.add_text_input("selector", "Selector", tab="properties")
        self.add_text_input("value", "Value", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("selector")
        self.add_input("value")
        self.add_output("exec_out")
        self.add_output("page")


# Data Extraction Nodes

class VisualExtractTextNode(VisualNode):
    """Visual representation of ExtractTextNode."""
    
    __identifier__ = "casare_rpa.data"
    NODE_NAME = "Extract Text"
    NODE_CATEGORY = "data"
    
    def __init__(self) -> None:
        """Initialize extract text node."""
        super().__init__()
        self.add_text_input("selector", "Selector", tab="properties")
        self.add_text_input("variable_name", "Variable Name", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("selector")
        self.add_output("exec_out")
        self.add_output("page")
        self.add_output("text")


class VisualGetAttributeNode(VisualNode):
    """Visual representation of GetAttributeNode."""
    
    __identifier__ = "casare_rpa.data"
    NODE_NAME = "Get Attribute"
    NODE_CATEGORY = "data"
    
    def __init__(self) -> None:
        """Initialize get attribute node."""
        super().__init__()
        self.add_text_input("selector", "Selector", tab="properties")
        self.add_text_input("attribute", "Attribute", tab="properties")
        self.add_text_input("variable_name", "Variable Name", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("selector")
        self.add_input("attribute")
        self.add_output("exec_out")
        self.add_output("page")
        self.add_output("value")


class VisualScreenshotNode(VisualNode):
    """Visual representation of ScreenshotNode."""
    
    __identifier__ = "casare_rpa.data"
    NODE_NAME = "Screenshot"
    NODE_CATEGORY = "data"
    
    def __init__(self) -> None:
        """Initialize screenshot node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", tab="properties")
        self.add_checkbox("full_page", "Full Page", state=False, tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("page")


# Wait Nodes

class VisualWaitNode(VisualNode):
    """Visual representation of WaitNode."""
    
    __identifier__ = "casare_rpa.wait"
    NODE_NAME = "Wait"
    NODE_CATEGORY = "wait"
    
    def __init__(self) -> None:
        """Initialize wait node."""
        super().__init__()
        self.add_text_input("duration", "Duration (s)", text="1.0", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("duration")
        self.add_output("exec_out")


class VisualWaitForElementNode(VisualNode):
    """Visual representation of WaitForElementNode."""
    
    __identifier__ = "casare_rpa.wait"
    NODE_NAME = "Wait For Element"
    NODE_CATEGORY = "wait"
    
    def __init__(self) -> None:
        """Initialize wait for element node."""
        super().__init__()
        self.add_text_input("selector", "Selector", tab="properties")
        self.add_combo_menu("state", "State", items=["visible", "hidden", "attached", "detached"], tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_input("selector")
        self.add_output("exec_out")
        self.add_output("page")


class VisualWaitForNavigationNode(VisualNode):
    """Visual representation of WaitForNavigationNode."""
    
    __identifier__ = "casare_rpa.wait"
    NODE_NAME = "Wait For Navigation"
    NODE_CATEGORY = "wait"
    
    def __init__(self) -> None:
        """Initialize wait for navigation node."""
        super().__init__()
        self.add_combo_menu("wait_until", "Wait Until", items=["load", "domcontentloaded", "networkidle"], tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("page")
        self.add_output("exec_out")
        self.add_output("page")


# Variable Nodes

class VisualSetVariableNode(VisualNode):
    """Visual representation of SetVariableNode."""
    
    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Set Variable"
    NODE_CATEGORY = "variable"
    
    def __init__(self) -> None:
        """Initialize set variable node."""
        super().__init__()
        self.add_text_input("variable_name", "Variable Name", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("value")
        self.add_input("variable_name")
        self.add_output("exec_out")
        self.add_output("value")


class VisualGetVariableNode(VisualNode):
    """Visual representation of GetVariableNode."""
    
    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Get Variable"
    NODE_CATEGORY = "variable"
    
    def __init__(self) -> None:
        """Initialize get variable node."""
        super().__init__()
        self.add_text_input("variable_name", "Variable Name", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("variable_name")
        self.add_output("exec_out")
        self.add_output("value")


class VisualIncrementVariableNode(VisualNode):
    """Visual representation of IncrementVariableNode."""
    
    __identifier__ = "casare_rpa.variable"
    NODE_NAME = "Increment Variable"
    NODE_CATEGORY = "variable"
    
    def __init__(self) -> None:
        """Initialize increment variable node."""
        super().__init__()
        self.add_text_input("variable_name", "Variable Name", tab="properties")
        self.add_text_input("increment", "Increment", text="1.0", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("variable_name")
        self.add_input("increment")
        self.add_output("exec_out")
        self.add_output("value")


# Control Flow Nodes

class VisualIfNode(VisualNode):
    """Visual representation of IfNode."""
    
    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "If"
    NODE_CATEGORY = "control_flow"
    
    def __init__(self) -> None:
        """Initialize If node."""
        super().__init__()
        self.add_text_input("expression", "Expression", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("condition")
        self.add_output("true")
        self.add_output("false")


class VisualForLoopNode(VisualNode):
    """Visual representation of ForLoopNode."""
    
    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "For Loop"
    NODE_CATEGORY = "control_flow"
    
    def __init__(self) -> None:
        """Initialize For Loop node."""
        super().__init__()
        self.add_text_input("start", "Start", text="0", tab="properties")
        self.add_text_input("end", "End", text="10", tab="properties")
        self.add_text_input("step", "Step", text="1", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("items")
        self.add_output("loop_body")
        self.add_output("completed")
        self.add_output("item")
        self.add_output("index")


class VisualWhileLoopNode(VisualNode):
    """Visual representation of WhileLoopNode."""
    
    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "While Loop"
    NODE_CATEGORY = "control_flow"
    
    def __init__(self) -> None:
        """Initialize While Loop node."""
        super().__init__()
        self.add_text_input("expression", "Expression", tab="properties")
        self.add_text_input("max_iterations", "Max Iterations", text="1000", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("condition")
        self.add_output("loop_body")
        self.add_output("completed")
        self.add_output("iteration")


class VisualBreakNode(VisualNode):
    """Visual representation of BreakNode."""
    
    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Break"
    NODE_CATEGORY = "control_flow"
    
    def __init__(self) -> None:
        """Initialize Break node."""
        super().__init__()
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")


class VisualContinueNode(VisualNode):
    """Visual representation of ContinueNode."""
    
    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Continue"
    NODE_CATEGORY = "control_flow"
    
    def __init__(self) -> None:
        """Initialize Continue node."""
        super().__init__()
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")


class VisualSwitchNode(VisualNode):
    """Visual representation of SwitchNode."""
    
    __identifier__ = "casare_rpa.control_flow"
    NODE_NAME = "Switch"
    NODE_CATEGORY = "control_flow"
    
    def __init__(self) -> None:
        """Initialize Switch node."""
        super().__init__()
        self.add_text_input("expression", "Expression", tab="properties")
        self.add_text_input("cases", "Cases (comma-separated)", text="success,error,pending", tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("value")
        
        # Cases will be created dynamically based on config
        # But we need at least the default output
        self.add_output("default")


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


# Node registry mapping visual nodes to CasareRPA nodes
VISUAL_NODE_CLASSES = [
    # Basic
    VisualStartNode,
    VisualEndNode,
    VisualCommentNode,
    # Browser
    VisualLaunchBrowserNode,
    VisualCloseBrowserNode,
    VisualNewTabNode,
    # Navigation
    VisualGoToURLNode,
    VisualGoBackNode,
    VisualGoForwardNode,
    VisualRefreshPageNode,
    # Interaction
    VisualClickElementNode,
    VisualTypeTextNode,
    VisualSelectDropdownNode,
    # Data
    VisualExtractTextNode,
    VisualGetAttributeNode,
    VisualScreenshotNode,
    # Wait
    VisualWaitNode,
    VisualWaitForElementNode,
    VisualWaitForNavigationNode,
    # Variable
    VisualSetVariableNode,
    VisualGetVariableNode,
    VisualIncrementVariableNode,
    # Control Flow
    VisualIfNode,
    VisualForLoopNode,
    VisualWhileLoopNode,
    VisualBreakNode,
    VisualContinueNode,
    VisualSwitchNode,
    # Error Handling
    VisualTryNode,
    VisualRetryNode,
    VisualRetrySuccessNode,
    VisualRetryFailNode,
    VisualThrowErrorNode,
]

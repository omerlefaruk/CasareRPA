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


# Color scheme for different node categories
NODE_COLORS = {
    "basic": QColor(100, 100, 100),      # Gray
    "browser": QColor(66, 135, 245),     # Blue
    "navigation": QColor(76, 175, 80),   # Green
    "interaction": QColor(255, 152, 0),  # Orange
    "data": QColor(156, 39, 176),        # Purple
    "wait": QColor(255, 235, 59),        # Yellow
    "variable": QColor(244, 67, 54),     # Red
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
        
        # Set node properties
        self.set_property("node_id", "")
        self.set_property("status", "idle")
    
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
        self.add_combo_menu("browser_type", "Browser", items=["chromium", "firefox", "webkit"], tab="properties")
        self.add_checkbox("headless", "Headless", state=False, tab="properties")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")
        self.add_output("browser")


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
]

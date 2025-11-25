"""
NodeGraphQt integration for CasareRPA nodes.

This module provides visual node classes that bridge CasareRPA's BaseNode
with NodeGraphQt's visual representation.
"""

import inspect
from typing import Type, Optional, Any, Dict
from NodeGraphQt import BaseNode as NodeGraphQtBaseNode
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush
from PySide6.QtCore import Qt, QSize

from ..core.base_node import BaseNode as CasareBaseNode
from ..core.types import PortType, DataType
from loguru import logger

# Import Data Operation Nodes
from .data_operations_visual import (
    VisualConcatenateNode,
    VisualFormatStringNode,
    VisualRegexMatchNode,
    VisualRegexReplaceNode,
    VisualMathOperationNode,
    VisualComparisonNode,
    VisualCreateListNode,
    VisualListGetItemNode,
    VisualJsonParseNode,
    VisualGetPropertyNode
)

# Import Rich Comment Nodes
from .rich_comment_node import (
    VisualRichCommentNode,
    VisualStickyNoteNode,
    VisualHeaderCommentNode
)

from .base_visual_node import VisualNode, UNIFIED_NODE_COLOR

# Legacy color scheme (kept for reference but not used)
NODE_COLORS = {
    "basic": UNIFIED_NODE_COLOR,
    "browser": UNIFIED_NODE_COLOR,
    "variable": UNIFIED_NODE_COLOR,
    "utility": UNIFIED_NODE_COLOR,
}


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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
    NODE_CATEGORY = "browser"
    
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
        self.add_combo_menu("variable_type", "Type", items=[
            "String", 
            "Boolean", 
            "Int32", 
            "Object", 
            "Array", 
            "DataTable"
        ], tab="properties")
        self.add_text_input("default_value", "Value", tab="properties")
    
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


# Desktop Automation Nodes

class VisualLaunchApplicationNode(VisualNode):
    """Visual representation of LaunchApplicationNode."""
    
    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Launch Application"
    NODE_CATEGORY = "desktop_automation"
    
    def __init__(self) -> None:
        """Initialize Launch Application node."""
        super().__init__()
        self.add_text_input("application_path", "Application Path", text="calc.exe", tab="inputs")
        self.add_text_input("arguments", "Arguments", text="", tab="inputs")
        self.add_text_input("working_directory", "Working Directory", text="", tab="inputs")
        self.add_text_input("window_title_hint", "Window Title Hint", text="", tab="config")
        self.create_property("timeout", 10.0, widget_type=2, tab="config")
        self.create_property("window_state", "normal", 
                           items=["normal", "maximized", "minimized"],
                           widget_type=3, tab="config")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("application_path")
        self.add_input("arguments")
        self.add_input("working_directory")
        self.add_output("exec_out")
        self.add_output("window")
        self.add_output("process_id")
        self.add_output("window_title")


class VisualCloseApplicationNode(VisualNode):
    """Visual representation of CloseApplicationNode."""
    
    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Close Application"
    NODE_CATEGORY = "desktop_automation"
    
    def __init__(self) -> None:
        """Initialize Close Application node."""
        super().__init__()
        self.add_text_input("window_title", "Window Title", text="", tab="inputs")
        self.create_property("force_close", False, widget_type=1, tab="config")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_input("process_id")
        self.add_input("window_title")
        self.add_output("exec_out")
        self.add_output("success")


class VisualActivateWindowNode(VisualNode):
    """Visual representation of ActivateWindowNode."""
    
    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Activate Window"
    NODE_CATEGORY = "desktop_automation"
    
    def __init__(self) -> None:
        """Initialize Activate Window node."""
        super().__init__()
        self.add_text_input("window_title", "Window Title", text="", tab="inputs")
        self.create_property("match_partial", True, widget_type=1, tab="config")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")
    
    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_input("window_title")
        self.add_output("exec_out")
        self.add_output("success")
        self.add_output("window")


class VisualGetWindowListNode(VisualNode):
    """Visual representation of GetWindowListNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Window List"
    NODE_CATEGORY = "desktop_automation"

    def __init__(self) -> None:
        """Initialize Get Window List node."""
        super().__init__()
        self.add_text_input("filter_title", "Filter by Title", text="", tab="config")
        self.create_property("include_invisible", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")
        self.add_output("window_list")
        self.add_output("window_count")


class VisualFindElementNode(VisualNode):
    """Visual representation of FindElementNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Find Element"
    NODE_CATEGORY = "desktop_automation"

    def __init__(self) -> None:
        """Initialize Find Element node."""
        super().__init__()
        self.add_text_input("selector", "Selector (JSON)", text="", tab="inputs")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")
        self.create_property("throw_on_not_found", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("element")
        self.add_output("found")


class VisualClickElementDesktopNode(VisualNode):
    """Visual representation of ClickElementNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Click Element (Desktop)"
    NODE_CATEGORY = "desktop_automation"

    def __init__(self) -> None:
        """Initialize Click Element node."""
        super().__init__()
        self.add_text_input("selector", "Selector (JSON)", text="", tab="inputs")
        self.create_property("simulate", False, widget_type=1, tab="config")
        self.create_property("x_offset", 0, widget_type=2, tab="config")
        self.create_property("y_offset", 0, widget_type=2, tab="config")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("success")


class VisualTypeTextDesktopNode(VisualNode):
    """Visual representation of TypeTextNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Type Text (Desktop)"
    NODE_CATEGORY = "desktop_automation"

    def __init__(self) -> None:
        """Initialize Type Text node."""
        super().__init__()
        self.add_text_input("selector", "Selector (JSON)", text="", tab="inputs")
        self.add_text_input("text", "Text to Type", text="", tab="inputs")
        self.create_property("clear_first", False, widget_type=1, tab="config")
        self.create_property("interval", 0.01, widget_type=2, tab="config")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("success")


class VisualGetElementTextNode(VisualNode):
    """Visual representation of GetElementTextNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Element Text"
    NODE_CATEGORY = "desktop_automation"

    def __init__(self) -> None:
        """Initialize Get Element Text node."""
        super().__init__()
        self.add_text_input("selector", "Selector (JSON)", text="", tab="inputs")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")
        self.create_property("variable_name", "", widget_type=0, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("text")
        self.add_output("element")


class VisualGetElementPropertyNode(VisualNode):
    """Visual representation of GetElementPropertyNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Element Property"
    NODE_CATEGORY = "desktop_automation"

    def __init__(self) -> None:
        """Initialize Get Element Property node."""
        super().__init__()
        self.add_text_input("selector", "Selector (JSON)", text="", tab="inputs")
        self.add_text_input("property_name", "Property Name", text="Name", tab="inputs")
        self.create_property("timeout", 5.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("value")
        self.add_output("element")


# Dynamic node discovery
def _get_visual_node_classes():
    """Dynamically discover all VisualNode subclasses in this module."""
    classes = []
    for name, obj in globals().items():
        if inspect.isclass(obj) and issubclass(obj, VisualNode) and obj is not VisualNode:
            # Ensure it has a valid NODE_NAME and is not a base class
            if hasattr(obj, 'NODE_NAME') and obj.NODE_NAME and obj.NODE_NAME != "Visual Node":
                classes.append(obj)
    return classes

VISUAL_NODE_CLASSES = _get_visual_node_classes()

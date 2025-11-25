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
    VisualGetPropertyNode,
    # List operation nodes
    VisualListLengthNode,
    VisualListAppendNode,
    VisualListContainsNode,
    VisualListSliceNode,
    VisualListJoinNode,
    VisualListSortNode,
    VisualListReverseNode,
    VisualListUniqueNode,
    VisualListFilterNode,
    VisualListMapNode,
    VisualListReduceNode,
    VisualListFlattenNode,
    # Dict operation nodes
    VisualDictGetNode,
    VisualDictSetNode,
    VisualDictRemoveNode,
    VisualDictMergeNode,
    VisualDictKeysNode,
    VisualDictValuesNode,
    VisualDictHasKeyNode,
    VisualCreateDictNode,
    VisualDictToJsonNode,
    VisualDictItemsNode,
)

# Import Rich Comment Nodes
from .rich_comment_node import (
    VisualRichCommentNode,
    VisualStickyNoteNode,
    VisualHeaderCommentNode
)

from .base_visual_node import VisualNode, UNIFIED_NODE_COLOR

# Import Extended Visual Nodes
from .extended_visual_nodes import EXTENDED_VISUAL_NODE_CLASSES

# Legacy color scheme (kept for reference but not used)
NODE_COLORS = {
    "basic": UNIFIED_NODE_COLOR,
    "browser": UNIFIED_NODE_COLOR,
    "variable": UNIFIED_NODE_COLOR,
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

class VisualLaunchApplicationNode(VisualNode):
    """Visual representation of LaunchApplicationNode."""
    
    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Launch Application"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"
    
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
    CASARE_NODE_MODULE = "desktop"
    
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
    CASARE_NODE_MODULE = "desktop"
    
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
    CASARE_NODE_MODULE = "desktop"

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
    CASARE_NODE_MODULE = "desktop"

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
    CASARE_NODE_CLASS = "ClickElementNode"

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Click Element (Desktop)"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

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
    CASARE_NODE_CLASS = "TypeTextNode"

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Type Text (Desktop)"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

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
    CASARE_NODE_MODULE = "desktop"

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
    CASARE_NODE_MODULE = "desktop"

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


# Window Management Nodes

class VisualResizeWindowNode(VisualNode):
    """Visual representation of ResizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Resize Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Resize Window node."""
        super().__init__()
        # Use window_width/window_height to avoid conflict with reserved "width"/"height" properties
        self.create_property("window_width", 800, widget_type=2, tab="config")
        self.create_property("window_height", 600, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_input("window_width")
        self.add_input("window_height")
        self.add_output("exec_out")
        self.add_output("success")


class VisualMoveWindowNode(VisualNode):
    """Visual representation of MoveWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Move Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Move Window node."""
        super().__init__()
        # Use pos_x/pos_y to avoid conflict with reserved "x"/"y" properties
        self.create_property("pos_x", 100, widget_type=2, tab="config")
        self.create_property("pos_y", 100, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_input("pos_x")
        self.add_input("pos_y")
        self.add_output("exec_out")
        self.add_output("success")


class VisualMaximizeWindowNode(VisualNode):
    """Visual representation of MaximizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Maximize Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("success")


class VisualMinimizeWindowNode(VisualNode):
    """Visual representation of MinimizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Minimize Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("success")


class VisualRestoreWindowNode(VisualNode):
    """Visual representation of RestoreWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Restore Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("success")


class VisualGetWindowPropertiesNode(VisualNode):
    """Visual representation of GetWindowPropertiesNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Window Properties"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_output("exec_out")
        self.add_output("properties")
        self.add_output("title")
        self.add_output("x")
        self.add_output("y")
        self.add_output("width")
        self.add_output("height")
        self.add_output("state")
        self.add_output("is_maximized")
        self.add_output("is_minimized")


class VisualSetWindowStateNode(VisualNode):
    """Visual representation of SetWindowStateNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Set Window State"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Set Window State node."""
        super().__init__()
        self.create_property("state", "normal",
                           items=["normal", "maximized", "minimized"],
                           widget_type=3, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("window")
        self.add_input("state")
        self.add_output("exec_out")
        self.add_output("success")


# Advanced Interaction Nodes

class VisualSelectFromDropdownNode(VisualNode):
    """Visual representation of SelectFromDropdownNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select From Dropdown"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Select From Dropdown node."""
        super().__init__()
        self.add_text_input("value", "Value to Select", text="", tab="inputs")
        self.create_property("by_text", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("value")
        self.add_output("exec_out")
        self.add_output("success")


class VisualCheckCheckboxNode(VisualNode):
    """Visual representation of CheckCheckboxNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Check Checkbox"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Check Checkbox node."""
        super().__init__()
        self.create_property("check", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_output("exec_out")
        self.add_output("success")


class VisualSelectRadioButtonNode(VisualNode):
    """Visual representation of SelectRadioButtonNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select Radio Button"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_output("exec_out")
        self.add_output("success")


class VisualSelectTabNode(VisualNode):
    """Visual representation of SelectTabNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select Tab"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Select Tab node."""
        super().__init__()
        self.add_text_input("tab_name", "Tab Name", text="", tab="inputs")
        self.create_property("tab_index", -1, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("tab_control")
        self.add_input("tab_name")
        self.add_input("tab_index")
        self.add_output("exec_out")
        self.add_output("success")


class VisualExpandTreeItemNode(VisualNode):
    """Visual representation of ExpandTreeItemNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Expand Tree Item"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Expand Tree Item node."""
        super().__init__()
        self.create_property("expand", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_output("exec_out")
        self.add_output("success")


class VisualScrollElementNode(VisualNode):
    """Visual representation of ScrollElementNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Scroll Element"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Scroll Element node."""
        super().__init__()
        self.create_property("direction", "down",
                           items=["up", "down", "left", "right"],
                           widget_type=3, tab="config")
        self.create_property("amount", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_output("exec_out")
        self.add_output("success")


# Mouse & Keyboard Control Nodes

class VisualMoveMouseNode(VisualNode):
    """Visual representation of MoveMouseNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Move Mouse"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Move Mouse node."""
        super().__init__()
        self.create_property("mouse_x", 0, widget_type=2, tab="config")
        self.create_property("mouse_y", 0, widget_type=2, tab="config")
        self.create_property("duration", 0.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("x")
        self.add_input("y")
        self.add_input("duration")
        self.add_output("exec_out")
        self.add_output("success")


class VisualMouseClickNode(VisualNode):
    """Visual representation of MouseClickNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Mouse Click"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Mouse Click node."""
        super().__init__()
        self.create_property("click_x", 0, widget_type=2, tab="config")
        self.create_property("click_y", 0, widget_type=2, tab="config")
        self.create_property("button", "left",
                           items=["left", "right", "middle"],
                           widget_type=3, tab="config")
        self.create_property("click_type", "single",
                           items=["single", "double", "triple"],
                           widget_type=3, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("x")
        self.add_input("y")
        self.add_output("exec_out")
        self.add_output("success")


class VisualSendKeysNode(VisualNode):
    """Visual representation of SendKeysNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Send Keys"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Send Keys node."""
        super().__init__()
        self.add_text_input("keys", "Keys to Send", text="", tab="inputs")
        self.create_property("interval", 0.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("keys")
        self.add_input("interval")
        self.add_output("exec_out")
        self.add_output("success")


class VisualSendHotKeyNode(VisualNode):
    """Visual representation of SendHotKeyNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Send Hotkey"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Send Hotkey node."""
        super().__init__()
        self.add_text_input("keys", "Hotkey (e.g., Ctrl,C)", text="Ctrl,C", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("keys")
        self.add_output("exec_out")
        self.add_output("success")


class VisualGetMousePositionNode(VisualNode):
    """Visual representation of GetMousePositionNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Mouse Position"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")
        self.add_output("x")
        self.add_output("y")


class VisualDragMouseNode(VisualNode):
    """Visual representation of DragMouseNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Drag Mouse"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Drag Mouse node."""
        super().__init__()
        self.create_property("start_x", 0, widget_type=2, tab="config")
        self.create_property("start_y", 0, widget_type=2, tab="config")
        self.create_property("end_x", 100, widget_type=2, tab="config")
        self.create_property("end_y", 100, widget_type=2, tab="config")
        self.create_property("button", "left",
                           items=["left", "right", "middle"],
                           widget_type=3, tab="config")
        self.create_property("duration", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("start_x")
        self.add_input("start_y")
        self.add_input("end_x")
        self.add_input("end_y")
        self.add_input("duration")
        self.add_output("exec_out")
        self.add_output("success")


# Wait & Verification Nodes

class VisualWaitForElementNode(VisualNode):
    """Visual representation of WaitForElementNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Wait For Element"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Wait For Element node."""
        super().__init__()
        self.create_property("timeout", 10.0, widget_type=2, tab="config")
        self.create_property("state", "visible",
                           items=["visible", "hidden", "enabled", "disabled"],
                           widget_type=3, tab="config")
        self.create_property("poll_interval", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("selector")
        self.add_input("timeout")
        self.add_output("exec_out")
        self.add_output("element")
        self.add_output("success")


class VisualWaitForWindowNode(VisualNode):
    """Visual representation of WaitForWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Wait For Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Wait For Window node."""
        super().__init__()
        self.add_text_input("title", "Window Title", text="", tab="inputs")
        self.add_text_input("title_regex", "Title Regex", text="", tab="inputs")
        self.add_text_input("class_name", "Class Name", text="", tab="inputs")
        self.create_property("timeout", 10.0, widget_type=2, tab="config")
        self.create_property("state", "visible",
                           items=["visible", "hidden"],
                           widget_type=3, tab="config")
        self.create_property("poll_interval", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("title")
        self.add_input("title_regex")
        self.add_input("class_name")
        self.add_input("timeout")
        self.add_output("exec_out")
        self.add_output("window")
        self.add_output("success")


class VisualVerifyElementExistsNode(VisualNode):
    """Visual representation of VerifyElementExistsNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Verify Element Exists"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Verify Element Exists node."""
        super().__init__()
        self.create_property("timeout", 0.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("selector")
        self.add_input("timeout")
        self.add_output("exec_out")
        self.add_output("exists")
        self.add_output("element")


class VisualVerifyElementPropertyNode(VisualNode):
    """Visual representation of VerifyElementPropertyNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Verify Element Property"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Verify Element Property node."""
        super().__init__()
        self.add_text_input("property_name", "Property Name", text="Name", tab="inputs")
        self.add_text_input("expected_value", "Expected Value", text="", tab="inputs")
        self.create_property("comparison", "equals",
                           items=["equals", "contains", "startswith", "endswith",
                                  "regex", "greater", "less", "not_equals"],
                           widget_type=3, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("property_name")
        self.add_input("expected_value")
        self.add_output("exec_out")
        self.add_output("result")
        self.add_output("actual_value")


# ============================================================
# Screenshot & OCR Visual Nodes (Bite 9)
# ============================================================

class VisualCaptureScreenshotNode(VisualNode):
    """Visual representation of CaptureScreenshotNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Capture Screenshot"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Capture Screenshot node."""
        super().__init__()
        self.add_text_input("file_path", "Save Path", text="", tab="inputs")
        self.create_property("format", "PNG",
                           items=["PNG", "JPEG", "BMP"],
                           widget_type=3, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("region")
        self.add_output("exec_out")
        self.add_output("image")
        self.add_output("success")


class VisualCaptureElementImageNode(VisualNode):
    """Visual representation of CaptureElementImageNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Capture Element Image"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Capture Element Image node."""
        super().__init__()
        self.add_text_input("file_path", "Save Path", text="", tab="inputs")
        self.create_property("padding", 0, widget_type=2, tab="config")
        self.create_property("format", "PNG",
                           items=["PNG", "JPEG", "BMP"],
                           widget_type=3, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("element")
        self.add_input("file_path")
        self.add_input("padding")
        self.add_output("exec_out")
        self.add_output("image")
        self.add_output("success")


class VisualOCRExtractTextNode(VisualNode):
    """Visual representation of OCRExtractTextNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "OCR Extract Text"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize OCR Extract Text node."""
        super().__init__()
        self.add_text_input("image_path", "Image Path", text="", tab="inputs")
        self.add_combo_menu("engine", "OCR Engine", items=["auto", "rapidocr", "tesseract", "winocr"], tab="config")
        self.add_text_input("language", "Language", text="eng", tab="config")
        self.add_text_input("config", "Tesseract Config", text="", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("image")
        self.add_input("image_path")
        self.add_input("region")
        self.add_output("exec_out")
        self.add_output("text")
        self.add_output("engine_used")
        self.add_output("success")


class VisualCompareImagesNode(VisualNode):
    """Visual representation of CompareImagesNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Compare Images"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Compare Images node."""
        super().__init__()
        self.add_text_input("image1_path", "Image 1 Path", text="", tab="inputs")
        self.add_text_input("image2_path", "Image 2 Path", text="", tab="inputs")
        self.create_property("method", "histogram",
                           items=["histogram", "ssim", "pixel"],
                           widget_type=3, tab="config")
        self.create_property("threshold", 0.9, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("image1")
        self.add_input("image2")
        self.add_input("image1_path")
        self.add_input("image2_path")
        self.add_output("exec_out")
        self.add_output("similarity")
        self.add_output("is_match")
        self.add_output("method")


# =============================================================================
# File System Nodes
# =============================================================================

class VisualReadFileNode(VisualNode):
    """Visual representation of ReadFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Read File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.create_property("binary_mode", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("content")
        self.add_output("size")
        self.add_output("success")


class VisualWriteFileNode(VisualNode):
    """Visual representation of WriteFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Write File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Write File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("content", "Content", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")
        self.create_property("create_dirs", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("content")
        self.add_output("exec_out")
        self.add_output("bytes_written")
        self.add_output("success")


class VisualAppendFileNode(VisualNode):
    """Visual representation of AppendFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Append File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Append File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("content", "Content", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("content")
        self.add_output("exec_out")
        self.add_output("bytes_written")
        self.add_output("success")


class VisualDeleteFileNode(VisualNode):
    """Visual representation of DeleteFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Delete File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Delete File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("ignore_errors", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("success")


class VisualCopyFileNode(VisualNode):
    """Visual representation of CopyFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Copy File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Copy File node."""
        super().__init__()
        self.add_text_input("source_path", "Source Path", text="", tab="inputs")
        self.add_text_input("dest_path", "Destination Path", text="", tab="inputs")
        self.create_property("overwrite", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("source_path")
        self.add_input("dest_path")
        self.add_output("exec_out")
        self.add_output("dest_path")
        self.add_output("success")


class VisualMoveFileNode(VisualNode):
    """Visual representation of MoveFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Move File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Move File node."""
        super().__init__()
        self.add_text_input("source_path", "Source Path", text="", tab="inputs")
        self.add_text_input("dest_path", "Destination Path", text="", tab="inputs")
        self.create_property("overwrite", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("source_path")
        self.add_input("dest_path")
        self.add_output("exec_out")
        self.add_output("dest_path")
        self.add_output("success")


class VisualCreateDirectoryNode(VisualNode):
    """Visual representation of CreateDirectoryNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Create Directory"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Create Directory node."""
        super().__init__()
        self.add_text_input("directory_path", "Directory Path", text="", tab="inputs")
        self.create_property("parents", True, widget_type=1, tab="config")
        self.create_property("exist_ok", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("directory_path")
        self.add_output("exec_out")
        self.add_output("directory_path")
        self.add_output("success")


class VisualListDirectoryNode(VisualNode):
    """Visual representation of ListDirectoryNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "List Directory"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize List Directory node."""
        super().__init__()
        self.add_text_input("directory_path", "Directory Path", text=".", tab="inputs")
        self.add_text_input("pattern", "Pattern", text="*", tab="config")
        self.create_property("recursive", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("directory_path")
        self.add_output("exec_out")
        self.add_output("files")
        self.add_output("count")
        self.add_output("success")


class VisualFileExistsNode(VisualNode):
    """Visual representation of FileExistsNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "File Exists"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize File Exists node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("exists")
        self.add_output("is_file")
        self.add_output("is_dir")


class VisualGetFileInfoNode(VisualNode):
    """Visual representation of GetFileInfoNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Get File Info"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Get File Info node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("size")
        self.add_output("created")
        self.add_output("modified")
        self.add_output("extension")
        self.add_output("name")
        self.add_output("parent")
        self.add_output("success")


class VisualReadCSVNode(VisualNode):
    """Visual representation of ReadCSVNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read CSV"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Read CSV node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("has_header", True, widget_type=1, tab="config")
        self.add_text_input("delimiter", "Delimiter", text=",", tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("headers")
        self.add_output("row_count")
        self.add_output("success")


class VisualWriteCSVNode(VisualNode):
    """Visual representation of WriteCSVNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Write CSV"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Write CSV node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("write_header", True, widget_type=1, tab="config")
        self.add_text_input("delimiter", "Delimiter", text=",", tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("data")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("rows_written")
        self.add_output("success")


class VisualReadJSONFileNode(VisualNode):
    """Visual representation of ReadJSONFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Read JSON File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Read JSON File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("success")


class VisualWriteJSONFileNode(VisualNode):
    """Visual representation of WriteJSONFileNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Write JSON File"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Write JSON File node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("indent", 2, widget_type=2, tab="config")
        self.add_text_input("encoding", "Encoding", text="utf-8", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_input("data")
        self.add_output("exec_out")
        self.add_output("success")


class VisualZipFilesNode(VisualNode):
    """Visual representation of ZipFilesNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Zip Files"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Zip Files node."""
        super().__init__()
        self.add_text_input("zip_path", "ZIP Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("zip_path")
        self.add_input("files")
        self.add_output("exec_out")
        self.add_output("zip_path")
        self.add_output("file_count")
        self.add_output("success")


class VisualUnzipFilesNode(VisualNode):
    """Visual representation of UnzipFilesNode."""

    __identifier__ = "casare_rpa.file"
    NODE_NAME = "Unzip Files"
    NODE_CATEGORY = "file_operations"
    CASARE_NODE_MODULE = "file"

    def __init__(self) -> None:
        """Initialize Unzip Files node."""
        super().__init__()
        self.add_text_input("zip_path", "ZIP Path", text="", tab="inputs")
        self.add_text_input("extract_to", "Extract To", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("zip_path")
        self.add_input("extract_to")
        self.add_output("exec_out")
        self.add_output("extract_to")
        self.add_output("files")
        self.add_output("file_count")
        self.add_output("success")


# =============================================================================
# Email Nodes
# =============================================================================

class VisualSendEmailNode(VisualNode):
    """Visual representation of SendEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Send Email"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Send Email node."""
        super().__init__()
        self.add_text_input("smtp_server", "SMTP Server", text="smtp.gmail.com", tab="connection")
        self.add_text_input("smtp_port", "SMTP Port", text="587", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("from_email", "From Email", text="", tab="email")
        self.add_text_input("to_email", "To Email", text="", tab="email")
        self.add_text_input("subject", "Subject", text="", tab="email")
        self.add_text_input("cc", "CC", text="", tab="email")
        self.add_text_input("bcc", "BCC", text="", tab="email")
        self.create_property("use_tls", True, widget_type=1, tab="config")
        self.create_property("is_html", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("to_email")
        self.add_input("subject")
        self.add_input("body")
        self.add_input("attachments")
        self.add_output("exec_out")
        self.add_output("success")
        self.add_output("message_id")


class VisualReadEmailsNode(VisualNode):
    """Visual representation of ReadEmailsNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Read Emails"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Read Emails node."""
        super().__init__()
        self.add_text_input("imap_server", "IMAP Server", text="imap.gmail.com", tab="connection")
        self.add_text_input("imap_port", "IMAP Port", text="993", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self.add_text_input("limit", "Limit", text="10", tab="config")
        self.add_combo_menu("search_criteria", "Search", items=[
            "ALL", "UNSEEN", "SEEN", "RECENT", "FLAGGED"
        ], tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("folder")
        self.add_input("limit")
        self.add_input("search_criteria")
        self.add_output("exec_out")
        self.add_output("emails")
        self.add_output("count")


class VisualGetEmailContentNode(VisualNode):
    """Visual representation of GetEmailContentNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Get Email Content"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Get Email Content node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email")
        self.add_output("exec_out")
        self.add_output("subject")
        self.add_output("from")
        self.add_output("to")
        self.add_output("date")
        self.add_output("body_text")
        self.add_output("body_html")
        self.add_output("attachments")


class VisualSaveAttachmentNode(VisualNode):
    """Visual representation of SaveAttachmentNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Save Attachment"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Save Attachment node."""
        super().__init__()
        self.add_text_input("imap_server", "IMAP Server", text="imap.gmail.com", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("save_path", "Save Path", text=".", tab="config")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_input("save_path")
        self.add_output("exec_out")
        self.add_output("saved_files")
        self.add_output("count")


class VisualFilterEmailsNode(VisualNode):
    """Visual representation of FilterEmailsNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Filter Emails"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Filter Emails node."""
        super().__init__()
        self.add_text_input("subject_contains", "Subject Contains", text="", tab="filters")
        self.add_text_input("from_contains", "From Contains", text="", tab="filters")
        self.create_property("has_attachments", False, widget_type=1, tab="filters")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("emails")
        self.add_input("subject_contains")
        self.add_input("from_contains")
        self.add_output("exec_out")
        self.add_output("filtered")
        self.add_output("count")


class VisualMarkEmailNode(VisualNode):
    """Visual representation of MarkEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Mark Email"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Mark Email node."""
        super().__init__()
        self.add_text_input("imap_server", "IMAP Server", text="imap.gmail.com", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self.add_combo_menu("mark_as", "Mark As", items=[
            "read", "unread", "flagged", "unflagged"
        ], tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_input("mark_as")
        self.add_output("exec_out")
        self.add_output("success")


class VisualDeleteEmailNode(VisualNode):
    """Visual representation of DeleteEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Delete Email"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Delete Email node."""
        super().__init__()
        self.add_text_input("imap_server", "IMAP Server", text="imap.gmail.com", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("folder", "Folder", text="INBOX", tab="config")
        self.create_property("permanent", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_output("exec_out")
        self.add_output("success")


class VisualMoveEmailNode(VisualNode):
    """Visual representation of MoveEmailNode."""

    __identifier__ = "casare_rpa.email"
    NODE_NAME = "Move Email"
    NODE_CATEGORY = "email"

    def __init__(self) -> None:
        """Initialize Move Email node."""
        super().__init__()
        self.add_text_input("imap_server", "IMAP Server", text="imap.gmail.com", tab="connection")
        self.add_text_input("username", "Username", text="", tab="connection")
        self.add_text_input("password", "Password", text="", tab="connection")
        self.add_text_input("source_folder", "Source Folder", text="INBOX", tab="config")
        self.add_text_input("target_folder", "Target Folder", text="", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("email_uid")
        self.add_input("target_folder")
        self.add_output("exec_out")
        self.add_output("success")


# =============================================================================
# Utility Nodes
# =============================================================================

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

class VisualExcelOpenNode(VisualNode):
    """Visual representation of ExcelOpenNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Open"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Open node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("show_window", True, widget_type=1, tab="config")
        self.create_property("read_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("workbook")
        self.add_output("success")


class VisualExcelReadCellNode(VisualNode):
    """Visual representation of ExcelReadCellNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Read Cell"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Read Cell node."""
        super().__init__()
        self.add_text_input("cell_address", "Cell Address", text="A1", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_input("cell_address")
        self.add_input("sheet_name")
        self.add_output("exec_out")
        self.add_output("value")
        self.add_output("success")


class VisualExcelWriteCellNode(VisualNode):
    """Visual representation of ExcelWriteCellNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Write Cell"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Write Cell node."""
        super().__init__()
        self.add_text_input("cell_address", "Cell Address", text="A1", tab="inputs")
        self.add_text_input("value", "Value", text="", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_input("cell_address")
        self.add_input("value")
        self.add_input("sheet_name")
        self.add_output("exec_out")
        self.add_output("success")


class VisualExcelGetRangeNode(VisualNode):
    """Visual representation of ExcelGetRangeNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Get Range"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Get Range node."""
        super().__init__()
        self.add_text_input("range_address", "Range Address", text="A1:B10", tab="inputs")
        self.add_text_input("sheet_name", "Sheet Name", text="Sheet1", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_input("range_address")
        self.add_input("sheet_name")
        self.add_output("exec_out")
        self.add_output("data")
        self.add_output("success")


class VisualExcelCloseNode(VisualNode):
    """Visual representation of ExcelCloseNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Excel Close"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Excel Close node."""
        super().__init__()
        self.create_property("save_changes", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("workbook")
        self.add_output("exec_out")
        self.add_output("success")


class VisualWordOpenNode(VisualNode):
    """Visual representation of WordOpenNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Open"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Open node."""
        super().__init__()
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.create_property("show_window", True, widget_type=1, tab="config")
        self.create_property("read_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("file_path")
        self.add_output("exec_out")
        self.add_output("document")
        self.add_output("success")


class VisualWordGetTextNode(VisualNode):
    """Visual representation of WordGetTextNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Get Text"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("document")
        self.add_output("exec_out")
        self.add_output("text")
        self.add_output("success")


class VisualWordReplaceTextNode(VisualNode):
    """Visual representation of WordReplaceTextNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Replace Text"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Replace Text node."""
        super().__init__()
        self.add_text_input("find_text", "Find Text", text="", tab="inputs")
        self.add_text_input("replace_text", "Replace Text", text="", tab="inputs")
        self.create_property("match_case", False, widget_type=1, tab="config")
        self.create_property("whole_word", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("document")
        self.add_input("find_text")
        self.add_input("replace_text")
        self.add_output("exec_out")
        self.add_output("replacements")
        self.add_output("success")


class VisualWordCloseNode(VisualNode):
    """Visual representation of WordCloseNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Word Close"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Word Close node."""
        super().__init__()
        self.create_property("save_changes", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("document")
        self.add_output("exec_out")
        self.add_output("success")


class VisualOutlookSendEmailNode(VisualNode):
    """Visual representation of OutlookSendEmailNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Send Email"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Send Email node."""
        super().__init__()
        self.add_text_input("to", "To", text="", tab="inputs")
        self.add_text_input("subject", "Subject", text="", tab="inputs")
        self.add_text_input("body", "Body", text="", tab="inputs")
        self.add_text_input("cc", "CC", text="", tab="inputs")
        self.add_text_input("bcc", "BCC", text="", tab="inputs")
        self.create_property("is_html", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("to")
        self.add_input("subject")
        self.add_input("body")
        self.add_input("attachments")
        self.add_output("exec_out")
        self.add_output("success")


class VisualOutlookReadEmailsNode(VisualNode):
    """Visual representation of OutlookReadEmailsNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Read Emails"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Read Emails node."""
        super().__init__()
        self.add_text_input("folder", "Folder", text="Inbox", tab="inputs")
        self.create_property("count", 10, widget_type=2, tab="config")
        self.create_property("unread_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("folder")
        self.add_output("exec_out")
        self.add_output("emails")
        self.add_output("count")
        self.add_output("success")


class VisualOutlookGetInboxCountNode(VisualNode):
    """Visual representation of OutlookGetInboxCountNode."""

    __identifier__ = "casare_rpa.office"
    NODE_NAME = "Outlook Get Inbox Count"
    NODE_CATEGORY = "office_automation"
    CASARE_NODE_MODULE = "office"

    def __init__(self) -> None:
        """Initialize Outlook Get Inbox Count node."""
        super().__init__()
        self.create_property("unread_only", False, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_output("exec_out")
        self.add_output("total_count")
        self.add_output("unread_count")
        self.add_output("success")


# Database Nodes

class VisualDatabaseConnectNode(VisualNode):
    """Visual representation of DatabaseConnectNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Database Connect"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Database Connect node."""
        super().__init__()
        self.add_combo_menu("db_type", "Database Type", items=["sqlite", "postgresql", "mysql"], tab="config")
        self.add_text_input("host", "Host", text="localhost", tab="inputs")
        self.create_property("port", 5432, widget_type=2, tab="inputs")
        self.add_text_input("database", "Database", text="", tab="inputs")
        self.add_text_input("username", "Username", text="", tab="inputs")
        self.add_text_input("password", "Password", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("db_type")
        self.add_input("host")
        self.add_input("database")
        self.add_input("username")
        self.add_input("password")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualExecuteQueryNode(VisualNode):
    """Visual representation of ExecuteQueryNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Query"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Execute Query node."""
        super().__init__()
        self.add_text_input("query", "SQL Query", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("query")
        self.add_input("parameters")
        self.add_output("exec_out")
        self.add_output("results")
        self.add_output("row_count")
        self.add_output("columns")
        self.add_output("success")
        self.add_output("error")


class VisualExecuteNonQueryNode(VisualNode):
    """Visual representation of ExecuteNonQueryNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Non-Query"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Execute Non-Query node."""
        super().__init__()
        self.add_text_input("query", "SQL Statement", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("query")
        self.add_input("parameters")
        self.add_output("exec_out")
        self.add_output("rows_affected")
        self.add_output("last_insert_id")
        self.add_output("success")
        self.add_output("error")


class VisualBeginTransactionNode(VisualNode):
    """Visual representation of BeginTransactionNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Begin Transaction"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Begin Transaction node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualCommitTransactionNode(VisualNode):
    """Visual representation of CommitTransactionNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Commit Transaction"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Commit Transaction node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualRollbackTransactionNode(VisualNode):
    """Visual representation of RollbackTransactionNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Rollback Transaction"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Rollback Transaction node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("connection")
        self.add_output("success")
        self.add_output("error")


class VisualCloseDatabaseNode(VisualNode):
    """Visual representation of CloseDatabaseNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Close Database"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Close Database node."""
        super().__init__()

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_output("exec_out")
        self.add_output("success")
        self.add_output("error")


class VisualTableExistsNode(VisualNode):
    """Visual representation of TableExistsNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Table Exists"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Table Exists node."""
        super().__init__()
        self.add_text_input("table_name", "Table Name", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("table_name")
        self.add_output("exec_out")
        self.add_output("exists")
        self.add_output("success")
        self.add_output("error")


class VisualGetTableColumnsNode(VisualNode):
    """Visual representation of GetTableColumnsNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Get Table Columns"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Get Table Columns node."""
        super().__init__()
        self.add_text_input("table_name", "Table Name", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("table_name")
        self.add_output("exec_out")
        self.add_output("columns")
        self.add_output("column_names")
        self.add_output("success")
        self.add_output("error")


class VisualExecuteBatchNode(VisualNode):
    """Visual representation of ExecuteBatchNode."""

    __identifier__ = "casare_rpa.database"
    NODE_NAME = "Execute Batch"
    NODE_CATEGORY = "database"
    CASARE_NODE_MODULE = "database_nodes"

    def __init__(self) -> None:
        """Initialize Execute Batch node."""
        super().__init__()
        self.create_property("stop_on_error", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("connection")
        self.add_input("statements")
        self.add_output("exec_out")
        self.add_output("results")
        self.add_output("total_rows_affected")
        self.add_output("success")
        self.add_output("error")


# HTTP/REST API Nodes

class VisualHttpRequestNode(VisualNode):
    """Visual representation of HttpRequestNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Request"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Request node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_combo_menu("method", "Method", items=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], tab="config")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")
        self.create_property("follow_redirects", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("headers")
        self.add_input("body")
        self.add_input("params")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("response_headers")
        self.add_output("success")
        self.add_output("error")


class VisualHttpGetNode(VisualNode):
    """Visual representation of HttpGetNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP GET"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP GET node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("params")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpPostNode(VisualNode):
    """Visual representation of HttpPostNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP POST"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP POST node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.add_combo_menu("content_type", "Content Type", items=["application/json", "application/x-www-form-urlencoded", "text/plain"], tab="config")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("body")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpPutNode(VisualNode):
    """Visual representation of HttpPutNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP PUT"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP PUT node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("body")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpPatchNode(VisualNode):
    """Visual representation of HttpPatchNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP PATCH"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP PATCH node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("body", "Body (JSON)", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("body")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualHttpDeleteNode(VisualNode):
    """Visual representation of HttpDeleteNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP DELETE"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP DELETE node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.create_property("timeout", 30.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualSetHttpHeadersNode(VisualNode):
    """Visual representation of SetHttpHeadersNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Set HTTP Headers"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize Set HTTP Headers node."""
        super().__init__()
        self.add_text_input("header_name", "Header Name", text="", tab="inputs")
        self.add_text_input("header_value", "Header Value", text="", tab="inputs")
        self.add_text_input("headers_json", "Headers (JSON)", text="{}", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("base_headers")
        self.add_input("header_name")
        self.add_input("header_value")
        self.add_output("exec_out")
        self.add_output("headers")


class VisualHttpAuthNode(VisualNode):
    """Visual representation of HttpAuthNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Auth"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Auth node."""
        super().__init__()
        self.add_combo_menu("auth_type", "Auth Type", items=["Bearer", "Basic", "ApiKey"], tab="config")
        self.add_text_input("token", "Token/API Key", text="", tab="inputs")
        self.add_text_input("username", "Username", text="", tab="inputs")
        self.add_text_input("password", "Password", text="", tab="inputs")
        self.add_text_input("api_key_name", "API Key Header", text="X-API-Key", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("token")
        self.add_input("username")
        self.add_input("password")
        self.add_input("base_headers")
        self.add_output("exec_out")
        self.add_output("headers")


class VisualParseJsonResponseNode(VisualNode):
    """Visual representation of ParseJsonResponseNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Parse JSON Response"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize Parse JSON Response node."""
        super().__init__()
        self.add_text_input("path", "JSON Path", text="", tab="inputs")
        self.add_text_input("default", "Default Value", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("json_data")
        self.add_input("path")
        self.add_input("default")
        self.add_output("exec_out")
        self.add_output("value")
        self.add_output("success")
        self.add_output("error")


class VisualHttpDownloadFileNode(VisualNode):
    """Visual representation of HttpDownloadFileNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Download File"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Download File node."""
        super().__init__()
        self.add_text_input("url", "URL", text="", tab="inputs")
        self.add_text_input("save_path", "Save Path", text="", tab="inputs")
        self.create_property("timeout", 300.0, widget_type=2, tab="config")
        self.create_property("overwrite", True, widget_type=1, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("save_path")
        self.add_input("headers")
        self.add_output("exec_out")
        self.add_output("file_path")
        self.add_output("file_size")
        self.add_output("success")
        self.add_output("error")


class VisualHttpUploadFileNode(VisualNode):
    """Visual representation of HttpUploadFileNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "HTTP Upload File"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize HTTP Upload File node."""
        super().__init__()
        self.add_text_input("url", "Upload URL", text="", tab="inputs")
        self.add_text_input("file_path", "File Path", text="", tab="inputs")
        self.add_text_input("field_name", "Field Name", text="file", tab="inputs")
        self.create_property("timeout", 300.0, widget_type=2, tab="config")
        self.create_property("verify_ssl", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("url")
        self.add_input("file_path")
        self.add_input("headers")
        self.add_input("extra_fields")
        self.add_output("exec_out")
        self.add_output("response_body")
        self.add_output("response_json")
        self.add_output("status_code")
        self.add_output("success")
        self.add_output("error")


class VisualBuildUrlNode(VisualNode):
    """Visual representation of BuildUrlNode."""

    __identifier__ = "casare_rpa.http"
    NODE_NAME = "Build URL"
    NODE_CATEGORY = "rest_api"
    CASARE_NODE_MODULE = "http_nodes"

    def __init__(self) -> None:
        """Initialize Build URL node."""
        super().__init__()
        self.add_text_input("base_url", "Base URL", text="", tab="inputs")
        self.add_text_input("path", "Path", text="", tab="inputs")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_input("exec_in")
        self.add_input("base_url")
        self.add_input("path")
        self.add_input("params")
        self.add_output("exec_out")
        self.add_output("url")


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

VISUAL_NODE_CLASSES = _get_visual_node_classes() + EXTENDED_VISUAL_NODE_CLASSES

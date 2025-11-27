"""Visual nodes for desktop_automation category."""
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

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
        # Modifier dropdown
        self.add_combo_menu("modifier", "Modifier", items=["none", "Ctrl", "Alt", "Shift", "Win"], tab="properties")
        # Key to send
        self.add_text_input("key", "Key", text="Enter", tab="properties")
        # Wait time after sending
        self.add_text_input("wait_time", "Wait Time (s)", text="0", tab="properties")
        # Override text (comma-separated keys) - overrides modifier + key if provided
        self.add_text_input("keys", "Custom Keys (overrides above)", placeholder_text="e.g., Ctrl,Alt,Delete", tab="advanced")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("keys", DataType.STRING)
        self.add_typed_input("wait_time", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)

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

class VisualDesktopWaitForElementNode(VisualNode):
    """Visual representation of desktop WaitForElementNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Wait For Desktop Element"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"
    CASARE_NODE_CLASS = "WaitForElementNode"

    def __init__(self) -> None:
        """Initialize Wait For Desktop Element node."""
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


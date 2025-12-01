"""Visual nodes for desktop_automation category."""

from casare_rpa.domain.value_objects.types import DataType
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
        self.add_text_input(
            "application_path", "Application Path", text="calc.exe", tab="inputs"
        )
        self.add_text_input("arguments", "Arguments", text="", tab="inputs")
        self.add_text_input(
            "working_directory", "Working Directory", text="", tab="inputs"
        )
        self.add_text_input(
            "window_title_hint", "Window Title Hint", text="", tab="config"
        )
        self.create_property("timeout", 10.0, widget_type=2, tab="config")
        self.create_property(
            "window_state",
            "normal",
            items=["normal", "maximized", "minimized"],
            widget_type=3,
            tab="config",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("application_path", DataType.STRING)
        self.add_typed_input("arguments", DataType.STRING)
        self.add_typed_input("working_directory", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("window", DataType.OBJECT)
        self.add_typed_output("process_id", DataType.INTEGER)
        self.add_typed_output("window_title", DataType.STRING)


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
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_typed_input("process_id", DataType.INTEGER)
        self.add_typed_input("window_title", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_typed_input("window_title", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("window", DataType.OBJECT)


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
        self.add_exec_input()
        self.add_exec_output()
        self.add_typed_output("window_list", DataType.LIST)
        self.add_typed_output("window_count", DataType.INTEGER)


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
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("element", DataType.OBJECT)
        self.add_typed_output("found", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("element", DataType.OBJECT)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("element", DataType.OBJECT)


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
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_typed_input("window_width", DataType.INTEGER)
        self.add_typed_input("window_height", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_typed_input("pos_x", DataType.INTEGER)
        self.add_typed_input("pos_y", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMaximizeWindowNode(VisualNode):
    """Visual representation of MaximizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Maximize Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMinimizeWindowNode(VisualNode):
    """Visual representation of MinimizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Minimize Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRestoreWindowNode(VisualNode):
    """Visual representation of RestoreWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Restore Window"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetWindowPropertiesNode(VisualNode):
    """Visual representation of GetWindowPropertiesNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Window Properties"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("properties", DataType.DICT)
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("x", DataType.INTEGER)
        self.add_typed_output("y", DataType.INTEGER)
        self.add_typed_output("width", DataType.INTEGER)
        self.add_typed_output("height", DataType.INTEGER)
        self.add_typed_output("state", DataType.STRING)
        self.add_typed_output("is_maximized", DataType.BOOLEAN)
        self.add_typed_output("is_minimized", DataType.BOOLEAN)


class VisualSetWindowStateNode(VisualNode):
    """Visual representation of SetWindowStateNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Set Window State"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Set Window State node."""
        super().__init__()
        self.create_property(
            "state",
            "normal",
            items=["normal", "maximized", "minimized"],
            widget_type=3,
            tab="config",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.OBJECT)
        self.add_typed_input("state", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("value", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSelectRadioButtonNode(VisualNode):
    """Visual representation of SelectRadioButtonNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select Radio Button"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("tab_control", DataType.OBJECT)
        self.add_typed_input("tab_name", DataType.STRING)
        self.add_typed_input("tab_index", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualScrollElementNode(VisualNode):
    """Visual representation of ScrollElementNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Scroll Element"
    NODE_CATEGORY = "desktop_automation"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Scroll Element node."""
        super().__init__()
        self.create_property(
            "direction",
            "down",
            items=["up", "down", "left", "right"],
            widget_type=3,
            tab="config",
        )
        self.create_property("amount", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("x", DataType.INTEGER)
        self.add_typed_input("y", DataType.INTEGER)
        self.add_typed_input("duration", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.create_property(
            "button",
            "left",
            items=["left", "right", "middle"],
            widget_type=3,
            tab="config",
        )
        self.create_property(
            "click_type",
            "single",
            items=["single", "double", "triple"],
            widget_type=3,
            tab="config",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("x", DataType.INTEGER)
        self.add_typed_input("y", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("keys", DataType.STRING)
        self.add_typed_input("interval", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_combo_menu(
            "modifier",
            "Modifier",
            items=["none", "Ctrl", "Alt", "Shift", "Win"],
            tab="properties",
        )
        # Key to send
        self.add_text_input("key", "Key", text="Enter", tab="properties")
        # Wait time after sending
        self.add_text_input("wait_time", "Wait Time (s)", text="0", tab="properties")
        # Override text (comma-separated keys) - overrides modifier + key if provided
        self.add_text_input(
            "keys",
            "Custom Keys (overrides above)",
            placeholder_text="e.g., Ctrl,Alt,Delete",
            tab="advanced",
        )

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
        self.add_exec_input()
        self.add_exec_output()
        self.add_typed_output("x", DataType.INTEGER)
        self.add_typed_output("y", DataType.INTEGER)


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
        self.create_property(
            "button",
            "left",
            items=["left", "right", "middle"],
            widget_type=3,
            tab="config",
        )
        self.create_property("duration", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("start_x", DataType.INTEGER)
        self.add_typed_input("start_y", DataType.INTEGER)
        self.add_typed_input("end_x", DataType.INTEGER)
        self.add_typed_input("end_y", DataType.INTEGER)
        self.add_typed_input("duration", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.create_property(
            "state",
            "visible",
            items=["visible", "hidden", "enabled", "disabled"],
            widget_type=3,
            tab="config",
        )
        self.create_property("poll_interval", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("selector", DataType.STRING)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("element", DataType.OBJECT)
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.create_property(
            "state", "visible", items=["visible", "hidden"], widget_type=3, tab="config"
        )
        self.create_property("poll_interval", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("title", DataType.STRING)
        self.add_typed_input("title_regex", DataType.STRING)
        self.add_typed_input("class_name", DataType.STRING)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("window", DataType.OBJECT)
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_exec_input()
        self.add_typed_input("selector", DataType.STRING)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("exists", DataType.BOOLEAN)
        self.add_typed_output("element", DataType.OBJECT)


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
        self.create_property(
            "comparison",
            "equals",
            items=[
                "equals",
                "contains",
                "startswith",
                "endswith",
                "regex",
                "greater",
                "less",
                "not_equals",
            ],
            widget_type=3,
            tab="config",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("property_name", DataType.STRING)
        self.add_typed_input("expected_value", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("result", DataType.BOOLEAN)
        self.add_typed_output("actual_value", DataType.STRING)


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
        self.create_property(
            "format", "PNG", items=["PNG", "JPEG", "BMP"], widget_type=3, tab="config"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("region", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("image", DataType.OBJECT)
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.create_property(
            "format", "PNG", items=["PNG", "JPEG", "BMP"], widget_type=3, tab="config"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.OBJECT)
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("padding", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("image", DataType.OBJECT)
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.add_combo_menu(
            "engine",
            "OCR Engine",
            items=["auto", "rapidocr", "tesseract", "winocr"],
            tab="config",
        )
        self.add_text_input("language", "Language", text="eng", tab="config")
        self.add_text_input("config", "Tesseract Config", text="", tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("image", DataType.OBJECT)
        self.add_typed_input("image_path", DataType.STRING)
        self.add_typed_input("region", DataType.OBJECT)
        self.add_exec_output()
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("engine_used", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


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
        self.create_property(
            "method",
            "histogram",
            items=["histogram", "ssim", "pixel"],
            widget_type=3,
            tab="config",
        )
        self.create_property("threshold", 0.9, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("image1", DataType.OBJECT)
        self.add_typed_input("image2", DataType.OBJECT)
        self.add_typed_input("image1_path", DataType.STRING)
        self.add_typed_input("image2_path", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("similarity", DataType.FLOAT)
        self.add_typed_output("is_match", DataType.BOOLEAN)
        self.add_typed_output("method", DataType.STRING)


# =============================================================================
# File System Nodes
# =============================================================================

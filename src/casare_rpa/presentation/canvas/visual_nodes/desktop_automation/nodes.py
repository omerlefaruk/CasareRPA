"""Visual nodes for desktop_automation category."""

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.presentation.canvas.graph.node_widgets import (
    NodeFilePathWidget,
    NodeDirectoryPathWidget,
)


def _replace_widget(node: VisualNode, widget) -> None:
    """
    Replace auto-generated widget with custom widget.

    If a property already exists (from @node_schema auto-generation),
    remove it first to avoid NodePropertyError conflicts.

    Args:
        node: The visual node
        widget: The custom widget to add (NodeFilePathWidget or NodeDirectoryPathWidget)
    """
    prop_name = widget._name  # NodeBaseWidget stores name as _name
    _remove_existing_property(node, prop_name)
    # Now safely add our custom widget
    node.add_custom_widget(widget)
    widget.setParentItem(node.view)


def _remove_existing_property(node: VisualNode, prop_name: str) -> None:
    """
    Remove an existing property if it was auto-generated from schema.

    Prevents NodePropertyError conflicts when adding custom widgets
    or text inputs that may already exist from @node_schema decoration.

    Args:
        node: The visual node
        prop_name: Name of property to remove if exists
    """
    # Remove from model's custom_properties if it exists
    if hasattr(node, "model") and prop_name in node.model.custom_properties:
        del node.model.custom_properties[prop_name]
        # Also remove from widgets dict if present
        if hasattr(node, "_widgets") and prop_name in node._widgets:
            del node._widgets[prop_name]


class VisualLaunchApplicationNode(VisualNode):
    """Visual representation of LaunchApplicationNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Launch Application"
    NODE_CATEGORY = "desktop_automation/application"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Launch Application node."""
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="application_path",
                label="Application",
                file_filter="Executables (*.exe);;All Files (*.*)",
                placeholder="Select application...",
                text="calc.exe",
            ),
        )
        # Remove auto-generated property before adding custom widget
        _remove_existing_property(self, "arguments")
        self._add_variable_aware_text_input(
            "arguments",
            "Arguments",
            text="",
            placeholder_text='e.g., --verbose -f "file.txt"',
            tab="inputs",
        )
        _replace_widget(
            self,
            NodeDirectoryPathWidget(
                name="working_directory",
                label="Working Directory",
                placeholder="Select working directory...",
            ),
        )
        # Remove auto-generated properties before adding custom widgets
        _remove_existing_property(self, "window_title_hint")
        self._add_variable_aware_text_input(
            "window_title_hint",
            "Window Title Hint",
            text="",
            placeholder_text="e.g., Untitled - Notepad",
            tab="config",
        )
        _remove_existing_property(self, "timeout")
        self._safe_create_property("timeout", 10.0, widget_type=2, tab="config")
        self._safe_create_property(
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
        self.add_typed_output("window", DataType.WINDOW)
        self.add_typed_output("process_id", DataType.INTEGER)
        self.add_typed_output("window_title", DataType.STRING)


class VisualCloseApplicationNode(VisualNode):
    """Visual representation of CloseApplicationNode.

    Widgets are auto-generated from the @node_schema on CloseApplicationNode.
    Schema provides: force_close, timeout properties.
    """

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Close Application"
    NODE_CATEGORY = "desktop_automation/application"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Close Application node."""
        super().__init__()
        # window_title is not in schema, add manually
        self._add_variable_aware_text_input(
            "window_title",
            "Window Title",
            text="",
            placeholder_text="e.g., Untitled - Notepad",
            tab="inputs",
        )
        # force_close and timeout are auto-generated from @node_schema

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_typed_input("process_id", DataType.INTEGER)
        self.add_typed_input("window_title", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualActivateWindowNode(VisualNode):
    """Visual representation of ActivateWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Activate Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Activate Window node."""
        super().__init__()
        self._add_variable_aware_text_input(
            "window_title",
            "Window Title",
            text="",
            placeholder_text="e.g., Chrome, Excel",
            tab="inputs",
        )
        self._safe_create_property("match_partial", True, widget_type=1, tab="config")
        self._safe_create_property("timeout", 5.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_typed_input("window_title", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("window", DataType.WINDOW)


class VisualGetWindowListNode(VisualNode):
    """Visual representation of GetWindowListNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Window List"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Get Window List node."""
        super().__init__()
        # Widgets auto-generated by @node_schema decorator

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
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Find Element node."""
        super().__init__()
        # Widgets auto-generated by @node_schema decorator

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_output("found", DataType.BOOLEAN)


class VisualClickElementDesktopNode(VisualNode):
    """Visual representation of ClickElementNode (Desktop)."""

    CASARE_NODE_CLASS = "ClickElementNode"

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Click Element (Desktop)"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Click Element node."""
        super().__init__()
        # Widgets auto-generated by @node_schema decorator

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualTypeTextDesktopNode(VisualNode):
    """Visual representation of TypeTextNode (Desktop)."""

    CASARE_NODE_CLASS = "TypeTextNode"

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Type Text (Desktop)"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Type Text node."""
        super().__init__()
        # Widgets auto-generated by @node_schema decorator

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetElementTextNode(VisualNode):
    """Visual representation of GetElementTextNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Element Text"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Get Element Text node."""
        super().__init__()
        # Widgets auto-generated by @node_schema decorator

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("element", DataType.DESKTOP_ELEMENT)


class VisualGetElementPropertyNode(VisualNode):
    """Visual representation of GetElementPropertyNode (Desktop)."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Element Property"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Get Element Property node."""
        super().__init__()
        # Widgets auto-generated by @node_schema decorator

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("element", DataType.DESKTOP_ELEMENT)


# Window Management Nodes


class VisualResizeWindowNode(VisualNode):
    """Visual representation of ResizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Resize Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Resize Window node."""
        super().__init__()
        # Use window_width/window_height to avoid conflict with reserved "width"/"height" properties
        self._safe_create_property("window_width", 800, widget_type=2, tab="config")
        self._safe_create_property("window_height", 600, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_typed_input("window_width", DataType.INTEGER)
        self.add_typed_input("window_height", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMoveWindowNode(VisualNode):
    """Visual representation of MoveWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Move Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Move Window node."""
        super().__init__()
        # Use pos_x/pos_y to avoid conflict with reserved "x"/"y" properties
        self._safe_create_property("pos_x", 100, widget_type=2, tab="config")
        self._safe_create_property("pos_y", 100, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_typed_input("pos_x", DataType.INTEGER)
        self.add_typed_input("pos_y", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMaximizeWindowNode(VisualNode):
    """Visual representation of MaximizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Maximize Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMinimizeWindowNode(VisualNode):
    """Visual representation of MinimizeWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Minimize Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRestoreWindowNode(VisualNode):
    """Visual representation of RestoreWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Restore Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetWindowPropertiesNode(VisualNode):
    """Visual representation of GetWindowPropertiesNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Get Window Properties"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
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
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Set Window State node."""
        super().__init__()
        self._safe_create_property(
            "state",
            "normal",
            items=["normal", "maximized", "minimized"],
            widget_type=3,
            tab="config",
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("window", DataType.WINDOW)
        self.add_typed_input("state", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


# Advanced Interaction Nodes


class VisualSelectFromDropdownNode(VisualNode):
    """Visual representation of SelectFromDropdownNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select From Dropdown"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Select From Dropdown node."""
        super().__init__()
        self._add_variable_aware_text_input(
            "value",
            "Value to Select",
            text="",
            placeholder_text="e.g., Option 1, USA",
            tab="inputs",
        )
        self._safe_create_property("by_text", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_input("value", DataType.STRING)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualCheckCheckboxNode(VisualNode):
    """Visual representation of CheckCheckboxNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Check Checkbox"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Check Checkbox node."""
        super().__init__()
        self._safe_create_property("check", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSelectRadioButtonNode(VisualNode):
    """Visual representation of SelectRadioButtonNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select Radio Button"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSelectTabNode(VisualNode):
    """Visual representation of SelectTabNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Select Tab"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Select Tab node."""
        super().__init__()
        self._add_variable_aware_text_input(
            "tab_name",
            "Tab Name",
            text="",
            placeholder_text="e.g., General, Settings",
            tab="inputs",
        )
        self._safe_create_property("tab_index", -1, widget_type=2, tab="config")

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
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Expand Tree Item node."""
        super().__init__()
        self._safe_create_property("expand", True, widget_type=1, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualScrollElementNode(VisualNode):
    """Visual representation of ScrollElementNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Scroll Element"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Scroll Element node."""
        super().__init__()
        self._safe_create_property(
            "direction",
            "down",
            items=["up", "down", "left", "right"],
            widget_type=3,
            tab="config",
        )
        self._safe_create_property("amount", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


# Mouse & Keyboard Control Nodes


class VisualMoveMouseNode(VisualNode):
    """Visual representation of MoveMouseNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Move Mouse"
    NODE_CATEGORY = "desktop_automation/input"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Move Mouse node."""
        super().__init__()
        self._safe_create_property("mouse_x", 0, widget_type=2, tab="config")
        self._safe_create_property("mouse_y", 0, widget_type=2, tab="config")
        self._safe_create_property("duration", 0.0, widget_type=2, tab="config")

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
    NODE_CATEGORY = "desktop_automation/input"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Mouse Click node."""
        super().__init__()
        self._safe_create_property("click_x", 0, widget_type=2, tab="config")
        self._safe_create_property("click_y", 0, widget_type=2, tab="config")
        self._safe_create_property(
            "button",
            "left",
            items=["left", "right", "middle"],
            widget_type=3,
            tab="config",
        )
        self._safe_create_property(
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
    """Visual representation of SendKeysNode.

    Widgets are auto-generated from the @node_schema on SendKeysNode.
    No __init__ override needed - schema provides: keys, interval, with_shift, etc.
    """

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Send Keys"
    NODE_CATEGORY = "desktop_automation/input"
    CASARE_NODE_MODULE = "desktop"

    # No __init__ needed - widgets auto-created from domain schema

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("keys", DataType.STRING)
        self.add_typed_input("interval", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSendHotKeyNode(VisualNode):
    """Visual representation of SendHotKeyNode.

    Widgets are auto-generated from the @node_schema on SendHotKeyNode:
    - modifier: Dropdown (none, Ctrl, Alt, Shift, Win)
    - key: Text input for main key
    - keys: Custom comma-separated keys override
    - wait_time: Delay after sending
    """

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Send Hotkey"
    NODE_CATEGORY = "desktop_automation/input"
    CASARE_NODE_MODULE = "desktop"

    # No __init__ needed - widgets auto-created from domain schema

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
    NODE_CATEGORY = "desktop_automation/input"
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
    NODE_CATEGORY = "desktop_automation/input"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Drag Mouse node."""
        super().__init__()
        self._safe_create_property("start_x", 0, widget_type=2, tab="config")
        self._safe_create_property("start_y", 0, widget_type=2, tab="config")
        self._safe_create_property("end_x", 100, widget_type=2, tab="config")
        self._safe_create_property("end_y", 100, widget_type=2, tab="config")
        self._safe_create_property(
            "button",
            "left",
            items=["left", "right", "middle"],
            widget_type=3,
            tab="config",
        )
        self._safe_create_property("duration", 0.5, widget_type=2, tab="config")

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
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"
    CASARE_NODE_CLASS = "WaitForElementNode"

    def __init__(self) -> None:
        """Initialize Wait For Desktop Element node."""
        super().__init__()
        self._safe_create_property("timeout", 10.0, widget_type=2, tab="config")
        self._safe_create_property(
            "state",
            "visible",
            items=["visible", "hidden", "enabled", "disabled"],
            widget_type=3,
            tab="config",
        )
        self._safe_create_property("poll_interval", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("selector", DataType.STRING)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWaitForWindowNode(VisualNode):
    """Visual representation of WaitForWindowNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Wait For Window"
    NODE_CATEGORY = "desktop_automation/window"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Wait For Window node."""
        super().__init__()
        self._add_variable_aware_text_input(
            "title",
            "Window Title",
            text="",
            placeholder_text="e.g., Untitled - Notepad",
            tab="inputs",
        )
        self._add_variable_aware_text_input(
            "title_regex",
            "Title Regex",
            text="",
            placeholder_text="e.g., .*Notepad.*",
            tab="inputs",
        )
        self._add_variable_aware_text_input(
            "class_name",
            "Class Name",
            text="",
            placeholder_text="e.g., Notepad, Chrome_WidgetWin_1",
            tab="inputs",
        )
        self._safe_create_property("timeout", 10.0, widget_type=2, tab="config")
        self._safe_create_property(
            "state", "visible", items=["visible", "hidden"], widget_type=3, tab="config"
        )
        self._safe_create_property("poll_interval", 0.5, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("title", DataType.STRING)
        self.add_typed_input("title_regex", DataType.STRING)
        self.add_typed_input("class_name", DataType.STRING)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("window", DataType.WINDOW)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualVerifyElementExistsNode(VisualNode):
    """Visual representation of VerifyElementExistsNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Verify Element Exists"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Verify Element Exists node."""
        super().__init__()
        self._safe_create_property("timeout", 0.0, widget_type=2, tab="config")

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("selector", DataType.STRING)
        self.add_typed_input("timeout", DataType.FLOAT)
        self.add_exec_output()
        self.add_typed_output("exists", DataType.BOOLEAN)
        self.add_typed_output("element", DataType.DESKTOP_ELEMENT)


class VisualVerifyElementPropertyNode(VisualNode):
    """Visual representation of VerifyElementPropertyNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "Verify Element Property"
    NODE_CATEGORY = "desktop_automation/element"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Verify Element Property node."""
        super().__init__()
        self._add_variable_aware_text_input(
            "property_name",
            "Property Name",
            text="Name",
            placeholder_text="e.g., Name, Value, IsEnabled",
            tab="inputs",
        )
        self._add_variable_aware_text_input(
            "expected_value",
            "Expected Value",
            text="",
            placeholder_text="e.g., Submit, true, 123",
            tab="inputs",
        )
        self._safe_create_property(
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
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
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
    NODE_CATEGORY = "desktop_automation/capture"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Capture Screenshot node."""
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="Save Path",
                file_filter="Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
                placeholder="Select save location...",
            ),
        )
        self._safe_create_property(
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
    NODE_CATEGORY = "desktop_automation/capture"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Capture Element Image node."""
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="file_path",
                label="Save Path",
                file_filter="Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
                placeholder="Select save location...",
            ),
        )
        self._safe_create_property("padding", 0, widget_type=2, tab="config")
        self._safe_create_property(
            "format", "PNG", items=["PNG", "JPEG", "BMP"], widget_type=3, tab="config"
        )

    def setup_ports(self) -> None:
        """Setup ports."""
        self.add_exec_input()
        self.add_typed_input("element", DataType.DESKTOP_ELEMENT)
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("padding", DataType.INTEGER)
        self.add_exec_output()
        self.add_typed_output("image", DataType.OBJECT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualOCRExtractTextNode(VisualNode):
    """Visual representation of OCRExtractTextNode."""

    __identifier__ = "casare_rpa.desktop"
    NODE_NAME = "OCR Extract Text"
    NODE_CATEGORY = "desktop_automation/capture"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize OCR Extract Text node."""
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="image_path",
                label="Image Path",
                file_filter="Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*.*)",
                placeholder="Select image file...",
            ),
        )
        self.add_combo_menu(
            "engine",
            "OCR Engine",
            items=["auto", "rapidocr", "tesseract", "winocr"],
            tab="config",
        )
        self._add_variable_aware_text_input(
            "language",
            "Language",
            text="eng",
            placeholder_text="e.g., eng, spa, fra, deu",
            tab="config",
        )
        self._add_variable_aware_text_input(
            "config",
            "Tesseract Config",
            text="",
            placeholder_text="e.g., --psm 6 --oem 3",
            tab="config",
        )

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
    NODE_CATEGORY = "desktop_automation/capture"
    CASARE_NODE_MODULE = "desktop"

    def __init__(self) -> None:
        """Initialize Compare Images node."""
        super().__init__()
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="image1_path",
                label="Image 1",
                file_filter="Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
                placeholder="Select first image...",
            ),
        )
        _replace_widget(
            self,
            NodeFilePathWidget(
                name="image2_path",
                label="Image 2",
                file_filter="Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
                placeholder="Select second image...",
            ),
        )
        self._safe_create_property(
            "method",
            "histogram",
            items=["histogram", "ssim", "pixel"],
            widget_type=3,
            tab="config",
        )
        self._safe_create_property("threshold", 0.9, widget_type=2, tab="config")

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

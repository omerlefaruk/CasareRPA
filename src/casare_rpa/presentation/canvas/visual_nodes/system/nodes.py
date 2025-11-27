"""Visual nodes for system category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.core.types import DataType

# Import logic layer nodes
from casare_rpa.nodes.system_nodes import (
    ClipboardCopyNode,
    ClipboardPasteNode,
    ClipboardClearNode,
    MessageBoxNode,
    InputDialogNode,
    TooltipNode,
    RunCommandNode,
    RunPowerShellNode,
    GetServiceStatusNode,
    StartServiceNode,
    StopServiceNode,
    RestartServiceNode,
    ListServicesNode,
)


# =============================================================================
# System Nodes - Clipboard
# =============================================================================


class VisualClipboardCopyNode(VisualNode):
    """Visual representation of ClipboardCopyNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Clipboard Copy"
    NODE_CATEGORY = "system"

    def get_node_class(self) -> type:
        return ClipboardCopyNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualClipboardPasteNode(VisualNode):
    """Visual representation of ClipboardPasteNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Clipboard Paste"
    NODE_CATEGORY = "system"

    def get_node_class(self) -> type:
        return ClipboardPasteNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)


class VisualClipboardClearNode(VisualNode):
    """Visual representation of ClipboardClearNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Clipboard Clear"
    NODE_CATEGORY = "system"

    def get_node_class(self) -> type:
        return ClipboardClearNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Dialogs
# =============================================================================


class VisualMessageBoxNode(VisualNode):
    """Visual representation of MessageBoxNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Message Box"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        # Basic properties
        self.add_text_input("title", "Title", text="Message", tab="properties")
        self.add_text_input("message", "Message", text="Hello!", tab="properties")
        self.add_combo_menu(
            "icon_type",
            "Icon",
            items=["information", "warning", "error", "question"],
            tab="properties",
        )
        self.add_combo_menu(
            "buttons",
            "Buttons",
            items=["ok", "ok_cancel", "yes_no", "yes_no_cancel"],
            tab="properties",
        )
        # Advanced options
        self.add_text_input(
            "detailed_text",
            "Detailed Text",
            placeholder_text="Expandable details...",
            tab="advanced",
        )
        self.add_combo_menu(
            "default_button",
            "Default Button",
            items=["", "ok", "cancel", "yes", "no"],
            tab="advanced",
        )
        self.add_checkbox("always_on_top", "Always On Top", state=True, tab="advanced")
        self.add_checkbox("play_sound", "Play Sound", state=False, tab="advanced")
        self.add_text_input(
            "auto_close_timeout",
            "Auto-Close (sec)",
            placeholder_text="0 = disabled",
            tab="advanced",
        )

    def get_node_class(self) -> type:
        return MessageBoxNode

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("message")
        self.add_output("exec_out")
        self.add_output("result")
        self.add_output("accepted")


class VisualInputDialogNode(VisualNode):
    """Visual representation of InputDialogNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Input Dialog"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("title", "Title", text="Input", tab="properties")
        self.add_text_input("default_value", "Default", text="", tab="properties")
        self.add_checkbox(
            "password_mode", "Password Mode", state=False, tab="properties"
        )

    def get_node_class(self) -> type:
        return InputDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("prompt", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("accepted", DataType.BOOLEAN)


class VisualTooltipNode(VisualNode):
    """Visual representation of TooltipNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Tooltip"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("title", "Title", text="Notification", tab="properties")
        self.add_text_input("duration", "Duration (s)", text="5", tab="properties")

    def get_node_class(self) -> type:
        return TooltipNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("shown", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Terminal
# =============================================================================


class VisualRunCommandNode(VisualNode):
    """Visual representation of RunCommandNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Run Command"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")
        self.add_checkbox("shell", "Use Shell", state=True, tab="properties")

    def get_node_class(self) -> type:
        return RunCommandNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("command", DataType.STRING)
        self.add_typed_input("working_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunPowerShellNode(VisualNode):
    """Visual representation of RunPowerShellNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Run PowerShell"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")

    def get_node_class(self) -> type:
        return RunPowerShellNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("script", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output", DataType.STRING)
        self.add_typed_output("error", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Windows Services
# =============================================================================


class VisualGetServiceStatusNode(VisualNode):
    """Visual representation of GetServiceStatusNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Get Service Status"
    NODE_CATEGORY = "system"

    def get_node_class(self) -> type:
        return GetServiceStatusNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("status", DataType.STRING)
        self.add_typed_output("is_running", DataType.BOOLEAN)
        self.add_typed_output("display_name", DataType.STRING)


class VisualStartServiceNode(VisualNode):
    """Visual representation of StartServiceNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Start Service"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")

    def get_node_class(self) -> type:
        return StartServiceNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("status", DataType.STRING)


class VisualStopServiceNode(VisualNode):
    """Visual representation of StopServiceNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Stop Service"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")

    def get_node_class(self) -> type:
        return StopServiceNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("status", DataType.STRING)


class VisualRestartServiceNode(VisualNode):
    """Visual representation of RestartServiceNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Restart Service"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="60", tab="properties")

    def get_node_class(self) -> type:
        return RestartServiceNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("status", DataType.STRING)


class VisualListServicesNode(VisualNode):
    """Visual representation of ListServicesNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "List Services"
    NODE_CATEGORY = "system"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu(
            "filter_status",
            "Filter",
            items=["all", "running", "stopped"],
            tab="properties",
        )

    def get_node_class(self) -> type:
        return ListServicesNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("services", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)

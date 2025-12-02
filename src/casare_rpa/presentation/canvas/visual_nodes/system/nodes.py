"""Visual nodes for system category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType

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
    NODE_CATEGORY = "system/clipboard"

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
    NODE_CATEGORY = "system/clipboard"

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
    NODE_CATEGORY = "system/clipboard"

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
    """Visual representation of MessageBoxNode.

    Widgets auto-generated from MessageBoxNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Message Box"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on MessageBoxNode

    def get_node_class(self) -> type:
        return MessageBoxNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("accepted", DataType.BOOLEAN)


class VisualInputDialogNode(VisualNode):
    """Visual representation of InputDialogNode.

    Widgets auto-generated from InputDialogNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Input Dialog"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on InputDialogNode

    def get_node_class(self) -> type:
        return InputDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("prompt", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("accepted", DataType.BOOLEAN)


class VisualTooltipNode(VisualNode):
    """Visual representation of TooltipNode.

    Widgets auto-generated from TooltipNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Tooltip"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on TooltipNode

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
    """Visual representation of RunCommandNode.

    Widgets auto-generated from RunCommandNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Run Command"
    NODE_CATEGORY = "system/terminal"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on RunCommandNode

    def get_node_class(self) -> type:
        return RunCommandNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("command", DataType.STRING)
        self.add_typed_input("args", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunPowerShellNode(VisualNode):
    """Visual representation of RunPowerShellNode.

    Widgets auto-generated from RunPowerShellNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Run PowerShell"
    NODE_CATEGORY = "system/terminal"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on RunPowerShellNode

    def get_node_class(self) -> type:
        return RunPowerShellNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("script", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Windows Services
# =============================================================================


class VisualGetServiceStatusNode(VisualNode):
    """Visual representation of GetServiceStatusNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Get Service Status"
    NODE_CATEGORY = "system/service"

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
    NODE_CATEGORY = "system/service"

    def get_node_class(self) -> type:
        return StartServiceNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("message", DataType.STRING)


class VisualStopServiceNode(VisualNode):
    """Visual representation of StopServiceNode."""

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Stop Service"
    NODE_CATEGORY = "system/service"

    def get_node_class(self) -> type:
        return StopServiceNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("message", DataType.STRING)


class VisualRestartServiceNode(VisualNode):
    """Visual representation of RestartServiceNode.

    Widgets auto-generated from RestartServiceNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Restart Service"
    NODE_CATEGORY = "system/service"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on RestartServiceNode

    def get_node_class(self) -> type:
        return RestartServiceNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("message", DataType.STRING)


class VisualListServicesNode(VisualNode):
    """Visual representation of ListServicesNode.

    Widgets auto-generated from ListServicesNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "List Services"
    NODE_CATEGORY = "system/service"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on ListServicesNode

    def get_node_class(self) -> type:
        return ListServicesNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("services", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)

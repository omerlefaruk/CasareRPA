"""Visual nodes for system category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType

# Import logic layer nodes
from casare_rpa.nodes.system import (
    ClipboardCopyNode,
    ClipboardPasteNode,
    ClipboardClearNode,
    MessageBoxNode,
    InputDialogNode,
    TooltipNode,
    SystemNotificationNode,
    ConfirmDialogNode,
    ProgressDialogNode,
    FilePickerDialogNode,
    FolderPickerDialogNode,
    ColorPickerDialogNode,
    DateTimePickerDialogNode,
    SnackbarNode,
    BalloonTipNode,
    RunCommandNode,
    RunPowerShellNode,
    GetServiceStatusNode,
    StartServiceNode,
    StopServiceNode,
    RestartServiceNode,
    ListServicesNode,
    # New dialog nodes
    ListPickerDialogNode,
    MultilineInputDialogNode,
    CredentialDialogNode,
    FormDialogNode,
    ImagePreviewDialogNode,
    TableDialogNode,
    WizardDialogNode,
    SplashScreenNode,
    AudioAlertNode,
    # System utilities
    ScreenRegionPickerNode,
    VolumeControlNode,
    ProcessListNode,
    ProcessKillNode,
    EnvironmentVariableNode,
    SystemInfoNode,
    # Quick nodes
    HotkeyWaitNode,
    BeepNode,
    ClipboardMonitorNode,
    # Utility system nodes
    FileWatcherNode,
    QRCodeNode,
    Base64Node,
    UUIDGeneratorNode,
    AssertSystemNode,
    LogToFileNode,
    # Media nodes
    TextToSpeechNode,
    PDFPreviewDialogNode,
    WebcamCaptureNode,
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
    Message property is essential (shows widget directly on node).
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
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSystemNotificationNode(VisualNode):
    """Visual representation of SystemNotificationNode.

    Widgets auto-generated from SystemNotificationNode's @node_schema decorator.
    Shows Windows system toast notifications.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "System Notification"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema on SystemNotificationNode

    def get_node_class(self) -> type:
        return SystemNotificationNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("title", DataType.STRING)
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("click_action", DataType.BOOLEAN)


class VisualConfirmDialogNode(VisualNode):
    """Visual representation of ConfirmDialogNode.

    Yes/No confirmation dialog with customizable buttons.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Confirm Dialog"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return ConfirmDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("confirmed", DataType.BOOLEAN)
        self.add_typed_output("button_clicked", DataType.STRING)


class VisualProgressDialogNode(VisualNode):
    """Visual representation of ProgressDialogNode.

    Shows progress bar during long operations.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Progress Dialog"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return ProgressDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("value", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("canceled", DataType.BOOLEAN)


class VisualFilePickerDialogNode(VisualNode):
    """Visual representation of FilePickerDialogNode.

    File selection dialog with filter and multi-select support.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "File Picker"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return FilePickerDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.ANY)
        self.add_typed_output("selected", DataType.BOOLEAN)


class VisualFolderPickerDialogNode(VisualNode):
    """Visual representation of FolderPickerDialogNode.

    Folder selection dialog.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Folder Picker"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return FolderPickerDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("folder_path", DataType.STRING)
        self.add_typed_output("selected", DataType.BOOLEAN)


class VisualColorPickerDialogNode(VisualNode):
    """Visual representation of ColorPickerDialogNode.

    Color selection dialog with optional alpha channel.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Color Picker"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return ColorPickerDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("color", DataType.STRING)
        self.add_typed_output("selected", DataType.BOOLEAN)
        self.add_typed_output("rgb", DataType.DICT)


class VisualDateTimePickerDialogNode(VisualNode):
    """Visual representation of DateTimePickerDialogNode.

    Date/time selection dialog with multiple modes.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "DateTime Picker"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return DateTimePickerDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("timestamp", DataType.INTEGER)
        self.add_typed_output("selected", DataType.BOOLEAN)


class VisualSnackbarNode(VisualNode):
    """Visual representation of SnackbarNode.

    Material-style bottom notification bar.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Snackbar"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return SnackbarNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("action_clicked", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualBalloonTipNode(VisualNode):
    """Visual representation of BalloonTipNode.

    Balloon tooltip anchored to screen position.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Balloon Tip"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return BalloonTipNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


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


# =============================================================================
# System Nodes - New Dialog Nodes
# =============================================================================


class VisualListPickerDialogNode(VisualNode):
    """Visual representation of ListPickerDialogNode.

    Single/multi-select list picker dialog.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "List Picker"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return ListPickerDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("items", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("selected", DataType.ANY)
        self.add_typed_output("confirmed", DataType.BOOLEAN)


class VisualMultilineInputDialogNode(VisualNode):
    """Visual representation of MultilineInputDialogNode.

    Multi-line text input dialog.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Multiline Input"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return MultilineInputDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("confirmed", DataType.BOOLEAN)
        self.add_typed_output("char_count", DataType.INTEGER)


class VisualCredentialDialogNode(VisualNode):
    """Visual representation of CredentialDialogNode.

    Username/password credential input dialog.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Credential Dialog"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return CredentialDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("username", DataType.STRING)
        self.add_typed_output("password", DataType.STRING)
        self.add_typed_output("remember", DataType.BOOLEAN)
        self.add_typed_output("confirmed", DataType.BOOLEAN)


class VisualFormDialogNode(VisualNode):
    """Visual representation of FormDialogNode.

    Custom form dialog with dynamic fields.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Form Dialog"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return FormDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("fields", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("data", DataType.DICT)
        self.add_typed_output("confirmed", DataType.BOOLEAN)


class VisualImagePreviewDialogNode(VisualNode):
    """Visual representation of ImagePreviewDialogNode.

    Image preview with zoom support.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Image Preview"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return ImagePreviewDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("image_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("confirmed", DataType.BOOLEAN)
        self.add_typed_output("canceled", DataType.BOOLEAN)


class VisualTableDialogNode(VisualNode):
    """Visual representation of TableDialogNode.

    Tabular data display dialog with optional row selection.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Table Dialog"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return TableDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("data", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("selected_row", DataType.ANY)
        self.add_typed_output("selected_index", DataType.INTEGER)
        self.add_typed_output("confirmed", DataType.BOOLEAN)


class VisualWizardDialogNode(VisualNode):
    """Visual representation of WizardDialogNode.

    Multi-step wizard dialog.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Wizard Dialog"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return WizardDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("steps", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("data", DataType.DICT)
        self.add_typed_output("completed", DataType.BOOLEAN)
        self.add_typed_output("canceled", DataType.BOOLEAN)
        self.add_typed_output("last_step", DataType.INTEGER)


class VisualSplashScreenNode(VisualNode):
    """Visual representation of SplashScreenNode.

    Splash screen with optional progress.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Splash Screen"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return SplashScreenNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualAudioAlertNode(VisualNode):
    """Visual representation of AudioAlertNode.

    Play audio file or system beep.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Audio Alert"
    NODE_CATEGORY = "system/dialog"

    def get_node_class(self) -> type:
        return AudioAlertNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# System Nodes - System Utilities
# =============================================================================


class VisualScreenRegionPickerNode(VisualNode):
    """Visual representation of ScreenRegionPickerNode.

    Interactive screen region selection.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Screen Region Picker"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return ScreenRegionPickerNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("x", DataType.INTEGER)
        self.add_typed_output("y", DataType.INTEGER)
        self.add_typed_output("width", DataType.INTEGER)
        self.add_typed_output("height", DataType.INTEGER)
        self.add_typed_output("confirmed", DataType.BOOLEAN)


class VisualVolumeControlNode(VisualNode):
    """Visual representation of VolumeControlNode.

    Get/set system volume.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Volume Control"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return VolumeControlNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("level", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("volume", DataType.INTEGER)
        self.add_typed_output("muted", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualProcessListNode(VisualNode):
    """Visual representation of ProcessListNode.

    List running processes.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Process List"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return ProcessListNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("filter_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("processes", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualProcessKillNode(VisualNode):
    """Visual representation of ProcessKillNode.

    Kill a process by PID or name.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Process Kill"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return ProcessKillNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("pid_or_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("killed_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualEnvironmentVariableNode(VisualNode):
    """Visual representation of EnvironmentVariableNode.

    Get/set environment variables.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Environment Variable"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return EnvironmentVariableNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("var_name", DataType.STRING)
        self.add_typed_input("value", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result_value", DataType.STRING)
        self.add_typed_output("exists", DataType.BOOLEAN)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSystemInfoNode(VisualNode):
    """Visual representation of SystemInfoNode.

    Get system information.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "System Info"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return SystemInfoNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("info", DataType.DICT)
        self.add_typed_output("os_name", DataType.STRING)
        self.add_typed_output("cpu_percent", DataType.FLOAT)
        self.add_typed_output("ram_percent", DataType.FLOAT)
        self.add_typed_output("disk_percent", DataType.FLOAT)


# =============================================================================
# System Nodes - Quick Nodes
# =============================================================================


class VisualHotkeyWaitNode(VisualNode):
    """Visual representation of HotkeyWaitNode.

    Wait for a specific hotkey combination.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Hotkey Wait"
    NODE_CATEGORY = "system/quick"

    def get_node_class(self) -> type:
        return HotkeyWaitNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("hotkey", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("triggered", DataType.BOOLEAN)
        self.add_typed_output("timed_out", DataType.BOOLEAN)


class VisualBeepNode(VisualNode):
    """Visual representation of BeepNode.

    Simple system beep.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Beep"
    NODE_CATEGORY = "system/quick"

    def get_node_class(self) -> type:
        return BeepNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("frequency", DataType.INTEGER)
        self.add_typed_input("duration", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualClipboardMonitorNode(VisualNode):
    """Visual representation of ClipboardMonitorNode.

    Monitor clipboard for changes.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Clipboard Monitor"
    NODE_CATEGORY = "system/quick"

    def get_node_class(self) -> type:
        return ClipboardMonitorNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("content", DataType.STRING)
        self.add_typed_output("changed", DataType.BOOLEAN)
        self.add_typed_output("timed_out", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Utility System Nodes
# =============================================================================


class VisualFileWatcherNode(VisualNode):
    """Visual representation of FileWatcherNode.

    Monitor file/folder for changes.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "File Watcher"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return FileWatcherNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("event_type", DataType.STRING)
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("triggered", DataType.BOOLEAN)
        self.add_typed_output("timed_out", DataType.BOOLEAN)


class VisualQRCodeNode(VisualNode):
    """Visual representation of QRCodeNode.

    Generate or read QR codes.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "QR Code"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return QRCodeNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("data", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualBase64Node(VisualNode):
    """Visual representation of Base64Node.

    Encode/decode base64 strings.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Base64"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return Base64Node

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("input_text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualUUIDGeneratorNode(VisualNode):
    """Visual representation of UUIDGeneratorNode.

    Generate UUIDs.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "UUID Generator"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return UUIDGeneratorNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("uuid", DataType.STRING)
        self.add_typed_output("uuids", DataType.LIST)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualAssertSystemNode(VisualNode):
    """Visual representation of AssertSystemNode.

    Validate conditions and optionally fail workflow.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Assert"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return AssertSystemNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("condition", DataType.ANY)
        self.add_typed_input("value", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("passed", DataType.BOOLEAN)
        self.add_typed_output("message", DataType.STRING)


class VisualLogToFileNode(VisualNode):
    """Visual representation of LogToFileNode.

    Write to custom log file.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Log to File"
    NODE_CATEGORY = "system/utility"

    def get_node_class(self) -> type:
        return LogToFileNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("log_message", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("lines_written", DataType.INTEGER)


# =============================================================================
# System Nodes - Media Nodes
# =============================================================================


class VisualTextToSpeechNode(VisualNode):
    """Visual representation of TextToSpeechNode.

    Read text aloud using text-to-speech.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Text to Speech"
    NODE_CATEGORY = "system/media"

    def get_node_class(self) -> type:
        return TextToSpeechNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualPDFPreviewDialogNode(VisualNode):
    """Visual representation of PDFPreviewDialogNode.

    Preview PDF with page navigation.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "PDF Preview"
    NODE_CATEGORY = "system/media"

    def get_node_class(self) -> type:
        return PDFPreviewDialogNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("confirmed", DataType.BOOLEAN)
        self.add_typed_output("current_page", DataType.INTEGER)
        self.add_typed_output("page_count", DataType.INTEGER)


class VisualWebcamCaptureNode(VisualNode):
    """Visual representation of WebcamCaptureNode.

    Capture image from webcam.
    Widgets auto-generated from @node_schema decorator.
    """

    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Webcam Capture"
    NODE_CATEGORY = "system/media"

    def get_node_class(self) -> type:
        return WebcamCaptureNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("image_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("width", DataType.INTEGER)
        self.add_typed_output("height", DataType.INTEGER)

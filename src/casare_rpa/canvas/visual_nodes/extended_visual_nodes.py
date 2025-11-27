"""
Visual nodes for extended functionality.

This module provides visual node classes for:
- Random operations
- DateTime operations
- Text operations
- System operations (Clipboard, Dialogs, Terminal, Services)
- Script execution
- XML operations
- PDF operations
- FTP operations
"""

from ...core.types import DataType
from .base_visual_node import VisualNode


# =============================================================================
# Random Nodes
# =============================================================================

class VisualRandomNumberNode(VisualNode):
    """Visual representation of RandomNumberNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random Number"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("min_value", "Min", text="0", tab="properties")
        self.add_text_input("max_value", "Max", text="100", tab="properties")
        self.add_checkbox("integer_only", "Integer Only", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("min_value", DataType.FLOAT)
        self.add_typed_input("max_value", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.FLOAT)


class VisualRandomChoiceNode(VisualNode):
    """Visual representation of RandomChoiceNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random Choice"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("count", "Count", text="1", tab="properties")
        self.add_checkbox("allow_duplicates", "Allow Duplicates", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("items", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("index", DataType.INTEGER)


class VisualRandomStringNode(VisualNode):
    """Visual representation of RandomStringNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random String"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("length", "Length", text="10", tab="properties")
        self.add_checkbox("include_uppercase", "Uppercase", state=True, tab="properties")
        self.add_checkbox("include_lowercase", "Lowercase", state=True, tab="properties")
        self.add_checkbox("include_digits", "Digits", state=True, tab="properties")
        self.add_checkbox("include_special", "Special", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("length", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualRandomUUIDNode(VisualNode):
    """Visual representation of RandomUUIDNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random UUID"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("format", "Format", items=["standard", "hex", "urn"], tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualShuffleListNode(VisualNode):
    """Visual representation of ShuffleListNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Shuffle List"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("items", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)


# =============================================================================
# DateTime Nodes
# =============================================================================

class VisualGetCurrentDateTimeNode(VisualNode):
    """Visual representation of GetCurrentDateTimeNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Get Current DateTime"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("format", "Format", text="%Y-%m-%d %H:%M:%S", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("datetime", DataType.STRING)
        self.add_typed_output("timestamp", DataType.FLOAT)
        self.add_typed_output("year", DataType.INTEGER)
        self.add_typed_output("month", DataType.INTEGER)
        self.add_typed_output("day", DataType.INTEGER)
        self.add_typed_output("hour", DataType.INTEGER)
        self.add_typed_output("minute", DataType.INTEGER)
        self.add_typed_output("second", DataType.INTEGER)
        self.add_typed_output("day_of_week", DataType.STRING)


class VisualFormatDateTimeNode(VisualNode):
    """Visual representation of FormatDateTimeNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Format DateTime"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("format", "Format", text="%Y-%m-%d", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("datetime", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualParseDateTimeNode(VisualNode):
    """Visual representation of ParseDateTimeNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Parse DateTime"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("format", "Format", text="%Y-%m-%d %H:%M:%S", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("datetime_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("year", DataType.INTEGER)
        self.add_typed_output("month", DataType.INTEGER)
        self.add_typed_output("day", DataType.INTEGER)
        self.add_typed_output("hour", DataType.INTEGER)
        self.add_typed_output("minute", DataType.INTEGER)
        self.add_typed_output("second", DataType.INTEGER)
        self.add_typed_output("timestamp", DataType.FLOAT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualDateTimeAddNode(VisualNode):
    """Visual representation of DateTimeAddNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "DateTime Add"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("datetime", DataType.ANY)
        self.add_typed_input("days", DataType.INTEGER)
        self.add_typed_input("hours", DataType.INTEGER)
        self.add_typed_input("minutes", DataType.INTEGER)
        self.add_typed_input("seconds", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("timestamp", DataType.FLOAT)


class VisualDateTimeDiffNode(VisualNode):
    """Visual representation of DateTimeDiffNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "DateTime Diff"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("datetime_1", DataType.ANY)
        self.add_typed_input("datetime_2", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("total_days", DataType.FLOAT)
        self.add_typed_output("total_hours", DataType.FLOAT)
        self.add_typed_output("total_minutes", DataType.FLOAT)
        self.add_typed_output("total_seconds", DataType.FLOAT)
        self.add_typed_output("days", DataType.INTEGER)
        self.add_typed_output("hours", DataType.INTEGER)
        self.add_typed_output("minutes", DataType.INTEGER)
        self.add_typed_output("seconds", DataType.INTEGER)


class VisualDateTimeCompareNode(VisualNode):
    """Visual representation of DateTimeCompareNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "DateTime Compare"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("datetime_1", DataType.ANY)
        self.add_typed_input("datetime_2", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("is_before", DataType.BOOLEAN)
        self.add_typed_output("is_after", DataType.BOOLEAN)
        self.add_typed_output("is_equal", DataType.BOOLEAN)
        self.add_typed_output("comparison", DataType.INTEGER)


class VisualGetTimestampNode(VisualNode):
    """Visual representation of GetTimestampNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Get Timestamp"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("milliseconds", "Milliseconds", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("timestamp", DataType.FLOAT)


# =============================================================================
# Text Nodes
# =============================================================================

class VisualTextSplitNode(VisualNode):
    """Visual representation of TextSplitNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Split"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("max_split", "Max Splits", text="-1", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("separator", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualTextReplaceNode(VisualNode):
    """Visual representation of TextReplaceNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Replace"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("use_regex", "Use Regex", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("old_value", DataType.STRING)
        self.add_typed_input("new_value", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("replacements", DataType.INTEGER)


class VisualTextTrimNode(VisualNode):
    """Visual representation of TextTrimNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Trim"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("mode", "Mode", items=["both", "left", "right"], tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextCaseNode(VisualNode):
    """Visual representation of TextCaseNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Case"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("case", "Case", items=["lower", "upper", "title", "capitalize", "swapcase"], tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextPadNode(VisualNode):
    """Visual representation of TextPadNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Pad"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("mode", "Mode", items=["left", "right", "center"], tab="properties")
        self.add_text_input("fill_char", "Fill Char", text=" ", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("length", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextSubstringNode(VisualNode):
    """Visual representation of TextSubstringNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Substring"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("start", DataType.INTEGER)
        self.add_typed_input("end", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("length", DataType.INTEGER)


class VisualTextContainsNode(VisualNode):
    """Visual representation of TextContainsNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Contains"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("case_sensitive", "Case Sensitive", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("search", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("contains", DataType.BOOLEAN)
        self.add_typed_output("position", DataType.INTEGER)
        self.add_typed_output("count", DataType.INTEGER)


class VisualTextStartsWithNode(VisualNode):
    """Visual representation of TextStartsWithNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Starts With"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("case_sensitive", "Case Sensitive", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("prefix", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.BOOLEAN)


class VisualTextEndsWithNode(VisualNode):
    """Visual representation of TextEndsWithNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Ends With"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("case_sensitive", "Case Sensitive", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("suffix", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.BOOLEAN)


class VisualTextLinesNode(VisualNode):
    """Visual representation of TextLinesNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Lines"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("mode", "Mode", items=["split", "join"], tab="properties")
        self.add_checkbox("keep_ends", "Keep Line Endings", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("input", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("count", DataType.INTEGER)


class VisualTextReverseNode(VisualNode):
    """Visual representation of TextReverseNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Reverse"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextCountNode(VisualNode):
    """Visual representation of TextCountNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Count"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("mode", "Mode", items=["characters", "words", "lines"], tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("characters", DataType.INTEGER)
        self.add_typed_output("words", DataType.INTEGER)
        self.add_typed_output("lines", DataType.INTEGER)


class VisualTextJoinNode(VisualNode):
    """Visual representation of TextJoinNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Join"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("items", DataType.LIST)
        self.add_typed_input("separator", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextExtractNode(VisualNode):
    """Visual representation of TextExtractNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Extract"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("all_matches", "All Matches", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("pattern", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("match", DataType.ANY)
        self.add_typed_output("groups", DataType.LIST)
        self.add_typed_output("found", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Clipboard
# =============================================================================

class VisualClipboardCopyNode(VisualNode):
    """Visual representation of ClipboardCopyNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Clipboard Copy"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualClipboardPasteNode(VisualNode):
    """Visual representation of ClipboardPasteNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Clipboard Paste"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)


class VisualClipboardClearNode(VisualNode):
    """Visual representation of ClipboardClearNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Clipboard Clear"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# System Nodes - Dialogs
# =============================================================================

class VisualMessageBoxNode(VisualNode):
    """Visual representation of MessageBoxNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Message Box"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        # Basic properties
        self.add_text_input("title", "Title", text="Message", tab="properties")
        self.add_text_input("message", "Message", text="Hello!", tab="properties")
        self.add_combo_menu("icon_type", "Icon", items=["information", "warning", "error", "question"], tab="properties")
        self.add_combo_menu("buttons", "Buttons", items=["ok", "ok_cancel", "yes_no", "yes_no_cancel"], tab="properties")
        # Advanced options
        self.add_text_input("detailed_text", "Detailed Text", placeholder_text="Expandable details...", tab="advanced")
        self.add_combo_menu("default_button", "Default Button", items=["", "ok", "cancel", "yes", "no"], tab="advanced")
        self.add_checkbox("always_on_top", "Always On Top", state=True, tab="advanced")
        self.add_checkbox("play_sound", "Play Sound", state=False, tab="advanced")
        self.add_text_input("auto_close_timeout", "Auto-Close (sec)", placeholder_text="0 = disabled", tab="advanced")

    def setup_ports(self) -> None:
        self.add_input("exec_in")
        self.add_input("message")
        self.add_output("exec_out")
        self.add_output("result")
        self.add_output("accepted")


class VisualInputDialogNode(VisualNode):
    """Visual representation of InputDialogNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Input Dialog"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("title", "Title", text="Input", tab="properties")
        self.add_text_input("default_value", "Default", text="", tab="properties")
        self.add_checkbox("password_mode", "Password Mode", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("prompt", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("accepted", DataType.BOOLEAN)


class VisualTooltipNode(VisualNode):
    """Visual representation of TooltipNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Tooltip"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("title", "Title", text="Notification", tab="properties")
        self.add_text_input("duration", "Duration (s)", text="5", tab="properties")

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

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Run Command"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")
        self.add_checkbox("shell", "Use Shell", state=True, tab="properties")

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

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Run PowerShell"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")

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

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Get Service Status"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("status", DataType.STRING)
        self.add_typed_output("is_running", DataType.BOOLEAN)
        self.add_typed_output("display_name", DataType.STRING)


class VisualStartServiceNode(VisualNode):
    """Visual representation of StartServiceNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Start Service"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("status", DataType.STRING)


class VisualStopServiceNode(VisualNode):
    """Visual representation of StopServiceNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Stop Service"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("status", DataType.STRING)


class VisualRestartServiceNode(VisualNode):
    """Visual representation of RestartServiceNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Restart Service"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="60", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("service_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("status", DataType.STRING)


class VisualListServicesNode(VisualNode):
    """Visual representation of ListServicesNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "List Services"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("filter_status", "Filter", items=["all", "running", "stopped"], tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("services", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


# =============================================================================
# Script Nodes
# =============================================================================

class VisualRunPythonScriptNode(VisualNode):
    """Visual representation of RunPythonScriptNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Run Python Script"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("code", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("output", DataType.STRING)
        self.add_typed_output("error", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunPythonFileNode(VisualNode):
    """Visual representation of RunPythonFileNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Run Python File"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="300", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("args", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualEvalExpressionNode(VisualNode):
    """Visual representation of EvalExpressionNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Eval Expression"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("expression", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("type", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunBatchScriptNode(VisualNode):
    """Visual representation of RunBatchScriptNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Run Batch Script"
    NODE_CATEGORY = "utility"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("timeout", "Timeout (s)", text="300", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("script", DataType.STRING)
        self.add_typed_input("working_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("stdout", DataType.STRING)
        self.add_typed_output("stderr", DataType.STRING)
        self.add_typed_output("return_code", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualRunJavaScriptNode(VisualNode):
    """Visual representation of RunJavaScriptNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Run JavaScript"
    NODE_CATEGORY = "utility"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("code", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("output", DataType.STRING)
        self.add_typed_output("error", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# XML Nodes
# =============================================================================

class VisualParseXMLNode(VisualNode):
    """Visual representation of ParseXMLNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Parse XML"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("root_tag", DataType.STRING)
        self.add_typed_output("child_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualReadXMLFileNode(VisualNode):
    """Visual representation of ReadXMLFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read XML File"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("xml_string", DataType.STRING)
        self.add_typed_output("root_tag", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualWriteXMLFileNode(VisualNode):
    """Visual representation of WriteXMLFileNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Write XML File"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("pretty_print", "Pretty Print", state=True, tab="properties")
        self.add_checkbox("xml_declaration", "XML Declaration", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("file_path", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualXPathQueryNode(VisualNode):
    """Visual representation of XPathQueryNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "XPath Query"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_typed_input("xpath", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("results", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("first_text", DataType.STRING)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetXMLElementNode(VisualNode):
    """Visual representation of GetXMLElementNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get XML Element"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_typed_input("tag_name", DataType.STRING)
        self.add_typed_input("index", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("tag", DataType.STRING)
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("attributes", DataType.DICT)
        self.add_typed_output("child_count", DataType.INTEGER)
        self.add_typed_output("found", DataType.BOOLEAN)


class VisualGetXMLAttributeNode(VisualNode):
    """Visual representation of GetXMLAttributeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get XML Attribute"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_typed_input("xpath", DataType.STRING)
        self.add_typed_input("attribute_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("value", DataType.STRING)
        self.add_typed_output("found", DataType.BOOLEAN)


class VisualXMLToJsonNode(VisualNode):
    """Visual representation of XMLToJsonNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "XML To JSON"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("include_attributes", "Include Attributes", state=True, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("xml_string", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("json_data", DataType.DICT)
        self.add_typed_output("json_string", DataType.STRING)


class VisualJsonToXMLNode(VisualNode):
    """Visual representation of JsonToXMLNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "JSON To XML"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("root_tag", "Root Tag", text="root", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("json_data", DataType.ANY)
        self.add_exec_output("exec_out")
        self.add_typed_output("xml_string", DataType.STRING)


# =============================================================================
# PDF Nodes
# =============================================================================

class VisualReadPDFTextNode(VisualNode):
    """Visual representation of ReadPDFTextNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Read PDF Text"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("start_page", "Start Page", text="", tab="properties")
        self.add_text_input("end_page", "End Page", text="", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("text", DataType.STRING)
        self.add_typed_output("pages", DataType.LIST)
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualGetPDFInfoNode(VisualNode):
    """Visual representation of GetPDFInfoNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Get PDF Info"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("title", DataType.STRING)
        self.add_typed_output("author", DataType.STRING)
        self.add_typed_output("subject", DataType.STRING)
        self.add_typed_output("creator", DataType.STRING)
        self.add_typed_output("metadata", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualMergePDFsNode(VisualNode):
    """Visual representation of MergePDFsNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Merge PDFs"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("input_files", DataType.LIST)
        self.add_typed_input("output_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_path", DataType.STRING)
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualSplitPDFNode(VisualNode):
    """Visual representation of SplitPDFNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Split PDF"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input("pages_per_file", "Pages Per File", text="1", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("output_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_files", DataType.LIST)
        self.add_typed_output("file_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualExtractPDFPagesNode(VisualNode):
    """Visual representation of ExtractPDFPagesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "Extract PDF Pages"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("pages", DataType.LIST)
        self.add_typed_input("output_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_path", DataType.STRING)
        self.add_typed_output("page_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


class VisualPDFToImagesNode(VisualNode):
    """Visual representation of PDFToImagesNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "PDF To Images"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu("format", "Format", items=["png", "jpeg", "jpg"], tab="properties")
        self.add_text_input("dpi", "DPI", text="200", tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("file_path", DataType.STRING)
        self.add_typed_input("output_dir", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("image_paths", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)


# =============================================================================
# FTP Nodes
# =============================================================================

class VisualFTPConnectNode(VisualNode):
    """Visual representation of FTPConnectNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Connect"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("passive", "Passive Mode", state=True, tab="properties")
        self.add_checkbox("use_tls", "Use TLS", state=False, tab="properties")
        self.add_text_input("timeout", "Timeout (s)", text="30", tab="properties")
        # Retry options
        self.add_text_input("retry_count", "Retry Count", placeholder_text="0", tab="advanced")
        self.add_text_input("retry_interval", "Retry Interval (s)", placeholder_text="2.0", tab="advanced")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("host", DataType.STRING)
        self.add_typed_input("port", DataType.INTEGER)
        self.add_typed_input("username", DataType.STRING)
        self.add_typed_input("password", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("connected", DataType.BOOLEAN)
        self.add_typed_output("server_message", DataType.STRING)


class VisualFTPUploadNode(VisualNode):
    """Visual representation of FTPUploadNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Upload"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("binary_mode", "Binary Mode", state=True, tab="properties")
        self.add_checkbox("create_dirs", "Create Dirs", state=False, tab="properties")
        # Retry options
        self.add_text_input("retry_count", "Retry Count", placeholder_text="0", tab="advanced")
        self.add_text_input("retry_interval", "Retry Interval (s)", placeholder_text="2.0", tab="advanced")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("local_path", DataType.STRING)
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("uploaded", DataType.BOOLEAN)
        self.add_typed_output("bytes_sent", DataType.INTEGER)


class VisualFTPDownloadNode(VisualNode):
    """Visual representation of FTPDownloadNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Download"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("binary_mode", "Binary Mode", state=True, tab="properties")
        self.add_checkbox("overwrite", "Overwrite", state=False, tab="properties")
        # Retry options
        self.add_text_input("retry_count", "Retry Count", placeholder_text="0", tab="advanced")
        self.add_text_input("retry_interval", "Retry Interval (s)", placeholder_text="2.0", tab="advanced")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_typed_input("local_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("downloaded", DataType.BOOLEAN)
        self.add_typed_output("bytes_received", DataType.INTEGER)


class VisualFTPListNode(VisualNode):
    """Visual representation of FTPListNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP List"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("detailed", "Detailed", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("items", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualFTPDeleteNode(VisualNode):
    """Visual representation of FTPDeleteNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Delete"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("deleted", DataType.BOOLEAN)


class VisualFTPMakeDirNode(VisualNode):
    """Visual representation of FTPMakeDirNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Make Dir"
    NODE_CATEGORY = "file_operations"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox("parents", "Create Parents", state=False, tab="properties")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("created", DataType.BOOLEAN)


class VisualFTPRemoveDirNode(VisualNode):
    """Visual representation of FTPRemoveDirNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Remove Dir"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("removed", DataType.BOOLEAN)


class VisualFTPRenameNode(VisualNode):
    """Visual representation of FTPRenameNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Rename"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("old_path", DataType.STRING)
        self.add_typed_input("new_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("renamed", DataType.BOOLEAN)


class VisualFTPDisconnectNode(VisualNode):
    """Visual representation of FTPDisconnectNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Disconnect"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("disconnected", DataType.BOOLEAN)


class VisualFTPGetSizeNode(VisualNode):
    """Visual representation of FTPGetSizeNode."""

    __identifier__ = "casare_rpa.file_operations"
    NODE_NAME = "FTP Get Size"
    NODE_CATEGORY = "file_operations"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("remote_path", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("size", DataType.INTEGER)
        self.add_typed_output("found", DataType.BOOLEAN)


# =============================================================================
# List of all visual node classes for auto-discovery
# =============================================================================

EXTENDED_VISUAL_NODE_CLASSES = [
    # Random
    VisualRandomNumberNode,
    VisualRandomChoiceNode,
    VisualRandomStringNode,
    VisualRandomUUIDNode,
    VisualShuffleListNode,
    # DateTime
    VisualGetCurrentDateTimeNode,
    VisualFormatDateTimeNode,
    VisualParseDateTimeNode,
    VisualDateTimeAddNode,
    VisualDateTimeDiffNode,
    VisualDateTimeCompareNode,
    VisualGetTimestampNode,
    # Text
    VisualTextSplitNode,
    VisualTextReplaceNode,
    VisualTextTrimNode,
    VisualTextCaseNode,
    VisualTextPadNode,
    VisualTextSubstringNode,
    VisualTextContainsNode,
    VisualTextStartsWithNode,
    VisualTextEndsWithNode,
    VisualTextLinesNode,
    VisualTextReverseNode,
    VisualTextCountNode,
    VisualTextJoinNode,
    VisualTextExtractNode,
    # Clipboard
    VisualClipboardCopyNode,
    VisualClipboardPasteNode,
    VisualClipboardClearNode,
    # Dialogs
    VisualMessageBoxNode,
    VisualInputDialogNode,
    VisualTooltipNode,
    # Terminal
    VisualRunCommandNode,
    VisualRunPowerShellNode,
    # Windows Services
    VisualGetServiceStatusNode,
    VisualStartServiceNode,
    VisualStopServiceNode,
    VisualRestartServiceNode,
    VisualListServicesNode,
    # Script
    VisualRunPythonScriptNode,
    VisualRunPythonFileNode,
    VisualEvalExpressionNode,
    VisualRunBatchScriptNode,
    VisualRunJavaScriptNode,
    # XML
    VisualParseXMLNode,
    VisualReadXMLFileNode,
    VisualWriteXMLFileNode,
    VisualXPathQueryNode,
    VisualGetXMLElementNode,
    VisualGetXMLAttributeNode,
    VisualXMLToJsonNode,
    VisualJsonToXMLNode,
    # PDF
    VisualReadPDFTextNode,
    VisualGetPDFInfoNode,
    VisualMergePDFsNode,
    VisualSplitPDFNode,
    VisualExtractPDFPagesNode,
    VisualPDFToImagesNode,
    # FTP
    VisualFTPConnectNode,
    VisualFTPUploadNode,
    VisualFTPDownloadNode,
    VisualFTPListNode,
    VisualFTPDeleteNode,
    VisualFTPMakeDirNode,
    VisualFTPRemoveDirNode,
    VisualFTPRenameNode,
    VisualFTPDisconnectNode,
    VisualFTPGetSizeNode,
]

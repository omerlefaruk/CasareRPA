"""Visual nodes for utility category."""

from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
from casare_rpa.domain.value_objects.types import DataType


# =============================================================================
# Random Nodes
# =============================================================================


class VisualRandomNumberNode(VisualNode):
    """Visual representation of RandomNumberNode.

    Widgets are auto-generated from RandomNumberNode's @node_schema decorator.
    min_value/max_value are input ports, not schema properties.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random Number"
    NODE_CATEGORY = "utility/random"

    def __init__(self) -> None:
        super().__init__()
        # min_value and max_value are NOT in schema, they're port inputs
        self.add_text_input("min_value", "Min", text="0", tab="properties")
        self.add_text_input("max_value", "Max", text="100", tab="properties")
        # integer_only IS in schema - auto-generated

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("min_value", DataType.FLOAT)
        self.add_typed_input("max_value", DataType.FLOAT)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.FLOAT)


class VisualRandomChoiceNode(VisualNode):
    """Visual representation of RandomChoiceNode.

    Widgets are auto-generated from RandomChoiceNode's @node_schema decorator.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random Choice"
    NODE_CATEGORY = "utility/random"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("items", DataType.LIST)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.ANY)
        self.add_typed_output("index", DataType.INTEGER)


class VisualRandomStringNode(VisualNode):
    """Visual representation of RandomStringNode.

    Widgets are auto-generated from RandomStringNode's @node_schema decorator.
    length is an input port, not a schema property.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random String"
    NODE_CATEGORY = "utility/random"

    def __init__(self) -> None:
        super().__init__()
        # length is NOT in schema, it's a port input
        self.add_text_input("length", "Length", text="10", tab="properties")
        # include_uppercase, include_lowercase, include_digits, include_special
        # ARE in schema - auto-generated

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("length", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualRandomUUIDNode(VisualNode):
    """Visual representation of RandomUUIDNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Random UUID"
    NODE_CATEGORY = "utility/random"

    def __init__(self) -> None:
        super().__init__()
        self.add_combo_menu(
            "format", "Format", items=["standard", "hex", "urn"], tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualShuffleListNode(VisualNode):
    """Visual representation of ShuffleListNode."""

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Shuffle List"
    NODE_CATEGORY = "utility/random"

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
    NODE_CATEGORY = "utility/datetime"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "format", "Format", text="%Y-%m-%d %H:%M:%S", tab="properties"
        )

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
    NODE_CATEGORY = "utility/datetime"

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
    NODE_CATEGORY = "utility/datetime"

    def __init__(self) -> None:
        super().__init__()
        self.add_text_input(
            "format", "Format", text="%Y-%m-%d %H:%M:%S", tab="properties"
        )

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
    NODE_CATEGORY = "utility/datetime"

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
    NODE_CATEGORY = "utility/datetime"

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
    NODE_CATEGORY = "utility/datetime"

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
    NODE_CATEGORY = "utility/datetime"

    def __init__(self) -> None:
        super().__init__()
        self.add_checkbox(
            "milliseconds", label="", text="Milliseconds", state=False, tab="properties"
        )

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_output("timestamp", DataType.FLOAT)


# =============================================================================
# Text Nodes
# =============================================================================


class VisualTextSplitNode(VisualNode):
    """Visual representation of TextSplitNode.

    Widgets are auto-generated from TextSplitNode's @node_schema decorator.
    max_split property is defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Split"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("separator", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.LIST)
        self.add_typed_output("count", DataType.INTEGER)


class VisualTextReplaceNode(VisualNode):
    """Visual representation of TextReplaceNode.

    Widgets are auto-generated from TextReplaceNode's @node_schema decorator.
    use_regex, ignore_case, multiline, dotall properties are defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Replace"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("old_value", DataType.STRING)
        self.add_typed_input("new_value", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("replacements", DataType.INTEGER)


class VisualTextTrimNode(VisualNode):
    """Visual representation of TextTrimNode.

    Widgets are auto-generated from TextTrimNode's @node_schema decorator.
    mode and characters properties are defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Trim"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextCaseNode(VisualNode):
    """Visual representation of TextCaseNode.

    Widgets are auto-generated from TextCaseNode's @node_schema decorator.
    case property is defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Case"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextPadNode(VisualNode):
    """Visual representation of TextPadNode.

    Widgets are auto-generated from TextPadNode's @node_schema decorator.
    mode and fill_char properties are defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Pad"
    NODE_CATEGORY = "utility/text"

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
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("start", DataType.INTEGER)
        self.add_typed_input("end", DataType.INTEGER)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)
        self.add_typed_output("length", DataType.INTEGER)


class VisualTextContainsNode(VisualNode):
    """Visual representation of TextContainsNode.

    Widgets are auto-generated from TextContainsNode's @node_schema decorator.
    case_sensitive property is defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Contains"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("search", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("contains", DataType.BOOLEAN)
        self.add_typed_output("position", DataType.INTEGER)
        self.add_typed_output("count", DataType.INTEGER)


class VisualTextStartsWithNode(VisualNode):
    """Visual representation of TextStartsWithNode.

    Widgets are auto-generated from TextStartsWithNode's @node_schema decorator.
    case_sensitive property is defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Starts With"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("prefix", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.BOOLEAN)


class VisualTextEndsWithNode(VisualNode):
    """Visual representation of TextEndsWithNode.

    Widgets are auto-generated from TextEndsWithNode's @node_schema decorator.
    case_sensitive property is defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Ends With"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("suffix", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.BOOLEAN)


class VisualTextLinesNode(VisualNode):
    """Visual representation of TextLinesNode.

    Widgets are auto-generated from TextLinesNode's @node_schema decorator.
    mode, line_separator, and keep_ends properties are defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Lines"
    NODE_CATEGORY = "utility/text"

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
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextCountNode(VisualNode):
    """Visual representation of TextCountNode.

    Widgets are auto-generated from TextCountNode's @node_schema decorator.
    mode and exclude_whitespace properties are defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Count"
    NODE_CATEGORY = "utility/text"

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
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("items", DataType.LIST)
        self.add_typed_input("separator", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("result", DataType.STRING)


class VisualTextExtractNode(VisualNode):
    """Visual representation of TextExtractNode.

    Widgets are auto-generated from TextExtractNode's @node_schema decorator.
    all_matches, ignore_case, multiline properties are defined in schema.
    """

    __identifier__ = "casare_rpa.utility"
    NODE_NAME = "Text Extract"
    NODE_CATEGORY = "utility/text"

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("pattern", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("match", DataType.ANY)
        self.add_typed_output("groups", DataType.LIST)
        self.add_typed_output("found", DataType.BOOLEAN)

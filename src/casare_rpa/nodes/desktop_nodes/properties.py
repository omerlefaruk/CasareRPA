"""
Desktop Node PropertyDef Constants

Reusable property definitions for desktop automation nodes.
Import these constants to maintain consistency across nodes.
"""

from casare_rpa.domain.schemas import PropertyDef, PropertyType

# =============================================================================
# Common Properties
# =============================================================================

TIMEOUT_PROP = PropertyDef(
    "timeout",
    PropertyType.FLOAT,
    default=5.0,
    min_value=0.1,
    label="Timeout (seconds)",
    tooltip="Maximum time to wait for operation",
    tab="advanced",
)

TIMEOUT_LONG_PROP = PropertyDef(
    "timeout",
    PropertyType.FLOAT,
    default=10.0,
    min_value=0.1,
    label="Timeout (seconds)",
    tooltip="Maximum time to wait for operation",
    tab="advanced",
)

RETRY_COUNT_PROP = PropertyDef(
    "retry_count",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Retry Count",
    tooltip="Number of retries on failure",
    tab="advanced",
)

RETRY_INTERVAL_PROP = PropertyDef(
    "retry_interval",
    PropertyType.FLOAT,
    default=1.0,
    min_value=0.1,
    label="Retry Interval (seconds)",
    tooltip="Delay between retries",
    tab="advanced",
)


# =============================================================================
# Element Selection Properties
# =============================================================================

SELECTOR_PROP = PropertyDef(
    "selector",
    PropertyType.JSON,
    required=False,
    label="Selector",
    tooltip="Element selector dictionary with 'strategy' and 'value'",
    tab="properties",
)

THROW_ON_NOT_FOUND_PROP = PropertyDef(
    "throw_on_not_found",
    PropertyType.BOOLEAN,
    default=True,
    label="Throw on Not Found",
    tooltip="Raise error if element is not found",
    tab="advanced",
)


# =============================================================================
# Element Interaction Properties
# =============================================================================

SIMULATE_PROP = PropertyDef(
    "simulate",
    PropertyType.BOOLEAN,
    default=False,
    label="Simulate",
    tooltip="Use simulated (programmatic) interaction vs physical input",
    tab="advanced",
)

X_OFFSET_PROP = PropertyDef(
    "x_offset",
    PropertyType.INTEGER,
    default=0,
    label="X Offset",
    tooltip="Horizontal offset from element center",
    tab="advanced",
)

Y_OFFSET_PROP = PropertyDef(
    "y_offset",
    PropertyType.INTEGER,
    default=0,
    label="Y Offset",
    tooltip="Vertical offset from element center",
    tab="advanced",
)


# =============================================================================
# Text Input Properties
# =============================================================================

TEXT_PROP = PropertyDef(
    "text",
    PropertyType.STRING,
    default="",
    label="Text",
    tooltip="Text to type into the element",
    tab="properties",
)

CLEAR_FIRST_PROP = PropertyDef(
    "clear_first",
    PropertyType.BOOLEAN,
    default=False,
    label="Clear First",
    tooltip="Clear existing text before typing",
    tab="properties",
)

INTERVAL_PROP = PropertyDef(
    "interval",
    PropertyType.FLOAT,
    default=0.01,
    min_value=0.0,
    label="Interval (seconds)",
    tooltip="Delay between keystrokes",
    tab="advanced",
)


# =============================================================================
# Variable Output Properties
# =============================================================================

VARIABLE_NAME_PROP = PropertyDef(
    "variable_name",
    PropertyType.STRING,
    default="",
    label="Variable Name",
    tooltip="Store result in this context variable",
    tab="advanced",
)


# =============================================================================
# Application Properties
# =============================================================================

APPLICATION_PATH_PROP = PropertyDef(
    "application_path",
    PropertyType.STRING,
    required=True,
    label="Application Path",
    tooltip="Full path to the executable",
    placeholder="C:\\Program Files\\App\\app.exe",
    tab="properties",
)

ARGUMENTS_PROP = PropertyDef(
    "arguments",
    PropertyType.STRING,
    default="",
    label="Arguments",
    tooltip="Command line arguments",
    tab="properties",
)

WORKING_DIRECTORY_PROP = PropertyDef(
    "working_directory",
    PropertyType.STRING,
    default="",
    label="Working Directory",
    tooltip="Starting directory for the application",
    tab="properties",
)

WINDOW_TITLE_HINT_PROP = PropertyDef(
    "window_title_hint",
    PropertyType.STRING,
    default="",
    label="Window Title Hint",
    tooltip="Expected window title to identify the application window",
    tab="properties",
)

WINDOW_STATE_PROP = PropertyDef(
    "window_state",
    PropertyType.CHOICE,
    default="normal",
    choices=["normal", "maximized", "minimized"],
    label="Window State",
    tooltip="Window state after operation",
    tab="properties",
)

FORCE_CLOSE_PROP = PropertyDef(
    "force_close",
    PropertyType.BOOLEAN,
    default=False,
    label="Force Close",
    tooltip="Forcefully terminate if graceful close fails",
    tab="advanced",
)

KEEP_OPEN_PROP = PropertyDef(
    "keep_open",
    PropertyType.BOOLEAN,
    default=True,
    label="Keep Open After Workflow",
    tooltip="Keep the application open when the workflow ends (default: True)",
    tab="properties",
)


# =============================================================================
# Window Properties
# =============================================================================

MATCH_PARTIAL_PROP = PropertyDef(
    "match_partial",
    PropertyType.BOOLEAN,
    default=True,
    label="Match Partial",
    tooltip="Allow partial title matching",
    tab="properties",
)

INCLUDE_INVISIBLE_PROP = PropertyDef(
    "include_invisible",
    PropertyType.BOOLEAN,
    default=False,
    label="Include Invisible",
    tooltip="Include invisible windows in results",
    tab="advanced",
)

FILTER_TITLE_PROP = PropertyDef(
    "filter_title",
    PropertyType.STRING,
    default="",
    label="Filter Title",
    tooltip="Filter windows by title (partial match)",
    tab="properties",
)

BRING_TO_FRONT_PROP = PropertyDef(
    "bring_to_front",
    PropertyType.BOOLEAN,
    default=False,
    label="Bring to Front",
    tooltip="Bring window to front before operation",
    tab="advanced",
)


# =============================================================================
# Mouse Properties
# =============================================================================

MOUSE_BUTTON_PROP = PropertyDef(
    "button",
    PropertyType.CHOICE,
    default="left",
    choices=["left", "right", "middle"],
    label="Mouse Button",
    tooltip="Mouse button to use",
    tab="properties",
)

CLICK_TYPE_PROP = PropertyDef(
    "click_type",
    PropertyType.CHOICE,
    default="single",
    choices=["single", "double", "triple"],
    label="Click Type",
    tooltip="Type of click to perform",
    tab="properties",
)

DURATION_PROP = PropertyDef(
    "duration",
    PropertyType.FLOAT,
    default=0.0,
    min_value=0.0,
    label="Duration (seconds)",
    tooltip="Animation duration (0 for instant)",
    tab="advanced",
)


# =============================================================================
# Keyboard Properties
# =============================================================================

KEYS_PROP = PropertyDef(
    "keys",
    PropertyType.STRING,
    default="",
    label="Keys",
    tooltip="Keys to send. Use {Key} for special keys (e.g., {Enter}, {Tab})",
    tab="properties",
)

HOTKEY_MODIFIER_PROP = PropertyDef(
    "modifier",
    PropertyType.CHOICE,
    default="none",
    choices=["none", "Ctrl", "Alt", "Shift", "Win"],
    label="Modifier",
    tooltip="Modifier key for hotkey",
    tab="properties",
)

WITH_CTRL_PROP = PropertyDef(
    "with_ctrl",
    PropertyType.BOOLEAN,
    default=False,
    label="With Ctrl",
    tooltip="Hold Ctrl key during operation",
    tab="advanced",
)

WITH_SHIFT_PROP = PropertyDef(
    "with_shift",
    PropertyType.BOOLEAN,
    default=False,
    label="With Shift",
    tooltip="Hold Shift key during operation",
    tab="advanced",
)

WITH_ALT_PROP = PropertyDef(
    "with_alt",
    PropertyType.BOOLEAN,
    default=False,
    label="With Alt",
    tooltip="Hold Alt key during operation",
    tab="advanced",
)


# =============================================================================
# Wait/Verification Properties
# =============================================================================

WAIT_STATE_PROP = PropertyDef(
    "state",
    PropertyType.CHOICE,
    default="visible",
    choices=["visible", "hidden", "enabled", "disabled"],
    label="State",
    tooltip="State to wait for",
    tab="properties",
)

POLL_INTERVAL_PROP = PropertyDef(
    "poll_interval",
    PropertyType.FLOAT,
    default=0.5,
    min_value=0.1,
    label="Poll Interval (seconds)",
    tooltip="Interval between state checks",
    tab="advanced",
)

COMPARISON_PROP = PropertyDef(
    "comparison",
    PropertyType.CHOICE,
    default="equals",
    choices=["equals", "contains", "startswith", "endswith", "regex"],
    label="Comparison",
    tooltip="How to compare values",
    tab="properties",
)


# =============================================================================
# Screenshot/OCR Properties
# =============================================================================

FILE_PATH_PROP = PropertyDef(
    "file_path",
    PropertyType.STRING,
    default="",
    label="File Path",
    tooltip="Path to save file",
    tab="properties",
)

IMAGE_FORMAT_PROP = PropertyDef(
    "format",
    PropertyType.CHOICE,
    default="PNG",
    choices=["PNG", "JPEG", "BMP"],
    label="Image Format",
    tooltip="Image file format",
    tab="properties",
)

PADDING_PROP = PropertyDef(
    "padding",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Padding",
    tooltip="Extra pixels around element bounds",
    tab="advanced",
)

OCR_ENGINE_PROP = PropertyDef(
    "engine",
    PropertyType.CHOICE,
    default="auto",
    choices=["auto", "rapidocr", "tesseract", "winocr"],
    label="OCR Engine",
    tooltip="OCR engine to use",
    tab="properties",
)

OCR_LANGUAGE_PROP = PropertyDef(
    "language",
    PropertyType.STRING,
    default="eng",
    label="Language",
    tooltip="OCR language code (e.g., eng, spa, fra)",
    tab="properties",
)


# =============================================================================
# Office Properties
# =============================================================================

VISIBLE_PROP = PropertyDef(
    "visible",
    PropertyType.BOOLEAN,
    default=False,
    label="Visible",
    tooltip="Show application window",
    tab="advanced",
)

CREATE_IF_MISSING_PROP = PropertyDef(
    "create_if_missing",
    PropertyType.BOOLEAN,
    default=False,
    label="Create If Missing",
    tooltip="Create new file if not found",
    tab="properties",
)

SHEET_PROP = PropertyDef(
    "sheet",
    PropertyType.STRING,
    default="1",
    label="Sheet",
    tooltip="Sheet name or index (1-based)",
    tab="properties",
)

CELL_PROP = PropertyDef(
    "cell",
    PropertyType.STRING,
    default="",
    label="Cell",
    tooltip="Cell reference (e.g., A1)",
    tab="properties",
)

RANGE_PROP = PropertyDef(
    "range",
    PropertyType.STRING,
    default="",
    label="Range",
    tooltip="Range reference (e.g., A1:C10)",
    tab="properties",
)

SAVE_BEFORE_CLOSE_PROP = PropertyDef(
    "save",
    PropertyType.BOOLEAN,
    default=True,
    label="Save Before Close",
    tooltip="Save document before closing",
    tab="properties",
)

QUIT_APP_PROP = PropertyDef(
    "quit_app",
    PropertyType.BOOLEAN,
    default=True,
    label="Quit Application",
    tooltip="Quit application after closing document",
    tab="advanced",
)

HTML_BODY_PROP = PropertyDef(
    "html_body",
    PropertyType.BOOLEAN,
    default=False,
    label="HTML Body",
    tooltip="Body content is HTML formatted",
    tab="advanced",
)

"""
Semantic Color System for CasareRPA Canvas.

A refined dark mode palette with ~30 semantic colors (down from 130+).
Colors are named by usage, not appearance (e.g., "primary" not "indigo-500").

Design Principles:
- Zinc-based neutral scale for excellent readability
- Electric Indigo as primary brand color
- Semantic colors for status (success, warning, error, info)
- WCAG AA compliant contrast ratios
- VSCode Dark+ compatible syntax colors

Usage:
    from casare_rpa.presentation.canvas.theme_system import THEME

    # Backgrounds
    widget.setStyleSheet(f"background-color: {THEME.bg_surface}")

    # Text
    widget.setStyleSheet(f"color: {THEME.text_primary}")

    # Semantic colors
    if status == "error":
        color = THEME.error
"""

from dataclasses import dataclass

# =============================================================================
# NEUTRAL SCALE (Zinc-based)
# =============================================================================
# Zinc provides warmer, more readable grays than pure black/white.
# Scale: 950 (darkest) → 600 (lightest used)

# Background levels (darkest to lightest)
BG_CANVAS = "#09090b"  # Zinc 950 - Main canvas background
BG_SURFACE = "#18181b"  # Zinc 900 - Panels, dialogs, containers
BG_ELEVATED = "#27272a"  # Zinc 800 - Raised surfaces (cards, headers)
BG_COMPONENT = "#3f3f46"  # Zinc 700 - Inputs, dropdowns, interactive
BG_BORDER = "#52525b"  # Zinc 600 - Borders, separators, dividers

# Text levels (lightest to darkest)
TEXT_PRIMARY = "#f4f4f5"  # Zinc 100 - Primary text, headings
TEXT_SECONDARY = "#a1a1aa"  # Zinc 400 - Secondary text, descriptions
TEXT_MUTED = "#71717a"  # Zinc 500 - Placeholder, disabled text
TEXT_DISABLED = "#52525b"  # Zinc 600 - Disabled controls

# Text on colored backgrounds
TEXT_ON_PRIMARY = "#ffffff"  # White text on primary color
TEXT_ON_SUCCESS = "#ffffff"  # White text on success color
TEXT_ON_WARNING = "#ffffff"  # White text on warning color
TEXT_ON_ERROR = "#ffffff"  # White text on error color


# =============================================================================
# PRIMARY BRAND COLOR
# =============================================================================
# Electric Indigo - modern, trustworthy, excellent contrast

PRIMARY = "#6366f1"  # Indigo 500 - Main brand color
PRIMARY_HOVER = "#4f46e5"  # Indigo 600 - Hover state
PRIMARY_ACTIVE = "#4338ca"  # Indigo 700 - Active/pressed state
PRIMARY_SUBTLE = "#312e81"  # Indigo 900 - Background tint


# =============================================================================
# SEMANTIC COLORS
# =============================================================================

# Success (Emerald)
SUCCESS = "#10b981"  # Emerald 500
SUCCESS_SUBTLE = "#064e3b"  # Emerald 900 (background)
SUCCESS_LIGHT = "#d1fae5"  # Emerald 100 (text on dark)

# Warning (Amber)
WARNING = "#f59e0b"  # Amber 500
WARNING_SUBTLE = "#78350f"  # Amber 900 (background)
WARNING_LIGHT = "#fef3c7"  # Amber 100 (text on dark)

# Error (Red)
ERROR = "#ef4444"  # Red 500
ERROR_SUBTLE = "#7f1d1d"  # Red 900 (background)
ERROR_LIGHT = "#fecaca"  # Red 100 (text on dark)

# Info (Blue)
INFO = "#3b82f6"  # Blue 500
INFO_SUBTLE = "#1e3a8a"  # Blue 900 (background)
INFO_LIGHT = "#bfdbfe"  # Blue 100 (text on dark)


# =============================================================================
# WIRE COLORS (Data Type Visualization)
# =============================================================================
# Distinct, accessible colors for canvas connection wires.
# High contrast against dark backgrounds.

WIRE_EXEC = "#ffffff"  # White - Execution flow
WIRE_BOOL = "#ef4444"  # Red - Boolean
WIRE_STRING = "#f97316"  # Orange - String
WIRE_NUMBER = "#10b981"  # Emerald - Number (int, float)
WIRE_LIST = "#a78bfa"  # Violet - List/Array
WIRE_DICT = "#2dd4bf"  # Teal - Dict/Object
WIRE_ANY = "#6366f1"  # Indigo - Any/Unknown


# =============================================================================
# NODE STATUS COLORS
# =============================================================================
# Pastel variants for better visibility on node headers

NODE_IDLE = "#a1a1aa"  # Gray - Not executed
NODE_RUNNING = "#fbbf24"  # Amber - Currently running
NODE_SUCCESS = "#34d399"  # Emerald - Completed successfully
NODE_ERROR = "#f87171"  # Red - Failed
NODE_SKIPPED = "#a78bfa"  # Violet - Skipped (conditional)
NODE_BREAKPOINT = "#f87171"  # Red - Breakpoint hit


# =============================================================================
# SYNTAX HIGHLIGHTING (VSCode Dark+ Compatible)
# =============================================================================

SYNTAX_KEYWORD = "#C586C0"  # Purple - if, for, def, class
SYNTAX_FUNCTION = "#DCDCAA"  # Yellow - Function names
SYNTAX_STRING = "#CE9178"  # Orange - String literals
SYNTAX_NUMBER = "#B5CEA8"  # Light green - Numbers
SYNTAX_COMMENT = "#6A9955"  # Green - Comments
SYNTAX_BUILTIN = "#4EC9B0"  # Teal - True, False, None
SYNTAX_VARIABLE = "#9CDCFE"  # Light blue - Variables
SYNTAX_CLASS = "#4EC9B0"  # Teal - Class names
SYNTAX_OPERATOR = "#D4D4D4"  # Light gray - Operators
SYNTAX_REGEX = "#D16969"  # Red - Regex patterns


# =============================================================================
# EDITOR COLORS
# =============================================================================

EDITOR_BG = "#1E1E1E"  # Editor background
EDITOR_LINE_NUMBER_BG = "#1E1E1E"  # Line number gutter
EDITOR_LINE_NUMBER_FG = "#858585"  # Line number text
EDITOR_CURRENT_LINE = "#282828"  # Current line highlight
EDITOR_SELECTION = "#264F78"  # Selection background
EDITOR_MATCHING_BRACKET = "#515151"  # Bracket match highlight
EDITOR_INDENT_GUIDE = "#404040"  # Indent guide lines


# =============================================================================
# WIDGET-SPECIFIC COLORS
# =============================================================================

# Toolbar
TOOLBAR_BG = "#18181b"  # Same as BG_SURFACE
TOOLBAR_BORDER = "#27272a"  # Same as BG_ELEVATED
TOOLBAR_BUTTON_HOVER = "#3f3f46"  # Same as BG_COMPONENT
TOOLBAR_BUTTON_PRESSED = "#4338ca"  # Same as PRIMARY_ACTIVE

# Menu (VSCode/Cursor style)
MENU_BG = "#252526"
MENU_BORDER = "#454545"
MENU_HOVER = "#094771"
MENU_TEXT = "#CCCCCC"
MENU_TEXT_SHORTCUT = "#858585"
MENU_TEXT_DISABLED = "#6B6B6B"
MENU_SEPARATOR = "#454545"

# Dock/Panel
DOCK_TITLE_BG = "#18181b"
DOCK_TITLE_TEXT = "#a1a1aa"
SPLITTER_HANDLE = "#18181b"  # Invisible (matches background)

# Input fields
INPUT_BG = "#09090b"  # Darker than surface for depth
INPUT_BORDER = "#3f3f46"  # Same as BG_COMPONENT
INPUT_BORDER_FOCUS = "#6366f1"  # Same as PRIMARY
INPUT_PLACEHOLDER = "#71717a"  # Same as TEXT_MUTED

# Buttons
BUTTON_PRIMARY_BG = "#6366f1"  # Same as PRIMARY
BUTTON_PRIMARY_HOVER = "#4f46e5"  # Same as PRIMARY_HOVER
BUTTON_PRIMARY_TEXT = "#ffffff"

BUTTON_SECONDARY_BG = "#3f3f46"  # Same as BG_COMPONENT
BUTTON_SECONDARY_HOVER = "#52525b"  # Slightly lighter
BUTTON_SECONDARY_TEXT = "#f4f4f5"  # Same as TEXT_PRIMARY

# Scrollbar
SCROLLBAR_BG = "#18181b"
SCROLLBAR_HANDLE = "#3f3f46"
SCROLLBAR_HANDLE_HOVER = "#52525b"


# =============================================================================
# OVERLAYS
# =============================================================================

OVERLAY_DARK = "rgba(0, 0, 0, 128)"  # 50% opacity black
OVERLAY_LIGHT = "rgba(255, 255, 255, 10)"  # Subtle white tint


# =============================================================================
# BRAND COLORS (OAuth providers)
# =============================================================================

BRAND_GOOGLE = "#4285f4"
BRAND_GOOGLE_HOVER = "#5a95f5"
BRAND_GEMINI = "#9C27B0"
BRAND_GEMINI_HOVER = "#B026B8"


# =============================================================================
# DATA TYPE BADGES (Variable Panel)
# =============================================================================

TYPE_STRING = "#4ec9b0"  # Teal
TYPE_INTEGER = "#b5cea8"  # Light green
TYPE_FLOAT = "#b5cea8"  # Light green (same as integer)
TYPE_BOOLEAN = "#569cd6"  # Blue
TYPE_LIST = "#dcdcaa"  # Yellow
TYPE_DICT = "#dcdcaa"  # Yellow (same as list)


# =============================================================================
# MAIN THEME DATA CLASS
# =============================================================================


@dataclass
class CanvasThemeColors:
    """
    Unified theme colors with semantic naming.

    All colors are organized by usage, not visual appearance.
    This makes the code more readable and theme changes easier.

    Backward Compatibility:
        Many legacy color names are preserved as aliases.
    """

    # Neutral backgrounds (semantic names)
    bg_canvas: str = BG_CANVAS
    bg_surface: str = BG_SURFACE
    bg_elevated: str = BG_ELEVATED
    bg_component: str = BG_COMPONENT
    bg_border: str = BG_BORDER

    # Legacy background names (deprecated, use semantic above)
    bg_darkest: str = BG_CANVAS
    bg_dark: str = BG_SURFACE
    bg_medium: str = BG_ELEVATED
    bg_light: str = BG_COMPONENT
    bg_lighter: str = BG_BORDER
    bg_panel: str = BG_SURFACE
    bg_header: str = BG_CANVAS
    bg_hover: str = BG_COMPONENT
    bg_selected: str = PRIMARY_SUBTLE

    # Node-specific backgrounds
    bg_node: str = BG_SURFACE
    bg_node_selected: str = PRIMARY_SUBTLE
    bg_node_header: str = BG_SURFACE

    # Borders
    border_dark: str = "#09090b"
    border: str = BG_COMPONENT
    border_light: str = BG_BORDER
    border_focus: str = PRIMARY

    # Text colors
    text_primary: str = TEXT_PRIMARY
    text_secondary: str = TEXT_SECONDARY
    text_muted: str = TEXT_MUTED
    text_disabled: str = TEXT_DISABLED
    text_header: str = "#e4e4e7"

    # Text on colored backgrounds
    text_on_primary: str = TEXT_ON_PRIMARY
    text_on_success: str = TEXT_ON_SUCCESS
    text_on_warning: str = TEXT_ON_WARNING
    text_on_error: str = TEXT_ON_ERROR

    # Primary brand color
    primary: str = PRIMARY
    primary_hover: str = PRIMARY_HOVER
    primary_active: str = PRIMARY_ACTIVE
    primary_subtle: str = PRIMARY_SUBTLE

    # Semantic colors
    success: str = SUCCESS
    success_subtle: str = SUCCESS_SUBTLE
    success_light: str = SUCCESS_LIGHT

    warning: str = WARNING
    warning_subtle: str = WARNING_SUBTLE
    warning_light: str = WARNING_LIGHT

    error: str = ERROR
    error_subtle: str = ERROR_SUBTLE
    error_light: str = ERROR_LIGHT

    info: str = INFO
    info_subtle: str = INFO_SUBTLE
    info_light: str = INFO_LIGHT

    # Status colors
    status_success: str = SUCCESS
    status_warning: str = WARNING
    status_error: str = ERROR
    status_info: str = INFO
    status_running: str = WARNING
    status_idle: str = TEXT_MUTED

    # Node status colors
    node_idle: str = NODE_IDLE
    node_running: str = NODE_RUNNING
    node_success: str = NODE_SUCCESS
    node_error: str = NODE_ERROR
    node_skipped: str = NODE_SKIPPED
    node_breakpoint: str = NODE_BREAKPOINT

    # Accent colors
    accent_primary: str = PRIMARY
    accent_secondary: str = "#818cf8"
    accent_hover: str = PRIMARY_HOVER
    accent_success: str = SUCCESS
    accent_warning: str = WARNING
    accent_error: str = ERROR

    # Wire colors (by data type)
    wire_exec: str = WIRE_EXEC
    wire_data: str = WIRE_ANY
    wire_bool: str = WIRE_BOOL
    wire_string: str = WIRE_STRING
    wire_number: str = WIRE_NUMBER
    wire_list: str = WIRE_LIST
    wire_dict: str = WIRE_DICT
    wire_table: str = "#3b82f6"

    # Syntax highlighting
    syntax_keyword: str = SYNTAX_KEYWORD
    syntax_function: str = SYNTAX_FUNCTION
    syntax_string: str = SYNTAX_STRING
    syntax_number: str = SYNTAX_NUMBER
    syntax_comment: str = SYNTAX_COMMENT
    syntax_builtin: str = SYNTAX_BUILTIN
    syntax_variable: str = SYNTAX_VARIABLE
    syntax_decorator: str = SYNTAX_FUNCTION
    syntax_regex: str = SYNTAX_REGEX
    syntax_operator: str = SYNTAX_OPERATOR
    syntax_class: str = SYNTAX_CLASS

    # Editor colors
    editor_bg: str = EDITOR_BG
    editor_line_number_bg: str = EDITOR_LINE_NUMBER_BG
    editor_line_number_fg: str = EDITOR_LINE_NUMBER_FG
    editor_current_line: str = EDITOR_CURRENT_LINE
    editor_selection: str = EDITOR_SELECTION
    editor_matching_bracket: str = EDITOR_MATCHING_BRACKET

    # Selection overlays
    selection_bg: str = PRIMARY_ACTIVE
    selection_success_bg: str = "#1a3d1a"
    selection_error_bg: str = "#3d1a1a"
    selection_warning_bg: str = "#3d3a1a"
    selection_info_bg: str = "#1a2d3d"

    # Widget-specific colors
    toolbar_bg: str = TOOLBAR_BG
    toolbar_border: str = TOOLBAR_BORDER
    toolbar_button_hover: str = TOOLBAR_BUTTON_HOVER
    toolbar_button_pressed: str = TOOLBAR_BUTTON_PRESSED

    dock_title_bg: str = DOCK_TITLE_BG
    dock_title_text: str = DOCK_TITLE_TEXT
    splitter_handle: str = SPLITTER_HANDLE

    menu_bg: str = MENU_BG
    menu_border: str = MENU_BORDER
    menu_hover: str = MENU_HOVER
    menu_text: str = MENU_TEXT
    menu_text_shortcut: str = MENU_TEXT_SHORTCUT
    menu_text_disabled: str = MENU_TEXT_DISABLED
    menu_separator: str = MENU_SEPARATOR
    menu_shadow: str = "#00000078"

    input_bg: str = INPUT_BG
    input_border: str = INPUT_BORDER
    input_border_focus: str = INPUT_BORDER_FOCUS
    input_placeholder: str = INPUT_PLACEHOLDER

    button_primary_bg: str = BUTTON_PRIMARY_BG
    button_primary_hover: str = BUTTON_PRIMARY_HOVER
    button_primary_text: str = BUTTON_PRIMARY_TEXT
    button_secondary_bg: str = BUTTON_SECONDARY_BG
    button_secondary_hover: str = BUTTON_SECONDARY_HOVER
    button_secondary_text: str = BUTTON_SECONDARY_TEXT

    scrollbar_bg: str = SCROLLBAR_BG
    scrollbar_handle: str = SCROLLBAR_HANDLE
    scrollbar_handle_hover: str = SCROLLBAR_HANDLE_HOVER

    # Overlays
    overlay_dark: str = OVERLAY_DARK
    overlay_light: str = OVERLAY_LIGHT

    # Brand colors
    brand_google: str = BRAND_GOOGLE
    brand_google_hover: str = BRAND_GOOGLE_HOVER
    brand_gemini: str = BRAND_GEMINI
    brand_gemini_hover: str = BRAND_GEMINI_HOVER

    # Data type badges
    type_string: str = TYPE_STRING
    type_integer: str = TYPE_INTEGER
    type_float: str = TYPE_FLOAT
    type_boolean: str = TYPE_BOOLEAN
    type_list: str = TYPE_LIST
    type_dict: str = TYPE_DICT

    # Legacy aliases for commonly used names
    brand_success: str = "#059669"
    brand_success_dark: str = "#047857"
    brand_warning: str = "#d97706"
    brand_error: str = "#dc2626"
    brand_error_dark: str = "#b91c1c"
    brand_info: str = "#2563eb"

    console_text: str = "#d4d4d4"
    console_info: str = "#4ec9b0"
    console_success: str = "#89d185"
    console_warning: str = "#cca700"
    console_error: str = "#f44747"
    console_debug: str = "#808080"

    json_key: str = "#9cdcfe"
    json_string: str = "#ce9178"
    json_number: str = "#b5cea8"
    json_boolean: str = "#569cd6"

    accent_orange: str = "#f97316"
    accent_light: str = "#818cf8"
    accent_danger: str = ERROR
    accent_pressed: str = "#005a9e"
    accent_darker: str = "#1d4ed8"

    error_bg: str = "#5a1d1d"
    error_light: str = ERROR_LIGHT
    info_light: str = INFO_LIGHT
    success_light: str = SUCCESS_LIGHT

    hover: str = "#2a2d2e"
    selected: str = "#264f78"

    primary_pressed: str = "#005a9e"

    # Border radius (deprecated, use TOKENS.radius)
    border_radius_small: int = 4
    border_radius_medium: int = 8
    border_radius_large: int = 12

    # Spacing (deprecated, use TOKENS.spacing)
    spacing_xsmall: int = 4
    spacing_small: int = 8
    spacing_medium: int = 16
    spacing_large: int = 24
    spacing_xlarge: int = 32

    # Additional legacy attributes
    bg_darker: str = "#1e1e1e"
    bg_primary: str = "#1e1e1e"
    bg_secondary: str = "#252526"
    bg_tertiary: str = "#2d2d30"
    bg_active: str = "#264f78"

    input_border: str = INPUT_BORDER
    border_radius_scrollbar: int = 5

    link: str = "#569cd6"
    selector_text: str = "#60a5fa"

    scrollbar: str = SCROLLBAR_HANDLE
    scrollbar_hover: str = SCROLLBAR_HANDLE_HOVER

    brand_google_light: str = BRAND_GOOGLE_HOVER
    brand_google_dark: str = "#2d5a9e"
    brand_gemini_light: str = BRAND_GEMINI_HOVER

    button_bg: str = BUTTON_SECONDARY_BG
    button_hover: str = BUTTON_SECONDARY_HOVER
    button_pressed: str = "#0078d4"
    button_text: str = BUTTON_SECONDARY_TEXT
    button_text_hover: str = "#ffffff"


# Global theme instance
THEME = CanvasThemeColors()


# =============================================================================
# COLOR MAPPINGS (for backward compatibility)
# =============================================================================

WIRE_COLOR_MAP: dict[str, str] = {
    "exec": WIRE_EXEC,
    "any": WIRE_ANY,
    "bool": WIRE_BOOL,
    "boolean": WIRE_BOOL,
    "string": WIRE_STRING,
    "str": WIRE_STRING,
    "number": WIRE_NUMBER,
    "int": WIRE_NUMBER,
    "float": WIRE_NUMBER,
    "list": WIRE_LIST,
    "array": WIRE_LIST,
    "dict": WIRE_DICT,
    "object": WIRE_DICT,
    "table": "#3b82f6",
}

NODE_STATUS_COLOR_MAP: dict[str, str] = {
    "idle": NODE_IDLE,
    "running": NODE_RUNNING,
    "success": NODE_SUCCESS,
    "error": NODE_ERROR,
    "skipped": NODE_SKIPPED,
    "breakpoint": NODE_BREAKPOINT,
}

STATUS_COLOR_MAP: dict[str, str] = {
    "success": SUCCESS,
    "completed": SUCCESS,
    "warning": WARNING,
    "running": WARNING,
    "error": ERROR,
    "failed": ERROR,
    "info": INFO,
    "idle": TEXT_MUTED,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_wire_color(data_type: str, theme: CanvasThemeColors = None) -> str:
    """Get color for a connection wire based on data type."""
    if theme is None:
        return WIRE_COLOR_MAP.get(data_type.lower(), WIRE_ANY)
    return WIRE_COLOR_MAP.get(data_type.lower(), theme.wire_any)


def get_node_status_color(status: str, theme: CanvasThemeColors = None) -> str:
    """Get color for a node execution status."""
    if theme is None:
        return NODE_STATUS_COLOR_MAP.get(status.lower(), NODE_IDLE)
    return NODE_STATUS_COLOR_MAP.get(status.lower(), theme.node_idle)


def get_status_color(status: str, theme: CanvasThemeColors = None) -> str:
    """Get color for a general status string."""
    if theme is None:
        return STATUS_COLOR_MAP.get(status.lower(), TEXT_MUTED)
    return STATUS_COLOR_MAP.get(status.lower(), theme.text_muted)

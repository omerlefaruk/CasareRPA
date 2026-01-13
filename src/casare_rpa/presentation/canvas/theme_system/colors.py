"""
Semantic Color System for CasareRPA Canvas.

Design System 2025: Minimal semantic color palette (~30 colors).
Colors are named by usage, not appearance (e.g., "primary" not "indigo-500").

Design Principles:
- Zinc-based neutral scale for excellent readability
- Electric Indigo as primary brand color
- Semantic colors for status (success, warning, error, info)
- WCAG AA compliant contrast ratios
- VSCode Dark+ compatible syntax colors
"""

from dataclasses import dataclass

from casare_rpa.domain.value_objects.types import DataType

# =============================================================================
# BASE PALETTE (Source of Truth)
# =============================================================================

# Neutral Scale (Zinc)
ZINC_950 = "#09090b"  # Deepest background
ZINC_900 = "#18181b"  # Surface / Panel Background
ZINC_800 = "#27272a"  # Component Background / Border
ZINC_700 = "#3f3f46"  # Hover / Border Light
ZINC_600 = "#52525b"  # Muted / Disabled
ZINC_500 = "#71717a"  # Secondary text
ZINC_400 = "#a1a1aa"  # Idle text
ZINC_300 = "#d4d4d8"  # Primary text (subtle)
ZINC_200 = "#e4e4e7"  # Primary text / Headers
ZINC_100 = "#f4f4f5"  # Inverse text

# Brand Colors (Indigo)
INDIGO_500 = "#6366f1"  # Primary
INDIGO_600 = "#4f46e5"  # Primary Hover
INDIGO_700 = "#4338ca"  # Primary Active
INDIGO_500_ALPHA = "#6366f126"  # Primary Subtle (15% opacity)

# Semantic Colors
EMERALD_500 = "#10b981"  # Success
AMBER_500 = "#f59e0b"  # Warning
RED_500 = "#ef4444"  # Error
SKY_500 = "#0ea5e9"  # Info

# Additional Category Colors (for node categorization)
VIOLET_500 = "#8b5cf6"  # Purple
PINK_500 = "#ec4899"  # Pink
TEAL_500 = "#14b8a6"  # Teal
CYAN_500 = "#06b6d4"  # Cyan
ROSE_500 = "#f43f5e"  # Rose
LIME_500 = "#84cc16"  # Lime
ORANGE_500 = "#f97316"  # Orange

# Brand Colors (for third-party integrations)
GOOGLE_BLUE = "#4285f4"
MICROSOFT_BLUE = "#00a4ef"

# Wire/Data Type Colors
WIRE_STRING = "#f97316"  # Orange
WIRE_NUMBER = "#10b981"  # Emerald
WIRE_LIST = "#a78bfa"  # Violet
WIRE_DICT = "#2dd4bf"  # Teal
WIRE_BOOL = "#3b82f6"  # Blue
WIRE_ANY = "#6366f1"  # Indigo
WIRE_EXEC = "#ffffff"  # White

# Syntax Highlighting (VSCode Dark+)
SYNTAX_KEYWORD = "#C586C0"
SYNTAX_FUNCTION = "#DCDCAA"
SYNTAX_STRING = "#CE9178"
SYNTAX_NUMBER = "#B5CEA8"
SYNTAX_COMMENT = "#6A9955"
SYNTAX_BUILTIN = "#4EC9B0"
SYNTAX_VARIABLE = "#9CDCFE"
SYNTAX_CLASS = "#4EC9B0"
SYNTAX_REGEX = "#D16969"


# =============================================================================
# SEMANTIC THEME
# =============================================================================


@dataclass
class CanvasThemeColors:
    """
    Unified theme colors with semantic naming.

    Design System 2025: Minimal, semantic color tokens.
    All colors are named by function, not appearance.
    """

    # === BACKGROUNDS ===
    bg_canvas: str = ZINC_950  # #09090b - Main canvas
    bg_surface: str = ZINC_900  # #18181b - Panels, dialogs
    bg_elevated: str = ZINC_800  # #27272a - Modals, dropdowns
    bg_component: str = ZINC_700  # #3f3f46 - Inputs, cards
    bg_hover: str = ZINC_700  # Hover state
    bg_selected: str = INDIGO_500_ALPHA  # Selection highlight
    bg_header: str = ZINC_950  # Header bars

    # === BORDERS ===
    border: str = ZINC_800  # Default border
    border_light: str = ZINC_700  # Lighter border
    border_dark: str = ZINC_950  # Darker border
    border_focus: str = INDIGO_500  # Focus ring
    bg_border: str = ZINC_600  # #52525b - Standard border color

    # === TEXT ===
    text_primary: str = ZINC_200  # Main text
    text_secondary: str = ZINC_500  # Secondary text
    text_muted: str = ZINC_600  # Muted/placeholder
    text_disabled: str = ZINC_700  # Disabled text
    text_header: str = ZINC_200  # Headers
    text_inverse: str = ZINC_950  # Text on light bg

    # === BRAND ===
    primary: str = INDIGO_500  # Primary brand color
    primary_hover: str = INDIGO_600  # Primary hover
    primary_active: str = INDIGO_700  # Primary pressed

    # === STATUS ===
    success: str = EMERALD_500
    warning: str = AMBER_500
    error: str = RED_500
    info: str = SKY_500

    # === TEXT ON STATUS BACKGROUNDS ===
    text_on_primary: str = "#ffffff"
    text_on_success: str = "#ffffff"
    text_on_warning: str = "#ffffff"
    text_on_error: str = "#ffffff"

    # === NODE GRAPH ===
    bg_node: str = ZINC_900
    bg_node_header: str = ZINC_900
    bg_node_selected: str = INDIGO_500_ALPHA
    node_idle: str = ZINC_600
    node_running: str = AMBER_500
    node_success: str = EMERALD_500
    node_error: str = RED_500
    node_skipped: str = WIRE_LIST
    node_breakpoint: str = RED_500

    # === WIRES ===
    wire_exec: str = WIRE_EXEC
    wire_data: str = WIRE_ANY
    wire_string: str = WIRE_STRING
    wire_number: str = WIRE_NUMBER
    wire_bool: str = WIRE_BOOL
    wire_list: str = WIRE_LIST
    wire_dict: str = WIRE_DICT
    wire_any: str = WIRE_ANY
    wire_table: str = "#3b82f6"

    # === DATA TYPE COLORS ===
    type_string: str = WIRE_STRING
    type_integer: str = WIRE_NUMBER
    type_float: str = WIRE_NUMBER
    type_boolean: str = WIRE_BOOL
    type_list: str = WIRE_LIST
    type_dict: str = WIRE_DICT
    type_any: str = WIRE_ANY

    # === SYNTAX HIGHLIGHTING ===
    syntax_keyword: str = SYNTAX_KEYWORD
    syntax_function: str = SYNTAX_FUNCTION
    syntax_string: str = SYNTAX_STRING
    syntax_number: str = SYNTAX_NUMBER
    syntax_comment: str = SYNTAX_COMMENT
    syntax_builtin: str = SYNTAX_BUILTIN
    syntax_variable: str = SYNTAX_VARIABLE
    syntax_class: str = SYNTAX_CLASS
    syntax_regex: str = SYNTAX_REGEX

    # JSON-specific colors (for JSON syntax highlighter)
    json_key: str = SYNTAX_VARIABLE
    json_string: str = SYNTAX_STRING
    json_number: str = SYNTAX_NUMBER
    json_boolean: str = "#569CD6"  # Blue for true/false/null
    json_null: str = "#569CD6"  # Same as boolean

    # Selector-specific colors
    selector_text: str = SYNTAX_VARIABLE  # Blue for selector strings

    # === NODE CATEGORY COLORS ===
    # Category colors for node organization in the graph
    category_basic: str = ZINC_500
    category_browser: str = INDIGO_500
    category_navigation: str = INDIGO_500
    category_interaction: str = INDIGO_500
    category_data: str = EMERALD_500
    category_data_operations: str = EMERALD_500
    category_desktop: str = AMBER_500
    category_desktop_automation: str = AMBER_500
    category_file: str = VIOLET_500
    category_file_operations: str = VIOLET_500
    category_http: str = RED_500
    category_rest_api: str = RED_500
    category_system: str = ZINC_500
    category_control_flow: str = PINK_500
    category_error_handling: str = PINK_500
    category_variable: str = TEAL_500
    category_wait: str = TEAL_500
    category_google: str = GOOGLE_BLUE
    category_microsoft: str = MICROSOFT_BLUE
    category_database: str = CYAN_500
    category_email: str = CYAN_500
    category_office_automation: str = MICROSOFT_BLUE
    category_scripts: str = ZINC_500
    category_debug: str = AMBER_500
    category_utility: str = ZINC_500
    category_triggers: str = PINK_500
    category_messaging: str = CYAN_500
    category_document: str = VIOLET_500

    # === EDITOR ===
    editor_bg: str = "#1e1e1e"
    editor_line_number_bg: str = "#1e1e1e"
    editor_line_number_fg: str = "#858585"
    editor_current_line: str = "#282828"
    editor_selection: str = "#264f78"

    # === UI COMPONENTS ===
    toolbar_bg: str = ZINC_900
    toolbar_border: str = ZINC_800
    menu_bg: str = "#252526"
    menu_border: str = "#454545"
    input_bg: str = ZINC_800
    input_border: str = ZINC_700
    scrollbar_bg: str = ZINC_900
    scrollbar_handle: str = ZINC_700
    scrollbar: str = ZINC_700  # Legacy alias for scrollbar_handle
    scrollbar_hover: str = ZINC_600  # Hover state for scrollbar

    # === BUTTON STATES ===
    button_bg: str = ZINC_800
    button_text: str = ZINC_200
    button_hover: str = ZINC_700
    button_pressed: str = ZINC_600

    # === LEGACY COMPATIBILITY ===
    # These map legacy attribute names to new semantic colors
    primary_pressed: str = INDIGO_700  # Alias for primary_active
    link: str = INDIGO_500  # Same as primary
    json_key: str = SYNTAX_VARIABLE  # For JSON syntax highlighting

    # Legacy accent_* mappings
    accent_dark: str = ZINC_600
    accent_danger: str = RED_500  # Alias for error
    accent_success: str = EMERALD_500  # Alias for success
    accent_info: str = SKY_500  # Alias for info
    accent_orange: str = AMBER_500  # Alias for warning
    accent_light: str = INDIGO_500_ALPHA  # Same as bg_selected
    accent_pressed: str = INDIGO_700  # Same as primary_active

    # Legacy selection_* mappings
    selection_bg: str = INDIGO_500_ALPHA  # Same as bg_selected
    selection_error_bg: str = "#7f1d1d"  # Dark red for error selection
    selection_warning_bg: str = "#78350f"  # Dark amber for warning selection
    selection_success_bg: str = "#14532d"  # Dark green for success selection

    # Legacy border mappings
    border_dark: str = ZINC_800  # Darker border for dividers

    # Legacy background colors for semantic states
    error_bg: str = "#450a0a"  # Dark red background for error states


# Global singleton
THEME = CanvasThemeColors()


# =============================================================================
# LEGACY COMPATIBILITY: Theme class
# =============================================================================


class Theme:
    """
    Legacy Theme class for backward compatibility.

    Provides the get_colors() class method that was used in the old ui.theme module.
    """

    @classmethod
    def get_colors(cls) -> CanvasThemeColors:
        """Return the global THEME singleton."""
        return THEME


# =============================================================================
# TYPE COLOR MAPPING
# =============================================================================

TYPE_COLORS: dict[DataType, str] = {
    DataType.STRING: THEME.type_string,
    DataType.INTEGER: THEME.type_integer,
    DataType.FLOAT: THEME.type_float,
    DataType.BOOLEAN: THEME.type_boolean,
    DataType.LIST: THEME.type_list,
    DataType.DICT: THEME.type_dict,
    DataType.ANY: THEME.type_any,
    DataType.PAGE: THEME.wire_bool,
    DataType.BROWSER: THEME.wire_bool,
    DataType.ELEMENT: THEME.wire_dict,
}


# =============================================================================
# PUBLIC HELPERS
# =============================================================================


def get_wire_color(data_type: str) -> str:
    """Get color for a connection wire based on data type string."""
    dt_lower = data_type.lower()
    if dt_lower in ("str", "string"):
        return THEME.wire_string
    if dt_lower in ("int", "float", "number"):
        return THEME.wire_number
    if dt_lower in ("bool", "boolean"):
        return THEME.wire_bool
    if dt_lower in ("list", "array"):
        return THEME.wire_list
    if dt_lower in ("dict", "object"):
        return THEME.wire_dict
    if dt_lower == "exec":
        return THEME.wire_exec
    return THEME.wire_any


def get_node_status_color(status: str) -> str:
    """Get color for a node execution status."""
    s_lower = status.lower()
    if s_lower == "running":
        return THEME.node_running
    if s_lower == "success":
        return THEME.node_success
    if s_lower == "error":
        return THEME.node_error
    if s_lower == "skipped":
        return THEME.node_skipped
    return THEME.node_idle


def get_status_color(status: str) -> str:
    """Get semantic color for general status."""
    s_lower = status.lower()
    if s_lower == "success":
        return THEME.success
    if s_lower == "warning":
        return THEME.warning
    if s_lower == "error":
        return THEME.error
    if s_lower == "info":
        return THEME.info
    return THEME.text_muted


def get_canvas_stylesheet() -> str:
    """Return the global QSS stylesheet for the canvas."""
    from .styles import get_base_stylesheet

    return get_base_stylesheet()

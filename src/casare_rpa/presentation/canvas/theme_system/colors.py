"""
Theme color definitions for CasareRPA Canvas.

Contains the CanvasThemeColors dataclass with all color values,
wire colors, status colors, and helper functions for color lookup.

ElevenLabs-inspired color system:
- Black/white core with neutral grays
- Semantic colors with AA-compliant tints
- 9 hues × 5 tint levels (simplified from 11)
"""

from dataclasses import dataclass

# Import TOKENS from .tokens to avoid circular import with __init__.py
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

# =============================================================================
# ELEVENLABS-INSPIRED COLOR TINTS (Simplified 5-level system)
# =============================================================================
# Tint levels: 50, 200, 500, 700, 900 (light to dark)
# 50: Background/lightest
# 200: Light backgrounds, secondary text
# 500: Default/mid tones
# 700: Darker tones, primary text on light
# 900: Darkest, text on light backgrounds

# Gray/Neutral tints (Zinc-based for better accessibility)
NEUTRAL_50 = "#FAFAFA"
NEUTRAL_200 = "#E4E4E7"
NEUTRAL_500 = "#71717A"
NEUTRAL_700 = "#3F3F46"
NEUTRAL_900 = "#18181B"

# Semantic tints (AA accessible combinations)
# Red (Negative/Error)
RED_50 = "#FEF2F2"
RED_200 = "#FECACA"
RED_500 = "#EF4444"
RED_700 = "#B91C1C"
RED_900 = "#7F1D1D"

# Amber/Yellow (Warning)
AMBER_50 = "#FFFBEB"
AMBER_200 = "#FDE68A"
AMBER_500 = "#F59E0B"
AMBER_700 = "#B45309"
AMBER_900 = "#78350F"

# Emerald/Green (Positive/Success)
EMERALD_50 = "#ECFDF5"
EMERALD_200 = "#A7F3D0"
EMERALD_500 = "#10B981"
EMERALD_700 = "#047857"
EMERALD_900 = "#064E3B"

# Blue (Info/Primary)
BLUE_50 = "#EFF6FF"
BLUE_200 = "#BFDBFE"
BLUE_500 = "#3B82F6"
BLUE_700 = "#1D4ED8"
BLUE_900 = "#1E3A8A"

# Indigo (Accent/Brand)
INDIGO_50 = "#EEF2FF"
INDIGO_200 = "#C7D2FE"
INDIGO_500 = "#6366F1"
INDIGO_700 = "#4338CA"
INDIGO_900 = "#312E81"


@dataclass
class CanvasThemeColors:
    """
    Premium Dark theme colors with ElevenLabs-inspired design tokens.

    A sophisticated dark palette using deep zinc grays and vibrant indigo accents
    for a modern, professional, and accessible interface.

    Design System:
    - Black/white core with neutral grays
    - Semantic colors with AA-compliant tints (Red/Amber/Emerald/Blue)
    - Indigo as the primary brand accent
    """

    # Base backgrounds (Zinc palette)
    bg_darkest: str = "#18181b"  # Zinc 900 (Main Layout BG)
    bg_dark: str = "#27272a"  # Zinc 800 (Panels/Sidebar)
    bg_medium: str = "#3f3f46"  # Zinc 700 (Inputs/Hovers)
    bg_light: str = "#52525b"  # Zinc 600 (Borders/Separators)
    bg_lighter: str = "#71717a"  # Zinc 500 (Disabled/Secondary)

    bg_panel: str = "#27272a"  # Panels
    bg_header: str = "#18181b"  # Headers (Darker for contrast)
    bg_hover: str = "#3f3f46"  # Hover states
    bg_selected: str = "#3730a3"  # Indigo 800 (Selection Background)

    # Node graph specific
    bg_canvas: str = "#18181b"  # Canvas background
    bg_node: str = "#27272a"  # Node body
    bg_node_selected: str = "#312e81"  # Indigo 900
    bg_node_header: str = "#27272a"  # Node header (same as body for seamless look)

    # Borders
    border_dark: str = "#09090b"  # Zinc 950
    border: str = "#3f3f46"  # Zinc 700
    border_light: str = "#52525b"  # Zinc 600
    border_focus: str = "#6366f1"  # Indigo 500 (Focus ring)

    # Text
    text_primary: str = "#f4f4f5"  # Zinc 100 (Primary Text)
    text_secondary: str = "#a1a1aa"  # Zinc 400 (Secondary Text)
    text_muted: str = "#71717a"  # Zinc 500 (Placeholder/Disabled)
    text_disabled: str = "#52525b"  # Zinc 600
    text_header: str = "#e4e4e7"  # Zinc 200

    # Status colors (Refined, less saturated)
    status_success: str = "#10b981"  # Emerald 500
    status_warning: str = "#f59e0b"  # Amber 500
    status_error: str = "#ef4444"  # Red 500
    status_info: str = "#3b82f6"  # Blue 500
    status_running: str = "#f59e0b"  # Amber 500 (Running)
    status_idle: str = "#71717a"  # Zinc 500

    # Node status (Pastel variants for better text contrast)
    node_idle: str = "#a1a1aa"
    node_running: str = "#fbbf24"
    node_success: str = "#34d399"
    node_error: str = "#f87171"
    node_skipped: str = "#a78bfa"
    node_breakpoint: str = "#f87171"

    # Selection/Input
    selection_bg: str = "#4338ca"  # Indigo 700
    input_bg: str = "#18181b"  # Darker input background for depth

    # Accent colors
    accent_primary: str = "#6366f1"  # Indigo 500 (Primary Brand Color)
    accent_secondary: str = "#818cf8"  # Indigo 400
    accent_hover: str = "#4f46e5"  # Indigo 600
    accent_success: str = "#10b981"
    accent_warning: str = "#f59e0b"
    accent_error: str = "#ef4444"

    # Wire colors (Vibrant for visibility against dark bg)
    wire_exec: str = "#ffffff"  # White
    wire_data: str = "#6366f1"  # Indigo 500
    wire_bool: str = "#ef4444"  # Red 500
    wire_string: str = "#f97316"  # Orange 500
    wire_number: str = "#10b981"  # Emerald 500
    wire_list: str = "#a78bfa"  # Violet 400
    wire_dict: str = "#2dd4bf"  # Teal 400
    wire_table: str = "#3b82f6"  # Blue 500

    # Toolbar
    toolbar_bg: str = "#18181b"
    toolbar_border: str = "#27272a"
    toolbar_button_hover: str = "#27272a"
    toolbar_button_pressed: str = "#3f3f46"

    # Dock/panel
    dock_title_bg: str = "#18181b"
    dock_title_text: str = "#a1a1aa"
    splitter_handle: str = "#18181b"  # Invisible splitter (matches bg)

    # Context menu (VS Code/Cursor style)
    menu_bg: str = "#252526"
    menu_border: str = "#454545"
    menu_hover: str = "#094771"
    menu_text: str = "#CCCCCC"
    menu_text_shortcut: str = "#858585"
    menu_text_disabled: str = "#6B6B6B"
    menu_separator: str = "#454545"
    menu_shadow: str = "#00000078"

    # Code Editor colors (VSCode Dark+ inspired)
    editor_bg: str = "#1E1E1E"  # Editor background
    editor_line_number_bg: str = "#1E1E1E"  # Line number gutter
    editor_line_number_fg: str = "#858585"  # Line number text
    editor_current_line: str = "#282828"  # Current line highlight
    editor_selection: str = "#264F78"  # Selection background
    editor_matching_bracket: str = "#515151"  # Bracket match

    # Syntax highlighting colors (VSCode Dark+ theme)
    syntax_keyword: str = "#C586C0"  # Purple (if, for, def)
    syntax_function: str = "#DCDCAA"  # Yellow (functions)
    syntax_string: str = "#CE9178"  # Orange-brown (strings)
    syntax_number: str = "#B5CEA8"  # Light green (numbers)
    syntax_comment: str = "#6A9955"  # Green (comments)
    syntax_builtin: str = "#4EC9B0"  # Teal (True, False, None)
    syntax_variable: str = "#9CDCFE"  # Light blue (variables)
    syntax_decorator: str = "#DCDCAA"  # Yellow (decorators)
    syntax_regex: str = "#D16969"  # Red (regex)
    syntax_operator: str = "#D4D4D4"  # Light gray (operators)
    syntax_class: str = "#4EC9B0"  # Teal (class names)

    # Selection overlays
    selection_success_bg: str = "#1a3d1a"
    selection_error_bg: str = "#3d1a1a"
    selection_warning_bg: str = "#3d3a1a"
    selection_info_bg: str = "#1a2d3d"

    # Brand colors for OAuth
    brand_google: str = "#4285f4"
    brand_google_hover: str = "#5a95f5"
    brand_gemini: str = "#9C27B0"
    brand_gemini_hover: str = "#B026B8"

    # Brand hover/disabled states
    brand_google_light: str = "#5a95f5"
    brand_google_dark: str = "#2d5a9e"
    brand_gemini_light: str = "#B026B8"

    # Semantic brand colors (for buttons, badges)
    brand_success: str = "#059669"  # Emerald 600
    brand_success_dark: str = "#047857"  # Emerald 700
    brand_warning: str = "#d97706"  # Amber 600
    brand_error: str = "#dc2626"  # Red 600
    brand_error_dark: str = "#b91c1c"  # Red 700
    brand_info: str = "#2563eb"  # Blue 600

    # Console output colors
    console_text: str = "#d4d4d4"
    console_info: str = "#4ec9b0"
    console_success: str = "#89d185"
    console_warning: str = "#cca700"
    console_error: str = "#f44747"
    console_debug: str = "#808080"

    # Data type badges (VSCode Dark+ type colors for variable panels)
    type_string: str = "#4ec9b0"  # Teal (String type)
    type_integer: str = "#b5cea8"  # Light green (Integer)
    type_float: str = "#b5cea8"  # Light green (Float)
    type_boolean: str = "#569cd6"  # Blue (Boolean)
    type_list: str = "#dcdcaa"  # Yellow (List)
    type_dict: str = "#dcdcaa"  # Yellow (Dict)

    # Overlays
    overlay_dark: str = "rgba(0, 0, 0, 128)"
    overlay_light: str = "rgba(255, 255, 255, 10)"


# Wire color mapping by data type
WIRE_COLOR_MAP: dict[str, str] = {
    "exec": "#ffffff",
    "any": "#6366f1",
    "bool": "#ef4444",
    "boolean": "#ef4444",
    "string": "#f97316",
    "str": "#f97316",
    "number": "#10b981",
    "int": "#10b981",
    "float": "#10b981",
    "list": "#a78bfa",
    "array": "#a78bfa",
    "dict": "#2dd4bf",
    "object": "#2dd4bf",
}

# Node status color mapping
NODE_STATUS_COLOR_MAP: dict[str, str] = {
    "idle": "#a1a1aa",
    "running": "#fbbf24",
    "success": "#34d399",
    "error": "#f87171",
    "skipped": "#a78bfa",
    "breakpoint": "#f87171",
}

# General status color mapping
STATUS_COLOR_MAP: dict[str, str] = {
    "success": "#10b981",
    "completed": "#10b981",
    "warning": "#f59e0b",
    "running": "#f59e0b",
    "error": "#ef4444",
    "failed": "#ef4444",
    "info": "#3b82f6",
    "idle": "#71717a",
}


def get_node_status_color(status: str, theme: CanvasThemeColors = None) -> str:
    """
    Get the color for a node execution status.

    Args:
        status: Node status string (idle, running, success, error, skipped)
        theme: Optional theme instance (uses defaults if None)

    Returns:
        Hex color string for the status.
    """
    if theme is None:
        return NODE_STATUS_COLOR_MAP.get(status.lower(), NODE_STATUS_COLOR_MAP["idle"])

    status_map = {
        "idle": theme.node_idle,
        "running": theme.node_running,
        "success": theme.node_success,
        "error": theme.node_error,
        "skipped": theme.node_skipped,
        "breakpoint": theme.node_breakpoint,
    }
    return status_map.get(status.lower(), theme.node_idle)


def get_wire_color(data_type: str, theme: CanvasThemeColors = None) -> str:
    """
    Get the color for a connection wire based on data type.

    Args:
        data_type: The data type of the connection.
        theme: Optional theme instance (uses defaults if None)

    Returns:
        Hex color string for the wire.
    """
    if theme is None:
        return WIRE_COLOR_MAP.get(data_type.lower(), WIRE_COLOR_MAP["any"])

    type_map = {
        "exec": theme.wire_exec,
        "any": theme.wire_data,
        "bool": theme.wire_bool,
        "boolean": theme.wire_bool,
        "string": theme.wire_string,
        "str": theme.wire_string,
        "number": theme.wire_number,
        "int": theme.wire_number,
        "float": theme.wire_number,
        "list": theme.wire_list,
        "array": theme.wire_list,
        "dict": theme.wire_dict,
        "object": theme.wire_dict,
    }
    return type_map.get(data_type.lower(), theme.wire_data)


def get_status_color(status: str, theme: CanvasThemeColors = None) -> str:
    """
    Get color for a general status string.

    Args:
        status: Status string.
        theme: Optional theme instance (uses defaults if None)

    Returns:
        Hex color string.
    """
    if theme is None:
        return STATUS_COLOR_MAP.get(status.lower(), "#a1a1aa")

    status_map = {
        "success": theme.status_success,
        "completed": theme.status_success,
        "warning": theme.status_warning,
        "running": theme.status_running,
        "error": theme.status_error,
        "failed": theme.status_error,
        "info": theme.status_info,
        "idle": theme.status_idle,
    }
    return status_map.get(status.lower(), theme.text_secondary)

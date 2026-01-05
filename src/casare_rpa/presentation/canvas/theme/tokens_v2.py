"""
Design Tokens v2 - Cursor/VS Code-like (Dark-Only, Compact).

This is a parallel token system for the v2 UI redesign.
Key differences from v1 (TOKENS):
- Dark-only neutral ramp (no light mode)
- Cursor-like blue accent (#0066ff instead of Indigo)
- Compact typography (1 step smaller)
- Tight spacing (4px grid with 6px exception)
- Small consistent radii (0/2/3/4/6 vs 0/4/8/12/20)
- Zero-motion animations (all 0ms)

Usage:
    from casare_rpa.presentation.canvas.theme import TOKENS_V2

    # Spacing
    layout.setSpacing(TOKENS_V2.spacing.md)

    # Typography
    font.setPointSize(TOKENS_V2.typography.body)

    # Colors via THEME_V2
    from casare_rpa.presentation.canvas.theme import THEME_V2
    widget.setStyleSheet(f"background: {THEME_V2.bg_surface};")

See: docs/UX_REDESIGN_PLAN.md Phase 1 Epic 1.1
"""

from __future__ import annotations

from dataclasses import dataclass

# =============================================================================
# COLOR PALETTE (Dark-Only)
# =============================================================================


@dataclass(frozen=True)
class NeutralRampV2:
    """
    Cursor-like neutral scale for dark mode only.

    Darker than v1's zinc scale for deeper blacks.
    """

    n950: str = "#080808"  # Deepest background (canvas)
    n900: str = "#0f0f0f"  # Surface background (panels)
    n800: str = "#1a1a1a"  # Elevated (dropdowns, popups)
    n700: str = "#252525"  # Component background (inputs)
    n600: str = "#303030"  # Border default
    n500: str = "#404040"  # Border light, hover
    n400: str = "#606060"  # Text disabled
    n300: str = "#808080"  # Text secondary
    n200: str = "#a0a0a0"  # Text primary
    n100: str = "#c0c0c0"  # Text header


@dataclass(frozen=True)
class AccentRampV2:
    """
    Cursor-like blue accent ramp.

    Uses electric blue (#0066ff) as primary, matching Cursor IDE.
    """

    base: str = "#0066ff"  # Primary accent
    hover: str = "#3385ff"  # Hover state
    active: str = "#0052cc"  # Pressed/active
    subtle: str = "#0066ff20"  # ~12.5% alpha for backgrounds


@dataclass(frozen=True)
class SemanticColorsV2:
    """
    Status colors (unchanged from v1 for consistency).
    """

    success: str = "#10b981"  # Emerald
    warning: str = "#f59e0b"  # Amber
    error: str = "#ef4444"  # Red
    info: str = "#f97316"  # Orange


@dataclass(frozen=True)
class ThemeColorsV2:
    """
    Unified theme colors v2 - single source of truth.

    Combines neutral, accent, and semantic ramps into semantic names.
    Named by function, not appearance (e.g., "bg_surface" not "dark-gray").
    """

    # === BACKGROUNDS ===
    bg_canvas: str = "#080808"  # Main canvas - deepest
    bg_surface: str = "#0f0f0f"  # Panels, dialogs
    bg_elevated: str = "#1a1a1a"  # Modals, dropdowns
    bg_component: str = "#252525"  # Inputs, cards
    bg_hover: str = "#303030"  # Hover state
    bg_selected: str = "#0066ff20"  # Selection highlight (subtle blue)
    bg_header: str = "#080808"  # Header bars (top areas are black)

    # === BORDERS ===
    border: str = "#303030"  # Default border
    border_light: str = "#404040"  # Lighter border
    border_dark: str = "#1a1a1a"  # Darker border
    border_focus: str = "#0066ff"  # Focus ring (Cursor blue)

    # === TEXT ===
    text_primary: str = "#a0a0a0"  # Main text
    text_secondary: str = "#808080"  # Secondary text
    text_muted: str = "#606060"  # Muted/placeholder
    text_disabled: str = "#404040"  # Disabled text
    text_header: str = "#c0c0c0"  # Headers

    # === BRAND (Cursor Blue) ===
    primary: str = "#0066ff"  # Primary brand color
    primary_hover: str = "#3385ff"  # Primary hover
    primary_active: str = "#0052cc"  # Primary pressed
    secondary: str = "#6366f1"  # Indigo (used for categories / secondary accents)

    # === STATUS ===
    success: str = "#10b981"
    success_hover: str = "#34d399"  # Lighter green for hover
    warning: str = "#f59e0b"
    warning_hover: str = "#fbbf24"  # Lighter amber for hover
    error: str = "#ef4444"
    error_hover: str = "#f87171"  # Lighter red for hover
    error_active: str = "#dc2626"  # Darker red for active
    info: str = "#f97316"
    info_hover: str = "#fb923c"  # Lighter orange for hover

    # === TEXT ON STATUS BACKGROUNDS ===
    text_on_primary: str = "#ffffff"
    text_on_success: str = "#ffffff"
    text_on_warning: str = "#ffffff"
    text_on_error: str = "#ffffff"

    # === NODE GRAPH ===
    bg_node: str = "#0f0f0f"
    bg_node_header: str = "#0f0f0f"
    bg_node_selected: str = "#0066ff20"
    node_idle: str = "#404040"
    node_disabled_wash: str = "#606060"
    node_running: str = "#f59e0b"
    node_success: str = "#10b981"
    node_error: str = "#ef4444"
    node_skipped: str = "#a78bfa"
    node_breakpoint: str = "#ef4444"

    # === WIRES (same as v1 for consistency) ===
    wire_exec: str = "#ffffff"
    wire_data: str = "#6366f1"
    wire_string: str = "#f97316"
    wire_number: str = "#10b981"
    wire_bool: str = "#3b82f6"
    wire_list: str = "#a78bfa"
    wire_dict: str = "#2dd4bf"
    wire_any: str = "#6366f1"
    wire_table: str = "#3b82f6"

    # === UI COMPONENTS ===
    toolbar_bg: str = "#0f0f0f"
    toolbar_border: str = "#1a1a1a"
    menu_bg: str = "#1a1a1a"
    menu_border: str = "#404040"
    input_bg: str = "#1a1a1a"
    input_border: str = "#303030"
    scrollbar_bg: str = "#0f0f0f"
    scrollbar_handle: str = "#303030"
    scrollbar_hover: str = "#404040"

    # === SELECTOR PICKER ===
    selector_text: str = "#3b82f6"  # Blue for included attributes
    selector_highlight: str = "#0066ff40"  # Selection highlight (semi-transparent blue)

    # === DATA TYPE COLORS ===
    type_string: str = wire_string
    type_integer: str = wire_number
    type_float: str = wire_number
    type_boolean: str = wire_bool
    type_list: str = wire_list
    type_dict: str = wire_dict
    type_any: str = wire_any

    # === NODE CATEGORY COLORS ===
    category_basic: str = "#71717a"
    category_browser: str = "#6366f1"
    category_control_flow: str = "#ec4899"
    category_data: str = "#10b981"
    category_data_operations: str = "#10b981"
    category_database: str = "#06b6d4"
    category_debug: str = "#f59e0b"
    category_desktop: str = "#f59e0b"
    category_desktop_automation: str = "#f59e0b"
    category_document: str = "#8b5cf6"
    category_email: str = "#06b6d4"
    category_error_handling: str = "#ec4899"
    category_file: str = "#8b5cf6"
    category_file_operations: str = "#8b5cf6"
    category_google: str = "#4285f4"
    category_http: str = "#ef4444"
    category_interaction: str = "#6366f1"
    category_messaging: str = "#06b6d4"
    category_microsoft: str = "#00a4ef"
    category_navigation: str = "#6366f1"
    category_office_automation: str = "#00a4ef"
    category_rest_api: str = "#ef4444"
    category_scripts: str = "#71717a"
    category_system: str = "#71717a"
    category_triggers: str = "#ec4899"
    category_utility: str = "#71717a"
    category_variable: str = "#14b8a6"
    category_wait: str = "#14b8a6"

    # === SYNTAX COLORS (VSCode Dark+) ===
    syntax_keyword: str = "#C586C0"
    syntax_function: str = "#DCDCAA"
    syntax_string: str = "#CE9178"
    syntax_number: str = "#B5CEA8"
    syntax_comment: str = "#6A9955"
    syntax_builtin: str = "#4EC9B0"
    syntax_variable: str = "#9CDCFE"
    syntax_class: str = "#4EC9B0"
    syntax_regex: str = "#D16969"
    syntax_error: str = error

    # === JSON COLORS (VSCode Dark+) ===
    json_key: str = "#9CDCFE"
    json_string: str = "#CE9178"
    json_number: str = "#B5CEA8"
    json_boolean: str = "#569CD6"


# Global singleton for theme colors v2
THEME_V2 = ThemeColorsV2()


def get_wire_color(data_type: str) -> str:
    data_type_lower = (data_type or "").strip().lower()
    match data_type_lower:
        case "string":
            return THEME_V2.wire_string
        case "integer" | "int" | "float" | "number":
            return THEME_V2.wire_number
        case "boolean" | "bool":
            return THEME_V2.wire_bool
        case "list" | "array":
            return THEME_V2.wire_list
        case "dict" | "object" | "map":
            return THEME_V2.wire_dict
        case "exec":
            return THEME_V2.wire_exec
        case _:
            return THEME_V2.wire_any


def get_node_status_color(status: str) -> str:
    status_lower = (status or "").strip().lower()
    match status_lower:
        case "running":
            return THEME_V2.node_running
        case "success":
            return THEME_V2.node_success
        case "error":
            return THEME_V2.node_error
        case "skipped":
            return THEME_V2.node_skipped
        case "breakpoint":
            return THEME_V2.node_breakpoint
        case _:
            return THEME_V2.node_idle


def get_status_color(status: str) -> str:
    status_lower = (status or "").strip().lower()
    match status_lower:
        case "success":
            return THEME_V2.success
        case "warning":
            return THEME_V2.warning
        case "error":
            return THEME_V2.error
        case "info":
            return THEME_V2.info
        case _:
            return THEME_V2.text_muted


# =============================================================================
# COMPACT TYPOGRAPHY
# =============================================================================


@dataclass(frozen=True)
class TypographyV2:
    """
    Compact font sizes for dense UI (1 step smaller than v1).

    Uses Geist Sans/Mono as primary with Segoe UI/Cascadia Code fallbacks.
    """

    # Font families (Geist Sans/Mono as of Epic 1.2)
    sans: str = "'Geist Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    mono: str = "'Geist Mono', 'Cascadia Code', 'Consolas', monospace"
    ui: str = "'Geist Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    family: str = "'Geist Sans', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"

    # Compact type scale (1px smaller than v1 across the board)
    display_lg: int = 18  # Page titles
    display_md: int = 16  # Large headings
    heading_lg: int = 14  # Primary headings
    heading_md: int = 13  # Secondary headings
    heading_sm: int = 12  # Tertiary headings
    body_lg: int = 12  # Emphasized body
    body: int = 11  # Default body (was 12 in v1)
    body_sm: int = 10  # Secondary text (was 11 in v1)
    caption: int = 9  # Tiny labels (was 10 in v1)

    # Line heights (tighter for compact density)
    lh_tight: float = 1.2  # Headings
    lh_normal: float = 1.4  # Body
    lh_relaxed: float = 1.6  # Long-form

    # Font weights
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600


# =============================================================================
# TIGHT SPACING (4px Grid)
# =============================================================================


@dataclass(frozen=True)
class SpacingV2:
    """
    4px-based spacing, tighter presets than v1.

    Includes 6px (sm) for form row vertical spacing - practical exception
    to strict 4px grid.
    """

    zero: int = 0
    xxs: int = 2  # Ultra tight
    xs: int = 4  # Tight (icons in buttons)
    sm: int = 6  # Compact (form rows) - non-standard but practical
    md: int = 8  # Default gap
    lg: int = 12  # Section spacing
    xl: int = 16  # Large sections
    xxl: int = 24  # Major sections


@dataclass(frozen=True)
class MarginV2:
    """Common margin presets using SpacingV2 values."""

    none: tuple[int, int, int, int] = (0, 0, 0, 0)
    tight: tuple[int, int, int, int] = (2, 2, 2, 2)
    compact: tuple[int, int, int, int] = (4, 4, 4, 4)
    standard: tuple[int, int, int, int] = (6, 6, 6, 6)
    comfortable: tuple[int, int, int, int] = (8, 8, 8, 8)
    spacious: tuple[int, int, int, int] = (12, 12, 12, 12)

    # Component-specific margins
    dialog: tuple[int, int, int, int] = (12, 12, 12, 12)
    panel: tuple[int, int, int, int] = (8, 8, 8, 8)
    toolbar: tuple[int, int, int, int] = (8, 4, 8, 4)
    form_row: tuple[int, int, int, int] = (0, 6, 0, 6)


# =============================================================================
# SMALL CONSISTENT RADII
# =============================================================================


@dataclass(frozen=True)
class RadiusV2:
    """
    Small border radius for compact look (smaller than v1).

    v1: 0/4/8/12/20
    v2: 0/2/3/4/6
    """

    none: int = 0
    xs: int = 2  # Tags, chips
    sm: int = 3  # Inputs, buttons (v1 uses 4)
    md: int = 4  # Cards, panels (v1 uses 8)
    lg: int = 6  # Dialogs (v1 uses 12)


# =============================================================================
# BORDER RULES
# =============================================================================


@dataclass(frozen=True)
class BorderV2:
    """
    Border specification - always 1px.

    No thick borders, focus ring is also 1px for minimal look.
    """

    width: int = 1  # Always 1px
    focus_width: int = 1  # Focus ring also 1px
    style: str = "solid"
    focus_style: str = "solid"


# =============================================================================
# ZERO MOTION
# =============================================================================


@dataclass(frozen=True)
class MotionV2:
    """
    Zero-motion tokens - all durations are 0ms.

    Explicit no-animation policy for instant UI responses.
    """

    instant: int = 0
    fast: int = 0
    normal: int = 0
    slow: int = 0


# =============================================================================
# COMPONENT SIZES (Compact)
# =============================================================================


@dataclass(frozen=True)
class SizesV2:
    """
    Standard component sizes for v2.

    Heights align with compact density (slightly smaller than v1).
    """

    # Button heights (smaller than v1)
    button_sm: int = 22
    button_md: int = 28
    button_lg: int = 34
    button_min_width: int = 70
    button_width_sm: int = 60
    button_width_md: int = 90

    # Input heights (align with button heights)
    input_sm: int = 22
    input_md: int = 28
    input_lg: int = 34
    input_min_width: int = 100
    input_max_width: int = 350

    # Dialog sizes
    dialog_sm_width: int = 380
    dialog_md_width: int = 550
    dialog_lg_width: int = 750
    dialog_xl_width: int = 900
    dialog_min_height: int = 180
    dialog_height_sm: int = 270
    dialog_height_md: int = 400
    dialog_height_lg: int = 700
    dialog_height_xl: int = 800

    # Window
    window_default_height: int = 650

    # Dropdown
    combo_dropdown_width: int = 160
    combo_width_sm: int = 120
    combo_width_md: int = 160

    # Icon sizes
    icon_sm: int = 16
    icon_md: int = 20
    icon_lg: int = 24
    icon_xl: int = 32

    # Panel/dock sizes
    panel_min_width: int = 180
    panel_default_width: int = 280
    panel_max_width: int = 450

    # Sidebar
    sidebar_width_default: int = 230

    # Toolbar
    toolbar_height: int = 36

    # Status bar
    statusbar_height: int = 22

    # Tab bar
    tab_height: int = 32
    tab_min_width: int = 90

    # Menu
    menu_item_height: int = 28
    menu_min_width: int = 180

    # Table/list
    row_height: int = 28
    row_height_compact: int = 22
    column_width_sm: int = 60
    column_width_md: int = 120
    column_width_lg: int = 180

    # Scrollbar
    scrollbar_width: int = 8
    scrollbar_min_height: int = 18

    # Splitter
    splitter_handle: int = 4

    # Checkbox/radio
    checkbox_size: int = 16

    # Node editor
    node_width_min: int = 90
    node_header_height: int = 28
    node_port_spacing: int = 18

    # Additional input/form sizes
    input_sm_width: int = 100  # Small input width (dropdown element type)
    slider_handle_size: int = 14  # Slider handle diameter

    # List/preview sizes
    list_max_height: int = 200  # Maximum height for list widgets
    thumbnail_width: int = 80  # Image preview thumbnail width
    thumbnail_height: int = 60  # Image preview thumbnail height

    # Footer
    footer_height: int = 52  # Dialog footer height


# =============================================================================
# Z-INDEX (Same as v1)
# =============================================================================


@dataclass(frozen=True)
class ZIndexV2:
    """Z-index stacking order."""

    base: int = 0
    dropdown: int = 1000
    sticky: int = 1020
    fixed: int = 1030
    modal_backdrop: int = 1040
    modal: int = 1050
    popover: int = 1060
    tooltip: int = 1070


# =============================================================================
# UNIFIED TOKENS V2
# =============================================================================


@dataclass(frozen=True)
class DesignTokensV2:
    """
    Unified design tokens v2 - single entry point for new UI.

    Usage:
        from casare_rpa.presentation.canvas.theme import TOKENS_V2

        # Spacing
        gap = TOKENS_V2.spacing.md

        # Typography
        font_size = TOKENS_V2.typography.body

        # Colors
    from casare_rpa.presentation.canvas.theme import THEME_V2
        bg = THEME_V2.bg_surface
    """

    spacing: SpacingV2 = SpacingV2()
    margin: MarginV2 = MarginV2()
    radius: RadiusV2 = RadiusV2()
    border: BorderV2 = BorderV2()
    typography: TypographyV2 = TypographyV2()
    sizes: SizesV2 = SizesV2()
    motion: MotionV2 = MotionV2()
    z_index: ZIndexV2 = ZIndexV2()


# Global singleton
TOKENS_V2 = DesignTokensV2()

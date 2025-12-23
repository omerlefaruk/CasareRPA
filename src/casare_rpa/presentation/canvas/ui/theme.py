"""
CasareRPA Unified Theme System.

Provides consistent visual styling across all UI components.
Dark theme only with centralized color management.

Usage:
    from casare_rpa.presentation.canvas.ui.theme import Theme

    # Get current colors
    colors = Theme.get_colors()
    bg = colors.background

    # Generate CSS for specific component
    style = Theme.button_style("md")
    style = Theme.panel_style()
    style = Theme.message_box_style()
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# =============================================================================
# ASSET PATHS
# =============================================================================

ASSETS_DIR = Path(__file__).parent.parent / "assets"
CHECKMARK_PATH = (ASSETS_DIR / "checkmark.svg").as_posix()


# =============================================================================
# THEME MODE ENUM
# =============================================================================


class ThemeMode(Enum):
    """Available theme modes."""

    DARK = "dark"


# =============================================================================
# FROZEN DATACLASSES FOR THEME COMPONENTS
# =============================================================================


@dataclass(frozen=True)
class Colors:
    """Color palette for the theme."""

    # Primary colors
    primary: str
    primary_hover: str
    primary_pressed: str

    # Secondary colors
    secondary: str
    secondary_hover: str

    # Accent colors
    accent: str
    accent_hover: str

    # Background colors
    background: str
    background_alt: str
    surface: str
    surface_hover: str
    header: str

    # Text colors
    text_primary: str
    text_secondary: str
    text_muted: str
    text_disabled: str
    text_header: str

    # Border colors
    border: str
    border_light: str
    border_dark: str
    border_focus: str

    # Status colors
    error: str
    warning: str
    success: str
    info: str

    # Selection
    selection: str

    # Node-specific colors
    node_background: str
    node_border: str
    node_selected: str
    node_header: str
    node_idle: str
    node_running: str
    node_success: str
    node_error: str
    node_skipped: str

    # Port/Wire colors
    port_exec: str
    port_data: str
    wire_exec: str
    wire_data: str
    wire_bool: str
    wire_string: str
    wire_number: str
    wire_list: str
    wire_dict: str
    wire_table: str

    # Toolbar
    toolbar_bg: str
    toolbar_border: str
    toolbar_button_hover: str
    toolbar_button_pressed: str

    # Dock/panel
    dock_title_bg: str
    dock_title_text: str
    splitter_handle: str


@dataclass(frozen=True)
class Spacing:
    """Spacing values in pixels."""

    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32


@dataclass(frozen=True)
class BorderRadius:
    """Border radius values in pixels."""

    none: int = 0
    sm: int = 4
    md: int = 8
    lg: int = 12
    full: int = 9999


@dataclass(frozen=True)
class FontSizes:
    """Font sizes in points."""

    xs: int = 10
    sm: int = 11
    md: int = 12
    lg: int = 14
    xl: int = 16
    xxl: int = 20


@dataclass(frozen=True)
class ButtonSizes:
    """Standard button heights in pixels."""

    sm: int = 24  # Compact spaces
    md: int = 28  # Inline/form buttons
    lg: int = 32  # Action/dialog buttons


@dataclass(frozen=True)
class IconSizes:
    """Icon sizes in pixels."""

    xs: int = 12
    sm: int = 16
    md: int = 24
    lg: int = 32


@dataclass(frozen=True)
class Animations:
    """Animation durations in milliseconds.

    Guidelines:
    - instant: Button press feedback, immediate response
    - fast: Hover effects, quick micro-interactions
    - normal: Standard fade/slide transitions
    - medium: Panel transitions, tab switching
    - slow: Modal dialogs, emphasis effects
    - emphasis: Attention-grabbing animations (shake, pulse)

    Usage:
        from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS
        duration = ANIMATIONS.normal  # 150ms
    """

    instant: int = 50  # Button press, immediate feedback
    fast: int = 100  # Hover effects
    normal: int = 150  # Standard fade/slide (was 300, reduced for snappier feel)
    medium: int = 200  # Panel transitions
    slow: int = 300  # Modal dialogs (was 500)
    emphasis: int = 400  # Attention effects (shake, pulse)


# =============================================================================
# TYPE BADGE SYSTEM (for Variable Picker)
# =============================================================================


TYPE_COLORS: dict[str, str] = {
    "String": "#4ec9b0",  # Teal
    "Integer": "#569cd6",  # Blue
    "Float": "#9cdcfe",  # Light Blue
    "Boolean": "#c586c0",  # Purple
    "List": "#ce9178",  # Orange
    "Dict": "#dcdcaa",  # Yellow
    "DataTable": "#d16d9e",  # Pink
    "Any": "#AAAAAA",  # Light gray (WCAG 4.5:1 compliant)
}

TYPE_BADGES: dict[str, str] = {
    "String": "T",
    "Integer": "#",
    "Float": ".",
    "Boolean": "?",
    "List": "[]",
    "Dict": "{}",
    "DataTable": "tbl",
    "Any": "*",
}


# =============================================================================
# CANVAS COLORS - Unified NodeGraph Styling
# =============================================================================
# Single source of truth for all canvas/NodeGraphQt colors.
# Resolves conflicts between custom_node_item.py and category_utils.py.


@dataclass(frozen=True)
class CanvasColors:
    """
    Centralized color definitions for NodeGraph canvas components.

    This replaces scattered hardcoded colors in:
    - custom_node_item.py (_CATEGORY_HEADER_COLORS)
    - custom_pipe.py (TYPE_WIRE_COLORS)
    - category_utils.py (ROOT_CATEGORY_COLORS)
    - node_icons.py (CATEGORY_COLORS)
    """

    # -------------------------------------------------------------------------
    # Category Header Colors (for node headers)
    # BOLD, VIBRANT, DISTINCT colors - each category easily recognizable
    # -------------------------------------------------------------------------
    category_browser: str = "#9C27B0"  # PURPLE - Browser automation
    category_desktop: str = "#E91E63"  # PINK - Desktop automation
    category_control_flow: str = "#F44336"  # RED - Control flow (if/loop/switch)
    category_error_handling: str = "#D32F2F"  # DARK RED - Error handling
    category_data: str = "#4CAF50"  # GREEN - Data operations
    category_variable: str = "#2196F3"  # BLUE - Variables
    category_database: str = "#00BCD4"  # CYAN - Database operations
    category_rest_api: str = "#FF5722"  # DEEP ORANGE - REST API
    category_file: str = "#FFC107"  # AMBER/YELLOW - File operations
    category_office_automation: str = "#217346"  # EXCEL GREEN - Office/Excel
    category_email: str = "#EA4335"  # GMAIL RED - Email
    category_google: str = "#4285F4"  # GOOGLE BLUE - Google services
    category_triggers: str = "#7C4DFF"  # DEEP PURPLE - Triggers/Events
    category_messaging: str = "#25D366"  # WHATSAPP GREEN - Messaging

    category_document: str = "#FF9800"  # ORANGE - Documents
    category_utility: str = "#607D8B"  # BLUE GRAY - Utilities
    category_basic: str = "#3F51B5"  # INDIGO - Basic nodes
    category_scripts: str = "#CDDC39"  # LIME - Scripts/Code
    category_system: str = "#795548"  # BROWN - System operations
    category_navigation: str = "#673AB7"  # VIOLET - Navigation
    category_interaction: str = "#03A9F4"  # LIGHT BLUE - Interaction
    category_wait: str = "#FF5722"  # DEEP ORANGE - Wait/Timing
    category_debug: str = "#9E9E9E"  # GRAY - Debug
    category_default: str = "#546E7A"  # SLATE - Default fallback

    # -------------------------------------------------------------------------
    # Wire Colors by DataType
    # -------------------------------------------------------------------------
    wire_exec: str = "#FFFFFF"  # White - execution flow (prominent)
    wire_string: str = "#CE9178"  # Orange-brown
    wire_integer: str = "#B5CEA8"  # Light green
    wire_float: str = "#B5CEA8"  # Light green (same as integer)
    wire_boolean: str = "#569CD6"  # Blue
    wire_list: str = "#C586C0"  # Purple
    wire_dict: str = "#4EC9B0"  # Teal
    wire_page: str = "#C586C0"  # Purple - browser page
    wire_element: str = "#C586C0"  # Purple - browser element
    wire_window: str = "#9CDCFE"  # Light blue - desktop window
    wire_desktop_element: str = "#9CDCFE"  # Light blue
    wire_db_connection: str = "#4EC9B0"  # Teal
    wire_workbook: str = "#217B4B"  # Office green
    wire_worksheet: str = "#217B4B"  # Office green
    wire_datatable: str = "#569CD6"  # Blue
    wire_document: str = "#FF9800"  # Orange
    wire_any: str = "#808080"  # Gray - fallback
    wire_default: str = "#808080"  # Gray
    wire_incompatible: str = "#F44336"  # Red - type mismatch

    # -------------------------------------------------------------------------
    # Status Colors (for node state indicators)
    # -------------------------------------------------------------------------
    status_success: str = "#22C55E"  # Green 500
    status_error: str = "#EF4444"  # Red 500
    status_warning: str = "#F59E0B"  # Amber 500
    status_running: str = "#FBBF24"  # Amber 400 (animated)
    status_idle: str = "#6B6B6B"  # Gray
    status_skipped: str = "#A1A1AA"  # Zinc 400
    status_disabled: str = "#3F3F46"  # Zinc 700
    status_breakpoint: str = "#EF4444"  # Red 500

    # -------------------------------------------------------------------------
    # Node Visual Elements
    # -------------------------------------------------------------------------
    node_bg: str = "#27272A"  # Zinc 800 - node body
    node_bg_header: str = "#3F3F46"  # Zinc 700 - header area
    node_border_normal: str = "#3F3F46"  # Zinc 700
    node_border_selected: str = "#FBBF24"  # Amber 400 - selection highlight
    node_border_running: str = "#FBBF24"  # Amber 400 - animated
    node_border_hover: str = "#52525B"  # Zinc 600
    node_text_title: str = "#FAFAFA"  # Zinc 50 - title text
    node_text_port: str = "#D4D4D8"  # Zinc 300 - port labels
    node_text_secondary: str = "#A1A1AA"  # Zinc 400 - secondary text

    # -------------------------------------------------------------------------
    # Badges and Indicators
    # -------------------------------------------------------------------------
    badge_bg: str = "#18181B"  # Zinc 900
    badge_text: str = "#E4E4E7"  # Zinc 200
    badge_border: str = "#3F3F46"  # Zinc 700

    # -------------------------------------------------------------------------
    # Collapse Button
    # -------------------------------------------------------------------------
    collapse_btn_bg: str = "#3F3F46"  # Zinc 700
    collapse_btn_bg_hover: str = "#52525B"  # Zinc 600
    collapse_btn_symbol: str = "#D4D4D8"  # Zinc 300

    # -------------------------------------------------------------------------
    # Wire Visual Effects
    # -------------------------------------------------------------------------
    wire_flow_dot: str = "#FFFFFF"  # White flow indicator
    wire_flow_glow: str = "#FFFFFF50"  # Semi-transparent glow
    wire_completion_glow: str = "#22C55E99"  # Green with alpha
    wire_hover: str = "#64B5F6"  # Light blue hover
    wire_insert_highlight: str = "#FF8C00"  # Orange insertion point

    # -------------------------------------------------------------------------
    # Labels and Previews
    # -------------------------------------------------------------------------
    label_bg: str = "#27272A"  # Zinc 800
    label_border: str = "#52525B"  # Zinc 600
    label_text: str = "#D4D4D8"  # Zinc 300
    preview_bg: str = "#32322D"  # Yellowish dark
    preview_border: str = "#64645A"  # Yellowish border
    preview_text: str = "#DCDCB4"  # Yellowish text


# Dark theme canvas colors (only theme supported)
DARK_CANVAS_COLORS = CanvasColors()


# =============================================================================
# DISABLED STATE VISUAL CONSTANTS
# =============================================================================
# Used by CasareNodeItem.paint() for disabled node rendering.
# Centralized here for consistency and easy adjustment.

# Opacity multiplier for disabled overlay (0.0 = invisible, 1.0 = fully opaque)
NODE_DISABLED_OPACITY: float = 0.5  # More prominent grayscale effect

# Background alpha for disabled nodes (0-255)
NODE_DISABLED_BG_ALPHA: int = 50  # ~20% opacity - clearly grayed out

# Overlay wash alpha for disabled effect (0-255)
NODE_DISABLED_WASH_ALPHA: int = 180  # Stronger desaturation wash

# Border width for disabled state (thicker dotted line for visibility)
NODE_DISABLED_BORDER_WIDTH: float = 2.5

# Border style: Use Qt.PenStyle.DotLine for dotted border
NODE_DISABLED_BORDER_STYLE: str = "dot"


# =============================================================================
# QCOLOR CACHE - Performance optimization for paint() methods
# =============================================================================
# Avoid creating QColor objects on every paint call.
# Colors are cached on first access and reused.

from PySide6.QtGui import QColor as _QColor

_qcolor_cache: dict[str, "_QColor"] = {}


def _hex_to_qcolor(hex_color: str) -> "_QColor":
    """
    Convert hex color string to QColor, with caching.

    Args:
        hex_color: Color in #RRGGBB or #RRGGBBAA format

    Returns:
        Cached QColor instance
    """
    if hex_color not in _qcolor_cache:
        _qcolor_cache[hex_color] = _QColor(hex_color)
    return _qcolor_cache[hex_color]


def _rgb_to_qcolor(r: int, g: int, b: int, a: int = 255) -> "_QColor":
    """
    Convert RGB(A) values to QColor, with caching.

    Args:
        r, g, b: RGB values (0-255)
        a: Alpha value (0-255), default 255

    Returns:
        Cached QColor instance
    """
    key = f"rgb({r},{g},{b},{a})"
    if key not in _qcolor_cache:
        _qcolor_cache[key] = _QColor(r, g, b, a)
    return _qcolor_cache[key]


# =============================================================================
# CATEGORY COLOR MAPPING
# =============================================================================
# Maps category names to their colors for fast lookup

CATEGORY_COLOR_MAP: dict[str, str] = {
    "browser": DARK_CANVAS_COLORS.category_browser,
    "navigation": DARK_CANVAS_COLORS.category_navigation,
    "interaction": DARK_CANVAS_COLORS.category_interaction,
    "data": DARK_CANVAS_COLORS.category_data,
    "data_operations": DARK_CANVAS_COLORS.category_data,
    "variable": DARK_CANVAS_COLORS.category_variable,
    "control_flow": DARK_CANVAS_COLORS.category_control_flow,
    "error_handling": DARK_CANVAS_COLORS.category_error_handling,
    "wait": DARK_CANVAS_COLORS.category_wait,
    "debug": DARK_CANVAS_COLORS.category_debug,
    "utility": DARK_CANVAS_COLORS.category_utility,
    "file": DARK_CANVAS_COLORS.category_file,
    "file_operations": DARK_CANVAS_COLORS.category_file,
    "database": DARK_CANVAS_COLORS.category_database,
    "rest_api": DARK_CANVAS_COLORS.category_rest_api,
    "email": DARK_CANVAS_COLORS.category_email,
    "office_automation": DARK_CANVAS_COLORS.category_office_automation,
    "desktop": DARK_CANVAS_COLORS.category_desktop,
    "desktop_automation": DARK_CANVAS_COLORS.category_desktop,
    "triggers": DARK_CANVAS_COLORS.category_triggers,
    "messaging": DARK_CANVAS_COLORS.category_messaging,
    "document": DARK_CANVAS_COLORS.category_document,
    "google": DARK_CANVAS_COLORS.category_google,
    "scripts": DARK_CANVAS_COLORS.category_scripts,
    "system": DARK_CANVAS_COLORS.category_system,
    "basic": DARK_CANVAS_COLORS.category_basic,
}


# =============================================================================
# DARK THEME COLOR PALETTE (VSCode Dark+)
# =============================================================================

DARK_COLORS = Colors(
    # Primary colors
    primary="#007ACC",
    primary_hover="#1177BB",
    primary_pressed="#005A9E",
    # Secondary colors
    secondary="#3E3E42",
    secondary_hover="#454545",
    # Accent colors
    accent="#007ACC",
    accent_hover="#1177BB",
    # Background colors
    background="#1E1E1E",
    background_alt="#252526",
    surface="#2D2D30",
    surface_hover="#2A2D2E",
    header="#2D2D30",
    # Text colors
    text_primary="#D4D4D4",
    text_secondary="#CCCCCC",
    text_muted="#A6A6A6",
    text_disabled="#6B6B6B",
    text_header="#BBBBBB",
    # Border colors
    border="#3E3E42",
    border_light="#454545",
    border_dark="#252526",
    border_focus="#007ACC",
    # Status colors
    error="#F48771",
    warning="#D7BA7D",
    success="#89D185",
    info="#75BEFF",
    # Selection
    selection="#264F78",
    # Node-specific colors
    node_background="#252526",
    node_border="#3E3E42",
    node_selected="#264F78",
    node_header="#2D2D30",
    node_idle="#6B6B6B",
    node_running="#D7BA7D",
    node_success="#89D185",
    node_error="#F48771",
    node_skipped="#C586C0",
    # Port/Wire colors
    port_exec="#FFFFFF",
    port_data="#007ACC",
    wire_exec="#FFFFFF",
    wire_data="#007ACC",
    wire_bool="#F48771",
    wire_string="#CE9178",
    wire_number="#B5CEA8",
    wire_list="#C586C0",
    wire_dict="#4EC9B0",
    wire_table="#569CD6",
    # Toolbar
    toolbar_bg="#2D2D30",
    toolbar_border="#3E3E42",
    toolbar_button_hover="#2A2D2E",
    toolbar_button_pressed="#0078D4",
    # Dock/panel
    dock_title_bg="#2D2D30",
    dock_title_text="#BBBBBB",
    splitter_handle="#3E3E42",
)


# =============================================================================
# SINGLETON INSTANCES
# =============================================================================

SPACING = Spacing()
BORDER_RADIUS = BorderRadius()
FONT_SIZES = FontSizes()
BUTTON_SIZES = ButtonSizes()
ICON_SIZES = IconSizes()
ANIMATIONS = Animations()


# =============================================================================
# THEME CLASS
# =============================================================================


class Theme:
    """
    Main theme class with getters and CSS generation helpers.

    This is a singleton-style class that provides static access to theme values.
    """

    _mode: ThemeMode = ThemeMode.DARK

    @classmethod
    def get_mode(cls) -> ThemeMode:
        """Get the current theme mode."""
        return cls._mode

    @classmethod
    def set_mode(cls, mode: ThemeMode) -> None:
        """
        Set the theme mode.

        Args:
            mode: ThemeMode.DARK (only dark mode supported)
        """
        cls._mode = mode

    @classmethod
    def get_colors(cls) -> Colors:
        """Get the current color palette (dark theme only)."""
        return DARK_COLORS

    @classmethod
    def get_spacing(cls) -> Spacing:
        """Get spacing values."""
        return SPACING

    @classmethod
    def get_border_radius(cls) -> BorderRadius:
        """Get border radius values."""
        return BORDER_RADIUS

    @classmethod
    def get_font_sizes(cls) -> FontSizes:
        """Get font size values."""
        return FONT_SIZES

    @classmethod
    def get_button_sizes(cls) -> ButtonSizes:
        """Get button height values."""
        return BUTTON_SIZES

    @classmethod
    def get_icon_sizes(cls) -> IconSizes:
        """Get icon size values."""
        return ICON_SIZES

    @classmethod
    def get_animations(cls) -> Animations:
        """Get animation duration values."""
        return ANIMATIONS

    # =========================================================================
    # CANVAS COLOR ACCESSORS
    # =========================================================================

    @classmethod
    def get_canvas_colors(cls) -> CanvasColors:
        """
        Get canvas-specific colors (dark theme only).

        Returns:
            CanvasColors instance for NodeGraph styling
        """
        return DARK_CANVAS_COLORS

    @classmethod
    def get_category_color(cls, category: str) -> str:
        """
        Get hex color for a node category.

        Args:
            category: Category name (may be hierarchical like "google/gmail")

        Returns:
            Hex color string (e.g., "#C586C0")
        """
        if not category:
            return cls.get_canvas_colors().category_default

        # Extract root category from hierarchical path
        root = category.split("/")[0].lower()
        return CATEGORY_COLOR_MAP.get(root, cls.get_canvas_colors().category_default)

    @classmethod
    def get_category_qcolor(cls, category: str) -> "_QColor":
        """
        Get QColor for a node category (cached for performance).

        Use this in paint() methods to avoid per-frame allocations.

        Args:
            category: Category name

        Returns:
            Cached QColor instance
        """
        hex_color = cls.get_category_color(category)
        return _hex_to_qcolor(hex_color)

    @classmethod
    def get_wire_color(cls, data_type: str) -> str:
        """
        Get hex color for a wire based on data type.

        Args:
            data_type: DataType name (STRING, INTEGER, LIST, etc.)

        Returns:
            Hex color string
        """
        cc = cls.get_canvas_colors()
        wire_map = {
            "EXEC": cc.wire_exec,
            "STRING": cc.wire_string,
            "INTEGER": cc.wire_integer,
            "INT": cc.wire_integer,
            "FLOAT": cc.wire_float,
            "BOOLEAN": cc.wire_boolean,
            "BOOL": cc.wire_boolean,
            "LIST": cc.wire_list,
            "DICT": cc.wire_dict,
            "PAGE": cc.wire_page,
            "ELEMENT": cc.wire_element,
            "BROWSER": cc.wire_page,
            "WINDOW": cc.wire_window,
            "DESKTOP_ELEMENT": cc.wire_desktop_element,
            "DB_CONNECTION": cc.wire_db_connection,
            "WORKBOOK": cc.wire_workbook,
            "WORKSHEET": cc.wire_worksheet,
            "DATATABLE": cc.wire_datatable,
            "DOCUMENT": cc.wire_document,
            "OBJECT": cc.wire_any,
            "ANY": cc.wire_any,
        }
        return wire_map.get(data_type.upper() if data_type else "", cc.wire_default)

    @classmethod
    def get_wire_qcolor(cls, data_type: str) -> "_QColor":
        """
        Get QColor for a wire (cached for performance).

        Args:
            data_type: DataType name

        Returns:
            Cached QColor instance
        """
        hex_color = cls.get_wire_color(data_type)
        return _hex_to_qcolor(hex_color)

    @classmethod
    def get_status_qcolor(cls, status: str) -> "_QColor":
        """
        Get QColor for a node execution status.

        Args:
            status: Status string (success, error, running, idle, skipped)

        Returns:
            Cached QColor instance
        """
        cc = cls.get_canvas_colors()
        status_map = {
            "success": cc.status_success,
            "completed": cc.status_success,
            "error": cc.status_error,
            "failed": cc.status_error,
            "warning": cc.status_warning,
            "running": cc.status_running,
            "idle": cc.status_idle,
            "skipped": cc.status_skipped,
            "disabled": cc.status_disabled,
            "breakpoint": cc.status_breakpoint,
        }
        hex_color = status_map.get(status.lower() if status else "", cc.status_idle)
        return _hex_to_qcolor(hex_color)

    @classmethod
    def get_node_border_qcolor(cls, state: str = "normal") -> "_QColor":
        """
        Get QColor for node border based on state.

        Args:
            state: "normal", "selected", "running", or "hover"

        Returns:
            Cached QColor instance
        """
        cc = cls.get_canvas_colors()
        state_map = {
            "normal": cc.node_border_normal,
            "selected": cc.node_border_selected,
            "running": cc.node_border_running,
            "hover": cc.node_border_hover,
        }
        hex_color = state_map.get(state, cc.node_border_normal)
        return _hex_to_qcolor(hex_color)

    @classmethod
    def get_node_bg_qcolor(cls) -> "_QColor":
        """Get cached QColor for node background."""
        return _hex_to_qcolor(cls.get_canvas_colors().node_bg)

    @classmethod
    def get_badge_colors(cls) -> tuple:
        """
        Get badge colors as QColor tuple.

        Returns:
            Tuple of (bg_qcolor, text_qcolor, border_qcolor)
        """
        cc = cls.get_canvas_colors()
        return (
            _hex_to_qcolor(cc.badge_bg),
            _hex_to_qcolor(cc.badge_text),
            _hex_to_qcolor(cc.badge_border),
        )

    # =========================================================================
    # CSS GENERATION HELPERS
    # =========================================================================

    @classmethod
    def button_style(cls, size: str = "md", variant: str = "default") -> str:
        """
        Generate QPushButton stylesheet.

        Args:
            size: "sm" (24px), "md" (28px), or "lg" (32px)
            variant: "default", "primary", or "danger"

        Returns:
            QSS stylesheet string
        """
        c = cls.get_colors()
        sizes = cls.get_button_sizes()
        height = getattr(sizes, size, sizes.md)

        if variant == "primary":
            return f"""
                QPushButton {{
                    background-color: {c.primary};
                    border: 1px solid {c.primary};
                    border-radius: 4px;
                    padding: 0 12px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                    min-height: {height}px;
                }}
                QPushButton:hover {{
                    background-color: {c.primary_hover};
                    border-color: {c.primary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {c.primary_pressed};
                }}
                QPushButton:disabled {{
                    background-color: {c.secondary};
                    color: {c.text_disabled};
                    border-color: {c.border};
                }}
            """
        elif variant == "danger":
            return f"""
                QPushButton {{
                    background-color: {c.error};
                    border: 1px solid {c.error};
                    border-radius: 4px;
                    padding: 0 12px;
                    color: #FFFFFF;
                    font-size: 12px;
                    font-weight: 600;
                    min-height: {height}px;
                }}
                QPushButton:hover {{
                    background-color: #FF6B5B;
                }}
                QPushButton:disabled {{
                    background-color: {c.secondary};
                    color: {c.text_disabled};
                }}
            """
        else:
            return f"""
                QPushButton {{
                    background-color: {c.surface};
                    border: 1px solid {c.border_light};
                    border-radius: 4px;
                    padding: 0 16px;
                    color: {c.text_primary};
                    font-size: 12px;
                    font-weight: 500;
                    min-height: {height}px;
                }}
                QPushButton:hover {{
                    background-color: {c.surface_hover};
                    border-color: {c.accent};
                    color: #FFFFFF;
                }}
                QPushButton:pressed {{
                    background-color: {c.secondary_hover};
                }}
                QPushButton:disabled {{
                    background-color: {c.surface};
                    color: {c.text_disabled};
                    border-color: {c.border_dark};
                }}
            """

    @classmethod
    def panel_style(cls) -> str:
        """
        Generate panel/card stylesheet.

        Returns:
            QSS stylesheet string for panels
        """
        c = cls.get_colors()
        return f"""
            QFrame {{
                background-color: {c.background_alt};
                border: 1px solid {c.border_dark};
                border-radius: 4px;
            }}
        """

    @classmethod
    def input_style(cls) -> str:
        """
        Generate QLineEdit stylesheet.

        Returns:
            QSS stylesheet string for inputs
        """
        c = cls.get_colors()
        return f"""
            QLineEdit {{
                background-color: {c.background};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 28px;
                selection-background-color: {c.accent};
            }}
            QLineEdit:focus {{
                border-color: {c.border_focus};
            }}
            QLineEdit:disabled {{
                background-color: {c.surface};
                color: {c.text_disabled};
            }}
        """

    @classmethod
    def message_box_style(cls) -> str:
        """
        Generate QMessageBox stylesheet.

        Use this instead of QMessageBox static methods to ensure consistent styling.

        Returns:
            QSS stylesheet string for message boxes
        """
        c = cls.get_colors()
        return f"""
            QMessageBox {{
                background: {c.background_alt};
            }}
            QMessageBox QLabel {{
                color: {c.text_primary};
                font-size: 12px;
            }}
            QPushButton {{
                background: {c.surface};
                border: 1px solid {c.border_light};
                border-radius: 4px;
                padding: 0 16px;
                color: {c.text_primary};
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {c.surface_hover};
                border-color: {c.accent};
                color: #FFFFFF;
            }}
            QPushButton:default {{
                background: {c.accent};
                border-color: {c.accent};
                color: #FFFFFF;
            }}
        """

    @classmethod
    def toolbar_button_style(cls) -> str:
        """
        Generate QToolButton stylesheet.

        Returns:
            QSS stylesheet string for toolbar buttons
        """
        c = cls.get_colors()
        return f"""
            QToolButton {{
                background-color: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                color: {c.text_secondary};
                font-weight: 500;
            }}
            QToolButton:hover {{
                background-color: {c.toolbar_button_hover};
                color: {c.text_primary};
            }}
            QToolButton:pressed {{
                background-color: {c.toolbar_button_pressed};
            }}
            QToolButton:checked {{
                background-color: {c.accent};
                color: #FFFFFF;
            }}
        """

    @classmethod
    def combo_box_style(cls) -> str:
        """
        Generate QComboBox stylesheet.

        Returns:
            QSS stylesheet string for combo boxes
        """
        c = cls.get_colors()
        return f"""
            QComboBox {{
                background-color: {c.background};
                color: {c.text_primary};
                border: 1px solid {c.border};
                border-radius: 4px;
                padding: 6px 10px;
                min-height: 28px;
            }}
            QComboBox:hover {{
                border-color: {c.border_light};
            }}
            QComboBox:focus {{
                border-color: {c.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {c.text_secondary};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c.surface};
                border: 1px solid {c.border};
                selection-background-color: {c.accent};
                outline: none;
            }}
        """

    @classmethod
    def variable_button_style(cls) -> str:
        """
        Generate variable picker button stylesheet.

        Returns:
            QSS stylesheet string for variable picker buttons
        """
        c = cls.get_colors()
        return f"""
            QPushButton {{
                background: {c.surface};
                border: 1px solid {c.border};
                border-radius: 3px;
                color: #FFFFFF;
                font-size: 10px;
                font-family: Consolas, monospace;
                padding: 2px 4px;
                min-width: 20px;
                max-width: 24px;
                min-height: 18px;
                max-height: 18px;
            }}
            QPushButton:hover {{
                background: {c.accent};
                border-color: {c.accent};
            }}
        """


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_node_status_color(status: str) -> str:
    """
    Get the color for a node execution status.

    Args:
        status: Node status string (idle, running, success, error, skipped)

    Returns:
        Hex color string for the status.
    """
    c = Theme.get_colors()
    status_map = {
        "idle": c.node_idle,
        "running": c.node_running,
        "success": c.node_success,
        "error": c.node_error,
        "skipped": c.node_skipped,
        "breakpoint": c.error,
    }
    return status_map.get(status.lower(), c.node_idle)


def get_wire_color(data_type: str) -> str:
    """
    Get the color for a connection wire based on data type.

    Args:
        data_type: The data type of the connection.

    Returns:
        Hex color string for the wire.
    """
    c = Theme.get_colors()
    type_map = {
        "exec": c.wire_exec,
        "any": c.wire_data,
        "bool": c.wire_bool,
        "boolean": c.wire_bool,
        "string": c.wire_string,
        "str": c.wire_string,
        "number": c.wire_number,
        "int": c.wire_number,
        "float": c.wire_number,
        "list": c.wire_list,
        "array": c.wire_list,
        "dict": c.wire_dict,
        "object": c.wire_dict,
        "table": c.wire_table,
        "datatable": c.wire_table,
    }
    return type_map.get(data_type.lower(), c.wire_data)


def get_status_color(status: str) -> str:
    """
    Get color for a general status string.

    Args:
        status: Status string.

    Returns:
        Hex color string.
    """
    c = Theme.get_colors()
    status_map = {
        "success": c.success,
        "completed": c.success,
        "warning": c.warning,
        "running": c.warning,
        "error": c.error,
        "failed": c.error,
        "info": c.info,
        "idle": c.node_idle,
        "ready": c.success,
        "paused": c.info,
    }
    return status_map.get(status.lower(), c.text_secondary)


def get_type_color(type_name: str) -> str:
    """
    Get color for a data type (for variable picker badges).

    Args:
        type_name: Type name string (String, Integer, Boolean, etc.)

    Returns:
        Hex color string.
    """
    return TYPE_COLORS.get(type_name, TYPE_COLORS["Any"])


def get_type_badge(type_name: str) -> str:
    """
    Get badge character for a data type.

    Args:
        type_name: Type name string.

    Returns:
        Badge character(s).
    """
    return TYPE_BADGES.get(type_name, TYPE_BADGES["Any"])


# =============================================================================
# MAIN APPLICATION STYLESHEET
# =============================================================================


def get_canvas_stylesheet() -> str:
    """
    Generate the main Canvas application stylesheet.

    Returns:
        Complete QSS stylesheet for the Canvas application.
    """
    c = Theme.get_colors()
    return f"""
/* ==================== MAIN WINDOW ==================== */
QMainWindow {{
    background-color: {c.background_alt};
}}

QMainWindow::separator {{
    background-color: {c.splitter_handle};
    width: 3px;
    height: 3px;
}}

QMainWindow::separator:hover {{
    background-color: {c.accent};
}}

/* ==================== BASE WIDGET ==================== */
QWidget {{
    background-color: transparent;
    color: {c.text_primary};
    font-family: 'Segoe UI', 'SF Pro Text', system-ui, sans-serif;
    font-size: 12px;
}}

/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {c.header};
    color: {c.text_primary};
    border-bottom: 1px solid {c.border_dark};
    padding: 2px 4px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {c.surface_hover};
}}

QMenu {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    border-radius: 6px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {c.accent};
    color: #FFFFFF;
}}

QMenu::separator {{
    height: 1px;
    background-color: rgba(255, 255, 255, 0.15);
    margin: 6px 10px;
}}

/* ==================== TOOLBAR ==================== */
QToolBar {{
    background-color: {c.toolbar_bg};
    border: none;
    border-bottom: 1px solid {c.toolbar_border};
    padding: 4px 6px;
    spacing: 4px;
}}

QToolBar::separator {{
    background-color: {c.toolbar_border};
    width: 1px;
    margin: 6px 8px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    color: {c.text_secondary};
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {c.toolbar_button_hover};
    color: {c.text_primary};
}}

QToolButton:pressed {{
    background-color: {c.toolbar_button_pressed};
}}

QToolButton:checked {{
    background-color: {c.accent};
    color: #FFFFFF;
}}

QToolButton::menu-indicator {{
    image: none;
}}

/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {c.accent};
    border-top: none;
    color: #FFFFFF;
    font-size: 11px;
    padding: 2px 8px;
}}

QStatusBar::item {{
    border: none;
}}

/* ==================== DOCK WIDGETS ==================== */
QDockWidget {{
    background-color: {c.background_alt};
    border: 1px solid {c.border_dark};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {c.dock_title_bg};
    color: {c.dock_title_text};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid {c.border_dark};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {c.surface_hover};
    border-radius: 3px;
}}

/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    background-color: {c.background_alt};
    border: 1px solid {c.border_dark};
    border-top: none;
}}

QTabBar {{
    background-color: {c.header};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {c.text_secondary};
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {c.background_alt};
    color: {c.text_primary};
    border-bottom: 2px solid {c.accent};
}}

QTabBar::tab:hover:!selected {{
    background-color: {c.surface_hover};
    color: {c.text_primary};
}}

/* ==================== TABLES ==================== */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {c.background_alt};
    alternate-background-color: {c.background};
    border: 1px solid {c.border_dark};
    gridline-color: {c.border_dark};
    selection-background-color: {c.selection};
    selection-color: {c.text_primary};
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {c.border_dark};
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {c.selection};
}}

QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
    background-color: {c.surface_hover};
}}

/* ==================== HEADER VIEW ==================== */
QHeaderView {{
    background-color: {c.header};
}}

QHeaderView::section {{
    background-color: {c.header};
    color: {c.text_header};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {c.border_dark};
    border-bottom: 1px solid {c.border_dark};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {c.surface_hover};
    color: {c.text_primary};
}}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {{
    background: {c.background};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {c.secondary_hover};
    min-height: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c.border_light};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {c.background};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {c.secondary_hover};
    min-width: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c.border_light};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {c.surface_hover};
    border-color: {c.border_light};
}}

QPushButton:pressed {{
    background-color: {c.secondary_hover};
}}

QPushButton:disabled {{
    background-color: {c.surface};
    color: {c.text_disabled};
    border-color: {c.border_dark};
}}

QPushButton[primary="true"] {{
    background-color: {c.accent};
    border-color: {c.accent};
    color: #FFFFFF;
}}

QPushButton[primary="true"]:hover {{
    background-color: {c.accent_hover};
}}

QPushButton[danger="true"] {{
    background-color: {c.error};
    border-color: {c.error};
    color: #FFFFFF;
}}

/* ==================== LINE EDIT ==================== */
QLineEdit {{
    background-color: {c.background};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {c.accent};
}}

QLineEdit:focus {{
    border-color: {c.border_focus};
}}

QLineEdit:disabled {{
    background-color: {c.surface};
    color: {c.text_disabled};
}}

/* ==================== COMBO BOX ==================== */
QComboBox {{
    background-color: {c.background};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 24px;
}}

QComboBox:hover {{
    border-color: {c.border_light};
}}

QComboBox:focus {{
    border-color: {c.border_focus};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c.text_secondary};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {c.surface};
    border: 1px solid {c.border};
    selection-background-color: {c.accent};
    outline: none;
}}

/* ==================== SPIN BOX ==================== */
QSpinBox, QDoubleSpinBox {{
    background-color: {c.background};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: 4px;
    padding: 6px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {c.border_focus};
}}

/* ==================== CHECK BOX ==================== */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {c.border};
    border-radius: 3px;
    background-color: {c.background};
}}

QCheckBox::indicator:unchecked:hover {{
    border-color: {c.accent};
}}

QCheckBox::indicator:checked {{
    background-color: {c.accent};
    border-color: {c.accent};
    image: url({CHECKMARK_PATH});
}}

QCheckBox::indicator:checked:hover {{
    background-color: {c.accent_hover};
    border-color: {c.accent_hover};
}}

/* ==================== PROGRESS BAR ==================== */
QProgressBar {{
    background-color: {c.surface};
    border: 1px solid {c.border_dark};
    border-radius: 3px;
    height: 18px;
    text-align: center;
    color: {c.text_primary};
    font-size: 10px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background-color: {c.accent};
    border-radius: 2px;
}}

/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {c.splitter_handle};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QSplitter::handle:hover {{
    background-color: {c.accent};
}}

/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {c.background_alt};
    border: 1px solid {c.border};
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {c.text_secondary};
}}

/* ==================== TOOLTIP ==================== */
QToolTip {{
    background-color: {c.surface};
    color: {c.text_primary};
    border: 1px solid {c.border};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* ==================== TEXT EDIT (LOGS) ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: {c.background};
    color: {c.text_primary};
    border: 1px solid {c.border_dark};
    font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
    font-size: 11px;
    selection-background-color: {c.accent};
}}

/* ==================== LABEL ==================== */
QLabel {{
    background: transparent;
    background-color: transparent;
    color: {c.text_primary};
}}

QLabel[muted="true"] {{
    color: {c.text_muted};
}}

QLabel[secondary="true"] {{
    color: {c.text_secondary};
}}

QLabel[heading="true"] {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel[subheading="true"] {{
    font-size: 11px;
    color: {c.text_secondary};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ==================== FRAME ==================== */
QFrame[panel="true"] {{
    background-color: {c.background_alt};
    border: 1px solid {c.border_dark};
}}

/* ==================== EMPTY STATE GUIDANCE ==================== */
QLabel[empty-state="true"] {{
    color: {c.text_muted};
    font-size: 13px;
    padding: 20px;
}}

/* ==================== DIALOGS ==================== */
QDialog {{
    background-color: {c.background_alt};
    color: {c.text_primary};
}}

QMessageBox {{
    background-color: {c.background_alt};
    color: {c.text_primary};
}}

QMessageBox QLabel {{
    color: {c.text_primary};
    background-color: transparent;
}}

QMessageBox QPushButton {{
    min-width: 70px;
}}

QInputDialog {{
    background-color: {c.background_alt};
    color: {c.text_primary};
}}

QInputDialog QLabel {{
    color: {c.text_primary};
}}

QFileDialog {{
    background-color: {c.background_alt};
    color: {c.text_primary};
}}
"""


# =============================================================================
# BACKWARD COMPATIBILITY - Legacy access via THEME global
# =============================================================================


class _LegacyThemeColors:
    """
    Legacy compatibility wrapper for CanvasThemeColors.

    Provides attribute-style access to theme colors for backward compatibility.
    """

    def __getattr__(self, name: str) -> str:
        c = Theme.get_colors()
        # Map old attribute names to new Colors dataclass
        mapping = {
            "bg_darkest": c.background,
            "bg_dark": c.background_alt,
            "bg_medium": c.surface,
            "bg_light": c.surface,
            "bg_lighter": c.secondary_hover,
            "bg_panel": c.background_alt,
            "bg_header": c.header,
            "bg_hover": c.surface_hover,
            "bg_selected": c.selection,
            "bg_canvas": c.background,
            "bg_node": c.node_background,
            "bg_node_selected": c.node_selected,
            "bg_node_header": c.node_header,
            "bg_darker": c.background,
            "border_dark": c.border_dark,
            "border": c.border,
            "border_light": c.border_light,
            "border_focus": c.border_focus,
            "text_primary": c.text_primary,
            "text_secondary": c.text_secondary,
            "text_muted": c.text_muted,
            "text_disabled": c.text_disabled,
            "text_header": c.text_header,
            "status_success": c.success,
            "status_warning": c.warning,
            "status_error": c.error,
            "status_info": c.info,
            "status_running": c.warning,
            "status_idle": c.node_idle,
            "node_idle": c.node_idle,
            "node_running": c.node_running,
            "node_success": c.node_success,
            "node_error": c.node_error,
            "node_skipped": c.node_skipped,
            "node_breakpoint": c.error,
            "selection_bg": c.selection,
            "input_bg": c.surface,
            "accent_primary": c.accent,
            "accent_secondary": c.selection,
            "accent_hover": c.accent_hover,
            "accent_success": c.success,
            "accent_warning": c.warning,
            "accent_error": c.error,
            # Additional theme colors for widgets
            "accent": c.accent,
            "accent_dark": c.primary_pressed,
            "accent_darker": "#1D4ED8",  # Deep blue for pressed states
            "success": c.success,
            "warning": c.warning,
            "error": c.error,
            "error_bg": "#5A1D1D",  # Dark red background for error states
            "hover": c.surface_hover,
            "selected": c.selection,
            "scrollbar": c.secondary_hover,
            "scrollbar_hover": c.border_light,
            "button_bg": c.surface,
            "button_hover": c.surface_hover,
            "link": "#569CD6",  # Blue for links
            "link_hover": "#9CDCFE",  # Light blue for link hover
            "selector_text": "#60A5FA",  # Blue for selector text
            # JSON syntax colors
            "json_key": "#9CDCFE",  # Light blue for keys
            "json_string": "#CE9178",  # Orange-brown for strings
            "json_number": "#B5CEA8",  # Light green for numbers
            "json_boolean": "#569CD6",  # Blue for booleans
            "wire_exec": c.wire_exec,
            "wire_data": c.wire_data,
            "wire_bool": c.wire_bool,
            "wire_string": c.wire_string,
            "wire_number": c.wire_number,
            "wire_list": c.wire_list,
            "wire_dict": c.wire_dict,
            "wire_table": c.wire_table,
            "toolbar_bg": c.toolbar_bg,
            "toolbar_border": c.toolbar_border,
            "toolbar_button_hover": c.toolbar_button_hover,
            "toolbar_button_pressed": c.toolbar_button_pressed,
            "dock_title_bg": c.dock_title_bg,
            "dock_title_text": c.dock_title_text,
            "splitter_handle": c.splitter_handle,
        }
        if name in mapping:
            return mapping[name]
        raise AttributeError(f"'_LegacyThemeColors' has no attribute '{name}'")


# Legacy global for backward compatibility
THEME = _LegacyThemeColors()

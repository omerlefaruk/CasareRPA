"""
CasareRPA Unified Theme System.

Provides consistent visual styling across all UI components.
Supports light and dark themes with centralized color management.

Usage:
    from casare_rpa.presentation.canvas.ui.theme import Theme, ThemeMode

    # Get current colors
    colors = Theme.get_colors()
    bg = colors.background

    # Generate CSS for specific component
    style = Theme.button_style("md")
    style = Theme.panel_style()
    style = Theme.message_box_style()

    # Switch themes
    Theme.set_mode(ThemeMode.LIGHT)
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Optional


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

    LIGHT = "light"
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


TYPE_COLORS: Dict[str, str] = {
    "String": "#4ec9b0",  # Teal
    "Integer": "#569cd6",  # Blue
    "Float": "#9cdcfe",  # Light Blue
    "Boolean": "#c586c0",  # Purple
    "List": "#ce9178",  # Orange
    "Dict": "#dcdcaa",  # Yellow
    "DataTable": "#d16d9e",  # Pink
    "Any": "#AAAAAA",  # Light gray (WCAG 4.5:1 compliant)
}

TYPE_BADGES: Dict[str, str] = {
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
# LIGHT THEME COLOR PALETTE
# =============================================================================

LIGHT_COLORS = Colors(
    # Primary colors
    primary="#0078D4",
    primary_hover="#106EBE",
    primary_pressed="#005A9E",
    # Secondary colors
    secondary="#E1E1E1",
    secondary_hover="#D0D0D0",
    # Accent colors
    accent="#0078D4",
    accent_hover="#106EBE",
    # Background colors
    background="#FFFFFF",
    background_alt="#F3F3F3",
    surface="#FAFAFA",
    surface_hover="#E8E8E8",
    header="#F0F0F0",
    # Text colors
    text_primary="#1E1E1E",
    text_secondary="#333333",
    text_muted="#6B6B6B",
    text_disabled="#A0A0A0",
    text_header="#444444",
    # Border colors
    border="#D0D0D0",
    border_light="#E0E0E0",
    border_dark="#C0C0C0",
    border_focus="#0078D4",
    # Status colors
    error="#E74C3C",
    warning="#F39C12",
    success="#27AE60",
    info="#3498DB",
    # Selection
    selection="#ADD6FF",
    # Node-specific colors
    node_background="#FFFFFF",
    node_border="#D0D0D0",
    node_selected="#ADD6FF",
    node_header="#F0F0F0",
    node_idle="#A0A0A0",
    node_running="#F39C12",
    node_success="#27AE60",
    node_error="#E74C3C",
    node_skipped="#9B59B6",
    # Port/Wire colors
    port_exec="#333333",
    port_data="#0078D4",
    wire_exec="#333333",
    wire_data="#0078D4",
    wire_bool="#E74C3C",
    wire_string="#E67E22",
    wire_number="#27AE60",
    wire_list="#9B59B6",
    wire_dict="#16A085",
    wire_table="#2980B9",
    # Toolbar
    toolbar_bg="#F0F0F0",
    toolbar_border="#D0D0D0",
    toolbar_button_hover="#E0E0E0",
    toolbar_button_pressed="#0078D4",
    # Dock/panel
    dock_title_bg="#F0F0F0",
    dock_title_text="#444444",
    splitter_handle="#D0D0D0",
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
            mode: ThemeMode.LIGHT or ThemeMode.DARK
        """
        cls._mode = mode

    @classmethod
    def get_colors(cls) -> Colors:
        """Get the current color palette based on theme mode."""
        return DARK_COLORS if cls._mode == ThemeMode.DARK else LIGHT_COLORS

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

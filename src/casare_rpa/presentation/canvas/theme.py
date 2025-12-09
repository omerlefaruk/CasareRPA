"""
Unified Theme System for CasareRPA Canvas.

Provides consistent styling across the visual workflow editor,
aligned with the Orchestrator color palette for a cohesive look.
"""

from dataclasses import dataclass
from pathlib import Path

# Get assets directory path
ASSETS_DIR = Path(__file__).parent / "assets"
CHECKMARK_PATH = (ASSETS_DIR / "checkmark.svg").as_posix()


@dataclass
class CanvasThemeColors:
    """
    Premium Dark theme colors.

    A sophisticated dark palette using deep zinc grays and vibrant indigo accents
    for a modern, professional, and accessible interface.
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


# Global theme instance
THEME = CanvasThemeColors()


def get_canvas_stylesheet() -> str:
    """
    Generate the main Canvas application stylesheet.

    Returns:
        Complete QSS stylesheet for the Canvas application.
    """
    return f"""
/* ==================== MAIN WINDOW ==================== */
QMainWindow {{
    background-color: {THEME.bg_darkest};
}}

QMainWindow::separator {{
    background-color: {THEME.bg_darkest}; /* Seamless splitter */
    width: 4px;
    height: 4px;
}}

QMainWindow::separator:hover {{
    background-color: {THEME.accent_primary}; /* Highlight on hover */
}}

/* ==================== BASE WIDGET ==================== */
QWidget {{
    background-color: transparent;
    color: {THEME.text_primary};
    font-family: 'Segoe UI', 'Inter', 'Roboto', system-ui, sans-serif;
    font-size: 13px; /* Slightly larger for readability */
}}

/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {THEME.bg_header};
    color: {THEME.text_primary};
    border-bottom: 1px solid {THEME.border};
    padding: 4px 6px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {THEME.bg_hover};
    color: {THEME.text_primary};
}}

QMenu {{
    background-color: {THEME.bg_dark}; /* Darker menu */
    border: 1px solid {THEME.border_light};
    border-radius: 8px; /* Rounded corners */
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 32px 8px 12px;
    border-radius: 4px;
    margin: 2px 0;
}}

QMenu::item:selected {{
    background-color: {THEME.accent_primary};
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background-color: {THEME.bg_light};
    margin: 4px 10px;
}}

/* ==================== TOOLBAR ==================== */
QToolBar {{
    background-color: {THEME.toolbar_bg};
    border: none;
    border-bottom: 1px solid {THEME.border};
    padding: 8px 12px;
    spacing: 8px;
}}

QToolBar::separator {{
    background-color: {THEME.border};
    width: 1px;
    margin: 4px 8px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    color: {THEME.text_secondary};
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {THEME.bg_hover};
    color: {THEME.text_primary};
}}

QToolButton:pressed {{
    background-color: {THEME.bg_medium};
}}

QToolButton:checked {{
    background-color: {THEME.accent_primary};
    color: #ffffff;
}}

/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {THEME.bg_darkest};
    border-top: 1px solid {THEME.border};
    color: {THEME.text_secondary};
    font-size: 11px;
    padding: 4px 12px;
}}

QStatusBar::item {{
    border: none;
}}

/* ==================== DOCK WIDGETS ==================== */
QDockWidget {{
    background-color: {THEME.bg_panel};
    border: none;
    color: {THEME.text_primary};
}}

QDockWidget::title {{
    background-color: {THEME.bg_panel};
    color: {THEME.text_secondary};
    padding: 10px 16px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid {THEME.border};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 4px;
    icon-size: 14px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {THEME.bg_hover};
    border-radius: 4px;
}}

/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    background-color: {THEME.bg_panel};
    border: none;
    border-top: 1px solid {THEME.border};
}}

QTabBar {{
    background-color: {THEME.bg_panel};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {THEME.text_secondary};
    padding: 12px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    color: {THEME.text_primary};
    border-bottom: 2px solid {THEME.accent_primary};
}}

QTabBar::tab:hover:!selected {{
    color: {THEME.text_primary};
    background-color: {THEME.bg_hover};
    border-radius: 4px 4px 0 0;
}}

/* ==================== TABLES ==================== */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {THEME.bg_dark}; /* Slightly lighter than canvas */
    alternate-background-color: {THEME.bg_darkest};
    border: none;
    selection-background-color: {THEME.bg_selected};
    selection-color: #ffffff;
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {THEME.bg_darkest}; /* Subtle separation */
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {THEME.bg_selected};
    border-radius: 4px;
}}

QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
    background-color: {THEME.bg_hover};
}}

/* ==================== HEADER VIEW ==================== */
QHeaderView {{
    background-color: {THEME.bg_panel};
    border: none;
}}

QHeaderView::section {{
    background-color: {THEME.bg_panel};
    color: {THEME.text_secondary};
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid {THEME.border};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}}

/* ==================== SCROLLBARS (Modern/Slim) ==================== */
QScrollBar:vertical {{
    background: {THEME.bg_darkest};
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {THEME.bg_light};
    min-height: 40px;
    border-radius: 4px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {THEME.bg_lighter};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {THEME.bg_darkest};
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {THEME.bg_light};
    min-width: 40px;
    border-radius: 4px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {THEME.bg_lighter};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {THEME.bg_medium};
    color: {THEME.text_primary};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {THEME.bg_light};
}}

QPushButton:pressed {{
    background-color: {THEME.bg_dark};
}}

QPushButton:disabled {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_disabled};
}}

QPushButton[primary="true"] {{
    background-color: {THEME.accent_primary};
    color: #ffffff;
}}

QPushButton[primary="true"]:hover {{
    background-color: {THEME.accent_hover};
}}

QPushButton[danger="true"] {{
    background-color: {THEME.status_error};
    color: #ffffff;
}}

/* ==================== INPUTS (Modern/Borderless) ==================== */
QLineEdit {{
    background-color: {THEME.input_bg};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {THEME.accent_primary};
}}

QLineEdit:focus {{
    border: 1px solid {THEME.accent_primary};
    background-color: {THEME.bg_dark};
}}

QLineEdit:disabled {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_disabled};
    border-color: transparent;
}}

/* ==================== COMBO BOX ==================== */
QComboBox {{
    background-color: {THEME.input_bg};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 28px;
}}

QComboBox:hover {{
    border-color: {THEME.border_light};
}}

QComboBox:focus {{
    border-color: {THEME.accent_primary};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {THEME.text_secondary};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {THEME.bg_dark};
    border: 1px solid {THEME.border_light};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {THEME.accent_primary};
    outline: none;
}}

/* ==================== SPIN BOX ==================== */
QSpinBox, QDoubleSpinBox {{
    background-color: {THEME.input_bg};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 24px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {THEME.accent_primary};
}}

/* ==================== CHECK BOX ==================== */
QCheckBox {{
    spacing: 8px;
    color: {THEME.text_primary};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {THEME.border_light};
    border-radius: 4px;
    background-color: {THEME.input_bg};
}}

QCheckBox::indicator:hover {{
    border-color: {THEME.accent_primary};
}}

QCheckBox::indicator:checked {{
    background-color: {THEME.accent_primary};
    border-color: {THEME.accent_primary};
    image: url({CHECKMARK_PATH});
}}

/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {THEME.bg_darkest};
}}

QSplitter::handle:hover {{
    background-color: {THEME.accent_primary};
}}

/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border};
    border-radius: 8px;
    margin-top: 20px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {THEME.text_secondary};
    font-weight: 600;
}}

/* ==================== TOOLTIP ==================== */
QToolTip {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border_light};
    border-radius: 4px;
    padding: 6px 12px;
}}

/* ==================== TEXT EDIT (LOGS) ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: {THEME.bg_darkest};
    color: {THEME.text_primary};
    border: none;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    padding: 8px;
    selection-background-color: {THEME.selection_bg};
}}
"""


def get_node_status_color(status: str) -> str:
    """
    Get the color for a node execution status.

    Args:
        status: Node status string (idle, running, success, error, skipped)

    Returns:
        Hex color string for the status.
    """
    status_map = {
        "idle": THEME.node_idle,
        "running": THEME.node_running,
        "success": THEME.node_success,
        "error": THEME.node_error,
        "skipped": THEME.node_skipped,
        "breakpoint": THEME.node_breakpoint,
    }
    return status_map.get(status.lower(), THEME.node_idle)


def get_wire_color(data_type: str) -> str:
    """
    Get the color for a connection wire based on data type.

    Args:
        data_type: The data type of the connection.

    Returns:
        Hex color string for the wire.
    """
    type_map = {
        "exec": THEME.wire_exec,
        "any": THEME.wire_data,
        "bool": THEME.wire_bool,
        "boolean": THEME.wire_bool,
        "string": THEME.wire_string,
        "str": THEME.wire_string,
        "number": THEME.wire_number,
        "int": THEME.wire_number,
        "float": THEME.wire_number,
        "list": THEME.wire_list,
        "array": THEME.wire_list,
        "dict": THEME.wire_dict,
        "object": THEME.wire_dict,
    }
    return type_map.get(data_type.lower(), THEME.wire_data)


def get_status_color(status: str) -> str:
    """
    Get color for a general status string.

    Args:
        status: Status string.

    Returns:
        Hex color string.
    """
    status_map = {
        "success": THEME.status_success,
        "completed": THEME.status_success,
        "warning": THEME.status_warning,
        "running": THEME.status_running,
        "error": THEME.status_error,
        "failed": THEME.status_error,
        "info": THEME.status_info,
        "idle": THEME.status_idle,
    }
    return status_map.get(status.lower(), THEME.text_secondary)

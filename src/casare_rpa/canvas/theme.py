"""
Unified Theme System for CasareRPA Canvas.

Provides consistent styling across the visual workflow editor,
aligned with the Orchestrator color palette for a cohesive look.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class CanvasThemeColors:
    """
    Canvas theme color palette.

    Aligned with Orchestrator theme for consistency across applications.
    Uses a modern professional dark theme with subtle blue undertones.
    """

    # Base backgrounds (neutral dark grays)
    bg_darkest: str = "#0f1114"
    bg_dark: str = "#121417"
    bg_medium: str = "#1a1d21"
    bg_light: str = "#22262b"
    bg_lighter: str = "#2a2f36"
    bg_panel: str = "#1e2126"
    bg_header: str = "#15171a"
    bg_hover: str = "#2a2f36"
    bg_selected: str = "#2d4a6f"

    # Node graph specific
    bg_canvas: str = "#1a1d21"
    bg_node: str = "#2a2f36"
    bg_node_selected: str = "#3a4555"
    bg_node_header: str = "#22262b"

    # Borders
    border_dark: str = "#1f2227"
    border: str = "#2a2f36"
    border_light: str = "#3a4046"
    border_focus: str = "#4a9eff"

    # Text - Minimum #9a9a9a for accessibility
    text_primary: str = "#e8eaed"
    text_secondary: str = "#9aa0a6"  # Above #9a9a9a threshold
    text_muted: str = "#7a7f85"      # Above #9a9a9a when used on dark bg
    text_disabled: str = "#5f6368"
    text_header: str = "#9aa0a6"

    # Status colors
    status_success: str = "#66bb6a"
    status_warning: str = "#ffb74d"
    status_error: str = "#ef5350"
    status_info: str = "#42a5f5"
    status_running: str = "#ffb74d"
    status_idle: str = "#5f6368"

    # Node status colors
    node_idle: str = "#5f6368"
    node_running: str = "#ffb74d"
    node_success: str = "#66bb6a"
    node_error: str = "#ef5350"
    node_skipped: str = "#9575cd"
    node_breakpoint: str = "#ef5350"

    # Accent colors
    accent_primary: str = "#4a9eff"
    accent_secondary: str = "#64b5f6"
    accent_success: str = "#66bb6a"
    accent_warning: str = "#ffb74d"
    accent_error: str = "#ef5350"

    # Connection/wire colors
    wire_exec: str = "#ffffff"
    wire_data: str = "#4a9eff"
    wire_bool: str = "#ef5350"
    wire_string: str = "#66bb6a"
    wire_number: str = "#ffb74d"
    wire_list: str = "#ab47bc"
    wire_dict: str = "#42a5f5"

    # Toolbar
    toolbar_bg: str = "#1a1d21"
    toolbar_border: str = "#2a2f36"
    toolbar_button_hover: str = "#2a2f36"
    toolbar_button_pressed: str = "#3a4046"

    # Dock/panel
    dock_title_bg: str = "#15171a"
    dock_title_text: str = "#9aa0a6"
    splitter_handle: str = "#1f2227"


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
    background-color: {THEME.bg_dark};
}}

QMainWindow::separator {{
    background-color: {THEME.splitter_handle};
    width: 3px;
    height: 3px;
}}

QMainWindow::separator:hover {{
    background-color: {THEME.accent_primary};
}}

/* ==================== BASE WIDGET ==================== */
QWidget {{
    background-color: transparent;
    color: {THEME.text_primary};
    font-family: 'Segoe UI', 'SF Pro Text', system-ui, sans-serif;
    font-size: 12px;
}}

/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {THEME.bg_header};
    color: {THEME.text_primary};
    border-bottom: 1px solid {THEME.border_dark};
    padding: 2px 4px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {THEME.bg_hover};
}}

QMenu {{
    background-color: {THEME.bg_light};
    border: 1px solid {THEME.border};
    border-radius: 6px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {THEME.accent_primary};
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background-color: {THEME.border};
    margin: 6px 8px;
}}

/* ==================== TOOLBAR ==================== */
QToolBar {{
    background-color: {THEME.toolbar_bg};
    border: none;
    border-bottom: 1px solid {THEME.toolbar_border};
    padding: 4px 6px;
    spacing: 4px;
}}

QToolBar::separator {{
    background-color: {THEME.toolbar_border};
    width: 1px;
    margin: 6px 8px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    color: {THEME.text_secondary};
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {THEME.toolbar_button_hover};
    color: {THEME.text_primary};
}}

QToolButton:pressed {{
    background-color: {THEME.toolbar_button_pressed};
}}

QToolButton:checked {{
    background-color: {THEME.accent_primary};
    color: #ffffff;
}}

QToolButton::menu-indicator {{
    image: none;
}}

/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {THEME.bg_header};
    border-top: 1px solid {THEME.border_dark};
    color: {THEME.text_secondary};
    font-size: 11px;
    padding: 2px 4px;
}}

QStatusBar::item {{
    border: none;
}}

/* ==================== DOCK WIDGETS ==================== */
QDockWidget {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border_dark};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {THEME.dock_title_bg};
    color: {THEME.dock_title_text};
    padding: 8px 12px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid {THEME.border_dark};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {THEME.bg_hover};
    border-radius: 3px;
}}

/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border_dark};
    border-top: none;
}}

QTabBar {{
    background-color: {THEME.bg_header};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {THEME.text_secondary};
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {THEME.bg_panel};
    color: {THEME.text_primary};
    border-bottom: 2px solid {THEME.accent_primary};
}}

QTabBar::tab:hover:!selected {{
    background-color: {THEME.bg_hover};
    color: {THEME.text_primary};
}}

/* ==================== TABLES ==================== */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {THEME.bg_panel};
    alternate-background-color: {THEME.bg_dark};
    border: 1px solid {THEME.border_dark};
    gridline-color: {THEME.border_dark};
    selection-background-color: {THEME.bg_selected};
    selection-color: {THEME.text_primary};
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {THEME.border_dark};
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {THEME.bg_selected};
}}

QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
    background-color: {THEME.bg_hover};
}}

/* ==================== HEADER VIEW ==================== */
QHeaderView {{
    background-color: {THEME.bg_header};
}}

QHeaderView::section {{
    background-color: {THEME.bg_header};
    color: {THEME.text_header};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {THEME.border_dark};
    border-bottom: 1px solid {THEME.border_dark};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {THEME.bg_hover};
    color: {THEME.text_primary};
}}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {{
    background: {THEME.bg_dark};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {THEME.bg_lighter};
    min-height: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {THEME.border_light};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {THEME.bg_dark};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {THEME.bg_lighter};
    min-width: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {THEME.border_light};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {THEME.bg_light};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 4px;
    padding: 6px 14px;
    font-weight: 500;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {THEME.bg_hover};
    border-color: {THEME.border_light};
}}

QPushButton:pressed {{
    background-color: {THEME.bg_lighter};
}}

QPushButton:disabled {{
    background-color: {THEME.bg_medium};
    color: {THEME.text_disabled};
    border-color: {THEME.border_dark};
}}

QPushButton[primary="true"] {{
    background-color: {THEME.accent_primary};
    border-color: {THEME.accent_primary};
    color: #ffffff;
}}

QPushButton[primary="true"]:hover {{
    background-color: #5ba8ff;
}}

QPushButton[danger="true"] {{
    background-color: {THEME.accent_error};
    border-color: {THEME.accent_error};
    color: #ffffff;
}}

/* ==================== LINE EDIT ==================== */
QLineEdit {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {THEME.accent_primary};
}}

QLineEdit:focus {{
    border-color: {THEME.border_focus};
}}

QLineEdit:disabled {{
    background-color: {THEME.bg_medium};
    color: {THEME.text_disabled};
}}

/* ==================== COMBO BOX ==================== */
QComboBox {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 24px;
}}

QComboBox:hover {{
    border-color: {THEME.border_light};
}}

QComboBox:focus {{
    border-color: {THEME.border_focus};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {THEME.text_secondary};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {THEME.bg_light};
    border: 1px solid {THEME.border};
    selection-background-color: {THEME.accent_primary};
    outline: none;
}}

/* ==================== SPIN BOX ==================== */
QSpinBox, QDoubleSpinBox {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 4px;
    padding: 6px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {THEME.border_focus};
}}

/* ==================== CHECK BOX ==================== */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {THEME.border};
    border-radius: 3px;
    background-color: {THEME.bg_dark};
}}

QCheckBox::indicator:checked {{
    background-color: {THEME.accent_primary};
    border-color: {THEME.accent_primary};
}}

QCheckBox::indicator:hover {{
    border-color: {THEME.border_light};
}}

/* ==================== PROGRESS BAR ==================== */
QProgressBar {{
    background-color: {THEME.bg_light};
    border: 1px solid {THEME.border_dark};
    border-radius: 3px;
    height: 18px;
    text-align: center;
    color: {THEME.text_primary};
    font-size: 10px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background-color: {THEME.accent_primary};
    border-radius: 2px;
}}

/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {THEME.splitter_handle};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QSplitter::handle:hover {{
    background-color: {THEME.accent_primary};
}}

/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border};
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {THEME.text_secondary};
}}

/* ==================== TOOLTIP ==================== */
QToolTip {{
    background-color: {THEME.bg_light};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* ==================== TEXT EDIT (LOGS) ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: {THEME.bg_darkest};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border_dark};
    font-family: 'Cascadia Code', 'Consolas', 'Monaco', monospace;
    font-size: 11px;
    selection-background-color: {THEME.accent_primary};
}}

/* ==================== LABEL ==================== */
QLabel {{
    background: transparent;
    color: {THEME.text_primary};
}}

QLabel[muted="true"] {{
    color: {THEME.text_muted};
}}

QLabel[secondary="true"] {{
    color: {THEME.text_secondary};
}}

QLabel[heading="true"] {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel[subheading="true"] {{
    font-size: 11px;
    color: {THEME.text_secondary};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ==================== FRAME ==================== */
QFrame[panel="true"] {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border_dark};
}}

/* ==================== EMPTY STATE GUIDANCE ==================== */
QLabel[empty-state="true"] {{
    color: {THEME.text_muted};
    font-size: 13px;
    padding: 20px;
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

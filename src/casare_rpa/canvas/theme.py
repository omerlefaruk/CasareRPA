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
    VSCode Dark+ theme colors - exact replication from microsoft/vscode repository.

    Colors sourced from dark_vs.json and dark_plus.json for pixel-perfect VSCode appearance.
    """

    # Base backgrounds (from VSCode dark_vs.json)
    bg_darkest: str = "#1E1E1E"        # VSCode editor background
    bg_dark: str = "#252526"           # VSCode sidebar/panel
    bg_medium: str = "#2D2D30"         # VSCode inactive tab
    bg_light: str = "#3E3E42"          # VSCode borders
    bg_lighter: str = "#454545"        # VSCode menu separator
    bg_panel: str = "#252526"          # Panel background
    bg_header: str = "#2D2D30"         # Header background
    bg_hover: str = "#2A2D2E"          # VSCode hover state
    bg_selected: str = "#0078D4"       # VSCode selection blue

    # Node graph specific
    bg_canvas: str = "#1E1E1E"         # Match editor background
    bg_node: str = "#252526"           # Nodes lighter than canvas
    bg_node_selected: str = "#264F78"  # VSCode editor selection
    bg_node_header: str = "#2D2D30"    # Node header

    # Borders (VSCode)
    border_dark: str = "#252526"       # Dark border
    border: str = "#3E3E42"            # Standard border
    border_light: str = "#454545"      # Light border
    border_focus: str = "#007ACC"      # Focus ring (VSCode blue)

    # Text (VSCode)
    text_primary: str = "#D4D4D4"      # VSCode editor foreground
    text_secondary: str = "#CCCCCC"    # VSCode menu foreground
    text_muted: str = "#A6A6A6"        # VSCode placeholder
    text_disabled: str = "#6B6B6B"     # VSCode checkbox border
    text_header: str = "#BBBBBB"       # VSCode sidebar title

    # Status colors (align with VSCode semantic colors from Dark+)
    status_success: str = "#89D185"    # Green (from Dark+)
    status_warning: str = "#D7BA7D"    # Yellow (from Dark+)
    status_error: str = "#F48771"      # Red (from Dark+)
    status_info: str = "#75BEFF"       # Info blue
    status_running: str = "#D7BA7D"    # Yellow
    status_idle: str = "#6B6B6B"       # Disabled gray

    # Node status
    node_idle: str = "#6B6B6B"
    node_running: str = "#D7BA7D"      # Warning yellow
    node_success: str = "#89D185"      # Success green
    node_error: str = "#F48771"        # Error red
    node_skipped: str = "#C586C0"      # Purple (control flow)
    node_breakpoint: str = "#F48771"   # Error red

    # Accent colors (VSCode blue)
    accent_primary: str = "#007ACC"    # VSCode signature blue
    accent_secondary: str = "#0078D4"  # Selection blue
    accent_success: str = "#89D185"
    accent_warning: str = "#D7BA7D"
    accent_error: str = "#F48771"

    # Wire colors (use VSCode syntax colors from Dark+)
    wire_exec: str = "#FFFFFF"         # White for execution
    wire_data: str = "#007ACC"         # Blue (VSCode accent)
    wire_bool: str = "#F48771"         # Red (error color)
    wire_string: str = "#CE9178"       # Orange (string color from Dark+)
    wire_number: str = "#B5CEA8"       # Light green (number color from Dark+)
    wire_list: str = "#C586C0"         # Purple (control flow from Dark+)
    wire_dict: str = "#4EC9B0"         # Teal (type color from Dark+)

    # Toolbar
    toolbar_bg: str = "#2D2D30"        # VSCode header
    toolbar_border: str = "#3E3E42"    # VSCode border
    toolbar_button_hover: str = "#2A2D2E"
    toolbar_button_pressed: str = "#0078D4"

    # Dock/panel
    dock_title_bg: str = "#2D2D30"     # VSCode header
    dock_title_text: str = "#BBBBBB"   # VSCode sidebar title
    splitter_handle: str = "#3E3E42"   # VSCode border


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
    background-color: {THEME.accent_primary};  /* VSCode signature blue #007ACC */
    border-top: none;
    color: #FFFFFF;  /* White text like VSCode */
    font-size: 11px;
    padding: 2px 8px;
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

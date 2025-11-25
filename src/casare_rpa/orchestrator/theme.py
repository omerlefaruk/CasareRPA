"""
Professional dark theme for CasareRPA Orchestrator.
Inspired by Deadline Monitor / industrial monitoring UIs.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeColors:
    """Theme color palette."""
    # Base backgrounds (darker, more industrial)
    bg_darkest: str = "#0d0d0d"
    bg_dark: str = "#141414"
    bg_medium: str = "#1c1c1c"
    bg_light: str = "#252525"
    bg_lighter: str = "#2d2d2d"
    bg_panel: str = "#1a1a1a"
    bg_header: str = "#181818"
    bg_row_alt: str = "#161616"
    bg_hover: str = "#2a2a2a"
    bg_selected: str = "#0a4d8c"
    bg_selected_inactive: str = "#333333"

    # Borders
    border_dark: str = "#0a0a0a"
    border: str = "#2a2a2a"
    border_light: str = "#3a3a3a"
    border_focus: str = "#0078d4"

    # Text
    text_primary: str = "#e0e0e0"
    text_secondary: str = "#a0a0a0"
    text_muted: str = "#666666"
    text_disabled: str = "#4a4a4a"
    text_header: str = "#b0b0b0"

    # Status colors (vibrant for visibility)
    status_online: str = "#00cc66"      # Green
    status_offline: str = "#666666"     # Gray
    status_busy: str = "#ffaa00"        # Orange
    status_error: str = "#ff3333"       # Red
    status_warning: str = "#ffcc00"     # Yellow
    status_idle: str = "#0099ff"        # Blue
    status_rendering: str = "#9966ff"   # Purple

    # Job status colors
    job_pending: str = "#666666"
    job_queued: str = "#0099ff"
    job_active: str = "#00cc66"
    job_running: str = "#ffaa00"
    job_completed: str = "#00aa44"
    job_failed: str = "#ff3333"
    job_suspended: str = "#9966ff"
    job_cancelled: str = "#cc6699"

    # Priority colors
    priority_critical: str = "#ff0000"
    priority_high: str = "#ff6600"
    priority_normal: str = "#00aaff"
    priority_low: str = "#666666"

    # Progress bar colors
    progress_bg: str = "#1a1a1a"
    progress_complete: str = "#00aa44"
    progress_running: str = "#ffaa00"
    progress_failed: str = "#ff3333"
    progress_queued: str = "#0066aa"

    # Accent
    accent_primary: str = "#0078d4"
    accent_secondary: str = "#00aaff"
    accent_success: str = "#00cc66"
    accent_warning: str = "#ffaa00"
    accent_error: str = "#ff4444"

    # Dock/panel
    dock_title_bg: str = "#1a1a1a"
    dock_title_text: str = "#909090"
    splitter_handle: str = "#0a0a0a"

    # Toolbar
    toolbar_bg: str = "#1c1c1c"
    toolbar_border: str = "#2a2a2a"
    toolbar_button_hover: str = "#333333"
    toolbar_button_pressed: str = "#444444"
    toolbar_separator: str = "#333333"


THEME = ThemeColors()


def get_main_stylesheet() -> str:
    """Generate the main application stylesheet."""
    return f"""
/* === MAIN WINDOW === */
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

/* === BASE WIDGET === */
QWidget {{
    background-color: transparent;
    color: {THEME.text_primary};
    font-family: 'Segoe UI', 'SF Pro Text', -apple-system, sans-serif;
    font-size: 12px;
}}

/* === DOCK WIDGETS === */
QDockWidget {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border_dark};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {THEME.dock_title_bg};
    color: {THEME.dock_title_text};
    padding: 6px 8px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    border-bottom: 1px solid {THEME.border_dark};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {THEME.bg_hover};
}}

/* === TOOLBAR === */
QToolBar {{
    background-color: {THEME.toolbar_bg};
    border: none;
    border-bottom: 1px solid {THEME.toolbar_border};
    padding: 2px 4px;
    spacing: 2px;
}}

QToolBar::separator {{
    background-color: {THEME.toolbar_separator};
    width: 1px;
    margin: 4px 8px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: 3px;
    padding: 4px 8px;
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
    color: {THEME.text_primary};
}}

QToolButton::menu-indicator {{
    image: none;
}}

/* === MENU BAR === */
QMenuBar {{
    background-color: {THEME.bg_header};
    border-bottom: 1px solid {THEME.border_dark};
    padding: 2px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 3px;
}}

QMenuBar::item:selected {{
    background-color: {THEME.bg_hover};
}}

QMenu {{
    background-color: {THEME.bg_light};
    border: 1px solid {THEME.border};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: 2px;
}}

QMenu::item:selected {{
    background-color: {THEME.accent_primary};
}}

QMenu::separator {{
    height: 1px;
    background-color: {THEME.border};
    margin: 4px 8px;
}}

/* === TABLES (DEADLINE STYLE) === */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {THEME.bg_panel};
    alternate-background-color: {THEME.bg_row_alt};
    border: 1px solid {THEME.border_dark};
    gridline-color: {THEME.border_dark};
    selection-background-color: {THEME.bg_selected};
    selection-color: {THEME.text_primary};
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: 4px 6px;
    border: none;
    border-bottom: 1px solid {THEME.border_dark};
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {THEME.bg_selected};
}}

QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
    background-color: {THEME.bg_hover};
}}

/* === HEADER VIEW === */
QHeaderView {{
    background-color: {THEME.bg_header};
}}

QHeaderView::section {{
    background-color: {THEME.bg_header};
    color: {THEME.text_header};
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {THEME.border_dark};
    border-bottom: 1px solid {THEME.border_dark};
    font-weight: 600;
    font-size: 11px;
}}

QHeaderView::section:hover {{
    background-color: {THEME.bg_hover};
}}

QHeaderView::section:pressed {{
    background-color: {THEME.bg_light};
}}

QHeaderView::down-arrow {{
    width: 12px;
    height: 12px;
}}

QHeaderView::up-arrow {{
    width: 12px;
    height: 12px;
}}

/* === SCROLLBARS === */
QScrollBar:vertical {{
    background: {THEME.bg_dark};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {THEME.bg_lighter};
    min-height: 30px;
    border-radius: 0;
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
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {THEME.bg_lighter};
    min-width: 30px;
    border-radius: 0;
}}

QScrollBar::handle:horizontal:hover {{
    background: {THEME.border_light};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* === TAB WIDGET === */
QTabWidget::pane {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border_dark};
    border-top: none;
}}

QTabWidget::tab-bar {{
    left: 0;
}}

QTabBar {{
    background-color: {THEME.bg_header};
}}

QTabBar::tab {{
    background-color: {THEME.bg_header};
    color: {THEME.text_secondary};
    padding: 6px 16px;
    border: 1px solid {THEME.border_dark};
    border-bottom: none;
    margin-right: 1px;
}}

QTabBar::tab:selected {{
    background-color: {THEME.bg_panel};
    color: {THEME.text_primary};
    border-bottom: 1px solid {THEME.bg_panel};
}}

QTabBar::tab:hover:!selected {{
    background-color: {THEME.bg_hover};
}}

/* === BUTTONS === */
QPushButton {{
    background-color: {THEME.bg_light};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 3px;
    padding: 5px 12px;
    font-weight: 500;
    min-height: 22px;
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
}}

QPushButton[primary="true"]:hover {{
    background-color: #0086e6;
}}

QPushButton[danger="true"] {{
    background-color: {THEME.accent_error};
    border-color: {THEME.accent_error};
}}

/* === LINE EDIT === */
QLineEdit {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 3px;
    padding: 5px 8px;
    selection-background-color: {THEME.accent_primary};
}}

QLineEdit:focus {{
    border-color: {THEME.border_focus};
}}

QLineEdit:disabled {{
    background-color: {THEME.bg_medium};
    color: {THEME.text_disabled};
}}

/* === COMBO BOX === */
QComboBox {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 22px;
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

/* === SPIN BOX === */
QSpinBox, QDoubleSpinBox {{
    background-color: {THEME.bg_dark};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    border-radius: 3px;
    padding: 4px;
}}

/* === CHECK BOX === */
QCheckBox {{
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {THEME.border};
    border-radius: 2px;
    background-color: {THEME.bg_dark};
}}

QCheckBox::indicator:checked {{
    background-color: {THEME.accent_primary};
    border-color: {THEME.accent_primary};
}}

QCheckBox::indicator:hover {{
    border-color: {THEME.border_light};
}}

/* === PROGRESS BAR === */
QProgressBar {{
    background-color: {THEME.progress_bg};
    border: 1px solid {THEME.border_dark};
    border-radius: 2px;
    height: 16px;
    text-align: center;
    color: {THEME.text_primary};
    font-size: 10px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background-color: {THEME.accent_primary};
    border-radius: 1px;
}}

/* === SPLITTER === */
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

/* === GROUP BOX === */
QGroupBox {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border};
    border-radius: 3px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {THEME.text_secondary};
}}

/* === TOOLTIP === */
QToolTip {{
    background-color: {THEME.bg_light};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border};
    padding: 4px 8px;
}}

/* === STATUS BAR === */
QStatusBar {{
    background-color: {THEME.bg_header};
    border-top: 1px solid {THEME.border_dark};
    color: {THEME.text_secondary};
    font-size: 11px;
}}

QStatusBar::item {{
    border: none;
}}

/* === TEXT EDIT (LOGS) === */
QTextEdit, QPlainTextEdit {{
    background-color: {THEME.bg_darkest};
    color: {THEME.text_primary};
    border: 1px solid {THEME.border_dark};
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 11px;
    selection-background-color: {THEME.accent_primary};
}}

/* === LABEL === */
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

/* === FRAME === */
QFrame[panel="true"] {{
    background-color: {THEME.bg_panel};
    border: 1px solid {THEME.border_dark};
}}
"""


def get_status_color(status: str) -> str:
    """Get color for a given status string."""
    status_map = {
        # Robot statuses
        "online": THEME.status_online,
        "offline": THEME.status_offline,
        "busy": THEME.status_busy,
        "error": THEME.status_error,
        "maintenance": THEME.status_warning,
        "idle": THEME.status_idle,
        "rendering": THEME.status_rendering,

        # Job statuses
        "pending": THEME.job_pending,
        "queued": THEME.job_queued,
        "active": THEME.job_active,
        "running": THEME.job_running,
        "completed": THEME.job_completed,
        "failed": THEME.job_failed,
        "suspended": THEME.job_suspended,
        "cancelled": THEME.job_cancelled,
        "timeout": THEME.job_failed,
    }
    return status_map.get(status.lower(), THEME.text_muted)


def get_priority_color(priority: int) -> str:
    """Get color for priority level (0=low, 3=critical)."""
    priority_map = {
        0: THEME.priority_low,
        1: THEME.priority_normal,
        2: THEME.priority_high,
        3: THEME.priority_critical,
    }
    return priority_map.get(priority, THEME.priority_normal)


def get_progress_color(status: str) -> str:
    """Get progress bar color based on job status."""
    if status in ("completed", "active"):
        return THEME.progress_complete
    elif status in ("running", "busy"):
        return THEME.progress_running
    elif status in ("failed", "error", "timeout"):
        return THEME.progress_failed
    elif status in ("queued", "pending"):
        return THEME.progress_queued
    return THEME.accent_primary

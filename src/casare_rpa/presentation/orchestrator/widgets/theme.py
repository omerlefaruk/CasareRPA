"""
Dark theme for CasareRPA Orchestrator.
Professional styling without icons - modern, clean design.
"""

# Color Palette - Modern Professional Dark Theme
# Consistent with main orchestrator styles
COLORS = {
    # Backgrounds (darkest to lightest)
    "bg_darkest": "#0f1114",  # Main background
    "bg_darker": "#121417",  # Panel backgrounds
    "bg_dark": "#1a1d21",  # Secondary panels
    "bg_medium": "#22262b",  # Elevated surfaces
    "bg_light": "#2a2f36",  # Hover states
    "bg_lighter": "#3a4046",  # Selected states
    "bg_header": "#15171a",  # Table headers
    # Text
    "text_primary": "#e8eaed",  # Primary text
    "text_secondary": "#9aa0a6",  # Secondary text
    "text_muted": "#5f6368",  # Muted/disabled text
    "text_bright": "#ffffff",  # Bright/emphasis text
    # Accent colors
    "accent_blue": "#4a9eff",  # Primary accent (selection)
    "accent_cyan": "#64b5f6",  # Secondary accent
    "accent_green": "#66bb6a",  # Success/online
    "accent_yellow": "#ffb74d",  # Warning/busy
    "accent_orange": "#ff7043",  # High priority
    "accent_red": "#ef5350",  # Error/critical
    "accent_purple": "#ab47bc",  # Special
    "accent_pink": "#ec407a",  # Critical priority
    # Status colors
    "status_idle": "#5f6368",  # Idle/offline
    "status_online": "#66bb6a",  # Online/ready
    "status_busy": "#ffb74d",  # Busy/rendering
    "status_error": "#ef5350",  # Error/failed
    "status_stalled": "#ff7043",  # Stalled/warning
    "status_offline": "#5f6368",  # Offline
    # Job status
    "job_queued": "#5f6368",  # Queued
    "job_rendering": "#42a5f5",  # Rendering/running (blue)
    "job_completed": "#66bb6a",  # Completed
    "job_failed": "#ef5350",  # Failed
    "job_suspended": "#ab47bc",  # Suspended
    "job_pending": "#ffb74d",  # Pending dependencies
    # Priority colors
    "priority_critical": "#ec407a",  # Critical (pink)
    "priority_high": "#ff7043",  # High (orange)
    "priority_normal": "#42a5f5",  # Normal (blue)
    "priority_low": "#5f6368",  # Low (gray)
    # Progress bar
    "progress_bg": "#22262b",
    "progress_fill": "#4a9eff",
    "progress_text": "#ffffff",
    # Borders
    "border_dark": "#1f2227",
    "border_medium": "#2a2f36",
    "border_light": "#3a4046",
    # Splitter
    "splitter": "#1f2227",
    "splitter_hover": "#4a9eff",
}

# Main stylesheet
STYLESHEET = f"""
/* ==================== GLOBAL ==================== */
QMainWindow, QWidget {{
    background-color: {COLORS['bg_darkest']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 12px;
}}

QMainWindow::separator {{
    background-color: {COLORS['splitter']};
    width: 3px;
    height: 3px;
}}

QMainWindow::separator:hover {{
    background-color: {COLORS['splitter_hover']};
}}

/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border_dark']};
    padding: 2px 4px;
}}

QMenuBar::item {{
    padding: 6px 10px;
    background: transparent;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_light']};
}}

QMenu {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 6px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent_blue']};
    color: {COLORS['text_bright']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border_medium']};
    margin: 6px 8px;
}}

/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    border: 1px solid {COLORS['border_dark']};
    background-color: {COLORS['bg_darker']};
}}

QTabBar {{
    background-color: {COLORS['bg_header']};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_darker']};
    color: {COLORS['text_bright']};
    border-bottom: 2px solid {COLORS['accent_blue']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

/* ==================== TOOLBAR ==================== */
QToolBar {{
    background-color: {COLORS['bg_header']};
    border: none;
    border-bottom: 1px solid {COLORS['border_dark']};
    spacing: 4px;
    padding: 4px 6px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {COLORS['border_medium']};
    margin: 6px 8px;
}}

QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 6px 10px;
    color: {COLORS['text_primary']};
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {COLORS['bg_light']};
    border-color: {COLORS['border_light']};
}}

QToolButton:pressed {{
    background-color: {COLORS['bg_lighter']};
}}

QToolButton:checked {{
    background-color: {COLORS['accent_blue']};
    color: {COLORS['text_bright']};
}}

/* ==================== TABLES ==================== */
QTableWidget, QTableView, QTreeWidget, QTreeView, QListWidget, QListView {{
    background-color: {COLORS['bg_darker']};
    alternate-background-color: {COLORS['bg_dark']};
    border: 1px solid {COLORS['border_dark']};
    gridline-color: {COLORS['border_dark']};
    selection-background-color: {COLORS['accent_blue']};
    selection-color: {COLORS['text_bright']};
    outline: none;
}}

QTableWidget::item, QTreeWidget::item, QListWidget::item {{
    padding: 6px 8px;
    border: none;
}}

QTableWidget::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {{
    background-color: {COLORS['accent_blue']};
}}

QTableWidget::item:hover, QTreeWidget::item:hover, QListWidget::item:hover {{
    background-color: {COLORS['bg_light']};
}}

QHeaderView {{
    background-color: {COLORS['bg_header']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {COLORS['border_dark']};
    border-bottom: 1px solid {COLORS['border_dark']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {{
    background-color: {COLORS['bg_darker']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_light']};
    min-height: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['bg_lighter']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background-color: {COLORS['bg_darker']};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_light']};
    min-width: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['bg_lighter']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {COLORS['splitter']};
}}

QSplitter::handle:horizontal {{
    width: 3px;
}}

QSplitter::handle:vertical {{
    height: 3px;
}}

QSplitter::handle:hover {{
    background-color: {COLORS['splitter_hover']};
}}

/* ==================== DOCK WIDGETS ==================== */
QDockWidget {{
    background-color: {COLORS['bg_darker']};
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
}}

QDockWidget::title {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    padding: 8px 12px;
    border-bottom: 1px solid {COLORS['border_dark']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background-color: {COLORS['bg_light']};
    border-radius: 3px;
}}

/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    padding: 6px 14px;
    min-height: 26px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {COLORS['bg_light']};
    border-color: {COLORS['border_light']};
}}

QPushButton:pressed {{
    background-color: {COLORS['bg_lighter']};
}}

QPushButton:disabled {{
    color: {COLORS['text_muted']};
    background-color: {COLORS['bg_dark']};
}}

QPushButton[primary="true"] {{
    background-color: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
    color: {COLORS['text_bright']};
}}

QPushButton[primary="true"]:hover {{
    background-color: #5ba8ff;
}}

/* ==================== INPUTS ==================== */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    padding: 6px 10px;
    selection-background-color: {COLORS['accent_blue']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent_blue']};
}}

QComboBox {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 26px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border_medium']};
    selection-background-color: {COLORS['accent_blue']};
}}

/* ==================== PROGRESS BAR ==================== */
QProgressBar {{
    background-color: {COLORS['progress_bg']};
    border: none;
    border-radius: 3px;
    height: 18px;
    text-align: center;
    color: {COLORS['progress_text']};
    font-size: 10px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background-color: {COLORS['progress_fill']};
    border-radius: 3px;
}}

/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {COLORS['bg_dark']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    margin-top: 14px;
    padding-top: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
    font-weight: 600;
}}

/* ==================== CHECKBOX & RADIO ==================== */
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {COLORS['text_primary']};
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
}}

QCheckBox::indicator {{
    border: 1px solid {COLORS['border_medium']};
    border-radius: 3px;
    background-color: {COLORS['bg_dark']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
}}

QRadioButton::indicator {{
    border: 1px solid {COLORS['border_medium']};
    border-radius: 8px;
    background-color: {COLORS['bg_dark']};
}}

QRadioButton::indicator:checked {{
    background-color: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
}}

/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    border-top: 1px solid {COLORS['border_dark']};
    padding: 2px 4px;
}}

QStatusBar::item {{
    border: none;
}}

/* ==================== TOOLTIPS ==================== */
QToolTip {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* ==================== LABELS ==================== */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

QLabel[heading="true"] {{
    font-size: 14px;
    font-weight: 600;
    color: {COLORS['text_bright']};
}}

QLabel[subheading="true"] {{
    font-size: 11px;
    color: {COLORS['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel[muted="true"] {{
    color: {COLORS['text_muted']};
}}
"""


# Additional style functions
def get_status_color(status: str) -> str:
    """Get color for a status string."""
    status_lower = status.lower()
    if status_lower in ("online", "ready", "idle"):
        return COLORS["status_online"]
    elif status_lower in ("busy", "rendering", "running"):
        return COLORS["status_busy"]
    elif status_lower in ("error", "failed"):
        return COLORS["status_error"]
    elif status_lower in ("stalled", "warning"):
        return COLORS["status_stalled"]
    elif status_lower in ("offline", "disabled"):
        return COLORS["status_offline"]
    return COLORS["status_idle"]


def get_job_status_color(status: str) -> str:
    """Get color for job status."""
    status_lower = status.lower()
    if status_lower in ("queued", "pending"):
        return COLORS["job_queued"]
    elif status_lower in ("rendering", "running", "active"):
        return COLORS["job_rendering"]
    elif status_lower in ("completed", "complete", "done"):
        return COLORS["job_completed"]
    elif status_lower in ("failed", "error"):
        return COLORS["job_failed"]
    elif status_lower in ("suspended", "paused"):
        return COLORS["job_suspended"]
    return COLORS["job_queued"]


def get_priority_color(priority: int) -> str:
    """Get color for priority level (0=low, 100=critical)."""
    if priority >= 80:
        return COLORS["priority_critical"]
    elif priority >= 60:
        return COLORS["priority_high"]
    elif priority >= 40:
        return COLORS["priority_normal"]
    return COLORS["priority_low"]

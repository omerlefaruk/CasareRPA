"""
Dark theme for CasareRPA Orchestrator.
Professional Deadline Monitor-inspired styling.
"""

# Color Palette - Dark Professional Theme
COLORS = {
    # Backgrounds (darkest to lightest)
    "bg_darkest": "#0d0d0d",      # Main background
    "bg_darker": "#141414",       # Panel backgrounds
    "bg_dark": "#1a1a1a",         # Secondary panels
    "bg_medium": "#242424",       # Elevated surfaces
    "bg_light": "#2d2d2d",        # Hover states
    "bg_lighter": "#363636",      # Selected states
    "bg_header": "#1e1e1e",       # Table headers

    # Text
    "text_primary": "#e0e0e0",    # Primary text
    "text_secondary": "#a0a0a0",  # Secondary text
    "text_muted": "#666666",      # Muted/disabled text
    "text_bright": "#ffffff",     # Bright/emphasis text

    # Accent colors
    "accent_blue": "#0078d4",     # Primary accent (selection)
    "accent_cyan": "#00b4d8",     # Secondary accent
    "accent_green": "#10b981",    # Success/online
    "accent_yellow": "#f59e0b",   # Warning/busy
    "accent_orange": "#f97316",   # High priority
    "accent_red": "#ef4444",      # Error/critical
    "accent_purple": "#8b5cf6",   # Special
    "accent_pink": "#ec4899",     # Critical priority

    # Status colors
    "status_idle": "#4b5563",     # Idle/offline
    "status_online": "#10b981",   # Online/ready
    "status_busy": "#f59e0b",     # Busy/rendering
    "status_error": "#ef4444",    # Error/failed
    "status_stalled": "#f97316",  # Stalled/warning
    "status_offline": "#374151",  # Offline

    # Job status
    "job_queued": "#6b7280",      # Queued
    "job_rendering": "#3b82f6",   # Rendering/running (blue)
    "job_completed": "#10b981",   # Completed
    "job_failed": "#ef4444",      # Failed
    "job_suspended": "#8b5cf6",   # Suspended
    "job_pending": "#f59e0b",     # Pending dependencies

    # Priority colors
    "priority_critical": "#ec4899",  # Critical (pink)
    "priority_high": "#f97316",      # High (orange)
    "priority_normal": "#3b82f6",    # Normal (blue)
    "priority_low": "#6b7280",       # Low (gray)

    # Progress bar
    "progress_bg": "#1a1a1a",
    "progress_fill": "#3b82f6",
    "progress_text": "#ffffff",

    # Borders
    "border_dark": "#1f1f1f",
    "border_medium": "#2a2a2a",
    "border_light": "#3a3a3a",

    # Splitter
    "splitter": "#2a2a2a",
    "splitter_hover": "#0078d4",
}

# Main stylesheet
STYLESHEET = f"""
/* ==================== GLOBAL ==================== */
QMainWindow, QWidget {{
    background-color: {COLORS['bg_darkest']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
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
    padding: 2px;
}}

QMenuBar::item {{
    padding: 4px 8px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['bg_light']};
}}

QMenu {{
    background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border_medium']};
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
}}

QMenu::item:selected {{
    background-color: {COLORS['accent_blue']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border_medium']};
    margin: 4px 8px;
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
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_secondary']};
    padding: 8px 16px;
    border: none;
    border-right: 1px solid {COLORS['border_dark']};
    min-width: 80px;
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
    spacing: 2px;
    padding: 2px 4px;
}}

QToolBar::separator {{
    width: 1px;
    background-color: {COLORS['border_medium']};
    margin: 4px 6px;
}}

QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 4px 8px;
    color: {COLORS['text_primary']};
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
    padding: 4px;
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
    padding: 6px 8px;
    border: none;
    border-right: 1px solid {COLORS['border_dark']};
    border-bottom: 1px solid {COLORS['border_dark']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
}}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {{
    background-color: {COLORS['bg_darker']};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['bg_light']};
    min-height: 30px;
    border-radius: 2px;
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
    height: 12px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['bg_light']};
    min-width: 30px;
    border-radius: 2px;
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
    padding: 6px 8px;
    border-bottom: 1px solid {COLORS['border_dark']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: 2px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background-color: {COLORS['bg_light']};
}}

/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 3px;
    padding: 6px 12px;
    min-height: 24px;
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
    background-color: #0066b8;
}}

/* ==================== INPUTS ==================== */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 3px;
    padding: 4px 8px;
    selection-background-color: {COLORS['accent_blue']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['accent_blue']};
}}

QComboBox {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 3px;
    padding: 4px 8px;
    min-height: 24px;
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
    border-radius: 2px;
    height: 16px;
    text-align: center;
    color: {COLORS['progress_text']};
    font-size: 10px;
    font-weight: 600;
}}

QProgressBar::chunk {{
    background-color: {COLORS['progress_fill']};
    border-radius: 2px;
}}

/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {COLORS['bg_dark']};
    border: 1px solid {COLORS['border_medium']};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {COLORS['text_secondary']};
    font-weight: 600;
}}

/* ==================== CHECKBOX & RADIO ==================== */
QCheckBox, QRadioButton {{
    spacing: 6px;
    color: {COLORS['text_primary']};
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 14px;
    height: 14px;
}}

QCheckBox::indicator {{
    border: 1px solid {COLORS['border_medium']};
    border-radius: 2px;
    background-color: {COLORS['bg_dark']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_blue']};
    border-color: {COLORS['accent_blue']};
}}

QRadioButton::indicator {{
    border: 1px solid {COLORS['border_medium']};
    border-radius: 7px;
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
}}

QStatusBar::item {{
    border: none;
}}

/* ==================== TOOLTIPS ==================== */
QToolTip {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border_medium']};
    padding: 4px 8px;
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

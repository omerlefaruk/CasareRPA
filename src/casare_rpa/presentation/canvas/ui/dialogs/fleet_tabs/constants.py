"""Fleet Dashboard shared constants.

Uses Canvas theme tokens (`casare_rpa.presentation.canvas.theme.THEME`) to avoid
hardcoded UI colors.
"""

from PySide6.QtGui import QColor

from casare_rpa.presentation.canvas.theme import THEME

# Robot status colors - used by robots_tab and robot_picker_panel
ROBOT_STATUS_COLORS = {
    "online": QColor(THEME.status_success),
    "idle": QColor(THEME.status_success),
    "busy": QColor(THEME.status_warning),
    "offline": QColor(THEME.status_error),
    "error": QColor(THEME.status_error),
    "maintenance": QColor(THEME.text_muted),
}

# Job status colors - used by jobs_tab
JOB_STATUS_COLORS = {
    "pending": QColor(THEME.text_muted),
    "queued": QColor(THEME.status_info),
    "claimed": QColor(THEME.status_warning),
    "running": QColor(THEME.status_running),
    "completed": QColor(THEME.status_success),
    "failed": QColor(THEME.status_error),
    "cancelled": QColor(THEME.text_muted),
    "timeout": QColor(THEME.status_error),
}

# Refresh intervals in milliseconds
REFRESH_INTERVALS = {
    "robots": 30000,  # 30 seconds
    "jobs": 10000,  # 10 seconds
    "schedules": 60000,  # 60 seconds
    "analytics": 60000,  # 60 seconds
    "api_keys": 60000,  # 60 seconds
}

# Deadline-inspired theme constants
DEADLINE_COLORS = {
    "bg_dark": THEME.bg_darkest,
    "bg_panel": THEME.bg_panel,
    "bg_header": THEME.bg_header,
    "border": THEME.border,
    "text_primary": THEME.text_primary,
    "text_secondary": THEME.text_secondary,
    "selection": THEME.selection_bg,
    "selection_text": THEME.text_primary,
    "hover": THEME.bg_hover,
}

# Shared dark theme base stylesheet for tab widgets
TAB_WIDGET_BASE_STYLE = f"""
    QWidget {{
        color: {DEADLINE_COLORS['text_primary']};
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}

    QTableWidget {{
        background: {DEADLINE_COLORS['bg_dark']};
        border: 1px solid {DEADLINE_COLORS['border']};
        gridline-color: {THEME.border_light};
        selection-background-color: {DEADLINE_COLORS['selection']};
        selection-color: {DEADLINE_COLORS['selection_text']};
        alternate-background-color: {THEME.bg_dark};
    }}

    QTableWidget::item {{
        padding: 4px; /* Dense padding */
        border-bottom: 1px solid {THEME.border_dark};
    }}

    QTableWidget::item:selected {{
        background: {DEADLINE_COLORS['selection']};
    }}

    QHeaderView::section {{
        background: {DEADLINE_COLORS['bg_header']};
        color: {DEADLINE_COLORS['text_primary']};
        padding: 6px;
        border: none;
        border-right: 1px solid {DEADLINE_COLORS['border']};
        border-bottom: 1px solid {DEADLINE_COLORS['border']};
        font-weight: bold;
    }}

    QLineEdit, QComboBox, QSpinBox {{
        background: {DEADLINE_COLORS['bg_panel']};
        border: 1px solid {THEME.border};
        border-radius: 2px;
        padding: 4px;
        selection-background-color: {DEADLINE_COLORS['selection']};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {DEADLINE_COLORS['selection']};
    }}

    QPushButton {{
        background: {DEADLINE_COLORS['bg_panel']};
        border: 1px solid {THEME.border};
        border-radius: 3px;
        padding: 5px 15px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background: {DEADLINE_COLORS['hover']};
        border-color: {THEME.border_light};
    }}

    QPushButton:pressed {{
        background: {THEME.bg_darkest};
    }}

    QLabel {{
        color: {DEADLINE_COLORS['text_primary']};
    }}

    QGroupBox {{
        border: 1px solid {THEME.border};
        border-radius: 4px;
        margin-top: 1em;
        padding-top: 10px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        color: {DEADLINE_COLORS['text_secondary']};
    }}

    QScrollBar:vertical {{
        border: none;
        background: {DEADLINE_COLORS['bg_dark']};
        width: 12px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {THEME.bg_light};
        min-height: 20px;
        border-radius: 2px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""

__all__ = [
    "ROBOT_STATUS_COLORS",
    "JOB_STATUS_COLORS",
    "REFRESH_INTERVALS",
    "TAB_WIDGET_BASE_STYLE",
    "DEADLINE_COLORS",
]

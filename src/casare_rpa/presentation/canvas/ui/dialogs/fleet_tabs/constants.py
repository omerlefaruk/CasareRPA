"""
Fleet Dashboard Shared Constants.

Eliminates duplicated color definitions and refresh intervals across tabs.
Implements a "Thinkbox Deadline" inspired dark theme.
"""

from PySide6.QtGui import QColor

# Robot status colors - used by robots_tab and robot_picker_panel
ROBOT_STATUS_COLORS = {
    "online": QColor(0x4C, 0xAF, 0x50),  # Green
    "idle": QColor(0x4C, 0xAF, 0x50),  # Green (alias)
    "busy": QColor(0xFF, 0xC1, 0x07),  # Yellow/Amber
    "offline": QColor(0xF4, 0x43, 0x36),  # Red
    "error": QColor(0xF4, 0x43, 0x36),  # Red
    "maintenance": QColor(0x9E, 0x9E, 0x9E),  # Gray
}

# Job status colors - used by jobs_tab
JOB_STATUS_COLORS = {
    "pending": QColor(0x9E, 0x9E, 0x9E),  # Gray
    "queued": QColor(0x21, 0x96, 0xF3),  # Blue
    "claimed": QColor(0xFF, 0x98, 0x00),  # Orange
    "running": QColor(0x4C, 0xAF, 0x50),  # Green
    "completed": QColor(0x00, 0xC8, 0x53),  # Bright Green
    "failed": QColor(0xF4, 0x43, 0x36),  # Red
    "cancelled": QColor(0x9E, 0x9E, 0x9E),  # Gray
    "timeout": QColor(0xE9, 0x1E, 0x63),  # Pink
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
    "bg_dark": "#222222",
    "bg_panel": "#333333",
    "bg_header": "#2A2A2A",
    "border": "#111111",
    "text_primary": "#E0E0E0",
    "text_secondary": "#AAAAAA",
    "selection": "#007ACC",  # Professional Blue
    "selection_text": "#FFFFFF",
    "hover": "#444444",
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
        gridline-color: #444444;
        selection-background-color: {DEADLINE_COLORS['selection']};
        selection-color: {DEADLINE_COLORS['selection_text']};
        alternate-background-color: #2A2A2A;
    }}

    QTableWidget::item {{
        padding: 4px; /* Dense padding */
        border-bottom: 1px solid #2A2A2A;
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
        border: 1px solid #555555;
        border-radius: 2px;
        padding: 4px;
        selection-background-color: {DEADLINE_COLORS['selection']};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {DEADLINE_COLORS['selection']};
    }}

    QPushButton {{
        background: {DEADLINE_COLORS['bg_panel']};
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 5px 15px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background: {DEADLINE_COLORS['hover']};
        border-color: #777777;
    }}

    QPushButton:pressed {{
        background: #222222;
    }}

    QLabel {{
        color: {DEADLINE_COLORS['text_primary']};
    }}

    QGroupBox {{
        border: 1px solid #555555;
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
        background: #555555;
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

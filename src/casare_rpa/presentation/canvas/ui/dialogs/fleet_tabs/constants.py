"""
Fleet Dashboard Shared Constants.

Eliminates duplicated color definitions and refresh intervals across tabs.
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

# Shared dark theme base stylesheet for tab widgets
TAB_WIDGET_BASE_STYLE = """
    QTableWidget {
        background: #1e1e1e;
        border: 1px solid #3d3d3d;
        gridline-color: #3d3d3d;
        color: #e0e0e0;
        alternate-background-color: #252525;
    }
    QTableWidget::item {
        padding: 6px;
    }
    QTableWidget::item:selected {
        background: #094771;
    }
    QHeaderView::section {
        background: #2d2d2d;
        color: #a0a0a0;
        padding: 6px;
        border: none;
        border-bottom: 1px solid #3d3d3d;
        border-right: 1px solid #3d3d3d;
    }
    QLineEdit, QComboBox {
        background: #3d3d3d;
        border: 1px solid #4a4a4a;
        border-radius: 3px;
        color: #e0e0e0;
        padding: 4px 8px;
        min-height: 24px;
    }
    QPushButton {
        background: #3d3d3d;
        border: 1px solid #4a4a4a;
        border-radius: 3px;
        color: #e0e0e0;
        padding: 6px 16px;
    }
    QPushButton:hover {
        background: #4a4a4a;
    }
    QLabel {
        color: #e0e0e0;
    }
"""


__all__ = [
    "ROBOT_STATUS_COLORS",
    "JOB_STATUS_COLORS",
    "REFRESH_INTERVALS",
    "TAB_WIDGET_BASE_STYLE",
]

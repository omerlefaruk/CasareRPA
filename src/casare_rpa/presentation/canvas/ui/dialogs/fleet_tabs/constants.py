"""Fleet Dashboard shared constants.

Uses Canvas theme tokens (THEME_V2, TOKENS_V2) for all UI styling.
"""

from PySide6.QtGui import QColor

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2

# Robot status colors - used by robots_tab and robot_picker_panel
ROBOT_STATUS_COLORS = {
    "online": QColor(THEME_V2.success),
    "idle": QColor(THEME_V2.success),
    "busy": QColor(THEME_V2.warning),
    "offline": QColor(THEME_V2.error),
    "error": QColor(THEME_V2.error),
    "maintenance": QColor(THEME_V2.text_muted),
}

# Job status colors - used by jobs_tab
JOB_STATUS_COLORS = {
    "pending": QColor(THEME_V2.text_muted),
    "queued": QColor(THEME_V2.info),
    "claimed": QColor(THEME_V2.warning),
    "running": QColor(THEME_V2.node_running),
    "completed": QColor(THEME_V2.success),
    "failed": QColor(THEME_V2.error),
    "cancelled": QColor(THEME_V2.text_muted),
    "timeout": QColor(THEME_V2.error),
}

# Refresh intervals in milliseconds
REFRESH_INTERVALS = {
    "robots": 30000,  # 30 seconds
    "jobs": 10000,  # 10 seconds
    "schedules": 60000,  # 60 seconds
    "analytics": 60000,  # 60 seconds
    "api_keys": 60000,  # 60 seconds
    "queues": 30000,  # 30 seconds
}


def get_tab_widget_style() -> str:
    """Generate compact stylesheet for tab widgets using TOKENS_V2."""
    t = THEME_V2
    tok = TOKENS_V2
    
    return f"""
    QWidget {{
        color: {t.text_primary};
        font-family: {tok.typography.sans};
        font-size: {tok.typography.body_sm}px;
    }}

    QTableWidget {{
        background: {t.bg_canvas};
        border: 1px solid {t.border};
        gridline-color: {t.border_light};
        selection-background-color: {t.bg_selected};
        selection-color: {t.text_primary};
        alternate-background-color: {t.bg_surface};
        font-size: {tok.typography.body_sm}px;
    }}

    QTableWidget::item {{
        padding: {tok.spacing.xxs}px;
        border-bottom: 1px solid {t.border_dark};
    }}

    QTableWidget::item:selected {{
        background: {t.bg_selected};
    }}

    QHeaderView::section {{
        background: {t.bg_header};
        color: {t.text_secondary};
        padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
        border: none;
        border-right: 1px solid {t.border};
        border-bottom: 1px solid {t.border};
        font-size: {tok.typography.caption}px;
        font-weight: {tok.typography.weight_semibold};
    }}

    QLineEdit, QComboBox, QSpinBox {{
        background: {t.input_bg};
        border: 1px solid {t.input_border};
        border-radius: {tok.radius.xs}px;
        padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
        font-size: {tok.typography.body_sm}px;
        min-height: {tok.sizes.input_sm}px;
        selection-background-color: {t.bg_selected};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {t.border_focus};
    }}

    QPushButton {{
        background: {t.bg_surface};
        border: 1px solid {t.border};
        border-radius: {tok.radius.xs}px;
        padding: {tok.spacing.xxs}px {tok.spacing.sm}px;
        font-size: {tok.typography.body_sm}px;
        font-weight: {tok.typography.weight_medium};
        min-height: {tok.sizes.button_sm}px;
    }}

    QPushButton:hover {{
        background: {t.bg_hover};
        border-color: {t.border_light};
    }}

    QPushButton:pressed {{
        background: {t.bg_canvas};
    }}

    QLabel {{
        color: {t.text_primary};
        font-size: {tok.typography.body_sm}px;
    }}

    QGroupBox {{
        border: 1px solid {t.border};
        border-radius: {tok.radius.sm}px;
        margin-top: {tok.spacing.sm}px;
        padding-top: {tok.spacing.sm}px;
        font-size: {tok.typography.body_sm}px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 {tok.spacing.xs}px;
        color: {t.text_secondary};
        font-size: {tok.typography.caption}px;
    }}

    QScrollBar:vertical {{
        border: none;
        background: {t.scrollbar_bg};
        width: {tok.sizes.scrollbar_width}px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {t.scrollbar_handle};
        min-height: {tok.sizes.scrollbar_min_height}px;
        border-radius: {tok.radius.xs}px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {t.scrollbar_hover};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        border: none;
        background: {t.scrollbar_bg};
        height: {tok.sizes.scrollbar_width}px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: {t.scrollbar_handle};
        min-width: {tok.sizes.scrollbar_min_height}px;
        border-radius: {tok.radius.xs}px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {t.scrollbar_hover};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    """


# For backward compatibility
TAB_WIDGET_BASE_STYLE = get_tab_widget_style()

__all__ = [
    "ROBOT_STATUS_COLORS",
    "JOB_STATUS_COLORS",
    "REFRESH_INTERVALS",
    "TAB_WIDGET_BASE_STYLE",
    "get_tab_widget_style",
]

"""
Styles and themes for CasareRPA Orchestrator.
Modern dark theme with accent colors.
"""

# Color palette
COLORS = {
    # Background colors
    "bg_dark": "#1a1a2e",
    "bg_medium": "#16213e",
    "bg_light": "#0f3460",
    "bg_card": "#1f2940",
    "bg_hover": "#2a3f5f",
    "bg_selected": "#3a5070",

    # Text colors
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "text_muted": "#6c757d",

    # Accent colors
    "accent_primary": "#e94560",
    "accent_secondary": "#0ea5e9",
    "accent_success": "#22c55e",
    "accent_warning": "#f59e0b",
    "accent_error": "#ef4444",
    "accent_info": "#3b82f6",

    # Status colors
    "status_online": "#22c55e",
    "status_offline": "#6c757d",
    "status_busy": "#f59e0b",
    "status_error": "#ef4444",

    # Job status colors
    "job_pending": "#6c757d",
    "job_queued": "#3b82f6",
    "job_running": "#f59e0b",
    "job_completed": "#22c55e",
    "job_failed": "#ef4444",
    "job_cancelled": "#a855f7",

    # Border colors
    "border": "#2d3748",
    "border_light": "#4a5568",
}

# Main application stylesheet
MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
    font-size: 13px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background: {COLORS['bg_medium']};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['bg_light']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['accent_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_medium']};
    height: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['bg_light']};
    border-radius: 5px;
    min-width: 30px;
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['accent_primary']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: #ff6b81;
}}

QPushButton:pressed {{
    background-color: #c73e54;
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}

QPushButton[secondary="true"] {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {COLORS['bg_hover']};
}}

/* Line Edit */
QLineEdit {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: {COLORS['accent_secondary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_secondary']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
}}

/* Combo Box */
QComboBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    min-height: 32px;
}}

QComboBox:hover {{
    border-color: {COLORS['accent_secondary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_secondary']};
    outline: none;
}}

/* Tables */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    alternate-background-color: {COLORS['bg_medium']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['bg_selected']};
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['bg_selected']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_secondary']};
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_card']};
}}

QTabBar::tab {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_secondary']};
    padding: 10px 20px;
    border: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['bg_hover']};
}}

/* Group Box */
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['bg_medium']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent_secondary']};
    border-radius: 4px;
}}

/* Spin Box */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
}}

/* Check Box */
QCheckBox {{
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color: {COLORS['bg_card']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_secondary']};
    border-color: {COLORS['accent_secondary']};
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* Menu */
QMenu {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['bg_hover']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 4px 8px;
}}
"""

# Sidebar specific styles
SIDEBAR_STYLESHEET = f"""
QWidget#sidebar {{
    background-color: {COLORS['bg_medium']};
    border-right: 1px solid {COLORS['border']};
}}

QPushButton#nav_button {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: left;
    font-weight: 500;
}}

QPushButton#nav_button:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}

QPushButton#nav_button:checked {{
    background-color: {COLORS['accent_primary']};
    color: {COLORS['text_primary']};
}}

QLabel#sidebar_title {{
    color: {COLORS['text_primary']};
    font-size: 18px;
    font-weight: 700;
    padding: 16px;
}}

QLabel#sidebar_subtitle {{
    color: {COLORS['text_muted']};
    font-size: 11px;
    padding: 0 16px 16px 16px;
}}
"""

# Card widget styles
CARD_STYLESHEET = f"""
QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}

QFrame#card:hover {{
    border-color: {COLORS['accent_secondary']};
}}

QLabel#card_title {{
    color: {COLORS['text_secondary']};
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
}}

QLabel#card_value {{
    color: {COLORS['text_primary']};
    font-size: 28px;
    font-weight: 700;
}}

QLabel#card_trend_up {{
    color: {COLORS['accent_success']};
    font-size: 12px;
}}

QLabel#card_trend_down {{
    color: {COLORS['accent_error']};
    font-size: 12px;
}}
"""

# Status badge styles
def get_status_badge_style(status: str) -> str:
    """Get style for status badge based on status value."""
    color_map = {
        "online": COLORS["status_online"],
        "offline": COLORS["status_offline"],
        "busy": COLORS["status_busy"],
        "error": COLORS["status_error"],
        "pending": COLORS["job_pending"],
        "queued": COLORS["job_queued"],
        "running": COLORS["job_running"],
        "completed": COLORS["job_completed"],
        "failed": COLORS["job_failed"],
        "cancelled": COLORS["job_cancelled"],
    }
    color = color_map.get(status.lower(), COLORS["text_muted"])
    return f"""
        QLabel {{
            background-color: {color}20;
            color: {color};
            border: 1px solid {color}40;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
    """


# Icon mappings (using Unicode symbols as fallback)
ICONS = {
    "dashboard": "📊",
    "robots": "🤖",
    "jobs": "📋",
    "workflows": "⚡",
    "schedules": "📅",
    "settings": "⚙️",
    "refresh": "🔄",
    "play": "▶️",
    "stop": "⏹️",
    "pause": "⏸️",
    "add": "➕",
    "delete": "🗑️",
    "edit": "✏️",
    "search": "🔍",
    "filter": "🔽",
    "export": "📤",
    "import": "📥",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "info": "ℹ️",
}

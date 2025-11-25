"""
Styles and themes for CasareRPA Orchestrator.
Modern dark theme with refined color palette - no icons.
"""

# Color palette - Modern Professional Dark Theme
# Inspired by professional IDEs and monitoring tools
COLORS = {
    # Background colors - Neutral dark grays with subtle blue undertone
    "bg_dark": "#121417",         # Darkest - main window background
    "bg_medium": "#1a1d21",       # Panel backgrounds
    "bg_light": "#22262b",        # Elevated surfaces, inputs
    "bg_card": "#1e2126",         # Card backgrounds
    "bg_hover": "#2a2f36",        # Hover states
    "bg_selected": "#2d4a6f",     # Selected items (blue tint)
    "bg_header": "#15171a",       # Table headers, toolbar

    # Text colors
    "text_primary": "#e8eaed",    # Primary text - high contrast
    "text_secondary": "#9aa0a6",  # Secondary text
    "text_muted": "#5f6368",      # Muted/disabled text

    # Accent colors - Refined, professional tones
    "accent_primary": "#4a9eff",  # Primary accent (selection, focus)
    "accent_secondary": "#64b5f6", # Secondary accent
    "accent_success": "#66bb6a",  # Success/online - softer green
    "accent_warning": "#ffb74d",  # Warning/busy - warm amber
    "accent_error": "#ef5350",    # Error/critical - clear red
    "accent_info": "#42a5f5",     # Information - light blue

    # Status colors
    "status_online": "#66bb6a",   # Online/ready
    "status_offline": "#5f6368",  # Offline/disabled
    "status_busy": "#ffb74d",     # Busy/working
    "status_error": "#ef5350",    # Error state

    # Job status colors
    "job_pending": "#5f6368",     # Pending - gray
    "job_queued": "#42a5f5",      # Queued - blue
    "job_running": "#ffb74d",     # Running - amber
    "job_completed": "#66bb6a",   # Completed - green
    "job_failed": "#ef5350",      # Failed - red
    "job_cancelled": "#ab47bc",   # Cancelled - purple

    # Border colors
    "border": "#2a2f36",          # Standard border
    "border_light": "#3a4046",    # Light border (hover)
    "border_focus": "#4a9eff",    # Focus ring
}

# Main application stylesheet
MAIN_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_dark']};
}}

QWidget {{
    background-color: transparent;
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}}

/* Scrollbars - Minimal design */
QScrollBar:vertical {{
    background: {COLORS['bg_medium']};
    width: 10px;
    border: none;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['bg_light']};
    min-height: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['bg_hover']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {COLORS['bg_medium']};
    height: 10px;
    border: none;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS['bg_light']};
    min-width: 32px;
    border-radius: 5px;
    margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS['bg_hover']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

/* Buttons - Clean, minimal style */
QPushButton {{
    background-color: {COLORS['accent_primary']};
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: #5ba8ff;
}}

QPushButton:pressed {{
    background-color: #3d8ae8;
}}

QPushButton:disabled {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_muted']};
}}

QPushButton[secondary="true"] {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['border_light']};
}}

QPushButton[danger="true"] {{
    background-color: {COLORS['accent_error']};
}}

QPushButton[danger="true"]:hover {{
    background-color: #f06660;
}}

/* Line Edit - Clean input fields */
QLineEdit {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px 12px;
    selection-background-color: {COLORS['accent_primary']};
}}

QLineEdit:focus {{
    border-color: {COLORS['accent_primary']};
}}

QLineEdit:disabled {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
}}

QLineEdit::placeholder {{
    color: {COLORS['text_muted']};
}}

/* Combo Box */
QComboBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px 12px;
    min-height: 32px;
}}

QComboBox:hover {{
    border-color: {COLORS['border_light']};
}}

QComboBox:focus {{
    border-color: {COLORS['accent_primary']};
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
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent_primary']};
    outline: none;
    padding: 4px;
}}

/* Tables - Professional data grid styling */
QTableWidget {{
    background-color: {COLORS['bg_medium']};
    alternate-background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    gridline-color: {COLORS['border']};
    selection-background-color: {COLORS['bg_selected']};
}}

QTableWidget::item {{
    padding: 10px 8px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['text_primary']};
}}

QTableWidget::item:hover {{
    background-color: {COLORS['bg_hover']};
}}

QHeaderView::section {{
    background-color: {COLORS['bg_header']};
    color: {COLORS['text_secondary']};
    padding: 12px 8px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    border-right: 1px solid {COLORS['border']};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px;
    letter-spacing: 0.5px;
}}

QHeaderView::section:last {{
    border-right: none;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
}}

/* Tab Widget - Clean tab design */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    background-color: {COLORS['bg_medium']};
    margin-top: -1px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_secondary']};
    padding: 12px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    color: {COLORS['text_primary']};
    border-bottom: 2px solid {COLORS['accent_primary']};
}}

QTabBar::tab:hover:!selected {{
    color: {COLORS['text_primary']};
    background-color: {COLORS['bg_hover']};
}}

/* Group Box */
QGroupBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    margin-top: 16px;
    padding-top: 16px;
    font-weight: 500;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: {COLORS['text_secondary']};
}}

/* Progress Bar */
QProgressBar {{
    background-color: {COLORS['bg_light']};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent_primary']};
    border-radius: 4px;
}}

/* Spin Box */
QSpinBox, QDoubleSpinBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['accent_primary']};
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
    background-color: {COLORS['bg_light']};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS['border_light']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['accent_primary']};
    border-color: {COLORS['accent_primary']};
}}

/* Tooltips */
QToolTip {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* Menu */
QMenu {{
    background-color: {COLORS['bg_light']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px;
}}

QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['bg_hover']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 6px 8px;
}}

/* Dialog */
QDialog {{
    background-color: {COLORS['bg_medium']};
}}

/* Message Box */
QMessageBox {{
    background-color: {COLORS['bg_medium']};
}}

QMessageBox QLabel {{
    color: {COLORS['text_primary']};
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
    border-radius: 6px;
    padding: 12px 16px;
    text-align: left;
    font-weight: 500;
    font-size: 13px;
}}

QPushButton#nav_button:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_primary']};
}}

QPushButton#nav_button:checked {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['text_primary']};
}}

QLabel#sidebar_title {{
    color: {COLORS['text_primary']};
    font-size: 18px;
    font-weight: 700;
    padding: 16px;
    letter-spacing: -0.5px;
}}

QLabel#sidebar_subtitle {{
    color: {COLORS['accent_primary']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 0 16px 16px 16px;
}}
"""

# Card widget styles
CARD_STYLESHEET = f"""
QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 16px;
}}

QFrame#card:hover {{
    border-color: {COLORS['border_light']};
}}

QLabel#card_title {{
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel#card_value {{
    color: {COLORS['text_primary']};
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -1px;
}}

QLabel#card_trend_up {{
    color: {COLORS['accent_success']};
    font-size: 12px;
    font-weight: 500;
}}

QLabel#card_trend_down {{
    color: {COLORS['accent_error']};
    font-size: 12px;
    font-weight: 500;
}}
"""


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

    # Calculate background color with transparency
    return f"""
        QLabel {{
            background-color: {color}1a;
            color: {color};
            border: 1px solid {color}40;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
    """

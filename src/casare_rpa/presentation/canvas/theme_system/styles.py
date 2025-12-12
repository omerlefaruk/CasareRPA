"""
QSS Style generators for CasareRPA Canvas.

Contains functions that generate QSS stylesheet fragments organized by widget type.
All functions take a CanvasThemeColors instance and return QSS strings.
"""

from pathlib import Path

from .colors import CanvasThemeColors
from .constants import FONTS, FONT_SIZES, RADIUS, SIZES, SPACING

# Get assets directory path
ASSETS_DIR = Path(__file__).parent.parent / "assets"
CHECKMARK_PATH = (ASSETS_DIR / "checkmark.svg").as_posix()


def get_main_window_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QMainWindow."""
    return f"""
/* ==================== MAIN WINDOW ==================== */
QMainWindow {{
    background-color: {theme.bg_darkest};
}}

QMainWindow::separator {{
    background-color: {theme.bg_darkest}; /* Seamless splitter */
    width: {SIZES.splitter_handle_size}px;
    height: {SIZES.splitter_handle_size}px;
}}

QMainWindow::separator:hover {{
    background-color: {theme.accent_primary}; /* Highlight on hover */
}}
"""


def get_base_widget_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for base QWidget."""
    return f"""
/* ==================== BASE WIDGET ==================== */
QWidget {{
    background-color: transparent;
    color: {theme.text_primary};
    font-family: {FONTS.ui};
    font-size: {FONT_SIZES.md}px; /* Slightly larger for readability */
}}
"""


def get_menu_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QMenuBar and QMenu."""
    return f"""
/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {theme.bg_header};
    color: {theme.text_primary};
    border-bottom: 1px solid {theme.border};
    padding: {SPACING.sm}px {SIZES.menu_padding}px;
}}

QMenuBar::item {{
    background: transparent;
    padding: {SIZES.menu_padding}px {SIZES.menu_item_padding_h}px;
    border-radius: {RADIUS.sm}px;
}}

QMenuBar::item:selected {{
    background-color: {theme.bg_hover};
    color: {theme.text_primary};
}}

QMenu {{
    background-color: {theme.bg_dark}; /* Darker menu */
    border: 1px solid {theme.border_light};
    border-radius: {RADIUS.lg}px; /* Rounded corners */
    padding: {SIZES.menu_padding}px;
}}

QMenu::item {{
    padding: {SIZES.menu_item_padding_v}px {SIZES.menu_item_padding_right}px {SIZES.menu_item_padding_v}px {SIZES.menu_item_padding_h}px;
    border-radius: {RADIUS.sm}px;
    margin: {SPACING.xs}px 0;
}}

QMenu::item:selected {{
    background-color: {theme.accent_primary};
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background-color: {theme.bg_light};
    margin: {SPACING.sm}px {SIZES.menu_separator_margin}px;
}}
"""


def get_toolbar_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QToolBar and QToolButton."""
    return f"""
/* ==================== TOOLBAR ==================== */
QToolBar {{
    background-color: {theme.toolbar_bg};
    border: none;
    border-bottom: 1px solid {theme.border};
    padding: {SIZES.toolbar_padding}px {SIZES.toolbar_padding + SPACING.sm}px;
    spacing: {SIZES.toolbar_spacing}px;
}}

QToolBar::separator {{
    background-color: {theme.border};
    width: {SIZES.toolbar_separator_width}px;
    margin: {SPACING.sm}px {SIZES.toolbar_separator_margin}px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: {RADIUS.md}px;
    padding: {SIZES.toolbar_button_padding_v}px {SIZES.toolbar_button_padding_h}px;
    color: {theme.text_secondary};
    font-weight: 500;
}}

QToolButton:hover {{
    background-color: {theme.bg_hover};
    color: {theme.text_primary};
}}

QToolButton:pressed {{
    background-color: {theme.bg_medium};
}}

QToolButton:checked {{
    background-color: {theme.accent_primary};
    color: #ffffff;
}}
"""


def get_statusbar_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QStatusBar."""
    return f"""
/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {theme.bg_darkest};
    border-top: 1px solid {theme.border};
    color: {theme.text_secondary};
    font-size: {FONT_SIZES.sm}px;
    padding: {SPACING.sm}px {SIZES.header_padding_h}px;
}}

QStatusBar::item {{
    border: none;
}}
"""


def get_dock_widget_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QDockWidget."""
    return f"""
/* ==================== DOCK WIDGETS ==================== */
QDockWidget {{
    background-color: {theme.bg_panel};
    border: none;
    color: {theme.text_primary};
}}

QDockWidget::title {{
    background-color: {theme.bg_panel};
    color: {theme.text_secondary};
    padding: {SIZES.dock_title_padding_v}px {SIZES.dock_title_padding_h}px;
    font-weight: 600;
    font-size: {FONT_SIZES.sm}px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid {theme.border};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: {SIZES.dock_button_padding}px;
    icon-size: {SIZES.dock_button_icon_size}px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {theme.bg_hover};
    border-radius: {RADIUS.sm}px;
}}
"""


def get_tab_widget_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QTabWidget and QTabBar."""
    return f"""
/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    background-color: {theme.bg_panel};
    border: none;
    border-top: 1px solid {theme.border};
}}

QTabBar {{
    background-color: {theme.bg_panel};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {theme.text_secondary};
    padding: {SIZES.tab_padding_v}px {SIZES.tab_padding_h}px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: {SIZES.tab_spacing}px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    color: {theme.text_primary};
    border-bottom: 2px solid {theme.accent_primary};
}}

QTabBar::tab:hover:!selected {{
    color: {theme.text_primary};
    background-color: {theme.bg_hover};
    border-radius: {RADIUS.sm}px {RADIUS.sm}px 0 0;
}}
"""


def get_table_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for table/tree/list views."""
    return f"""
/* ==================== TABLES ==================== */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {theme.bg_dark}; /* Slightly lighter than canvas */
    alternate-background-color: {theme.bg_darkest};
    border: none;
    selection-background-color: {theme.bg_selected};
    selection-color: #ffffff;
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: {SIZES.table_item_padding_v}px {SIZES.table_item_padding_h}px;
    border: none;
    border-bottom: 1px solid {theme.bg_darkest}; /* Subtle separation */
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {theme.bg_selected};
    border-radius: {RADIUS.sm}px;
}}

QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
    background-color: {theme.bg_hover};
}}
"""


def get_header_view_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QHeaderView."""
    return f"""
/* ==================== HEADER VIEW ==================== */
QHeaderView {{
    background-color: {theme.bg_panel};
    border: none;
}}

QHeaderView::section {{
    background-color: {theme.bg_panel};
    color: {theme.text_secondary};
    padding: {SIZES.header_padding_v}px {SIZES.header_padding_h}px;
    border: none;
    border-bottom: 1px solid {theme.border};
    font-weight: 600;
    font-size: {FONT_SIZES.sm}px;
    text-transform: uppercase;
}}
"""


def get_scrollbar_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for scrollbars (modern/slim style)."""
    return f"""
/* ==================== SCROLLBARS (Modern/Slim) ==================== */
QScrollBar:vertical {{
    background: {theme.bg_darkest};
    width: {SIZES.scrollbar_width}px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {theme.bg_light};
    min-height: {SIZES.scrollbar_min_handle}px;
    border-radius: {RADIUS.sm}px;
    margin: {SPACING.xs}px;
}}

QScrollBar::handle:vertical:hover {{
    background: {theme.bg_lighter};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {theme.bg_darkest};
    height: {SIZES.scrollbar_width}px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {theme.bg_light};
    min-width: {SIZES.scrollbar_min_handle}px;
    border-radius: {RADIUS.sm}px;
    margin: {SPACING.xs}px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {theme.bg_lighter};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


def get_button_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QPushButton."""
    return f"""
/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {theme.bg_medium};
    color: {theme.text_primary};
    border: none;
    border-radius: {RADIUS.md}px;
    padding: {SIZES.button_padding_v}px {SIZES.button_padding_h}px;
    font-weight: 500;
}}

QPushButton:hover {{
    background-color: {theme.bg_light};
}}

QPushButton:pressed {{
    background-color: {theme.bg_dark};
}}

QPushButton:disabled {{
    background-color: {theme.bg_dark};
    color: {theme.text_disabled};
}}

QPushButton[primary="true"] {{
    background-color: {theme.accent_primary};
    color: #ffffff;
}}

QPushButton[primary="true"]:hover {{
    background-color: {theme.accent_hover};
}}

QPushButton[danger="true"] {{
    background-color: {theme.status_error};
    color: #ffffff;
}}
"""


def get_input_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QLineEdit (modern/borderless style)."""
    return f"""
/* ==================== INPUTS (Modern/Borderless) ==================== */
QLineEdit {{
    background-color: {theme.input_bg};
    color: {theme.text_primary};
    border: 1px solid {theme.border};
    border-radius: {RADIUS.md}px;
    padding: {SIZES.input_padding_v}px {SIZES.input_padding_h}px;
    selection-background-color: {theme.accent_primary};
}}

QLineEdit:focus {{
    border: 1px solid {theme.accent_primary};
    background-color: {theme.bg_dark};
}}

QLineEdit:disabled {{
    background-color: {theme.bg_dark};
    color: {theme.text_disabled};
    border-color: transparent;
}}
"""


def get_combobox_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QComboBox."""
    return f"""
/* ==================== COMBO BOX ==================== */
QComboBox {{
    background-color: {theme.input_bg};
    color: {theme.text_primary};
    border: 1px solid {theme.border};
    border-radius: {RADIUS.md}px;
    padding: {SIZES.menu_padding}px {SIZES.input_padding_h}px;
    min-height: 28px;
}}

QComboBox:hover {{
    border-color: {theme.border_light};
}}

QComboBox:focus {{
    border-color: {theme.accent_primary};
}}

QComboBox::drop-down {{
    border: none;
    width: {SIZES.combo_dropdown_width}px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: {SIZES.combo_arrow_size}px solid transparent;
    border-right: {SIZES.combo_arrow_size}px solid transparent;
    border-top: {SIZES.combo_arrow_size}px solid {theme.text_secondary};
    margin-right: {SIZES.combo_arrow_margin}px;
}}

QComboBox QAbstractItemView {{
    background-color: {theme.bg_dark};
    border: 1px solid {theme.border_light};
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px;
    selection-background-color: {theme.accent_primary};
    outline: none;
}}
"""


def get_spinbox_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QSpinBox and QDoubleSpinBox."""
    return f"""
/* ==================== SPIN BOX ==================== */
QSpinBox, QDoubleSpinBox {{
    background-color: {theme.input_bg};
    color: {theme.text_primary};
    border: 1px solid {theme.border};
    border-radius: {RADIUS.md}px;
    padding: {SPACING.sm}px {SIZES.input_padding_v}px;
    min-height: {SIZES.input_min_height}px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {theme.accent_primary};
}}
"""


def get_checkbox_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QCheckBox."""
    return f"""
/* ==================== CHECK BOX ==================== */
QCheckBox {{
    spacing: {SIZES.checkbox_spacing}px;
    color: {theme.text_primary};
}}

QCheckBox::indicator {{
    width: {SIZES.checkbox_size}px;
    height: {SIZES.checkbox_size}px;
    border: 1px solid {theme.border_light};
    border-radius: {RADIUS.sm}px;
    background-color: {theme.input_bg};
}}

QCheckBox::indicator:hover {{
    border-color: {theme.accent_primary};
}}

QCheckBox::indicator:checked {{
    background-color: {theme.accent_primary};
    border-color: {theme.accent_primary};
    image: url({CHECKMARK_PATH});
}}
"""


def get_splitter_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QSplitter."""
    return f"""
/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {theme.bg_darkest};
}}

QSplitter::handle:hover {{
    background-color: {theme.accent_primary};
}}
"""


def get_groupbox_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QGroupBox."""
    return f"""
/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {theme.bg_panel};
    border: 1px solid {theme.border};
    border-radius: {RADIUS.lg}px;
    margin-top: {SIZES.dock_title_padding_v * 2}px;
    padding-top: {SIZES.dock_title_padding_h}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {SIZES.input_padding_v}px;
    color: {theme.text_secondary};
    font-weight: 600;
}}
"""


def get_tooltip_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QToolTip."""
    return f"""
/* ==================== TOOLTIP ==================== */
QToolTip {{
    background-color: {theme.bg_dark};
    color: {theme.text_primary};
    border: 1px solid {theme.border_light};
    border-radius: {RADIUS.sm}px;
    padding: {SIZES.tooltip_padding_v}px {SIZES.tooltip_padding_h}px;
}}
"""


def get_textedit_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QTextEdit and QPlainTextEdit (logs style)."""
    return f"""
/* ==================== TEXT EDIT (LOGS) ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: {theme.bg_darkest};
    color: {theme.text_primary};
    border: none;
    font-family: {FONTS.mono};
    font-size: {FONT_SIZES.sm + 1}px;
    padding: {SIZES.input_padding_v}px;
    selection-background-color: {theme.selection_bg};
}}
"""


def get_canvas_stylesheet(theme: CanvasThemeColors) -> str:
    """
    Generate the complete Canvas application stylesheet.

    Args:
        theme: CanvasThemeColors instance with color values

    Returns:
        Complete QSS stylesheet for the Canvas application.
    """
    return "".join(
        [
            get_main_window_styles(theme),
            get_base_widget_styles(theme),
            get_menu_styles(theme),
            get_toolbar_styles(theme),
            get_statusbar_styles(theme),
            get_dock_widget_styles(theme),
            get_tab_widget_styles(theme),
            get_table_styles(theme),
            get_header_view_styles(theme),
            get_scrollbar_styles(theme),
            get_button_styles(theme),
            get_input_styles(theme),
            get_combobox_styles(theme),
            get_spinbox_styles(theme),
            get_checkbox_styles(theme),
            get_splitter_styles(theme),
            get_groupbox_styles(theme),
            get_tooltip_styles(theme),
            get_textedit_styles(theme),
        ]
    )

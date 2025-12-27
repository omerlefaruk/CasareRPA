"""
QSS Style generators for CasareRPA Canvas.

Contains functions that generate QSS stylesheet fragments organized by widget type.
All functions take a CanvasThemeColors instance and return QSS strings.

Design System 2025: Uses semantic TOKENS.spacing.* and TOKENS.radius.* only.
No custom component-specific size tokens - keeps the token set minimal.
"""

from pathlib import Path

from .colors import CanvasThemeColors
from .design_tokens import TOKENS

# Get assets directory path
ASSETS_DIR = Path(__file__).parent.parent / "assets"
CHECKMARK_PATH = (ASSETS_DIR / "checkmark.svg").as_posix()


def get_main_window_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QMainWindow."""
    return f"""
/* ==================== MAIN WINDOW ==================== */
QMainWindow {{
    background-color: {theme.bg_canvas};
}}

QMainWindow::separator {{
    background-color: {theme.bg_canvas};
    width: {TOKENS.sizes.splitter_handle}px;
    height: {TOKENS.sizes.splitter_handle}px;
}}

QMainWindow::separator:hover {{
    background-color: {theme.primary};
}}
"""


def get_base_widget_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for base QWidget."""
    return f"""
/* ==================== BASE WIDGET ==================== */
QWidget {{
    background-color: transparent;
    color: {theme.text_primary};
    font-family: {TOKENS.typography.sans};
    font-size: {TOKENS.typography.body}px;
}}
"""


def get_menu_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QMenuBar and QMenu with VS Code/Cursor style."""
    return f"""
/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {theme.bg_header};
    color: {theme.text_primary};
    border-bottom: 1px solid {theme.border};
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.xxs}px;
}}

QMenuBar::item {{
    background: transparent;
    padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px;
    border-radius: {TOKENS.radius.sm}px;
}}

QMenuBar::item:selected {{
    background-color: {theme.bg_hover};
    color: {theme.text_primary};
}}

/* ==================== CONTEXT MENU (VS Code/Cursor Style) ==================== */
QMenu {{
    background-color: {theme.menu_bg};
    border: 1px solid {theme.menu_border};
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xs}px;
}}

QMenu::item {{
    background-color: transparent;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.lg}px {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
    border-radius: {TOKENS.radius.sm}px;
    height: {TOKENS.sizes.menu_item_height}px;
    color: {theme.text_primary};
    font-size: {TOKENS.typography.heading_m}px;
}}

QMenu::item:selected {{
    background-color: {theme.primary};
    color: {theme.text_on_primary};
}}

QMenu::item:disabled {{
    color: {theme.text_disabled};
}}

QMenu::separator {{
    height: 1px;
    background-color: {theme.border};
    margin: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px;
}}

QMenu::indicator {{
    width: {TOKENS.sizes.icon_sm}px;
    height: {TOKENS.sizes.icon_sm}px;
    left: {TOKENS.spacing.xs}px;
}}

QMenu::indicator:exclusive {{
    width: 12px;
    height: 12px;
    border-radius: 6px;
    border: 2px solid {theme.text_secondary};
}}

QMenu::indicator:exclusive:selected {{
    background-color: {theme.primary};
    border-color: {theme.primary};
}}

QMenu::indicator:non-exclusive {{
    width: 14px;
    height: 14px;
    border: 2px solid {theme.text_secondary};
    border-radius: 2px;
}}

QMenu::indicator:non-exclusive:checked {{
    background-color: {theme.primary};
    border-color: {theme.primary};
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
    padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.xs}px;
    spacing: {TOKENS.spacing.xxs}px;
}}

QToolBar::separator {{
    background-color: {theme.border};
    width: 1px;
    margin: {TOKENS.spacing.xs}px {TOKENS.spacing.xs}px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
    color: {theme.text_secondary};
    font-weight: {TOKENS.typography.weight_medium};
}}

QToolButton:hover {{
    background-color: {theme.bg_hover};
    color: {theme.text_primary};
}}

QToolButton:pressed {{
    background-color: {theme.bg_component};
}}

QToolButton:checked {{
    background-color: {theme.primary};
    color: {theme.text_on_primary};
}}
"""


def get_statusbar_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QStatusBar."""
    return f"""
/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {theme.bg_canvas};
    border-top: 1px solid {theme.border};
    color: {theme.text_secondary};
    font-size: {TOKENS.typography.body_s}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
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
    background-color: {theme.bg_surface};
    border: none;
    color: {theme.text_primary};
}}

QDockWidget::title {{
    background-color: {theme.bg_surface};
    color: {theme.text_secondary};
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
    font-weight: {TOKENS.typography.weight_semibold};
    font-size: {TOKENS.typography.body_s}px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid {theme.border};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: {TOKENS.spacing.xxs}px;
    icon-size: {TOKENS.sizes.icon_sm}px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {theme.bg_hover};
    border-radius: {TOKENS.radius.sm}px;
}}
"""


def get_tab_widget_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QTabWidget and QTabBar."""
    return f"""
/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    background-color: {theme.bg_surface};
    border: none;
    border-top: 1px solid {theme.border};
}}

QTabBar {{
    background-color: {theme.bg_surface};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {theme.text_secondary};
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: {TOKENS.spacing.xxs}px;
    font-weight: {TOKENS.typography.weight_medium};
}}

QTabBar::tab:selected {{
    color: {theme.text_primary};
    border-bottom: 2px solid {theme.primary};
}}

QTabBar::tab:hover:!selected {{
    color: {theme.text_primary};
    background-color: {theme.bg_hover};
    border-radius: {TOKENS.radius.sm}px {TOKENS.radius.sm}px 0 0;
}}
"""


def get_table_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for table/tree/list views."""
    return f"""
/* ==================== TABLES ==================== */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {theme.bg_surface};
    alternate-background-color: {theme.bg_canvas};
    border: none;
    selection-background-color: {theme.bg_selected};
    selection-color: {theme.text_on_primary};
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
    border: none;
    border-bottom: 1px solid {theme.bg_canvas};
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {theme.bg_selected};
    border-radius: {TOKENS.radius.sm}px;
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
    background-color: {theme.bg_surface};
    border: none;
}}

QHeaderView::section {{
    background-color: {theme.bg_surface};
    color: {theme.text_secondary};
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
    border: none;
    border-bottom: 1px solid {theme.border};
    font-weight: {TOKENS.typography.weight_semibold};
    font-size: {TOKENS.typography.body_s}px;
    text-transform: uppercase;
}}
"""


def get_scrollbar_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for scrollbars (modern/slim style)."""
    return f"""
/* ==================== SCROLLBARS (Modern/Slim) ==================== */
QScrollBar:vertical {{
    background: {theme.scrollbar_bg};
    width: {TOKENS.sizes.scrollbar_width}px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {theme.scrollbar_handle};
    min-height: {TOKENS.sizes.scrollbar_min_height}px;
    border-radius: {TOKENS.radius.sm}px;
    margin: {TOKENS.spacing.xxs}px;
}}

QScrollBar::handle:vertical:hover {{
    background: {theme.bg_hover};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {theme.scrollbar_bg};
    height: {TOKENS.sizes.scrollbar_width}px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {theme.scrollbar_handle};
    min-width: {TOKENS.sizes.scrollbar_min_height}px;
    border-radius: {TOKENS.radius.sm}px;
    margin: {TOKENS.spacing.xxs}px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {theme.bg_hover};
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
    background-color: {theme.bg_component};
    color: {theme.text_primary};
    border: none;
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
    font-weight: {TOKENS.typography.weight_medium};
    font-family: {TOKENS.typography.sans};
    min-height: {TOKENS.sizes.button_md}px;
}}

QPushButton:hover {{
    background-color: {theme.bg_hover};
}}

QPushButton:pressed {{
    background-color: {theme.bg_surface};
}}

QPushButton:disabled {{
    background-color: {theme.bg_surface};
    color: {theme.text_disabled};
}}

QPushButton[primary="true"] {{
    background-color: {theme.primary};
    color: {theme.text_on_primary};
}}

QPushButton[primary="true"]:hover {{
    background-color: {theme.primary_hover};
}}

QPushButton[danger="true"] {{
    background-color: {theme.error};
    color: {theme.text_on_error};
}}
"""


def get_input_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QLineEdit."""
    return f"""
/* ==================== INPUTS ==================== */
QLineEdit {{
    background-color: {theme.input_bg};
    color: {theme.text_primary};
    border: 1px solid {theme.border};
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
    selection-background-color: {theme.primary};
    min-height: {TOKENS.sizes.input_md}px;
}}

QLineEdit:focus {{
    border: 1px solid {theme.primary};
    background-color: {theme.bg_surface};
}}

QLineEdit:disabled {{
    background-color: {theme.bg_surface};
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
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px;
    min-height: {TOKENS.sizes.input_md}px;
}}

QComboBox:hover {{
    border-color: {theme.border_light};
}}

QComboBox:focus {{
    border-color: {theme.primary};
}}

QComboBox::drop-down {{
    border: none;
    width: {TOKENS.spacing.lg}px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {theme.text_secondary};
    margin-right: {TOKENS.spacing.xs}px;
}}

QComboBox QAbstractItemView {{
    background-color: {theme.bg_surface};
    border: 1px solid {theme.border_light};
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xs}px;
    selection-background-color: {theme.primary};
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
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.xs}px;
    min-height: {TOKENS.sizes.input_md}px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {theme.primary};
}}
"""


def get_checkbox_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QCheckBox."""
    return f"""
/* ==================== CHECK BOX ==================== */
QCheckBox {{
    spacing: {TOKENS.spacing.xs}px;
    color: {theme.text_primary};
}}

QCheckBox::indicator {{
    width: {TOKENS.sizes.checkbox_size}px;
    height: {TOKENS.sizes.checkbox_size}px;
    border: 1px solid {theme.border_light};
    border-radius: {TOKENS.radius.sm}px;
    background-color: {theme.input_bg};
}}

QCheckBox::indicator:hover {{
    border-color: {theme.primary};
}}

QCheckBox::indicator:checked {{
    background-color: {theme.primary};
    border-color: {theme.primary};
    image: url({CHECKMARK_PATH});
}}
"""


def get_splitter_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QSplitter."""
    return f"""
/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {theme.bg_canvas};
}}

QSplitter::handle:hover {{
    background-color: {theme.primary};
}}
"""


def get_groupbox_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QGroupBox."""
    return f"""
/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {theme.bg_surface};
    border: 1px solid {theme.border};
    border-radius: {TOKENS.radius.lg}px;
    margin-top: {TOKENS.spacing.md}px;
    padding-top: {TOKENS.spacing.sm}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {TOKENS.spacing.xs}px;
    color: {theme.text_secondary};
    font-weight: {TOKENS.typography.weight_semibold};
}}
"""


def get_tooltip_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QToolTip."""
    return f"""
/* ==================== TOOLTIP ==================== */
QToolTip {{
    background-color: {theme.bg_surface};
    color: {theme.text_primary};
    border: 1px solid {theme.border_light};
    border-radius: {TOKENS.radius.sm}px;
    padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
}}
"""


def get_textedit_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QTextEdit and QPlainTextEdit."""
    return f"""
/* ==================== TEXT EDIT ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: {theme.bg_canvas};
    color: {theme.text_primary};
    border: none;
    font-family: {TOKENS.typography.mono};
    font-size: {TOKENS.typography.body}px;
    padding: {TOKENS.spacing.xs}px;
    selection-background-color: {theme.editor_selection};
}}
"""


def get_dialog_styles(theme: CanvasThemeColors) -> str:
    """Generate QSS for QDialog."""
    return f"""
/* ==================== DIALOGS ==================== */
QDialog {{
    background-color: {theme.bg_surface};
    color: {theme.text_primary};
    border: 1px solid {theme.border};
    border-radius: {TOKENS.radius.xl}px;
}}

QDialog QLabel {{
    color: {theme.text_primary};
    font-family: {TOKENS.typography.sans};
}}

QDialog QPushButton {{
    border-radius: {TOKENS.radius.md}px;
    padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
    font-weight: {TOKENS.typography.weight_medium};
    min-width: {TOKENS.sizes.button_min_width}px;
}}
"""


def get_base_stylesheet() -> str:
    """Generate the complete base stylesheet using default THEME."""
    from .colors import THEME
    return get_canvas_stylesheet(THEME)


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
            get_dialog_styles(theme),
        ]
    )

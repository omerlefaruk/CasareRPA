"""
QSS Style generators v2 - Cursor/VS Code-like (Dark-Only, Compact).

Fresh implementation for v2 using TOKENS_V2 and THEME_V2.
Key differences from v1 styles:
- Uses v2 tokens (compact, tight, small radii)
- No transition/animation properties (0ms motion)
- Cursor blue (#0066ff) accent
- Tighter spacing throughout

All functions return QSS strings for direct use with setStyleSheet().

Usage:
    from casare_rpa.presentation.canvas.theme import get_canvas_stylesheet_v2

    stylesheet = get_canvas_stylesheet_v2()
    widget.setStyleSheet(stylesheet)

See: docs/UX_REDESIGN_PLAN.md Phase 1 Epic 1.1
"""

from .tokens_v2 import THEME_V2, TOKENS_V2


def get_main_window_styles_v2() -> str:
    """Generate QSS for QMainWindow (v2)."""
    return f"""
/* ==================== MAIN WINDOW ==================== */
QMainWindow {{
    background-color: {THEME_V2.bg_canvas};
}}

QMainWindow::separator {{
    background-color: {THEME_V2.bg_canvas};
    width: {TOKENS_V2.sizes.splitter_handle}px;
    height: {TOKENS_V2.sizes.splitter_handle}px;
}}

QMainWindow::separator:hover {{
    background-color: {THEME_V2.primary};
}}
"""


def get_base_widget_styles_v2() -> str:
    """Generate QSS for base QWidget (v2)."""
    return f"""
/* ==================== BASE WIDGET ==================== */
QWidget {{
    background-color: transparent;
    color: {THEME_V2.text_primary};
    font-family: {TOKENS_V2.typography.sans};
    font-size: {TOKENS_V2.typography.body}px;
}}

QLabel[muted="true"] {{
    color: {THEME_V2.text_muted};
}}
"""


def get_menu_styles_v2() -> str:
    """Generate QSS for QMenuBar and QMenu (v2)."""
    return f"""
/* ==================== MENU BAR ==================== */
QMenuBar {{
    background-color: {THEME_V2.bg_header};
    color: {THEME_V2.text_primary};
    border-bottom: 1px solid {THEME_V2.border};
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xxs}px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 1px {TOKENS_V2.spacing.sm}px;
    border-radius: {TOKENS_V2.radius.xs}px;
}}

QMenuBar::item:selected {{
    background-color: {THEME_V2.bg_hover};
    color: {THEME_V2.text_primary};
}}

/* ==================== CONTEXT MENU (Cursor Style) ==================== */
QMenu {{
    background-color: {THEME_V2.menu_bg};
    border: 1px solid {THEME_V2.menu_border};
    border-radius: {TOKENS_V2.radius.md}px;
    padding: 1px;
}}

QMenu::item {{
    background-color: transparent;
    padding: 1px {TOKENS_V2.spacing.xs}px 1px {TOKENS_V2.spacing.xs}px;
    border-radius: {TOKENS_V2.radius.xs}px;
    height: {max(18, TOKENS_V2.sizes.menu_item_height - 6)}px;
    color: {THEME_V2.text_primary};
    font-size: {TOKENS_V2.typography.body_sm}px;
}}

QMenu::item:selected {{
    background-color: {THEME_V2.primary};
    color: {THEME_V2.text_on_primary};
}}

QMenu::item:disabled {{
    color: {THEME_V2.text_disabled};
}}

QMenu::separator {{
    height: 1px;
    background-color: {THEME_V2.border};
    margin: 1px {TOKENS_V2.spacing.xxs}px;
}}

QMenu::indicator {{
    width: 12px;
    height: 12px;
    left: 1px;
}}

QMenu::icon {{
    width: 12px;
    height: 12px;
}}

QMenu::indicator:exclusive {{
    width: 10px;
    height: 10px;
    border-radius: 5px;
    border: 2px solid {THEME_V2.text_secondary};
}}

QMenu::indicator:exclusive:selected {{
    background-color: {THEME_V2.primary};
    border-color: {THEME_V2.primary};
}}

QMenu::indicator:non-exclusive {{
    width: 12px;
    height: 12px;
    border: 2px solid {THEME_V2.text_secondary};
    border-radius: 2px;
}}

QMenu::indicator:non-exclusive:checked {{
    background-color: {THEME_V2.primary};
    border-color: {THEME_V2.primary};
}}
"""


def get_toolbar_styles_v2() -> str:
    """Generate QSS for QToolBar and QToolButton (v2)."""
    return f"""
/* ==================== TOOLBAR ==================== */
QToolBar {{
    background-color: {THEME_V2.toolbar_bg};
    border: none;
    border-bottom: 1px solid {THEME_V2.toolbar_border};
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    spacing: {TOKENS_V2.spacing.xxs}px;
}}

QToolBar::separator {{
    background-color: {THEME_V2.border};
    width: 1px;
    margin: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
}}

QToolButton {{
    background-color: transparent;
    border: none;
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    color: {THEME_V2.text_secondary};
    font-weight: {TOKENS_V2.typography.weight_medium};
}}

QToolButton:hover {{
    background-color: {THEME_V2.bg_hover};
    color: {THEME_V2.text_primary};
}}

QToolButton:pressed {{
    background-color: {THEME_V2.bg_component};
}}

QToolButton:checked {{
    background-color: {THEME_V2.primary};
    color: {THEME_V2.text_on_primary};
}}
"""


def get_statusbar_styles_v2() -> str:
    """Generate QSS for QStatusBar (v2)."""
    return f"""
/* ==================== STATUS BAR ==================== */
QStatusBar {{
    background-color: {THEME_V2.bg_canvas};
    border-top: 1px solid {THEME_V2.border};
    color: {THEME_V2.text_secondary};
    font-size: {TOKENS_V2.typography.body_sm}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
}}

QStatusBar::item {{
    border: none;
}}
"""


def get_dock_widget_styles_v2() -> str:
    """Generate QSS for QDockWidget (v2)."""
    return f"""
/* ==================== DOCK WIDGETS ==================== */
QDockWidget {{
    background-color: {THEME_V2.bg_surface};
    border: none;
    color: {THEME_V2.text_primary};
}}

QDockWidget::title {{
    background-color: {THEME_V2.bg_header};
    color: {THEME_V2.text_secondary};
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xxs}px;
    font-weight: {TOKENS_V2.typography.weight_semibold};
    font-size: {TOKENS_V2.typography.caption}px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid {THEME_V2.border};
}}

QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    padding: {TOKENS_V2.spacing.xxs}px;
    icon-size: {TOKENS_V2.sizes.icon_sm}px;
}}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {{
    background: {THEME_V2.bg_hover};
    border-radius: {TOKENS_V2.radius.xs}px;
}}

/* ==================== DOCK DENSITY (COMPACT) ==================== */
QDockWidget QPushButton {{
    min-height: 16px;
    padding: 0px 4px;
    border-radius: {TOKENS_V2.radius.xs}px;
    font-size: {TOKENS_V2.typography.body_sm}px;
}}

QDockWidget QWidget[panelToolbar="true"] {{
    background-color: {THEME_V2.bg_header};
    border-bottom: 1px solid {THEME_V2.border};
    min-height: {TOKENS_V2.sizes.input_lg}px;
    max-height: {TOKENS_V2.sizes.input_lg}px;
}}

QDockWidget QLineEdit,
QDockWidget QComboBox,
QDockWidget QSpinBox,
QDockWidget QDoubleSpinBox {{
    min-height: {TOKENS_V2.sizes.input_sm}px;
    font-size: {TOKENS_V2.typography.body_sm}px;
    padding: 0px {TOKENS_V2.spacing.xs}px;
}}

QDockWidget QWidget[panelToolbar="true"] QCheckBox {{
    font-size: {TOKENS_V2.typography.body_sm}px;
    color: {THEME_V2.text_secondary};
    spacing: {TOKENS_V2.spacing.xxs}px;
}}

QDockWidget QWidget[panelToolbar="true"] QCheckBox::indicator {{
    width: 12px;
    height: 12px;
}}

QDockWidget QWidget[panelToolbar="true"] QLabel {{
    font-size: {TOKENS_V2.typography.body_sm}px;
    color: {THEME_V2.text_secondary};
}}

QDockWidget QTabBar::tab {{
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    font-size: {TOKENS_V2.typography.body_sm}px;
    min-height: 20px;
    min-width: 60px;
}}
"""


def get_tab_widget_styles_v2() -> str:
    """Generate QSS for QTabWidget and QTabBar (v2)."""
    return f"""
/* ==================== TAB WIDGET ==================== */
QTabWidget::pane {{
    background-color: {THEME_V2.bg_surface};
    border: none;
    border-top: 1px solid {THEME_V2.border};
}}

QTabBar {{
    background-color: {THEME_V2.bg_surface};
}}

QTabBar::tab {{
    background-color: transparent;
    color: {THEME_V2.text_secondary};
    padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: {TOKENS_V2.spacing.xxs}px;
    font-weight: {TOKENS_V2.typography.weight_medium};
    font-size: {TOKENS_V2.typography.body}px;
    min-height: {TOKENS_V2.sizes.tab_height}px;
    min-width: {TOKENS_V2.sizes.tab_min_width}px;
}}

QTabBar::tab:selected {{
    color: {THEME_V2.text_primary};
    border-bottom: 2px solid {THEME_V2.primary};
}}

QTabBar::tab:hover:!selected {{
    color: {THEME_V2.text_primary};
    background-color: {THEME_V2.bg_hover};
    border-radius: {TOKENS_V2.radius.xs}px {TOKENS_V2.radius.xs}px 0 0;
}}
"""


def get_table_styles_v2() -> str:
    """Generate QSS for table/tree/list views (v2)."""
    return f"""
/* ==================== TABLES ==================== */
QTableView, QTableWidget, QTreeView, QTreeWidget, QListView, QListWidget {{
    background-color: {THEME_V2.bg_surface};
    alternate-background-color: {THEME_V2.bg_elevated};
    border: none;
    selection-background-color: {THEME_V2.bg_selected};
    selection-color: {THEME_V2.text_on_primary};
    outline: none;
}}

QTableView::item, QTreeView::item, QListView::item {{
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    border: none;
    border-bottom: 1px solid {THEME_V2.border_dark};
}}

QTableView::item:selected, QTreeView::item:selected, QListView::item:selected {{
    background-color: {THEME_V2.bg_selected};
    border-radius: {TOKENS_V2.radius.xs}px;
}}

QTableView::item:hover, QTreeView::item:hover, QListView::item:hover {{
    background-color: {THEME_V2.bg_hover};
}}
"""


def get_header_view_styles_v2() -> str:
    """Generate QSS for QHeaderView (v2)."""
    return f"""
/* ==================== HEADER VIEW ==================== */
QHeaderView {{
    background-color: {THEME_V2.bg_surface};
    border: none;
}}

QHeaderView::section {{
    background-color: {THEME_V2.bg_surface};
    color: {THEME_V2.text_secondary};
    min-height: {TOKENS_V2.sizes.input_lg}px;
    max-height: {TOKENS_V2.sizes.input_lg}px;
    padding: 0 {TOKENS_V2.spacing.xs}px;
    border: none;
    border-bottom: 1px solid {THEME_V2.border};
    font-weight: {TOKENS_V2.typography.weight_semibold};
    font-size: {TOKENS_V2.typography.body_sm}px;
    text-transform: uppercase;
}}
"""


def get_scrollbar_styles_v2() -> str:
    """Generate QSS for scrollbars (v2 - slim, modern)."""
    return f"""
/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {{
    background: {THEME_V2.scrollbar_bg};
    width: {TOKENS_V2.sizes.scrollbar_width}px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {THEME_V2.scrollbar_handle};
    min-height: {TOKENS_V2.sizes.scrollbar_min_height}px;
    border-radius: {TOKENS_V2.radius.xs}px;
    margin: {TOKENS_V2.spacing.xxs}px;
}}

QScrollBar::handle:vertical:hover {{
    background: {THEME_V2.bg_hover};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {THEME_V2.scrollbar_bg};
    height: {TOKENS_V2.sizes.scrollbar_width}px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: {THEME_V2.scrollbar_handle};
    min-width: {TOKENS_V2.sizes.scrollbar_min_height}px;
    border-radius: {TOKENS_V2.radius.xs}px;
    margin: {TOKENS_V2.spacing.xxs}px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {THEME_V2.bg_hover};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


def get_button_styles_v2() -> str:
    """Generate QSS for QPushButton (v2)."""
    return f"""
/* ==================== BUTTONS ==================== */
QPushButton {{
    background-color: {THEME_V2.bg_component};
    color: {THEME_V2.text_primary};
    border: none;
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.sm}px;
    font-weight: {TOKENS_V2.typography.weight_medium};
    font-family: {TOKENS_V2.typography.sans};
    min-height: {TOKENS_V2.sizes.button_md}px;
    font-size: {TOKENS_V2.typography.body}px;
}}

QPushButton:hover {{
    background-color: {THEME_V2.bg_hover};
}}

QPushButton:pressed {{
    background-color: {THEME_V2.bg_surface};
}}

QPushButton:disabled {{
    background-color: {THEME_V2.bg_surface};
    color: {THEME_V2.text_disabled};
}}

QPushButton[primary="true"] {{
    background-color: {THEME_V2.primary};
    color: {THEME_V2.text_on_primary};
}}

QPushButton[primary="true"]:hover {{
    background-color: {THEME_V2.primary_hover};
}}

QPushButton[primary="true"]:pressed {{
    background-color: {THEME_V2.primary_active};
}}

QPushButton[danger="true"] {{
    background-color: {THEME_V2.error};
    color: {THEME_V2.text_on_error};
}}
"""


def get_input_styles_v2() -> str:
    """Generate QSS for QLineEdit (v2)."""
    return f"""
/* ==================== INPUTS ==================== */
QLineEdit {{
    background-color: {THEME_V2.input_bg};
    color: {THEME_V2.text_primary};
    border: 1px solid {THEME_V2.border};
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    selection-background-color: {THEME_V2.primary};
    min-height: {TOKENS_V2.sizes.input_md}px;
    font-size: {TOKENS_V2.typography.body}px;
}}

QLineEdit:focus {{
    border: 1px solid {THEME_V2.border_focus};
    background-color: {THEME_V2.bg_surface};
}}

QLineEdit:disabled {{
    background-color: {THEME_V2.bg_surface};
    color: {THEME_V2.text_disabled};
    border-color: transparent;
}}
"""


def get_combobox_styles_v2() -> str:
    """Generate QSS for QComboBox (v2)."""
    return f"""
/* ==================== COMBO BOX ==================== */
QComboBox {{
    background-color: {THEME_V2.input_bg};
    color: {THEME_V2.text_primary};
    border: 1px solid {THEME_V2.border};
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    min-height: {TOKENS_V2.sizes.input_md}px;
    font-size: {TOKENS_V2.typography.body}px;
}}

QComboBox:hover {{
    border-color: {THEME_V2.border_light};
}}

QComboBox:focus {{
    border-color: {THEME_V2.border_focus};
}}

QComboBox::drop-down {{
    border: none;
    width: {TOKENS_V2.spacing.sm}px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {THEME_V2.text_secondary};
    margin-right: {TOKENS_V2.spacing.xxs}px;
}}

QComboBox QAbstractItemView {{
    background-color: {THEME_V2.bg_surface};
    border: 1px solid {THEME_V2.border_light};
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xxs}px;
    selection-background-color: {THEME_V2.primary};
    outline: none;
}}
"""


def get_spinbox_styles_v2() -> str:
    """Generate QSS for QSpinBox and QDoubleSpinBox (v2)."""
    return f"""
/* ==================== SPIN BOX ==================== */
QSpinBox, QDoubleSpinBox {{
    background-color: {THEME_V2.input_bg};
    color: {THEME_V2.text_primary};
    border: 1px solid {THEME_V2.border};
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xxs}px;
    min-height: {TOKENS_V2.sizes.input_md}px;
    font-size: {TOKENS_V2.typography.body}px;
}}

QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {THEME_V2.border_focus};
}}
"""


def get_checkbox_styles_v2() -> str:
    """Generate QSS for QCheckBox (v2)."""
    return f"""
/* ==================== CHECK BOX ==================== */
QCheckBox {{
    spacing: {TOKENS_V2.spacing.xxs}px;
    color: {THEME_V2.text_primary};
    font-size: {TOKENS_V2.typography.body}px;
}}

QCheckBox::indicator {{
    width: {TOKENS_V2.sizes.checkbox_size}px;
    height: {TOKENS_V2.sizes.checkbox_size}px;
    border: 1px solid {THEME_V2.border_light};
    border-radius: {TOKENS_V2.radius.xs}px;
    background-color: {THEME_V2.input_bg};
}}

QCheckBox::indicator:hover {{
    border-color: {THEME_V2.primary};
}}

QCheckBox::indicator:checked {{
    background-color: {THEME_V2.primary};
    border-color: {THEME_V2.primary};
}}
"""


def get_splitter_styles_v2() -> str:
    """Generate QSS for QSplitter (v2)."""
    return f"""
/* ==================== SPLITTER ==================== */
QSplitter::handle {{
    background-color: {THEME_V2.border_dark};
}}

QSplitter::handle:hover {{
    background-color: {THEME_V2.primary};
}}
"""


def get_groupbox_styles_v2() -> str:
    """Generate QSS for QGroupBox (v2)."""
    return f"""
/* ==================== GROUP BOX ==================== */
QGroupBox {{
    background-color: {THEME_V2.bg_surface};
    border: 1px solid {THEME_V2.border};
    border-radius: {TOKENS_V2.radius.lg}px;
    margin-top: {TOKENS_V2.spacing.sm}px;
    padding-top: {TOKENS_V2.spacing.xs}px;
    font-size: {TOKENS_V2.typography.body}px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 {TOKENS_V2.spacing.xxs}px;
    color: {THEME_V2.text_secondary};
    font-weight: {TOKENS_V2.typography.weight_semibold};
}}
"""


def get_tooltip_styles_v2() -> str:
    """Generate QSS for QToolTip (v2)."""
    return f"""
/* ==================== TOOLTIP ==================== */
QToolTip {{
    background-color: {THEME_V2.bg_elevated};
    color: {THEME_V2.text_primary};
    border: 1px solid {THEME_V2.border_light};
    border-radius: {TOKENS_V2.radius.xs}px;
    padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
    font-size: {TOKENS_V2.typography.body_sm}px;
}}
"""


def get_textedit_styles_v2() -> str:
    """Generate QSS for QTextEdit and QPlainTextEdit (v2)."""
    return f"""
/* ==================== TEXT EDIT ==================== */
QTextEdit, QPlainTextEdit {{
    background-color: {THEME_V2.input_bg};
    color: {THEME_V2.text_primary};
    border: none;
    font-family: {TOKENS_V2.typography.mono};
    font-size: {TOKENS_V2.typography.body}px;
    padding: {TOKENS_V2.spacing.xs}px;
    selection-background-color: {THEME_V2.bg_selected};
}}
"""


def get_dialog_styles_v2() -> str:
    """Generate QSS for QDialog (v2)."""
    return f"""
/* ==================== DIALOGS ==================== */
QDialog {{
    background-color: {THEME_V2.bg_surface};
    color: {THEME_V2.text_primary};
    border: 1px solid {THEME_V2.border};
}}

QDialog QLabel {{
    color: {THEME_V2.text_primary};
    font-family: {TOKENS_V2.typography.sans};
    font-size: {TOKENS_V2.typography.body}px;
}}

QDialog QPushButton {{
    border-radius: {TOKENS_V2.radius.sm}px;
    padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
    font-weight: {TOKENS_V2.typography.weight_medium};
    min-width: {TOKENS_V2.sizes.button_min_width}px;
    font-size: {TOKENS_V2.typography.body}px;
}}
"""


def get_canvas_stylesheet_v2() -> str:
    """
    Generate the complete v2 Canvas application stylesheet.

    Returns:
        Complete QSS stylesheet using v2 tokens (dark-only, compact).
        No transitions/animations (zero-motion policy).
    """
    return "".join(
        [
            get_main_window_styles_v2(),
            get_base_widget_styles_v2(),
            get_menu_styles_v2(),
            get_toolbar_styles_v2(),
            get_statusbar_styles_v2(),
            get_dock_widget_styles_v2(),
            get_tab_widget_styles_v2(),
            get_table_styles_v2(),
            get_header_view_styles_v2(),
            get_scrollbar_styles_v2(),
            get_button_styles_v2(),
            get_input_styles_v2(),
            get_combobox_styles_v2(),
            get_spinbox_styles_v2(),
            get_checkbox_styles_v2(),
            get_splitter_styles_v2(),
            get_groupbox_styles_v2(),
            get_tooltip_styles_v2(),
            get_textedit_styles_v2(),
            get_dialog_styles_v2(),
        ]
    )


def get_popup_styles_v2() -> str:
    """
    Generate QSS for PopupWindowBase (v2).

    Returns:
        QSS stylesheet for v2 popup components.
        No shadows, no animations, crisp borders.
    """
    return f"""
/* ==================== POPUP WINDOW BASE ==================== */
PopupWindowBase {{
    background: transparent;
}}

PopupWindowBase QFrame#popupContainer {{
    background-color: {THEME_V2.bg_elevated};
    border: 1px solid {THEME_V2.border};
    border-radius: {TOKENS_V2.radius.md}px;
}}

PopupWindowBase QFrame#header {{
    background-color: {THEME_V2.bg_component};
    border-top-left-radius: {TOKENS_V2.radius.md}px;
    border-top-right-radius: {TOKENS_V2.radius.md}px;
    border-bottom: 1px solid {THEME_V2.border};
}}

PopupWindowBase QFrame#contentArea {{
    background-color: {THEME_V2.bg_elevated};
    border-bottom-left-radius: {TOKENS_V2.radius.md}px;
    border-bottom-right-radius: {TOKENS_V2.radius.md}px;
}}

/* Header buttons */
PopupWindowBase QFrame#header QPushButton {{
    background: transparent;
    border: none;
    border-radius: {TOKENS_V2.radius.xs}px;
    color: {THEME_V2.text_secondary};
    font-size: 14px;
}}

PopupWindowBase QFrame#header QPushButton:hover {{
    background-color: {THEME_V2.bg_hover};
    color: {THEME_V2.text_primary};
}}

PopupWindowBase QFrame#header QPushButton:checked {{
    color: {THEME_V2.primary};
}}

/* Header label */
PopupWindowBase QFrame#header QLabel {{
    color: {THEME_V2.text_primary};
    font-size: {TOKENS_V2.typography.body_sm}px;
    font-weight: {TOKENS_V2.typography.weight_medium};
}}

/* Resize grip */
ResizeGrip {{
    background-color: transparent;
    border: none;
}}

ResizeGrip:hover {{
    background-color: {THEME_V2.border_focus};
}}
"""

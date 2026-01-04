"""
Dialog-specific QSS generators v2.

Uses THEME_V2 and TOKENS_V2 for consistent styling.
No shadows, no animations, crisp borders.

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs_v2._styles import (
        get_dialog_base_styles_v2,
        get_dialog_footer_styles_v2,
        get_dialog_title_styles_v2,
    )

    stylesheet = get_dialog_base_styles_v2()
    dialog.setStyleSheet(stylesheet)
"""

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2


def get_dialog_base_styles_v2() -> str:
    """
    Generate QSS for BaseDialogV2.

    Returns:
        QSS stylesheet for base dialog container.
    """
    t = THEME_V2
    tok = TOKENS_V2

    return f"""
/* ==================== DIALOG V2 BASE ==================== */
BaseDialogV2 {{
    background-color: {t.bg_surface};
    border: 1px solid {t.border};
    border-radius: {tok.radius.lg}px;
}}

/* Main container */
BaseDialogV2 #dialogContainer {{
    background-color: {t.bg_surface};
    border-radius: {tok.radius.lg}px;
}}

/* Body area */
BaseDialogV2 #dialogBody {{
    background-color: {t.bg_surface};
    border-bottom-left-radius: {tok.radius.lg}px;
    border-bottom-right-radius: {tok.radius.lg}px;
}}

/* Body labels */
BaseDialogV2 #dialogBody QLabel {{
    color: {t.text_primary};
    font-family: {tok.typography.family};
    font-size: {tok.typography.body}px;
}}

/* Body text edits */
BaseDialogV2 #dialogBody QTextEdit,
BaseDialogV2 #dialogBody QPlainTextEdit {{
    background-color: {t.input_bg};
    color: {t.text_primary};
    border: 1px solid {t.border};
    border-radius: {tok.radius.sm}px;
    padding: {tok.spacing.xs}px;
    font-family: {tok.typography.family};
    font-size: {tok.typography.body}px;
    selection-background-color: {t.bg_selected};
}}

BaseDialogV2 #dialogBody QTextEdit:focus,
BaseDialogV2 #dialogBody QPlainTextEdit:focus {{
    border-color: {t.border_focus};
}}

/* Body line edits */
BaseDialogV2 #dialogBody QLineEdit {{
    background-color: {t.input_bg};
    color: {t.text_primary};
    border: 1px solid {t.border};
    border-radius: {tok.radius.sm}px;
    padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
    min-height: {tok.sizes.input_md}px;
    font-size: {tok.typography.body}px;
}}

BaseDialogV2 #dialogBody QLineEdit:focus {{
    border-color: {t.border_focus};
}}

/* Body spin boxes */
BaseDialogV2 #dialogBody QSpinBox,
BaseDialogV2 #dialogBody QDoubleSpinBox {{
    background-color: {t.input_bg};
    color: {t.text_primary};
    border: 1px solid {t.border};
    border-radius: {tok.radius.sm}px;
    padding: {tok.spacing.xxs}px {tok.spacing.xxs}px;
    min-height: {tok.sizes.input_md}px;
}}

BaseDialogV2 #dialogBody QSpinBox:focus,
BaseDialogV2 #dialogBody QDoubleSpinBox:focus {{
    border-color: {t.border_focus};
}}

/* Body combo boxes */
BaseDialogV2 #dialogBody QComboBox {{
    background-color: {t.input_bg};
    color: {t.text_primary};
    border: 1px solid {t.border};
    border-radius: {tok.radius.sm}px;
    padding: {tok.spacing.xxs}px {tok.spacing.xs}px;
    min-height: {tok.sizes.input_md}px;
}}

BaseDialogV2 #dialogBody QComboBox:focus {{
    border-color: {t.border_focus};
}}

BaseDialogV2 #dialogBody QComboBox::drop-down {{
    border: none;
    width: {tok.spacing.sm}px;
}}

BaseDialogV2 #dialogBody QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {t.text_secondary};
    margin-right: {tok.spacing.xxs}px;
}}

BaseDialogV2 #dialogBody QComboBox QAbstractItemView {{
    background-color: {t.bg_elevated};
    border: 1px solid {t.border};
    border-radius: {tok.radius.sm}px;
    padding: {tok.spacing.xxs}px;
    selection-background-color: {t.primary};
}}

/* Body check boxes */
BaseDialogV2 #dialogBody QCheckBox {{
    spacing: {tok.spacing.xxs}px;
    color: {t.text_primary};
}}

BaseDialogV2 #dialogBody QCheckBox::indicator {{
    width: {tok.sizes.checkbox_size}px;
    height: {tok.sizes.checkbox_size}px;
    border: 1px solid {t.border_light};
    border-radius: {tok.radius.xs}px;
    background-color: {t.input_bg};
}}

BaseDialogV2 #dialogBody QCheckBox::indicator:checked {{
    background-color: {t.primary};
    border-color: {t.primary};
}}

/* Body scrollbars */
BaseDialogV2 #dialogBody QScrollBar:vertical {{
    background: {t.scrollbar_bg};
    width: {tok.sizes.scrollbar_width}px;
    margin: 0;
}}

BaseDialogV2 #dialogBody QScrollBar::handle:vertical {{
    background: {t.scrollbar_handle};
    min-height: {tok.sizes.scrollbar_min_height}px;
    border-radius: {tok.radius.xs}px;
    margin: {tok.spacing.xxs}px;
}}

BaseDialogV2 #dialogBody QScrollBar::handle:vertical:hover {{
    background: {t.bg_hover};
}}

BaseDialogV2 #dialogBody QScrollBar::add-line:vertical,
BaseDialogV2 #dialogBody QScrollBar::sub-line:vertical {{
    height: 0;
}}

BaseDialogV2 #dialogBody QScrollBar:horizontal {{
    background: {t.scrollbar_bg};
    height: {tok.sizes.scrollbar_width}px;
    margin: 0;
}}

BaseDialogV2 #dialogBody QScrollBar::handle:horizontal {{
    background: {t.scrollbar_handle};
    min-width: {tok.sizes.scrollbar_min_height}px;
    border-radius: {tok.radius.xs}px;
    margin: {tok.spacing.xxs}px;
}}

BaseDialogV2 #dialogBody QScrollBar::handle:horizontal:hover {{
    background: {t.bg_hover};
}}

BaseDialogV2 #dialogBody QScrollBar::add-line:horizontal,
BaseDialogV2 #dialogBody QScrollBar::sub-line:horizontal {{
    width: 0;
}}
"""


def get_dialog_footer_styles_v2() -> str:
    """
    Generate QSS for DialogFooter.

    Returns:
        QSS stylesheet for dialog footer with button row.
    """
    t = THEME_V2
    tok = TOKENS_V2

    return f"""
/* ==================== DIALOG V2 FOOTER ==================== */
DialogFooter {{
    background-color: {t.bg_surface};
    border-top: 1px solid {t.border};
    border-bottom-left-radius: {tok.radius.lg}px;
    border-bottom-right-radius: {tok.radius.lg}px;
}}

DialogFooter QPushButton {{
    border-radius: {tok.radius.sm}px;
    padding: {tok.spacing.xs}px {tok.spacing.sm}px;
    font-weight: {tok.typography.weight_medium};
    min-width: {tok.sizes.button_min_width}px;
    font-size: {tok.typography.body}px;
}}

DialogFooter QPushButton[role="primary"] {{
    background-color: {t.primary};
    color: {t.text_on_primary};
    border: 1px solid {t.primary};
}}

DialogFooter QPushButton[role="primary"]:hover {{
    background-color: {t.primary_hover};
    border-color: {t.primary_hover};
}}

DialogFooter QPushButton[role="primary"]:pressed {{
    background-color: {t.primary_active};
}}

DialogFooter QPushButton[role="primary"]:disabled {{
    background-color: {t.bg_component};
    border-color: {t.border};
    color: {t.text_disabled};
}}

DialogFooter QPushButton[role="secondary"] {{
    background-color: {t.bg_component};
    color: {t.text_primary};
    border: 1px solid {t.border};
}}

DialogFooter QPushButton[role="secondary"]:hover {{
    background-color: {t.bg_hover};
    border-color: {t.border_light};
}}

DialogFooter QPushButton[role="secondary"]:pressed {{
    background-color: {t.bg_selected};
}}

DialogFooter QPushButton[role="secondary"]:disabled {{
    background-color: {t.bg_surface};
    color: {t.text_disabled};
}}

DialogFooter QPushButton[role="destructive"] {{
    background-color: {t.error};
    color: {t.text_on_error};
    border: 1px solid {t.error};
}}

DialogFooter QPushButton[role="destructive"]:hover {{
    background-color: {t.error_hover};
    border-color: {t.error_hover};
}}

DialogFooter QPushButton[role="destructive"]:pressed {{
    background-color: {t.error_active};
}}

DialogFooter QPushButton[role="destructive"]:disabled {{
    background-color: {t.bg_component};
    border-color: {t.border};
    color: {t.text_disabled};
}}

DialogFooter QPushButton[role="cancel"] {{
    background-color: transparent;
    color: {t.text_primary};
    border: 1px solid transparent;
}}

DialogFooter QPushButton[role="cancel"]:hover {{
    background-color: {t.bg_hover};
    border-color: {t.border};
}}

DialogFooter QPushButton[role="cancel"]:pressed {{
    background-color: {t.bg_selected};
}}

DialogFooter QPushButton[role="cancel"]:disabled {{
    color: {t.text_disabled};
}}
"""


def get_dialog_title_styles_v2() -> str:
    """
    Generate QSS for DialogTitleBar.

    Returns:
        QSS stylesheet for dialog title bar.
    """
    t = THEME_V2
    tok = TOKENS_V2

    return f"""
/* ==================== DIALOG V2 TITLE BAR ==================== */
DialogTitleBar {{
    background-color: {t.bg_surface};
    border-bottom: 1px solid {t.border};
    border-top-left-radius: {tok.radius.lg}px;
    border-top-right-radius: {tok.radius.lg}px;
}}

DialogTitleBar QLabel {{
    color: {t.text_primary};
    font-family: {tok.typography.family};
    font-size: {tok.typography.heading_md}px;
    font-weight: {tok.typography.weight_semibold};
    padding: {tok.spacing.xs}px;
}}

DialogTitleBar QPushButton {{
    background: transparent;
    border: none;
    border-radius: {tok.radius.xs}px;
    color: {t.text_secondary};
    padding: {tok.spacing.xxs}px;
}}

DialogTitleBar QPushButton:hover {{
    background-color: {t.bg_hover};
    color: {t.text_primary};
}}

DialogTitleBar QPushButton:pressed {{
    background-color: {t.bg_selected};
}}
"""


def get_dialog_styles_v2() -> str:
    """
    Generate complete QSS for all v2 dialog components.

    Returns:
        Combined stylesheet for all dialog components.
    """
    return "\n".join(
        [
            get_dialog_base_styles_v2(),
            get_dialog_footer_styles_v2(),
            get_dialog_title_styles_v2(),
        ]
    )

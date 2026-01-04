"""
Dialog Styling Standards for CasareRPA.

Provides consistent styling across all dialogs with ElevenLabs design tokens:
- 28px border radius for dialogs (ElevenLabs radius-2xl)
- 8px border radius for inputs/buttons (ElevenLabs radius-md)
- Inter font family
- Proper spacing and typography

Usage:
    from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
        DialogStyles, DialogSize, apply_dialog_style
    )

    class MyDialog(QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)
            apply_dialog_style(self, DialogSize.MD)
"""

from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import QDialog, QMessageBox, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS


class DialogSize(Enum):
    """Standard dialog sizes."""

    SM = "sm"  # 400x300 - Simple confirmations, small forms
    MD = "md"  # 600x450 - Standard forms, settings
    LG = "lg"  # 800x600 - Complex forms, multi-tab dialogs
    XL = "xl"  # 1000x750 - Wizards, dashboards


# Size dimensions
DIALOG_DIMENSIONS = {
    DialogSize.SM: (400, 300),
    DialogSize.MD: (600, 450),
    DialogSize.LG: (800, 600),
    DialogSize.XL: (1000, 750),
}


@dataclass(frozen=True)
class DialogColors:
    """
    Dialog color palette using ElevenLabs-inspired theme.

    All colors sourced from THEME for consistency.
    """

    # Backgrounds (from THEME)
    bg_dialog: str = THEME.bg_surface  # Dialog background
    bg_panel: str = THEME.bg_surface  # Panel/card background
    bg_input: str = THEME.input_bg  # Input field background
    bg_input_readonly: str = THEME.bg_surface  # Read-only input
    bg_button: str = THEME.bg_component  # Secondary button
    bg_button_primary: str = THEME.primary  # Primary button (Indigo 500)
    bg_button_danger: str = THEME.error  # Danger button
    bg_hover: str = THEME.bg_hover  # Hover state
    bg_header: str = THEME.bg_surface  # Header background

    # Text (from THEME)
    text_primary: str = THEME.text_primary  # Main text
    text_secondary: str = THEME.text_secondary  # Secondary text
    text_muted: str = THEME.text_muted  # Muted/placeholder
    text_disabled: str = THEME.text_disabled  # Disabled state
    text_error: str = THEME.error  # Error message
    text_success: str = THEME.success  # Success message
    text_warning: str = THEME.warning  # Warning message

    # Borders (from THEME)
    border: str = THEME.border  # Standard border
    border_light: str = THEME.border_light  # Light border
    border_input: str = THEME.border  # Input border
    border_focus: str = THEME.border_focus  # Focus ring

    # Accent (from THEME)
    accent_primary: str = THEME.primary  # Indigo 500
    accent_hover: str = THEME.primary_hover  # Indigo 600
    accent_pressed: str = THEME.primary_active  # Indigo 700


# Global colors instance
COLORS = DialogColors()


class DialogStyles:
    """
    Centralized dialog styling methods.

    All methods return QSS stylesheet strings.
    """

    @staticmethod
    def dialog_base() -> str:
        """
        Base dialog styling with ElevenLabs design tokens.

        Uses 28px radius (RADIUS.two_xl) for dialog containers.
        """
        return f"""
            QDialog {{
                background-color: {COLORS.bg_dialog};
                color: {COLORS.text_primary};
                font-family: {TOKENS.typography.ui};
            }}
            QLabel {{
                color: {COLORS.text_primary};
                font-family: {TOKENS.typography.ui};
            }}
        """

    @staticmethod
    def header(font_size: int = 16) -> str:
        """
        Header styling with bottom separator.

        Args:
            font_size: Header font size in pixels (default 16 = TOKENS.typography.xl)
        """
        return f"""
            font-size: {font_size}px;
            font-weight: bold;
            color: {COLORS.text_primary};
            font-family: {TOKENS.typography.ui};
            padding-bottom: {TOKENS.spacing.md}px;
            border-bottom: 1px solid {COLORS.border};
            margin-bottom: {TOKENS.spacing.md}px;
        """

    @staticmethod
    def subheader() -> str:
        """Subheader/subtitle styling with ElevenLabs tokens."""
        return f"""
            color: {COLORS.text_muted};
            font-size: {TOKENS.typography.md}px;
            font-family: {TOKENS.typography.ui};
            margin-bottom: {TOKENS.spacing.xl}px;
        """

    @staticmethod
    def input_field() -> str:
        """
        Standard input field (QLineEdit) styling with ElevenLabs tokens.

        Uses 8px radius (RADIUS.md) for inputs.
        """
        return f"""
            QLineEdit {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: {TOKENS.spacing.sm}px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
                min-height: 28px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS.border_focus};
            }}
            QLineEdit:read-only {{
                background: {COLORS.bg_input_readonly};
            }}
            QLineEdit:disabled {{
                background: {COLORS.bg_input_readonly};
                color: {COLORS.text_disabled};
            }}
        """

    @staticmethod
    def text_edit() -> str:
        """Text edit (QTextEdit) styling with ElevenLabs tokens."""
        return f"""
            QTextEdit {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: {TOKENS.spacing.sm}px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
            }}
            QTextEdit:focus {{
                border-color: {COLORS.border_focus};
            }}
        """

    @staticmethod
    def combo_box() -> str:
        """ComboBox styling with ElevenLabs tokens."""
        return f"""
            QComboBox {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.sm}px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
                min-height: 28px;
            }}
            QComboBox:focus {{
                border-color: {COLORS.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLORS.text_secondary};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS.bg_panel};
                border: 1px solid {COLORS.border};
                selection-background-color: {COLORS.accent_primary};
                outline: none;
            }}
        """

    @staticmethod
    def spin_box() -> str:
        """SpinBox styling with ElevenLabs tokens."""
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: {TOKENS.spacing.sm}px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
                min-height: 28px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {COLORS.border_focus};
            }}
        """

    @staticmethod
    def checkbox() -> str:
        """Checkbox styling with ElevenLabs tokens."""
        return f"""
            QCheckBox {{
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
                spacing: {TOKENS.spacing.sm}px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {COLORS.border_input};
                border-radius: {TOKENS.radius.sm}px;  /* 4px - ElevenLabs radius-sm */
                background: {COLORS.bg_input};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: {COLORS.accent_primary};
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {COLORS.accent_primary};
                border-radius: {TOKENS.radius.sm}px;  /* 4px */
                background: {COLORS.accent_primary};
            }}
        """

    @staticmethod
    def group_box() -> str:
        """GroupBox styling with ElevenLabs tokens."""
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
                border: 1px solid {COLORS.border};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                margin-top: {TOKENS.spacing.xl}px;
                padding-top: {TOKENS.spacing.sm}px;
                background: {COLORS.bg_button};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS.spacing.xl}px;
                padding: 0 {TOKENS.spacing.xs}px;
                color: {COLORS.text_primary};
            }}
        """

    @staticmethod
    def button_primary() -> str:
        """
        Primary action button (32px height) with ElevenLabs tokens.

        Uses 8px radius (RADIUS.md) for buttons.
        """
        return f"""
            QPushButton {{
                background: {COLORS.bg_button_primary};
                border: none;
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: 0 20px;
                color: white;
                font-size: {TOKENS.typography.md}px;
                font-weight: 600;
                font-family: {TOKENS.typography.ui};
                min-height: 32px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {COLORS.accent_hover};
            }}
            QPushButton:pressed {{
                background: {COLORS.accent_pressed};
            }}
            QPushButton:disabled {{
                background: {COLORS.border};
                color: {COLORS.text_disabled};
            }}
        """

    @staticmethod
    def button_secondary() -> str:
        """
        Secondary action button (32px height) with ElevenLabs tokens.
        """
        return f"""
            QPushButton {{
                background: {COLORS.bg_button};
                border: 1px solid {COLORS.border_light};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: 0 20px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-weight: 500;
                font-family: {TOKENS.typography.ui};
                min-height: 32px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {COLORS.bg_hover};
                border-color: {COLORS.accent_primary};
                color: white;
            }}
            QPushButton:pressed {{
                background: {COLORS.bg_panel};
            }}
            QPushButton:disabled {{
                background: {COLORS.bg_button};
                color: {COLORS.text_disabled};
                border-color: {COLORS.border};
            }}
        """

    @staticmethod
    def button_inline() -> str:
        """Inline button for forms (28px height) with ElevenLabs tokens."""
        return f"""
            QPushButton {{
                background: {COLORS.bg_button_primary};
                border: none;
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: 0 {TOKENS.spacing.xl}px;
                color: white;
                font-size: {TOKENS.typography.sm}px;
                font-weight: 600;
                font-family: {TOKENS.typography.ui};
                min-height: 28px;
            }}
            QPushButton:hover {{
                background: {COLORS.accent_hover};
            }}
        """

    @staticmethod
    def button_danger() -> str:
        """Danger/destructive action button with ElevenLabs tokens."""
        return f"""
            QPushButton {{
                background: {COLORS.bg_button_danger};
                border: none;
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: 0 {TOKENS.spacing.xl}px;
                color: white;
                font-size: {TOKENS.typography.md}px;
                font-weight: 600;
                font-family: {TOKENS.typography.ui};
                min-height: 32px;
            }}
            QPushButton:hover {{
                background: #E53935;
            }}
            QPushButton:disabled {{
                background: {COLORS.border};
                color: {COLORS.text_disabled};
            }}
        """

    @staticmethod
    def tab_widget() -> str:
        """TabWidget styling with ElevenLabs tokens."""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS.border};
                background-color: {COLORS.bg_panel};
            }}
            QTabBar::tab {{
                background-color: {COLORS.bg_button};
                color: {COLORS.text_primary};
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.xl}px;
                border: 1px solid {COLORS.border};
                border-bottom: none;
                border-top-left-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                border-top-right-radius: {TOKENS.radius.md}px;
                margin-right: 2px;
                font-family: {TOKENS.typography.ui};
                font-size: {TOKENS.typography.md}px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS.bg_panel};
                border-bottom: 2px solid {COLORS.accent_primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS.bg_hover};
            }}
        """

    @staticmethod
    def list_widget() -> str:
        """ListWidget styling with ElevenLabs tokens."""
        return f"""
            QListWidget {{
                background-color: {COLORS.bg_panel};
                border: 1px solid {COLORS.border};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                outline: none;
                font-family: {TOKENS.typography.ui};
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.sm}px;
                border-bottom: 1px solid {COLORS.border};
            }}
            QListWidget::item:selected {{
                background-color: {COLORS.accent_pressed};
            }}
            QListWidget::item:hover {{
                background-color: {COLORS.bg_hover};
            }}
        """

    @staticmethod
    def dialog_button_box() -> str:
        """QDialogButtonBox styling with ElevenLabs tokens."""
        return f"""
            QDialogButtonBox {{
                button-layout: 2;
            }}
            QDialogButtonBox QPushButton {{
                background: {COLORS.bg_button};
                border: 1px solid {COLORS.border_light};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: 0 {TOKENS.spacing.xl}px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-weight: 500;
                font-family: {TOKENS.typography.ui};
                min-height: 32px;
                min-width: 80px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background: {COLORS.bg_hover};
                border-color: {COLORS.accent_primary};
                color: white;
            }}
            QDialogButtonBox QPushButton:default {{
                background: {COLORS.bg_button_primary};
                border-color: {COLORS.bg_button_primary};
                color: white;
            }}
            QDialogButtonBox QPushButton:default:hover {{
                background: {COLORS.accent_hover};
            }}
        """

    @staticmethod
    def message_box() -> str:
        """QMessageBox styling with ElevenLabs tokens."""
        return f"""
            QMessageBox {{
                background: {COLORS.bg_panel};
            }}
            QMessageBox QLabel {{
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-family: {TOKENS.typography.ui};
            }}
            QPushButton {{
                background: {COLORS.bg_button};
                border: 1px solid {COLORS.border_light};
                border-radius: {TOKENS.radius.md}px;  /* 8px - ElevenLabs radius-md */
                padding: 0 {TOKENS.spacing.xl}px;
                color: {COLORS.text_primary};
                font-size: {TOKENS.typography.md}px;
                font-weight: 500;
                font-family: {TOKENS.typography.ui};
                min-height: 32px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {COLORS.bg_hover};
                border-color: {COLORS.accent_primary};
                color: white;
            }}
            QPushButton:default {{
                background: {COLORS.accent_primary};
                border-color: {COLORS.accent_primary};
                color: white;
            }}
        """

    @staticmethod
    def nav_bar() -> str:
        """Navigation bar (footer) styling."""
        return f"""
            background: {COLORS.bg_dialog};
            border-top: 1px solid {COLORS.border};
        """

    @staticmethod
    def step_header() -> str:
        """Step/wizard header styling."""
        return f"""
            background: {COLORS.bg_dialog};
            border-bottom: 1px solid {COLORS.border};
        """

    @staticmethod
    def error_label() -> str:
        """Error message label styling."""
        return f"""
            color: {COLORS.text_error};
            font-size: {TOKENS.typography.sm}px;
            padding: {TOKENS.spacing.xs}px 0;
        """

    @staticmethod
    def success_label() -> str:
        """Success message label styling."""
        return f"""
            color: {COLORS.text_success};
            font-size: {TOKENS.typography.sm}px;
            padding: {TOKENS.spacing.xs}px 0;
        """

    @staticmethod
    def warning_label() -> str:
        """Warning message label styling."""
        return f"""
            color: {COLORS.text_warning};
            font-size: {TOKENS.typography.sm}px;
            padding: {TOKENS.spacing.xs}px 0;
        """

    @staticmethod
    def info_label() -> str:
        """Info/muted label styling."""
        return f"""
            color: {COLORS.text_muted};
            font-size: {TOKENS.typography.sm}px;
        """

    @staticmethod
    def scroll_area() -> str:
        """ScrollArea styling."""
        return f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {COLORS.bg_panel};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS.border};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS.border_light};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
        """

    @classmethod
    def full_dialog_style(cls) -> str:
        """
        Complete dialog stylesheet combining all common elements.

        Apply to dialog root for consistent styling.
        """
        return "\n".join(
            [
                cls.dialog_base(),
                cls.input_field(),
                cls.text_edit(),
                cls.combo_box(),
                cls.spin_box(),
                cls.checkbox(),
                cls.group_box(),
                cls.tab_widget(),
                cls.list_widget(),
                cls.dialog_button_box(),
                cls.scroll_area(),
            ]
        )


def apply_dialog_style(
    dialog: QDialog,
    size: DialogSize = DialogSize.MD,
    resizable: bool = True,
) -> None:
    """
    Apply standardized ElevenLabs styling to a dialog.

    Uses 28px radius (RADIUS.two_xl) for dialog containers.

    Args:
        dialog: The QDialog to style
        size: Dialog size category
        resizable: Whether dialog can be resized
    """
    # Set size
    width, height = DIALOG_DIMENSIONS[size]
    dialog.setMinimumSize(width, height)

    if not resizable:
        dialog.setFixedSize(width, height)

    # Apply full style with 28px radius for dialog container
    base_style = DialogStyles.full_dialog_style()
    dialog_radius_style = f"""
        QDialog {{
            border-radius: {TOKENS.radius.two_xl}px;  /* 28px - ElevenLabs radius-2xl */
        }}
    """
    dialog.setStyleSheet(base_style + dialog_radius_style)


def show_styled_message(
    parent: QWidget | None,
    title: str,
    text: str,
    info: str = "",
    icon: QMessageBox.Icon = QMessageBox.Icon.Information,
) -> None:
    """
    Show a styled message box.

    Args:
        parent: Parent widget
        title: Dialog title
        text: Main message text
        info: Optional informative text
        icon: Message box icon
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    if info:
        msg.setInformativeText(info)
    msg.setIcon(icon)
    msg.setStyleSheet(DialogStyles.message_box())
    msg.exec()


def show_styled_warning(
    parent: QWidget | None,
    title: str,
    text: str,
    info: str = "",
) -> None:
    """Show a styled warning message box."""
    show_styled_message(parent, title, text, info, QMessageBox.Icon.Warning)


def show_styled_error(
    parent: QWidget | None,
    title: str,
    text: str,
    info: str = "",
) -> None:
    """Show a styled error message box."""
    show_styled_message(parent, title, text, info, QMessageBox.Icon.Critical)


def show_styled_question(
    parent: QWidget | None,
    title: str,
    text: str,
    buttons: QMessageBox.StandardButton = (
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    ),
    default: QMessageBox.StandardButton = QMessageBox.StandardButton.No,
) -> QMessageBox.StandardButton:
    """
    Show a styled question message box.

    Args:
        parent: Parent widget
        title: Dialog title
        text: Question text
        buttons: Available buttons
        default: Default button

    Returns:
        Selected button
    """
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Question)
    msg.setStandardButtons(buttons)
    msg.setDefaultButton(default)
    msg.setStyleSheet(DialogStyles.message_box())
    return msg.exec()

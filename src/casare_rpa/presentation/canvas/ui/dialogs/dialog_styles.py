"""
Dialog Styling Standards for CasareRPA.

Provides consistent styling across all dialogs:
- Standard sizes
- Button placement (OK/Cancel right-aligned)
- Header styling
- Input field styling
- Error message styling

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
from typing import Optional

from PySide6.QtWidgets import QDialog, QMessageBox, QWidget


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
    """Dialog color palette (VSCode Dark+ aligned)."""

    # Backgrounds
    bg_dialog: str = "#1E1E1E"  # Dialog background
    bg_panel: str = "#252526"  # Panel/card background
    bg_input: str = "#3C3C3C"  # Input field background
    bg_input_readonly: str = "#2D2D30"  # Read-only input
    bg_button: str = "#2D2D30"  # Secondary button
    bg_button_primary: str = "#007ACC"  # Primary button
    bg_button_danger: str = "#D32F2F"  # Danger button
    bg_hover: str = "#2A2D2E"  # Hover state
    bg_header: str = "#2D2D30"  # Header background

    # Text
    text_primary: str = "#D4D4D4"  # Main text
    text_secondary: str = "#CCCCCC"  # Secondary text
    text_muted: str = "#888888"  # Muted/placeholder
    text_disabled: str = "#6B6B6B"  # Disabled state
    text_error: str = "#F44336"  # Error message
    text_success: str = "#4CAF50"  # Success message
    text_warning: str = "#FF9800"  # Warning message

    # Borders
    border: str = "#3E3E42"  # Standard border
    border_light: str = "#454545"  # Light border
    border_input: str = "#5C5C5C"  # Input border
    border_focus: str = "#007ACC"  # Focus ring

    # Accent
    accent_primary: str = "#007ACC"  # VSCode blue
    accent_hover: str = "#1177BB"  # Hover blue
    accent_pressed: str = "#094771"  # Pressed blue


# Global colors instance
COLORS = DialogColors()


class DialogStyles:
    """
    Centralized dialog styling methods.

    All methods return QSS stylesheet strings.
    """

    @staticmethod
    def dialog_base() -> str:
        """Base dialog styling."""
        return f"""
            QDialog {{
                background-color: {COLORS.bg_dialog};
                color: {COLORS.text_primary};
            }}
            QLabel {{
                color: {COLORS.text_primary};
            }}
        """

    @staticmethod
    def header(font_size: int = 16) -> str:
        """
        Header styling with bottom separator.

        Args:
            font_size: Header font size in pixels (default 16)
        """
        return f"""
            font-size: {font_size}px;
            font-weight: bold;
            color: {COLORS.text_primary};
            padding-bottom: 8px;
            border-bottom: 1px solid {COLORS.border};
            margin-bottom: 12px;
        """

    @staticmethod
    def subheader() -> str:
        """Subheader/subtitle styling."""
        return f"""
            color: {COLORS.text_muted};
            font-size: 12px;
            margin-bottom: 16px;
        """

    @staticmethod
    def input_field() -> str:
        """Standard input field (QLineEdit) styling."""
        return f"""
            QLineEdit {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS.text_primary};
                font-size: 12px;
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
        """Text edit (QTextEdit) styling."""
        return f"""
            QTextEdit {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: 4px;
                padding: 8px;
                color: {COLORS.text_primary};
                font-size: 12px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS.border_focus};
            }}
        """

    @staticmethod
    def combo_box() -> str:
        """ComboBox styling."""
        return f"""
            QComboBox {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: 4px;
                padding: 6px 8px;
                color: {COLORS.text_primary};
                font-size: 12px;
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
        """SpinBox styling."""
        return f"""
            QSpinBox, QDoubleSpinBox {{
                background: {COLORS.bg_input};
                border: 1px solid {COLORS.border_input};
                border-radius: 4px;
                padding: 6px;
                color: {COLORS.text_primary};
                font-size: 12px;
                min-height: 28px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border-color: {COLORS.border_focus};
            }}
        """

    @staticmethod
    def checkbox() -> str:
        """Checkbox styling."""
        return f"""
            QCheckBox {{
                color: {COLORS.text_primary};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {COLORS.border_input};
                border-radius: 3px;
                background: {COLORS.bg_input};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: {COLORS.accent_primary};
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {COLORS.accent_primary};
                border-radius: 3px;
                background: {COLORS.accent_primary};
            }}
        """

    @staticmethod
    def group_box() -> str:
        """GroupBox styling."""
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12px;
                border: 1px solid {COLORS.border};
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                background: {COLORS.bg_button};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
                color: {COLORS.text_primary};
            }}
        """

    @staticmethod
    def button_primary() -> str:
        """Primary action button (32px height)."""
        return f"""
            QPushButton {{
                background: {COLORS.bg_button_primary};
                border: none;
                border-radius: 4px;
                padding: 0 20px;
                color: white;
                font-size: 12px;
                font-weight: 600;
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
        """Secondary action button (32px height)."""
        return f"""
            QPushButton {{
                background: {COLORS.bg_button};
                border: 1px solid {COLORS.border_light};
                border-radius: 4px;
                padding: 0 20px;
                color: {COLORS.text_primary};
                font-size: 12px;
                font-weight: 500;
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
        """Inline button for forms (28px height)."""
        return f"""
            QPushButton {{
                background: {COLORS.bg_button_primary};
                border: none;
                border-radius: 4px;
                padding: 0 12px;
                color: white;
                font-size: 11px;
                font-weight: 600;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background: {COLORS.accent_hover};
            }}
        """

    @staticmethod
    def button_danger() -> str:
        """Danger/destructive action button."""
        return f"""
            QPushButton {{
                background: {COLORS.bg_button_danger};
                border: none;
                border-radius: 4px;
                padding: 0 16px;
                color: white;
                font-size: 12px;
                font-weight: 600;
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
        """TabWidget styling."""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS.border};
                background-color: {COLORS.bg_panel};
            }}
            QTabBar::tab {{
                background-color: {COLORS.bg_button};
                color: {COLORS.text_primary};
                padding: 8px 16px;
                border: 1px solid {COLORS.border};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
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
        """ListWidget styling."""
        return f"""
            QListWidget {{
                background-color: {COLORS.bg_panel};
                border: 1px solid {COLORS.border};
                border-radius: 4px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px;
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
        """QDialogButtonBox styling."""
        return f"""
            QDialogButtonBox {{
                button-layout: 2;
            }}
            QDialogButtonBox QPushButton {{
                background: {COLORS.bg_button};
                border: 1px solid {COLORS.border_light};
                border-radius: 4px;
                padding: 0 16px;
                color: {COLORS.text_primary};
                font-size: 12px;
                font-weight: 500;
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
        """QMessageBox styling."""
        return f"""
            QMessageBox {{
                background: {COLORS.bg_panel};
            }}
            QMessageBox QLabel {{
                color: {COLORS.text_primary};
                font-size: 12px;
            }}
            QPushButton {{
                background: {COLORS.bg_button};
                border: 1px solid {COLORS.border_light};
                border-radius: 4px;
                padding: 0 16px;
                color: {COLORS.text_primary};
                font-size: 12px;
                font-weight: 500;
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
            font-size: 11px;
            padding: 4px 0;
        """

    @staticmethod
    def success_label() -> str:
        """Success message label styling."""
        return f"""
            color: {COLORS.text_success};
            font-size: 11px;
            padding: 4px 0;
        """

    @staticmethod
    def warning_label() -> str:
        """Warning message label styling."""
        return f"""
            color: {COLORS.text_warning};
            font-size: 11px;
            padding: 4px 0;
        """

    @staticmethod
    def info_label() -> str:
        """Info/muted label styling."""
        return f"""
            color: {COLORS.text_muted};
            font-size: 11px;
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
    Apply standardized styling to a dialog.

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

    # Apply full style
    dialog.setStyleSheet(DialogStyles.full_dialog_style())


def show_styled_message(
    parent: Optional[QWidget],
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
    parent: Optional[QWidget],
    title: str,
    text: str,
    info: str = "",
) -> None:
    """Show a styled warning message box."""
    show_styled_message(parent, title, text, info, QMessageBox.Icon.Warning)


def show_styled_error(
    parent: Optional[QWidget],
    title: str,
    text: str,
    info: str = "",
) -> None:
    """Show a styled error message box."""
    show_styled_message(parent, title, text, info, QMessageBox.Icon.Critical)


def show_styled_question(
    parent: Optional[QWidget],
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

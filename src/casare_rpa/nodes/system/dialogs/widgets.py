"""
Styled widget factories for runtime dialogs.

These factory functions create themed widgets for runtime dialogs,
ensuring visual consistency with the CasareRPA theme.
"""

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLineEdit, QTextEdit


def _create_styled_line_edit(
    placeholder: str = "",
    text: str = "",
    echo_mode: int | None = None,
) -> "QLineEdit":
    """
    Create a themed QLineEdit for runtime dialogs.

    Args:
        placeholder: Placeholder text
        text: Initial text value
        echo_mode: Optional echo mode (e.g., QLineEdit.Password)

    Returns:
        Styled QLineEdit widget
    """
    from PySide6.QtWidgets import QLineEdit

    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    line_edit.setText(text)
    if echo_mode is not None:
        line_edit.setEchoMode(echo_mode)

    # Apply CasareRPA dark theme styling
    line_edit.setStyleSheet("""
        QLineEdit {
            background: #18181b;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            color: #f4f4f5;
            padding: 6px 10px;
            font-size: 13px;
            selection-background-color: #4338ca;
        }
        QLineEdit:focus {
            border: 1px solid #6366f1;
            background: #27272a;
        }
        QLineEdit:hover {
            border: 1px solid #52525b;
        }
        QLineEdit::placeholder {
            color: #71717a;
        }
    """)
    return line_edit


def _create_styled_text_edit(
    placeholder: str = "",
    text: str = "",
) -> "QTextEdit":
    """
    Create a themed QTextEdit for runtime dialogs.

    Args:
        placeholder: Placeholder text
        text: Initial text value

    Returns:
        Styled QTextEdit widget
    """
    from PySide6.QtWidgets import QTextEdit

    text_edit = QTextEdit()
    text_edit.setPlaceholderText(placeholder)
    text_edit.setPlainText(text)

    # Apply CasareRPA dark theme styling
    text_edit.setStyleSheet("""
        QTextEdit {
            background: #18181b;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            color: #f4f4f5;
            padding: 8px;
            font-size: 13px;
            selection-background-color: #4338ca;
        }
        QTextEdit:focus {
            border: 1px solid #6366f1;
            background: #27272a;
        }
        QTextEdit:hover {
            border: 1px solid #52525b;
        }
    """)
    return text_edit

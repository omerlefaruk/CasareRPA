"""
Rich Text Editor for CasareRPA Expression Editors.

Provides a general-purpose text editor with:
- Variable insertion with {{ trigger
- Integration with VariableAutocomplete widget
- Expression highlighting for {{variable}} syntax
- Simple validation display (border color)
"""

import re
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import (
    QColor,
    QKeyEvent,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets.variable_autocomplete import (
    VariableAutocomplete,
)


class ExpressionHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for {{variable}} expressions in rich text.

    Highlights variable references in a distinct color to make them
    stand out from regular text content.
    """

    COLOR_VARIABLE = "#4EC9B0"  # Teal (VSCode Dark+ built-in color)

    def __init__(self, document: QTextDocument | None = None) -> None:
        """
        Initialize the expression highlighter.

        Args:
            document: QTextDocument to highlight
        """
        super().__init__(document)

        self._variable_format = QTextCharFormat()
        self._variable_format.setForeground(QColor(self.COLOR_VARIABLE))
        self._variable_format.setFontWeight(600)  # Semi-bold

    def highlightBlock(self, text: str) -> None:
        """
        Highlight {{variable}} expressions.

        Args:
            text: Text block to highlight
        """
        if not text:
            return

        # Match {{...}} patterns
        pattern = re.compile(r"\{\{[^}]+\}\}")
        for match in pattern.finditer(text):
            self.setFormat(
                match.start(),
                match.end() - match.start(),
                self._variable_format,
            )


class RichTextEditor(BaseExpressionEditor):
    """
    General-purpose rich text editor with variable support.

    Features:
    - QTextEdit base for rich editing
    - Variable insertion with {{ trigger
    - Integration with VariableAutocomplete widget
    - Expression highlighting for {{variable}} syntax
    - Simple validation display (border color change)

    Usage:
        editor = RichTextEditor()
        editor.set_value("Hello {{name}}, your order {{order_id}} is ready.")
        editor.set_node_context(node_id, graph)  # Enable upstream variables
    """

    # Validation statuses
    VALIDATION_VALID = "valid"
    VALIDATION_WARNING = "warning"
    VALIDATION_ERROR = "error"

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the rich text editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._editor_type = EditorType.RICH_TEXT

        self._current_node_id: str | None = None
        self._graph: Any | None = None
        self._validation_status: str = self.VALIDATION_VALID
        self._autocomplete: VariableAutocomplete | None = None
        self._autocomplete_trigger_pos: int = -1

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        logger.debug("RichTextEditor initialized")

    def _setup_ui(self) -> None:
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main text editor
        self._text_edit = QTextEdit()
        self._text_edit.setAcceptRichText(False)  # Plain text only
        self._text_edit.setPlaceholderText("Enter text... Use {{ to insert variables")
        self._text_edit.setTabStopDistance(40)

        # Expression highlighter
        self._highlighter = ExpressionHighlighter(self._text_edit.document())

        layout.addWidget(self._text_edit)

        # Autocomplete widget (created on demand)
        self._autocomplete = VariableAutocomplete()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._text_edit.textChanged.connect(self._on_text_changed)

        # Autocomplete signals
        self._autocomplete.variable_selected.connect(self._on_variable_selected)
        self._autocomplete.cancelled.connect(self._on_autocomplete_cancelled)

    def _apply_styles(self) -> None:
        """Apply THEME styling."""
        self._update_border_style()

    def _update_border_style(self) -> None:
        """Update border style based on validation status."""
        c = THEME

        border_colors = {
            self.VALIDATION_VALID: c.border,
            self.VALIDATION_WARNING: c.warning,
            self.VALIDATION_ERROR: c.error,
        }
        border_color = border_colors.get(self._validation_status, c.border)
        border_width = "2px" if self._validation_status != self.VALIDATION_VALID else "1px"

        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c.background};
                color: {c.text_primary};
                border: {border_width} solid {border_color};
                border-radius: 4px;
                padding: 8px;
                font-family: "Segoe UI", "SF Pro Text", sans-serif;
                font-size: 13px;
                selection-background-color: {c.selection};
            }}
            QTextEdit:focus {{
                border-color: {border_color if self._validation_status != self.VALIDATION_VALID else c.border_focus};
            }}
            QScrollBar:vertical {{
                background: {c.bg_elevated};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {c.bg_component};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {c.border_light};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

    # =========================================================================
    # BaseExpressionEditor Implementation
    # =========================================================================

    def get_value(self) -> str:
        """Get the current text content."""
        return self._text_edit.toPlainText()

    def set_value(self, value: str) -> None:
        """Set the text content."""
        self._text_edit.setPlainText(value)

    def insert_at_cursor(self, text: str) -> None:
        """Insert text at the current cursor position."""
        cursor = self._text_edit.textCursor()
        cursor.insertText(text)
        self._text_edit.setTextCursor(cursor)

    def get_cursor_position(self) -> int:
        """Get the current cursor position."""
        return self._text_edit.textCursor().position()

    def set_focus(self) -> None:
        """Set focus to the text editor."""
        self._text_edit.setFocus()

    # =========================================================================
    # Node Context
    # =========================================================================

    def set_node_context(
        self,
        node_id: str | None,
        graph: Any | None,
    ) -> None:
        """
        Set the current node context for upstream variable detection.

        Args:
            node_id: ID of the currently selected node
            graph: NodeGraphQt graph instance
        """
        self._current_node_id = node_id
        self._graph = graph
        if self._autocomplete:
            self._autocomplete.set_node_context(node_id, graph)

    # =========================================================================
    # Validation
    # =========================================================================

    def set_validation_status(
        self,
        status: str,
        message: str = "",
    ) -> None:
        """
        Set the validation status to update border color.

        Args:
            status: "valid", "warning", or "error"
            message: Optional validation message (sets tooltip)
        """
        if status not in (
            self.VALIDATION_VALID,
            self.VALIDATION_WARNING,
            self.VALIDATION_ERROR,
        ):
            logger.warning(f"Invalid validation status: {status}")
            status = self.VALIDATION_VALID

        self._validation_status = status
        self._update_border_style()

        if message:
            self._text_edit.setToolTip(message)
        else:
            self._text_edit.setToolTip("")

    def get_validation_status(self) -> str:
        """Get the current validation status."""
        return self._validation_status

    # =========================================================================
    # Autocomplete
    # =========================================================================

    @Slot()
    def _on_text_changed(self) -> None:
        """Handle text changes - check for {{ trigger."""
        self._on_content_changed()
        self._check_autocomplete_trigger()

    def _check_autocomplete_trigger(self) -> None:
        """Check if user typed {{ and show autocomplete."""
        text = self.get_value()
        cursor_pos = self.get_cursor_position()

        # Check if cursor is after {{
        if cursor_pos >= 2 and text[cursor_pos - 2 : cursor_pos] == "{{":
            self._show_autocomplete("")
            self._autocomplete_trigger_pos = cursor_pos

        # If autocomplete is visible, update filter
        elif self._autocomplete.isVisible() and self._autocomplete_trigger_pos >= 0:
            # Extract text after {{ up to cursor
            filter_text = text[self._autocomplete_trigger_pos : cursor_pos]
            # Close if user types }} or deletes back past {{
            if "}}" in filter_text or cursor_pos < self._autocomplete_trigger_pos:
                self._autocomplete.hide()
                self._autocomplete_trigger_pos = -1
            else:
                self._autocomplete.set_filter(filter_text)

    def _show_autocomplete(self, filter_text: str = "") -> None:
        """Show the autocomplete popup."""
        self._autocomplete.set_node_context(self._current_node_id, self._graph)
        self._autocomplete.set_filter(filter_text)

        if self._autocomplete.has_matches():
            cursor_rect = self._text_edit.cursorRect()
            self._autocomplete.show_at_cursor(self._text_edit, cursor_rect)

    @Slot(str)
    def _on_variable_selected(self, var_text: str) -> None:
        """
        Handle variable selection from autocomplete.

        Replaces the {{ trigger and any partial text with the full variable.

        Args:
            var_text: Full variable insertion text (e.g., "{{node_id.port}}")
        """
        if self._autocomplete_trigger_pos < 0:
            # No trigger position - just insert
            self.insert_at_cursor(var_text)
            return

        # Replace from {{ onwards
        cursor = self._text_edit.textCursor()
        current_pos = cursor.position()

        # Select from trigger position (after {{) back to {{ and to current position
        cursor.setPosition(self._autocomplete_trigger_pos - 2)  # Before {{
        cursor.setPosition(current_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(var_text)

        self._text_edit.setTextCursor(cursor)
        self._autocomplete_trigger_pos = -1

    @Slot()
    def _on_autocomplete_cancelled(self) -> None:
        """Handle autocomplete cancellation."""
        self._autocomplete_trigger_pos = -1

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key events for autocomplete navigation."""
        # If autocomplete is visible, forward navigation keys
        if self._autocomplete.isVisible():
            key = event.key()
            if key in (
                Qt.Key.Key_Down,
                Qt.Key.Key_Up,
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
                Qt.Key.Key_Tab,
                Qt.Key.Key_Escape,
            ):
                self._autocomplete.keyPressEvent(event)
                return

        super().keyPressEvent(event)

"""
Code Expression Editor for CasareRPA.

Provides a code editor with:
- Line number area
- Syntax highlighting (language-specific)
- Tab handling (4 spaces)
- Variable insertion at cursor

Based on Qt's Code Editor Example with VSCode Dark+ styling.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import QRect, QSize, Qt, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_detector import (
    CodeDetector,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
    JavaScriptHighlighter,
    get_javascript_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.json_highlighter import (
    JsonHighlighter,
    get_json_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
    MarkdownHighlighter,
    get_markdown_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
    PythonHighlighter,
    get_python_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.yaml_highlighter import (
    YamlHighlighter,
    get_yaml_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets.variable_autocomplete import (
    VariableAutocomplete,
)


class LineNumberArea(QWidget):
    """
    Line number area widget for the code editor.

    Displays line numbers alongside the editor content.
    Positioned to the left of the editor.
    """

    def __init__(self, editor: "CodePlainTextEdit") -> None:
        """
        Initialize line number area.

        Args:
            editor: The code editor this line number area belongs to
        """
        super().__init__(editor)
        self._editor = editor
        self.setStyleSheet(f"background-color: {THEME.bg_canvas};")

    def sizeHint(self) -> QSize:
        """Return the recommended size."""
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:
        """Paint the line numbers."""
        self._editor.line_number_area_paint_event(event)


class CodePlainTextEdit(QPlainTextEdit):
    """
    QPlainTextEdit with line numbers support.

    Features:
    - Line number area
    - Current line highlighting
    - Tab-to-spaces conversion
    - Fixed-width font
    - Variable autocomplete trigger
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the code text edit."""
        super().__init__(parent)

        # Setup font
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        # Setup tab width (4 spaces)
        tab_width = self.fontMetrics().horizontalAdvance(" ") * 4
        self.setTabStopDistance(tab_width)

        # Line number area
        self._line_number_area = LineNumberArea(self)

        # Autocomplete widget (set by parent editor)
        self._autocomplete: VariableAutocomplete | None = None

        # Connect signals
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        # Initial setup
        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Apply stylesheet
        self.setStyleSheet(get_python_editor_stylesheet())

        # Line wrap off for code
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

    def set_autocomplete(self, autocomplete: VariableAutocomplete) -> None:
        """Set the autocomplete widget reference."""
        self._autocomplete = autocomplete

    def line_number_area_width(self) -> int:
        """
        Calculate the width needed for the line number area.

        Returns:
            Width in pixels
        """
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        # Minimum 3 digits width
        digits = max(digits, 3)

        # Add padding
        space = 8 + self.fontMetrics().horizontalAdvance("9") * digits + 8
        return space

    def resizeEvent(self, event) -> None:
        """Handle resize to update line number area."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event) -> None:
        """
        Paint line numbers in the line number area.

        Args:
            event: Paint event
        """
        painter = QPainter(self._line_number_area)
        painter.fillRect(event.rect(), QColor(THEME.bg_canvas))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        # Line number color
        line_number_color = QColor(THEME.text_muted)
        current_line_color = QColor(THEME.text_primary)
        current_block = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)

                # Highlight current line number
                if block_number == current_block:
                    painter.setPen(current_line_color)
                else:
                    painter.setPen(line_number_color)

                painter.drawText(
                    0,
                    top,
                    self._line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    @Slot(int)
    def _update_line_number_area_width(self, _: int) -> None:
        """Update editor margins when line count changes."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    @Slot(QRect, int)
    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        """Update line number area on scroll or resize."""
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(
                0, rect.y(), self._line_number_area.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    @Slot()
    def _highlight_current_line(self) -> None:
        """Highlight the current line."""
        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(THEME.bg_component)
            line_color.setAlpha(60)

            selection.format.setBackground(line_color)
            selection.format.setProperty(selection.format.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events.

        Converts tabs to spaces and handles indentation.
        Forward navigation keys to autocomplete if visible.
        """
        # If autocomplete is visible, forward navigation keys
        if self._autocomplete and self._autocomplete.isVisible():
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

        # Tab -> 4 spaces
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            event.accept()
            return

        # Shift+Tab -> remove indentation
        if event.key() == Qt.Key.Key_Backtab or (
            event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
        ):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                4,
            )
            if cursor.selectedText() == "    ":
                cursor.removeSelectedText()
            event.accept()
            return

        super().keyPressEvent(event)


class CodeExpressionEditor(BaseExpressionEditor):
    """
    Code editor with syntax highlighting.

    Features:
    - QPlainTextEdit with line numbers
    - Language-specific syntax highlighting
    - Tab/indent handling
    - Variable insertion ({{var}} syntax)
    - Auto-detection of language

    Supported languages:
    - Python (default)
    - JavaScript
    - JSON
    - YAML
    - Markdown
    - CMD/Shell (basic)
    """

    def __init__(
        self,
        language: str = "python",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the code expression editor.

        Args:
            language: Programming language for syntax highlighting
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._initial_language = language.lower()
        self._language = self._initial_language
        self._highlighter = None
        self._current_node_id: str | None = None
        self._graph: Any | None = None
        self._autocomplete_trigger_pos: int = -1

        # Set editor type based on language
        language_to_type = {
            "python": EditorType.CODE_PYTHON,
            "javascript": EditorType.CODE_JAVASCRIPT,
            "cmd": EditorType.CODE_CMD,
            "json": EditorType.CODE_JSON,
            "yaml": EditorType.CODE_YAML,
            "markdown": EditorType.CODE_MARKDOWN,
            "auto": EditorType.AUTO,
        }
        self._editor_type = language_to_type.get(self._language, EditorType.CODE_PYTHON)

        self._setup_ui()
        logger.debug(f"CodeExpressionEditor initialized for language: {language}")

    def _setup_ui(self) -> None:
        """Setup the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create code editor
        self._editor = CodePlainTextEdit()
        layout.addWidget(self._editor)

        # Setup autocomplete
        self._autocomplete = VariableAutocomplete()
        self._editor.set_autocomplete(self._autocomplete)

        # Setup syntax highlighter based on language
        self._setup_highlighter()

        # Connect signals
        self._editor.textChanged.connect(self._on_text_changed)
        self._autocomplete.variable_selected.connect(self._on_variable_selected)
        self._autocomplete.cancelled.connect(self._on_autocomplete_cancelled)

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

    @Slot()
    def _on_text_changed(self) -> None:
        """Handle text changes."""
        # Auto-detection logic
        if self._initial_language == "auto":
            text = self.get_value()
            if text.strip():
                detected_type = CodeDetector.detect_language(text)

                # Map EditorType to string language
                type_to_lang = {
                    EditorType.CODE_PYTHON: "python",
                    EditorType.CODE_JAVASCRIPT: "javascript",
                    EditorType.CODE_JSON: "json",
                    EditorType.CODE_YAML: "yaml",
                    EditorType.CODE_MARKDOWN: "markdown",
                    EditorType.RICH_TEXT: "python",  # Default fallback
                }

                detected_lang = type_to_lang.get(detected_type, "python")

                # Only switch if confident and different
                if detected_lang != self._language:
                    self.set_language(detected_lang)

        # Emit signal for popup
        self.value_changed.emit(self.get_value())

        # Check for {{ trigger
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
            cursor_rect = self._editor.cursorRect()
            self._autocomplete.show_at_cursor(self._editor, cursor_rect)

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
        cursor = self._editor.textCursor()
        current_pos = cursor.position()

        # Select from trigger position (after {{) back to {{ and to current position
        cursor.setPosition(self._autocomplete_trigger_pos - 2)  # Before {{
        cursor.setPosition(current_pos, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(var_text)

        self._editor.setTextCursor(cursor)
        self._autocomplete_trigger_pos = -1

    @Slot()
    def _on_autocomplete_cancelled(self) -> None:
        """Handle autocomplete cancellation."""
        self._autocomplete_trigger_pos = -1

    def _setup_highlighter(self) -> None:
        """Setup syntax highlighter for the selected language."""
        # Clean up old highlighter
        if self._highlighter:
            self._highlighter.setDocument(None)
            self._highlighter = None

        document = self._editor.document()

        if self._language == "python":
            self._highlighter = PythonHighlighter(document)
            self._editor.setStyleSheet(get_python_editor_stylesheet())
        elif self._language == "javascript":
            self._highlighter = JavaScriptHighlighter(document)
            self._editor.setStyleSheet(get_javascript_editor_stylesheet())
        elif self._language == "json":
            self._highlighter = JsonHighlighter(document)
            self._editor.setStyleSheet(get_json_editor_stylesheet())
        elif self._language == "yaml":
            self._highlighter = YamlHighlighter(document)
            self._editor.setStyleSheet(get_yaml_editor_stylesheet())
        elif self._language == "markdown":
            self._highlighter = MarkdownHighlighter(document)
            self._editor.setStyleSheet(get_markdown_editor_stylesheet())
        elif self._language == "cmd":
            # CMD highlighter (basic)
            self._editor.setStyleSheet(get_python_editor_stylesheet())
        elif self._language == "auto":
            # Start with Python as default until detected
            self._highlighter = PythonHighlighter(document)
            self._editor.setStyleSheet(get_python_editor_stylesheet())
        else:
            # Default to Python
            self._highlighter = PythonHighlighter(document)
            self._editor.setStyleSheet(get_python_editor_stylesheet())

    def set_language(self, language: str) -> None:
        """
        Set the syntax highlighting language.

        Args:
            language: Language name (python, javascript, json, yaml, etc.)
        """
        language = language.lower()
        if language == self._language:
            return

        self._language = language
        self._setup_highlighter()
        logger.debug(f"Switched editor language to: {language}")

    def get_value(self) -> str:
        """
        Get the current editor content.

        Returns:
            Current text content
        """
        return self._editor.toPlainText()

    def set_value(self, value: str) -> None:
        """
        Set the editor content.

        Args:
            value: Text to set
        """
        self._editor.setPlainText(value)
        # Trigger detection on initial set if auto
        if self._initial_language == "auto":
            self._on_text_changed()

    def insert_at_cursor(self, text: str) -> None:
        """
        Insert text at the current cursor position.

        Args:
            text: Text to insert
        """
        cursor = self._editor.textCursor()
        cursor.insertText(text)
        self._editor.setTextCursor(cursor)

    def get_cursor_position(self) -> int:
        """
        Get the current cursor position.

        Returns:
            Character offset of cursor from start
        """
        return self._editor.textCursor().position()

    def set_focus(self) -> None:
        """Set focus to the editor."""
        self._editor.setFocus()


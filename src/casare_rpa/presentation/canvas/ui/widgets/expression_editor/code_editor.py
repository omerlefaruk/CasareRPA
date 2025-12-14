"""
Code Expression Editor for CasareRPA.

Provides a code editor with:
- Line number area
- Syntax highlighting (language-specific)
- Tab handling (4 spaces)
- Variable insertion at cursor

Based on Qt's Code Editor Example with VSCode Dark+ styling.
"""

from typing import Optional

from PySide6.QtCore import QRect, QSize, Qt, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QVBoxLayout, QWidget

from loguru import logger

from casare_rpa.presentation.canvas.ui.theme import THEME
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
    PythonHighlighter,
    get_python_editor_stylesheet,
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
        self.setStyleSheet(f"background-color: {THEME.bg_darkest};")

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
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
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
        painter.fillRect(event.rect(), QColor(THEME.bg_darkest))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
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
            line_color = QColor(THEME.bg_medium)
            line_color.setAlpha(60)

            selection.format.setBackground(line_color)
            selection.format.setProperty(
                selection.format.Property.FullWidthSelection, True
            )
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

    def keyPressEvent(self, event) -> None:
        """
        Handle key press events.

        Converts tabs to spaces and handles indentation.
        """
        # Tab -> 4 spaces
        if event.key() == Qt.Key.Key_Tab:
            cursor = self.textCursor()
            cursor.insertText("    ")
            event.accept()
            return

        # Shift+Tab -> remove indentation
        if event.key() == Qt.Key.Key_Backtab or (
            event.key() == Qt.Key.Key_Tab
            and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
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

    Supported languages:
    - Python (default)
    - JavaScript (planned)
    - CMD/Shell (planned)
    """

    def __init__(
        self,
        language: str = "python",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the code expression editor.

        Args:
            language: Programming language for syntax highlighting
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._language = language.lower()
        self._highlighter = None

        # Set editor type based on language
        language_to_type = {
            "python": EditorType.CODE_PYTHON,
            "javascript": EditorType.CODE_JAVASCRIPT,
            "cmd": EditorType.CODE_CMD,
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

        # Setup syntax highlighter based on language
        self._setup_highlighter()

        # Connect text changed signal
        self._editor.textChanged.connect(self._on_content_changed)

    def _setup_highlighter(self) -> None:
        """Setup syntax highlighter for the selected language."""
        if self._language == "python":
            self._highlighter = PythonHighlighter(self._editor.document())
        elif self._language == "javascript":
            # JavaScript highlighter (same as Python for now)
            self._highlighter = PythonHighlighter(self._editor.document())
        elif self._language == "cmd":
            # CMD highlighter (basic, no special highlighting yet)
            pass
        else:
            # Default to Python
            self._highlighter = PythonHighlighter(self._editor.document())

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

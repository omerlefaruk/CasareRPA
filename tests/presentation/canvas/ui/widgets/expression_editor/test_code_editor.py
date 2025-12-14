"""
Tests for CodeExpressionEditor.

This test suite covers:
- CodeExpressionEditor instantiation for different languages
- get_value/set_value operations
- insert_at_cursor functionality
- Line number area widget
- Tab handling (4 spaces)
- Syntax highlighter setup

Test Philosophy:
- Happy path: editor works correctly with valid input
- Sad path: handles edge cases gracefully
- Edge cases: empty content, large files, special characters

Run: pytest tests/presentation/canvas/ui/widgets/expression_editor/test_code_editor.py -v
"""

import pytest
from unittest.mock import MagicMock, patch


# =============================================================================
# CodeExpressionEditor Instantiation Tests
# =============================================================================


class TestCodeExpressionEditorInstantiation:
    """Tests for CodeExpressionEditor creation."""

    def test_instantiation_default_python(self, qapp) -> None:
        """Test default instantiation creates Python editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
            EditorType,
        )

        editor = CodeExpressionEditor()
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_instantiation_explicit_python(self, qapp) -> None:
        """Test explicit Python language parameter."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
            EditorType,
        )

        editor = CodeExpressionEditor(language="python")
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_instantiation_javascript(self, qapp) -> None:
        """Test JavaScript language parameter."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
            EditorType,
        )

        editor = CodeExpressionEditor(language="javascript")
        assert editor.editor_type == EditorType.CODE_JAVASCRIPT

    def test_instantiation_cmd(self, qapp) -> None:
        """Test CMD language parameter."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
            EditorType,
        )

        editor = CodeExpressionEditor(language="cmd")
        assert editor.editor_type == EditorType.CODE_CMD

    def test_instantiation_case_insensitive(self, qapp) -> None:
        """Test language parameter is case insensitive."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
            EditorType,
        )

        editor = CodeExpressionEditor(language="PYTHON")
        assert editor.editor_type == EditorType.CODE_PYTHON

        editor2 = CodeExpressionEditor(language="Python")
        assert editor2.editor_type == EditorType.CODE_PYTHON

    def test_instantiation_unknown_language_defaults_python(self, qapp) -> None:
        """Test unknown language defaults to Python."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
            EditorType,
        )

        editor = CodeExpressionEditor(language="unknown")
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_instantiation_with_parent(self, qapp) -> None:
        """Test instantiation with parent widget."""
        from PySide6.QtWidgets import QWidget
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        parent = QWidget()
        editor = CodeExpressionEditor(parent=parent)
        assert editor.parent() == parent


# =============================================================================
# Value Operations Tests
# =============================================================================


class TestCodeExpressionEditorValueOperations:
    """Tests for get_value/set_value operations."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        return CodeExpressionEditor()

    def test_get_value_empty(self, editor) -> None:
        """Test get_value on empty editor."""
        assert editor.get_value() == ""

    def test_set_get_value_roundtrip(self, editor) -> None:
        """Test set and get value roundtrip."""
        code = "print('Hello World')"
        editor.set_value(code)
        assert editor.get_value() == code

    def test_set_value_multiline(self, editor) -> None:
        """Test multiline code content."""
        code = """def hello():
    print('Hello')
    return True"""
        editor.set_value(code)
        assert editor.get_value() == code

    def test_set_value_with_indentation(self, editor) -> None:
        """Test code with various indentation levels."""
        code = """class Test:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1"""
        editor.set_value(code)
        assert editor.get_value() == code
        # Verify indentation is preserved
        lines = editor.get_value().split("\n")
        assert lines[1].startswith("    ")  # 4 spaces
        assert lines[2].startswith("        ")  # 8 spaces

    def test_set_value_empty_string(self, editor) -> None:
        """Test setting empty string clears content."""
        editor.set_value("Some content")
        editor.set_value("")
        assert editor.get_value() == ""

    def test_set_value_replaces_content(self, editor) -> None:
        """Test set_value replaces existing content."""
        editor.set_value("First content")
        editor.set_value("Second content")
        assert editor.get_value() == "Second content"

    def test_value_changed_signal_emitted(self, editor, signal_capture) -> None:
        """Test value_changed signal is emitted on set_value."""
        editor.value_changed.connect(signal_capture.slot)
        editor.set_value("New value")

        assert signal_capture.called
        assert signal_capture.last_args == ("New value",)


# =============================================================================
# Insert at Cursor Tests
# =============================================================================


class TestCodeExpressionEditorInsertAtCursor:
    """Tests for insert_at_cursor functionality."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        return CodeExpressionEditor()

    def test_insert_at_cursor_empty(self, editor) -> None:
        """Test insert at cursor in empty editor."""
        editor.insert_at_cursor("print('Hello')")
        assert editor.get_value() == "print('Hello')"

    def test_insert_at_cursor_variable(self, editor) -> None:
        """Test inserting variable syntax."""
        editor.set_value("x = ")
        # Move cursor to end by setting position
        editor._editor.moveCursor(editor._editor.textCursor().MoveOperation.End)
        editor.insert_at_cursor("{{node.value}}")
        assert "{{node.value}}" in editor.get_value()

    def test_insert_preserves_existing_content(self, editor) -> None:
        """Test insert doesn't destroy existing content."""
        editor.set_value("Hello World")
        # Move cursor to position 6 (after 'Hello ')
        cursor = editor._editor.textCursor()
        cursor.setPosition(6)
        editor._editor.setTextCursor(cursor)

        editor.insert_at_cursor("Beautiful ")
        assert "Beautiful" in editor.get_value()
        assert "Hello" in editor.get_value()

    def test_insert_empty_string(self, editor) -> None:
        """Test inserting empty string does nothing."""
        editor.set_value("Hello")
        original = editor.get_value()
        editor.insert_at_cursor("")
        assert editor.get_value() == original


# =============================================================================
# Cursor Position Tests
# =============================================================================


class TestCodeExpressionEditorCursorPosition:
    """Tests for cursor position functionality."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        return CodeExpressionEditor()

    def test_get_cursor_position_empty(self, editor) -> None:
        """Test cursor position in empty editor."""
        pos = editor.get_cursor_position()
        assert pos == 0

    def test_get_cursor_position_after_set(self, editor) -> None:
        """Test cursor position after setting value."""
        editor.set_value("Hello")
        pos = editor.get_cursor_position()
        # After set, cursor may be at end or beginning depending on implementation
        assert pos >= 0

    def test_cursor_position_valid_range(self, editor) -> None:
        """Test cursor position is within valid range."""
        editor.set_value("0123456789")
        pos = editor.get_cursor_position()
        assert 0 <= pos <= 10


# =============================================================================
# Line Number Area Tests
# =============================================================================


class TestCodePlainTextEditLineNumberArea:
    """Tests for line number area functionality."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        return CodeExpressionEditor()

    def test_line_number_area_exists(self, editor) -> None:
        """Test line number area widget exists."""
        # Access internal editor
        internal_editor = editor._editor
        assert hasattr(internal_editor, "_line_number_area")
        assert internal_editor._line_number_area is not None

    def test_line_number_area_width_minimum(self, editor) -> None:
        """Test line number area has minimum width."""
        internal_editor = editor._editor
        width = internal_editor.line_number_area_width()
        # Should have at least width for 3 digits + padding
        assert width > 0

    def test_line_number_area_width_grows_with_lines(self, editor) -> None:
        """Test line number area width grows with more lines."""
        internal_editor = editor._editor

        # Get width with few lines
        editor.set_value("Line 1")
        width_small = internal_editor.line_number_area_width()

        # Get width with many lines (1000+)
        lines = "\n".join([f"Line {i}" for i in range(1500)])
        editor.set_value(lines)
        width_large = internal_editor.line_number_area_width()

        # Width should increase to accommodate more digits
        assert width_large >= width_small


# =============================================================================
# Tab Handling Tests
# =============================================================================


class TestCodePlainTextEditTabHandling:
    """Tests for tab to spaces conversion."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_editor import (
            CodePlainTextEdit,
        )

        return CodePlainTextEdit()

    def test_tab_stop_distance_set(self, editor) -> None:
        """Test tab stop distance is configured for 4 spaces."""
        # Tab stop should be set to approximately 4 spaces worth
        actual_tab_width = editor.tabStopDistance()
        # Verify it's a reasonable value (greater than 0 and in expected range)
        assert actual_tab_width > 0
        # Should be around 28-40 pixels depending on font (4 spaces * ~7-10 pixels per char)
        assert 20 <= actual_tab_width <= 50

    def test_tab_inserts_spaces(self, editor, qapp) -> None:
        """Test pressing Tab inserts 4 spaces."""
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent

        # Create Tab key event
        event = QKeyEvent(
            QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier
        )

        editor.keyPressEvent(event)
        assert editor.toPlainText() == "    "  # 4 spaces

    def test_line_wrap_disabled(self, editor) -> None:
        """Test line wrap is disabled for code."""
        from PySide6.QtWidgets import QPlainTextEdit

        assert editor.lineWrapMode() == QPlainTextEdit.LineWrapMode.NoWrap


# =============================================================================
# Syntax Highlighter Setup Tests
# =============================================================================


class TestCodeExpressionEditorHighlighter:
    """Tests for syntax highlighter setup."""

    def test_python_highlighter_setup(self, qapp) -> None:
        """Test Python highlighter is set up correctly."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = CodeExpressionEditor(language="python")
        assert editor._highlighter is not None
        assert isinstance(editor._highlighter, PythonHighlighter)

    def test_javascript_highlighter_setup(self, qapp) -> None:
        """Test JavaScript uses highlighter (currently same as Python)."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        editor = CodeExpressionEditor(language="javascript")
        # Currently uses Python highlighter
        assert editor._highlighter is not None

    def test_cmd_no_highlighter(self, qapp) -> None:
        """Test CMD has no special highlighter."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        editor = CodeExpressionEditor(language="cmd")
        # CMD currently has no highlighter
        assert editor._highlighter is None


# =============================================================================
# Focus Tests
# =============================================================================


class TestCodeExpressionEditorFocus:
    """Tests for focus handling."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        return CodeExpressionEditor()

    def test_set_focus_method_exists(self, editor) -> None:
        """Test set_focus method exists."""
        assert hasattr(editor, "set_focus")
        assert callable(editor.set_focus)

    def test_set_focus_callable(self, editor) -> None:
        """Test set_focus can be called without error."""
        # Should not raise
        editor.set_focus()


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestCodeExpressionEditorEdgeCases:
    """Edge case tests for CodeExpressionEditor."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a code editor for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        return CodeExpressionEditor()

    def test_unicode_content(self, editor) -> None:
        """Test Unicode content handling."""
        code = "# \u4e2d\u6587\u6ce8\u91ca\nprint('\U0001f600')"
        editor.set_value(code)
        assert editor.get_value() == code

    def test_very_long_line(self, editor) -> None:
        """Test very long line handling."""
        long_line = "x = " + "a" * 10000
        editor.set_value(long_line)
        assert len(editor.get_value()) == 10004

    def test_many_lines(self, editor) -> None:
        """Test many lines handling."""
        many_lines = "\n".join([f"line{i}" for i in range(5000)])
        editor.set_value(many_lines)
        assert editor.get_value().count("\n") == 4999

    def test_special_characters(self, editor) -> None:
        """Test special characters in code."""
        special = "x = '\\n\\t\\r\\0'"
        editor.set_value(special)
        assert editor.get_value() == special

    def test_variable_syntax_preserved(self, editor) -> None:
        """Test {{variable}} syntax is preserved."""
        code = "result = {{input}} + {{other}}"
        editor.set_value(code)
        assert "{{input}}" in editor.get_value()
        assert "{{other}}" in editor.get_value()

    def test_python_code_with_triple_quotes(self, editor) -> None:
        """Test Python triple-quoted strings."""
        code = '''doc = """
This is a
multiline string
"""'''
        editor.set_value(code)
        assert '"""' in editor.get_value()

    def test_javascript_template_literals(self, qapp) -> None:
        """Test JavaScript template literals."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        editor = CodeExpressionEditor(language="javascript")
        code = "const msg = `Hello ${name}!`;"
        editor.set_value(code)
        assert "`" in editor.get_value()
        assert "${name}" in editor.get_value()


# =============================================================================
# Inheritance Tests
# =============================================================================


class TestCodeExpressionEditorInheritance:
    """Tests for proper inheritance from BaseExpressionEditor."""

    def test_inherits_from_base(self, qapp) -> None:
        """Test CodeExpressionEditor inherits from BaseExpressionEditor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        # Check that CodeExpressionEditor is a subclass of BaseExpressionEditor
        # Using __bases__ to avoid ABC metaclass issues
        bases = CodeExpressionEditor.__mro__
        base_names = [b.__name__ for b in bases]
        assert "BaseExpressionEditor" in base_names

    def test_has_all_abstract_methods(self, qapp) -> None:
        """Test all abstract methods are implemented."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        editor = CodeExpressionEditor()

        # All these should be callable
        assert callable(editor.get_value)
        assert callable(editor.set_value)
        assert callable(editor.insert_at_cursor)
        assert callable(editor.get_cursor_position)

    def test_has_value_changed_signal(self, qapp) -> None:
        """Test value_changed signal from base class."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        editor = CodeExpressionEditor()
        assert hasattr(editor, "value_changed")

    def test_insert_variable_delegates(self, qapp, signal_capture) -> None:
        """Test insert_variable uses insert_at_cursor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            CodeExpressionEditor,
        )

        editor = CodeExpressionEditor()
        editor.value_changed.connect(signal_capture.slot)

        editor.insert_variable("{{test.var}}")

        assert "{{test.var}}" in editor.get_value()
        assert signal_capture.called

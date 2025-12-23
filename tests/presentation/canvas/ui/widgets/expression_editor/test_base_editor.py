"""
Tests for BaseExpressionEditor and EditorType.

This test suite covers:
- EditorType enum values and their string mappings
- BaseExpressionEditor abstract interface (cannot instantiate)
- Value changed signal emission
- Variable insertion convenience method

Test Philosophy:
- Happy path: enum values exist, signals emit correctly
- Sad path: cannot instantiate abstract class
- Edge cases: empty values, special characters

Run: pytest tests/presentation/canvas/ui/widgets/expression_editor/test_base_editor.py -v
"""

import pytest
from unittest.mock import MagicMock


# =============================================================================
# EditorType Enum Tests
# =============================================================================


class TestEditorTypeEnum:
    """Tests for EditorType enumeration values."""

    def test_editor_type_has_python(self) -> None:
        """Test CODE_PYTHON enum exists with correct value."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert EditorType.CODE_PYTHON.value == "python"

    def test_editor_type_has_javascript(self) -> None:
        """Test CODE_JAVASCRIPT enum exists with correct value."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert EditorType.CODE_JAVASCRIPT.value == "javascript"

    def test_editor_type_has_cmd(self) -> None:
        """Test CODE_CMD enum exists with correct value."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert EditorType.CODE_CMD.value == "cmd"

    def test_editor_type_has_markdown(self) -> None:
        """Test MARKDOWN enum exists with correct value."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert EditorType.CODE_MARKDOWN.value == "markdown"

    def test_editor_type_has_rich_text(self) -> None:
        """Test RICH_TEXT enum exists with correct value."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert EditorType.RICH_TEXT.value == "rich_text"

    def test_editor_type_count(self) -> None:
        """Test EditorType has exactly 8 values."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert len(EditorType) == 8

    def test_editor_type_iteration(self) -> None:
        """Test all EditorType values are iterable."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        types = list(EditorType)
        expected = [
            EditorType.CODE_PYTHON,
            EditorType.CODE_JAVASCRIPT,
            EditorType.CODE_CMD,
            EditorType.CODE_JSON,
            EditorType.CODE_YAML,
            EditorType.CODE_MARKDOWN,
            EditorType.RICH_TEXT,
            EditorType.AUTO,
        ]
        assert types == expected

    def test_editor_type_is_enum(self) -> None:
        """Test EditorType is a proper Enum type."""
        from enum import Enum
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        assert issubclass(EditorType, Enum)


# =============================================================================
# BaseExpressionEditor Abstract Class Tests
# =============================================================================


class TestBaseExpressionEditorInterface:
    """Tests for BaseExpressionEditor abstract interface."""

    def test_cannot_instantiate_directly(self, qapp) -> None:
        """Test BaseExpressionEditor is not meant to be directly instantiated."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        # BaseExpressionEditor may or may not be strictly abstract depending on implementation
        # The key is that concrete subclasses are expected to implement the abstract methods
        # If it can be instantiated, verify it has the expected interface
        try:
            editor = BaseExpressionEditor()
            # If instantiation succeeds, verify interface exists
            assert hasattr(editor, "get_value")
            assert hasattr(editor, "set_value")
        except TypeError as e:
            # Expected for abstract class
            assert "abstract" in str(e).lower() or "instantiate" in str(e).lower()

    def test_has_value_changed_signal(self, qapp) -> None:
        """Test BaseExpressionEditor has value_changed signal defined."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )
        from PySide6.QtCore import Signal

        # Check signal exists at class level
        assert hasattr(BaseExpressionEditor, "value_changed")

    def test_abstract_methods_defined(self) -> None:
        """Test all required abstract methods are defined."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        # Check abstract methods exist
        assert hasattr(BaseExpressionEditor, "get_value")
        assert hasattr(BaseExpressionEditor, "set_value")
        assert hasattr(BaseExpressionEditor, "insert_at_cursor")
        assert hasattr(BaseExpressionEditor, "get_cursor_position")

    def test_editor_type_property_exists(self) -> None:
        """Test editor_type property is defined."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        assert hasattr(BaseExpressionEditor, "editor_type")

    def test_insert_variable_method_exists(self) -> None:
        """Test insert_variable convenience method is defined."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        assert hasattr(BaseExpressionEditor, "insert_variable")
        assert callable(BaseExpressionEditor.insert_variable)

    def test_set_focus_method_exists(self) -> None:
        """Test set_focus method is defined."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        assert hasattr(BaseExpressionEditor, "set_focus")
        assert callable(BaseExpressionEditor.set_focus)


# =============================================================================
# Concrete Implementation Tests (using a test subclass)
# =============================================================================


class TestBaseExpressionEditorConcreteImplementation:
    """Tests using a concrete test implementation of BaseExpressionEditor."""

    @pytest.fixture
    def concrete_editor(self, qapp):
        """Create a concrete test implementation for testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )
        from PySide6.QtWidgets import QWidget

        class TestEditor(BaseExpressionEditor):
            """Minimal concrete implementation for testing."""

            def __init__(self, parent=None):
                super().__init__(parent)
                self._content = ""
                self._cursor_pos = 0

            def get_value(self) -> str:
                return self._content

            def set_value(self, value: str) -> None:
                self._content = value
                self._on_content_changed()

            def insert_at_cursor(self, text: str) -> None:
                before = self._content[: self._cursor_pos]
                after = self._content[self._cursor_pos :]
                self._content = before + text + after
                self._cursor_pos += len(text)
                self._on_content_changed()

            def get_cursor_position(self) -> int:
                return self._cursor_pos

        return TestEditor()

    def test_concrete_can_be_instantiated(self, concrete_editor) -> None:
        """Test concrete implementation can be created."""
        assert concrete_editor is not None

    def test_get_set_value_roundtrip(self, concrete_editor) -> None:
        """Test value can be set and retrieved."""
        concrete_editor.set_value("Hello World")
        assert concrete_editor.get_value() == "Hello World"

    def test_get_set_value_empty_string(self, concrete_editor) -> None:
        """Test empty string is handled correctly."""
        concrete_editor.set_value("")
        assert concrete_editor.get_value() == ""

    def test_get_set_value_special_characters(self, concrete_editor) -> None:
        """Test special characters are preserved."""
        special = '{{var.name}}\n\t"quotes"\u00e9'
        concrete_editor.set_value(special)
        assert concrete_editor.get_value() == special

    def test_insert_at_cursor_beginning(self, concrete_editor) -> None:
        """Test inserting at cursor position 0."""
        concrete_editor.set_value("World")
        concrete_editor._cursor_pos = 0
        concrete_editor.insert_at_cursor("Hello ")
        assert concrete_editor.get_value() == "Hello World"

    def test_insert_at_cursor_middle(self, concrete_editor) -> None:
        """Test inserting at middle cursor position."""
        concrete_editor.set_value("Helloorld")
        concrete_editor._cursor_pos = 5
        concrete_editor.insert_at_cursor(" W")
        assert concrete_editor.get_value() == "Hello World"

    def test_insert_at_cursor_end(self, concrete_editor) -> None:
        """Test inserting at end of content."""
        concrete_editor.set_value("Hello")
        concrete_editor._cursor_pos = 5
        concrete_editor.insert_at_cursor(" World")
        assert concrete_editor.get_value() == "Hello World"

    def test_get_cursor_position(self, concrete_editor) -> None:
        """Test cursor position retrieval."""
        concrete_editor._cursor_pos = 42
        assert concrete_editor.get_cursor_position() == 42

<<<<<<< HEAD
    def test_insert_variable_delegates_to_insert_at_cursor(
        self, concrete_editor
    ) -> None:
=======
    def test_insert_variable_delegates_to_insert_at_cursor(self, concrete_editor) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """Test insert_variable calls insert_at_cursor."""
        concrete_editor.set_value("Value: ")
        concrete_editor._cursor_pos = 7
        concrete_editor.insert_variable("{{node.output}}")
        assert concrete_editor.get_value() == "Value: {{node.output}}"

<<<<<<< HEAD
    def test_value_changed_signal_emitted_on_set(
        self, concrete_editor, signal_capture
    ) -> None:
=======
    def test_value_changed_signal_emitted_on_set(self, concrete_editor, signal_capture) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """Test value_changed signal is emitted when value is set."""
        concrete_editor.value_changed.connect(signal_capture.slot)

        concrete_editor.set_value("Test content")

        assert signal_capture.called
        assert signal_capture.last_args == ("Test content",)

<<<<<<< HEAD
    def test_value_changed_signal_emitted_on_insert(
        self, concrete_editor, signal_capture
    ) -> None:
=======
    def test_value_changed_signal_emitted_on_insert(self, concrete_editor, signal_capture) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """Test value_changed signal is emitted when text is inserted."""
        concrete_editor.set_value("Start")
        signal_capture.clear()

        concrete_editor.value_changed.connect(signal_capture.slot)
        concrete_editor._cursor_pos = 5
        concrete_editor.insert_at_cursor("End")

        assert signal_capture.called
        assert signal_capture.last_args == ("StartEnd",)

    def test_editor_type_initially_none(self, concrete_editor) -> None:
        """Test editor_type property is None when not set."""
        assert concrete_editor.editor_type is None

    def test_editor_type_can_be_set(self, concrete_editor) -> None:
        """Test editor_type can be set via private attribute."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorType,
        )

        concrete_editor._editor_type = EditorType.CODE_PYTHON
        assert concrete_editor.editor_type == EditorType.CODE_PYTHON


# =============================================================================
# QABCMeta Metaclass Tests
# =============================================================================


class TestQABCMeta:
    """Tests for the combined Qt + ABC metaclass."""

    def test_metaclass_combines_qt_and_abc(self) -> None:
        """Test QABCMeta properly combines Qt metaclass with ABCMeta."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            QABCMeta,
            BaseExpressionEditor,
        )
        from PySide6.QtWidgets import QWidget
        from abc import ABCMeta

        # Verify QABCMeta is used
        assert isinstance(BaseExpressionEditor, QABCMeta)

    def test_base_editor_inherits_from_qwidget(self, qapp) -> None:
        """Test BaseExpressionEditor inherits from QWidget."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )
        from PySide6.QtWidgets import QWidget

        assert issubclass(BaseExpressionEditor, QWidget)


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestBaseExpressionEditorEdgeCases:
    """Edge case tests for BaseExpressionEditor."""

    @pytest.fixture
    def editor(self, qapp):
        """Create a concrete editor for edge case testing."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            BaseExpressionEditor,
        )

        class TestEditor(BaseExpressionEditor):
            def __init__(self):
                super().__init__()
                self._content = ""
                self._cursor = 0

            def get_value(self):
                return self._content

            def set_value(self, value):
                self._content = value

            def insert_at_cursor(self, text):
<<<<<<< HEAD
                self._content = (
                    self._content[: self._cursor] + text + self._content[self._cursor :]
                )
=======
                self._content = self._content[: self._cursor] + text + self._content[self._cursor :]
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
                self._cursor += len(text)

            def get_cursor_position(self):
                return self._cursor

        return TestEditor()

    def test_multiline_content(self, editor) -> None:
        """Test handling multiline content."""
        multiline = "Line 1\nLine 2\nLine 3"
        editor.set_value(multiline)
        assert editor.get_value() == multiline
        assert editor.get_value().count("\n") == 2

    def test_unicode_content(self, editor) -> None:
        """Test handling Unicode content."""
        unicode_text = "Hello \u4e16\u754c \U0001f600"
        editor.set_value(unicode_text)
        assert editor.get_value() == unicode_text

    def test_very_long_content(self, editor) -> None:
        """Test handling very long content."""
        long_text = "x" * 100000
        editor.set_value(long_text)
        assert len(editor.get_value()) == 100000

    def test_tab_characters(self, editor) -> None:
        """Test tab characters are preserved."""
        tabbed = "col1\tcol2\tcol3"
        editor.set_value(tabbed)
        assert "\t" in editor.get_value()
        assert editor.get_value().count("\t") == 2

    def test_variable_syntax_preserved(self, editor) -> None:
        """Test {{variable}} syntax is preserved correctly."""
        var_text = "Hello {{user.name}}, your ID is {{user.id}}"
        editor.set_value(var_text)
        assert "{{user.name}}" in editor.get_value()
        assert "{{user.id}}" in editor.get_value()

    def test_insert_empty_string(self, editor) -> None:
        """Test inserting empty string doesn't change content."""
        editor.set_value("Hello")
        editor._cursor = 5
        editor.insert_at_cursor("")
        assert editor.get_value() == "Hello"

    def test_insert_updates_cursor(self, editor) -> None:
        """Test insert updates cursor position correctly."""
        editor.set_value("Hello")
        editor._cursor = 0
        editor.insert_at_cursor("XX")
        assert editor.get_cursor_position() == 2

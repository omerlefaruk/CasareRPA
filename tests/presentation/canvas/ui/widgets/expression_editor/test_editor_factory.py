"""
Tests for EditorFactory.

This test suite covers:
- EditorFactory.create() returns correct editor types
- All EditorType values produce valid editors
- EditorFactory.create_for_property_type() property type mapping
- Node-specific editor overrides

Test Philosophy:
- Happy path: all editor types create correct instances
- Sad path: unknown editor type raises ValueError
- Edge cases: property type case sensitivity, missing overrides

Run: pytest tests/presentation/canvas/ui/widgets/expression_editor/test_editor_factory.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


# =============================================================================
# EditorFactory.create() Tests
# =============================================================================


class TestEditorFactoryCreate:
    """Tests for EditorFactory.create() method."""

    def test_create_python_editor(self, qapp) -> None:
        """Test creating CODE_PYTHON editor returns CodeExpressionEditor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
            CodeExpressionEditor,
        )

        editor = EditorFactory.create(EditorType.CODE_PYTHON)

        assert isinstance(editor, CodeExpressionEditor)
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_create_javascript_editor(self, qapp) -> None:
        """Test creating CODE_JAVASCRIPT editor returns CodeExpressionEditor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
            CodeExpressionEditor,
        )

        editor = EditorFactory.create(EditorType.CODE_JAVASCRIPT)

        assert isinstance(editor, CodeExpressionEditor)
        assert editor.editor_type == EditorType.CODE_JAVASCRIPT

    def test_create_cmd_editor(self, qapp) -> None:
        """Test creating CODE_CMD editor returns CodeExpressionEditor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
            CodeExpressionEditor,
        )

        editor = EditorFactory.create(EditorType.CODE_CMD)

        assert isinstance(editor, CodeExpressionEditor)
        assert editor.editor_type == EditorType.CODE_CMD

    def test_create_markdown_editor(self, qapp) -> None:
        """Test creating MARKDOWN editor returns MarkdownEditor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
            MarkdownEditor,
        )

        editor = EditorFactory.create(EditorType.CODE_MARKDOWN)

        assert isinstance(editor, MarkdownEditor)
        assert editor.editor_type == EditorType.CODE_MARKDOWN

    def test_create_rich_text_editor(self, qapp) -> None:
        """Test creating RICH_TEXT editor returns RichTextEditor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
            RichTextEditor,
        )

        editor = EditorFactory.create(EditorType.RICH_TEXT)

        assert isinstance(editor, RichTextEditor)
        assert editor.editor_type == EditorType.RICH_TEXT

    def test_create_all_editor_types(self, qapp) -> None:
        """Test all EditorType values create valid editors."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        for editor_type in EditorType:
            editor = EditorFactory.create(editor_type)
            # Verify editor has expected interface
            assert hasattr(editor, "get_value")
            assert hasattr(editor, "set_value")
            assert hasattr(editor, "editor_type")
            assert editor.editor_type == editor_type

    def test_create_with_parent(self, qapp) -> None:
        """Test creating editor with parent widget."""
        from PySide6.QtWidgets import QWidget
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        parent = QWidget()
        editor = EditorFactory.create(EditorType.CODE_PYTHON, parent=parent)

        assert editor.parent() == parent


# =============================================================================
# EditorFactory Error Handling Tests
# =============================================================================


class TestEditorFactoryErrorHandling:
    """Tests for EditorFactory error handling."""

    def test_create_invalid_type_raises_value_error(self, qapp) -> None:
        """Test that invalid editor type raises ValueError."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.editor_factory import (
            EditorFactory,
        )

        # Create a mock "invalid" type
        class FakeType:
            pass

        with pytest.raises(ValueError) as exc_info:
            EditorFactory.create(FakeType())

        assert "Unknown editor type" in str(exc_info.value)

    def test_create_none_type_raises_error(self, qapp) -> None:
        """Test that None editor type raises appropriate error."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.editor_factory import (
            EditorFactory,
        )

        with pytest.raises((ValueError, AttributeError)):
            EditorFactory.create(None)


# =============================================================================
# EditorFactory.create_for_property_type() Tests
# =============================================================================


class TestEditorFactoryCreateForPropertyType:
    """Tests for property type to editor type mapping."""

    def test_code_property_creates_python_editor(self, qapp) -> None:
        """Test CODE property type creates Python editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type("CODE")
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_text_property_creates_rich_text_editor(self, qapp) -> None:
        """Test TEXT property type creates AUTO editor (new default)."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type("TEXT")
        assert editor.editor_type == EditorType.AUTO

    def test_string_property_creates_rich_text_editor(self, qapp) -> None:
        """Test STRING property type creates AUTO editor (new default)."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type("STRING")
        assert editor.editor_type == EditorType.AUTO

    def test_json_property_creates_javascript_editor(self, qapp) -> None:
        """Test JSON property type creates JSON editor (new default)."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type("JSON")
        assert editor.editor_type == EditorType.CODE_JSON

    def test_script_property_creates_python_editor(self, qapp) -> None:
        """Test SCRIPT property type creates Python editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type("SCRIPT")
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_property_type_case_insensitive(self, qapp) -> None:
        """Test property type mapping is case insensitive."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        # Test lowercase
        editor_lower = EditorFactory.create_for_property_type("code")
        assert editor_lower.editor_type == EditorType.CODE_PYTHON

        # Test mixed case
        editor_mixed = EditorFactory.create_for_property_type("Code")
        assert editor_mixed.editor_type == EditorType.CODE_PYTHON

    def test_unknown_property_type_defaults_to_rich_text(self, qapp) -> None:
        """Test unknown property type defaults to RICH_TEXT."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type("UNKNOWN_TYPE")
        assert editor.editor_type == EditorType.RICH_TEXT


# =============================================================================
# Node-Specific Override Tests
# =============================================================================


class TestEditorFactoryNodeOverrides:
    """Tests for node-specific editor overrides."""

    def test_email_body_uses_markdown(self, qapp) -> None:
        """Test EmailSendNode.body property uses Markdown editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type(
            property_type="TEXT",
            node_type="EmailSendNode",
            property_name="body",
        )
        assert editor.editor_type == EditorType.CODE_MARKDOWN

    def test_browser_evaluate_uses_javascript(self, qapp) -> None:
        """Test BrowserEvaluateNode.script uses JavaScript editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type(
            property_type="CODE",
            node_type="BrowserEvaluateNode",
            property_name="script",
        )
        assert editor.editor_type == EditorType.CODE_JAVASCRIPT

    def test_run_python_uses_python(self, qapp) -> None:
        """Test RunPythonNode.code uses Python editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type(
            property_type="CODE",
            node_type="RunPythonNode",
            property_name="code",
        )
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_command_node_uses_cmd(self, qapp) -> None:
        """Test CommandNode.command uses CMD editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type(
            property_type="TEXT",
            node_type="CommandNode",
            property_name="command",
        )
        assert editor.editor_type == EditorType.CODE_CMD

    def test_execute_script_uses_python(self, qapp) -> None:
        """Test ExecuteScriptNode.script uses Python editor."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create_for_property_type(
            property_type="CODE",
            node_type="ExecuteScriptNode",
            property_name="script",
        )
        assert editor.editor_type == EditorType.CODE_PYTHON

    def test_override_not_applied_for_different_property(self, qapp) -> None:
        """Test override is not applied for different property name."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        # EmailSendNode has override for 'body', not 'subject'
        editor = EditorFactory.create_for_property_type(
            property_type="TEXT",
            node_type="EmailSendNode",
            property_name="subject",
        )
        # Should use default TEXT mapping (AUTO), not MARKDOWN
        assert editor.editor_type == EditorType.AUTO

    def test_override_not_applied_for_different_node(self, qapp) -> None:
        """Test override is not applied for different node type."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        # 'body' override only applies to EmailSendNode
        editor = EditorFactory.create_for_property_type(
            property_type="TEXT",
            node_type="SomeOtherNode",
            property_name="body",
        )
        # Should use default TEXT mapping (AUTO)
        assert editor.editor_type == EditorType.AUTO


# =============================================================================
# Factory Static Method Tests
# =============================================================================


class TestEditorFactoryStaticMethods:
    """Tests for EditorFactory being a static factory class."""

    def test_create_is_static_method(self) -> None:
        """Test create is a static method."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
        )

        # Can call without instantiation
        assert callable(EditorFactory.create)

    def test_create_for_property_type_is_static_method(self) -> None:
        """Test create_for_property_type is a static method."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
        )

        # Can call without instantiation
        assert callable(EditorFactory.create_for_property_type)

    def test_factory_not_singleton(self) -> None:
        """Test EditorFactory is not a singleton (no shared state)."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
        )

        # Can create multiple instances (though not recommended)
        f1 = EditorFactory()
        f2 = EditorFactory()
        assert f1 is not f2


# =============================================================================
# Integration Tests
# =============================================================================


class TestEditorFactoryIntegration:
    """Integration tests for EditorFactory with actual editors."""

    def test_created_editor_has_working_value_methods(self, qapp) -> None:
        """Test created editor can get/set values."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create(EditorType.CODE_PYTHON)
        editor.set_value("print('Hello')")

        assert editor.get_value() == "print('Hello')"

    def test_created_editor_has_working_cursor_methods(self, qapp) -> None:
        """Test created editor has working cursor position."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create(EditorType.CODE_PYTHON)
        editor.set_value("Hello World")

        # Cursor should be at valid position
        pos = editor.get_cursor_position()
        assert pos >= 0

    def test_created_editor_emits_value_changed(self, qapp, signal_capture) -> None:
        """Test created editor emits value_changed signal."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor = EditorFactory.create(EditorType.RICH_TEXT)
        editor.value_changed.connect(signal_capture.slot)

        editor.set_value("Test content")

        assert signal_capture.called

    def test_different_editor_types_independent(self, qapp) -> None:
        """Test different editor types are independent instances."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
            EditorFactory,
            EditorType,
        )

        editor1 = EditorFactory.create(EditorType.CODE_PYTHON)
        editor2 = EditorFactory.create(EditorType.CODE_PYTHON)

        editor1.set_value("Editor 1")
        editor2.set_value("Editor 2")

        assert editor1.get_value() == "Editor 1"
        assert editor2.get_value() == "Editor 2"
        assert editor1 is not editor2

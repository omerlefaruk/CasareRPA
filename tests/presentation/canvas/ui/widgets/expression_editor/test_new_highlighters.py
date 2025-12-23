"""
Tests for New Syntax Highlighters (JSON, YAML) and Code Detector.
"""

from unittest.mock import MagicMock, call, patch

import pytest
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QPlainTextEdit

from casare_rpa.presentation.canvas.ui.widgets.expression_editor.code_detector import (
    CodeDetector,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.json_highlighter import (
    JsonHighlighter,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.yaml_highlighter import (
    YamlHighlighter,
)

# =============================================================================
# JsonHighlighter Tests
# =============================================================================


class TestJsonHighlighter:
    """Tests for JSON syntax highlighting."""

    @pytest.fixture
    def highlighter_with_editor(self, qapp):
        """Create a JSON highlighter with a real editor."""
        editor = QPlainTextEdit()
        highlighter = JsonHighlighter(editor.document())
        return highlighter, editor

    def test_highlight_keywords(self, highlighter_with_editor):
        """Test JSON keywords (true, false, null)."""
        highlighter, editor = highlighter_with_editor
        with patch.object(highlighter, "setFormat") as mock_set_format:
            highlighter.highlightBlock("true false null")
            # Should be called for keywords
            assert mock_set_format.call_count >= 3

    def test_highlight_keys(self, highlighter_with_editor):
        """Test JSON keys."""
        highlighter, editor = highlighter_with_editor
        with patch.object(highlighter, "setFormat") as mock_set_format:
            highlighter.highlightBlock('{"key": "value"}')
            # Keys are #9CDCFE
            key_calls = [
                c
                for c in mock_set_format.call_args_list
                if c[0][2].foreground().color().name().upper() == "#9CDCFE"
            ]
            assert len(key_calls) >= 1

    def test_highlight_variable(self, highlighter_with_editor):
        """Test variable references in JSON."""
        highlighter, editor = highlighter_with_editor
        with patch.object(highlighter, "setFormat") as mock_set_format:
            highlighter.highlightBlock('{"val": "{{node.out}}"}')
            # Variable color check (usually Light Blue #9CDCFE and Bold)
            var_calls = [
                c
                for c in mock_set_format.call_args_list
                if c[0][2].fontWeight() == QFont.Weight.Bold
            ]
            assert len(var_calls) >= 1


# =============================================================================
# YamlHighlighter Tests
# =============================================================================


class TestYamlHighlighter:
    """Tests for YAML syntax highlighting."""

    @pytest.fixture
    def highlighter_with_editor(self, qapp):
        """Create a YAML highlighter."""
        editor = QPlainTextEdit()
        highlighter = YamlHighlighter(editor.document())
        return highlighter, editor

    def test_highlight_keys(self, highlighter_with_editor):
        """Test YAML keys."""
        highlighter, editor = highlighter_with_editor
        with patch.object(highlighter, "setFormat") as mock_set_format:
            highlighter.highlightBlock("key: value")
            # Keys are #9CDCFE
            key_calls = [
                c
                for c in mock_set_format.call_args_list
                if c[0][2].foreground().color().name().upper() == "#9CDCFE"
            ]
            assert len(key_calls) >= 1

    def test_highlight_comments(self, highlighter_with_editor):
        """Test YAML comments."""
        highlighter, editor = highlighter_with_editor
        with patch.object(highlighter, "setFormat") as mock_set_format:
            highlighter.highlightBlock("# comment here")
            # Comments are #6A9955
            comment_calls = [
                c
                for c in mock_set_format.call_args_list
                if c[0][2].foreground().color().name().upper() == "#6A9955"
            ]
            assert len(comment_calls) >= 1

    def test_highlight_variable(self, highlighter_with_editor):
        """Test variable references in YAML."""
        highlighter, editor = highlighter_with_editor
        with patch.object(highlighter, "setFormat") as mock_set_format:
            highlighter.highlightBlock("key: {{node.var}}")
            # Variable color check
            var_calls = [
                c
                for c in mock_set_format.call_args_list
                if c[0][2].fontWeight() == QFont.Weight.Bold
            ]
            assert len(var_calls) >= 1


# =============================================================================
# CodeDetector Tests
# =============================================================================


class TestCodeDetector:
    """Tests for automatic language detection."""

    def test_detect_python(self):
        """Test detection of Python code."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        code = "def my_func(a, b):\n    return a + b"
        assert CodeDetector.detect_language(code) == EditorType.CODE_PYTHON

    def test_detect_javascript(self):
        """Test detection of JavaScript code."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        code = "const x = (a, b) => a + b;"
        assert CodeDetector.detect_language(code) == EditorType.CODE_JAVASCRIPT

    def test_detect_json(self):
        """Test detection of JSON data."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        code = '{"id": 1, "name": "test", "active": true}'
        assert CodeDetector.detect_language(code) == EditorType.CODE_JSON

    def test_detect_yaml(self):
        """Test detection of YAML data."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        code = "name: test\nitems:\n  - id: 1\n    active: true"
        assert CodeDetector.detect_language(code) == EditorType.CODE_YAML

    def test_detect_markdown(self):
        """Test detection of Markdown."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        code = "# Heading\n\n**Bold text** and [links](http://example.com)"
        assert CodeDetector.detect_language(code) == EditorType.CODE_MARKDOWN

    def test_detect_empty(self):
        """Test detection of empty string."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        assert CodeDetector.detect_language("") == EditorType.RICH_TEXT  # Default

    def test_detect_ambiguous(self):
        """Test detection of ambiguous plain text."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
            EditorType,
        )

        assert CodeDetector.detect_language("Hello world") == EditorType.RICH_TEXT  # Default

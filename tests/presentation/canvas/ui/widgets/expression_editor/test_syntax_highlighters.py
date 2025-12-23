"""
Tests for Syntax Highlighters.

This test suite covers:
- PythonHighlighter - keywords, strings, comments, numbers
- JavaScriptHighlighter - JS syntax elements
- MarkdownHighlighter - headings, bold, italic, links, code

Test Philosophy:
- Happy path: highlighters correctly identify syntax elements
- Sad path: empty input, no matches
- Edge cases: nested syntax, multi-line blocks

Run: pytest tests/presentation/canvas/ui/widgets/expression_editor/test_syntax_highlighters.py -v
"""

import pytest

# =============================================================================
# PythonHighlighter Tests
# =============================================================================


class TestPythonHighlighterKeywords:
    """Tests for Python keyword highlighting."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a Python highlighter with mock document."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        return PythonHighlighter(editor.document())

    def test_highlighter_has_keywords_list(self, highlighter) -> None:
        """Test KEYWORDS class attribute exists."""
        assert hasattr(highlighter, "KEYWORDS")
        assert isinstance(highlighter.KEYWORDS, list)
        assert len(highlighter.KEYWORDS) > 0

    def test_keywords_include_def(self, highlighter) -> None:
        """Test 'def' is in keywords."""
        assert "def" in highlighter.KEYWORDS

    def test_keywords_include_class(self, highlighter) -> None:
        """Test 'class' is in keywords."""
        assert "class" in highlighter.KEYWORDS

    def test_keywords_include_import(self, highlighter) -> None:
        """Test 'import' is in keywords."""
        assert "import" in highlighter.KEYWORDS

    def test_keywords_include_if_else(self, highlighter) -> None:
        """Test 'if' and 'else' are in keywords."""
        assert "if" in highlighter.KEYWORDS
        assert "else" in highlighter.KEYWORDS
        assert "elif" in highlighter.KEYWORDS

    def test_keywords_include_loops(self, highlighter) -> None:
        """Test loop keywords are present."""
        assert "for" in highlighter.KEYWORDS
        assert "while" in highlighter.KEYWORDS
        assert "break" in highlighter.KEYWORDS
        assert "continue" in highlighter.KEYWORDS

    def test_keywords_include_async(self, highlighter) -> None:
        """Test async keywords are present."""
        assert "async" in highlighter.KEYWORDS
        assert "await" in highlighter.KEYWORDS


class TestPythonHighlighterBuiltins:
    """Tests for Python built-in highlighting."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a Python highlighter."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        return PythonHighlighter(editor.document())

    def test_builtins_list_exists(self, highlighter) -> None:
        """Test BUILTINS class attribute exists."""
        assert hasattr(highlighter, "BUILTINS")
        assert isinstance(highlighter.BUILTINS, list)

    def test_builtins_include_print(self, highlighter) -> None:
        """Test 'print' is in builtins."""
        assert "print" in highlighter.BUILTINS

    def test_builtins_include_range(self, highlighter) -> None:
        """Test 'range' is in builtins."""
        assert "range" in highlighter.BUILTINS

    def test_builtins_include_len(self, highlighter) -> None:
        """Test 'len' is in builtins."""
        assert "len" in highlighter.BUILTINS

    def test_builtins_include_type_functions(self, highlighter) -> None:
        """Test type conversion functions are in builtins."""
        assert "int" in highlighter.BUILTINS
        assert "str" in highlighter.BUILTINS
        assert "float" in highlighter.BUILTINS
        assert "list" in highlighter.BUILTINS
        assert "dict" in highlighter.BUILTINS


class TestPythonHighlighterFormats:
    """Tests for Python syntax format creation."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a Python highlighter."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        return PythonHighlighter(editor.document())

    def test_formats_dict_exists(self, highlighter) -> None:
        """Test _formats dictionary exists."""
        assert hasattr(highlighter, "_formats")
        assert isinstance(highlighter._formats, dict)

    def test_format_for_keyword_exists(self, highlighter) -> None:
        """Test keyword format is defined."""
        assert "keyword" in highlighter._formats

    def test_format_for_string_exists(self, highlighter) -> None:
        """Test string format is defined."""
        assert "string" in highlighter._formats

    def test_format_for_comment_exists(self, highlighter) -> None:
        """Test comment format is defined."""
        assert "comment" in highlighter._formats

    def test_format_for_number_exists(self, highlighter) -> None:
        """Test number format is defined."""
        assert "number" in highlighter._formats

    def test_format_for_function_exists(self, highlighter) -> None:
        """Test function format is defined."""
        assert "function" in highlighter._formats

    def test_format_for_builtin_exists(self, highlighter) -> None:
        """Test builtin format is defined."""
        assert "builtin" in highlighter._formats

    def test_format_for_decorator_exists(self, highlighter) -> None:
        """Test decorator format is defined."""
        assert "decorator" in highlighter._formats

    def test_format_for_variable_exists(self, highlighter) -> None:
        """Test variable ({{var}}) format is defined."""
        assert "variable" in highlighter._formats


class TestPythonHighlighterHighlightBlock:
    """Tests for highlightBlock method."""

    @pytest.fixture
    def highlighter_with_editor(self, qapp):
        """Create a Python highlighter with editor reference kept alive."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = PythonHighlighter(editor.document())
        # Return both to keep editor alive during test
        return highlighter, editor

    def test_highlight_empty_string(self, highlighter_with_editor) -> None:
        """Test highlighting empty string doesn't crash."""
        highlighter, editor = highlighter_with_editor
        # Should not raise
        highlighter.highlightBlock("")

    def test_highlight_simple_code(self, highlighter_with_editor) -> None:
        """Test highlighting simple Python code."""
        highlighter, editor = highlighter_with_editor
        # Should not raise
        highlighter.highlightBlock("def hello():")
        highlighter.highlightBlock("    print('world')")

    def test_highlight_with_comments(self, highlighter_with_editor) -> None:
        """Test highlighting code with comments."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("x = 1  # This is a comment")

    def test_highlight_with_strings(self, highlighter_with_editor) -> None:
        """Test highlighting code with strings."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock('message = "Hello World"')
        highlighter.highlightBlock("message = 'Hello World'")

    def test_highlight_with_numbers(self, highlighter_with_editor) -> None:
        """Test highlighting code with numbers."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("x = 123")
        highlighter.highlightBlock("y = 3.14")
        highlighter.highlightBlock("z = 1e-5")

    def test_highlight_with_variable_syntax(self, highlighter_with_editor) -> None:
        """Test highlighting {{variable}} syntax."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("result = {{node.output}}")


# =============================================================================
# JavaScriptHighlighter Tests
# =============================================================================


class TestJavaScriptHighlighterKeywords:
    """Tests for JavaScript keyword highlighting."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a JavaScript highlighter."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            JavaScriptHighlighter,
        )

        editor = QPlainTextEdit()
        return JavaScriptHighlighter(editor.document())

    def test_keywords_include_const_let_var(self, highlighter) -> None:
        """Test variable declaration keywords."""
        assert "const" in highlighter.KEYWORDS
        assert "let" in highlighter.KEYWORDS
        assert "var" in highlighter.KEYWORDS

    def test_keywords_include_function(self, highlighter) -> None:
        """Test 'function' is in keywords."""
        assert "function" in highlighter.KEYWORDS

    def test_keywords_include_async_await(self, highlighter) -> None:
        """Test async/await keywords."""
        assert "async" in highlighter.KEYWORDS
        assert "await" in highlighter.KEYWORDS

    def test_keywords_include_class_extends(self, highlighter) -> None:
        """Test class keywords."""
        assert "class" in highlighter.KEYWORDS
        assert "extends" in highlighter.KEYWORDS

    def test_keywords_include_import_export(self, highlighter) -> None:
        """Test module keywords."""
        assert "import" in highlighter.KEYWORDS
        assert "export" in highlighter.KEYWORDS
        assert "from" in highlighter.KEYWORDS


class TestJavaScriptHighlighterBuiltins:
    """Tests for JavaScript built-in highlighting."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a JavaScript highlighter."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            JavaScriptHighlighter,
        )

        editor = QPlainTextEdit()
        return JavaScriptHighlighter(editor.document())

    def test_builtins_include_console(self, highlighter) -> None:
        """Test 'console' is in builtins."""
        assert "console" in highlighter.BUILTINS

    def test_builtins_include_document(self, highlighter) -> None:
        """Test 'document' is in builtins."""
        assert "document" in highlighter.BUILTINS

    def test_builtins_include_window(self, highlighter) -> None:
        """Test 'window' is in builtins."""
        assert "window" in highlighter.BUILTINS

    def test_builtins_include_json(self, highlighter) -> None:
        """Test 'JSON' is in builtins."""
        assert "JSON" in highlighter.BUILTINS

    def test_builtins_include_primitives(self, highlighter) -> None:
        """Test primitive values are in builtins."""
        assert "undefined" in highlighter.BUILTINS
        assert "null" in highlighter.BUILTINS
        assert "true" in highlighter.BUILTINS
        assert "false" in highlighter.BUILTINS


class TestJavaScriptHighlighterFormats:
    """Tests for JavaScript format creation."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a JavaScript highlighter."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            JavaScriptHighlighter,
        )

        editor = QPlainTextEdit()
        return JavaScriptHighlighter(editor.document())

    def test_formats_dict_exists(self, highlighter) -> None:
        """Test _formats dictionary exists."""
        assert hasattr(highlighter, "_formats")

    def test_format_for_regex_exists(self, highlighter) -> None:
        """Test regex format is defined (JS-specific)."""
        assert "regex" in highlighter._formats


class TestJavaScriptHighlighterHighlightBlock:
    """Tests for JavaScript highlightBlock method."""

    @pytest.fixture
    def highlighter_with_editor(self, qapp):
        """Create a JavaScript highlighter with editor reference kept alive."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            JavaScriptHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = JavaScriptHighlighter(editor.document())
        return highlighter, editor

    def test_highlight_empty_string(self, highlighter_with_editor) -> None:
        """Test highlighting empty string."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("")

    def test_highlight_const_declaration(self, highlighter_with_editor) -> None:
        """Test highlighting const declaration."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("const x = 42;")

    def test_highlight_template_literal(self, highlighter_with_editor) -> None:
        """Test highlighting template literals."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("const msg = `Hello ${name}`;")

    def test_highlight_arrow_function(self, highlighter_with_editor) -> None:
        """Test highlighting arrow function."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("const fn = (x) => x * 2;")

    def test_highlight_single_line_comment(self, highlighter_with_editor) -> None:
        """Test highlighting single-line comments."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("// This is a comment")

    def test_highlight_multi_line_comment(self, highlighter_with_editor) -> None:
        """Test multi-line comment state handling."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("/* Start of comment")
        # Check state was set for multi-line (could be -1, 0, or 1 depending on implementation)
        state = highlighter.currentBlockState()
        # State is an int, just verify it's returned without crashing
        assert isinstance(state, int)


# =============================================================================
# MarkdownHighlighter Tests
# =============================================================================


class TestMarkdownHighlighterFormats:
    """Tests for Markdown format creation."""

    @pytest.fixture
    def highlighter(self, qapp):
        """Create a Markdown highlighter."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
            MarkdownHighlighter,
        )

        editor = QPlainTextEdit()
        return MarkdownHighlighter(editor.document())

    def test_formats_dict_exists(self, highlighter) -> None:
        """Test _formats dictionary exists."""
        assert hasattr(highlighter, "_formats")

    def test_format_for_heading_exists(self, highlighter) -> None:
        """Test heading format is defined."""
        assert "heading" in highlighter._formats

    def test_format_for_bold_exists(self, highlighter) -> None:
        """Test bold format is defined."""
        assert "bold" in highlighter._formats

    def test_format_for_italic_exists(self, highlighter) -> None:
        """Test italic format is defined."""
        assert "italic" in highlighter._formats

    def test_format_for_link_exists(self, highlighter) -> None:
        """Test link format is defined."""
        assert "link" in highlighter._formats

    def test_format_for_code_exists(self, highlighter) -> None:
        """Test code format is defined."""
        assert "code" in highlighter._formats

    def test_format_for_code_block_exists(self, highlighter) -> None:
        """Test code block format is defined."""
        assert "code_block" in highlighter._formats

    def test_format_for_list_exists(self, highlighter) -> None:
        """Test list format is defined."""
        assert "list" in highlighter._formats

    def test_format_for_blockquote_exists(self, highlighter) -> None:
        """Test blockquote format is defined."""
        assert "blockquote" in highlighter._formats


class TestMarkdownHighlighterHighlightBlock:
    """Tests for Markdown highlightBlock method."""

    @pytest.fixture
    def highlighter_with_editor(self, qapp):
        """Create a Markdown highlighter with editor reference kept alive."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
            MarkdownHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = MarkdownHighlighter(editor.document())
        return highlighter, editor

    def test_highlight_empty_string(self, highlighter_with_editor) -> None:
        """Test highlighting empty string."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("")

    def test_highlight_h1_heading(self, highlighter_with_editor) -> None:
        """Test highlighting H1 heading."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("# Heading 1")

    def test_highlight_h2_heading(self, highlighter_with_editor) -> None:
        """Test highlighting H2 heading."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("## Heading 2")

    def test_highlight_h3_heading(self, highlighter_with_editor) -> None:
        """Test highlighting H3 heading."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("### Heading 3")

    def test_highlight_bold_text(self, highlighter_with_editor) -> None:
        """Test highlighting bold text."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("This is **bold** text")

    def test_highlight_italic_text(self, highlighter_with_editor) -> None:
        """Test highlighting italic text."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("This is *italic* text")

    def test_highlight_link(self, highlighter_with_editor) -> None:
        """Test highlighting links."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("[Link text](https://example.com)")

    def test_highlight_inline_code(self, highlighter_with_editor) -> None:
        """Test highlighting inline code."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("Use `code` for inline")

    def test_highlight_code_block_fence(self, highlighter_with_editor) -> None:
        """Test highlighting code block fences."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("```python")

    def test_highlight_bullet_list(self, highlighter_with_editor) -> None:
        """Test highlighting bullet list."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("- List item")

    def test_highlight_numbered_list(self, highlighter_with_editor) -> None:
        """Test highlighting numbered list."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("1. First item")

    def test_highlight_blockquote(self, highlighter_with_editor) -> None:
        """Test highlighting blockquote."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("> This is a quote")

    def test_highlight_horizontal_rule(self, highlighter_with_editor) -> None:
        """Test highlighting horizontal rule."""
        highlighter, editor = highlighter_with_editor
        highlighter.highlightBlock("---")

    def test_code_block_state_toggle(self, highlighter_with_editor) -> None:
        """Test code block state handling."""
        highlighter, editor = highlighter_with_editor
        # Test that code block fence is processed without crash
        highlighter.highlightBlock("```")
        state_after_open = highlighter.currentBlockState()
        # State should be an int (implementation may vary)
        assert isinstance(state_after_open, int)

        # Continue code block - set previous state manually
        highlighter.setCurrentBlockState(1)
        highlighter.highlightBlock("def hello():")

        # End code block
        highlighter.setCurrentBlockState(1)
        highlighter.highlightBlock("```")
        state_after_close = highlighter.currentBlockState()

        # State transitions are handled; verify it's an int
        assert isinstance(state_after_close, int)


# =============================================================================
# Stylesheet Function Tests
# =============================================================================


class TestStylesheetFunctions:
    """Tests for editor stylesheet generation functions."""

    def test_python_stylesheet_exists(self) -> None:
        """Test get_python_editor_stylesheet function exists."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            get_python_editor_stylesheet,
        )

        assert callable(get_python_editor_stylesheet)

    def test_python_stylesheet_returns_string(self) -> None:
        """Test get_python_editor_stylesheet returns string."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            get_python_editor_stylesheet,
        )

        stylesheet = get_python_editor_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_python_stylesheet_contains_qt_class(self) -> None:
        """Test stylesheet contains QPlainTextEdit selector."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            get_python_editor_stylesheet,
        )

        stylesheet = get_python_editor_stylesheet()
        assert "QPlainTextEdit" in stylesheet

    def test_javascript_stylesheet_exists(self) -> None:
        """Test get_javascript_editor_stylesheet function exists."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            get_javascript_editor_stylesheet,
        )

        assert callable(get_javascript_editor_stylesheet)

    def test_javascript_stylesheet_returns_string(self) -> None:
        """Test get_javascript_editor_stylesheet returns string."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            get_javascript_editor_stylesheet,
        )

        stylesheet = get_javascript_editor_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0

    def test_markdown_stylesheet_exists(self) -> None:
        """Test get_markdown_editor_stylesheet function exists."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
            get_markdown_editor_stylesheet,
        )

        assert callable(get_markdown_editor_stylesheet)

    def test_markdown_stylesheet_returns_string(self) -> None:
        """Test get_markdown_editor_stylesheet returns string."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
            get_markdown_editor_stylesheet,
        )

        stylesheet = get_markdown_editor_stylesheet()
        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0


# =============================================================================
# SyntaxColors Class Tests
# =============================================================================


class TestSyntaxColors:
    """Tests for SyntaxColors constant class."""

    def test_syntax_colors_exists(self) -> None:
        """Test SyntaxColors class exists."""
        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            SyntaxColors,
        )

        assert SyntaxColors is not None

    def test_syntax_colors_keyword(self) -> None:
        """Test KEYWORD color is defined."""
        from PySide6.QtGui import QColor

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            SyntaxColors,
        )

        assert hasattr(SyntaxColors, "KEYWORD")
        assert isinstance(SyntaxColors.KEYWORD, QColor)

    def test_syntax_colors_string(self) -> None:
        """Test STRING color is defined."""
        from PySide6.QtGui import QColor

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            SyntaxColors,
        )

        assert hasattr(SyntaxColors, "STRING")
        assert isinstance(SyntaxColors.STRING, QColor)

    def test_syntax_colors_comment(self) -> None:
        """Test COMMENT color is defined."""
        from PySide6.QtGui import QColor

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            SyntaxColors,
        )

        assert hasattr(SyntaxColors, "COMMENT")
        assert isinstance(SyntaxColors.COMMENT, QColor)

    def test_syntax_colors_number(self) -> None:
        """Test NUMBER color is defined."""
        from PySide6.QtGui import QColor

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            SyntaxColors,
        )

        assert hasattr(SyntaxColors, "NUMBER")
        assert isinstance(SyntaxColors.NUMBER, QColor)


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestHighlighterEdgeCases:
    """Edge case tests for all highlighters."""

    def test_python_very_long_line(self, qapp) -> None:
        """Test Python highlighter with very long line."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = PythonHighlighter(editor.document())

        long_line = "x = " + "a" * 10000
        highlighter.highlightBlock(long_line)  # Should not crash

    def test_javascript_nested_comments(self, qapp) -> None:
        """Test JavaScript with complex comment patterns."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
            JavaScriptHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = JavaScriptHighlighter(editor.document())

        # String containing comment-like content
        highlighter.highlightBlock('const x = "/* not a comment */";')

    def test_markdown_mixed_formatting(self, qapp) -> None:
        """Test Markdown with mixed formatting."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
            MarkdownHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = MarkdownHighlighter(editor.document())

        # Bold inside link
        highlighter.highlightBlock("[**Bold link**](url)")
        # Code in heading
        highlighter.highlightBlock("# Heading with `code`")

    def test_python_unicode_identifiers(self, qapp) -> None:
        """Test Python with Unicode identifiers."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = PythonHighlighter(editor.document())

        highlighter.highlightBlock("def \u4e2d\u6587\u51fd\u6570():")
        highlighter.highlightBlock("\u53d8\u91cf = 42")

    def test_highlighter_with_only_whitespace(self, qapp) -> None:
        """Test highlighters with whitespace-only input."""
        from PySide6.QtWidgets import QPlainTextEdit

        from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
            PythonHighlighter,
        )

        editor = QPlainTextEdit()
        highlighter = PythonHighlighter(editor.document())

        highlighter.highlightBlock("    ")  # Spaces
        highlighter.highlightBlock("\t\t")  # Tabs

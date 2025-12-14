"""
Syntax Highlighters for CasareRPA Expression Editors.

Contains QSyntaxHighlighter implementations for various languages:
- PythonHighlighter: Python syntax (VSCode Dark+)
- JavaScriptHighlighter: JavaScript syntax
- MarkdownHighlighter: Markdown syntax
"""

from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
    PythonHighlighter,
    get_python_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
    MarkdownHighlighter,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
    JavaScriptHighlighter,
)

__all__ = [
    "PythonHighlighter",
    "get_python_editor_stylesheet",
    "MarkdownHighlighter",
    "JavaScriptHighlighter",
]

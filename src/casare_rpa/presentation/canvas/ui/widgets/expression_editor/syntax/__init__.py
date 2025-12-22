"""
Syntax Highlighters for CasareRPA Expression Editors.

Contains QSyntaxHighlighter implementations for various languages:
- PythonHighlighter: Python syntax (VSCode Dark+)
- JavaScriptHighlighter: JavaScript syntax
- MarkdownHighlighter: Markdown syntax
- JsonHighlighter: JSON syntax
- YamlHighlighter: YAML syntax
"""

from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.python_highlighter import (
    PythonHighlighter,
    get_python_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
    MarkdownHighlighter,
    get_markdown_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.javascript_highlighter import (
    JavaScriptHighlighter,
    get_javascript_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.json_highlighter import (
    JsonHighlighter,
    get_json_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.yaml_highlighter import (
    YamlHighlighter,
    get_yaml_editor_stylesheet,
)

__all__ = [
    "PythonHighlighter",
    "get_python_editor_stylesheet",
    "MarkdownHighlighter",
    "get_markdown_editor_stylesheet",
    "JavaScriptHighlighter",
    "get_javascript_editor_stylesheet",
    "JsonHighlighter",
    "get_json_editor_stylesheet",
    "YamlHighlighter",
    "get_yaml_editor_stylesheet",
]

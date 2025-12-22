"""
Python Syntax Highlighter for CasareRPA Expression Editor.

Provides VSCode Dark+ style syntax highlighting for Python code.

Colors follow VSCode Dark+ theme:
- Keywords (#C586C0): def, if, for, while, return, import, class, etc.
- Functions (#DCDCAA): function definitions and calls
- Strings (#CE9178): single/double/triple quoted
- Numbers (#B5CEA8): integers, floats
- Comments (#6A9955): # comments
- Built-ins (#4EC9B0): True, False, None
- Decorators (#DCDCAA): @decorator
- Variables (#9CDCFE): variable references
"""

import re
from typing import List, Tuple

from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from casare_rpa.presentation.canvas.ui.theme import THEME


class SyntaxColors:
    """VSCode Dark+ syntax highlighting colors."""

    KEYWORD = QColor("#C586C0")  # Purple - keywords
    FUNCTION = QColor("#DCDCAA")  # Yellow - function names
    STRING = QColor("#CE9178")  # Orange-brown - strings
    NUMBER = QColor("#B5CEA8")  # Light green - numbers
    COMMENT = QColor("#6A9955")  # Green - comments
    BUILTIN = QColor("#4EC9B0")  # Teal - built-ins (True, False, None)
    DECORATOR = QColor("#DCDCAA")  # Yellow - decorators
    VARIABLE = QColor("#9CDCFE")  # Light blue - variables
    OPERATOR = QColor("#D4D4D4")  # Gray - operators
    CLASS = QColor("#4EC9B0")  # Teal - class names
    SELF = QColor("#569CD6")  # Blue - self keyword


class PythonHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for Python code with VSCode Dark+ colors.

    Highlights:
    - Keywords (def, if, for, while, return, etc.)
    - Function definitions and calls
    - String literals (single, double, triple quoted)
    - Numbers (integers, floats, scientific notation)
    - Comments (# style)
    - Built-in constants (True, False, None)
    - Decorators (@decorator)
    - Class names

    Usage:
        editor = QPlainTextEdit()
        highlighter = PythonHighlighter(editor.document())
    """

    # Python keywords
    KEYWORDS = [
        "False",
        "None",
        "True",
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "try",
        "while",
        "with",
        "yield",
    ]

    # Built-in functions
    BUILTINS = [
        "abs",
        "all",
        "any",
        "bin",
        "bool",
        "bytearray",
        "bytes",
        "callable",
        "chr",
        "classmethod",
        "compile",
        "complex",
        "delattr",
        "dict",
        "dir",
        "divmod",
        "enumerate",
        "eval",
        "exec",
        "filter",
        "float",
        "format",
        "frozenset",
        "getattr",
        "globals",
        "hasattr",
        "hash",
        "help",
        "hex",
        "id",
        "input",
        "int",
        "isinstance",
        "issubclass",
        "iter",
        "len",
        "list",
        "locals",
        "map",
        "max",
        "memoryview",
        "min",
        "next",
        "object",
        "oct",
        "open",
        "ord",
        "pow",
        "print",
        "property",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "setattr",
        "slice",
        "sorted",
        "staticmethod",
        "str",
        "sum",
        "super",
        "tuple",
        "type",
        "vars",
        "zip",
    ]

    def __init__(self, document: QTextDocument = None) -> None:
        """
        Initialize the Python syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)

        self._formats = {}
        self._rules: List[Tuple[re.Pattern, str]] = []

        self._create_formats()
        self._create_rules()

    def _create_formats(self) -> None:
        """Create text formats for each token type."""
        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(SyntaxColors.KEYWORD)
        keyword_format.setFontWeight(QFont.Weight.Normal)
        self._formats["keyword"] = keyword_format

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(SyntaxColors.FUNCTION)
        self._formats["function"] = function_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(SyntaxColors.STRING)
        self._formats["string"] = string_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(SyntaxColors.NUMBER)
        self._formats["number"] = number_format

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(SyntaxColors.COMMENT)
        comment_format.setFontItalic(True)
        self._formats["comment"] = comment_format

        # Built-in format (True, False, None, built-in functions)
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(SyntaxColors.BUILTIN)
        self._formats["builtin"] = builtin_format

        # Decorator format
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(SyntaxColors.DECORATOR)
        self._formats["decorator"] = decorator_format

        # Class format
        class_format = QTextCharFormat()
        class_format.setForeground(SyntaxColors.CLASS)
        self._formats["class"] = class_format

        # Self format
        self_format = QTextCharFormat()
        self_format.setForeground(SyntaxColors.SELF)
        self._formats["self"] = self_format

        # Variable reference format ({{var}})
        variable_format = QTextCharFormat()
        variable_format.setForeground(SyntaxColors.VARIABLE)
        variable_format.setFontWeight(QFont.Weight.Bold)
        self._formats["variable"] = variable_format

    def _create_rules(self) -> None:
        """Create highlighting rules."""
        # Keywords (True, False, None are handled separately as builtins)
        keywords = [kw for kw in self.KEYWORDS if kw not in ("True", "False", "None")]
        keyword_pattern = r"\b(" + "|".join(keywords) + r")\b"
        self._rules.append((re.compile(keyword_pattern), "keyword"))

        # Built-in constants (True, False, None)
        builtin_const_pattern = r"\b(True|False|None)\b"
        self._rules.append((re.compile(builtin_const_pattern), "builtin"))

        # Built-in functions
        builtin_pattern = r"\b(" + "|".join(self.BUILTINS) + r")\b(?=\s*\()"
        self._rules.append((re.compile(builtin_pattern), "builtin"))

        # Self keyword
        self._rules.append((re.compile(r"\bself\b"), "self"))

        # Function definitions
        self._rules.append((re.compile(r"\bdef\s+(\w+)"), "function"))

        # Class definitions
        self._rules.append((re.compile(r"\bclass\s+(\w+)"), "class"))

        # Function calls (word followed by parenthesis)
        self._rules.append((re.compile(r"\b(\w+)(?=\s*\()"), "function"))

        # Decorators
        self._rules.append((re.compile(r"@\w+(\.\w+)*"), "decorator"))

        # Numbers (integers, floats, scientific notation)
        number_pattern = r"\b[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?\b"
        self._rules.append((re.compile(number_pattern), "number"))

        # Hex numbers
        self._rules.append((re.compile(r"\b0[xX][0-9a-fA-F]+\b"), "number"))

        # Binary numbers
        self._rules.append((re.compile(r"\b0[bB][01]+\b"), "number"))

        # Octal numbers
        self._rules.append((re.compile(r"\b0[oO][0-7]+\b"), "number"))

        # Variable references {{var.path}}
        self._rules.append((re.compile(r"\{\{[^}]+\}\}"), "variable"))

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of Python text.

        Args:
            text: The text block to highlight
        """
        if not text:
            return

        # Track highlighted positions to avoid overlapping
        highlighted = [False] * len(text)

        # Handle multi-line strings state
        self.setCurrentBlockState(0)

        # Check for multi-line strings (triple quotes)
        self.previousBlockState() == 1

        # Triple-quoted strings (must be checked first)
        for match in re.finditer(r'""".*?"""|\'\'\'.*?\'\'\'', text, re.DOTALL):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self._formats["string"])
            for i in range(start, min(start + length, len(text))):
                highlighted[i] = True

        # Unterminated triple quotes (start of multi-line)
        for pattern in (r'"""', r"'''"):
            if pattern in text:
                idx = text.find(pattern)
                # Check if there's a closing quote
                close_idx = text.find(pattern, idx + 3)
                if close_idx == -1:
                    # Multi-line string starts
                    self.setCurrentBlockState(1)
                    self.setFormat(idx, len(text) - idx, self._formats["string"])
                    for i in range(idx, len(text)):
                        highlighted[i] = True

        # Single/double quoted strings
        string_patterns = [
            re.compile(r'"(?:[^"\\]|\\.)*"'),
            re.compile(r"'(?:[^'\\]|\\.)*'"),
        ]
        for pattern in string_patterns:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - start
                if start < len(highlighted) and not highlighted[start]:
                    self.setFormat(start, length, self._formats["string"])
                    for i in range(start, min(start + length, len(highlighted))):
                        highlighted[i] = True

        # Comments (must be after strings to not highlight # in strings)
        comment_pattern = re.compile(r"#.*$")
        for match in comment_pattern.finditer(text):
            start = match.start()
            length = match.end() - start
            # Only highlight if not inside a string
            if start < len(highlighted) and not highlighted[start]:
                self.setFormat(start, length, self._formats["comment"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Apply regular rules (keywords, numbers, etc.)
        for pattern, format_name in self._rules:
            for match in pattern.finditer(text):
                # For patterns with groups, use the group
                if match.lastindex and match.lastindex >= 1:
                    start = match.start(1)
                    length = match.end(1) - start
                else:
                    start = match.start()
                    length = match.end() - start

                # Don't highlight if already highlighted (e.g., in string or comment)
                if start < len(highlighted) and not highlighted[start]:
                    self.setFormat(start, length, self._formats[format_name])


def get_python_editor_stylesheet() -> str:
    """
    Get CSS stylesheet for QPlainTextEdit with Python highlighting.

    Returns:
        CSS stylesheet string for dark theme Python editor
    """
    return f"""
        QPlainTextEdit {{
            background-color: {THEME.bg_darkest};
            color: {THEME.text_primary};
            border: none;
            font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
            font-size: 12px;
            selection-background-color: {THEME.selected};
            selection-color: #FFFFFF;
        }}
        QScrollBar:vertical {{
            background: {THEME.bg_dark};
            width: 12px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {THEME.scrollbar};
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {THEME.scrollbar_hover};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {THEME.bg_dark};
            height: 12px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {THEME.scrollbar};
            min-width: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {THEME.scrollbar_hover};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """

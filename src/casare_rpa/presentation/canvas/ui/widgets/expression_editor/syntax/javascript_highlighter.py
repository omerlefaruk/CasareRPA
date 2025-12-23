"""
JavaScript Syntax Highlighter for CasareRPA.

Provides VSCode Dark+ style syntax highlighting for JavaScript content.

Colors (VSCode Dark+):
- Keywords: #C586C0 (purple) - const, let, var, function, async, await, if, for, return
- Functions: #DCDCAA (yellow)
- Strings: #CE9178 (orange-brown) - single/double quotes, template literals
- Numbers: #B5CEA8 (light green)
- Comments: #6A9955 (green) - // and /* */
- Built-ins: #4EC9B0 (teal) - document, window, console
- Regex: #D16969 (red) - /pattern/flags
"""

import re

from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)


class JavaScriptHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for JavaScript content with VSCode Dark+ colors.

    Highlights:
    - Keywords (const, let, var, function, async, await, if, else, for, etc.)
    - Built-in objects (document, window, console, Math, etc.)
    - Functions and method calls
    - Strings (single quotes, double quotes, template literals)
    - Numbers (integers, floats, hex, binary, octal)
    - Comments (single-line // and multi-line /* */)
    - Regular expressions (/pattern/flags)

    Usage:
        editor = QPlainTextEdit()
        highlighter = JavaScriptHighlighter(editor.document())
    """

    # VSCode Dark+ colors
    COLOR_KEYWORD = "#C586C0"  # Purple
    COLOR_FUNCTION = "#DCDCAA"  # Yellow
    COLOR_STRING = "#CE9178"  # Orange-brown
    COLOR_NUMBER = "#B5CEA8"  # Light green
    COLOR_COMMENT = "#6A9955"  # Green
    COLOR_BUILTIN = "#4EC9B0"  # Teal
    COLOR_REGEX = "#D16969"  # Red
    COLOR_OPERATOR = "#D4D4D4"  # Light gray
    COLOR_PROPERTY = "#9CDCFE"  # Light blue
    COLOR_VARIABLE = "#9CDCFE"  # Light blue

    # JavaScript keywords
    KEYWORDS = [
        "async",
        "await",
        "break",
        "case",
        "catch",
        "class",
        "const",
        "continue",
        "debugger",
        "default",
        "delete",
        "do",
        "else",
        "export",
        "extends",
        "finally",
        "for",
        "function",
        "if",
        "import",
        "in",
        "instanceof",
        "let",
        "new",
        "return",
        "static",
        "super",
        "switch",
        "this",
        "throw",
        "try",
        "typeof",
        "var",
        "void",
        "while",
        "with",
        "yield",
        "from",
        "of",
    ]

    # Built-in objects and functions
    BUILTINS = [
        "document",
        "window",
        "console",
        "Math",
        "JSON",
        "Array",
        "Object",
        "String",
        "Number",
        "Boolean",
        "Date",
        "RegExp",
        "Error",
        "Promise",
        "Map",
        "Set",
        "WeakMap",
        "WeakSet",
        "Symbol",
        "Proxy",
        "Reflect",
        "Intl",
        "globalThis",
        "undefined",
        "null",
        "true",
        "false",
        "NaN",
        "Infinity",
        "parseInt",
        "parseFloat",
        "isNaN",
        "isFinite",
        "eval",
        "setTimeout",
        "setInterval",
        "clearTimeout",
        "clearInterval",
        "fetch",
        "alert",
        "confirm",
        "prompt",
        "print",
    ]

    def __init__(self, document: QTextDocument | None = None) -> None:
        """
        Initialize the JavaScript syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)

        self._formats = {}
        self._create_formats()

    def _create_formats(self) -> None:
        """Create text formats for each JavaScript element type."""
        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(self.COLOR_KEYWORD))
        self._formats["keyword"] = keyword_format

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor(self.COLOR_FUNCTION))
        self._formats["function"] = function_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(self.COLOR_STRING))
        self._formats["string"] = string_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(self.COLOR_NUMBER))
        self._formats["number"] = number_format

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(self.COLOR_COMMENT))
        comment_format.setFontItalic(True)
        self._formats["comment"] = comment_format

        # Built-in format
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor(self.COLOR_BUILTIN))
        self._formats["builtin"] = builtin_format

        # Regex format
        regex_format = QTextCharFormat()
        regex_format.setForeground(QColor(self.COLOR_REGEX))
        self._formats["regex"] = regex_format

        # Property/variable format
        property_format = QTextCharFormat()
        property_format.setForeground(QColor(self.COLOR_PROPERTY))
        self._formats["property"] = property_format

        # CasareRPA Variable format ({{var}})
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor(self.COLOR_VARIABLE))
        variable_format.setFontWeight(QFont.Weight.Bold)
        self._formats["variable"] = variable_format

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of JavaScript text.

        Args:
            text: The text block to highlight
        """
        if not text:
            return

        # Track highlighted positions to avoid overlapping
        highlighted = [False] * len(text)

        # Check for multi-line comment state
        previous_state = self.previousBlockState()
        in_block_comment = previous_state == 1

        # Handle multi-line comments
        if in_block_comment:
            end_idx = text.find("*/")
            if end_idx >= 0:
                self.setFormat(0, end_idx + 2, self._formats["comment"])
                for i in range(end_idx + 2):
                    if i < len(highlighted):
                        highlighted[i] = True
                self.setCurrentBlockState(0)
            else:
                self.setFormat(0, len(text), self._formats["comment"])
                self.setCurrentBlockState(1)
                return
        else:
            self.setCurrentBlockState(0)

        # Single-line comments: //
        single_comment_pattern = re.compile(r"//.*$")
        for match in single_comment_pattern.finditer(text):
            start = match.start()
            if not highlighted[start]:
                self.setFormat(start, match.end() - start, self._formats["comment"])
                for i in range(start, match.end()):
                    if i < len(highlighted):
                        highlighted[i] = True

        # Multi-line comment start: /*
        block_comment_start = re.compile(r"/\*")
        for match in block_comment_start.finditer(text):
            start = match.start()
            if highlighted[start]:
                continue

            end_match = re.search(r"\*/", text[start + 2 :])
            if end_match:
                end = start + 2 + end_match.end()
                self.setFormat(start, end - start, self._formats["comment"])
                for i in range(start, end):
                    if i < len(highlighted):
                        highlighted[i] = True
            else:
                self.setFormat(start, len(text) - start, self._formats["comment"])
                for i in range(start, len(text)):
                    if i < len(highlighted):
                        highlighted[i] = True
                self.setCurrentBlockState(1)
                return

        # Strings: "..." '...' `...`
        string_patterns = [
            (re.compile(r'"(?:[^"\\]|\\.)*"'), "string"),
            (re.compile(r"'(?:[^'\\]|\\.)*'"), "string"),
            (re.compile(r"`(?:[^`\\]|\\.)*`"), "string"),
        ]
        for pattern, format_name in string_patterns:
            for match in pattern.finditer(text):
                start = match.start()
                length = match.end() - match.start()
                if not any(highlighted[start : start + length]):
                    self.setFormat(start, length, self._formats[format_name])
                    for i in range(start, min(start + length, len(highlighted))):
                        highlighted[i] = True

        # Regular expressions: /pattern/flags
        # Simplified - matches common regex patterns
        regex_pattern = re.compile(r"(?<=[=(\[,!&|?:;])\s*/(?![/*])(?:[^/\\]|\\.)+/[gimsuy]*")
        for match in regex_pattern.finditer(text):
            start = match.start()
            # Skip leading whitespace
            while start < match.end() and text[start].isspace():
                start += 1
            length = match.end() - start
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["regex"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Keywords
        keyword_pattern = re.compile(r"\b(" + "|".join(self.KEYWORDS) + r")\b")
        for match in keyword_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["keyword"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Built-ins
        builtin_pattern = re.compile(r"\b(" + "|".join(self.BUILTINS) + r")\b")
        for match in builtin_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["builtin"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Function calls: identifier(
        function_pattern = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
        for match in function_pattern.finditer(text):
            start = match.start(1)
            length = len(match.group(1))
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["function"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Numbers: integers, floats, hex, binary, octal
        number_pattern = re.compile(
            r"\b("
            r"0[xX][0-9a-fA-F]+|"  # Hex
            r"0[bB][01]+|"  # Binary
            r"0[oO][0-7]+|"  # Octal
            r"\d+\.?\d*(?:[eE][+-]?\d+)?|"  # Decimal/float
            r"\.\d+(?:[eE][+-]?\d+)?"  # Float starting with .
            r")\b"
        )
        for match in number_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["number"])

        # CasareRPA Variable references {{var}}
        variable_pattern = re.compile(r"\{\{[^}]+\}\}")
        for match in variable_pattern.finditer(text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self._formats["variable"])
            for i in range(start, min(start + length, len(highlighted))):
                highlighted[i] = True


def get_javascript_editor_stylesheet() -> str:
    """
    Get CSS stylesheet for QPlainTextEdit with JavaScript editing.

    Returns:
        CSS stylesheet string for dark theme JavaScript editor
    """
    from casare_rpa.presentation.canvas.ui.theme import Theme

    c = Theme.get_colors()
    return f"""
        QPlainTextEdit {{
            background-color: {c.background};
            color: {c.text_primary};
            border: none;
            font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
            font-size: 12px;
            selection-background-color: {c.selection};
            selection-color: #FFFFFF;
        }}
        QScrollBar:vertical {{
            background: {c.background_alt};
            width: 10px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {c.secondary_hover};
            min-height: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {c.border_light};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar:horizontal {{
            background: {c.background_alt};
            height: 10px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {c.secondary_hover};
            min-width: 20px;
            border-radius: 5px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {c.border_light};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """

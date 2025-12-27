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

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS


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

    def __init__(self, document: QTextDocument | None = None) -> None:
        """
        Initialize the JavaScript syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)
        self._theme_colors = THEME
        self._formats = {}
        self._create_formats()

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

    def _create_formats(self) -> None:
        """Create text formats for each JavaScript element type."""
        # Get syntax colors from theme
        syntax_colors = {
            "keyword": QColor(self._theme_colors.syntax_keyword),
            "function": QColor(self._theme_colors.syntax_string),
            "string": QColor(self._theme_colors.syntax_string),
            "number": QColor(self._theme_colors.syntax_number),
            "comment": QColor(self._theme_colors.syntax_comment),
            "builtin": QColor(self._theme_colors.syntax_variable),
            "regex": QColor(self._theme_colors.syntax_error),
            "property": QColor(self._theme_colors.syntax_keyword),
            "variable": QColor(self._theme_colors.syntax_variable),
        }

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(syntax_colors["keyword"])
        self._formats["keyword"] = keyword_format

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(syntax_colors["function"])
        self._formats["function"] = function_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(syntax_colors["string"])
        self._formats["string"] = string_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(syntax_colors["number"])
        self._formats["number"] = number_format

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(syntax_colors["comment"])
        comment_format.setFontItalic(True)
        self._formats["comment"] = comment_format

        # Built-in format
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(syntax_colors["builtin"])
        self._formats["builtin"] = builtin_format

        # Regex format
        regex_format = QTextCharFormat()
        regex_format.setForeground(syntax_colors["regex"])
        self._formats["regex"] = regex_format

        # Property/variable format
        property_format = QTextCharFormat()
        property_format.setForeground(syntax_colors["property"])
        self._formats["property"] = property_format

        # CasareRPA Variable format ({{var}})
        variable_format = QTextCharFormat()
        variable_format.setForeground(syntax_colors["variable"])
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
    from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS

    c = THEME
    return f"""
        QPlainTextEdit {{
            background-color: {c.bg_canvas};
            color: {c.text_primary};
            border: none;
            font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
            font-size: {TOKENS.typography.body}px;
            selection-background-color: {c.bg_selected};
            selection-color: {THEME.text_primary};
        }}
        QScrollBar:vertical {{
            background: {c.bg_elevated};
            width: 10px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {c.bg_component};
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
            background: {c.bg_elevated};
            height: 10px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background: {c.bg_component};
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

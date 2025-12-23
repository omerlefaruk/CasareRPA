"""
JSON Syntax Highlighter for CasareRPA.

Provides VSCode Dark+ style syntax highlighting for JSON content
displayed in the Node Output Inspector.

Colors:
- Keys: #9CDCFE (light blue)
- Strings: #CE9178 (orange-brown)
- Numbers: #B5CEA8 (light green)
- Booleans/null: #569CD6 (blue)
- Brackets/braces: #D4D4D4 (light gray)
"""

import re
from typing import Optional

from PySide6.QtGui import (
    QColor,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from casare_rpa.presentation.canvas.ui.theme import THEME


# VSCode Dark+ color scheme using THEME
class JsonColors:
    """VSCode Dark+ JSON colors using THEME."""

    KEY = QColor(THEME.json_key)
    STRING = QColor(THEME.json_string)
    NUMBER = QColor(THEME.json_number)
    BOOLEAN = QColor(THEME.json_boolean)
    NULL = QColor(THEME.json_boolean)  # Same as boolean
    BRACKET = QColor(THEME.text_primary)
    COLON = QColor(THEME.text_primary)
    COMMA = QColor(THEME.text_primary)


class JsonSyntaxHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for JSON content with VSCode Dark+ colors.

    Highlights:
    - Keys (property names)
    - String values
    - Number values
    - Boolean values (true/false)
    - Null values
    - Brackets and braces

    Usage:
        editor = QPlainTextEdit()
        highlighter = JsonSyntaxHighlighter(editor.document())
    """

    def __init__(self, document: QTextDocument | None = None) -> None:
        """
        Initialize the JSON syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)

        # Create text formats for each token type
        self._formats = {}
        self._create_formats()

        # Compile regex patterns for each token type
        self._patterns = []
        self._create_patterns()

    def _create_formats(self) -> None:
        """Create text formats for each JSON token type."""
        # Key format (property names)
        key_format = QTextCharFormat()
        key_format.setForeground(JsonColors.KEY)
        self._formats["key"] = key_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(JsonColors.STRING)
        self._formats["string"] = string_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(JsonColors.NUMBER)
        self._formats["number"] = number_format

        # Boolean format
        boolean_format = QTextCharFormat()
        boolean_format.setForeground(JsonColors.BOOLEAN)
        self._formats["boolean"] = boolean_format

        # Null format
        null_format = QTextCharFormat()
        null_format.setForeground(JsonColors.NULL)
        self._formats["null"] = null_format

        # Bracket format (includes braces and square brackets)
        bracket_format = QTextCharFormat()
        bracket_format.setForeground(JsonColors.BRACKET)
        self._formats["bracket"] = bracket_format

        # Punctuation format (colon, comma)
        punctuation_format = QTextCharFormat()
        punctuation_format.setForeground(JsonColors.COLON)
        self._formats["punctuation"] = punctuation_format

    def _create_patterns(self) -> None:
        """Create regex patterns for each JSON token type."""
        # Key pattern: "key":
        # Match quoted string followed by colon
        key_pattern = re.compile(r'"([^"\\]|\\.)*"\s*(?=:)')
        self._patterns.append((key_pattern, "key"))

        # String pattern: "value" (not followed by colon, so not a key)
        # This is handled in highlightBlock to avoid matching keys
        string_pattern = re.compile(r'"([^"\\]|\\.)*"')
        self._patterns.append((string_pattern, "string"))

        # Number pattern: integers and floats (including negative and scientific)
        number_pattern = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
        self._patterns.append((number_pattern, "number"))

        # Boolean pattern: true or false
        boolean_pattern = re.compile(r"\b(true|false)\b")
        self._patterns.append((boolean_pattern, "boolean"))

        # Null pattern
        null_pattern = re.compile(r"\bnull\b")
        self._patterns.append((null_pattern, "null"))

        # Bracket pattern: {}, []
        bracket_pattern = re.compile(r"[{}\[\]]")
        self._patterns.append((bracket_pattern, "bracket"))

        # Punctuation pattern: :, ,
        punctuation_pattern = re.compile(r"[:,]")
        self._patterns.append((punctuation_pattern, "punctuation"))

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of JSON text.

        Args:
            text: The text block to highlight
        """
        if not text:
            return

        # Track which positions have been highlighted (to avoid overlapping)
        highlighted = [False] * len(text)

        # First pass: highlight keys (quoted strings followed by colon)
        key_pattern = re.compile(r'"([^"\\]|\\.)*"\s*(?=:)')
        for match in key_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            # Only highlight the quoted part, not trailing whitespace
            quoted_match = re.match(r'"([^"\\]|\\.)*"', match.group())
            if quoted_match:
                length = quoted_match.end()
            self.setFormat(start, length, self._formats["key"])
            for i in range(start, start + length):
                if i < len(highlighted):
                    highlighted[i] = True

        # Second pass: highlight string values (not keys)
        string_pattern = re.compile(r'"([^"\\]|\\.)*"')
        for match in string_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            # Only highlight if not already highlighted as key
            if start < len(highlighted) and not highlighted[start]:
                self.setFormat(start, length, self._formats["string"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Highlight numbers
        number_pattern = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
        for match in number_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if start < len(highlighted) and not highlighted[start]:
                self.setFormat(start, length, self._formats["number"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Highlight booleans
        boolean_pattern = re.compile(r"\b(true|false)\b")
        for match in boolean_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if start < len(highlighted) and not highlighted[start]:
                self.setFormat(start, length, self._formats["boolean"])

        # Highlight null
        null_pattern = re.compile(r"\bnull\b")
        for match in null_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if start < len(highlighted) and not highlighted[start]:
                self.setFormat(start, length, self._formats["null"])

        # Highlight brackets (always visible)
        bracket_pattern = re.compile(r"[{}\[\]]")
        for match in bracket_pattern.finditer(text):
            start = match.start()
            length = 1
            self.setFormat(start, length, self._formats["bracket"])

        # Highlight punctuation (always visible)
        punctuation_pattern = re.compile(r"[:,]")
        for match in punctuation_pattern.finditer(text):
            start = match.start()
            length = 1
            self.setFormat(start, length, self._formats["punctuation"])


def get_json_highlighter_stylesheet() -> str:
    """
    Get CSS stylesheet for QPlainTextEdit with JSON highlighting.

    Returns:
        CSS stylesheet string for dark theme JSON editor
    """
    return f"""
        QPlainTextEdit {{
            background-color: {THEME.bg_darker};
            color: {THEME.text_primary};
            border: none;
            font-family: "Consolas", "Courier New", monospace;
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

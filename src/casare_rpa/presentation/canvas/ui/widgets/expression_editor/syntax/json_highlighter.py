"""
JSON Syntax Highlighter for CasareRPA Expression Editor.

Provides VSCode Dark+ style syntax highlighting for JSON content.

Colors follow VSCode Dark+ theme:
- Keys (#9CDCFE): "key": ...
- Strings (#CE9178): "string value"
- Numbers (#B5CEA8): integers, floats
- Keywords (#569CD6): true, false, null
- Braces/Brackets (#D4D4D4): {}, []
- Variables (#9CDCFE): variable references
"""

import re

from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from casare_rpa.presentation.canvas.ui.theme import THEME


class JsonHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for JSON code with VSCode Dark+ colors.

    Highlights:
    - Keys ("key":)
    - String values ("value")
    - Numbers
    - Boolean/Null (true, false, null)
    - Braces/Brackets
    - Variable references {{var}}

    Usage:
        editor = QPlainTextEdit()
        highlighter = JsonHighlighter(editor.document())
    """

    def __init__(self, document: QTextDocument = None) -> None:
        """
        Initialize the JSON syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)

        self._theme_colors = THEME
        self._formats = {}
        self._rules: list[tuple[re.Pattern, str]] = []

        self._create_formats()
        self._create_rules()

    def _create_formats(self) -> None:
        """Create text formats for each token type."""
        # Get syntax colors from theme
        syntax_colors = {
            "key": QColor(self._theme_colors.syntax_keyword),
            "string": QColor(self._theme_colors.syntax_string),
            "number": QColor(self._theme_colors.syntax_number),
            "keyword": QColor(self._theme_colors.syntax_variable),
            "operator": QColor(self._theme_colors.text_secondary),
            "variable": QColor(self._theme_colors.syntax_keyword),
        }

        # Key format
        key_format = QTextCharFormat()
        key_format.setForeground(syntax_colors["key"])
        key_format.setFontWeight(QFont.Weight.Bold)
        self._formats["key"] = key_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(syntax_colors["string"])
        self._formats["string"] = string_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(syntax_colors["number"])
        self._formats["number"] = number_format

        # Keyword format (true, false, null)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(syntax_colors["keyword"])
        self._formats["keyword"] = keyword_format

        # Operator format ({, }, [, ], :)
        operator_format = QTextCharFormat()
        operator_format.setForeground(syntax_colors["operator"])
        self._formats["operator"] = operator_format

        # Variable reference format ({{var}})
        variable_format = QTextCharFormat()
        variable_format.setForeground(syntax_colors["variable"])
        variable_format.setFontWeight(QFont.Weight.Bold)
        self._formats["variable"] = variable_format

    def _create_rules(self) -> None:
        """Create highlighting rules."""
        # Keywords
        self._rules.append((re.compile(r"\b(true|false|null)\b"), "keyword"))

        # Keys (string followed by colon)
        # We handle this carefully: capture "key" part before :
        self._rules.append((re.compile(r'("[^"\\]*")\s*:'), "key"))

        # String values (string NOT followed by colon)
        self._rules.append((re.compile(r'("[^"\\]*")(?!\s*:)'), "string"))

        # Numbers
        number_pattern = r"\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b"
        self._rules.append((re.compile(number_pattern), "number"))

        # Operators
        self._rules.append((re.compile(r"[\[\]{}\\:,]"), "operator"))

        # Variable references {{var}}
        self._rules.append((re.compile(r"\{\{[^}]+\}\}"), "variable"))

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of JSON text.

        Args:
            text: The text block to highlight
        """
        if not text:
            return

        # Track highlighted positions to avoid overlapping
        highlighted = [False] * len(text)

        # Apply rules
        for pattern, format_name in self._rules:
            for match in pattern.finditer(text):
                # For patterns with groups (like keys), use group 1
                if match.lastindex and match.lastindex >= 1:
                    start = match.start(1)
                    length = match.end(1) - start
                else:
                    start = match.start()
                    length = match.end() - start

                # Don't highlight if already highlighted
                if start < len(highlighted) and not highlighted[start]:
                    self.setFormat(start, length, self._formats[format_name])
                    for i in range(start, min(start + length, len(highlighted))):
                        highlighted[i] = True


def get_json_editor_stylesheet() -> str:
    """
    Get CSS stylesheet for QPlainTextEdit with JSON highlighting.

    Returns:
        CSS stylesheet string for dark theme JSON editor
    """
    return f"""
        QPlainTextEdit {{
            background-color: {THEME.bg_darkest};
            color: {THEME.text_primary};
            border: none;
            font-family: "Consolas", "Cascadia Code", "Courier New", monospace;
            font-size: {TOKENS.fonts.md}px;
            selection-background-color: {THEME.selected};
            selection-color: {THEME.text_primary};
        }}
        QScrollBar:vertical {{
            background: {THEME.bg_dark};
            width: 12px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background: {THEME.scrollbar};
            min-height: 20px;
            border-radius: {TOKENS.radii.md}px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {THEME.scrollbar_hover};
        }}
        QScrollBar:add-line:vertical,
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
            border-radius: {TOKENS.radii.md}px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {THEME.scrollbar_hover};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
    """

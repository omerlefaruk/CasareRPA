"""
YAML Syntax Highlighter for CasareRPA Expression Editor.

Provides VSCode Dark+ style syntax highlighting for YAML content.

Colors follow VSCode Dark+ theme:
- Keys (#9CDCFE): key:
- Strings (#CE9178): "string value"
- Numbers (#B5CEA8): integers, floats
- Keywords (#569CD6): true, false, null
- Comments (#6A9955): # comments
- Anchors/Aliases (#C586C0): &anchor, *alias
- Tags (#4EC9B0): !!str, !tag
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

from casare_rpa.presentation.canvas.ui.theme import Theme


class YamlHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for YAML code with VSCode Dark+ colors.

    Highlights:
    - Keys (key:)
    - String values
    - Numbers
    - Boolean/Null
    - Comments
    - Anchors (&) and Aliases (*)
    - Tags (!)
    - Variable references {{var}}

    Usage:
        editor = QPlainTextEdit()
        highlighter = YamlHighlighter(editor.document())
    """

    def __init__(self, document: QTextDocument = None) -> None:
        """
        Initialize the YAML syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)

        self._theme_colors = Theme.get_colors()
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
            "comment": QColor(self._theme_colors.syntax_comment),
            "anchor": QColor(self._theme_colors.syntax_keyword),
            "tag": QColor(self._theme_colors.syntax_variable),
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

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(syntax_colors["keyword"])
        self._formats["keyword"] = keyword_format

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(syntax_colors["comment"])
        comment_format.setFontItalic(True)
        self._formats["comment"] = comment_format

        # Anchor/Alias format
        anchor_format = QTextCharFormat()
        anchor_format.setForeground(syntax_colors["anchor"])
        self._formats["anchor"] = anchor_format

        # Tag format
        tag_format = QTextCharFormat()
        tag_format.setForeground(syntax_colors["tag"])
        self._formats["tag"] = tag_format

        # Variable reference format
        variable_format = QTextCharFormat()
        variable_format.setForeground(syntax_colors["variable"])
        variable_format.setFontWeight(QFont.Weight.Bold)
        self._formats["variable"] = variable_format

    def _create_rules(self) -> None:
        """Create highlighting rules."""
        # Comments
        self._rules.append((re.compile(r"#.*$"), "comment"))

        # Keys (key:) - standard
        self._rules.append((re.compile(r"^(\s*[\w\-\.]+):", re.MULTILINE), "key"))
        # Keys with quotes
        self._rules.append((re.compile(r'^(\s*"[^"]*"):', re.MULTILINE), "key"))
        self._rules.append((re.compile(r"^(\s*'[^']*'):", re.MULTILINE), "key"))

        # String values (double quotes)
        self._rules.append((re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"'), "string"))
        # String values (single quotes)
        self._rules.append((re.compile(r"'[^'\\]*(?:\\.[^'\\]*)*'"), "string"))

        # Numbers
        self._rules.append((re.compile(r"\b\d+(\.\d+)?\b"), "number"))

        # Keywords (true, false, null)
        keywords = ["true", "false", "null", "yes", "no", "on", "off"]
        for word in keywords:
            pattern = re.compile(rf"\b{word}\b", re.IGNORECASE)
            self._rules.append((pattern, "keyword"))

        # Anchors/Aliases
        self._rules.append((re.compile(r"&[\w\-]+"), "anchor"))
        self._rules.append((re.compile(r"\*[\w\-]+"), "anchor"))

        # Tags
        self._rules.append((re.compile(r"!!?[\w\-]+"), "tag"))

        # CasareRPA Variable syntax: {{variable_name}}
        self._rules.append((re.compile(r"\{\{[^}]+\}\}"), "variable"))

    def highlightBlock(self, text: str) -> None:
        """Apply highlighting rules to a block of text."""
        for pattern, format_name in self._rules:
            format_obj = self._formats[format_name]
            for match in pattern.finditer(text):
                # For keys, only highlight the key part, not the colon
                if format_name == "key":
                    start, end = match.span(1)
                else:
                    start, end = match.span()
                self.setFormat(start, end - start, format_obj)


def get_yaml_editor_stylesheet() -> str:
    """Get the CSS stylesheet for YAML editor."""
    return f"""
        QPlainTextEdit {{
            background-color: {THEME.bg_darkest};
            color: {THEME.text_primary};
            selection-background-color: {THEME.selected};
            selection-color: {THEME.text_primary};
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 13px;
            border: none;
        }}
    """

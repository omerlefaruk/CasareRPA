"""
Markdown Syntax Highlighter for CasareRPA.

Provides VSCode Dark+ style syntax highlighting for Markdown content.

Colors (VSCode Dark+):
- Headings: #569CD6 (blue)
- Bold: #CE9178 (orange-brown)
- Italic: #9CDCFE (light blue)
- Links: #4EC9B0 (teal)
- Code: #D4D4D4 on darker bg
- Lists: #C586C0 (purple)
"""

import re

from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS


class MarkdownHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for Markdown content with VSCode Dark+ colors.

    Highlights:
    - Headings (# ## ### etc.)
    - Bold (**text** or __text__)
    - Italic (*text* or _text_)
    - Links [text](url)
    - Inline code `code`
    - Code blocks ```
    - Lists (- item, 1. item)
    - Blockquotes (> text)

    Usage:
        editor = QPlainTextEdit()
        highlighter = MarkdownHighlighter(editor.document())
    """

    def __init__(self, document: QTextDocument | None = None) -> None:
        """
        Initialize the Markdown syntax highlighter.

        Args:
            document: Optional QTextDocument to highlight
        """
        super().__init__(document)

        self._theme_colors = THEME
        self._formats = {}
        self._create_formats()

        # State for multi-line code blocks
        self._in_code_block = False

    def _get_syntax_color(self, element: str) -> QColor:
        """Get syntax color for markdown element from theme."""
        syntax_colors = {
            "heading": QColor(self._theme_colors.syntax_variable),
            "bold": QColor(self._theme_colors.syntax_string),
            "italic": QColor(self._theme_colors.syntax_keyword),
            "link": QColor(self._theme_colors.syntax_variable),
            "link_url": QColor(self._theme_colors.syntax_comment),
            "code": QColor(self._theme_colors.text_secondary),
            "code_bg": QColor(self._theme_colors.bg_component),
            "list": QColor(self._theme_colors.syntax_keyword),
            "blockquote": QColor(self._theme_colors.syntax_comment),
            "hr": QColor(self._theme_colors.text_muted),
        }
        return syntax_colors.get(element, QColor(self._theme_colors.text_primary))

    def _create_formats(self) -> None:
        """Create text formats for each Markdown element type."""
        # Heading format (H1-H6)
        heading_format = QTextCharFormat()
        heading_format.setForeground(self._get_syntax_color("heading"))
        heading_format.setFontWeight(QFont.Weight.Bold)
        self._formats["heading"] = heading_format

        # Bold format
        bold_format = QTextCharFormat()
        bold_format.setForeground(self._get_syntax_color("bold"))
        bold_format.setFontWeight(QFont.Weight.Bold)
        self._formats["bold"] = bold_format

        # Italic format
        italic_format = QTextCharFormat()
        italic_format.setForeground(self._get_syntax_color("italic"))
        italic_format.setFontItalic(True)
        self._formats["italic"] = italic_format

        # Link text format
        link_format = QTextCharFormat()
        link_format.setForeground(self._get_syntax_color("link"))
        link_format.setFontUnderline(True)
        self._formats["link"] = link_format

        # Link URL format
        link_url_format = QTextCharFormat()
        link_url_format.setForeground(self._get_syntax_color("link_url"))
        self._formats["link_url"] = link_url_format

        # Inline code format
        code_format = QTextCharFormat()
        code_format.setForeground(self._get_syntax_color("code"))
        code_format.setBackground(self._get_syntax_color("code_bg"))
        code_format.setFontFamily("Consolas")
        self._formats["code"] = code_format

        # Code block format
        code_block_format = QTextCharFormat()
        code_block_format.setForeground(self._get_syntax_color("code"))
        code_block_format.setBackground(self._get_syntax_color("code_bg"))
        code_block_format.setFontFamily("Consolas")
        self._formats["code_block"] = code_block_format

        # List marker format
        list_format = QTextCharFormat()
        list_format.setForeground(self._get_syntax_color("list"))
        list_format.setFontWeight(QFont.Weight.Bold)
        self._formats["list"] = list_format

        # Blockquote format
        blockquote_format = QTextCharFormat()
        blockquote_format.setForeground(self._get_syntax_color("blockquote"))
        blockquote_format.setFontItalic(True)
        self._formats["blockquote"] = blockquote_format

        # Horizontal rule format
        hr_format = QTextCharFormat()
        hr_format.setForeground(self._get_syntax_color("hr"))
        self._formats["hr"] = hr_format

        # CasareRPA Variable format ({{var}})
        variable_format = QTextCharFormat()
        variable_format.setForeground(
            self._get_syntax_color("bold")
        )  # Use bold color for variables
        variable_format.setFontWeight(QFont.Weight.Bold)
        self._formats["variable"] = variable_format

    def highlightBlock(self, text: str) -> None:
        """
        Highlight a block of Markdown text.

        Args:
            text: The text block to highlight
        """
        if not text:
            return

        # Track highlighted positions to avoid overlapping
        highlighted = [False] * len(text)

        # Check for code block state (``` blocks)
        previous_state = self.previousBlockState()
        in_code_block = previous_state == 1

        # Code block start/end
        code_fence_pattern = re.compile(r"^```")
        if code_fence_pattern.match(text):
            self.setFormat(0, len(text), self._formats["code_block"])
            # Toggle state
            self.setCurrentBlockState(0 if in_code_block else 1)
            return

        if in_code_block:
            self.setFormat(0, len(text), self._formats["code_block"])
            self.setCurrentBlockState(1)
            return

        self.setCurrentBlockState(0)

        # Headings: # ## ### etc.
        heading_pattern = re.compile(r"^(#{1,6})\s+(.*)$")
        match = heading_pattern.match(text)
        if match:
            self.setFormat(0, len(text), self._formats["heading"])
            for i in range(len(text)):
                highlighted[i] = True
            return  # Heading takes the whole line

        # Horizontal rule: --- or *** or ___
        hr_pattern = re.compile(r"^(\*{3,}|-{3,}|_{3,})$")
        if hr_pattern.match(text):
            self.setFormat(0, len(text), self._formats["hr"])
            return

        # Blockquote: > text
        blockquote_pattern = re.compile(r"^>\s*")
        match = blockquote_pattern.match(text)
        if match:
            self.setFormat(0, len(text), self._formats["blockquote"])
            return

        # List markers: - item or * item or 1. item
        list_pattern = re.compile(r"^(\s*)(-|\*|\+|\d+\.)\s")
        match = list_pattern.match(text)
        if match:
            marker_start = match.start(2)
            marker_end = match.end(2)
            self.setFormat(marker_start, marker_end - marker_start, self._formats["list"])
            for i in range(marker_start, marker_end):
                if i < len(highlighted):
                    highlighted[i] = True

        # Bold: **text** or __text__
        bold_pattern = re.compile(r"(\*\*|__)(.+?)\1")
        for match in bold_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["bold"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Italic: *text* or _text_ (but not ** or __)
        italic_pattern = re.compile(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)|(?<!_)_(?!_)(.+?)(?<!_)_(?!_)"
        )
        for match in italic_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["italic"])
                for i in range(start, min(start + length, len(highlighted))):
                    highlighted[i] = True

        # Links: [text](url)
        link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        for match in link_pattern.finditer(text):
            # Highlight link text
            text_start = match.start(1)
            text_length = len(match.group(1))
            self.setFormat(match.start(), 1, self._formats["link"])  # [
            self.setFormat(text_start, text_length, self._formats["link"])
            self.setFormat(text_start + text_length, 2, self._formats["link"])  # ](

            # Highlight URL
            url_start = match.start(2)
            url_length = len(match.group(2))
            self.setFormat(url_start, url_length, self._formats["link_url"])
            self.setFormat(url_start + url_length, 1, self._formats["link_url"])  # )

            for i in range(match.start(), match.end()):
                if i < len(highlighted):
                    highlighted[i] = True

        # Inline code: `code`
        code_pattern = re.compile(r"`([^`]+)`")
        for match in code_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            if not any(highlighted[start : start + length]):
                self.setFormat(start, length, self._formats["code"])

        # CasareRPA Variable references {{var}}
        variable_pattern = re.compile(r"\{\{[^}]+\}\}")
        for match in variable_pattern.finditer(text):
            start = match.start()
            length = match.end() - start
            self.setFormat(start, length, self._formats["variable"])
            # We don't necessarily need to mark it as highlighted for MD as it can overlap with other things ideally
            # but for safety against other regexes:
            for i in range(start, min(start + length, len(highlighted))):
                highlighted[i] = True


def get_markdown_editor_stylesheet() -> str:
    """
    Get CSS stylesheet for QPlainTextEdit with Markdown editing.

    Returns:
        CSS stylesheet string for dark theme Markdown editor
    """
    from casare_rpa.presentation.canvas.theme_system import THEME

    c = THEME
    return f"""
        QPlainTextEdit {{
            background-color: {c.bg_canvas};
            color: {c.text_primary};
            border: none;
            font-family: "Segoe UI", "SF Pro Text", sans-serif;
            font-size: {TOKENS.typography.body}px;
            selection-background-color: {c.bg_selected};
            selection-color: {THEME.text_primary};
            line-height: 1.5;
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

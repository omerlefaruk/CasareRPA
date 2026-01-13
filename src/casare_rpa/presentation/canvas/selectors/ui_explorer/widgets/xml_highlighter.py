"""
XML Syntax Highlighter for UI Explorer.

QSyntaxHighlighter subclass that provides syntax coloring for
XML/selector preview text in the SelectorPreviewPanel.

Color scheme:
- Tags: Blue (#3b82f6)
- Attributes: Cyan (#22d3ee)
- Values: Orange (#f97316)
- Comments: Gray italic
"""

import re

from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument)


class XMLHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for XML/selector preview.

    Highlights:
    - Tag names: <html>, </button>, <input />
    - Attribute names: class=, id=, name=
    - Attribute values: 'value', "value"
    - Comments: <!-- comment -->

    Usage:
        text_edit = QTextEdit()
        highlighter = XMLHighlighter(text_edit.document())
    """

    # Color constants
    TAG_COLOR = QColor("#3b82f6")  # Blue
    ATTR_NAME_COLOR = QColor("#22d3ee")  # Cyan
    ATTR_VALUE_COLOR = QColor("#f97316")  # Orange
    COMMENT_COLOR = QColor("#6b7280")  # Gray
    BRACKET_COLOR = QColor("#a855f7")  # Purple for < > / =

    def __init__(self, document: QTextDocument | None = None) -> None:
        """
        Initialize the XML highlighter.

        Args:
            document: QTextDocument to highlight
        """
        super().__init__(document)

        self._highlighting_rules: list[tuple[re.Pattern, QTextCharFormat]] = []
        self._setup_formats()
        self._setup_rules()

    def _setup_formats(self) -> None:
        """Create text formats for different syntax elements."""
        # Tag format (blue)
        self._tag_format = QTextCharFormat()
        self._tag_format.setForeground(self.TAG_COLOR)
        self._tag_format.setFontWeight(QFont.Weight.Bold)

        # Attribute name format (cyan)
        self._attr_name_format = QTextCharFormat()
        self._attr_name_format.setForeground(self.ATTR_NAME_COLOR)

        # Attribute value format (orange)
        self._attr_value_format = QTextCharFormat()
        self._attr_value_format.setForeground(self.ATTR_VALUE_COLOR)

        # Comment format (gray italic)
        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(self.COMMENT_COLOR)
        self._comment_format.setFontItalic(True)

        # Bracket format (purple)
        self._bracket_format = QTextCharFormat()
        self._bracket_format.setForeground(self.BRACKET_COLOR)

    def _setup_rules(self) -> None:
        """Setup highlighting rules."""
        # Order matters - later rules override earlier ones

        # Rule 1: Brackets and special chars < > / =
        # Match individual brackets
        self._highlighting_rules.append((re.compile(r"[<>/=]"), self._bracket_format))

        # Rule 2: Tag names (after < or </)
        # Matches: <tagname or </tagname
        self._highlighting_rules.append(
            (
                re.compile(r"(?<=<)/?\s*([a-zA-Z_][a-zA-Z0-9_\-]*)", re.IGNORECASE),
                self._tag_format)
        )

        # Rule 3: Attribute names (word followed by =)
        # Matches: attr=
        self._highlighting_rules.append(
            (
                re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_\-]*)(?=\s*=)"),
                self._attr_name_format)
        )

        # Rule 4: Attribute values in single quotes
        # Matches: 'value'
        self._highlighting_rules.append((re.compile(r"'[^']*'"), self._attr_value_format))

        # Rule 5: Attribute values in double quotes
        # Matches: "value"
        self._highlighting_rules.append((re.compile(r'"[^"]*"'), self._attr_value_format))

        # Rule 6: Comments
        # Matches: <!-- comment -->
        self._highlighting_rules.append(
            (re.compile(r"<!--.*?-->", re.DOTALL), self._comment_format)
        )

    def highlightBlock(self, text: str) -> None:
        """
        Apply highlighting to a block of text.

        Args:
            text: The text block to highlight
        """
        if not text:
            return

        # Apply each rule
        for pattern, fmt in self._highlighting_rules:
            for match in pattern.finditer(text):
                # If there's a group, use the group; otherwise use full match
                if match.lastindex and match.lastindex >= 1:
                    start = match.start(1)
                    length = match.end(1) - match.start(1)
                else:
                    start = match.start()
                    length = match.end() - match.start()

                self.setFormat(start, length, fmt)

        # Handle multi-line comments
        self._handle_multiline_comments(text)

    def _handle_multiline_comments(self, text: str) -> None:
        """
        Handle multi-line XML comments.

        Args:
            text: Current text block
        """
        # Comment start/end patterns
        comment_start = re.compile(r"<!--")
        comment_end = re.compile(r"-->")

        # Block states:
        # 0 = normal
        # 1 = inside comment

        self.setCurrentBlockState(0)
        start_index = 0

        if self.previousBlockState() != 1:
            # Not continuing a comment, look for comment start
            match = comment_start.search(text)
            if match:
                start_index = match.start()
            else:
                return  # No comment in this block
        else:
            # Continuing a comment from previous block
            pass

        while start_index >= 0:
            # Look for comment end
            end_match = comment_end.search(text, start_index)

            if end_match:
                # Found end of comment
                comment_length = end_match.end() - start_index
                self.setFormat(start_index, comment_length, self._comment_format)

                # Look for next comment start
                next_start = comment_start.search(text, end_match.end())
                if next_start:
                    start_index = next_start.start()
                else:
                    break
            else:
                # Comment continues to end of block
                self.setCurrentBlockState(1)
                comment_length = len(text) - start_index
                self.setFormat(start_index, comment_length, self._comment_format)
                break

    def set_tag_color(self, color: QColor) -> None:
        """
        Set custom tag color.

        Args:
            color: QColor for tag names
        """
        self._tag_format.setForeground(color)
        self.rehighlight()

    def set_attr_name_color(self, color: QColor) -> None:
        """
        Set custom attribute name color.

        Args:
            color: QColor for attribute names
        """
        self._attr_name_format.setForeground(color)
        self.rehighlight()

    def set_attr_value_color(self, color: QColor) -> None:
        """
        Set custom attribute value color.

        Args:
            color: QColor for attribute values
        """
        self._attr_value_format.setForeground(color)
        self.rehighlight()

    def set_comment_color(self, color: QColor) -> None:
        """
        Set custom comment color.

        Args:
            color: QColor for comments
        """
        self._comment_format.setForeground(color)
        self.rehighlight()

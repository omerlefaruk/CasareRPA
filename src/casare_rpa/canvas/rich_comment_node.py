"""
Rich Comment Node

Enhanced comment node with rich text formatting, colors, and styling options.
"""

from PySide6.QtWidgets import QTextEdit, QColorDialog, QFontDialog
from PySide6.QtGui import QTextCharFormat, QFont, QColor, QTextCursor
from PySide6.QtCore import Qt
from loguru import logger

from .base_visual_node import VisualNode


class VisualRichCommentNode(VisualNode):
    """
    Enhanced visual comment node with rich text formatting.

    Features:
    - Rich text (bold, italic, underline)
    - Text colors
    - Font sizes
    - Lists and formatting
    - Markdown-style shortcuts
    """

    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "Rich Comment"
    NODE_CATEGORY = "basic"

    def __init__(self) -> None:
        """Initialize rich comment node."""
        super().__init__()

        # Add rich text input
        self.add_text_input("comment", "Comment", tab="properties")

        # Comment style properties
        self.create_property("comment_color", "#e0e0e0", widget_type=0, tab="style")
        self.create_property("background_color", "#2b2b2b", widget_type=0, tab="style")
        self.create_property("font_size", 11, widget_type=2, tab="style")
        self.create_property("bold", False, widget_type=1, tab="style")
        self.create_property("italic", False, widget_type=1, tab="style")

        logger.info("Rich Comment node created")

    def setup_ports(self) -> None:
        """Setup ports for comment node."""
        # Comments don't need ports
        pass


class VisualStickyNoteNode(VisualNode):
    """
    Sticky note style comment node.

    Features:
    - Colored sticky note appearance
    - Predefined color themes
    - Large text area
    - No execution ports
    """

    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "Sticky Note"
    NODE_CATEGORY = "basic"

    # Sticky note color themes
    THEMES = {
        'yellow': {'bg': '#FFF59D', 'text': '#000000'},
        'pink': {'bg': '#F48FB1', 'text': '#000000'},
        'blue': {'bg': '#81D4FA', 'text': '#000000'},
        'green': {'bg': '#A5D6A7', 'text': '#000000'},
        'orange': {'bg': '#FFAB91', 'text': '#000000'},
        'purple': {'bg': '#CE93D8', 'text': '#000000'},
    }

    def __init__(self) -> None:
        """Initialize sticky note node."""
        super().__init__()

        # Add text input
        self.add_text_input("note", "Note", tab="properties")

        # Theme selection
        theme_options = list(self.THEMES.keys())
        self.create_property("theme", "yellow", widget_type=3, tab="style")

        # Apply sticky note styling
        self._apply_sticky_style()

        logger.info("Sticky Note node created")

    def setup_ports(self) -> None:
        """Setup ports for sticky note."""
        # Sticky notes don't need ports
        pass

    def _apply_sticky_style(self):
        """Apply sticky note visual styling."""
        theme_name = self.get_property("theme") or "yellow"
        theme = self.THEMES.get(theme_name, self.THEMES['yellow'])

        # Set node colors to match sticky note
        bg_color = QColor(theme['bg'])
        self.set_color(bg_color.red(), bg_color.green(), bg_color.blue())

        # Set border to slightly darker
        border = bg_color.darker(120)
        self.model.border_color = (border.red(), border.green(), border.blue(), 255)

        # Set text color
        text_color = QColor(theme['text'])
        self.model.text_color = (text_color.red(), text_color.green(), text_color.blue(), 255)


class VisualHeaderCommentNode(VisualNode):
    """
    Large header comment for section titles.

    Features:
    - Large, bold text
    - Centered alignment
    - Underline
    - Color themes
    """

    __identifier__ = "casare_rpa.basic"
    NODE_NAME = "Section Header"
    NODE_CATEGORY = "basic"

    def __init__(self) -> None:
        """Initialize header comment node."""
        super().__init__()

        # Add text input
        self.add_text_input("header", "Section Title", tab="properties")

        # Style properties
        self.create_property("header_color", "#60a5fa", widget_type=0, tab="style")
        self.create_property("font_size", 16, widget_type=2, tab="style")
        self.create_property("show_underline", True, widget_type=1, tab="style")

        logger.info("Section Header node created")

    def setup_ports(self) -> None:
        """Setup ports for header."""
        # Headers don't need ports
        pass


def create_markdown_comment(text: str) -> str:
    """
    Convert markdown-style text to HTML for rich comments.

    Supported syntax:
    - **bold** or __bold__
    - *italic* or _italic_
    - # Heading
    - - List item
    - [link](url)

    Args:
        text: Markdown-style text

    Returns:
        HTML string
    """
    import re

    # Convert bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)

    # Convert italic
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.*?)_', r'<i>\1</i>', text)

    # Convert headings
    text = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)

    # Convert lists
    text = re.sub(r'^- (.*?)$', r'<li>\1</li>', text, flags=re.MULTILINE)

    # Convert links
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

    # Wrap in HTML
    html = f"""
    <html>
    <body style="color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif;">
        {text}
    </body>
    </html>
    """

    return html


def get_comment_shortcuts() -> str:
    """
    Get help text for comment formatting shortcuts.

    Returns:
        Help text string
    """
    return """
    Comment Formatting Shortcuts:

    **Bold Text**: **text** or __text__
    *Italic Text*: *text* or _text_

    # Large Heading
    ## Medium Heading
    ### Small Heading

    - List item
    - Another item

    [Link Text](https://url.com)
    """

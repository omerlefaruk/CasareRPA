"""
Markdown Editor for CasareRPA Expression Editors.

Provides a Markdown editor with:
- Horizontal split: edit pane (left) + preview pane (right, toggleable)
- Toolbar with formatting buttons
- Markdown syntax highlighting
- Keyboard shortcuts for common actions
"""

from typing import Any, Optional

from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QTextBrowser,
    QSplitter,
    QPushButton,
)

from loguru import logger

from casare_rpa.presentation.canvas.ui.theme import Theme
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.base_editor import (
    BaseExpressionEditor,
    EditorType,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.syntax.markdown_highlighter import (
    MarkdownHighlighter,
    get_markdown_editor_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor.widgets.toolbar import (
    EditorToolbar,
)


class MarkdownEditor(BaseExpressionEditor):
    """
    Markdown editor with preview for email bodies and rich content.

    Features:
    - Side-by-side edit/preview (toggleable)
    - Toolbar: bold, italic, heading, link, list (bullet/numbered), code
    - Markdown syntax highlighting
    - Preview renders HTML via QTextBrowser
    - Keyboard shortcuts: Ctrl+B (bold), Ctrl+I (italic), Ctrl+K (link)
    - Variable insertion support

    Usage:
        editor = MarkdownEditor()
        editor.set_value("# Hello\\n\\nThis is **bold** text.")
        content = editor.get_value()
    """

    PREVIEW_DELAY_MS = 300  # Debounce delay for preview updates

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Markdown editor.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._editor_type = EditorType.MARKDOWN
        self._preview_visible = True
        self._preview_timer: Optional[QTimer] = None

        self._setup_ui()
        self._setup_toolbar()
        self._setup_shortcuts()
        self._connect_signals()
        self._apply_styles()

        logger.debug("MarkdownEditor initialized")

    def _setup_ui(self) -> None:
        """Set up the editor UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        self._toolbar = EditorToolbar()
        layout.addWidget(self._toolbar)

        # Splitter with edit and preview panes
        self._splitter = QSplitter(Qt.Orientation.Horizontal)

        # Edit pane
        self._edit_pane = QPlainTextEdit()
        self._edit_pane.setPlaceholderText("Enter Markdown content...")
        self._edit_pane.setTabStopDistance(40)  # 4 spaces worth

        # Syntax highlighter
        self._highlighter = MarkdownHighlighter(self._edit_pane.document())

        # Preview pane
        self._preview_pane = QTextBrowser()
        self._preview_pane.setOpenExternalLinks(True)

        self._splitter.addWidget(self._edit_pane)
        self._splitter.addWidget(self._preview_pane)
        self._splitter.setSizes([300, 300])

        layout.addWidget(self._splitter)

        # Preview update timer (debounce)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(self.PREVIEW_DELAY_MS)
        self._preview_timer.timeout.connect(self._update_preview)

    def _setup_toolbar(self) -> None:
        """Set up toolbar with formatting buttons."""
        self._toolbar.add_action("B", "Bold (Ctrl+B)", self._toggle_bold)
        self._toolbar.add_action("I", "Italic (Ctrl+I)", self._toggle_italic)
        self._toolbar.add_separator()
        self._toolbar.add_action("H", "Heading", self._insert_heading)
        self._toolbar.add_action("L", "Link (Ctrl+K)", self._insert_link)
        self._toolbar.add_separator()
        self._toolbar.add_action("-", "Bullet List", self._insert_bullet_list)
        self._toolbar.add_action("1.", "Numbered List", self._insert_numbered_list)
        self._toolbar.add_separator()
        self._toolbar.add_action("`", "Code", self._insert_code)

        # Add preview toggle on the right
        self._toolbar.add_stretch()
        self._preview_toggle_btn = self._toolbar.add_action(
            "P",
            "Toggle Preview",
            self._toggle_preview,
        )

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Bold: Ctrl+B
        bold_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        bold_shortcut.activated.connect(self._toggle_bold)

        # Italic: Ctrl+I
        italic_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)
        italic_shortcut.activated.connect(self._toggle_italic)

        # Link: Ctrl+K
        link_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        link_shortcut.activated.connect(self._insert_link)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._edit_pane.textChanged.connect(self._on_text_changed)

    def _apply_styles(self) -> None:
        """Apply THEME styling."""
        c = Theme.get_colors()

        # Edit pane styling
        self._edit_pane.setStyleSheet(get_markdown_editor_stylesheet())

        # Preview pane styling
        self._preview_pane.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {c.background_alt};
                color: {c.text_primary};
                border: none;
                padding: 12px;
                font-family: "Segoe UI", "SF Pro Text", sans-serif;
                font-size: 13px;
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
        """)

        # Splitter styling
        self._splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {c.border};
                width: 2px;
            }}
            QSplitter::handle:hover {{
                background: {c.accent};
            }}
        """)

    # =========================================================================
    # BaseExpressionEditor Implementation
    # =========================================================================

    def get_value(self) -> str:
        """Get the current Markdown content."""
        return self._edit_pane.toPlainText()

    def set_value(self, value: str) -> None:
        """Set the Markdown content."""
        self._edit_pane.setPlainText(value)
        self._update_preview()

    def insert_at_cursor(self, text: str) -> None:
        """Insert text at the current cursor position."""
        cursor = self._edit_pane.textCursor()
        cursor.insertText(text)
        self._edit_pane.setTextCursor(cursor)

    def get_cursor_position(self) -> int:
        """Get the current cursor position."""
        return self._edit_pane.textCursor().position()

    def set_focus(self) -> None:
        """Set focus to the edit pane."""
        self._edit_pane.setFocus()

    # =========================================================================
    # Formatting Actions
    # =========================================================================

    @Slot()
    def _toggle_bold(self) -> None:
        """Toggle bold formatting around selection or insert bold markers."""
        self._wrap_selection("**", "**")

    @Slot()
    def _toggle_italic(self) -> None:
        """Toggle italic formatting around selection or insert italic markers."""
        self._wrap_selection("*", "*")

    @Slot()
    def _insert_heading(self) -> None:
        """Insert heading marker at start of current line."""
        cursor = self._edit_pane.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)

        # Check if line already has heading markers
        cursor.movePosition(
            QTextCursor.MoveOperation.EndOfLine,
            QTextCursor.MoveMode.KeepAnchor,
        )
        line_text = cursor.selectedText()

        if line_text.startswith("### "):
            # Remove heading (cycle back)
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.movePosition(
                QTextCursor.MoveOperation.Right,
                QTextCursor.MoveMode.KeepAnchor,
                4,
            )
            cursor.removeSelectedText()
        elif line_text.startswith("## "):
            # Upgrade to H3
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.insertText("#")
        elif line_text.startswith("# "):
            # Upgrade to H2
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.insertText("#")
        else:
            # Add H1
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
            cursor.insertText("# ")

        self._edit_pane.setTextCursor(cursor)

    @Slot()
    def _insert_link(self) -> None:
        """Insert link syntax at cursor or wrap selection."""
        cursor = self._edit_pane.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.insertText(f"[{text}](url)")
            # Select "url" for easy replacement
            cursor.movePosition(
                QTextCursor.MoveOperation.Left,
                QTextCursor.MoveMode.MoveAnchor,
                1,
            )
            cursor.movePosition(
                QTextCursor.MoveOperation.Left,
                QTextCursor.MoveMode.KeepAnchor,
                3,
            )
        else:
            cursor.insertText("[text](url)")
            # Select "text" for easy replacement
            cursor.movePosition(
                QTextCursor.MoveOperation.Left,
                QTextCursor.MoveMode.MoveAnchor,
                6,
            )
            cursor.movePosition(
                QTextCursor.MoveOperation.Left,
                QTextCursor.MoveMode.KeepAnchor,
                4,
            )
        self._edit_pane.setTextCursor(cursor)

    @Slot()
    def _insert_bullet_list(self) -> None:
        """Insert bullet list marker at start of current line."""
        cursor = self._edit_pane.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("- ")
        self._edit_pane.setTextCursor(cursor)

    @Slot()
    def _insert_numbered_list(self) -> None:
        """Insert numbered list marker at start of current line."""
        cursor = self._edit_pane.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine)
        cursor.insertText("1. ")
        self._edit_pane.setTextCursor(cursor)

    @Slot()
    def _insert_code(self) -> None:
        """Insert inline code or code block markers."""
        cursor = self._edit_pane.textCursor()
        if cursor.hasSelection():
            # Wrap selection in inline code
            self._wrap_selection("`", "`")
        else:
            # Insert code block
            cursor.insertText("```\n\n```")
            cursor.movePosition(
                QTextCursor.MoveOperation.Up,
                QTextCursor.MoveMode.MoveAnchor,
            )
            self._edit_pane.setTextCursor(cursor)

    def _wrap_selection(self, prefix: str, suffix: str) -> None:
        """Wrap the current selection with prefix and suffix."""
        cursor = self._edit_pane.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            # Check if already wrapped
            if text.startswith(prefix) and text.endswith(suffix):
                # Remove wrapping
                text = text[len(prefix) : -len(suffix)]
            else:
                # Add wrapping
                text = f"{prefix}{text}{suffix}"
            cursor.insertText(text)
        else:
            # Insert markers and position cursor between them
            pos = cursor.position()
            cursor.insertText(f"{prefix}{suffix}")
            cursor.setPosition(pos + len(prefix))
        self._edit_pane.setTextCursor(cursor)

    # =========================================================================
    # Preview
    # =========================================================================

    @Slot()
    def _toggle_preview(self) -> None:
        """Toggle the preview pane visibility."""
        self._preview_visible = not self._preview_visible
        self._preview_pane.setVisible(self._preview_visible)
        if self._preview_visible:
            self._update_preview()

    @Slot()
    def _on_text_changed(self) -> None:
        """Handle text changes - schedule preview update."""
        self._on_content_changed()
        if self._preview_visible and self._preview_timer:
            self._preview_timer.start()

    @Slot()
    def _update_preview(self) -> None:
        """Update the preview pane with rendered HTML."""
        markdown_text = self.get_value()
        html = self._markdown_to_html(markdown_text)
        self._preview_pane.setHtml(html)

    def _markdown_to_html(self, text: str) -> str:
        """
        Convert Markdown to HTML.

        Simple converter for common Markdown elements.
        For full Markdown support, consider using markdown2 or similar.

        Args:
            text: Markdown text

        Returns:
            HTML string
        """
        import re

        c = Theme.get_colors()

        # Escape HTML entities
        html = text.replace("&", "&amp;")
        html = html.replace("<", "&lt;")
        html = html.replace(">", "&gt;")

        # Code blocks (must come before other processing)
        html = re.sub(
            r"```(\w*)\n(.*?)```",
            lambda m: f'<pre style="background: {c.surface}; padding: 8px; border-radius: 4px; font-family: Consolas;">{m.group(2)}</pre>',
            html,
            flags=re.DOTALL,
        )

        # Inline code
        html = re.sub(
            r"`([^`]+)`",
            lambda m: f'<code style="background: {c.surface}; padding: 2px 4px; border-radius: 2px; font-family: Consolas;">{m.group(1)}</code>',
            html,
        )

        # Headings
        html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)

        # Bold and Italic
        html = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", html)
        html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
        html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

        # Links
        html = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            f'<a href="\\2" style="color: {c.info};">\\1</a>',
            html,
        )

        # Unordered lists
        html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)
        html = re.sub(r"(<li>.*</li>\n?)+", r"<ul>\g<0></ul>", html)

        # Numbered lists
        html = re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # Horizontal rules
        html = re.sub(r"^---+$", "<hr>", html, flags=re.MULTILINE)
        html = re.sub(r"^\*\*\*+$", "<hr>", html, flags=re.MULTILINE)

        # Blockquotes
        html = re.sub(
            r"^&gt; (.+)$",
            f'<blockquote style="border-left: 3px solid {c.border_light}; padding-left: 10px; color: {c.text_secondary};">\\1</blockquote>',
            html,
            flags=re.MULTILINE,
        )

        # Paragraphs (double newline)
        html = re.sub(r"\n\n", "</p><p>", html)
        html = f"<p>{html}</p>"

        # Wrap in styled container
        return f"""
        <html>
        <body style="color: {c.text_primary}; font-family: 'Segoe UI', sans-serif; line-height: 1.6;">
        {html}
        </body>
        </html>
        """

"""
Chat Area Widget for AI Assistant.

Provides a scrollable area with message bubbles for conversation display.
Supports user messages, AI responses, system notifications, and code blocks.

Features:
- User messages: Right-aligned, accent color
- AI messages: Left-aligned, surface color
- Code blocks for workflow JSON preview
- "Thinking..." animation during generation
- Auto-scroll to newest messages
"""

from enum import Enum
from typing import List, Optional

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QTimer,
    Qt,
)
from PySide6.QtGui import QFont, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class MessageType(Enum):
    """Types of chat messages."""

    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    CODE = "code"


class MessageBubble(QFrame):
    """
    Individual message bubble widget.

    Displays a single message with appropriate styling based on type.
    Supports text content and code blocks.

    States:
    - USER: Right-aligned, accent background
    - AI: Left-aligned, surface background
    - SYSTEM: Centered, muted text
    - CODE: Left-aligned, monospace font, dark background
    """

    def __init__(
        self,
        content: str,
        message_type: MessageType = MessageType.USER,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize message bubble.

        Args:
            content: Message text content
            message_type: Type of message (USER, AI, SYSTEM, CODE)
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._content = content
        self._message_type = message_type

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Set up the message UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Message label or text edit for code
        if self._message_type == MessageType.CODE:
            self._content_widget = QTextEdit()
            self._content_widget.setReadOnly(True)
            self._content_widget.setPlainText(self._content)
            self._content_widget.setMinimumHeight(60)
            self._content_widget.setMaximumHeight(200)

            # Set monospace font
            font = QFont("Consolas", 10)
            font.setStyleHint(QFont.StyleHint.Monospace)
            self._content_widget.setFont(font)
        else:
            self._content_widget = QLabel(self._content)
            self._content_widget.setWordWrap(True)
            self._content_widget.setTextFormat(Qt.TextFormat.PlainText)

        layout.addWidget(self._content_widget)

        # Set size policies
        if self._message_type in (MessageType.USER, MessageType.AI):
            self.setMaximumWidth(280)
        else:
            self.setMaximumWidth(320)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

    def _apply_style(self) -> None:
        """Apply styling based on message type."""
        colors = Theme.get_colors()
        radius = Theme.get_border_radius()

        if self._message_type == MessageType.USER:
            # User message: accent color, right-aligned
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {colors.accent};
                    border-radius: {radius.md}px;
                    border-top-right-radius: {radius.sm}px;
                }}
                QLabel {{
                    color: #FFFFFF;
                    background-color: transparent;
                    font-size: 12px;
                    line-height: 1.4;
                }}
            """)

        elif self._message_type == MessageType.AI:
            # AI message: surface color, left-aligned
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {colors.surface};
                    border: 1px solid {colors.border};
                    border-radius: {radius.md}px;
                    border-top-left-radius: {radius.sm}px;
                }}
                QLabel {{
                    color: {colors.text_primary};
                    background-color: transparent;
                    font-size: 12px;
                    line-height: 1.4;
                }}
            """)

        elif self._message_type == MessageType.SYSTEM:
            # System message: centered, muted
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: transparent;
                    border: none;
                }}
                QLabel {{
                    color: {colors.text_muted};
                    background-color: transparent;
                    font-size: 11px;
                    font-style: italic;
                }}
            """)

        elif self._message_type == MessageType.CODE:
            # Code block: dark background, monospace
            self.setStyleSheet(f"""
                MessageBubble {{
                    background-color: {colors.background};
                    border: 1px solid {colors.border};
                    border-radius: {radius.sm}px;
                }}
                QTextEdit {{
                    color: {colors.text_primary};
                    background-color: transparent;
                    border: none;
                    selection-background-color: {colors.selection};
                }}
            """)

    def get_content(self) -> str:
        """Get the message content."""
        return self._content

    def get_type(self) -> MessageType:
        """Get the message type."""
        return self._message_type


class ThinkingIndicator(QFrame):
    """
    Animated "Thinking..." indicator shown during AI generation.

    Displays animated dots to indicate processing.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize thinking indicator."""
        super().__init__(parent)
        self._dot_count = 0
        self._timer: Optional[QTimer] = None
        self._opacity = 1.0

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Set up the indicator UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # AI icon
        icon_label = QLabel("AI")
        icon_label.setObjectName("ThinkingIcon")
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Thinking text
        self._text_label = QLabel("Thinking")
        self._text_label.setObjectName("ThinkingText")
        layout.addWidget(self._text_label)

        # Animated dots
        self._dots_label = QLabel("")
        self._dots_label.setObjectName("ThinkingDots")
        self._dots_label.setFixedWidth(20)
        layout.addWidget(self._dots_label)

        layout.addStretch()

        self.setMaximumWidth(150)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def _apply_style(self) -> None:
        """Apply styling."""
        colors = Theme.get_colors()
        radius = Theme.get_border_radius()

        self.setStyleSheet(f"""
            ThinkingIndicator {{
                background-color: {colors.surface};
                border: 1px solid {colors.border};
                border-radius: {radius.md}px;
                border-top-left-radius: {radius.sm}px;
            }}
            #ThinkingIcon {{
                background-color: {colors.accent};
                color: #FFFFFF;
                border-radius: {radius.sm}px;
                font-size: 10px;
                font-weight: bold;
            }}
            #ThinkingText {{
                color: {colors.text_secondary};
                font-size: 12px;
                background-color: transparent;
            }}
            #ThinkingDots {{
                color: {colors.text_secondary};
                font-size: 12px;
                background-color: transparent;
            }}
        """)

    def start(self) -> None:
        """Start the animation."""
        if self._timer is None:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._update_dots)
        self._timer.start(400)
        self._dot_count = 0

    def stop(self) -> None:
        """Stop the animation."""
        if self._timer:
            self._timer.stop()
        self._dot_count = 0
        self._dots_label.setText("")

    def _update_dots(self) -> None:
        """Update animated dots."""
        self._dot_count = (self._dot_count + 1) % 4
        self._dots_label.setText("." * self._dot_count)


class ChatArea(QScrollArea):
    """
    Scrollable chat area with message history.

    Features:
    - Automatic scrolling to new messages
    - User/AI message differentiation
    - Thinking indicator during generation
    - Code block support
    - Message history retrieval
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize chat area."""
        super().__init__(parent)
        self._messages: List[MessageBubble] = []
        self._thinking_indicator: Optional[ThinkingIndicator] = None
        self._last_user_message: str = ""

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Set up the chat area UI."""
        # Configure scroll area
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget
        self._content = QWidget()
        self._content.setObjectName("ChatContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 8, 8, 8)
        self._content_layout.setSpacing(12)
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add spacer to push messages to top
        self._content_layout.addStretch()

        self.setWidget(self._content)

        # Thinking indicator (hidden)
        self._thinking_indicator = ThinkingIndicator()
        self._thinking_indicator.setVisible(False)

    def _apply_style(self) -> None:
        """Apply styling."""
        colors = Theme.get_colors()

        self.setStyleSheet(f"""
            ChatArea {{
                background-color: {colors.background_alt};
                border: none;
            }}
            #ChatContent {{
                background-color: {colors.background_alt};
            }}
            QScrollBar:vertical {{
                background-color: {colors.background_alt};
                width: 10px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {colors.secondary_hover};
                border-radius: 5px;
                min-height: 30px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {colors.border_light};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the chat."""
        QTimer.singleShot(50, self._do_scroll)

    def _do_scroll(self) -> None:
        """Perform the actual scroll."""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _add_message_widget(
        self, bubble: MessageBubble, align_right: bool = False
    ) -> None:
        """Add a message widget to the layout."""
        # Create container for alignment
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        if align_right:
            container_layout.addStretch()
            container_layout.addWidget(bubble)
        else:
            container_layout.addWidget(bubble)
            container_layout.addStretch()

        # Remove stretch, add message, re-add stretch
        self._content_layout.insertWidget(self._content_layout.count() - 1, container)

        self._messages.append(bubble)
        self._scroll_to_bottom()

    # ==================== Public API ====================

    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the chat.

        Args:
            content: Message text
        """
        self._last_user_message = content
        bubble = MessageBubble(content, MessageType.USER)
        self._add_message_widget(bubble, align_right=True)

    def add_ai_message(self, content: str) -> None:
        """
        Add an AI response message to the chat.

        Args:
            content: Message text
        """
        bubble = MessageBubble(content, MessageType.AI)
        self._add_message_widget(bubble, align_right=False)

    def add_system_message(self, content: str) -> None:
        """
        Add a system notification message to the chat.

        Args:
            content: Message text
        """
        bubble = MessageBubble(content, MessageType.SYSTEM)
        self._add_message_widget(bubble, align_right=False)

    def add_code_block(self, code: str) -> None:
        """
        Add a code block to the chat.

        Args:
            code: Code content (e.g., JSON)
        """
        bubble = MessageBubble(code, MessageType.CODE)
        self._add_message_widget(bubble, align_right=False)

    def show_thinking(self) -> None:
        """Show the thinking indicator."""
        if self._thinking_indicator:
            # Create container
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.addWidget(self._thinking_indicator)
            container_layout.addStretch()

            self._content_layout.insertWidget(
                self._content_layout.count() - 1, container
            )

            self._thinking_indicator.setVisible(True)
            self._thinking_indicator.start()
            self._scroll_to_bottom()

    def hide_thinking(self) -> None:
        """Hide the thinking indicator."""
        if self._thinking_indicator:
            self._thinking_indicator.stop()
            self._thinking_indicator.setVisible(False)

            # Remove from layout
            parent = self._thinking_indicator.parentWidget()
            if parent and parent != self._content:
                parent.setParent(None)
                parent.deleteLater()

            # Recreate thinking indicator for next use
            self._thinking_indicator = ThinkingIndicator()
            self._thinking_indicator.setVisible(False)

    def clear_messages(self) -> None:
        """Clear all messages from the chat."""
        # Remove all message widgets
        for _ in range(self._content_layout.count()):
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._messages.clear()
        self._last_user_message = ""

        # Re-add stretch
        self._content_layout.addStretch()

        # Add welcome message
        self.add_system_message("Welcome! Describe the workflow you want to create.")

    def get_last_user_message(self) -> str:
        """
        Get the last user message.

        Returns:
            Last user message text or empty string
        """
        return self._last_user_message

    def get_message_history(self) -> List[dict]:
        """
        Get all messages as a list of dicts.

        Returns:
            List of message dicts with 'type' and 'content' keys
        """
        return [
            {"type": msg.get_type().value, "content": msg.get_content()}
            for msg in self._messages
        ]

    def get_message_count(self) -> int:
        """
        Get the number of messages.

        Returns:
            Message count
        """
        return len(self._messages)

"""
Chat Area Widget for AI Assistant (ChatGPT-Style).

Clean messaging interface with:
- Minimalist bubble design like ChatGPT
- Subtle avatars
- Clean typography
- Animated "Thinking" state
- Smooth auto-scrolling
- Code block highlighting
"""

from enum import Enum

from PySide6.QtCore import (
    Qt,
    QTimer,
)
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

from casare_rpa.presentation.canvas.theme_system import THEME


class MessageType(Enum):
    """Types of chat messages."""

    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    CODE = "code"


class AvatarWidget(QFrame):
    """Minimalist circular avatar for ChatGPT-style."""

    def __init__(self, label: str, color: str, parent=None, size: int = 28):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._label = label
        self._color = color
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            AvatarWidget {{
                background-color: {self._color};
                border-radius: {self.width() // 2}px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self._label)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "color: white; font-weight: 600; font-size: 11px; background: transparent;"
        )
        layout.addWidget(label)


class MessageBubble(QFrame):
    """
    ChatGPT-style message bubble - clean and minimalist.
    """

    def __init__(
        self,
        content: str,
        message_type: MessageType = MessageType.USER,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._content = content
        self._message_type = message_type

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._setup_ui()

    def _setup_ui(self) -> None:
        colors = THEME

        # Main layout for the bubble row (Avatar + Content)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        if self._message_type == MessageType.USER:
            # User message: Right-aligned, no avatar, subtle background
            layout.addStretch()

            content_frame = QFrame()
            content_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.surface};
                    border-radius: 12px;
                }}
            """)
            content_layout = QVBoxLayout(content_frame)
            content_layout.setContentsMargins(12, 8, 12, 8)
            content_layout.setSpacing(2)

            self._content_widget = QLabel(self._content)
            self._content_widget.setWordWrap(True)
            self._content_widget.setTextFormat(Qt.TextFormat.RichText)
            self._content_widget.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._content_widget.setStyleSheet(
                f"color: {colors.text_primary}; font-size: 13px; line-height: 1.5; background: transparent;"
            )
            content_layout.addWidget(self._content_widget)

            layout.addWidget(content_frame)

        elif self._message_type == MessageType.AI:
            # AI message: Left-aligned with avatar, blue iMessage style
            avatar = AvatarWidget("AI", "#007AFF", size=28)  # iMessage blue
            layout.addWidget(avatar)
            layout.setAlignment(avatar, Qt.AlignmentFlag.AlignTop)

            content_frame = QFrame()
            content_frame.setStyleSheet("""
                QFrame {
                    background-color: #007AFF;
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                }
            """)
            content_layout = QVBoxLayout(content_frame)
            content_layout.setContentsMargins(12, 10, 12, 10)
            content_layout.setSpacing(2)

            self._content_widget = QLabel(self._content)
            self._content_widget.setWordWrap(True)
            self._content_widget.setTextFormat(Qt.TextFormat.RichText)
            self._content_widget.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._content_widget.setStyleSheet(
                "color: white; font-size: 13px; line-height: 1.5; background: transparent;"
            )
            content_layout.addWidget(self._content_widget)

            layout.addWidget(content_frame)
            layout.addStretch()

        elif self._message_type == MessageType.SYSTEM:
            layout.addStretch()
            lbl = QLabel(self._content)
            lbl.setStyleSheet(
                f"color: {colors.text_muted}; font-size: 12px; font-style: italic; background: transparent;"
            )
            layout.addWidget(lbl)
            layout.addStretch()

        elif self._message_type == MessageType.CODE:
            # Code block: Full width with monospace
            layout.addStretch()

            code_frame = QFrame()
            code_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.bg_elevated};
                    border: 1px solid {colors.border};
                    border-radius: 8px;
                }}
            """)
            code_layout = QVBoxLayout(code_frame)
            code_layout.setContentsMargins(12, 10, 12, 10)

            self._content_widget = QTextEdit()
            self._content_widget.setReadOnly(True)
            self._content_widget.setPlainText(self._content)
            self._content_widget.setMinimumHeight(60)
            self._content_widget.setMaximumHeight(250)
            self._content_widget.setStyleSheet(f"""
                QTextEdit {{
                    background-color: transparent;
                    border: none;
                    color: {colors.text_primary};
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    line-height: 1.4;
                }}
            """)
            code_layout.addWidget(self._content_widget)

            layout.addWidget(code_frame)
            layout.addStretch()

    def get_content(self) -> str:
        return self._content

    def get_type(self) -> MessageType:
        return self._message_type


class ThinkingIndicator(QFrame):
    """
    Minimalist animated 'Thinking' indicator.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Avatar
        self._avatar = AvatarWidget("AI", "#10A37F", size=28)
        layout.addWidget(self._avatar)
        layout.setAlignment(self._avatar, Qt.AlignmentFlag.AlignTop)

        # Dots container
        self._dots_label = QLabel("...")
        self._dots_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME.text_muted};
                font-size: 18px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        layout.addWidget(self._dots_label)
        layout.addStretch()

        # Animation timer for dots
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._dot_count = 0

    def _animate(self):
        self._dot_count = (self._dot_count + 1) % 4
        self._dots_label.setText("." * self._dot_count)

    def start(self):
        self._timer.start(350)

    def stop(self):
        self._timer.stop()


class ChatArea(QScrollArea):
    """
    Next-Gen Scrollable Chat Area.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._messages: list[MessageBubble] = []
        self._thinking_indicator: ThinkingIndicator | None = None
        self._last_user_message: str = ""

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content.setObjectName("ChatContent")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(16)  # More breathing room
        self._content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._content_layout.addStretch()
        self.setWidget(self._content)

        self._thinking_indicator = ThinkingIndicator()
        self._thinking_indicator.setVisible(False)
        self._content_layout.addWidget(self._thinking_indicator)

    def _apply_style(self) -> None:
        colors = THEME
        self.setStyleSheet(f"""
            ChatArea {{
                background-color: {colors.background};
                border: none;
            }}
            #ChatContent {{
                background-color: {colors.background};
            }}
            QScrollBar:vertical {{
                background-color: transparent;
                width: 6px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: rgba(255, 255, 255, 0.08);
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: rgba(255, 255, 255, 0.15);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                height: 0;
                background: none;
            }}
        """)

    def _scroll_to_bottom(self) -> None:
        # v2 policy: No animations - use instant scroll
        QTimer.singleShot(100, self._do_scroll)

    def _do_scroll(self) -> None:
        scrollbar = self.verticalScrollBar()
        # Instant scroll to bottom (no animation per v2 requirement)
        scrollbar.setValue(scrollbar.maximum())

    def _add_bubble(self, bubble: MessageBubble):
        # Insert before thinking indicator and stretch
        # Standard implementation for sticky-bottom behavior
        if self._thinking_indicator:
            self._content_layout.removeWidget(self._thinking_indicator)

        self._content_layout.addWidget(bubble)
        self._messages.append(bubble)

        if self._thinking_indicator:
            self._content_layout.addWidget(self._thinking_indicator)

        self._scroll_to_bottom()

    # --- Public API ---

    def add_user_message(self, content: str) -> None:
        self._last_user_message = content
        self._add_bubble(MessageBubble(content, MessageType.USER))

    def add_ai_message(self, content: str) -> None:
        self._add_bubble(MessageBubble(content, MessageType.AI))

    def add_system_message(self, content: str) -> None:
        self._add_bubble(MessageBubble(content, MessageType.SYSTEM))

    def add_code_block(self, code: str) -> None:
        self._add_bubble(MessageBubble(code, MessageType.CODE))

    def show_thinking(self) -> None:
        if self._thinking_indicator:
            self._thinking_indicator.setVisible(True)
            self._thinking_indicator.start()
            self._scroll_to_bottom()

    def hide_thinking(self) -> None:
        if self._thinking_indicator:
            self._thinking_indicator.stop()
            self._thinking_indicator.setVisible(False)

    def clear_messages(self) -> None:
        for msg in self._messages:
            msg.deleteLater()
        self._messages.clear()
        self._last_user_message = ""
        self.add_system_message("New conversation started.")

    def get_last_user_message(self) -> str:
        return self._last_user_message

    def get_message_count(self) -> int:
        return len(self._messages)

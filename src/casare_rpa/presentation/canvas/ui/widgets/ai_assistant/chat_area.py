"""
Chat Area Widget for AI Assistant (Next-Gen).

Premium messaging interface with:
- Rich text bubbles (Markdown-like support) (User & AI)
- Avatars and identity styling
- Glassmorphism effects and modern gradients
- Animated "Thinking" state with pulsing dots
- Timestamp/Status indicators
- Smooth auto-scrolling
- Code block highlighting support
"""

from enum import Enum
from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import (
    QTimer,
    Qt,
    QSize,
    QPropertyAnimation,
    QEasingCurve,
    QAbstractAnimation,
)
from PySide6.QtGui import (
    QFont,
    QColor,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QTextOption,
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
    QGraphicsOpacityEffect,
)

from casare_rpa.presentation.canvas.ui.theme import Theme


class MessageType(Enum):
    """Types of chat messages."""

    USER = "user"
    AI = "ai"
    SYSTEM = "system"
    CODE = "code"


class AvatarWidget(QFrame):
    """Circular avatar widget with initials or icon."""

    def __init__(self, label: str, color: str, parent=None, size: int = 32):
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
                border: 2px solid rgba(255, 255, 255, 0.1);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(self._label)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "color: white; font-weight: bold; font-size: 12px; background: transparent;"
        )
        layout.addWidget(label)


class MessageBubble(QFrame):
    """
    Premium message bubble with gradients, rich text, and shadows.
    """

    def __init__(
        self,
        content: str,
        message_type: MessageType = MessageType.USER,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._content = content
        self._message_type = message_type
        self._timestamp = datetime.now().strftime("%I:%M %p")

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._setup_ui()

    def _setup_ui(self) -> None:
        colors = Theme.get_colors()

        # Main layout for the bubble row (Avatar + Bubble)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # Bubble Container (The actual colored box)
        self._bubble_frame = QFrame()
        self._bubble_frame.setSizePolicy(
            QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum
        )
        self._bubble_frame.setMaximumWidth(400)  # Max width constraint

        bubble_layout = QVBoxLayout(self._bubble_frame)
        bubble_layout.setContentsMargins(14, 10, 14, 10)
        bubble_layout.setSpacing(4)

        # Content Text
        if self._message_type == MessageType.CODE:
            self._content_widget = QTextEdit()
            self._content_widget.setReadOnly(True)
            self._content_widget.setPlainText(self._content)
            self._content_widget.setMinimumHeight(60)
            self._content_widget.setMaximumHeight(300)
            self._content_widget.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(0, 0, 0, 0.3);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                    color: #e0e0e0;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                    padding: 8px;
                }
            """)
        else:
            self._content_widget = QLabel(self._content)
            self._content_widget.setWordWrap(True)
            self._content_widget.setTextFormat(
                Qt.TextFormat.RichText
            )  # Basic formatting
            self._content_widget.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._content_widget.setStyleSheet("background: transparent; padding: 0;")

            # Adjust styling based on type
            if self._message_type == MessageType.USER:
                self._content_widget.setStyleSheet(
                    "color: white; font-size: 13px; line-height: 1.4;"
                )
            else:
                self._content_widget.setStyleSheet(
                    f"color: {colors.text_primary}; font-size: 13px; line-height: 1.4;"
                )

        bubble_layout.addWidget(self._content_widget)

        # Timestamp (Footer)
        time_label = QLabel(self._timestamp)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        ts_color = (
            "rgba(255, 255, 255, 0.6)"
            if self._message_type == MessageType.USER
            else colors.text_muted
        )
        time_label.setStyleSheet(
            f"color: {ts_color}; font-size: 9px; background: transparent; margin-top: 2px;"
        )
        bubble_layout.addWidget(time_label)

        # Assemble the row
        if self._message_type == MessageType.USER:
            layout.addStretch()
            layout.addWidget(self._bubble_frame)

            # User Avatar (Initial 'U')
            avatar = AvatarWidget("U", colors.accent, size=32)
            layout.addWidget(avatar)
            layout.setAlignment(avatar, Qt.AlignmentFlag.AlignBottom)

            # Styling for User Bubble (Right)
            self._bubble_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.accent};
                    border-radius: 16px;
                    border-top-right-radius: 4px;
                }}
            """)

        elif self._message_type == MessageType.AI:
            # AI Avatar (Icon 'AI')
            avatar = AvatarWidget("AI", "#6C5CE7", size=32)  # Distinct purple for AI
            layout.addWidget(avatar)
            layout.setAlignment(avatar, Qt.AlignmentFlag.AlignBottom)

            layout.addWidget(self._bubble_frame)
            layout.addStretch()

            # Styling for AI Bubble (Left)
            self._bubble_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.surface};
                    border: 1px solid {colors.border};
                    border-radius: 16px;
                    border-top-left-radius: 4px;
                }}
            """)

        elif self._message_type == MessageType.SYSTEM:
            layout.addStretch()
            lbl = QLabel(f"✨ {self._content}")
            lbl.setStyleSheet(
                f"color: {colors.text_muted}; font-size: 11px; font-style: italic;"
            )
            layout.addWidget(lbl)
            layout.addStretch()
            self._bubble_frame.hide()  # We don't use the standard frame for system

        elif self._message_type == MessageType.CODE:
            # Just like AI but wider maybe?
            layout.addWidget(self._bubble_frame)
            layout.addStretch()
            self._bubble_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {colors.surface};
                    border: 1px solid {colors.border};
                    border-radius: 12px;
                }}
            """)

    def get_content(self) -> str:
        return self._content

    def get_type(self) -> MessageType:
        return self._message_type


class ThinkingIndicator(QFrame):
    """
    Fluid animated 'Thinking' bubble.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)

        # Avatar
        self._avatar = AvatarWidget("AI", "#6C5CE7", size=28)
        layout.addWidget(self._avatar)

        # Bubble Frame
        self._bubble = QFrame()
        self._bubble.setStyleSheet("""
            QFrame {
                background-color: rgba(108, 92, 231, 0.1);
                border-radius: 14px;
                border-top-left-radius: 4px;
                border: 1px solid rgba(108, 92, 231, 0.2);
            }
        """)
        self._bubble.setFixedSize(60, 28)

        # Dots Layout
        dots_layout = QHBoxLayout(self._bubble)
        dots_layout.setContentsMargins(0, 0, 0, 0)
        dots_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._dots = QLabel("...")
        self._dots.setStyleSheet(
            "color: #6C5CE7; font-weight: 900; font-size: 16px; padding-bottom: 8px;"
        )
        dots_layout.addWidget(self._dots)

        layout.addWidget(self._bubble)
        layout.addStretch()

        # Animation timer for dots
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._dot_count = 0

    def _animate(self):
        self._dot_count = (self._dot_count + 1) % 4
        self._dots.setText("." * self._dot_count)

    def start(self):
        self._timer.start(300)

    def stop(self):
        self._timer.stop()


class ChatArea(QScrollArea):
    """
    Next-Gen Scrollable Chat Area.
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._messages: List[MessageBubble] = []
        self._thinking_indicator: Optional[ThinkingIndicator] = None
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
        colors = Theme.get_colors()
        self.setStyleSheet("""
            ChatArea {
                background-color: transparent;
                border: none;
            }
            #ChatContent {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                height: 0;
                background: none;
            }
        """)

    def _scroll_to_bottom(self) -> None:
        QTimer.singleShot(100, self._do_scroll)

    def _do_scroll(self) -> None:
        scrollbar = self.verticalScrollBar()
        # Smooth scroll
        anim = QPropertyAnimation(scrollbar, b"value")
        anim.setDuration(300)
        anim.setStartValue(scrollbar.value())
        anim.setEndValue(scrollbar.maximum())
        anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        # Store ref to prevent GC
        self._scroll_anim = anim

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
        self.add_system_message("Welcome back to your workflow assistant.")

    def get_last_user_message(self) -> str:
        return self._last_user_message

    def get_message_count(self) -> int:
        return len(self._messages)

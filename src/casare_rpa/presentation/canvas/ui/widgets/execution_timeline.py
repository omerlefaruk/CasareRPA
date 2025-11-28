"""
Execution Timeline for CasareRPA.

Visual timeline showing node execution order and timing.
"""

from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QLabel,
    QPushButton,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont


@dataclass
class TimelineEvent:
    """Represents an event on the timeline."""

    node_id: str
    node_name: str
    event_type: str  # 'started', 'completed', 'error'
    timestamp: datetime
    duration_ms: Optional[float] = None
    error_message: Optional[str] = None


class TimelineBar(QWidget):
    """Individual timeline bar representing a node execution."""

    clicked = Signal(str)  # node_id

    def __init__(
        self,
        event: TimelineEvent,
        start_time: datetime,
        total_duration: float,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._event = event
        self._start_time = start_time
        self._total_duration = total_duration
        self._hovered = False

        self.setMinimumHeight(28)
        self.setMaximumHeight(28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        # Calculate position and width
        event_offset = (event.timestamp - start_time).total_seconds() * 1000
        self._x_offset = event_offset / total_duration if total_duration > 0 else 0
        self._width_ratio = (
            (event.duration_ms or 100) / total_duration if total_duration > 0 else 0.1
        )

    def paintEvent(self, event) -> None:
        """Paint the timeline bar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        margin = 2

        # Calculate bar position
        available_width = rect.width() - 2 * margin
        bar_x = margin + int(self._x_offset * available_width)
        bar_width = max(4, int(self._width_ratio * available_width))
        bar_height = rect.height() - 2 * margin

        # Determine color based on status
        if self._event.event_type == "error":
            color = QColor("#f44336")  # Red
        elif self._event.event_type == "completed":
            color = QColor("#4CAF50")  # Green
        else:
            color = QColor("#FFA500")  # Orange (running)

        if self._hovered:
            color = color.lighter(120)

        # Draw bar
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bar_x, margin, bar_width, bar_height, 3, 3)

        # Draw node name
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        text = self._event.node_name
        if self._event.duration_ms:
            text += f" ({self._event.duration_ms:.0f}ms)"

        text_rect = rect.adjusted(bar_x + 4, 0, 0, 0)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, text)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        # Show tooltip
        tooltip = f"{self._event.node_name}\n"
        tooltip += f"Status: {self._event.event_type}\n"
        if self._event.duration_ms:
            tooltip += f"Duration: {self._event.duration_ms:.2f}ms"
        if self._event.error_message:
            tooltip += f"\nError: {self._event.error_message}"
        self.setToolTip(tooltip)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._event.node_id)


class ExecutionTimeline(QWidget):
    """
    Visual timeline of workflow execution.

    Shows node executions as horizontal bars with timing information.

    Signals:
        node_clicked: Emitted when a node bar is clicked (node_id: str)
    """

    node_clicked = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._events: List[TimelineEvent] = []
        self._start_time: Optional[datetime] = None
        self._is_running = False

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Execution Timeline")
        title.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)

        self._duration_label = QLabel("Duration: --")
        self._duration_label.setStyleSheet("color: #888888;")
        header.addWidget(self._duration_label)

        header.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self.clear)
        header.addWidget(clear_btn)

        layout.addLayout(header)

        # Timeline area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._timeline_container = QWidget()
        self._timeline_layout = QVBoxLayout(self._timeline_container)
        self._timeline_layout.setContentsMargins(0, 0, 0, 0)
        self._timeline_layout.setSpacing(2)
        self._timeline_layout.addStretch()

        scroll.setWidget(self._timeline_container)
        layout.addWidget(scroll)

        # Time scale
        self._scale_widget = QWidget()
        self._scale_widget.setFixedHeight(20)
        layout.addWidget(self._scale_widget)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QWidget {
                background: #252525;
            }
            QScrollArea {
                background: #2b2b2b;
                border: 1px solid #3d3d3d;
            }
            QPushButton {
                background: #3c3f41;
                color: #cccccc;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: #4c4f51;
            }
        """)

    def _rebuild_timeline(self) -> None:
        """Rebuild the timeline display."""
        # Clear existing bars
        while self._timeline_layout.count() > 1:
            item = self._timeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._events or not self._start_time:
            return

        # Calculate total duration
        end_time = max(e.timestamp for e in self._events)
        if self._events:
            last_event = max(self._events, key=lambda e: e.timestamp)
            if last_event.duration_ms:
                from datetime import timedelta

                end_time = last_event.timestamp + timedelta(
                    milliseconds=last_event.duration_ms
                )

        total_duration = (end_time - self._start_time).total_seconds() * 1000

        # Update duration label
        self._duration_label.setText(f"Duration: {total_duration:.0f}ms")

        # Create bars for each event
        for event in self._events:
            if event.event_type in ("completed", "error"):
                bar = TimelineBar(event, self._start_time, total_duration)
                bar.clicked.connect(self.node_clicked.emit)
                self._timeline_layout.insertWidget(
                    self._timeline_layout.count() - 1, bar
                )

    # ==================== Public API ====================

    def start_execution(self) -> None:
        """Mark the start of execution."""
        self._events.clear()
        self._start_time = datetime.now()
        self._is_running = True
        self._rebuild_timeline()

    def add_event(
        self,
        node_id: str,
        node_name: str,
        event_type: str,
        duration_ms: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """
        Add an execution event.

        Args:
            node_id: Node ID
            node_name: Display name
            event_type: 'started', 'completed', or 'error'
            duration_ms: Execution duration in milliseconds
            error_message: Error message if failed
        """
        event = TimelineEvent(
            node_id=node_id,
            node_name=node_name,
            event_type=event_type,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            error_message=error_message,
        )
        self._events.append(event)
        self._rebuild_timeline()

    def end_execution(self) -> None:
        """Mark the end of execution."""
        self._is_running = False

    def clear(self) -> None:
        """Clear the timeline."""
        self._events.clear()
        self._start_time = None
        self._is_running = False
        self._duration_label.setText("Duration: --")
        self._rebuild_timeline()

    def get_events(self) -> List[TimelineEvent]:
        """Get all timeline events."""
        return self._events.copy()

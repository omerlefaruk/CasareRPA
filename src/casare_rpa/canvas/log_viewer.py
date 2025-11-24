"""
Execution Log Viewer for CasareRPA.

Provides a dockable panel showing workflow execution events, errors,
and node outputs in real-time.
"""

from datetime import datetime
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTextEdit,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QTextCursor, QColor

from ..core.events import Event, EventType
from loguru import logger


class ExecutionLogViewer(QWidget):
    """
    Dockable widget displaying workflow execution logs.
    
    Shows real-time events including:
    - Workflow start/stop
    - Node execution progress
    - Errors and warnings
    - Variable changes
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize log viewer.
        
        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        
        self._setup_ui()
        self._max_lines = 1000  # Limit log size
    
    def _setup_ui(self) -> None:
        """Setup user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Filter combo box
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("All Events", None)
        self.filter_combo.addItem("Workflow", "workflow")
        self.filter_combo.addItem("Nodes", "node")
        self.filter_combo.addItem("Errors", "error")
        self.filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_log)
        
        # Auto-scroll checkbox
        self.auto_scroll_btn = QPushButton("Auto-scroll: ON")
        self.auto_scroll_btn.setCheckable(True)
        self.auto_scroll_btn.setChecked(True)
        self.auto_scroll_btn.clicked.connect(self._on_auto_scroll_toggled)
        
        toolbar.addWidget(QLabel("Filter:"))
        toolbar.addWidget(self.filter_combo)
        toolbar.addStretch()
        toolbar.addWidget(self.auto_scroll_btn)
        toolbar.addWidget(clear_btn)
        
        layout.addLayout(toolbar)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        
        # Style the log area
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #3c3c3c;
            }
        """)
        
        layout.addWidget(self.log_text)
        
        # Event type colors
        self._event_colors = {
            EventType.WORKFLOW_STARTED: QColor(100, 180, 255),  # Blue
            EventType.WORKFLOW_COMPLETED: QColor(76, 175, 80),  # Green
            EventType.WORKFLOW_ERROR: QColor(244, 67, 54),  # Red
            EventType.WORKFLOW_STOPPED: QColor(255, 152, 0),  # Orange
            EventType.WORKFLOW_PAUSED: QColor(255, 193, 7),  # Yellow
            EventType.WORKFLOW_RESUMED: QColor(100, 180, 255),  # Blue
            EventType.NODE_STARTED: QColor(149, 117, 205),  # Purple
            EventType.NODE_COMPLETED: QColor(129, 199, 132),  # Light green
            EventType.NODE_ERROR: QColor(229, 115, 115),  # Light red
        }
        
        self._current_filter = None
        self._auto_scroll = True
    
    def _on_filter_changed(self, index: int) -> None:
        """Handle filter change."""
        self._current_filter = self.filter_combo.itemData(index)
        logger.debug(f"Log filter changed to: {self._current_filter}")
    
    def _on_auto_scroll_toggled(self, checked: bool) -> None:
        """Handle auto-scroll toggle."""
        self._auto_scroll = checked
        self.auto_scroll_btn.setText(f"Auto-scroll: {'ON' if checked else 'OFF'}")
    
    def _should_show_event(self, event: Event) -> bool:
        """
        Check if event should be displayed based on current filter.
        
        Args:
            event: Event to check
            
        Returns:
            True if event should be shown
        """
        if self._current_filter is None:
            return True
        
        event_name = event.event_type.name.lower()
        
        if self._current_filter == "workflow":
            return event_name.startswith("workflow")
        elif self._current_filter == "node":
            return event_name.startswith("node")
        elif self._current_filter == "error":
            return "error" in event_name
        
        return True
    
    def _format_timestamp(self, dt: datetime) -> str:
        """Format timestamp for display."""
        return dt.strftime("%H:%M:%S.%f")[:-3]  # Include milliseconds
    
    def _append_colored_text(self, text: str, color: QColor) -> None:
        """
        Append colored text to log.
        
        Args:
            text: Text to append
            color: Text color
        """
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        # Set text color
        format = cursor.charFormat()
        format.setForeground(color)
        cursor.setCharFormat(format)
        
        # Insert text
        cursor.insertText(text)
        
        # Scroll to end if auto-scroll enabled
        if self._auto_scroll:
            self.log_text.setTextCursor(cursor)
            self.log_text.ensureCursorVisible()
    
    @Slot(object)
    def log_event(self, event: Event) -> None:
        """
        Log an event to the viewer.
        
        Args:
            event: Event to log
        """
        # Check filter
        if not self._should_show_event(event):
            return
        
        # Format event
        timestamp = self._format_timestamp(event.timestamp)
        event_type = event.event_type.name
        
        # Get color for event type
        color = self._event_colors.get(event.event_type, QColor(212, 212, 212))
        
        # Build message
        message_parts = [f"[{timestamp}] "]
        message_parts.append(f"[{event_type}]")
        
        if event.node_id:
            message_parts.append(f" Node: {event.node_id}")
        
        # Add event data
        if event.data:
            data_str = ", ".join(f"{k}={v}" for k, v in event.data.items())
            message_parts.append(f" | {data_str}")
        
        message = "".join(message_parts) + "\n"
        
        # Append to log
        self._append_colored_text(message, color)
        
        # Limit log size
        self._trim_log()
    
    def _trim_log(self) -> None:
        """Trim log to max lines."""
        doc = self.log_text.document()
        if doc.blockCount() > self._max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            # Remove oldest blocks
            blocks_to_remove = doc.blockCount() - self._max_lines
            for _ in range(blocks_to_remove):
                cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # Remove the newline
    
    def clear_log(self) -> None:
        """Clear all log entries."""
        self.log_text.clear()
        logger.debug("Execution log cleared")
    
    def log_message(self, message: str, level: str = "info") -> None:
        """
        Log a custom message.
        
        Args:
            message: Message text
            level: Log level (info, warning, error, success)
        """
        timestamp = datetime.now()
        timestamp_str = self._format_timestamp(timestamp)
        
        # Choose color based on level
        color_map = {
            "info": QColor(212, 212, 212),
            "warning": QColor(255, 193, 7),
            "error": QColor(244, 67, 54),
            "success": QColor(76, 175, 80),
        }
        color = color_map.get(level, QColor(212, 212, 212))
        
        formatted_message = f"[{timestamp_str}] [{level.upper()}] {message}\n"
        self._append_colored_text(formatted_message, color)

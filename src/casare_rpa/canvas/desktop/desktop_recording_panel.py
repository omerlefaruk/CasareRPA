"""
Desktop Recording Panel for CasareRPA

Provides UI for recording desktop actions and generating workflows.
"""

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QTimer
from loguru import logger

from ...desktop.desktop_recorder import (
    DesktopRecorder,
    DesktopRecordedAction,
    DesktopActionType,
    WorkflowGenerator,
)


class ActionListItem(QListWidgetItem):
    """Custom list item for displaying recorded actions."""

    def __init__(self, action: DesktopRecordedAction, index: int):
        super().__init__()
        self.action = action
        self.index = index

        # Set display text
        self.setText(f"{index + 1}. {action.get_description()}")

        # Set icon based on action type
        icon_map = {
            DesktopActionType.MOUSE_CLICK: "🖱️",
            DesktopActionType.MOUSE_DOUBLE_CLICK: "🖱️🖱️",
            DesktopActionType.MOUSE_RIGHT_CLICK: "🖱️➡️",
            DesktopActionType.KEYBOARD_TYPE: "⌨️",
            DesktopActionType.KEYBOARD_HOTKEY: "⌨️🔗",
            DesktopActionType.MOUSE_DRAG: "↔️",
            DesktopActionType.WINDOW_ACTIVATE: "🪟",
        }
        icon_text = icon_map.get(action.action_type, "❓")
        self.setText(f"{icon_text} {index + 1}. {action.get_description()}")

        # Set tooltip with details
        tooltip_lines = [
            f"Action: {action.action_type.value}",
            f"Time: {action.timestamp.strftime('%H:%M:%S')}",
        ]
        if action.element_name:
            tooltip_lines.append(f"Element: {action.element_name}")
        if action.window_title:
            tooltip_lines.append(f"Window: {action.window_title}")
        if action.x or action.y:
            tooltip_lines.append(f"Position: ({action.x}, {action.y})")

        self.setToolTip("\n".join(tooltip_lines))


class DesktopRecordingPanel(QDockWidget):
    """
    Dockable panel for desktop action recording.

    Features:
    - Start/Stop/Pause recording
    - Live action list display
    - Generate workflow from recording
    - Clear and delete actions
    """

    # Signals
    workflow_generated = Signal(dict)  # Emits workflow data

    def __init__(self, parent=None):
        super().__init__("Desktop Recorder", parent)

        self.recorder = DesktopRecorder()
        self.recorder.set_callbacks(
            on_action_recorded=self._on_action_recorded,
            on_recording_started=self._on_recording_started,
            on_recording_stopped=self._on_recording_stopped,
            on_recording_paused=self._on_recording_paused,
        )

        self._setup_ui()
        self._update_ui_state()

        # Timer for elapsed time display
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_timer_display)

        logger.info("Desktop recording panel initialized")

    def _setup_ui(self):
        """Setup the user interface."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )

        # Main widget
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with hotkey hints
        header = QLabel("Desktop Action Recorder")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        hints = QLabel("F9: Start/Stop | F10: Pause | Esc: Cancel")
        hints.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(hints)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #444;")
        layout.addWidget(sep)

        # Control buttons
        btn_layout = QHBoxLayout()

        self.record_btn = QPushButton("Start Recording")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton:disabled { background-color: #666; }
        """)
        self.record_btn.clicked.connect(self._toggle_recording)
        btn_layout.addWidget(self.record_btn)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._toggle_pause)
        btn_layout.addWidget(self.pause_btn)

        layout.addLayout(btn_layout)

        # Status display
        status_layout = QHBoxLayout()

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-family: monospace; color: #888;")
        status_layout.addWidget(self.timer_label)

        self.action_count_label = QLabel("0 actions")
        self.action_count_label.setStyleSheet("color: #888;")
        status_layout.addWidget(self.action_count_label)

        layout.addLayout(status_layout)

        # Action list
        self.action_list = QListWidget()
        self.action_list.setAlternatingRowColors(True)
        self.action_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2a2a;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #3d5a80;
            }
            QListWidget::item:alternate {
                background-color: #252525;
            }
        """)
        layout.addWidget(self.action_list, stretch=1)

        # Action buttons
        action_btn_layout = QHBoxLayout()

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.clicked.connect(self._delete_selected)
        action_btn_layout.addWidget(self.delete_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear_all)
        action_btn_layout.addWidget(self.clear_btn)

        action_btn_layout.addStretch()

        layout.addLayout(action_btn_layout)

        # Generate workflow button
        self.generate_btn = QPushButton("Generate Workflow")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #1565C0; }
            QPushButton:disabled { background-color: #666; }
        """)
        self.generate_btn.clicked.connect(self._generate_workflow)
        layout.addWidget(self.generate_btn)

        self.setWidget(main_widget)

    def _toggle_recording(self):
        """Toggle recording state."""
        if self.recorder.is_recording:
            self.recorder.stop()
        else:
            try:
                self.recorder.start()
            except RuntimeError as e:
                QMessageBox.critical(self, "Error", str(e))

    def _toggle_pause(self):
        """Toggle pause state."""
        self.recorder.toggle_pause()

    def _on_recording_started(self):
        """Handle recording started."""
        self._update_ui_state()
        self._timer.start(1000)  # Update every second

    def _on_recording_stopped(self):
        """Handle recording stopped."""
        self._update_ui_state()
        self._timer.stop()

    def _on_recording_paused(self, paused: bool):
        """Handle recording paused/resumed."""
        self._update_ui_state()

    def _on_action_recorded(self, action: DesktopRecordedAction):
        """Handle new action recorded."""
        # Add to list (thread-safe via signal would be better, but this works for now)
        item = ActionListItem(action, self.action_list.count())
        self.action_list.addItem(item)
        self.action_list.scrollToBottom()

        # Update count
        self.action_count_label.setText(f"{self.action_list.count()} actions")

    def _update_ui_state(self):
        """Update UI based on current state."""
        is_recording = self.recorder.is_recording
        is_paused = self.recorder.is_paused
        has_actions = self.action_list.count() > 0

        # Record button
        if is_recording:
            self.record_btn.setText("Stop Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #da190b; }
            """)
        else:
            self.record_btn.setText("Start Recording")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #45a049; }
            """)

        # Pause button
        self.pause_btn.setEnabled(is_recording)
        self.pause_btn.setText("Resume" if is_paused else "Pause")

        # Status label
        if is_recording:
            if is_paused:
                self.status_label.setText("Paused")
                self.status_label.setStyleSheet("color: #FFC107;")
            else:
                self.status_label.setText("Recording...")
                self.status_label.setStyleSheet("color: #4CAF50;")
        else:
            self.status_label.setText("Ready")
            self.status_label.setStyleSheet("color: #888;")

        # Action buttons
        self.delete_btn.setEnabled(has_actions and not is_recording)
        self.clear_btn.setEnabled(has_actions and not is_recording)
        self.generate_btn.setEnabled(has_actions and not is_recording)

    def _update_timer_display(self):
        """Update the timer display."""
        if self.recorder.start_time:
            from datetime import datetime

            elapsed = (datetime.now() - self.recorder.start_time).total_seconds()
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def _delete_selected(self):
        """Delete selected actions."""
        selected = self.action_list.selectedItems()
        if not selected:
            return

        for item in reversed(selected):
            row = self.action_list.row(item)
            self.action_list.takeItem(row)
            if row < len(self.recorder.actions):
                del self.recorder.actions[row]

        # Re-number items
        self._renumber_items()
        self._update_ui_state()

    def _clear_all(self):
        """Clear all recorded actions."""
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all recorded actions?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.action_list.clear()
            self.recorder.clear()
            self.action_count_label.setText("0 actions")
            self._update_ui_state()

    def _renumber_items(self):
        """Re-number all items after deletion."""
        for i in range(self.action_list.count()):
            item = self.action_list.item(i)
            if isinstance(item, ActionListItem):
                action = item.action
                icon_map = {
                    DesktopActionType.MOUSE_CLICK: "🖱️",
                    DesktopActionType.MOUSE_DOUBLE_CLICK: "🖱️🖱️",
                    DesktopActionType.MOUSE_RIGHT_CLICK: "🖱️➡️",
                    DesktopActionType.KEYBOARD_TYPE: "⌨️",
                    DesktopActionType.KEYBOARD_HOTKEY: "⌨️🔗",
                    DesktopActionType.MOUSE_DRAG: "↔️",
                    DesktopActionType.WINDOW_ACTIVATE: "🪟",
                }
                icon_text = icon_map.get(action.action_type, "❓")
                item.setText(f"{icon_text} {i + 1}. {action.get_description()}")

        self.action_count_label.setText(f"{self.action_list.count()} actions")

    def _generate_workflow(self):
        """Generate workflow from recorded actions."""
        if self.action_list.count() == 0:
            QMessageBox.warning(
                self, "No Actions", "No actions recorded to generate workflow."
            )
            return

        actions = self.recorder.get_actions()
        workflow_data = WorkflowGenerator.generate_workflow_data(actions)

        logger.info(f"Generated workflow with {len(actions)} actions")

        # Emit signal for main window to handle
        self.workflow_generated.emit(workflow_data)

        QMessageBox.information(
            self,
            "Workflow Generated",
            f"Generated workflow with {len(actions)} nodes.\n"
            "The workflow has been added to the canvas.",
        )

    def keyPressEvent(self, event):
        """Handle key press events for global hotkeys."""
        key = event.key()

        if key == Qt.Key.Key_F9:
            self._toggle_recording()
        elif key == Qt.Key.Key_F10:
            if self.recorder.is_recording:
                self._toggle_pause()
        elif key == Qt.Key.Key_Escape:
            if self.recorder.is_recording:
                self.recorder.stop()
                self._clear_all()

        super().keyPressEvent(event)

"""
Browser Recording Panel for CasareRPA.

Provides a UI panel for recording browser actions and converting them
to workflow nodes. Integrates with the BrowserRecorder to capture
user interactions in real-time.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QGroupBox,
    QMessageBox,
    QSplitter,
    QTextEdit,
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.infrastructure.browser.browser_recorder import (
        BrowserRecorder,
        BrowserRecordedAction,
    )


class BrowserRecordingPanel(QDockWidget):
    """
    Dockable panel for browser action recording.

    Features:
    - Record/Stop button with visual state indication
    - Real-time action list with timestamps
    - Action details view
    - Convert to Workflow button
    - Clear recording button

    Signals:
        recording_started: Emitted when recording begins.
        recording_stopped: Emitted when recording ends (list of actions).
        convert_to_workflow: Emitted when user wants to convert actions.
    """

    # Signals
    recording_started = Signal()
    recording_stopped = Signal(list)  # List[BrowserRecordedAction]
    convert_to_workflow = Signal(list)  # List[Dict] - node configs

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the browser recording panel."""
        super().__init__("Browser Recording", parent)
        self.setObjectName("BrowserRecordingDock")

        # State
        self._recorder: Optional["BrowserRecorder"] = None
        self._is_recording = False
        self._recording_duration = 0
        self._actions: List["BrowserRecordedAction"] = []

        # Timer for duration display
        self._duration_timer = QTimer(self)
        self._duration_timer.timeout.connect(self._update_duration)
        self._duration_timer.setInterval(1000)

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._update_button_states()

        logger.debug("BrowserRecordingPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(300)
        self.setMinimumHeight(400)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Recording Controls Group
        controls_group = QGroupBox("Recording Controls")
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(8)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(8)

        self._status_indicator = QLabel()
        self._status_indicator.setFixedSize(16, 16)
        self._status_indicator.setStyleSheet("background-color: #808080; border-radius: 8px;")

        self._status_label = QLabel("Ready to Record")
        self._status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self._duration_label = QLabel("00:00")
        self._duration_label.setFont(QFont("Consolas", 10))
        self._duration_label.setStyleSheet("color: #9cdcfe;")

        status_row.addWidget(self._status_indicator)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        status_row.addWidget(self._duration_label)

        controls_layout.addLayout(status_row)

        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self._record_btn = QPushButton("Record")
        self._record_btn.setFixedHeight(32)
        self._record_btn.setCheckable(True)
        self._record_btn.clicked.connect(self._on_record_clicked)
        self._record_btn.setToolTip("Start/Stop recording browser actions (F9)")

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(32)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self._clear_btn.setToolTip("Clear all recorded actions")

        button_row.addWidget(self._record_btn, stretch=2)
        button_row.addWidget(self._clear_btn, stretch=1)

        controls_layout.addLayout(button_row)

        main_layout.addWidget(controls_group)

        # Actions List Group
        actions_group = QGroupBox("Recorded Actions")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(4)

        # Action count label
        count_row = QHBoxLayout()
        self._action_count_label = QLabel("0 actions recorded")
        self._action_count_label.setStyleSheet("color: #808080;")
        count_row.addWidget(self._action_count_label)
        count_row.addStretch()
        actions_layout.addLayout(count_row)

        # Splitter for list and details
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Action list
        self._action_list = QListWidget()
        self._action_list.setAlternatingRowColors(True)
        self._action_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._action_list.itemSelectionChanged.connect(self._on_action_selected)
        splitter.addWidget(self._action_list)

        # Action details
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("Action Details")
        details_label.setStyleSheet("color: #808080; font-weight: bold;")
        details_layout.addWidget(details_label)

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        self._details_text.setMaximumHeight(120)
        self._details_text.setFont(QFont("Consolas", 9))
        details_layout.addWidget(self._details_text)

        splitter.addWidget(details_container)
        splitter.setSizes([200, 100])

        actions_layout.addWidget(splitter)

        main_layout.addWidget(actions_group, stretch=1)

        # Convert to Workflow Group
        convert_group = QGroupBox("Workflow Generation")
        convert_layout = QVBoxLayout(convert_group)

        self._convert_btn = QPushButton("Convert to Workflow")
        self._convert_btn.setFixedHeight(32)
        self._convert_btn.clicked.connect(self._on_convert_clicked)
        self._convert_btn.setToolTip("Generate workflow nodes from recorded actions")
        self._convert_btn.setEnabled(False)

        convert_layout.addWidget(self._convert_btn)

        # Info label
        info_label = QLabel(
            "Recorded actions will be converted to workflow nodes that can be "
            "edited and connected in the canvas."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #808080; font-size: 9pt;")
        convert_layout.addWidget(info_label)

        main_layout.addWidget(convert_group)

        self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #252525;
                color: #e0e0e0;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
            }
            QGroupBox {
                background: #2d2d2d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: #e0e0e0;
            }
            QListWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252525;
                border: 1px solid #3d3d3d;
                color: #d4d4d4;
                font-family: 'Segoe UI', sans-serif;
                font-size: 9pt;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #264f78;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #5a5a5a;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #808080;
                border-color: #3d3d3d;
            }
            QPushButton:checked {
                background-color: #c42b1c;
                border-color: #e81123;
            }
            QPushButton#convert_btn {
                background-color: #0078d7;
                border-color: #0086f0;
            }
            QPushButton#convert_btn:hover {
                background-color: #0086f0;
            }
            QPushButton#convert_btn:disabled {
                background-color: #2d2d2d;
                border-color: #3d3d3d;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                color: #9cdcfe;
            }
            QLabel {
                color: #e0e0e0;
            }
            QSplitter::handle {
                background-color: #4a4a4a;
                height: 2px;
            }
        """)

        # Apply specific style to convert button
        self._convert_btn.setObjectName("convert_btn")

    def set_recorder(self, recorder: "BrowserRecorder") -> None:
        """
        Set the browser recorder instance.

        Args:
            recorder: BrowserRecorder to use for recording.
        """
        self._recorder = recorder

        # Set up callbacks
        recorder.set_callbacks(
            on_action_recorded=self._on_action_recorded,
            on_recording_started=self._on_recording_started_callback,
            on_recording_stopped=self._on_recording_stopped_callback,
        )

        logger.debug("BrowserRecorder connected to panel")

    def _on_record_clicked(self, checked: bool) -> None:
        """Handle record button click."""
        if checked:
            self._start_recording()
        else:
            self._stop_recording()

    async def start_recording_async(self) -> None:
        """Start recording (async version for external use)."""
        if self._recorder is None:
            QMessageBox.warning(
                self,
                "No Browser",
                "No browser recorder available. Please open a browser first.",
            )
            return

        if self._is_recording:
            logger.warning("Already recording")
            return

        try:
            await self._recorder.start_recording()
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            QMessageBox.critical(
                self,
                "Recording Error",
                f"Failed to start recording: {e}",
            )
            self._record_btn.setChecked(False)

    def _start_recording(self) -> None:
        """Start recording browser actions."""
        if self._recorder is None:
            QMessageBox.warning(
                self,
                "No Browser",
                "No browser recorder available. Please open a browser first.",
            )
            self._record_btn.setChecked(False)
            return

        # Clear previous actions
        self._actions.clear()
        self._action_list.clear()
        self._details_text.clear()

        # Note: Actual recording start happens via async call
        # The UI state is updated via the callback
        self.recording_started.emit()

    def _stop_recording(self) -> None:
        """Stop recording browser actions."""
        if self._recorder is None:
            return

        # Note: Actual recording stop happens via async call
        # The UI state is updated via the callback
        self.recording_stopped.emit(self._actions)

    def _on_recording_started_callback(self) -> None:
        """Callback when recording actually starts."""
        self._is_recording = True
        self._recording_duration = 0
        self._duration_timer.start()

        # Update UI
        self._record_btn.setText("Stop Recording")
        self._record_btn.setChecked(True)
        self._status_label.setText("Recording...")
        self._status_indicator.setStyleSheet("background-color: #c42b1c; border-radius: 8px;")
        self._clear_btn.setEnabled(False)
        self._convert_btn.setEnabled(False)

        self._update_button_states()
        logger.info("Browser recording started")

    def _on_recording_stopped_callback(self) -> None:
        """Callback when recording actually stops."""
        self._is_recording = False
        self._duration_timer.stop()

        # Update UI
        self._record_btn.setText("Record")
        self._record_btn.setChecked(False)
        self._status_label.setText("Recording Complete")
        self._status_indicator.setStyleSheet("background-color: #89d185; border-radius: 8px;")
        self._clear_btn.setEnabled(True)
        self._convert_btn.setEnabled(len(self._actions) > 0)

        self._update_button_states()
        logger.info(f"Browser recording stopped with {len(self._actions)} actions")

    def _on_action_recorded(self, action: "BrowserRecordedAction") -> None:
        """
        Handle a new recorded action.

        Args:
            action: The recorded browser action.
        """
        self._actions.append(action)

        # Add to list
        item = QListWidgetItem()
        item.setText(action.get_description())
        item.setData(Qt.ItemDataRole.UserRole, len(self._actions) - 1)

        # Set icon/color based on action type
        type_colors = {
            "click": "#4fc3f7",
            "type": "#81c784",
            "navigate": "#ffb74d",
            "select": "#ba68c8",
            "check": "#7986cb",
            "keyboard": "#f06292",
        }
        color = type_colors.get(action.action_type.value, "#9e9e9e")
        item.setForeground(QColor(color))

        self._action_list.addItem(item)
        self._action_list.scrollToBottom()

        # Update count
        self._action_count_label.setText(f"{len(self._actions)} actions recorded")

    def _on_action_selected(self) -> None:
        """Handle action selection in list."""
        selected_items = self._action_list.selectedItems()
        if not selected_items:
            self._details_text.clear()
            return

        item = selected_items[0]
        index = item.data(Qt.ItemDataRole.UserRole)

        if index is not None and 0 <= index < len(self._actions):
            action = self._actions[index]
            self._show_action_details(action)

    def _show_action_details(self, action: "BrowserRecordedAction") -> None:
        """
        Display action details in the details panel.

        Args:
            action: The action to display details for.
        """
        details = []
        details.append(f"Type: {action.action_type.value}")
        details.append(f"Timestamp: {action.timestamp:.2f}s")

        if action.selector:
            details.append(f"Selector: {action.selector}")

        if action.value:
            details.append(f"Value: {action.value}")

        if action.url:
            details.append(f"URL: {action.url}")

        if action.coordinates:
            details.append(f"Coordinates: ({action.coordinates[0]}, {action.coordinates[1]})")

        if action.keys:
            details.append(f"Keys: {'+'.join(action.keys)}")

        if action.element_info:
            el = action.element_info
            details.append("")
            details.append("Element Info:")
            if el.get("tag"):
                details.append(f"  Tag: {el.get('tag')}")
            if el.get("id"):
                details.append(f"  ID: {el.get('id')}")
            if el.get("text"):
                details.append(f"  Text: {el.get('text')[:50]}")
            if el.get("classes"):
                details.append(f"  Classes: {', '.join(el.get('classes', [])[:3])}")

        self._details_text.setText("\n".join(details))

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        if self._is_recording:
            return

        if self._actions:
            reply = QMessageBox.question(
                self,
                "Clear Recording",
                f"Clear {len(self._actions)} recorded actions?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        self._actions.clear()
        self._action_list.clear()
        self._details_text.clear()
        self._action_count_label.setText("0 actions recorded")
        self._status_label.setText("Ready to Record")
        self._status_indicator.setStyleSheet("background-color: #808080; border-radius: 8px;")
        self._duration_label.setText("00:00")
        self._convert_btn.setEnabled(False)

        if self._recorder:
            self._recorder.clear()

        logger.info("Recording cleared")

    def _on_convert_clicked(self) -> None:
        """Handle convert to workflow button click."""
        if not self._actions:
            QMessageBox.information(
                self,
                "No Actions",
                "No actions to convert. Record some browser actions first.",
            )
            return

        if self._recorder:
            node_configs = self._recorder.to_workflow_nodes()
            self.convert_to_workflow.emit(node_configs)
            logger.info(f"Emitting convert_to_workflow with {len(node_configs)} nodes")
        else:
            # Fallback: emit raw actions
            self.convert_to_workflow.emit(self._actions)

    def _update_duration(self) -> None:
        """Update the recording duration display."""
        self._recording_duration += 1
        minutes = self._recording_duration // 60
        seconds = self._recording_duration % 60
        self._duration_label.setText(f"{minutes:02d}:{seconds:02d}")

    def _update_button_states(self) -> None:
        """Update button enabled states based on current state."""
        has_actions = len(self._actions) > 0

        self._clear_btn.setEnabled(not self._is_recording and has_actions)
        self._convert_btn.setEnabled(not self._is_recording and has_actions)

    def get_actions(self) -> List["BrowserRecordedAction"]:
        """
        Get all recorded actions.

        Returns:
            List of recorded browser actions.
        """
        return self._actions.copy()

    def get_node_configs(self) -> List[Dict[str, Any]]:
        """
        Get recorded actions as node configurations.

        Returns:
            List of node configuration dictionaries.
        """
        if self._recorder:
            return self._recorder.to_workflow_nodes()
        return []

    def cleanup(self) -> None:
        """Clean up resources."""
        self._duration_timer.stop()
        self._recorder = None
        logger.debug("BrowserRecordingPanel cleaned up")


__all__ = ["BrowserRecordingPanel"]

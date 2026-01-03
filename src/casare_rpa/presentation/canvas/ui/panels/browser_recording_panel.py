"""
Browser Recording Panel for CasareRPA.

Provides a UI panel for recording browser actions and converting them
to workflow nodes. Integrates with the BrowserRecorder to capture
user interactions in real-time.

Epic 6.1: Migrated to v2 design system (THEME_V2/TOKENS_V2).
"""

from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDockWidget,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.helpers import (
    margin_none,
    margin_panel,
    set_fixed_size,
    set_max_size,
    set_min_size,
    set_spacing,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton

if TYPE_CHECKING:
    from casare_rpa.infrastructure.browser.browser_recorder import (
        BrowserRecordedAction,
        BrowserRecorder,
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

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the browser recording panel."""
        super().__init__("Browser Recording", parent)
        self.setObjectName("BrowserRecordingDock")

        # State
        self._recorder: BrowserRecorder | None = None
        self._is_recording = False
        self._recording_duration = 0
        self._actions: list[BrowserRecordedAction] = []

        # Timer for duration display
        self._duration_timer = QTimer(self)
        self._duration_timer.timeout.connect(self._update_duration)
        self._duration_timer.setInterval(1000)

        self._setup_dock()
        self._setup_ui()
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
            # NO DockWidgetFloatable - dock-only enforcement (v2 requirement)
        )
        set_min_size(self, TOKENS_V2.sizes.panel_default_width, TOKENS_V2.sizes.dialog_height_md)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        margin_panel(main_layout)
        set_spacing(main_layout, TOKENS_V2.spacing.md)

        # Recording Controls Group
        controls_group = QGroupBox("Recording Controls")
        controls_layout = QVBoxLayout(controls_group)
        set_spacing(controls_layout, TOKENS_V2.spacing.md)

        # Status row
        status_row = QHBoxLayout()
        set_spacing(status_row, TOKENS_V2.spacing.md)

        self._status_indicator = QLabel()
        set_fixed_size(self._status_indicator, TOKENS_V2.sizes.icon_md, TOKENS_V2.sizes.icon_md)
        self._status_indicator.setStyleSheet(
            f"background-color: {THEME_V2.text_muted}; border-radius: {TOKENS_V2.sizes.icon_lg}px;"
        )

        self._status_label = QLabel("Ready to Record")
        self._status_label.setFont(
            QFont(TOKENS_V2.typography.ui, TOKENS_V2.typography.display_md, QFont.Weight.Bold)
        )

        self._duration_label = QLabel("00:00")
        self._duration_label.setFont(QFont(TOKENS_V2.typography.mono, TOKENS_V2.typography.body))
        self._duration_label.setStyleSheet(f"color: {THEME_V2.info};")

        status_row.addWidget(self._status_indicator)
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        status_row.addWidget(self._duration_label)

        controls_layout.addLayout(status_row)

        # Button row
        button_row = QHBoxLayout()
        set_spacing(button_row, TOKENS_V2.spacing.md)

        self._record_btn = PushButton(text="Record", variant="secondary", size="md")
        self._record_btn.setCheckable(True)
        self._record_btn.clicked.connect(self._on_record_clicked)
        self._record_btn.setToolTip("Start/Stop recording browser actions (F9)")

        self._clear_btn = PushButton(text="Clear", variant="secondary", size="md")
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self._clear_btn.setToolTip("Clear all recorded actions")

        button_row.addWidget(self._record_btn, stretch=2)
        button_row.addWidget(self._clear_btn, stretch=1)

        controls_layout.addLayout(button_row)

        main_layout.addWidget(controls_group)

        # Actions List Group
        actions_group = QGroupBox("Recorded Actions")
        actions_layout = QVBoxLayout(actions_group)
        set_spacing(actions_layout, TOKENS_V2.spacing.sm)

        # Action count label
        count_row = QHBoxLayout()
        self._action_count_label = QLabel("0 actions recorded")
        self._action_count_label.setStyleSheet(f"color: {THEME_V2.text_muted};")
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
        margin_none(details_layout)

        details_label = QLabel("Action Details")
        details_label.setStyleSheet(f"color: {THEME_V2.text_muted}; font-weight: bold;")
        details_layout.addWidget(details_label)

        self._details_text = QTextEdit()
        self._details_text.setReadOnly(True)
        set_max_size(
            self._details_text,
            TOKENS_V2.sizes.panel_max_width,
            TOKENS_V2.sizes.dialog_height_md,
        )
        self._details_text.setFont(QFont(TOKENS_V2.typography.mono, TOKENS_V2.typography.body))
        details_layout.addWidget(self._details_text)

        splitter.addWidget(details_container)
        splitter.setSizes(
            [
                TOKENS_V2.sizes.panel_default_width * 2 // 3,
                TOKENS_V2.sizes.panel_default_width // 3,
            ]
        )

        actions_layout.addWidget(splitter)

        main_layout.addWidget(actions_group, stretch=1)

        # Convert to Workflow Group
        convert_group = QGroupBox("Workflow Generation")
        convert_layout = QVBoxLayout(convert_group)

        self._convert_btn = PushButton(
            text="Convert to Workflow",
            variant="primary",
            size="md",
        )
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
        info_label.setStyleSheet(
            f"color: {THEME_V2.text_muted}; font-size: {TOKENS_V2.typography.caption}pt;"
        )
        convert_layout.addWidget(info_label)

        main_layout.addWidget(convert_group)

        self.setWidget(container)

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
        try:
            self._record_btn.set_variant("danger" if checked else "secondary")
            self._record_btn.setText("Stop" if checked else "Record")
        except Exception:
            pass
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
        self._status_indicator.setStyleSheet(
            f"background-color: {THEME_V2.error}; border-radius: {TOKENS_V2.sizes.icon_lg}px;"
        )
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
        self._status_indicator.setStyleSheet(
            f"background-color: {THEME_V2.success}; border-radius: {TOKENS_V2.sizes.icon_lg}px;"
        )
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
        # Epic 6.1: Mapped to THEME_V2 semantic colors
        type_colors = {
            "click": THEME_V2.info,  # #4fc3f7 -> info
            "type": THEME_V2.success,  # #81c784 -> success
            "navigate": THEME_V2.warning,  # #ffb74d -> warning
            "select": THEME_V2.primary,  # #ba68c8 -> primary/accent
            "check": THEME_V2.secondary,
            "keyboard": THEME_V2.error,  # #f06292 -> error/danger
        }
        color = type_colors.get(action.action_type.value, THEME_V2.text_muted)
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
        self._status_indicator.setStyleSheet(
            f"background-color: {THEME_V2.text_muted}; border-radius: {TOKENS_V2.sizes.icon_lg}px;"
        )
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

    def get_actions(self) -> list["BrowserRecordedAction"]:
        """
        Get all recorded actions.

        Returns:
            List of recorded browser actions.
        """
        return self._actions.copy()

    def get_node_configs(self) -> list[dict[str, Any]]:
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


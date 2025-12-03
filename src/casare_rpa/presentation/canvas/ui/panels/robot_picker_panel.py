"""
Robot Picker Panel UI Component.

Dockable panel for selecting robots and toggling execution mode.
Allows users to choose between local execution and cloud robot submission.
"""

from typing import Optional, List, Dict, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QComboBox,
    QLabel,
    QHeaderView,
    QButtonGroup,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.domain.orchestrator.entities.robot import Robot, RobotStatus


# Status colors for visual indicators
STATUS_COLORS = {
    "online": QColor(0x4C, 0xAF, 0x50),  # Green
    "busy": QColor(0xFF, 0xC1, 0x07),  # Yellow/Amber
    "offline": QColor(0xF4, 0x43, 0x36),  # Red
    "error": QColor(0xF4, 0x43, 0x36),  # Red
    "maintenance": QColor(0x9E, 0x9E, 0x9E),  # Gray
}


class RobotPickerPanel(QDockWidget):
    """
    Panel to select robots and execution mode.

    Features:
    - Execution mode toggle: Local vs Cloud
    - Tree view of available robots with status indicators
    - Robot filtering by capability
    - Refresh button to update robot list
    - Status indicators: green=online, yellow=busy, red=offline, gray=maintenance

    Signals:
        robot_selected: Emitted when user selects a robot (robot_id: str)
        execution_mode_changed: Emitted when execution mode changes ('local' or 'cloud')
        refresh_requested: Emitted when user requests robot list refresh
    """

    robot_selected = Signal(str)
    execution_mode_changed = Signal(str)
    refresh_requested = Signal()
    submit_to_cloud_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the Robot Picker Panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Robot Picker", parent)
        self.setObjectName("RobotPickerDock")

        self._selected_robot_id: Optional[str] = None
        self._execution_mode: str = "local"
        self._robots: List["Robot"] = []
        self._robot_items: Dict[str, QTreeWidgetItem] = {}
        self._connected_to_orchestrator: bool = False

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("RobotPickerPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(280)
        self.setMinimumHeight(300)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Execution mode selector
        mode_group = QGroupBox("Execution Mode")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(4)

        self._mode_button_group = QButtonGroup(self)

        self._local_radio = QRadioButton("Run Local")
        self._local_radio.setToolTip(
            "Execute workflow on this machine using local resources"
        )
        self._local_radio.setChecked(True)
        mode_layout.addWidget(self._local_radio)
        self._mode_button_group.addButton(self._local_radio, 0)

        self._cloud_radio = QRadioButton("Submit to Cloud")
        self._cloud_radio.setToolTip(
            "Submit workflow to orchestrator for cloud robot execution"
        )
        mode_layout.addWidget(self._cloud_radio)
        self._mode_button_group.addButton(self._cloud_radio, 1)

        self._local_radio.toggled.connect(self._on_mode_changed)
        self._cloud_radio.toggled.connect(self._on_mode_changed)

        layout.addWidget(mode_group)

        # Robot selection group (enabled when cloud mode selected)
        self._robot_group = QGroupBox("Select Robot")
        robot_layout = QVBoxLayout(self._robot_group)
        robot_layout.setSpacing(4)

        # Filter by capability dropdown
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(4)

        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color: #a0a0a0;")
        filter_layout.addWidget(filter_label)

        self._capability_filter = QComboBox()
        self._capability_filter.addItems(
            [
                "All Robots",
                "Browser Capable",
                "Desktop Capable",
                "GPU Available",
                "High Memory",
                "Secure Zone",
                "Cloud Hosted",
                "On-Premise",
            ]
        )
        self._capability_filter.setToolTip("Filter robots by capability")
        self._capability_filter.currentIndexChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self._capability_filter, 1)

        robot_layout.addLayout(filter_layout)

        # Robot tree view
        self._robot_tree = QTreeWidget()
        self._robot_tree.setHeaderLabels(["Robot", "Status", "Jobs", "Capabilities"])
        self._robot_tree.setRootIsDecorated(False)
        self._robot_tree.setAlternatingRowColors(True)
        self._robot_tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

        # Configure columns
        header = self._robot_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self._robot_tree.itemSelectionChanged.connect(self._on_robot_selection_changed)
        self._robot_tree.itemDoubleClicked.connect(self._on_robot_double_clicked)

        robot_layout.addWidget(self._robot_tree)

        # Refresh button and status
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self._status_label = QLabel("0 robots available")
        self._status_label.setStyleSheet("color: #888888; font-size: 11px;")
        button_layout.addWidget(self._status_label, 1)

        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.setToolTip("Refresh robot list from orchestrator")
        self._refresh_button.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(self._refresh_button)

        robot_layout.addLayout(button_layout)

        layout.addWidget(self._robot_group)

        # Submit to Cloud button (below robot selection group)
        self._submit_button = QPushButton("⬆ Submit to Cloud")
        self._submit_button.setObjectName("submitToCloudButton")
        self._submit_button.setToolTip(
            "Submit current workflow to selected robot for execution"
        )
        self._submit_button.setMinimumHeight(36)
        self._submit_button.clicked.connect(self._on_submit_clicked)
        layout.addWidget(self._submit_button)

        # Initially disable robot selection in local mode
        self._robot_group.setEnabled(False)

        # Update submit button state
        self._update_submit_button_state()

        # Add stretch at bottom
        layout.addStretch()

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
                background: #2a2a2a;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: #e0e0e0;
            }
            QRadioButton {
                color: #e0e0e0;
                spacing: 6px;
            }
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
            }
            QRadioButton::indicator:checked {
                background: #5a9;
                border: 2px solid #4a8;
                border-radius: 7px;
            }
            QRadioButton::indicator:unchecked {
                background: #3d3d3d;
                border: 2px solid #4a4a4a;
                border-radius: 7px;
            }
            QComboBox {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
                min-height: 24px;
            }
            QComboBox:hover {
                border-color: #5a8a9a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QTreeWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                color: #e0e0e0;
                alternate-background-color: #252525;
            }
            QTreeWidget::item {
                padding: 4px 2px;
            }
            QTreeWidget::item:hover {
                background: #2a2d2e;
            }
            QTreeWidget::item:selected {
                background: #094771;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #a0a0a0;
                padding: 4px 6px;
                border: none;
                border-right: 1px solid #3d3d3d;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #5a8a9a;
            }
            QPushButton:pressed {
                background: #2d2d2d;
            }
            QPushButton#submitToCloudButton {
                background: #2a6a4a;
                border: 1px solid #3a8a5a;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton#submitToCloudButton:hover {
                background: #3a8a5a;
                border-color: #4aaa6a;
            }
            QPushButton#submitToCloudButton:pressed {
                background: #1a5a3a;
            }
            QPushButton#submitToCloudButton:disabled {
                background: #3d3d3d;
                border-color: #4a4a4a;
                color: #888888;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def _on_mode_changed(self, checked: bool) -> None:
        """Handle execution mode radio button change."""
        if not checked:
            return

        if self._local_radio.isChecked():
            self._execution_mode = "local"
            self._robot_group.setEnabled(False)
            self._selected_robot_id = None
        else:
            self._execution_mode = "cloud"
            self._robot_group.setEnabled(True)

        self._update_submit_button_state()
        self.execution_mode_changed.emit(self._execution_mode)
        logger.debug(f"Execution mode changed to: {self._execution_mode}")

    def _on_filter_changed(self, index: int) -> None:
        """Handle capability filter change."""
        self._apply_filter()

    def _apply_filter(self) -> None:
        """Apply capability filter to robot tree."""
        filter_text = self._capability_filter.currentText()

        # Map filter text to capability value
        capability_map = {
            "All Robots": None,
            "Browser Capable": "browser",
            "Desktop Capable": "desktop",
            "GPU Available": "gpu",
            "High Memory": "high_memory",
            "Secure Zone": "secure",
            "Cloud Hosted": "cloud",
            "On-Premise": "on_premise",
        }

        required_capability = capability_map.get(filter_text)

        visible_count = 0
        for robot_id, item in self._robot_items.items():
            robot = self._find_robot_by_id(robot_id)
            if robot is None:
                item.setHidden(True)
                continue

            if required_capability is None:
                item.setHidden(False)
                visible_count += 1
            else:
                has_capability = any(
                    cap.value == required_capability for cap in robot.capabilities
                )
                item.setHidden(not has_capability)
                if has_capability:
                    visible_count += 1

        self._status_label.setText(f"{visible_count} robots available")

    def _find_robot_by_id(self, robot_id: str) -> Optional["Robot"]:
        """Find robot in current list by ID."""
        for robot in self._robots:
            if robot.id == robot_id:
                return robot
        return None

    def _on_robot_selection_changed(self) -> None:
        """Handle robot selection change in tree."""
        selected_items = self._robot_tree.selectedItems()
        if not selected_items:
            self._selected_robot_id = None
            self._update_submit_button_state()
            return

        item = selected_items[0]
        robot_id = item.data(0, Qt.ItemDataRole.UserRole)
        if robot_id and robot_id != self._selected_robot_id:
            self._selected_robot_id = robot_id
            self._update_submit_button_state()
            self.robot_selected.emit(robot_id)
            logger.debug(f"Robot selected: {robot_id}")

    def _on_robot_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on robot item."""
        robot_id = item.data(0, Qt.ItemDataRole.UserRole)
        if robot_id:
            self._selected_robot_id = robot_id
            self.robot_selected.emit(robot_id)
            logger.debug(f"Robot double-clicked: {robot_id}")

    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        self.refresh_requested.emit()
        logger.debug("Robot list refresh requested")

    def _on_submit_clicked(self) -> None:
        """Handle submit to cloud button click."""
        if self._can_submit():
            self.submit_to_cloud_requested.emit()
            logger.debug(
                f"Submit to cloud requested for robot: {self._selected_robot_id}"
            )

    def _can_submit(self) -> bool:
        """Check if submission is currently allowed."""
        return (
            self._execution_mode == "cloud"
            and self._selected_robot_id is not None
            and self._connected_to_orchestrator
        )

    def _update_submit_button_state(self) -> None:
        """Update submit button enabled state and tooltip based on current conditions."""
        can_submit = self._can_submit()
        self._submit_button.setEnabled(can_submit)

        # Update tooltip based on why button might be disabled
        if self._execution_mode != "cloud":
            self._submit_button.setToolTip(
                "Switch to 'Submit to Cloud' mode to submit workflows"
            )
        elif not self._connected_to_orchestrator:
            self._submit_button.setToolTip(
                "Not connected to orchestrator. Click Refresh to connect."
            )
        elif self._selected_robot_id is None:
            self._submit_button.setToolTip(
                "Select a robot from the list to submit workflow"
            )
        else:
            robot = self._find_robot_by_id(self._selected_robot_id)
            robot_name = robot.name if robot else self._selected_robot_id
            self._submit_button.setToolTip(
                f"Submit current workflow to '{robot_name}' for execution"
            )

    def update_robots(self, robots: List["Robot"]) -> None:
        """
        Update robot list from data.

        Args:
            robots: List of Robot entities to display
        """
        self._robots = robots
        self._robot_tree.clear()
        self._robot_items.clear()

        for robot in robots:
            item = self._create_robot_item(robot)
            self._robot_tree.addTopLevelItem(item)
            self._robot_items[robot.id] = item

        # Update status label
        available_count = sum(1 for r in robots if r.is_available)
        self._status_label.setText(f"{available_count} robots available")

        # Apply current filter
        self._apply_filter()

        # Restore selection if robot still exists
        if self._selected_robot_id and self._selected_robot_id in self._robot_items:
            self._robot_items[self._selected_robot_id].setSelected(True)

        # Update submit button state
        self._update_submit_button_state()

        logger.debug(f"Robot tree updated with {len(robots)} robots")

    def _create_robot_item(self, robot: "Robot") -> QTreeWidgetItem:
        """
        Create a tree item for a robot.

        Args:
            robot: Robot entity

        Returns:
            QTreeWidgetItem for the robot
        """
        # Get capability abbreviations
        capability_abbrevs = []
        for cap in robot.capabilities:
            cap_map = {
                "browser": "B",
                "desktop": "D",
                "gpu": "G",
                "high_memory": "M",
                "secure": "S",
                "cloud": "C",
                "on_premise": "P",
            }
            abbrev = cap_map.get(cap.value, cap.value[0].upper())
            capability_abbrevs.append(abbrev)

        capabilities_str = ", ".join(sorted(capability_abbrevs)) or "-"

        # Create item
        item = QTreeWidgetItem(
            [
                robot.name,
                robot.status.value.title(),
                f"{robot.current_jobs}/{robot.max_concurrent_jobs}",
                capabilities_str,
            ]
        )

        # Store robot ID
        item.setData(0, Qt.ItemDataRole.UserRole, robot.id)

        # Apply status color
        self._set_status_icon(item, robot.status)

        # Set tooltip with full info
        tooltip = (
            f"ID: {robot.id}\n"
            f"Name: {robot.name}\n"
            f"Status: {robot.status.value}\n"
            f"Environment: {robot.environment}\n"
            f"Jobs: {robot.current_jobs}/{robot.max_concurrent_jobs}\n"
            f"Capabilities: {', '.join(c.value for c in robot.capabilities) or 'None'}\n"
            f"Tags: {', '.join(robot.tags) or 'None'}"
        )
        item.setToolTip(0, tooltip)

        return item

    def _set_status_icon(self, item: QTreeWidgetItem, status: "RobotStatus") -> None:
        """
        Set colored status indicator for robot item.

        Args:
            item: Tree widget item
            status: Robot status
        """
        status_color = STATUS_COLORS.get(status.value, STATUS_COLORS["offline"])

        # Set status column foreground color
        item.setForeground(1, QBrush(status_color))

        # Make status text bold for emphasis
        font = item.font(1)
        font.setBold(True)
        item.setFont(1, font)

    def get_selected_robot(self) -> Optional[str]:
        """
        Get selected robot ID.

        Returns:
            Selected robot ID or None
        """
        return self._selected_robot_id

    def get_execution_mode(self) -> str:
        """
        Get current execution mode.

        Returns:
            'local' or 'cloud'
        """
        return self._execution_mode

    def set_execution_mode(self, mode: str) -> None:
        """
        Set execution mode programmatically.

        Args:
            mode: 'local' or 'cloud'
        """
        if mode == "local":
            self._local_radio.setChecked(True)
        elif mode == "cloud":
            self._cloud_radio.setChecked(True)

    def select_robot(self, robot_id: str) -> bool:
        """
        Select a robot by ID.

        Args:
            robot_id: Robot ID to select

        Returns:
            True if robot was found and selected
        """
        if robot_id in self._robot_items:
            self._robot_tree.clearSelection()
            self._robot_items[robot_id].setSelected(True)
            self._selected_robot_id = robot_id
            return True
        return False

    def clear_selection(self) -> None:
        """Clear robot selection."""
        self._robot_tree.clearSelection()
        self._selected_robot_id = None

    def set_refreshing(self, refreshing: bool) -> None:
        """
        Set refresh button state during refresh operation.

        Args:
            refreshing: True to show refreshing state
        """
        self._refresh_button.setEnabled(not refreshing)
        if refreshing:
            self._refresh_button.setText("Refreshing...")
        else:
            self._refresh_button.setText("Refresh")

    def refresh(self) -> None:
        """Trigger a refresh of the robot list."""
        self._on_refresh_clicked()

    def set_connected(self, connected: bool) -> None:
        """
        Set orchestrator connection status.

        Args:
            connected: True if connected to orchestrator
        """
        self._connected_to_orchestrator = connected
        self._update_submit_button_state()
        logger.debug(f"Orchestrator connection status: {connected}")

    def is_connected(self) -> bool:
        """
        Get orchestrator connection status.

        Returns:
            True if connected to orchestrator
        """
        return self._connected_to_orchestrator

    def set_submitting(self, submitting: bool) -> None:
        """
        Set submit button state during submission.

        Args:
            submitting: True to show submitting state
        """
        self._submit_button.setEnabled(not submitting)
        if submitting:
            self._submit_button.setText("⬆ Submitting...")
        else:
            self._submit_button.setText("⬆ Submit to Cloud")
            self._update_submit_button_state()

    def show_submit_result(self, success: bool, message: str) -> None:
        """
        Show result of job submission.

        Args:
            success: Whether submission succeeded
            message: Result message (job ID or error)
        """
        if success:
            self._status_label.setText(f"✓ Submitted: {message}")
            self._status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        else:
            self._status_label.setText(f"✗ Failed: {message}")
            self._status_label.setStyleSheet("color: #F44336; font-size: 11px;")

        # Reset status after 5 seconds
        from PySide6.QtCore import QTimer

        QTimer.singleShot(5000, self._reset_status_label)

    def _reset_status_label(self) -> None:
        """Reset status label to default."""
        available = sum(1 for r in self._robots if r.is_available)
        self._status_label.setText(f"{available} robots available")
        self._status_label.setStyleSheet("color: #888888; font-size: 11px;")

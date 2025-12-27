"""
Robot Override Widget for Node-Level Robot Targeting.

Provides UI for configuring node-level robot overrides within workflows.
Allows users to target specific robots or required capabilities for individual nodes.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS

# Available robot capabilities matching RobotCapability enum
ROBOT_CAPABILITIES = [
    ("browser", "Browser", "Can run browser automation (Playwright)"),
    ("desktop", "Desktop", "Can run desktop automation (UIAutomation)"),
    ("gpu", "GPU", "Has GPU for ML workloads"),
    ("high_memory", "High Memory", "Has high memory for large data processing"),
    ("secure", "Secure", "In secure network zone"),
    ("cloud", "Cloud", "Cloud-hosted robot"),
    ("on_premise", "On-Premise", "On-premise robot"),
]


class RobotOverrideWidget(QWidget):
    """
    Widget for configuring node robot override.

    Allows users to override the workflow's default robot assignment
    for individual nodes, either by selecting a specific robot or
    by specifying required capabilities.

    Features:
    - Enable/disable override checkbox
    - Mode selector: Specific Robot vs By Capability
    - Robot dropdown for specific mode
    - Capability checkboxes for capability mode
    - Reason field for documentation

    Signals:
        override_changed: Emitted when override config changes (dict with config)
        override_cleared: Emitted when override is disabled/cleared
    """

    override_changed = Signal(dict)
    override_cleared = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize robot override widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._available_robots: list[dict[str, Any]] = []
        self._is_enabled = False

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("RobotOverrideWidget initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Enable override checkbox
        self._enable_checkbox = QCheckBox("Override workflow robot")
        self._enable_checkbox.setToolTip(
            "Enable to assign a specific robot or required capabilities for this node"
        )
        layout.addWidget(self._enable_checkbox)

        # Content container (shown when enabled)
        self._content_widget = QWidget()
        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(16, 8, 0, 0)
        content_layout.setSpacing(8)

        # Mode selector
        mode_row = QHBoxLayout()
        mode_row.setSpacing(8)
        mode_label = QLabel("Mode:")
        mode_label.setMinimumWidth(70)
        mode_label.setStyleSheet(f"color: {THEME.text_secondary};")
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Specific Robot", "By Capability"])
        self._mode_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self._mode_combo)
        content_layout.addLayout(mode_row)

        # Robot selector (for specific mode)
        self._robot_group = QWidget()
        robot_layout = QHBoxLayout(self._robot_group)
        robot_layout.setContentsMargins(0, 0, 0, 0)
        robot_layout.setSpacing(8)
        robot_label = QLabel("Robot:")
        robot_label.setMinimumWidth(70)
        robot_label.setStyleSheet(f"color: {THEME.text_secondary};")
        self._robot_combo = QComboBox()
        self._robot_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._robot_combo.setPlaceholderText("Select robot...")
        robot_layout.addWidget(robot_label)
        robot_layout.addWidget(self._robot_combo)
        content_layout.addWidget(self._robot_group)

        # Capability checkboxes (for capability mode)
        self._capability_group = QGroupBox("Required Capabilities")
        cap_layout = QVBoxLayout(self._capability_group)
        cap_layout.setContentsMargins(8, 8, 8, 8)
        cap_layout.setSpacing(4)

        self._capability_checks: dict[str, QCheckBox] = {}
        for cap_id, cap_name, cap_tooltip in ROBOT_CAPABILITIES:
            checkbox = QCheckBox(cap_name)
            checkbox.setToolTip(cap_tooltip)
            checkbox.setProperty("capability_id", cap_id)
            self._capability_checks[cap_id] = checkbox
            cap_layout.addWidget(checkbox)

        content_layout.addWidget(self._capability_group)
        self._capability_group.hide()

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background: {THEME.input_bg};")
        content_layout.addWidget(separator)

        # Reason field
        reason_row = QHBoxLayout()
        reason_row.setSpacing(8)
        reason_label = QLabel("Reason:")
        reason_label.setMinimumWidth(70)
        reason_label.setStyleSheet(f"color: {THEME.text_secondary};")
        self._reason_edit = QLineEdit()
        self._reason_edit.setPlaceholderText("Reason for override (optional)")
        reason_row.addWidget(reason_label)
        reason_row.addWidget(self._reason_edit)
        content_layout.addLayout(reason_row)

        # Clear button
        self._clear_btn = QPushButton("Clear Override")
        self._clear_btn.setToolTip("Remove this override configuration")
        content_layout.addWidget(self._clear_btn)

        layout.addWidget(self._content_widget)
        self._content_widget.hide()

    def _apply_styles(self) -> None:
        """Apply dark theme styling using THEME."""
        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                color: {THEME.text_primary};
            }}
            QGroupBox {{
                background: {THEME.bg_component};
                border: 1px solid {THEME.input_bg};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
                color: {THEME.text_secondary};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {THEME.border};
                background: {THEME.input_bg};
                border-radius: 2px;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {THEME.primary};
                background: {THEME.primary};
                border-radius: 2px;
            }}
            QComboBox {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 4px 8px;
                min-height: 20px;
            }}
            QComboBox:focus {{
                border: 1px solid {THEME.primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {THEME.text_secondary};
            }}
            QComboBox QAbstractItemView {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                color: {THEME.text_primary};
                selection-background-color: {THEME.bg_selected};
            }}
            QLineEdit {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 4px 8px;
                min-height: 20px;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME.primary};
            }}
            QPushButton {{
                background: {THEME.bg_component};
                border: 1px solid {THEME.border_light};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME.input_bg};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._enable_checkbox.toggled.connect(self._on_enable_changed)
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self._robot_combo.currentIndexChanged.connect(self._emit_override_changed)
        self._reason_edit.textChanged.connect(self._emit_override_changed)
        self._clear_btn.clicked.connect(self._on_clear_clicked)

        # Connect capability checkboxes
        for checkbox in self._capability_checks.values():
            checkbox.toggled.connect(self._emit_override_changed)

    def _on_enable_changed(self, enabled: bool) -> None:
        """Handle enable/disable toggle.

        Args:
            enabled: Whether override is enabled
        """
        self._is_enabled = enabled
        self._content_widget.setVisible(enabled)

        if enabled:
            self._emit_override_changed()
        else:
            self.override_cleared.emit()

        logger.debug(f"Robot override {'enabled' if enabled else 'disabled'}")

    def _on_mode_changed(self, index: int) -> None:
        """Handle mode change.

        Args:
            index: Selected mode index (0=Specific Robot, 1=By Capability)
        """
        is_specific = index == 0
        self._robot_group.setVisible(is_specific)
        self._capability_group.setVisible(not is_specific)
        self._emit_override_changed()

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self._enable_checkbox.setChecked(False)
        self._robot_combo.setCurrentIndex(-1)
        self._reason_edit.clear()
        for checkbox in self._capability_checks.values():
            checkbox.setChecked(False)
        self.override_cleared.emit()
        logger.debug("Robot override cleared")

    def _emit_override_changed(self) -> None:
        """Emit override configuration change."""
        if not self._is_enabled:
            return

        config = self.get_override()
        if config:
            self.override_changed.emit(config)
            logger.debug(f"Robot override changed: {config}")

    def set_override(self, override: dict[str, Any] | None) -> None:
        """
        Load existing override configuration into widget.

        Args:
            override: Override dict with keys:
                - robot_id: Optional specific robot ID
                - required_capabilities: List of capability strings
                - reason: Optional reason string
                - is_active: Whether override is active
        """
        if override is None:
            self._enable_checkbox.setChecked(False)
            return

        # Block signals while loading
        self._enable_checkbox.blockSignals(True)
        self._mode_combo.blockSignals(True)
        self._robot_combo.blockSignals(True)
        self._reason_edit.blockSignals(True)

        try:
            is_active = override.get("is_active", True)
            self._enable_checkbox.setChecked(is_active)
            self._content_widget.setVisible(is_active)

            robot_id = override.get("robot_id")
            capabilities = override.get("required_capabilities", [])

            if robot_id:
                # Specific robot mode
                self._mode_combo.setCurrentIndex(0)
                self._robot_group.setVisible(True)
                self._capability_group.setVisible(False)

                # Find and select robot
                for i in range(self._robot_combo.count()):
                    if self._robot_combo.itemData(i) == robot_id:
                        self._robot_combo.setCurrentIndex(i)
                        break
            else:
                # Capability mode
                self._mode_combo.setCurrentIndex(1)
                self._robot_group.setVisible(False)
                self._capability_group.setVisible(True)

                # Set capability checkboxes
                for cap_id, checkbox in self._capability_checks.items():
                    checkbox.blockSignals(True)
                    checkbox.setChecked(cap_id in capabilities)
                    checkbox.blockSignals(False)

            # Set reason
            self._reason_edit.setText(override.get("reason", "") or "")

        finally:
            self._enable_checkbox.blockSignals(False)
            self._mode_combo.blockSignals(False)
            self._robot_combo.blockSignals(False)
            self._reason_edit.blockSignals(False)

        logger.debug(f"Override loaded: {override}")

    def get_override(self) -> dict[str, Any] | None:
        """
        Get current override configuration from widget.

        Returns:
            Override dict or None if disabled. Dict contains:
                - robot_id: Specific robot ID (if specific mode)
                - required_capabilities: List of capability strings (if capability mode)
                - reason: Optional reason string
                - is_active: Always True when returned
        """
        if not self._is_enabled:
            return None

        is_specific = self._mode_combo.currentIndex() == 0

        config: dict[str, Any] = {
            "is_active": True,
            "reason": self._reason_edit.text().strip() or None,
        }

        if is_specific:
            robot_id = self._robot_combo.currentData()
            if robot_id:
                config["robot_id"] = robot_id
                config["required_capabilities"] = []
            else:
                # No robot selected, invalid config
                return None
        else:
            # Capability mode
            selected_caps = [
                cap_id
                for cap_id, checkbox in self._capability_checks.items()
                if checkbox.isChecked()
            ]
            if selected_caps:
                config["robot_id"] = None
                config["required_capabilities"] = selected_caps
            else:
                # No capabilities selected, invalid config
                return None

        return config

    def set_available_robots(self, robots: list[dict[str, Any]]) -> None:
        """
        Update robot dropdown with available robots.

        Args:
            robots: List of robot dicts with 'id', 'name', 'status' keys
        """
        self._available_robots = robots

        current_id = self._robot_combo.currentData()
        self._robot_combo.clear()

        for robot in robots:
            robot_id = robot.get("id", "")
            robot_name = robot.get("name", robot_id)
            robot_status = robot.get("status", "offline")

            # Format display text with status indicator
            status_indicator = {
                "online": "[Online]",
                "busy": "[Busy]",
                "offline": "[Offline]",
                "error": "[Error]",
                "maintenance": "[Maintenance]",
            }.get(robot_status, f"[{robot_status}]")

            display_text = f"{robot_name} {status_indicator}"
            self._robot_combo.addItem(display_text, robot_id)

        # Restore selection if possible
        if current_id:
            for i in range(self._robot_combo.count()):
                if self._robot_combo.itemData(i) == current_id:
                    self._robot_combo.setCurrentIndex(i)
                    break

        logger.debug(f"Available robots updated: {len(robots)} robots")

    def is_override_enabled(self) -> bool:
        """
        Check if override is currently enabled.

        Returns:
            True if override is enabled
        """
        return self._is_enabled

    def set_cloud_mode(self, enabled: bool) -> None:
        """
        Enable/disable based on cloud execution mode.

        When cloud mode is disabled, this widget should be hidden
        as robot overrides only apply to cloud execution.

        Args:
            enabled: Whether cloud execution mode is enabled
        """
        self.setVisible(enabled)
        if not enabled:
            self._enable_checkbox.setChecked(False)


__all__ = ["RobotOverrideWidget", "ROBOT_CAPABILITIES"]

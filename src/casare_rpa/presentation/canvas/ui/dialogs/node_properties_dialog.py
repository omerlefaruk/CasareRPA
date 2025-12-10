"""
Node Properties Dialog UI Component.

Modal dialog for editing comprehensive node properties.
"""

from typing import Optional, Any, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QGroupBox,
    QTabWidget,
    QWidget,
)
from PySide6.QtCore import Signal

from loguru import logger

from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    DialogStyles,
    DialogSize,
    apply_dialog_style,
    COLORS,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_dialog import AnimatedDialog


class NodePropertiesDialog(AnimatedDialog):
    """
    Dialog for editing node properties.

    Features:
    - Basic properties (name, description)
    - Input/output configuration
    - Advanced settings
    - Validation

    Signals:
        properties_changed: Emitted when properties are saved (dict: properties)
    """

    properties_changed = Signal(dict)

    def __init__(
        self,
        node_id: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize node properties dialog.

        Args:
            node_id: Node ID
            node_type: Node type name
            properties: Current node properties
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.node_id = node_id
        self.node_type = node_type
        self.properties = properties or {}
        self._property_widgets: Dict[str, QWidget] = {}

        self.setWindowTitle(f"Node Properties - {node_type}")
        self.setModal(True)

        # Apply standardized dialog styling
        apply_dialog_style(self, DialogSize.MD)

        self._setup_ui()
        self._load_properties()

        logger.debug(f"NodePropertiesDialog opened for {node_id}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel(self.node_type)
        header.setStyleSheet(DialogStyles.header(font_size=16))
        layout.addWidget(header)

        id_label = QLabel(f"ID: {self.node_id}")
        id_label.setStyleSheet(f"color: {COLORS.text_muted}; font-size: 10px;")
        layout.addWidget(id_label)

        # Tabs for different property categories
        self._tabs = QTabWidget()

        # Basic properties tab
        basic_tab = self._create_basic_tab()
        self._tabs.addTab(basic_tab, "Basic")

        # Advanced properties tab
        advanced_tab = self._create_advanced_tab()
        self._tabs.addTab(advanced_tab, "Advanced")

        layout.addWidget(self._tabs)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_basic_tab(self) -> QWidget:
        """
        Create basic properties tab.

        Returns:
            Basic properties widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Name and description group
        info_group = QGroupBox("Information")
        info_layout = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Node name")
        info_layout.addRow("Name:", self._name_edit)
        self._property_widgets["name"] = self._name_edit

        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Node description (optional)")
        self._description_edit.setMaximumHeight(80)
        info_layout.addRow("Description:", self._description_edit)
        self._property_widgets["description"] = self._description_edit

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Configuration group
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout()

        # These will be populated based on node type
        self._config_layout = config_layout

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        layout.addStretch()

        return widget

    def _create_advanced_tab(self) -> QWidget:
        """
        Create advanced properties tab.

        Returns:
            Advanced properties widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Execution settings group
        exec_group = QGroupBox("Execution Settings")
        exec_layout = QFormLayout()

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(0, 3600)
        self._timeout_spin.setSuffix(" seconds")
        self._timeout_spin.setSpecialValueText("No timeout")
        self._timeout_spin.setToolTip("Maximum execution time (0 = no limit)")
        exec_layout.addRow("Timeout:", self._timeout_spin)
        self._property_widgets["timeout"] = self._timeout_spin

        self._retry_spin = QSpinBox()
        self._retry_spin.setRange(0, 10)
        self._retry_spin.setToolTip("Number of retry attempts on failure")
        exec_layout.addRow("Retry Count:", self._retry_spin)
        self._property_widgets["retry_count"] = self._retry_spin

        self._continue_on_error = QCheckBox("Continue workflow on error")
        exec_layout.addRow("Error Handling:", self._continue_on_error)
        self._property_widgets["continue_on_error"] = self._continue_on_error

        exec_group.setLayout(exec_layout)
        layout.addWidget(exec_group)

        # Logging settings group
        log_group = QGroupBox("Logging Settings")
        log_layout = QFormLayout()

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        self._log_level_combo.setCurrentText("Info")
        log_layout.addRow("Log Level:", self._log_level_combo)
        self._property_widgets["log_level"] = self._log_level_combo

        self._log_output = QCheckBox("Log execution output")
        self._log_output.setChecked(True)
        log_layout.addRow("Output:", self._log_output)
        self._property_widgets["log_output"] = self._log_output

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()

        return widget

    def _load_properties(self) -> None:
        """Load current properties into widgets."""
        # Load basic properties
        if "name" in self.properties:
            self._name_edit.setText(str(self.properties["name"]))

        if "description" in self.properties:
            self._description_edit.setPlainText(str(self.properties["description"]))

        # Load advanced properties
        if "timeout" in self.properties:
            self._timeout_spin.setValue(int(self.properties["timeout"]))

        if "retry_count" in self.properties:
            self._retry_spin.setValue(int(self.properties["retry_count"]))

        if "continue_on_error" in self.properties:
            self._continue_on_error.setChecked(
                bool(self.properties["continue_on_error"])
            )

        if "log_level" in self.properties:
            self._log_level_combo.setCurrentText(str(self.properties["log_level"]))

        if "log_output" in self.properties:
            self._log_output.setChecked(bool(self.properties["log_output"]))

    def _gather_properties(self) -> Dict[str, Any]:
        """
        Gather properties from widgets.

        Returns:
            Dictionary of all properties
        """
        properties = {}

        # Basic properties
        properties["name"] = self._name_edit.text()
        properties["description"] = self._description_edit.toPlainText()

        # Advanced properties
        properties["timeout"] = self._timeout_spin.value()
        properties["retry_count"] = self._retry_spin.value()
        properties["continue_on_error"] = self._continue_on_error.isChecked()
        properties["log_level"] = self._log_level_combo.currentText()
        properties["log_output"] = self._log_output.isChecked()

        return properties

    def _validate(self) -> bool:
        """
        Validate property values.

        Returns:
            True if validation passes
        """
        # Ensure name is not empty
        if not self._name_edit.text().strip():
            logger.warning("Node name cannot be empty")
            return False

        return True

    def _on_accept(self) -> None:
        """Handle dialog accept."""
        if not self._validate():
            return

        properties = self._gather_properties()
        self.properties_changed.emit(properties)
        self.accept()

        logger.debug(f"Node properties saved for {self.node_id}")

    def get_properties(self) -> Dict[str, Any]:
        """
        Get the current properties.

        Returns:
            Dictionary of properties
        """
        return self._gather_properties()

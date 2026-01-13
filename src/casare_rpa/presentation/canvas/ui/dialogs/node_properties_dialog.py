"""
Node Properties Dialog UI Component.

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.

Modal dialog for editing comprehensive node properties.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)


class NodePropertiesDialog(BaseDialogV2):
    """
    Dialog for editing node properties.

    Migrated to BaseDialogV2 (Epic 7.x).

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
        properties: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize node properties dialog.

        Args:
            node_id: Node ID
            node_type: Node type name
            properties: Current node properties
            parent: Optional parent widget
        """
        self.node_id = node_id
        self.node_type = node_type
        self.properties = properties or {}
        self._property_widgets: dict[str, QWidget] = {}

        super().__init__(
            title=f"Node Properties - {node_type}",
            parent=parent,
            size=DialogSizeV2.MD,
        )

        self._setup_content()
        self._load_properties()

        logger.debug(f"NodePropertiesDialog opened for {node_id}")

    def _setup_content(self) -> None:
        """Set up the dialog content."""
        # Main content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Header
        header = QLabel(self.node_type)
        header.setStyleSheet(f"""
            font-size: {TOKENS_V2.typography.heading_lg}px;
            font-weight: {TOKENS_V2.typography.weight_semibold};
            color: {THEME_V2.text_primary};
        """)
        layout.addWidget(header)

        id_label = QLabel(f"ID: {self.node_id}")
        id_label.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.caption}px;
        """)
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

        # Set content and buttons
        self.set_body_widget(content)
        self.set_primary_button("Save", self._on_accept)
        self.set_secondary_button("Cancel", self.reject)

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
        info_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.body}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.lg}px;
                padding-top: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.lg}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)
        info_layout = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Node name")
        self._name_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QLineEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        info_layout.addRow("Name:", self._name_edit)
        self._property_widgets["name"] = self._name_edit

        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Node description (optional)")
        self._description_edit.setMaximumHeight(80)
        self._description_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QTextEdit:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        info_layout.addRow("Description:", self._description_edit)
        self._property_widgets["description"] = self._description_edit

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Configuration group
        config_group = QGroupBox("Configuration")
        config_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.body}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.lg}px;
                padding-top: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.lg}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)
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
        exec_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.body}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.lg}px;
                padding-top: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.lg}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)
        exec_layout = QFormLayout()

        self._timeout_spin = QSpinBox()
        self._timeout_spin.setRange(0, 3600)
        self._timeout_spin.setSuffix(" seconds")
        self._timeout_spin.setSpecialValueText("No timeout")
        self._timeout_spin.setToolTip("Maximum execution time (0 = no limit)")
        self._timeout_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QSpinBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        exec_layout.addRow("Timeout:", self._timeout_spin)
        self._property_widgets["timeout"] = self._timeout_spin

        self._retry_spin = QSpinBox()
        self._retry_spin.setRange(0, 10)
        self._retry_spin.setStyleSheet(f"""
            QSpinBox {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QSpinBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        self._retry_spin.setToolTip("Number of retry attempts on failure")
        exec_layout.addRow("Retry Count:", self._retry_spin)
        self._property_widgets["retry_count"] = self._retry_spin

        self._continue_on_error = QCheckBox("Continue workflow on error")
        self._continue_on_error.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                spacing: {TOKENS_V2.spacing.sm}px;
            }}
        """)
        exec_layout.addRow("Error Handling:", self._continue_on_error)
        self._property_widgets["continue_on_error"] = self._continue_on_error

        exec_group.setLayout(exec_layout)
        layout.addWidget(exec_group)

        # Logging settings group
        log_group = QGroupBox("Logging Settings")
        log_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.body}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.lg}px;
                padding-top: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.lg}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)
        log_layout = QFormLayout()

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        self._log_level_combo.setCurrentText("Info")
        self._log_level_combo.setStyleSheet(f"""
            QComboBox {{
                background: {THEME_V2.bg_input};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QComboBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """)
        log_layout.addRow("Log Level:", self._log_level_combo)
        self._property_widgets["log_level"] = self._log_level_combo

        self._log_output = QCheckBox("Log execution output")
        self._log_output.setChecked(True)
        self._log_output.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                spacing: {TOKENS_V2.spacing.sm}px;
            }}
        """)
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
            self._continue_on_error.setChecked(bool(self.properties["continue_on_error"]))

        if "log_level" in self.properties:
            self._log_level_combo.setCurrentText(str(self.properties["log_level"]))

        if "log_output" in self.properties:
            self._log_output.setChecked(bool(self.properties["log_output"]))

    def _gather_properties(self) -> dict[str, Any]:
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

    def validate(self) -> bool:
        """
        Validate property values.

        Returns:
            True if validation passes
        """
        # Ensure name is not empty
        if not self._name_edit.text().strip():
            self.set_validation_error("Node name cannot be empty")
            return False

        return True

    def _on_accept(self) -> None:
        """Handle dialog accept."""
        properties = self._gather_properties()
        self.properties_changed.emit(properties)
        self.accept()

        logger.debug(f"Node properties saved for {self.node_id}")

    def get_properties(self) -> dict[str, Any]:
        """
        Get the current properties.

        Returns:
            Dictionary of properties
        """
        return self._gather_properties()

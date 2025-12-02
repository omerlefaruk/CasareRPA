"""
Properties Panel UI Component.

Dockable panel that displays and edits properties of the selected node.
Extracted from canvas/panels/properties_panel.py for reusability.
"""

from typing import Optional, Any, Dict, List, TYPE_CHECKING

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QComboBox,
    QTextEdit,
    QScrollArea,
    QFrame,
    QPushButton,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from loguru import logger
from ..widgets.robot_override_widget import RobotOverrideWidget

if TYPE_CHECKING:
    from NodeGraphQt import BaseNode


class CollapsibleSection(QWidget):
    """
    A collapsible section widget with header and content area.

    Provides expandable/collapsible sections similar to UiPath, n8n, and VS Code.
    """

    def __init__(self, title: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize collapsible section.

        Args:
            title: Section title
            parent: Optional parent widget
        """
        super().__init__(parent)
        self._is_collapsed = False
        self._title = title

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self._header = QPushButton(f"▼ {self._title}")
        self._header.setStyleSheet("""
            QPushButton {
                background: #3d3d3d;
                border: none;
                color: #e0e0e0;
                padding: 6px 10px;
                text-align: left;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        self._header.clicked.connect(self._toggle)
        layout.addWidget(self._header)

        # Content container
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 5, 10, 10)
        self._content_layout.setSpacing(8)
        layout.addWidget(self._content)

    def _toggle(self) -> None:
        """Toggle section collapsed state."""
        self._is_collapsed = not self._is_collapsed
        self._content.setVisible(not self._is_collapsed)
        arrow = "▶" if self._is_collapsed else "▼"
        self._header.setText(f"{arrow} {self._title}")

    def add_widget(self, widget: QWidget) -> None:
        """
        Add widget to content area.

        Args:
            widget: Widget to add
        """
        self._content_layout.addWidget(widget)

    def add_property_row(self, label: str, widget: QWidget) -> QWidget:
        """
        Add a label + widget row to content area.

        Args:
            label: Property label text
            widget: Property input widget

        Returns:
            Row container widget
        """
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setMinimumWidth(80)
        lbl.setStyleSheet("color: #a0a0a0;")
        row_layout.addWidget(lbl)

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        row_layout.addWidget(widget)

        self._content_layout.addWidget(row)
        return row


class PropertiesPanel(QDockWidget):
    """
    Dockable properties panel for editing selected node properties.

    Features:
    - Node information display (name, type, ID)
    - Collapsible property sections
    - Type-aware property editors
    - Real-time property updates

    Signals:
        property_changed: Emitted when property value changes (str: node_id, str: property_name, object: value)
        robot_override_changed: Emitted when node robot override changes (str: node_id, dict: override_config)
        robot_override_cleared: Emitted when node robot override is cleared (str: node_id)
    """

    property_changed = Signal(str, str, object)
    robot_override_changed = Signal(str, dict)
    robot_override_cleared = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the properties panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Properties", parent)
        self.setObjectName("PropertiesDock")

        self._current_node: Optional["BaseNode"] = None
        self._property_widgets: Dict[str, QWidget] = {}
        self._cloud_mode_enabled: bool = False
        self._available_robots: List[Dict[str, Any]] = []

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("PropertiesPanel initialized")

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
        self.setMinimumWidth(250)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Main container
        self._container = QWidget()
        self._main_layout = QVBoxLayout(self._container)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Header with node info
        self._header = QWidget()
        header_layout = QVBoxLayout(self._header)
        header_layout.setContentsMargins(10, 10, 10, 10)

        self._node_name_label = QLabel("No Selection")
        self._node_name_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #e0e0e0;
        """)
        header_layout.addWidget(self._node_name_label)

        self._node_type_label = QLabel("")
        self._node_type_label.setStyleSheet("color: #888888; font-size: 11px;")
        header_layout.addWidget(self._node_type_label)

        self._node_id_label = QLabel("")
        self._node_id_label.setStyleSheet("color: #666666; font-size: 10px;")
        header_layout.addWidget(self._node_id_label)

        self._main_layout.addWidget(self._header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #3d3d3d;")
        self._main_layout.addWidget(sep)

        # Properties content area
        self._properties_container = QWidget()
        self._properties_layout = QVBoxLayout(self._properties_container)
        self._properties_layout.setContentsMargins(0, 0, 0, 0)
        self._properties_layout.setSpacing(0)
        self._main_layout.addWidget(self._properties_container)

        # No selection message
        self._no_selection = QLabel("Select a node to view its properties")
        self._no_selection.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_selection.setStyleSheet("color: #666666; padding: 20px;")
        self._properties_layout.addWidget(self._no_selection)

        # Robot Override Section (for cloud execution mode)
        self._robot_override_section = self._create_target_robot_section()
        self._main_layout.addWidget(self._robot_override_section)
        self._robot_override_section.hide()  # Hidden until cloud mode enabled

        # Stretch at bottom
        self._main_layout.addStretch()

        scroll.setWidget(self._container)
        self.setWidget(scroll)

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
            QScrollArea {
                background: #252525;
                border: none;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #5a8a9a;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
            }
        """)

    def set_node(self, node: Optional["BaseNode"]) -> None:
        """
        Set the node to display properties for.

        Args:
            node: The selected node, or None to clear
        """
        self._current_node = node
        self._clear_properties()

        if node is None:
            self._node_name_label.setText("No Selection")
            self._node_type_label.setText("")
            self._node_id_label.setText("")
            self._no_selection.show()
            self._robot_override_section.hide()
            return

        self._no_selection.hide()

        # Show robot override section if cloud mode is enabled
        self._robot_override_section.setVisible(self._cloud_mode_enabled)

        # Update header
        self._node_name_label.setText(node.name() if hasattr(node, "name") else "Node")
        node_type = node.__class__.__name__
        self._node_type_label.setText(f"Type: {node_type}")
        node_id = node.get_property("node_id") if hasattr(node, "get_property") else ""
        self._node_id_label.setText(
            f"ID: {node_id[:20]}..." if len(str(node_id)) > 20 else f"ID: {node_id}"
        )

        # Build property sections
        self._build_properties(node)

        # Clear robot override widget for the new node
        # The actual override will be loaded by the controller if one exists
        self._robot_override_widget.set_override(None)

    def _clear_properties(self) -> None:
        """Clear all property widgets."""
        self._property_widgets.clear()

        # Remove all widgets from properties layout except no_selection
        while self._properties_layout.count() > 1:
            item = self._properties_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

    def _build_properties(self, node: "BaseNode") -> None:
        """
        Build property widgets for the node.

        Args:
            node: Node to display properties for
        """
        # Get casare_node config (source of truth for execution)
        casare_node = (
            node.get_casare_node() if hasattr(node, "get_casare_node") else None
        )

        if casare_node and hasattr(casare_node, "config"):
            config = casare_node.config

            # Config properties section
            if config:
                config_section = CollapsibleSection("Configuration")

                for prop_name, prop_value in config.items():
                    # Skip internal properties
                    if prop_name.startswith("_"):
                        continue

                    widget = self._create_property_widget(prop_name, prop_value, node)
                    if widget:
                        config_section.add_property_row(prop_name, widget)
                        self._property_widgets[prop_name] = widget

                self._properties_layout.addWidget(config_section)

        # Node-specific inputs section (port default values)
        if casare_node and hasattr(casare_node, "input_ports"):
            inputs_section = CollapsibleSection("Inputs")

            for port_name, port in casare_node.input_ports.items():
                if hasattr(port, "default_value"):
                    widget = self._create_property_widget(
                        port_name, port.default_value, node
                    )
                    if widget:
                        inputs_section.add_property_row(port_name, widget)

            self._properties_layout.addWidget(inputs_section)

    def _create_property_widget(
        self, name: str, value: Any, node: "BaseNode"
    ) -> Optional[QWidget]:
        """
        Create an appropriate widget for the property type.

        Args:
            name: Property name
            value: Property value
            node: Node instance

        Returns:
            Property editor widget or None
        """
        if isinstance(value, bool):
            widget = QCheckBox()
            widget.setChecked(value)
            widget.toggled.connect(lambda v, n=name: self._on_property_changed(n, v))
            return widget

        elif isinstance(value, int):
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
            widget.setValue(value)
            widget.valueChanged.connect(
                lambda v, n=name: self._on_property_changed(n, v)
            )
            return widget

        elif isinstance(value, float):
            widget = QDoubleSpinBox()
            widget.setRange(-999999.0, 999999.0)
            widget.setDecimals(3)
            widget.setValue(value)
            widget.valueChanged.connect(
                lambda v, n=name: self._on_property_changed(n, v)
            )
            return widget

        elif isinstance(value, str):
            if len(value) > 100 or "\n" in value:
                widget = QTextEdit()
                widget.setPlainText(value)
                widget.setMaximumHeight(80)
                widget.textChanged.connect(
                    lambda n=name, w=widget: self._on_property_changed(
                        n, w.toPlainText()
                    )
                )
            else:
                widget = QLineEdit()
                widget.setText(value)
                widget.textChanged.connect(
                    lambda v, n=name: self._on_property_changed(n, v)
                )
            return widget

        elif isinstance(value, list) and all(isinstance(v, str) for v in value):
            widget = QComboBox()
            widget.addItems(value)
            widget.currentTextChanged.connect(
                lambda v, n=name: self._on_property_changed(n, v)
            )
            return widget

        else:
            # Fallback: display as read-only text
            widget = QLineEdit()
            widget.setText(str(value))
            widget.setReadOnly(True)
            widget.setStyleSheet("background: #2d2d2d; color: #888888;")
            return widget

    def _on_property_changed(self, name: str, value: Any) -> None:
        """
        Handle property value change.

        Args:
            name: Property name
            value: New property value
        """
        if self._current_node:
            node_id = (
                self._current_node.get_property("node_id")
                if hasattr(self._current_node, "get_property")
                else ""
            )
            self.property_changed.emit(node_id, name, value)
            logger.debug(f"Property changed: {name} = {value}")

    def _create_target_robot_section(self) -> QWidget:
        """
        Create the target robot override section.

        Collapsible section for robot targeting with:
        - Checkbox: "Override workflow default"
        - Dropdown: Select specific robot OR
        - Multi-select: Required capabilities
        - Text field: Reason for override

        Returns:
            Container widget with robot override controls
        """
        section = CollapsibleSection("Target Robot")

        # Create robot override widget
        self._robot_override_widget = RobotOverrideWidget()
        section.add_widget(self._robot_override_widget)

        # Connect signals
        self._robot_override_widget.override_changed.connect(
            self._on_robot_override_changed
        )
        self._robot_override_widget.override_cleared.connect(
            self._on_robot_override_cleared
        )

        return section

    def _on_robot_override_changed(self, config: Dict[str, Any]) -> None:
        """
        Handle robot override configuration change.

        Args:
            config: Override configuration dictionary
        """
        if self._current_node:
            node_id = (
                self._current_node.get_property("node_id")
                if hasattr(self._current_node, "get_property")
                else ""
            )
            if node_id:
                self.robot_override_changed.emit(node_id, config)
                logger.debug(f"Robot override changed for node {node_id}: {config}")

                # Update visual indicator on node
                self._update_node_override_indicator(True)

    def _on_robot_override_cleared(self) -> None:
        """Handle robot override being cleared."""
        if self._current_node:
            node_id = (
                self._current_node.get_property("node_id")
                if hasattr(self._current_node, "get_property")
                else ""
            )
            if node_id:
                self.robot_override_cleared.emit(node_id)
                logger.debug(f"Robot override cleared for node {node_id}")

                # Update visual indicator on node
                self._update_node_override_indicator(False)

    def _update_node_override_indicator(self, has_override: bool) -> None:
        """
        Update the visual indicator on the current node.

        Args:
            has_override: Whether the node has a robot override
        """
        if self._current_node and hasattr(self._current_node, "view"):
            view = self._current_node.view
            if hasattr(view, "set_robot_override"):
                view.set_robot_override(has_override)

    def set_cloud_mode(self, enabled: bool) -> None:
        """
        Enable or disable cloud execution mode.

        When cloud mode is enabled, the robot override section is shown.
        Robot overrides only apply to cloud execution.

        Args:
            enabled: Whether cloud execution mode is enabled
        """
        self._cloud_mode_enabled = enabled
        self._robot_override_section.setVisible(
            enabled and self._current_node is not None
        )
        self._robot_override_widget.set_cloud_mode(enabled)
        logger.debug(f"Cloud mode {'enabled' if enabled else 'disabled'}")

    def set_available_robots(self, robots: List[Dict[str, Any]]) -> None:
        """
        Update the list of available robots for selection.

        Args:
            robots: List of robot dictionaries with id, name, status keys
        """
        self._available_robots = robots
        self._robot_override_widget.set_available_robots(robots)

    def set_node_override(self, override: Optional[Dict[str, Any]]) -> None:
        """
        Set the current node's robot override configuration.

        Called when a node is selected to load its existing override.

        Args:
            override: Override configuration dict or None
        """
        self._robot_override_widget.set_override(override)

    def refresh(self) -> None:
        """Refresh the properties display."""
        if self._current_node:
            self.set_node(self._current_node)

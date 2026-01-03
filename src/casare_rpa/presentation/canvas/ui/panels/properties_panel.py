"""
Properties Panel (Inspector) for CasareRPA Canvas.

Epic 6.1 Upgrade: Dockable panel that embeds InspectorContent for node property editing.
Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QDockWidget, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.popups.inspector_v2 import InspectorContent


class PropertiesPanel(QDockWidget):
    """
    Dockable panel that displays properties for the selected node.

    Features:
    - Searchable property list via InspectorContent
    - Type badges and inline editing
    - Persistent state between selections
    - v2 design system integration

    Signals:
        property_changed: Emitted when a property is edited (node_id, key, value)
    """

    property_changed = Signal(str, str, object)  # node_id, key, value

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the properties panel."""
        super().__init__("Properties", parent)
        self.setObjectName("PropertiesDock")

        self._current_node_id: str | None = None

        self._setup_dock()
        self._setup_ui()

        logger.debug("PropertiesPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        # Dock-only: NO DockWidgetFloatable (v2 requirement)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.setMinimumWidth(TOKENS_V2.sizes.panel_min_width)

    def _setup_ui(self) -> None:
        """Set up the content widget."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.sm,
        )
        layout.setSpacing(0)

        # Use InspectorContent for property display/search
        self._inspector = InspectorContent()
        layout.addWidget(self._inspector)

        self.setWidget(container)

    # ==================== Public API ====================

    @Slot(str, dict)
    def set_node_properties(self, node_id: str, properties: dict[str, Any]) -> None:
        """
        Update the panel to show properties for a specific node.

        Args:
            node_id: Identifier of the selected node
            properties: Dictionary of properties to display
        """
        self._current_node_id = node_id
        self._inspector.clear_properties()

        for key, value in properties.items():
            # Skip internal properties (starting with underscore)
            if key.startswith("_") and key not in ("_disabled", "_cache_enabled"):
                continue

            row = self._inspector.add_property(key, value, editable=True)

            # Connect row value changes to our signal
            # Note: We need to handle this carefully to include node_id
            self._connect_row_signal(row, key)

        logger.debug(f"PropertiesPanel: updated for node {node_id}")

    def _connect_row_signal(self, row: Any, key: str) -> None:
        """Connect individual property row signals with closure for node_id."""
        if hasattr(row, "_value_editor"):
            original_handler = row._on_edit_finished

            def wrapped_handler() -> None:
                original_handler()
                if self._current_node_id:
                    new_value = row.get_value()
                    self.property_changed.emit(self._current_node_id, key, new_value)

            row._value_editor.editingFinished.connect(wrapped_handler)

    def clear(self) -> None:
        """Clear all properties from the display."""
        self._current_node_id = None
        self._inspector.clear_properties()
        logger.debug("PropertiesPanel: cleared")


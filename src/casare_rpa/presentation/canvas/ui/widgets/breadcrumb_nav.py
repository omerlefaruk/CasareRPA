"""
Breadcrumb Navigation Widget for Subflow Navigation.

Minimal breadcrumb display: root / SubflowName
- Hidden when at root level
- Visible when inside a subflow
- Click "root" to navigate back to main workflow
- Press C key to go back one level

Example display: root / My Subflow
"""

from typing import Optional, List
from dataclasses import dataclass, field

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QCursor

from loguru import logger

from casare_rpa.presentation.canvas.theme import THEME


@dataclass
class BreadcrumbItem:
    """Single breadcrumb navigation item."""

    id: str  # Workflow or subflow ID
    name: str  # Display name
    path: Optional[str] = None  # File path if applicable
    data: dict = field(
        default_factory=dict
    )  # Additional data (nodes, connections, etc.)


class BreadcrumbButton(QPushButton):
    """Clickable breadcrumb segment."""

    def __init__(self, item: BreadcrumbItem, is_current: bool = False, parent=None):
        super().__init__(item.name, parent)
        self.item = item
        self.is_current = is_current

        self.setFlat(True)
        if not is_current:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.adjustSize()

        self._apply_style()

    def _apply_style(self) -> None:
        """Apply visual styling based on state using THEME constants."""
        if self.is_current:
            # Current level - bold white, not clickable
            self.setStyleSheet(f"""
                QPushButton {{
                    color: {THEME.text_primary};
                    background: transparent;
                    border: none;
                    padding: 0 2px;
                    font-weight: bold;
                    font-size: 11px;
                }}
            """)
        else:
            # Clickable parent - light blue, underline on hover
            self.setStyleSheet(f"""
                QPushButton {{
                    color: {THEME.accent_primary};
                    background: transparent;
                    border: none;
                    padding: 0 2px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    text-decoration: underline;
                }}
            """)


class BreadcrumbSeparator(QLabel):
    """Separator between breadcrumb items (/)."""

    def __init__(self, parent=None):
        super().__init__("/", parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {THEME.text_disabled};
                padding: 0 3px;
                font-size: 11px;
            }}
        """)


class BreadcrumbNavWidget(QFrame):
    """
    Minimal breadcrumb navigation for subflow navigation.

    Displays: root / SubflowName
    - Hidden at root level
    - Click parent names to navigate back

    Signals:
        navigate_to: Emitted when user clicks a breadcrumb (item_id, level_index)
        navigate_back: Emitted when going back (C key)
    """

    # Signal emitted when navigating to a specific level
    navigate_to = Signal(str, int)  # (item_id, level_index)

    # Signal emitted when going back one level
    navigate_back = Signal()

    # Signal emitted when diving into subflow
    dive_in = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Navigation stack
        self._items: List[BreadcrumbItem] = []
        self._current_index: int = -1

        self._setup_ui()
        self._apply_style()

        # Initially hidden until we're inside a subflow
        self.hide()

    def _setup_ui(self) -> None:
        """Setup the breadcrumb UI - minimal design, no back button."""
        self.setFixedHeight(24)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        # Container for breadcrumb items only (no back button - use C key)
        self._breadcrumb_container = QWidget()
        self._breadcrumb_container.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self._breadcrumb_layout = QHBoxLayout(self._breadcrumb_container)
        self._breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self._breadcrumb_layout.setSpacing(0)
        layout.addWidget(self._breadcrumb_container)

    def _apply_style(self) -> None:
        """Apply widget styling - subtle semi-transparent background using THEME."""
        self.setStyleSheet("""
            BreadcrumbNavWidget {
                background-color: rgba(25, 25, 25, 0.85);
                border: none;
                border-radius: 4px;
            }
        """)

    def set_path(self, items: List[BreadcrumbItem]) -> None:
        """
        Set the breadcrumb path.

        Args:
            items: List of BreadcrumbItem from root to current
        """
        self._items = items
        self._current_index = len(items) - 1
        self._rebuild_breadcrumbs()

        # Show if we're inside a subflow (more than 1 level)
        if len(items) > 1:
            self.show()
        else:
            self.hide()

    def push(self, item: BreadcrumbItem) -> None:
        """
        Push a new level onto the navigation stack.

        Args:
            item: The subflow to dive into
        """
        self._items.append(item)
        self._current_index = len(self._items) - 1
        self._rebuild_breadcrumbs()

        if len(self._items) > 1:
            self.show()

        logger.debug(f"Breadcrumb: pushed '{item.name}', depth={len(self._items)}")

    def pop(self) -> Optional[BreadcrumbItem]:
        """
        Pop the current level and go back to parent.

        Returns:
            The popped item, or None if at root
        """
        if len(self._items) <= 1:
            return None

        popped = self._items.pop()
        self._current_index = len(self._items) - 1
        self._rebuild_breadcrumbs()

        if len(self._items) <= 1:
            self.hide()

        logger.debug(f"Breadcrumb: popped '{popped.name}', depth={len(self._items)}")
        return popped

    def navigate_to_level(self, index: int) -> List[BreadcrumbItem]:
        """
        Navigate to a specific level, popping all deeper levels.

        Args:
            index: The level index to navigate to

        Returns:
            List of popped items
        """
        if index < 0 or index >= len(self._items):
            return []

        popped = self._items[index + 1 :]
        self._items = self._items[: index + 1]
        self._current_index = index
        self._rebuild_breadcrumbs()

        if len(self._items) <= 1:
            self.hide()

        return popped

    def get_current(self) -> Optional[BreadcrumbItem]:
        """Get the current breadcrumb item."""
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return None

    def get_parent(self) -> Optional[BreadcrumbItem]:
        """Get the parent breadcrumb item."""
        if self._current_index > 0:
            return self._items[self._current_index - 1]
        return None

    def get_path(self) -> List[BreadcrumbItem]:
        """Get the full navigation path."""
        return self._items.copy()

    def get_depth(self) -> int:
        """Get the current navigation depth."""
        return len(self._items)

    def is_at_root(self) -> bool:
        """Check if at root level (main workflow)."""
        return len(self._items) <= 1

    def clear(self) -> None:
        """Clear the navigation stack."""
        self._items.clear()
        self._current_index = -1
        self._rebuild_breadcrumbs()
        self.hide()

    def _rebuild_breadcrumbs(self) -> None:
        """Rebuild the breadcrumb buttons."""
        # Clear existing
        while self._breadcrumb_layout.count():
            item = self._breadcrumb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add breadcrumb buttons
        for i, item in enumerate(self._items):
            is_current = i == len(self._items) - 1

            # Add separator before non-first items
            if i > 0:
                sep = BreadcrumbSeparator()
                self._breadcrumb_layout.addWidget(sep)

            # Add button
            btn = BreadcrumbButton(item, is_current)
            if not is_current:
                btn.clicked.connect(
                    lambda checked, idx=i: self._on_breadcrumb_clicked(idx)
                )
            self._breadcrumb_layout.addWidget(btn)

        # Resize widget to fit content
        self.adjustSize()

    def _on_breadcrumb_clicked(self, index: int) -> None:
        """Handle click on a breadcrumb item."""
        if index < len(self._items) - 1:
            item = self._items[index]
            self.navigate_to.emit(item.id, index)

    def _on_back_clicked(self) -> None:
        """Handle back button click."""
        self.navigate_back.emit()


class SubflowNavigationController:
    """
    Controller for subflow navigation.

    Manages the state of diving into and out of subflows,
    coordinating between the canvas, breadcrumb widget, and workflow data.
    """

    def __init__(self, graph_widget, breadcrumb: BreadcrumbNavWidget, main_window=None):
        self._graph = graph_widget
        self._breadcrumb = breadcrumb
        self._main_window = main_window

        # Stack of saved workflow states for going back
        self._state_stack: List[dict] = []

        # Connect signals
        self._breadcrumb.navigate_back.connect(self.go_back)
        self._breadcrumb.navigate_to.connect(self._on_navigate_to)

    def set_main_window(self, main_window) -> None:
        """Set the main window reference for serialization."""
        self._main_window = main_window

    def initialize(
        self, workflow_name: str = "Main Workflow", workflow_id: str = "main"
    ) -> None:
        """
        Initialize with the root workflow.

        Args:
            workflow_name: Display name of the main workflow
            workflow_id: ID of the main workflow
        """
        root = BreadcrumbItem(
            id=workflow_id,
            name=workflow_name,
        )
        self._breadcrumb.set_path([root])
        self._state_stack.clear()

    def can_dive_in(self) -> bool:
        """Check if we can dive into the selected node."""
        selected = self._graph.selected_nodes()
        if len(selected) != 1:
            return False

        node = selected[0]

        # Check if it's a subflow node
        return (
            hasattr(node, "__identifier__") and "subflow" in node.__identifier__.lower()
        )

    def dive_in(self) -> bool:
        """
        Dive into the selected subflow.

        Returns:
            True if successfully dived in
        """
        if not self.can_dive_in():
            logger.warning("Cannot dive in: no subflow node selected")
            return False

        node = self._graph.selected_nodes()[0]

        # Get subflow info
        subflow_id = (
            node.get_property("subflow_id") if hasattr(node, "get_property") else None
        )
        subflow_name = (
            node.get_property("subflow_name")
            if hasattr(node, "get_property")
            else "Subflow"
        )
        subflow_path = (
            node.get_property("subflow_path") if hasattr(node, "get_property") else None
        )

        if not subflow_id and not subflow_path:
            logger.warning("Cannot dive in: subflow not configured")
            return False

        # Save current state
        self._save_current_state()

        # Load subflow content
        success = self._load_subflow(subflow_id, subflow_path, subflow_name)

        if success:
            # Push to breadcrumb
            item = BreadcrumbItem(
                id=subflow_id or subflow_path,
                name=subflow_name,
                path=subflow_path,
            )
            self._breadcrumb.push(item)
        else:
            # Restore state on failure
            self._restore_state(self._state_stack.pop())

        return success

    def go_back(self) -> bool:
        """
        Go back to the parent workflow.

        Returns:
            True if successfully went back
        """
        if self._breadcrumb.is_at_root():
            logger.debug("Already at root, cannot go back")
            return False

        if not self._state_stack:
            logger.warning("No saved state to restore")
            return False

        # Save current subflow state before leaving
        current = self._breadcrumb.get_current()
        if current and current.path:
            self._save_subflow_state(current.path)

        # Pop breadcrumb
        popped = self._breadcrumb.pop()

        # Restore parent state
        state = self._state_stack.pop()
        self._restore_state(state)

        logger.debug(f"Went back from: {popped.name if popped else 'unknown'}")
        return True

    def navigate_to_level(self, level_index: int) -> None:
        """
        Navigate to a specific level in the breadcrumb.

        Args:
            level_index: The level to navigate to (0 = root)
        """
        # Save current subflow state before navigating away
        current = self._breadcrumb.get_current()
        if current and current.path:
            self._save_subflow_state(current.path)

        # Navigate breadcrumb first
        self._breadcrumb.navigate_to_level(level_index)

        # Restore state at target level
        if level_index == 0:
            # Going to root - restore first saved state (the root workflow)
            if self._state_stack:
                state = self._state_stack[0]
                self._restore_state(state)
                self._state_stack.clear()
                logger.debug("Restored root workflow state")
        else:
            # Pop states after target level, then restore
            while len(self._state_stack) > level_index:
                self._state_stack.pop()
            if self._state_stack:
                state = self._state_stack[-1]
                self._restore_state(state)

    def _on_navigate_to(self, item_id: str, level_index: int) -> None:
        """Handle navigation signal from breadcrumb widget."""
        self.navigate_to_level(level_index)

    def _save_current_state(self) -> None:
        """Save the current canvas state for later restoration."""
        try:
            # Use WorkflowSerializer for proper state capture
            from casare_rpa.presentation.canvas.serialization import WorkflowSerializer

            if self._main_window:
                serializer = WorkflowSerializer(self._graph, self._main_window)
                state = serializer.serialize()
                self._state_stack.append(state)
                node_count = len(state.get("nodes", {}))
                conn_count = len(state.get("connections", []))
                logger.debug(
                    f"Saved workflow state: {node_count} nodes, {conn_count} connections"
                )
            else:
                # Fallback: minimal state capture
                logger.warning("No main_window - using minimal state capture")
                state = {
                    "nodes": {},
                    "connections": [],
                    "variables": {},
                    "frames": [],
                    "settings": {},
                    "metadata": {"name": "Saved State"},
                }
                self._state_stack.append(state)

        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def _restore_state(self, state: dict) -> None:
        """Restore a saved canvas state."""
        try:
            # Use WorkflowDeserializer for proper state restoration
            from casare_rpa.presentation.canvas.serialization import (
                WorkflowDeserializer,
            )

            node_count = len(state.get("nodes", {}))
            conn_count = len(state.get("connections", []))
            logger.debug(
                f"Restoring workflow state: {node_count} nodes, {conn_count} connections"
            )

            if self._main_window:
                deserializer = WorkflowDeserializer(self._graph, self._main_window)
                success = deserializer.deserialize(state)
                if not success:
                    logger.error("Failed to deserialize saved state")
            else:
                logger.warning("No main_window - cannot restore state properly")
                self._graph.clear_session()

        except Exception as e:
            logger.error(f"Failed to restore state: {e}")

    def _save_subflow_state(self, subflow_path: str) -> bool:
        """
        Save the current canvas state back to the subflow file.

        This preserves changes made while editing inside a subflow.

        Args:
            subflow_path: File path to save the subflow to

        Returns:
            True if saved successfully
        """
        try:
            from casare_rpa.domain.entities.subflow import Subflow
            from casare_rpa.presentation.canvas.serialization import WorkflowSerializer

            if not self._main_window:
                logger.warning("No main_window - cannot save subflow state")
                return False

            # Capture current canvas state
            serializer = WorkflowSerializer(self._graph, self._main_window)
            state = serializer.serialize()

            # Load existing subflow to preserve metadata
            try:
                subflow = Subflow.load_from_file(subflow_path)
            except Exception:
                # Create new subflow if file doesn't exist
                subflow = Subflow(
                    id="",
                    name="Subflow",
                    description="",
                )

            # Convert workflow state back to subflow format
            transformed_nodes = {}
            for node_id, node_data in state.get("nodes", {}).items():
                # Convert position from [x, y] list to {x, y} dict
                pos = node_data.get("position", [0, 0])
                if isinstance(pos, list) and len(pos) >= 2:
                    position = {"x": pos[0], "y": pos[1]}
                else:
                    position = {"x": 0, "y": 0}

                # Transform node data back to subflow format
                transformed_nodes[node_id] = {
                    "node_id": node_data.get("node_id", node_id),
                    "type": node_data.get("node_type", ""),
                    "position": position,
                    "properties": node_data.get("config", {}),
                    "name": node_data.get("name", ""),
                }

            # Update subflow with new node data
            subflow.nodes = transformed_nodes
            subflow.connections = state.get("connections", [])

            # Save back to file
            subflow.save_to_file(subflow_path)
            logger.info(f"Saved subflow state to: {subflow_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save subflow state: {e}")
            return False

    def _load_subflow(self, subflow_id: str, subflow_path: str, name: str) -> bool:
        """
        Load a subflow's content into the canvas.

        Args:
            subflow_id: ID of the subflow
            subflow_path: File path to subflow definition
            name: Display name

        Returns:
            True if loaded successfully
        """
        try:
            from casare_rpa.domain.entities.subflow import Subflow
            from casare_rpa.presentation.canvas.serialization import (
                WorkflowDeserializer,
            )

            # Load subflow from file
            if subflow_path:
                subflow = Subflow.load_from_file(subflow_path)
            else:
                # Try to find by ID in registry
                logger.warning(
                    f"Subflow loading by ID not yet implemented: {subflow_id}"
                )
                return False

            # Convert subflow to workflow-compatible format
            # Subflow format differs from workflow format - need to transform
            subflow_data = subflow.to_dict()

            # Transform nodes from subflow format to workflow format
            transformed_nodes = {}
            for node_id, node_data in subflow_data.get("nodes", {}).items():
                # Convert position from {x, y} dict to [x, y] list
                pos = node_data.get("position", {})
                if isinstance(pos, dict):
                    position = [pos.get("x", 0), pos.get("y", 0)]
                else:
                    position = pos if isinstance(pos, list) else [0, 0]

                # Transform node data
                transformed_nodes[node_id] = {
                    "node_id": node_data.get("node_id", node_id),
                    "node_type": node_data.get("type", ""),  # 'type' → 'node_type'
                    "position": position,
                    "config": node_data.get(
                        "properties", {}
                    ),  # 'properties' → 'config'
                    "name": node_data.get("name", ""),
                }

            workflow_data = {
                "nodes": transformed_nodes,
                "connections": subflow_data.get("connections", []),
                "variables": {},  # Subflows don't have top-level variables
                "frames": [],
                "settings": {},
                "metadata": {
                    "name": subflow.name,
                    "description": subflow.description,
                },
            }

            # Use WorkflowDeserializer to load content
            if self._main_window:
                deserializer = WorkflowDeserializer(self._graph, self._main_window)
                success = deserializer.deserialize(workflow_data)
                if success:
                    return True
                else:
                    logger.error(f"Failed to deserialize subflow: {subflow.name}")
                    return False
            else:
                # Fallback: just clear canvas (no main_window to deserialize)
                logger.warning("No main_window - cannot load subflow content properly")
                self._graph.clear_session()
                return True

        except Exception as e:
            logger.error(f"Failed to load subflow: {e}")
            return False

"""
Variable Picker Widget for CasareRPA.

Provides variable insertion functionality for text input fields in node widgets.
Shows a popup with all available variables, supporting nested access and value preview.

Design follows VSCode dark theme styling.

Features:
- Workflow variables from VariablesTab
- Node output variables from upstream connected nodes
- System variables (date, time, etc.)
- Nested expansion for Dict/List types
"""

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from PySide6.QtCore import QEvent, QMimeData, QModelIndex, QObject, QPoint, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QDrag, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.managers.popup_manager import PopupManager
from casare_rpa.presentation.canvas.theme_system import THEME

# Get colors from theme (modern API)
_colors = THEME

# Pre-compiled pattern for secret references
_SECRET_REF_PATTERN = re.compile(r"\{\{\$secret:([^}]+)\}\}")

if TYPE_CHECKING:
    from NodeGraphQt import BaseNode

    from casare_rpa.presentation.canvas.main_window import MainWindow


# =============================================================================
# Styles (Using THEME constants)
# =============================================================================


def _get_variable_button_style() -> str:
    """Generate variable button stylesheet using current theme."""
    c = THEME
    return f"""
QPushButton {{
    background: {c.bg_surface};
    border: 1px solid {c.border};
    border-radius: 3px;
    color: {c.text_secondary};
    font-size: 9px;
    font-family: Consolas, monospace;
    padding: 0px;
    min-width: 16px;
    max-width: 16px;
    min-height: 16px;
    max-height: 16px;
}}
QPushButton:hover {{
    background: {c.primary};
    border-color: {c.primary};
    color: {c.text_primary};
}}
QPushButton:pressed {{
    background: {c.primary_hover};
    border-color: {c.primary_hover};
}}
"""


def _get_variable_popup_style() -> str:
    """Generate variable popup stylesheet using current theme."""
    c = THEME
    return f"""
QWidget#VariablePickerPopup {{
    background: {c.bg_surface};
    border: 1px solid {c.border_light};
    border-radius: 8px;
}}
QListWidget {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 4px;
    margin: 1px 4px;
}}
QListWidget::item:hover {{
    background: {c.bg_hover};
}}
QListWidget::item:selected {{
    background: {c.bg_selected};
    color: {c.text_primary};
}}
QTreeWidget {{
    background: {c.bg_elevated};
    border: none;
    outline: none;
    font-size: 12px;
}}
QTreeWidget::item {{
    padding: 6px 10px;
    border-radius: 4px;
    margin: 1px 0px;
    border-bottom: 1px solid {c.border};
}}
QTreeWidget::item:hover {{
    background: {c.bg_hover};
}}
QTreeWidget::item:selected {{
    background: {c.bg_selected};
    color: {c.text_primary};
}}
QTreeWidget::branch {{
    background: transparent;
}}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {{
    image: url(none);
    border-image: none;
}}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {{
    image: url(none);
    border-image: none;
}}
QLineEdit#SearchBox {{
    background: {c.bg_elevated};
    border: 1px solid {c.border};
    border-radius: 6px;
    color: {c.text_primary};
    padding: 8px 12px;
    font-size: 12px;
    selection-background-color: {c.primary};
}}
QLineEdit#SearchBox:focus {{
    border: 1px solid {c.primary};
}}
QLabel#SectionHeader {{
    color: {c.text_muted};
    font-size: 10px;
    font-weight: 600;
    padding: 8px 12px 4px 12px;
    background: transparent;
    letter-spacing: 0.5px;
}}
QFrame#SearchDivider {{
    background: {c.border};
    max-height: 1px;
    min-height: 1px;
}}
"""


# Legacy module-level style constants for backward compatibility
VARIABLE_BUTTON_STYLE = _get_variable_button_style()
VARIABLE_POPUP_STYLE = _get_variable_popup_style()


# =============================================================================
# Fuzzy Matching
# =============================================================================


def fuzzy_match(pattern: str, text: str) -> tuple[bool, int]:
    """
    Perform fuzzy matching of pattern against text.

    Returns:
        (matches: bool, score: int) - Higher score = better match

    Scoring:
        - Exact match: 1000
        - Starts with pattern: 500 + length bonus
        - Contains pattern: 200 + position bonus
        - Fuzzy match (all chars in order): 100 + consecutive bonus
        - No match: 0
    """
    if not pattern:
        return (True, 0)

    pattern_lower = pattern.lower()
    text_lower = text.lower()

    # Exact match
    if pattern_lower == text_lower:
        return (True, 1000)

    # Starts with
    if text_lower.startswith(pattern_lower):
        return (True, 500 + len(pattern) * 10)

    # Contains
    if pattern_lower in text_lower:
        pos = text_lower.index(pattern_lower)
        return (True, 200 + max(0, 50 - pos))

    # Fuzzy: all characters must appear in order
    pattern_idx = 0
    consecutive = 0
    max_consecutive = 0
    last_match_idx = -2

    for i, char in enumerate(text_lower):
        if pattern_idx < len(pattern_lower) and char == pattern_lower[pattern_idx]:
            pattern_idx += 1
            if i == last_match_idx + 1:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 1
            last_match_idx = i

    if pattern_idx == len(pattern_lower):
        # All pattern chars found in order
        return (True, 100 + max_consecutive * 20)

    return (False, 0)


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class VariableInfo:
    """
    Information about a variable available for insertion.

    Attributes:
        name: Variable name (e.g., "url", "data")
        var_type: Type string (String, Integer, Float, Boolean, List, Dict, DataTable)
        source: Where the variable comes from ("workflow", "node:NodeName", "system")
        value: Optional current value for preview tooltip
        children: For nested access (Dict/List types), contains child VariableInfo items
        path: Full access path (e.g., "data.name" for nested)
        is_expandable: Whether this variable can be expanded (Dict/List types)
        indent_level: Indentation level for display (0 = root)
    """

    name: str
    var_type: str = "Any"
    source: str = "workflow"
    value: Any | None = None
    children: list["VariableInfo"] = field(default_factory=list)
    path: str | None = None
    insertion_path: str | None = None  # Actual path for {{}} insertion (uses node_id)
    is_expandable: bool = False
    indent_level: int = 0

    @property
    def display_name(self) -> str:
        """Get display name (uses path if nested, else name)."""
        return self.path if self.path else self.name

    @property
    def insertion_text(self) -> str:
        """Get the text to insert (wrapped in {{ }})."""
        # Use insertion_path (node_id based) if set, otherwise fall back to display_name
        actual_path = self.insertion_path if self.insertion_path else self.display_name
        return f"{{{{{actual_path}}}}}"

    @property
    def type_color(self) -> str:
        """Get the color for this variable's type."""
        return THEME.text_muted

    @property
    def type_badge(self) -> str:
        """Get the badge text for this variable's type."""
        return TYPE_BADGES.get(self.var_type, TYPE_BADGES["Any"])

    def get_preview_text(self) -> str:
        """Get value preview text for tooltip."""
        if self.value is None:
            return "(no value)"

        val_str = str(self.value)
        if len(val_str) > 50:
            val_str = val_str[:47] + "..."
        return val_str


# =============================================================================
# Variable Provider
# =============================================================================


class VariableProvider:
    """
    Provides variables for the picker.

    Connects to:
    - VariablesTab in bottom panel for workflow variables
    - NodeGraphQt graph for upstream node output variables
    - System variables (date, time, etc.)

    Usage:
        provider = VariableProvider.get_instance()
        provider.set_main_window(main_window)  # Connect to MainWindow

        # Get all variables including upstream node outputs
        all_vars = provider.get_all_variables(current_node_id, graph)
    """

    _instance: Optional["VariableProvider"] = None

    @classmethod
    def get_instance(cls) -> "VariableProvider":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = VariableProvider()
        return cls._instance

    def __init__(self) -> None:
        """Initialize provider."""
        self._custom_variables: dict[str, VariableInfo] = {}
        self._main_window: MainWindow | None = None
        self._workflow_controller = None

    def set_main_window(self, main_window: "MainWindow") -> None:
        """
        Set the main window for accessing panels and controllers.

        Args:
            main_window: MainWindow instance
        """
        self._main_window = main_window
        logger.debug("VariableProvider connected to MainWindow")

    def set_workflow_controller(self, controller) -> None:
        """
        Set the workflow controller for accessing variables.

        Args:
            controller: WorkflowController instance
        """
        self._workflow_controller = controller

    def add_variable(self, var_info: VariableInfo) -> None:
        """Add a custom variable."""
        self._custom_variables[var_info.name] = var_info

    def remove_variable(self, name: str) -> None:
        """Remove a custom variable."""
        self._custom_variables.pop(name, None)

    def clear_variables(self) -> None:
        """Clear all custom variables."""
        self._custom_variables.clear()

    def get_all_variables(
        self,
        current_node_id: str | None = None,
        graph: Any | None = None,
    ) -> list[VariableInfo]:
        """
        Get all available variables.

        Args:
            current_node_id: ID of the currently selected node (for upstream detection)
            graph: NodeGraphQt graph instance

        Returns:
            List of VariableInfo objects grouped by source
        """
        variables: list[VariableInfo] = []

        # 1. Add custom/workflow variables
        variables.extend(self._custom_variables.values())

        # 2. Get variables from bottom panel VariablesTab
        panel_vars = self._get_panel_variables()
        variables.extend(panel_vars)

        # 3. Try to get variables from workflow controller (legacy support)
        if self._workflow_controller and not panel_vars:
            try:
                wf_vars = self._get_workflow_controller_variables()
                variables.extend(wf_vars)
            except Exception as e:
                logger.debug(f"Could not get workflow controller variables: {e}")

        # 4. Get upstream node output variables
        if current_node_id and graph:
            try:
                upstream_vars = self.get_node_output_variables(current_node_id, graph)
                variables.extend(upstream_vars)
            except Exception as e:
                logger.debug(f"Could not get upstream node variables: {e}")

        # 5. Add system variables
        variables.extend(self._get_system_variables())

        return variables

    def _get_panel_variables(self) -> list[VariableInfo]:
        """Get variables from bottom panel VariablesTab."""
        if not self._main_window:
            return []

        try:
            bottom_panel = self._main_window.get_bottom_panel()
            if not bottom_panel:
                return []

            # Get VariablesTab from bottom panel
            variables_tab = bottom_panel.get_variables_tab()
            if not variables_tab:
                return []

            # Get variables dict: {name: {type: str, default: Any, scope: str}}
            raw_vars = variables_tab.get_variables()

            result = []
            for name, var_data in raw_vars.items():
                var_type = var_data.get("type", "String")
                default_value = var_data.get("default", "")

                # Check if expandable (Dict or List)
                is_expandable = var_type in ("Dict", "List") and default_value

                var_info = VariableInfo(
                    name=name,
                    var_type=var_type,
                    source="workflow",
                    value=default_value,
                    is_expandable=is_expandable,
                )

                # Generate children for expandable types
                if is_expandable:
                    var_info.children = self._expand_variable(var_info)

                result.append(var_info)

            return result

        except Exception as e:
            logger.debug(f"Error getting panel variables: {e}")
            return []

    def _get_workflow_controller_variables(self) -> list[VariableInfo]:
        """Get variables from workflow controller (legacy support)."""
        if not self._workflow_controller:
            return []

        try:
            if hasattr(self._workflow_controller, "get_variables"):
                raw_vars = self._workflow_controller.get_variables()
                return [
                    VariableInfo(
                        name=name,
                        var_type=self._infer_type(value),
                        source="workflow",
                        value=value,
                    )
                    for name, value in raw_vars.items()
                ]
        except Exception as e:
            logger.debug(f"Error getting workflow variables: {e}")

        return []

    def get_node_output_variables(
        self,
        current_node_id: str,
        graph: Any,
    ) -> list[VariableInfo]:
        """
        Get output variables from upstream connected nodes.

        Traverses the execution flow backwards from the current node
        to find all nodes that connect to it (via exec_in port).
        Returns VariableInfo for each output port of those nodes.

        Args:
            current_node_id: ID of the current node
            graph: NodeGraphQt graph instance

        Returns:
            List of VariableInfo objects from upstream nodes
        """
        if not graph:
            return []

        variables: list[VariableInfo] = []

        try:
            # Find the current node
            current_node = None
            for node in graph.all_nodes():
                node_id = node.id() if hasattr(node, "id") else None
                prop_id = node.get_property("node_id") if hasattr(node, "get_property") else None
                if node_id == current_node_id or prop_id == current_node_id:
                    current_node = node
                    break

            if not current_node:
                return []

            # Find all upstream nodes by traversing input connections
            upstream_nodes = self._get_upstream_nodes(current_node, set())

            # Get output ports from each upstream node
            for upstream_node in upstream_nodes:
                node_name = upstream_node.name() if hasattr(upstream_node, "name") else "Unknown"

                # Get node_id for variable resolution (stored outputs use node_id)
                # Priority: get_property("node_id") first - id() returns Qt object ID which won't work
                node_id = None
                if hasattr(upstream_node, "get_property"):
                    prop_node_id = upstream_node.get_property("node_id")
                    if prop_node_id:  # Not None and not empty string
                        node_id = prop_node_id
                        logger.debug(f"Got node_id from property: {node_id}")
                if node_id is None and hasattr(upstream_node, "id"):
                    node_id = upstream_node.id()
                    logger.debug(f"Fallback to id(): {node_id}")

                for port in upstream_node.output_ports():
                    port_name = port.name()

                    # Skip exec ports
                    if self._is_exec_port(port_name, upstream_node):
                        continue

                    # Get port data type
                    data_type = self._get_port_data_type(port_name, upstream_node)

                    insertion_path = f"{node_id}.{port_name}" if node_id else None
                    var_info = VariableInfo(
                        name=port_name,
                        var_type=data_type,
                        source=f"node:{node_name}",
                        value=None,  # Runtime value not available at design time
                        path=f"{node_name}.{port_name}",  # Display path (user-friendly)
                        insertion_path=insertion_path,  # Resolution path
                    )
                    logger.debug(
                        f"Created variable: display={node_name}.{port_name}, "
                        f"insertion={insertion_path}, insertion_text={var_info.insertion_text}"
                    )

                    variables.append(var_info)

        except Exception as e:
            logger.debug(f"Error getting upstream node variables: {e}")

        return variables

    def _get_upstream_nodes(
        self,
        node: "BaseNode",
        visited: set,
    ) -> list["BaseNode"]:
        """
        Recursively get all upstream nodes connected to this node.

        Args:
            node: Current node to check
            visited: Set of visited node IDs to prevent cycles

        Returns:
            List of upstream nodes
        """
        upstream = []
        node_id = node.id() if hasattr(node, "id") else id(node)

        if node_id in visited:
            return upstream

        visited.add(node_id)

        try:
            # Check all input ports
            for input_port in node.input_ports():
                # Get connected ports
                connected_ports = input_port.connected_ports()

                for connected_port in connected_ports:
                    # Get the node that owns this connected port
                    connected_node = connected_port.node()

                    if connected_node:
                        upstream.append(connected_node)

                        # Recursively get nodes upstream of this one
                        further_upstream = self._get_upstream_nodes(connected_node, visited)
                        upstream.extend(further_upstream)

        except Exception as e:
            logger.debug(f"Error traversing upstream nodes: {e}")

        return upstream

    def _is_exec_port(self, port_name: str, node: "BaseNode") -> bool:
        """Check if a port is an execution flow port."""
        # Check via visual node method if available
        if hasattr(node, "is_exec_port"):
            return node.is_exec_port(port_name)

        # Fallback to name-based detection
        port_lower = port_name.lower()
        exec_port_names = {
            "exec_in",
            "exec_out",
            "exec",
            "loop_body",
            "completed",
            "true",
            "false",
            "then",
            "else",
            "on_success",
            "on_error",
            "on_finally",
            "body",
            "done",
            "finish",
            "next",
        }
        return port_lower in exec_port_names or "exec" in port_lower

    def _get_port_data_type(self, port_name: str, node: "BaseNode") -> str:
        """Get the data type for a port."""
        try:
            # Try to get from visual node's port types
            if hasattr(node, "get_port_type"):
                data_type = node.get_port_type(port_name)
                if data_type is not None:
                    return data_type.name if hasattr(data_type, "name") else str(data_type)

            # Try to get from casare node's output ports
            if hasattr(node, "_casare_node") and node._casare_node:
                casare_node = node._casare_node
                if hasattr(casare_node, "output_ports"):
                    output_ports = casare_node.output_ports
                    if port_name in output_ports:
                        port = output_ports[port_name]
                        if hasattr(port, "data_type"):
                            dt = port.data_type
                            return dt.name if hasattr(dt, "name") else str(dt)
        except Exception:
            pass

        return "Any"

    def _expand_variable(self, var: VariableInfo) -> list[VariableInfo]:
        """
        Create child VariableInfo for Dict/List variables.

        Args:
            var: Parent variable to expand

        Returns:
            List of child VariableInfo objects
        """
        children = []

        if var.var_type == "Dict" and isinstance(var.value, dict):
            for key, value in var.value.items():
                child_path = f"{var.display_name}.{key}"
                child_type = self._infer_type(value)
                is_expandable = child_type in ("Dict", "List") and value

                child = VariableInfo(
                    name=key,
                    var_type=child_type,
                    source=var.source,
                    value=value,
                    path=child_path,
                    is_expandable=is_expandable,
                    indent_level=var.indent_level + 1,
                )

                # Recursively expand nested structures (limit depth)
                if is_expandable and var.indent_level < 3:
                    child.children = self._expand_variable(child)

                children.append(child)

        elif var.var_type == "List" and isinstance(var.value, list):
            # Limit to first 10 items
            for i, item in enumerate(var.value[:10]):
                child_path = f"{var.display_name}[{i}]"
                child_type = self._infer_type(item)
                is_expandable = child_type in ("Dict", "List") and item

                child = VariableInfo(
                    name=f"[{i}]",
                    var_type=child_type,
                    source=var.source,
                    value=item,
                    path=child_path,
                    is_expandable=is_expandable,
                    indent_level=var.indent_level + 1,
                )

                # Recursively expand nested structures (limit depth)
                if is_expandable and var.indent_level < 3:
                    child.children = self._expand_variable(child)

                children.append(child)

            # Add indicator if more items exist
            if len(var.value) > 10:
                children.append(
                    VariableInfo(
                        name=f"... ({len(var.value) - 10} more)",
                        var_type="Any",
                        source=var.source,
                        value=None,
                        path=None,
                        indent_level=var.indent_level + 1,
                    )
                )

        return children

    def _get_system_variables(self) -> list[VariableInfo]:
        """Get system variables (date, time, etc.)."""
        from datetime import datetime

        now = datetime.now()

        return [
            VariableInfo(
                name="$currentDate",
                var_type="String",
                source="system",
                value=now.strftime("%Y-%m-%d"),
            ),
            VariableInfo(
                name="$currentTime",
                var_type="String",
                source="system",
                value=now.strftime("%H:%M:%S"),
            ),
            VariableInfo(
                name="$currentDateTime",
                var_type="String",
                source="system",
                value=now.isoformat(),
            ),
            VariableInfo(
                name="$timestamp",
                var_type="Integer",
                source="system",
                value=int(now.timestamp()),
            ),
        ]

    def _infer_type(self, value: Any) -> str:
        """Infer variable type from value."""
        if isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Integer"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, list):
            return "List"
        elif isinstance(value, dict):
            return "Dict"
        else:
            return "Any"


# =============================================================================
# Custom Delegate for Selection Highlight
# =============================================================================


class HighlightDelegate(QStyledItemDelegate):
    """Custom delegate that paints background for selected items with rounded corners."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_item: QTreeWidgetItem | None = None
        self._highlight_color = QColor(_colors.selection)  # Selection blue
        self._hover_color = QColor(_colors.surface_hover)  # Subtle hover

    def set_selected_item(self, item: QTreeWidgetItem | None) -> None:
        """Set the currently selected item."""
        self._selected_item = item

    def paint(self, painter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint the item with custom background if selected."""
        from PySide6.QtGui import QPainterPath

        # Get the tree widget item from index
        tree_widget = option.widget
        if tree_widget:
            item = tree_widget.itemFromIndex(index)
            if item and item == self._selected_item:
                # Paint highlight background with rounded corners
                painter.save()
                painter.setRenderHint(painter.RenderHint.Antialiasing, True)
                path = QPainterPath()
                # Create rounded rect with 4px radius
                rect = option.rect.adjusted(2, 1, -2, -1)
                path.addRoundedRect(rect, 4, 4)
                painter.fillPath(path, self._highlight_color)
                painter.restore()

        # Call parent to draw text and other elements
        super().paint(painter, option, index)


# =============================================================================
# Draggable Variable Tree Widget
# =============================================================================


class DraggableVariableTree(QTreeWidget):
    """
    Tree widget that supports dragging variables to input fields.

    Enables drag-and-drop from the variable picker popup to VariableAwareLineEdit
    and other drop-accepting widgets.
    """

    MIME_TYPE = "application/x-casare-variable"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_start_pos: QPoint | None = None

        # Enable drag
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)

    def mousePressEvent(self, event) -> None:
        """Track drag start position."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Handle drag initiation."""
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return

        if self._drag_start_pos is None:
            super().mouseMoveEvent(event)
            return

        # Check if moved enough to start drag
        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        # Get selected item
        item = self.itemAt(self._drag_start_pos)
        if not item:
            super().mouseMoveEvent(event)
            return

        # Get VariableInfo from item
        var_info = item.data(0, Qt.ItemDataRole.UserRole)
        if not var_info or not hasattr(var_info, "insertion_text"):
            super().mouseMoveEvent(event)
            return

        # Start drag
        self.setCursor(Qt.CursorShape.ClosedHandCursor)

        drag = QDrag(self)
        mime_data = QMimeData()

        # Create drag data matching the format expected by VariableAwareLineEdit
        drag_data = {
            "variable": var_info.insertion_text,
            "name": var_info.name,
            "type": var_info.var_type,
            "path": var_info.path,
        }
        mime_data.setData(self.MIME_TYPE, json.dumps(drag_data).encode("utf-8"))

        # Also set as plain text for widgets that accept text drops
        mime_data.setText(var_info.insertion_text)

        drag.setMimeData(mime_data)

        logger.debug(f"Starting drag for variable: {var_info.insertion_text}")

        # Execute drag
        drag.exec(Qt.DropAction.CopyAction)

        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._drag_start_pos = None

    def mouseReleaseEvent(self, event) -> None:
        """Reset drag state."""
        self._drag_start_pos = None
        super().mouseReleaseEvent(event)


# =============================================================================
# Variable Picker Popup
# =============================================================================


class VariablePickerPopup(QWidget):
    """
    Dropdown popup showing available variables with search/filter.

    Features:
        - Search box at top for filtering
        - Tree widget with grouped sections (Variables, Node Outputs, System)
        - Type badges (color-coded)
        - Keyboard navigation: arrows, Enter, Escape
        - Nested expansion for Dict/List types
        - Value preview tooltip on hover

    Signals:
        variable_selected: Emits the full insertion text "{{varName}}"
        closed: Emitted when popup is closed
    """

    variable_selected = Signal(str)
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the popup."""
        # Use Tool window - allows proper keyboard handling unlike Popup
        super().__init__(
            parent,
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )

        self.setObjectName("VariablePickerPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._all_variables: list[VariableInfo] = []
        self._filtered_variables: list[VariableInfo] = []
        self._provider: VariableProvider | None = None
        self._current_node_id: str | None = None
        self._graph: Any | None = None
        self._selected_item: QTreeWidgetItem | None = None  # Track selection ourselves
        self._delegate: HighlightDelegate | None = None

        self._setup_ui()
        self._apply_styles()

        # Debounce timer for search filtering (150ms delay)
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(150)  # 150ms debounce
        self._filter_timer.timeout.connect(self._do_filter)
        self._pending_filter_text = ""

    def _setup_ui(self) -> None:
        """Set up the popup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)  # Control spacing manually for better depth control

        # Search box - handles typing, forwards navigation keys
        self._search_box = QLineEdit()
        self._search_box.setObjectName("SearchBox")
        self._search_box.setPlaceholderText("Search variables...")
        self._search_box.textChanged.connect(self._on_search_changed)
        self._search_box.installEventFilter(self)  # Capture arrow/Enter/Escape
        layout.addWidget(self._search_box)

        # Divider between search and tree (creates visual depth)
        search_divider = QFrame()
        search_divider.setObjectName("SearchDivider")
        search_divider.setFrameShape(QFrame.Shape.HLine)
        search_divider.setFixedHeight(1)
        layout.addSpacing(8)
        layout.addWidget(search_divider)
        layout.addSpacing(4)

        # Tree widget for hierarchical display (draggable for variable insertion)
        self._tree_widget = DraggableVariableTree()
        self._tree_widget.setMinimumHeight(220)
        self._tree_widget.setMinimumWidth(320)
        self._tree_widget.setHeaderHidden(True)
        self._tree_widget.setColumnCount(2)
        self._tree_widget.setIndentation(16)
        self._tree_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # Keep focus on search
        self._tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self._tree_widget.setRootIsDecorated(True)
        self._tree_widget.setAnimated(True)
        self._tree_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree_widget.itemClicked.connect(self._on_item_clicked)

        # Custom delegate for selection highlighting
        self._delegate = HighlightDelegate(self._tree_widget)
        self._tree_widget.setItemDelegate(self._delegate)

        # Configure column sizing
        header = self._tree_widget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self._tree_widget)

        # Set fixed size
        self.setMinimumWidth(340)
        self.setMaximumHeight(420)

    def _apply_styles(self) -> None:
        """Apply VSCode dark theme styling."""
        self.setStyleSheet(VARIABLE_POPUP_STYLE)

    def set_provider(self, provider: VariableProvider) -> None:
        """Set the variable provider."""
        self._provider = provider

    def set_node_context(self, node_id: str | None, graph: Any | None) -> None:
        """
        Set the current node context for upstream variable detection.

        Args:
            node_id: ID of the currently selected node
            graph: NodeGraphQt graph instance
        """
        self._current_node_id = node_id
        self._graph = graph

    def refresh_variables(self) -> None:
        """Refresh the variable list from provider."""
        provider = self._provider or VariableProvider.get_instance()
        self._all_variables = provider.get_all_variables(
            self._current_node_id,
            self._graph,
        )
        self._filter_and_display("")

    def _filter_and_display(self, filter_text: str) -> None:
        """Filter variables using fuzzy matching and update display."""
        filter_text = filter_text.strip()

        if filter_text:
            # Filter using fuzzy matching, returns (var, score) tuples
            scored_vars = self._filter_variables_fuzzy(
                self._all_variables,
                filter_text,
            )
            # Sort by score descending (best matches first)
            scored_vars.sort(key=lambda x: x[1], reverse=True)
            self._filtered_variables = [var for var, score in scored_vars]
        else:
            self._filtered_variables = self._all_variables[:]

        self._populate_tree()

        # Auto-select first item when filtering
        if filter_text and self._filtered_variables:
            self._select_first_selectable()

    def _filter_variables_fuzzy(
        self,
        variables: list[VariableInfo],
        filter_text: str,
    ) -> list[tuple[VariableInfo, int]]:
        """Filter variables using fuzzy matching, returns (var, score) tuples."""
        result = []

        for var in variables:
            # Check fuzzy match on name
            name_match, name_score = fuzzy_match(filter_text, var.name)

            # Also check path if available
            path_score = 0
            if var.path:
                path_match, path_score = fuzzy_match(filter_text, var.path)

            # Use best score between name and path
            best_score = max(name_score, path_score)

            # Check if any children match
            filtered_children_with_scores = []
            if var.children:
                filtered_children_with_scores = self._filter_variables_fuzzy(
                    var.children,
                    filter_text,
                )

            # Get best child score
            child_best_score = 0
            if filtered_children_with_scores:
                child_best_score = max(score for _, score in filtered_children_with_scores)

            if best_score > 0 or filtered_children_with_scores:
                # Create a copy with filtered children
                filtered_children = [var for var, _ in filtered_children_with_scores]
                filtered_var = VariableInfo(
                    name=var.name,
                    var_type=var.var_type,
                    source=var.source,
                    value=var.value,
                    children=filtered_children if filtered_children else var.children,
                    path=var.path,
                    is_expandable=var.is_expandable,
                    indent_level=var.indent_level,
                )
                # Use own score or boost from children
                final_score = max(best_score, child_best_score - 10)
                result.append((filtered_var, final_score))

        return result

    def _populate_tree(self) -> None:
        """Populate the tree widget with filtered variables."""
        self._tree_widget.clear()
        self._selected_item = None  # Reset selection when repopulating

        # Group by source
        grouped: dict[str, list[VariableInfo]] = {}
        for var in self._filtered_variables:
            source = var.source
            if source.startswith("node:"):
                source = f"FROM: {source[5:]}"
            elif source == "workflow":
                source = "VARIABLES"
            elif source == "system":
                source = "SYSTEM"

            if source not in grouped:
                grouped[source] = []
            grouped[source].append(var)

        # Display in order: VARIABLES, node outputs, SYSTEM
        order = ["VARIABLES"]
        for key in grouped.keys():
            if key not in order and key != "SYSTEM":
                order.append(key)
        if "SYSTEM" in grouped:
            order.append("SYSTEM")

        for source in order:
            if source not in grouped:
                continue

            # Add section header with modern uppercase styling and visual depth
            header_item = QTreeWidgetItem([source.upper(), ""])
            header_item.setFlags(Qt.ItemFlag.NoItemFlags)
            header_font = QFont()
            header_font.setBold(True)
            header_font.setPointSize(9)
            header_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
            header_item.setFont(0, header_font)
            header_item.setForeground(0, QColor(_colors.text_secondary))
            # Section header background for visual depth
            header_item.setBackground(0, QBrush(QColor(_colors.surface)))
            header_item.setBackground(1, QBrush(QColor(_colors.surface)))
            self._tree_widget.addTopLevelItem(header_item)

            # Add variables in this group
            for var in grouped[source]:
                self._add_variable_item(header_item, var)

            # Expand section header
            header_item.setExpanded(True)

        # Select first selectable item
        self._select_first_selectable()

    def _add_variable_item(
        self,
        parent: QTreeWidgetItem,
        var: VariableInfo,
    ) -> QTreeWidgetItem:
        """Add a variable item to the tree."""
        # Format: [badge] name     Type
        # Use unicode brackets for a cleaner pill-like badge appearance
        badge = var.type_badge
        display_text = f"[{badge}]  {var.name}"

        # Show type in second column with cleaner formatting
        type_display = var.var_type.lower()

        item = QTreeWidgetItem([display_text, type_display])
        item.setData(0, Qt.ItemDataRole.UserRole, var)

        # Set tooltip with value preview
        preview = var.get_preview_text()
        tooltip = f"{var.display_name}: {var.var_type}\nValue: {preview}"
        if var.path:
            tooltip += f"\nInserts: {{{{{var.path}}}}}"
        item.setToolTip(0, tooltip)
        item.setToolTip(1, tooltip)

        # Color-code name by type color
        item.setForeground(0, QColor(var.type_color))

        # Subtle background on type column for visual depth (badge area)
        item.setBackground(1, QBrush(QColor(_colors.bg_component)))

        # Muted type label on the right with subtle styling
        type_font = QFont()
        type_font.setPointSize(10)
        type_font.setItalic(True)
        item.setFont(1, type_font)
        item.setForeground(1, QColor(_colors.text_muted))

        parent.addChild(item)

        # Add children recursively
        if var.children:
            for child_var in var.children:
                self._add_variable_item(item, child_var)

            # Expand if filtering
            if self._search_box.text():
                item.setExpanded(True)

        return item

    def _select_item(self, item: QTreeWidgetItem) -> None:
        """Select an item and highlight it visually using delegate."""
        # Update tracked selection
        self._selected_item = item

        # Update delegate and repaint
        if self._delegate:
            self._delegate.set_selected_item(item)

        if item:
            self._tree_widget.scrollToItem(item)

        # Force repaint
        self._tree_widget.viewport().update()

    def _select_first_selectable(self) -> None:
        """Select the first selectable item in the tree."""
        # Iterate through top-level items (section headers)
        for i in range(self._tree_widget.topLevelItemCount()):
            header_item = self._tree_widget.topLevelItem(i)
            # Check children of each header (actual variables)
            for j in range(header_item.childCount()):
                child = header_item.child(j)
                var = child.data(0, Qt.ItemDataRole.UserRole)
                # Select if it's a valid variable (has name and is not placeholder)
                if (
                    var
                    and isinstance(var, VariableInfo)
                    and var.name
                    and not var.name.startswith("...")
                ):
                    self._select_item(child)
                    return

    def _is_selectable_item(self, item: QTreeWidgetItem | None) -> bool:
        """Check if item is a selectable variable (not header or placeholder)."""
        if not item:
            return False
        # Check flags - headers have NoItemFlags
        if item.flags() == Qt.ItemFlag.NoItemFlags:
            return False
        # Check for valid VariableInfo
        var = item.data(0, Qt.ItemDataRole.UserRole)
        if not var or not isinstance(var, VariableInfo):
            return False
        # Skip placeholder items
        if var.name and var.name.startswith("..."):
            return False
        return True

    def _navigate_down(self) -> None:
        """Move selection down in the tree, skipping headers."""
        current = self._selected_item
        if current:
            next_item = self._tree_widget.itemBelow(current)
            # Skip non-selectable items (headers, placeholders)
            while next_item and not self._is_selectable_item(next_item):
                next_item = self._tree_widget.itemBelow(next_item)
            if next_item:
                self._select_item(next_item)
        else:
            # Select first item if none selected
            self._select_first_selectable()

    def _navigate_up(self) -> None:
        """Move selection up in the tree, skipping headers."""
        current = self._selected_item
        if current:
            prev_item = self._tree_widget.itemAbove(current)
            # Skip non-selectable items (headers, placeholders)
            while prev_item and not self._is_selectable_item(prev_item):
                prev_item = self._tree_widget.itemAbove(prev_item)
            if prev_item:
                self._select_item(prev_item)

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change with debounce."""
        self._pending_filter_text = text
        self._filter_timer.start()  # Restart timer on each keystroke

    def _do_filter(self) -> None:
        """Execute the actual filter after debounce delay."""
        self._filter_and_display(self._pending_filter_text)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle single click - select variable immediately."""
        var = item.data(0, Qt.ItemDataRole.UserRole)
        if var and isinstance(var, VariableInfo):
            # Don't select section headers or placeholder items
            if var.name and not var.name.startswith("...") and var.source != "header":
                self.variable_selected.emit(var.insertion_text)
                self.close()

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double click - same as single click for consistency."""
        self._on_item_clicked(item, column)

    def _select_current_item(self) -> None:
        """Select the currently highlighted item, or first item if none selected."""
        item = self._selected_item

        # If no item selected, select the first one
        if not item:
            self._select_first_selectable()
            item = self._selected_item

        if item:
            var = item.data(0, Qt.ItemDataRole.UserRole)
            if var and isinstance(var, VariableInfo):
                if var.name and not var.name.startswith("..."):
                    self.variable_selected.emit(var.insertion_text)
                    self.close()

    def eventFilter(self, obj, event: QEvent) -> bool:
        """Handle keyboard events from search box."""
        event_type = event.type()

        # Handle keyboard events from search box
        if event_type == QEvent.Type.KeyPress and obj == self._search_box:
            key = event.key()

            if key == Qt.Key.Key_Down:
                self._navigate_down()
                return True
            elif key == Qt.Key.Key_Up:
                self._navigate_up()
                return True
            elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
                self._select_current_item()
                return True
            elif key == Qt.Key.Key_Escape:
                self.close()
                return True

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Fallback key handler if event filter doesn't catch keys."""
        key = event.key()

        if key == Qt.Key.Key_Down:
            self._navigate_down()
            event.accept()
            return
        elif key == Qt.Key.Key_Up:
            self._navigate_up()
            event.accept()
            return
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Tab):
            self._select_current_item()
            event.accept()
            return
        elif key == Qt.Key.Key_Escape:
            self.close()
            event.accept()
            return

        super().keyPressEvent(event)

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)

        # Register with PopupManager for click-outside-to-close handling
        PopupManager.register(self)

        self.refresh_variables()

        # Activate window to receive keyboard events
        self.activateWindow()
        self.raise_()
        self._search_box.setFocus(Qt.FocusReason.PopupFocusReason)
        self._search_box.selectAll()

        # Ensure first item is selected and visible
        self._select_first_selectable()

    def closeEvent(self, event) -> None:
        """Handle close event and clean up resources."""
        # Unregister from PopupManager
        PopupManager.unregister(self)
        self.closed.emit()
        super().closeEvent(event)


# =============================================================================
# Variable Button
# =============================================================================


class VariableButton(QPushButton):
    """
    Small '{x}' button that appears on hover for variable insertion.

    This button is positioned on the right side of a text input and
    shows a variable picker popup when clicked.
    """

    clicked_for_popup = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the button."""
        super().__init__("{x}", parent)

        self.setFixedSize(22, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Insert variable (Ctrl+Space)")
        self.setStyleSheet(VARIABLE_BUTTON_STYLE)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.clicked.connect(self._on_clicked)

    def _on_clicked(self) -> None:
        """Handle click."""
        self.clicked_for_popup.emit()


# =============================================================================
# Variable Aware Line Edit
# =============================================================================


class VariableAwareLineEdit(QLineEdit):
    """
    Enhanced LineEdit with variable picker integration and inline validation.

    Features:
        - Shows VariableButton on hover (right side)
        - Ctrl+Space opens popup
        - "{{" typing triggers inline autocomplete
        - insert_variable() method inserts at cursor position
        - Node context for upstream variable detection
        - Inline validation with visual feedback (red/orange border)
        - Drag-and-drop support for variable insertion from Output Inspector

    Signals:
        variable_inserted: Emitted when a variable is inserted (str: var_text)
        validation_changed: Emitted when validation status changes
    """

    # MIME type for variable drag-and-drop from Node Output Inspector
    VARIABLE_MIME_TYPE = "application/x-casare-variable"

    variable_inserted = Signal(str)
    validation_changed = Signal(object)  # ValidationResult
    expand_clicked = Signal()  # Emitted when expand button is clicked
    encryption_changed = Signal(bool)  # Emitted when encryption state changes

    def __init__(self, parent: QWidget | None = None, show_expand_button: bool = True) -> None:
        """Initialize the widget.

        Args:
            parent: Optional parent widget
            show_expand_button: Whether to show the expand button for expression editor
        """
        super().__init__(parent)

        self._variable_button: VariableButton | None = None
        self._expand_button: QPushButton | None = None
        self._lock_button: QPushButton | None = None
        self._popup: VariablePickerPopup | None = None
        self._provider: VariableProvider | None = None
        self._always_show_button = True  # Button always visible, not just on hover
        self._autocomplete_trigger = "{{"
        self._show_expand_button = show_expand_button

        # Node context for upstream variable detection
        self._current_node_id: str | None = None
        self._graph: Any | None = None

        # Validation support
        self._validators: list[Any] = []  # List of validator functions
        self._validation_status = "valid"  # "valid", "invalid", "warning"
        self._validation_message = ""
        self._base_stylesheet = ""  # Store base stylesheet for validation overlay

        # Encryption support
        self._is_encrypted = False
        self._credential_id: str | None = None
        self._plaintext_cache: str | None = None
        self._secret_reference: str | None = None  # Actual {{$secret:id}} for saving

        # Enable drag-and-drop
        self.setAcceptDrops(True)

        # Install event filter on self to intercept key events before scene filter
        self.installEventFilter(self)

        self._setup_variable_button()
        self._setup_lock_button()
        self._setup_expand_button()
        self._connect_signals()

    def _setup_variable_button(self) -> None:
        """Set up the variable button overlay."""
        self._variable_button = VariableButton(self)
        self._variable_button.clicked_for_popup.connect(self._show_popup)

        # Button always visible by default
        if self._always_show_button:
            self._variable_button.show()
        else:
            self._variable_button.hide()

        # Position button on right side
        self._update_button_position()

    def _setup_expand_button(self) -> None:
        """Set up the expand button for expression editor."""
        if not self._show_expand_button:
            return

        c = THEME
        self._expand_button = QPushButton("...", self)
        self._expand_button.setFixedSize(16, 16)
        self._expand_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._expand_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._expand_button.setToolTip("Open expression editor (Ctrl+E)")
        self._expand_button.setStyleSheet(f"""
            QPushButton {{
                background: {c.bg_surface};
                border: 1px solid {c.border};
                border-radius: 3px;
                color: {c.text_secondary};
                font-size: 8px;
                font-weight: bold;
                font-family: Consolas, monospace;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {c.primary};
                border-color: {c.primary};
                color: {c.text_primary};
            }}
            QPushButton:pressed {{
                background: {c.primary_hover};
                border-color: {c.primary_hover};
            }}
        """)
        self._expand_button.clicked.connect(self._on_expand_clicked)
        self._expand_button.show()

    def _on_expand_clicked(self) -> None:
        """Handle expand button click."""
        self.expand_clicked.emit()

    def _setup_lock_button(self) -> None:
        """Set up the lock button for encryption."""
        c = THEME
        self._lock_button = QPushButton("🔒", self)
        self._lock_button.setFixedSize(16, 16)
        self._lock_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._lock_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._lock_button.setToolTip("Encrypt this value")
        self._lock_button.setStyleSheet(f"""
            QPushButton {{
                background: {c.bg_surface};
                border: 1px solid {c.border};
                border-radius: 3px;
                color: {c.text_secondary};
                font-size: 9px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background: {c.primary};
                border-color: {c.primary};
                color: {c.text_primary};
            }}
        """)
        self._lock_button.clicked.connect(self._on_lock_clicked)
        self._lock_button.show()

    @Slot()
    def _on_lock_clicked(self) -> None:
        """Handle lock button click - toggle encryption."""
        if self._is_encrypted:
            self._unlock_for_editing()
        else:
            self._encrypt_current_text()

    def _encrypt_current_text(self) -> None:
        """Encrypt the current text."""
        text = self.text().strip()
        if not text:
            return

        # Don't encrypt if it's already masked or a secret reference
        if text == "•••••••••":
            return
        if _SECRET_REF_PATTERN.match(text):
            return

        try:
            from casare_rpa.infrastructure.security.credential_store import (
                get_credential_store,
            )

            store = get_credential_store()
            credential_id = store.encrypt_inline_secret(
                plaintext=text,
                name="inline_secret",
                description="Encrypted from parameter widget",
            )

            self._credential_id = credential_id
            self._is_encrypted = True
            self._plaintext_cache = text
            self._secret_reference = f"{{{{$secret:{credential_id}}}}}"

            # Update display to show masked dots (cleaner UX)
            self.blockSignals(True)
            self.setText("•••••••••")
            self.blockSignals(False)
            self.setToolTip("🔒 Encrypted (click lock to edit)")

            # Update button appearance
            self._update_lock_button_style()
            self.encryption_changed.emit(True)

            logger.debug(f"Encrypted text to credential: {credential_id}")

        except Exception as e:
            logger.error(f"Failed to encrypt text: {e}")

    def _unlock_for_editing(self) -> None:
        """Unlock encrypted value for editing."""
        if not self._credential_id:
            return

        try:
            # Get plaintext from cache or decrypt
            plaintext = self._plaintext_cache
            if not plaintext:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                store = get_credential_store()
                plaintext = store.decrypt_inline_secret(self._credential_id)

            if plaintext:
                self.blockSignals(True)
                self.setText(plaintext)
                self.blockSignals(False)

                # Clear encrypted state
                self._is_encrypted = False
                self._secret_reference = None
                self.setToolTip("")  # Clear encryption tooltip
                self._update_lock_button_style()
                self.encryption_changed.emit(False)

        except Exception as e:
            logger.error(f"Failed to unlock for editing: {e}")

    def _update_lock_button_style(self) -> None:
        """Update lock button appearance based on encryption state."""
        if not self._lock_button:
            return

        c = THEME
        if self._is_encrypted:
            self._lock_button.setText("🔓")
            self._lock_button.setToolTip("Click to edit (currently encrypted)")
            self._lock_button.setStyleSheet(f"""
                QPushButton {{
                    background: {c.success};
                    border: 1px solid {c.success};
                    border-radius: 3px;
                    color: {c.text_primary};
                    font-size: 9px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background: {c.primary};
                    border-color: {c.primary};
                }}
            """)
        else:
            self._lock_button.setText("🔒")
            self._lock_button.setToolTip("Encrypt this value")
            self._lock_button.setStyleSheet(f"""
                QPushButton {{
                    background: {c.bg_surface};
                    border: 1px solid {c.border};
                    border-radius: 3px;
                    color: {c.text_secondary};
                    font-size: 9px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background: {c.primary};
                    border-color: {c.primary};
                    color: {c.text_primary};
                }}
            """)

    def isEncrypted(self) -> bool:
        """Return whether the current value is encrypted."""
        return self._is_encrypted

    def getCredentialId(self) -> str | None:
        """Return the credential ID if encrypted."""
        return self._credential_id if self._is_encrypted else None

    def getValue(self) -> str:
        """
        Get the actual value for saving to workflows.

        If encrypted, returns the {{$secret:id}} reference.
        Otherwise returns the displayed text.

        Use this instead of text() when saving to workflow JSON.
        """
        if self._is_encrypted and self._secret_reference:
            return self._secret_reference
        return self.text()

    def setValue(self, value: str) -> None:
        """
        Set the value, detecting and handling encrypted references.

        If value is a {{$secret:id}} pattern, shows masked display.
        Otherwise shows the plain value.
        """
        match = _SECRET_REF_PATTERN.match(value)
        if match:
            credential_id = match.group(1).strip()
            self._credential_id = credential_id
            self._is_encrypted = True
            self._secret_reference = value
            self._plaintext_cache = None  # Will be fetched on unlock

            self.blockSignals(True)
            self.setText("•••••••••")
            self.blockSignals(False)
            self.setToolTip("🔒 Encrypted (click lock to edit)")
            self._update_lock_button_style()
        else:
            self._is_encrypted = False
            self._secret_reference = None
            self._credential_id = None
            self._plaintext_cache = None

            self.blockSignals(True)
            self.setText(value)
            self.blockSignals(False)
            self.setToolTip("")
            if self._lock_button:
                self._update_lock_button_style()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.textChanged.connect(self._on_text_changed)
        # Run validation when editing is finished
        self.editingFinished.connect(self._run_validation)

    def _update_button_position(self) -> None:
        """Update variable, lock, and expand button positions."""
        right_margin = 4
        button_spacing = 2

        # Position expand button first (rightmost)
        if self._expand_button:
            exp_width = self._expand_button.width()
            exp_height = self._expand_button.height()
            exp_x = self.width() - exp_width - right_margin
            exp_y = (self.height() - exp_height) // 2
            self._expand_button.move(exp_x, exp_y)
            right_margin = exp_x - button_spacing  # Next button goes to the left

        # Position variable button (middle)
        if self._variable_button:
            btn_width = self._variable_button.width()
            btn_height = self._variable_button.height()
            x = right_margin - btn_width
            y = (self.height() - btn_height) // 2
            self._variable_button.move(x, y)
            right_margin = x - button_spacing  # Lock button goes to the left

        # Position lock button (leftmost of the button group)
        if self._lock_button:
            lock_width = self._lock_button.width()
            lock_height = self._lock_button.height()
            lock_x = right_margin - lock_width
            lock_y = (self.height() - lock_height) // 2
            self._lock_button.move(lock_x, lock_y)

    def resizeEvent(self, event) -> None:
        """Handle resize to reposition button."""
        super().resizeEvent(event)
        self._update_button_position()

    # =========================================================================
    # Drag and Drop Support
    # =========================================================================

    def dragEnterEvent(self, event) -> None:
        """
        Handle drag enter - accept variable drops from Node Output Inspector.

        Accepts:
        - application/x-casare-variable MIME type (from Schema view)
        - text/plain as fallback
        """
        mime_data = event.mimeData()

        # Accept our custom MIME type
        if mime_data.hasFormat(self.VARIABLE_MIME_TYPE):
            event.acceptProposedAction()
            return

        # Also accept plain text as fallback
        if mime_data.hasText():
            text = mime_data.text()
            # Only accept if it looks like a variable reference
            if text.startswith("{{") and text.endswith("}}"):
                event.acceptProposedAction()
                return

        event.ignore()

    def dragMoveEvent(self, event) -> None:
        """Handle drag move - keep accepting the drop."""
        mime_data = event.mimeData()

        if mime_data.hasFormat(self.VARIABLE_MIME_TYPE):
            event.acceptProposedAction()
        elif mime_data.hasText():
            text = mime_data.text()
            if text.startswith("{{") and text.endswith("}}"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        """
        Handle drop - insert variable at cursor position.

        Extracts variable reference from:
        - Custom MIME data (JSON with "variable" key)
        - Plain text fallback
        """
        import json as json_module

        mime_data = event.mimeData()
        variable_text = None

        # Try custom MIME type first
        if mime_data.hasFormat(self.VARIABLE_MIME_TYPE):
            try:
                data_bytes = mime_data.data(self.VARIABLE_MIME_TYPE)
                data_str = bytes(data_bytes).decode("utf-8")
                data = json_module.loads(data_str)
                variable_text = data.get("variable", "")
            except Exception as e:
                logger.debug(f"Failed to parse variable drag data: {e}")

        # Fall back to plain text
        if not variable_text and mime_data.hasText():
            text = mime_data.text()
            if text.startswith("{{") and text.endswith("}}"):
                variable_text = text

        if variable_text:
            # Insert at cursor position (or append if no focus)
            self.insert_variable(variable_text)
            self.variable_inserted.emit(variable_text)
            event.acceptProposedAction()
            logger.debug(f"Variable dropped: {variable_text}")
        else:
            event.ignore()

    def enterEvent(self, event) -> None:
        """Handle enter event."""
        super().enterEvent(event)
        # Button is always visible when _always_show_button is True
        if not self._always_show_button and self._variable_button:
            self._variable_button.show()

    def leaveEvent(self, event) -> None:
        """Handle leave event."""
        super().leaveEvent(event)
        # Don't hide if button should always be visible
        if not self._always_show_button and self._variable_button and not self._popup_is_visible():
            self._variable_button.hide()

    def _popup_is_visible(self) -> bool:
        """Check if popup is currently visible."""
        return self._popup is not None and self._popup.isVisible()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Event filter to intercept key events before the scene's event filter.

        This ensures that typing in the line edit (including 'x' and Delete keys)
        is handled locally and not intercepted by the graph's keyboard shortcuts.
        """
        if obj is self and event.type() == QEvent.Type.KeyPress:
            # Handle all key presses in the line edit locally
            # This prevents the scene's event filter from intercepting keys like 'x' or Delete
            key_event = event
            key = key_event.key()

            # Check for Ctrl+Space (our special shortcut)
            if (
                key_event.modifiers() & Qt.KeyboardModifier.ControlModifier
                and key == Qt.Key.Key_Space
            ):
                self._show_popup()
                return True  # Event handled

            # For all other key presses, let the normal keyPressEvent handle them
            # Return False to let the event propagate to keyPressEvent
            return False

        return super().eventFilter(obj, event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press for Ctrl+Space shortcut."""
        # Check for Ctrl+Space
        if (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
            and event.key() == Qt.Key.Key_Space
        ):
            self._show_popup()
            event.accept()
            return

        super().keyPressEvent(event)

    def _on_text_changed(self, text: str) -> None:
        """Handle text changes - auto-popup disabled, user must click {x} or Ctrl+Space."""
        # Auto-popup on typing is disabled - let user type freely
        # Popup only shows on: button click or Ctrl+Space
        pass

    def _has_matching_variables(self, filter_text: str) -> bool:
        """Check if any variables match the filter text."""
        provider = self._provider or VariableProvider.get_instance()
        all_vars = provider.get_all_variables(self._current_node_id, self._graph)

        for var in all_vars:
            match, score = fuzzy_match(filter_text, var.name)
            if match and score >= 100:  # At least fuzzy match
                return True
            # Also check children
            if var.children:
                for child in var.children:
                    match, score = fuzzy_match(filter_text, child.name)
                    if match and score >= 100:
                        return True
        return False

    def _show_popup(self, initial_filter: str = "") -> None:
        """Show the variable picker popup."""
        self._show_popup_with_filter(initial_filter)

    def _show_popup_with_filter(self, initial_filter: str = "") -> None:
        """Show the variable picker popup with optional initial filter."""
        if self._popup is None:
            self._popup = VariablePickerPopup()
            self._popup.variable_selected.connect(self._on_variable_selected)
            self._popup.closed.connect(self._on_popup_closed)

        if self._provider:
            self._popup.set_provider(self._provider)

        # Pass node context for upstream variable detection
        self._popup.set_node_context(self._current_node_id, self._graph)

        # Position popup below the line edit (shifted left 21px, up 15px for better alignment)
        global_pos = self.mapToGlobal(QPoint(-21, self.height() - 15))
        self._popup.move(global_pos)

        # Set initial filter text if provided
        if initial_filter:
            self._popup._search_box.setText(initial_filter)

        self._popup.show()

    def _on_variable_selected(self, var_text: str) -> None:
        """Handle variable selection from popup."""
        self.insert_variable(var_text)
        self.variable_inserted.emit(var_text)

    def _on_popup_closed(self) -> None:
        """Handle popup close."""
        # If always showing button, don't hide it
        if self._always_show_button:
            return

        if self._variable_button:
            # Hide button if mouse is not over the widget
            app = QApplication.instance()
            if app:
                cursor_pos = self.mapFromGlobal(app.cursor().pos())
                if not self.rect().contains(cursor_pos):
                    self._variable_button.hide()

    def insert_variable(self, var_text: str) -> None:
        """
        Insert variable text at cursor position.

        If the cursor is right after "{{", replace that with the variable.
        Otherwise, insert at cursor position.

        Args:
            var_text: The variable text to insert (e.g., "{{myVar}}")
        """
        cursor_pos = self.cursorPosition()
        current_text = self.text()

        # Check if we should replace {{ prefix
        if cursor_pos >= 2 and current_text[cursor_pos - 2 : cursor_pos] == "{{":
            # Remove the {{ and insert variable
            new_text = current_text[: cursor_pos - 2] + var_text + current_text[cursor_pos:]
            self.setText(new_text)
            self.setCursorPosition(cursor_pos - 2 + len(var_text))
        else:
            # Simple insert at cursor
            self.insert(var_text)

    def set_provider(self, provider: VariableProvider) -> None:
        """Set the variable provider."""
        self._provider = provider

    def set_node_context(self, node_id: str | None, graph: Any | None) -> None:
        """
        Set the current node context for upstream variable detection.

        Args:
            node_id: ID of the node this widget belongs to
            graph: NodeGraphQt graph instance
        """
        self._current_node_id = node_id
        self._graph = graph

    def set_always_show_button(self, always_show: bool) -> None:
        """Set whether button is always visible or only on hover."""
        self._always_show_button = always_show
        if self._variable_button:
            if always_show:
                self._variable_button.show()
            else:
                self._variable_button.hide()

    # =========================================================================
    # Validation Methods
    # =========================================================================

    def add_validator(self, validator) -> None:
        """
        Add a validator function for inline validation.

        Validators are called in order on editingFinished. First failure stops.

        Args:
            validator: Function that takes value and returns ValidationResult
                       (from casare_rpa.presentation.canvas.ui.widgets.validated_input)
        """
        self._validators.append(validator)

    def clear_validators(self) -> None:
        """Remove all validators."""
        self._validators.clear()
        self._set_validation_visual("valid", "")

    def _run_validation(self) -> None:
        """Run all validators and update visual state."""
        if not self._validators:
            return

        value = self.text()
        status = "valid"
        message = ""

        for validator in self._validators:
            try:
                result = validator(value)
                # Handle ValidationResult objects
                if hasattr(result, "status"):
                    status_val = result.status
                    # Convert enum to string if needed
                    if hasattr(status_val, "name"):
                        status = status_val.name.lower()
                    elif hasattr(status_val, "value"):
                        status = str(status_val.value).lower()
                    else:
                        status = str(status_val).lower()
                    message = getattr(result, "message", "")
                    if status != "valid":
                        break
            except Exception as e:
                logger.debug(f"Validator error: {e}")
                status = "invalid"
                message = str(e)
                break

        self._set_validation_visual(status, message)

    def _set_validation_visual(self, status: str, message: str) -> None:
        """
        Update visual state based on validation status.

        Args:
            status: "valid", "invalid", or "warning"
            message: Error/warning message
        """
        if self._validation_status == status and self._validation_message == message:
            return  # No change

        self._validation_status = status
        self._validation_message = message

        # Define border colors
        border_colors = {
            "valid": _colors.border,  # Normal border
            "invalid": _colors.error,  # Red border
            "warning": _colors.warning,  # Orange border
        }
        border_color = border_colors.get(status, _colors.border)
        border_width = "2px" if status != "valid" else "1px"

        # Apply validation-aware stylesheet
        self.setStyleSheet(f"""
            QLineEdit {{
                background: {_colors.surface};
                border: {border_width} solid {border_color};
                border-radius: 3px;
                color: {_colors.text_primary};
                padding: 2px 28px 2px 4px;
            }}
            QLineEdit:focus {{
                border: {border_width} solid {border_color if status != 'valid' else _colors.border_focus};
            }}
        """)

        # Update tooltip with validation message
        if message:
            self.setToolTip(message)
        else:
            self.setToolTip("")

        # Emit validation changed signal
        try:
            from casare_rpa.presentation.canvas.ui.widgets.validated_input import (
                ValidationResult,
                ValidationStatus,
            )

            status_enum = {
                "valid": ValidationStatus.VALID,
                "invalid": ValidationStatus.INVALID,
                "warning": ValidationStatus.WARNING,
            }.get(status, ValidationStatus.VALID)
            self.validation_changed.emit(ValidationResult(status=status_enum, message=message))
        except ImportError:
            pass  # Emit raw data if ValidationResult not available

    def validate(self) -> bool:
        """
        Manually trigger validation.

        Returns:
            True if valid, False otherwise
        """
        self._run_validation()
        return self._validation_status == "valid"

    def is_valid(self) -> bool:
        """Check if current value is valid."""
        return self._validation_status == "valid"

    def get_validation_status(self) -> str:
        """Get current validation status string."""
        return self._validation_status

    def get_validation_message(self) -> str:
        """Get current validation message."""
        return self._validation_message

    def set_validation_status(self, status: str, message: str = "") -> None:
        """
        Manually set validation status (for external validation).

        Args:
            status: "valid", "invalid", or "warning"
            message: Optional message
        """
        self._set_validation_visual(status, message)


# =============================================================================
# Helper Function for Widget Replacement
# =============================================================================


def _replace_widget_with_variable_aware(
    container: QWidget,
    line_edit: QLineEdit,
    provider: VariableProvider | None = None,
) -> VariableAwareLineEdit:
    """
    Replace a QLineEdit with a VariableAwareLineEdit in place.

    This preserves the line edit's current text and styling.

    Args:
        container: Parent container widget
        line_edit: Original QLineEdit to replace
        provider: Optional VariableProvider

    Returns:
        The new VariableAwareLineEdit
    """
    # Create new variable-aware line edit
    var_line_edit = VariableAwareLineEdit(container)

    # Copy properties
    var_line_edit.setText(line_edit.text())
    var_line_edit.setPlaceholderText(line_edit.placeholderText())
    var_line_edit.setMinimumHeight(line_edit.minimumHeight())
    var_line_edit.setMinimumWidth(line_edit.minimumWidth())
    var_line_edit.setSizePolicy(line_edit.sizePolicy())
    var_line_edit.setStyleSheet(line_edit.styleSheet())

    if provider:
        var_line_edit.set_provider(provider)

    # Find and replace in layout
    layout = container.layout()
    if layout:
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() == line_edit:
                # Get layout item properties
                layout.removeWidget(line_edit)
                layout.insertWidget(i, var_line_edit)
                line_edit.deleteLater()
                break

    return var_line_edit


# =============================================================================
# Factory Functions for NodeGraphQt Integration
# =============================================================================


def create_variable_aware_line_edit(
    text: str = "",
    placeholder: str = "",
    min_height: int = 24,
    min_width: int = 100,
    provider: VariableProvider | None = None,
) -> VariableAwareLineEdit:
    """
    Factory function to create a VariableAwareLineEdit for use in node widgets.

    Args:
        text: Initial text value
        placeholder: Placeholder text
        min_height: Minimum height
        min_width: Minimum width
        provider: Optional VariableProvider

    Returns:
        Configured VariableAwareLineEdit
    """
    line_edit = VariableAwareLineEdit()
    line_edit.setText(text)
    line_edit.setPlaceholderText(placeholder)
    line_edit.setMinimumHeight(min_height)
    line_edit.setMinimumWidth(min_width)

    # Apply dark theme styling
    line_edit.setStyleSheet(f"""
        QLineEdit {{
            background: {_colors.surface};
            border: 1px solid {_colors.border};
            border-radius: 3px;
            color: {_colors.text_primary};
            padding: 2px 28px 2px 4px;
        }}
        QLineEdit:focus {{
            border: 1px solid {_colors.border_focus};
        }}
    """)

    if provider:
        line_edit.set_provider(provider)

    return line_edit

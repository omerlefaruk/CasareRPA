"""
Breakpoints Panel for managing workflow breakpoints.

Provides a dedicated panel to view, edit, enable/disable, and delete breakpoints.
Integrates with DebugController for breakpoint management.

Features:
- List view of all breakpoints with type, node, condition, hit count
- Context menu for edit, delete, go to node actions
- Enable/disable individual breakpoints or all at once
- Double-click to edit condition
- Click to navigate to node on canvas
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDockWidget,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Epic 6.1: Migrated to v2 design system
from casare_rpa.presentation.canvas.theme import THEME_V2
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    ToolbarButton,
    get_panel_table_stylesheet,
)

if TYPE_CHECKING:
    from ...debugger.debug_controller import Breakpoint, BreakpointType, DebugController


class BreakpointsPanel(QDockWidget):
    """
    Panel for managing workflow breakpoints.

    Displays all breakpoints in a tree view with columns for:
    - Enabled state (checkbox)
    - Node name
    - Type (Regular, Conditional, Hit-Count, Log Point)
    - Condition expression
    - Hit count

    Signals:
        navigate_to_node: Emitted to navigate to a node on canvas
        edit_breakpoint: Emitted to edit a breakpoint
        breakpoint_toggled: Emitted when breakpoint enabled state changes
    """

    navigate_to_node = Signal(str)
    edit_breakpoint = Signal(str)
    breakpoint_toggled = Signal(str, bool)

    def __init__(
        self,
        parent: QWidget | None = None,
        debug_controller: Optional["DebugController"] = None,
    ) -> None:
        """
        Initialize breakpoints panel.

        Args:
            parent: Parent widget
            debug_controller: Debug controller for breakpoint management
        """
        super().__init__("Breakpoints", parent)
        self._debug_controller = debug_controller
        self._tree: QTreeWidget | None = None
        self._empty_state: EmptyStateWidget | None = None

        self.setObjectName("BreakpointsPanel")
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.setMinimumWidth(250)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.debug("BreakpointsPanel initialized")

    def set_debug_controller(self, controller: "DebugController") -> None:
        """
        Set the debug controller.

        Args:
            controller: Debug controller to use
        """
        if self._debug_controller:
            self._disconnect_controller()

        self._debug_controller = controller
        self._connect_controller()
        self.refresh_breakpoints()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Tree widget for breakpoints
        self._tree = QTreeWidget()
        self._tree.setObjectName("breakpoints_tree")
        self._tree.setColumnCount(5)
        self._tree.setHeaderLabels(["", "Node", "Type", "Condition", "Hits"])
        self._tree.setRootIsDecorated(False)
        self._tree.setAlternatingRowColors(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Column sizing
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._tree.setColumnWidth(0, 30)
        self._tree.setColumnWidth(4, 50)

        layout.addWidget(self._tree)

        # Empty state (shown when no breakpoints)
        self._empty_state = EmptyStateWidget(
            icon_text="",
            title="No Breakpoints",
            description="Click on a node and press F9 to set a breakpoint,\nor right-click a node and select 'Toggle Breakpoint'",
            parent=container,
        )
        self._empty_state.hide()
        layout.addWidget(self._empty_state)

        self.setWidget(container)

    def _create_toolbar(self) -> QWidget:
        """Create the toolbar with action buttons."""
        toolbar = QWidget()
        toolbar.setObjectName("breakpoints_toolbar")
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Enable All button
        self._btn_enable_all = ToolbarButton(
            text="Enable All",
            tooltip="Enable all breakpoints",
        )
        self._btn_enable_all.clicked.connect(self._on_enable_all)
        layout.addWidget(self._btn_enable_all)

        # Disable All button
        self._btn_disable_all = ToolbarButton(
            text="Disable All",
            tooltip="Disable all breakpoints",
        )
        self._btn_disable_all.clicked.connect(self._on_disable_all)
        layout.addWidget(self._btn_disable_all)

        layout.addStretch()

        # Clear All button
        self._btn_clear_all = ToolbarButton(
            text="Clear All",
            tooltip="Remove all breakpoints",
            danger=True,
        )
        self._btn_clear_all.clicked.connect(self._on_clear_all)
        layout.addWidget(self._btn_clear_all)

        return toolbar

    def _apply_styles(self) -> None:
        """Apply panel styling using THEME_V2 tokens."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
                titlebar-close-icon: none;
                titlebar-normal-icon: none;
            }}
            QDockWidget::title {{
                background-color: {THEME_V2.bg_header};
                color: {THEME_V2.text_header};
                padding: 6px 10px;
                font-weight: 600;
                font-size: 11px;
            }}
            #breakpoints_toolbar {{
                background-color: {THEME_V2.bg_header};
                border-bottom: 1px solid {THEME_V2.border};
            }}
            {get_panel_table_stylesheet()}
            QTreeWidget::item {{
                padding: 4px 6px;
            }}
            QTreeWidget::indicator {{
                width: 16px;
                height: 16px;
            }}
            QTreeWidget::indicator:unchecked {{
                background-color: {THEME_V2.bg_hover};
                border: 1px solid {THEME_V2.border};
                border-radius: 3px;
            }}
            QTreeWidget::indicator:checked {{
                background-color: {THEME_V2.primary};
                border: 1px solid {THEME_V2.primary};
                border-radius: 3px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        if self._tree:
            self._tree.itemClicked.connect(self._on_item_clicked)
            self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
            self._tree.customContextMenuRequested.connect(self._on_context_menu)

    def _connect_controller(self) -> None:
        """Connect to debug controller signals."""
        if not self._debug_controller:
            return

        self._debug_controller.breakpoint_added.connect(self._on_breakpoint_added)
        self._debug_controller.breakpoint_removed.connect(self._on_breakpoint_removed)

    def _disconnect_controller(self) -> None:
        """Disconnect from debug controller signals."""
        if not self._debug_controller:
            return

        try:
            self._debug_controller.breakpoint_added.disconnect(self._on_breakpoint_added)
            self._debug_controller.breakpoint_removed.disconnect(self._on_breakpoint_removed)
        except RuntimeError:
            pass

    def refresh_breakpoints(self) -> None:
        """Refresh the breakpoints list from controller."""
        if not self._tree:
            return

        self._tree.clear()

        if not self._debug_controller:
            self._update_empty_state()
            return

        breakpoints = self._debug_controller.get_all_breakpoints()
        for bp in breakpoints:
            self._add_breakpoint_item(bp)

        self._update_empty_state()

    def _add_breakpoint_item(self, breakpoint: "Breakpoint") -> None:
        """
        Add a breakpoint item to the tree.

        Args:
            breakpoint: Breakpoint to add
        """
        if not self._tree:
            return

        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, breakpoint.node_id)

        # Enabled checkbox
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(
            0,
            Qt.CheckState.Checked if breakpoint.enabled else Qt.CheckState.Unchecked,
        )

        # Node ID (truncated for display)
        node_display = self._get_node_display_name(breakpoint.node_id)
        item.setText(1, node_display)
        item.setToolTip(1, breakpoint.node_id)

        # Type
        type_text = self._get_type_display(breakpoint.breakpoint_type)
        item.setText(2, type_text)

        # Condition
        condition_text = self._get_condition_display(breakpoint)
        item.setText(3, condition_text)
        if breakpoint.condition:
            item.setToolTip(3, breakpoint.condition)

        # Hit count
        item.setText(4, str(breakpoint.hit_count))
        item.setTextAlignment(4, Qt.AlignmentFlag.AlignCenter)

        # Style based on enabled state
        if not breakpoint.enabled:
            for col in range(5):
                item.setForeground(col, THEME_V2.text_disabled)

        self._tree.addTopLevelItem(item)

    def _get_node_display_name(self, node_id: str) -> str:
        """Get display name for a node."""
        if len(node_id) > 30:
            return node_id[:27] + "..."
        return node_id

    def _get_type_display(self, bp_type: "BreakpointType") -> str:
        """Get display text for breakpoint type."""
        from ...debugger.debug_controller import BreakpointType

        type_map = {
            BreakpointType.REGULAR: "Regular",
            BreakpointType.CONDITIONAL: "Conditional",
            BreakpointType.HIT_COUNT: "Hit Count",
            BreakpointType.LOG_POINT: "Log Point",
        }
        return type_map.get(bp_type, "Unknown")

    def _get_condition_display(self, breakpoint: "Breakpoint") -> str:
        """Get display text for breakpoint condition."""
        from ...debugger.debug_controller import BreakpointType

        if breakpoint.breakpoint_type == BreakpointType.CONDITIONAL:
            return breakpoint.condition or "-"
        elif breakpoint.breakpoint_type == BreakpointType.HIT_COUNT:
            return f">= {breakpoint.hit_count_target}"
        elif breakpoint.breakpoint_type == BreakpointType.LOG_POINT:
            if breakpoint.log_message:
                msg = breakpoint.log_message
                return msg[:20] + "..." if len(msg) > 20 else msg
            return "-"
        return "-"

    def _update_empty_state(self) -> None:
        """Update visibility of empty state widget."""
        if not self._tree or not self._empty_state:
            return

        has_items = self._tree.topLevelItemCount() > 0
        self._tree.setVisible(has_items)
        self._empty_state.setVisible(not has_items)

        # Update button states
        self._btn_enable_all.setEnabled(has_items)
        self._btn_disable_all.setEnabled(has_items)
        self._btn_clear_all.setEnabled(has_items)

    @Slot(QTreeWidgetItem, int)
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click."""
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_id:
            return

        # Handle checkbox toggle
        if column == 0:
            enabled = item.checkState(0) == Qt.CheckState.Checked
            self._toggle_breakpoint_enabled(node_id, enabled)
            self.breakpoint_toggled.emit(node_id, enabled)

    @Slot(QTreeWidgetItem, int)
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click (navigate to node or edit)."""
        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_id:
            return

        if column in (3,):  # Condition column - edit
            self.edit_breakpoint.emit(node_id)
        else:  # Other columns - navigate
            self.navigate_to_node.emit(node_id)

    @Slot(object)
    def _on_context_menu(self, position) -> None:
        """Show context menu for breakpoint item."""
        item = self._tree.itemAt(position) if self._tree else None
        if not item:
            return

        node_id = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_id:
            return

        # Store context data for slot methods
        self._context_node_id = node_id
        bp = self._debug_controller.get_breakpoint(node_id) if self._debug_controller else None
        self._context_bp_enabled = bp.enabled if bp else False

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME_V2.bg_elevated};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {THEME_V2.primary};
                color: {THEME_V2.text_on_primary};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {THEME_V2.border};
                margin: 4px 8px;
            }}
        """)

        # Go to Node
        action_goto = QAction("Go to Node", menu)
        action_goto.triggered.connect(self._on_context_goto_node)
        menu.addAction(action_goto)

        # Edit Condition
        action_edit = QAction("Edit Breakpoint...", menu)
        action_edit.triggered.connect(self._on_context_edit_breakpoint)
        menu.addAction(action_edit)

        menu.addSeparator()

        # Enable/Disable
        if bp:
            enable_text = "Disable" if bp.enabled else "Enable"
            action_toggle = QAction(f"{enable_text} Breakpoint", menu)
            action_toggle.triggered.connect(self._on_context_toggle_breakpoint)
            menu.addAction(action_toggle)

        menu.addSeparator()

        # Delete
        action_delete = QAction("Delete Breakpoint", menu)
        action_delete.triggered.connect(self._on_context_delete_breakpoint)
        menu.addAction(action_delete)

        menu.exec(self._tree.mapToGlobal(position))

    @Slot()
    def _on_context_goto_node(self) -> None:
        """Navigate to node from context menu."""
        if hasattr(self, "_context_node_id") and self._context_node_id:
            self.navigate_to_node.emit(self._context_node_id)

    @Slot()
    def _on_context_edit_breakpoint(self) -> None:
        """Edit breakpoint from context menu."""
        if hasattr(self, "_context_node_id") and self._context_node_id:
            self.edit_breakpoint.emit(self._context_node_id)

    @Slot()
    def _on_context_toggle_breakpoint(self) -> None:
        """Toggle breakpoint from context menu."""
        if hasattr(self, "_context_node_id") and self._context_node_id:
            self._toggle_breakpoint_enabled(self._context_node_id, not self._context_bp_enabled)

    @Slot()
    def _on_context_delete_breakpoint(self) -> None:
        """Delete breakpoint from context menu."""
        if hasattr(self, "_context_node_id") and self._context_node_id:
            self._delete_breakpoint(self._context_node_id)

    def _toggle_breakpoint_enabled(self, node_id: str, enabled: bool) -> None:
        """Toggle enabled state of a breakpoint."""
        if not self._debug_controller:
            return

        bp = self._debug_controller.get_breakpoint(node_id)
        if bp:
            bp.enabled = enabled
            self.refresh_breakpoints()
            logger.debug(f"Breakpoint {node_id} {'enabled' if enabled else 'disabled'}")

    def _delete_breakpoint(self, node_id: str) -> None:
        """Delete a breakpoint."""
        if not self._debug_controller:
            return

        self._debug_controller.remove_breakpoint(node_id)
        # refresh_breakpoints will be called via signal

    @Slot()
    def _on_enable_all(self) -> None:
        """Enable all breakpoints."""
        if not self._debug_controller:
            return

        for bp in self._debug_controller.get_all_breakpoints():
            bp.enabled = True

        self.refresh_breakpoints()
        logger.debug("All breakpoints enabled")

    @Slot()
    def _on_disable_all(self) -> None:
        """Disable all breakpoints."""
        if not self._debug_controller:
            return

        for bp in self._debug_controller.get_all_breakpoints():
            bp.enabled = False

        self.refresh_breakpoints()
        logger.debug("All breakpoints disabled")

    @Slot()
    def _on_clear_all(self) -> None:
        """Clear all breakpoints."""
        if not self._debug_controller:
            return

        count = self._debug_controller.clear_all_breakpoints()
        # refresh_breakpoints will be called via signal
        logger.info(f"Cleared {count} breakpoints")

    @Slot(str)
    def _on_breakpoint_added(self, node_id: str) -> None:
        """Handle breakpoint added signal."""
        self.refresh_breakpoints()

    @Slot(str)
    def _on_breakpoint_removed(self, node_id: str) -> None:
        """Handle breakpoint removed signal."""
        self.refresh_breakpoints()

    def cleanup(self) -> None:
        """Clean up panel resources."""
        self._disconnect_controller()
        self._debug_controller = None
        logger.debug("BreakpointsPanel cleaned up")

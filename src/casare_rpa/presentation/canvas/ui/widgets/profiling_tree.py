"""
UiPath-style Profiling Tree Widget.

Displays hierarchical execution profiling with:
- Node execution tree structure
- Duration in human format (Xs Yms)
- Colored percentage progress bars
- Search/filter functionality
"""

from __future__ import annotations

import csv
import functools
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QModelIndex, QRect, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.ui.theme import THEME

if TYPE_CHECKING:
    from PySide6.QtWidgets import QStyleOptionViewItem


@dataclass
class ProfilingEntry:
    """Single profiling entry for a node execution."""

    node_id: str
    node_name: str
    node_type: str
    start_time: datetime
    end_time: datetime | None = None
    duration_ms: float = 0.0
    parent_id: str | None = None
    children: list[ProfilingEntry] = field(default_factory=list)
    percentage: float = 0.0
    status: str = "running"  # running, completed, failed

    @property
    def duration_formatted(self) -> str:
        """Format duration as 'Xs Yms'."""
        if self.duration_ms <= 0:
            return "..."

        total_ms = int(self.duration_ms)

        if total_ms < 1000:
            return f"{total_ms}ms"

        seconds = total_ms // 1000
        ms = total_ms % 1000

        if seconds < 60:
            return f"{seconds}s {ms}ms"

        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s {ms}ms"


class PercentageBarDelegate(QStyledItemDelegate):
    """
    Custom delegate for drawing colored percentage bars.

    Color scheme (UiPath-inspired) using THEME:
    - >= 80%: Red (error)
    - >= 50%: Orange (warning)
    - >= 20%: Yellow
    - < 20%: Green (success)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._colors = [
            (80, QColor(THEME.error)),  # Red for >= 80%
            (50, QColor(THEME.warning)),  # Orange for >= 50%
            (20, QColor(THEME.warning)),  # Yellow/Amber for >= 20%
            (0, QColor(THEME.success)),  # Green for < 20%
        ]

    def _get_color(self, percentage: float) -> QColor:
        """Get color based on percentage value."""
        for threshold, color in self._colors:
            if percentage >= threshold:
                return color
        return self._colors[-1][1]

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Paint the percentage bar with text."""
        # Get percentage value from item data
        percentage = index.data(Qt.ItemDataRole.UserRole)
        if percentage is None:
            super().paint(painter, option, index)
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw selection background if selected
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        # Bar dimensions - slightly smaller than cell
        margin_v = 6
        margin_h = 6
        rect = option.rect.adjusted(margin_h, margin_v, -margin_h, -margin_v)
        radius = rect.height() / 2

        # Draw background bar (track)
        bg_color = QColor(THEME.bg_darkest)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(rect, radius, radius)

        # Draw filled portion
        if percentage > 0:
            fill_width = int(rect.width() * min(percentage, 100) / 100)
            if fill_width > 0:
                # Minimum width for visibility if > 0%
                fill_width = max(fill_width, int(radius * 2))

                fill_rect = QRect(rect.x(), rect.y(), fill_width, rect.height())
                bar_color = self._get_color(percentage)

                painter.setBrush(bar_color)
                painter.drawRoundedRect(fill_rect, radius, radius)

        # Draw percentage text (if enough space)
        if rect.width() > 40:
            text = f"{percentage:.1f}%"
            painter.setPen(QColor(THEME.text_header))
            font = painter.font()
            font.setPointSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignCenter,
                text,
            )

        painter.restore()

    def sizeHint(
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex,
    ) -> None:
        """Return size hint for the item."""
        size = super().sizeHint(option, index)
        size.setWidth(max(size.width(), 80))
        return size


class ProfilingTreeWidget(QWidget):
    """
    UiPath-style profiling tree widget.

    Displays hierarchical execution profiling with colored percentage bars.
    Features a collapsible root node showing total execution time.

    Signals:
        node_clicked: Emitted when a node is clicked (str: node_id) - selects node
        node_double_clicked: Emitted when a node is double-clicked (str: node_id)
    """

    node_clicked = Signal(str)
    node_double_clicked = Signal(str)

    # Column indices
    COL_ACTIVITY = 0
    COL_DURATION = 1
    COL_PERCENTAGE = 2

    # Root node identifier
    ROOT_NODE_ID = "__root__"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._entries: dict[str, ProfilingEntry] = {}
        self._root_entries: list[str] = []
        self._total_duration_ms: float = 0.0
        self._total_nodes: int = 0
        self._failed_nodes: int = 0
        self._tree_items: dict[str, QTreeWidgetItem] = {}
        self._root_item: QTreeWidgetItem | None = None
        self._workflow_name: str = "Workflow Execution"

        # Pulse timer for live indicator
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._on_pulse_tick)
        self._pulse_step = 0

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Summary Header
        self._summary_widget = QWidget()
        summary_layout = QHBoxLayout(self._summary_widget)
        summary_layout.setContentsMargins(8, 4, 8, 4)

        self._lbl_total_time = QLabel("Total Time: 0ms")
        self._lbl_nodes_count = QLabel("Nodes: 0")
        self._lbl_success_rate = QLabel("Success: 100%")

        summary_layout.addWidget(self._lbl_total_time)
        summary_layout.addStretch()
        summary_layout.addWidget(self._lbl_nodes_count)
        summary_layout.addSpacing(10)
        summary_layout.addWidget(self._lbl_success_rate)

        layout.addWidget(self._summary_widget)

        # Tree widget (created before toolbar to allow connections)
        self._tree = QTreeWidget()
        self._tree.setColumnCount(3)
        self._tree.setHeaderLabels(["Activity", "Duration", "% Time"])
        self._tree.setAlternatingRowColors(True)
        self._tree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setAnimated(True)
        self._tree.setIndentation(20)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Set column widths
        header = self._tree.header()
        header.setSectionResizeMode(self.COL_ACTIVITY, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_DURATION, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PERCENTAGE, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(self.COL_PERCENTAGE, 100)

        # Set custom delegate for percentage column
        self._percentage_delegate = PercentageBarDelegate(self._tree)
        self._tree.setItemDelegateForColumn(self.COL_PERCENTAGE, self._percentage_delegate)

        # Toolbar with search and buttons
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 0, 4, 0)
        toolbar.setSpacing(4)

        self._search_input = QLineEdit()
        self._search_input.setObjectName("profiling_search")
        self._search_input.setPlaceholderText("Search activities...")
        self._search_input.textChanged.connect(self._filter_tree)

        self._btn_expand = QPushButton("Expand")
        self._btn_expand.setObjectName("profiling_btn")
        self._btn_expand.setFixedWidth(60)
        self._btn_expand.clicked.connect(functools.partial(self._tree.expandAll))

        self._btn_collapse = QPushButton("Collapse")
        self._btn_collapse.setObjectName("profiling_btn")
        self._btn_collapse.setFixedWidth(60)
        self._btn_collapse.clicked.connect(functools.partial(self._tree.collapseAll))

        self._btn_export = QPushButton("Export")
        self._btn_export.setObjectName("profiling_btn")
        self._btn_export.setFixedWidth(60)
        self._btn_export.clicked.connect(self.export_csv)

        self._btn_clear = QPushButton("Clear")
        self._btn_clear.setObjectName("profiling_btn")
        self._btn_clear.setFixedWidth(50)
        self._btn_clear.clicked.connect(self.clear)

        toolbar.addWidget(self._search_input)
        toolbar.addWidget(self._btn_expand)
        toolbar.addWidget(self._btn_collapse)
        toolbar.addWidget(self._btn_export)
        toolbar.addWidget(self._btn_clear)

        layout.addLayout(toolbar)
        layout.addWidget(self._tree)

    def _apply_styles(self) -> None:
        """Apply dark theme styling using THEME."""
        self.setStyleSheet(f"""
            ProfilingTreeWidget {{
                background-color: {THEME.bg_panel};
            }}
            #summary_widget {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            QLabel {{
                color: {THEME.text_secondary};
                font-size: 11px;
                font-weight: 500;
            }}
            QTreeWidget {{
                background-color: {THEME.bg_medium};
                alternate-background-color: {THEME.bg_light};
                border: 1px solid {THEME.border};
                color: {THEME.text_primary};
                font-size: 11px;
            }}
            QTreeWidget::item {{
                padding: 4px 2px;
                min-height: 24px;
            }}
            QTreeWidget::item:selected {{
                background-color: {THEME.selected};
            }}
            QHeaderView::section {{
                background-color: {THEME.input_bg};
                color: {THEME.text_primary};
                border: none;
                border-right: 1px solid {THEME.border};
                border-bottom: 1px solid {THEME.border};
                padding: 6px;
                font-weight: bold;
                font-size: 10px;
                text-transform: uppercase;
            }}
            QLineEdit#profiling_search {{
                background-color: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 11px;
            }}
            QLineEdit#profiling_search:focus {{
                border-color: {THEME.accent_primary};
            }}
            QPushButton#profiling_btn {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 10px;
            }}
            QPushButton#profiling_btn:hover {{
                background-color: {THEME.bg_hover};
            }}
            QPushButton#profiling_btn:pressed {{
                background-color: {THEME.bg_lighter};
            }}
        """)
        self._summary_widget.setObjectName("summary_widget")

    def clear(self) -> None:
        """Clear all profiling data."""
        self._entries.clear()
        self._root_entries.clear()
        self._tree_items.clear()
        self._total_duration_ms = 0.0
        self._total_nodes = 0
        self._failed_nodes = 0
        self._root_item = None
        self._tree.clear()
        self._pulse_timer.stop()
        self._update_summary_labels()

    def export_csv(self) -> None:
        """Export profiling data to CSV file."""
        if not self._entries:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Profiling Data", "profiling_data.csv", "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Node ID", "Name", "Type", "Duration (ms)", "Percentage", "Status"]
                )

                # Use a stack-based traversal to keep hierarchy if needed,
                # but flat is easier for basic CSV
                for entry in self._entries.values():
                    writer.writerow(
                        [
                            entry.node_id,
                            entry.node_name,
                            entry.node_type,
                            f"{entry.duration_ms:.2f}",
                            f"{entry.percentage:.1f}%",
                            entry.status,
                        ]
                    )
            logger.info(f"Exported profiling data to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export profiling data: {e}")

    def _on_pulse_tick(self) -> None:
        """Update live indicator pulse effect."""
        self._pulse_step = (self._pulse_step + 1) % 4
        pulse_icons = ["⏳", "⌛", "⏳", "⌛"]

        for node_id, entry in self._entries.items():
            if entry.status == "running" and node_id in self._tree_items:
                item = self._tree_items[node_id]
                icon = pulse_icons[self._pulse_step]
                item.setText(self.COL_ACTIVITY, f"{icon} {entry.node_name}")

    def _update_summary_labels(self) -> None:
        """Update the summary header labels."""
        self._lbl_total_time.setText(f"Total Time: {self._format_ms(self._total_duration_ms)}")
        self._lbl_nodes_count.setText(f"Nodes: {self._total_nodes}")

        success_rate = 100.0
        if self._total_nodes > 0:
            success_rate = ((self._total_nodes - self._failed_nodes) / self._total_nodes) * 100

        self._lbl_success_rate.setText(f"Success: {success_rate:.1f}%")
        if success_rate < 80:
            self._lbl_success_rate.setStyleSheet(f"color: {THEME.status_error};")
        elif success_rate < 100:
            self._lbl_success_rate.setStyleSheet(f"color: {THEME.status_warning};")
        else:
            self._lbl_success_rate.setStyleSheet(f"color: {THEME.text_secondary};")

    def _format_ms(self, ms: float) -> str:
        """Format milliseconds into human readable string."""
        total_ms = int(ms)
        if total_ms < 1000:
            return f"{total_ms}ms"

        seconds = total_ms / 1000
        if seconds < 60:
            return f"{seconds:.2f}s"

        minutes = int(seconds // 60)
        rem_seconds = seconds % 60
        return f"{minutes}m {rem_seconds:.1f}s"

    def set_workflow_name(self, name: str) -> None:
        """Set the workflow name displayed in the root node."""
        self._workflow_name = name or "Workflow Execution"
        if self._root_item:
            self._root_item.setText(self.COL_ACTIVITY, f"🔷 {self._workflow_name}")

    def _ensure_root_item(self) -> QTreeWidgetItem:
        """Ensure the root item exists and return it."""
        if self._root_item is None:
            self._root_item = QTreeWidgetItem(self._tree)
            self._root_item.setText(self.COL_ACTIVITY, f"🔷 {self._workflow_name}")
            self._root_item.setText(self.COL_DURATION, "...")
            self._root_item.setData(self.COL_PERCENTAGE, Qt.ItemDataRole.UserRole, 100.0)
            self._root_item.setData(self.COL_ACTIVITY, Qt.ItemDataRole.UserRole, self.ROOT_NODE_ID)

            # Style the root item with bold font
            font = self._root_item.font(self.COL_ACTIVITY)
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            self._root_item.setFont(self.COL_ACTIVITY, font)
            self._root_item.setFont(self.COL_DURATION, font)

            # Expand by default
            self._root_item.setExpanded(True)

        return self._root_item

    def _update_root_item(self) -> None:
        """Update the root item with total duration."""
        if self._root_item is None:
            return

        # Format total duration
        total_ms = int(self._total_duration_ms)
        if total_ms <= 0:
            duration_text = "..."
        elif total_ms < 1000:
            duration_text = f"{total_ms}ms"
        elif total_ms < 60000:
            seconds = total_ms // 1000
            ms = total_ms % 1000
            duration_text = f"{seconds}s {ms}ms"
        else:
            minutes = total_ms // 60000
            remaining_ms = total_ms % 60000
            seconds = remaining_ms // 1000
            ms = remaining_ms % 1000
            duration_text = f"{minutes}m {seconds}s {ms}ms"

        self._root_item.setText(self.COL_DURATION, duration_text)
        self._root_item.setData(self.COL_PERCENTAGE, Qt.ItemDataRole.UserRole, 100.0)

    @Slot(str, str, str, object)
    def add_entry(
        self,
        node_id: str,
        node_name: str,
        node_type: str,
        parent_id: str | None = None,
    ) -> None:
        """
        Add a new profiling entry when node execution starts.

        Args:
            node_id: Unique node identifier
            node_name: Display name of the node
            node_type: Type of the node
            parent_id: Optional parent node ID for hierarchy
        """
        entry = ProfilingEntry(
            node_id=node_id,
            node_name=node_name,
            node_type=node_type,
            start_time=datetime.now(),
            parent_id=parent_id,
        )
        self._entries[node_id] = entry
        self._total_nodes += 1

        # Add to parent's children or root list
        if parent_id and parent_id in self._entries:
            self._entries[parent_id].children.append(entry)
        else:
            self._root_entries.append(node_id)

        # Create tree item
        self._create_tree_item(entry)
        self._update_summary_labels()

        # Start pulse timer if not running
        if not self._pulse_timer.isActive():
            self._pulse_timer.start(500)

    @Slot(str, float, str)
    def update_entry(
        self,
        node_id: str,
        duration_ms: float,
        status: str = "completed",
    ) -> None:
        """
        Update a profiling entry when node execution completes.

        Args:
            node_id: Unique node identifier
            duration_ms: Execution duration in milliseconds
            status: Execution status (completed, failed)
        """
        if node_id not in self._entries:
            return

        entry = self._entries[node_id]
        entry.end_time = datetime.now()
        entry.duration_ms = duration_ms
        entry.status = status

        if status == "failed":
            self._failed_nodes += 1

        # Recalculate total duration and percentages
        self._recalculate_percentages()

        # Update tree item
        self._update_tree_item(entry)
        self._update_summary_labels()

        # Check if any nodes are still running
        any_running = any(e.status == "running" for e in self._entries.values())
        if not any_running:
            self._pulse_timer.stop()

    def _recalculate_percentages(self) -> None:
        """Recalculate percentages for all entries."""
        # Find total duration from root entries
        self._total_duration_ms = sum(
            self._entries[node_id].duration_ms
            for node_id in self._root_entries
            if node_id in self._entries and self._entries[node_id].duration_ms > 0
        )

        # Update root item with total duration
        self._update_root_item()

        if self._total_duration_ms <= 0:
            return

        # Calculate percentage for each entry
        for entry in self._entries.values():
            if entry.duration_ms > 0:
                entry.percentage = (entry.duration_ms / self._total_duration_ms) * 100

    def _create_tree_item(self, entry: ProfilingEntry) -> QTreeWidgetItem:
        """Create a tree item for the entry."""
        # Determine parent - use root item for top-level entries
        if entry.parent_id and entry.parent_id in self._tree_items:
            parent = self._tree_items[entry.parent_id]
        else:
            # Top-level entries go under the root item
            parent = self._ensure_root_item()

        item = QTreeWidgetItem(parent)
        item.setText(self.COL_ACTIVITY, f"{self._get_icon(entry.node_type)} {entry.node_name}")
        item.setText(self.COL_DURATION, entry.duration_formatted)
        item.setData(self.COL_PERCENTAGE, Qt.ItemDataRole.UserRole, entry.percentage)
        item.setData(self.COL_ACTIVITY, Qt.ItemDataRole.UserRole, entry.node_id)

        # Set font for running status
        if entry.status == "running":
            font = item.font(self.COL_ACTIVITY)
            font.setItalic(True)
            item.setFont(self.COL_ACTIVITY, font)

        self._tree_items[entry.node_id] = item

        # Expand parent
        if entry.parent_id and entry.parent_id in self._tree_items:
            self._tree_items[entry.parent_id].setExpanded(True)

        return item

    def _update_tree_item(self, entry: ProfilingEntry) -> None:
        """Update tree item with new entry data."""
        if entry.node_id not in self._tree_items:
            return

        item = self._tree_items[entry.node_id]
        item.setText(self.COL_DURATION, entry.duration_formatted)
        item.setData(self.COL_PERCENTAGE, Qt.ItemDataRole.UserRole, entry.percentage)

        # Reset font
        font = item.font(self.COL_ACTIVITY)
        font.setItalic(False)
        item.setFont(self.COL_ACTIVITY, font)

        # Color for failed status
        if entry.status == "failed":
            item.setForeground(self.COL_ACTIVITY, QBrush(QColor(THEME.error)))

        # Update all items with new percentages
        for node_id, e in self._entries.items():
            if node_id in self._tree_items:
                self._tree_items[node_id].setData(
                    self.COL_PERCENTAGE,
                    Qt.ItemDataRole.UserRole,
                    e.percentage,
                )

        # Force repaint
        self._tree.viewport().update()

    def _get_icon(self, node_type: str) -> str:
        """Get icon character for node type."""
        type_lower = node_type.lower()

        if "browser" in type_lower or "web" in type_lower:
            return "🌐"
        elif "click" in type_lower:
            return "👆"
        elif "type" in type_lower or "input" in type_lower:
            return "⌨️"
        elif "read" in type_lower or "get" in type_lower:
            return "📖"
        elif "write" in type_lower or "set" in type_lower:
            return "✏️"
        elif "loop" in type_lower or "for" in type_lower:
            return "🔄"
        elif "if" in type_lower or "condition" in type_lower:
            return "❓"
        elif "excel" in type_lower or "spreadsheet" in type_lower:
            return "📊"
        elif "email" in type_lower or "mail" in type_lower:
            return "📧"
        elif "file" in type_lower:
            return "📁"
        elif "database" in type_lower or "sql" in type_lower:
            return "🗃️"
        elif "api" in type_lower or "http" in type_lower:
            return "🔗"
        elif "delay" in type_lower or "wait" in type_lower:
            return "⏳"
        elif "start" in type_lower:
            return "▶️"
        elif "end" in type_lower:
            return "⏹️"
        elif "subflow" in type_lower or "invoke" in type_lower:
            return "📦"
        elif "python" in type_lower or "script" in type_lower:
            return "🐍"
        elif "ocr" in type_lower:
            return "👁️"
        elif "keyboard" in type_lower:
            return "⌨️"
        elif "mouse" in type_lower:
            return "🖱️"
        elif "terminal" in type_lower:
            return "🖥️"
        elif "variable" in type_lower:
            return "💎"
        else:
            return "⚡"

    def _filter_tree(self, text: str) -> None:
        """Filter tree items by search text."""
        search_text = text.lower().strip()

        def set_item_visible(item: QTreeWidgetItem, is_root: bool = False) -> bool:
            """Recursively set item visibility."""
            activity = item.text(self.COL_ACTIVITY).lower()
            # Root always matches if any child matches
            matches = is_root or not search_text or search_text in activity

            # Check children
            child_matches = False
            for i in range(item.childCount()):
                child = item.child(i)
                if set_item_visible(child, is_root=False):
                    child_matches = True

            # Root stays visible if any child matches
            if is_root:
                matches = child_matches or not search_text
            elif child_matches:
                matches = True

            item.setHidden(not matches)
            if matches and search_text:
                item.setExpanded(True)

            return matches

        # Process root item (the only top-level item)
        if self._root_item:
            set_item_visible(self._root_item, is_root=True)

    @Slot(QTreeWidgetItem, int)
    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click to select node in canvas."""
        node_id = item.data(self.COL_ACTIVITY, Qt.ItemDataRole.UserRole)
        logger.debug(f"ProfilingTree: Item clicked, node_id={node_id}")

        # Don't emit for root node, only for actual workflow nodes
        if node_id and node_id != self.ROOT_NODE_ID:
            logger.debug(f"ProfilingTree: Emitting node_clicked({node_id})")
            self.node_clicked.emit(node_id)
        else:
            logger.debug("ProfilingTree: Clicked root or empty node_id, not emitting")

    @Slot(QTreeWidgetItem, int)
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click to navigate to node."""
        node_id = item.data(self.COL_ACTIVITY, Qt.ItemDataRole.UserRole)
        # Don't emit for root node, only for actual workflow nodes
        if node_id and node_id != self.ROOT_NODE_ID:
            self.node_double_clicked.emit(node_id)

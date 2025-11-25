"""
Workflows view for CasareRPA Orchestrator.
Displays workflow library and management.
"""
import asyncio
from pathlib import Path
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QLabel, QMessageBox, QMenu, QDialog,
    QFormLayout, QLineEdit, QTextEdit, QComboBox, QDialogButtonBox,
    QFileDialog
)
from PySide6.QtCore import Qt, Signal

from ..styles import COLORS
from ..widgets import SearchBar, ActionButton, SectionHeader, StatusBadge, EmptyState
from ..models import Workflow, WorkflowStatus
from ..services import OrchestratorService


class WorkflowDetailsDialog(QDialog):
    """Dialog showing workflow details."""

    def __init__(self, workflow: Workflow, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"Workflow: {workflow.name}")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Info
        info_layout = QFormLayout()
        info_layout.setSpacing(12)

        info_layout.addRow("Name:", QLabel(workflow.name))
        info_layout.addRow("Version:", QLabel(f"v{workflow.version}"))

        status_badge = StatusBadge(workflow.status.value)
        info_layout.addRow("Status:", status_badge)

        info_layout.addRow("Description:", QLabel(workflow.description or "-"))
        info_layout.addRow("Created:", QLabel(str(workflow.created_at) if workflow.created_at else "-"))
        info_layout.addRow("Updated:", QLabel(str(workflow.updated_at) if workflow.updated_at else "-"))
        info_layout.addRow("Executions:", QLabel(str(workflow.execution_count)))
        info_layout.addRow("Success Rate:", QLabel(f"{workflow.success_rate:.1f}%"))

        if workflow.tags:
            info_layout.addRow("Tags:", QLabel(", ".join(workflow.tags)))

        layout.addLayout(info_layout)

        # JSON preview
        json_label = QLabel("Workflow JSON:")
        json_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-weight: 600;")
        layout.addWidget(json_label)

        json_text = QTextEdit()
        json_text.setReadOnly(True)
        json_text.setPlainText(workflow.json_definition[:2000] + "..." if len(workflow.json_definition) > 2000 else workflow.json_definition)
        json_text.setStyleSheet(f"""
            background-color: {COLORS['bg_medium']};
            color: {COLORS['text_primary']};
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
        """)
        layout.addWidget(json_text)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class DispatchDialog(QDialog):
    """Dialog for dispatching a workflow."""

    def __init__(
        self,
        workflow: Workflow,
        robots: list,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Dispatch: {workflow.name}")
        self.setMinimumWidth(400)

        self.workflow = workflow
        self.selected_robot_id = None

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Workflow info
        info_label = QLabel(f"Dispatching workflow: <b>{workflow.name}</b> (v{workflow.version})")
        layout.addWidget(info_label)

        # Robot selection
        form = QFormLayout()

        self._robot_combo = QComboBox()
        available_robots = [r for r in robots if r.is_available]

        if available_robots:
            for robot in available_robots:
                self._robot_combo.addItem(f"{robot.name} ({robot.id[:8]}...)", robot.id)
        else:
            self._robot_combo.addItem("No available robots", None)
            self._robot_combo.setEnabled(False)

        form.addRow("Target Robot:", self._robot_combo)

        # Priority
        self._priority_combo = QComboBox()
        self._priority_combo.addItems(["Normal", "Low", "High", "Critical"])
        form.addRow("Priority:", self._priority_combo)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        if not available_robots:
            buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(buttons)

    def _on_accept(self):
        self.selected_robot_id = self._robot_combo.currentData()
        self.selected_priority = self._priority_combo.currentText().upper()
        self.accept()


class WorkflowsView(QWidget):
    """Workflows library view."""

    def __init__(self, service: OrchestratorService, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._service = service
        self._workflows: List[Workflow] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        header = SectionHeader("Workflows")
        header_layout.addWidget(header)

        header_layout.addStretch()

        import_btn = ActionButton("Import", "📥", primary=False)
        import_btn.clicked.connect(self._import_workflow)
        header_layout.addWidget(import_btn)

        refresh_btn = ActionButton("Refresh", "🔄", primary=False)
        refresh_btn.clicked.connect(lambda: asyncio.get_event_loop().create_task(self.refresh()))
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Search and filters
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search = SearchBar(
            "Search workflows...",
            filters=["All", "Draft", "Published", "Archived"]
        )
        self._search.search_changed.connect(self._apply_filter)
        self._search.filter_changed.connect(self._apply_filter)
        toolbar.addWidget(self._search)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Workflows table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels([
            "Status", "Name", "Version", "Executions", "Success Rate", "Updated", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 100)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(2, 80)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 200)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        # Empty state
        self._empty_state = EmptyState(
            icon="📁",
            title="No Workflows Found",
            description="Import a workflow JSON file to get started.",
            action_text="Import Workflow"
        )
        self._empty_state.action_clicked.connect(self._import_workflow)
        self._empty_state.hide()
        layout.addWidget(self._empty_state)

    def _apply_filter(self):
        """Apply search and filter to table."""
        search_text = self._search.get_search_text().lower()
        filter_status = self._search.get_filter()

        for row in range(self._table.rowCount()):
            show = True

            if filter_status and filter_status != "All":
                status_widget = self._table.cellWidget(row, 0)
                if status_widget:
                    status_text = status_widget.text().lower()
                    if filter_status.lower() != status_text:
                        show = False

            if show and search_text:
                row_text = ""
                for col in range(self._table.columnCount()):
                    item = self._table.item(row, col)
                    if item:
                        row_text += item.text().lower() + " "
                if search_text not in row_text:
                    show = False

            self._table.setRowHidden(row, not show)

    def _show_context_menu(self, pos):
        """Show context menu for workflow row."""
        row = self._table.rowAt(pos.y())
        if row < 0 or row >= len(self._workflows):
            return

        workflow = self._workflows[row]
        menu = QMenu(self)

        view_action = menu.addAction("👁️ View Details")
        view_action.triggered.connect(lambda: self._show_details(workflow))

        dispatch_action = menu.addAction("▶️ Dispatch")
        dispatch_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._dispatch_workflow(workflow)))
        dispatch_action.setEnabled(workflow.status == WorkflowStatus.PUBLISHED)

        menu.addSeparator()

        if workflow.status == WorkflowStatus.DRAFT:
            publish_action = menu.addAction("📤 Publish")
            publish_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._publish_workflow(workflow)))

        if workflow.status == WorkflowStatus.PUBLISHED:
            archive_action = menu.addAction("📦 Archive")
            archive_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._archive_workflow(workflow)))

        menu.addSeparator()

        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: asyncio.get_event_loop().create_task(self._delete_workflow(workflow)))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_double_click(self, row: int, col: int):
        """Handle double-click on table row."""
        if 0 <= row < len(self._workflows):
            self._show_details(self._workflows[row])

    def _show_details(self, workflow: Workflow):
        """Show workflow details dialog."""
        dialog = WorkflowDetailsDialog(workflow, self)
        dialog.exec()

    def _import_workflow(self):
        """Import a workflow from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Workflow",
            str(Path.cwd() / "workflows"),
            "Workflow Files (*.json)"
        )

        if file_path:
            asyncio.get_event_loop().create_task(self._do_import(Path(file_path)))

    async def _do_import(self, file_path: Path):
        """Perform workflow import."""
        workflow = await self._service.import_workflow_from_file(file_path)
        if workflow:
            QMessageBox.information(self, "Success", f"Workflow '{workflow.name}' imported successfully!")
            await self.refresh()
        else:
            QMessageBox.warning(self, "Error", "Failed to import workflow")

    async def _dispatch_workflow(self, workflow: Workflow):
        """Dispatch a workflow to a robot."""
        robots = await self._service.get_robots()

        dialog = DispatchDialog(workflow, robots, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            from ..models import JobPriority
            priority_map = {
                "LOW": JobPriority.LOW,
                "NORMAL": JobPriority.NORMAL,
                "HIGH": JobPriority.HIGH,
                "CRITICAL": JobPriority.CRITICAL,
            }
            priority = priority_map.get(dialog.selected_priority, JobPriority.NORMAL)

            job = await self._service.dispatch_workflow(
                workflow.id,
                dialog.selected_robot_id,
                priority
            )
            if job:
                QMessageBox.information(self, "Success", f"Job dispatched: {job.id[:8]}...")
            else:
                QMessageBox.warning(self, "Error", "Failed to dispatch workflow")

    async def _publish_workflow(self, workflow: Workflow):
        """Publish a workflow."""
        workflow.status = WorkflowStatus.PUBLISHED
        if await self._service.save_workflow(workflow):
            await self.refresh()
        else:
            QMessageBox.warning(self, "Error", "Failed to publish workflow")

    async def _archive_workflow(self, workflow: Workflow):
        """Archive a workflow."""
        workflow.status = WorkflowStatus.ARCHIVED
        if await self._service.save_workflow(workflow):
            await self.refresh()
        else:
            QMessageBox.warning(self, "Error", "Failed to archive workflow")

    async def _delete_workflow(self, workflow: Workflow):
        """Delete a workflow."""
        reply = QMessageBox.question(
            self, "Delete Workflow",
            f"Are you sure you want to delete '{workflow.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if await self._service.delete_workflow(workflow.id):
                await self.refresh()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete workflow")

    def _update_table(self):
        """Update the table with current workflows."""
        self._table.setRowCount(len(self._workflows))

        if not self._workflows:
            self._table.hide()
            self._empty_state.show()
            return

        self._table.show()
        self._empty_state.hide()

        for row, workflow in enumerate(self._workflows):
            # Status badge
            status_badge = StatusBadge(workflow.status.value)
            self._table.setCellWidget(row, 0, status_badge)

            # Name
            self._table.setItem(row, 1, QTableWidgetItem(workflow.name))

            # Version
            self._table.setItem(row, 2, QTableWidgetItem(f"v{workflow.version}"))

            # Executions
            self._table.setItem(row, 3, QTableWidgetItem(str(workflow.execution_count)))

            # Success Rate
            self._table.setItem(row, 4, QTableWidgetItem(f"{workflow.success_rate:.1f}%"))

            # Updated
            updated = str(workflow.updated_at)[:19] if workflow.updated_at else "-"
            self._table.setItem(row, 5, QTableWidgetItem(updated))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(4)

            view_btn = ActionButton("View", "👁️", primary=False)
            view_btn.clicked.connect(lambda checked, w=workflow: self._show_details(w))
            actions_layout.addWidget(view_btn)

            dispatch_btn = ActionButton("Dispatch", "▶️", primary=True)
            dispatch_btn.setEnabled(workflow.status == WorkflowStatus.PUBLISHED)
            dispatch_btn.clicked.connect(lambda checked, w=workflow: asyncio.get_event_loop().create_task(self._dispatch_workflow(w)))
            actions_layout.addWidget(dispatch_btn)

            self._table.setCellWidget(row, 6, actions_widget)

    async def refresh(self):
        """Refresh workflows data."""
        try:
            self._workflows = await self._service.get_workflows()
            self._update_table()
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to refresh workflows: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load workflows: {e}")

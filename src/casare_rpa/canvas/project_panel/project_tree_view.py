"""
CasareRPA - Project Tree View (QTreeView)

A QTreeView subclass for displaying the project tree.
Handles user interactions, context menus, and visual styling.
"""

from typing import Optional, Set

from PySide6.QtWidgets import (
    QTreeView,
    QMenu,
    QAbstractItemView,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)
from PySide6.QtCore import Qt, Signal, QModelIndex, QItemSelectionModel
from PySide6.QtGui import QAction, QPainter, QFont
from loguru import logger

from ..theme import THEME
from .project_model import ProjectModel, TreeItemType
from .project_proxy_model import ProjectProxyModel
from ...core.project_schema import Project, Scenario


class ProjectTreeView(QTreeView):
    """
    Tree view for project navigation using Model/View architecture.

    Displays:
    - Projects section with expandable projects
      - Scenarios folder with scenario items
      - Variables folder
      - Credentials folder
    - Global Resources section
      - Global Variables
      - Global Credentials

    Signals:
        item_double_clicked: Emitted on double-click (item_type: str, item_data: object)
        scenario_selected: Emitted when scenario is selected (Scenario)
        project_selected: Emitted when project is selected (Project)
        variables_requested: Emitted when user wants to edit variables (scope: str)
        credentials_requested: Emitted when user wants to edit credentials (scope: str)
        new_scenario_requested: Emitted when user wants to create new scenario
        delete_scenario_requested: Emitted when user wants to delete scenario (Scenario)
        duplicate_scenario_requested: Emitted when user wants to duplicate scenario (Scenario)
        delete_project_requested: Emitted when user wants to delete project (Project)
        close_project_requested: Emitted when user wants to close current project
        import_workflow_requested: Emitted when user wants to import workflow
        export_scenario_requested: Emitted when user wants to export scenario (Scenario)
    """

    item_double_clicked = Signal(str, object)  # item_type, item_data
    scenario_selected = Signal(object)  # Scenario
    project_selected = Signal(object)  # Project
    variables_requested = Signal(str)  # scope
    credentials_requested = Signal(str)  # scope
    new_scenario_requested = Signal()
    delete_scenario_requested = Signal(object)  # Scenario
    duplicate_scenario_requested = Signal(object)  # Scenario
    delete_project_requested = Signal(object)  # Project
    close_project_requested = Signal()  # Close current project
    import_workflow_requested = Signal()  # Import workflow file as scenario
    export_scenario_requested = Signal(object)  # Export scenario (Scenario)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Setup view properties
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setIndentation(16)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(False)  # We handle double-click ourselves

        # Track expanded state for restoration after refresh
        self._expanded_items: Set[str] = set()

        # Connect signals
        self._connect_signals()
        self._apply_styles()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.doubleClicked.connect(self._on_double_clicked)
        self.clicked.connect(self._on_clicked)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self.expanded.connect(self._on_expanded)
        self.collapsed.connect(self._on_collapsed)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QTreeView {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: none;
                outline: none;
            }}

            QTreeView::item {{
                padding: 4px 8px;
                border-radius: 2px;
            }}

            QTreeView::item:hover {{
                background: {THEME.bg_hover};
            }}

            QTreeView::item:selected {{
                background: {THEME.bg_selected};
                color: white;
            }}

            QTreeView::branch {{
                background: {THEME.bg_panel};
            }}

            QTreeView::branch:has-siblings:!adjoins-item {{
                border-image: none;
            }}

            QTreeView::branch:has-siblings:adjoins-item {{
                border-image: none;
            }}

            QTreeView::branch:!has-children:!has-siblings:adjoins-item {{
                border-image: none;
            }}

            QTreeView::branch:has-children:!has-siblings:closed,
            QTreeView::branch:closed:has-children:has-siblings {{
                image: none;
                border-image: none;
            }}

            QTreeView::branch:open:has-children:!has-siblings,
            QTreeView::branch:open:has-children:has-siblings {{
                image: none;
                border-image: none;
            }}
        """)

    def _get_item_type(self, index: QModelIndex) -> Optional[TreeItemType]:
        """Get item type from index (handles proxy model)."""
        model = self.model()
        if isinstance(model, ProjectProxyModel):
            return model.getItemType(index)
        elif isinstance(model, ProjectModel):
            return model.getItemType(index)
        return None

    def _get_item_data(self, index: QModelIndex):
        """Get item data from index (handles proxy model)."""
        model = self.model()
        if isinstance(model, ProjectProxyModel):
            return model.getItemData(index)
        elif isinstance(model, ProjectModel):
            return model.getItemData(index)
        return None

    def _get_item_key(self, index: QModelIndex) -> str:
        """Generate a unique key for tracking expanded state."""
        item_type = self._get_item_type(index)
        item_data = self._get_item_data(index)

        if item_type == TreeItemType.PROJECT and isinstance(item_data, Project):
            return f"project:{item_data.id}"
        elif item_type == TreeItemType.SCENARIOS_FOLDER:
            return "scenarios_folder"
        elif item_type == TreeItemType.PROJECTS_HEADER:
            return "projects_header"
        elif item_type == TreeItemType.GLOBAL_HEADER:
            return "global_header"

        # Default key based on text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        return f"item:{text}"

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_clicked(self, index: QModelIndex) -> None:
        """Handle single click on item."""
        item_type = self._get_item_type(index)
        item_data = self._get_item_data(index)

        if item_type == TreeItemType.SCENARIO:
            self.scenario_selected.emit(item_data)
        elif item_type == TreeItemType.PROJECT and isinstance(item_data, Project):
            self.project_selected.emit(item_data)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        """Handle double-click on item."""
        item_type = self._get_item_type(index)
        item_data = self._get_item_data(index)

        if item_type == TreeItemType.SCENARIO:
            self.item_double_clicked.emit("scenario", item_data)
        elif item_type == TreeItemType.PROJECT:
            if isinstance(item_data, dict):
                # Recent project - open it
                self.item_double_clicked.emit("recent_project", item_data)
            else:
                self.item_double_clicked.emit("project", item_data)
        elif item_type == TreeItemType.RECENT_PROJECT:
            self.item_double_clicked.emit("recent_project", item_data)
        elif item_type == TreeItemType.VARIABLES_FOLDER:
            self.variables_requested.emit("project")
        elif item_type == TreeItemType.CREDENTIALS_FOLDER:
            self.credentials_requested.emit("project")
        elif item_type == TreeItemType.GLOBAL_VARIABLES:
            self.variables_requested.emit("global")
        elif item_type == TreeItemType.GLOBAL_CREDENTIALS:
            self.credentials_requested.emit("global")
        elif item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER,
                          TreeItemType.SCENARIOS_FOLDER):
            # Toggle expansion on double-click for folders/headers
            if self.isExpanded(index):
                self.collapse(index)
            else:
                self.expand(index)

    def _on_context_menu(self, position) -> None:
        """Handle context menu request."""
        index = self.indexAt(position)
        if not index.isValid():
            return

        item_type = self._get_item_type(index)
        item_data = self._get_item_data(index)
        menu = QMenu(self)

        if item_type == TreeItemType.PROJECT:
            if isinstance(item_data, Project):
                # Current project context menu
                menu.addAction("Close Project", self.close_project_requested.emit)
                menu.addSeparator()
                menu.addAction("New Scenario...", self.new_scenario_requested.emit)
                menu.addSeparator()
                menu.addAction("Manage Variables...",
                               lambda: self.variables_requested.emit("project"))
                menu.addAction("Manage Credentials...",
                               lambda: self.credentials_requested.emit("project"))
                menu.addSeparator()
                menu.addAction("Delete Project...",
                               lambda: self.delete_project_requested.emit(item_data))

        elif item_type == TreeItemType.RECENT_PROJECT:
            # Recent project context menu
            menu.addAction("Open Project",
                           lambda: self.item_double_clicked.emit("recent_project", item_data))
            menu.addSeparator()
            menu.addAction("Remove from Recent",
                           lambda: self._remove_from_recent(item_data))

        elif item_type == TreeItemType.SCENARIOS_FOLDER:
            menu.addAction("New Scenario...", self.new_scenario_requested.emit)
            menu.addSeparator()
            menu.addAction("Import Workflow...", self.import_workflow_requested.emit)

        elif item_type == TreeItemType.SCENARIO:
            scenario = item_data
            menu.addAction("Open", lambda: self.item_double_clicked.emit("scenario", scenario))
            menu.addSeparator()
            menu.addAction("Duplicate", lambda: self.duplicate_scenario_requested.emit(scenario))
            menu.addAction("Rename...", lambda: self._rename_scenario(scenario))
            menu.addAction("Export...", lambda: self.export_scenario_requested.emit(scenario))
            menu.addSeparator()
            menu.addAction("Delete", lambda: self.delete_scenario_requested.emit(scenario))

        elif item_type == TreeItemType.VARIABLES_FOLDER:
            menu.addAction("Manage Variables...",
                           lambda: self.variables_requested.emit("project"))

        elif item_type == TreeItemType.CREDENTIALS_FOLDER:
            menu.addAction("Manage Credentials...",
                           lambda: self.credentials_requested.emit("project"))

        elif item_type == TreeItemType.GLOBAL_VARIABLES:
            menu.addAction("Manage Global Variables...",
                           lambda: self.variables_requested.emit("global"))

        elif item_type == TreeItemType.GLOBAL_CREDENTIALS:
            menu.addAction("Manage Global Credentials...",
                           lambda: self.credentials_requested.emit("global"))

        if menu.actions():
            menu.exec(self.mapToGlobal(position))

    def _on_expanded(self, index: QModelIndex) -> None:
        """Track expanded items for state restoration."""
        key = self._get_item_key(index)
        self._expanded_items.add(key)

    def _on_collapsed(self, index: QModelIndex) -> None:
        """Track collapsed items."""
        key = self._get_item_key(index)
        self._expanded_items.discard(key)

    def _remove_from_recent(self, project_info: dict) -> None:
        """Remove a project from the recent list."""
        from ...project.project_manager import get_project_manager

        try:
            manager = get_project_manager()
            if hasattr(manager, 'remove_from_recent'):
                manager.remove_from_recent(project_info.get("id"))
            logger.info(f"Removed from recent: {project_info.get('name')}")
        except Exception as e:
            logger.error(f"Failed to remove from recent: {e}")

    def _rename_scenario(self, scenario: Scenario) -> None:
        """Rename a scenario (placeholder - would show dialog)."""
        # TODO: Show rename dialog
        logger.debug(f"Rename scenario: {scenario.name}")

    # =========================================================================
    # Public Methods
    # =========================================================================

    def expandDefaultItems(self) -> None:
        """Expand default items after model refresh."""
        model = self.model()
        if not model:
            return

        # Expand headers and current project by default
        for row in range(model.rowCount()):
            index = model.index(row, 0, QModelIndex())
            item_type = self._get_item_type(index)

            if item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER):
                self.expand(index)

                # Also expand current project and its scenarios folder
                if item_type == TreeItemType.PROJECTS_HEADER:
                    for child_row in range(model.rowCount(index)):
                        child_index = model.index(child_row, 0, index)
                        child_type = self._get_item_type(child_index)

                        if child_type == TreeItemType.PROJECT:
                            self.expand(child_index)

                            # Expand scenarios folder
                            for grandchild_row in range(model.rowCount(child_index)):
                                grandchild_index = model.index(grandchild_row, 0, child_index)
                                grandchild_type = self._get_item_type(grandchild_index)

                                if grandchild_type == TreeItemType.SCENARIOS_FOLDER:
                                    self.expand(grandchild_index)
                                    break
                            break  # Only expand first (current) project

    def restoreExpandedState(self) -> None:
        """Restore previously expanded items after model refresh."""
        model = self.model()
        if not model:
            return

        def restore_recursive(parent: QModelIndex):
            for row in range(model.rowCount(parent)):
                index = model.index(row, 0, parent)
                key = self._get_item_key(index)

                if key in self._expanded_items:
                    self.expand(index)

                # Recurse into children
                restore_recursive(index)

        restore_recursive(QModelIndex())

    def selectScenario(self, scenario_id: str) -> None:
        """Select a scenario by ID."""
        model = self.model()
        if not model:
            return

        # Find scenario in model
        source_model = model.sourceModel() if isinstance(model, ProjectProxyModel) else model
        if isinstance(source_model, ProjectModel):
            source_index = source_model.findScenarioIndex(scenario_id)
            if source_index.isValid():
                # Map to proxy index if using proxy
                if isinstance(model, ProjectProxyModel):
                    proxy_index = model.mapFromSource(source_index)
                else:
                    proxy_index = source_index

                if proxy_index.isValid():
                    self.setCurrentIndex(proxy_index)
                    self.scrollTo(proxy_index)

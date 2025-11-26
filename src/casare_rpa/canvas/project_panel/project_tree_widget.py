"""
CasareRPA - Project Tree Widget
Tree view for navigating projects, scenarios, and resources.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor
from loguru import logger

from ..theme import THEME
from ...core.project_schema import Project, Scenario
from ...project.project_manager import get_project_manager
from ...project.scenario_storage import ScenarioStorage


class TreeItemType:
    """Tree item type identifiers."""
    PROJECTS_HEADER = "projects_header"
    PROJECT = "project"
    SCENARIOS_FOLDER = "scenarios_folder"
    SCENARIO = "scenario"
    VARIABLES_FOLDER = "variables_folder"
    CREDENTIALS_FOLDER = "credentials_folder"
    GLOBAL_HEADER = "global_header"
    GLOBAL_VARIABLES = "global_variables"
    GLOBAL_CREDENTIALS = "global_credentials"


class ProjectTreeWidget(QTreeWidget):
    """
    Tree widget for project navigation.

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
    """

    item_double_clicked = Signal(str, object)  # item_type, item_data
    scenario_selected = Signal(object)  # Scenario
    project_selected = Signal(object)  # Project
    variables_requested = Signal(str)  # scope
    credentials_requested = Signal(str)  # scope
    new_scenario_requested = Signal()
    delete_scenario_requested = Signal(object)  # Scenario
    duplicate_scenario_requested = Signal(object)  # Scenario

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setIndentation(16)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setAnimated(True)

        # Store item data references
        self._item_data: Dict[int, tuple] = {}  # item_id -> (type, data)

        self._connect_signals()
        self._apply_styles()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.itemClicked.connect(self._on_item_clicked)
        self.customContextMenuRequested.connect(self._on_context_menu)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QTreeWidget {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
                border: none;
                outline: none;
            }}

            QTreeWidget::item {{
                padding: 4px 8px;
                border-radius: 2px;
            }}

            QTreeWidget::item:hover {{
                background: {THEME.bg_hover};
            }}

            QTreeWidget::item:selected {{
                background: {THEME.bg_selected};
                color: white;
            }}

            QTreeWidget::branch {{
                background: {THEME.bg_panel};
            }}

            QTreeWidget::branch:has-siblings:!adjoins-item {{
                border-image: none;
            }}

            QTreeWidget::branch:has-siblings:adjoins-item {{
                border-image: none;
            }}

            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {{
                border-image: none;
            }}

            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: none;
                border-image: none;
            }}

            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: none;
                border-image: none;
            }}
        """)

    def _store_item_data(self, item: QTreeWidgetItem, item_type: str, data: Any) -> None:
        """Store type and data reference for an item."""
        item_id = id(item)
        self._item_data[item_id] = (item_type, data)

    def _get_item_data(self, item: QTreeWidgetItem) -> tuple:
        """Get type and data for an item."""
        item_id = id(item)
        return self._item_data.get(item_id, (None, None))

    def refresh(
        self,
        current_project: Optional[Project] = None,
        current_scenario: Optional[Scenario] = None,
    ) -> None:
        """
        Refresh the tree with current state.

        Args:
            current_project: Currently open project (if any)
            current_scenario: Currently open scenario (if any)
        """
        self.clear()
        self._item_data.clear()

        manager = get_project_manager()

        # === PROJECTS SECTION ===
        projects_header = QTreeWidgetItem(["PROJECTS"])
        projects_header.setFlags(projects_header.flags() & ~Qt.ItemIsSelectable)
        projects_header.setForeground(0, QColor(THEME.text_header))
        self._store_item_data(projects_header, TreeItemType.PROJECTS_HEADER, None)
        self.addTopLevelItem(projects_header)

        # Add current project if open
        if current_project:
            project_item = self._create_project_item(
                current_project,
                current_scenario,
                is_current=True
            )
            projects_header.addChild(project_item)
            project_item.setExpanded(True)

        # Add recent projects (that aren't the current one)
        recent = manager.get_recent_projects(limit=5)
        for recent_info in recent:
            if current_project and recent_info["id"] == current_project.id:
                continue  # Skip current project

            recent_item = QTreeWidgetItem([recent_info["name"]])
            recent_item.setForeground(0, QColor(THEME.text_muted))
            recent_item.setToolTip(0, recent_info["path"])
            self._store_item_data(
                recent_item,
                TreeItemType.PROJECT,
                {"path": recent_info["path"], "id": recent_info["id"]}
            )
            projects_header.addChild(recent_item)

        projects_header.setExpanded(True)

        # === GLOBAL RESOURCES SECTION ===
        global_header = QTreeWidgetItem(["GLOBAL RESOURCES"])
        global_header.setFlags(global_header.flags() & ~Qt.ItemIsSelectable)
        global_header.setForeground(0, QColor(THEME.text_header))
        self._store_item_data(global_header, TreeItemType.GLOBAL_HEADER, None)
        self.addTopLevelItem(global_header)

        # Global Variables
        global_vars = manager.get_global_variables()
        global_vars_item = QTreeWidgetItem([f"Global Variables ({len(global_vars)})"])
        self._store_item_data(global_vars_item, TreeItemType.GLOBAL_VARIABLES, None)
        global_header.addChild(global_vars_item)

        # Global Credentials
        global_creds = manager.get_global_credentials()
        global_creds_item = QTreeWidgetItem([f"Global Credentials ({len(global_creds)})"])
        self._store_item_data(global_creds_item, TreeItemType.GLOBAL_CREDENTIALS, None)
        global_header.addChild(global_creds_item)

        global_header.setExpanded(True)

    def _create_project_item(
        self,
        project: Project,
        current_scenario: Optional[Scenario],
        is_current: bool = False,
    ) -> QTreeWidgetItem:
        """Create a tree item for a project."""
        # Project item
        project_item = QTreeWidgetItem([project.name])
        if is_current:
            font = project_item.font(0)
            font.setBold(True)
            project_item.setFont(0, font)
        self._store_item_data(project_item, TreeItemType.PROJECT, project)

        # Scenarios folder
        scenarios = ScenarioStorage.load_all_scenarios(project)
        scenarios_folder = QTreeWidgetItem([f"Scenarios ({len(scenarios)})"])
        self._store_item_data(scenarios_folder, TreeItemType.SCENARIOS_FOLDER, project)
        project_item.addChild(scenarios_folder)

        # Add scenario items
        for scenario in scenarios:
            scenario_item = QTreeWidgetItem([scenario.name])
            if current_scenario and scenario.id == current_scenario.id:
                font = scenario_item.font(0)
                font.setBold(True)
                scenario_item.setFont(0, font)
                scenario_item.setForeground(0, QColor(THEME.accent_primary))
            self._store_item_data(scenario_item, TreeItemType.SCENARIO, scenario)
            scenarios_folder.addChild(scenario_item)

        scenarios_folder.setExpanded(True)

        # Variables folder
        manager = get_project_manager()
        project_vars = manager.get_project_variables()
        vars_folder = QTreeWidgetItem([f"Variables ({len(project_vars)})"])
        self._store_item_data(vars_folder, TreeItemType.VARIABLES_FOLDER, project)
        project_item.addChild(vars_folder)

        # Credentials folder
        project_creds = manager.get_project_credentials()
        creds_folder = QTreeWidgetItem([f"Credentials ({len(project_creds)})"])
        self._store_item_data(creds_folder, TreeItemType.CREDENTIALS_FOLDER, project)
        project_item.addChild(creds_folder)

        return project_item

    def filter_items(self, text: str) -> None:
        """Filter tree items based on search text."""
        text = text.lower().strip()

        def filter_recursive(item: QTreeWidgetItem) -> bool:
            """Returns True if item or any child matches."""
            item_type, data = self._get_item_data(item)

            # Headers are always visible
            if item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER):
                child_visible = False
                for i in range(item.childCount()):
                    if filter_recursive(item.child(i)):
                        child_visible = True
                item.setHidden(False)
                return child_visible

            # Check if this item matches
            item_text = item.text(0).lower()
            matches = not text or text in item_text

            # Check children
            child_matches = False
            for i in range(item.childCount()):
                if filter_recursive(item.child(i)):
                    child_matches = True

            # Show if matches or has matching children
            visible = matches or child_matches
            item.setHidden(not visible)

            # Expand if has matching children
            if child_matches and text:
                item.setExpanded(True)

            return visible

        # Filter all top-level items
        for i in range(self.topLevelItemCount()):
            filter_recursive(self.topLevelItem(i))

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click."""
        item_type, data = self._get_item_data(item)

        if item_type == TreeItemType.SCENARIO:
            self.scenario_selected.emit(data)
        elif item_type == TreeItemType.PROJECT and isinstance(data, Project):
            self.project_selected.emit(data)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item double-click."""
        item_type, data = self._get_item_data(item)

        if item_type == TreeItemType.SCENARIO:
            self.item_double_clicked.emit("scenario", data)
        elif item_type == TreeItemType.PROJECT:
            if isinstance(data, dict):
                # Recent project - open it
                self.item_double_clicked.emit("recent_project", data)
            else:
                self.item_double_clicked.emit("project", data)
        elif item_type == TreeItemType.VARIABLES_FOLDER:
            self.variables_requested.emit("project")
        elif item_type == TreeItemType.CREDENTIALS_FOLDER:
            self.credentials_requested.emit("project")
        elif item_type == TreeItemType.GLOBAL_VARIABLES:
            self.variables_requested.emit("global")
        elif item_type == TreeItemType.GLOBAL_CREDENTIALS:
            self.credentials_requested.emit("global")

    def _on_context_menu(self, position) -> None:
        """Handle context menu request."""
        item = self.itemAt(position)
        if not item:
            return

        item_type, data = self._get_item_data(item)
        menu = QMenu(self)

        if item_type == TreeItemType.PROJECT:
            if isinstance(data, Project):
                # Current project context menu
                menu.addAction("Close Project", self._close_current_project)
                menu.addSeparator()
                menu.addAction("New Scenario...", self.new_scenario_requested.emit)
                menu.addSeparator()
                menu.addAction("Manage Variables...",
                               lambda: self.variables_requested.emit("project"))
                menu.addAction("Manage Credentials...",
                               lambda: self.credentials_requested.emit("project"))
            elif isinstance(data, dict):
                # Recent project context menu
                menu.addAction("Open Project",
                               lambda: self.item_double_clicked.emit("recent_project", data))

        elif item_type == TreeItemType.SCENARIOS_FOLDER:
            menu.addAction("New Scenario...", self.new_scenario_requested.emit)

        elif item_type == TreeItemType.SCENARIO:
            scenario = data
            menu.addAction("Open", lambda: self.item_double_clicked.emit("scenario", scenario))
            menu.addSeparator()
            menu.addAction("Duplicate", lambda: self.duplicate_scenario_requested.emit(scenario))
            menu.addAction("Rename...", lambda: self._rename_scenario(scenario))
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

    def _close_current_project(self) -> None:
        """Close current project (placeholder - handled by parent)."""
        # This will be handled by the dock widget
        pass

    def _rename_scenario(self, scenario: Scenario) -> None:
        """Rename a scenario (placeholder - would show dialog)."""
        # TODO: Show rename dialog
        logger.debug(f"Rename scenario: {scenario.name}")

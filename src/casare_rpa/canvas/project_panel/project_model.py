"""
CasareRPA - Project Model (QAbstractItemModel)

Implements a proper Qt Model/View architecture for the project tree.
The model wraps ProjectManager and exposes project structure as a tree.
"""

from typing import Optional, Any, List, Dict
from enum import IntEnum, auto

from PySide6.QtCore import (
    Qt,
    QAbstractItemModel,
    QModelIndex,
    QPersistentModelIndex,
    Signal,
)
from PySide6.QtGui import QFont, QColor
from loguru import logger

from ...core.project_schema import Project, Scenario
from ...project.project_manager import get_project_manager
from ...project.scenario_storage import ScenarioStorage


class TreeItemType(IntEnum):
    """Tree item type identifiers."""
    ROOT = 0
    PROJECTS_HEADER = auto()
    PROJECT = auto()
    SCENARIOS_FOLDER = auto()
    SCENARIO = auto()
    VARIABLES_FOLDER = auto()
    CREDENTIALS_FOLDER = auto()
    GLOBAL_HEADER = auto()
    GLOBAL_VARIABLES = auto()
    GLOBAL_CREDENTIALS = auto()
    RECENT_PROJECT = auto()


class TreeItem:
    """
    Wrapper class for tree items.

    Each TreeItem holds:
    - item_type: The type of item (from TreeItemType enum)
    - data: The associated data object (Project, Scenario, dict, or None)
    - display_text: Text to display
    - children: List of child TreeItems
    - parent: Parent TreeItem (None for root)
    """

    def __init__(
        self,
        item_type: TreeItemType,
        display_text: str = "",
        data: Any = None,
        parent: Optional["TreeItem"] = None,
    ):
        self.item_type = item_type
        self.display_text = display_text
        self.data = data
        self._parent = parent
        self._children: List["TreeItem"] = []

    def appendChild(self, child: "TreeItem") -> None:
        """Add a child item."""
        child._parent = self
        self._children.append(child)

    def insertChild(self, position: int, child: "TreeItem") -> bool:
        """Insert a child at a specific position."""
        if position < 0 or position > len(self._children):
            return False
        child._parent = self
        self._children.insert(position, child)
        return True

    def removeChild(self, position: int) -> bool:
        """Remove child at position."""
        if position < 0 or position >= len(self._children):
            return False
        child = self._children.pop(position)
        child._parent = None
        return True

    def child(self, row: int) -> Optional["TreeItem"]:
        """Get child at row index."""
        if 0 <= row < len(self._children):
            return self._children[row]
        return None

    def childCount(self) -> int:
        """Get number of children."""
        return len(self._children)

    def parent(self) -> Optional["TreeItem"]:
        """Get parent item."""
        return self._parent

    def row(self) -> int:
        """Get row index in parent."""
        if self._parent:
            return self._parent._children.index(self)
        return 0

    def clearChildren(self) -> None:
        """Remove all children."""
        for child in self._children:
            child._parent = None
        self._children.clear()


class ProjectModel(QAbstractItemModel):
    """
    Qt Item Model for project tree structure.

    Provides a "pull" model where the view queries data from the model,
    rather than manually building the tree.

    Structure:
    - PROJECTS (header)
      - Current Project (if open)
        - Scenarios (folder)
          - Scenario 1
          - Scenario 2
        - Variables (folder)
        - Credentials (folder)
      - Recent Project 1
      - Recent Project 2
    - GLOBAL RESOURCES (header)
      - Global Variables
      - Global Credentials
    """

    # Custom roles for additional data
    ItemTypeRole = Qt.ItemDataRole.UserRole + 1
    ItemDataRole = Qt.ItemDataRole.UserRole + 2
    IsCurrentRole = Qt.ItemDataRole.UserRole + 3

    # Signals for item interactions
    scenario_activated = Signal(object)  # Scenario
    project_activated = Signal(object)   # Project or dict (for recent)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root_item = TreeItem(TreeItemType.ROOT, "Root")
        self._current_project: Optional[Project] = None
        self._current_scenario: Optional[Scenario] = None

        # Build initial tree
        self._build_tree()

    def _build_tree(self) -> None:
        """Build the complete tree structure."""
        self._root_item.clearChildren()

        manager = get_project_manager()

        # === PROJECTS SECTION ===
        projects_header = TreeItem(
            TreeItemType.PROJECTS_HEADER,
            "PROJECTS",
            parent=self._root_item
        )
        self._root_item.appendChild(projects_header)

        # Add current project if open
        if self._current_project:
            project_item = self._create_project_item(self._current_project)
            projects_header.appendChild(project_item)

        # Add recent projects (that aren't the current one)
        recent = manager.get_recent_projects(limit=5)
        for recent_info in recent:
            if self._current_project and recent_info["id"] == self._current_project.id:
                continue  # Skip current project

            recent_item = TreeItem(
                TreeItemType.RECENT_PROJECT,
                recent_info["name"],
                data=recent_info,
            )
            projects_header.appendChild(recent_item)

        # === GLOBAL RESOURCES SECTION ===
        global_header = TreeItem(
            TreeItemType.GLOBAL_HEADER,
            "GLOBAL RESOURCES",
            parent=self._root_item
        )
        self._root_item.appendChild(global_header)

        # Global Variables
        global_vars = manager.get_global_variables()
        global_vars_item = TreeItem(
            TreeItemType.GLOBAL_VARIABLES,
            f"Global Variables ({len(global_vars)})",
        )
        global_header.appendChild(global_vars_item)

        # Global Credentials
        global_creds = manager.get_global_credentials()
        global_creds_item = TreeItem(
            TreeItemType.GLOBAL_CREDENTIALS,
            f"Global Credentials ({len(global_creds)})",
        )
        global_header.appendChild(global_creds_item)

    def _create_project_item(self, project: Project) -> TreeItem:
        """Create a TreeItem for a project with all its children."""
        project_item = TreeItem(
            TreeItemType.PROJECT,
            project.name,
            data=project,
        )

        # Scenarios folder
        scenarios = ScenarioStorage.load_all_scenarios(project)
        scenarios_folder = TreeItem(
            TreeItemType.SCENARIOS_FOLDER,
            f"Scenarios ({len(scenarios)})",
            data=project,
        )
        project_item.appendChild(scenarios_folder)

        # Add scenario items
        for scenario in scenarios:
            scenario_item = TreeItem(
                TreeItemType.SCENARIO,
                scenario.name,
                data=scenario,
            )
            scenarios_folder.appendChild(scenario_item)

        # Variables folder
        manager = get_project_manager()
        project_vars = manager.get_project_variables()
        vars_folder = TreeItem(
            TreeItemType.VARIABLES_FOLDER,
            f"Variables ({len(project_vars)})",
            data=project,
        )
        project_item.appendChild(vars_folder)

        # Credentials folder
        project_creds = manager.get_project_credentials()
        creds_folder = TreeItem(
            TreeItemType.CREDENTIALS_FOLDER,
            f"Credentials ({len(project_creds)})",
            data=project,
        )
        project_item.appendChild(creds_folder)

        return project_item

    # =========================================================================
    # QAbstractItemModel Required Methods
    # =========================================================================

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create model index for item at row/column under parent."""
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get parent index of given index."""
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item is None or parent_item == self._root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of rows under parent."""
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self._root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Get number of columns (always 1 for tree)."""
        return 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get data for index and role."""
        if not index.isValid():
            return None

        item: TreeItem = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            return item.display_text

        elif role == Qt.ItemDataRole.FontRole:
            font = QFont()
            # Bold for headers
            if item.item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER):
                font.setBold(True)
                font.setPointSize(9)
            # Bold for current project
            elif item.item_type == TreeItemType.PROJECT and item.data == self._current_project:
                font.setBold(True)
            # Bold for current scenario
            elif item.item_type == TreeItemType.SCENARIO:
                if self._current_scenario and item.data and item.data.id == self._current_scenario.id:
                    font.setBold(True)
            return font

        elif role == Qt.ItemDataRole.ForegroundRole:
            # Headers get special color
            if item.item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER):
                return QColor(150, 150, 150)  # Gray for headers
            # Recent projects are muted
            elif item.item_type == TreeItemType.RECENT_PROJECT:
                return QColor(128, 128, 128)  # Muted gray
            # Current scenario gets accent color
            elif item.item_type == TreeItemType.SCENARIO:
                if self._current_scenario and item.data and item.data.id == self._current_scenario.id:
                    return QColor(100, 180, 255)  # Accent blue
            return None

        elif role == self.ItemTypeRole:
            return item.item_type

        elif role == self.ItemDataRole:
            return item.data

        elif role == self.IsCurrentRole:
            if item.item_type == TreeItemType.PROJECT:
                return item.data == self._current_project
            elif item.item_type == TreeItemType.SCENARIO:
                return self._current_scenario and item.data and item.data.id == self._current_scenario.id
            return False

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """Get item flags."""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        item: TreeItem = index.internalPointer()

        # Headers are not selectable
        if item.item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER):
            return Qt.ItemFlag.ItemIsEnabled

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """Get header data (not used for trees but required)."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Project"
        return None

    # =========================================================================
    # Public Methods
    # =========================================================================

    def refresh(
        self,
        current_project: Optional[Project] = None,
        current_scenario: Optional[Scenario] = None,
    ) -> None:
        """
        Refresh the model with new state.

        Args:
            current_project: Currently open project
            current_scenario: Currently open scenario
        """
        self.beginResetModel()
        self._current_project = current_project
        self._current_scenario = current_scenario
        self._build_tree()
        self.endResetModel()

    def getItemType(self, index: QModelIndex) -> Optional[TreeItemType]:
        """Get the item type for an index."""
        if not index.isValid():
            return None
        item: TreeItem = index.internalPointer()
        return item.item_type

    def getItemData(self, index: QModelIndex) -> Any:
        """Get the data object for an index."""
        if not index.isValid():
            return None
        item: TreeItem = index.internalPointer()
        return item.data

    def findScenarioIndex(self, scenario_id: str) -> QModelIndex:
        """Find the index of a scenario by ID."""
        def search(parent_item: TreeItem, parent_index: QModelIndex) -> QModelIndex:
            for row in range(parent_item.childCount()):
                child = parent_item.child(row)
                child_index = self.index(row, 0, parent_index)

                if child.item_type == TreeItemType.SCENARIO:
                    if child.data and child.data.id == scenario_id:
                        return child_index

                # Recurse
                result = search(child, child_index)
                if result.isValid():
                    return result

            return QModelIndex()

        return search(self._root_item, QModelIndex())

    def findProjectIndex(self) -> QModelIndex:
        """Find the index of the current project."""
        if not self._current_project:
            return QModelIndex()

        # Projects are under the first header (row 0)
        projects_header_index = self.index(0, 0, QModelIndex())
        if projects_header_index.isValid():
            # Current project is the first child
            return self.index(0, 0, projects_header_index)

        return QModelIndex()

    def getScenariosFolder(self) -> QModelIndex:
        """Get the index of the scenarios folder."""
        project_index = self.findProjectIndex()
        if project_index.isValid():
            # Scenarios folder is the first child of project
            return self.index(0, 0, project_index)
        return QModelIndex()

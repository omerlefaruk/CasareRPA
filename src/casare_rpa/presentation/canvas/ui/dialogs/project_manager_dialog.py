"""
Project Manager Dialog UI Component.

Dialog for creating, opening, and managing CasareRPA projects.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME

if TYPE_CHECKING:
    from casare_rpa.domain.entities.project import ProjectIndexEntry


class ProjectManagerDialog(QDialog):
    """
    Dialog for managing CasareRPA projects.

    Features:
    - Create new projects
    - Open recent projects
    - Browse for existing projects
    - View project details
    - View and open scenarios within projects

    Signals:
        project_created: Emitted when new project created (Project)
        project_opened: Emitted when project opened (str: path)
        project_deleted: Emitted when project deleted (str: project_id)
        scenario_opened: Emitted when scenario opened (str: project_path, str: scenario_path)
    """

    project_created = Signal(object)  # Project
    project_opened = Signal(str)  # path
    project_deleted = Signal(str)  # project_id
    scenario_opened = Signal(str, str)  # project_path, scenario_path

    def __init__(
        self,
        recent_projects: list["ProjectIndexEntry"] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize project manager dialog.

        Args:
            recent_projects: List of recent project entries
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._recent_projects = recent_projects or []
        self._selected_project: ProjectIndexEntry | None = None
        self._selected_scenario: dict | None = None

        self.setWindowTitle("Project Manager")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setModal(True)

        self._setup_ui()
        self._load_recent_projects()
        self._apply_styles()

        logger.debug("ProjectManagerDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header = QLabel("Project Manager")
        header.setFont(QFont("", 14, QFont.Weight.Bold))
        header.setStyleSheet("padding: 5px;")
        layout.addWidget(header)

        # Tabs
        self._tabs = QTabWidget()

        # Recent Projects tab
        recent_tab = self._create_recent_tab()
        self._tabs.addTab(recent_tab, "Recent Projects")

        # New Project tab
        new_tab = self._create_new_project_tab()
        self._tabs.addTab(new_tab, "New Project")

        layout.addWidget(self._tabs)

        # Bottom buttons
        bottom_layout = QHBoxLayout()

        self._browse_btn = QPushButton("Browse...")
        self._browse_btn.setToolTip("Open a project from file system")
        self._browse_btn.clicked.connect(self._on_browse)
        bottom_layout.addWidget(self._browse_btn)

        bottom_layout.addStretch()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.reject)
        bottom_layout.addWidget(self._close_btn)

        layout.addLayout(bottom_layout)

    def _create_recent_tab(self) -> QWidget:
        """
        Create recent projects tab with tree view showing projects and scenarios.

        Returns:
            Recent projects tab widget
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Use splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Project/Scenario tree
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        tree_label = QLabel("Recent Projects:")
        tree_layout.addWidget(tree_label)

        self._project_tree = QTreeWidget()
        self._project_tree.setMinimumWidth(280)
        self._project_tree.setHeaderHidden(True)
        self._project_tree.setIndentation(16)
        self._project_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self._project_tree.itemDoubleClicked.connect(self._on_tree_double_clicked)
        tree_layout.addWidget(self._project_tree)

        splitter.addWidget(tree_container)

        # Right: Details panel
        details_container = QWidget()
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)

        details_label = QLabel("Details:")
        details_layout.addWidget(details_label)

        self._details_group = QGroupBox()
        details_group_layout = QVBoxLayout()

        self._detail_name = QLabel("Name: -")
        self._detail_path = QLabel("Path: -")
        self._detail_path.setWordWrap(True)
        self._detail_opened = QLabel("Last Opened: -")
        self._detail_type = QLabel("Type: -")
        self._detail_scenarios = QLabel("Scenarios: -")

        details_group_layout.addWidget(self._detail_type)
        details_group_layout.addWidget(self._detail_name)
        details_group_layout.addWidget(self._detail_path)
        details_group_layout.addWidget(self._detail_opened)
        details_group_layout.addWidget(self._detail_scenarios)
        details_group_layout.addStretch()

        self._details_group.setLayout(details_group_layout)
        details_layout.addWidget(self._details_group)

        # Action buttons
        btn_layout = QHBoxLayout()

        self._open_btn = QPushButton("Open")
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._on_open_selected)
        btn_layout.addWidget(self._open_btn)

        self._remove_btn = QPushButton("Remove from List")
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._on_remove_from_list)
        btn_layout.addWidget(self._remove_btn)

        details_layout.addLayout(btn_layout)

        splitter.addWidget(details_container)
        splitter.setSizes([300, 350])

        layout.addWidget(splitter)

        return widget

    def _create_new_project_tab(self) -> QWidget:
        """
        Create new project tab.

        Returns:
            New project tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Project name
        name_group = QGroupBox("Project Name")
        name_layout = QVBoxLayout()

        self._new_name_edit = QLineEdit()
        self._new_name_edit.setPlaceholderText("Enter project name")
        self._new_name_edit.textChanged.connect(self._validate_new_project)
        name_layout.addWidget(self._new_name_edit)

        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # Project location
        location_group = QGroupBox("Location")
        location_layout = QHBoxLayout()

        self._new_path_edit = QLineEdit()
        self._new_path_edit.setPlaceholderText("Select project folder")
        self._new_path_edit.textChanged.connect(self._validate_new_project)
        location_layout.addWidget(self._new_path_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse_new_location)
        location_layout.addWidget(browse_btn)

        location_group.setLayout(location_layout)
        layout.addWidget(location_group)

        # Description
        desc_group = QGroupBox("Description (optional)")
        desc_layout = QVBoxLayout()

        self._new_description_edit = QTextEdit()
        self._new_description_edit.setPlaceholderText("Project description")
        self._new_description_edit.setMaximumHeight(80)
        desc_layout.addWidget(self._new_description_edit)

        desc_group.setLayout(desc_layout)
        layout.addWidget(desc_group)

        # Author
        author_group = QGroupBox("Author (optional)")
        author_layout = QVBoxLayout()

        self._new_author_edit = QLineEdit()
        self._new_author_edit.setPlaceholderText("Your name")
        author_layout.addWidget(self._new_author_edit)

        author_group.setLayout(author_layout)
        layout.addWidget(author_group)

        layout.addStretch()

        # Create button
        create_layout = QHBoxLayout()
        create_layout.addStretch()

        self._create_btn = QPushButton("Create Project")
        self._create_btn.setEnabled(False)
        self._create_btn.clicked.connect(self._on_create_project)
        create_layout.addWidget(self._create_btn)

        layout.addLayout(create_layout)

        return widget

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background: #252525;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #5a8a9a;
            }
            QListWidget {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #4a4a4a;
            }
            QListWidget::item:selected {
                background: #4a6a8a;
            }
            QListWidget::item:hover {
                background: #3d4d5d;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border: 1px solid #5a5a5a;
            }
            QPushButton:pressed {
                background: #5a5a5a;
            }
            QPushButton:disabled {
                background: #2d2d2d;
                color: #666666;
            }
            QTabWidget::pane {
                border: 1px solid #4a4a4a;
                background: #2d2d2d;
            }
            QTabBar::tab {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #4a6a8a;
            }
            QTabBar::tab:hover:!selected {
                background: #4a4a4a;
            }
            QSplitter::handle {
                background: #4a4a4a;
                width: 2px;
            }
            QTreeWidget {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
            }
            QTreeWidget::item {
                padding: 6px 4px;
            }
            QTreeWidget::item:selected {
                background: #4a6a8a;
            }
            QTreeWidget::item:hover {
                background: #3d4d5d;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                border-image: none;
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                border-image: none;
            }
        """)

    def _load_recent_projects(self) -> None:
        """Load recent projects and their scenarios into the tree."""
        self._project_tree.clear()

        for entry in self._recent_projects:
            # Create project item
            project_item = QTreeWidgetItem()
            project_item.setText(0, f"📁 {entry.name}")
            project_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "project", "entry": entry})
            project_item.setToolTip(0, entry.path)

            # Load scenarios for this project
            scenarios = self._get_scenarios_for_project(entry.path)
            for scenario_info in scenarios:
                scenario_item = QTreeWidgetItem(project_item)
                scenario_item.setText(0, f"  📄 {scenario_info['name']}")
                scenario_item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {
                        "type": "scenario",
                        "project_path": entry.path,
                        "scenario_path": scenario_info["path"],
                        "scenario_name": scenario_info["name"],
                    },
                )
                scenario_item.setToolTip(0, scenario_info["path"])

            self._project_tree.addTopLevelItem(project_item)
            project_item.setExpanded(True)

        if not self._recent_projects:
            empty_item = QTreeWidgetItem()
            empty_item.setText(0, "No recent projects")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._project_tree.addTopLevelItem(empty_item)

    def _get_scenarios_for_project(self, project_path: str) -> list[dict]:
        """
        Get list of scenarios for a project.

        Args:
            project_path: Path to project folder

        Returns:
            List of scenario info dicts with name and path
        """
        scenarios = []
        project_dir = Path(project_path)
        scenarios_dir = project_dir / "scenarios"

        if not scenarios_dir.exists():
            return scenarios

        try:
            import orjson

            for scenario_file in scenarios_dir.glob("*.json"):
                try:
                    data = orjson.loads(scenario_file.read_bytes())
                    name = data.get("metadata", {}).get("name") or scenario_file.stem
                    scenarios.append(
                        {
                            "name": name,
                            "path": str(scenario_file),
                        }
                    )
                except Exception as e:
                    logger.debug(f"Failed to read scenario {scenario_file}: {e}")
                    scenarios.append(
                        {
                            "name": scenario_file.stem,
                            "path": str(scenario_file),
                        }
                    )
        except Exception as e:
            logger.debug(f"Failed to list scenarios in {scenarios_dir}: {e}")

        return sorted(scenarios, key=lambda x: x["name"])

    def _on_tree_selection_changed(self) -> None:
        """Handle tree selection change."""
        items = self._project_tree.selectedItems()
        if not items:
            self._selected_project = None
            self._selected_scenario = None
            self._update_details_for_selection(None)
            return

        item_data = items[0].data(0, Qt.ItemDataRole.UserRole)
        if item_data is None:
            self._selected_project = None
            self._selected_scenario = None
            self._update_details_for_selection(None)
            return

        if item_data.get("type") == "project":
            self._selected_project = item_data.get("entry")
            self._selected_scenario = None
            self._update_details_for_project(self._selected_project)
        elif item_data.get("type") == "scenario":
            # Find parent project
            parent = items[0].parent()
            if parent:
                parent_data = parent.data(0, Qt.ItemDataRole.UserRole)
                self._selected_project = parent_data.get("entry") if parent_data else None
            self._selected_scenario = item_data
            self._update_details_for_scenario(item_data)

    def _update_details_for_selection(self, data: dict | None) -> None:
        """Clear details panel."""
        self._detail_type.setText("Type: -")
        self._detail_name.setText("Name: -")
        self._detail_path.setText("Path: -")
        self._detail_opened.setText("Last Opened: -")
        self._detail_scenarios.setText("Scenarios: -")
        self._open_btn.setEnabled(False)
        self._remove_btn.setEnabled(False)

    def _update_details_for_project(self, entry: Optional["ProjectIndexEntry"]) -> None:
        """Update details panel for a project."""
        if entry is None:
            self._update_details_for_selection(None)
            return

        self._detail_type.setText("Type: Project")
        self._detail_name.setText(f"Name: {entry.name}")
        self._detail_path.setText(f"Path: {entry.path}")

        if entry.last_opened:
            last_opened = entry.last_opened.strftime("%Y-%m-%d %H:%M")
            self._detail_opened.setText(f"Last Opened: {last_opened}")
        else:
            self._detail_opened.setText("Last Opened: Never")

        # Count scenarios
        scenarios = self._get_scenarios_for_project(entry.path)
        self._detail_scenarios.setText(f"Scenarios: {len(scenarios)}")

        # Check if path exists
        path_exists = Path(entry.path).exists()
        self._open_btn.setEnabled(path_exists)
        self._open_btn.setText("Open Project")
        self._remove_btn.setEnabled(True)

        if not path_exists:
            self._detail_path.setStyleSheet(f"color: {THEME.status_error};")
            self._detail_path.setText(f"Path: {entry.path} (NOT FOUND)")
        else:
            self._detail_path.setStyleSheet("")

    def _update_details_for_scenario(self, data: dict) -> None:
        """Update details panel for a scenario."""
        self._detail_type.setText("Type: Scenario")
        self._detail_name.setText(f"Name: {data.get('scenario_name', '-')}")
        self._detail_path.setText(f"Path: {data.get('scenario_path', '-')}")
        self._detail_opened.setText("Last Opened: -")
        self._detail_scenarios.setText("Scenarios: -")

        # Check if path exists
        scenario_path = data.get("scenario_path", "")
        path_exists = Path(scenario_path).exists() if scenario_path else False
        self._open_btn.setEnabled(path_exists)
        self._open_btn.setText("Open Scenario")
        self._remove_btn.setEnabled(False)  # Can't remove scenarios from here

        if scenario_path and not path_exists:
            self._detail_path.setStyleSheet(f"color: {THEME.status_error};")
            self._detail_path.setText(f"Path: {scenario_path} (NOT FOUND)")
        else:
            self._detail_path.setStyleSheet("")

    def _on_tree_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on tree item."""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return

        if item_data.get("type") == "project":
            entry = item_data.get("entry")
            if entry and Path(entry.path).exists():
                self.project_opened.emit(entry.path)
                self.accept()
        elif item_data.get("type") == "scenario":
            project_path = item_data.get("project_path", "")
            scenario_path = item_data.get("scenario_path", "")
            if project_path and scenario_path and Path(scenario_path).exists():
                self.scenario_opened.emit(project_path, scenario_path)
                self.accept()

    def _on_open_selected(self) -> None:
        """Open the selected project or scenario."""
        if self._selected_scenario:
            project_path = self._selected_scenario.get("project_path", "")
            scenario_path = self._selected_scenario.get("scenario_path", "")
            if project_path and scenario_path and Path(scenario_path).exists():
                self.scenario_opened.emit(project_path, scenario_path)
                self.accept()
        elif self._selected_project and Path(self._selected_project.path).exists():
            self.project_opened.emit(self._selected_project.path)
            self.accept()

    def _on_remove_from_list(self) -> None:
        """Remove selected project from recent list."""
        if self._selected_project and not self._selected_scenario:
            reply = QMessageBox.question(
                self,
                "Remove Project",
                f"Remove '{self._selected_project.name}' from recent projects?\n\n"
                "This will not delete the project files.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.project_deleted.emit(self._selected_project.id)
                # Remove from tree
                root = self._project_tree.invisibleRootItem()
                for i in range(root.childCount()):
                    item = root.child(i)
                    item_data = item.data(0, Qt.ItemDataRole.UserRole)
                    if item_data and item_data.get("type") == "project":
                        entry = item_data.get("entry")
                        if entry and entry.id == self._selected_project.id:
                            root.removeChild(item)
                            break
                self._selected_project = None
                self._selected_scenario = None
                self._update_details_for_selection(None)

    def _on_browse(self) -> None:
        """Browse for existing project."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Project Folder",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            # Check if it's a valid project folder
            project_file = Path(folder) / "project.json"
            if project_file.exists():
                self.project_opened.emit(folder)
                self.accept()
            else:
                QMessageBox.warning(
                    self,
                    "Invalid Project",
                    f"The selected folder is not a valid CasareRPA project.\n\n"
                    f"Expected 'project.json' file not found in:\n{folder}",
                )

    def _on_browse_new_location(self) -> None:
        """Browse for new project location."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Project Location",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            # Append project name if set
            name = self._new_name_edit.text().strip()
            if name:
                folder = str(Path(folder) / name)
            self._new_path_edit.setText(folder)

    def _validate_new_project(self) -> None:
        """Validate new project form."""
        name = self._new_name_edit.text().strip()
        path = self._new_path_edit.text().strip()

        valid = bool(name and path)
        self._create_btn.setEnabled(valid)

    def _on_create_project(self) -> None:
        """Create a new project."""
        name = self._new_name_edit.text().strip()
        path = Path(self._new_path_edit.text().strip())
        description = self._new_description_edit.toPlainText().strip()
        author = self._new_author_edit.text().strip()

        if not name:
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            return

        if not path:
            QMessageBox.warning(self, "Validation Error", "Project location is required.")
            return

        # Check if path exists and is not empty
        if path.exists() and any(path.iterdir()):
            reply = QMessageBox.question(
                self,
                "Directory Not Empty",
                f"The selected directory is not empty:\n{path}\n\n"
                "Do you want to create the project anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # Emit signal with project data
        project_data = {
            "name": name,
            "path": path,
            "description": description,
            "author": author,
        }
        self.project_created.emit(project_data)
        self.accept()

    def update_recent_projects(self, projects: list["ProjectIndexEntry"]) -> None:
        """
        Update the recent projects list.

        Args:
            projects: New list of project entries
        """
        self._recent_projects = projects
        self._load_recent_projects()

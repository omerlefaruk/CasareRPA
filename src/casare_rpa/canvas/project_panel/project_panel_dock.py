"""
CasareRPA - Project Panel Dock Widget
Left dock panel for managing projects and scenarios.

Uses Qt Model/View architecture for better performance and maintainability.
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QMenu,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, Signal
from loguru import logger

from ..theme import THEME
from .project_model import ProjectModel, TreeItemType
from .project_proxy_model import ProjectProxyModel
from .project_tree_view import ProjectTreeView
from ...core.project_schema import Project, Scenario
from ...project.project_manager import get_project_manager


class ProjectPanelDock(QDockWidget):
    """
    Left dock panel for project and scenario management.

    Uses Model/View architecture:
    - ProjectModel: Data model wrapping ProjectManager
    - ProjectProxyModel: Filtering support
    - ProjectTreeView: Visual presentation

    Signals:
        project_opened: Emitted when a project is opened (Project)
        project_closed: Emitted when a project is closed
        scenario_opened: Emitted when a scenario is opened (Project, Scenario)
        scenario_closed: Emitted when a scenario is closed
        variable_edit_requested: Emitted when user wants to edit variables (scope: str)
        credential_edit_requested: Emitted when user wants to edit credentials (scope: str)
    """

    project_opened = Signal(object)  # Project
    project_closed = Signal()
    scenario_opened = Signal(object, object)  # Project, Scenario
    scenario_closed = Signal()
    variable_edit_requested = Signal(str)  # scope: "global" or "project"
    credential_edit_requested = Signal(str)  # scope: "global" or "project"

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__("Project", parent)

        self.setObjectName("ProjectPanelDock")
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )

        # Create model/view components
        self._model = ProjectModel(self)
        self._proxy_model = ProjectProxyModel(self)
        self._proxy_model.setSourceModel(self._model)

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        # Initial refresh
        self._refresh_tree()

    def _setup_ui(self) -> None:
        """Setup the dock widget UI."""
        # Main container widget
        container = QWidget()
        self.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search bar section
        search_section = self._create_search_section()
        layout.addWidget(search_section)

        # Tree view (using Model/View)
        self._tree = ProjectTreeView()
        self._tree.setModel(self._proxy_model)
        layout.addWidget(self._tree, 1)  # Stretch factor 1

        # Button section
        button_section = self._create_button_section()
        layout.addWidget(button_section)

    def _create_search_section(self) -> QWidget:
        """Create the search/filter section."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Search input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search projects/scenarios...")
        self._search_input.setClearButtonEnabled(True)
        layout.addWidget(self._search_input, 1)

        # Add button (dropdown menu)
        self._add_button = QPushButton("+")
        self._add_button.setFixedSize(28, 28)
        self._add_button.setToolTip("Add new project or scenario")
        layout.addWidget(self._add_button)

        # Setup add menu
        add_menu = QMenu(self._add_button)
        add_menu.addAction("New Project...", self._on_new_project)
        add_menu.addAction("New Scenario...", self._on_new_scenario)
        add_menu.addSeparator()
        add_menu.addAction("Import Project...", self._on_import_project)
        self._add_button.setMenu(add_menu)

        return widget

    def _create_button_section(self) -> QWidget:
        """Create the bottom button section."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # New Project button
        self._new_project_btn = QPushButton("New Project")
        self._new_project_btn.clicked.connect(self._on_new_project)
        layout.addWidget(self._new_project_btn)

        # Open Project button
        self._open_project_btn = QPushButton("Open Project")
        self._open_project_btn.clicked.connect(self._on_open_project)
        layout.addWidget(self._open_project_btn)

        return widget

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Search filtering
        self._search_input.textChanged.connect(self._on_search_changed)

        # Tree view interactions
        self._tree.item_double_clicked.connect(self._on_tree_item_double_clicked)
        self._tree.scenario_selected.connect(self._on_scenario_selected)
        self._tree.project_selected.connect(self._on_project_selected)
        self._tree.variables_requested.connect(self._on_variables_requested)
        self._tree.credentials_requested.connect(self._on_credentials_requested)
        self._tree.new_scenario_requested.connect(self._on_new_scenario)
        self._tree.delete_scenario_requested.connect(self._on_delete_scenario)
        self._tree.duplicate_scenario_requested.connect(self._on_duplicate_scenario)
        self._tree.delete_project_requested.connect(self._on_delete_project)
        self._tree.close_project_requested.connect(self.close_project)
        self._tree.import_workflow_requested.connect(self._on_import_workflow)
        self._tree.export_scenario_requested.connect(self._on_export_scenario)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QDockWidget {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
                font-size: 12px;
            }}

            QDockWidget::title {{
                background: {THEME.dock_title_bg};
                color: {THEME.dock_title_text};
                padding: 6px 8px;
                font-weight: bold;
            }}

            QLineEdit {{
                background: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 4px 8px;
            }}

            QLineEdit:focus {{
                border-color: {THEME.border_focus};
            }}

            QPushButton {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 12px;
            }}

            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}

            QPushButton:pressed {{
                background: {THEME.accent_primary};
            }}

            QPushButton::menu-indicator {{
                image: none;
            }}

            QMenu {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
            }}

            QMenu::item {{
                padding: 6px 24px;
            }}

            QMenu::item:selected {{
                background: {THEME.bg_hover};
            }}

            QMenu::separator {{
                height: 1px;
                background: {THEME.border};
                margin: 4px 8px;
            }}
        """)

    def _refresh_tree(self) -> None:
        """Refresh the project tree model."""
        manager = get_project_manager()
        self._model.refresh(
            current_project=manager.current_project,
            current_scenario=manager.current_scenario,
        )
        # Expand default items after refresh
        self._tree.expandDefaultItems()

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._proxy_model.setFilterText(text)

        # If filtering, expand all visible items to show matches
        if text.strip():
            self._tree.expandAll()

    def _on_tree_item_double_clicked(self, item_type: str, item_data: object) -> None:
        """Handle double-click on tree item."""
        if item_type == "scenario":
            self._open_scenario(item_data)
        elif item_type == "recent_project":
            # Open recent project by path
            if isinstance(item_data, dict):
                path = item_data.get("path")
                if path:
                    self._open_project(Path(path))
        elif item_type == "project":
            # Already open project - just expand/collapse in tree
            pass

    def _on_scenario_selected(self, scenario: Scenario) -> None:
        """Handle scenario selection in tree."""
        pass  # Single-click selection, double-click opens

    def _on_project_selected(self, project: Project) -> None:
        """Handle project selection in tree."""
        pass  # Single-click selection

    def _on_variables_requested(self, scope: str) -> None:
        """Handle request to edit variables."""
        self.variable_edit_requested.emit(scope)

    def _on_credentials_requested(self, scope: str) -> None:
        """Handle request to edit credentials."""
        self.credential_edit_requested.emit(scope)

    def _on_new_project(self) -> None:
        """Handle new project request."""
        from ..dialogs.new_project_dialog import NewProjectDialog

        dialog = NewProjectDialog(self)
        if dialog.exec():
            name = dialog.get_name()
            path = dialog.get_path()
            description = dialog.get_description()

            try:
                manager = get_project_manager()
                project = manager.create_project(
                    name=name,
                    path=Path(path),
                    description=description,
                )

                self._refresh_tree()
                self.project_opened.emit(project)
                logger.info(f"Created and opened project: {name}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create project: {e}"
                )
                logger.error(f"Failed to create project: {e}")

    def _on_open_project(self) -> None:
        """Handle open project request."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Open Project",
            "",
            QFileDialog.Option.ShowDirsOnly
        )

        if path:
            self._open_project(Path(path))

    def _on_import_project(self) -> None:
        """Handle import project request."""
        # For now, same as open project
        self._on_open_project()

    def _on_new_scenario(self) -> None:
        """Handle new scenario request."""
        manager = get_project_manager()
        if manager.current_project is None:
            QMessageBox.warning(
                self,
                "No Project Open",
                "Please open a project before creating a scenario."
            )
            return

        from ..dialogs.new_scenario_dialog import NewScenarioDialog

        dialog = NewScenarioDialog(self)
        if dialog.exec():
            name = dialog.get_name()
            description = dialog.get_description()

            try:
                scenario = manager.create_scenario(
                    name=name,
                    description=description,
                )

                self._refresh_tree()
                self.scenario_opened.emit(manager.current_project, scenario)
                logger.info(f"Created and opened scenario: {name}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to create scenario: {e}"
                )
                logger.error(f"Failed to create scenario: {e}")

    def _on_delete_scenario(self, scenario: Scenario) -> None:
        """Handle delete scenario request."""
        reply = QMessageBox.question(
            self,
            "Delete Scenario",
            f"Are you sure you want to delete '{scenario.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                manager = get_project_manager()
                was_current = manager.current_scenario == scenario
                manager.delete_scenario(scenario)
                self._refresh_tree()

                if was_current:
                    self.scenario_closed.emit()

                logger.info(f"Deleted scenario: {scenario.name}")

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete scenario: {e}"
                )

    def _on_duplicate_scenario(self, scenario: Scenario) -> None:
        """Handle duplicate scenario request."""
        manager = get_project_manager()

        # Generate unique name
        base_name = f"{scenario.name} - Copy"
        new_name = base_name
        counter = 1
        existing_names = {s.name for s in manager.get_scenarios()}

        while new_name in existing_names:
            counter += 1
            new_name = f"{base_name} ({counter})"

        try:
            # Temporarily set current scenario for duplication
            old_scenario = manager.current_scenario
            manager._current_scenario = scenario

            new_scenario = manager.duplicate_scenario(new_name)

            manager._current_scenario = old_scenario
            self._refresh_tree()

            logger.info(f"Duplicated scenario: {scenario.name} -> {new_name}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to duplicate scenario: {e}"
            )

    def _on_delete_project(self, project: Project) -> None:
        """Handle delete project request."""
        import shutil

        reply = QMessageBox.warning(
            self,
            "Delete Project",
            f"Are you sure you want to delete the project '{project.name}'?\n\n"
            f"This will permanently delete:\n"
            f"  - All scenarios in this project\n"
            f"  - All project variables\n"
            f"  - All project credentials\n\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Double-confirm for safety
            confirm = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you ABSOLUTELY sure you want to delete '{project.name}'?\n\n"
                f"All project data will be permanently removed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if confirm == QMessageBox.StandardButton.Yes:
                try:
                    manager = get_project_manager()

                    # Close project first if it's the current one
                    is_current = manager.current_project and manager.current_project.id == project.id
                    if is_current:
                        manager.close_project()
                        self.project_closed.emit()

                    # Delete project files
                    project_path = Path(project.path)
                    if project_path.exists():
                        shutil.rmtree(project_path)
                        logger.info(f"Deleted project folder: {project_path}")

                    # Remove from recent projects
                    if hasattr(manager, 'remove_from_recent'):
                        manager.remove_from_recent(project.id)

                    self._refresh_tree()

                    logger.info(f"Deleted project: {project.name}")
                    QMessageBox.information(
                        self,
                        "Project Deleted",
                        f"Project '{project.name}' has been deleted."
                    )

                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to delete project: {e}"
                    )
                    logger.error(f"Failed to delete project: {e}")

    def _on_import_workflow(self) -> None:
        """Handle import workflow request."""
        from ...project.scenario_storage import ScenarioStorage

        manager = get_project_manager()
        if manager.current_project is None:
            QMessageBox.warning(
                self,
                "No Project Open",
                "Please open a project before importing a workflow."
            )
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Workflow",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            scenario = ScenarioStorage.import_workflow_file(
                Path(file_path),
                manager.current_project
            )

            self._refresh_tree()
            self.scenario_opened.emit(manager.current_project, scenario)
            logger.info(f"Imported workflow as scenario: {scenario.name}")

            QMessageBox.information(
                self,
                "Import Successful",
                f"Workflow imported as scenario '{scenario.name}'."
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Failed to import workflow: {e}"
            )
            logger.error(f"Failed to import workflow: {e}")

    def _on_export_scenario(self, scenario: Scenario) -> None:
        """Handle export scenario request."""
        from ...project.scenario_storage import ScenarioStorage

        # Ask user for export format
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Export Format")
        msg_box.setText("How would you like to export this scenario?")
        msg_box.setInformativeText(
            "Scenario format includes metadata and variable values.\n"
            "Workflow format exports just the workflow for use in other projects."
        )

        scenario_btn = msg_box.addButton("Scenario Format", QMessageBox.ButtonRole.AcceptRole)
        workflow_btn = msg_box.addButton("Workflow Format", QMessageBox.ButtonRole.AcceptRole)
        msg_box.addButton(QMessageBox.StandardButton.Cancel)

        msg_box.exec()

        clicked = msg_box.clickedButton()
        if clicked == scenario_btn:
            export_format = "scenario"
            default_name = f"{scenario.name}.scenario.json"
        elif clicked == workflow_btn:
            export_format = "workflow"
            default_name = f"{scenario.name}.workflow.json"
        else:
            return  # Cancelled

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Scenario",
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            ScenarioStorage.export_scenario(
                scenario,
                Path(file_path),
                export_format
            )

            logger.info(f"Exported scenario '{scenario.name}' to {file_path}")

            QMessageBox.information(
                self,
                "Export Successful",
                f"Scenario exported to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export scenario: {e}"
            )
            logger.error(f"Failed to export scenario: {e}")

    # =========================================================================
    # Public Methods
    # =========================================================================

    def _open_project(self, path: Path) -> None:
        """Open a project from path."""
        try:
            manager = get_project_manager()
            project = manager.open_project(path)

            self._refresh_tree()
            self.project_opened.emit(project)
            logger.info(f"Opened project: {project.name}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to open project: {e}"
            )
            logger.error(f"Failed to open project: {e}")

    def _open_scenario(self, scenario: Scenario) -> None:
        """Open a scenario."""
        manager = get_project_manager()
        if manager.current_project is None:
            return

        manager.open_scenario(scenario)
        self._refresh_tree()
        self.scenario_opened.emit(manager.current_project, scenario)

    def close_project(self) -> None:
        """Close the current project."""
        manager = get_project_manager()
        manager.close_project()
        self._refresh_tree()
        self.project_closed.emit()

    def refresh(self) -> None:
        """Refresh the panel content."""
        self._refresh_tree()

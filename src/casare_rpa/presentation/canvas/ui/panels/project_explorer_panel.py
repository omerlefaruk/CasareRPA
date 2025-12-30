"""
Project Explorer Panel for CasareRPA Canvas.

VS Code-style dockable panel showing project folder hierarchy.
Supports folder creation, renaming, deletion, color customization,
and drag-drop project organization.

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

from functools import partial
from typing import Any

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QDockWidget,
    QHBoxLayout,
    QInputDialog,
    QMenu,
    QMessageBox,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.domain.entities.project.folder import (
    ProjectFolder,
)
from casare_rpa.infrastructure.persistence.folder_storage import FolderStorage
from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import apply_tree_style
from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import EmptyState


class ProjectExplorerPanel(QDockWidget):
    """
    Dockable panel for project folder hierarchy.

    Features:
    - VS Code-style tree view
    - Folder hierarchy with colors
    - Right-click context menu
    - Drag-drop project organization
    - Double-click to open project

    Signals:
        folder_created: Emitted when folder is created (folder_id: str)
        folder_renamed: Emitted when folder is renamed (folder_id: str, new_name: str)
        folder_deleted: Emitted when folder is deleted (folder_id: str)
        folder_color_changed: Emitted when folder color changes (folder_id: str, color: str)
        project_moved: Emitted when project is moved (project_id: str, folder_id: str)
        project_opened: Emitted when project is double-clicked (project_id: str)
        project_selected: Emitted when project is selected (project_id: str)
    """

    folder_created = Signal(str)  # folder_id
    folder_renamed = Signal(str, str)  # folder_id, new_name
    folder_deleted = Signal(str)  # folder_id
    folder_color_changed = Signal(str, str)  # folder_id, color
    project_moved = Signal(str, str)  # project_id, target_folder_id
    project_opened = Signal(str)  # project_id
    project_selected = Signal(str)  # project_id

    # Item types for tree items
    ITEM_TYPE_FOLDER = 1
    ITEM_TYPE_PROJECT = 2

    # Custom roles
    ROLE_ITEM_ID = Qt.ItemDataRole.UserRole
    ROLE_ITEM_TYPE = Qt.ItemDataRole.UserRole + 1
    ROLE_FOLDER_COLOR = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QWidget | None = None, embedded: bool = False) -> None:
        """
        Initialize the project explorer panel.

        Args:
            parent: Optional parent widget
            embedded: If True, behave as QWidget (for embedding in tab panels)
        """
        self._embedded = embedded
        if embedded:
            QWidget.__init__(self, parent)
        else:
            super().__init__("Project Explorer", parent)
            self.setObjectName("ProjectExplorerDock")

        self._projects: dict[str, dict[str, Any]] = {}  # project_id -> project_data
        self._folder_items: dict[str, QTreeWidgetItem] = {}  # folder_id -> tree_item
        self._project_items: dict[str, QTreeWidgetItem] = {}  # project_id -> tree_item
        self._context_item_id: str | None = None  # Context menu target item ID
        self._context_item_type: int | None = None  # Context menu target item type
        self._move_project_id: str | None = None  # Project being moved

        if not embedded:
            self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("ProjectExplorerPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        # Dock-only: NO DockWidgetFloatable (Epic 6.1 requirement)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.setMinimumWidth(TOKENS_V2.sizes.panel_min_width)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        if self._embedded:
            main_layout = QVBoxLayout(self)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar (v2 style)
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("explorerToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        toolbar.setSpacing(TOKENS_V2.spacing.xs)

        # New folder button (v2 PushButton)
        new_folder_btn = PushButton(
            text="New Folder",
            variant="secondary",
            size="sm",
        )
        new_folder_btn.setToolTip("Create a new folder")
        new_folder_btn.clicked.connect(self._on_new_folder)

        # Refresh button (v2 ToolButton with icon)
        refresh_btn = PushButton(
            text="Refresh",
            variant="ghost",
            size="sm",
        )
        refresh_btn.setToolTip("Refresh folder tree")
        refresh_btn.clicked.connect(self.refresh)

        # Collapse all button
        collapse_btn = PushButton(
            text="Collapse",
            variant="ghost",
            size="sm",
        )
        collapse_btn.setToolTip("Collapse all folders")
        collapse_btn.clicked.connect(self._collapse_all)

        # Expand all button
        expand_btn = PushButton(
            text="Expand",
            variant="ghost",
            size="sm",
        )
        expand_btn.setToolTip("Expand all folders")
        expand_btn.clicked.connect(self._expand_all)

        toolbar.addWidget(new_folder_btn)
        toolbar.addStretch()
        toolbar.addWidget(collapse_btn)
        toolbar.addWidget(expand_btn)
        toolbar.addWidget(refresh_btn)

        main_layout.addWidget(toolbar_widget)

        # Content stack (empty state vs tree)
        self._content_stack = QStackedWidget()

        # Empty state (index 0) - v2 EmptyState component
        self._empty_state = EmptyState(
            icon="folder",
            text="No Folders",
            action_text="Create First Folder",
        )
        self._empty_state.action_clicked.connect(self._on_new_folder)
        self._content_stack.addWidget(self._empty_state)

        # Tree widget (index 1)
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
        )
        tree_layout.setSpacing(0)

        self._tree = QTreeWidget()
        # Apply v2 tree styling
        apply_tree_style(self._tree)
        self._tree.setAnimated(False)  # Zero motion (Epic 6.1)
        self._tree.setIndentation(TOKENS_V2.spacing.lg)
        self._tree.setAlternatingRowColors(False)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Enable drag and drop
        self._tree.setDragEnabled(True)
        self._tree.setAcceptDrops(True)
        self._tree.setDropIndicatorShown(True)
        self._tree.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # Connect signals
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemSelectionChanged.connect(self._on_selection_changed)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemCollapsed.connect(self._on_item_collapsed)

        tree_layout.addWidget(self._tree)
        self._content_stack.addWidget(tree_container)

        main_layout.addWidget(self._content_stack)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

        if not self._embedded:
            self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply v2 theme styling (Epic 6.1)."""
        t = THEME_V2
        tok = TOKENS_V2
        self.setStyleSheet(f"""
            QDockWidget {{
                background-color: {t.bg_surface};
                color: {t.text_primary};
            }}
            QDockWidget::title {{
                background-color: {t.bg_header};
                color: {t.text_header};
                padding: {tok.spacing.xs}px {tok.spacing.md}px;
                font-weight: {tok.typography.weight_semibold};
                font-size: {tok.typography.caption}px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {t.border};
            }}
            #explorerToolbar {{
                background-color: {t.bg_header};
                border-bottom: 1px solid {t.border};
            }}
        """)

    def _update_display(self) -> None:
        """Update empty state vs tree display."""
        has_folders = self._tree.topLevelItemCount() > 0
        self._content_stack.setCurrentIndex(1 if has_folders else 0)

    def _create_folder_item(self, folder: ProjectFolder) -> QTreeWidgetItem:
        """
        Create a tree item for a folder.

        Args:
            folder: ProjectFolder entity

        Returns:
            Configured QTreeWidgetItem
        """
        item = QTreeWidgetItem()
        item.setText(0, folder.name)
        item.setData(0, self.ROLE_ITEM_ID, folder.id)
        item.setData(0, self.ROLE_ITEM_TYPE, self.ITEM_TYPE_FOLDER)
        item.setData(0, self.ROLE_FOLDER_COLOR, folder.color)

        # Set folder icon with color badge
        item.setIcon(0, self._create_folder_icon(folder.color))

        # Expand state from folder
        item.setExpanded(folder.is_expanded)

        # Enable drop on folders
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsDragEnabled)

        # Store mapping
        self._folder_items[folder.id] = item

        return item

    def _create_project_item(self, project_id: str, project_name: str) -> QTreeWidgetItem:
        """
        Create a tree item for a project.

        Args:
            project_id: Project identifier
            project_name: Display name

        Returns:
            Configured QTreeWidgetItem
        """
        item = QTreeWidgetItem()
        item.setText(0, project_name)
        item.setData(0, self.ROLE_ITEM_ID, project_id)
        item.setData(0, self.ROLE_ITEM_TYPE, self.ITEM_TYPE_PROJECT)

        # Set project text color (v2)
        item.setForeground(0, QBrush(QColor(THEME_V2.text_secondary)))

        # Enable drag for projects
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled & ~Qt.ItemFlag.ItemIsDropEnabled)

        # Store mapping
        self._project_items[project_id] = item

        return item

    def _create_folder_icon(self, color: str) -> QIcon:
        """
        Create a folder icon with color badge.

        Args:
            color: Hex color string

        Returns:
            QIcon with colored folder appearance
        """
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw folder shape
        folder_color = QColor(color)
        painter.setBrush(QBrush(folder_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Simple folder shape
        painter.drawRoundedRect(0, 3, 16, 11, 2, 2)
        painter.drawRoundedRect(0, 1, 8, 4, 1, 1)

        painter.end()

        return QIcon(pixmap)

    @Slot()
    def _on_new_folder(self) -> None:
        """Handle new folder creation."""
        name, ok = QInputDialog.getText(
            self,
            "New Folder",
            "Folder name:",
            text="New Folder",
        )

        if ok and name.strip():
            try:
                # Get selected folder as parent
                parent_id = None
                selected = self._tree.currentItem()
                if selected:
                    item_type = selected.data(0, self.ROLE_ITEM_TYPE)
                    if item_type == self.ITEM_TYPE_FOLDER:
                        parent_id = selected.data(0, self.ROLE_ITEM_ID)
                    elif item_type == self.ITEM_TYPE_PROJECT:
                        # Get parent folder of selected project
                        parent_item = selected.parent()
                        if parent_item:
                            parent_id = parent_item.data(0, self.ROLE_ITEM_ID)

                # Create folder
                folder = FolderStorage.create_folder(
                    name=name.strip(),
                    parent_id=parent_id,
                )

                # Refresh tree
                self.refresh()

                # Emit signal
                self.folder_created.emit(folder.id)

                logger.info(f"Created folder: {folder.name} (id={folder.id})")

            except Exception as e:
                logger.error(f"Failed to create folder: {e}")
                self._show_error("Failed to create folder", str(e))

    @Slot()
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on tree item."""
        item_type = item.data(0, self.ROLE_ITEM_TYPE)
        item_id = item.data(0, self.ROLE_ITEM_ID)

        if item_type == self.ITEM_TYPE_PROJECT:
            self.project_opened.emit(item_id)
        elif item_type == self.ITEM_TYPE_FOLDER:
            # Toggle expand/collapse
            item.setExpanded(not item.isExpanded())

    @Slot()
    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        selected = self._tree.currentItem()
        if selected:
            item_type = selected.data(0, self.ROLE_ITEM_TYPE)
            item_id = selected.data(0, self.ROLE_ITEM_ID)

            if item_type == self.ITEM_TYPE_PROJECT:
                self.project_selected.emit(item_id)

    @Slot()
    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """Handle folder expansion - persist state."""
        item_type = item.data(0, self.ROLE_ITEM_TYPE)
        if item_type == self.ITEM_TYPE_FOLDER:
            folder_id = item.data(0, self.ROLE_ITEM_ID)
            self._save_expand_state(folder_id, True)

    @Slot()
    def _on_item_collapsed(self, item: QTreeWidgetItem) -> None:
        """Handle folder collapse - persist state."""
        item_type = item.data(0, self.ROLE_ITEM_TYPE)
        if item_type == self.ITEM_TYPE_FOLDER:
            folder_id = item.data(0, self.ROLE_ITEM_ID)
            self._save_expand_state(folder_id, False)

    def _save_expand_state(self, folder_id: str, expanded: bool) -> None:
        """Save folder expand state to storage."""
        try:
            folders_file = FolderStorage.load_folders()
            folder = folders_file.get_folder(folder_id)
            if folder:
                folder.is_expanded = expanded
                FolderStorage.save_folders(folders_file)
        except Exception as e:
            logger.debug(f"Failed to save expand state: {e}")

    @Slot()
    def _on_context_menu(self, pos: QPoint) -> None:
        """Show context menu for tree item."""
        item = self._tree.itemAt(pos)

        menu = QMenu(self)
        # v2 context menu styling
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME_V2.menu_bg};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.menu_border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px;
            }}
            QMenu::item {{
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.lg}px;
                border-radius: {TOKENS_V2.radius.xs}px;
                min-height: {TOKENS_V2.sizes.menu_item_height}px;
            }}
            QMenu::item:selected {{
                background-color: {THEME_V2.bg_selected};
                color: {THEME_V2.text_primary};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {THEME_V2.border};
                margin: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
            }}
        """)

        if item:
            item_type = item.data(0, self.ROLE_ITEM_TYPE)
            item_id = item.data(0, self.ROLE_ITEM_ID)

            # Store context item for slot methods
            self._context_item_id = item_id
            self._context_item_type = item_type

            if item_type == self.ITEM_TYPE_FOLDER:
                # Folder context menu
                new_folder_action = menu.addAction("New Subfolder")
                new_folder_action.triggered.connect(self._on_context_create_subfolder)

                menu.addSeparator()

                rename_action = menu.addAction("Rename")
                rename_action.triggered.connect(self._on_context_rename_folder)

                color_action = menu.addAction("Change Color")
                color_action.triggered.connect(self._on_context_change_color)

                menu.addSeparator()

                delete_action = menu.addAction("Delete")
                delete_action.triggered.connect(self._on_context_delete_folder)

            elif item_type == self.ITEM_TYPE_PROJECT:
                # Project context menu
                open_action = menu.addAction("Open Project")
                open_action.triggered.connect(self._on_context_open_project)

                menu.addSeparator()

                move_menu = menu.addMenu("Move to Folder")
                self._populate_move_menu(move_menu, item_id)

        else:
            # Empty area context menu
            new_folder_action = menu.addAction("New Folder")
            new_folder_action.triggered.connect(self._on_new_folder)

        menu.exec_(self._tree.mapToGlobal(pos))

    @Slot()
    def _on_context_create_subfolder(self) -> None:
        """Handle create subfolder context menu action."""
        if self._context_item_id:
            self._create_subfolder(self._context_item_id)

    @Slot()
    def _on_context_rename_folder(self) -> None:
        """Handle rename folder context menu action."""
        if self._context_item_id:
            self._rename_folder(self._context_item_id)

    @Slot()
    def _on_context_change_color(self) -> None:
        """Handle change color context menu action."""
        if self._context_item_id:
            self._change_folder_color(self._context_item_id)

    @Slot()
    def _on_context_delete_folder(self) -> None:
        """Handle delete folder context menu action."""
        if self._context_item_id:
            self._delete_folder(self._context_item_id)

    @Slot()
    def _on_context_open_project(self) -> None:
        """Handle open project context menu action."""
        if self._context_item_id:
            self.project_opened.emit(self._context_item_id)

    def _populate_move_menu(self, menu: QMenu, project_id: str) -> None:
        """Populate the 'Move to Folder' submenu."""
        # Store project_id for move operations
        self._move_project_id = project_id

        # Add root option
        root_action = menu.addAction("(Root)")
        root_action.triggered.connect(partial(self._move_project_to_folder, project_id, None))

        menu.addSeparator()

        # Add all folders (with error handling)
        try:
            folders_file = FolderStorage.load_folders()
            for folder in sorted(folders_file.folders.values(), key=lambda f: f.name):
                if not folder.is_archived:
                    action = menu.addAction(folder.name)
                    action.triggered.connect(
                        partial(self._move_project_to_folder, project_id, folder.id)
                    )
        except Exception as e:
            logger.error(f"Failed to load folders for move menu: {e}")

    def _create_subfolder(self, parent_id: str) -> None:
        """Create a subfolder under the specified parent."""
        name, ok = QInputDialog.getText(
            self,
            "New Subfolder",
            "Folder name:",
            text="New Subfolder",
        )

        if ok and name.strip():
            try:
                folder = FolderStorage.create_folder(
                    name=name.strip(),
                    parent_id=parent_id,
                )
                self.refresh()
                self.folder_created.emit(folder.id)
                logger.info(f"Created subfolder: {folder.name}")
            except Exception as e:
                logger.error(f"Failed to create subfolder: {e}")
                self._show_error("Failed to create subfolder", str(e))

    def _rename_folder(self, folder_id: str) -> None:
        """Rename a folder."""
        folders_file = FolderStorage.load_folders()
        folder = folders_file.get_folder(folder_id)
        if not folder:
            return

        name, ok = QInputDialog.getText(
            self,
            "Rename Folder",
            "New name:",
            text=folder.name,
        )

        if ok and name.strip():
            try:
                FolderStorage.rename_folder(folder_id, name.strip())
                self.refresh()
                self.folder_renamed.emit(folder_id, name.strip())
                logger.info(f"Renamed folder to: {name.strip()}")
            except Exception as e:
                logger.error(f"Failed to rename folder: {e}")
                self._show_error("Failed to rename folder", str(e))

    def _change_folder_color(self, folder_id: str) -> None:
        """Change folder color."""
        folders_file = FolderStorage.load_folders()
        folder = folders_file.get_folder(folder_id)
        if not folder:
            return

        color = QColorDialog.getColor(
            QColor(folder.color),
            self,
            "Choose Folder Color",
        )

        if color.isValid():
            try:
                color_hex = color.name()
                FolderStorage.set_folder_color(folder_id, color_hex)
                self.refresh()
                self.folder_color_changed.emit(folder_id, color_hex)
                logger.info(f"Changed folder color to: {color_hex}")
            except Exception as e:
                logger.error(f"Failed to change folder color: {e}")
                self._show_error("Failed to change color", str(e))

    def _delete_folder(self, folder_id: str) -> None:
        """Delete a folder after confirmation."""
        folders_file = FolderStorage.load_folders()
        folder = folders_file.get_folder(folder_id)
        if not folder:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Folder")
        msg.setText(f"Delete folder '{folder.name}'?")
        msg.setInformativeText("Projects in this folder will be moved to the parent folder.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(self._get_message_box_style())

        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                FolderStorage.delete_folder(folder_id)
                self.refresh()
                self.folder_deleted.emit(folder_id)
                logger.info(f"Deleted folder: {folder.name}")
            except Exception as e:
                logger.error(f"Failed to delete folder: {e}")
                self._show_error("Failed to delete folder", str(e))

    def _move_project_to_folder(self, project_id: str, folder_id: str | None) -> None:
        """Move a project to a folder."""
        try:
            FolderStorage.move_project_to_folder(project_id, folder_id)
            self.refresh()
            self.project_moved.emit(project_id, folder_id or "")
            logger.info(f"Moved project {project_id} to folder {folder_id}")
        except Exception as e:
            logger.error(f"Failed to move project: {e}")
            self._show_error("Failed to move project", str(e))

    @Slot()
    def _collapse_all(self) -> None:
        """Collapse all folders."""
        self._tree.collapseAll()

    @Slot()
    def _expand_all(self) -> None:
        """Expand all folders."""
        self._tree.expandAll()

    def _show_error(self, title: str, message: str) -> None:
        """Show styled error message."""
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet(self._get_message_box_style())
        msg.exec()

    def _get_message_box_style(self) -> str:
        """Get styled QMessageBox stylesheet (v2)."""
        t = THEME_V2
        tok = TOKENS_V2
        return f"""
            QMessageBox {{ background: {t.bg_surface}; }}
            QMessageBox QLabel {{ color: {t.text_primary}; font-size: {tok.typography.body}px; }}
            QPushButton {{
                background: {t.bg_component};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: 0 {tok.spacing.md}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-weight: {tok.typography.weight_medium};
                min-height: {tok.sizes.button_md}px;
                min-width: {tok.sizes.button_min_width}px;
            }}
            QPushButton:hover {{ background: {t.bg_hover}; border-color: {t.border_focus}; color: {t.text_primary}; }}
            QPushButton:default {{ background: {t.primary}; border-color: {t.primary}; color: {t.text_on_primary}; }}
        """

    # ==================== Public API ====================

    @Slot()
    def refresh(self) -> None:
        """Refresh the folder tree from storage."""
        self._tree.clear()
        self._folder_items.clear()
        self._project_items.clear()

        try:
            folder_tree = FolderStorage.get_folder_tree()
            self._build_tree(folder_tree, None)
            self._update_display()
        except Exception as e:
            logger.error(f"Failed to refresh folder tree: {e}")

    def _build_tree(self, nodes: list[dict], parent_item: QTreeWidgetItem | None) -> None:
        """
        Recursively build tree from folder structure.

        Args:
            nodes: List of folder nodes with children
            parent_item: Parent tree item (None for root)
        """
        for node in nodes:
            folder = node["folder"]
            folder_item = self._create_folder_item(folder)

            if parent_item:
                parent_item.addChild(folder_item)
            else:
                self._tree.addTopLevelItem(folder_item)

            # Add projects in this folder
            for project_id in folder.project_ids:
                project_data = self._projects.get(project_id)
                if project_data:
                    project_name = project_data.get("name", project_id)
                    project_item = self._create_project_item(project_id, project_name)
                    folder_item.addChild(project_item)

            # Recursively add children
            self._build_tree(node["children"], folder_item)

            # Restore expand state
            folder_item.setExpanded(folder.is_expanded)

    def set_projects(self, projects: dict[str, dict[str, Any]]) -> None:
        """
        Set the projects data for display.

        Args:
            projects: Dict of project_id -> project_data (must have 'name' key)
        """
        self._projects = projects
        self.refresh()

    def add_project(self, project_id: str, name: str, folder_id: str | None = None) -> None:
        """
        Add a project to the tree.

        Args:
            project_id: Project identifier
            name: Project display name
            folder_id: Optional folder to place project in
        """
        self._projects[project_id] = {"name": name}

        if folder_id:
            FolderStorage.move_project_to_folder(project_id, folder_id)

        self.refresh()

    def remove_project(self, project_id: str) -> None:
        """
        Remove a project from the tree.

        Args:
            project_id: Project identifier to remove
        """
        if project_id in self._projects:
            del self._projects[project_id]
        self.refresh()

    def select_project(self, project_id: str) -> None:
        """
        Select a project in the tree.

        Args:
            project_id: Project identifier to select
        """
        if project_id in self._project_items:
            item = self._project_items[project_id]
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)

    def expand_to_folder(self, folder_id: str) -> None:
        """
        Expand tree to show a specific folder.

        Args:
            folder_id: Folder identifier to expand to
        """
        if folder_id in self._folder_items:
            item = self._folder_items[folder_id]
            # Expand all parents
            parent = item.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            self._tree.scrollToItem(item)

    def get_selected_folder_id(self) -> str | None:
        """
        Get the currently selected folder ID.

        Returns:
            Folder ID or None if no folder selected
        """
        selected = self._tree.currentItem()
        if selected:
            item_type = selected.data(0, self.ROLE_ITEM_TYPE)
            if item_type == self.ITEM_TYPE_FOLDER:
                return selected.data(0, self.ROLE_ITEM_ID)
        return None

    def get_selected_project_id(self) -> str | None:
        """
        Get the currently selected project ID.

        Returns:
            Project ID or None if no project selected
        """
        selected = self._tree.currentItem()
        if selected:
            item_type = selected.data(0, self.ROLE_ITEM_TYPE)
            if item_type == self.ITEM_TYPE_PROJECT:
                return selected.data(0, self.ROLE_ITEM_ID)
        return None

    def cleanup(self) -> None:
        """Clean up resources."""
        self._folder_items.clear()
        self._project_items.clear()
        self._projects.clear()
        logger.debug("ProjectExplorerPanel cleaned up")

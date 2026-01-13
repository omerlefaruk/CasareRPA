"""File and folder picker components v2 - Epic 5.2.

Consistent UX for file/folder selection.
All using THEME_V2/TOKENS_V2 exclusively.
"""

from enum import Enum
from typing import Literal

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import (
    BasePrimitive,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import ToolButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import TextInput

# =============================================================================
# TYPE ALIASES
# =============================================================================

InputSize = Literal["sm", "md", "lg"]

# Map size values to icon sizes
_SIZE_TO_ICON_SIZE = {
    "sm": TOKENS_V2.sizes.icon_sm,
    "md": TOKENS_V2.sizes.icon_md,
    "lg": TOKENS_V2.sizes.icon_lg,
}

# =============================================================================
# PATH TYPE ENUM
# =============================================================================

class PathType(Enum):
    """Type of path selection."""
    FILE = "file"
    DIRECTORY = "directory"
    SAVE_FILE = "save_file"

# =============================================================================
# FILE FILTERS
# =============================================================================

class FileFilter:
    """Common file filter strings for QFileDialog."""

    ALL = "All Files (*.*)"
    TEXT = "Text Files (*.txt);;All Files (*.*)"
    EXCEL = "Excel Files (*.xlsx *.xls);;All Files (*.*)"
    CSV = "CSV Files (*.csv);;All Files (*.*)"
    JSON = "JSON Files (*.json);;All Files (*.*)"
    XML = "XML Files (*.xml);;All Files (*.*)"
    PDF = "PDF Files (*.pdf);;All Files (*.*)"
    IMAGES = "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*.*)"
    PYTHON = "Python Files (*.py);;All Files (*.*)"

# =============================================================================
# FILE PICKER
# =============================================================================

class FilePicker(BasePrimitive):
    r"""File path input with browse button.

    Layout:
    ┌────────────────────────────────────────────┐
    │ ┌────────────────────────────────┐ ┌───┐  │
    │ │ C:\path\to\file.xlsx          │ │…│  │
    │ └────────────────────────────────┘ └───┘  │
    └────────────────────────────────────────────┘

    Signals:
        path_changed(str): Emitted when the selected path changes
        browsing_started(): Emitted when browse dialog opens
        browsing_finished(str): Emitted when browse dialog closes with path
    """

    path_changed = Signal(str)
    browsing_started = Signal()
    browsing_finished = Signal(str)

    def __init__(
        self,
        path_type: PathType = PathType.FILE,
        *,
        filter: str = "",
        placeholder: str = "",
        size: InputSize = "md",
        parent: QWidget | None = None,
    ):
        self._path_type = path_type
        self._filter = filter or FileFilter.ALL
        self._placeholder = placeholder or self._get_default_placeholder()
        self._size = size
        self._current_path = ""
        super().__init__(parent=parent)

    def _get_default_placeholder(self) -> str:
        """Get default placeholder based on path type."""
        if self._path_type == PathType.FILE:
            return "Select file..."
        elif self._path_type == PathType.SAVE_FILE:
            return "Enter file name..."
        return "Select folder..."

    def setup_ui(self) -> None:
        """Set up the file picker UI."""
        from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Path input
        self._input = TextInput(
            placeholder=self._placeholder,
            size=self._size,
            readonly=self._path_type != PathType.SAVE_FILE,
        )
        self._input.text_changed.connect(self._on_text_changed)
        layout.addWidget(self._input, 1)

        # Browse button with icon
        icon_size = _SIZE_TO_ICON_SIZE.get(self._size, TOKENS_V2.sizes.icon_md)
        self._browse_btn = ToolButton(
            icon=get_icon("folder_open", size=icon_size),
            tooltip="Browse..." if self._path_type == PathType.FILE else "Select folder...",
            icon_size=icon_size,
        )
        self._browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self._browse_btn)

    def connect_signals(self) -> None:
        """Connect signals (handled in setup_ui)."""
        pass

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """Handle text change in input."""
        self._current_path = text
        self.path_changed.emit(text)

    @Slot()
    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        self.browsing_started.emit()

        # Show appropriate dialog
        if self._path_type == PathType.DIRECTORY:
            path = self._show_directory_dialog()
        elif self._path_type == PathType.SAVE_FILE:
            path = self._show_save_dialog()
        else:
            path = self._show_file_dialog()

        if path:
            self.set_path(path)

        self.browsing_finished.emit(path or "")

    def _show_file_dialog(self) -> str:
        """Show file open dialog."""
        parent = self.window()
        filename, _ = QFileDialog.getOpenFileName(
            parent,
            "Select File",
            self._current_path,
            self._filter,
        )
        return filename

    def _show_save_dialog(self) -> str:
        """Show file save dialog."""
        parent = self.window()
        filename, _ = QFileDialog.getSaveFileName(
            parent,
            "Save File",
            self._current_path,
            self._filter,
        )
        return filename

    def _show_directory_dialog(self) -> str:
        """Show directory dialog."""
        parent = self.window()
        dirname = QFileDialog.getExistingDirectory(
            parent,
            "Select Folder",
            self._current_path,
        )
        return dirname

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_path(self) -> str:
        """Get the current path."""
        return self._current_path

    def set_path(self, path: str) -> None:
        """Set the current path."""
        self._current_path = path
        self._input.set_value(path)
        self.path_changed.emit(path)

    def clear(self) -> None:
        """Clear the path."""
        self.set_path("")

    def set_filter(self, filter: str) -> None:
        """Set the file filter for the browse dialog."""
        self._filter = filter

    def set_placeholder(self, placeholder: str) -> None:
        """Set the input placeholder text."""
        self._placeholder = placeholder
        self._input.set_placeholder(placeholder)

# =============================================================================
# FOLDER PICKER
# =============================================================================

class FolderPicker(BasePrimitive):
    """Folder path input with browse button.

    Simpler interface than FilePicker, specialized for directories.

    Signals:
        path_changed(str): Emitted when the selected path changes
        browsing_started(): Emitted when browse dialog opens
        browsing_finished(str): Emitted when browse dialog closes with path
    """

    path_changed = Signal(str)
    browsing_started = Signal()
    browsing_finished = Signal(str)

    def __init__(
        self,
        *,
        placeholder: str = "Select folder...",
        size: InputSize = "md",
        show_hidden: bool = False,
        parent: QWidget | None = None,
    ):
        self._placeholder = placeholder
        self._size = size
        self._show_hidden = show_hidden
        self._current_path = ""
        super().__init__(parent=parent)

    def setup_ui(self) -> None:
        """Set up the folder picker UI."""
        from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Path input
        self._input = TextInput(
            placeholder=self._placeholder,
            size=self._size,
            readonly=True,
        )
        self._input.text_changed.connect(self._on_text_changed)
        layout.addWidget(self._input, 1)

        # Browse button with folder icon
        icon_size = _SIZE_TO_ICON_SIZE.get(self._size, TOKENS_V2.sizes.icon_md)
        self._browse_btn = ToolButton(
            icon=get_icon("folder", size=icon_size),
            tooltip="Select folder...",
            icon_size=icon_size,
        )
        self._browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self._browse_btn)

    def connect_signals(self) -> None:
        """Connect signals (handled in setup_ui)."""
        pass

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """Handle text change in input."""
        self._current_path = text
        self.path_changed.emit(text)

    @Slot()
    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        self.browsing_started.emit()

        parent = self.window()
        options = QFileDialog.Option.ShowDirsOnly
        dirname = QFileDialog.getExistingDirectory(
            parent,
            "Select Folder",
            self._current_path,
            options,
        )

        if dirname:
            self.set_path(dirname)

        self.browsing_finished.emit(dirname or "")

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_path(self) -> str:
        """Get the current path."""
        return self._current_path

    def set_path(self, path: str) -> None:
        """Set the current path."""
        self._current_path = path
        self._input.set_value(path)
        self.path_changed.emit(path)

    def clear(self) -> None:
        """Clear the path."""
        self.set_path("")

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_file_picker(
    path_type: PathType = PathType.FILE,
    *,
    filter: str = "",
    placeholder: str = "",
    size: InputSize = "md",
    parent: QWidget | None = None,
) -> FilePicker:
    """Factory function to create a FilePicker."""
    return FilePicker(
        path_type=path_type,
        filter=filter,
        placeholder=placeholder,
        size=size,
        parent=parent,
    )

def create_folder_picker(
    *,
    placeholder: str = "Select folder...",
    size: InputSize = "md",
    show_hidden: bool = False,
    parent: QWidget | None = None,
) -> FolderPicker:
    """Factory function to create a FolderPicker."""
    return FolderPicker(
        placeholder=placeholder,
        size=size,
        show_hidden=show_hidden,
        parent=parent,
    )

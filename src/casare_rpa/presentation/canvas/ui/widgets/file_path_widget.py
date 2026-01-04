"""
File Path Widget.

Reusable widget for file and directory path selection with browse button.
Provides Windows Explorer integration for easy file/folder selection.
"""

from enum import Enum

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME


class PathType(Enum):
    """Types of paths that can be selected."""

    FILE = "file"
    DIRECTORY = "directory"
    SAVE_FILE = "save_file"  # For saving new files


class FilePathWidget(QWidget):
    """
    A widget combining a text input with a browse button for file/directory selection.

    Features:
    - Text input for manual path entry
    - Browse button that opens Windows Explorer dialog
    - Support for file, directory, and save dialogs
    - File type filtering
    - Placeholder text support
    - Signal emission on path changes

    Usage:
        # For file selection
        widget = FilePathWidget(
            path_type=PathType.FILE,
            filter="Excel Files (*.xlsx *.xls);;All Files (*.*)",
            placeholder="Select an Excel file..."
        )
        widget.path_changed.connect(on_path_changed)

        # For directory selection
        widget = FilePathWidget(
            path_type=PathType.DIRECTORY,
            placeholder="Select output folder..."
        )

        # Get/set path
        path = widget.get_path()
        widget.set_path("C:/Users/example.xlsx")
    """

    # Signal emitted when path changes (either by typing or browsing)
    path_changed = Signal(str)

    # Common file filters for reuse
    FILTER_ALL = "All Files (*.*)"
    FILTER_EXCEL = "Excel Files (*.xlsx *.xls);;All Files (*.*)"
    FILTER_CSV = "CSV Files (*.csv);;All Files (*.*)"
    FILTER_TEXT = "Text Files (*.txt);;All Files (*.*)"
    FILTER_JSON = "JSON Files (*.json);;All Files (*.*)"
    FILTER_XML = "XML Files (*.xml);;All Files (*.*)"
    FILTER_PDF = "PDF Files (*.pdf);;All Files (*.*)"
    FILTER_IMAGE = "Image Files (*.png *.jpg *.jpeg *.gif *.bmp);;All Files (*.*)"
    FILTER_WORD = "Word Documents (*.docx *.doc);;All Files (*.*)"
    FILTER_DATA = "Data Files (*.xlsx *.xls *.csv *.json);;All Files (*.*)"

    def __init__(
        self,
        path_type: PathType = PathType.FILE,
        filter: str = "",
        placeholder: str = "",
        initial_path: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the file path widget.

        Args:
            path_type: Type of path selection (FILE, DIRECTORY, SAVE_FILE)
            filter: File type filter for dialog (e.g., "Excel Files (*.xlsx)")
            placeholder: Placeholder text for the input field
            initial_path: Initial path to display
            parent: Parent widget
        """
        super().__init__(parent)

        self._path_type = path_type
        self._filter = filter or self.FILTER_ALL
        self._placeholder = placeholder
        self._last_directory = ""  # Remember last browsed directory

        self._setup_ui()

        if initial_path:
            self.set_path(initial_path)

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Path input field
        self._path_input = QLineEdit()
        self._path_input.setPlaceholderText(self._placeholder or self._get_default_placeholder())
        self._path_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._path_input, 1)  # Stretch factor 1

        # Browse button with folder icon
        self._browse_btn = QPushButton()
        self._browse_btn.setFixedWidth(28)
        self._browse_btn.setToolTip(self._get_button_tooltip())
        self._browse_btn.clicked.connect(self._on_browse_clicked)

        # Use v2 icons for folder/file
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

        if self._path_type == PathType.DIRECTORY:
            icon = get_icon_v2("open", size=16)  # "folder" mapping
        else:
            icon = get_icon_v2("new", size=16)  # "file" mapping
        self._browse_btn.setIcon(icon)

        layout.addWidget(self._browse_btn)

        # Apply styling
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply dark theme styling using THEME constants."""
        self._path_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME.bg_hover};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 4px 8px;
            }}
            QLineEdit:focus {{
                border-color: {THEME.border_focus};
            }}
            QLineEdit:hover {{
                border-color: {THEME.border_light};
            }}
        """)

        self._browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME.bg_hover};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: {THEME.bg_hover};
                border-color: {THEME.border_focus};
            }}
            QPushButton:pressed {{
                background-color: {THEME.primary};
            }}
        """)

    def _get_default_placeholder(self) -> str:
        """Get default placeholder text based on path type."""
        if self._path_type == PathType.DIRECTORY:
            return "Select folder..."
        elif self._path_type == PathType.SAVE_FILE:
            return "Select save location..."
        else:
            return "Select file..."

    def _get_button_tooltip(self) -> str:
        """Get tooltip for browse button."""
        if self._path_type == PathType.DIRECTORY:
            return "Browse for folder"
        elif self._path_type == PathType.SAVE_FILE:
            return "Browse for save location"
        else:
            return "Browse for file"

    def _on_text_changed(self, text: str) -> None:
        """Handle text input changes."""
        self.path_changed.emit(text)

    def _on_browse_clicked(self) -> None:
        """Open file/directory browser dialog."""
        # Determine starting directory
        current_path = self._path_input.text().strip()
        start_dir = ""

        if current_path:
            import os

            if os.path.isdir(current_path):
                start_dir = current_path
            elif os.path.dirname(current_path):
                parent = os.path.dirname(current_path)
                if os.path.isdir(parent):
                    start_dir = parent

        if not start_dir and self._last_directory:
            start_dir = self._last_directory

        # Open appropriate dialog
        path = ""

        if self._path_type == PathType.DIRECTORY:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Directory",
                start_dir,
                QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
            )
        elif self._path_type == PathType.SAVE_FILE:
            path, _ = QFileDialog.getSaveFileName(self, "Save File As", start_dir, self._filter)
        else:  # PathType.FILE
            path, _ = QFileDialog.getOpenFileName(self, "Select File", start_dir, self._filter)

        if path:
            # Remember directory for next time
            import os

            self._last_directory = os.path.dirname(path) if os.path.isfile(path) else path

            # Update input and emit signal
            self._path_input.setText(path)
            logger.debug(f"Selected path: {path}")

    def get_path(self) -> str:
        """
        Get the current path value.

        Returns:
            Current path string
        """
        return self._path_input.text().strip()

    def set_path(self, path: str) -> None:
        """
        Set the path value.

        Args:
            path: Path to set
        """
        self._path_input.setText(path)

    def set_filter(self, filter: str) -> None:
        """
        Set the file type filter for the dialog.

        Args:
            filter: Filter string (e.g., "Excel Files (*.xlsx)")
        """
        self._filter = filter

    def set_placeholder(self, text: str) -> None:
        """
        Set placeholder text.

        Args:
            text: Placeholder text
        """
        self._path_input.setPlaceholderText(text)

    def clear(self) -> None:
        """Clear the path input."""
        self._path_input.clear()

    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the widget."""
        super().setEnabled(enabled)
        self._path_input.setEnabled(enabled)
        self._browse_btn.setEnabled(enabled)


def get_filter_for_property(property_name: str) -> str:
    """
    Get appropriate file filter based on property name.

    This helper function infers the file type from common property naming patterns.

    Args:
        property_name: Name of the property (e.g., "excel_path", "image_file")

    Returns:
        Appropriate file filter string
    """
    name_lower = property_name.lower()

    # Excel-related
    if any(x in name_lower for x in ["excel", "xlsx", "xls", "workbook", "spreadsheet"]):
        return FilePathWidget.FILTER_EXCEL

    # CSV-related
    if "csv" in name_lower:
        return FilePathWidget.FILTER_CSV

    # Image-related
    if any(x in name_lower for x in ["image", "img", "photo", "picture", "screenshot"]):
        return FilePathWidget.FILTER_IMAGE

    # PDF-related
    if "pdf" in name_lower:
        return FilePathWidget.FILTER_PDF

    # JSON-related
    if "json" in name_lower:
        return FilePathWidget.FILTER_JSON

    # XML-related
    if "xml" in name_lower:
        return FilePathWidget.FILTER_XML

    # Text-related
    if any(x in name_lower for x in ["text", "txt", "log"]):
        return FilePathWidget.FILTER_TEXT

    # Word-related
    if any(x in name_lower for x in ["word", "doc", "docx", "document"]):
        return FilePathWidget.FILTER_WORD

    # Data files (generic)
    if any(x in name_lower for x in ["data", "input", "output"]):
        return FilePathWidget.FILTER_DATA

    # Default: all files
    return FilePathWidget.FILTER_ALL


def is_file_path_property(property_name: str) -> bool:
    """
    Check if a property name indicates a file path.

    Args:
        property_name: Name of the property

    Returns:
        True if the property appears to be a file path
    """
    name_lower = property_name.lower()

    # Common file path property patterns
    file_path_patterns = [
        "file_path",
        "filepath",
        "file",
        "path",
        "filename",
        "file_name",
        "source_file",
        "target_file",
        "input_file",
        "output_file",
        "excel_path",
        "csv_path",
        "image_path",
        "pdf_path",
        "document_path",
        "template_path",
        "attachment",
        "workbook_path",
    ]

    return any(pattern in name_lower for pattern in file_path_patterns)


def is_directory_path_property(property_name: str) -> bool:
    """
    Check if a property name indicates a directory path.

    Args:
        property_name: Name of the property

    Returns:
        True if the property appears to be a directory path
    """
    name_lower = property_name.lower()

    # Common directory path property patterns
    dir_path_patterns = [
        "directory",
        "folder",
        "dir_path",
        "folder_path",
        "output_dir",
        "input_dir",
        "save_dir",
        "target_dir",
        "source_dir",
        "working_dir",
        "base_dir",
        "root_dir",
    ]

    return any(pattern in name_lower for pattern in dir_path_patterns)

"""
Tests for Picker Components v2 - Epic 5.2.

Tests FilePicker, FolderPicker, PathType, and FileFilter.
"""

from unittest.mock import MagicMock, patch

import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QWidget

from casare_rpa.presentation.canvas.theme_system import TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.pickers import (
    FileFilter,
    FilePicker,
    FolderPicker,
    InputSize,
    PathType,
    create_file_picker,
    create_folder_picker,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import TextInput


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def widget(qapp):
    """Parent widget for testing."""
    return QWidget()


# =============================================================================
# PATH TYPE TESTS
# =============================================================================


class TestPathType:
    """Tests for PathType enum."""

    def test_file_value(self):
        """Test FILE enum value."""
        assert PathType.FILE.value == "file"

    def test_directory_value(self):
        """Test DIRECTORY enum value."""
        assert PathType.DIRECTORY.value == "directory"

    def test_save_file_value(self):
        """Test SAVE_FILE enum value."""
        assert PathType.SAVE_FILE.value == "save_file"

    def test_all_values(self):
        """Test all PathType values are unique."""
        values = [t.value for t in PathType]
        assert len(values) == len(set(values))


# =============================================================================
# FILE FILTER TESTS
# =============================================================================


class TestFileFilter:
    """Tests for FileFilter class."""

    def test_all_filter(self):
        """Test ALL filter string."""
        assert "All Files" in FileFilter.ALL
        assert "*.*" in FileFilter.ALL

    def test_text_filter(self):
        """Test TEXT filter string."""
        assert ".txt" in FileFilter.TEXT

    def test_excel_filter(self):
        """Test EXCEL filter string."""
        assert ".xlsx" in FileFilter.EXCEL
        assert ".xls" in FileFilter.EXCEL

    def test_csv_filter(self):
        """Test CSV filter string."""
        assert ".csv" in FileFilter.CSV

    def test_json_filter(self):
        """Test JSON filter string."""
        assert ".json" in FileFilter.JSON

    def test_xml_filter(self):
        """Test XML filter string."""
        assert ".xml" in FileFilter.XML

    def test_pdf_filter(self):
        """Test PDF filter string."""
        assert ".pdf" in FileFilter.PDF

    def test_images_filter(self):
        """Test IMAGES filter string."""
        extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
        for ext in extensions:
            assert ext in FileFilter.IMAGES

    def test_python_filter(self):
        """Test PYTHON filter string."""
        assert ".py" in FileFilter.PYTHON


# =============================================================================
# FILE PICKER TESTS
# =============================================================================


class TestFilePicker:
    """Tests for FilePicker component."""

    def test_initialization_file_mode(self, widget):
        """Test FilePicker initializes in FILE mode."""
        picker = FilePicker(PathType.FILE, parent=widget)
        assert picker._path_type == PathType.FILE
        assert picker._filter == FileFilter.ALL
        assert picker.get_path() == ""

    def test_initialization_directory_mode(self, widget):
        """Test FilePicker initializes in DIRECTORY mode."""
        picker = FilePicker(PathType.DIRECTORY, parent=widget)
        assert picker._path_type == PathType.DIRECTORY

    def test_initialization_save_file_mode(self, widget):
        """Test FilePicker initializes in SAVE_FILE mode."""
        picker = FilePicker(PathType.SAVE_FILE, parent=widget)
        assert picker._path_type == PathType.SAVE_FILE

    def test_custom_filter(self, widget):
        """Test FilePicker with custom filter."""
        picker = FilePicker(PathType.FILE, filter=FileFilter.JSON, parent=widget)
        assert ".json" in picker._filter

    def test_custom_placeholder(self, widget):
        """Test FilePicker with custom placeholder."""
        placeholder = "Select config file..."
        picker = FilePicker(PathType.FILE, placeholder=placeholder, parent=widget)
        assert picker._placeholder == placeholder

    def test_default_placeholder_file(self, widget):
        """Test default placeholder for FILE type."""
        picker = FilePicker(PathType.FILE, parent=widget)
        assert "file" in picker._placeholder.lower()

    def test_default_placeholder_save(self, widget):
        """Test default placeholder for SAVE_FILE type."""
        picker = FilePicker(PathType.SAVE_FILE, parent=widget)
        assert "file name" in picker._placeholder.lower()

    def test_default_placeholder_directory(self, widget):
        """Test default placeholder for DIRECTORY type."""
        picker = FilePicker(PathType.DIRECTORY, parent=widget)
        assert "folder" in picker._placeholder.lower()

    def test_size_variants(self, widget):
        """Test FilePicker size variants."""
        for size in ["sm", "md", "lg"]:
            picker = FilePicker(PathType.FILE, size=size, parent=widget)
            assert picker._size == size

    def test_input_readonly_file_mode(self, widget):
        """Test input is readonly in FILE mode."""
        picker = FilePicker(PathType.FILE, parent=widget)
        assert picker._input.is_readonly()

    def test_input_readonly_directory_mode(self, widget):
        """Test input is readonly in DIRECTORY mode."""
        picker = FilePicker(PathType.DIRECTORY, parent=widget)
        assert picker._input.is_readonly()

    def test_input_editable_save_mode(self, widget):
        """Test input is editable in SAVE_FILE mode."""
        picker = FilePicker(PathType.SAVE_FILE, parent=widget)
        assert not picker._input.is_readonly()

    def test_get_path(self, widget):
        """Test get_path method."""
        picker = FilePicker(PathType.FILE, parent=widget)
        picker.set_path("C:\\test\\file.txt")
        assert picker.get_path() == "C:\\test\\file.txt"

    def test_set_path(self, widget):
        """Test set_path method."""
        picker = FilePicker(PathType.FILE, parent=widget)
        picker.set_path("/home/user/document.pdf")
        assert picker.get_path() == "/home/user/document.pdf"
        assert picker._input.get_value() == "/home/user/document.pdf"

    def test_clear(self, widget):
        """Test clear method."""
        picker = FilePicker(PathType.FILE, parent=widget)
        picker.set_path("some/path")
        picker.clear()
        assert picker.get_path() == ""

    def test_set_filter(self, widget):
        """Test set_filter method."""
        picker = FilePicker(PathType.FILE, parent=widget)
        picker.set_filter(FileFilter.IMAGES)
        assert ".png" in picker._filter

    def test_set_placeholder(self, widget):
        """Test set_placeholder method."""
        picker = FilePicker(PathType.FILE, parent=widget)
        picker.set_placeholder("Choose a file...")
        assert picker._placeholder == "Choose a file..."

    def test_path_changed_signal(self, widget):
        """Test path_changed signal emission."""
        picker = FilePicker(PathType.FILE, parent=widget)
        results = []

        picker.path_changed.connect(lambda p: results.append(p))
        picker.set_path("/test/path")

        assert "/test/path" in results

    def test_path_changed_on_text_edit(self, widget):
        """Test path_changed signal on text edit in SAVE mode."""
        picker = FilePicker(PathType.SAVE_FILE, parent=widget)
        results = []

        picker.path_changed.connect(lambda p: results.append(p))
        picker._input.set_value("myfile.txt")
        QApplication.processEvents()

        assert "myfile.txt" in results

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getOpenFileName")
    def test_browse_file_dialog(self, mock_get_open, widget):
        """Test browse button opens file dialog in FILE mode."""
        mock_get_open.return_value = ("/path/to/file.txt", "")

        picker = FilePicker(PathType.FILE, parent=widget)
        picker._browse_btn.click()
        QApplication.processEvents()

        mock_get_open.assert_called_once()
        assert picker.get_path() == "/path/to/file.txt"

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getSaveFileName")
    def test_browse_save_dialog(self, mock_get_save, widget):
        """Test browse button opens save dialog in SAVE_FILE mode."""
        mock_get_save.return_value = ("/path/to/save.txt", "")

        picker = FilePicker(PathType.SAVE_FILE, parent=widget)
        picker._browse_btn.click()
        QApplication.processEvents()

        mock_get_save.assert_called_once()
        assert picker.get_path() == "/path/to/save.txt"

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getExistingDirectory")
    def test_browse_directory_dialog(self, mock_get_dir, widget):
        """Test browse button opens directory dialog in DIRECTORY mode."""
        mock_get_dir.return_value = "/path/to/folder"

        picker = FilePicker(PathType.DIRECTORY, parent=widget)
        picker._browse_btn.click()
        QApplication.processEvents()

        mock_get_dir.assert_called_once()
        assert picker.get_path() == "/path/to/folder"

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getOpenFileName")
    def test_browse_started_signal(self, mock_get_open, widget):
        """Test browsing_started signal emission."""
        mock_get_open.return_value = ("", "")

        picker = FilePicker(PathType.FILE, parent=widget)
        results = []

        picker.browsing_started.connect(lambda: results.append("start"))
        picker._browse_btn.click()
        QApplication.processEvents()

        assert "start" in results

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getOpenFileName")
    def test_browsing_finished_signal(self, mock_get_open, widget):
        """Test browsing_finished signal emission."""
        mock_get_open.return_value = ("/selected/path", "")

        picker = FilePicker(PathType.FILE, parent=widget)
        results = []

        picker.browsing_finished.connect(lambda p: results.append(p))
        picker._browse_btn.click()
        QApplication.processEvents()

        assert "/selected/path" in results

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getOpenFileName")
    def test_browse_cancellation(self, mock_get_open, widget):
        """Test path is unchanged when browse is cancelled."""
        mock_get_open.return_value = ("", "")

        picker = FilePicker(PathType.FILE, parent=widget)
        picker.set_path("existing/path.txt")

        picker._browse_btn.click()
        QApplication.processEvents()

        # Path should remain unchanged
        assert picker.get_path() == "existing/path.txt"

    def test_browse_button_exists(self, widget):
        """Test browse button is present."""
        picker = FilePicker(PathType.FILE, parent=widget)
        assert picker._browse_btn is not None

    def test_input_widget_exists(self, widget):
        """Test input widget is present."""
        picker = FilePicker(PathType.FILE, parent=widget)
        assert picker._input is not None
        assert isinstance(picker._input, TextInput)


# =============================================================================
# FOLDER PICKER TESTS
# =============================================================================


class TestFolderPicker:
    """Tests for FolderPicker component."""

    def test_initialization(self, widget):
        """Test FolderPicker initializes correctly."""
        picker = FolderPicker(parent=widget)
        assert picker.get_path() == ""
        assert picker._placeholder == "Select folder..."

    def test_custom_placeholder(self, widget):
        """Test FolderPicker with custom placeholder."""
        picker = FolderPicker(placeholder="Choose directory...", parent=widget)
        assert picker._placeholder == "Choose directory..."

    def test_size_variants(self, widget):
        """Test FolderPicker size variants."""
        for size in ["sm", "md", "lg"]:
            picker = FolderPicker(size=size, parent=widget)
            assert picker._size == size

    def test_show_hidden_flag(self, widget):
        """Test show_hidden parameter is stored."""
        picker = FolderPicker(show_hidden=True, parent=widget)
        assert picker._show_hidden

    def test_get_path(self, widget):
        """Test get_path method."""
        picker = FolderPicker(parent=widget)
        picker.set_path("C:\\Users\\Test")
        assert picker.get_path() == "C:\\Users\\Test"

    def test_set_path(self, widget):
        """Test set_path method."""
        picker = FolderPicker(parent=widget)
        picker.set_path("/home/user/folder")
        assert picker.get_path() == "/home/user/folder"
        assert picker._input.get_value() == "/home/user/folder"

    def test_clear(self, widget):
        """Test clear method."""
        picker = FolderPicker(parent=widget)
        picker.set_path("some/folder")
        picker.clear()
        assert picker.get_path() == ""

    def test_input_is_readonly(self, widget):
        """Test input is always readonly for FolderPicker."""
        picker = FolderPicker(parent=widget)
        assert picker._input.is_readonly()

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getExistingDirectory")
    def test_browse_dialog(self, mock_get_dir, widget):
        """Test browse button opens directory dialog."""
        mock_get_dir.return_value = "/selected/folder"

        picker = FolderPicker(parent=widget)
        picker._browse_btn.click()
        QApplication.processEvents()

        mock_get_dir.assert_called_once()
        assert picker.get_path() == "/selected/folder"

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getExistingDirectory")
    def test_browse_started_signal(self, mock_get_dir, widget):
        """Test browsing_started signal emission."""
        mock_get_dir.return_value = ""

        picker = FolderPicker(parent=widget)
        results = []

        picker.browsing_started.connect(lambda: results.append("start"))
        picker._browse_btn.click()
        QApplication.processEvents()

        assert "start" in results

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getExistingDirectory")
    def test_browsing_finished_signal(self, mock_get_dir, widget):
        """Test browsing_finished signal emission."""
        mock_get_dir.return_value = "/selected/folder"

        picker = FolderPicker(parent=widget)
        results = []

        picker.browsing_finished.connect(lambda p: results.append(p))
        picker._browse_btn.click()
        QApplication.processEvents()

        assert "/selected/folder" in results

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getExistingDirectory")
    def test_path_changed_signal(self, mock_get_dir, widget):
        """Test path_changed signal emission on browse."""
        mock_get_dir.return_value = "/new/folder"

        picker = FolderPicker(parent=widget)
        results = []

        picker.path_changed.connect(lambda p: results.append(p))
        picker._browse_btn.click()
        QApplication.processEvents()

        assert "/new/folder" in results

    @patch("casare_rpa.presentation.canvas.ui.widgets.primitives.pickers.QFileDialog.getExistingDirectory")
    def test_browse_cancellation(self, mock_get_dir, widget):
        """Test path unchanged when browse cancelled."""
        mock_get_dir.return_value = ""

        picker = FolderPicker(parent=widget)
        picker.set_path("existing/folder")

        picker._browse_btn.click()
        QApplication.processEvents()

        assert picker.get_path() == "existing/folder"

    def test_browse_button_exists(self, widget):
        """Test browse button is present."""
        picker = FolderPicker(parent=widget)
        assert picker._browse_btn is not None

    def test_input_widget_exists(self, widget):
        """Test input widget is present."""
        picker = FolderPicker(parent=widget)
        assert picker._input is not None
        assert isinstance(picker._input, TextInput)


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestFactoryFunctions:
    """Tests for picker factory functions."""

    def test_create_file_picker_default(self, widget):
        """Test create_file_picker with defaults."""
        picker = create_file_picker(parent=widget)
        assert isinstance(picker, FilePicker)
        assert picker._path_type == PathType.FILE

    def test_create_file_picker_with_options(self, widget):
        """Test create_file_picker with custom options."""
        picker = create_file_picker(
            path_type=PathType.SAVE_FILE,
            filter=FileFilter.PDF,
            placeholder="Save PDF...",
            size="lg",
            parent=widget,
        )
        assert picker._path_type == PathType.SAVE_FILE
        assert ".pdf" in picker._filter
        assert picker._size == "lg"

    def test_create_folder_picker_default(self, widget):
        """Test create_folder_picker with defaults."""
        picker = create_folder_picker(parent=widget)
        assert isinstance(picker, FolderPicker)

    def test_create_folder_picker_with_options(self, widget):
        """Test create_folder_picker with custom options."""
        picker = create_folder_picker(
            placeholder="Select output directory...",
            size="sm",
            show_hidden=True,
            parent=widget,
        )
        assert picker._placeholder == "Select output directory..."
        assert picker._size == "sm"
        assert picker._show_hidden

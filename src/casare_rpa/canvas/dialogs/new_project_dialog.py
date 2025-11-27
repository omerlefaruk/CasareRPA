"""
CasareRPA - New Project Dialog
Dialog for creating a new project.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QDialogButtonBox,
    QGroupBox,
)
from PySide6.QtGui import QFont

from ..theme import THEME
from ...utils.config import WORKFLOWS_DIR


def _sanitize_folder_name(name: str) -> str:
    """Convert a name to a valid folder name."""
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    result = name
    for char in invalid_chars:
        result = result.replace(char, "_")
    return result.strip()


class NewProjectDialog(QDialog):
    """
    Dialog for creating a new CasareRPA project.

    Collects:
    - Project name
    - Project description
    - Project location (folder path)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("New Project")
        self.setMinimumWidth(500)
        self.setModal(True)

        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

        # Set default location
        default_path = WORKFLOWS_DIR.parent / "projects"
        default_path.mkdir(parents=True, exist_ok=True)
        self._location_input.setText(str(default_path))

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header = QLabel("Create New Project")
        header.setFont(QFont(header.font().family(), 14, QFont.Bold))
        layout.addWidget(header)

        # Form section
        form_group = QGroupBox("Project Details")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(12)

        # Name input
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("My RPA Project")
        form_layout.addRow("Name:", self._name_input)

        # Description input
        self._description_input = QTextEdit()
        self._description_input.setPlaceholderText("Describe what this project does...")
        self._description_input.setMaximumHeight(80)
        form_layout.addRow("Description:", self._description_input)

        layout.addWidget(form_group)

        # Location section
        location_group = QGroupBox("Location")
        location_layout = QVBoxLayout(location_group)

        # Location row
        location_row = QHBoxLayout()
        self._location_input = QLineEdit()
        self._location_input.setPlaceholderText("Select project folder location...")
        location_row.addWidget(self._location_input, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        location_row.addWidget(browse_btn)

        location_layout.addLayout(location_row)

        # Preview label
        self._preview_label = QLabel("")
        self._preview_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: 11px;"
        )
        location_layout.addWidget(self._preview_label)

        layout.addWidget(location_group)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)

        self._ok_button = button_box.button(QDialogButtonBox.Ok)
        self._ok_button.setText("Create Project")
        self._ok_button.setEnabled(False)

        layout.addWidget(button_box)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self._name_input.textChanged.connect(self._on_input_changed)
        self._location_input.textChanged.connect(self._on_input_changed)

    def _apply_styles(self) -> None:
        """Apply theme styles."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}

            QGroupBox {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: 6px;
                margin-top: 12px;
                padding: 12px;
                font-weight: bold;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {THEME.text_header};
            }}

            QLineEdit, QTextEdit {{
                background: {THEME.bg_darkest};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 8px;
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border-color: {THEME.border_focus};
            }}

            QPushButton {{
                background: {THEME.bg_medium};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }}

            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}

            QPushButton:pressed {{
                background: {THEME.accent_primary};
            }}

            QPushButton:disabled {{
                background: {THEME.bg_dark};
                color: {THEME.text_disabled};
            }}

            QLabel {{
                color: {THEME.text_primary};
            }}
        """)

    def _on_input_changed(self) -> None:
        """Handle input change - validate and update preview."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()

        # Update preview
        if name and location:
            folder_name = _sanitize_folder_name(name)
            full_path = Path(location) / folder_name
            self._preview_label.setText(f"Project will be created at: {full_path}")
        else:
            self._preview_label.setText("")

        # Validate
        is_valid = self._validate()
        self._ok_button.setEnabled(is_valid)

    def _validate(self) -> bool:
        """Validate inputs."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()

        if not name:
            return False

        if not location:
            return False

        # Check location exists
        location_path = Path(location)
        if not location_path.exists():
            return False

        # Check project folder doesn't already exist
        folder_name = _sanitize_folder_name(name)
        project_path = location_path / folder_name
        if project_path.exists():
            self._preview_label.setText(
                f"Warning: Folder already exists: {project_path}"
            )
            self._preview_label.setStyleSheet(
                f"color: {THEME.status_warning}; font-size: 11px;"
            )
            return False

        self._preview_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: 11px;"
        )
        return True

    def _on_browse(self) -> None:
        """Handle browse button click."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Project Location",
            self._location_input.text() or str(WORKFLOWS_DIR.parent),
            QFileDialog.ShowDirsOnly,
        )

        if path:
            self._location_input.setText(path)

    def _on_accept(self) -> None:
        """Handle accept button click."""
        if self._validate():
            self.accept()

    # =========================================================================
    # Public Methods
    # =========================================================================

    def get_name(self) -> str:
        """Get the project name."""
        return self._name_input.text().strip()

    def get_description(self) -> str:
        """Get the project description."""
        return self._description_input.toPlainText().strip()

    def get_path(self) -> Path:
        """Get the full project path."""
        name = self._name_input.text().strip()
        location = self._location_input.text().strip()
        folder_name = _sanitize_folder_name(name)
        return Path(location) / folder_name

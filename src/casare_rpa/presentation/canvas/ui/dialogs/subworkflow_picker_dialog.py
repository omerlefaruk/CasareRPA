"""
Subworkflow Picker Dialog for CasareRPA.

Provides a dialog for selecting subworkflows when configuring CallSubworkflowNode.
Features:
- List of available subworkflows with search/filter
- Preview of input/output ports
- Category filtering
- Recent subworkflows section
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QPushButton,
    QComboBox,
    QFrame,
    QGroupBox,
    QWidget,
)

from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    COLORS,
)


DIALOG_STYLE = f"""
QDialog {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
}}
QListWidget {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
}}
QListWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['border']};
}}
QListWidget::item:selected {{
    background-color: {COLORS['accent']};
}}
QListWidget::item:hover:!selected {{
    background-color: {COLORS['bg_hover']};
}}
QLineEdit {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    color: {COLORS['text_primary']};
}}
QLineEdit:focus {{
    border-color: {COLORS['accent']};
}}
QComboBox {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px;
    color: {COLORS['text_primary']};
    min-width: 150px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    selection-background-color: {COLORS['accent']};
}}
QGroupBox {{
    font-weight: bold;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    margin-top: 8px;
    padding: 8px;
    color: {COLORS['text_primary']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 4px;
    left: 8px;
}}
QLabel {{
    color: {COLORS['text_primary']};
}}
QLabel[type="title"] {{
    font-size: 14px;
    font-weight: bold;
}}
QLabel[type="subtitle"] {{
    font-size: 12px;
    color: {COLORS['text_secondary']};
}}
QLabel[type="port-input"] {{
    color: #4ec9b0;
}}
QLabel[type="port-output"] {{
    color: #dcdcaa;
}}
QPushButton {{
    background-color: {COLORS['bg_secondary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 8px 16px;
    color: {COLORS['text_primary']};
    min-width: 80px;
}}
QPushButton:hover {{
    background-color: {COLORS['bg_hover']};
    border-color: {COLORS['accent']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent']};
}}
QPushButton[type="primary"] {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
    color: white;
}}
QPushButton[type="primary"]:hover {{
    background-color: #0078d4;
}}
"""


class SubworkflowListItem(QListWidgetItem):
    """Custom list item for subworkflow display."""

    def __init__(self, subflow_data: Dict[str, Any]) -> None:
        super().__init__()
        self.subflow_data = subflow_data
        self.id = subflow_data.get("id", "")
        self.name = subflow_data.get("name", "Unnamed")
        self.category = subflow_data.get("category", "General")
        self.description = subflow_data.get("description", "")
        self.path = subflow_data.get("path", "")
        self.inputs = subflow_data.get("inputs", [])
        self.outputs = subflow_data.get("outputs", [])

        self.setText(self.name)
        self.setToolTip(self.description or f"Category: {self.category}")
        self.setData(Qt.ItemDataRole.UserRole, subflow_data)


class PortPreviewWidget(QWidget):
    """Widget showing port preview for a subworkflow."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Inputs section
        inputs_group = QGroupBox("Inputs")
        self._inputs_layout = QVBoxLayout(inputs_group)
        self._inputs_layout.setSpacing(4)
        layout.addWidget(inputs_group)

        # Outputs section
        outputs_group = QGroupBox("Outputs")
        self._outputs_layout = QVBoxLayout(outputs_group)
        self._outputs_layout.setSpacing(4)
        layout.addWidget(outputs_group)

        layout.addStretch()

    def set_ports(self, inputs: List[Dict], outputs: List[Dict]) -> None:
        """Update port preview."""
        # Clear existing
        self._clear_layout(self._inputs_layout)
        self._clear_layout(self._outputs_layout)

        # Add inputs
        if inputs:
            for port in inputs:
                label = QLabel(f"  {port.get('name', 'unnamed')}  ({port.get('data_type', 'ANY')})")
                label.setProperty("type", "port-input")
                required = port.get("required", False)
                if required:
                    label.setStyleSheet("color: #4ec9b0; font-weight: bold;")
                else:
                    label.setStyleSheet("color: #4ec9b0;")
                self._inputs_layout.addWidget(label)
        else:
            self._inputs_layout.addWidget(QLabel("  No inputs"))

        # Add outputs
        if outputs:
            for port in outputs:
                label = QLabel(f"  {port.get('name', 'unnamed')}  ({port.get('data_type', 'ANY')})")
                label.setProperty("type", "port-output")
                label.setStyleSheet("color: #dcdcaa;")
                self._outputs_layout.addWidget(label)
        else:
            self._outputs_layout.addWidget(QLabel("  No outputs"))

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class SubworkflowPickerDialog(QDialog):
    """
    Dialog for selecting a subworkflow.

    Features:
    - List of available subworkflows
    - Search/filter functionality
    - Category filtering
    - Port preview
    - Double-click to select
    """

    subflow_selected = Signal(dict)  # Emits selected subflow data

    def __init__(
        self,
        subflows: Optional[List[Dict]] = None,
        loader: Optional[Callable[[], List[Dict]]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize dialog.

        Args:
            subflows: List of subflow data dicts (if None, uses loader)
            loader: Callable that returns list of subflow dicts
            parent: Parent widget
        """
        super().__init__(parent)
        self._subflows = subflows or []
        self._loader = loader
        self._selected_subflow: Optional[Dict] = None
        self._categories: List[str] = []

        self._setup_ui()
        self._connect_signals()
        self._load_subflows()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Select Subworkflow")
        self.setMinimumSize(700, 500)
        self.setStyleSheet(DIALOG_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("Select a Subworkflow")
        header.setProperty("type", "title")
        layout.addWidget(header)

        # Search and filter bar
        filter_layout = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search subworkflows...")
        self._search_edit.setClearButtonEnabled(True)
        filter_layout.addWidget(self._search_edit, 1)

        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories")
        filter_layout.addWidget(self._category_combo)

        self._refresh_btn = QPushButton("Refresh")
        filter_layout.addWidget(self._refresh_btn)

        layout.addLayout(filter_layout)

        # Main splitter (list + preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Subflow list
        self._list_widget = QListWidget()
        self._list_widget.setMinimumWidth(300)
        splitter.addWidget(self._list_widget)

        # Preview panel
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(8, 8, 8, 8)

        self._preview_title = QLabel("Select a subworkflow")
        self._preview_title.setProperty("type", "title")
        preview_layout.addWidget(self._preview_title)

        self._preview_description = QLabel("")
        self._preview_description.setProperty("type", "subtitle")
        self._preview_description.setWordWrap(True)
        preview_layout.addWidget(self._preview_description)

        # Port preview
        self._port_preview = PortPreviewWidget()
        preview_layout.addWidget(self._port_preview)

        # Path info
        self._path_label = QLabel("")
        self._path_label.setProperty("type", "subtitle")
        self._path_label.setWordWrap(True)
        preview_layout.addWidget(self._path_label)

        preview_layout.addStretch()

        splitter.addWidget(preview_frame)
        splitter.setSizes([350, 350])

        layout.addWidget(splitter, 1)

        # Button bar
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self._cancel_btn)

        self._select_btn = QPushButton("Select")
        self._select_btn.setProperty("type", "primary")
        self._select_btn.setEnabled(False)
        button_layout.addWidget(self._select_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        self._search_edit.textChanged.connect(self._filter_list)
        self._category_combo.currentTextChanged.connect(self._filter_list)
        self._refresh_btn.clicked.connect(self._load_subflows)
        self._list_widget.currentItemChanged.connect(self._on_selection_changed)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._cancel_btn.clicked.connect(self.reject)
        self._select_btn.clicked.connect(self._on_select)

    def _load_subflows(self) -> None:
        """Load subflows from loader or scan filesystem."""
        if self._loader:
            try:
                self._subflows = self._loader()
            except Exception as e:
                logger.error(f"Failed to load subflows: {e}")
                self._subflows = []
        elif not self._subflows:
            self._subflows = self._scan_subflows()

        # Extract categories
        self._categories = sorted(set(sf.get("category", "General") for sf in self._subflows))

        # Update category combo
        self._category_combo.clear()
        self._category_combo.addItem("All Categories")
        for cat in self._categories:
            self._category_combo.addItem(cat)

        self._populate_list()

    def _scan_subflows(self) -> List[Dict]:
        """Scan filesystem for subflow files."""
        subflows = []

        # Try common locations
        search_paths = [
            Path.cwd() / "workflows" / "subflows",
            Path.home() / ".casare_rpa" / "subflows",
        ]

        for search_path in search_paths:
            if not search_path.exists():
                continue

            for filepath in search_path.glob("*.json"):
                try:
                    from casare_rpa.domain.entities.subflow import Subflow

                    subflow = Subflow.load_from_file(str(filepath))
                    subflows.append(
                        {
                            "id": subflow.id,
                            "name": subflow.name,
                            "description": subflow.description,
                            "category": subflow.category,
                            "path": str(filepath),
                            "inputs": [
                                {
                                    "name": p.name,
                                    "data_type": p.data_type.name
                                    if hasattr(p.data_type, "name")
                                    else str(p.data_type),
                                    "required": p.required,
                                }
                                for p in subflow.inputs
                            ],
                            "outputs": [
                                {
                                    "name": p.name,
                                    "data_type": p.data_type.name
                                    if hasattr(p.data_type, "name")
                                    else str(p.data_type),
                                }
                                for p in subflow.outputs
                            ],
                        }
                    )
                except Exception as e:
                    logger.debug(f"Could not load subflow {filepath}: {e}")

        return subflows

    def _populate_list(self) -> None:
        """Populate list with subflows."""
        self._list_widget.clear()

        for sf_data in self._subflows:
            item = SubworkflowListItem(sf_data)
            self._list_widget.addItem(item)

        self._filter_list()

    def _filter_list(self) -> None:
        """Filter list based on search and category."""
        search_text = self._search_edit.text().lower()
        category = self._category_combo.currentText()

        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if not isinstance(item, SubworkflowListItem):
                continue

            # Category filter
            if category != "All Categories" and item.category != category:
                item.setHidden(True)
                continue

            # Search filter
            if search_text:
                matches = (
                    search_text in item.name.lower()
                    or search_text in item.description.lower()
                    or search_text in item.category.lower()
                )
                item.setHidden(not matches)
            else:
                item.setHidden(False)

    def _on_selection_changed(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Handle selection change."""
        if not current or not isinstance(current, SubworkflowListItem):
            self._select_btn.setEnabled(False)
            self._preview_title.setText("Select a subworkflow")
            self._preview_description.setText("")
            self._port_preview.set_ports([], [])
            self._path_label.setText("")
            return

        self._selected_subflow = current.subflow_data
        self._select_btn.setEnabled(True)

        # Update preview
        self._preview_title.setText(current.name)
        self._preview_description.setText(current.description or "No description")
        self._port_preview.set_ports(current.inputs, current.outputs)
        self._path_label.setText(f"Path: {current.path}")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click to select."""
        if isinstance(item, SubworkflowListItem):
            self._selected_subflow = item.subflow_data
            self.accept()

    def _on_select(self) -> None:
        """Handle select button click."""
        if self._selected_subflow:
            self.accept()

    def get_selected_subflow(self) -> Optional[Dict]:
        """Get the selected subflow data."""
        return self._selected_subflow


def show_subworkflow_picker(
    subflows: Optional[List[Dict]] = None,
    loader: Optional[Callable[[], List[Dict]]] = None,
    parent: Optional[QWidget] = None,
) -> Optional[Dict]:
    """
    Show subworkflow picker dialog.

    Args:
        subflows: List of subflow data dicts
        loader: Callable that returns list of subflow dicts
        parent: Parent widget

    Returns:
        Selected subflow data dict, or None if cancelled
    """
    dialog = SubworkflowPickerDialog(subflows, loader, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_selected_subflow()
    return None


__all__ = [
    "SubworkflowPickerDialog",
    "show_subworkflow_picker",
]

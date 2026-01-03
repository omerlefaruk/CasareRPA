"""
Subworkflow Picker Dialog for CasareRPA.

Provides a dialog for selecting subworkflows when configuring CallSubworkflowNode.
Features:
- List of available subworkflows with search/filter
- Preview of input/output ports
- Category filtering
- Recent subworkflows section

Epic 7.x migration: Converted to use BaseDialogV2 and THEME_V2/TOKENS_V2.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton


class SubworkflowListItem(QListWidgetItem):
    """Custom list item for subworkflow display."""

    def __init__(self, subflow_data: dict[str, Any]) -> None:
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Inputs section
        inputs_group = QGroupBox("Inputs")
        self._apply_group_style(inputs_group)
        self._inputs_layout = QVBoxLayout(inputs_group)
        self._inputs_layout.setSpacing(TOKENS_V2.spacing.xs)
        layout.addWidget(inputs_group)

        # Outputs section
        outputs_group = QGroupBox("Outputs")
        self._apply_group_style(outputs_group)
        self._outputs_layout = QVBoxLayout(outputs_group)
        self._outputs_layout.setSpacing(TOKENS_V2.spacing.xs)
        layout.addWidget(outputs_group)

        layout.addStretch()

    def _apply_group_style(self, widget: QGroupBox) -> None:
        """Apply v2 styling to group box."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {tok.typography.weight_medium};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                margin-top: {tok.spacing.xs}px;
                padding-top: {tok.spacing.xs}px;
                background: {t.bg_surface};
                color: {t.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tok.spacing.sm}px;
                padding: 0 {tok.spacing.xs}px;
                color: {t.text_primary};
            }}
        """)

    def set_ports(self, inputs: list[dict], outputs: list[dict]) -> None:
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
                weight = (
                    TOKENS_V2.typography.weight_semibold
                    if required
                    else TOKENS_V2.typography.weight_normal
                )
                label.setStyleSheet(
                    f"color: {THEME_V2.success}; font-weight: {weight}; font-size: {TOKENS_V2.typography.body}px;"
                )
                self._inputs_layout.addWidget(label)
        else:
            label = QLabel("  No inputs")
            label.setStyleSheet(
                f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body_sm}px;"
            )
            self._inputs_layout.addWidget(label)

        # Add outputs
        if outputs:
            for port in outputs:
                label = QLabel(f"  {port.get('name', 'unnamed')}  ({port.get('data_type', 'ANY')})")
                label.setProperty("type", "port-output")
                label.setStyleSheet(
                    f"color: {THEME_V2.info}; font-size: {TOKENS_V2.typography.body}px;"
                )
                self._outputs_layout.addWidget(label)
        else:
            label = QLabel("  No outputs")
            label.setStyleSheet(
                f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body_sm}px;"
            )
            self._outputs_layout.addWidget(label)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class SubworkflowPickerDialog(BaseDialogV2):
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
        subflows: list[dict] | None = None,
        loader: Callable[[], list[dict]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize dialog.

        Args:
            subflows: List of subflow data dicts (if None, uses loader)
            loader: Callable that returns list of subflow dicts
            parent: Parent widget
        """
        super().__init__(
            title="Select Subworkflow",
            parent=parent,
            size=DialogSizeV2.LG,
            resizable=True,
        )
        self._subflows = subflows or []
        self._loader = loader
        self._selected_subflow: dict | None = None
        self._categories: list[str] = []

        self._setup_ui()
        self._connect_signals()
        self._load_subflows()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        # Main content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Header
        header = QLabel("Select a Subworkflow")
        header.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.heading_lg}px; font-weight: {TOKENS_V2.typography.weight_semibold}; color: {THEME_V2.text_primary};"
        )
        layout.addWidget(header)

        # Search and filter bar
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(TOKENS_V2.spacing.sm)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search subworkflows...")
        self._apply_input_style(self._search_edit)
        filter_layout.addWidget(self._search_edit, 1)

        self._category_combo = QComboBox()
        self._category_combo.addItem("All Categories")
        self._apply_combo_style(self._category_combo)
        filter_layout.addWidget(self._category_combo)

        self._refresh_btn = PushButton(text="Refresh", variant="secondary", size="md")
        filter_layout.addWidget(self._refresh_btn)

        layout.addLayout(filter_layout)

        # Main splitter (list + preview)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Subflow list
        self._list_widget = QListWidget()
        self._list_widget.setMinimumWidth(300)
        self._apply_list_style(self._list_widget)
        splitter.addWidget(self._list_widget)

        # Preview panel
        preview_frame = QFrame()
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(
            TOKENS_V2.spacing.sm, TOKENS_V2.spacing.sm, TOKENS_V2.spacing.sm, TOKENS_V2.spacing.sm
        )
        preview_layout.setSpacing(TOKENS_V2.spacing.sm)

        self._preview_title = QLabel("Select a subworkflow")
        self._preview_title.setStyleSheet(
            f"font-size: {TOKENS_V2.typography.heading_md}px; font-weight: {TOKENS_V2.typography.weight_semibold}; color: {THEME_V2.text_primary};"
        )
        preview_layout.addWidget(self._preview_title)

        self._preview_description = QLabel("")
        self._preview_description.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body_sm}px;"
        )
        self._preview_description.setWordWrap(True)
        preview_layout.addWidget(self._preview_description)

        # Port preview
        self._port_preview = PortPreviewWidget()
        preview_layout.addWidget(self._port_preview)

        # Path info
        self._path_label = QLabel("")
        self._path_label.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.caption}px;"
        )
        self._path_label.setWordWrap(True)
        preview_layout.addWidget(self._path_label)

        preview_layout.addStretch()

        splitter.addWidget(preview_frame)
        splitter.setSizes([350, 350])

        layout.addWidget(splitter, 1)

        # Set as body widget
        self.set_body_widget(content)

        # Setup footer buttons
        self._select_btn = self.set_primary_button("Select", self._on_select)
        self._select_btn.setEnabled(False)
        self.set_secondary_button("Cancel", self.reject)

    @Slot()
    def _connect_signals(self) -> None:
        """Connect signals."""
        self._search_edit.textChanged.connect(self._filter_list)
        self._category_combo.currentTextChanged.connect(self._filter_list)
        self._refresh_btn.clicked.connect(self._load_subflows)
        self._list_widget.currentItemChanged.connect(self._on_selection_changed)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

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

    def _scan_subflows(self) -> list[dict]:
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

    @Slot()
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

    @Slot()
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click to select."""
        if isinstance(item, SubworkflowListItem):
            self._selected_subflow = item.subflow_data
            self.accept()

    @Slot()
    def _on_select(self) -> None:
        """Handle select button click."""
        if self._selected_subflow:
            self.accept()

    def get_selected_subflow(self) -> dict | None:
        """Get the selected subflow data."""
        return self._selected_subflow

    # ========================================================================
    # WIDGET STYLING HELPERS (using THEME_V2/TOKENS_V2)
    # ========================================================================

    def _apply_input_style(self, widget: QLineEdit) -> None:
        """Apply v2 input styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QLineEdit {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                min-height: {tok.sizes.input_md}px;
            }}
            QLineEdit:focus {{
                border-color: {t.border_focus};
            }}
        """)

    def _apply_combo_style(self, widget: QComboBox) -> None:
        """Apply v2 combo box styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QComboBox {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                min-height: {tok.sizes.input_md}px;
                min-width: 150px;
            }}
            QComboBox:focus {{
                border-color: {t.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t.bg_elevated};
                border: 1px solid {t.border};
                selection-background-color: {t.bg_selected};
                color: {t.text_primary};
            }}
        """)

    def _apply_list_style(self, widget: QListWidget) -> None:
        """Apply v2 list widget styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {t.bg_surface};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                outline: none;
                font-family: {tok.typography.family};
                font-size: {tok.typography.body}px;
            }}
            QListWidget::item {{
                padding: {tok.spacing.sm}px;
                border-bottom: 1px solid {t.border};
                color: {t.text_primary};
            }}
            QListWidget::item:selected {{
                background-color: {t.bg_selected};
                color: {t.text_primary};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {t.bg_hover};
            }}
        """)


def show_subworkflow_picker(
    subflows: list[dict] | None = None,
    loader: Callable[[], list[dict]] | None = None,
    parent: QWidget | None = None,
) -> dict | None:
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
    if dialog.exec() == BaseDialogV2.DialogCode.Accepted:
        return dialog.get_selected_subflow()
    return None


__all__ = [
    "SubworkflowPickerDialog",
    "show_subworkflow_picker",
]


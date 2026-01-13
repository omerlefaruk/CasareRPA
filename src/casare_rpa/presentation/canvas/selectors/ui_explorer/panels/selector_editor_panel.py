"""
Selector Editor Panel for UI Explorer.

Displays all element attributes with checkboxes for include/exclude.
Syncs with SelectorModel for state management.
"""

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget)

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.selector_model import (
    SelectorAttribute,
    SelectorModel)
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.attribute_row import (
    AttributeRow)


class SelectorEditorPanel(QFrame):
    """
    Selector Attribute Editor Panel.

    Displays all element attributes with checkboxes.
    Features:
    - Scrollable list of AttributeRow widgets
    - Include All / Minimum buttons
    - Syncs with SelectorModel

    Signals:
        attribute_toggled: Emitted when any attribute checkbox is toggled
    """

    attribute_toggled = Signal(str, bool)  # attribute_name, is_checked

    def __init__(
        self,
        model: SelectorModel | None = None,
        parent: QWidget | None = None) -> None:
        """
        Initialize the selector editor panel.

        Args:
            model: SelectorModel to sync with (can be set later)
            parent: Parent widget
        """
        super().__init__(parent)

        self._model = model
        self._attribute_rows: dict[str, AttributeRow] = {}

        self._setup_ui()
        self._apply_styles()

        # Connect to model if provided
        if model:
            self.set_model(model)

    def _setup_ui(self) -> None:
        """Build the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 4)
        header.setSpacing(8)

        # Title
        title_label = QLabel("SELECTOR ATTRIBUTES")
        title_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        header.addWidget(title_label)
        header.addStretch()

        # Action buttons
        self._include_all_btn = QPushButton("All")
        self._include_all_btn.setFixedSize(40, 22)
        self._include_all_btn.setToolTip("Include all non-empty attributes")
        self._include_all_btn.clicked.connect(self._on_include_all)
        header.addWidget(self._include_all_btn)

        self._include_min_btn = QPushButton("Min")
        self._include_min_btn.setFixedSize(40, 22)
        self._include_min_btn.setToolTip("Include only essential attributes")
        self._include_min_btn.clicked.connect(self._on_include_minimum)
        header.addWidget(self._include_min_btn)

        layout.addLayout(header)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #3a3a3a; max-height: 1px;")
        layout.addWidget(separator)

        # Scroll area for attribute rows
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Container for rows
        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 4, 0, 4)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch()  # Push rows to top

        self._scroll_area.setWidget(self._rows_container)
        layout.addWidget(self._scroll_area, 1)

        # Footer with count
        footer = QHBoxLayout()
        footer.setContentsMargins(8, 4, 8, 8)

        self._count_label = QLabel("0 attributes")
        self._count_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 10px;
            }
        """)
        footer.addWidget(self._count_label)
        footer.addStretch()

        self._selected_count_label = QLabel("0 selected")
        self._selected_count_label.setStyleSheet("""
            QLabel {
                color: #60a5fa;
                font-size: 10px;
            }
        """)
        footer.addWidget(self._selected_count_label)

        layout.addLayout(footer)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            SelectorEditorPanel {
                background: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
        """)

        button_style = """
            QPushButton {
                background: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                color: #e0e0e0;
                font-size: 10px;
                padding: 2px 6px;
            }
            QPushButton:hover {
                background: #3a3a3a;
            }
            QPushButton:pressed {
                background: #252525;
            }
        """
        self._include_all_btn.setStyleSheet(button_style)
        self._include_min_btn.setStyleSheet(button_style)

        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self._rows_container.setStyleSheet("background: transparent;")

    def set_model(self, model: SelectorModel) -> None:
        """
        Set the selector model to sync with.

        Args:
            model: SelectorModel instance
        """
        # Disconnect from old model (suppress warnings with filterwarnings)
        if self._model:
            import warnings

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    self._model.changed.disconnect(self._on_model_changed)
                except (RuntimeError, TypeError):
                    pass
                try:
                    self._model.attribute_toggled.disconnect(self._on_model_attribute_toggled)
                except (RuntimeError, TypeError):
                    pass

        self._model = model

        # Connect to new model
        if model:
            model.changed.connect(self._on_model_changed)
            model.attribute_toggled.connect(self._on_model_attribute_toggled)

            # Initial load
            self._refresh_from_model()

    def get_model(self) -> SelectorModel | None:
        """Get the current model."""
        return self._model

    def clear(self) -> None:
        """Clear all attribute rows."""
        # Remove all rows except the stretch
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._attribute_rows.clear()
        self._update_counts()

    def get_checked_attributes(self) -> list[str]:
        """
        Get list of checked attribute names.

        Returns:
            List of attribute names that are checked
        """
        return [name for name, row in self._attribute_rows.items() if row.is_checked]

    def _refresh_from_model(self) -> None:
        """Refresh rows from current model state."""
        self.clear()

        if not self._model:
            return

        # Create rows for each attribute
        for attr in self._model.attributes:
            self._add_attribute_row(attr)

        self._update_counts()

    def _add_attribute_row(self, attribute: SelectorAttribute) -> None:
        """
        Add a row for an attribute.

        Args:
            attribute: SelectorAttribute to display
        """
        row = AttributeRow(attribute)
        row.toggled.connect(self._on_row_toggled)

        # Insert before the stretch
        insert_idx = self._rows_layout.count() - 1
        self._rows_layout.insertWidget(insert_idx, row)

        self._attribute_rows[attribute.name] = row

    def _update_counts(self) -> None:
        """Update the count labels."""
        total = len(self._attribute_rows)
        selected = sum(1 for row in self._attribute_rows.values() if row.is_checked)

        self._count_label.setText(f"{total} attribute{'s' if total != 1 else ''}")
        self._selected_count_label.setText(f"{selected} selected")

    def _on_row_toggled(self, name: str, is_checked: bool) -> None:
        """Handle row checkbox toggle."""
        # Update model
        if self._model:
            self._model.set_attribute_included(name, is_checked)

        # Update counts
        self._update_counts()

        # Emit signal
        self.attribute_toggled.emit(name, is_checked)

    def _on_model_changed(self) -> None:
        """Handle model changed signal."""
        self._refresh_from_model()

    def _on_model_attribute_toggled(self, name: str, included: bool) -> None:
        """Handle model attribute toggled signal."""
        if name in self._attribute_rows:
            row = self._attribute_rows[name]
            if row.is_checked != included:
                row.set_checked(included)
        self._update_counts()

    def _on_include_all(self) -> None:
        """Handle Include All button."""
        if self._model:
            self._model.include_all()
        else:
            # Fallback: check all rows
            for row in self._attribute_rows.values():
                row.set_checked(True)
        self._update_counts()
        logger.debug("Selector Editor: Include all clicked")

    def _on_include_minimum(self) -> None:
        """Handle Include Minimum button."""
        if self._model:
            self._model.include_minimum()
        else:
            # Fallback: uncheck all except required
            for row in self._attribute_rows.values():
                row.set_checked(row.attribute.required)
        self._update_counts()
        logger.debug("Selector Editor: Include minimum clicked")

    def set_attribute_checked(self, name: str, checked: bool) -> None:
        """
        Set a specific attribute's checked state.

        Args:
            name: Attribute name
            checked: Whether to check it
        """
        if name in self._attribute_rows:
            self._attribute_rows[name].set_checked(checked)
            self._update_counts()

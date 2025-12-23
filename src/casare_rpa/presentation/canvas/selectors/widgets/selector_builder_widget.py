"""
Selector Builder Widget for Element Selector Dialog.

Shows attribute rows with checkboxes and score bars.
User toggles attributes to include in generated selector.
Provides live validation with debouncing.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, List, Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.state.selector_state import (
    AttributeRow,
    ValidationStatus,
)

if TYPE_CHECKING:
    pass


class ScoreBar(QProgressBar):
    """
    Visual score bar with color coding.

    Colors:
    - Green (#10b981): 80-100 (high reliability)
    - Yellow (#fbbf24): 60-79 (medium reliability)
    - Red (#ef4444): 0-59 (low reliability)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setRange(0, 100)
        self.setValue(0)
        self.setTextVisible(True)
        self.setFormat("%v")
        self.setFixedWidth(60)
        self.setFixedHeight(16)
        self._update_style(0)

    def set_score(self, score: float) -> None:
        """Set score value and update color."""
        value = int(min(100, max(0, score)))
        self.setValue(value)
        self._update_style(value)

    def _update_style(self, value: int) -> None:
        """Update style based on score value."""
        if value >= 80:
            color = "#10b981"  # Green
            bg = "#1a3d2e"
        elif value >= 60:
            color = "#fbbf24"  # Yellow
            bg = "#3d3520"
        else:
            color = "#ef4444"  # Red
            bg = "#3d1e1e"

        self.setStyleSheet(f"""
            QProgressBar {{
                background: {bg};
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                text-align: center;
                color: {color};
                font-size: 10px;
                font-weight: bold;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 2px;
            }}
        """)


class AttributeRowWidget(QWidget):
    """
    Single attribute row in the selector builder.

    Layout:
    [x] id="submit"                    [=======95]
    ^checkbox  ^attribute info          ^score bar

    Signals:
        toggled: Emitted when checkbox is toggled (row_index, enabled)
        value_changed: Emitted when value is edited (row_index, new_value)
    """

    toggled = Signal(int, bool)
    value_changed = Signal(int, str)

    def __init__(
        self,
        row_index: int,
        attribute: AttributeRow,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._row_index = row_index
        self._attribute = attribute
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build row UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Checkbox
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._attribute.enabled)
        self._checkbox.toggled.connect(self._on_toggled)
        self._checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._checkbox)

        # Attribute name
        self._name_label = QLabel(self._attribute.name)
        self._name_label.setFixedWidth(80)
        self._name_label.setStyleSheet("color: #22d3ee; font-weight: bold; font-size: 11px;")
        layout.addWidget(self._name_label)

        # Equals sign
        equals = QLabel("=")
        equals.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(equals)

        # Attribute value (truncated display)
        value = self._attribute.value
        if len(value) > 40:
            value = value[:37] + "..."
        self._value_label = QLabel(f'"{value}"')
        self._value_label.setStyleSheet("color: #fb923c; font-family: Consolas; font-size: 11px;")
        self._value_label.setToolTip(self._attribute.value)
        layout.addWidget(self._value_label, 1)

        # Score bar
        self._score_bar = ScoreBar()
        self._score_bar.set_score(self._attribute.score)
        layout.addWidget(self._score_bar)

        # Update enabled state
        self._update_enabled_state()

    def _on_toggled(self, checked: bool) -> None:
        """Handle checkbox toggle."""
        self._attribute.enabled = checked
        self._update_enabled_state()
        self.toggled.emit(self._row_index, checked)

    def _update_enabled_state(self) -> None:
        """Update visual state based on enabled."""
        opacity = 1.0 if self._attribute.enabled else 0.5
        self._name_label.setStyleSheet(
            f"color: #22d3ee; font-weight: bold; font-size: 11px; opacity: {opacity};"
        )
        self._value_label.setStyleSheet(
            f"color: #fb923c; font-family: Consolas; font-size: 11px; opacity: {opacity};"
        )

    def set_attribute(self, attribute: AttributeRow) -> None:
        """Update attribute data."""
        self._attribute = attribute
        self._checkbox.setChecked(attribute.enabled)
        self._name_label.setText(attribute.name)

        value = attribute.value
        if len(value) > 40:
            value = value[:37] + "..."
        self._value_label.setText(f'"{value}"')
        self._value_label.setToolTip(attribute.value)

        self._score_bar.set_score(attribute.score)
        self._update_enabled_state()


class SelectorBuilderWidget(QWidget):
    """
    Widget for building selectors from element attributes.

    Layout:
    +---------------------------------------------------------------+
    | [x] id         submit                        Score: 95        |
    | [x] class      btn-primary                   Score: 70        |
    | [ ] text       Submit                        Score: 60        |
    | [ ] xpath      //button[@id='submit']        Score: 90        |
    +---------------------------------------------------------------+
    | Generated: #submit.btn-primary               Matches: 1       |
    +---------------------------------------------------------------+

    Signals:
        selector_changed: Generated selector changed
        validate_requested: User manually requested validation
        attribute_toggled: User toggled an attribute (index, enabled)
    """

    selector_changed = Signal(str, str)  # selector, selector_type
    validate_requested = Signal(str)  # selector
    attribute_toggled = Signal(int, bool)  # index, enabled

    def __init__(
        self,
        parent: QWidget | None = None,
        validate_callback: Callable | None = None,
    ) -> None:
        super().__init__(parent)
        self._validate_callback = validate_callback
        self._attribute_rows: list[AttributeRow] = []
        self._row_widgets: list[AttributeRowWidget] = []

        # Debounce timer for validation
        self._validation_timer = QTimer(self)
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._do_validate)
        self._validation_delay_ms = 300

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Selector Builder")
        title.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
        header.addWidget(title)

        header.addStretch()

        # Info label
        self._info_label = QLabel("Toggle attributes to include in selector")
        self._info_label.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(self._info_label)

        layout.addLayout(header)

        # Scroll area for attribute rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(200)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                background: #1e1e1e;
            }
        """)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(2)
        self._rows_layout.addStretch()

        scroll.setWidget(self._rows_container)
        layout.addWidget(scroll)

        # Generated selector section
        generated_frame = QFrame()
        generated_frame.setStyleSheet("""
            QFrame {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)

        generated_layout = QVBoxLayout(generated_frame)
        generated_layout.setContentsMargins(12, 8, 12, 8)
        generated_layout.setSpacing(8)

        # Selector type and label
        selector_header = QHBoxLayout()

        selector_label = QLabel("Generated:")
        selector_label.setStyleSheet("color: #888; font-size: 11px;")
        selector_header.addWidget(selector_label)

        self._selector_type_label = QLabel("CSS")
        self._selector_type_label.setStyleSheet(
            "color: #60a5fa; font-size: 10px; background: #1e3a5f; "
            "padding: 2px 6px; border-radius: 3px;"
        )
        selector_header.addWidget(self._selector_type_label)

        selector_header.addStretch()

        # Match count badge
        self._match_badge = QLabel("Matches: -")
        self._match_badge.setStyleSheet(
            "color: #888; font-size: 11px; background: #3a3a3a; "
            "padding: 2px 8px; border-radius: 3px;"
        )
        selector_header.addWidget(self._match_badge)

        generated_layout.addLayout(selector_header)

        # Editable selector input
        selector_row = QHBoxLayout()
        selector_row.setSpacing(8)

        self._selector_input = QLineEdit()
        self._selector_input.setFont(QFont("Consolas", 11))
        self._selector_input.setPlaceholderText("(select attributes above)")
        self._selector_input.textChanged.connect(self._on_selector_changed)
        self._selector_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                color: #60a5fa;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        selector_row.addWidget(self._selector_input, 1)

        # Validate button
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setFixedHeight(32)
        self._validate_btn.clicked.connect(self._on_validate_clicked)
        self._validate_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #e0e0e0;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        selector_row.addWidget(self._validate_btn)

        generated_layout.addLayout(selector_row)

        # Validation status
        self._validation_status = QLabel("")
        self._validation_status.setStyleSheet("font-size: 11px;")
        self._validation_status.setVisible(False)
        generated_layout.addWidget(self._validation_status)

        layout.addWidget(generated_frame)

        # Empty state
        self._empty_state = QLabel("Pick an element to see available selectors")
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setStyleSheet("color: #666; font-size: 11px; padding: 20px;")
        self._empty_state.setVisible(True)
        layout.addWidget(self._empty_state)

    def set_attributes(self, attributes: list[AttributeRow]) -> None:
        """Set attribute rows."""
        self._attribute_rows = attributes

        # Clear existing row widgets
        for widget in self._row_widgets:
            widget.deleteLater()
        self._row_widgets.clear()

        # Remove stretch
        while self._rows_layout.count() > 0:
            item = self._rows_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new rows
        for i, attr in enumerate(attributes):
            row_widget = AttributeRowWidget(i, attr)
            row_widget.toggled.connect(self._on_attribute_toggled)
            self._rows_layout.addWidget(row_widget)
            self._row_widgets.append(row_widget)

        self._rows_layout.addStretch()

        # Update empty state
        self._empty_state.setVisible(len(attributes) == 0)

        # Generate selector from enabled attributes
        self._regenerate_selector()

    def _on_attribute_toggled(self, index: int, enabled: bool) -> None:
        """Handle attribute toggle."""
        if 0 <= index < len(self._attribute_rows):
            self._attribute_rows[index].enabled = enabled
            self.attribute_toggled.emit(index, enabled)
            self._regenerate_selector()

    def _regenerate_selector(self) -> None:
        """Regenerate selector from enabled attributes."""
        enabled = [row for row in self._attribute_rows if row.enabled]

        if not enabled:
            self._selector_input.setText("")
            return

        # Build selector based on highest score enabled attribute
        best = max(enabled, key=lambda r: r.score)

        # Use value directly as selector
        selector = best.value
        selector_type = best.selector_type

        self._selector_input.setText(selector)
        self._selector_type_label.setText(selector_type.upper())

        # Trigger debounced validation
        self._validation_timer.start(self._validation_delay_ms)

    def _on_selector_changed(self, selector: str) -> None:
        """Handle selector text change."""
        self.selector_changed.emit(selector, "css")
        # Restart validation timer
        self._validation_timer.start(self._validation_delay_ms)

    def _on_validate_clicked(self) -> None:
        """Handle validate button click."""
        selector = self._selector_input.text().strip()
        if selector:
            self.validate_requested.emit(selector)
            self._do_validate()

    def _do_validate(self) -> None:
        """Perform validation (debounced)."""
        selector = self._selector_input.text().strip()
        if not selector or not self._validate_callback:
            return

        # Callback is expected to be async, will be handled by dialog
        # Just emit signal for now
        self.validate_requested.emit(selector)

    def set_validation_result(
        self,
        status: ValidationStatus,
        match_count: int = 0,
        time_ms: float = 0.0,
    ) -> None:
        """Update validation display."""
        self._validation_status.setVisible(True)

        if status == ValidationStatus.VALIDATING:
            self._match_badge.setText("Validating...")
            self._match_badge.setStyleSheet(
                "color: #60a5fa; font-size: 11px; background: #1e3a5f; "
                "padding: 2px 8px; border-radius: 3px;"
            )
            self._validation_status.setText("Validating...")
            self._validation_status.setStyleSheet("color: #60a5fa; font-size: 11px;")

        elif status == ValidationStatus.VALID:
            if match_count == 1:
                self._match_badge.setText("Matches: 1")
                self._match_badge.setStyleSheet(
                    "color: #10b981; font-size: 11px; background: #1a3d2e; "
                    "padding: 2px 8px; border-radius: 3px;"
                )
                self._validation_status.setText(f"Found 1 unique element ({time_ms:.1f}ms)")
                self._validation_status.setStyleSheet("color: #10b981; font-size: 11px;")
            else:
                self._match_badge.setText(f"Matches: {match_count}")
                self._match_badge.setStyleSheet(
                    "color: #fbbf24; font-size: 11px; background: #3d3520; "
                    "padding: 2px 8px; border-radius: 3px;"
                )
                self._validation_status.setText(
                    f"Found {match_count} elements - not unique ({time_ms:.1f}ms)"
                )
                self._validation_status.setStyleSheet("color: #fbbf24; font-size: 11px;")

        elif status == ValidationStatus.INVALID:
            self._match_badge.setText("Matches: 0")
            self._match_badge.setStyleSheet(
                "color: #ef4444; font-size: 11px; background: #3d1e1e; "
                "padding: 2px 8px; border-radius: 3px;"
            )
            self._validation_status.setText("No elements found")
            self._validation_status.setStyleSheet("color: #ef4444; font-size: 11px;")

        elif status == ValidationStatus.ERROR:
            self._match_badge.setText("Error")
            self._match_badge.setStyleSheet(
                "color: #ef4444; font-size: 11px; background: #3d1e1e; "
                "padding: 2px 8px; border-radius: 3px;"
            )
            self._validation_status.setText("Validation failed")
            self._validation_status.setStyleSheet("color: #ef4444; font-size: 11px;")

        else:
            self._match_badge.setText("Matches: -")
            self._match_badge.setStyleSheet(
                "color: #888; font-size: 11px; background: #3a3a3a; "
                "padding: 2px 8px; border-radius: 3px;"
            )
            self._validation_status.setVisible(False)

    def get_selector(self) -> str:
        """Get current selector value."""
        return self._selector_input.text().strip()

    def set_selector(self, selector: str, selector_type: str = "css") -> None:
        """Set selector value directly."""
        self._selector_input.setText(selector)
        self._selector_type_label.setText(selector_type.upper())

    def clear(self) -> None:
        """Clear all state."""
        self.set_attributes([])
        self._selector_input.clear()
        self._match_badge.setText("Matches: -")
        self._validation_status.setVisible(False)


__all__ = ["SelectorBuilderWidget", "AttributeRowWidget", "ScoreBar"]

"""
Selector Builder Widget for Element Selector Dialog.

Shows attribute rows with checkboxes and score bars.
User toggles attributes to include in generated selector.
Provides live validation with debouncing.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

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
    QWidget)

from casare_rpa.presentation.canvas.selectors.state.selector_state import (
    AttributeRow,
    ValidationStatus)
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_margins,
    set_spacing)

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
            color = THEME.success
            bg = THEME.success_subtle
        elif value >= 60:
            color = THEME.warning
            bg = THEME.warning_subtle
        else:
            color = THEME.error
            bg = THEME.error_subtle

        self.setStyleSheet(f"""
            QProgressBar {{
                background: {bg};
                border: 1px solid {THEME.bg_border};
                border-radius: {TOKENS.radius.sm // 2}px;
                text-align: center;
                color: {color};
                font-size: {TOKENS.typography.caption}pt;
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
        parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._row_index = row_index
        self._attribute = attribute
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build row UI."""
        layout = QHBoxLayout(self)
        set_margins(layout, TOKENS.margin.compact)
        set_spacing(layout, TOKENS.spacing.md)

        # Checkbox
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(self._attribute.enabled)
        self._checkbox.toggled.connect(self._on_toggled)
        self._checkbox.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: {TOKENS.sizes.icon_sm}px;
                height: {TOKENS.sizes.icon_sm}px;
            }}
            QCheckBox::indicator:unchecked {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.bg_component};
                border-radius: 3px;
            }}
            QCheckBox::indicator:checked {{
                background: {THEME.info};
                border: 1px solid {THEME.info_subtle};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self._checkbox)

        # Attribute name
        self._name_label = QLabel(self._attribute.name)
        self._name_label.setFixedWidth(80)
        self._name_label.setStyleSheet(
            f"color: {THEME.info}; font-weight: bold; font-size: {TOKENS.typography.caption}pt;"
        )
        layout.addWidget(self._name_label)

        # Equals sign
        equals = QLabel("=")
        equals.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}pt;"
        )
        layout.addWidget(equals)

        # Attribute value (truncated display)
        value = self._attribute.value
        if len(value) > 40:
            value = value[:37] + "..."
        self._value_label = QLabel(f'"{value}"')
        self._value_label.setStyleSheet(
            f"color: {THEME.warning}; font-family: {TOKENS.typography.mono}; font-size: {TOKENS.typography.caption}pt;"
        )
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
            f"color: {THEME.info}; font-weight: bold; font-size: {TOKENS.typography.caption}pt; opacity: {opacity};"
        )
        self._value_label.setStyleSheet(
            f"color: {THEME.warning}; font-family: {TOKENS.typography.mono}; font-size: {TOKENS.typography.caption}pt; opacity: {opacity};"
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
        validate_callback: Callable | None = None) -> None:
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
        set_margins(layout, TOKENS.margin.none)
        set_spacing(layout, TOKENS.spacing.md)

        # Header
        header = QHBoxLayout()
        set_spacing(header, TOKENS.spacing.md)

        title = QLabel("Selector Builder")
        title.setStyleSheet(
            f"color: {THEME.success}; font-weight: bold; font-size: {TOKENS.typography.body_sm}pt;"
        )
        header.addWidget(title)

        header.addStretch()

        # Info label
        self._info_label = QLabel("Toggle attributes to include in selector")
        self._info_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}pt;"
        )
        header.addWidget(self._info_label)

        layout.addLayout(header)

        # Scroll area for attribute rows
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setMaximumHeight(200)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {THEME.bg_border};
                border-radius: {TOKENS.radius.sm // 2 * 2}px;
                background: {THEME.bg_surface};
            }}
        """)

        self._rows_container = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_container)
        set_margins(self._rows_layout, TOKENS.margin.none)
        set_spacing(self._rows_layout, TOKENS.spacing.xs)
        self._rows_layout.addStretch()

        scroll.setWidget(self._rows_container)
        layout.addWidget(scroll)

        # Generated selector section
        generated_frame = QFrame()
        generated_frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.bg_border};
                border-radius: {TOKENS.radius.sm // 2 * 2}px;
            }}
        """)

        generated_layout = QVBoxLayout(generated_frame)
        set_margins(generated_layout, TOKENS.margin.compact)
        set_spacing(generated_layout, TOKENS.spacing.md)

        # Selector type and label
        selector_header = QHBoxLayout()

        selector_label = QLabel("Generated:")
        selector_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}pt;"
        )
        selector_header.addWidget(selector_label)

        self._selector_type_label = QLabel("CSS")
        self._selector_type_label.setStyleSheet(
            f"color: {THEME.info}; font-size: {TOKENS.typography.caption}pt; background: {THEME.info_subtle}; "
            f"padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.xs}px; border-radius: {TOKENS.radius.sm // 2}px;"
        )
        selector_header.addWidget(self._selector_type_label)

        selector_header.addStretch()

        # Match count badge
        self._match_badge = QLabel("Matches: -")
        self._match_badge.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}pt; background: {THEME.bg_component}; "
            f"padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px; border-radius: {TOKENS.radius.sm // 2}px;"
        )
        selector_header.addWidget(self._match_badge)

        generated_layout.addLayout(selector_header)

        # Editable selector input
        selector_row = QHBoxLayout()
        set_spacing(selector_row, TOKENS.spacing.md)

        self._selector_input = QLineEdit()
        self._selector_input.setFont(
            QFont(TOKENS.typography.mono.split(",")[0].replace("'", ""), 11)
        )
        self._selector_input.setPlaceholderText("(select attributes above)")
        self._selector_input.textChanged.connect(self._on_selector_changed)
        self._selector_input.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.bg_canvas};
                border: 1px solid {THEME.bg_border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px;
                color: {THEME.info};
            }}
            QLineEdit:focus {{
                border-color: {THEME.primary};
            }}
        """)
        selector_row.addWidget(self._selector_input, 1)

        # Validate button
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setFixedHeight(TOKENS.sizes.button_md)
        self._validate_btn.clicked.connect(self._on_validate_clicked)
        self._validate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_component};
                border: 1px solid {THEME.bg_elevated};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px;
                color: #e0e0e0;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: #4a4a4a;
            }}
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
        self._empty_state.setStyleSheet(
            f"color: #666; font-size: 11px; padding: {TOKENS.spacing.xl}px;"
        )
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
        time_ms: float = 0.0) -> None:
        """Update validation display."""
        self._validation_status.setVisible(True)

        # Common badge style
        badge_style = lambda color, bg: (
            f"color: {color}; font-size: {TOKENS.typography.caption}pt; background: {bg}; "
            f"padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px; border-radius: {TOKENS.radius.sm // 2}px;"
        )
        status_style = lambda color: f"color: {color}; font-size: {TOKENS.typography.caption}pt;"

        if status == ValidationStatus.VALIDATING:
            self._match_badge.setText("Validating...")
            self._match_badge.setStyleSheet(badge_style(THEME.info, THEME.info_subtle))
            self._validation_status.setText("Validating...")
            self._validation_status.setStyleSheet(status_style(THEME.info))

        elif status == ValidationStatus.VALID:
            if match_count == 1:
                self._match_badge.setText("Matches: 1")
                self._match_badge.setStyleSheet(badge_style(THEME.success, THEME.success_subtle))
                self._validation_status.setText(f"Found 1 unique element ({time_ms:.1f}ms)")
                self._validation_status.setStyleSheet(status_style(THEME.success))
            else:
                self._match_badge.setText(f"Matches: {match_count}")
                self._match_badge.setStyleSheet(badge_style(THEME.warning, THEME.warning_subtle))
                self._validation_status.setText(
                    f"Found {match_count} elements - not unique ({time_ms:.1f}ms)"
                )
                self._validation_status.setStyleSheet(status_style(THEME.warning))

        elif status == ValidationStatus.INVALID:
            self._match_badge.setText("Matches: 0")
            self._match_badge.setStyleSheet(badge_style(THEME.error, THEME.error_subtle))
            self._validation_status.setText("No elements found")
            self._validation_status.setStyleSheet(status_style(THEME.error))

        elif status == ValidationStatus.ERROR:
            self._match_badge.setText("Error")
            self._match_badge.setStyleSheet(badge_style(THEME.error, THEME.error_subtle))
            self._validation_status.setText("Validation failed")
            self._validation_status.setStyleSheet(status_style(THEME.error))

        else:
            self._match_badge.setText("Matches: -")
            self._match_badge.setStyleSheet(
                f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}pt; background: {THEME.bg_component}; "
                f"padding: {TOKENS.spacing.xxs}px {TOKENS.spacing.sm}px; border-radius: {TOKENS.radius.sm // 2}px;"
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

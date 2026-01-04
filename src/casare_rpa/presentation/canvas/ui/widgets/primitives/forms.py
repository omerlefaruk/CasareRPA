"""Form components v2 - Epic 5.2.

Labeled rows, inline errors, required markers, form containers.
Fieldsets with collapsible sections.
All using THEME_V2/TOKENS_V2 exclusively.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import (
    BasePrimitive,
)

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import (
        SectionHeader,
    )

# =============================================================================
# TYPE ALIASES
# =============================================================================

# FormLabelWidth valid values: "auto", "sm", "md", "lg"

LabelWidths = {
    "auto": 0,
    "sm": 100,
    "md": 140,
    "lg": 180,
}

# =============================================================================
# VALIDATION TYPES
# =============================================================================


class FormValidationStatus(Enum):
    """Validation status for form fields."""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    PENDING = "pending"


@dataclass
class FormValidationResult:
    """Validation result dataclass."""

    status: FormValidationStatus
    message: str = ""
    field_id: str = ""

    @classmethod
    def valid(cls) -> FormValidationResult:
        return cls(status=FormValidationStatus.VALID)

    @classmethod
    def invalid(cls, message: str, field_id: str = "") -> FormValidationResult:
        return cls(status=FormValidationStatus.INVALID, message=message, field_id=field_id)

    @classmethod
    def warning(cls, message: str, field_id: str = "") -> FormValidationResult:
        return cls(status=FormValidationStatus.WARNING, message=message, field_id=field_id)

    @classmethod
    def pending(cls, message: str = "") -> FormValidationResult:
        return cls(status=FormValidationStatus.PENDING, message=message)


ValidatorFunc = Callable[[Any], FormValidationResult]

# =============================================================================
# BUILT-IN VALIDATORS
# =============================================================================


def required_validator(value: Any) -> FormValidationResult:
    """Validate that value is not empty."""
    if value is None or value == "":
        return FormValidationResult.invalid("This field is required")
    return FormValidationResult.valid()


def min_value_validator(min_val: float) -> ValidatorFunc:
    """Create a validator for minimum value."""

    def validate(value: Any) -> FormValidationResult:
        try:
            num_val = float(value)
            if num_val < min_val:
                return FormValidationResult.invalid(f"Must be at least {min_val}")
        except (ValueError, TypeError):
            return FormValidationResult.invalid("Must be a number")
        return FormValidationResult.valid()

    return validate


def max_value_validator(max_val: float) -> ValidatorFunc:
    """Create a validator for maximum value."""

    def validate(value: Any) -> FormValidationResult:
        try:
            num_val = float(value)
            if num_val > max_val:
                return FormValidationResult.invalid(f"Must be at most {max_val}")
        except (ValueError, TypeError):
            return FormValidationResult.invalid("Must be a number")
        return FormValidationResult.valid()

    return validate


def range_validator(min_val: float, max_val: float) -> ValidatorFunc:
    """Create a validator for value range."""

    def validate(value: Any) -> FormValidationResult:
        try:
            num_val = float(value)
            if num_val < min_val or num_val > max_val:
                return FormValidationResult.invalid(f"Must be between {min_val} and {max_val}")
        except (ValueError, TypeError):
            return FormValidationResult.invalid("Must be a number")
        return FormValidationResult.valid()

    return validate


def integer_validator(value: Any) -> FormValidationResult:
    """Validate that value is an integer."""
    try:
        int(value)
        return FormValidationResult.valid()
    except (ValueError, TypeError):
        return FormValidationResult.invalid("Must be an integer")


def positive_validator(value: Any) -> FormValidationResult:
    """Validate that value is positive."""
    try:
        num_val = float(value)
        if num_val <= 0:
            return FormValidationResult.invalid("Must be positive")
        return FormValidationResult.valid()
    except (ValueError, TypeError):
        return FormValidationResult.invalid("Must be a number")


def non_negative_validator(value: Any) -> FormValidationResult:
    """Validate that value is non-negative."""
    try:
        num_val = float(value)
        if num_val < 0:
            return FormValidationResult.invalid("Must be non-negative")
        return FormValidationResult.valid()
    except (ValueError, TypeError):
        return FormValidationResult.invalid("Must be a number")


def email_validator(value: str) -> FormValidationResult:
    """Basic email format validation."""
    if not value:
        return FormValidationResult.valid()  # Empty is OK, use with required_validator
    email = str(value).strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        return FormValidationResult.invalid("Invalid email format")
    return FormValidationResult.valid()


def url_validator(value: str) -> FormValidationResult:
    """Basic URL format validation."""
    if not value:
        return FormValidationResult.valid()  # Empty is OK, use with required_validator
    url = str(value).strip().lower()
    if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file:///")):
        return FormValidationResult.invalid("URL must start with http://, https://, or file:///")
    return FormValidationResult.valid()


# =============================================================================
# FORM FIELD
# =============================================================================


class FormField(BasePrimitive):
    """Label + widget + required marker + inline error (vertical layout).

    Layout:
    ┌─────────────────────────────────────────┐
    │ Label Text *                            │  <- THEME_V2.text_secondary
    │ ┌────────────────────────────────────────┐│
    │ │ Input Widget                          ││
    │ └────────────────────────────────────────┘│
    │   ⚠ Error message here                   │  <- THEME_V2.error, caption
    └─────────────────────────────────────────┘

    Signals:
        validation_changed(FormValidationResult): Emitted when validation state changes
        value_changed(object): Emitted when widget value changes
    """

    validation_changed = Signal(object)
    value_changed = Signal(object)

    def __init__(
        self,
        label: str,
        widget: QWidget,
        *,
        required: bool = False,
        help_text: str = "",
        field_id: str = "",
        validator: ValidatorFunc | None = None,
        parent: QWidget | None = None,
    ):
        self._label_text = label
        self._widget = widget
        self._required = required
        self._help_text = help_text
        self._field_id = field_id or label.lower().replace(" ", "_")
        self._validator = validator
        # Start as PENDING if validator is set, otherwise VALID
        self._validation_result = (
            FormValidationResult.pending() if validator else FormValidationResult.valid()
        )
        self._validate_on_change = True
        self._debounce_ms = 300
        self._debounce_timer: QTimer | None = None
        super().__init__(parent=parent)

    def setup_ui(self) -> None:
        """Set up the form field UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self._get_margins("form_row"))
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Label row
        label_row = QHBoxLayout()
        label_row.setSpacing(TOKENS_V2.spacing.xs)

        self._label = QLabel(self._label_text)
        self._apply_label_style(False)
        label_row.addWidget(self._label)

        if self._required:
            self._asterisk = QLabel("*")
            self._asterisk.setStyleSheet(f"color: {THEME_V2.error};")
            label_row.addWidget(self._asterisk)

        label_row.addStretch()
        layout.addLayout(label_row)

        # Help text (if provided)
        if self._help_text:
            self._help_label = QLabel(self._help_text)
            self._help_label.setStyleSheet(f"color: {THEME_V2.text_muted}; font-size: 10pt;")
            self._help_label.setVisible(False)
            layout.addWidget(self._help_label)

        # Widget container
        self._widget_container = QWidget()
        widget_layout = QHBoxLayout(self._widget_container)
        widget_layout.setContentsMargins(0, 0, 0, 0)
        widget_layout.addWidget(self._widget)
        layout.addWidget(self._widget_container)

        # Error message row
        self._error_row = QHBoxLayout()
        self._error_row.setSpacing(TOKENS_V2.spacing.xs)
        self._error_row.setContentsMargins(0, TOKENS_V2.spacing.xs, 0, 0)

        self._error_icon = QLabel("⚠")
        self._error_icon.setVisible(False)
        self._error_icon.setStyleSheet(f"color: {THEME_V2.error}; font-size: 10pt;")
        self._error_row.addWidget(self._error_icon)

        self._error_label = QLabel("")
        self._error_label.setVisible(False)
        self._apply_error_style()
        self._error_row.addWidget(self._error_label)
        self._error_row.addStretch()

        layout.addLayout(self._error_row)
        layout.addStretch()

    def _apply_label_style(self, focused: bool) -> None:
        """Apply label styling."""
        color = THEME_V2.text_primary if focused else THEME_V2.text_secondary
        self._label.setStyleSheet(f"color: {color}; font-size: 11pt;")

    def _apply_error_style(self) -> None:
        """Apply error message styling."""
        self._error_label.setStyleSheet(
            f"color: {THEME_V2.error}; font-size: 10pt; background: transparent; padding: 0;"
        )

    def _set_widget_border(self, status: FormValidationStatus) -> None:
        """Set widget border based on validation status."""
        if not hasattr(self._widget, "setStyleSheet"):
            return

        border = THEME_V2.border
        border_width = "1px"

        if status == FormValidationStatus.INVALID:
            border = THEME_V2.error
            border_width = "2px"
        elif status == FormValidationStatus.WARNING:
            border = THEME_V2.warning
            border_width = "2px"

        # Try to apply to primitive widgets with get_input_stylesheet
        if hasattr(self._widget, "_get_v2_stylesheet"):
            stylesheet = self._widget._get_v2_stylesheet()
            # Inject border override
            inject = f"border: {border_width} solid {border};"
            self._widget.setStyleSheet(stylesheet + inject)
        else:
            # Generic border injection
            self._widget.setStyleSheet(f"border: {border_width} solid {border};")

    def connect_signals(self) -> None:
        """Connect widget signals."""
        # Connect to widget value changes
        if hasattr(self._widget, "text_changed"):
            self._widget.text_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "value_changed"):
            self._widget.value_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "current_changed"):
            self._widget.current_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "checked_changed"):
            self._widget.checked_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "textChanged"):
            self._widget.textChanged.connect(self._on_value_changed)

    @Slot(object)
    def _on_value_changed(self, value: Any) -> None:
        """Handle value change from widget."""
        self.value_changed.emit(value)

        if self._validate_on_change and self._validator:
            self._schedule_validation()

    def _schedule_validation(self) -> None:
        """Schedule debounced validation."""
        if self._debounce_timer is None:
            self._debounce_timer = QTimer()
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._run_validation)

        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_ms)

    def _run_validation(self) -> None:
        """Run validation and update UI."""
        if not self._validator:
            return

        value = self.get_value()
        self._validation_result = self._validator(value)
        self._update_validation_ui()
        self.validation_changed.emit(self._validation_result)

    def _update_validation_ui(self) -> None:
        """Update UI based on validation result."""
        status = self._validation_result.status

        # Show/hide error row
        has_error = status in (FormValidationStatus.INVALID, FormValidationStatus.WARNING)
        self._error_icon.setVisible(has_error)
        self._error_label.setVisible(has_error)

        if has_error:
            self._error_label.setText(self._validation_result.message)

        # Update widget border
        self._set_widget_border(status)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_value(self) -> Any:
        """Get current value from widget."""
        if hasattr(self._widget, "get_value"):
            return self._widget.get_value()
        elif hasattr(self._widget, "text"):
            return self._widget.text()
        elif hasattr(self._widget, "isChecked"):
            return self._widget.isChecked()
        elif hasattr(self._widget, "currentText"):
            return self._widget.currentText()
        elif hasattr(self._widget, "value"):
            return self._widget.value()
        return None

    def set_value(self, value: Any) -> None:
        """Set value on widget."""
        if hasattr(self._widget, "set_value"):
            self._widget.set_value(value)
        elif hasattr(self._widget, "setText"):
            self._widget.setText(str(value))
        elif hasattr(self._widget, "setChecked"):
            self._widget.setChecked(bool(value))

    def validate(self) -> FormValidationResult:
        """Run validation immediately (no debounce)."""
        if self._validator:
            value = self.get_value()
            self._validation_result = self._validator(value)
            self._update_validation_ui()
            self.validation_changed.emit(self._validation_result)
        return self._validation_result

    def is_valid(self) -> bool:
        """Check if field is valid."""
        if self._validation_result.status == FormValidationStatus.PENDING:
            self.validate()
        return self._validation_result.status == FormValidationStatus.VALID

    def set_validator(self, validator: ValidatorFunc | None) -> None:
        """Set the validator function."""
        self._validator = validator
        self._validation_result = FormValidationResult.pending()

    def clear_validation(self) -> None:
        """Clear validation state."""
        self._validation_result = FormValidationResult.valid()
        self._update_validation_ui()

    @property
    def widget(self) -> QWidget:
        """Get the contained widget."""
        return self._widget

    @property
    def field_id(self) -> str:
        """Get the field ID."""
        return self._field_id


# =============================================================================
# FORM ROW
# =============================================================================


class FormRow(BasePrimitive):
    """Horizontal label + widget layout.

    Layout:
    ┌───────────────────────────────────────────────────────┐
    │ Label Text *    ┌──────────────────────────────────┐  │
    │ (140px)         │ Input Widget                     │  │
    │                 └──────────────────────────────────┘  │
    │                 ⚠ Error message here                   │
    └───────────────────────────────────────────────────────┘

    Signals:
        validation_changed(FormValidationResult): Emitted when validation state changes
        value_changed(object): Emitted when widget value changes
    """

    validation_changed = Signal(object)
    value_changed = Signal(object)

    def __init__(
        self,
        label: str,
        widget: QWidget,
        *,
        label_width: str = "md",
        required: bool = False,
        help_text: str = "",
        field_id: str = "",
        validator: ValidatorFunc | None = None,
        parent: QWidget | None = None,
    ):
        self._label_text = label
        self._widget = widget
        self._label_width_val = label_width
        self._required = required
        self._help_text = help_text
        self._field_id = field_id or label.lower().replace(" ", "_")
        self._validator = validator
        # Start as PENDING if validator is set, otherwise VALID
        self._validation_result = (
            FormValidationResult.pending() if validator else FormValidationResult.valid()
        )
        self._validate_on_change = True
        self._debounce_ms = 300
        self._debounce_timer: QTimer | None = None
        super().__init__(parent=parent)

    def setup_ui(self) -> None:
        """Set up the form row UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*self._get_margins("form_row"))
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Label container (for fixed width)
        label_container = QWidget()
        label_layout = QVBoxLayout(label_container)
        label_layout.setContentsMargins(0, 0, 0, 0)
        label_layout.setSpacing(TOKENS_V2.spacing.xs)

        self._label = QLabel(self._label_text)
        self._apply_label_style()
        label_layout.addWidget(self._label)

        if self._required:
            self._asterisk = QLabel("*")
            self._asterisk.setStyleSheet(f"color: {THEME_V2.error};")
            label_layout.addWidget(self._asterisk)

        label_layout.addStretch()

        # Set label width
        width = LabelWidths.get(self._label_width_val, 140)
        if width > 0:
            label_container.setFixedWidth(width)

        layout.addWidget(label_container)

        # Widget column
        widget_col = QVBoxLayout()
        widget_col.setSpacing(TOKENS_V2.spacing.xs)

        widget_col.addWidget(self._widget)

        # Error row
        self._error_row = QHBoxLayout()
        self._error_row.setSpacing(TOKENS_V2.spacing.xs)

        self._error_icon = QLabel("⚠")
        self._error_icon.setVisible(False)
        self._error_icon.setStyleSheet(f"color: {THEME_V2.error}; font-size: 10pt;")
        self._error_row.addWidget(self._error_icon)

        self._error_label = QLabel("")
        self._error_label.setVisible(False)
        self._apply_error_style()
        self._error_row.addWidget(self._error_label)
        self._error_row.addStretch()

        widget_col.addLayout(self._error_row)
        widget_col.addStretch()

        layout.addLayout(widget_col, 1)

    def _apply_label_style(self) -> None:
        """Apply label styling."""
        self._label.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: 11pt; background: transparent;"
        )

    def _apply_error_style(self) -> None:
        """Apply error message styling."""
        self._error_label.setStyleSheet(
            f"color: {THEME_V2.error}; font-size: 10pt; background: transparent; padding: 0;"
        )

    def _set_widget_border(self, status: FormValidationStatus) -> None:
        """Set widget border based on validation status."""
        if not hasattr(self._widget, "setStyleSheet"):
            return

        border = THEME_V2.border
        border_width = "1px"

        if status == FormValidationStatus.INVALID:
            border = THEME_V2.error
            border_width = "2px"
        elif status == FormValidationStatus.WARNING:
            border = THEME_V2.warning
            border_width = "2px"

        if hasattr(self._widget, "_get_v2_stylesheet"):
            stylesheet = self._widget._get_v2_stylesheet()
            inject = f"border: {border_width} solid {border};"
            self._widget.setStyleSheet(stylesheet + inject)
        else:
            self._widget.setStyleSheet(f"border: {border_width} solid {border};")

    def connect_signals(self) -> None:
        """Connect widget signals."""
        if hasattr(self._widget, "text_changed"):
            self._widget.text_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "value_changed"):
            self._widget.value_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "current_changed"):
            self._widget.current_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "checked_changed"):
            self._widget.checked_changed.connect(self._on_value_changed)
        elif hasattr(self._widget, "textChanged"):
            self._widget.textChanged.connect(self._on_value_changed)

    @Slot(object)
    def _on_value_changed(self, value: Any) -> None:
        """Handle value change from widget."""
        self.value_changed.emit(value)

        if self._validate_on_change and self._validator:
            self._schedule_validation()

    def _schedule_validation(self) -> None:
        """Schedule debounced validation."""
        if self._debounce_timer is None:
            self._debounce_timer = QTimer()
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._run_validation)

        self._debounce_timer.stop()
        self._debounce_timer.start(self._debounce_ms)

    def _run_validation(self) -> None:
        """Run validation and update UI."""
        if not self._validator:
            return

        value = self.get_value()
        self._validation_result = self._validator(value)
        self._update_validation_ui()
        self.validation_changed.emit(self._validation_result)

    def _update_validation_ui(self) -> None:
        """Update UI based on validation result."""
        status = self._validation_result.status

        has_error = status in (FormValidationStatus.INVALID, FormValidationStatus.WARNING)
        self._error_icon.setVisible(has_error)
        self._error_label.setVisible(has_error)

        if has_error:
            self._error_label.setText(self._validation_result.message)

        self._set_widget_border(status)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def get_value(self) -> Any:
        """Get current value from widget."""
        if hasattr(self._widget, "get_value"):
            return self._widget.get_value()
        elif hasattr(self._widget, "text"):
            return self._widget.text()
        elif hasattr(self._widget, "isChecked"):
            return self._widget.isChecked()
        elif hasattr(self._widget, "currentText"):
            return self._widget.currentText()
        elif hasattr(self._widget, "value"):
            return self._widget.value()
        return None

    def set_value(self, value: Any) -> None:
        """Set value on widget."""
        if hasattr(self._widget, "set_value"):
            self._widget.set_value(value)
        elif hasattr(self._widget, "setText"):
            self._widget.setText(str(value))
        elif hasattr(self._widget, "setChecked"):
            self._widget.setChecked(bool(value))

    def validate(self) -> FormValidationResult:
        """Run validation immediately."""
        if self._validator:
            value = self.get_value()
            self._validation_result = self._validator(value)
            self._update_validation_ui()
            self.validation_changed.emit(self._validation_result)
        return self._validation_result

    def is_valid(self) -> bool:
        """Check if field is valid."""
        if self._validation_result.status == FormValidationStatus.PENDING:
            self.validate()
        return self._validation_result.status == FormValidationStatus.VALID

    def set_validator(self, validator: ValidatorFunc | None) -> None:
        """Set the validator function."""
        self._validator = validator
        self._validation_result = FormValidationResult.pending()

    def clear_validation(self) -> None:
        """Clear validation state."""
        self._validation_result = FormValidationResult.valid()
        self._update_validation_ui()

    @property
    def widget(self) -> QWidget:
        """Get the contained widget."""
        return self._widget

    @property
    def field_id(self) -> str:
        """Get the field ID."""
        return self._field_id


# =============================================================================
# READ ONLY FIELD
# =============================================================================


class ReadOnlyField(BasePrimitive):
    """Read-only display field for values.

    Signals:
        copy_clicked(): Emitted when copy button is clicked
    """

    copy_clicked = Signal()

    def __init__(
        self,
        label: str = "",
        value: str = "",
        *,
        copyable: bool = False,
        monospace: bool = False,
        select_text: bool = True,
        parent: QWidget | None = None,
    ):
        self._label_text = label
        self._value_text = value
        self._copyable = copyable
        self._monospace = monospace
        self._select_text = select_text
        super().__init__(parent=parent)

    def setup_ui(self) -> None:
        """Set up the read-only field UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self._get_margins("form_row"))
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Label
        if self._label_text:
            self._label = QLabel(self._label_text)
            self._label.setStyleSheet(
                f"color: {THEME_V2.text_secondary}; font-size: 11pt; background: transparent;"
            )
            layout.addWidget(self._label)

        # Value row
        value_row = QHBoxLayout()
        value_row.setSpacing(TOKENS_V2.spacing.sm)

        self._value_label = QLabel(self._value_text)
        self._apply_value_style()
        if self._select_text:
            self._value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        value_row.addWidget(self._value_label, 1)

        # Copy button
        if self._copyable:
            from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
            from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import ToolButton

            icon = get_icon("copy", size=TOKENS_V2.sizes.icon_sm)
            self._copy_btn = ToolButton(
                icon=icon,
                tooltip="Copy to clipboard",
                icon_size=TOKENS_V2.sizes.icon_sm,
            )
            self._copy_btn.clicked.connect(self._on_copy_clicked)
            value_row.addWidget(self._copy_btn)

        layout.addLayout(value_row)
        layout.addStretch()

    def connect_signals(self) -> None:
        """Connect signals (no-op for read-only)."""
        pass

    def _apply_value_style(self) -> None:
        """Apply value styling."""
        font_family = TOKENS_V2.typography.mono if self._monospace else TOKENS_V2.typography.family
        self._value_label.setStyleSheet(
            f"color: {THEME_V2.text_muted}; "
            f"font-family: {font_family}; "
            f"font-size: 11pt; "
            f"background: {THEME_V2.bg_surface}; "
            f"border: 1px solid {THEME_V2.border}; "
            f"border-radius: {TOKENS_V2.radius.sm}px; "
            f"padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;"
        )

    @Slot()
    def _on_copy_clicked(self) -> None:
        """Handle copy button click."""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(self._value_text)
        self.copy_clicked.emit()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_value(self, value: str) -> None:
        """Set the displayed value."""
        self._value_text = str(value)
        self._value_label.setText(self._value_text)

    def get_value(self) -> str:
        """Get the displayed value."""
        return self._value_text

    def set_label(self, label: str) -> None:
        """Set the label text."""
        self._label_text = label
        if hasattr(self, "_label"):
            self._label.setText(label)


# =============================================================================
# FORM CONTAINER
# =============================================================================


class FormContainer(QWidget):
    """Form-level validation aggregation.

    Tracks all FormField/FormRow children and provides:
    - validate_all() -> List[FormValidationResult]
    - is_valid() -> bool
    - get_invalid_fields() -> List[str]
    - auto_tab_order() - Set tab order by visual position
    - set_tab_order(widgets) - Manual tab order

    Signals:
        form_validation_changed(bool): Emitted when any field's validation changes
        value_changed(str, object): Emitted when any field's value changes (field_id, value)
    """

    form_validation_changed = Signal(bool)
    value_changed = Signal(str, object)

    def __init__(self, parent: QWidget | None = None):
        self._fields: dict[str, FormField | FormRow] = {}
        self._field_list: list[FormField | FormRow] = []
        self._scroll: QScrollArea | None = None
        self._content_widget: QWidget | None = None
        super().__init__(parent)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the form container with scrollable layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create scroll area for form content
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Content widget
        self._content_widget = QWidget(self._scroll)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
        )
        self._content_layout.setSpacing(TOKENS_V2.spacing.md)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content_widget)
        layout.addWidget(self._scroll)

        # Apply basic styling
        self._apply_stylesheet()

    def _apply_stylesheet(self) -> None:
        """Apply theme stylesheet."""
        self.setStyleSheet(f"""
            FormContainer {{
                background: {THEME_V2.bg_canvas};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
        """)

    def add_field(self, field: FormField | FormRow) -> None:
        """Add a field to the form."""
        field_id = field.field_id

        # Check for duplicate IDs
        if field_id in self._fields:
            # Generate unique ID
            counter = 1
            new_id = f"{field_id}_{counter}"
            while new_id in self._fields:
                counter += 1
                new_id = f"{field_id}_{counter}"
            field_id = new_id

        self._fields[field_id] = field
        self._field_list.append(field)

        # Insert before stretch
        if self._content_layout:
            self._content_layout.insertWidget(self._content_layout.count() - 1, field)

        # Connect signals
        if hasattr(field, "validation_changed"):
            field.validation_changed.connect(self._on_field_validation_changed)
        if hasattr(field, "value_changed"):
            field.value_changed.connect(
                lambda val, fid=field_id: self._on_field_value_changed(fid, val)
            )

    def remove_field(self, field_id: str) -> None:
        """Remove a field by ID."""
        if field_id not in self._fields:
            return

        field = self._fields[field_id]

        # Disconnect signals
        if hasattr(field, "validation_changed"):
            try:
                field.validation_changed.disconnect(self._on_field_validation_changed)
            except RuntimeError:
                pass
        if hasattr(field, "value_changed"):
            try:
                field.value_changed.disconnect()
            except RuntimeError:
                pass

        # Remove from layout
        if self._content_layout:
            self._content_layout.removeWidget(field)

        # Remove from tracking
        del self._fields[field_id]
        self._field_list = [f for f in self._field_list if f.field_id != field_id]

        # Schedule deletion
        field.deleteLater()

    def get_field(self, field_id: str) -> FormField | FormRow | None:
        """Get a field by ID."""
        return self._fields.get(field_id)

    def get_fields(self) -> list[FormField | FormRow]:
        """Get all fields."""
        return list(self._field_list)

    def validate_all(self) -> list[FormValidationResult]:
        """Validate all fields and return list of results."""
        results = []
        for field in self._field_list:
            if hasattr(field, "validate"):
                result = field.validate()
                result.field_id = field.field_id
                results.append(result)
        return results

    def is_valid(self) -> bool:
        """Check if all fields are valid."""
        for field in self._field_list:
            if hasattr(field, "is_valid"):
                if not field.is_valid():
                    return False
        return True

    def get_invalid_fields(self) -> list[str]:
        """Get list of invalid field IDs."""
        invalid = []
        for field in self._field_list:
            if hasattr(field, "is_valid"):
                if not field.is_valid():
                    invalid.append(field.field_id)
        return invalid

    def get_values(self) -> dict[str, Any]:
        """Get all field values as dict."""
        values = {}
        for field_id, field in self._fields.items():
            if hasattr(field, "get_value"):
                values[field_id] = field.get_value()
        return values

    def set_values(self, values: dict[str, Any]) -> None:
        """Set field values from dict."""
        for field_id, value in values.items():
            field = self._fields.get(field_id)
            if field and hasattr(field, "set_value"):
                field.set_value(value)

    def clear(self) -> None:
        """Clear all field values."""
        for field in self._field_list:
            if hasattr(field, "set_value"):
                field.set_value("")

    def clear_validation(self) -> None:
        """Clear validation state on all fields."""
        for field in self._field_list:
            if hasattr(field, "clear_validation"):
                field.clear_validation()

    def auto_tab_order(self) -> None:
        """Set tab order based on visual position (top to bottom)."""
        prev_widget: QWidget | None = None
        for field in self._field_list:
            widget = field.widget if hasattr(field, "widget") else field
            if prev_widget:
                self.setTabOrder(prev_widget, widget)
            prev_widget = widget

    def set_tab_order(self, field_ids: list[str]) -> None:
        """Set explicit tab order by field IDs."""
        prev_widget: QWidget | None = None
        for field_id in field_ids:
            field = self._fields.get(field_id)
            if field:
                widget = field.widget if hasattr(field, "widget") else field
                if prev_widget:
                    self.setTabOrder(prev_widget, widget)
                prev_widget = widget

    @Slot(object)
    def _on_field_validation_changed(self, result: FormValidationResult) -> None:
        """Handle validation change from a field."""
        self.form_validation_changed.emit(self.is_valid())

    @Slot(str, object)
    def _on_field_value_changed(self, field_id: str, value: Any) -> None:
        """Handle value change from a field."""
        self.value_changed.emit(field_id, value)

    @property
    def scroll_area(self) -> QScrollArea | None:
        """Get the scroll area widget."""
        return self._scroll

    @property
    def content_widget(self) -> QWidget | None:
        """Get the content widget."""
        return self._content_widget


# =============================================================================
# FIELDSET
# =============================================================================


class Fieldset(BasePrimitive):
    """Collapsible section with form fields inside.

    Uses SectionHeader from structural.py for the collapsible header.

    Layout:
    ┌─────────────────────────────────────────┐
    │ ▼ Section Title              [collapse]│
    │ ┌─────────────────────────────────────┐│
    │ │ Form fields go here...              ││
    │ │                                     ││
    │ └─────────────────────────────────────┘│
    └─────────────────────────────────────────┘

    Signals:
        collapsed_changed(bool): Emitted when collapsed state changes
        field_added(str): Emitted when a field is added
    """

    collapsed_changed = Signal(bool)
    field_added = Signal(str)

    def __init__(
        self,
        title: str,
        *,
        collapsible: bool = True,
        collapsed: bool = False,
        parent: QWidget | None = None,
    ):
        self._title = title
        self._collapsible = collapsible
        self._is_collapsed = collapsed
        self._header: SectionHeader | None = None
        self._content_container: QWidget | None = None
        self._content_layout: QVBoxLayout | None = None
        self._fields: list[QWidget] = []
        super().__init__(parent=parent)

    def setup_ui(self) -> None:
        """Set up the fieldset UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Import SectionHeader from structural module
        from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import (
            SectionHeader,
        )

        # Create section header
        self._header = SectionHeader(
            text=self._title,
            collapsible=self._collapsible,
            collapsed=self._is_collapsed,
            level=2,
        )
        layout.addWidget(self._header)

        # Content container
        self._content_container = QWidget(self)
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
        )
        self._content_layout.setSpacing(TOKENS_V2.spacing.md)
        self._content_layout.addStretch()

        layout.addWidget(self._content_container, 1)

        # Set initial collapsed state
        if self._is_collapsed:
            self._content_container.setVisible(False)

    def connect_signals(self) -> None:
        """Connect signals."""
        if self._header is not None:
            self._header.collapsed_changed.connect(self._on_header_collapsed_changed)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        return f"""
            Fieldset {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
            }}
        """

    @Slot(bool)
    def _on_header_collapsed_changed(self, collapsed: bool) -> None:
        """Handle collapse state change from header."""
        self._is_collapsed = collapsed
        if self._content_container:
            self._content_container.setVisible(not collapsed)
        self.collapsed_changed.emit(collapsed)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def add_field(self, field: QWidget | FormField | FormRow) -> None:
        """Add a field to the fieldset."""
        if self._content_layout is None:
            return

        self._fields.append(field)

        # Insert before stretch
        self._content_layout.insertWidget(self._content_layout.count() - 1, field)

        # Emit signal with field_id if available
        field_id = getattr(field, "field_id", "")
        self.field_added.emit(field_id)

    def add_widget(self, widget: QWidget) -> None:
        """Add any widget to the fieldset."""
        self.add_field(widget)

    def remove_field(self, index: int) -> None:
        """Remove field at index."""
        if 0 <= index < len(self._fields):
            field = self._fields.pop(index)
            if self._content_layout:
                self._content_layout.removeWidget(field)
            field.deleteLater()

    def clear(self) -> None:
        """Remove all fields."""
        if self._content_layout is None:
            return

        for field in self._fields:
            self._content_layout.removeWidget(field)
            field.deleteLater()

        self._fields.clear()

    def set_collapsed(self, collapsed: bool) -> None:
        """Set collapsed state."""
        if self._header:
            self._header.set_collapsed(collapsed)
        else:
            self._is_collapsed = collapsed
            if self._content_container:
                self._content_container.setVisible(not collapsed)

    def is_collapsed(self) -> bool:
        """Check if collapsed."""
        if self._header:
            return self._header.is_collapsed()
        return self._is_collapsed

    def toggle(self) -> None:
        """Toggle collapsed state."""
        self.set_collapsed(not self.is_collapsed())

    def set_title(self, title: str) -> None:
        """Set the fieldset title."""
        self._title = title
        if self._header:
            self._header.set_text(title)

    def title(self) -> str:
        """Get the fieldset title."""
        return self._title

    @property
    def header(self) -> SectionHeader | None:
        """Get the section header widget."""
        return self._header

    @property
    def content_container(self) -> QWidget | None:
        """Get the content container widget."""
        return self._content_container

    @property
    def fields(self) -> list[QWidget]:
        """Get all fields in the fieldset."""
        return list(self._fields)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_form_field(
    label: str,
    widget: QWidget,
    *,
    required: bool = False,
    help_text: str = "",
    field_id: str = "",
    validator: ValidatorFunc | None = None,
    parent: QWidget | None = None,
) -> FormField:
    """Factory function to create a FormField with consistent settings."""
    return FormField(
        label=label,
        widget=widget,
        required=required,
        help_text=help_text,
        field_id=field_id,
        validator=validator,
        parent=parent,
    )


def create_form_row(
    label: str,
    widget: QWidget,
    *,
    label_width: str = "md",
    required: bool = False,
    help_text: str = "",
    field_id: str = "",
    validator: ValidatorFunc | None = None,
    parent: QWidget | None = None,
) -> FormRow:
    """Factory function to create a FormRow with consistent settings."""
    return FormRow(
        label=label,
        widget=widget,
        label_width=label_width,
        required=required,
        help_text=help_text,
        field_id=field_id,
        validator=validator,
        parent=parent,
    )


def create_read_only_field(
    label: str = "",
    value: str = "",
    *,
    copyable: bool = False,
    monospace: bool = False,
    parent: QWidget | None = None,
) -> ReadOnlyField:
    """Factory function to create a ReadOnlyField."""
    return ReadOnlyField(
        label=label,
        value=value,
        copyable=copyable,
        monospace=monospace,
        parent=parent,
    )


def create_form_container(
    parent: QWidget | None = None,
) -> FormContainer:
    """Factory function to create a FormContainer."""
    return FormContainer(parent=parent)


def create_fieldset(
    title: str,
    *,
    collapsible: bool = True,
    collapsed: bool = False,
    parent: QWidget | None = None,
) -> Fieldset:
    """Factory function to create a Fieldset."""
    return Fieldset(
        title=title,
        collapsible=collapsible,
        collapsed=collapsed,
        parent=parent,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Validation types
    "FormValidationStatus",
    "FormValidationResult",
    "ValidatorFunc",
    # Built-in validators
    "required_validator",
    "min_value_validator",
    "max_value_validator",
    "range_validator",
    "integer_validator",
    "positive_validator",
    "non_negative_validator",
    "email_validator",
    "url_validator",
    # Form components
    "FormField",
    "FormRow",
    "ReadOnlyField",
    "FormContainer",
    "Fieldset",
    # Factory functions
    "create_form_field",
    "create_form_row",
    "create_read_only_field",
    "create_form_container",
    "create_fieldset",
    # Type aliases
    "LabelWidths",
]

"""
Validated Input Widgets for CasareRPA.

Provides inline validation feedback for node property inputs.
Shows real-time validation with visual feedback:
- Valid: Normal border
- Invalid: Red border + error message below
- Warning: Orange border + warning message below

Design follows VSCode dark theme styling.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.ui.theme import THEME

# =============================================================================
# Validation Status Types
# =============================================================================


class ValidationStatus(Enum):
    """Validation status for input fields."""

    VALID = auto()
    INVALID = auto()
    WARNING = auto()


@dataclass
class ValidationResult:
    """Result of validating an input value."""

    status: ValidationStatus
    message: str = ""

    @classmethod
    def valid(cls) -> "ValidationResult":
        """Create a valid result."""
        return cls(status=ValidationStatus.VALID)

    @classmethod
    def invalid(cls, message: str) -> "ValidationResult":
        """Create an invalid result with error message."""
        return cls(status=ValidationStatus.INVALID, message=message)

    @classmethod
    def warning(cls, message: str) -> "ValidationResult":
        """Create a warning result with warning message."""
        return cls(status=ValidationStatus.WARNING, message=message)


# Type alias for validator functions
ValidatorFunc = Callable[[Any], ValidationResult]


# =============================================================================
# Validation Colors (Using THEME)
# =============================================================================

VALIDATION_COLORS = {
    ValidationStatus.VALID: THEME.border,  # Normal border
    ValidationStatus.INVALID: THEME.error,  # Red border
    ValidationStatus.WARNING: THEME.warning,  # Orange border
}

VALIDATION_BG_COLORS = {
    ValidationStatus.VALID: THEME.input_bg,  # Normal background
    ValidationStatus.INVALID: THEME.input_bg,  # Same background, border shows status
    ValidationStatus.WARNING: THEME.input_bg,  # Same background, border shows status
}


# =============================================================================
# Validation Styles
# =============================================================================


def get_validated_line_edit_style(status: ValidationStatus) -> str:
    """
    Get QSS style for a validated line edit based on status.

    Args:
        status: Current validation status

    Returns:
        QSS stylesheet string
    """
    border_color = VALIDATION_COLORS[status]
    bg_color = VALIDATION_BG_COLORS[status]

    # Border width increases for invalid/warning states
    border_width = "2px" if status != ValidationStatus.VALID else "1px"

    return f"""
        QLineEdit {{
            background: {bg_color};
            border: {border_width} solid {border_color};
            border-radius: 3px;
            color: {THEME.text_primary};
            padding: 2px 28px 2px 4px;
        }}
        QLineEdit:focus {{
            border: {border_width} solid {border_color if status != ValidationStatus.VALID else THEME.accent};
        }}
    """


# =============================================================================
# Validated Line Edit
# =============================================================================


class ValidatedLineEdit(QLineEdit):
    """
    QLineEdit with inline validation feedback.

    Features:
    - Validation runs on editingFinished signal
    - Visual feedback via border color (red=invalid, orange=warning)
    - Validation message shown below widget
    - Debounced validation to avoid excessive calls

    Signals:
        validation_changed: Emitted when validation status changes
    """

    validation_changed = Signal(ValidationResult)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the widget."""
        super().__init__(parent)

        self._validators: list[ValidatorFunc] = []
        self._validation_status = ValidationStatus.VALID
        self._validation_message = ""
        self._validate_on_change = False  # Validate on every keystroke
        self._debounce_timer: QTimer | None = None
        self._debounce_delay_ms = 300  # Debounce delay for change validation

        self._setup_validation()

    def _setup_validation(self) -> None:
        """Set up validation connections."""
        # Validate on editing finished (focus lost or Enter pressed)
        self.editingFinished.connect(self._run_validation)

        # Optional: validate on text change with debounce
        if self._validate_on_change:
            self._debounce_timer = QTimer()
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._run_validation)
            self.textChanged.connect(self._on_text_changed_debounced)

    def _on_text_changed_debounced(self, text: str) -> None:
        """Handle text change with debounce."""
        if self._debounce_timer:
            self._debounce_timer.start(self._debounce_delay_ms)

    def add_validator(self, validator: ValidatorFunc) -> None:
        """
        Add a validator function.

        Validators are called in order. First failure stops validation.

        Args:
            validator: Function that takes value and returns ValidationResult
        """
        self._validators.append(validator)

    def clear_validators(self) -> None:
        """Remove all validators."""
        self._validators.clear()

    def set_validate_on_change(self, enabled: bool, debounce_ms: int = 300) -> None:
        """
        Enable/disable validation on text change.

        Args:
            enabled: Whether to validate on every change
            debounce_ms: Debounce delay in milliseconds
        """
        self._validate_on_change = enabled
        self._debounce_delay_ms = debounce_ms

        if enabled and not self._debounce_timer:
            self._debounce_timer = QTimer()
            self._debounce_timer.setSingleShot(True)
            self._debounce_timer.timeout.connect(self._run_validation)
            self.textChanged.connect(self._on_text_changed_debounced)
        elif not enabled and self._debounce_timer:
            self._debounce_timer.stop()
            try:
                self.textChanged.disconnect(self._on_text_changed_debounced)
            except RuntimeError:
                pass  # Already disconnected

    def _run_validation(self) -> None:
        """Run all validators and update status."""
        value = self.text()

        # Run validators in order
        result = ValidationResult.valid()
        for validator in self._validators:
            try:
                result = validator(value)
                if result.status != ValidationStatus.VALID:
                    break  # Stop on first failure
            except Exception as e:
                logger.debug(f"Validator error: {e}")
                result = ValidationResult.invalid(f"Validation error: {e}")
                break

        # Update status if changed
        if result.status != self._validation_status or result.message != self._validation_message:
            self._validation_status = result.status
            self._validation_message = result.message
            self._update_visual_state()
            self.validation_changed.emit(result)

    def _update_visual_state(self) -> None:
        """Update visual state based on validation status."""
        self.setStyleSheet(get_validated_line_edit_style(self._validation_status))

    def validate(self) -> ValidationResult:
        """
        Manually trigger validation and return result.

        Returns:
            Current validation result
        """
        self._run_validation()
        return ValidationResult(
            status=self._validation_status,
            message=self._validation_message,
        )

    def get_validation_status(self) -> ValidationStatus:
        """Get current validation status."""
        return self._validation_status

    def get_validation_message(self) -> str:
        """Get current validation message."""
        return self._validation_message

    def is_valid(self) -> bool:
        """Check if current value is valid."""
        return self._validation_status == ValidationStatus.VALID

    def set_validation_status(self, status: ValidationStatus, message: str = "") -> None:
        """
        Manually set validation status (for external validation).

        Args:
            status: Validation status
            message: Optional message
        """
        self._validation_status = status
        self._validation_message = message
        self._update_visual_state()


# =============================================================================
# Validated Input Container
# =============================================================================


class ValidatedInputWidget(QWidget):
    """
    Container widget that wraps an input with validation message display.

    Displays the input widget and shows validation message below it.
    Use this when you need to show validation errors inline in nodes.

    Layout:
        [Input Widget]
        [Warning Icon] Validation message (if any)
    """

    validation_changed = Signal(ValidationResult)

    def __init__(
        self,
        input_widget: QWidget,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the container.

        Args:
            input_widget: The input widget to wrap (QLineEdit, etc.)
            parent: Parent widget
        """
        super().__init__(parent)

        self._input_widget = input_widget
        self._validators: list[ValidatorFunc] = []
        self._validation_status = ValidationStatus.VALID
        self._validation_message = ""

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Add input widget
        layout.addWidget(self._input_widget)

        # Validation message row
        self._message_row = QWidget()
        self._message_row.setVisible(False)  # Hidden by default
        message_layout = QHBoxLayout(self._message_row)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(4)

        # Warning/error icon (using text for simplicity)
        self._icon_label = QLabel()
        self._icon_label.setFixedWidth(14)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message_layout.addWidget(self._icon_label)

        # Message text
        self._message_label = QLabel()
        self._message_label.setWordWrap(True)
        self._message_label.setStyleSheet(f"""
            QLabel {{
                color: {THEME.error};
                font-size: 10px;
            }}
        """)
        message_layout.addWidget(self._message_label, 1)

        layout.addWidget(self._message_row)

    def _connect_signals(self) -> None:
        """Connect to input widget signals."""
        # Connect to editingFinished if available
        if hasattr(self._input_widget, "editingFinished"):
            self._input_widget.editingFinished.connect(self._run_validation)

        # Connect to validation_changed if input widget has it
        if hasattr(self._input_widget, "validation_changed"):
            self._input_widget.validation_changed.connect(self._on_input_validation)

    def _on_input_validation(self, result: ValidationResult) -> None:
        """Handle validation from input widget."""
        self._update_display(result)
        self.validation_changed.emit(result)

    def add_validator(self, validator: ValidatorFunc) -> None:
        """
        Add a validator function.

        Args:
            validator: Function that takes value and returns ValidationResult
        """
        self._validators.append(validator)

        # Also add to input widget if it supports validators
        if hasattr(self._input_widget, "add_validator"):
            self._input_widget.add_validator(validator)

    def _run_validation(self) -> None:
        """Run validation and update display."""
        # Get value from input widget
        value = ""
        if hasattr(self._input_widget, "text"):
            value = self._input_widget.text()
        elif hasattr(self._input_widget, "get_value"):
            value = self._input_widget.get_value()

        # Run validators
        result = ValidationResult.valid()
        for validator in self._validators:
            try:
                result = validator(value)
                if result.status != ValidationStatus.VALID:
                    break
            except Exception as e:
                result = ValidationResult.invalid(str(e))
                break

        self._update_display(result)
        self.validation_changed.emit(result)

    def _update_display(self, result: ValidationResult) -> None:
        """Update display based on validation result."""
        self._validation_status = result.status
        self._validation_message = result.message

        # Update input widget style if possible
        if hasattr(self._input_widget, "setStyleSheet"):
            self._input_widget.setStyleSheet(get_validated_line_edit_style(result.status))

        # Show/hide message row
        if result.status == ValidationStatus.VALID:
            self._message_row.setVisible(False)
        else:
            self._message_row.setVisible(True)

            # Set icon and color based on status
            if result.status == ValidationStatus.INVALID:
                self._icon_label.setText("!")
                self._icon_label.setStyleSheet(f"color: {THEME.error}; font-weight: bold;")
                self._message_label.setStyleSheet(f"color: {THEME.error}; font-size: 10px;")
            else:  # WARNING
                self._icon_label.setText("!")
                self._icon_label.setStyleSheet(f"color: {THEME.warning}; font-weight: bold;")
                self._message_label.setStyleSheet(f"color: {THEME.warning}; font-size: 10px;")

            self._message_label.setText(result.message)

    def get_input_widget(self) -> QWidget:
        """Get the wrapped input widget."""
        return self._input_widget

    def get_validation_status(self) -> ValidationStatus:
        """Get current validation status."""
        return self._validation_status

    def is_valid(self) -> bool:
        """Check if current value is valid."""
        return self._validation_status == ValidationStatus.VALID


# =============================================================================
# Built-in Validators
# =============================================================================


def required_validator(value: Any) -> ValidationResult:
    """Validate that value is not empty."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return ValidationResult.invalid("This field is required")
    return ValidationResult.valid()


def min_value_validator(min_val: float) -> ValidatorFunc:
    """
    Create validator for minimum value.

    Args:
        min_val: Minimum allowed value

    Returns:
        Validator function
    """

    def validator(value: Any) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult.valid()  # Empty is valid (use required_validator for required)
        try:
            num_val = float(value)
            if num_val < min_val:
                return ValidationResult.invalid(f"Value must be >= {min_val}")
        except (ValueError, TypeError):
            return ValidationResult.invalid("Must be a number")
        return ValidationResult.valid()

    return validator


def max_value_validator(max_val: float) -> ValidatorFunc:
    """
    Create validator for maximum value.

    Args:
        max_val: Maximum allowed value

    Returns:
        Validator function
    """

    def validator(value: Any) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult.valid()
        try:
            num_val = float(value)
            if num_val > max_val:
                return ValidationResult.invalid(f"Value must be <= {max_val}")
        except (ValueError, TypeError):
            return ValidationResult.invalid("Must be a number")
        return ValidationResult.valid()

    return validator


def range_validator(min_val: float, max_val: float) -> ValidatorFunc:
    """
    Create validator for value range.

    Args:
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validator function
    """

    def validator(value: Any) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult.valid()
        try:
            num_val = float(value)
            if num_val < min_val or num_val > max_val:
                return ValidationResult.invalid(f"Value must be between {min_val} and {max_val}")
        except (ValueError, TypeError):
            return ValidationResult.invalid("Must be a number")
        return ValidationResult.valid()

    return validator


def integer_validator(value: Any) -> ValidationResult:
    """Validate that value is an integer."""
    if value is None or value == "":
        return ValidationResult.valid()
    try:
        int(value)
    except (ValueError, TypeError):
        return ValidationResult.invalid("Must be an integer")
    return ValidationResult.valid()


def positive_validator(value: Any) -> ValidationResult:
    """Validate that value is positive (> 0)."""
    if value is None or value == "":
        return ValidationResult.valid()
    try:
        num_val = float(value)
        if num_val <= 0:
            return ValidationResult.invalid("Value must be positive (> 0)")
    except (ValueError, TypeError):
        return ValidationResult.invalid("Must be a number")
    return ValidationResult.valid()


def non_negative_validator(value: Any) -> ValidationResult:
    """Validate that value is non-negative (>= 0)."""
    if value is None or value == "":
        return ValidationResult.valid()
    try:
        num_val = float(value)
        if num_val < 0:
            return ValidationResult.invalid("Value must be >= 0")
    except (ValueError, TypeError):
        return ValidationResult.invalid("Must be a number")
    return ValidationResult.valid()


def selector_warning_validator(value: Any) -> ValidationResult:
    """
    Validate selector format (warning only).

    This is a soft validator that shows warnings for potentially problematic selectors.
    """
    if value is None or value == "":
        return ValidationResult.valid()

    # Check for common issues
    selector = str(value).strip()

    # Very short selectors might be too generic
    if len(selector) < 3 and not selector.startswith("#") and not selector.startswith("."):
        return ValidationResult.warning("Selector may be too generic")

    # Check for potentially fragile selectors
    if ":nth-child" in selector and ">" in selector:
        return ValidationResult.warning("Complex path selectors may be fragile")

    # Check for very long selectors
    if len(selector) > 200:
        return ValidationResult.warning("Very long selector - consider simplifying")

    return ValidationResult.valid()


__all__ = [
    "ValidationStatus",
    "ValidationResult",
    "ValidatorFunc",
    "ValidatedLineEdit",
    "ValidatedInputWidget",
    "get_validated_line_edit_style",
    "required_validator",
    "min_value_validator",
    "max_value_validator",
    "range_validator",
    "integer_validator",
    "positive_validator",
    "non_negative_validator",
    "selector_warning_validator",
]

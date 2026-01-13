"""
Tests for Form Components v2 - Epic 5.2.

Tests FormField, FormRow, ReadOnlyField, FormContainer, Fieldset,
and built-in validators.
"""

import pytest

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QSpinBox, QWidget

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.forms import (
    Fieldset,
    FormContainer,
    FormField,
    FormRow,
    FormValidationResult,
    FormValidationStatus,
    LabelWidths,
    ReadOnlyField,
    ValidatorFunc,
    create_fieldset,
    create_form_container,
    create_form_field,
    create_form_row,
    create_read_only_field,
    email_validator,
    integer_validator,
    max_value_validator,
    min_value_validator,
    non_negative_validator,
    positive_validator,
    range_validator,
    required_validator,
    url_validator,
)
from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import TextInput


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def widget(qapp):
    """Parent widget for testing."""
    return QWidget()


@pytest.fixture
def text_input(widget):
    """TextInput widget for testing."""
    return TextInput(parent=widget)


# =============================================================================
# VALIDATION RESULT TESTS
# =============================================================================


class TestFormValidationResult:
    """Tests for FormValidationResult dataclass."""

    def test_valid_factory(self):
        """Test valid() class method creates valid result."""
        result = FormValidationResult.valid()
        assert result.status == FormValidationStatus.VALID
        assert result.message == ""

    def test_invalid_factory(self):
        """Test invalid() class method creates invalid result."""
        result = FormValidationResult.invalid("Field is required", "test_field")
        assert result.status == FormValidationStatus.INVALID
        assert result.message == "Field is required"
        assert result.field_id == "test_field"

    def test_warning_factory(self):
        """Test warning() class method creates warning result."""
        result = FormValidationResult.warning("Value is unusual", "test_field")
        assert result.status == FormValidationStatus.WARNING
        assert result.message == "Value is unusual"

    def test_pending_factory(self):
        """Test pending() class method creates pending result."""
        result = FormValidationResult.pending("Validating...")
        assert result.status == FormValidationStatus.PENDING
        assert result.message == "Validating..."


# =============================================================================
# BUILT-IN VALIDATOR TESTS
# =============================================================================


class TestValidators:
    """Tests for built-in validator functions."""

    def test_required_validator_with_value(self):
        """Test required_validator passes with non-empty value."""
        result = required_validator("test")
        assert result.status == FormValidationStatus.VALID

    def test_required_validator_with_string(self):
        """Test required_validator passes with non-empty string."""
        result = required_validator("hello")
        assert result.status == FormValidationStatus.VALID

    def test_required_validator_with_empty_string(self):
        """Test required_validator fails with empty string."""
        result = required_validator("")
        assert result.status == FormValidationStatus.INVALID
        assert "required" in result.message.lower()

    def test_required_validator_with_none(self):
        """Test required_validator fails with None."""
        result = required_validator(None)
        assert result.status == FormValidationStatus.INVALID

    def test_min_value_validator_pass(self):
        """Test min_value_validator passes with valid value."""
        validator = min_value_validator(10)
        result = validator(15)
        assert result.status == FormValidationStatus.VALID

    def test_min_value_validator_fail(self):
        """Test min_value_validator fails with low value."""
        validator = min_value_validator(10)
        result = validator(5)
        assert result.status == FormValidationStatus.INVALID
        assert "10" in result.message

    def test_min_value_validator_boundary(self):
        """Test min_value_validator at boundary."""
        validator = min_value_validator(10)
        result = validator(10)
        assert result.status == FormValidationStatus.VALID

    def test_max_value_validator_pass(self):
        """Test max_value_validator passes with valid value."""
        validator = max_value_validator(100)
        result = validator(50)
        assert result.status == FormValidationStatus.VALID

    def test_max_value_validator_fail(self):
        """Test max_value_validator fails with high value."""
        validator = max_value_validator(100)
        result = validator(150)
        assert result.status == FormValidationStatus.INVALID
        assert "100" in result.message

    def test_max_value_validator_boundary(self):
        """Test max_value_validator at boundary."""
        validator = max_value_validator(100)
        result = validator(100)
        assert result.status == FormValidationStatus.VALID

    def test_range_validator_pass(self):
        """Test range_validator passes with value in range."""
        validator = range_validator(1, 10)
        result = validator(5)
        assert result.status == FormValidationStatus.VALID

    def test_range_validator_too_low(self):
        """Test range_validator fails with value below range."""
        validator = range_validator(1, 10)
        result = validator(0)
        assert result.status == FormValidationStatus.INVALID

    def test_range_validator_too_high(self):
        """Test range_validator fails with value above range."""
        validator = range_validator(1, 10)
        result = validator(11)
        assert result.status == FormValidationStatus.INVALID

    def test_range_validator_boundaries(self):
        """Test range_validator at boundaries."""
        validator = range_validator(1, 10)
        result1 = validator(1)
        result2 = validator(10)
        assert result1.status == FormValidationStatus.VALID
        assert result2.status == FormValidationStatus.VALID

    def test_range_validator_invalid_type(self):
        """Test range_validator handles non-numeric input."""
        validator = range_validator(1, 10)
        result = validator("abc")
        assert result.status == FormValidationStatus.INVALID

    def test_integer_validator_pass(self):
        """Test integer_validator passes with integer."""
        result = integer_validator("42")
        assert result.status == FormValidationStatus.VALID

    def test_integer_validator_with_int(self):
        """Test integer_validator passes with int type."""
        result = integer_validator(42)
        assert result.status == FormValidationStatus.VALID

    def test_integer_validator_fail(self):
        """Test integer_validator fails with non-integer."""
        result = integer_validator("3.14")
        assert result.status == FormValidationStatus.INVALID
        assert "integer" in result.message.lower()

    def test_positive_validator_pass(self):
        """Test positive_validator passes with positive number."""
        result = positive_validator(5)
        assert result.status == FormValidationStatus.VALID

    def test_positive_validator_zero(self):
        """Test positive_validator fails with zero."""
        result = positive_validator(0)
        assert result.status == FormValidationStatus.INVALID

    def test_positive_validator_negative(self):
        """Test positive_validator fails with negative number."""
        result = positive_validator(-5)
        assert result.status == FormValidationStatus.INVALID

    def test_non_negative_validator_pass(self):
        """Test non_negative_validator passes with positive."""
        result = non_negative_validator(5)
        assert result.status == FormValidationStatus.VALID

    def test_non_negative_validator_zero(self):
        """Test non_negative_validator passes with zero."""
        result = non_negative_validator(0)
        assert result.status == FormValidationStatus.VALID

    def test_non_negative_validator_fail(self):
        """Test non_negative_validator fails with negative."""
        result = non_negative_validator(-1)
        assert result.status == FormValidationStatus.INVALID

    def test_email_validator_valid(self):
        """Test email_validator passes with valid email."""
        result = email_validator("user@example.com")
        assert result.status == FormValidationStatus.VALID

    def test_email_validator_empty(self):
        """Test email_validator passes with empty string (use with required)."""
        result = email_validator("")
        assert result.status == FormValidationStatus.VALID

    def test_email_validator_no_at(self):
        """Test email_validator fails without @."""
        result = email_validator("userexample.com")
        assert result.status == FormValidationStatus.INVALID

    def test_email_validator_no_domain(self):
        """Test email_validator fails without domain."""
        result = email_validator("user@")
        assert result.status == FormValidationStatus.INVALID

    def test_email_validator_no_tld(self):
        """Test email_validator fails without TLD."""
        result = email_validator("user@example")
        assert result.status == FormValidationStatus.INVALID

    def test_url_validator_valid_http(self):
        """Test url_validator passes with http://."""
        result = url_validator("http://example.com")
        assert result.status == FormValidationStatus.VALID

    def test_url_validator_valid_https(self):
        """Test url_validator passes with https://."""
        result = url_validator("https://example.com")
        assert result.status == FormValidationStatus.VALID

    def test_url_validator_valid_file(self):
        """Test url_validator passes with file:///."""
        result = url_validator("file:///C:/path/to/file.txt")
        assert result.status == FormValidationStatus.VALID

    def test_url_validator_empty(self):
        """Test url_validator passes with empty string (use with required)."""
        result = url_validator("")
        assert result.status == FormValidationStatus.VALID

    def test_url_validator_invalid_protocol(self):
        """Test url_validator fails with invalid protocol."""
        result = url_validator("ftp://example.com")
        assert result.status == FormValidationStatus.INVALID

    def test_url_validator_no_protocol(self):
        """Test url_validator fails without protocol."""
        result = url_validator("example.com")
        assert result.status == FormValidationStatus.INVALID


# =============================================================================
# FORM FIELD TESTS
# =============================================================================


class TestFormField:
    """Tests for FormField component."""

    def test_initialization(self, widget, text_input):
        """Test FormField initializes correctly."""
        field = FormField("Name", text_input, parent=widget)
        assert field.field_id == "name"
        assert field.widget is text_input
        assert not field._required

    def test_with_required_marker(self, widget):
        """Test FormField with required marker."""
        field = FormField("Email", TextInput(parent=widget), required=True, parent=widget)
        assert field._required
        # Asterisk label should exist
        assert hasattr(field, "_asterisk")

    def test_with_help_text(self, widget):
        """Test FormField with help text."""
        field = FormField(
            "Username",
            TextInput(parent=widget),
            help_text="Must be unique",
            parent=widget,
        )
        assert field._help_text == "Must be unique"
        assert hasattr(field, "_help_label")

    def test_with_custom_field_id(self, widget):
        """Test FormField with custom field ID."""
        field = FormField(
            "Label",
            TextInput(parent=widget),
            field_id="custom_id",
            parent=widget,
        )
        assert field.field_id == "custom_id"

    def test_get_value(self, widget):
        """Test get_value method."""
        input_widget = TextInput(value="test_value", parent=widget)
        field = FormField("Test", input_widget, parent=widget)
        assert field.get_value() == "test_value"

    def test_set_value(self, widget):
        """Test set_value method."""
        input_widget = TextInput(parent=widget)
        field = FormField("Test", input_widget, parent=widget)
        field.set_value("new_value")
        assert field.get_value() == "new_value"

    def test_value_changed_signal(self, widget):
        """Test value_changed signal emission."""
        input_widget = TextInput(parent=widget)
        field = FormField("Test", input_widget, parent=widget)
        results = []

        field.value_changed.connect(lambda v: results.append(v))
        input_widget.set_value("hello")
        QApplication.processEvents()

        assert len(results) > 0

    def test_validate_without_validator(self, widget):
        """Test validate without validator always returns valid."""
        field = FormField("Test", TextInput(parent=widget), parent=widget)
        result = field.validate()
        assert result.status == FormValidationStatus.VALID

    def test_validate_with_required_validator(self, widget):
        """Test validate with required validator."""
        input_widget = TextInput(parent=widget)
        field = FormField(
            "Test",
            input_widget,
            required=True,
            validator=required_validator,
            parent=widget,
        )

        # Empty should be invalid
        result = field.validate()
        assert result.status == FormValidationStatus.INVALID

        # With value should be valid
        input_widget.set_value("value")
        QApplication.processEvents()
        result = field.validate()
        assert result.status == FormValidationStatus.VALID

    def test_is_valid(self, widget):
        """Test is_valid method."""
        input_widget = TextInput(parent=widget)
        field = FormField(
            "Test",
            input_widget,
            validator=required_validator,
            parent=widget,
        )

        # Empty field should be invalid (triggers validation via is_valid)
        assert not field.is_valid()

        # Set value - validation runs on change (debounced)
        input_widget.set_value("value")
        QApplication.processEvents()

        # Wait for debounce timer
        from PySide6.QtTest import QTest
        QTest.qWait(350)  # Wait for debounce timer (300ms)

        # Should now be valid
        assert field.is_valid()

    def test_clear_validation(self, widget):
        """Test clear_validation method."""
        input_widget = TextInput(parent=widget)
        field = FormField(
            "Test",
            input_widget,
            validator=required_validator,
            parent=widget,
        )

        # Trigger validation (should fail)
        field.validate()
        assert field._validation_result.status == FormValidationStatus.INVALID

        # Clear validation
        field.clear_validation()
        assert field._validation_result.status == FormValidationStatus.VALID

    def test_set_validator(self, widget):
        """Test set_validator method."""
        field = FormField("Test", TextInput(parent=widget), parent=widget)
        assert field._validator is None

        field.set_validator(required_validator)
        assert field._validator is not None

    def test_validation_changed_signal(self, widget):
        """Test validation_changed signal emission."""
        input_widget = TextInput(parent=widget)
        field = FormField(
            "Test",
            input_widget,
            validator=required_validator,
            parent=widget,
        )
        results = []

        field.validation_changed.connect(lambda r: results.append(r))
        field.validate()

        assert len(results) > 0
        assert results[0].status == FormValidationStatus.INVALID

    def test_error_visibility(self, widget):
        """Test error label visibility changes."""
        input_widget = TextInput(parent=widget)
        field = FormField(
            "Test",
            input_widget,
            validator=required_validator,
            parent=widget,
        )

        # Initially hidden (check via validation result status)
        assert field._validation_result.status == FormValidationStatus.PENDING

        # After validation failure, error label should be set to visible
        field.validate()
        assert field._validation_result.status == FormValidationStatus.INVALID

        # Note: isVisible() may return false if parent isn't shown,
        # but we can verify the validation UI was updated
        assert field._error_label.text() != ""


# =============================================================================
# FORM ROW TESTS
# =============================================================================


class TestFormRow:
    """Tests for FormRow component."""

    def test_initialization(self, widget, text_input):
        """Test FormRow initializes correctly."""
        row = FormRow("Name", text_input, parent=widget)
        assert row.field_id == "name"
        assert row.widget is text_input

    def test_label_width_default(self, widget):
        """Test FormRow default label width."""
        row = FormRow("Test", TextInput(parent=widget), parent=widget)
        assert row._label_width_val == "md"

    def test_label_width_variants(self, widget):
        """Test FormRow label width variants."""
        for width in ["auto", "sm", "md", "lg"]:
            row = FormRow("Test", TextInput(parent=widget), label_width=width, parent=widget)
            assert row._label_width_val == width

    def test_label_widths_dict(self):
        """Test LabelWidths dictionary values."""
        assert LabelWidths["auto"] == 0
        assert LabelWidths["sm"] == 100
        assert LabelWidths["md"] == 140
        assert LabelWidths["lg"] == 180

    def test_required_marker(self, widget):
        """Test FormRow with required marker."""
        row = FormRow("Email", TextInput(parent=widget), required=True, parent=widget)
        assert row._required
        assert hasattr(row, "_asterisk")

    def test_get_value(self, widget):
        """Test get_value method."""
        input_widget = TextInput(value="test", parent=widget)
        row = FormRow("Test", input_widget, parent=widget)
        assert row.get_value() == "test"

    def test_set_value(self, widget):
        """Test set_value method."""
        input_widget = TextInput(parent=widget)
        row = FormRow("Test", input_widget, parent=widget)
        row.set_value("new_value")
        assert row.get_value() == "new_value"

    def test_validate_with_validator(self, widget):
        """Test validate with validator."""
        input_widget = TextInput(parent=widget)
        row = FormRow(
            "Count",
            input_widget,
            validator=min_value_validator(1),
            parent=widget,
        )

        # Empty should be invalid (not a number)
        result = row.validate()
        assert result.status == FormValidationStatus.INVALID

        # Valid value
        input_widget.set_value("5")
        QApplication.processEvents()
        result = row.validate()
        assert result.status == FormValidationStatus.VALID

    def test_is_valid(self, widget):
        """Test is_valid method."""
        input_widget = TextInput(parent=widget)
        row = FormRow(
            "Test",
            input_widget,
            validator=integer_validator,
            parent=widget,
        )

        input_widget.set_value("abc")
        QApplication.processEvents()

        # Wait for debounce timer
        from PySide6.QtTest import QTest
        QTest.qWait(350)

        assert not row.is_valid()

        input_widget.set_value("42")
        QApplication.processEvents()
        QTest.qWait(350)
        assert row.is_valid()

    def test_clear_validation(self, widget):
        """Test clear_validation method."""
        input_widget = TextInput(parent=widget)
        row = FormRow(
            "Test",
            input_widget,
            validator=required_validator,
            parent=widget,
        )

        row.validate()
        assert row._validation_result.status == FormValidationStatus.INVALID

        row.clear_validation()
        assert row._validation_result.status == FormValidationStatus.VALID


# =============================================================================
# READ ONLY FIELD TESTS
# =============================================================================


class TestReadOnlyField:
    """Tests for ReadOnlyField component."""

    def test_initialization(self, widget):
        """Test ReadOnlyField initializes correctly."""
        field = ReadOnlyField("Label", "value123", parent=widget)
        assert field.get_value() == "value123"

    def test_without_label(self, widget):
        """Test ReadOnlyField without label."""
        field = ReadOnlyField(value="test_value", parent=widget)
        assert field.get_value() == "test_value"

    def test_set_value(self, widget):
        """Test set_value method."""
        field = ReadOnlyField(parent=widget)
        field.set_value("new_value")
        assert field.get_value() == "new_value"

    def test_set_label(self, widget):
        """Test set_label method."""
        field = ReadOnlyField(label="Old", parent=widget)
        field.set_label("New Label")
        assert field._label_text == "New Label"

    def test_copyable_true(self, widget):
        """Test copyable field has copy button."""
        field = ReadOnlyField("Token", "secret", copyable=True, parent=widget)
        assert hasattr(field, "_copy_btn")

    def test_copyable_false(self, widget):
        """Test non-copyable field has no copy button."""
        field = ReadOnlyField("Token", "secret", copyable=False, parent=widget)
        assert not hasattr(field, "_copy_btn")

    def test_copy_clicked_signal(self, widget):
        """Test copy_clicked signal emission."""
        field = ReadOnlyField("Text", "value", copyable=True, parent=widget)
        results = []

        field.copy_clicked.connect(lambda: results.append(True))
        field._on_copy_clicked()

        assert len(results) == 1

    def test_monospace_mode(self, widget):
        """Test monospace mode uses monospace font."""
        field = ReadOnlyField("Code", "print('hello')", monospace=True, parent=widget)
        assert field._monospace
        # Monospace font family should be used
        assert TOKENS_V2.typography.mono in field._value_label.styleSheet()

    def test_selectable_by_default(self, widget):
        """Test text is selectable by default."""
        field = ReadOnlyField(value="selectable text", parent=widget)
        flags = field._value_label.textInteractionFlags()
        assert Qt.TextInteractionFlag.TextSelectableByMouse in flags

    def test_non_selectable(self, widget):
        """Test non-selectable field."""
        field = ReadOnlyField(value="text", select_text=False, parent=widget)
        flags = field._value_label.textInteractionFlags()
        assert Qt.TextInteractionFlag.TextSelectableByMouse not in flags


# =============================================================================
# FORM CONTAINER TESTS
# =============================================================================


class TestFormContainer:
    """Tests for FormContainer component."""

    def test_initialization(self, qapp):
        """Test FormContainer initializes correctly."""
        form = FormContainer()
        assert form.get_fields() == []
        assert form.is_valid()

    def test_add_field(self, widget):
        """Test adding fields to form."""
        form = FormContainer()
        field = FormField("Name", TextInput(parent=widget), parent=widget)

        form.add_field(field)
        assert len(form.get_fields()) == 1
        assert form.get_field("name") is field

    def test_add_multiple_fields(self, widget):
        """Test adding multiple fields."""
        form = FormContainer()
        field1 = FormField("Name", TextInput(parent=widget), parent=widget)
        field2 = FormField("Email", TextInput(parent=widget), parent=widget)

        form.add_field(field1)
        form.add_field(field2)

        assert len(form.get_fields()) == 2
        assert form.get_field("name") is field1
        assert form.get_field("email") is field2

    def test_duplicate_field_id(self, widget):
        """Test duplicate field IDs are stored with unique keys."""
        form = FormContainer()
        field1 = FormField("Name", TextInput(parent=widget), field_id="test", parent=widget)
        field2 = FormField("Name", TextInput(parent=widget), field_id="test", parent=widget)

        form.add_field(field1)
        form.add_field(field2)

        # Both fields should be accessible via their internal keys
        assert form.get_field("test") is field1
        assert form.get_field("test_1") is field2

    def test_remove_field(self, widget):
        """Test removing field by ID."""
        form = FormContainer()
        field = FormField("Name", TextInput(parent=widget), parent=widget)

        form.add_field(field)
        assert len(form.get_fields()) == 1

        form.remove_field("name")
        assert len(form.get_fields()) == 0

    def test_validate_all(self, widget):
        """Test validate_all returns results for all fields."""
        form = FormContainer()
        field1 = FormField(
            "Name",
            TextInput(parent=widget),
            validator=required_validator,
            parent=widget,
        )
        field2 = FormField(
            "Email",
            TextInput(value="test@example.com", parent=widget),
            validator=email_validator,
            parent=widget,
        )

        form.add_field(field1)
        form.add_field(field2)

        results = form.validate_all()
        assert len(results) == 2
        assert results[0].status == FormValidationStatus.INVALID
        assert results[1].status == FormValidationStatus.VALID

    def test_is_valid(self, widget):
        """Test is_valid checks all fields."""
        form = FormContainer()
        field1 = FormField(
            "Name",
            TextInput(value="John", parent=widget),
            validator=required_validator,
            parent=widget,
        )
        field2 = FormField(
            "Age",
            TextInput(value="25", parent=widget),
            validator=integer_validator,
            parent=widget,
        )

        form.add_field(field1)
        form.add_field(field2)

        assert form.is_valid()

    def test_is_valid_with_invalid_field(self, widget):
        """Test is_valid returns False with invalid field."""
        form = FormContainer()
        field = FormField(
            "Name",
            TextInput(parent=widget),
            validator=required_validator,
            parent=widget,
        )

        form.add_field(field)
        assert not form.is_valid()

    def test_get_invalid_fields(self, widget):
        """Test get_invalid_fields returns list of invalid field IDs."""
        form = FormContainer()
        field1 = FormField(
            "Valid",
            TextInput(value="ok", parent=widget),
            validator=required_validator,
            parent=widget,
        )
        field2 = FormField(
            "Invalid",
            TextInput(parent=widget),
            validator=required_validator,
            parent=widget,
        )

        form.add_field(field1)
        form.add_field(field2)

        invalid = form.get_invalid_fields()
        assert "invalid" in invalid
        assert "valid" not in invalid

    def test_get_values(self, widget):
        """Test get_values returns dict of all field values."""
        form = FormContainer()
        field1 = FormField("Name", TextInput(value="John", parent=widget), parent=widget)
        field2 = FormField("Age", TextInput(value="25", parent=widget), parent=widget)

        form.add_field(field1)
        form.add_field(field2)

        values = form.get_values()
        assert values["name"] == "John"
        assert values["age"] == "25"

    def test_set_values(self, widget):
        """Test set_values sets multiple field values."""
        form = FormContainer()
        field1 = FormField("Name", TextInput(parent=widget), parent=widget)
        field2 = FormField("Age", TextInput(parent=widget), parent=widget)

        form.add_field(field1)
        form.add_field(field2)

        form.set_values({"name": "Jane", "age": "30"})
        assert field1.get_value() == "Jane"
        assert field2.get_value() == "30"

    def test_clear(self, widget):
        """Test clear clears all field values."""
        form = FormContainer()
        field1 = FormField("Name", TextInput(value="John", parent=widget), parent=widget)
        field2 = FormField("Age", TextInput(value="25", parent=widget), parent=widget)

        form.add_field(field1)
        form.add_field(field2)

        form.clear()
        assert field1.get_value() == ""
        assert field2.get_value() == ""

    def test_clear_validation(self, widget):
        """Test clear_validation clears all field validation states."""
        form = FormContainer()
        field = FormField(
            "Name",
            TextInput(parent=widget),
            validator=required_validator,
            parent=widget,
        )

        form.add_field(field)
        field.validate()
        assert field._validation_result.status == FormValidationStatus.INVALID

        form.clear_validation()
        assert field._validation_result.status == FormValidationStatus.VALID

    def test_form_validation_changed_signal(self, widget):
        """Test form_validation_changed signal emission."""
        form = FormContainer()
        field = FormField(
            "Name",
            TextInput(parent=widget),
            validator=required_validator,
            parent=widget,
        )

        results = []
        form.form_validation_changed.connect(lambda v: results.append(v))

        form.add_field(field)
        field.validate()

        assert len(results) > 0

    def test_value_changed_signal(self, widget):
        """Test value_changed signal emission with field_id."""
        form = FormContainer()
        field = FormField("Name", TextInput(parent=widget), parent=widget)

        results = []
        form.value_changed.connect(lambda fid, val: results.append((fid, val)))

        form.add_field(field)
        field.set_value("test")
        QApplication.processEvents()

        # Should have received field_id and value
        assert any(r[0] == "name" for r in results)

    def test_scroll_area(self, qapp):
        """Test scroll_area property."""
        form = FormContainer()
        assert form.scroll_area is not None

    def test_content_widget(self, qapp):
        """Test content_widget property."""
        form = FormContainer()
        assert form.content_widget is not None

    def test_auto_tab_order(self, widget):
        """Test auto_tab_order sets tab order visually."""
        form = FormContainer()
        field1 = FormField("First", TextInput(parent=widget), parent=widget)
        field2 = FormField("Second", TextInput(parent=widget), parent=widget)
        field3 = FormField("Third", TextInput(parent=widget), parent=widget)

        form.add_field(field1)
        form.add_field(field2)
        form.add_field(field3)

        # Should not raise
        form.auto_tab_order()

    def test_set_tab_order(self, widget):
        """Test set_tab_order sets explicit tab order."""
        form = FormContainer()
        field1 = FormField("First", TextInput(parent=widget), parent=widget)
        field2 = FormField("Second", TextInput(parent=widget), parent=widget)
        field3 = FormField("Third", TextInput(parent=widget), parent=widget)

        form.add_field(field1)
        form.add_field(field2)
        form.add_field(field3)

        # Custom order
        form.set_tab_order(["third", "first", "second"])

        # Should not raise
        assert form.get_field("third") is not None


# =============================================================================
# FIELDSET TESTS
# =============================================================================


class TestFieldset:
    """Tests for Fieldset component."""

    def test_initialization(self, widget):
        """Test Fieldset initializes correctly."""
        fieldset = Fieldset("Section Title", parent=widget)
        assert fieldset.title() == "Section Title"
        assert not fieldset.is_collapsed()

    def test_initial_collapsed_state(self, widget):
        """Test Fieldset with initial collapsed state."""
        fieldset = Fieldset("Title", collapsed=True, parent=widget)
        assert fieldset.is_collapsed()
        assert not fieldset._content_container.isVisible()

    def test_non_collapsible(self, widget):
        """Test non-collapsible fieldset."""
        fieldset = Fieldset("Title", collapsible=False, parent=widget)
        # Should always be expanded
        assert not fieldset.is_collapsed()

    def test_set_collapsed(self, widget):
        """Test set_collapsed method."""
        fieldset = Fieldset("Title", parent=widget)
        assert not fieldset.is_collapsed()

        fieldset.set_collapsed(True)
        assert fieldset.is_collapsed()

        fieldset.set_collapsed(False)
        assert not fieldset.is_collapsed()

    def test_toggle(self, widget):
        """Test toggle method."""
        fieldset = Fieldset("Title", parent=widget)
        initial = fieldset.is_collapsed()

        fieldset.toggle()
        assert fieldset.is_collapsed() != initial

        fieldset.toggle()
        assert fieldset.is_collapsed() == initial

    def test_add_field(self, widget):
        """Test adding field to fieldset."""
        fieldset = Fieldset("Section", parent=widget)
        field = FormField("Name", TextInput(parent=widget), parent=widget)

        fieldset.add_field(field)
        assert len(fieldset.fields) == 1

    def test_add_widget(self, widget):
        """Test adding any widget to fieldset."""
        fieldset = Fieldset("Section", parent=widget)
        label = QLabel("Test", parent=widget)

        fieldset.add_widget(label)
        assert len(fieldset.fields) == 1

    def test_remove_field(self, widget):
        """Test removing field by index."""
        fieldset = Fieldset("Section", parent=widget)
        field = FormField("Name", TextInput(parent=widget), parent=widget)

        fieldset.add_field(field)
        assert len(fieldset.fields) == 1

        fieldset.remove_field(0)
        assert len(fieldset.fields) == 0

    def test_clear(self, widget):
        """Test clearing all fields."""
        fieldset = Fieldset("Section", parent=widget)
        fieldset.add_field(FormField("A", TextInput(parent=widget), parent=widget))
        fieldset.add_field(FormField("B", TextInput(parent=widget), parent=widget))

        assert len(fieldset.fields) == 2

        fieldset.clear()
        assert len(fieldset.fields) == 0

    def test_set_title(self, widget):
        """Test set_title method."""
        fieldset = Fieldset("Old Title", parent=widget)
        fieldset.set_title("New Title")
        assert fieldset.title() == "New Title"

    def test_header_property(self, widget):
        """Test header property."""
        fieldset = Fieldset("Title", parent=widget)
        assert fieldset.header is not None

    def test_content_container_property(self, widget):
        """Test content_container property."""
        fieldset = Fieldset("Title", parent=widget)
        assert fieldset.content_container is not None

    def test_collapsed_changed_signal(self, widget):
        """Test collapsed_changed signal emission."""
        fieldset = Fieldset("Title", parent=widget)
        results = []

        fieldset.collapsed_changed.connect(lambda v: results.append(v))

        fieldset.set_collapsed(True)
        QApplication.processEvents()

        assert True in results

    def test_field_added_signal(self, widget):
        """Test field_added signal emission."""
        fieldset = Fieldset("Title", parent=widget)
        results = []

        fieldset.field_added.connect(lambda fid: results.append(fid))

        field = FormField("Name", TextInput(parent=widget), field_id="test_field", parent=widget)
        fieldset.add_field(field)

        assert "test_field" in results


# =============================================================================
# FACTORY FUNCTION TESTS
# =============================================================================


class TestFactoryFunctions:
    """Tests for factory functions."""

    def test_create_form_field(self, widget):
        """Test create_form_field factory function."""
        field = create_form_field(
            "Name",
            TextInput(parent=widget),
            required=True,
            field_id="custom",
            parent=widget,
        )
        assert isinstance(field, FormField)
        assert field.field_id == "custom"
        assert field._required

    def test_create_form_row(self, widget):
        """Test create_form_row factory function."""
        row = create_form_row(
            "Email",
            TextInput(parent=widget),
            label_width="lg",
            required=True,
            parent=widget,
        )
        assert isinstance(row, FormRow)
        assert row._label_width_val == "lg"
        assert row._required

    def test_create_read_only_field(self, widget):
        """Test create_read_only_field factory function."""
        field = create_read_only_field(
            label="Token",
            value="abc123",
            copyable=True,
            monospace=True,
            parent=widget,
        )
        assert isinstance(field, ReadOnlyField)
        assert field._copyable
        assert field._monospace

    def test_create_form_container(self):
        """Test create_form_container factory function."""
        form = create_form_container()
        assert isinstance(form, FormContainer)

    def test_create_fieldset(self, widget):
        """Test create_fieldset factory function."""
        fieldset = create_fieldset(
            title="Settings",
            collapsible=True,
            collapsed=False,
            parent=widget,
        )
        assert isinstance(fieldset, Fieldset)
        assert fieldset.title() == "Settings"

"""
Tests for Selection Controls v2 - Epic 5.1 Component Library.

Tests CheckBox, Switch, RadioButton, and RadioGroup components.
"""

import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    CheckBox,
    RadioGroup,
    RadioOrientation,
    RadioButton,
    Switch,
    create_checkbox,
    create_switch,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def parent_widget(qapp) -> QWidget:
    """Parent widget fixture."""
    widget = QWidget()
    yield widget
    widget.close()


# =============================================================================
# CHECKBOX TESTS
# =============================================================================


class TestCheckBox:
    """Tests for CheckBox component."""

    def test_initialization(self, parent_widget):
        """Test checkbox can be initialized."""
        checkbox = CheckBox(text="Test", parent=parent_widget)
        assert checkbox.text() == "Test"
        assert checkbox.isEnabled()

    def test_initial_checked_state(self, parent_widget):
        """Test checkbox initial checked state."""
        checkbox = CheckBox(text="Test", checked=True, parent=parent_widget)
        assert checkbox.isChecked()
        assert checkbox.checkState() == Qt.CheckState.Checked

        checkbox_unchecked = CheckBox(text="Test", checked=False, parent=parent_widget)
        assert not checkbox_unchecked.isChecked()

    def test_initial_disabled_state(self, parent_widget):
        """Test checkbox can be created disabled."""
        checkbox = CheckBox(text="Test", enabled=False, parent=parent_widget)
        assert not checkbox.isEnabled()

    def test_tristate_mode(self, parent_widget):
        """Test tristate checkbox can be enabled."""
        checkbox = CheckBox(text="Test", tristate=True, parent=parent_widget)
        assert checkbox.isTristate()
        assert checkbox.is_tristate()

    def test_tristate_states(self, parent_widget):
        """Test checkbox can have three states."""
        checkbox = CheckBox(text="Test", tristate=True, parent=parent_widget)

        # Set to partially checked
        checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        assert checkbox.checkState() == Qt.CheckState.PartiallyChecked

        # Cycle through states
        checkbox.nextCheckState()
        assert checkbox.checkState() == Qt.CheckState.Checked

        checkbox.nextCheckState()
        assert checkbox.checkState() == Qt.CheckState.Unchecked

    def test_set_tristate(self, parent_widget):
        """Test tristate mode can be toggled."""
        checkbox = CheckBox(text="Test", parent=parent_widget)

        assert not checkbox.is_tristate()

        checkbox.set_tristate(True)
        assert checkbox.is_tristate()
        assert checkbox.isTristate()

        checkbox.set_tristate(False)
        assert not checkbox.is_tristate()

    def test_checked_signal(self, parent_widget):
        """Test checked_changed signal emission."""
        from PySide6.QtWidgets import QApplication

        checkbox = CheckBox(text="Test", parent=parent_widget)
        received = []

        checkbox.checked_changed.connect(lambda checked: received.append(checked))

        checkbox.setChecked(True)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] is True

        checkbox.setChecked(False)
        QApplication.instance().processEvents()

        assert received[-1] is False

    def test_next_check_state_emits_signal(self, parent_widget):
        """Test nextCheckState emits checked_changed signal."""
        from PySide6.QtWidgets import QApplication

        checkbox = CheckBox(text="Test", parent=parent_widget)
        received = []

        checkbox.checked_changed.connect(lambda checked: received.append(checked))

        checkbox.nextCheckState()
        QApplication.instance().processEvents()

        assert len(received) >= 1

    def test_indicator_size(self, parent_widget):
        """Test checkbox has correct indicator size."""
        checkbox = CheckBox(text="Test", parent=parent_widget)
        expected_size = TOKENS_V2.sizes.checkbox_size  # 16px
        assert checkbox._INDICATOR_SIZE == expected_size

    def test_empty_text(self, parent_widget):
        """Test checkbox with no text."""
        checkbox = CheckBox(parent=parent_widget)
        assert checkbox.text() == ""


# =============================================================================
# SWITCH TESTS
# =============================================================================


class TestSwitch:
    """Tests for Switch component."""

    def test_initialization(self, parent_widget):
        """Test switch can be initialized."""
        switch = Switch(text="Test", parent=parent_widget)
        assert not switch.is_checked()

    def test_initial_checked_state(self, parent_widget):
        """Test switch initial checked state."""
        switch = Switch(text="Test", checked=True, parent=parent_widget)
        assert switch.is_checked()

    def test_initial_disabled_state(self, parent_widget):
        """Test switch can be created disabled."""
        switch = Switch(text="Test", enabled=False, parent=parent_widget)
        assert not switch.isEnabled()

    def test_toggle(self, parent_widget):
        """Test switch can be toggled."""
        switch = Switch(text="Test", checked=False, parent=parent_widget)

        assert not switch.is_checked()

        switch.toggle()
        assert switch.is_checked()

        switch.toggle()
        assert not switch.is_checked()

    def test_set_checked(self, parent_widget):
        """Test switch checked state can be set."""
        switch = Switch(text="Test", parent=parent_widget)

        switch.set_checked(True)
        assert switch.is_checked()

        switch.set_checked(False)
        assert not switch.is_checked()

    def test_checked_signal(self, parent_widget):
        """Test checked_changed signal emission."""
        from PySide6.QtWidgets import QApplication

        switch = Switch(text="Test", parent=parent_widget)
        received = []

        switch.checked_changed.connect(lambda checked: received.append(checked))

        switch.toggle()
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] is True

        switch.toggle()
        QApplication.instance().processEvents()

        assert received[-1] is False

    def test_with_on_off_text(self, parent_widget):
        """Test switch with on/off text labels."""
        switch = Switch(
            text="Mode",
            on_text="On",
            off_text="Off",
            checked=False,
            parent=parent_widget
        )

        # Label should show "Mode: Off" when unchecked
        assert "Off" in switch._label.text()

        switch.set_checked(True)
        # Label should show "Mode: On" when checked
        assert "On" in switch._label.text()

    def test_with_only_state_text(self, parent_widget):
        """Test switch with only on/off text (no base text)."""
        switch = Switch(
            on_text="Enabled",
            off_text="Disabled",
            checked=True,
            parent=parent_widget
        )

        # Label should show "Enabled" when checked
        assert switch._label.text() == "Enabled"

        switch.set_checked(False)
        # Label should show "Disabled" when unchecked
        assert switch._label.text() == "Disabled"

    def test_no_label(self, parent_widget):
        """Test switch without label."""
        switch = Switch(parent=parent_widget)
        assert not hasattr(switch, "_label") or not switch._label.text()

    def test_switch_dimensions(self, parent_widget):
        """Test switch has correct dimensions."""
        switch = Switch(parent=parent_widget)
        assert switch.height() == switch._TRACK_HEIGHT
        assert switch._TRACK_WIDTH == 40
        assert switch._TRACK_HEIGHT == 22
        assert switch._THUMB_SIZE == 18

    def test_enabled_state(self, parent_widget):
        """Test switch enabled state."""
        switch = Switch(text="Test", enabled=True, parent=parent_widget)

        assert switch.isEnabled()
        assert switch.is_enabled()

        switch.setEnabled(False)
        assert not switch.isEnabled()
        assert not switch.is_enabled()

    def test_paint_event_called(self, parent_widget):
        """Test paintEvent can be called without errors."""
        from PySide6.QtGui import QPaintEvent

        switch = Switch(text="Test", checked=True, parent=parent_widget)

        # Trigger paint event
        switch.paintEvent(QPaintEvent(switch.rect()))

        # Just ensure no exception was raised
        assert True


# =============================================================================
# RADIO BUTTON TESTS
# =============================================================================


class TestRadioButton:
    """Tests for RadioButton component."""

    def test_initialization(self, parent_widget):
        """Test radio button can be initialized."""
        radio = RadioButton(text="Test", parent=parent_widget)
        assert radio.text() == "Test"
        assert radio.isEnabled()

    def test_initial_checked_state(self, parent_widget):
        """Test radio button initial checked state."""
        radio = RadioButton(text="Test", checked=True, parent=parent_widget)
        assert radio.isChecked()

        radio_unchecked = RadioButton(text="Test", checked=False, parent=parent_widget)
        assert not radio_unchecked.isChecked()

    def test_initial_disabled_state(self, parent_widget):
        """Test radio button can be created disabled."""
        radio = RadioButton(text="Test", enabled=False, parent=parent_widget)
        assert not radio.isEnabled()

    def test_check_state_change(self, parent_widget):
        """Test radio button checked state can change."""
        radio = RadioButton(text="Test", parent=parent_widget)

        assert not radio.isChecked()

        radio.setChecked(True)
        assert radio.isChecked()

        radio.setChecked(False)
        assert not radio.isChecked()

    def test_empty_text(self, parent_widget):
        """Test radio button with no text."""
        radio = RadioButton(parent=parent_widget)
        assert radio.text() == ""

    def test_indicator_size(self, parent_widget):
        """Test radio button has correct indicator size."""
        radio = RadioButton(text="Test", parent=parent_widget)
        expected_size = TOKENS_V2.sizes.checkbox_size  # 16px
        assert radio._INDICATOR_SIZE == expected_size


# =============================================================================
# RADIO GROUP TESTS
# =============================================================================


class TestRadioGroup:
    """Tests for RadioGroup component."""

    def test_initialization_empty(self, parent_widget):
        """Test empty radio group can be created."""
        group = RadioGroup(parent=parent_widget)
        assert len(group._buttons) == 0
        assert group.get_selected() is None

    def test_initialization_with_items(self, parent_widget):
        """Test radio group with initial items."""
        items = [
            {"value": "a", "label": "Option A"},
            {"value": "b", "label": "Option B"},
            {"value": "c", "label": "Option C"},
        ]
        group = RadioGroup(items=items, parent=parent_widget)

        assert len(group._buttons) == 3
        assert group._button_values == ["a", "b", "c"]

    def test_initial_selection(self, parent_widget):
        """Test radio group with initial selection."""
        items = [
            {"value": "a", "label": "Option A"},
            {"value": "b", "label": "Option B"},
        ]
        group = RadioGroup(items=items, selected="b", parent=parent_widget)

        assert group.get_selected() == "b"
        assert group._buttons[1].isChecked()

    def test_get_selected(self, parent_widget):
        """Test getting selected value."""
        items = [{"value": "x", "label": "X"}, {"value": "y", "label": "Y"}]
        group = RadioGroup(items=items, selected="x", parent=parent_widget)

        assert group.get_selected() == "x"

    def test_get_selected_index(self, parent_widget):
        """Test getting selected index."""
        items = [
            {"value": "a", "label": "A"},
            {"value": "b", "label": "B"},
            {"value": "c", "label": "C"},
        ]
        group = RadioGroup(items=items, selected="c", parent=parent_widget)

        assert group.get_selected_index() == 2

    def test_set_selected(self, parent_widget):
        """Test setting selection by value."""
        from PySide6.QtWidgets import QApplication

        items = [
            {"value": "a", "label": "A"},
            {"value": "b", "label": "B"},
        ]
        group = RadioGroup(items=items, parent=parent_widget)

        group.set_selected("b")
        QApplication.instance().processEvents()

        assert group.get_selected() == "b"
        assert group._buttons[1].isChecked()

    def test_set_selected_index(self, parent_widget):
        """Test setting selection by index."""
        from PySide6.QtWidgets import QApplication

        items = [
            {"value": "a", "label": "A"},
            {"value": "b", "label": "B"},
            {"value": "c", "label": "C"},
        ]
        group = RadioGroup(items=items, parent=parent_widget)

        group.set_selected_index(1)
        QApplication.instance().processEvents()

        assert group.get_selected() == "b"

    def test_selection_changed_signal(self, parent_widget):
        """Test selection_changed signal."""
        from PySide6.QtWidgets import QApplication

        items = [{"value": "a", "label": "A"}, {"value": "b", "label": "B"}]
        group = RadioGroup(items=items, parent=parent_widget)

        received = []
        group.selection_changed.connect(lambda value: received.append(value))

        group._buttons[0].click()
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] == "a"

    def test_exclusive_behavior(self, parent_widget):
        """Test only one radio can be selected at a time."""
        from PySide6.QtWidgets import QApplication

        items = [
            {"value": "a", "label": "A"},
            {"value": "b", "label": "B"},
            {"value": "c", "label": "C"},
        ]
        group = RadioGroup(items=items, parent=parent_widget)

        # Select first
        group._buttons[0].click()
        QApplication.instance().processEvents()
        assert group._buttons[0].isChecked()
        assert not group._buttons[1].isChecked()
        assert not group._buttons[2].isChecked()

        # Select second
        group._buttons[1].click()
        QApplication.instance().processEvents()
        assert not group._buttons[0].isChecked()
        assert group._buttons[1].isChecked()
        assert not group._buttons[2].isChecked()

    def test_horizontal_orientation(self, parent_widget):
        """Test horizontal orientation layout."""
        items = [{"value": "a", "label": "A"}, {"value": "b", "label": "B"}]
        group = RadioGroup(items=items, orientation="horizontal", parent=parent_widget)

        assert group._orientation == "horizontal"
        assert isinstance(group.layout(), type(QHBoxLayout()))

    def test_vertical_orientation(self, parent_widget):
        """Test vertical orientation layout."""
        items = [{"value": "a", "label": "A"}, {"value": "b", "label": "B"}]
        group = RadioGroup(items=items, orientation="vertical", parent=parent_widget)

        assert group._orientation == "vertical"
        assert isinstance(group.layout(), type(QVBoxLayout()))

    def test_get_items(self, parent_widget):
        """Test getting items list."""
        items = [
            {"value": "a", "label": "Option A"},
            {"value": "b", "label": "Option B"},
        ]
        group = RadioGroup(items=items, parent=parent_widget)

        retrieved = group.get_items()
        assert len(retrieved) == 2
        assert retrieved[0] == {"value": "a", "label": "Option A"}
        assert retrieved[1] == {"value": "b", "label": "Option B"}

    def test_set_enabled(self, parent_widget):
        """Test enabling/disabling all buttons."""
        items = [
            {"value": "a", "label": "A"},
            {"value": "b", "label": "B"},
        ]
        group = RadioGroup(items=items, enabled=True, parent=parent_widget)

        assert group.is_enabled()
        assert all(btn.isEnabled() for btn in group._buttons)

        group.set_enabled(False)
        assert not group.is_enabled()
        assert all(not btn.isEnabled() for btn in group._buttons)

    def test_initial_disabled_state(self, parent_widget):
        """Test radio group can be created with buttons disabled."""
        items = [{"value": "a", "label": "A"}]
        group = RadioGroup(items=items, enabled=False, parent=parent_widget)

        assert not group.is_enabled()
        assert not group._buttons[0].isEnabled()

    def test_set_selected_invalid_value(self, parent_widget):
        """Test setting invalid selected value is handled gracefully."""
        items = [{"value": "a", "label": "A"}]
        group = RadioGroup(items=items, parent=parent_widget)

        # Should not raise, just log warning
        group.set_selected("invalid")

        # Selection should be unchanged
        assert group.get_selected() is None

    def test_set_selected_invalid_index(self, parent_widget):
        """Test setting invalid selected index is handled gracefully."""
        items = [{"value": "a", "label": "A"}]
        group = RadioGroup(items=items, parent=parent_widget)

        # Should not raise, just log warning
        group.set_selected_index(999)

        # Selection should be unchanged
        assert group.get_selected() is None


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_create_checkbox(self, parent_widget):
        """Test create_checkbox convenience function."""
        checkbox = create_checkbox("Remember me", checked=True, parent=parent_widget)

        assert isinstance(checkbox, CheckBox)
        assert checkbox.text() == "Remember me"
        assert checkbox.isChecked()

    def test_create_switch(self, parent_widget):
        """Test create_switch convenience function."""
        switch = create_switch("Dark mode", checked=False, parent=parent_widget)

        assert isinstance(switch, Switch)
        assert not switch.is_checked()

    def test_create_checkbox_defaults(self, parent_widget):
        """Test create_checkbox with default values."""
        checkbox = create_checkbox("Test", parent=parent_widget)

        assert isinstance(checkbox, CheckBox)
        assert checkbox.text() == "Test"
        assert not checkbox.isChecked()

    def test_create_switch_defaults(self, parent_widget):
        """Test create_switch with default values."""
        switch = create_switch(parent=parent_widget)

        assert isinstance(switch, Switch)
        assert not switch.is_checked()

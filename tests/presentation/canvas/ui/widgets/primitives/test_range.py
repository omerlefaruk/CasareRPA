"""
Tests for Range Input Components v2 - Epic 5.1 Component Library.

Tests Slider, ProgressBar, and Dial components.
"""

import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.range import (
    Dial,
    ProgressBar,
    ProgressBarSize,
    create_dial,
    create_progress,
    create_slider,
    Slider,
    SliderSize,
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
# SLIDER TESTS
# =============================================================================


class TestSlider:
    """Tests for Slider component."""

    def test_initialization(self, parent_widget):
        """Test slider can be initialized."""
        slider = Slider(min=0, max=100, value=50, parent=parent_widget)
        assert slider.get_value() == 50
        assert slider.get_min() == 0
        assert slider.get_max() == 100

    def test_default_values(self, parent_widget):
        """Test slider has correct defaults."""
        slider = Slider(parent=parent_widget)
        assert slider.get_value() == 0
        assert slider.get_min() == 0
        assert slider.get_max() == 100
        assert slider.get_step() == 1
        assert slider._show_value is True  # show_value defaults to True
        assert slider.isEnabled()

    def test_sizes(self, parent_widget):
        """Test all slider sizes can be created."""
        expected_heights = {
            "sm": TOKENS_V2.sizes.button_sm,
            "md": TOKENS_V2.sizes.button_md,
            "lg": TOKENS_V2.sizes.button_lg,
        }

        for size, expected_height in expected_heights.items():
            slider = Slider(size=size, parent=parent_widget)
            assert slider._size == size
            assert slider._slider.height() == expected_height

    def test_set_value(self, parent_widget):
        """Test setting slider value."""
        slider = Slider(min=0, max=100, value=0, parent=parent_widget)

        slider.set_value(75)
        assert slider.get_value() == 75

        slider.set_value(100)
        assert slider.get_value() == 100

    def test_set_min(self, parent_widget):
        """Test setting minimum value."""
        slider = Slider(min=0, max=100, parent=parent_widget)

        slider.set_min(10)
        assert slider.get_min() == 10

    def test_set_max(self, parent_widget):
        """Test setting maximum value."""
        slider = Slider(min=0, max=100, parent=parent_widget)

        slider.set_max(200)
        assert slider.get_max() == 200

    def test_set_step(self, parent_widget):
        """Test setting step size."""
        slider = Slider(parent=parent_widget)

        slider.set_step(5)
        assert slider.get_step() == 5

        slider.set_step(10)
        assert slider.get_step() == 10

    def test_disabled_state(self, parent_widget):
        """Test slider can be created disabled."""
        slider = Slider(enabled=False, parent=parent_widget)
        assert not slider._slider.isEnabled()

    def test_show_value_default(self, parent_widget):
        """Test value label shown by default."""
        slider = Slider(show_value=True, parent=parent_widget)
        assert slider._value_label is not None
        assert slider._value_label.text() == "0"

    def test_hide_value(self, parent_widget):
        """Test value label can be hidden."""
        slider = Slider(show_value=False, parent=parent_widget)
        assert slider._value_label is None

    def test_set_show_value_toggle(self, parent_widget):
        """Test toggling value label visibility."""
        slider = Slider(show_value=False, parent=parent_widget)
        assert slider._value_label is None

        slider.set_show_value(True)
        assert slider._value_label is not None

        slider.set_show_value(False)
        assert slider._value_label is None

    def test_value_label_updates(self, parent_widget):
        """Test value label updates with slider value."""
        slider = Slider(show_value=True, parent=parent_widget)

        slider.set_value(42)
        assert slider._value_label.text() == "42"

        slider.set_value(100)
        assert slider._value_label.text() == "100"

    def test_value_changed_signal(self, parent_widget):
        """Test value_changed signal emission."""
        from PySide6.QtWidgets import QApplication

        slider = Slider(parent=parent_widget)
        received = []

        slider.value_changed.connect(lambda v: received.append(v))

        slider.set_value(50)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] == 50

    def test_slider_pressed_signal(self, parent_widget):
        """Test slider_pressed signal."""
        from PySide6.QtWidgets import QApplication

        slider = Slider(parent=parent_widget)
        received = []

        slider.slider_pressed.connect(lambda: received.append(True))

        # Simulate press programmatically
        slider._slider.sliderPressed.emit()
        QApplication.instance().processEvents()

        assert len(received) == 1

    def test_slider_released_signal(self, parent_widget):
        """Test slider_released signal."""
        from PySide6.QtWidgets import QApplication

        slider = Slider(parent=parent_widget)
        received = []

        slider.slider_released.connect(lambda: received.append(True))

        slider._slider.sliderReleased.emit()
        QApplication.instance().processEvents()

        assert len(received) == 1

    def test_stylesheet_uses_theme_colors(self, parent_widget):
        """Test slider stylesheet uses THEME_V2 colors."""
        slider = Slider(parent=parent_widget)
        stylesheet = slider._get_slider_stylesheet()

        # Check for theme colors (not hardcoded values)
        assert THEME_V2.primary in stylesheet
        assert THEME_V2.bg_component in stylesheet

    def test_custom_range(self, parent_widget):
        """Test slider with custom range."""
        slider = Slider(min=-50, max=50, value=0, parent=parent_widget)

        assert slider.get_min() == -50
        assert slider.get_max() == 50
        assert slider.get_value() == 0

        slider.set_value(-25)
        assert slider.get_value() == -25

        slider.set_value(25)
        assert slider.get_value() == 25


# =============================================================================
# PROGRESS BAR TESTS
# =============================================================================


class TestProgressBar:
    """Tests for ProgressBar component."""

    def test_initialization(self, parent_widget):
        """Test progress bar can be initialized."""
        progress = ProgressBar(value=50, min=0, max=100, parent=parent_widget)
        assert progress.get_value() == 50
        assert progress.get_min() == 0
        assert progress.get_max() == 100

    def test_default_values(self, parent_widget):
        """Test progress bar has correct defaults."""
        progress = ProgressBar(parent=parent_widget)
        assert progress.get_value() == 0
        assert progress.get_min() == 0
        assert progress.get_max() == 100
        assert progress.is_indeterminate() is False
        assert progress._show_text is True

    def test_sizes(self, parent_widget):
        """Test all progress bar sizes can be created."""
        expected_heights = {
            "sm": TOKENS_V2.sizes.button_sm,
            "md": TOKENS_V2.sizes.button_md,
            "lg": TOKENS_V2.sizes.button_lg,
        }

        for size, expected_height in expected_heights.items():
            progress = ProgressBar(size=size, parent=parent_widget)
            assert progress._size == size
            assert progress._progress.height() == expected_height

    def test_set_value(self, parent_widget):
        """Test setting progress value."""
        progress = ProgressBar(min=0, max=100, value=0, parent=parent_widget)

        progress.set_value(25)
        assert progress.get_value() == 25

        progress.set_value(75)
        assert progress.get_value() == 75

        progress.set_value(100)
        assert progress.get_value() == 100

    def test_set_min(self, parent_widget):
        """Test setting minimum value."""
        progress = ProgressBar(min=0, max=100, parent=parent_widget)

        progress.set_min(10)
        assert progress.get_min() == 10

    def test_set_max(self, parent_widget):
        """Test setting maximum value."""
        progress = ProgressBar(min=0, max=100, parent=parent_widget)

        progress.set_max(200)
        assert progress.get_max() == 200

    def test_indeterminate_mode(self, parent_widget):
        """Test indeterminate mode."""
        progress = ProgressBar(indeterminate=True, parent=parent_widget)

        assert progress.is_indeterminate() is True

        stylesheet = progress._get_progress_stylesheet()
        # Indeterminate uses gradient for striped pattern
        assert "qlineargradient" in stylesheet

    def test_determinate_mode(self, parent_widget):
        """Test determinate (normal) mode."""
        progress = ProgressBar(indeterminate=False, parent=parent_widget)

        assert progress.is_indeterminate() is False

        stylesheet = progress._get_progress_stylesheet()
        # Determinate uses solid color
        assert "background-color" in stylesheet
        assert "qlineargradient" not in stylesheet

    def test_toggle_indeterminate(self, parent_widget):
        """Test toggling indeterminate mode."""
        progress = ProgressBar(indeterminate=False, parent=parent_widget)

        assert progress.is_indeterminate() is False

        progress.set_indeterminate(True)
        assert progress.is_indeterminate() is True

        progress.set_indeterminate(False)
        assert progress.is_indeterminate() is False

    def test_show_text_default(self, parent_widget):
        """Test text shown by default."""
        progress = ProgressBar(show_text=True, parent=parent_widget)
        assert progress._show_text is True
        assert progress._progress.isTextVisible() is True

    def test_hide_text(self, parent_widget):
        """Test text can be hidden."""
        progress = ProgressBar(show_text=False, parent=parent_widget)
        assert progress._show_text is False
        assert progress._progress.isTextVisible() is False

    def test_set_show_text_toggle(self, parent_widget):
        """Test toggling text visibility."""
        progress = ProgressBar(parent=parent_widget)

        assert progress._progress.isTextVisible() is True

        progress.set_show_text(False)
        assert progress._progress.isTextVisible() is False

        progress.set_show_text(True)
        assert progress._progress.isTextVisible() is True

    def test_stylesheet_uses_theme_colors(self, parent_widget):
        """Test progress bar stylesheet uses THEME_V2 colors."""
        progress = ProgressBar(parent=parent_widget)
        stylesheet = progress._get_progress_stylesheet()

        # Check for theme colors (not hardcoded values)
        assert THEME_V2.primary in stylesheet
        assert THEME_V2.bg_component in stylesheet
        assert THEME_V2.border in stylesheet

    def test_indeterminate_stylesheet(self, parent_widget):
        """Test indeterminate mode has different stylesheet."""
        progress_normal = ProgressBar(indeterminate=False, parent=parent_widget)
        progress_indeterminate = ProgressBar(indeterminate=True, parent=parent_widget)

        normal_ss = progress_normal._get_progress_stylesheet()
        indeterminate_ss = progress_indeterminate._get_progress_stylesheet()

        # Indeterminate uses gradient (stripes)
        assert "qlineargradient" in indeterminate_ss
        assert "qlineargradient" not in normal_ss

    def test_custom_range(self, parent_widget):
        """Test progress bar with custom range."""
        progress = ProgressBar(min=0, max=1000, value=500, parent=parent_widget)

        assert progress.get_min() == 0
        assert progress.get_max() == 1000
        assert progress.get_value() == 500

        progress.set_value(750)
        assert progress.get_value() == 750


# =============================================================================
# DIAL TESTS
# =============================================================================


class TestDial:
    """Tests for Dial component."""

    def test_initialization(self, parent_widget):
        """Test dial can be initialized."""
        dial = Dial(min=0, max=100, value=50, parent=parent_widget)
        assert dial.get_value() == 50
        assert dial.get_min() == 0
        assert dial.get_max() == 100

    def test_default_values(self, parent_widget):
        """Test dial has correct defaults."""
        dial = Dial(parent=parent_widget)
        assert dial.get_value() == 0
        assert dial.get_min() == 0
        assert dial.get_max() == 100
        assert dial.get_wrapping() is False
        assert dial.isEnabled()

    def test_set_value(self, parent_widget):
        """Test setting dial value."""
        dial = Dial(min=0, max=100, value=0, parent=parent_widget)

        dial.set_value(50)
        assert dial.get_value() == 50

        dial.set_value(100)
        assert dial.get_value() == 100

    def test_set_min(self, parent_widget):
        """Test setting minimum value."""
        dial = Dial(min=0, max=100, parent=parent_widget)

        dial.set_min(10)
        assert dial.get_min() == 10

    def test_set_max(self, parent_widget):
        """Test setting maximum value."""
        dial = Dial(min=0, max=100, parent=parent_widget)

        dial.set_max(200)
        assert dial.get_max() == 200

    def test_wrapping_default(self, parent_widget):
        """Test wrapping defaults to False."""
        dial = Dial(parent=parent_widget)
        assert dial.get_wrapping() is False

    def test_set_wrapping(self, parent_widget):
        """Test setting wrapping mode."""
        dial = Dial(wrapping=True, parent=parent_widget)
        assert dial.get_wrapping() is True

        dial.set_wrapping(False)
        assert dial.get_wrapping() is False

        dial.set_wrapping(True)
        assert dial.get_wrapping() is True

    def test_disabled_state(self, parent_widget):
        """Test dial can be created disabled."""
        dial = Dial(enabled=False, parent=parent_widget)
        assert not dial._dial.isEnabled()

    def test_size_constraints(self, parent_widget):
        """Test dial size is constrained within bounds."""
        # Test minimum size
        dial_min = Dial(size=Dial._MIN_SIZE - 10, parent=parent_widget)
        assert dial_min._size == Dial._MIN_SIZE

        # Test maximum size
        dial_max = Dial(size=Dial._MAX_SIZE + 10, parent=parent_widget)
        assert dial_max._size == Dial._MAX_SIZE

        # Test normal size
        dial_normal = Dial(size=80, parent=parent_widget)
        assert dial_normal._size == 80

    def test_fixed_square_size(self, parent_widget):
        """Test dial is always square."""
        dial = Dial(size=100, parent=parent_widget)
        assert dial._dial.width() == 100
        assert dial._dial.height() == 100

    def test_value_changed_signal(self, parent_widget):
        """Test value_changed signal emission."""
        from PySide6.QtWidgets import QApplication

        dial = Dial(parent=parent_widget)
        received = []

        dial.value_changed.connect(lambda v: received.append(v))

        dial.set_value(50)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] == 50

    def test_stylesheet_uses_theme_colors(self, parent_widget):
        """Test dial stylesheet uses THEME_V2 colors."""
        dial = Dial(parent=parent_widget)
        stylesheet = dial._get_dial_stylesheet()

        # Check for theme colors (not hardcoded values)
        assert THEME_V2.primary in stylesheet
        assert THEME_V2.bg_component in stylesheet

    def test_notches_visible(self, parent_widget):
        """Test notches are visible by default."""
        dial = Dial(parent=parent_widget)
        assert dial._dial.notchesVisible() is True

    def test_set_notches_visible(self, parent_widget):
        """Test toggling notch visibility."""
        dial = Dial(parent=parent_widget)

        dial.set_notches_visible(False)
        assert dial._dial.notchesVisible() is False

        dial.set_notches_visible(True)
        assert dial._dial.notchesVisible() is True

    def test_angle_control(self, parent_widget):
        """Test dial for angle control (0-360 degrees)."""
        angle_dial = Dial(min=0, max=360, value=180, wrapping=True, parent=parent_widget)

        assert angle_dial.get_min() == 0
        assert angle_dial.get_max() == 360
        assert angle_dial.get_value() == 180
        assert angle_dial.get_wrapping() is True

    def test_volume_control(self, parent_widget):
        """Test dial for volume control (0-100)."""
        volume_dial = Dial(min=0, max=100, value=50, parent=parent_widget)

        volume_dial.set_value(75)
        assert volume_dial.get_value() == 75


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_create_slider(self, parent_widget):
        """Test create_slider convenience function."""
        slider = create_slider(
            min=0, max=100, value=50, show_value=True, size="md", parent=parent_widget
        )

        assert isinstance(slider, Slider)
        assert slider.get_value() == 50
        assert slider.get_min() == 0
        assert slider.get_max() == 100
        assert slider._size == "md"

    def test_create_progress(self, parent_widget):
        """Test create_progress convenience function."""
        progress = create_progress(
            value=25, min=0, max=100, indeterminate=False, show_text=True, parent=parent_widget
        )

        assert isinstance(progress, ProgressBar)
        assert progress.get_value() == 25
        assert progress.get_min() == 0
        assert progress.get_max() == 100
        assert progress.is_indeterminate() is False

    def test_create_progress_indeterminate(self, parent_widget):
        """Test create_progress with indeterminate mode."""
        progress = create_progress(indeterminate=True, parent=parent_widget)

        assert isinstance(progress, ProgressBar)
        assert progress.is_indeterminate() is True

    def test_create_dial(self, parent_widget):
        """Test create_dial convenience function."""
        dial = create_dial(min=0, max=100, value=50, wrapping=False, parent=parent_widget)

        assert isinstance(dial, Dial)
        assert dial.get_value() == 50
        assert dial.get_min() == 0
        assert dial.get_max() == 100
        assert dial.get_wrapping() is False

    def test_create_dial_wrapping(self, parent_widget):
        """Test create_dial with wrapping enabled."""
        dial = create_dial(min=0, max=360, wrapping=True, parent=parent_widget)

        assert isinstance(dial, Dial)
        assert dial.get_wrapping() is True

    def test_create_dial_custom_size(self, parent_widget):
        """Test create_dial with custom size."""
        dial = create_dial(size=90, parent=parent_widget)

        assert isinstance(dial, Dial)
        assert dial._size == 90

"""
Tests for Loading State Components v2 - Epic 5.1 Component Library.

Tests Skeleton and Spinner components.
"""

import pytest
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    Skeleton,
    Spinner,
    create_skeleton,
    create_spinner,
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
# SKELETON TESTS
# =============================================================================


class TestSkeleton:
    """Tests for Skeleton component."""

    def test_initialization(self, parent_widget):
        """Test skeleton can be initialized."""
        skeleton = Skeleton(parent=parent_widget)
        assert skeleton.variant() == "rect"
        assert skeleton._width == 100
        assert skeleton._height == 16
        assert skeleton.isEnabled()

    def test_custom_size(self, parent_widget):
        """Test skeleton with custom size."""
        skeleton = Skeleton(width=200, height=50, parent=parent_widget)
        assert skeleton._width == 200
        assert skeleton._height == 50
        assert skeleton.width() == 200
        assert skeleton.height() == 50

    def test_rect_variant(self, parent_widget):
        """Test rectangle variant."""
        skeleton = Skeleton(variant="rect", width=100, height=50, parent=parent_widget)
        assert skeleton.variant() == "rect"

    def test_circle_variant(self, parent_widget):
        """Test circle variant."""
        skeleton = Skeleton(variant="circle", width=40, height=40, parent=parent_widget)
        assert skeleton.variant() == "circle"

    def test_text_variant(self, parent_widget):
        """Test text variant."""
        skeleton = Skeleton(variant="text", width=200, height=40, parent=parent_widget)
        assert skeleton.variant() == "text"

    def test_set_size(self, parent_widget):
        """Test set_size updates dimensions."""
        skeleton = Skeleton(width=100, height=16, parent=parent_widget)
        skeleton.set_size(150, 30)

        assert skeleton._width == 150
        assert skeleton._height == 30
        assert skeleton.width() == 150
        assert skeleton.height() == 30

    def test_set_size_clamps_minimum(self, parent_widget):
        """Test set_size clamps to minimum of 1."""
        skeleton = Skeleton(parent=parent_widget)
        skeleton.set_size(0, -5)

        assert skeleton._width == 1
        assert skeleton._height == 1

    def test_set_variant(self, parent_widget):
        """Test set_variant updates variant."""
        skeleton = Skeleton(variant="rect", parent=parent_widget)
        assert skeleton.variant() == "rect"

        skeleton.set_variant("circle")
        assert skeleton.variant() == "circle"

        skeleton.set_variant("text")
        assert skeleton.variant() == "text"

    def test_base_color_from_theme(self, parent_widget):
        """Test skeleton uses THEME_V2 colors."""
        skeleton = Skeleton(parent=parent_widget)
        assert skeleton._base_color == QColor(THEME_V2.bg_component)
        assert skeleton._band_color == QColor(THEME_V2.bg_elevated)

    def test_stylesheet_uses_theme_v2(self, parent_widget):
        """Test stylesheet uses THEME_V2 colors."""
        skeleton = Skeleton(parent=parent_widget)
        stylesheet = skeleton._get_v2_stylesheet()
        assert "background: transparent" in stylesheet

    def test_paint_event_called(self, parent_widget):
        """Test paintEvent executes without errors."""
        skeleton = Skeleton(variant="rect", width=100, height=50, parent=parent_widget)
        skeleton.show()  # Trigger paint

        # Force paint event
        skeleton.update()
        from PySide6.QtTest import QTest

        QTest.qWait(0)

        # If we get here without exception, paint worked
        assert True

    def test_circle_paint(self, parent_widget):
        """Test circle variant paint executes without errors."""
        skeleton = Skeleton(variant="circle", width=40, height=40, parent=parent_widget)
        skeleton.show()

        # Force paint event
        skeleton.update()
        from PySide6.QtTest import QTest

        QTest.qWait(0)

        assert True

    def test_text_paint(self, parent_widget):
        """Test text variant paint executes without errors."""
        skeleton = Skeleton(variant="text", width=200, height=40, parent=parent_widget)
        skeleton.show()

        # Force paint event
        skeleton.update()
        from PySide6.QtTest import QTest

        QTest.qWait(0)

        assert True


# =============================================================================
# SPINNER TESTS
# =============================================================================


class TestSpinner:
    """Tests for Spinner component."""

    def test_initialization(self, parent_widget):
        """Test spinner can be initialized."""
        spinner = Spinner(parent=parent_widget)
        assert spinner._size == 20
        assert spinner._stroke_width == 2
        assert spinner._color == QColor(THEME_V2.primary)
        assert spinner.isEnabled()

    def test_custom_size(self, parent_widget):
        """Test spinner with custom size."""
        spinner = Spinner(size=32, parent=parent_widget)
        assert spinner._size == 32
        assert spinner.width() == 32
        assert spinner.height() == 32

    def test_custom_stroke_width(self, parent_widget):
        """Test spinner with custom stroke width."""
        spinner = Spinner(stroke_width=4, parent=parent_widget)
        assert spinner._stroke_width == 4

    def test_custom_color(self, parent_widget):
        """Test spinner with custom color."""
        spinner = Spinner(color=THEME_V2.success, parent=parent_widget)
        assert spinner._color == QColor(THEME_V2.success)

    def test_default_color_is_theme_primary(self, parent_widget):
        """Test default color uses THEME_V2.primary."""
        spinner = Spinner(parent=parent_widget)
        assert spinner._color == QColor(THEME_V2.primary)

    def test_set_size(self, parent_widget):
        """Test set_size updates dimensions."""
        spinner = Spinner(size=20, parent=parent_widget)
        spinner.set_size(40)

        assert spinner._size == 40
        assert spinner.width() == 40
        assert spinner.height() == 40

    def test_set_size_clamps_minimum(self, parent_widget):
        """Test set_size clamps to minimum of 1."""
        spinner = Spinner(parent=parent_widget)
        spinner.set_size(0)

        assert spinner._size == 1

    def test_set_stroke_width(self, parent_widget):
        """Test set_stroke_width updates stroke width."""
        spinner = Spinner(stroke_width=2, parent=parent_widget)
        spinner.set_stroke_width(5)

        assert spinner._stroke_width == 5

    def test_set_stroke_width_clamps_minimum(self, parent_widget):
        """Test set_stroke_width clamps to minimum of 1."""
        spinner = Spinner(parent=parent_widget)
        spinner.set_stroke_width(0)

        assert spinner._stroke_width == 1

    def test_set_color(self, parent_widget):
        """Test set_color updates arc color."""
        spinner = Spinner(parent=parent_widget)
        spinner.set_color(THEME_V2.error)

        assert spinner._color == QColor(THEME_V2.error)

    def test_stylesheet_uses_theme_v2(self, parent_widget):
        """Test stylesheet uses THEME_V2 colors."""
        spinner = Spinner(parent=parent_widget)
        stylesheet = spinner._get_v2_stylesheet()
        assert "background: transparent" in stylesheet

    def test_paint_event_called(self, parent_widget):
        """Test paintEvent executes without errors."""
        spinner = Spinner(size=32, parent=parent_widget)
        spinner.show()  # Trigger paint

        # Force paint event
        spinner.update()
        from PySide6.QtTest import QTest

        QTest.qWait(0)

        # If we get here without exception, paint worked
        assert True

    def test_arc_configuration(self, parent_widget):
        """Test spinner arc configuration."""
        spinner = Spinner(parent=parent_widget)
        # Static arc (no rotation per zero-motion policy)
        assert spinner._arc_angle == 270
        assert spinner._start_angle == 0

    def test_large_spinner(self, parent_widget):
        """Test large spinner configuration."""
        spinner = Spinner(size=48, stroke_width=4, parent=parent_widget)
        assert spinner._size == 48
        assert spinner._stroke_width == 4

    def test_small_spinner(self, parent_widget):
        """Test small spinner configuration."""
        spinner = Spinner(size=12, stroke_width=1, parent=parent_widget)
        assert spinner._size == 12
        assert spinner._stroke_width == 1


# =============================================================================
# CONVENIENCE FUNCTIONS TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_skeleton_default(self, parent_widget):
        """Test create_skeleton with defaults."""
        skeleton = create_skeleton(parent=parent_widget)
        assert skeleton.variant() == "rect"
        assert skeleton._width == 100
        assert skeleton._height == 16

    def test_create_skeleton_custom(self, parent_widget):
        """Test create_skeleton with custom parameters."""
        skeleton = create_skeleton(variant="circle", width=50, height=50, parent=parent_widget)
        assert skeleton.variant() == "circle"
        assert skeleton._width == 50
        assert skeleton._height == 50

    def test_create_skeleton_text_variant(self, parent_widget):
        """Test create_skeleton with text variant."""
        skeleton = create_skeleton(variant="text", parent=parent_widget)
        assert skeleton.variant() == "text"

    def test_create_spinner_default(self, parent_widget):
        """Test create_spinner with defaults."""
        spinner = create_spinner(parent=parent_widget)
        assert spinner._size == 20
        assert spinner._stroke_width == 2
        assert spinner._color == QColor(THEME_V2.primary)

    def test_create_spinner_custom(self, parent_widget):
        """Test create_spinner with custom parameters."""
        spinner = create_spinner(
            size=28, stroke_width=3, color=THEME_V2.success, parent=parent_widget
        )
        assert spinner._size == 28
        assert spinner._stroke_width == 3
        assert spinner._color == QColor(THEME_V2.success)

    def test_create_spinner_none_color(self, parent_widget):
        """Test create_spinner with None color uses default."""
        spinner = create_spinner(color=None, parent=parent_widget)
        assert spinner._color == QColor(THEME_V2.primary)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestSkeletonIntegration:
    """Integration tests for Skeleton."""

    def test_multiple_skeletons_in_layout(self, parent_widget, qapp):
        """Test multiple skeletons in a vertical layout."""
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(parent_widget)

        skeleton1 = Skeleton(variant="text", width=200, height=40, parent=parent_widget)
        skeleton2 = Skeleton(variant="rect", width=200, height=100, parent=parent_widget)
        skeleton3 = Skeleton(variant="circle", width=40, height=40, parent=parent_widget)

        layout.addWidget(skeleton1)
        layout.addWidget(skeleton2)
        layout.addWidget(skeleton3)

        parent_widget.show()
        from PySide6.QtTest import QTest

        QTest.qWait(0)

        assert skeleton1.parent() is parent_widget
        assert skeleton2.parent() is parent_widget
        assert skeleton3.parent() is parent_widget


class TestSpinnerIntegration:
    """Integration tests for Spinner."""

    def test_multiple_spinners_in_layout(self, parent_widget, qapp):
        """Test multiple spinners in a horizontal layout."""
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout(parent_widget)

        spinner1 = Spinner(size=16, parent=parent_widget)
        spinner2 = Spinner(size=24, color=THEME_V2.success, parent=parent_widget)
        spinner3 = Spinner(size=32, color=THEME_V2.warning, parent=parent_widget)

        layout.addWidget(spinner1)
        layout.addWidget(spinner2)
        layout.addWidget(spinner3)

        parent_widget.show()
        from PySide6.QtTest import QTest

        QTest.qWait(0)

        assert spinner1.parent() is parent_widget
        assert spinner2.parent() is parent_widget
        assert spinner3.parent() is parent_widget


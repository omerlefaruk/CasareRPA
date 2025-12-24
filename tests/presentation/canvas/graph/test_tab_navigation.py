"""
Unit tests for tab navigation functionality.

Tests the TabNavigationInterceptor class and related functions for
proper tab key navigation between node widget parameters.
"""

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
)

from casare_rpa.presentation.canvas.graph.tab_navigation import (
    TabNavigationInterceptor,
    _get_focusable_from_container,
    _is_button,
    _is_focusable_input,
    install_tab_navigation,
    install_tab_navigation_on_widgets,
    navigate_to_next,
    navigate_to_previous,
    remove_tab_navigation,
)


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture(autouse=True)
def process_events(qapp):
    """Process Qt events after each test."""
    yield
    qapp.processEvents()


class TestIsFocusableInput:
    """Tests for _is_focusable_input function."""

    def test_none_widget_returns_false(self):
        """None input should return False."""
        assert _is_focusable_input(None) is False

    def test_line_edit_is_focusable(self, qapp):
        """QLineEdit should be focusable."""
        widget = QLineEdit()
        widget.setEnabled(True)
        widget.setVisible(True)
        assert _is_focusable_input(widget) is True

    def test_combo_box_is_focusable(self, qapp):
        """QComboBox should be focusable."""
        widget = QComboBox()
        widget.setEnabled(True)
        widget.setVisible(True)
        assert _is_focusable_input(widget) is True

    def test_spin_box_is_focusable(self, qapp):
        """QSpinBox should be focusable."""
        widget = QSpinBox()
        widget.setEnabled(True)
        widget.setVisible(True)
        assert _is_focusable_input(widget) is True

    def test_disabled_widget_not_focusable(self, qapp):
        """Disabled widget should not be focusable."""
        widget = QLineEdit()
        widget.setEnabled(False)
        widget.setVisible(True)
        assert _is_focusable_input(widget) is False

    def test_hidden_widget_not_focusable(self, qapp):
        """Hidden widget should not be focusable."""
        widget = QLineEdit()
        widget.setEnabled(True)
        widget.setVisible(False)
        assert _is_focusable_input(widget) is False

    def test_button_not_focusable_for_input(self, qapp):
        """Button should not be considered focusable input."""
        widget = QPushButton()
        widget.setEnabled(True)
        widget.setVisible(True)
        assert _is_focusable_input(widget) is False

    def test_no_focus_policy_not_focusable(self, qapp):
        """Widget with NoFocus policy should not be focusable."""
        widget = QLineEdit()
        widget.setEnabled(True)
        widget.setVisible(True)
        widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        assert _is_focusable_input(widget) is False


class TestIsButton:
    """Tests for _is_button function."""

    def test_push_button_is_button(self, qapp):
        """QPushButton should be detected as button."""
        widget = QPushButton()
        assert _is_button(widget) is True

    def test_line_edit_is_not_button(self, qapp):
        """QLineEdit should not be detected as button."""
        widget = QLineEdit()
        assert _is_button(widget) is False


class TestGetFocusableFromContainer:
    """Tests for _get_focusable_from_container function."""

    def test_none_container_returns_empty(self):
        """None container should return empty list."""
        assert _get_focusable_from_container(None) == []

    def test_line_edit_returns_line_edit(self, qapp):
        """QLineEdit should return itself."""
        widget = QLineEdit()
        result = _get_focusable_from_container(widget)
        assert widget in result
        assert len(result) == 1

    def test_button_skipped(self, qapp):
        """Button should be skipped."""
        widget = QPushButton()
        result = _get_focusable_from_container(widget)
        assert widget not in result


class TestTabNavigationInterceptorNavigation:
    """Tests for TabNavigationInterceptor navigation methods."""

    def test_forward_navigation_from_first(self, qapp):
        """Tab from first widget should go to second."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 0)
        interceptor._navigate_forward()

        assert interceptor._current_index == 1

    def test_forward_navigation_from_last_wraps(self, qapp):
        """Tab from last widget should wrap to first."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 2)
        interceptor._navigate_forward()

        assert interceptor._current_index == 0

    def test_backward_navigation_from_second(self, qapp):
        """Shift+Tab from second widget should go to first."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 1)
        interceptor._navigate_backward()

        assert interceptor._current_index == 0

    def test_backward_navigation_from_first_wraps(self, qapp):
        """Shift+Tab from first widget should wrap to last."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 0)
        interceptor._navigate_backward()

        assert interceptor._current_index == 2

    def test_skip_disabled_forward(self, qapp):
        """Tab should skip disabled widgets."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w2.setEnabled(False)
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 0)
        interceptor._navigate_forward()

        assert interceptor._current_index == 2

    def test_skip_disabled_backward(self, qapp):
        """Shift+Tab should skip disabled widgets."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w1.setEnabled(False)
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 2)
        interceptor._navigate_backward()

        assert interceptor._current_index == 1

    def test_skip_hidden_forward(self, qapp):
        """Tab should skip hidden widgets."""
        w1 = QLineEdit()
        w2 = QLineEdit()
        w2.setVisible(False)
        w3 = QLineEdit()

        widgets = [w1, w2, w3]
        interceptor = TabNavigationInterceptor(widgets, 0)
        interceptor._navigate_forward()

        assert interceptor._current_index == 2

    def test_all_disabled_no_infinite_loop(self, qapp):
        """All disabled widgets should not cause infinite loop."""
        w1 = QLineEdit()
        w1.setEnabled(False)
        w2 = QLineEdit()
        w2.setEnabled(False)

        widgets = [w1, w2]
        interceptor = TabNavigationInterceptor(widgets, 0)

        interceptor._navigate_forward()
        interceptor._navigate_backward()


class TestTabNavigationInterceptorEventFilter:
    """Tests for TabNavigationInterceptor eventFilter method."""

    def test_tab_key_returns_true(self, qapp):
        """Tab key press should return True (handled)."""
        w1 = QLineEdit()
        w2 = QLineEdit()

        widgets = [w1, w2]
        interceptor = TabNavigationInterceptor(widgets, 0)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
        result = interceptor.eventFilter(w1, event)

        assert result is True

    def test_backtab_key_returns_true(self, qapp):
        """Shift+Tab key press should return True (handled)."""
        w1 = QLineEdit()
        w2 = QLineEdit()

        widgets = [w1, w2]
        interceptor = TabNavigationInterceptor(widgets, 1)
        event = QKeyEvent(
            QEvent.Type.KeyPress, Qt.Key.Key_Backtab, Qt.KeyboardModifier.ShiftModifier
        )
        result = interceptor.eventFilter(w2, event)

        assert result is True

    def test_other_key_returns_false(self, qapp):
        """Non-tab key press should return False (passed through)."""
        w1 = QLineEdit()
        w2 = QLineEdit()

        widgets = [w1, w2]
        interceptor = TabNavigationInterceptor(widgets, 0)
        event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        result = interceptor.eventFilter(w1, event)

        assert result is False

    def test_non_key_event_returns_false(self, qapp):
        """Non-key event should return False (passed through)."""
        w1 = QLineEdit()

        widgets = [w1]
        interceptor = TabNavigationInterceptor(widgets, 0)
        event = QEvent(QEvent.Type.MouseButtonPress)
        result = interceptor.eventFilter(w1, event)

        assert result is False


class TestNavigateToNext:
    """Tests for navigate_to_next function."""

    def test_navigate_to_next_no_widgets(self, qapp):
        """navigate_to_next with no widgets should return False."""

        class MockNode:
            def widgets(self):
                return {}

        node = MockNode()
        result = navigate_to_next(node)
        assert result is False


class TestNavigateToPrevious:
    """Tests for navigate_to_previous function."""

    def test_navigate_to_previous_no_widgets(self, qapp):
        """navigate_to_previous with no widgets should return False."""

        class MockNode:
            def widgets(self):
                return {}

        node = MockNode()
        result = navigate_to_previous(node)
        assert result is False


class TestRemoveTabNavigation:
    """Tests for remove_tab_navigation function."""

    def test_remove_tab_navigation_removes_interceptors(self, qapp):
        """remove_tab_navigation should remove event filters."""
        w1 = QLineEdit()
        w2 = QLineEdit()

        widgets = [w1, w2]
        install_tab_navigation_on_widgets(widgets)

        assert len(w1.findChildren(TabNavigationInterceptor)) == 1
        assert len(w2.findChildren(TabNavigationInterceptor)) == 1

        class MockNodeBaseWidget:
            def __init__(self, custom_widget):
                self._custom_widget = custom_widget

            def get_custom_widget(self):
                return self._custom_widget

        class MockNode:
            def widgets(self):
                return {
                    "w1": MockNodeBaseWidget(w1),
                    "w2": MockNodeBaseWidget(w2),
                }

        node = MockNode()
        remove_tab_navigation(node)

        assert len(w1.findChildren(TabNavigationInterceptor)) == 0
        assert len(w2.findChildren(TabNavigationInterceptor)) == 0


class TestInstallTabNavigation:
    """Tests for install_tab_navigation function."""

    def test_install_tab_navigation_collects_widgets(self, qapp):
        """install_tab_navigation should collect widgets from node."""
        w1 = QLineEdit()
        w2 = QLineEdit()

        class MockNodeBaseWidget:
            def __init__(self, custom_widget):
                self._custom_widget = custom_widget

            def get_custom_widget(self):
                return self._custom_widget

        class MockNode:
            def widgets(self):
                return {
                    "w1": MockNodeBaseWidget(w1),
                    "w2": MockNodeBaseWidget(w2),
                }

        node = MockNode()
        install_tab_navigation(node)

        assert len(w1.findChildren(TabNavigationInterceptor)) == 1
        assert len(w2.findChildren(TabNavigationInterceptor)) == 1

    def test_install_tab_navigation_no_widgets(self, qapp):
        """install_tab_navigation with no widgets should not crash."""

        class MockNode:
            def widgets(self):
                return {}

        node = MockNode()
        install_tab_navigation(node)


class TestInstallTabNavigationOnWidgets:
    """Tests for install_tab_navigation_on_widgets function."""

    def test_install_on_empty_list(self, qapp):
        """install_tab_navigation_on_widgets with empty list should not crash."""
        install_tab_navigation_on_widgets([])

    def test_install_on_single_widget(self, qapp):
        """install_tab_navigation_on_widgets with single widget should work."""
        w1 = QLineEdit()

        widgets = [w1]
        install_tab_navigation_on_widgets(widgets)

        assert len(w1.findChildren(TabNavigationInterceptor)) == 1

    def test_install_stores_interceptors(self, qapp):
        """install_tab_navigation_on_widgets should store interceptors on widget."""
        w1 = QLineEdit()
        w2 = QLineEdit()

        widgets = [w1, w2]
        install_tab_navigation_on_widgets(widgets)

        assert hasattr(w1, "_tab_navigation_interceptors")
        assert hasattr(w2, "_tab_navigation_interceptors")
        assert len(w1._tab_navigation_interceptors) == 1
        assert len(w2._tab_navigation_interceptors) == 1

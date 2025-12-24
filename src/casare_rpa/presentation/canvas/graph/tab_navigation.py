"""
Tab Key Navigation for Node Widget Parameters.

This module provides utilities for implementing tab key navigation between
input widgets within node parameters on the canvas.

Features:
- Tab moves focus forward through input widgets in visual order
- Shift+Tab moves focus backward through input widgets
- Buttons (browse, picker) are automatically skipped
- Works with custom widgets (VariableAwareLineEdit, NodeFilePathWidget, etc.)
- Compatible with NodeGraphQt's widget embedding

Usage:
    from casare_rpa.presentation.canvas.graph.tab_navigation import install_tab_navigation

    # After creating a node with all widgets:
    install_tab_navigation(node)

    # Or install on individual widgets for custom navigation:
    install_tab_navigation_on_widgets([widget1, widget2, widget3])
"""

from typing import TYPE_CHECKING, Literal

from loguru import logger
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtWidgets import (
    QAbstractButton,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QSpinBox,
    QTextEdit,
    QWidget,
)

if TYPE_CHECKING:
    from NodeGraphQt import BaseNode


class TabNavigationInterceptor(QObject):
    """
    Event filter that intercepts Tab and Shift+Tab key events to implement
    custom navigation between node widget parameters.

    This class filters key events on focusable input widgets and handles
    tab navigation programmatically when Tab is pressed.

    Note: Event filters are stored on the widget to prevent garbage collection.
    """

    def __init__(
        self, widgets_list: list[QWidget], current_index: int, parent: QObject | None = None
    ) -> None:
        """
        Initialize the tab navigation interceptor.

        Args:
            widgets_list: List of focusable widgets in visual order
            current_index: Index of the widget this interceptor is attached to
            parent: Parent object
        """
        super().__init__(parent)
        self._widgets = widgets_list
        self._current_index = current_index
        self._widget_count = len(widgets_list)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filter key events to implement custom tab navigation.

        Args:
            obj: The object receiving the event
            event: The event being processed

        Returns:
            True if the event was handled, False to pass it through
        """
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Tab:
                self._navigate_forward()
                return True
            elif key == Qt.Key.Key_Backtab:
                self._navigate_backward()
                return True
        return False

    def _navigate_forward(self) -> None:
        """Move focus to the next enabled widget in the list."""
        if not self._widgets:
            return

        next_index = (self._current_index + 1) % self._widget_count
        next_widget = self._widgets[next_index]
        if next_widget and next_widget.isEnabled() and next_widget.isVisible():
            self._current_index = next_index
            next_widget.setFocus(Qt.FocusReason.TabFocusReason)
        elif next_index != self._current_index:
            self._skip_disabled_forward(next_index)

    def _navigate_backward(self) -> None:
        """Move focus to the previous enabled widget in the list."""
        if not self._widgets:
            return

        prev_index = (self._current_index - 1) % self._widget_count
        prev_widget = self._widgets[prev_index]
        if prev_widget and prev_widget.isEnabled() and prev_widget.isVisible():
            self._current_index = prev_index
            prev_widget.setFocus(Qt.FocusReason.BacktabFocusReason)
        elif prev_index != self._current_index:
            self._skip_disabled_backward(prev_index)

    def _skip_disabled_forward(self, start_index: int) -> None:
        """Skip disabled/hidden widgets when navigating forward."""
        checked = set()
        current = start_index
        checked_count = 0
        max_checks = self._widget_count

        while current not in checked and checked_count < max_checks:
            checked.add(current)
            checked_count += 1
            widget = self._widgets[current]
            if widget and widget.isEnabled() and widget.isVisible():
                widget.setFocus(Qt.FocusReason.TabFocusReason)
                return
            current = (current + 1) % self._widget_count
            if current == self._current_index:
                break

    def _skip_disabled_backward(self, start_index: int) -> None:
        """Skip disabled/hidden widgets when navigating backward."""
        checked = set()
        current = start_index
        checked_count = 0
        max_checks = self._widget_count

        while current not in checked and checked_count < max_checks:
            checked.add(current)
            checked_count += 1
            widget = self._widgets[current]
            if widget and widget.isEnabled() and widget.isVisible():
                widget.setFocus(Qt.FocusReason.BacktabFocusReason)
                return
            current = (current - 1) % self._widget_count
            if current == self._current_index:
                break


def _is_focusable_input(widget: QObject) -> bool:
    """
    Check if a widget is a focusable input widget.

    Args:
        widget: The widget to check

    Returns:
        True if the widget accepts text/number input and can receive focus
    """
    if widget is None:
        return False

    if not widget.isWidgetType():
        return False

    if not widget.isEnabled():
        return False

    if not widget.isVisible():
        return False

    if widget.focusPolicy() == Qt.FocusPolicy.NoFocus:
        return False

    return isinstance(widget, QLineEdit | QTextEdit | QPlainTextEdit | QComboBox | QSpinBox)


def _is_button(widget: QObject) -> bool:
    """
    Check if a widget is a button that should be skipped during tab navigation.

    Args:
        widget: The widget to check

    Returns:
        True if the widget is a button type
    """
    return isinstance(widget, QAbstractButton)


def _get_focusable_from_container(container: QWidget | None) -> list[QWidget]:
    """
    Extract focusable widgets from a container widget.

    Some custom widgets contain multiple sub-widgets (e.g., line_edit + button).
    This function extracts only the focusable input widgets.

    Args:
        container: Container widget potentially containing focusable widgets

    Returns:
        List of focusable input widgets found in the container
    """
    from casare_rpa.presentation.canvas.ui.widgets.variable_picker import VariableAwareLineEdit

    focusable: list[QWidget] = []

    if container is None:
        return focusable

    if isinstance(container, VariableAwareLineEdit):
        focusable.append(container)
        return focusable

    if isinstance(container, QLineEdit):
        focusable.append(container)
        return focusable

    for child in container.findChildren(QWidget):
        if _is_focusable_input(child) and not _is_button(child):
            focusable.append(child)

    return focusable


def collect_focusable_widgets(node: object) -> list[QWidget]:
    """
    Collect all focusable input widgets from a node in visual order.

    This function recursively searches through a node's widgets and returns
    a list of all focusable input widgets sorted by their visual position
    (top to bottom, left to right).

    Args:
        node: The visual node to search for focusable widgets

    Returns:
        List of focusable input widgets in visual order
    """
    from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

    focusable: list[QWidget] = []

    try:
        if not hasattr(node, "widgets") or not callable(node.widgets):
            return focusable

        widgets_dict = node.widgets()

        for name, widget in widgets_dict.items():
            if not isinstance(widget, NodeBaseWidget):
                continue

            custom_widget = widget.get_custom_widget()

            if custom_widget is not None:
                extracted = _get_focusable_from_container(custom_widget)
                focusable.extend(extracted)
            else:
                if hasattr(widget, "_line_edit"):
                    line_edit = widget._line_edit
                    if _is_focusable_input(line_edit):
                        focusable.append(line_edit)
                elif hasattr(widget, "_picker"):
                    picker = widget._picker
                    if _is_focusable_input(picker):
                        focusable.append(picker)

    except Exception as e:
        logger.debug("Error collecting focusable widgets from node: %s", e)

    return focusable


def install_tab_navigation(node: object) -> None:
    """
    Install tab navigation on all input widgets within a node.

    This function collects all focusable widgets from the node and installs
    event filters to handle Tab/Shift+Tab key events.

    Note: Event filters are stored on each widget to prevent garbage collection.

    Args:
        node: The visual node to install tab navigation on
    """
    widgets = collect_focusable_widgets(node)

    if not widgets:
        logger.debug("No focusable widgets found in node for tab navigation")
        return

    for i, widget in enumerate(widgets):
        if widget is None:
            continue

        interceptor = TabNavigationInterceptor(widgets, i, widget)
        widget.installEventFilter(interceptor)

        if not hasattr(widget, "_tab_navigation_interceptors"):
            widget._tab_navigation_interceptors = []
        widget._tab_navigation_interceptors.append(interceptor)

    logger.debug("Installed tab navigation on %d widgets", len(widgets))


def install_tab_navigation_on_widgets(widgets_list: list[QWidget]) -> None:
    """
    Install tab navigation on a list of widgets.

    This is a convenience function for installing tab navigation on widgets
    that are not part of a node's widget collection.

    Note: Event filters are stored on each widget to prevent garbage collection.

    Args:
        widgets_list: List of widgets to install navigation on
    """
    if not widgets_list:
        return

    for i, widget in enumerate(widgets_list):
        if widget is None:
            continue

        interceptor = TabNavigationInterceptor(widgets_list, i, widget)
        widget.installEventFilter(interceptor)

        if not hasattr(widget, "_tab_navigation_interceptors"):
            widget._tab_navigation_interceptors = []
        widget._tab_navigation_interceptors.append(interceptor)


NavigationContextKey = Literal["widgets", "node", "current_index"]
NavigationContext = dict[NavigationContextKey, object]


def create_navigation_context(node: object) -> NavigationContext:
    """
    Create a navigation context for a node.

    This context can be stored and used to programmatically navigate
    between widgets or to update the navigation when widgets change.

    Args:
        node: The visual node to create context for

    Returns:
        Dictionary containing navigation context with keys:
        - 'widgets': List of focusable widgets
        - 'node': Reference to the node
        - 'current_index': Current focused widget index (-1 if none)
    """
    widgets = collect_focusable_widgets(node)

    return {
        "widgets": widgets,
        "node": node,
        "current_index": -1,
    }


def navigate_to_next(node: object) -> bool:
    """
    Programmatically move focus to the next widget in a node.

    Args:
        node: The visual node to navigate within

    Returns:
        True if navigation succeeded, False if no widgets found or all disabled
    """
    widgets = collect_focusable_widgets(node)

    if not widgets:
        return False

    current = None
    for widget in widgets:
        if widget.hasFocus():
            current = widget
            break

    if current is None:
        if widgets:
            widgets[0].setFocus(Qt.FocusReason.TabFocusReason)
            return True
        return False

    current_index = widgets.index(current)
    next_index = (current_index + 1) % len(widgets)
    next_widget = widgets[next_index]

    if next_widget and next_widget.isEnabled() and next_widget.isVisible():
        next_widget.setFocus(Qt.FocusReason.TabFocusReason)
        return True

    return False


def navigate_to_previous(node: object) -> bool:
    """
    Programmatically move focus to the previous widget in a node.

    Args:
        node: The visual node to navigate within

    Returns:
        True if navigation succeeded, False if no widgets found or all disabled
    """
    widgets = collect_focusable_widgets(node)

    if not widgets:
        return False

    current = None
    for widget in widgets:
        if widget.hasFocus():
            current = widget
            break

    if current is None:
        if widgets:
            widgets[-1].setFocus(Qt.FocusReason.BacktabFocusReason)
            return True
        return False

    current_index = widgets.index(current)
    prev_index = (current_index - 1) % len(widgets)
    prev_widget = widgets[prev_index]

    if prev_widget and prev_widget.isEnabled() and prev_widget.isVisible():
        prev_widget.setFocus(Qt.FocusReason.BacktabFocusReason)
        return True

    return False


def remove_tab_navigation(node: object) -> None:
    """
    Remove tab navigation from all widgets in a node.

    This function removes all event filters and clears the stored interceptors.

    Args:
        node: The visual node to remove tab navigation from
    """
    widgets = collect_focusable_widgets(node)

    for widget in widgets:
        if widget is None:
            continue

        if hasattr(widget, "_tab_navigation_interceptors"):
            for interceptor in widget._tab_navigation_interceptors:
                try:
                    widget.removeEventFilter(interceptor)
                except Exception:
                    pass
            widget._tab_navigation_interceptors.clear()
            delattr(widget, "_tab_navigation_interceptors")

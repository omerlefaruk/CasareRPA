"""
Fixtures for visual node tests.

Provides mocks to isolate visual nodes from Qt dependencies during import/instantiation tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch


@pytest.fixture
def mock_nodegraphqt():
    """
    Mock NodeGraphQt to avoid Qt dependencies.

    Returns a module mock that provides BaseNode with necessary methods.
    """
    mock_module = MagicMock()

    # Create a mock BaseNode class
    class MockBaseNode:
        def __init__(self, qgraphics_item=None):
            self.model = Mock()
            self.model.selected_color = (0, 0, 0, 0)
            self.model.selected_border_color = (0, 0, 0, 0)
            self.model.border_color = (0, 0, 0, 0)
            self.model.text_color = (0, 0, 0, 0)
            self.model.icon = ""
            self._widgets = {}
            self._view = Mock()

        def create_property(self, name, value):
            pass

        def set_property(self, name, value):
            pass

        def get_property(self, name):
            return None

        def add_input(self, name, multi_input=False):
            pass

        def add_output(self, name):
            pass

        def add_text_input(
            self,
            name,
            label=None,
            text="",
            placeholder_text=None,
            tab=None,
            tooltip=None,
        ):
            if name in self._widgets:
                raise Exception(f"NodePropertyError: property already exists: {name}")
            self._widgets[name] = {"type": "text", "value": text}

        def add_combo_menu(self, name, label=None, items=None, tab=None):
            if name in self._widgets:
                raise Exception(f"NodePropertyError: property already exists: {name}")
            self._widgets[name] = {"type": "combo", "items": items}

        def add_checkbox(self, name, label=None, state=False, tab=None):
            if name in self._widgets:
                raise Exception(f"NodePropertyError: property already exists: {name}")
            self._widgets[name] = {"type": "checkbox", "state": state}

        def add_int_input(self, name, label=None, value=0, tab=None):
            if name in self._widgets:
                raise Exception(f"NodePropertyError: property already exists: {name}")
            self._widgets[name] = {"type": "int", "value": value}

        def add_float_input(self, name, label=None, value=0.0, tab=None):
            if name in self._widgets:
                raise Exception(f"NodePropertyError: property already exists: {name}")
            self._widgets[name] = {"type": "float", "value": value}

        def set_color(self, r, g, b):
            pass

        def input_ports(self):
            return []

        def output_ports(self):
            return []

        def widgets(self):
            return self._widgets

        @property
        def view(self):
            return self._view

    mock_module.BaseNode = MockBaseNode
    return mock_module


@pytest.fixture
def mock_qt_dependencies():
    """
    Mock Qt and PySide6 dependencies for visual node tests.
    """
    mocks = {}

    # Mock QColor
    mock_qcolor = Mock()
    mock_qcolor.return_value = Mock(
        red=Mock(return_value=100),
        green=Mock(return_value=100),
        blue=Mock(return_value=100),
    )

    patches = [
        patch("PySide6.QtGui.QColor", mock_qcolor),
        patch("PySide6.QtCore.Signal", Mock()),
        patch("PySide6.QtCore.QObject", Mock),
    ]

    for p in patches:
        mocks[p] = p.start()

    yield mocks

    for p in patches:
        p.stop()

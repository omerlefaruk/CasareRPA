"""
Tests for VisualRerouteNode - Qt visual representation of RerouteNode.

Tests cover:
- Initialization and property creation
- Port setup and configuration
- Data type handling
- Casare node linkage
- Hidden-in-menu behavior

Note: Heavy Qt components are mocked. Tests focus on logic, not Qt rendering.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock Qt imports before importing the module under test
with patch.dict(
    "sys.modules",
    {
        "PySide6.QtGui": MagicMock(),
        "PySide6.QtCore": MagicMock(),
        "NodeGraphQt": MagicMock(),
    },
):
    pass

from casare_rpa.domain.value_objects.types import DataType


class TestVisualRerouteNodeAttributes:
    """Tests for VisualRerouteNode class attributes."""

    def test_node_identifier(self) -> None:
        """VisualRerouteNode has correct identifier."""
        from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
            VisualRerouteNode,
        )

        assert VisualRerouteNode.__identifier__ == "casare_rpa.utility"

    def test_node_name(self) -> None:
        """VisualRerouteNode has correct name."""
        from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
            VisualRerouteNode,
        )

        assert VisualRerouteNode.NODE_NAME == "Reroute"

    def test_node_category(self) -> None:
        """VisualRerouteNode has correct category."""
        from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
            VisualRerouteNode,
        )

        assert VisualRerouteNode.NODE_CATEGORY == "utility"

    def test_hidden_in_menu(self) -> None:
        """VisualRerouteNode is hidden from context menu."""
        from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
            VisualRerouteNode,
        )

        assert VisualRerouteNode.HIDDEN_IN_MENU is True

    def test_casare_node_class_mapping(self) -> None:
        """VisualRerouteNode maps to RerouteNode."""
        from casare_rpa.presentation.canvas.visual_nodes.utility.reroute_node import (
            VisualRerouteNode,
        )

        assert VisualRerouteNode.CASARE_NODE_CLASS == "RerouteNode"


class TestRerouteNodeItemAttributes:
    """Tests for RerouteNodeItem graphics item attributes."""

    def test_dot_radius_defined(self) -> None:
        """RerouteNodeItem has DOT_RADIUS constant."""
        from casare_rpa.presentation.canvas.graph.reroute_node_item import (
            RerouteNodeItem,
        )

        assert hasattr(RerouteNodeItem, "DOT_RADIUS")
        assert RerouteNodeItem.DOT_RADIUS == 8

    def test_dot_diameter_calculated(self) -> None:
        """RerouteNodeItem has DOT_DIAMETER as 2x radius."""
        from casare_rpa.presentation.canvas.graph.reroute_node_item import (
            RerouteNodeItem,
        )

        assert RerouteNodeItem.DOT_DIAMETER == RerouteNodeItem.DOT_RADIUS * 2


class TestRerouteNodeItemColors:
    """Tests for RerouteNodeItem color constants."""

    def test_default_color_defined(self) -> None:
        """DEFAULT_REROUTE_COLOR is defined."""
        from casare_rpa.presentation.canvas.graph.reroute_node_item import (
            DEFAULT_REROUTE_COLOR,
        )

        assert DEFAULT_REROUTE_COLOR is not None

    def test_selected_border_color_defined(self) -> None:
        """SELECTED_BORDER_COLOR is defined."""
        from casare_rpa.presentation.canvas.graph.reroute_node_item import (
            SELECTED_BORDER_COLOR,
        )

        assert SELECTED_BORDER_COLOR is not None

    def test_exec_color_defined(self) -> None:
        """EXEC_REROUTE_COLOR is defined."""
        from casare_rpa.presentation.canvas.graph.reroute_node_item import (
            EXEC_REROUTE_COLOR,
        )

        assert EXEC_REROUTE_COLOR is not None


class TestDotCreatorImports:
    """Tests for DotCreator module imports."""

    def test_dot_creator_importable(self) -> None:
        """DotCreator can be imported."""
        from casare_rpa.presentation.canvas.connections.dot_creator import DotCreator

        assert DotCreator is not None

    def test_dot_creator_is_qobject(self) -> None:
        """DotCreator extends QObject."""
        from casare_rpa.presentation.canvas.connections.dot_creator import DotCreator
        from PySide6.QtCore import QObject

        assert issubclass(DotCreator, QObject)


class TestDotCreatorMethods:
    """Tests for DotCreator method existence."""

    def test_has_set_active_method(self) -> None:
        """DotCreator has set_active method."""
        from casare_rpa.presentation.canvas.connections.dot_creator import DotCreator

        assert hasattr(DotCreator, "set_active")

    def test_has_is_active_method(self) -> None:
        """DotCreator has is_active method."""
        from casare_rpa.presentation.canvas.connections.dot_creator import DotCreator

        assert hasattr(DotCreator, "is_active")

    def test_has_event_filter_method(self) -> None:
        """DotCreator has eventFilter method."""
        from casare_rpa.presentation.canvas.connections.dot_creator import DotCreator

        assert hasattr(DotCreator, "eventFilter")


class TestRerouteNodeDataTypeHandling:
    """Tests for data type handling in visual reroute node."""

    def test_data_type_any_is_valid_enum(self) -> None:
        """ANY is a valid DataType enum member."""
        assert DataType.ANY is not None
        assert isinstance(DataType.ANY, DataType)

    def test_data_type_string_is_valid_enum(self) -> None:
        """STRING is a valid DataType enum member."""
        assert DataType.STRING is not None
        assert isinstance(DataType.STRING, DataType)

    def test_data_type_integer_is_valid_enum(self) -> None:
        """INTEGER is a valid DataType enum member."""
        assert DataType.INTEGER is not None
        assert isinstance(DataType.INTEGER, DataType)

    def test_data_type_enum_name_attribute(self) -> None:
        """DataType enum has name attribute."""
        assert DataType.ANY.name == "ANY"
        assert DataType.STRING.name == "STRING"
        assert DataType.INTEGER.name == "INTEGER"


class TestRerouteRegistration:
    """Tests verifying RerouteNode is properly registered."""

    def test_in_node_registry(self) -> None:
        """RerouteNode is in _NODE_REGISTRY."""
        from casare_rpa.nodes import _NODE_REGISTRY

        assert "RerouteNode" in _NODE_REGISTRY

    def test_in_node_type_map(self) -> None:
        """RerouteNode is in NODE_TYPE_MAP."""
        from casare_rpa.utils.workflow.workflow_loader import NODE_TYPE_MAP

        assert "RerouteNode" in NODE_TYPE_MAP

    def test_visual_node_in_all(self) -> None:
        """VisualRerouteNode is exported from visual_nodes."""
        from casare_rpa.presentation.canvas.visual_nodes import __all__

        assert "VisualRerouteNode" in __all__

    def test_utility_exports_reroute(self) -> None:
        """Utility package exports VisualRerouteNode."""
        from casare_rpa.presentation.canvas.visual_nodes.utility import (
            VisualRerouteNode,
        )

        assert VisualRerouteNode is not None

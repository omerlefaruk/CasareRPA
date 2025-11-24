"""
Tests for canvas/node_registry.py - Node registration and factory.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestCasareNodeMapping:
    """Test CASARE_NODE_MAPPING configuration."""

    def test_mapping_exists(self):
        """Test that CASARE_NODE_MAPPING is defined."""
        from casare_rpa.canvas.node_registry import CASARE_NODE_MAPPING

        assert isinstance(CASARE_NODE_MAPPING, dict)
        assert len(CASARE_NODE_MAPPING) > 0

    def test_basic_node_mappings(self):
        """Test that basic nodes are mapped."""
        from casare_rpa.canvas.node_registry import CASARE_NODE_MAPPING
        from casare_rpa.canvas.visual_nodes import VisualStartNode, VisualEndNode
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode

        assert CASARE_NODE_MAPPING[VisualStartNode] == StartNode
        assert CASARE_NODE_MAPPING[VisualEndNode] == EndNode

    def test_all_visual_nodes_have_mapping(self):
        """Test that all visual node classes have a mapping."""
        from casare_rpa.canvas.node_registry import CASARE_NODE_MAPPING
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        for visual_class in VISUAL_NODE_CLASSES:
            assert visual_class in CASARE_NODE_MAPPING, \
                f"Missing mapping for {visual_class.__name__}"


class TestNodeRegistry:
    """Test NodeRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh node registry."""
        from casare_rpa.canvas.node_registry import NodeRegistry
        return NodeRegistry()

    def test_registry_initialization(self, registry):
        """Test registry initial state."""
        assert registry._registered_nodes == {}
        assert registry._categories == {}

    def test_register_node(self, registry):
        """Test registering a single node."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode

        registry.register_node(VisualStartNode)

        assert VisualStartNode.NODE_NAME in registry._registered_nodes
        assert registry._registered_nodes[VisualStartNode.NODE_NAME] == VisualStartNode

    def test_register_node_adds_to_category(self, registry):
        """Test that registering adds node to category."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode

        registry.register_node(VisualStartNode)

        category = VisualStartNode.NODE_CATEGORY
        assert category in registry._categories
        assert VisualStartNode in registry._categories[category]

    def test_get_node_class(self, registry):
        """Test getting node class by name."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode

        registry.register_node(VisualStartNode)

        result = registry.get_node_class(VisualStartNode.NODE_NAME)
        assert result == VisualStartNode

    def test_get_node_class_not_found(self, registry):
        """Test getting non-existent node class."""
        result = registry.get_node_class("NonExistent")
        assert result is None

    def test_get_nodes_by_category(self, registry):
        """Test getting nodes by category."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode, VisualEndNode

        registry.register_node(VisualStartNode)
        registry.register_node(VisualEndNode)

        basic_nodes = registry.get_nodes_by_category("basic")
        assert VisualStartNode in basic_nodes
        assert VisualEndNode in basic_nodes

    def test_get_nodes_by_category_empty(self, registry):
        """Test getting nodes from non-existent category."""
        nodes = registry.get_nodes_by_category("nonexistent")
        assert nodes == []

    def test_get_categories(self, registry):
        """Test getting all categories."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode, VisualLaunchBrowserNode

        registry.register_node(VisualStartNode)
        registry.register_node(VisualLaunchBrowserNode)

        categories = registry.get_categories()
        assert "basic" in categories
        assert "browser" in categories

    def test_get_all_nodes(self, registry):
        """Test getting all registered nodes."""
        from casare_rpa.canvas.visual_nodes import VisualStartNode, VisualEndNode

        registry.register_node(VisualStartNode)
        registry.register_node(VisualEndNode)

        all_nodes = registry.get_all_nodes()
        assert VisualStartNode in all_nodes
        assert VisualEndNode in all_nodes


class TestNodeFactory:
    """Test NodeFactory class."""

    @pytest.fixture
    def factory(self):
        """Create a fresh node factory."""
        from casare_rpa.canvas.node_registry import NodeFactory
        return NodeFactory()

    def test_factory_initialization(self, factory):
        """Test factory initial state."""
        # Counter starts at 0 for a new factory instance
        assert factory._node_counter >= 0

    def test_create_casare_node_unknown_type(self, factory):
        """Test creating node for unknown visual type returns None."""
        mock_visual_node = MagicMock()
        mock_visual_node.__class__ = type("UnknownNode", (), {})

        result = factory.create_casare_node(mock_visual_node)
        assert result is None

    def test_factory_has_create_methods(self, factory):
        """Test that factory has required creation methods."""
        assert hasattr(factory, 'create_casare_node')
        assert hasattr(factory, 'create_visual_node')
        assert hasattr(factory, 'create_linked_node')

    def test_factory_counter_attribute(self, factory):
        """Test that factory has counter attribute."""
        assert hasattr(factory, '_node_counter')
        assert isinstance(factory._node_counter, int)


class TestGlobalInstances:
    """Test global registry and factory instances."""

    def test_get_node_registry(self):
        """Test getting global node registry."""
        from casare_rpa.canvas.node_registry import get_node_registry, NodeRegistry

        registry = get_node_registry()
        assert isinstance(registry, NodeRegistry)

    def test_get_node_registry_singleton(self):
        """Test that get_node_registry returns same instance."""
        from casare_rpa.canvas.node_registry import get_node_registry

        registry1 = get_node_registry()
        registry2 = get_node_registry()
        assert registry1 is registry2

    def test_get_node_factory(self):
        """Test getting global node factory."""
        from casare_rpa.canvas.node_registry import get_node_factory, NodeFactory

        factory = get_node_factory()
        assert isinstance(factory, NodeFactory)

    def test_get_node_factory_singleton(self):
        """Test that get_node_factory returns same instance."""
        from casare_rpa.canvas.node_registry import get_node_factory

        factory1 = get_node_factory()
        factory2 = get_node_factory()
        assert factory1 is factory2


class TestNodeRegistryCategories:
    """Test node categorization."""

    def test_all_expected_categories_exist(self):
        """Test that all expected categories are present."""
        from casare_rpa.canvas.node_registry import NodeRegistry
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        registry = NodeRegistry()
        for node_class in VISUAL_NODE_CLASSES:
            registry.register_node(node_class)

        categories = registry.get_categories()
        categories_lower = [c.lower().replace(" ", "_") for c in categories]

        # Check that expected category keywords are present
        expected_keywords = [
            "basic", "browser", "navigation", "interaction",
            "data", "wait", "variable", "control", "error", "desktop"
        ]

        for keyword in expected_keywords:
            found = any(keyword in cat for cat in categories_lower)
            assert found, f"Missing category containing: {keyword}"


class TestNodeNameUniqueness:
    """Test that node names are unique."""

    def test_visual_node_names_unique(self):
        """Test that all visual node names are unique."""
        from casare_rpa.canvas.visual_nodes import VISUAL_NODE_CLASSES

        names = [cls.NODE_NAME for cls in VISUAL_NODE_CLASSES]
        assert len(names) == len(set(names)), "Duplicate node names found"

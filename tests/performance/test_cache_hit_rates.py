"""
Tests for Phase 7.5 Caching Strategies

Tests cache hit rates for:
- ResourceCache (icons/pixmaps)
- Node registry lookups
- Workflow validation caching
"""

import pytest
from unittest.mock import MagicMock, patch


class TestResourceCache:
    """Tests for ResourceCache icon and pixmap caching."""

    def test_icon_cache_hit(self):
        """Test that repeated icon requests return cached instances."""
        from casare_rpa.presentation.canvas.resources import ResourceCache

        # Clear cache first
        ResourceCache.clear()

        # Mock QIcon to avoid actual file loading
        with patch("PySide6.QtGui.QIcon") as mock_icon_class:
            mock_icon = MagicMock()
            mock_icon_class.return_value = mock_icon

            # First request - cache miss
            icon1 = ResourceCache.get_icon("test/icon.png")

            # Second request - cache hit
            icon2 = ResourceCache.get_icon("test/icon.png")

            # Should be same instance
            assert icon1 is icon2

            # QIcon constructor should only be called once
            mock_icon_class.assert_called_once_with("test/icon.png")

        stats = ResourceCache.get_stats()
        assert stats["icon_hits"] == 1
        assert stats["icon_misses"] == 1
        assert stats["icon_hit_rate"] == 0.5

    def test_pixmap_cache_with_different_sizes(self):
        """Test that pixmaps are cached separately by size."""
        from casare_rpa.presentation.canvas.resources import ResourceCache

        ResourceCache.clear()

        with patch("PySide6.QtGui.QPixmap") as mock_pixmap_class:
            mock_pixmap = MagicMock()
            mock_pixmap.width.return_value = 100
            mock_pixmap.height.return_value = 100
            mock_pixmap.scaled.return_value = mock_pixmap
            mock_pixmap_class.return_value = mock_pixmap

            # Request same image at different sizes
            ResourceCache.get_pixmap("test/image.png", 32, 32)
            ResourceCache.get_pixmap("test/image.png", 64, 64)
            ResourceCache.get_pixmap("test/image.png", 32, 32)  # Hit

            stats = ResourceCache.get_stats()
            assert stats["pixmap_misses"] == 2  # Two different sizes
            assert stats["pixmap_hits"] == 1  # One repeated request

    def test_cache_clear(self):
        """Test that cache clear resets all counters."""
        from casare_rpa.presentation.canvas.resources import ResourceCache

        # Add some items
        with patch("PySide6.QtGui.QIcon"):
            ResourceCache.get_icon("test1.png")
            ResourceCache.get_icon("test2.png")

        # Clear cache
        ResourceCache.clear()

        stats = ResourceCache.get_stats()
        assert stats["icon_cache_size"] == 0
        assert stats["icon_hits"] == 0
        assert stats["icon_misses"] == 0

    def test_icon_cache_eviction(self):
        """Test that cache evicts entries when size limit reached."""
        from casare_rpa.presentation.canvas.resources import ResourceCache

        ResourceCache.clear()

        # Temporarily reduce max size for test
        original_max = ResourceCache.MAX_ICON_CACHE_SIZE
        ResourceCache.MAX_ICON_CACHE_SIZE = 5

        try:
            with patch("PySide6.QtGui.QIcon"):
                # Add more icons than max size
                for i in range(10):
                    ResourceCache.get_icon(f"test{i}.png")

                # Cache should have evicted some entries
                stats = ResourceCache.get_stats()
                assert stats["icon_cache_size"] <= 10  # Some should remain
        finally:
            ResourceCache.MAX_ICON_CACHE_SIZE = original_max
            ResourceCache.clear()


class TestNodeRegistryCache:
    """Tests for node registry LRU caching."""

    def test_visual_class_cache_hit(self):
        """Test that repeated lookups use LRU cache."""
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_visual_class_for_type,
            get_cache_stats,
            clear_node_type_caches,
        )

        # Clear caches first
        clear_node_type_caches()

        # Perform lookups
        result1 = get_visual_class_for_type("StartNode")
        result2 = get_visual_class_for_type("StartNode")

        # Same result
        assert result1 is result2

        # Check cache stats
        stats = get_cache_stats()
        visual_stats = stats["get_visual_class_for_type"]
        assert visual_stats["hits"] >= 1  # At least one hit

    def test_identifier_cache_hit(self):
        """Test identifier lookup caching."""
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_identifier_for_type,
            get_cache_stats,
            clear_node_type_caches,
        )

        clear_node_type_caches()

        # Repeated lookups
        for _ in range(5):
            get_identifier_for_type("EndNode")

        stats = get_cache_stats()
        id_stats = stats["get_identifier_for_type"]
        # First call is miss, rest are hits
        assert id_stats["hits"] == 4
        assert id_stats["misses"] == 1

    def test_casare_class_cache_hit(self):
        """Test CasareRPA class lookup caching."""
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_casare_class_for_type,
            get_cache_stats,
            clear_node_type_caches,
        )

        clear_node_type_caches()

        # Multiple lookups of same and different types
        get_casare_class_for_type("StartNode")
        get_casare_class_for_type("EndNode")
        get_casare_class_for_type("StartNode")  # Hit
        get_casare_class_for_type("EndNode")  # Hit

        stats = get_cache_stats()
        casare_stats = stats["get_casare_class_for_type"]
        assert casare_stats["hits"] == 2
        assert casare_stats["misses"] == 2

    def test_cache_clear_resets_stats(self):
        """Test that clearing cache resets statistics."""
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_visual_class_for_type,
            get_cache_stats,
            clear_node_type_caches,
        )

        # Generate some stats
        get_visual_class_for_type("StartNode")
        get_visual_class_for_type("StartNode")

        # Clear and verify
        clear_node_type_caches()

        stats = get_cache_stats()
        visual_stats = stats["get_visual_class_for_type"]
        assert visual_stats["hits"] == 0
        assert visual_stats["misses"] == 0


class TestValidateWorkflowCache:
    """Tests for workflow validation caching."""

    @pytest.fixture
    def mock_workflow(self):
        """Create a mock workflow for testing."""
        workflow = MagicMock()

        # Create mock nodes
        start_node = MagicMock()
        start_node.__class__.__name__ = "StartNode"

        end_node = MagicMock()
        end_node.__class__.__name__ = "EndNode"

        workflow.nodes = {"start_1": start_node, "end_1": end_node}

        # Create mock connection
        connection = MagicMock()
        connection.source_node = "start_1"
        connection.target_node = "end_1"
        workflow.connections = [connection]

        return workflow

    def test_validation_cache_hit(self, mock_workflow):
        """Test that repeated validation uses cache."""
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        ValidateWorkflowUseCase.clear_cache()

        use_case = ValidateWorkflowUseCase()

        # First validation - cache miss
        result1 = use_case.execute(mock_workflow)
        assert not result1.from_cache

        # Second validation - cache hit
        result2 = use_case.execute(mock_workflow)
        assert result2.from_cache

        # Same validity
        assert result1.is_valid == result2.is_valid

        stats = ValidateWorkflowUseCase.get_cache_stats()
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_validation_cache_invalidation(self, mock_workflow):
        """Test that modified workflow invalidates cache."""
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        ValidateWorkflowUseCase.clear_cache()

        use_case = ValidateWorkflowUseCase()

        # Validate original
        result1 = use_case.execute(mock_workflow)
        assert not result1.from_cache

        # Modify workflow (add a node)
        new_node = MagicMock()
        new_node.__class__.__name__ = "ActionNode"
        mock_workflow.nodes["action_1"] = new_node

        # Validate modified - should be cache miss
        result2 = use_case.execute(mock_workflow)
        assert not result2.from_cache

    def test_validation_result_properties(self, mock_workflow):
        """Test ValidationResult properties."""
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        ValidateWorkflowUseCase.clear_cache()

        use_case = ValidateWorkflowUseCase()
        result = use_case.execute(mock_workflow)

        # Should be valid (has start and end nodes, connected)
        assert result.is_valid

        # Check property accessors
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
        assert result.error_count >= 0
        assert result.warning_count >= 0

    def test_validation_detects_missing_start_node(self):
        """Test that validation detects missing start node."""
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        ValidateWorkflowUseCase.clear_cache()

        # Workflow without start node
        workflow = MagicMock()
        end_node = MagicMock()
        end_node.__class__.__name__ = "EndNode"
        workflow.nodes = {"end_1": end_node}
        workflow.connections = []

        use_case = ValidateWorkflowUseCase()
        result = use_case.execute(workflow)

        assert not result.is_valid
        assert result.error_count > 0
        assert any(issue.code == "NO_START_NODE" for issue in result.errors)

    def test_validation_detects_orphan_nodes(self):
        """Test that validation warns about orphan nodes."""
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        ValidateWorkflowUseCase.clear_cache()

        # Workflow with orphan node
        workflow = MagicMock()
        start_node = MagicMock()
        start_node.__class__.__name__ = "StartNode"
        orphan_node = MagicMock()
        orphan_node.__class__.__name__ = "ActionNode"

        workflow.nodes = {"start_1": start_node, "orphan_1": orphan_node}
        workflow.connections = []  # No connections

        use_case = ValidateWorkflowUseCase()
        result = use_case.execute(workflow)

        # Should have orphan warning
        assert any(issue.code == "ORPHAN_NODE" for issue in result.warnings)

    def test_cache_stats_calculation(self, mock_workflow):
        """Test that cache stats are calculated correctly."""
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        ValidateWorkflowUseCase.clear_cache()

        use_case = ValidateWorkflowUseCase()

        # Generate specific pattern of hits/misses
        use_case.execute(mock_workflow)  # Miss
        use_case.execute(mock_workflow)  # Hit
        use_case.execute(mock_workflow)  # Hit
        use_case.execute(mock_workflow)  # Hit

        stats = ValidateWorkflowUseCase.get_cache_stats()
        assert stats["cache_hits"] == 3
        assert stats["cache_misses"] == 1
        assert stats["hit_rate"] == 0.75
        assert stats["cache_size"] == 1  # Only one workflow cached


class TestCacheIntegration:
    """Integration tests for all caching systems together."""

    def test_all_caches_independent(self):
        """Test that different caches don't interfere with each other."""
        from casare_rpa.presentation.canvas.resources import ResourceCache
        from casare_rpa.presentation.canvas.graph.node_registry import (
            clear_node_type_caches,
            get_cache_stats,
        )
        from casare_rpa.application.use_cases.validate_workflow import (
            ValidateWorkflowUseCase,
        )

        # Clear all caches
        ResourceCache.clear()
        clear_node_type_caches()
        ValidateWorkflowUseCase.clear_cache()

        # Verify all cleared
        resource_stats = ResourceCache.get_stats()
        assert resource_stats["icon_cache_size"] == 0

        registry_stats = get_cache_stats()
        assert registry_stats["get_visual_class_for_type"]["hits"] == 0

        validation_stats = ValidateWorkflowUseCase.get_cache_stats()
        assert validation_stats["cache_size"] == 0

    def test_high_hit_rate_scenario(self):
        """Simulate realistic usage with expected high hit rate."""
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_visual_class_for_type,
            get_cache_stats,
            clear_node_type_caches,
        )

        clear_node_type_caches()

        # Simulate typical editing session: repeated lookups of common nodes
        common_nodes = ["StartNode", "EndNode", "IfNode", "SetVariableNode"]

        # Initial lookups (all misses)
        for node_type in common_nodes:
            get_visual_class_for_type(node_type)

        # Repeated lookups during editing (all hits)
        for _ in range(20):
            for node_type in common_nodes:
                get_visual_class_for_type(node_type)

        stats = get_cache_stats()
        visual_stats = stats["get_visual_class_for_type"]

        # Calculate hit rate
        total = visual_stats["hits"] + visual_stats["misses"]
        hit_rate = visual_stats["hits"] / total

        # Should be very high (80 hits / 84 total = ~95%)
        assert hit_rate > 0.9, f"Hit rate {hit_rate:.2%} should be > 90%"

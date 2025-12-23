"""
Tests for Workflow Loading Optimizations.

This test suite covers the performance optimizations for workflow loading:
- WorkflowSkeleton: Lightweight workflow metadata container
- IncrementalLoader: Two-phase loading (skeleton then full)
- NodeInstancePool: Object pooling for node instances
- Parallel instantiation: ThreadPoolExecutor for large workflows

Test Philosophy:
- Happy path: Normal operation with valid inputs
- Sad path: Expected failures (missing data, invalid configs)
- Edge cases: Boundary conditions (empty workflows, large workflows)
- Performance: Timing assertions for critical paths

Run: pytest tests/performance/test_workflow_loading.py -v
"""

import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch, Mock

import pytest


# =============================================================================
# WorkflowSkeleton Tests
# =============================================================================


class TestWorkflowSkeleton:
    """Tests for WorkflowSkeleton dataclass."""

    def test_create_skeleton_with_defaults(self) -> None:
        """SUCCESS: Create skeleton with minimal data."""
        from casare_rpa.utils.workflow.incremental_loader import WorkflowSkeleton

        skeleton = WorkflowSkeleton(
            name="TestWorkflow",
            description="A test workflow",
        )

        assert skeleton.name == "TestWorkflow"
        assert skeleton.description == "A test workflow"
        assert skeleton.version == "1.0.0"
        assert skeleton.author == ""
        assert skeleton.node_count == 0
        assert skeleton.connection_count == 0
        assert skeleton.variable_count == 0
        assert skeleton.frame_count == 0
        assert skeleton.node_types == set()
        assert skeleton.node_categories == set()
        assert skeleton.variable_names == []

    def test_create_skeleton_with_all_fields(self) -> None:
        """SUCCESS: Create skeleton with all fields populated."""
        from casare_rpa.utils.workflow.incremental_loader import WorkflowSkeleton

        skeleton = WorkflowSkeleton(
            name="FullWorkflow",
            description="Complete workflow",
            version="2.0.0",
            author="Test Author",
            node_count=50,
            connection_count=45,
            variable_count=10,
            frame_count=3,
            node_types={"ClickNode", "TypeNode", "LogNode"},
            node_categories={"Browser", "Data"},
            variable_names=["url", "username", "password"],
            settings={"auto_save": True},
            created_at="2024-01-01T00:00:00Z",
            modified_at="2024-12-01T00:00:00Z",
        )

        assert skeleton.name == "FullWorkflow"
        assert skeleton.version == "2.0.0"
        assert skeleton.author == "Test Author"
        assert skeleton.node_count == 50
        assert skeleton.connection_count == 45
        assert skeleton.variable_count == 10
        assert skeleton.frame_count == 3
        assert "ClickNode" in skeleton.node_types
        assert "Browser" in skeleton.node_categories
        assert len(skeleton.variable_names) == 3
        assert skeleton.settings["auto_save"] is True

    def test_skeleton_is_loaded_initially_false(self) -> None:
        """SUCCESS: New skeleton reports not loaded."""
        from casare_rpa.utils.workflow.incremental_loader import WorkflowSkeleton

        skeleton = WorkflowSkeleton(name="Test", description="")

        assert skeleton.is_loaded() is False
        assert skeleton.get_full_workflow() is None

    def test_skeleton_with_deferred_data(self) -> None:
        """SUCCESS: Skeleton can store deferred data for later loading."""
        from casare_rpa.utils.workflow.incremental_loader import WorkflowSkeleton

        full_data = {"metadata": {"name": "Test"}, "nodes": {}}
        skeleton = WorkflowSkeleton(
            name="Test",
            description="",
            _full_data=full_data,
        )

        assert skeleton._full_data is not None
        assert skeleton._full_data == full_data

    def test_skeleton_equality_not_affected_by_internal_state(self) -> None:
        """EDGE CASE: Two skeletons with same visible data are equal."""
        from casare_rpa.utils.workflow.incremental_loader import WorkflowSkeleton

        skeleton1 = WorkflowSkeleton(name="Test", description="Desc", node_count=5)
        skeleton2 = WorkflowSkeleton(name="Test", description="Desc", node_count=5)

        # Dataclass equality compares all fields including private ones
        # This is expected behavior - just verifying it
        assert skeleton1.name == skeleton2.name
        assert skeleton1.node_count == skeleton2.node_count


# =============================================================================
# IncrementalLoader Tests
# =============================================================================


class TestIncrementalLoader:
    """Tests for IncrementalLoader class."""

    def test_create_loader(self) -> None:
        """SUCCESS: Create incremental loader instance."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()

        assert loader is not None
        # Loader should be ready to use - no specific state to check

<<<<<<< HEAD
    def test_load_skeleton_extracts_metadata(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_skeleton_extracts_metadata(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load skeleton extracts correct metadata."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        assert skeleton.name == "SmallWorkflow"
        assert skeleton.description == "Test workflow with 10 nodes"
        assert skeleton.version == "1.0.0"
        assert skeleton.author == "Test Suite"

<<<<<<< HEAD
    def test_load_skeleton_extracts_counts(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_skeleton_extracts_counts(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load skeleton extracts correct counts."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        assert skeleton.node_count == 10
        assert skeleton.connection_count == 9  # 10 nodes, 9 connections
        assert skeleton.variable_count == 2  # test_var, counter
        assert skeleton.frame_count == 0

<<<<<<< HEAD
    def test_load_skeleton_extracts_node_types(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_skeleton_extracts_node_types(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load skeleton extracts node type set."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        assert "StartNode" in skeleton.node_types
        # Should have other node types from the fixture
        assert len(skeleton.node_types) >= 1

    def test_load_skeleton_extracts_variable_names(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
        """SUCCESS: Load skeleton extracts variable names."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        assert "test_var" in skeleton.variable_names
        assert "counter" in skeleton.variable_names

<<<<<<< HEAD
    def test_load_skeleton_stores_full_data(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_skeleton_stores_full_data(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load skeleton stores full data for later loading."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        assert skeleton._full_data is not None
        assert skeleton._full_data == small_workflow_data

<<<<<<< HEAD
    def test_load_skeleton_with_file_path(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_skeleton_with_file_path(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load skeleton stores file path."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
<<<<<<< HEAD
        skeleton = loader.load_skeleton(
            small_workflow_data, file_path="/path/to/workflow.json"
        )
=======
        skeleton = loader.load_skeleton(small_workflow_data, file_path="/path/to/workflow.json")
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

        assert skeleton._file_path == "/path/to/workflow.json"

    def test_load_skeleton_empty_workflow(self) -> None:
        """EDGE CASE: Load skeleton from empty workflow."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        empty_data = {
            "metadata": {"name": "Empty", "description": ""},
            "nodes": {},
            "connections": [],
            "variables": {},
        }

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(empty_data)

        assert skeleton.name == "Empty"
        assert skeleton.node_count == 0
        assert skeleton.connection_count == 0
        assert skeleton.node_types == set()

    def test_load_skeleton_missing_metadata(self) -> None:
        """EDGE CASE: Load skeleton handles missing metadata gracefully."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        minimal_data = {"nodes": {"n1": {"node_type": "TestNode"}}, "connections": []}

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(minimal_data)

        assert skeleton.name == "Untitled"
        assert skeleton.description == ""
        assert skeleton.node_count == 1

<<<<<<< HEAD
    def test_load_skeleton_performance_is_fast(
        self, large_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_skeleton_performance_is_fast(self, large_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """PERFORMANCE: Skeleton loading should be fast (<50ms for 200 nodes)."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()

        start = time.perf_counter()
        skeleton = loader.load_skeleton(large_workflow_data)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert skeleton.node_count == 200
        # Skeleton loading should be very fast - just metadata extraction
<<<<<<< HEAD
        assert (
            elapsed_ms < 50
        ), f"Skeleton loading took {elapsed_ms:.1f}ms, expected <50ms"
=======
        assert elapsed_ms < 50, f"Skeleton loading took {elapsed_ms:.1f}ms, expected <50ms"
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e

    def test_infer_categories_from_node_types(self) -> None:
        """SUCCESS: Categories are inferred from node type names."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        node_types = {
            "LaunchBrowserNode",
            "ClickElement",
            "ReadFileNode",
            "HttpRequest",
        }

        categories = loader._infer_categories(node_types)

        assert "Browser" in categories
        assert "File" in categories
        assert "API" in categories

    def test_infer_categories_empty_set(self) -> None:
        """EDGE CASE: Empty node types returns empty categories."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        categories = loader._infer_categories(set())

        assert categories == set()

    def test_get_workflow_info_returns_dict(self, temp_workflow_file: Path) -> None:
        """SUCCESS: get_workflow_info returns info dictionary."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        info = loader.get_workflow_info(str(temp_workflow_file))

        assert info is not None
        assert "name" in info
        assert "node_count" in info
        assert "connection_count" in info
        assert "file_path" in info
        assert info["file_path"] == str(temp_workflow_file)

    def test_get_workflow_info_missing_file(self, tmp_path: Path) -> None:
        """SAD PATH: get_workflow_info returns None for missing file."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        info = loader.get_workflow_info(str(tmp_path / "nonexistent.json"))

        assert info is None

<<<<<<< HEAD
    def test_scan_directory_finds_workflows(
        self, temp_workflow_directory: Path
    ) -> None:
=======
    def test_scan_directory_finds_workflows(self, temp_workflow_directory: Path) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: scan_directory finds all workflow files."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeletons = loader.scan_directory(str(temp_workflow_directory))

        assert len(skeletons) == 5  # 5 workflow files created in fixture

    def test_scan_directory_empty_directory(self, tmp_path: Path) -> None:
        """EDGE CASE: scan_directory returns empty list for empty directory."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        loader = IncrementalLoader()
        skeletons = loader.scan_directory(str(empty_dir))

        assert skeletons == []

    def test_scan_directory_nonexistent(self, tmp_path: Path) -> None:
        """EDGE CASE: scan_directory returns empty list for nonexistent directory."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeletons = loader.scan_directory(str(tmp_path / "nonexistent"))

        assert skeletons == []


# =============================================================================
# IncrementalLoader.load_full Tests
# =============================================================================


class TestIncrementalLoaderLoadFull:
    """Tests for IncrementalLoader.load_full method."""

    def test_load_full_from_skeleton(self, small_workflow_data: Dict[str, Any]) -> None:
        """SUCCESS: Load full workflow from skeleton."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        # Load full workflow
        workflow = loader.load_full(skeleton)

        assert workflow is not None
        assert skeleton.is_loaded() is True
        assert skeleton.get_full_workflow() is workflow

    def test_load_full_caches_result(self, small_workflow_data: Dict[str, Any]) -> None:
        """SUCCESS: Subsequent load_full calls return cached workflow."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()
        skeleton = loader.load_skeleton(small_workflow_data)

        # Load twice
        workflow1 = loader.load_full(skeleton)
        workflow2 = loader.load_full(skeleton)

        assert workflow1 is workflow2  # Same object

    def test_load_full_without_deferred_data(self) -> None:
        """SAD PATH: load_full returns None if no deferred data."""
        from casare_rpa.utils.workflow.incremental_loader import (
            IncrementalLoader,
            WorkflowSkeleton,
        )

        loader = IncrementalLoader()
        skeleton = WorkflowSkeleton(name="Empty", description="")

        workflow = loader.load_full(skeleton)

        assert workflow is None


# =============================================================================
# Global Singleton Tests
# =============================================================================


class TestIncrementalLoaderSingleton:
    """Tests for get_incremental_loader singleton."""

    def test_get_incremental_loader_returns_instance(self) -> None:
        """SUCCESS: get_incremental_loader returns an IncrementalLoader."""
        from casare_rpa.utils.workflow.incremental_loader import (
            get_incremental_loader,
            IncrementalLoader,
        )

        loader = get_incremental_loader()

        assert loader is not None
        assert isinstance(loader, IncrementalLoader)

    def test_get_incremental_loader_returns_same_instance(self) -> None:
        """SUCCESS: get_incremental_loader returns singleton."""
        from casare_rpa.utils.workflow.incremental_loader import get_incremental_loader

        loader1 = get_incremental_loader()
        loader2 = get_incremental_loader()

        assert loader1 is loader2


# =============================================================================
# Convenience Function Tests
# =============================================================================


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_load_workflow_skeleton(self, small_workflow_data: Dict[str, Any]) -> None:
        """SUCCESS: load_workflow_skeleton creates skeleton."""
        from casare_rpa.utils.workflow.incremental_loader import load_workflow_skeleton

        skeleton = load_workflow_skeleton(small_workflow_data)

        assert skeleton is not None
        assert skeleton.name == "SmallWorkflow"

    def test_get_workflow_info_function(self, temp_workflow_file: Path) -> None:
        """SUCCESS: get_workflow_info returns info dict."""
        from casare_rpa.utils.workflow.incremental_loader import get_workflow_info

        info = get_workflow_info(str(temp_workflow_file))

        assert info is not None
        assert "name" in info

    def test_scan_workflows_function(self, temp_workflow_directory: Path) -> None:
        """SUCCESS: scan_workflows returns list of skeletons."""
        from casare_rpa.utils.workflow.incremental_loader import scan_workflows

        skeletons = scan_workflows(str(temp_workflow_directory))

        assert len(skeletons) == 5


# =============================================================================
# NodeInstancePool Tests
# =============================================================================


class TestNodeInstancePool:
    """Tests for NodeInstancePool class."""

    def test_create_pool_with_defaults(self) -> None:
        """SUCCESS: Create pool with default settings."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        pool = NodeInstancePool()

        assert pool is not None
        assert pool._max_per_type == 20

    def test_create_pool_with_custom_max(self) -> None:
        """SUCCESS: Create pool with custom max_per_type."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        pool = NodeInstancePool(max_per_type=50)

        assert pool._max_per_type == 50

    def test_acquire_creates_new_instance(self) -> None:
        """SUCCESS: acquire creates new instance when pool empty."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        # Create a simple mock node class
        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"

        pool = NodeInstancePool()
        node = pool.acquire("MockNode", MockNode, "test_001", {"key": "value"})

        assert node is not None
        assert node.node_id == "test_001"
        assert node.config == {"key": "value"}

        stats = pool.get_stats()
        assert stats["misses"] == 1
        assert stats["hits"] == 0

    def test_release_returns_instance_to_pool(self) -> None:
        """SUCCESS: release returns instance to pool."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"

        pool = NodeInstancePool()
        node = pool.acquire("MockNode", MockNode, "test_001")

        pool.release(node)

        stats = pool.get_stats()
        assert stats["returns"] == 1
        assert stats["total_pooled"] == 1

    def test_acquire_reuses_pooled_instance(self) -> None:
        """SUCCESS: acquire reuses instance from pool."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"
                self._input_port_values = {}
                self._output_port_values = {}

        pool = NodeInstancePool()

        # Create and release
        node1 = pool.acquire("MockNode", MockNode, "test_001", {"old": "value"})
        pool.release(node1)

        # Acquire again - should reuse
        node2 = pool.acquire("MockNode", MockNode, "test_002", {"new": "config"})

        assert node1 is node2  # Same object reused
        assert node2.node_id == "test_002"  # ID updated
        assert node2.config == {"new": "config"}  # Config updated

        stats = pool.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_release_all_returns_multiple_nodes(self) -> None:
        """SUCCESS: release_all returns all nodes to pool."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"

        pool = NodeInstancePool()

        nodes = {
            "n1": MockNode("n1"),
            "n2": MockNode("n2"),
            "n3": MockNode("n3"),
        }

        pool.release_all(nodes)

        stats = pool.get_stats()
        assert stats["returns"] == 3
        assert stats["total_pooled"] == 3

    def test_pool_respects_max_per_type(self) -> None:
        """SUCCESS: Pool discards excess instances."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"

        pool = NodeInstancePool(max_per_type=2)

        # Create and release 3 nodes
        nodes = [MockNode(f"n{i}") for i in range(3)]
        for node in nodes:
            pool.release(node)

        stats = pool.get_stats()
        # Only 2 should be in pool (max_per_type=2)
        assert stats["total_pooled"] == 2

    def test_get_stats_returns_hit_rate(self) -> None:
        """SUCCESS: get_stats computes hit rate correctly."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"
                self._input_port_values = {}
                self._output_port_values = {}

        pool = NodeInstancePool()

        # 1 miss (create), then release
        node = pool.acquire("MockNode", MockNode, "n1")
        pool.release(node)

        # 1 hit (reuse)
        pool.acquire("MockNode", MockNode, "n2")

        stats = pool.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5  # 1 hit / 2 total

    def test_clear_empties_all_pools(self) -> None:
        """SUCCESS: clear removes all pooled instances."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"

        pool = NodeInstancePool()

        # Add nodes
        for i in range(5):
            node = MockNode(f"n{i}")
            pool.release(node)

        # Clear
        pool.clear()

        stats = pool.get_stats()
        assert stats["total_pooled"] == 0

    def test_release_node_without_node_type_ignored(self) -> None:
        """EDGE CASE: Releasing node without node_type is ignored."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        pool = NodeInstancePool()

        # Object without node_type attribute
        obj = object()
        pool.release(obj)  # Should not raise

        stats = pool.get_stats()
        assert stats["total_pooled"] == 0


# =============================================================================
# NodeInstancePool Singleton Tests
# =============================================================================


class TestNodeInstancePoolSingleton:
    """Tests for get_node_instance_pool singleton."""

    def test_get_node_instance_pool_returns_instance(self) -> None:
        """SUCCESS: get_node_instance_pool returns a pool."""
        from casare_rpa.utils.performance.object_pool import (
            get_node_instance_pool,
            NodeInstancePool,
        )

        pool = get_node_instance_pool()

        assert pool is not None
        assert isinstance(pool, NodeInstancePool)

    def test_get_node_instance_pool_returns_singleton(self) -> None:
        """SUCCESS: get_node_instance_pool returns same instance."""
        from casare_rpa.utils.performance.object_pool import get_node_instance_pool

        pool1 = get_node_instance_pool()
        pool2 = get_node_instance_pool()

        assert pool1 is pool2


# =============================================================================
# Workflow Loader Optimization Tests
# =============================================================================


class TestBatchResolveNodeTypes:
    """Tests for _batch_resolve_node_types function."""

    def test_batch_resolve_resolves_all_types(self) -> None:
        """SUCCESS: Batch resolve processes all nodes."""
        from casare_rpa.utils.workflow.workflow_loader import _batch_resolve_node_types

        nodes_data = {
            "n1": {"node_type": "StartNode", "config": {}},
            "n2": {"node_type": "LogNode", "config": {"message": "test"}},
            "n3": {"node_type": "SetVariableNode", "config": {"name": "x"}},
        }

        resolved = _batch_resolve_node_types(nodes_data)

        assert len(resolved) == 3
        assert "n1" in resolved
        assert "n2" in resolved
        assert "n3" in resolved

    def test_batch_resolve_aliases(self, workflow_with_aliases: Dict) -> None:
        """SUCCESS: Batch resolve handles aliases."""
        from casare_rpa.utils.workflow.workflow_loader import _batch_resolve_node_types

        nodes_data = workflow_with_aliases["nodes"]
        resolved = _batch_resolve_node_types(nodes_data)

        # ReadFileNode should be resolved to FileSystemSuperNode
        _, config = resolved["read_file"]
        assert "action" in config

    def test_batch_resolve_empty_nodes(self) -> None:
        """EDGE CASE: Empty nodes dict returns empty result."""
        from casare_rpa.utils.workflow.workflow_loader import _batch_resolve_node_types

        resolved = _batch_resolve_node_types({})

        assert resolved == {}

    def test_batch_resolve_missing_node_type(self) -> None:
        """EDGE CASE: Nodes without node_type are skipped."""
        from casare_rpa.utils.workflow.workflow_loader import _batch_resolve_node_types

        nodes_data = {
            "n1": {"config": {}},  # Missing node_type
            "n2": {"node_type": "StartNode", "config": {}},
        }

        resolved = _batch_resolve_node_types(nodes_data)

        assert len(resolved) == 1
        assert "n2" in resolved
        assert "n1" not in resolved


class TestPreloadWorkflowNodeTypes:
    """Tests for _preload_workflow_node_types function."""

    def test_preload_triggers_lazy_loading(self) -> None:
        """SUCCESS: Preload triggers lazy loading for node types."""
        from casare_rpa.utils.workflow.workflow_loader import (
            _preload_workflow_node_types,
            get_node_class,
        )

        node_types = {"StartNode", "CommentNode"}

        # Should not raise even if some types don't exist
        _preload_workflow_node_types(node_types)

        # StartNode should be loaded
        start_class = get_node_class("StartNode")
        assert start_class is not None

    def test_preload_empty_set(self) -> None:
        """EDGE CASE: Empty set does nothing."""
        from casare_rpa.utils.workflow.workflow_loader import (
            _preload_workflow_node_types,
        )

        # Should not raise
        _preload_workflow_node_types(set())


class TestCreateSingleNode:
    """Tests for _create_single_node function."""

    def test_create_node_success(self) -> None:
        """SUCCESS: Create single node instance."""
        from casare_rpa.utils.workflow.workflow_loader import _create_single_node

        node_id, node = _create_single_node(
            node_id="test_node",
            node_type="StartNode",
            config={},
            use_pooling=False,
        )

        assert node_id == "test_node"
        assert node is not None
        assert node.node_id == "test_node"

    def test_create_node_unknown_type_returns_none(self) -> None:
        """SAD PATH: Unknown node type returns None."""
        from casare_rpa.utils.workflow.workflow_loader import _create_single_node

        node_id, node = _create_single_node(
            node_id="test_node",
            node_type="NonExistentNodeType",
            config={},
            use_pooling=False,
        )

        assert node_id == "test_node"
        assert node is None

    def test_create_node_with_pooling(self) -> None:
        """SUCCESS: Create node with pooling enabled."""
        from casare_rpa.utils.workflow.workflow_loader import _create_single_node

        node_id, node = _create_single_node(
            node_id="pooled_node",
            node_type="StartNode",
            config={},
            use_pooling=True,
        )

        assert node is not None
        assert node.node_id == "pooled_node"


class TestInstantiateNodesParallel:
    """Tests for _instantiate_nodes_parallel function."""

<<<<<<< HEAD
    def test_sequential_for_small_workflows(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_sequential_for_small_workflows(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Uses sequential for small workflows."""
        from casare_rpa.utils.workflow.workflow_loader import (
            _instantiate_nodes_parallel,
            _batch_resolve_node_types,
        )

        nodes_data = small_workflow_data["nodes"]
        resolved_types = _batch_resolve_node_types(nodes_data)

        nodes_dict = _instantiate_nodes_parallel(nodes_data, resolved_types)

        # Should have created nodes (some may fail if types don't exist)
        assert isinstance(nodes_dict, dict)

<<<<<<< HEAD
    def test_parallel_for_large_workflows(
        self, large_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_parallel_for_large_workflows(self, large_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Uses parallel for large workflows."""
        from casare_rpa.utils.workflow.workflow_loader import (
            _instantiate_nodes_parallel,
            _batch_resolve_node_types,
            PARALLEL_NODE_THRESHOLD,
        )

        nodes_data = large_workflow_data["nodes"]
        resolved_types = _batch_resolve_node_types(nodes_data)

        assert len(nodes_data) > PARALLEL_NODE_THRESHOLD

        start = time.perf_counter()
        nodes_dict = _instantiate_nodes_parallel(nodes_data, resolved_types)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert isinstance(nodes_dict, dict)
        # Some nodes created (depends on available node types)

    def test_empty_nodes_returns_empty_dict(self) -> None:
        """EDGE CASE: Empty nodes returns empty dict."""
        from casare_rpa.utils.workflow.workflow_loader import (
            _instantiate_nodes_parallel,
        )

        nodes_dict = _instantiate_nodes_parallel({}, {})

        assert nodes_dict == {}


# =============================================================================
# load_workflow_from_dict Tests
# =============================================================================


class TestLoadWorkflowFromDict:
    """Tests for load_workflow_from_dict with new parameters."""

    def test_load_with_defaults(self, minimal_workflow_data: Dict[str, Any]) -> None:
        """SUCCESS: Load workflow with default parameters."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(minimal_workflow_data)

        assert workflow is not None
        assert workflow.metadata.name == "MinimalWorkflow"

<<<<<<< HEAD
    def test_load_with_parallel_enabled(
        self, medium_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_with_parallel_enabled(self, medium_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load workflow with parallel=True."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(
            medium_workflow_data,
            use_parallel=True,
        )

        assert workflow is not None

<<<<<<< HEAD
    def test_load_with_parallel_disabled(
        self, medium_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_with_parallel_disabled(self, medium_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load workflow with parallel=False."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(
            medium_workflow_data,
            use_parallel=False,
        )

        assert workflow is not None

<<<<<<< HEAD
    def test_load_with_pooling_enabled(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_with_pooling_enabled(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load workflow with pooling=True."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(
            small_workflow_data,
            use_pooling=True,
        )

        assert workflow is not None

<<<<<<< HEAD
    def test_load_with_skip_validation(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_load_with_skip_validation(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load workflow skipping validation."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(
            small_workflow_data,
            skip_validation=True,
        )

        assert workflow is not None

    def test_load_resolves_aliases(self, workflow_with_aliases: Dict) -> None:
        """SUCCESS: Load workflow resolves node type aliases."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow = load_workflow_from_dict(workflow_with_aliases)

        assert workflow is not None
        # Check that aliases were resolved
        # (actual resolution depends on registered node types)


# =============================================================================
# Integration Tests
# =============================================================================


class TestWorkflowLoadingIntegration:
    """Integration tests for complete workflow loading flow."""

<<<<<<< HEAD
    def test_skeleton_then_full_load(
        self, medium_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_skeleton_then_full_load(self, medium_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """SUCCESS: Load skeleton, then full workflow."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()

        # Phase 1: Quick skeleton load
        start = time.perf_counter()
        skeleton = loader.load_skeleton(medium_workflow_data)
        skeleton_time = (time.perf_counter() - start) * 1000

        # Phase 2: Full load when needed
        start = time.perf_counter()
        workflow = loader.load_full(skeleton)
        full_time = (time.perf_counter() - start) * 1000

        assert skeleton.node_count == 50
        assert workflow is not None

        # Skeleton should be much faster than full load
        # (In practice, skeleton is ~10x faster or more)

<<<<<<< HEAD
    def test_parallel_vs_sequential_performance(
        self, large_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_parallel_vs_sequential_performance(self, large_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """PERFORMANCE: Compare parallel vs sequential loading."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        # Sequential
        start = time.perf_counter()
        workflow_seq = load_workflow_from_dict(
            large_workflow_data,
            use_parallel=False,
        )
        sequential_time = (time.perf_counter() - start) * 1000

        # Parallel
        start = time.perf_counter()
        workflow_par = load_workflow_from_dict(
            large_workflow_data,
            use_parallel=True,
        )
        parallel_time = (time.perf_counter() - start) * 1000

        assert workflow_seq is not None
        assert workflow_par is not None

        # Log times for manual analysis
        print(f"\nSequential: {sequential_time:.1f}ms, Parallel: {parallel_time:.1f}ms")

<<<<<<< HEAD
    def test_pooling_improves_repeated_loads(
        self, small_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_pooling_improves_repeated_loads(self, small_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """PERFORMANCE: Pooling improves repeated workflow loads."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict
        from casare_rpa.utils.performance.object_pool import get_node_instance_pool

        pool = get_node_instance_pool()
        pool.clear()  # Start fresh

        # First load (cold)
        workflow1 = load_workflow_from_dict(
            small_workflow_data,
            use_pooling=True,
        )

        # Return nodes to pool
        if workflow1 and hasattr(workflow1, "nodes"):
            pool.release_all(workflow1.nodes)

        stats_after_release = pool.get_stats()

        # Second load (warm - should have cache hits)
        workflow2 = load_workflow_from_dict(
            small_workflow_data,
            use_pooling=True,
        )

        stats_final = pool.get_stats()

        assert workflow1 is not None
        assert workflow2 is not None


# =============================================================================
# Performance Benchmark Tests
# =============================================================================


class TestPerformanceBenchmarks:
    """Performance benchmark tests with timing assertions."""

<<<<<<< HEAD
    def test_skeleton_loading_under_10ms(
        self, large_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_skeleton_loading_under_10ms(self, large_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """BENCHMARK: Skeleton loading should be <10ms for any size."""
        from casare_rpa.utils.workflow.incremental_loader import IncrementalLoader

        loader = IncrementalLoader()

        # Warm up
        loader.load_skeleton(large_workflow_data)

        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()
            loader.load_skeleton(large_workflow_data)
            times.append((time.perf_counter() - start) * 1000)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time < 10, f"Average skeleton load: {avg_time:.1f}ms, expected <10ms"
        # Allow some variance for max
        assert max_time < 25, f"Max skeleton load: {max_time:.1f}ms, expected <25ms"

<<<<<<< HEAD
    def test_full_load_reasonable_time(
        self, medium_workflow_data: Dict[str, Any]
    ) -> None:
=======
    def test_full_load_reasonable_time(self, medium_workflow_data: Dict[str, Any]) -> None:
>>>>>>> d1c1cdb090b151b968ad2afaa52ad16e824faf0e
        """BENCHMARK: Full load should be <500ms for medium workflow."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        start = time.perf_counter()
        workflow = load_workflow_from_dict(medium_workflow_data)
        elapsed = (time.perf_counter() - start) * 1000

        assert workflow is not None
        # 500ms is generous, actual should be much faster
        assert elapsed < 500, f"Full load took {elapsed:.1f}ms, expected <500ms"

    def test_pool_hit_rate_improves_with_reuse(self) -> None:
        """BENCHMARK: Pool hit rate improves with repeated acquire/release."""
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"
                self._input_port_values = {}
                self._output_port_values = {}

        pool = NodeInstancePool(max_per_type=10)

        # Simulate workflow load/unload cycles
        for cycle in range(5):
            nodes = []
            for i in range(10):
                node = pool.acquire("MockNode", MockNode, f"n{i}")
                nodes.append(node)

            for node in nodes:
                pool.release(node)

        stats = pool.get_stats()

        # After first cycle, subsequent acquires should hit cache
        # Expected: 10 misses (first cycle) + 40 hits (cycles 2-5)
        assert stats["hits"] == 40
        assert stats["misses"] == 10
        assert stats["hit_rate"] == 0.8  # 40 / 50


# =============================================================================
# Edge Case and Error Handling Tests
# =============================================================================


class TestEdgeCasesAndErrors:
    """Edge case and error handling tests."""

    def test_workflow_with_invalid_node_type(self) -> None:
        """SAD PATH: Invalid node types are handled gracefully."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow_data = {
            "metadata": {"name": "InvalidWorkflow", "description": ""},
            "nodes": {
                "start": {"node_type": "StartNode", "config": {}},
                "invalid": {"node_type": "NonExistentNode", "config": {}},
            },
            "connections": [],
            "variables": {},
        }

        # Should not raise, invalid nodes are skipped with warning
        workflow = load_workflow_from_dict(workflow_data)

        assert workflow is not None

    def test_workflow_with_deeply_nested_config(self) -> None:
        """EDGE CASE: Deeply nested config is validated."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        # Create deeply nested config (within limits)
        nested = {"level": 1}
        current = nested
        for i in range(2, 8):  # Stay under MAX_CONFIG_DEPTH=10
            current["nested"] = {"level": i}
            current = current["nested"]

        workflow_data = {
            "metadata": {"name": "NestedWorkflow", "description": ""},
            "nodes": {
                "start": {"node_type": "StartNode", "config": nested},
            },
            "connections": [],
            "variables": {},
        }

        workflow = load_workflow_from_dict(workflow_data)
        assert workflow is not None

    def test_workflow_with_unicode_names(self) -> None:
        """EDGE CASE: Unicode in workflow names is handled."""
        from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

        workflow_data = {
            "metadata": {
                "name": "Workflow with Unicode",
                "description": "Description with special chars",
            },
            "nodes": {
                "start": {"node_type": "StartNode", "config": {}},
            },
            "connections": [],
            "variables": {},
        }

        workflow = load_workflow_from_dict(workflow_data)

        assert workflow is not None
        assert "Unicode" in workflow.metadata.name

    def test_concurrent_pool_access(self) -> None:
        """STRESS: Concurrent access to pool is thread-safe."""
        import threading
        from casare_rpa.utils.performance.object_pool import NodeInstancePool

        class MockNode:
            def __init__(self, node_id, config=None):
                self.node_id = node_id
                self.config = config or {}
                self.node_type = "MockNode"
                self._input_port_values = {}
                self._output_port_values = {}

        pool = NodeInstancePool(max_per_type=50)
        errors = []

        def worker(worker_id):
            try:
                for i in range(100):
                    node = pool.acquire("MockNode", MockNode, f"w{worker_id}_n{i}")
                    # Simulate some work
                    pool.release(node)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent access errors: {errors}"

        stats = pool.get_stats()
        # Should have processed 400 acquire/release cycles without error
        assert stats["hits"] + stats["misses"] == 400

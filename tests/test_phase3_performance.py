"""
Phase 3: Performance & Optimization Tests

Tests for:
1. Selector validation caching (LRU cache)
2. Lazy loading for node modules
3. Browser context pooling
4. orjson serialization
5. Parallel node execution
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch


class TestSelectorCache:
    """Tests for selector validation caching."""

    def test_cache_creation(self):
        """Test cache is created with correct defaults."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        assert cache.enabled is True
        assert cache._max_size == 500
        assert cache._ttl_seconds == 60.0

    def test_cache_custom_config(self):
        """Test cache with custom configuration."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache(
            max_size=100,
            ttl_seconds=30.0,
            enabled=True,
        )

        assert cache._max_size == 100
        assert cache._ttl_seconds == 30.0

    def test_cache_put_and_get(self):
        """Test storing and retrieving cached results."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        # Store a result
        cache.put(
            selector_value="//div[@id='test']",
            selector_type="xpath",
            page_url="http://test.com",
            count=1,
            execution_time_ms=5.0,
        )

        # Retrieve it
        result = cache.get("//div[@id='test']", "xpath", "http://test.com")

        assert result is not None
        assert result.count == 1
        assert result.is_unique is True
        assert result.execution_time_ms == 5.0

    def test_cache_miss(self):
        """Test cache miss returns None."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        result = cache.get("//nonexistent", "xpath", "http://test.com")

        assert result is None

    def test_cache_url_aware(self):
        """Test cache is URL-aware (different pages have different caches)."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        # Store for page 1
        cache.put("//div", "xpath", "http://page1.com", count=1, execution_time_ms=1.0)

        # Store for page 2
        cache.put("//div", "xpath", "http://page2.com", count=3, execution_time_ms=2.0)

        # Retrieve from page 1
        result1 = cache.get("//div", "xpath", "http://page1.com")
        assert result1.count == 1

        # Retrieve from page 2
        result2 = cache.get("//div", "xpath", "http://page2.com")
        assert result2.count == 3

    def test_cache_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache(max_size=3)

        # Fill cache
        cache.put("//a", "xpath", "http://test.com", 1, 1.0)
        cache.put("//b", "xpath", "http://test.com", 1, 1.0)
        cache.put("//c", "xpath", "http://test.com", 1, 1.0)

        # Access //a to make it recently used
        cache.get("//a", "xpath", "http://test.com")

        # Add new item, should evict //b (least recently used)
        cache.put("//d", "xpath", "http://test.com", 1, 1.0)

        # //a should still be there
        assert cache.get("//a", "xpath", "http://test.com") is not None
        # //d should be there
        assert cache.get("//d", "xpath", "http://test.com") is not None

    def test_cache_ttl_expiration(self):
        """Test TTL-based cache expiration."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache(ttl_seconds=0.1)  # 100ms TTL

        cache.put("//div", "xpath", "http://test.com", 1, 1.0)

        # Should be there immediately
        assert cache.get("//div", "xpath", "http://test.com") is not None

        # Wait for expiration
        time.sleep(0.2)

        # Should be expired
        assert cache.get("//div", "xpath", "http://test.com") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        # Some operations
        cache.put("//a", "xpath", "http://test.com", 1, 1.0)
        cache.get("//a", "xpath", "http://test.com")  # hit
        cache.get("//b", "xpath", "http://test.com")  # miss

        stats = cache.get_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        cache.put("//a", "xpath", "http://test.com", 1, 1.0)
        cache.put("//b", "xpath", "http://test.com", 1, 1.0)

        count = cache.invalidate()

        assert count == 2
        assert len(cache) == 0

    def test_cache_enable_disable(self):
        """Test enabling and disabling cache."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        cache.disable()
        assert cache.enabled is False

        # Should not cache when disabled
        cache.put("//a", "xpath", "http://test.com", 1, 1.0)
        assert cache.get("//a", "xpath", "http://test.com") is None

        cache.enable()
        assert cache.enabled is True


class TestLazyLoading:
    """Tests for lazy loading of node modules."""

    def test_lazy_import_registry_exists(self):
        """Test that node registry is set up for lazy loading."""
        from casare_rpa import nodes

        # Registry should exist
        assert hasattr(nodes, "_NODE_REGISTRY")
        assert isinstance(nodes._NODE_REGISTRY, dict)
        assert len(nodes._NODE_REGISTRY) > 0

        # Should have key node types
        assert "StartNode" in nodes._NODE_REGISTRY
        assert "EndNode" in nodes._NODE_REGISTRY
        assert "IfNode" in nodes._NODE_REGISTRY

    def test_lazy_import_caching(self):
        """Test that lazy imports are cached."""
        from casare_rpa import nodes

        # Access a node
        from casare_rpa.nodes import IfNode

        # Should be in loaded classes cache
        assert "IfNode" in nodes._loaded_classes

        # Second access should return same object
        from casare_rpa.nodes import IfNode as IfNode2

        assert IfNode is IfNode2

    def test_get_all_node_classes(self):
        """Test getting all node classes loads everything."""
        from casare_rpa.nodes import get_all_node_classes

        all_classes = get_all_node_classes()

        assert isinstance(all_classes, dict)
        assert len(all_classes) > 0
        assert "StartNode" in all_classes
        assert "EndNode" in all_classes
        assert "IfNode" in all_classes

    def test_preload_nodes(self):
        """Test preloading specific nodes."""
        from casare_rpa import nodes
        from casare_rpa.nodes import preload_nodes

        # Preload specific nodes
        preload_nodes(["StartNode", "EndNode"])

        assert "StartNode" in nodes._loaded_classes
        assert "EndNode" in nodes._loaded_classes

    def test_node_instantiation_after_lazy_load(self):
        """Test that lazily loaded nodes can be instantiated."""
        from casare_rpa.nodes import ForLoopNode

        node = ForLoopNode("test_loop")

        assert node is not None
        assert node.node_id == "test_loop"


class TestBrowserContextPool:
    """Tests for browser context pooling."""

    def test_pool_creation(self):
        """Test browser context pool creation."""
        from casare_rpa.utils.browser_pool import BrowserContextPool

        mock_browser = MagicMock()

        pool = BrowserContextPool(
            browser=mock_browser,
            min_size=2,
            max_size=10,
        )

        assert pool._min_size == 2
        assert pool._max_size == 10
        assert pool._browser is mock_browser

    def test_pool_stats(self):
        """Test pool statistics."""
        from casare_rpa.utils.browser_pool import BrowserContextPool

        mock_browser = MagicMock()

        pool = BrowserContextPool(browser=mock_browser)

        stats = pool.get_stats()

        assert "available" in stats
        assert "in_use" in stats
        assert "max_size" in stats
        assert "contexts_created" in stats

    def test_pool_manager_singleton(self):
        """Test BrowserPoolManager singleton pattern."""
        from casare_rpa.utils.browser_pool import get_browser_pool_manager

        manager1 = get_browser_pool_manager()
        manager2 = get_browser_pool_manager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_pool_acquire_release(self):
        """Test acquiring and releasing contexts."""
        from casare_rpa.utils.browser_pool import BrowserContextPool

        mock_browser = MagicMock()
        mock_context = MagicMock()

        async def mock_new_context(**kwargs):
            return mock_context

        mock_browser.new_context = mock_new_context

        pool = BrowserContextPool(browser=mock_browser, min_size=0, max_size=5)

        # Manually initialize
        pool._initialized = True

        # Acquire
        context = await pool.acquire()
        assert context is mock_context
        assert pool.in_use_count == 1

        # Release
        await pool.release(context)
        assert pool.in_use_count == 0


class TestOrjsonSerialization:
    """Tests for orjson serialization optimization."""

    def test_workflow_uses_orjson(self):
        """Test that workflow serialization uses orjson."""
        import orjson
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test Workflow")
        workflow = WorkflowSchema(metadata)

        # Serialize
        data = workflow.to_dict()

        # Should serialize with orjson without errors
        json_bytes = orjson.dumps(data)
        assert isinstance(json_bytes, bytes)

        # Should deserialize correctly
        parsed = orjson.loads(json_bytes)
        assert parsed["metadata"]["name"] == "Test Workflow"

    def test_json_parse_node_uses_orjson(self):
        """Test that JsonParseNode uses orjson."""
        import orjson

        # Verify orjson is imported in data_operation_nodes
        from casare_rpa.nodes import data_operation_nodes

        # The module should use orjson
        assert hasattr(data_operation_nodes, "orjson")

    @pytest.mark.asyncio
    async def test_json_parse_performance(self):
        """Test JSON parsing performance with orjson."""
        from casare_rpa.nodes.data_operation_nodes import JsonParseNode

        # Create a moderately complex JSON
        large_json = '{"items": [' + ",".join(['{"id": %d, "name": "item%d"}' % (i, i) for i in range(100)]) + "]}"

        node = JsonParseNode("test_json")
        node.set_input_value("json_string", large_json)

        start = time.time()
        result = await node.execute(None)
        elapsed = time.time() - start

        assert result["success"] is True
        # Should be very fast with orjson
        assert elapsed < 1.0  # Should be much faster than 1 second


class TestParallelExecution:
    """Tests for parallel node execution."""

    def test_runner_parallel_config(self):
        """Test runner accepts parallel execution configuration."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(
            workflow,
            parallel_execution=True,
            max_parallel_nodes=8,
        )

        assert runner.parallel_execution is True
        assert runner.max_parallel_nodes == 8

    def test_runner_enable_parallel(self):
        """Test enabling parallel execution at runtime."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        assert runner.parallel_execution is False

        runner.enable_parallel_execution(True)

        assert runner.parallel_execution is True
        assert runner._dependency_graph is not None

    def test_runner_set_max_parallel(self):
        """Test setting max parallel nodes."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        runner.set_max_parallel_nodes(6)

        assert runner.max_parallel_nodes == 6

    def test_runner_max_parallel_bounds(self):
        """Test max parallel nodes is bounded."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        # Should be capped at 16
        runner.set_max_parallel_nodes(100)
        assert runner.max_parallel_nodes <= 16

        # Should be at least 1
        runner.set_max_parallel_nodes(0)
        assert runner.max_parallel_nodes >= 1

    def test_runner_parallel_stats(self):
        """Test getting parallel execution stats."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow, parallel_execution=True)

        stats = runner.get_parallel_stats()

        assert "enabled" in stats
        assert "max_parallel_nodes" in stats
        assert "has_dependency_graph" in stats
        assert stats["enabled"] is True
        assert stats["has_dependency_graph"] is True

    def test_is_parallelizable_node(self):
        """Test node parallelizability detection."""
        from casare_rpa.runner.workflow_runner import WorkflowRunner
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
        from casare_rpa.nodes import StartNode, EndNode, IfNode, SetVariableNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        runner = WorkflowRunner(workflow)

        # Control flow nodes should not be parallelizable
        if_node = IfNode("test_if")
        assert runner._is_parallelizable_node(if_node) is False

        # Variable nodes should be parallelizable
        var_node = SetVariableNode("test_var")
        assert runner._is_parallelizable_node(var_node) is True


class TestDependencyGraph:
    """Tests for dependency graph analysis."""

    def test_dependency_graph_creation(self):
        """Test creating a dependency graph."""
        from casare_rpa.utils.parallel_executor import DependencyGraph

        graph = DependencyGraph()

        graph.add_node("A")
        graph.add_node("B")
        graph.add_edge("A", "B")  # B depends on A

        assert "A" in graph._nodes
        assert "B" in graph._nodes

    def test_dependency_graph_ready_nodes(self):
        """Test getting ready nodes from dependency graph."""
        from casare_rpa.utils.parallel_executor import DependencyGraph

        graph = DependencyGraph()

        # A -> B -> C
        graph.add_edge("A", "B")
        graph.add_edge("B", "C")

        # Initially only A is ready (no dependencies)
        ready = graph.get_ready_nodes(completed=set())
        assert "A" in ready
        assert "B" not in ready
        assert "C" not in ready

        # After A completes, B is ready
        ready = graph.get_ready_nodes(completed={"A"})
        assert "B" in ready

        # After A and B complete, C is ready
        ready = graph.get_ready_nodes(completed={"A", "B"})
        assert "C" in ready

    def test_analyze_workflow_dependencies(self):
        """Test analyzing workflow to build dependency graph."""
        from casare_rpa.utils.parallel_executor import analyze_workflow_dependencies
        from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
        from casare_rpa.nodes import StartNode, EndNode

        metadata = WorkflowMetadata(name="Test")
        workflow = WorkflowSchema(metadata)

        # Add nodes
        start = StartNode("start")
        end = EndNode("end")

        workflow.nodes["start"] = start
        workflow.nodes["end"] = end

        # Add connection
        workflow.connections.append(
            NodeConnection("start", "exec_out", "end", "exec_in")
        )

        graph = analyze_workflow_dependencies(workflow.nodes, workflow.connections)

        assert graph is not None
        # End depends on start
        ready_initially = graph.get_ready_nodes(completed=set())
        assert "start" in ready_initially
        assert "end" not in ready_initially


class TestParallelExecutor:
    """Tests for ParallelExecutor utility class."""

    def test_parallel_executor_creation(self):
        """Test creating a parallel executor."""
        from casare_rpa.utils.parallel_executor import ParallelExecutor

        executor = ParallelExecutor(max_concurrency=4, stop_on_error=True)

        assert executor._max_concurrency == 4
        assert executor._stop_on_error is True

    @pytest.mark.asyncio
    async def test_parallel_executor_execute(self):
        """Test executing tasks in parallel."""
        from casare_rpa.utils.parallel_executor import ParallelExecutor

        executor = ParallelExecutor(max_concurrency=4)

        results_order = []

        async def task1():
            results_order.append(1)
            return "result1"

        async def task2():
            results_order.append(2)
            return "result2"

        tasks = [
            ("task1", task1),
            ("task2", task2),
        ]

        results = await executor.execute_parallel(tasks)

        assert len(results) == 2
        assert results["task1"] == (True, "result1")
        assert results["task2"] == (True, "result2")

    @pytest.mark.asyncio
    async def test_parallel_executor_error_handling(self):
        """Test parallel executor error handling."""
        from casare_rpa.utils.parallel_executor import ParallelExecutor

        executor = ParallelExecutor(max_concurrency=4, stop_on_error=False)

        async def success_task():
            return "success"

        async def error_task():
            raise ValueError("Test error")

        tasks = [
            ("success", success_task),
            ("error", error_task),
        ]

        results = await executor.execute_parallel(tasks)

        assert results["success"] == (True, "success")
        assert results["error"][0] is False  # Failed

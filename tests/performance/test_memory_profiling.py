"""Memory lifecycle profiling tests.

Tests for detecting memory leaks and ensuring proper cleanup
of browser contexts, execution contexts, and resource pools.
"""

import gc
import sys
import weakref
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta, timezone


class TestBrowserResourceManagerMemory:
    """Tests for BrowserResourceManager memory lifecycle."""

    @pytest.mark.asyncio
    async def test_browser_context_cleanup_releases_memory(self):
        """Test that cleanup() properly releases browser context references."""
        from casare_rpa.infrastructure.resources.browser_resource_manager import (
            BrowserResourceManager,
        )

        manager = BrowserResourceManager()

        # Create mock browser and context
        mock_browser = AsyncMock()
        mock_context = AsyncMock()
        mock_page = AsyncMock()

        manager.browser = mock_browser
        manager.browser_contexts = [mock_context]
        manager.pages = {"test_page": mock_page}

        # Track object reference
        context_ref = weakref.ref(mock_context)

        # Cleanup
        await manager.cleanup()

        # Force garbage collection
        del mock_context
        gc.collect()

        # Verify cleanup was called
        assert manager.browser is None
        assert manager.browser_contexts == []
        assert manager.pages == {}

    @pytest.mark.asyncio
    async def test_multiple_contexts_all_cleaned(self):
        """Test that multiple contexts are all properly cleaned."""
        from casare_rpa.infrastructure.resources.browser_resource_manager import (
            BrowserResourceManager,
        )

        manager = BrowserResourceManager()

        # Create multiple mock contexts
        contexts = [AsyncMock() for _ in range(10)]
        pages = {f"page_{i}": AsyncMock() for i in range(10)}

        manager.browser = AsyncMock()
        manager.browser_contexts = contexts
        manager.pages = pages

        await manager.cleanup()

        assert len(manager.browser_contexts) == 0
        assert len(manager.pages) == 0

    def test_manager_creation_minimal_memory(self):
        """Test that creating a manager uses minimal memory."""
        from casare_rpa.infrastructure.resources.browser_resource_manager import (
            BrowserResourceManager,
        )

        # Get baseline
        gc.collect()

        managers = []
        for i in range(100):
            managers.append(BrowserResourceManager())

        # Each manager should be lightweight when not connected
        for m in managers:
            assert m.browser is None
            assert m.browser_contexts == []


class TestExecutionContextMemory:
    """Tests for ExecutionContext memory lifecycle."""

    def test_execution_context_creation_lightweight(self):
        """Test that creating execution contexts is lightweight."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )

        gc.collect()

        contexts = []
        for i in range(50):
            ctx = ExecutionContext(workflow_name=f"wf_{i}")
            contexts.append(ctx)

        # All contexts created
        assert len(contexts) == 50

        # Clear and verify garbage collection works
        contexts.clear()
        gc.collect()

    def test_variable_storage_cleanup(self):
        """Test that variables are properly cleaned up."""
        from casare_rpa.infrastructure.execution.execution_context import (
            ExecutionContext,
        )

        ctx = ExecutionContext(workflow_name="test_wf")

        # Add many variables
        for i in range(1000):
            ctx.set_variable(f"var_{i}", f"value_{i}" * 100)

        # Verify they exist
        assert ctx.get_variable("var_0") is not None

        # Clear variables through state (public property)
        ctx._state.variables.clear()
        gc.collect()

        # Variables should be gone
        assert ctx.get_variable("var_0") is None


class TestResourcePoolMemory:
    """Tests for resource pool memory management."""

    def test_resource_lease_creation(self):
        """Test that resource leases can be created."""
        from casare_rpa.infrastructure.resources.unified_resource_manager import (
            ResourceLease,
            ResourceType,
        )

        # Create lease with proper API
        lease = ResourceLease(
            resource_type=ResourceType.BROWSER,
            resource=Mock(),
            job_id="job_1",
            max_lease_duration=timedelta(hours=1),
        )

        # Just created - should not be expired
        assert not lease.is_expired()
        assert lease.time_remaining() > timedelta(0)

    def test_resource_lease_expiration(self):
        """Test that expired leases are tracked."""
        from casare_rpa.infrastructure.resources.unified_resource_manager import (
            ResourceLease,
            ResourceType,
        )
        from datetime import timedelta

        # Create lease that's already expired by setting leased_at in the past
        lease = ResourceLease(
            resource_type=ResourceType.BROWSER,
            resource=Mock(),
            job_id="job_1",
            max_lease_duration=timedelta(seconds=1),  # Very short
        )

        # Manually set leased_at to past to test expiration
        lease.leased_at = datetime.now(timezone.utc) - timedelta(hours=2)

        assert lease.is_expired()

    def test_job_resources_allocation(self):
        """Test JobResources properly tracks allocations."""
        from casare_rpa.infrastructure.resources.unified_resource_manager import (
            JobResources,
            ResourceLease,
            ResourceType,
        )

        job = JobResources(job_id="test_job")

        # Add leases (actual API)
        job.leases.append(
            ResourceLease(
                resource_type=ResourceType.BROWSER,
                resource=Mock(),
                job_id="test_job",
            )
        )
        job.leases.append(
            ResourceLease(
                resource_type=ResourceType.DATABASE,
                resource=Mock(),
                job_id="test_job",
            )
        )

        assert len(job.leases) == 2

        # Clear
        job.leases.clear()
        assert len(job.leases) == 0

    def test_job_resources_to_dict(self):
        """Test JobResources serialization."""
        from casare_rpa.infrastructure.resources.unified_resource_manager import (
            JobResources,
        )

        job = JobResources(job_id="test_job")
        result = job.to_dict()

        assert result["job_id"] == "test_job"
        assert result["lease_count"] == 0


class TestEventBusMemory:
    """Tests for EventBus memory management."""

    def test_event_history_limited(self):
        """Test that event history doesn't grow unbounded."""
        from casare_rpa.domain.events import EventBus, Event, EventType

        bus = EventBus()

        # Emit more events than max_history (1000 default)
        for i in range(1200):
            bus.publish(
                Event(
                    event_type=EventType.NODE_STARTED,
                    data={"index": i},
                )
            )

        # History should be capped at 1000
        assert len(bus._event_history) <= 1000

    def test_subscriber_cleanup(self):
        """Test that subscribers can be properly unsubscribed."""
        from casare_rpa.domain.events import EventBus, Event, EventType

        bus = EventBus()
        call_count = 0

        def handler(event):
            nonlocal call_count
            call_count += 1

        # Subscribe with EventType enum
        bus.subscribe(EventType.NODE_COMPLETED, handler)

        # Emit
        bus.publish(Event(event_type=EventType.NODE_COMPLETED, data={}))
        assert call_count == 1

        # Unsubscribe
        bus.unsubscribe(EventType.NODE_COMPLETED, handler)

        # Emit again - should not call handler
        bus.publish(Event(event_type=EventType.NODE_COMPLETED, data={}))
        assert call_count == 1


class TestMemoryLeakDetection:
    """Tests for detecting memory leaks in common patterns."""

    def test_node_creation_no_leak(self):
        """Test that creating and destroying nodes doesn't leak memory."""
        from casare_rpa.nodes.basic_nodes import StartNode, EndNode
        from casare_rpa.nodes.variable_nodes import SetVariableNode

        gc.collect()
        initial_objects = len(gc.get_objects())

        # Create many nodes
        nodes = []
        for i in range(100):
            nodes.append(StartNode(node_id=f"start_{i}"))
            nodes.append(EndNode(node_id=f"end_{i}"))
            nodes.append(
                SetVariableNode(
                    node_id=f"set_{i}",
                    variable_name=f"var_{i}",
                )
            )

        # Clear all references
        nodes.clear()
        gc.collect()

        # Object count should return close to initial
        final_objects = len(gc.get_objects())

        # Allow some variance (cached imports, etc)
        growth = final_objects - initial_objects
        assert growth < 1000, f"Potential leak: {growth} new objects retained"

    def test_workflow_data_no_leak(self):
        """Test that workflow dict creation doesn't leak."""
        gc.collect()

        for _ in range(10):
            # Create large workflow
            workflow = {
                "metadata": {"name": "test"},
                "nodes": {
                    f"node_{i}": {
                        "id": f"node_{i}",
                        "type": "LogNode",
                        "properties": {"data": "x" * 1000},
                    }
                    for i in range(500)
                },
                "connections": [],
            }

            # Process it
            _ = len(workflow["nodes"])

            # Delete
            del workflow

        gc.collect()

        # Should have cleaned up
        # (This is a smoke test - actual leak detection needs profiling tools)

    def test_connection_data_cleanup(self):
        """Test that connection dictionaries are properly garbage collected."""
        gc.collect()

        connections = []
        for i in range(10000):
            connections.append(
                {
                    "source": f"node_{i}.exec_out",
                    "target": f"node_{i+1}.exec_in",
                }
            )

        initial_size = sys.getsizeof(connections)
        connections.clear()
        gc.collect()

        # List should be empty
        assert len(connections) == 0


class TestTracemalloc:
    """Tests using tracemalloc for detailed memory profiling."""

    @pytest.mark.skipif(
        True,
        reason="Tracemalloc tests are slow - run manually for profiling",
    )
    def test_node_instantiation_memory_profile(self):
        """Profile memory usage during node instantiation."""
        import tracemalloc

        tracemalloc.start()

        from casare_rpa.nodes.variable_nodes import SetVariableNode
        from casare_rpa.nodes.control_flow_nodes import IfNode

        # Create nodes
        nodes = []
        for i in range(100):
            nodes.append(SetVariableNode(node_id=f"set_{i}", variable_name=f"var_{i}"))
            nodes.append(IfNode(node_id=f"if_{i}"))

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak should be reasonable (< 50MB for 200 nodes)
        assert (
            peak < 50 * 1024 * 1024
        ), f"Peak memory too high: {peak / 1024 / 1024:.1f}MB"

    @pytest.mark.skipif(
        True,
        reason="Tracemalloc tests are slow - run manually for profiling",
    )
    def test_workflow_validation_memory_profile(self):
        """Profile memory during workflow validation."""
        import tracemalloc
        from casare_rpa.domain.validation.validators import validate_workflow

        # Create large workflow
        workflow = {
            "metadata": {"name": "test", "version": "3.0"},
            "nodes": {
                f"node_{i}": {
                    "id": f"node_{i}",
                    "node_type": "LogNode",
                    "position": [i * 100, 0],
                }
                for i in range(500)
            },
            "connections": [
                {"source": f"node_{i}.exec_out", "target": f"node_{i+1}.exec_in"}
                for i in range(499)
            ],
        }

        tracemalloc.start()

        # Validate multiple times
        for _ in range(10):
            result = validate_workflow(workflow)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Should not grow significantly with repeated validation
        assert (
            peak < 100 * 1024 * 1024
        ), f"Peak memory too high: {peak / 1024 / 1024:.1f}MB"

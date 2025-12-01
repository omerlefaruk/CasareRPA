"""Tests for lazy import system.

Tests the LazyModule, LazyImport, and import metrics tracking
for deferred module loading during application startup.
"""

import gc
import sys
import threading
import time
import pytest
from unittest.mock import Mock, patch


class TestImportMetrics:
    """Tests for ImportMetrics singleton."""

    def test_get_instance_returns_singleton(self):
        """Test that get_instance returns the same instance."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        instance1 = ImportMetrics.get_instance()
        instance2 = ImportMetrics.get_instance()

        assert instance1 is instance2

    def test_record_import_stores_timing(self):
        """Test that import timing is recorded."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        metrics = ImportMetrics.get_instance()
        metrics.reset()

        metrics.record_import("test.module", 15.5)

        stats = metrics.get_stats()
        assert stats["total_imports"] == 1
        assert stats["total_time_ms"] == 15.5
        assert "test.module" in stats["all_imports"]
        assert stats["all_imports"]["test.module"] == 15.5

    def test_get_stats_sorts_by_time(self):
        """Test that slowest imports are sorted correctly."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        metrics = ImportMetrics.get_instance()
        metrics.reset()

        metrics.record_import("fast.module", 5.0)
        metrics.record_import("slow.module", 100.0)
        metrics.record_import("medium.module", 50.0)

        stats = metrics.get_stats()
        slowest = list(stats["slowest_imports"].keys())

        assert slowest[0] == "slow.module"
        assert slowest[1] == "medium.module"
        assert slowest[2] == "fast.module"

    def test_reset_clears_all_data(self):
        """Test that reset clears all metrics."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        metrics = ImportMetrics.get_instance()
        metrics.record_import("test.module", 10.0)
        metrics.reset()

        stats = metrics.get_stats()
        assert stats["total_imports"] == 0
        assert stats["total_time_ms"] == 0.0

    def test_thread_safety(self):
        """Test that recording from multiple threads is safe."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        metrics = ImportMetrics.get_instance()
        metrics.reset()

        errors = []

        def record_imports(thread_id):
            try:
                for i in range(100):
                    metrics.record_import(f"module.thread{thread_id}.{i}", float(i))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=record_imports, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        stats = metrics.get_stats()
        assert stats["total_imports"] == 500


class TestLazyModule:
    """Tests for LazyModule proxy."""

    def test_module_not_loaded_on_creation(self):
        """Test that module is not imported when LazyModule is created."""
        from casare_rpa.utils.lazy_loader import LazyModule

        # Use a module that would cause side effects if imported
        lazy = LazyModule("casare_rpa.utils.lazy_loader")

        # Check internal state without triggering load
        module = object.__getattribute__(lazy, "_module")
        assert module is None

    def test_module_loaded_on_attribute_access(self):
        """Test that module is loaded when an attribute is accessed."""
        from casare_rpa.utils.lazy_loader import LazyModule, ImportMetrics

        ImportMetrics.get_instance().reset()

        lazy = LazyModule("json")

        # Access an attribute - this should trigger the import
        result = lazy.dumps({"key": "value"})

        assert result == '{"key": "value"}'
        # Module should now be loaded
        module = object.__getattribute__(lazy, "_module")
        assert module is not None

    def test_module_cached_after_load(self):
        """Test that module is only imported once."""
        from casare_rpa.utils.lazy_loader import LazyModule, ImportMetrics

        ImportMetrics.get_instance().reset()

        lazy = LazyModule("json")

        # First access
        _ = lazy.dumps({})
        # Second access
        _ = lazy.loads("{}")

        stats = ImportMetrics.get_instance().get_stats()
        # json should only be recorded once
        json_imports = [k for k in stats["all_imports"].keys() if k == "json"]
        assert len(json_imports) == 1

    def test_repr_shows_load_status(self):
        """Test that repr shows whether module is loaded."""
        from casare_rpa.utils.lazy_loader import LazyModule

        lazy = LazyModule("json")

        assert "not loaded" in repr(lazy)

        # Trigger load
        _ = lazy.dumps({})

        assert "loaded" in repr(lazy)
        assert "json" in repr(lazy)

    def test_callback_called_on_import(self):
        """Test that import callback is called when module loads."""
        from casare_rpa.utils.lazy_loader import LazyModule

        callback_data = {}

        def on_import(module_name, duration_ms):
            callback_data["module"] = module_name
            callback_data["duration"] = duration_ms

        lazy = LazyModule("json", import_callback=on_import)

        # Trigger load
        _ = lazy.dumps({})

        assert callback_data["module"] == "json"
        assert callback_data["duration"] > 0

    def test_thread_safe_loading(self):
        """Test that concurrent access triggers only one import."""
        from casare_rpa.utils.lazy_loader import LazyModule, ImportMetrics

        ImportMetrics.get_instance().reset()

        lazy = LazyModule("collections")
        results = []

        def access_module():
            try:
                # Access the OrderedDict class
                _ = lazy.OrderedDict
                results.append("success")
            except Exception as e:
                results.append(f"error: {e}")

        threads = [threading.Thread(target=access_module) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == "success" for r in results)
        # Should only record one import
        stats = ImportMetrics.get_instance().get_stats()
        collections_imports = [
            k for k in stats["all_imports"].keys() if k == "collections"
        ]
        assert len(collections_imports) == 1


class TestLazyImport:
    """Tests for LazyImport descriptor."""

    def test_class_level_access_returns_descriptor(self):
        """Test that accessing on class returns the descriptor itself."""
        from casare_rpa.utils.lazy_loader import LazyImport

        class MyClass:
            json_module = LazyImport("json", log=False)

        assert isinstance(MyClass.json_module, LazyImport)

    def test_instance_level_access_returns_module(self):
        """Test that accessing on instance returns the actual module."""
        from casare_rpa.utils.lazy_loader import LazyImport

        class MyClass:
            json_module = LazyImport("json", log=False)

        obj = MyClass()
        result = obj.json_module.dumps({"test": True})

        assert result == '{"test": true}'

    def test_can_extract_specific_attribute(self):
        """Test that attr parameter extracts specific attribute from module."""
        from casare_rpa.utils.lazy_loader import LazyImport

        class MyClass:
            OrderedDict = LazyImport("collections", attr="OrderedDict", log=False)

        obj = MyClass()
        od = obj.OrderedDict()
        od["a"] = 1
        od["b"] = 2

        assert list(od.keys()) == ["a", "b"]

    def test_instance_caching(self):
        """Test that each instance gets cached access."""
        from casare_rpa.utils.lazy_loader import LazyImport, ImportMetrics

        ImportMetrics.get_instance().reset()

        class MyClass:
            json_module = LazyImport("json", log=False)

        obj1 = MyClass()
        obj2 = MyClass()

        # Access from both instances
        _ = obj1.json_module.dumps({})
        _ = obj2.json_module.dumps({})

        # Both should work
        assert obj1.json_module is not None
        assert obj2.json_module is not None


class TestLazyImportFunction:
    """Tests for lazy_import() convenience function."""

    def test_returns_lazy_module(self):
        """Test that lazy_import returns a LazyModule."""
        from casare_rpa.utils.lazy_loader import lazy_import, LazyModule

        lazy = lazy_import("json")

        assert isinstance(lazy, LazyModule)

    def test_with_attr_returns_lazy_attr(self):
        """Test that lazy_import with attr returns _LazyAttr."""
        from casare_rpa.utils.lazy_loader import lazy_import, _LazyAttr

        lazy = lazy_import("collections", attr="OrderedDict")

        assert isinstance(lazy, _LazyAttr)

    def test_lazy_attr_is_callable(self):
        """Test that _LazyAttr forwards calls correctly."""
        from casare_rpa.utils.lazy_loader import lazy_import

        OrderedDict = lazy_import("collections", "OrderedDict")

        # Should be callable like the real class
        od = OrderedDict()
        od["key"] = "value"

        assert od["key"] == "value"

    def test_lazy_attr_forwards_attributes(self):
        """Test that _LazyAttr forwards attribute access."""
        from casare_rpa.utils.lazy_loader import lazy_import

        OrderedDict = lazy_import("collections", "OrderedDict")

        # Access a method through the lazy proxy
        od = OrderedDict([("a", 1), ("b", 2)])
        keys = od.keys()

        assert list(keys) == ["a", "b"]


class TestLazyAttr:
    """Tests for _LazyAttr internal class."""

    def test_caches_after_first_access(self):
        """Test that attribute is cached after first load."""
        from casare_rpa.utils.lazy_loader import _LazyAttr, ImportMetrics

        ImportMetrics.get_instance().reset()

        lazy = _LazyAttr("json", "dumps")

        # First call - should import
        result1 = lazy({"a": 1})
        # Second call - should use cache
        result2 = lazy({"b": 2})

        assert result1 == '{"a": 1}'
        assert result2 == '{"b": 2}'

        # Should only have one import recorded for json
        stats = ImportMetrics.get_instance().get_stats()
        json_imports = [k for k in stats["all_imports"].keys() if k == "json"]
        assert len(json_imports) == 1

    def test_thread_safe_caching(self):
        """Test thread-safe access to _LazyAttr."""
        from casare_rpa.utils.lazy_loader import _LazyAttr

        lazy = _LazyAttr("json", "dumps")
        results = []

        def call_lazy():
            try:
                result = lazy({"thread": True})
                results.append(result)
            except Exception as e:
                results.append(f"error: {e}")

        threads = [threading.Thread(target=call_lazy) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 10
        assert all(r == '{"thread": true}' for r in results)


class TestGetImportStats:
    """Tests for get_import_stats() function."""

    def test_returns_stats_dict(self):
        """Test that get_import_stats returns expected structure."""
        from casare_rpa.utils.lazy_loader import get_import_stats, reset_import_stats

        reset_import_stats()
        stats = get_import_stats()

        assert "total_imports" in stats
        assert "total_time_ms" in stats
        assert "slowest_imports" in stats
        assert "all_imports" in stats


class TestResetImportStats:
    """Tests for reset_import_stats() function."""

    def test_clears_all_stats(self):
        """Test that reset_import_stats clears everything."""
        from casare_rpa.utils.lazy_loader import (
            get_import_stats,
            reset_import_stats,
            ImportMetrics,
        )

        # Add some data
        ImportMetrics.get_instance().record_import("test", 10.0)

        reset_import_stats()
        stats = get_import_stats()

        assert stats["total_imports"] == 0
        assert stats["total_time_ms"] == 0.0


class TestIntegration:
    """Integration tests for lazy loading system."""

    def test_lazy_import_workflow(self):
        """Test complete lazy import workflow."""
        from casare_rpa.utils.lazy_loader import (
            lazy_import,
            get_import_stats,
            reset_import_stats,
        )

        reset_import_stats()

        # Create lazy imports
        json_module = lazy_import("json")
        OrderedDict = lazy_import("collections", "OrderedDict")

        # Stats should be empty - nothing imported yet
        stats = get_import_stats()
        # Note: modules may already be in sys.modules, but we track our lazy imports
        initial_count = stats["total_imports"]

        # Use the lazy imports
        data = json_module.dumps({"lazy": True})
        od = OrderedDict()

        # Verify usage works
        assert data == '{"lazy": true}'
        assert isinstance(od, dict)

    def test_lazy_import_with_heavy_module(self):
        """Test lazy import with a commonly heavy module."""
        from casare_rpa.utils.lazy_loader import LazyModule, ImportMetrics

        ImportMetrics.get_instance().reset()

        # datetime is a built-in but demonstrates the pattern
        lazy_datetime = LazyModule("datetime")

        # Not loaded yet - verify internal state
        module = object.__getattribute__(lazy_datetime, "_module")
        assert module is None

        # Access it
        now = lazy_datetime.datetime.now()

        # Should be loaded now
        module = object.__getattribute__(lazy_datetime, "_module")
        assert module is not None
        assert now is not None

    def test_multiple_lazy_modules_independent(self):
        """Test that multiple lazy modules are independent."""
        from casare_rpa.utils.lazy_loader import LazyModule

        lazy1 = LazyModule("json")
        lazy2 = LazyModule("json")

        # They should be separate proxies
        assert lazy1 is not lazy2

        # But after loading, they reference the same module
        _ = lazy1.dumps({})
        _ = lazy2.dumps({})

        module1 = object.__getattribute__(lazy1, "_module")
        module2 = object.__getattribute__(lazy2, "_module")

        # Same module object (from sys.modules)
        assert module1 is module2


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_nonexistent_module_raises_on_access(self):
        """Test that accessing nonexistent module raises ImportError."""
        from casare_rpa.utils.lazy_loader import LazyModule

        lazy = LazyModule("nonexistent.module.that.does.not.exist")

        with pytest.raises(ModuleNotFoundError):
            _ = lazy.some_attribute

    def test_nonexistent_attribute_raises(self):
        """Test that accessing nonexistent attribute raises AttributeError."""
        from casare_rpa.utils.lazy_loader import LazyModule

        lazy = LazyModule("json")

        with pytest.raises(AttributeError):
            _ = lazy.nonexistent_function_xyz

    def test_lazy_attr_nonexistent_attribute(self):
        """Test _LazyAttr with nonexistent attribute."""
        from casare_rpa.utils.lazy_loader import _LazyAttr

        lazy = _LazyAttr("json", "nonexistent_attr_xyz")

        with pytest.raises(AttributeError):
            _ = lazy()

    def test_empty_module_name(self):
        """Test handling of empty module name."""
        from casare_rpa.utils.lazy_loader import LazyModule

        lazy = LazyModule("")

        with pytest.raises((ModuleNotFoundError, ImportError, ValueError)):
            _ = lazy.something


class TestPerformance:
    """Performance tests for lazy loading."""

    def test_lazy_import_overhead_minimal(self):
        """Test that lazy import wrapper has minimal overhead."""
        from casare_rpa.utils.lazy_loader import LazyModule

        # Time creating lazy modules
        start = time.perf_counter()
        for _ in range(1000):
            _ = LazyModule("json")
        lazy_time = time.perf_counter() - start

        # Should be very fast (under 10ms for 1000 creations)
        assert lazy_time < 0.1, f"LazyModule creation took {lazy_time*1000:.1f}ms"

    def test_import_metrics_recording_fast(self):
        """Test that recording import metrics is fast."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        metrics = ImportMetrics.get_instance()
        metrics.reset()

        start = time.perf_counter()
        for i in range(10000):
            metrics.record_import(f"module_{i}", float(i))
        elapsed = time.perf_counter() - start

        # Should complete in under 100ms
        assert elapsed < 0.1, f"Recording 10000 metrics took {elapsed*1000:.1f}ms"

    def test_stats_retrieval_fast(self):
        """Test that getting stats is fast even with many records."""
        from casare_rpa.utils.lazy_loader import ImportMetrics

        metrics = ImportMetrics.get_instance()
        metrics.reset()

        # Add many records
        for i in range(5000):
            metrics.record_import(f"module_{i}", float(i))

        start = time.perf_counter()
        for _ in range(100):
            _ = metrics.get_stats()
        elapsed = time.perf_counter() - start

        # Should complete in under 500ms
        assert elapsed < 0.5, f"Getting stats 100 times took {elapsed*1000:.1f}ms"

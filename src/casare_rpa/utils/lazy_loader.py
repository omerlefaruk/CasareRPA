"""
Lazy import system for deferred module loading.

Provides infrastructure for deferring heavy module imports until they're
actually needed, significantly reducing application startup time.

Features:
- LazyImport descriptor for class-level lazy imports
- LazyModule proxy for module-level lazy imports
- Import timing metrics for profiling
- Thread-safe implementation

Usage:
    # Class-level lazy import
    class MyClass:
        heavy_module = LazyImport("casare_rpa.nodes.browser_nodes")

        def use_browser(self):
            # Module only imported when accessed
            return self.heavy_module.NavigateNode()

    # Module-level lazy import
    from casare_rpa.utils.lazy_loader import lazy_import
    browser_nodes = lazy_import("casare_rpa.nodes.browser_nodes")
"""

import importlib
import threading
import time
from typing import Any, Callable, Dict, Optional


class ImportMetrics:
    """
    Track import timing metrics for performance analysis.

    Thread-safe singleton for collecting import statistics.
    """

    _instance: Optional["ImportMetrics"] = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._imports: Dict[str, float] = {}
        self._import_lock = threading.Lock()
        self._total_time: float = 0.0

    @classmethod
    def get_instance(cls) -> "ImportMetrics":
        """Get the singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def record_import(self, module_name: str, duration_ms: float) -> None:
        """Record an import timing."""
        with self._import_lock:
            self._imports[module_name] = duration_ms
            self._total_time += duration_ms

    def get_stats(self) -> Dict[str, Any]:
        """Get import statistics."""
        with self._import_lock:
            sorted_imports = sorted(
                self._imports.items(), key=lambda x: x[1], reverse=True
            )
            return {
                "total_imports": len(self._imports),
                "total_time_ms": self._total_time,
                "slowest_imports": dict(sorted_imports[:10]),
                "all_imports": dict(sorted_imports),
            }

    def reset(self) -> None:
        """Reset all metrics."""
        with self._import_lock:
            self._imports.clear()
            self._total_time = 0.0


class LazyModule:
    """
    Proxy object for lazy module loading.

    Acts like a module but only imports when an attribute is accessed.
    Thread-safe with double-checked locking.

    Example:
        browser_nodes = LazyModule("casare_rpa.nodes.browser_nodes")
        # Module not imported yet

        node = browser_nodes.NavigateNode()
        # Module imported on first access
    """

    __slots__ = ("_module_name", "_module", "_lock", "_import_callback")

    def __init__(
        self,
        module_name: str,
        import_callback: Optional[Callable[[str, float], None]] = None,
    ) -> None:
        """
        Initialize lazy module proxy.

        Args:
            module_name: Full dotted module path
            import_callback: Optional callback(module_name, duration_ms) on import
        """
        object.__setattr__(self, "_module_name", module_name)
        object.__setattr__(self, "_module", None)
        object.__setattr__(self, "_lock", threading.Lock())
        object.__setattr__(self, "_import_callback", import_callback)

    def _load_module(self) -> Any:
        """Load the actual module (thread-safe with double-check)."""
        module = object.__getattribute__(self, "_module")
        if module is not None:
            return module

        lock = object.__getattribute__(self, "_lock")
        with lock:
            # Double-check after acquiring lock
            module = object.__getattribute__(self, "_module")
            if module is not None:
                return module

            module_name = object.__getattribute__(self, "_module_name")

            start = time.perf_counter()
            module = importlib.import_module(module_name)
            duration_ms = (time.perf_counter() - start) * 1000

            object.__setattr__(self, "_module", module)

            # Record metrics
            ImportMetrics.get_instance().record_import(module_name, duration_ms)

            # Call callback if provided
            callback = object.__getattribute__(self, "_import_callback")
            if callback:
                callback(module_name, duration_ms)

            return module

    def __getattr__(self, name: str) -> Any:
        """Get attribute from loaded module."""
        module = self._load_module()
        return getattr(module, name)

    def __repr__(self) -> str:
        module_name = object.__getattribute__(self, "_module_name")
        module = object.__getattribute__(self, "_module")
        loaded = "loaded" if module is not None else "not loaded"
        return f"<LazyModule({module_name!r}) [{loaded}]>"


class LazyImport:
    """
    Descriptor for class-level lazy imports.

    Use as a class attribute to defer module loading until access.

    Example:
        class BrowserAutomation:
            playwright = LazyImport("playwright.async_api")

            async def navigate(self, url: str):
                # playwright module imported on first access
                browser = await self.playwright.async_playwright().start()
    """

    def __init__(
        self, module_name: str, attr: Optional[str] = None, log: bool = True
    ) -> None:
        """
        Initialize lazy import descriptor.

        Args:
            module_name: Full dotted module path
            attr: Optional attribute to extract from module (e.g., "Page")
            log: Whether to log import timing
        """
        self._module_name = module_name
        self._attr = attr
        self._log = log
        self._cache: Dict[int, Any] = {}
        self._lock = threading.Lock()

    def __get__(self, obj: Any, objtype: Any = None) -> Any:
        """Get the lazy-loaded module or attribute."""
        # Class-level access returns the descriptor itself
        if obj is None:
            return self

        # Instance-level access with caching
        obj_id = id(obj)

        # Fast path - check cache without lock
        if obj_id in self._cache:
            return self._cache[obj_id]

        with self._lock:
            # Double-check after lock
            if obj_id in self._cache:
                return self._cache[obj_id]

            # Import the module
            start = time.perf_counter()
            module = importlib.import_module(self._module_name)
            duration_ms = (time.perf_counter() - start) * 1000

            # Record metrics
            ImportMetrics.get_instance().record_import(self._module_name, duration_ms)

            if self._log:
                from loguru import logger

                logger.debug(
                    f"LazyImport: Loaded {self._module_name} in {duration_ms:.2f}ms"
                )

            # Extract specific attribute if requested
            result = getattr(module, self._attr) if self._attr else module

            self._cache[obj_id] = result
            return result


def lazy_import(module_name: str, attr: Optional[str] = None) -> Any:
    """
    Create a lazy module proxy.

    The module is only imported when an attribute is accessed.

    Args:
        module_name: Full dotted module path
        attr: Optional attribute to extract after import

    Returns:
        LazyModule proxy or actual attribute

    Example:
        # Lazy module
        browser_nodes = lazy_import("casare_rpa.nodes.browser_nodes")
        node = browser_nodes.NavigateNode()  # Import happens here

        # Lazy attribute
        NavigateNode = lazy_import("casare_rpa.nodes.browser_nodes", "NavigateNode")
        node = NavigateNode()  # Import happens here
    """
    if attr:
        # Return a wrapper that imports and extracts the attribute
        return _LazyAttr(module_name, attr)
    return LazyModule(module_name)


class _LazyAttr:
    """Internal class for lazy attribute import."""

    __slots__ = ("_module_name", "_attr", "_cached", "_lock")

    def __init__(self, module_name: str, attr: str) -> None:
        self._module_name = module_name
        self._attr = attr
        self._cached: Any = None
        self._lock = threading.Lock()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """If the attribute is callable, forward the call."""
        return self._get_attr()(*args, **kwargs)

    def _get_attr(self) -> Any:
        """Get the actual attribute, importing if needed."""
        if self._cached is not None:
            return self._cached

        with self._lock:
            if self._cached is not None:
                return self._cached

            start = time.perf_counter()
            module = importlib.import_module(self._module_name)
            duration_ms = (time.perf_counter() - start) * 1000

            ImportMetrics.get_instance().record_import(self._module_name, duration_ms)

            self._cached = getattr(module, self._attr)
            return self._cached

    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to the loaded attribute."""
        return getattr(self._get_attr(), name)


def get_import_stats() -> Dict[str, Any]:
    """
    Get lazy import statistics.

    Returns:
        Dict with total_imports, total_time_ms, slowest_imports, all_imports
    """
    return ImportMetrics.get_instance().get_stats()


def reset_import_stats() -> None:
    """Reset import statistics."""
    ImportMetrics.get_instance().reset()


__all__ = [
    "LazyModule",
    "LazyImport",
    "lazy_import",
    "get_import_stats",
    "reset_import_stats",
    "ImportMetrics",
]

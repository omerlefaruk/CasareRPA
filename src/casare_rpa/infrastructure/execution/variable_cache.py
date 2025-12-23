"""
Variable Resolution Cache for CasareRPA.

Provides caching for {{variable}} pattern resolutions to avoid
repeated regex parsing and value lookups during workflow execution.

Thread-safe implementation with automatic invalidation on variable changes.
"""

import re
import threading
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

# Pattern to extract variable names from templates (matches domain pattern)
VARIABLE_PATTERN = re.compile(
    r"\{\{\s*(\$?[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[\d+\])*)\s*\}\}"
)


@dataclass
class CacheEntry:
    """Represents a cached resolution result."""

    result: Any
    var_refs: list[str]  # Variable names referenced by this template
    var_versions: dict[str, int]  # Version snapshot when cached


@dataclass
class CacheStats:
    """Statistics for cache performance monitoring."""

    hits: int = 0
    misses: int = 0
    invalidations: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for reporting."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "evictions": self.evictions,
            "hit_rate": self.hit_rate,
        }


class VariableResolutionCache:
    """
    Cache for {{variable}} pattern resolutions.

    This cache stores:
    1. Parsed variable references for each template (pattern_cache)
    2. Resolved results with version tracking (result_cache)

    Cache invalidation occurs automatically when:
    - A referenced variable value changes (version mismatch)
    - Cache size exceeds max_size (LRU eviction)
    - clear() is explicitly called

    Thread-safe: All operations use a reentrant lock.

    Performance characteristics:
    - O(1) pattern lookup for previously seen templates
    - O(n) version check where n = number of referenced variables
    - LRU eviction keeps frequently used templates cached
    """

    def __init__(self, max_size: int = 500) -> None:
        """
        Initialize the cache.

        Args:
            max_size: Maximum number of cached results (default: 500)
        """
        self._max_size = max_size
        self._lock = threading.RLock()

        # Pattern cache: template string -> list of variable names
        # This never expires as patterns are deterministic
        self._pattern_cache: dict[str, list[str]] = {}

        # Result cache: template string -> CacheEntry
        # Uses OrderedDict for LRU eviction
        self._result_cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Variable versions: var_name -> version (increments on change)
        self._var_versions: dict[str, int] = {}

        # Statistics
        self._stats = CacheStats()

    def extract_variable_refs(self, template: str) -> list[str]:
        """
        Extract and cache variable references from a template.

        Args:
            template: String potentially containing {{variable}} patterns

        Returns:
            List of variable names found in the template
        """
        with self._lock:
            if template in self._pattern_cache:
                return self._pattern_cache[template]

            refs = VARIABLE_PATTERN.findall(template)
            self._pattern_cache[template] = refs
            return refs

    def get_cached(
        self,
        template: str,
        variables: dict[str, Any],
    ) -> tuple[bool, Any]:
        """
        Get cached resolution result if valid.

        Args:
            template: Template string to resolve
            variables: Current variable values (for version comparison)

        Returns:
            Tuple of (found, result):
            - found: True if valid cache entry exists
            - result: Cached result (None if not found)
        """
        with self._lock:
            if template not in self._result_cache:
                self._stats.misses += 1
                return False, None

            entry = self._result_cache[template]

            # Check if any referenced variable or its parents have changed
            for var_name in entry.var_refs:
                # Check version of the full path
                cached_version = entry.var_versions.get(var_name, 0)
                current_version = self._var_versions.get(var_name, 0)

                if cached_version != current_version:
                    invalidate = True
                else:
                    # Check versions of all parent prefixes (e.g. for 'a.b.c', check 'a' and 'a.b')
                    invalidate = False
                    if "." in var_name:
                        parts = var_name.split(".")
                        prefix = ""
                        for r in range(len(parts) - 1):
                            prefix = (prefix + "." + parts[r]) if prefix else parts[r]
                            if self._var_versions.get(prefix, 0) != entry.var_versions.get(
                                prefix, 0
                            ):
                                invalidate = True
                                break

                if invalidate:
                    # Version mismatch - invalidate this entry
                    del self._result_cache[template]
                    self._stats.invalidations += 1
                    self._stats.misses += 1
                    return False, None

            # Cache hit - move to end for LRU
            self._result_cache.move_to_end(template)
            self._stats.hits += 1
            return True, entry.result

    def cache_result(
        self,
        template: str,
        variables: dict[str, Any],
        result: Any,
    ) -> None:
        """
        Cache a resolution result.

        Args:
            template: Template string that was resolved
            variables: Variable values used for resolution
            result: Resolution result to cache
        """
        with self._lock:
            # Get or compute variable references
            var_refs = self.extract_variable_refs(template)

            # Capture current versions of referenced variables
            var_versions = {var_name: self._var_versions.get(var_name, 0) for var_name in var_refs}

            # Create cache entry
            entry = CacheEntry(
                result=result,
                var_refs=var_refs,
                var_versions=var_versions,
            )

            # Evict if at capacity
            while len(self._result_cache) >= self._max_size:
                self._result_cache.popitem(last=False)  # Remove oldest
                self._stats.evictions += 1

            self._result_cache[template] = entry

    def notify_variable_changed(self, var_name: str) -> None:
        """
        Notify the cache that a variable value has changed.

        Increments the version for the variable, which will cause
        cache entries referencing it to be invalidated on next access.

        Args:
            var_name: Name of the variable that changed
        """
        with self._lock:
            self._var_versions[var_name] = self._var_versions.get(var_name, 0) + 1

    def notify_variables_changed(self, var_names: set[str]) -> None:
        """
        Notify the cache that multiple variables have changed.

        Args:
            var_names: Set of variable names that changed
        """
        with self._lock:
            for var_name in var_names:
                self._var_versions[var_name] = self._var_versions.get(var_name, 0) + 1

    def clear(self) -> None:
        """Clear all cached results."""
        with self._lock:
            self._result_cache.clear()
            # Keep pattern cache - patterns never change
            # Reset versions
            self._var_versions.clear()

    def clear_all(self) -> None:
        """Clear all caches including patterns."""
        with self._lock:
            self._result_cache.clear()
            self._pattern_cache.clear()
            self._var_versions.clear()

    def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        with self._lock:
            return CacheStats(
                hits=self._stats.hits,
                misses=self._stats.misses,
                invalidations=self._stats.invalidations,
                evictions=self._stats.evictions,
            )

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        with self._lock:
            self._stats = CacheStats()

    @property
    def size(self) -> int:
        """Current number of cached results."""
        with self._lock:
            return len(self._result_cache)

    @property
    def pattern_cache_size(self) -> int:
        """Current number of cached patterns."""
        with self._lock:
            return len(self._pattern_cache)


class CachedVariableResolver:
    """
    Variable resolver with integrated caching.

    Wraps the domain variable resolver with caching for improved performance.
    Use this in high-frequency resolution scenarios (e.g., large loops).
    """

    def __init__(
        self,
        variables: dict[str, Any],
        cache: VariableResolutionCache | None = None,
    ) -> None:
        """
        Initialize resolver with cache.

        Args:
            variables: Variable dictionary to resolve against
            cache: Optional cache instance (creates new if not provided)
        """
        self._variables = variables
        self._cache = cache or VariableResolutionCache()

    def resolve(self, value: Any) -> Any:
        """
        Resolve {{variable}} patterns in a value.

        Args:
            value: Value to resolve (only strings are processed)

        Returns:
            Resolved value
        """
        if not isinstance(value, str) or "{{" not in value:
            return value

        # Check cache first
        found, result = self._cache.get_cached(value, self._variables)
        if found:
            return result

        # Resolve using domain resolver
        from casare_rpa.domain.services.variable_resolver import resolve_variables

        result = resolve_variables(value, self._variables)

        # Cache the result
        self._cache.cache_result(value, self._variables, result)

        return result

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set a variable and notify cache of the change.

        Args:
            name: Variable name
            value: Variable value
        """
        self._variables[name] = value
        self._cache.notify_variable_changed(name)

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._cache.get_stats()

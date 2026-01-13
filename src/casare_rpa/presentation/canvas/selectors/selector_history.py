"""
Selector History Storage.

Persists recently used selectors to JSON for quick reuse.
Supports per-project history and global recent selectors.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

# Maximum history entries
MAX_HISTORY_ENTRIES = 50
MAX_RECENT_ENTRIES = 20


@dataclass
class SelectorHistoryEntry:
    """
    Single entry in selector history.

    Attributes:
        selector: The selector string
        selector_type: Type (css, xpath, etc.)
        element_tag: HTML tag of target element
        element_id: ID attribute if present
        timestamp: ISO timestamp when used
        project_id: Optional project identifier
        use_count: Number of times used
        success_rate: Historical success rate 0.0-1.0
    """

    selector: str
    selector_type: str = "css"
    element_tag: str = ""
    element_id: str = ""
    timestamp: str = ""
    project_id: str = ""
    use_count: int = 1
    success_rate: float = 1.0
    healing_context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SelectorHistoryEntry:
        """Create from dictionary."""
        return cls(
            selector=data.get("selector", ""),
            selector_type=data.get("selector_type", "css"),
            element_tag=data.get("element_tag", ""),
            element_id=data.get("element_id", ""),
            timestamp=data.get("timestamp", ""),
            project_id=data.get("project_id", ""),
            use_count=data.get("use_count", 1),
            success_rate=data.get("success_rate", 1.0),
            healing_context=data.get("healing_context", {}))


class SelectorHistory:
    """
    Manages selector history persistence.

    Features:
    - JSON-based storage
    - Per-project history
    - Global recent list
    - Use count tracking
    - Success rate tracking

    Usage:
        history = SelectorHistory()
        history.add_selector("#submit", "css", element_tag="button")
        recent = history.get_recent(limit=10)
    """

    def __init__(
        self,
        storage_path: Path | None = None,
        max_entries: int = MAX_HISTORY_ENTRIES) -> None:
        """
        Initialize selector history.

        Args:
            storage_path: Path to JSON storage file. Defaults to config dir.
            max_entries: Maximum entries to keep.
        """
        if storage_path is None:
            # Default to config/selector_history.json
            storage_path = Path("config") / "selector_history.json"

        self._storage_path = storage_path
        self._max_entries = max_entries
        self._entries: list[SelectorHistoryEntry] = []
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """Ensure history is loaded from disk."""
        if self._loaded:
            return

        self._loaded = True

        if not self._storage_path.exists():
            logger.debug(f"Selector history file not found: {self._storage_path}")
            return

        try:
            with open(self._storage_path, encoding="utf-8") as f:
                data = json.load(f)

            entries_data = data.get("entries", [])
            self._entries = [SelectorHistoryEntry.from_dict(e) for e in entries_data]
            logger.debug(f"Loaded {len(self._entries)} selector history entries")

        except Exception as e:
            logger.warning(f"Failed to load selector history: {e}")
            self._entries = []

    def _save(self) -> None:
        """Save history to disk."""
        try:
            # Ensure parent directory exists
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": 1,
                "updated": datetime.now().isoformat(),
                "entries": [e.to_dict() for e in self._entries],
            }

            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self._entries)} selector history entries")

        except Exception as e:
            logger.warning(f"Failed to save selector history: {e}")

    def add_selector(
        self,
        selector: str,
        selector_type: str = "css",
        element_tag: str = "",
        element_id: str = "",
        project_id: str = "",
        healing_context: dict[str, Any] | None = None) -> None:
        """
        Add or update a selector in history.

        Args:
            selector: The selector string
            selector_type: Type (css, xpath, etc.)
            element_tag: HTML tag of element
            element_id: ID attribute
            project_id: Optional project identifier
            healing_context: Optional healing context data
        """
        self._ensure_loaded()

        if not selector.strip():
            return

        # Check if selector already exists
        existing = None
        for i, entry in enumerate(self._entries):
            if entry.selector == selector and entry.selector_type == selector_type:
                existing = (i, entry)
                break

        if existing:
            i, entry = existing
            # Update existing entry
            entry.use_count += 1
            entry.timestamp = datetime.now().isoformat()
            if healing_context:
                entry.healing_context = healing_context
            # Move to front
            self._entries.pop(i)
            self._entries.insert(0, entry)
        else:
            # Create new entry
            entry = SelectorHistoryEntry(
                selector=selector,
                selector_type=selector_type,
                element_tag=element_tag,
                element_id=element_id,
                project_id=project_id,
                healing_context=healing_context or {})
            self._entries.insert(0, entry)

        # Trim to max entries
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[: self._max_entries]

        self._save()

    def get_recent(
        self,
        limit: int = MAX_RECENT_ENTRIES,
        project_id: str | None = None,
        selector_type: str | None = None) -> list[SelectorHistoryEntry]:
        """
        Get recent selectors.

        Args:
            limit: Maximum entries to return
            project_id: Filter by project
            selector_type: Filter by type

        Returns:
            List of recent selector entries
        """
        self._ensure_loaded()

        entries = self._entries

        if project_id:
            entries = [e for e in entries if e.project_id == project_id or not e.project_id]

        if selector_type:
            entries = [e for e in entries if e.selector_type == selector_type]

        return entries[:limit]

    def get_selectors(
        self,
        limit: int = MAX_RECENT_ENTRIES,
        project_id: str | None = None) -> list[str]:
        """
        Get recent selector strings only.

        Args:
            limit: Maximum entries
            project_id: Filter by project

        Returns:
            List of selector strings
        """
        entries = self.get_recent(limit=limit, project_id=project_id)
        return [e.selector for e in entries]

    def record_success(self, selector: str, selector_type: str = "css") -> None:
        """
        Record successful use of a selector.

        Updates success rate for the entry.

        Args:
            selector: The selector string
            selector_type: Type of selector
        """
        self._ensure_loaded()

        for entry in self._entries:
            if entry.selector == selector and entry.selector_type == selector_type:
                # Moving average of success rate
                entry.success_rate = (entry.success_rate * entry.use_count + 1.0) / (
                    entry.use_count + 1
                )
                entry.use_count += 1
                self._save()
                return

    def record_failure(self, selector: str, selector_type: str = "css") -> None:
        """
        Record failed use of a selector.

        Updates success rate for the entry.

        Args:
            selector: The selector string
            selector_type: Type of selector
        """
        self._ensure_loaded()

        for entry in self._entries:
            if entry.selector == selector and entry.selector_type == selector_type:
                # Moving average of success rate
                entry.success_rate = (entry.success_rate * entry.use_count + 0.0) / (
                    entry.use_count + 1
                )
                entry.use_count += 1
                self._save()
                return

    def remove_selector(self, selector: str, selector_type: str = "css") -> bool:
        """
        Remove a selector from history.

        Args:
            selector: The selector string
            selector_type: Type of selector

        Returns:
            True if removed, False if not found
        """
        self._ensure_loaded()

        for i, entry in enumerate(self._entries):
            if entry.selector == selector and entry.selector_type == selector_type:
                self._entries.pop(i)
                self._save()
                return True

        return False

    def clear(self, project_id: str | None = None) -> int:
        """
        Clear history.

        Args:
            project_id: If provided, only clear entries for this project

        Returns:
            Number of entries removed
        """
        self._ensure_loaded()

        if project_id:
            original_count = len(self._entries)
            self._entries = [e for e in self._entries if e.project_id != project_id]
            removed = original_count - len(self._entries)
        else:
            removed = len(self._entries)
            self._entries = []

        if removed > 0:
            self._save()

        return removed

    def search(
        self,
        query: str,
        limit: int = 10) -> list[SelectorHistoryEntry]:
        """
        Search history for matching selectors.

        Args:
            query: Search query (substring match)
            limit: Maximum results

        Returns:
            Matching entries
        """
        self._ensure_loaded()

        query = query.lower()
        results = []

        for entry in self._entries:
            if (
                query in entry.selector.lower()
                or query in entry.element_tag.lower()
                or query in entry.element_id.lower()
            ):
                results.append(entry)
                if len(results) >= limit:
                    break

        return results


# Global singleton instance
_history_instance: SelectorHistory | None = None


def get_selector_history() -> SelectorHistory:
    """
    Get the global selector history instance.

    Returns:
        SelectorHistory singleton instance
    """
    global _history_instance
    if _history_instance is None:
        _history_instance = SelectorHistory()
    return _history_instance


__all__ = [
    "SelectorHistory",
    "SelectorHistoryEntry",
    "get_selector_history",
]

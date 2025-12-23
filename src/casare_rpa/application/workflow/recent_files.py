"""
Recent Files Manager for CasareRPA.

Manages a list of recently opened workflow files for quick access.
"""

from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime

from loguru import logger

from casare_rpa.config import CONFIG_DIR


class RecentFilesManager:
    """
    Manages recent files list with persistence.

    Features:
    - Stores up to N recent files
    - Persists across sessions
    - Removes non-existent files
    - Tracks last opened time
    """

    MAX_RECENT_FILES = 10
    RECENT_FILES_PATH = CONFIG_DIR / "recent_files.json"

    def __init__(self) -> None:
        """Initialize the recent files manager."""
        self._recent_files: List[dict] = []
        self._load()

    def _load(self) -> None:
        """Load recent files from disk."""
        try:
            if self.RECENT_FILES_PATH.exists():
                with open(self.RECENT_FILES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._recent_files = data.get("files", [])

                # Remove non-existent files
                self._recent_files = [f for f in self._recent_files if Path(f["path"]).exists()]

                logger.debug(f"Loaded {len(self._recent_files)} recent files")
        except Exception as e:
            logger.warning(f"Could not load recent files: {e}")
            self._recent_files = []

    def _save(self) -> None:
        """Save recent files to disk."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.RECENT_FILES_PATH, "w", encoding="utf-8") as f:
                json.dump({"files": self._recent_files}, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save recent files: {e}")

    def add_file(self, file_path: Path) -> None:
        """
        Add a file to the recent files list.

        Args:
            file_path: Path to the workflow file
        """
        path_str = str(file_path.absolute())

        # Remove if already exists
        self._recent_files = [f for f in self._recent_files if f["path"] != path_str]

        # Add to front
        self._recent_files.insert(
            0,
            {
                "path": path_str,
                "name": file_path.name,
                "last_opened": datetime.now().isoformat(),
            },
        )

        # Trim to max
        self._recent_files = self._recent_files[: self.MAX_RECENT_FILES]

        self._save()
        logger.debug(f"Added to recent files: {file_path.name}")

    def get_recent_files(self) -> List[dict]:
        """
        Get the list of recent files.

        Returns:
            List of dicts with 'path', 'name', 'last_opened' keys
        """
        # Filter out non-existent files
        valid_files = [f for f in self._recent_files if Path(f["path"]).exists()]

        if len(valid_files) != len(self._recent_files):
            self._recent_files = valid_files
            self._save()

        return self._recent_files

    def clear(self) -> None:
        """Clear the recent files list."""
        self._recent_files = []
        self._save()

    def remove_file(self, file_path: Path) -> None:
        """
        Remove a specific file from the recent list.

        Args:
            file_path: Path to remove
        """
        path_str = str(file_path.absolute())
        self._recent_files = [f for f in self._recent_files if f["path"] != path_str]
        self._save()


# Module-level singleton with thread-safe lazy initialization
import threading

_recent_files_manager: Optional[RecentFilesManager] = None
_manager_lock = threading.Lock()


def _get_manager_singleton() -> RecentFilesManager:
    """Get or create the manager singleton with double-checked locking."""
    _local_instance = _recent_files_manager
    if _local_instance is None:
        with _manager_lock:
            _local_instance = _recent_files_manager
            if _local_instance is None:
                _local_instance = RecentFilesManager()
                globals()["_recent_files_manager"] = _local_instance
    return _local_instance


def get_recent_files_manager() -> RecentFilesManager:
    """Get the recent files manager instance."""
    return _get_manager_singleton()


def reset_recent_files_manager() -> None:
    """
    Reset the recent files manager singleton (for testing).

    Clears the singleton so it will be recreated on next access.
    """
    with _manager_lock:
        globals()["_recent_files_manager"] = None

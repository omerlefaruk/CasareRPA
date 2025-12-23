"""
Update Manager for CasareRPA Desktop Application.

Provides high-level update management:
- Background update checking
- User notification
- Download with progress
- Atomic update application
"""

import asyncio
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from casare_rpa.infrastructure.updater.tuf_updater import (
    TUFUpdater,
    UpdateInfo,
    DownloadProgress,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# Default TUF repository URL (Supabase Storage)
DEFAULT_REPO_URL = os.getenv(
    "CASARE_UPDATE_REPO_URL",
    "https://your-project.supabase.co/storage/v1/object/public/updates",
)

# Check interval (default: every 4 hours)
UPDATE_CHECK_INTERVAL_HOURS = int(os.getenv("CASARE_UPDATE_CHECK_INTERVAL", "4"))

# Local cache directory
DEFAULT_CACHE_DIR = Path.home() / ".casare_rpa" / "updates"


# =============================================================================
# ENUMS
# =============================================================================


class UpdateState(str, Enum):
    """Current state of the update manager."""

    IDLE = "idle"
    CHECKING = "checking"
    UPDATE_AVAILABLE = "update_available"
    DOWNLOADING = "downloading"
    READY_TO_INSTALL = "ready_to_install"
    INSTALLING = "installing"
    ERROR = "error"


# =============================================================================
# UPDATE MANAGER
# =============================================================================


class UpdateManager:
    """
    High-level update manager for desktop application.

    Usage:
        manager = UpdateManager(current_version="3.0.0")
        await manager.start()

        # Check manually
        update = await manager.check_for_updates()
        if update:
            await manager.download_update()
            await manager.apply_update()
    """

    def __init__(
        self,
        current_version: str,
        repo_url: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        auto_check: bool = True,
        on_update_available: Optional[Callable[[UpdateInfo], None]] = None,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        on_state_change: Optional[Callable[[UpdateState], None]] = None,
    ):
        """
        Initialize the update manager.

        Args:
            current_version: Currently installed version
            repo_url: TUF repository URL (default from env)
            cache_dir: Local cache directory (default: ~/.casare_rpa/updates)
            auto_check: Whether to automatically check for updates
            on_update_available: Callback when update is available
            on_progress: Callback for download progress
            on_state_change: Callback for state changes
        """
        self._current_version = current_version
        self._repo_url = repo_url or DEFAULT_REPO_URL
        self._cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self._auto_check = auto_check

        # Callbacks
        self._on_update_available = on_update_available
        self._on_progress = on_progress
        self._on_state_change = on_state_change

        # State
        self._state = UpdateState.IDLE
        self._update_info: Optional[UpdateInfo] = None
        self._downloaded_path: Optional[Path] = None
        self._last_check: Optional[datetime] = None
        self._check_task: Optional[asyncio.Task] = None

        # TUF updater
        self._updater = TUFUpdater(
            repo_url=self._repo_url,
            local_cache_dir=self._cache_dir,
            current_version=current_version,
        )

        logger.info(
            f"UpdateManager initialized: version={current_version} " f"repo={self._repo_url}"
        )

    @property
    def state(self) -> UpdateState:
        """Get current update state."""
        return self._state

    @property
    def update_info(self) -> Optional[UpdateInfo]:
        """Get available update info."""
        return self._update_info

    @property
    def is_update_available(self) -> bool:
        """Check if update is available."""
        return self._state == UpdateState.UPDATE_AVAILABLE or self._update_info is not None

    @property
    def is_ready_to_install(self) -> bool:
        """Check if update is downloaded and ready."""
        return self._state == UpdateState.READY_TO_INSTALL

    def _set_state(self, state: UpdateState) -> None:
        """Set state and notify callback."""
        if self._state != state:
            old_state = self._state
            self._state = state
            logger.debug(f"Update state: {old_state.value} -> {state.value}")
            if self._on_state_change:
                try:
                    self._on_state_change(state)
                except Exception as e:
                    logger.error(f"State change callback error: {e}")

    async def start(self) -> None:
        """
        Start the update manager.

        Begins background update checking if auto_check is enabled.
        """
        if self._auto_check:
            self._check_task = asyncio.create_task(self._background_check_loop())
            logger.info("Update manager started with background checking")

    async def stop(self) -> None:
        """Stop the update manager."""
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
            self._check_task = None
            logger.info("Update manager stopped")

    async def _background_check_loop(self) -> None:
        """Background loop for periodic update checks."""
        while True:
            try:
                # Wait before first check (give app time to start)
                await asyncio.sleep(60)  # 1 minute delay

                # Check for updates
                await self.check_for_updates()

                # Wait for next check interval
                await asyncio.sleep(UPDATE_CHECK_INTERVAL_HOURS * 3600)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background update check failed: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour on error

    async def check_for_updates(self) -> Optional[UpdateInfo]:
        """
        Check for available updates.

        Returns:
            UpdateInfo if update available, None otherwise
        """
        if self._state == UpdateState.DOWNLOADING:
            logger.warning("Cannot check for updates while downloading")
            return None

        self._set_state(UpdateState.CHECKING)
        self._last_check = datetime.now(timezone.utc)

        try:
            update = await self._updater.check_for_updates()

            if update:
                self._update_info = update
                self._set_state(UpdateState.UPDATE_AVAILABLE)

                logger.info(
                    f"Update available: {update.version} " f"(current: {self._current_version})"
                )

                # Notify callback
                if self._on_update_available:
                    try:
                        self._on_update_available(update)
                    except Exception as e:
                        logger.error(f"Update available callback error: {e}")

                return update
            else:
                self._set_state(UpdateState.IDLE)
                return None

        except Exception as e:
            logger.error(f"Update check failed: {e}")
            self._set_state(UpdateState.ERROR)
            return None

    async def download_update(self) -> Optional[Path]:
        """
        Download the available update.

        Returns:
            Path to downloaded file, or None if failed
        """
        if not self._update_info:
            logger.error("No update available to download")
            return None

        if self._state == UpdateState.DOWNLOADING:
            logger.warning("Download already in progress")
            return None

        self._set_state(UpdateState.DOWNLOADING)

        try:
            path = await self._updater.download_update(
                self._update_info,
                progress_callback=self._on_progress,
            )

            self._downloaded_path = path
            self._set_state(UpdateState.READY_TO_INSTALL)

            logger.info(f"Update downloaded: {path}")
            return path

        except Exception as e:
            logger.error(f"Update download failed: {e}")
            self._set_state(UpdateState.ERROR)
            return None

    async def apply_update(self, restart: bool = True) -> bool:
        """
        Apply the downloaded update.

        Args:
            restart: Whether to restart the application

        Returns:
            True if update applied successfully
        """
        if not self._downloaded_path:
            logger.error("No update downloaded to apply")
            return False

        if not self._downloaded_path.exists():
            logger.error(f"Downloaded file not found: {self._downloaded_path}")
            return False

        self._set_state(UpdateState.INSTALLING)

        try:
            success = await self._updater.apply_update(
                self._downloaded_path,
                restart_app=restart,
            )

            if success:
                logger.info("Update applied successfully")
            else:
                self._set_state(UpdateState.ERROR)

            return success

        except Exception as e:
            logger.error(f"Update application failed: {e}")
            self._set_state(UpdateState.ERROR)
            return False

    def skip_version(self, version: str) -> None:
        """
        Mark a version to be skipped.

        Args:
            version: Version to skip
        """
        skip_file = self._cache_dir / "skipped_versions.txt"
        skip_file.parent.mkdir(parents=True, exist_ok=True)

        with open(skip_file, "a") as f:
            f.write(f"{version}\n")

        logger.info(f"Skipped version: {version}")

        # Clear current update if it matches
        if self._update_info and self._update_info.version == version:
            self._update_info = None
            self._set_state(UpdateState.IDLE)

    def is_version_skipped(self, version: str) -> bool:
        """Check if a version is marked as skipped."""
        skip_file = self._cache_dir / "skipped_versions.txt"
        if not skip_file.exists():
            return False

        with open(skip_file) as f:
            skipped = [line.strip() for line in f.readlines()]

        return version in skipped

    def clear_skipped_versions(self) -> None:
        """Clear all skipped versions."""
        skip_file = self._cache_dir / "skipped_versions.txt"
        if skip_file.exists():
            skip_file.unlink()
            logger.info("Cleared skipped versions")

    def cleanup(self) -> int:
        """
        Clean up old downloaded files.

        Returns:
            Number of files cleaned up
        """
        return self._updater.cleanup_old_versions()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Module-level singleton with thread-safe lazy initialization
import threading

_update_manager_instance: Optional[UpdateManager] = None
_update_manager_lock = threading.Lock()
_update_manager_version: Optional[str] = None


def get_update_manager(
    current_version: Optional[str] = None,
    **kwargs,
) -> UpdateManager:
    """
    Get or create the update manager instance.

    Thread-safe singleton accessor.

    Args:
        current_version: Current app version (required on first call)
        **kwargs: Additional arguments for UpdateManager

    Returns:
        UpdateManager instance
    """
    _local_instance = _update_manager_instance
    if _local_instance is not None:
        return _local_instance

    with _update_manager_lock:
        _local_instance = _update_manager_instance
        if _local_instance is None:
            if current_version is None:
                raise ValueError("current_version required on first call")
            _local_instance = UpdateManager(current_version, **kwargs)
            globals()["_update_manager_instance"] = _local_instance
            globals()["_update_manager_version"] = current_version

    return _local_instance


def reset_update_manager() -> None:
    """
    Reset the update manager singleton (for testing).

    Clears the singleton so it will be recreated on next access.
    """
    with _update_manager_lock:
        globals()["_update_manager_instance"] = None
        globals()["_update_manager_version"] = None

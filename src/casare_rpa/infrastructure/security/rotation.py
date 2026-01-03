"""
CasareRPA - Secret Rotation Manager.

Handles automatic and scheduled secret rotation with:
- Configurable rotation policies
- Pre-rotation hooks for validation
- Post-rotation hooks for propagation
- Rotation history tracking
- Failure handling and rollback
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from loguru import logger

from casare_rpa.infrastructure.security.vault_client import (
    VaultClient,
    VaultError,
)


class RotationFrequency(str, Enum):
    """Predefined rotation frequencies."""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RotationStatus(str, Enum):
    """Status of a rotation operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class RotationPolicy:
    """Defines rotation schedule and behavior for a secret."""

    path: str
    frequency: RotationFrequency
    custom_interval_hours: int | None = None  # For CUSTOM frequency
    enabled: bool = True
    last_rotated: datetime | None = None
    next_rotation: datetime | None = None
    notify_on_failure: bool = True
    max_retry_attempts: int = 3
    pre_rotation_hook: str | None = None  # Callback identifier
    post_rotation_hook: str | None = None  # Callback identifier

    def get_interval(self) -> timedelta:
        """Get rotation interval as timedelta."""
        intervals = {
            RotationFrequency.HOURLY: timedelta(hours=1),
            RotationFrequency.DAILY: timedelta(days=1),
            RotationFrequency.WEEKLY: timedelta(weeks=1),
            RotationFrequency.MONTHLY: timedelta(days=30),
            RotationFrequency.QUARTERLY: timedelta(days=90),
            RotationFrequency.YEARLY: timedelta(days=365),
        }

        if self.frequency == RotationFrequency.CUSTOM:
            hours = self.custom_interval_hours or 24
            return timedelta(hours=hours)

        return intervals.get(self.frequency, timedelta(days=1))

    def calculate_next_rotation(self) -> datetime:
        """Calculate the next rotation time."""
        base = self.last_rotated or datetime.now(UTC)
        return base + self.get_interval()


@dataclass
class RotationRecord:
    """Record of a rotation operation."""

    path: str
    started_at: datetime
    completed_at: datetime | None = None
    status: RotationStatus = RotationStatus.PENDING
    old_version: int | None = None
    new_version: int | None = None
    error_message: str | None = None
    attempt_number: int = 1


class RotationHook(ABC):
    """Abstract base class for rotation hooks."""

    @abstractmethod
    async def execute(
        self,
        path: str,
        old_data: dict[str, Any] | None,
        new_data: dict[str, Any] | None,
    ) -> bool:
        """
        Execute the hook.

        Args:
            path: Secret path being rotated
            old_data: Old secret data (for post-rotation)
            new_data: New secret data (for pre-rotation validation)

        Returns:
            True if hook succeeded, False to abort rotation
        """
        pass


class LoggingRotationHook(RotationHook):
    """Simple hook that logs rotation events."""

    async def execute(
        self,
        path: str,
        old_data: dict[str, Any] | None,
        new_data: dict[str, Any] | None,
    ) -> bool:
        """Log the rotation event."""
        if old_data and new_data:
            logger.info(f"Secret rotated: {path}")
        elif new_data:
            logger.info(f"Pre-rotation validation for: {path}")
        else:
            logger.info(f"Post-rotation cleanup for: {path}")
        return True


class SecretRotationManager:
    """
    Manages secret rotation lifecycle.

    Features:
    - Automatic scheduled rotation
    - Manual rotation triggers
    - Pre/post rotation hooks
    - Failure handling with retry
    - Rotation history tracking
    """

    def __init__(
        self,
        vault_client: VaultClient,
        check_interval_seconds: int = 60,
    ) -> None:
        """
        Initialize rotation manager.

        Args:
            vault_client: Connected vault client
            check_interval_seconds: How often to check for due rotations
        """
        self._client = vault_client
        self._check_interval = check_interval_seconds
        self._policies: dict[str, RotationPolicy] = {}
        self._hooks: dict[str, RotationHook] = {}
        self._history: list[RotationRecord] = []
        self._max_history = 1000
        self._running = False
        self._scheduler_task: asyncio.Task | None = None

        # Register default hooks
        self.register_hook("logging", LoggingRotationHook())

    def register_policy(self, policy: RotationPolicy) -> None:
        """
        Register a rotation policy for a secret.

        Args:
            policy: Rotation policy to register
        """
        if policy.next_rotation is None:
            policy.next_rotation = policy.calculate_next_rotation()

        self._policies[policy.path] = policy
        logger.info(
            f"Registered rotation policy for {policy.path} (frequency: {policy.frequency.value})"
        )

    def unregister_policy(self, path: str) -> bool:
        """
        Unregister a rotation policy.

        Args:
            path: Secret path

        Returns:
            True if policy was removed
        """
        if path in self._policies:
            del self._policies[path]
            logger.info(f"Unregistered rotation policy for {path}")
            return True
        return False

    def register_hook(self, name: str, hook: RotationHook) -> None:
        """
        Register a rotation hook.

        Args:
            name: Hook identifier
            hook: Hook implementation
        """
        self._hooks[name] = hook
        logger.debug(f"Registered rotation hook: {name}")

    async def start(self) -> None:
        """Start the rotation scheduler."""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Secret rotation scheduler started")

    async def stop(self) -> None:
        """Stop the rotation scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Secret rotation scheduler stopped")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_rotate()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rotation scheduler error: {e}")
                await asyncio.sleep(self._check_interval)

    async def _check_and_rotate(self) -> None:
        """Check for due rotations and execute them."""
        now = datetime.now(UTC)
        due_rotations: list[RotationPolicy] = []

        for policy in self._policies.values():
            if not policy.enabled:
                continue
            if policy.next_rotation and policy.next_rotation <= now:
                due_rotations.append(policy)

        for policy in due_rotations:
            await self.rotate_secret(policy.path)

    async def rotate_secret(
        self,
        path: str,
        force: bool = False,
    ) -> RotationRecord:
        """
        Rotate a secret.

        Args:
            path: Secret path to rotate
            force: If True, rotate even if not due

        Returns:
            RotationRecord with operation details
        """
        policy = self._policies.get(path)
        if not policy and not force:
            raise VaultError(f"No rotation policy for: {path}", path=path)

        record = RotationRecord(
            path=path,
            started_at=datetime.now(UTC),
            status=RotationStatus.IN_PROGRESS,
        )

        try:
            # Get current secret for version tracking
            try:
                current = await self._client.get_secret(path)
                record.old_version = current.metadata.version
            except Exception:
                record.old_version = 0

            # Execute pre-rotation hook
            if policy and policy.pre_rotation_hook:
                hook = self._hooks.get(policy.pre_rotation_hook)
                if hook:
                    success = await hook.execute(path, None, None)
                    if not success:
                        raise VaultError(
                            f"Pre-rotation hook failed for: {path}",
                            path=path,
                        )

            # Perform rotation
            new_metadata = await self._client.rotate_secret(path)
            record.new_version = new_metadata.version

            # Execute post-rotation hook
            if policy and policy.post_rotation_hook:
                hook = self._hooks.get(policy.post_rotation_hook)
                if hook:
                    await hook.execute(path, None, None)

            # Update policy
            if policy:
                policy.last_rotated = datetime.now(UTC)
                policy.next_rotation = policy.calculate_next_rotation()

            record.status = RotationStatus.COMPLETED
            record.completed_at = datetime.now(UTC)

            logger.info(
                f"Rotated secret {path}: version {record.old_version} -> {record.new_version}"
            )

        except Exception as e:
            record.status = RotationStatus.FAILED
            record.completed_at = datetime.now(UTC)
            record.error_message = str(e)

            logger.error(f"Failed to rotate secret {path}: {e}")

            # Retry logic
            max_attempts = policy.max_retry_attempts if policy else 1
            if record.attempt_number < max_attempts:
                record.attempt_number += 1
                logger.info(
                    f"Retrying rotation for {path} (attempt {record.attempt_number}/{max_attempts})"
                )
                # Schedule retry with exponential backoff
                delay = 2**record.attempt_number
                await asyncio.sleep(delay)
                return await self.rotate_secret(path, force=True)

        # Record history
        self._add_to_history(record)

        return record

    def _add_to_history(self, record: RotationRecord) -> None:
        """Add rotation record to history."""
        self._history.append(record)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

    def get_rotation_history(
        self,
        path: str | None = None,
        limit: int = 100,
    ) -> list[RotationRecord]:
        """
        Get rotation history.

        Args:
            path: Optional filter by secret path
            limit: Maximum records to return

        Returns:
            List of rotation records
        """
        history = self._history
        if path:
            history = [r for r in history if r.path == path]
        return history[-limit:]

    def get_policies(self) -> list[RotationPolicy]:
        """Get all registered rotation policies."""
        return list(self._policies.values())

    def get_due_rotations(self) -> list[RotationPolicy]:
        """Get policies with due rotations."""
        now = datetime.now(UTC)
        return [
            p
            for p in self._policies.values()
            if p.enabled and p.next_rotation and p.next_rotation <= now
        ]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


async def setup_rotation_for_credentials(
    rotation_manager: SecretRotationManager,
    credential_bindings: dict[str, str],
    frequency: RotationFrequency = RotationFrequency.MONTHLY,
) -> int:
    """
    Setup rotation policies for credential bindings.

    Args:
        rotation_manager: Rotation manager instance
        credential_bindings: Dict mapping alias to vault path
        frequency: Rotation frequency for all credentials

    Returns:
        Number of policies registered
    """
    count = 0
    for _alias, path in credential_bindings.items():
        policy = RotationPolicy(
            path=path,
            frequency=frequency,
            pre_rotation_hook="logging",
            post_rotation_hook="logging",
        )
        rotation_manager.register_policy(policy)
        count += 1

    logger.info(f"Registered {count} rotation policies with {frequency.value} frequency")
    return count

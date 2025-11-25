"""
Resilience Module for CasareRPA Orchestrator.
Provides error recovery, health monitoring, and secure communication features.
"""
import asyncio
import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from loguru import logger


# ==================== ERROR RECOVERY ====================

class RecoveryStrategy(Enum):
    """Strategies for error recovery."""
    RETRY = "retry"
    FAILOVER = "failover"
    RESTART = "restart"
    IGNORE = "ignore"
    ESCALATE = "escalate"


@dataclass
class RecoveryAction:
    """Action taken during error recovery."""
    timestamp: datetime
    error_type: str
    strategy: RecoveryStrategy
    success: bool
    robot_id: Optional[str] = None
    job_id: Optional[str] = None
    details: str = ""


@dataclass
class RetryPolicy:
    """Policy for retry behavior."""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retriable_errors: Set[str] = field(default_factory=lambda: {
        "ConnectionError", "TimeoutError", "NetworkError",
        "TemporaryError", "ResourceBusy"
    })

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a retry attempt."""
        delay = min(
            self.initial_delay * (self.backoff_multiplier ** attempt),
            self.max_delay
        )
        if self.jitter:
            # Add 0-25% random jitter
            delay *= (1 + secrets.randbelow(25) / 100)
        return delay

    def should_retry(self, error_type: str, attempt: int) -> bool:
        """Check if error should be retried."""
        return (
            attempt < self.max_retries and
            error_type in self.retriable_errors
        )


class ErrorRecoveryManager:
    """
    Manages error recovery for the orchestrator.

    Handles:
    - Connection failures
    - Job execution errors
    - Robot crashes
    - Automatic failover
    """

    def __init__(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        max_history: int = 1000,
    ):
        """
        Initialize error recovery manager.

        Args:
            retry_policy: Default retry policy
            max_history: Maximum recovery history entries
        """
        self._retry_policy = retry_policy or RetryPolicy()
        self._max_history = max_history

        # Recovery tracking
        self._recovery_history: List[RecoveryAction] = []
        self._active_recoveries: Dict[str, int] = {}  # key -> retry count

        # Callbacks
        self._on_recovery_success: Optional[Callable] = None
        self._on_recovery_failure: Optional[Callable] = None
        self._on_escalation: Optional[Callable] = None

        logger.info("ErrorRecoveryManager initialized")

    def set_callbacks(
        self,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
        on_escalation: Optional[Callable] = None,
    ):
        """Set recovery callbacks."""
        self._on_recovery_success = on_success
        self._on_recovery_failure = on_failure
        self._on_escalation = on_escalation

    async def handle_connection_error(
        self,
        robot_id: str,
        error: Exception,
        reconnect_fn: Callable,
    ) -> bool:
        """
        Handle robot connection error.

        Args:
            robot_id: Robot that disconnected
            error: The error that occurred
            reconnect_fn: Function to attempt reconnection

        Returns:
            True if recovery successful
        """
        key = f"conn:{robot_id}"
        attempt = self._active_recoveries.get(key, 0)

        error_type = type(error).__name__

        if not self._retry_policy.should_retry(error_type, attempt):
            self._record_action(
                error_type=error_type,
                strategy=RecoveryStrategy.ESCALATE,
                success=False,
                robot_id=robot_id,
                details=f"Max retries exceeded for connection error: {error}",
            )
            self._active_recoveries.pop(key, None)

            if self._on_escalation:
                try:
                    result = self._on_escalation(robot_id, str(error))
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Escalation callback error: {e}")

            return False

        # Attempt retry
        self._active_recoveries[key] = attempt + 1
        delay = self._retry_policy.calculate_delay(attempt)

        logger.info(f"Retrying connection to robot {robot_id} in {delay:.1f}s (attempt {attempt + 1})")
        await asyncio.sleep(delay)

        try:
            await reconnect_fn()
            self._record_action(
                error_type=error_type,
                strategy=RecoveryStrategy.RETRY,
                success=True,
                robot_id=robot_id,
                details=f"Reconnected after {attempt + 1} attempts",
            )
            self._active_recoveries.pop(key, None)

            if self._on_recovery_success:
                try:
                    result = self._on_recovery_success(robot_id, "connection")
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Recovery success callback error: {e}")

            return True

        except Exception as e:
            logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
            return await self.handle_connection_error(robot_id, e, reconnect_fn)

    async def handle_job_error(
        self,
        job_id: str,
        robot_id: str,
        error: Exception,
        retry_fn: Optional[Callable] = None,
        failover_fn: Optional[Callable] = None,
    ) -> bool:
        """
        Handle job execution error.

        Args:
            job_id: Job that failed
            robot_id: Robot that was running the job
            error: The error that occurred
            retry_fn: Function to retry job on same robot
            failover_fn: Function to failover to different robot

        Returns:
            True if recovery successful
        """
        key = f"job:{job_id}"
        attempt = self._active_recoveries.get(key, 0)

        error_type = type(error).__name__

        # Try retry first
        if retry_fn and self._retry_policy.should_retry(error_type, attempt):
            self._active_recoveries[key] = attempt + 1
            delay = self._retry_policy.calculate_delay(attempt)

            logger.info(f"Retrying job {job_id[:8]} in {delay:.1f}s (attempt {attempt + 1})")
            await asyncio.sleep(delay)

            try:
                await retry_fn()
                self._record_action(
                    error_type=error_type,
                    strategy=RecoveryStrategy.RETRY,
                    success=True,
                    robot_id=robot_id,
                    job_id=job_id,
                    details=f"Job retry successful after {attempt + 1} attempts",
                )
                self._active_recoveries.pop(key, None)
                return True

            except Exception as e:
                logger.warning(f"Job retry attempt {attempt + 1} failed: {e}")

        # Try failover
        if failover_fn:
            try:
                await failover_fn()
                self._record_action(
                    error_type=error_type,
                    strategy=RecoveryStrategy.FAILOVER,
                    success=True,
                    robot_id=robot_id,
                    job_id=job_id,
                    details="Job failed over to different robot",
                )
                self._active_recoveries.pop(key, None)
                return True

            except Exception as e:
                logger.error(f"Job failover failed: {e}")

        # Recovery failed
        self._record_action(
            error_type=error_type,
            strategy=RecoveryStrategy.ESCALATE,
            success=False,
            robot_id=robot_id,
            job_id=job_id,
            details=f"All recovery attempts failed: {error}",
        )
        self._active_recoveries.pop(key, None)

        if self._on_recovery_failure:
            try:
                result = self._on_recovery_failure(job_id, str(error))
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(f"Recovery failure callback error: {e}")

        return False

    async def handle_robot_crash(
        self,
        robot_id: str,
        active_jobs: List[str],
        restart_fn: Optional[Callable] = None,
        reassign_fn: Optional[Callable[[str], Any]] = None,
    ) -> Dict[str, bool]:
        """
        Handle robot crash.

        Args:
            robot_id: Robot that crashed
            active_jobs: Jobs that were running on robot
            restart_fn: Function to restart robot
            reassign_fn: Function to reassign a job

        Returns:
            Dict of job_id -> recovery success
        """
        results = {}

        self._record_action(
            error_type="RobotCrash",
            strategy=RecoveryStrategy.RESTART,
            success=False,  # Updated later
            robot_id=robot_id,
            details=f"Robot crashed with {len(active_jobs)} active jobs",
        )

        # Try to restart robot
        if restart_fn:
            try:
                await restart_fn()
                logger.info(f"Robot {robot_id} restart initiated")
            except Exception as e:
                logger.error(f"Robot restart failed: {e}")

        # Reassign jobs
        for job_id in active_jobs:
            if reassign_fn:
                try:
                    await reassign_fn(job_id)
                    results[job_id] = True
                    logger.info(f"Job {job_id[:8]} reassigned")
                except Exception as e:
                    results[job_id] = False
                    logger.error(f"Job {job_id[:8]} reassignment failed: {e}")
            else:
                results[job_id] = False

        return results

    def _record_action(
        self,
        error_type: str,
        strategy: RecoveryStrategy,
        success: bool,
        robot_id: Optional[str] = None,
        job_id: Optional[str] = None,
        details: str = "",
    ):
        """Record a recovery action."""
        action = RecoveryAction(
            timestamp=datetime.utcnow(),
            error_type=error_type,
            strategy=strategy,
            success=success,
            robot_id=robot_id,
            job_id=job_id,
            details=details,
        )
        self._recovery_history.append(action)

        # Trim history
        if len(self._recovery_history) > self._max_history:
            self._recovery_history = self._recovery_history[-self._max_history:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        total = len(self._recovery_history)
        successful = sum(1 for a in self._recovery_history if a.success)

        strategy_counts = defaultdict(int)
        for action in self._recovery_history:
            strategy_counts[action.strategy.value] += 1

        return {
            "total_recoveries": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": successful / total * 100 if total > 0 else 0.0,
            "by_strategy": dict(strategy_counts),
            "active_recoveries": len(self._active_recoveries),
        }

    def get_recent_actions(self, limit: int = 20) -> List[RecoveryAction]:
        """Get recent recovery actions."""
        return self._recovery_history[-limit:]


# ==================== HEALTH MONITORING ====================

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthMetrics:
    """Health metrics for a robot."""
    robot_id: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_heartbeat: Optional[datetime] = None
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    active_jobs: int = 0
    error_count: int = 0
    response_time_ms: float = 0.0

    @property
    def is_healthy(self) -> bool:
        """Check if robot is healthy."""
        return self.status == HealthStatus.HEALTHY

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "robot_id": self.robot_id,
            "status": self.status.value,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "active_jobs": self.active_jobs,
            "error_count": self.error_count,
            "response_time_ms": self.response_time_ms,
        }


@dataclass
class HealthThresholds:
    """Thresholds for health checks."""
    heartbeat_timeout: float = 60.0  # seconds
    cpu_warning: float = 80.0
    cpu_critical: float = 95.0
    memory_warning: float = 80.0
    memory_critical: float = 95.0
    disk_warning: float = 80.0
    disk_critical: float = 95.0
    error_rate_warning: float = 10.0  # percent
    error_rate_critical: float = 25.0


class HealthMonitor:
    """
    Monitors health of robots and the orchestrator.

    Tracks:
    - Heartbeat timeouts
    - Resource utilization
    - Error rates
    - Response times
    """

    def __init__(
        self,
        thresholds: Optional[HealthThresholds] = None,
        check_interval: float = 30.0,
    ):
        """
        Initialize health monitor.

        Args:
            thresholds: Health check thresholds
            check_interval: Interval between health checks
        """
        self._thresholds = thresholds or HealthThresholds()
        self._check_interval = check_interval

        # Robot health
        self._robot_metrics: Dict[str, HealthMetrics] = {}
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._request_counts: Dict[str, int] = defaultdict(int)

        # Monitoring state
        self._running = False
        self._check_task: Optional[asyncio.Task] = None

        # Callbacks
        self._on_health_change: Optional[Callable] = None
        self._on_robot_unhealthy: Optional[Callable] = None

        logger.info("HealthMonitor initialized")

    def set_callbacks(
        self,
        on_health_change: Optional[Callable] = None,
        on_robot_unhealthy: Optional[Callable] = None,
    ):
        """Set health monitoring callbacks."""
        self._on_health_change = on_health_change
        self._on_robot_unhealthy = on_robot_unhealthy

    async def start(self):
        """Start health monitoring."""
        if self._running:
            return

        self._running = True
        self._check_task = asyncio.create_task(self._check_loop())
        logger.info("Health monitoring started")

    async def stop(self):
        """Stop health monitoring."""
        self._running = False

        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

        logger.info("Health monitoring stopped")

    def update_heartbeat(
        self,
        robot_id: str,
        cpu_percent: float = 0.0,
        memory_percent: float = 0.0,
        disk_percent: float = 0.0,
        active_jobs: int = 0,
    ):
        """
        Update robot heartbeat.

        Args:
            robot_id: Robot ID
            cpu_percent: CPU usage
            memory_percent: Memory usage
            disk_percent: Disk usage
            active_jobs: Active job count
        """
        metrics = self._robot_metrics.get(robot_id)

        if not metrics:
            metrics = HealthMetrics(robot_id=robot_id)
            self._robot_metrics[robot_id] = metrics

        metrics.last_heartbeat = datetime.utcnow()
        metrics.cpu_percent = cpu_percent
        metrics.memory_percent = memory_percent
        metrics.disk_percent = disk_percent
        metrics.active_jobs = active_jobs

        # Recalculate status
        new_status = self._calculate_status(metrics)
        if new_status != metrics.status:
            old_status = metrics.status
            metrics.status = new_status
            self._notify_health_change(robot_id, old_status, new_status)

    def record_error(self, robot_id: str):
        """Record an error for a robot."""
        self._error_counts[robot_id] += 1

    def record_request(self, robot_id: str, response_time_ms: float = 0.0):
        """Record a successful request."""
        self._request_counts[robot_id] += 1

        metrics = self._robot_metrics.get(robot_id)
        if metrics:
            # Exponential moving average
            alpha = 0.3
            metrics.response_time_ms = (
                alpha * response_time_ms +
                (1 - alpha) * metrics.response_time_ms
            )

    def _calculate_status(self, metrics: HealthMetrics) -> HealthStatus:
        """Calculate health status from metrics."""
        if not metrics.last_heartbeat:
            return HealthStatus.UNKNOWN

        # Check heartbeat timeout
        elapsed = (datetime.utcnow() - metrics.last_heartbeat).total_seconds()
        if elapsed > self._thresholds.heartbeat_timeout:
            return HealthStatus.UNHEALTHY

        # Check critical thresholds
        if (metrics.cpu_percent > self._thresholds.cpu_critical or
            metrics.memory_percent > self._thresholds.memory_critical or
            metrics.disk_percent > self._thresholds.disk_critical):
            return HealthStatus.UNHEALTHY

        # Check warning thresholds
        if (metrics.cpu_percent > self._thresholds.cpu_warning or
            metrics.memory_percent > self._thresholds.memory_warning or
            metrics.disk_percent > self._thresholds.disk_warning):
            return HealthStatus.DEGRADED

        # Check error rate
        error_count = self._error_counts.get(metrics.robot_id, 0)
        request_count = self._request_counts.get(metrics.robot_id, 0)
        if request_count > 0:
            error_rate = (error_count / request_count) * 100
            if error_rate > self._thresholds.error_rate_critical:
                return HealthStatus.UNHEALTHY
            if error_rate > self._thresholds.error_rate_warning:
                return HealthStatus.DEGRADED

        metrics.error_count = error_count
        return HealthStatus.HEALTHY

    def _notify_health_change(
        self,
        robot_id: str,
        old_status: HealthStatus,
        new_status: HealthStatus,
    ):
        """Notify callbacks of health status change."""
        if self._on_health_change:
            try:
                self._on_health_change(robot_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Health change callback error: {e}")

        if new_status == HealthStatus.UNHEALTHY and self._on_robot_unhealthy:
            try:
                self._on_robot_unhealthy(robot_id)
            except Exception as e:
                logger.error(f"Robot unhealthy callback error: {e}")

    async def _check_loop(self):
        """Periodic health check loop."""
        while self._running:
            try:
                await asyncio.sleep(self._check_interval)
                await self._check_all_robots()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _check_all_robots(self):
        """Check health of all robots."""
        now = datetime.utcnow()

        for robot_id, metrics in self._robot_metrics.items():
            if not metrics.last_heartbeat:
                continue

            # Check for stale heartbeat
            elapsed = (now - metrics.last_heartbeat).total_seconds()
            if elapsed > self._thresholds.heartbeat_timeout:
                if metrics.status != HealthStatus.UNHEALTHY:
                    old_status = metrics.status
                    metrics.status = HealthStatus.UNHEALTHY
                    self._notify_health_change(robot_id, old_status, HealthStatus.UNHEALTHY)

    def get_robot_health(self, robot_id: str) -> Optional[HealthMetrics]:
        """Get health metrics for a robot."""
        return self._robot_metrics.get(robot_id)

    def get_all_health(self) -> Dict[str, HealthMetrics]:
        """Get health metrics for all robots."""
        return dict(self._robot_metrics)

    def get_unhealthy_robots(self) -> List[str]:
        """Get list of unhealthy robot IDs."""
        return [
            robot_id for robot_id, metrics in self._robot_metrics.items()
            if metrics.status == HealthStatus.UNHEALTHY
        ]

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        total = len(self._robot_metrics)
        healthy = sum(1 for m in self._robot_metrics.values() if m.status == HealthStatus.HEALTHY)
        degraded = sum(1 for m in self._robot_metrics.values() if m.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for m in self._robot_metrics.values() if m.status == HealthStatus.UNHEALTHY)

        # Overall status
        if unhealthy > 0:
            overall = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall = HealthStatus.DEGRADED
        elif total > 0:
            overall = HealthStatus.HEALTHY
        else:
            overall = HealthStatus.UNKNOWN

        return {
            "overall_status": overall.value,
            "total_robots": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "health_percentage": healthy / total * 100 if total > 0 else 0.0,
        }

    def remove_robot(self, robot_id: str):
        """Remove a robot from monitoring."""
        self._robot_metrics.pop(robot_id, None)
        self._error_counts.pop(robot_id, None)
        self._request_counts.pop(robot_id, None)


# ==================== SECURE COMMUNICATION ====================

class TokenType(Enum):
    """Token types for authentication."""
    API_KEY = "api_key"
    JWT = "jwt"
    HMAC = "hmac"


@dataclass
class AuthToken:
    """Authentication token."""
    token: str
    token_type: TokenType
    robot_id: str
    expires_at: Optional[datetime] = None
    scopes: List[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class SecurityManager:
    """
    Manages security for orchestrator communication.

    Provides:
    - Token generation and validation
    - HMAC signing
    - Rate limiting
    """

    def __init__(
        self,
        secret_key: Optional[str] = None,
        token_ttl_hours: int = 24,
        rate_limit_requests: int = 100,
        rate_limit_window: int = 60,
    ):
        """
        Initialize security manager.

        Args:
            secret_key: Secret for signing
            token_ttl_hours: Token time-to-live in hours
            rate_limit_requests: Max requests per window
            rate_limit_window: Rate limit window in seconds
        """
        self._secret_key = secret_key or secrets.token_hex(32)
        self._token_ttl = timedelta(hours=token_ttl_hours)
        self._rate_limit_requests = rate_limit_requests
        self._rate_limit_window = rate_limit_window

        # Token storage
        self._tokens: Dict[str, AuthToken] = {}

        # Rate limiting
        self._request_counts: Dict[str, List[float]] = defaultdict(list)

        logger.info("SecurityManager initialized")

    def generate_token(
        self,
        robot_id: str,
        scopes: Optional[List[str]] = None,
    ) -> AuthToken:
        """
        Generate an authentication token.

        Args:
            robot_id: Robot to generate token for
            scopes: Token scopes/permissions

        Returns:
            Generated token
        """
        token_str = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self._token_ttl

        token = AuthToken(
            token=token_str,
            token_type=TokenType.API_KEY,
            robot_id=robot_id,
            expires_at=expires_at,
            scopes=scopes or ["execute", "report"],
        )

        self._tokens[token_str] = token
        logger.debug(f"Generated token for robot {robot_id}")

        return token

    def validate_token(self, token_str: str) -> Optional[AuthToken]:
        """
        Validate an authentication token.

        Args:
            token_str: Token string to validate

        Returns:
            Token if valid, None otherwise
        """
        token = self._tokens.get(token_str)

        if not token:
            return None

        if token.is_expired:
            self._tokens.pop(token_str, None)
            return None

        return token

    def revoke_token(self, token_str: str) -> bool:
        """
        Revoke an authentication token.

        Args:
            token_str: Token to revoke

        Returns:
            True if token was revoked
        """
        if token_str in self._tokens:
            del self._tokens[token_str]
            return True
        return False

    def revoke_robot_tokens(self, robot_id: str) -> int:
        """
        Revoke all tokens for a robot.

        Args:
            robot_id: Robot to revoke tokens for

        Returns:
            Number of tokens revoked
        """
        to_revoke = [
            t for t, token in self._tokens.items()
            if token.robot_id == robot_id
        ]

        for token_str in to_revoke:
            del self._tokens[token_str]

        return len(to_revoke)

    def sign_message(self, message: str) -> str:
        """
        Sign a message with HMAC.

        Args:
            message: Message to sign

        Returns:
            Hex-encoded signature
        """
        signature = hmac.new(
            self._secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    def verify_signature(self, message: str, signature: str) -> bool:
        """
        Verify a message signature.

        Args:
            message: Original message
            signature: Signature to verify

        Returns:
            True if signature is valid
        """
        expected = self.sign_message(message)
        return hmac.compare_digest(expected, signature)

    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if request is within rate limits.

        Args:
            identifier: Client identifier (robot_id, IP, etc.)

        Returns:
            True if within limits
        """
        now = time.time()
        window_start = now - self._rate_limit_window

        # Clean old entries
        self._request_counts[identifier] = [
            ts for ts in self._request_counts[identifier]
            if ts > window_start
        ]

        # Check limit
        if len(self._request_counts[identifier]) >= self._rate_limit_requests:
            return False

        # Record request
        self._request_counts[identifier].append(now)
        return True

    def get_rate_limit_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        window_start = now - self._rate_limit_window

        current_count = sum(
            1 for ts in self._request_counts.get(identifier, [])
            if ts > window_start
        )

        return max(0, self._rate_limit_requests - current_count)

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired tokens.

        Returns:
            Number of tokens removed
        """
        expired = [
            t for t, token in self._tokens.items()
            if token.is_expired
        ]

        for token_str in expired:
            del self._tokens[token_str]

        return len(expired)

    def get_statistics(self) -> Dict[str, Any]:
        """Get security statistics."""
        now = datetime.utcnow()

        active_tokens = sum(1 for t in self._tokens.values() if not t.is_expired)
        expired_tokens = sum(1 for t in self._tokens.values() if t.is_expired)

        return {
            "total_tokens": len(self._tokens),
            "active_tokens": active_tokens,
            "expired_tokens": expired_tokens,
            "rate_limited_clients": len(self._request_counts),
        }

    @property
    def active_token_count(self) -> int:
        """Get count of active tokens."""
        return sum(1 for t in self._tokens.values() if not t.is_expired)

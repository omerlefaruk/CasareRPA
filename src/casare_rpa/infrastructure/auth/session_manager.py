"""
CasareRPA - Session Manager.

Manages user sessions with:
- Session creation and validation
- Idle timeout enforcement
- Concurrent session limits
- Activity tracking

Usage:
    from casare_rpa.infrastructure.auth import SessionManager, SessionConfig

    config = SessionConfig(
        session_timeout_minutes=480,  # 8 hours
        idle_timeout_minutes=30,
        max_sessions_per_user=3
    )
    manager = SessionManager(config)

    # Create session
    session = await manager.create_session(user_id, token, client_info)

    # Validate on each request
    session = await manager.validate_session(token)
    if session:
        await manager.update_activity(session.id)
"""

import asyncio
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID

from loguru import logger

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_SESSION_TIMEOUT_MINUTES = 480  # 8 hours
DEFAULT_IDLE_TIMEOUT_MINUTES = 30
DEFAULT_MAX_SESSIONS_PER_USER = 3
DEFAULT_REFRESH_TOKEN_DAYS = 30
SESSION_ID_BYTES = 32


# =============================================================================
# EXCEPTIONS
# =============================================================================


class SessionError(Exception):
    """Base exception for session operations."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(message)


class SessionNotFoundError(SessionError):
    """Raised when session is not found."""

    pass


class SessionExpiredError(SessionError):
    """Raised when session has expired."""

    pass


class SessionLimitExceededError(SessionError):
    """Raised when max sessions per user exceeded."""

    pass


# =============================================================================
# DATA MODELS
# =============================================================================


class SessionStatus(str, Enum):
    """Session status."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    IDLE_TIMEOUT = "idle_timeout"


@dataclass
class SessionConfig:
    """Session configuration."""

    session_timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES
    idle_timeout_minutes: int = DEFAULT_IDLE_TIMEOUT_MINUTES
    max_sessions_per_user: int = DEFAULT_MAX_SESSIONS_PER_USER
    refresh_token_days: int = DEFAULT_REFRESH_TOKEN_DAYS
    enforce_single_session: bool = False


@dataclass
class ClientInfo:
    """Client connection information."""

    ip_address: str | None = None
    user_agent: str | None = None
    device_id: str | None = None
    location: str | None = None


@dataclass
class Session:
    """User session data."""

    id: str
    user_id: UUID
    token_hash: str  # Hashed token for lookup
    status: SessionStatus = SessionStatus.ACTIVE
    client_info: ClientInfo = field(default_factory=ClientInfo)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revoked_at: datetime | None = None
    revoke_reason: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        if self.status != SessionStatus.ACTIVE:
            return True
        if self.expires_at and datetime.now(UTC) > self.expires_at:
            return True
        return False

    @property
    def is_valid(self) -> bool:
        """Check if session is currently valid."""
        return self.status == SessionStatus.ACTIVE and not self.is_expired

    @property
    def time_since_activity(self) -> timedelta:
        """Get time since last activity."""
        return datetime.now(UTC) - self.last_activity_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": str(self.user_id),
            "status": self.status.value,
            "client_ip": self.client_info.ip_address,
            "user_agent": self.client_info.user_agent,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_activity_at": self.last_activity_at.isoformat(),
        }


# =============================================================================
# SESSION MANAGER
# =============================================================================


class SessionManager:
    """
    Manager for user session lifecycle.

    Handles session creation, validation, and cleanup.
    Supports in-memory storage with optional database persistence.
    """

    def __init__(
        self,
        config: SessionConfig | None = None,
        db_client: Any = None,
    ) -> None:
        """
        Initialize session manager.

        Args:
            config: Session configuration options
            db_client: Optional database client for persistence
        """
        self._config = config or SessionConfig()
        self._client = db_client
        self._sessions: dict[str, Session] = {}  # session_id -> Session
        self._user_sessions: dict[UUID, list[str]] = {}  # user_id -> [session_ids]
        self._token_to_session: dict[str, str] = {}  # token_hash -> session_id
        self._lock = asyncio.Lock()

    async def create_session(
        self,
        user_id: UUID,
        token: str,
        client_info: ClientInfo | None = None,
    ) -> Session:
        """
        Create a new session for a user.

        Args:
            user_id: User ID
            token: JWT token for the session
            client_info: Optional client connection info

        Returns:
            Created Session

        Raises:
            SessionLimitExceededError: If max sessions exceeded and not auto-removing
        """
        async with self._lock:
            # Check session limit
            user_session_ids = self._user_sessions.get(user_id, [])

            if self._config.enforce_single_session:
                # Revoke all existing sessions
                for session_id in user_session_ids.copy():
                    await self._revoke_session_internal(
                        session_id, "New login with single session enforcement"
                    )
            elif len(user_session_ids) >= self._config.max_sessions_per_user:
                # Remove oldest session
                oldest_id = user_session_ids[0]
                await self._revoke_session_internal(
                    oldest_id, "Session limit exceeded - oldest removed"
                )

            # Create new session
            session_id = secrets.token_urlsafe(SESSION_ID_BYTES)
            token_hash = self._hash_token(token)
            now = datetime.now(UTC)
            expires_at = now + timedelta(minutes=self._config.session_timeout_minutes)

            session = Session(
                id=session_id,
                user_id=user_id,
                token_hash=token_hash,
                status=SessionStatus.ACTIVE,
                client_info=client_info or ClientInfo(),
                created_at=now,
                expires_at=expires_at,
                last_activity_at=now,
            )

            # Store session
            self._sessions[session_id] = session
            self._token_to_session[token_hash] = session_id

            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(session_id)

            # Persist to database if configured
            if self._client:
                await self._persist_session(session)

            logger.info(
                f"Created session for user {user_id}: id={session_id[:12]}..., "
                f"expires={expires_at.isoformat()}"
            )
            return session

    async def validate_session(
        self,
        token: str,
        update_activity: bool = True,
    ) -> Session | None:
        """
        Validate a session by its token.

        Args:
            token: JWT token
            update_activity: Whether to update last activity timestamp

        Returns:
            Session if valid, None if invalid/expired

        Raises:
            SessionExpiredError: If session has expired
        """
        token_hash = self._hash_token(token)
        session_id = self._token_to_session.get(token_hash)

        if not session_id:
            logger.debug("Session not found for token")
            return None

        session = self._sessions.get(session_id)
        if not session:
            logger.debug(f"Session data not found: {session_id[:12]}...")
            return None

        # Check expiration
        if session.is_expired:
            logger.debug(f"Session expired: {session_id[:12]}...")
            raise SessionExpiredError("Session has expired")

        # Check idle timeout
        idle_limit = timedelta(minutes=self._config.idle_timeout_minutes)
        if session.time_since_activity > idle_limit:
            session.status = SessionStatus.IDLE_TIMEOUT
            logger.info(f"Session idle timeout: {session_id[:12]}...")
            raise SessionExpiredError("Session idle timeout")

        # Update activity
        if update_activity:
            await self.update_activity(session_id)

        return session

    async def update_activity(self, session_id: str) -> bool:
        """
        Update last activity timestamp for a session.

        Args:
            session_id: Session ID

        Returns:
            True if updated
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.last_activity_at = datetime.now(UTC)

        # Persist update if configured
        if self._client:
            await self._update_session_activity(session_id)

        return True

    async def invalidate_session(
        self,
        token: str,
        reason: str | None = None,
    ) -> bool:
        """
        Invalidate a session (logout).

        Args:
            token: JWT token
            reason: Optional revocation reason

        Returns:
            True if invalidated
        """
        token_hash = self._hash_token(token)
        session_id = self._token_to_session.get(token_hash)

        if not session_id:
            return False

        async with self._lock:
            return await self._revoke_session_internal(session_id, reason or "User logout")

    async def invalidate_all_sessions(
        self,
        user_id: UUID,
        reason: str | None = None,
    ) -> int:
        """
        Invalidate all sessions for a user.

        Args:
            user_id: User ID
            reason: Optional revocation reason

        Returns:
            Number of sessions invalidated
        """
        async with self._lock:
            session_ids = self._user_sessions.get(user_id, []).copy()
            count = 0

            for session_id in session_ids:
                if await self._revoke_session_internal(
                    session_id, reason or "All sessions invalidated"
                ):
                    count += 1

            logger.info(f"Invalidated {count} sessions for user {user_id}")
            return count

    async def get_user_sessions(self, user_id: UUID) -> list[Session]:
        """
        Get all active sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of active Sessions
        """
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []

        for session_id in session_ids:
            session = self._sessions.get(session_id)
            if session and session.is_valid:
                sessions.append(session)

        return sessions

    async def get_session_by_id(self, session_id: str) -> Session | None:
        """Get a session by its ID."""
        return self._sessions.get(session_id)

    async def get_active_session_count(self, user_id: UUID) -> int:
        """Get count of active sessions for a user."""
        sessions = await self.get_user_sessions(user_id)
        return len(sessions)

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from memory.

        Returns:
            Number of sessions cleaned up
        """
        async with self._lock:
            expired_ids = []
            now = datetime.now(UTC)

            for session_id, session in self._sessions.items():
                if session.expires_at and now > session.expires_at:
                    expired_ids.append(session_id)
                elif session.status != SessionStatus.ACTIVE:
                    expired_ids.append(session_id)

            for session_id in expired_ids:
                await self._remove_session_internal(session_id)

            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions")

            return len(expired_ids)

    async def refresh_session(
        self,
        old_token: str,
        new_token: str,
    ) -> Session | None:
        """
        Refresh a session with a new token.

        Args:
            old_token: Current token
            new_token: New token

        Returns:
            Updated Session or None
        """
        old_hash = self._hash_token(old_token)
        session_id = self._token_to_session.get(old_hash)

        if not session_id:
            return None

        async with self._lock:
            session = self._sessions.get(session_id)
            if not session or not session.is_valid:
                return None

            # Update token hash
            new_hash = self._hash_token(new_token)
            del self._token_to_session[old_hash]
            self._token_to_session[new_hash] = session_id

            # Update session
            session.token_hash = new_hash
            session.last_activity_at = datetime.now(UTC)
            session.expires_at = datetime.now(UTC) + timedelta(
                minutes=self._config.session_timeout_minutes
            )

            logger.debug(f"Refreshed session: {session_id[:12]}...")
            return session

    def _hash_token(self, token: str) -> str:
        """Hash a token for secure storage/lookup."""
        import hashlib

        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def _revoke_session_internal(self, session_id: str, reason: str) -> bool:
        """Internal session revocation (must hold lock)."""
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.status = SessionStatus.REVOKED
        session.revoked_at = datetime.now(UTC)
        session.revoke_reason = reason

        # Remove from token mapping
        if session.token_hash in self._token_to_session:
            del self._token_to_session[session.token_hash]

        # Remove from user sessions
        if session.user_id in self._user_sessions:
            if session_id in self._user_sessions[session.user_id]:
                self._user_sessions[session.user_id].remove(session_id)

        # Persist if configured
        if self._client:
            await self._persist_session_revocation(session_id, reason)

        logger.debug(f"Revoked session {session_id[:12]}...: {reason}")
        return True

    async def _remove_session_internal(self, session_id: str) -> None:
        """Internal session removal (must hold lock)."""
        session = self._sessions.get(session_id)
        if not session:
            return

        # Remove from all mappings
        if session.token_hash in self._token_to_session:
            del self._token_to_session[session.token_hash]

        if session.user_id in self._user_sessions:
            if session_id in self._user_sessions[session.user_id]:
                self._user_sessions[session.user_id].remove(session_id)

        del self._sessions[session_id]

    # =========================================================================
    # DATABASE OPERATIONS (optional persistence)
    # =========================================================================

    async def _persist_session(self, session: Session) -> None:
        """Persist session to database."""
        if not self._client:
            return

        data = {
            "id": session.id,
            "user_id": str(session.user_id),
            "token_hash": session.token_hash,
            "status": session.status.value,
            "client_ip": session.client_info.ip_address,
            "user_agent": session.client_info.user_agent,
            "device_id": session.client_info.device_id,
            "created_at": session.created_at.isoformat(),
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "last_activity_at": session.last_activity_at.isoformat(),
        }

        try:
            if hasattr(self._client, "table"):
                self._client.table("user_sessions").insert(data).execute()
            elif hasattr(self._client, "acquire"):
                async with self._client.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO user_sessions (
                            id, user_id, token_hash, status, client_ip, user_agent,
                            device_id, created_at, expires_at, last_activity_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """,
                        session.id,
                        session.user_id,
                        session.token_hash,
                        session.status.value,
                        session.client_info.ip_address,
                        session.client_info.user_agent,
                        session.client_info.device_id,
                        session.created_at,
                        session.expires_at,
                        session.last_activity_at,
                    )
        except Exception as e:
            logger.error(f"Failed to persist session: {e}")

    async def _update_session_activity(self, session_id: str) -> None:
        """Update session activity in database."""
        if not self._client:
            return

        now = datetime.now(UTC)

        try:
            if hasattr(self._client, "table"):
                self._client.table("user_sessions").update(
                    {"last_activity_at": now.isoformat()}
                ).eq("id", session_id).execute()
            elif hasattr(self._client, "acquire"):
                async with self._client.acquire() as conn:
                    await conn.execute(
                        "UPDATE user_sessions SET last_activity_at = $1 WHERE id = $2",
                        now,
                        session_id,
                    )
        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")

    async def _persist_session_revocation(self, session_id: str, reason: str) -> None:
        """Persist session revocation to database."""
        if not self._client:
            return

        now = datetime.now(UTC)

        try:
            if hasattr(self._client, "table"):
                self._client.table("user_sessions").update(
                    {
                        "status": SessionStatus.REVOKED.value,
                        "revoked_at": now.isoformat(),
                        "revoke_reason": reason,
                    }
                ).eq("id", session_id).execute()
            elif hasattr(self._client, "acquire"):
                async with self._client.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE user_sessions SET
                            status = $1, revoked_at = $2, revoke_reason = $3
                        WHERE id = $4
                        """,
                        SessionStatus.REVOKED.value,
                        now,
                        reason,
                        session_id,
                    )
        except Exception as e:
            logger.error(f"Failed to persist session revocation: {e}")


__all__ = [
    "SessionManager",
    "SessionConfig",
    "Session",
    "SessionStatus",
    "ClientInfo",
    "SessionError",
    "SessionNotFoundError",
    "SessionExpiredError",
    "SessionLimitExceededError",
]

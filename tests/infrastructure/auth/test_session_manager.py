"""
Tests for SessionManager - Session lifecycle management.

Tests cover:
- Session creation
- Session validation
- Idle timeout
- Concurrent session limits
- Session invalidation
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from casare_rpa.infrastructure.auth.session_manager import (
    SessionManager,
    SessionConfig,
    Session,
    SessionStatus,
    ClientInfo,
    SessionExpiredError,
    SessionLimitExceededError,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def session_config():
    """Create test session configuration."""
    return SessionConfig(
        session_timeout_minutes=60,
        idle_timeout_minutes=15,
        max_sessions_per_user=3,
    )


@pytest.fixture
def session_manager(session_config):
    """Create SessionManager with test config."""
    return SessionManager(config=session_config)


@pytest.fixture
def client_info():
    """Create sample client info."""
    return ClientInfo(
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        device_id="test-device-123",
    )


@pytest.fixture
def sample_token():
    """Generate a sample JWT-like token."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"


# =============================================================================
# SESSION CREATION TESTS
# =============================================================================


class TestSessionCreation:
    """Tests for session creation."""

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, session_manager, client_info, sample_token
    ):
        """Successfully create a new session."""
        user_id = uuid4()

        session = await session_manager.create_session(
            user_id=user_id,
            token=sample_token,
            client_info=client_info,
        )

        assert session is not None
        assert session.user_id == user_id
        assert session.status == SessionStatus.ACTIVE
        assert session.client_info.ip_address == client_info.ip_address
        assert session.expires_at is not None
        assert session.is_valid is True

    @pytest.mark.asyncio
    async def test_create_session_without_client_info(
        self, session_manager, sample_token
    ):
        """Create session without client info succeeds."""
        user_id = uuid4()

        session = await session_manager.create_session(
            user_id=user_id,
            token=sample_token,
        )

        assert session is not None
        assert session.client_info is not None  # Default ClientInfo

    @pytest.mark.asyncio
    async def test_create_session_enforces_limit(self, session_manager, sample_token):
        """Creating beyond limit removes oldest session."""
        user_id = uuid4()

        # Create max sessions
        sessions = []
        for i in range(3):
            session = await session_manager.create_session(
                user_id=user_id,
                token=f"token_{i}",
            )
            sessions.append(session)

        # Create one more - should remove oldest
        new_session = await session_manager.create_session(
            user_id=user_id,
            token="token_new",
        )

        # First session should be revoked
        assert sessions[0].status == SessionStatus.REVOKED

        # User should still have 3 sessions
        user_sessions = await session_manager.get_user_sessions(user_id)
        assert len(user_sessions) == 3

    @pytest.mark.asyncio
    async def test_create_session_single_session_mode(self, sample_token):
        """Single session mode revokes all existing sessions."""
        config = SessionConfig(enforce_single_session=True)
        manager = SessionManager(config=config)
        user_id = uuid4()

        # Create first session
        first = await manager.create_session(user_id, "token_1")

        # Create second session
        second = await manager.create_session(user_id, "token_2")

        # First should be revoked
        assert first.status == SessionStatus.REVOKED

        # Only one active session
        sessions = await manager.get_user_sessions(user_id)
        assert len(sessions) == 1
        assert sessions[0].id == second.id


# =============================================================================
# SESSION VALIDATION TESTS
# =============================================================================


class TestSessionValidation:
    """Tests for session validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_session(self, session_manager, sample_token):
        """Valid session passes validation."""
        user_id = uuid4()
        created = await session_manager.create_session(user_id, sample_token)

        session = await session_manager.validate_session(sample_token)

        assert session is not None
        assert session.id == created.id
        assert session.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_unknown_token(self, session_manager):
        """Unknown token returns None."""
        session = await session_manager.validate_session("unknown_token")
        assert session is None

    @pytest.mark.asyncio
    async def test_validate_expired_session(self, session_manager, sample_token):
        """Expired session raises error."""
        config = SessionConfig(session_timeout_minutes=0)  # Immediate expiry
        manager = SessionManager(config=config)
        user_id = uuid4()

        await manager.create_session(user_id, sample_token)

        with pytest.raises(SessionExpiredError):
            await manager.validate_session(sample_token)

    @pytest.mark.asyncio
    async def test_validate_idle_timeout(self, sample_token):
        """Idle session raises timeout error."""
        config = SessionConfig(idle_timeout_minutes=0)  # Immediate idle timeout
        manager = SessionManager(config=config)
        user_id = uuid4()

        await manager.create_session(user_id, sample_token)

        # Force last_activity to be in the past
        session_id = list(manager._sessions.keys())[0]
        manager._sessions[session_id].last_activity_at = datetime.now(
            timezone.utc
        ) - timedelta(minutes=5)

        with pytest.raises(SessionExpiredError) as exc_info:
            await manager.validate_session(sample_token)
        assert "idle" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_validate_updates_activity(self, session_manager, sample_token):
        """Validation updates last activity timestamp."""
        user_id = uuid4()
        await session_manager.create_session(user_id, sample_token)

        original_time = session_manager._sessions[
            list(session_manager._sessions.keys())[0]
        ].last_activity_at

        # Small delay to ensure time difference
        import asyncio

        await asyncio.sleep(0.01)

        session = await session_manager.validate_session(sample_token)

        assert session.last_activity_at >= original_time


# =============================================================================
# SESSION INVALIDATION TESTS
# =============================================================================


class TestSessionInvalidation:
    """Tests for session invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_session(self, session_manager, sample_token):
        """Successfully invalidate a session."""
        user_id = uuid4()
        await session_manager.create_session(user_id, sample_token)

        result = await session_manager.invalidate_session(sample_token)

        assert result is True

        # Session should now be invalid
        session = await session_manager.validate_session(sample_token)
        assert session is None

    @pytest.mark.asyncio
    async def test_invalidate_unknown_session(self, session_manager):
        """Invalidating unknown session returns False."""
        result = await session_manager.invalidate_session("unknown_token")
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_all_sessions(self, session_manager):
        """Invalidate all sessions for a user."""
        user_id = uuid4()

        # Create multiple sessions
        for i in range(3):
            await session_manager.create_session(user_id, f"token_{i}")

        count = await session_manager.invalidate_all_sessions(user_id)

        assert count == 3

        # All sessions should be invalid
        sessions = await session_manager.get_user_sessions(user_id)
        assert len(sessions) == 0


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================


class TestSessionManagement:
    """Tests for session management operations."""

    @pytest.mark.asyncio
    async def test_get_user_sessions(self, session_manager):
        """Get all active sessions for a user."""
        user_id = uuid4()

        for i in range(3):
            await session_manager.create_session(user_id, f"token_{i}")

        sessions = await session_manager.get_user_sessions(user_id)

        assert len(sessions) == 3
        assert all(s.user_id == user_id for s in sessions)
        assert all(s.is_valid for s in sessions)

    @pytest.mark.asyncio
    async def test_get_active_session_count(self, session_manager):
        """Get count of active sessions."""
        user_id = uuid4()

        for i in range(2):
            await session_manager.create_session(user_id, f"token_{i}")

        count = await session_manager.get_active_session_count(user_id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_refresh_session(self, session_manager):
        """Refresh session with new token."""
        user_id = uuid4()
        old_token = "old_token"
        new_token = "new_token"

        await session_manager.create_session(user_id, old_token)

        session = await session_manager.refresh_session(old_token, new_token)

        assert session is not None

        # Old token should no longer work
        old_session = await session_manager.validate_session(old_token)
        assert old_session is None

        # New token should work
        new_session = await session_manager.validate_session(new_token)
        assert new_session is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager):
        """Cleanup removes expired sessions."""
        user_id = uuid4()

        # Create session
        await session_manager.create_session(user_id, "token")

        # Force expiration
        session_id = list(session_manager._sessions.keys())[0]
        session_manager._sessions[session_id].expires_at = datetime.now(
            timezone.utc
        ) - timedelta(hours=1)

        count = await session_manager.cleanup_expired_sessions()

        assert count == 1
        assert len(session_manager._sessions) == 0


# =============================================================================
# SESSION STATUS TESTS
# =============================================================================


class TestSessionStatus:
    """Tests for Session status properties."""

    def test_session_is_expired(self):
        """Session with past expiration is expired."""
        session = Session(
            id="test-id",
            user_id=uuid4(),
            token_hash="hash",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        assert session.is_expired is True
        assert session.is_valid is False

    def test_session_is_valid(self):
        """Active session with future expiration is valid."""
        session = Session(
            id="test-id",
            user_id=uuid4(),
            token_hash="hash",
            status=SessionStatus.ACTIVE,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert session.is_expired is False
        assert session.is_valid is True

    def test_session_revoked(self):
        """Revoked session is not valid."""
        session = Session(
            id="test-id",
            user_id=uuid4(),
            token_hash="hash",
            status=SessionStatus.REVOKED,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        assert session.is_valid is False

    def test_session_to_dict(self):
        """Session converts to dictionary."""
        user_id = uuid4()
        session = Session(
            id="test-id",
            user_id=user_id,
            token_hash="hash",
            client_info=ClientInfo(ip_address="127.0.0.1"),
        )

        data = session.to_dict()

        assert data["id"] == "test-id"
        assert data["user_id"] == str(user_id)
        assert data["status"] == "active"
        assert data["client_ip"] == "127.0.0.1"


__all__ = [
    "TestSessionCreation",
    "TestSessionValidation",
    "TestSessionInvalidation",
    "TestSessionManagement",
    "TestSessionStatus",
]

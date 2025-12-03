"""
Tests for auth REST API router.

Tests cover:
- Login endpoint (success, rate limiting, error handling)
- Token refresh endpoint
- Logout endpoint
- Current user endpoint (GET /me)
- API key validation
- Rate limiting behavior

Test Patterns:
- SUCCESS: 200/201 responses with valid payloads
- ERROR: 400, 401, 403, 404, 429 responses
- EDGE CASES: rate limit edge cases, token expiration
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from casare_rpa.infrastructure.orchestrator.api.routers.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    UserInfoResponse,
    LogoutResponse,
    router,
    _login_attempts,
    _check_rate_limit,
    _record_login_attempt,
    _get_client_ip,
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    LOGIN_RATE_LIMIT_LOCKOUT_SECONDS,
)
from casare_rpa.infrastructure.orchestrator.api.auth import (
    get_current_user,
    verify_token,
    AuthenticatedUser,
    create_access_token,
    create_refresh_token,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
)


# ============================================================================
# Test Constants
# ============================================================================

TEST_USER_ID = "test-user-001"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword"
TEST_TENANT_ID = "test-tenant"
TEST_IP = "192.168.1.100"


# ============================================================================
# Mock Authentication
# ============================================================================


def get_mock_current_user() -> AuthenticatedUser:
    """Return a mock authenticated user for testing."""
    return AuthenticatedUser(
        user_id=TEST_USER_ID,
        roles=["admin", "developer"],
        tenant_id=TEST_TENANT_ID,
        dev_mode=True,
    )


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_user() -> AuthenticatedUser:
    """Mock authenticated user for direct function calls."""
    return get_mock_current_user()


@pytest.fixture
def client() -> TestClient:
    """Create FastAPI test client with mocked authentication."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")

    # Override authentication dependency for protected endpoints
    app.dependency_overrides[get_current_user] = get_mock_current_user

    return TestClient(app)


@pytest.fixture
def client_no_auth_override() -> TestClient:
    """Create FastAPI test client without auth override (for testing auth flow)."""
    app = FastAPI()
    app.include_router(router, prefix="/auth")
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit tracking before each test."""
    _login_attempts.clear()
    yield
    _login_attempts.clear()


@pytest.fixture
def valid_access_token() -> str:
    """Create a valid access token for testing."""
    return create_access_token(
        user_id=TEST_USER_ID,
        roles=["admin", "developer"],
        tenant_id=TEST_TENANT_ID,
    )


@pytest.fixture
def valid_refresh_token() -> str:
    """Create a valid refresh token for testing."""
    return create_refresh_token(
        user_id=TEST_USER_ID,
        tenant_id=TEST_TENANT_ID,
    )


@pytest.fixture
def expired_token() -> str:
    """Create an expired token for testing."""
    return create_access_token(
        user_id=TEST_USER_ID,
        roles=["admin"],
        expires_delta=timedelta(seconds=-1),  # Already expired
    )


# ============================================================================
# Request Model Validation Tests
# ============================================================================


class TestLoginRequestValidation:
    """Tests for LoginRequest model validation."""

    def test_valid_request(self) -> None:
        """Test valid login request passes validation."""
        request = LoginRequest(username="user", password="pass")
        assert request.username == "user"
        assert request.password == "pass"
        assert request.tenant_id is None

    def test_with_tenant_id(self) -> None:
        """Test login request with tenant_id."""
        request = LoginRequest(
            username="user",
            password="pass",
            tenant_id="tenant-123",
        )
        assert request.tenant_id == "tenant-123"

    def test_empty_username_fails(self) -> None:
        """Test empty username fails validation."""
        with pytest.raises(ValueError):
            LoginRequest(username="", password="pass")

    def test_empty_password_fails(self) -> None:
        """Test empty password fails validation."""
        with pytest.raises(ValueError):
            LoginRequest(username="user", password="")


class TestRefreshRequestValidation:
    """Tests for RefreshRequest model validation."""

    def test_valid_request(self) -> None:
        """Test valid refresh request."""
        request = RefreshRequest(refresh_token="token123")
        assert request.refresh_token == "token123"


# ============================================================================
# Rate Limiting Tests
# ============================================================================


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_check_rate_limit_first_attempt_allowed(self) -> None:
        """Test first attempt is always allowed."""
        is_allowed, retry_after = _check_rate_limit(TEST_IP)
        assert is_allowed is True
        assert retry_after is None

    def test_check_rate_limit_under_threshold_allowed(self) -> None:
        """Test attempts under threshold are allowed."""
        # Record some failed attempts
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS - 1):
            _record_login_attempt(TEST_IP, success=False)

        is_allowed, retry_after = _check_rate_limit(TEST_IP)
        assert is_allowed is True
        assert retry_after is None

    def test_check_rate_limit_at_threshold_blocked(self) -> None:
        """Test attempts at threshold trigger lockout."""
        # Record max failed attempts
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            _record_login_attempt(TEST_IP, success=False)

        is_allowed, retry_after = _check_rate_limit(TEST_IP)
        assert is_allowed is False
        assert retry_after == LOGIN_RATE_LIMIT_LOCKOUT_SECONDS

    def test_record_login_attempt_success_resets(self) -> None:
        """Test successful login resets attempt counter."""
        # Record some failed attempts
        for _ in range(3):
            _record_login_attempt(TEST_IP, success=False)

        # Verify attempts were recorded
        attempts, _, _ = _login_attempts[TEST_IP]
        assert attempts == 3

        # Successful login should reset
        _record_login_attempt(TEST_IP, success=True)
        attempts, _, _ = _login_attempts[TEST_IP]
        assert attempts == 0

    def test_get_client_ip_direct(self) -> None:
        """Test client IP extraction from direct connection."""
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "10.0.0.1"

        ip = _get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_get_client_ip_forwarded_for(self) -> None:
        """Test client IP extraction from X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            "203.0.113.50, 70.41.3.18" if h == "X-Forwarded-For" else None
        )

        ip = _get_client_ip(mock_request)
        assert ip == "203.0.113.50"

    def test_get_client_ip_real_ip(self) -> None:
        """Test client IP extraction from X-Real-IP header."""
        mock_request = MagicMock()
        mock_request.headers.get.side_effect = lambda h: (
            "192.0.2.1" if h == "X-Real-IP" else None
        )

        ip = _get_client_ip(mock_request)
        assert ip == "192.0.2.1"


# ============================================================================
# Login Endpoint Tests
# ============================================================================


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    def test_login_success_dev_mode(self, client: TestClient) -> None:
        """Test successful login in dev mode."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            response = client.post(
                "/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600

    def test_login_returns_valid_jwt(self, client: TestClient) -> None:
        """Test login returns decodable JWT tokens."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            response = client.post(
                "/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

        data = response.json()
        # Decode and verify access token
        payload = jwt.decode(
            data["access_token"],
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        assert payload["sub"] == TEST_USERNAME
        assert payload["type"] == "access"
        assert "admin" in payload["roles"]

    def test_login_with_tenant_id(self, client: TestClient) -> None:
        """Test login with tenant_id included."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            response = client.post(
                "/auth/login",
                json={
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD,
                    "tenant_id": TEST_TENANT_ID,
                },
            )

        assert response.status_code == 200
        data = response.json()

        # Verify tenant_id is in token
        payload = jwt.decode(
            data["access_token"],
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        assert payload["tenant_id"] == TEST_TENANT_ID

    def test_login_rate_limited(self, client: TestClient) -> None:
        """Test login rate limiting returns 429."""
        # Exhaust rate limit
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            _record_login_attempt(TEST_IP, success=False)

        # Set the IP in test client
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth._get_client_ip",
            return_value=TEST_IP,
        ):
            response = client.post(
                "/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert "Too many login attempts" in response.json()["detail"]

    def test_login_invalid_json(self, client: TestClient) -> None:
        """Test login with invalid JSON returns 422."""
        response = client.post(
            "/auth/login",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_login_missing_fields(self, client: TestClient) -> None:
        """Test login with missing fields returns 422."""
        response = client.post(
            "/auth/login",
            json={"username": TEST_USERNAME},  # Missing password
        )
        assert response.status_code == 422


# ============================================================================
# Token Refresh Endpoint Tests
# ============================================================================


class TestRefreshEndpoint:
    """Tests for POST /auth/refresh endpoint."""

    def test_refresh_success(
        self, client: TestClient, valid_refresh_token: str
    ) -> None:
        """Test successful token refresh."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": valid_refresh_token},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["expires_in"] == 3600

    def test_refresh_with_expired_token(self, client: TestClient) -> None:
        """Test refresh with expired token returns 401."""
        # Create an expired refresh token
        expired_refresh = create_refresh_token(
            user_id=TEST_USER_ID,
            expires_delta=timedelta(seconds=-1),
        )

        response = client.post(
            "/auth/refresh",
            json={"refresh_token": expired_refresh},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_refresh_with_invalid_token(self, client: TestClient) -> None:
        """Test refresh with invalid token returns 401."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    def test_refresh_with_access_token_fails(
        self, client: TestClient, valid_access_token: str
    ) -> None:
        """Test refresh with access token (wrong type) returns 400."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": valid_access_token},
        )

        assert response.status_code == 400
        assert "Invalid token type" in response.json()["detail"]

    def test_refresh_rate_limited(self, client: TestClient) -> None:
        """Test refresh endpoint is rate limited."""
        # Exhaust rate limit
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            _record_login_attempt(TEST_IP, success=False)

        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth._get_client_ip",
            return_value=TEST_IP,
        ):
            response = client.post(
                "/auth/refresh",
                json={"refresh_token": "any-token"},
            )

        assert response.status_code == 429


# ============================================================================
# Logout Endpoint Tests
# ============================================================================


class TestLogoutEndpoint:
    """Tests for POST /auth/logout endpoint."""

    def test_logout_success(self, client: TestClient) -> None:
        """Test successful logout."""
        response = client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    def test_logout_unauthenticated(self, client_no_auth_override: TestClient) -> None:
        """Test logout without authentication fails."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.auth.JWT_DEV_MODE",
            False,
        ):
            response = client_no_auth_override.post("/auth/logout")
            # Should fail because no token provided
            assert response.status_code == 401


# ============================================================================
# Get Current User Endpoint Tests
# ============================================================================


class TestGetMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    def test_get_me_success(self, client: TestClient) -> None:
        """Test successful user info retrieval."""
        response = client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == TEST_USER_ID
        assert "admin" in data["roles"]
        assert data["tenant_id"] == TEST_TENANT_ID
        assert data["dev_mode"] is True

    def test_get_me_with_valid_token(
        self, client_no_auth_override: TestClient, valid_access_token: str
    ) -> None:
        """Test user info with valid bearer token."""
        response = client_no_auth_override.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {valid_access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == TEST_USER_ID

    def test_get_me_unauthenticated(self, client_no_auth_override: TestClient) -> None:
        """Test user info without authentication fails."""
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.auth.JWT_DEV_MODE",
            False,
        ):
            response = client_no_auth_override.get("/auth/me")
            assert response.status_code == 401

    def test_get_me_with_expired_token(
        self, client_no_auth_override: TestClient, expired_token: str
    ) -> None:
        """Test user info with expired token fails."""
        response = client_no_auth_override.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401


# ============================================================================
# Integration Tests
# ============================================================================


class TestAuthIntegration:
    """Integration tests for full auth flows."""

    def test_login_then_access_protected_endpoint(self, client: TestClient) -> None:
        """Test login flow and accessing protected endpoint."""
        # Login
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            login_response = client.post(
                "/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )

        assert login_response.status_code == 200
        tokens = login_response.json()

        # Access protected endpoint with token
        # Note: Client fixture overrides auth, so this tests the flow
        me_response = client.get("/auth/me")
        assert me_response.status_code == 200

    def test_login_refresh_logout_flow(self, client: TestClient) -> None:
        """Test complete authentication lifecycle."""
        # 1. Login
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            login_response = client.post(
                "/auth/login",
                json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # 2. Refresh token
        with patch(
            "casare_rpa.infrastructure.orchestrator.api.routers.auth.JWT_DEV_MODE",
            True,
        ):
            refresh_response = client.post(
                "/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            )
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        # Note: Tokens may be identical if generated in same second (same timestamp)
        # The important thing is that both operations succeed
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

        # 3. Logout
        logout_response = client.post("/auth/logout")
        assert logout_response.status_code == 200

    def test_rate_limit_recovery_after_window(self) -> None:
        """Test rate limit resets after window expires."""
        # Exhaust rate limit
        for _ in range(LOGIN_RATE_LIMIT_MAX_ATTEMPTS):
            _record_login_attempt(TEST_IP, success=False)

        # Verify blocked
        is_allowed, _ = _check_rate_limit(TEST_IP)
        assert is_allowed is False

        # Simulate window expiration by modifying the timestamp
        attempts, window_start, lockout_until = _login_attempts[TEST_IP]
        _login_attempts[TEST_IP] = (
            attempts,
            window_start - LOGIN_RATE_LIMIT_WINDOW_SECONDS - 1,
            None,  # Clear lockout
        )

        # Should be allowed now
        is_allowed, _ = _check_rate_limit(TEST_IP)
        assert is_allowed is True

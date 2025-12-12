"""
CasareRPA Infrastructure - Authentication.

Comprehensive authentication and session management:
- Robot API keys for robot-to-orchestrator auth
- User authentication with password hashing
- JWT token management
- TOTP-based MFA
- Session management with timeouts

Usage:
    from casare_rpa.infrastructure.auth import (
        # Robot API Keys
        RobotApiKeyService,
        RobotApiKey,
        # User Authentication
        UserManager,
        AuthenticationResult,
        # JWT Tokens
        TokenManager,
        TokenPayload,
        # MFA
        TOTPManager,
        # Sessions
        SessionManager,
        SessionConfig,
    )
"""

# Robot API Keys
from casare_rpa.infrastructure.auth.robot_api_keys import (
    ApiKeyValidationResult,
    RobotApiKey,
    RobotApiKeyError,
    RobotApiKeyService,
    generate_api_key_raw,
    hash_api_key,
)

# TOTP Manager
from casare_rpa.infrastructure.auth.totp_manager import (
    TOTPManager,
    TOTPError,
    InvalidSecretError,
    InvalidCodeError,
)

# Token Manager
from casare_rpa.infrastructure.auth.token_manager import (
    TokenManager,
    TokenConfig,
    TokenPayload,
    TokenType,
    TokenError,
    TokenExpiredError,
    TokenInvalidError,
    TokenRevokedError,
    generate_secret_key,
)

# User Manager
from casare_rpa.infrastructure.auth.user_manager import (
    UserManager,
    UserManagerError,
    UserNotFoundError,
    UserExistsError,
    InvalidPasswordError,
    InvalidEmailError,
    AccountLockedError,
    AuthenticationResult,
    AuthResult,
    PasswordPolicy,
)

# Session Manager
from casare_rpa.infrastructure.auth.session_manager import (
    SessionManager,
    SessionConfig,
    Session,
    SessionStatus,
    ClientInfo,
    SessionError,
    SessionNotFoundError,
    SessionExpiredError,
    SessionLimitExceededError,
)

__all__ = [
    # Robot API Keys
    "RobotApiKey",
    "RobotApiKeyService",
    "RobotApiKeyError",
    "ApiKeyValidationResult",
    "generate_api_key_raw",
    "hash_api_key",
    # TOTP Manager
    "TOTPManager",
    "TOTPError",
    "InvalidSecretError",
    "InvalidCodeError",
    # Token Manager
    "TokenManager",
    "TokenConfig",
    "TokenPayload",
    "TokenType",
    "TokenError",
    "TokenExpiredError",
    "TokenInvalidError",
    "TokenRevokedError",
    "generate_secret_key",
    # User Manager
    "UserManager",
    "UserManagerError",
    "UserNotFoundError",
    "UserExistsError",
    "InvalidPasswordError",
    "InvalidEmailError",
    "AccountLockedError",
    "AuthenticationResult",
    "AuthResult",
    "PasswordPolicy",
    # Session Manager
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

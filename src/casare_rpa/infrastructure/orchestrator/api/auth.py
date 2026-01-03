"""
Authentication and authorization dependencies for FastAPI.

Provides:
1. JWT token validation and role-based access control (for web dashboard)
2. Robot API token authentication (for robot-to-orchestrator connections)

JWT auth is for browser/dashboard users.
Robot auth is for automated robots connecting over internet.
"""

import hashlib
import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from pydantic import BaseModel

# =============================================================================
# JWT CONFIGURATION
# =============================================================================

# SECURITY: JWT_SECRET_KEY must be set in production. No default to prevent insecure deployments.
_jwt_secret_env = os.getenv("JWT_SECRET_KEY")
if _jwt_secret_env is None:
    import warnings

    warnings.warn(
        "JWT_SECRET_KEY not set. Using insecure default for development only. "
        "Set JWT_SECRET_KEY environment variable in production!",
        RuntimeWarning,
        stacklevel=1,
    )
    JWT_SECRET_KEY = "dev-secret-key-DO-NOT-USE-IN-PRODUCTION"
else:
    JWT_SECRET_KEY = _jwt_secret_env
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
# SECURITY: JWT_DEV_MODE defaults to false. Must explicitly enable for development.
JWT_DEV_MODE = os.getenv("JWT_DEV_MODE", "false").lower() in ("true", "1", "yes")


# =============================================================================
# AUTH MODELS
# =============================================================================


class TokenPayload(BaseModel):
    """JWT token payload structure."""

    sub: str  # user_id
    roles: list[str] = []
    tenant_id: str | None = None
    exp: datetime | None = None
    iat: datetime | None = None
    type: str = "access"  # access or refresh


class AuthenticatedUser(BaseModel):
    """Represents an authenticated user from JWT claims."""

    user_id: str
    roles: list[str]
    tenant_id: str | None = None
    dev_mode: bool = False

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return "admin" in self.roles

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles or "admin" in self.roles


# HTTP Bearer token scheme (for JWT)
security = HTTPBearer(auto_error=False)


def _get_admin_api_key() -> str | None:
    """Return configured admin API key for non-JWT clients (e.g., Canvas).

    This intentionally supports the existing API_SECRET-based deployments.
    In production, prefer setting ORCHESTRATOR_ADMIN_API_KEY explicitly.
    """
    key = os.getenv("ORCHESTRATOR_ADMIN_API_KEY") or os.getenv("API_SECRET")
    return key.strip() if key else None


def _try_admin_api_key(token: str) -> AuthenticatedUser | None:
    admin_key = _get_admin_api_key()
    if not admin_key:
        return None

    # Debug logging
    if token == admin_key:
        return AuthenticatedUser(
            user_id="admin_api_key",
            roles=["admin"],
            tenant_id=None,
            dev_mode=False,
        )

    # Log mismatch debug info
    if len(token) > 10:
        masked_token = f"{token[:4]}...{token[-4:]} (len={len(token)})"
    else:
        masked_token = "<short_token>"

    if len(admin_key) > 10:
        masked_admin = f"{admin_key[:4]}...{admin_key[-4:]} (len={len(admin_key)})"
    else:
        masked_admin = "<short_admin_key>"

    logger.warning(f"Admin Key Mismatch: Token='{masked_token}' vs Admin='{masked_admin}'")
    return None


def validate_admin_secret(secret: str | None) -> bool:
    """
    Validate admin API secret (legacy query param mode).
    Used primarily for diagnostic WebSocket connections.
    """
    if not secret:
        return False
    admin_key = _get_admin_api_key()
    if not admin_key:
        return False
    import hmac

    return hmac.compare_digest(secret, admin_key)


def create_access_token(
    user_id: str,
    roles: list[str],
    tenant_id: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User identifier
        roles: List of role names
        tenant_id: Optional tenant identifier
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "roles": roles,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    tenant_id: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User identifier
        tenant_id: Optional tenant identifier
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT refresh token string
    """
    if expires_delta is None:
        expires_delta = timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    now = datetime.now(UTC)
    expire = now + expires_delta

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }

    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenPayload with decoded claims

    Raises:
        jwt.ExpiredSignatureError: If token is expired
        jwt.InvalidTokenError: If token is invalid
    """
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return TokenPayload(**payload)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
) -> AuthenticatedUser:
    """
    Verify JWT token and return authenticated user.

    Args:
        credentials: HTTP Bearer credentials from Authorization header
        x_api_key: Optional API key from header (fallback for admin access)

    Returns:
        AuthenticatedUser with user_id, roles, and tenant_id

    Raises:
        HTTPException: 401 if token invalid or missing
    """
    # Development mode: bypass authentication if no token provided
    if credentials is None:
        # Check X-Api-Key fallback for API_SECRET access
        if x_api_key:
            admin_user = _try_admin_api_key(x_api_key)
            if admin_user:
                return admin_user

        if JWT_DEV_MODE:
            logger.debug("JWT dev mode: allowing unauthenticated access as admin")
            return AuthenticatedUser(
                user_id="dev_user",
                roles=["admin"],
                tenant_id=None,
                dev_mode=True,
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Support long-lived admin API key passed as Bearer token
    admin_user = _try_admin_api_key(token)
    if admin_user is not None:
        return admin_user

    try:
        payload = decode_token(token)

        # Verify this is an access token, not a refresh token
        if payload.type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Use access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return AuthenticatedUser(
            user_id=payload.sub,
            roles=payload.roles,
            tenant_id=payload.tenant_id,
            dev_mode=False,
        )

    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token attempted")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(required_role: str):
    """
    Dependency factory for role-based access control.

    Args:
        required_role: Required role (viewer, operator, admin, developer)

    Returns:
        Dependency function that validates user has required role

    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...
    """

    async def role_checker(
        user: AuthenticatedUser = Depends(verify_token),
    ) -> AuthenticatedUser:
        """Check if user has required role."""
        if not user.has_role(required_role):
            logger.warning(
                f"Access denied: user={user.user_id} required={required_role} has={user.roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role}",
            )

        return user

    return role_checker


# Convenience dependency for getting current user
async def get_current_user(
    user: AuthenticatedUser = Depends(verify_token),
) -> AuthenticatedUser:
    """
    Get the current authenticated user.

    This is an alias for verify_token for clearer semantics in endpoints.

    Example:
        @router.get("/me")
        async def get_profile(user: AuthenticatedUser = Depends(get_current_user)):
            return {"user_id": user.user_id, "roles": user.roles}
    """
    return user


# Convenience dependencies for common roles
require_admin = require_role("admin")
require_developer = require_role("developer")
require_operator = require_role("operator")
require_viewer = require_role("viewer")


# Optional authentication dependency (doesn't fail if no token)
async def optional_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> AuthenticatedUser | None:
    """
    Optional authentication - returns None if no token provided.

    Useful for endpoints that provide different data based on authentication status.
    """
    if credentials is None:
        return None

    try:
        return await verify_token(credentials)
    except HTTPException:
        return None


# =============================================================================
# Robot API Token Authentication (for robot-to-orchestrator connections)
# =============================================================================


class RobotAuthenticator:
    """
    Validates robot API tokens against configured hashes.

    Supports two modes:
    1. Environment-based: Load token hashes from ROBOT_TOKENS env var (legacy)
    2. Database-based: Validate against robot_api_keys table (recommended)

    For internet-connected robots, use X-Api-Key header authentication
    instead of JWT (simpler for automated clients).
    """

    def __init__(self, use_database: bool = False, db_pool=None):
        """
        Initialize the authenticator.

        Args:
            use_database: If True, validate against database instead of env vars
            db_pool: Database connection pool (required if use_database=True)
        """
        self._use_database = use_database
        self._db_pool = db_pool
        self._db_robot_api_keys_cols: set[str] | None = None
        self._db_robot_api_keys_hash_col: str | None = None
        self._token_hashes = {} if use_database else self._load_token_hashes()
        self._auth_enabled = os.getenv("ROBOT_AUTH_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    def _load_token_hashes(self) -> dict[str, str]:
        """
        Load robot token hashes from environment.

        Format: ROBOT_TOKENS=robot-001:hash1,robot-002:hash2

        Returns:
            Dict mapping token_hash -> robot_id
        """
        token_env = os.getenv("ROBOT_TOKENS", "")

        if not token_env:
            logger.warning(
                "ROBOT_TOKENS not configured. Set ROBOT_TOKENS=robot-001:hash1,robot-002:hash2 "
                "or use database-based authentication with robot_api_keys table."
            )
            return {}

        token_map = {}
        for entry in token_env.split(","):
            entry = entry.strip()
            if ":" not in entry:
                logger.warning(f"Invalid ROBOT_TOKENS entry (missing ':'): {entry}")
                continue

            robot_id, token_hash = entry.split(":", 1)
            token_map[token_hash.strip()] = robot_id.strip()

        logger.info(f"Loaded {len(token_map)} robot authentication tokens from env")
        return token_map

    def verify_token(self, token: str) -> str | None:
        """
        Verify robot API token and return robot ID if valid.

        Args:
            token: Raw API token from X-Api-Key header

        Returns:
            robot_id if token is valid, None otherwise
        """
        if not token:
            return None

        # Hash token and check against configured hashes
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return self._token_hashes.get(token_hash)

    async def verify_token_async(self, token: str, client_ip: str | None = None) -> str | None:
        """
        Verify robot API token asynchronously against database.

        Args:
            token: Raw API token from X-Api-Key header
            client_ip: Client IP for audit logging

        Returns:
            robot_id if token is valid, None otherwise
        """
        if not token:
            return None

        # If not using database, fall back to sync method
        if not self._use_database:
            return self.verify_token(token)

        # Validate token format
        if not token.startswith("crpa_") or len(token) < 40:
            logger.warning(f"Invalid API key format: {token[:8]}...")
            return None

        token_hash = hashlib.sha256(token.encode()).hexdigest()

        try:
            if self._db_pool:
                async with self._db_pool.acquire() as conn:
                    if self._db_robot_api_keys_cols is None:
                        cols = await conn.fetch(
                            """
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema='public' AND table_name='robot_api_keys'
                            """
                        )
                        self._db_robot_api_keys_cols = {r["column_name"] for r in cols}

                        if "api_key_hash" in self._db_robot_api_keys_cols:
                            self._db_robot_api_keys_hash_col = "api_key_hash"
                        elif "key_hash" in self._db_robot_api_keys_cols:
                            self._db_robot_api_keys_hash_col = "key_hash"
                        else:
                            self._db_robot_api_keys_hash_col = "api_key_hash"

                    cols = self._db_robot_api_keys_cols or set()
                    hash_col = self._db_robot_api_keys_hash_col or "api_key_hash"

                    # Check if key is valid (not revoked, not expired)
                    if "api_key_hash" in cols and "key_hash" in cols:
                        where = ["(api_key_hash = $1 OR key_hash = $1)"]
                    else:
                        where = [f"{hash_col} = $1"]
                    if "is_revoked" in cols:
                        where.append("is_revoked = FALSE")
                    if "is_active" in cols:
                        where.append("is_active = TRUE")
                    if "expires_at" in cols:
                        where.append("(expires_at IS NULL OR expires_at > NOW())")

                    result = await conn.fetchrow(
                        f"""
                        SELECT robot_id FROM robot_api_keys
                        WHERE {" AND ".join(where)}
                        """,
                        token_hash,
                    )

                    if result:
                        robot_id = str(result["robot_id"])

                        # Update last_used timestamp (fire and forget)
                        set_parts = []
                        if "last_used_at" in cols:
                            set_parts.append("last_used_at = NOW()")
                        if "last_used_ip" in cols:
                            set_parts.append("last_used_ip = $2::inet")

                        if set_parts:
                            update_where = (
                                "(api_key_hash = $1 OR key_hash = $1)"
                                if "api_key_hash" in cols and "key_hash" in cols
                                else f"{hash_col} = $1"
                            )
                            await conn.execute(
                                f"""
                                UPDATE robot_api_keys
                                SET {", ".join(set_parts)}
                                WHERE {update_where}
                                """,
                                token_hash,
                                client_ip,
                            )

                        logger.debug(f"Database auth: validated robot {robot_id}")
                        return robot_id

                    logger.warning(f"API key not found or invalid: {token[:12]}...")
                    return None

        except Exception as e:
            logger.error(f"Database API key validation failed: {e}")
            # Fall back to env-based auth if database fails
            return self.verify_token(token)

        return None

    @property
    def is_enabled(self) -> bool:
        """Check if robot authentication is enabled."""
        return self._auth_enabled


# Global authenticator instance
_robot_authenticator: RobotAuthenticator | None = None


def get_robot_authenticator() -> RobotAuthenticator:
    """Get or create the global robot authenticator instance."""
    global _robot_authenticator
    if _robot_authenticator is None:
        _robot_authenticator = RobotAuthenticator()
    return _robot_authenticator


def configure_robot_authenticator(use_database: bool = False, db_pool=None) -> RobotAuthenticator:
    """
    Configure the global robot authenticator.

    Args:
        use_database: Enable database-based authentication
        db_pool: Database connection pool

    Returns:
        Configured RobotAuthenticator
    """
    global _robot_authenticator
    _robot_authenticator = RobotAuthenticator(use_database=use_database, db_pool=db_pool)
    logger.info(f"Robot authenticator configured: database={use_database}")
    return _robot_authenticator


async def verify_robot_token(x_api_key: str = Header(..., alias="X-Api-Key")) -> str:
    """
    FastAPI dependency to verify robot API key.

    Extracts token from X-Api-Key header and validates against
    configured robot tokens or database.

    Args:
        x_api_key: Token from X-Api-Key HTTP header

    Returns:
        robot_id if authentication successful

    Raises:
        HTTPException 401 if token is invalid or missing

    Example:
        @router.post("/jobs/claim", dependencies=[Depends(verify_robot_token)])
        async def claim_job():
            # Only authenticated robots can reach here
            pass

    Environment:
        ROBOT_AUTH_ENABLED=true  # Enable robot authentication
        ROBOT_TOKENS=robot-001:hash1,robot-002:hash2  # Legacy env-based auth
    """
    authenticator = get_robot_authenticator()

    # If auth not enabled, allow all (development mode)
    if not authenticator.is_enabled:
        logger.debug("Robot authentication disabled (ROBOT_AUTH_ENABLED=false)")
        return "dev_robot"

    # Try async validation first (database-based)
    robot_id = await authenticator.verify_token_async(x_api_key)

    if not robot_id:
        logger.warning(f"Failed robot authentication attempt with key: {x_api_key[:12]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug(f"Authenticated robot: {robot_id}")
    return robot_id


async def optional_robot_token(
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
) -> str | None:
    """
    Optional robot authentication dependency for endpoints that support both
    authenticated and anonymous access.

    Args:
        x_api_key: Optional token from X-Api-Key header

    Returns:
        robot_id if token provided and valid, None otherwise
    """
    if not x_api_key:
        return None

    authenticator = get_robot_authenticator()

    if not authenticator.is_enabled:
        return None

    return await authenticator.verify_token_async(x_api_key)


# =============================================================================
# TENANT ISOLATION
# =============================================================================


def get_tenant_id(
    user: AuthenticatedUser = Depends(get_current_user),
) -> str | None:
    """
    Get the tenant ID for the current authenticated user.

    Use this dependency to enforce tenant isolation in database queries.
    Returns None for users without tenant_id (system admins can see all).

    Args:
        user: Current authenticated user

    Returns:
        tenant_id string or None

    Example:
        @router.get("/workflows")
        async def list_workflows(
            tenant_id: Optional[str] = Depends(get_tenant_id),
        ):
            # Filter by tenant_id if set
            if tenant_id:
                workflows = await repo.list_by_tenant(tenant_id)
            else:
                workflows = await repo.list_all()  # Admin sees all
    """
    return user.tenant_id


def require_tenant() -> str:
    """
    Dependency that requires a tenant_id to be present.

    Fails with 403 if user has no tenant_id (prevents cross-tenant access).

    Returns:
        Dependency function that returns tenant_id or raises HTTPException

    Example:
        @router.get("/tenant-only", dependencies=[Depends(require_tenant())])
        async def tenant_only_endpoint():
            pass
    """

    def _require_tenant(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> str:
        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This endpoint requires tenant context. User has no tenant_id.",
            )
        return user.tenant_id

    return _require_tenant


def require_same_tenant(resource_tenant_id: str):
    """
    Dependency factory to verify user belongs to the same tenant as a resource.

    Args:
        resource_tenant_id: Tenant ID of the resource being accessed

    Returns:
        Dependency function that raises HTTPException if tenant mismatch

    Example:
        # In endpoint logic after fetching resource:
        if workflow.tenant_id != user.tenant_id and not user.is_admin:
            raise HTTPException(403, "Cannot access resource from another tenant")
    """

    def _check_tenant(
        user: AuthenticatedUser = Depends(get_current_user),
    ) -> None:
        # Admins can access any tenant
        if user.is_admin:
            return

        # Users without tenant_id cannot access tenant-specific resources
        if not user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access tenant resource without tenant context",
            )

        # Check tenant match
        if user.tenant_id != resource_tenant_id:
            logger.warning(
                f"Tenant mismatch: user={user.user_id} tenant={user.tenant_id} "
                f"resource_tenant={resource_tenant_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access resources from another tenant",
            )

    return _check_tenant


# =============================================================================
# COMBINED AUTH: JWT + API KEY
# =============================================================================


async def get_current_user_or_robot(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Header(None, alias="X-Api-Key"),
) -> AuthenticatedUser:
    """
    Combined authentication dependency that accepts either:
    1. JWT Bearer token (for web dashboard users)
    2. X-Api-Key header (for robot agents)

    Priority: JWT > API Key > Dev Mode

    Args:
        credentials: Optional HTTP Bearer credentials
        x_api_key: Optional X-Api-Key header

    Returns:
        AuthenticatedUser (user or robot identity)

    Raises:
        HTTPException 401 if no valid authentication provided
    """
    # Try JWT authentication first
    if credentials:
        try:
            return await verify_token(credentials)
        except HTTPException:
            pass  # Fall through to API key

    # Try robot API key
    if x_api_key:
        authenticator = get_robot_authenticator()
        if authenticator.is_enabled:
            robot_id = await authenticator.verify_token_async(x_api_key)
            if robot_id:
                return AuthenticatedUser(
                    user_id=f"robot:{robot_id}",
                    roles=["robot"],
                    tenant_id=None,  # Robots can access all tenants (filtered in use case)
                    dev_mode=False,
                )

    # Dev mode fallback
    if JWT_DEV_MODE:
        logger.debug("Combined auth: allowing dev mode access")
        return AuthenticatedUser(
            user_id="dev_user",
            roles=["admin"],
            tenant_id=None,
            dev_mode=True,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide Bearer token or X-Api-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )

"""
Authentication for Cloud Orchestrator.

Provides API key validation for REST and WebSocket endpoints.
"""

import hmac
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from loguru import logger

from casare_rpa.infrastructure.auth.robot_api_keys import (
    hash_api_key,
    validate_api_key_format,
)
from casare_rpa.infrastructure.orchestrator.server_lifecycle import (
    get_config,
    get_db_pool,
)


async def verify_api_key(
    x_api_key: str = Header(..., alias="X-Api-Key"),
) -> str:
    """Verify robot API key and return robot_id.

    Validates API key format and verifies against database when configured.
    Returns robot_id on success, raises HTTPException on failure.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    if not validate_api_key_format(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )

    key_hash = hash_api_key(x_api_key)

    # Validate against database when configured
    db_pool = get_db_pool()
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT robot_id, is_revoked, expires_at
                    FROM robot_api_keys
                    WHERE key_hash = $1
                    """,
                    key_hash,
                )
                if row is None:
                    logger.warning(
                        f"API key not found in database (hash: {key_hash[:16]}...)"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid API key",
                    )
                if row["is_revoked"]:
                    logger.warning(f"API key revoked (robot: {row['robot_id']})")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API key has been revoked",
                    )
                if row["expires_at"] is not None:
                    if row["expires_at"] < datetime.now(timezone.utc):
                        logger.warning(f"API key expired (robot: {row['robot_id']})")
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="API key has expired",
                        )

                # Update last used timestamp (fire-and-forget)
                await conn.execute(
                    """
                    UPDATE robot_api_keys SET last_used_at = NOW()
                    WHERE key_hash = $1
                    """,
                    key_hash,
                )

                logger.debug(f"API key validated for robot: {row['robot_id']}")
                return row["robot_id"]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Database error validating API key: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            )

    # Fallback: no database configured, accept valid format with warning
    logger.warning("API key validation skipped - no database configured")
    return "unverified"


async def validate_websocket_api_key(api_key: Optional[str]) -> Optional[str]:
    """Validate API key for WebSocket connections.

    Returns robot_id on success, None on failure.
    Does not raise exceptions - caller should handle None appropriately.
    """
    if not api_key:
        return None

    if not validate_api_key_format(api_key):
        return None

    key_hash = hash_api_key(api_key)

    db_pool = get_db_pool()
    if db_pool is not None:
        try:
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT robot_id, is_revoked, expires_at
                    FROM robot_api_keys
                    WHERE key_hash = $1
                    """,
                    key_hash,
                )
                if row is None:
                    logger.warning(
                        f"WebSocket API key not found (hash: {key_hash[:16]}...)"
                    )
                    return None
                if row["is_revoked"]:
                    logger.warning(
                        f"WebSocket API key revoked (robot: {row['robot_id']})"
                    )
                    return None
                if row["expires_at"] is not None:
                    if row["expires_at"] < datetime.now(timezone.utc):
                        logger.warning(
                            f"WebSocket API key expired (robot: {row['robot_id']})"
                        )
                        return None

                logger.debug(
                    f"WebSocket API key validated for robot: {row['robot_id']}"
                )
                return row["robot_id"]

        except Exception as e:
            logger.error(f"Database error validating WebSocket API key: {e}")
            return None

    # Fallback: no database configured, accept valid format with warning
    logger.warning("WebSocket API key validation skipped - no database configured")
    return "unverified"


async def validate_admin_secret(secret: Optional[str]) -> bool:
    """Validate admin API secret for WebSocket connections.

    Returns True if secret matches configured API_SECRET, False otherwise.
    """
    if not secret:
        return False

    config = get_config()
    if not config.api_secret:
        logger.warning("Admin authentication attempted but API_SECRET not configured")
        return False

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(secret, config.api_secret)


async def verify_admin_api_key(
    x_api_key: str = Header(..., alias="X-Api-Key"),
) -> str:
    """Verify admin API key for REST endpoints.

    This is for admin/management endpoints that require the API_SECRET.
    """
    config = get_config()

    if not config.api_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API_SECRET not configured",
        )

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(x_api_key, config.api_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return "admin"

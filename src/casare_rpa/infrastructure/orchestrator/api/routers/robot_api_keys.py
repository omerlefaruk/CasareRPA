"""REST API endpoints for robot API key management.

These endpoints back the Canvas Fleet Dashboard "API Keys" tab.

Security:
- Admin only. (Bearer JWT access token OR configured admin API key)
- Robot agents should authenticate with X-Api-Key, not use these endpoints.
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from loguru import logger
from pydantic import BaseModel, Field

from casare_rpa.infrastructure.orchestrator.api.auth import (
    AuthenticatedUser,
    require_admin,
)

router = APIRouter()

# Module-level database pool reference (asyncpg.Pool)
_db_pool = None


def set_db_pool(pool) -> None:
    global _db_pool
    _db_pool = pool
    logger.debug("Database pool set for robot_api_keys router")


def get_db_pool():
    return _db_pool


def _require_db_pool():
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")
    return pool


async def _ensure_table_exists(pool, table_name: str) -> None:
    try:
        async with pool.acquire() as conn:
            exists = await conn.fetchval("SELECT to_regclass($1)", table_name)
            if exists is None:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"Required table '{table_name}' not found. "
                        "Run database migrations (deploy/migrations)."
                    ),
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed checking table existence ({table_name}): {e}")
        raise HTTPException(status_code=503, detail="Database schema check failed") from e


def _generate_raw_api_key() -> str:
    # Must satisfy RobotAuthenticator format check: startswith crpa_ and len>=40
    return f"crpa_{uuid.uuid4().hex}_{secrets.token_urlsafe(24)}"


def _hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


class CreateRobotApiKeyRequest(BaseModel):
    robot_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    expires_at: datetime | None = None


class RobotApiKeyResponse(BaseModel):
    id: str
    robot_id: str
    robot_name: str | None = None
    key_name: str | None = None
    description: str | None = None
    status: str
    created_at: datetime | None = None
    expires_at: datetime | None = None
    last_used_at: datetime | None = None
    last_used_ip: str | None = None


class CreateRobotApiKeyResponse(BaseModel):
    api_key: str
    key: RobotApiKeyResponse


class RobotApiKeyListResponse(BaseModel):
    keys: list[RobotApiKeyResponse]
    total: int


class RevokeRobotApiKeyRequest(BaseModel):
    reason: str | None = Field(None, max_length=2000)


@router.get(
    "/robot-api-keys",
    response_model=RobotApiKeyListResponse,
    dependencies=[Depends(require_admin)],
)
async def list_robot_api_keys(
    request: Request,
    robot_id: str | None = Query(None, description="Filter by robot ID"),
    status_filter: str | None = Query(
        None, alias="status", description="Filter by status: active|revoked|expired"
    ),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: AuthenticatedUser = Depends(require_admin),
) -> RobotApiKeyListResponse:
    del request
    del user

    pool = _require_db_pool()
    await _ensure_table_exists(pool, "robot_api_keys")

    where = ["1=1"]
    params: list[Any] = []
    idx = 1

    if robot_id:
        where.append(f"k.robot_id = ${idx}")
        params.append(robot_id)
        idx += 1

    try:
        async with pool.acquire() as conn:
            # Be robust to older/partial schemas by selecting missing columns as NULL/defaults.
            cols = await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'robot_api_keys'
                """
            )
            colset = {r["column_name"] for r in cols}

            has_description = "description" in colset
            has_is_revoked = "is_revoked" in colset
            has_revoked_at = "revoked_at" in colset
            has_expires_at = "expires_at" in colset
            has_last_used_at = "last_used_at" in colset
            has_last_used_ip = "last_used_ip" in colset

            if status_filter:
                normalized = status_filter.lower()
                if normalized == "active":
                    if has_is_revoked:
                        where.append("k.is_revoked = FALSE")
                    if has_expires_at:
                        where.append("(k.expires_at IS NULL OR k.expires_at > NOW())")
                elif normalized == "revoked":
                    if not has_is_revoked:
                        return RobotApiKeyListResponse(keys=[], total=0)
                    where.append("k.is_revoked = TRUE")
                elif normalized == "expired":
                    if has_is_revoked:
                        where.append("k.is_revoked = FALSE")
                    if has_expires_at:
                        where.append("k.expires_at IS NOT NULL AND k.expires_at <= NOW()")
                    else:
                        return RobotApiKeyListResponse(keys=[], total=0)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Invalid status filter. Use active|revoked|expired.",
                    )

            where_sql = " AND ".join(where)

            description_col = "k.description" if has_description else "NULL AS description"
            is_revoked_col = "k.is_revoked" if has_is_revoked else "FALSE AS is_revoked"
            revoked_at_col = "k.revoked_at" if has_revoked_at else "NULL AS revoked_at"
            expires_at_col = "k.expires_at" if has_expires_at else "NULL AS expires_at"
            last_used_at_col = "k.last_used_at" if has_last_used_at else "NULL AS last_used_at"
            last_used_ip_col = "k.last_used_ip" if has_last_used_ip else "NULL AS last_used_ip"

            total = await conn.fetchval(
                f"""
                SELECT COUNT(*)
                FROM robot_api_keys k
                JOIN robots r ON r.robot_id = k.robot_id
                WHERE {where_sql}
                """,
                *params,
            )

            rows = await conn.fetch(
                f"""
                SELECT
                    k.id,
                    k.robot_id,
                    r.name AS robot_name,
                    k.name AS key_name,
                    {description_col},
                    k.created_at,
                    {expires_at_col},
                    {last_used_at_col},
                    {last_used_ip_col},
                    {is_revoked_col},
                    {revoked_at_col}
                FROM robot_api_keys k
                JOIN robots r ON r.robot_id = k.robot_id
                WHERE {where_sql}
                ORDER BY k.created_at DESC
                LIMIT ${idx} OFFSET ${idx + 1}
                """,
                *params,
                limit,
                offset,
            )

        def to_status(row: dict[str, Any]) -> str:
            if row.get("is_revoked"):
                return "revoked"
            expires = row.get("expires_at")
            if expires is not None and expires <= datetime.utcnow().astimezone(expires.tzinfo):
                return "expired"
            return "active"

        keys = [
            RobotApiKeyResponse(
                id=str(r["id"]),
                robot_id=str(r["robot_id"]),
                robot_name=r.get("robot_name"),
                key_name=r.get("key_name"),
                description=r.get("description"),
                status=to_status(dict(r)),
                created_at=r.get("created_at"),
                expires_at=r.get("expires_at"),
                last_used_at=r.get("last_used_at"),
                last_used_ip=str(r.get("last_used_ip")) if r.get("last_used_ip") else None,
            )
            for r in rows
        ]

        return RobotApiKeyListResponse(keys=keys, total=int(total or 0))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list robot API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys") from e


@router.post(
    "/robot-api-keys",
    response_model=CreateRobotApiKeyResponse,
    dependencies=[Depends(require_admin)],
)
async def create_robot_api_key(
    request: Request,
    payload: CreateRobotApiKeyRequest,
    user: AuthenticatedUser = Depends(require_admin),
) -> CreateRobotApiKeyResponse:
    del request

    pool = _require_db_pool()
    await _ensure_table_exists(pool, "robot_api_keys")

    raw_key = _generate_raw_api_key()
    key_hash = _hash_api_key(raw_key)

    try:
        async with pool.acquire() as conn:
            cols = await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='robot_api_keys'
                """
            )
            colset = {r["column_name"] for r in cols}
            has_api_key_hash = "api_key_hash" in colset
            has_key_hash = "key_hash" in colset

            robot = await conn.fetchrow(
                "SELECT robot_id, name FROM robots WHERE robot_id = $1",
                payload.robot_id,
            )
            if not robot:
                raise HTTPException(status_code=404, detail="Robot not found")

            insert_cols = ["robot_id"]
            insert_vals = ["$1"]
            insert_params: list[Any] = [payload.robot_id]
            param_idx = 2

            # Support both schemas: some deployments use `key_hash`, newer ones use `api_key_hash`.
            if has_api_key_hash:
                insert_cols.append("api_key_hash")
                insert_vals.append(f"${param_idx}")
                insert_params.append(key_hash)
                param_idx += 1
            if has_key_hash:
                insert_cols.append("key_hash")
                insert_vals.append(f"${param_idx}")
                insert_params.append(key_hash)
                param_idx += 1

            insert_cols.extend(["name", "description", "expires_at", "created_by"])
            insert_vals.extend(
                [
                    f"${param_idx}",
                    f"${param_idx + 1}",
                    f"${param_idx + 2}",
                    f"${param_idx + 3}",
                ]
            )
            insert_params.extend(
                [payload.name, payload.description, payload.expires_at, user.user_id]
            )
            if "is_active" in colset:
                insert_cols.append("is_active")
                insert_vals.append("TRUE")

            row = await conn.fetchrow(
                f"""
                INSERT INTO robot_api_keys ({', '.join(insert_cols)})
                VALUES ({', '.join(insert_vals)})
                RETURNING id, robot_id, name, description, created_at, expires_at, last_used_at, last_used_ip, is_revoked
                """,
                *insert_params,
            )

        key = RobotApiKeyResponse(
            id=str(row["id"]),
            robot_id=str(row["robot_id"]),
            robot_name=str(robot["name"]),
            key_name=row.get("name"),
            description=row.get("description"),
            status="active",
            created_at=row.get("created_at"),
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            last_used_ip=str(row.get("last_used_ip")) if row.get("last_used_ip") else None,
        )

        return CreateRobotApiKeyResponse(api_key=raw_key, key=key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create robot API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key") from e


@router.post(
    "/robot-api-keys/{key_id}/revoke",
    dependencies=[Depends(require_admin)],
)
async def revoke_robot_api_key(
    request: Request,
    key_id: str = Path(..., min_length=1),
    payload: RevokeRobotApiKeyRequest = RevokeRobotApiKeyRequest(),
    user: AuthenticatedUser = Depends(require_admin),
) -> dict[str, Any]:
    del request

    pool = _require_db_pool()
    await _ensure_table_exists(pool, "robot_api_keys")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM robot_api_keys WHERE id = $1::uuid",
                key_id,
            )
            if not row:
                raise HTTPException(status_code=404, detail="API key not found")

            await conn.execute(
                """
                UPDATE robot_api_keys
                SET is_revoked = TRUE,
                    revoked_at = NOW(),
                    revoked_by = $2,
                    revoke_reason = $3
                WHERE id = $1::uuid
                """,
                key_id,
                user.user_id,
                payload.reason,
            )

        return {"revoked": True, "key_id": key_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke robot API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key") from e


@router.post(
    "/robot-api-keys/{key_id}/rotate",
    response_model=CreateRobotApiKeyResponse,
    dependencies=[Depends(require_admin)],
)
async def rotate_robot_api_key(
    request: Request,
    key_id: str = Path(..., min_length=1),
    user: AuthenticatedUser = Depends(require_admin),
) -> CreateRobotApiKeyResponse:
    del request

    pool = _require_db_pool()
    await _ensure_table_exists(pool, "robot_api_keys")

    raw_key = _generate_raw_api_key()
    key_hash = _hash_api_key(raw_key)

    try:
        async with pool.acquire() as conn:
            cols = await conn.fetch(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name='robot_api_keys'
                """
            )
            colset = {r["column_name"] for r in cols}
            has_api_key_hash = "api_key_hash" in colset
            has_key_hash = "key_hash" in colset

            existing = await conn.fetchrow(
                """
                SELECT k.id, k.robot_id, k.name, r.name AS robot_name
                FROM robot_api_keys k
                JOIN robots r ON r.robot_id = k.robot_id
                WHERE k.id = $1::uuid
                """,
                key_id,
            )
            if not existing:
                raise HTTPException(status_code=404, detail="API key not found")

            # Revoke old key
            await conn.execute(
                """
                UPDATE robot_api_keys
                SET is_revoked = TRUE,
                    revoked_at = NOW(),
                    revoked_by = $2,
                    revoke_reason = 'rotated'
                WHERE id = $1::uuid
                """,
                key_id,
                user.user_id,
            )

            # Create new key with same robot + name suffix
            new_name = f"{existing['name']} (rotated)" if existing.get("name") else "Rotated Key"

            insert_cols = ["robot_id"]
            insert_vals = ["$1"]
            insert_params: list[Any] = [str(existing["robot_id"])]
            param_idx = 2

            if has_api_key_hash:
                insert_cols.append("api_key_hash")
                insert_vals.append(f"${param_idx}")
                insert_params.append(key_hash)
                param_idx += 1
            if has_key_hash:
                insert_cols.append("key_hash")
                insert_vals.append(f"${param_idx}")
                insert_params.append(key_hash)
                param_idx += 1

            insert_cols.extend(["name", "description", "expires_at", "created_by"])
            insert_vals.extend([f"${param_idx}", "NULL", "NULL", f"${param_idx + 1}"])
            insert_params.extend([new_name, user.user_id])
            if "is_active" in colset:
                insert_cols.append("is_active")
                insert_vals.append("TRUE")

            row = await conn.fetchrow(
                f"""
                INSERT INTO robot_api_keys ({', '.join(insert_cols)})
                VALUES ({', '.join(insert_vals)})
                RETURNING id, robot_id, name, description, created_at, expires_at, last_used_at, last_used_ip, is_revoked
                """,
                *insert_params,
            )

        key = RobotApiKeyResponse(
            id=str(row["id"]),
            robot_id=str(row["robot_id"]),
            robot_name=str(existing.get("robot_name")),
            key_name=row.get("name"),
            description=row.get("description"),
            status="active",
            created_at=row.get("created_at"),
            expires_at=row.get("expires_at"),
            last_used_at=row.get("last_used_at"),
            last_used_ip=str(row.get("last_used_ip")) if row.get("last_used_ip") else None,
        )

        return CreateRobotApiKeyResponse(api_key=raw_key, key=key)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rotate robot API key {key_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to rotate API key") from e

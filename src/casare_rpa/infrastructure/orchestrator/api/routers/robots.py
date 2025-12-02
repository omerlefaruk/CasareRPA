"""
REST API endpoints for robot management.

Provides CRUD operations for robot registration, status updates, and deletion.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from loguru import logger
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Module-level database pool reference
_db_pool = None


def set_db_pool(pool) -> None:
    """Set database pool for this router."""
    global _db_pool
    _db_pool = pool
    logger.debug("Database pool set for robots router")


def get_db_pool():
    """Get database pool."""
    return _db_pool


# ==================== PYDANTIC MODELS ====================


class RobotRegistration(BaseModel):
    """Request model for robot registration."""

    robot_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    hostname: str = Field(..., min_length=1, max_length=256)
    capabilities: List[str] = Field(default_factory=list)
    environment: str = Field(default="default", max_length=64)
    max_concurrent_jobs: int = Field(default=1, ge=1, le=100)
    tags: List[str] = Field(default_factory=list)


class RobotUpdate(BaseModel):
    """Request model for robot update."""

    name: Optional[str] = Field(None, min_length=1, max_length=128)
    hostname: Optional[str] = Field(None, min_length=1, max_length=256)
    capabilities: Optional[List[str]] = None
    environment: Optional[str] = Field(None, max_length=64)
    max_concurrent_jobs: Optional[int] = Field(None, ge=1, le=100)
    tags: Optional[List[str]] = None


class RobotStatusUpdate(BaseModel):
    """Request model for status update."""

    status: str = Field(..., pattern="^(idle|busy|offline|error|maintenance)$")


class RobotResponse(BaseModel):
    """Response model for robot data."""

    robot_id: str
    name: str
    hostname: str
    status: str
    environment: str
    max_concurrent_jobs: int
    capabilities: List[str]
    tags: List[str]
    current_job_ids: List[str]
    last_seen: Optional[datetime]
    last_heartbeat: Optional[datetime]
    created_at: Optional[datetime]
    metrics: Dict[str, Any] = Field(default_factory=dict)


class RobotListResponse(BaseModel):
    """Response model for robot list."""

    robots: List[RobotResponse]
    total: int


# ==================== ENDPOINTS ====================


@router.post("/robots/register", response_model=RobotResponse)
@limiter.limit("30/minute")
async def register_robot(
    request: Request,
    registration: RobotRegistration,
):
    """
    Register a new robot with the orchestrator.

    If robot_id already exists, updates the existing registration.
    Uses upsert semantics (INSERT ON CONFLICT UPDATE).

    Rate Limit: 30 requests/minute per IP
    """
    logger.info(f"Registering robot: {registration.robot_id}")

    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        import orjson

        now = datetime.utcnow()

        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO robots (
                    robot_id, name, hostname, status, environment,
                    max_concurrent_jobs, capabilities, tags,
                    current_job_ids, metrics, registered_at, last_seen, created_at
                ) VALUES (
                    $1, $2, $3, 'idle', $4, $5, $6::jsonb, $7::jsonb,
                    '[]'::jsonb, '{}'::jsonb, $8, $8, $8
                )
                ON CONFLICT (robot_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    hostname = EXCLUDED.hostname,
                    environment = EXCLUDED.environment,
                    max_concurrent_jobs = EXCLUDED.max_concurrent_jobs,
                    capabilities = EXCLUDED.capabilities,
                    tags = EXCLUDED.tags,
                    last_seen = EXCLUDED.last_seen,
                    updated_at = NOW()
                """,
                registration.robot_id,
                registration.name,
                registration.hostname,
                registration.environment,
                registration.max_concurrent_jobs,
                orjson.dumps(registration.capabilities).decode(),
                orjson.dumps(registration.tags).decode(),
                now,
            )

            # Fetch the robot back
            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE robot_id = $1",
                registration.robot_id,
            )

            if row is None:
                raise HTTPException(
                    status_code=500, detail="Failed to fetch registered robot"
                )

            return _row_to_response(dict(row))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register robot {registration.robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {e}")


@router.get("/robots", response_model=RobotListResponse)
@limiter.limit("100/minute")
async def list_robots(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status"),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    List all registered robots with optional filtering.

    Rate Limit: 100 requests/minute per IP
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            # Build query with filters
            query = "SELECT * FROM robots WHERE 1=1"
            params = []
            param_idx = 1

            if status:
                query += f" AND status = ${param_idx}"
                params.append(status)
                param_idx += 1

            if environment:
                query += f" AND environment = ${param_idx}"
                params.append(environment)
                param_idx += 1

            # Get total count
            count_query = query.replace("SELECT *", "SELECT COUNT(*)")
            total = await conn.fetchval(count_query, *params)

            # Add pagination
            query += f" ORDER BY name LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            return RobotListResponse(
                robots=[_row_to_response(dict(row)) for row in rows],
                total=total or 0,
            )

    except Exception as e:
        logger.error(f"Failed to list robots: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list robots: {e}")


@router.get("/robots/{robot_id}", response_model=RobotResponse)
@limiter.limit("200/minute")
async def get_robot(
    request: Request,
    robot_id: str = Path(..., min_length=1, max_length=64),
):
    """
    Get details for a single robot.

    Rate Limit: 200 requests/minute per IP
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE robot_id = $1",
                robot_id,
            )

            if row is None:
                raise HTTPException(
                    status_code=404, detail=f"Robot {robot_id} not found"
                )

            return _row_to_response(dict(row))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get robot: {e}")


@router.put("/robots/{robot_id}", response_model=RobotResponse)
@limiter.limit("60/minute")
async def update_robot(
    request: Request,
    robot_id: str = Path(..., min_length=1, max_length=64),
    update: RobotUpdate = ...,
):
    """
    Update robot configuration.

    Only provided fields are updated.

    Rate Limit: 60 requests/minute per IP
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        import orjson

        async with pool.acquire() as conn:
            # Check robot exists
            existing = await conn.fetchrow(
                "SELECT robot_id FROM robots WHERE robot_id = $1",
                robot_id,
            )
            if existing is None:
                raise HTTPException(
                    status_code=404, detail=f"Robot {robot_id} not found"
                )

            # Build dynamic update
            updates = ["updated_at = NOW()"]
            params = [robot_id]
            param_idx = 2

            if update.name is not None:
                updates.append(f"name = ${param_idx}")
                params.append(update.name)
                param_idx += 1

            if update.hostname is not None:
                updates.append(f"hostname = ${param_idx}")
                params.append(update.hostname)
                param_idx += 1

            if update.capabilities is not None:
                updates.append(f"capabilities = ${param_idx}::jsonb")
                params.append(orjson.dumps(update.capabilities).decode())
                param_idx += 1

            if update.environment is not None:
                updates.append(f"environment = ${param_idx}")
                params.append(update.environment)
                param_idx += 1

            if update.max_concurrent_jobs is not None:
                updates.append(f"max_concurrent_jobs = ${param_idx}")
                params.append(update.max_concurrent_jobs)
                param_idx += 1

            if update.tags is not None:
                updates.append(f"tags = ${param_idx}::jsonb")
                params.append(orjson.dumps(update.tags).decode())
                param_idx += 1

            query = f"UPDATE robots SET {', '.join(updates)} WHERE robot_id = $1"
            await conn.execute(query, *params)

            # Fetch updated robot
            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE robot_id = $1",
                robot_id,
            )

            return _row_to_response(dict(row))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update robot: {e}")


@router.put("/robots/{robot_id}/status", response_model=RobotResponse)
@limiter.limit("120/minute")
async def update_robot_status(
    request: Request,
    robot_id: str = Path(..., min_length=1, max_length=64),
    status_update: RobotStatusUpdate = ...,
):
    """
    Update robot status.

    Valid statuses: idle, busy, offline, error, maintenance

    Rate Limit: 120 requests/minute per IP (higher for heartbeats)
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            now = datetime.utcnow()

            result = await conn.execute(
                """
                UPDATE robots
                SET status = $2,
                    last_seen = $3,
                    last_heartbeat = $3,
                    updated_at = NOW()
                WHERE robot_id = $1
                """,
                robot_id,
                status_update.status,
                now,
            )

            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=404, detail=f"Robot {robot_id} not found"
                )

            row = await conn.fetchrow(
                "SELECT * FROM robots WHERE robot_id = $1",
                robot_id,
            )

            return _row_to_response(dict(row))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update status for robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update status: {e}")


@router.delete("/robots/{robot_id}")
@limiter.limit("30/minute")
async def delete_robot(
    request: Request,
    robot_id: str = Path(..., min_length=1, max_length=64),
):
    """
    Delete/deregister a robot.

    Rate Limit: 30 requests/minute per IP
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        async with pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM robots WHERE robot_id = $1",
                robot_id,
            )

            if result == "DELETE 0":
                raise HTTPException(
                    status_code=404, detail=f"Robot {robot_id} not found"
                )

            logger.info(f"Deleted robot: {robot_id}")
            return {"deleted": True, "robot_id": robot_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete robot: {e}")


@router.post("/robots/{robot_id}/heartbeat")
@limiter.limit("600/minute")
async def robot_heartbeat(
    request: Request,
    robot_id: str = Path(..., min_length=1, max_length=64),
    metrics: Optional[Dict[str, Any]] = None,
):
    """
    Record robot heartbeat.

    Updates last_seen and optionally metrics (CPU, memory, etc).

    Rate Limit: 600 requests/minute per IP (very high for heartbeats)
    """
    pool = get_db_pool()
    if pool is None:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        import orjson

        async with pool.acquire() as conn:
            now = datetime.utcnow()

            if metrics:
                result = await conn.execute(
                    """
                    UPDATE robots
                    SET last_seen = $2,
                        last_heartbeat = $2,
                        metrics = $3::jsonb,
                        status = CASE WHEN status = 'offline' THEN 'idle' ELSE status END,
                        updated_at = NOW()
                    WHERE robot_id = $1
                    """,
                    robot_id,
                    now,
                    orjson.dumps(metrics).decode(),
                )
            else:
                result = await conn.execute(
                    """
                    UPDATE robots
                    SET last_seen = $2,
                        last_heartbeat = $2,
                        status = CASE WHEN status = 'offline' THEN 'idle' ELSE status END,
                        updated_at = NOW()
                    WHERE robot_id = $1
                    """,
                    robot_id,
                    now,
                )

            if result == "UPDATE 0":
                raise HTTPException(
                    status_code=404, detail=f"Robot {robot_id} not found"
                )

            return {"ok": True, "timestamp": now.isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record heartbeat for robot {robot_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Heartbeat failed: {e}")


# ==================== HELPERS ====================


def _row_to_response(row: Dict[str, Any]) -> RobotResponse:
    """Convert database row to response model."""
    import orjson

    def parse_jsonb(val):
        if val is None:
            return []
        if isinstance(val, str):
            return orjson.loads(val)
        return val

    return RobotResponse(
        robot_id=row.get("robot_id", ""),
        name=row.get("name", ""),
        hostname=row.get("hostname", ""),
        status=row.get("status", "offline"),
        environment=row.get("environment", "default"),
        max_concurrent_jobs=row.get("max_concurrent_jobs", 1),
        capabilities=parse_jsonb(row.get("capabilities", [])),
        tags=parse_jsonb(row.get("tags", [])),
        current_job_ids=parse_jsonb(row.get("current_job_ids", [])),
        last_seen=row.get("last_seen"),
        last_heartbeat=row.get("last_heartbeat"),
        created_at=row.get("created_at"),
        metrics=parse_jsonb(row.get("metrics", {})) or {},
    )

"""
WebSocket endpoints for real-time monitoring updates.

Provides live streams for:
- Job status updates
- Robot heartbeats
- Queue metrics

Security:
- All WebSocket endpoints require token authentication via query parameter
- Tokens are validated against JWT or robot API keys
"""

from typing import Optional, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger
import asyncio
import orjson

from casare_rpa.infrastructure.events import MonitoringEvent
from casare_rpa.infrastructure.observability.metrics import get_metrics_collector
from casare_rpa.infrastructure.orchestrator.api.auth import (
    decode_token,
    get_robot_authenticator,
    JWT_DEV_MODE,
)
from casare_rpa.infrastructure.orchestrator.api.models import (
    LiveJobUpdate,
    QueueMetricsUpdate,
    RobotStatusUpdate,
)

# WebSocket send timeout (seconds)
WS_SEND_TIMEOUT = 1.0


async def verify_websocket_token(
    websocket: WebSocket,
    token: Optional[str] = None,
) -> Optional[str]:
    """
    Verify WebSocket authentication token.

    WebSockets cannot use HTTP headers for authentication in the same way as
    REST endpoints. Token must be passed as a query parameter.

    Args:
        websocket: WebSocket connection
        token: Authentication token from query parameter

    Returns:
        user_id/robot_id if authenticated, None if authentication fails

    Security Flow:
    1. Check for token in query parameter
    2. Try JWT token validation first
    3. Fall back to robot API key validation
    4. Allow in dev mode if no token and JWT_DEV_MODE=true
    """
    # Allow unauthenticated access in development mode
    if not token:
        if JWT_DEV_MODE:
            logger.debug("WebSocket dev mode: allowing unauthenticated connection")
            return "dev_user"
        logger.warning("WebSocket connection rejected: no authentication token")
        await websocket.close(code=4001, reason="Authentication required")
        return None

    # Try JWT token first
    try:
        payload = decode_token(token)
        if payload.type == "access":
            logger.debug(f"WebSocket authenticated via JWT: user={payload.sub}")
            return payload.sub
    except Exception as jwt_error:
        logger.debug(f"JWT validation failed, trying robot token: {jwt_error}")

    # Try robot API key
    try:
        authenticator = get_robot_authenticator()
        if authenticator.is_enabled:
            robot_id = await authenticator.verify_token_async(token)
            if robot_id:
                logger.debug(f"WebSocket authenticated via robot token: {robot_id}")
                return robot_id
    except Exception as robot_error:
        logger.debug(f"Robot token validation failed: {robot_error}")

    # Authentication failed
    logger.warning("WebSocket connection rejected: invalid authentication token")
    await websocket.close(code=4001, reason="Invalid authentication token")
    return None


router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(
            f"WebSocket connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        """Remove disconnected WebSocket."""
        self.active_connections.discard(websocket)
        logger.info(
            f"WebSocket disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients with timeout protection.

        Prevents slow clients from blocking the entire broadcast.
        """
        disconnected = set()

        for connection in self.active_connections:
            try:
                # Add timeout to prevent slow clients from blocking broadcast
                await asyncio.wait_for(
                    connection.send_text(orjson.dumps(message).decode()),
                    timeout=WS_SEND_TIMEOUT,
                )
            except asyncio.TimeoutError:
                logger.warning("Client send timeout, disconnecting")
                disconnected.add(connection)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


# Global connection managers for each endpoint
live_jobs_manager = ConnectionManager()
robot_status_manager = ConnectionManager()
queue_metrics_manager = ConnectionManager()


@router.websocket("/live-jobs")
async def websocket_live_jobs(
    websocket: WebSocket,
    token: Optional[str] = Query(None, alias="token"),
):
    """
    WebSocket endpoint for real-time job status updates.

    Security:
        Requires authentication via token query parameter.
        Example: ws://host/live-jobs?token=<jwt_or_api_key>

    Clients receive job updates as they transition through states:
    pending -> claimed -> completed/failed

    Message format:
    {
        "job_id": "abc123",
        "status": "completed",
        "timestamp": "2025-11-29T10:30:00Z"
    }
    """
    # Verify authentication before accepting connection
    user_id = await verify_websocket_token(websocket, token)
    if not user_id:
        return  # Connection already closed by verify_websocket_token

    await live_jobs_manager.connect(websocket)

    try:
        # Keep connection alive and handle ping/pong
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        live_jobs_manager.disconnect(websocket)
        logger.info("Client disconnected from live-jobs")
    except Exception as e:
        logger.error(f"WebSocket error in live-jobs: {e}")
        live_jobs_manager.disconnect(websocket)


@router.websocket("/robot-status")
async def websocket_robot_status(
    websocket: WebSocket,
    token: Optional[str] = Query(None, alias="token"),
):
    """
    WebSocket endpoint for robot heartbeat stream.

    Security:
        Requires authentication via token query parameter.
        Example: ws://host/robot-status?token=<jwt_or_api_key>

    Broadcasts robot status updates every 5-10 seconds.

    Message format:
    {
        "robot_id": "robot-001",
        "status": "busy",
        "cpu_percent": 45.2,
        "memory_mb": 1024.5,
        "timestamp": "2025-11-29T10:30:00Z"
    }
    """
    # Verify authentication before accepting connection
    user_id = await verify_websocket_token(websocket, token)
    if not user_id:
        return  # Connection already closed by verify_websocket_token

    await robot_status_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        robot_status_manager.disconnect(websocket)
        logger.info("Client disconnected from robot-status")
    except Exception as e:
        logger.error(f"WebSocket error in robot-status: {e}")
        robot_status_manager.disconnect(websocket)


@router.websocket("/queue-metrics")
async def websocket_queue_metrics(
    websocket: WebSocket,
    token: Optional[str] = Query(None, alias="token"),
):
    """
    WebSocket endpoint for queue depth updates.

    Security:
        Requires authentication via token query parameter.
        Example: ws://host/queue-metrics?token=<jwt_or_api_key>

    Broadcasts queue metrics every 5 seconds.

    Message format:
    {
        "depth": 42,
        "timestamp": "2025-11-29T10:30:00Z"
    }
    """
    # Verify authentication before accepting connection
    user_id = await verify_websocket_token(websocket, token)
    if not user_id:
        return  # Connection already closed by verify_websocket_token

    await queue_metrics_manager.connect(websocket)

    try:
        # Send initial queue depth from metrics collector
        metrics = get_metrics_collector()
        current_depth = metrics.get_queue_depth()
        initial_message = QueueMetricsUpdate(
            depth=current_depth,
            timestamp=datetime.now(),
        )
        await websocket.send_text(orjson.dumps(initial_message.model_dump()).decode())

        # Keep connection alive
        while True:
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        queue_metrics_manager.disconnect(websocket)
        logger.info("Client disconnected from queue-metrics")
    except Exception as e:
        logger.error(f"WebSocket error in queue-metrics: {e}")
        queue_metrics_manager.disconnect(websocket)


# Broadcast helper functions (to be called by EventBus or metrics collector)


async def broadcast_job_update(job_id: str, status: str):
    """
    Broadcast job status update to all connected clients.

    Args:
        job_id: Job identifier
        status: New job status (pending/claimed/completed/failed)
    """
    message = LiveJobUpdate(
        job_id=job_id,
        status=status,
        timestamp=datetime.now(),
    )
    await live_jobs_manager.broadcast(message.model_dump())
    logger.debug(f"Broadcasted job update: {job_id} → {status}")


async def broadcast_robot_status(
    robot_id: str, status: str, cpu_percent: float, memory_mb: float
):
    """
    Broadcast robot status update to all connected clients.

    Args:
        robot_id: Robot identifier
        status: Robot status (idle/busy/offline)
        cpu_percent: CPU usage percentage
        memory_mb: Memory usage in MB
    """
    message = RobotStatusUpdate(
        robot_id=robot_id,
        status=status,
        cpu_percent=cpu_percent,
        memory_mb=memory_mb,
        timestamp=datetime.now(),
    )
    await robot_status_manager.broadcast(message.model_dump())
    logger.debug(f"Broadcasted robot status: {robot_id} → {status}")


async def broadcast_queue_metrics(depth: int):
    """
    Broadcast queue depth update to all connected clients.

    Args:
        depth: Current queue depth (pending jobs)
    """
    message = QueueMetricsUpdate(
        depth=depth,
        timestamp=datetime.now(),
    )
    await queue_metrics_manager.broadcast(message.model_dump())
    logger.debug(f"Broadcasted queue metrics: depth={depth}")


# =============================================================================
# Event Bus Handlers (subscribe these in main.py lifespan)
# =============================================================================


async def on_job_status_changed(event: MonitoringEvent) -> None:
    """
    Handle JOB_STATUS_CHANGED events from metrics collector.

    Args:
        event: Monitoring event with job status data
    """
    payload = event.payload
    job_id = payload.get("job_id")
    status = payload.get("status")

    if job_id and status:
        await broadcast_job_update(job_id, status)


async def on_robot_heartbeat(event: MonitoringEvent) -> None:
    """
    Handle ROBOT_HEARTBEAT events from robots.

    Args:
        event: Monitoring event with robot heartbeat data
    """
    payload = event.payload
    robot_id = payload.get("robot_id")
    status = payload.get("status", "idle")
    cpu_percent = payload.get("cpu_percent", 0.0)
    memory_mb = payload.get("memory_mb", 0.0)

    if robot_id:
        await broadcast_robot_status(robot_id, status, cpu_percent, memory_mb)


async def on_queue_depth_changed(event: MonitoringEvent) -> None:
    """
    Handle QUEUE_DEPTH_CHANGED events from metrics collector.

    Args:
        event: Monitoring event with queue depth data
    """
    payload = event.payload
    queue_depth = payload.get("queue_depth", 0)

    await broadcast_queue_metrics(queue_depth)

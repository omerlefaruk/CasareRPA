"""
WebSocket endpoints for real-time monitoring updates.

Provides live streams for:
- Job status updates
- Robot heartbeats
- Queue metrics
"""

from typing import Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
import asyncio
import orjson

from casare_rpa.infrastructure.events import MonitoringEvent, MonitoringEventType
from ..models import LiveJobUpdate, RobotStatusUpdate, QueueMetricsUpdate

# WebSocket send timeout (seconds)
WS_SEND_TIMEOUT = 1.0


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
async def websocket_live_jobs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time job status updates.

    Clients receive job updates as they transition through states:
    pending → claimed → completed/failed

    Message format:
    {
        "job_id": "abc123",
        "status": "completed",
        "timestamp": "2025-11-29T10:30:00Z"
    }
    """
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
async def websocket_robot_status(websocket: WebSocket):
    """
    WebSocket endpoint for robot heartbeat stream.

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
async def websocket_queue_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for queue depth updates.

    Broadcasts queue metrics every 5 seconds.

    Message format:
    {
        "depth": 42,
        "timestamp": "2025-11-29T10:30:00Z"
    }
    """
    await queue_metrics_manager.connect(websocket)

    try:
        # Send initial queue depth
        # TODO: Get actual queue depth from metrics collector
        initial_message = QueueMetricsUpdate(
            depth=0,
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

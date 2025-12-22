"""
WebSocket Handlers for Cloud Orchestrator.

Handles Robot, Admin, and Log streaming WebSocket connections.
"""

from datetime import datetime, timezone
from typing import Optional

import orjson
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from loguru import logger

from casare_rpa.domain.value_objects.log_entry import LogLevel
from casare_rpa.infrastructure.orchestrator.robot_manager import ConnectedRobot
from casare_rpa.infrastructure.orchestrator.server_lifecycle import (
    get_log_streaming_service,
    get_robot_manager,
)
from casare_rpa.infrastructure.orchestrator.api.auth import (
    validate_admin_secret,
    get_robot_authenticator,
)


router = APIRouter()


@router.websocket("/robot/{robot_id}")
async def robot_websocket(
    websocket: WebSocket,
    robot_id: str,
    api_key: Optional[str] = Query(None, alias="api_key"),
):
    """WebSocket endpoint for robot connections.

    Requires API key authentication via query parameter.
    Example: ws://host/ws/robot/robot-123?api_key=crpa_xxxxx
    """
    # Validate API key before accepting connection
    authenticator = get_robot_authenticator()
    if authenticator.is_enabled:
        validated_robot_id = await authenticator.verify_token_async(api_key)
        if validated_robot_id is None:
            logger.warning(f"Robot WebSocket auth failed for robot_id={robot_id}: Invalid API key")
            await websocket.close(code=4001)  # 4001 = Unauthorized
            return

        # Verify robot_id matches the API key's robot (if database validation succeeded)
        if validated_robot_id != "unverified" and validated_robot_id != robot_id:
            logger.warning(f"Robot ID mismatch: URL={robot_id}, API key={validated_robot_id}")
            await websocket.close(code=4003)  # 4003 = Forbidden
            return
    else:
        logger.warning(f"Robot auth disabled, allowing connection for {robot_id}")

    await websocket.accept()
    logger.info(f"Robot WebSocket connected: {robot_id}")

    manager = get_robot_manager()
    registered_robot: Optional[ConnectedRobot] = None

    try:
        while True:
            raw_message = await websocket.receive_text()
            message = orjson.loads(raw_message)
            msg_type = message.get("type", "")

            if msg_type == "register":
                registered_robot = await manager.register_robot(
                    websocket=websocket,
                    robot_id=message.get("robot_id", robot_id),
                    robot_name=message.get("robot_name", robot_id),
                    capabilities=message.get("capabilities", {}),
                    environment=message.get("environment", "production"),
                    tenant_id=message.get("tenant_id"),
                )

                await websocket.send_text(
                    orjson.dumps(
                        {
                            "type": "register_ack",
                            "robot_id": registered_robot.robot_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ).decode()
                )

            elif msg_type == "heartbeat":
                await manager.update_heartbeat(robot_id, message)
                await websocket.send_text(
                    orjson.dumps(
                        {
                            "type": "heartbeat_ack",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ).decode()
                )

            elif msg_type == "job_accept":
                job_id = message.get("job_id")
                logger.debug(f"Robot {robot_id} accepted job {job_id}")

            elif msg_type == "job_reject":
                job_id = message.get("job_id")
                reason = message.get("reason", "Unknown")
                logger.warning(f"Robot {robot_id} rejected job {job_id}: {reason}")
                await manager.requeue_job(robot_id, job_id, reason)

            elif msg_type == "job_progress":
                job_id = message.get("job_id")
                progress = message.get("progress", 0)
                logger.debug(f"Job {job_id} progress: {progress}%")

            elif msg_type == "job_complete":
                job_id = message.get("job_id")
                result = message.get("result", {})
                await manager.job_completed(robot_id, job_id, True, result)

            elif msg_type == "job_failed":
                job_id = message.get("job_id")
                error = message.get("error", "Unknown error")
                await manager.job_completed(robot_id, job_id, False, {"error": error})

            elif msg_type == "pong":
                logger.debug(f"Pong from {robot_id}")

            elif msg_type == "log_batch":
                log_streaming_service = get_log_streaming_service()
                if log_streaming_service is not None and registered_robot is not None:
                    tenant_id = registered_robot.tenant_id or "default"
                    try:
                        count = await log_streaming_service.receive_log_batch(
                            robot_id, message, tenant_id
                        )
                        logger.debug(f"Received {count} logs from {robot_id}")
                    except Exception as e:
                        logger.warning(f"Failed to process log batch from {robot_id}: {e}")

            else:
                logger.warning(f"Unknown message type from {robot_id}: {msg_type}")

    except WebSocketDisconnect:
        logger.info(f"Robot WebSocket disconnected: {robot_id}")
    except Exception as e:
        logger.error(f"Robot WebSocket error: {e}")
    finally:
        await manager.unregister_robot(robot_id)


@router.websocket("/admin")
async def admin_websocket(
    websocket: WebSocket,
    api_secret: Optional[str] = Query(None, alias="api_secret"),
):
    """WebSocket endpoint for admin dashboard.

    Requires API secret authentication via query parameter.
    Example: ws://host/ws/admin?api_secret=your-secret-key
    """
    if not await validate_admin_secret(api_secret):
        logger.warning("Admin WebSocket auth failed - invalid or missing api_secret")
        await websocket.close(code=4001)  # 4001 = Unauthorized
        return

    await websocket.accept()
    logger.info("Admin WebSocket connected")

    manager = get_robot_manager()
    await manager.add_admin_connection(websocket)

    try:
        # Send initial state
        robots = manager.get_all_robots()
        await websocket.send_text(
            orjson.dumps(
                {
                    "type": "initial_state",
                    "robots": [
                        {
                            "robot_id": r.robot_id,
                            "robot_name": r.robot_name,
                            "status": r.status,
                            "capabilities": r.capabilities,
                        }
                        for r in robots
                    ],
                    "pending_jobs": len(manager.get_pending_jobs()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ).decode()
        )

        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info("Admin WebSocket disconnected")
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
    finally:
        manager.remove_admin_connection(websocket)


@router.websocket("/logs/{robot_id}")
async def log_stream_websocket(
    websocket: WebSocket,
    robot_id: str,
    api_secret: Optional[str] = Query(None, alias="api_secret"),
    min_level: str = Query("DEBUG", alias="min_level"),
):
    """WebSocket endpoint for streaming logs from a specific robot.

    Requires admin API secret authentication.
    Example: ws://host/ws/logs/robot-123?api_secret=your-secret&min_level=INFO
    """
    if not await validate_admin_secret(api_secret):
        logger.warning(f"Log stream auth failed for robot_id={robot_id}")
        await websocket.close(code=4001)
        return

    log_streaming_service = get_log_streaming_service()
    if log_streaming_service is None:
        await websocket.close(code=4503)  # Service unavailable
        return

    await websocket.accept()
    logger.info(f"Log stream connected for robot: {robot_id}")

    try:
        level = LogLevel.from_string(min_level)
        await log_streaming_service.subscribe(
            websocket,
            robot_ids=[robot_id],
            min_level=level,
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"Log stream disconnected for robot: {robot_id}")
    except Exception as e:
        logger.error(f"Log stream error: {e}")
    finally:
        await log_streaming_service.unsubscribe(websocket)


@router.websocket("/logs")
async def all_logs_stream_websocket(
    websocket: WebSocket,
    api_secret: Optional[str] = Query(None, alias="api_secret"),
    tenant_id: Optional[str] = Query(None, alias="tenant_id"),
    min_level: str = Query("DEBUG", alias="min_level"),
):
    """WebSocket endpoint for streaming all logs (admin view).

    Requires admin API secret authentication.
    Example: ws://host/ws/logs?api_secret=your-secret&tenant_id=xxx&min_level=INFO
    """
    if not await validate_admin_secret(api_secret):
        logger.warning("All logs stream auth failed")
        await websocket.close(code=4001)
        return

    log_streaming_service = get_log_streaming_service()
    if log_streaming_service is None:
        await websocket.close(code=4503)
        return

    await websocket.accept()
    logger.info(f"All logs stream connected (tenant={tenant_id})")

    try:
        level = LogLevel.from_string(min_level)
        await log_streaming_service.subscribe(
            websocket,
            robot_ids=None,  # All robots
            tenant_id=tenant_id,
            min_level=level,
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info("All logs stream disconnected")
    except Exception as e:
        logger.error(f"All logs stream error: {e}")
    finally:
        await log_streaming_service.unsubscribe(websocket)

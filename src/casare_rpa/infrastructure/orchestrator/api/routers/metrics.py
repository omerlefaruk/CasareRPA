"""
REST API endpoints for metrics and monitoring.

Provides fleet, robot, job, and analytics data for the React dashboard.
Includes WebSocket endpoint for real-time metrics streaming.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional, List, Set
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import PlainTextResponse
from loguru import logger
from slowapi import Limiter
from slowapi.util import get_remote_address

from casare_rpa.infrastructure.orchestrator.api.dependencies import (
    get_metrics_collector,
)
from casare_rpa.infrastructure.orchestrator.api.models import (
    ActivityEvent,
    ActivityResponse,
    AnalyticsSummary,
    FleetMetrics,
    JobDetails,
    JobSummary,
    RobotMetrics,
    RobotSummary,
)
from casare_rpa.infrastructure.observability.metrics import (
    get_metrics_exporter,
    MetricsSnapshot,
    get_metrics_collector as get_rpa_metrics_collector,
)


router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# WebSocket connection manager for metrics streaming
_metrics_ws_connections: Set[WebSocket] = set()


@router.get("/metrics/fleet", response_model=FleetMetrics)
@limiter.limit("100/minute")
async def get_fleet_metrics(
    request: Request,
    collector=Depends(get_metrics_collector),
):
    """
    Get fleet-wide metrics summary.

    Returns:
        - Total/active/idle/offline robot counts
        - Active jobs count
        - Queue depth

    Rate Limit: 100 requests/minute per IP
    """
    logger.debug("Fetching fleet metrics")

    try:
        # Use async method to query database
        data = await collector.get_fleet_summary_async()
        return FleetMetrics(**data)
    except Exception as e:
        logger.error(f"Failed to fetch fleet metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fleet metrics")


@router.get("/metrics/robots", response_model=List[RobotSummary])
@limiter.limit("100/minute")
async def get_robots(
    request: Request,
    status: Optional[str] = Query(
        None, description="Filter by status: idle, busy, offline"
    ),
    collector=Depends(get_metrics_collector),
):
    """
    Get list of all robots with optional status filter.

    Query Parameters:
        - status: Filter robots by status (idle/busy/offline)

    Returns list of robot summaries with current status and resource usage.

    Rate Limit: 100 requests/minute per IP
    """
    logger.debug(f"Fetching robots list (status={status})")

    try:
        # Use async method to query database
        robots = await collector.get_robot_list_async(status=status)
        return [RobotSummary(**robot) for robot in robots]
    except Exception as e:
        logger.error(f"Failed to fetch robots: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch robots")


@router.get("/metrics/robots/{robot_id}", response_model=RobotMetrics)
@limiter.limit("200/minute")
async def get_robot_details(
    request: Request,
    robot_id: str = Path(
        ...,
        pattern="^[a-zA-Z0-9_-]{1,64}$",
        description="Robot ID (alphanumeric, underscore, hyphen, max 64 chars)",
    ),
    collector=Depends(get_metrics_collector),
):
    """
    Get detailed metrics for a single robot.

    Path Parameters:
        - robot_id: Robot identifier

    Returns detailed robot metrics including:
        - Resource usage (CPU, memory)
        - Current job
        - Performance stats (jobs completed/failed today, avg duration)

    Rate Limit: 200 requests/minute per IP (higher for detail views)
    """
    logger.debug(f"Fetching robot details: {robot_id}")

    try:
        robot = collector.get_robot_details(robot_id)
        if not robot:
            raise HTTPException(status_code=404, detail=f"Robot {robot_id} not found")

        return RobotMetrics(**robot)
    except HTTPException:
        raise  # Re-raise HTTPException for 404
    except Exception as e:
        logger.error(f"Failed to fetch robot details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch robot details")


@router.get("/metrics/jobs", response_model=List[JobSummary])
@limiter.limit("50/minute")
async def get_jobs(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Number of jobs to return"),
    status: Optional[str] = Query(
        None, description="Filter by status: pending, claimed, completed, failed"
    ),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
):
    """
    Get job execution history with filtering and pagination.

    Query Parameters:
        - limit: Max number of jobs (default: 50, max: 500)
        - status: Filter by job status
        - workflow_id: Filter by workflow
        - robot_id: Filter by robot

    Returns paginated job history sorted by creation time (newest first).

    Rate Limit: 50 requests/minute per IP (lower for database queries)
    """
    logger.debug(
        f"Fetching jobs (limit={limit}, status={status}, workflow={workflow_id}, robot={robot_id})"
    )

    # Get collector with database pool automatically injected from request
    collector = get_metrics_collector(request)

    try:
        jobs = await collector.get_job_history(
            limit=limit,
            status=status,
            workflow_id=workflow_id,
            robot_id=robot_id,
        )
        return [JobSummary(**job) for job in jobs]
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch jobs")


@router.get("/metrics/jobs/{job_id}", response_model=JobDetails)
@limiter.limit("200/minute")
async def get_job_details(
    request: Request,
    job_id: str = Path(
        ...,
        pattern="^[a-zA-Z0-9_-]{1,64}$",
        description="Job ID (alphanumeric, underscore, hyphen, max 64 chars)",
    ),
    collector=Depends(get_metrics_collector),
):
    """
    Get detailed execution information for a single job.

    Path Parameters:
        - job_id: Job identifier

    Returns:
        - Job status and timestamps
        - Error information (if failed)
        - Node-by-node execution breakdown
        - DBOS workflow status

    Rate Limit: 200 requests/minute per IP
    """
    logger.debug(f"Fetching job details: {job_id}")

    try:
        # Use async method for database-backed job lookups
        job = await collector.get_job_details_async(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobDetails(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job details")


@router.get("/metrics/analytics", response_model=AnalyticsSummary)
@limiter.limit("20/minute")
async def get_analytics(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
):
    """
    Get aggregated analytics and statistics.

    Query Parameters:
        - days: Number of days to analyze (default: 7, max: 90)

    Returns:
        - Success/failure rates
        - Duration percentiles (P50/P90/P99)
        - Top 10 slowest workflows
        - Error distribution by type
        - Self-healing success rate

    Note:
        This endpoint is async because it performs database-backed percentile
        calculations using PostgreSQL's PERCENTILE_CONT function for accurate
        P50/P90/P99 metrics across all job executions in the time window.

    Rate Limit: 20 requests/minute per IP (lowest for expensive analytics queries)
    """
    logger.debug(f"Fetching analytics (days={days})")

    # Get collector with database pool automatically injected from request
    collector = get_metrics_collector(request)

    try:
        # Use async method for accurate percentile calculations from database
        data = await collector.get_analytics_async(days=days)
        return AnalyticsSummary(**data)
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")


@router.get("/metrics/activity", response_model=ActivityResponse)
@limiter.limit("60/minute")
async def get_activity(
    request: Request,
    limit: int = Query(
        default=50, ge=1, le=200, description="Number of events to return"
    ),
    since: Optional[datetime] = Query(
        default=None, description="Only return events after this timestamp"
    ),
    event_type: Optional[str] = Query(
        default=None,
        description="Filter by event type: job_started, job_completed, job_failed, robot_online, robot_offline, schedule_triggered",
    ),
):
    """
    Fetch historical activity events for the dashboard.

    Combines:
    - Recent job status changes (started, completed, failed)
    - Robot status changes (online, offline)
    - Schedule triggers

    Returns events sorted by timestamp descending.

    Query Parameters:
        - limit: Max number of events (default: 50, max: 200)
        - since: Only return events after this timestamp (ISO format)
        - event_type: Filter by specific event type

    Rate Limit: 60 requests/minute per IP
    """
    logger.debug(
        f"Fetching activity events (limit={limit}, since={since}, event_type={event_type})"
    )

    collector = get_metrics_collector(request)

    try:
        data = await collector.get_activity_events_async(
            limit=limit,
            since=since,
            event_type=event_type,
        )
        events = [ActivityEvent(**event) for event in data["events"]]
        return ActivityResponse(events=events, total=data["total"])
    except Exception as e:
        logger.error(f"Failed to fetch activity events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch activity events")


# =============================================================================
# Real-time Metrics Streaming
# =============================================================================


@router.get("/metrics/snapshot")
async def get_metrics_snapshot(
    request: Request,
    environment: str = Query(default="development", description="Environment name"),
):
    """
    Get a point-in-time snapshot of all metrics.

    Returns complete metrics state as JSON for dashboard initialization.
    Useful for initial page load before WebSocket connection.

    Rate Limit: Inherits from /metrics/fleet rate limit
    """
    try:
        collector = get_rpa_metrics_collector()
        snapshot = MetricsSnapshot.from_collector(collector, environment)
        return snapshot.to_dict()
    except Exception as e:
        logger.error(f"Failed to get metrics snapshot: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics snapshot")


@router.get("/metrics/prometheus", response_class=PlainTextResponse)
async def get_prometheus_metrics(
    request: Request,
    environment: str = Query(default="development", description="Environment name"),
):
    """
    Get metrics in Prometheus exposition format.

    Returns plain text metrics compatible with Prometheus scraping.
    Can be used to configure Prometheus to scrape CasareRPA metrics.

    Example Prometheus scrape config:
        - job_name: 'casare-rpa'
          static_configs:
            - targets: ['localhost:8000']
          metrics_path: '/api/v1/metrics/prometheus'
    """
    try:
        exporter = get_metrics_exporter(environment=environment)
        return exporter.get_prometheus_format()
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Prometheus metrics")


@router.websocket("/metrics/stream")
async def metrics_websocket_stream(
    websocket: WebSocket,
    interval: int = Query(
        default=5, ge=1, le=60, description="Update interval in seconds"
    ),
    environment: str = Query(default="development", description="Environment name"),
):
    """
    WebSocket endpoint for real-time metrics streaming.

    Clients connect and receive periodic metrics updates as JSON messages.
    Connection is maintained until client disconnects.

    Query Parameters:
        - interval: Update frequency in seconds (1-60, default: 5)
        - environment: Environment name for metrics labels

    Message Format:
        {
            "type": "metrics",
            "timestamp": "2024-01-15T10:30:00.000Z",
            "data": { ... metrics snapshot ... }
        }

    Usage (JavaScript):
        const ws = new WebSocket('ws://localhost:8000/api/v1/metrics/stream?interval=5');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            updateDashboard(data.data);
        };
    """
    await websocket.accept()
    _metrics_ws_connections.add(websocket)

    logger.info(
        f"Metrics WebSocket connected (interval={interval}s, "
        f"total connections={len(_metrics_ws_connections)})"
    )

    try:
        # Send initial snapshot immediately
        collector = get_rpa_metrics_collector()
        snapshot = MetricsSnapshot.from_collector(collector, environment)
        await websocket.send_json(
            {
                "type": "metrics",
                "timestamp": snapshot.timestamp,
                "data": snapshot.to_dict(),
            }
        )

        # Stream updates at configured interval
        while True:
            await asyncio.sleep(interval)

            try:
                snapshot = MetricsSnapshot.from_collector(collector, environment)
                await websocket.send_json(
                    {
                        "type": "metrics",
                        "timestamp": snapshot.timestamp,
                        "data": snapshot.to_dict(),
                    }
                )
            except Exception as e:
                logger.warning(f"Error sending metrics update: {e}")
                # Continue trying - connection may still be valid

    except WebSocketDisconnect:
        logger.debug("Metrics WebSocket client disconnected normally")
    except Exception as e:
        logger.warning(f"Metrics WebSocket error: {e}")
    finally:
        _metrics_ws_connections.discard(websocket)
        logger.info(
            f"Metrics WebSocket closed (remaining connections={len(_metrics_ws_connections)})"
        )


async def broadcast_metrics_to_websockets(data: Dict[str, Any]) -> None:
    """
    Broadcast metrics data to all connected WebSocket clients.

    Called by MetricsExporter to push updates to all dashboards.

    Args:
        data: Metrics data dictionary to broadcast
    """
    if not _metrics_ws_connections:
        return

    message = json.dumps(
        {
            "type": "metrics",
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }
    )

    disconnected = set()
    for ws in _metrics_ws_connections:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.add(ws)

    # Remove disconnected clients
    for ws in disconnected:
        _metrics_ws_connections.discard(ws)


def get_websocket_connection_count() -> int:
    """Get number of active WebSocket connections."""
    return len(_metrics_ws_connections)

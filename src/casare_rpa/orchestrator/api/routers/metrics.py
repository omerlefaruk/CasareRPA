"""
REST API endpoints for metrics and monitoring.

Provides fleet, robot, job, and analytics data for the React dashboard.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from loguru import logger

from ..models import (
    FleetMetrics,
    RobotSummary,
    RobotMetrics,
    JobSummary,
    JobDetails,
    AnalyticsSummary,
)
from ..dependencies import get_metrics_collector, get_db_pool


router = APIRouter()


@router.get("/metrics/fleet", response_model=FleetMetrics)
async def get_fleet_metrics(
    collector=Depends(get_metrics_collector),
):
    """
    Get fleet-wide metrics summary.

    Returns:
        - Total/active/idle/offline robot counts
        - Active jobs count
        - Queue depth
    """
    logger.debug("Fetching fleet metrics")

    try:
        data = collector.get_fleet_summary()
        return FleetMetrics(**data)
    except Exception as e:
        logger.error(f"Failed to fetch fleet metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch fleet metrics")


@router.get("/metrics/robots", response_model=List[RobotSummary])
async def get_robots(
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
    """
    logger.debug(f"Fetching robots list (status={status})")

    try:
        robots = collector.get_robot_list(status=status)
        return [RobotSummary(**robot) for robot in robots]
    except Exception as e:
        logger.error(f"Failed to fetch robots: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch robots")


@router.get("/metrics/robots/{robot_id}", response_model=RobotMetrics)
async def get_robot_details(
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
async def get_jobs(
    limit: int = Query(50, ge=1, le=500, description="Number of jobs to return"),
    status: Optional[str] = Query(
        None, description="Filter by status: pending, claimed, completed, failed"
    ),
    workflow_id: Optional[str] = Query(None, description="Filter by workflow ID"),
    robot_id: Optional[str] = Query(None, description="Filter by robot ID"),
    collector=Depends(get_metrics_collector),
    db_pool=Depends(get_db_pool),
):
    """
    Get job execution history with filtering and pagination.

    Query Parameters:
        - limit: Max number of jobs (default: 50, max: 500)
        - status: Filter by job status
        - workflow_id: Filter by workflow
        - robot_id: Filter by robot

    Returns paginated job history sorted by creation time (newest first).
    """
    logger.debug(
        f"Fetching jobs (limit={limit}, status={status}, workflow={workflow_id}, robot={robot_id})"
    )

    try:
        # Inject database pool into adapter for this request
        collector.set_db_pool(db_pool)

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
async def get_job_details(
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
    """
    logger.debug(f"Fetching job details: {job_id}")

    try:
        job = collector.get_job_details(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return JobDetails(**job)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch job details: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch job details")


@router.get("/metrics/analytics", response_model=AnalyticsSummary)
async def get_analytics(
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    collector=Depends(get_metrics_collector),
    db_pool=Depends(get_db_pool),
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
    """
    logger.debug(f"Fetching analytics (days={days})")

    try:
        # Inject database pool for database-backed analytics
        collector.set_db_pool(db_pool)

        # Use async method for accurate percentile calculations from database
        data = await collector.get_analytics_async(days=days)
        return AnalyticsSummary(**data)
    except Exception as e:
        logger.error(f"Failed to fetch analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

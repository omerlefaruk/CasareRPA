"""
Dependency injection for FastAPI endpoints.

Provides shared dependencies like database connections and metrics collectors.
"""

from typing import AsyncGenerator
from functools import lru_cache

from loguru import logger


@lru_cache
def get_metrics_collector():
    """
    Get the RPAMetricsCollector singleton instance.

    TODO: Import and return actual RPAMetricsCollector from infrastructure.
    For now, returns a mock object for development.
    """
    logger.warning("Using mock metrics collector - implement actual collector")

    class MockMetricsCollector:
        """Mock metrics collector for development."""

        def get_fleet_summary(self):
            return {
                "total_robots": 0,
                "active_robots": 0,
                "idle_robots": 0,
                "offline_robots": 0,
                "active_jobs": 0,
                "queue_depth": 0,
            }

        def get_robot_list(self, status=None):
            return []

        def get_robot_details(self, robot_id: str):
            return None

        def get_job_history(
            self, limit=50, status=None, workflow_id=None, robot_id=None
        ):
            return []

        def get_job_details(self, job_id: str):
            return None

        def get_analytics(self):
            return {
                "total_jobs": 0,
                "success_rate": 0.0,
                "failure_rate": 0.0,
                "average_duration_ms": 0.0,
                "p50_duration_ms": 0.0,
                "p90_duration_ms": 0.0,
                "p99_duration_ms": 0.0,
                "slowest_workflows": [],
                "error_distribution": [],
            }

    return MockMetricsCollector()


async def get_db_pool() -> AsyncGenerator:
    """
    Get database connection pool.

    TODO: Implement actual database connection pool.
    For now, yields None for development.
    """
    logger.warning("Using mock database pool - implement actual pool")
    yield None

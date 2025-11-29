"""
Dependency injection for FastAPI endpoints.

Provides shared dependencies like database connections and metrics collectors.
"""

import os
from typing import AsyncGenerator
from functools import lru_cache

from loguru import logger
import asyncpg

from casare_rpa.infrastructure.observability.metrics import (
    get_metrics_collector as get_rpa_metrics,
)
from casare_rpa.infrastructure.analytics.metrics_aggregator import MetricsAggregator
from .adapters import MonitoringDataAdapter


@lru_cache
def get_metrics_collector():
    """
    Get the monitoring data adapter (wraps RPAMetricsCollector + MetricsAggregator).

    Returns adapter that provides API-compatible interface to infrastructure metrics.
    """
    logger.info("Using MonitoringDataAdapter with PR #33 infrastructure")

    rpa_metrics = get_rpa_metrics()
    analytics = MetricsAggregator.get_instance()

    return MonitoringDataAdapter(rpa_metrics, analytics)


async def get_db_pool() -> AsyncGenerator:
    """
    Get database connection pool for PostgreSQL.

    Reads connection info from environment variables:
    - DB_HOST (default: localhost)
    - DB_PORT (default: 5432)
    - DB_NAME (default: casare_rpa)
    - DB_USER (default: postgres)
    - DB_PASSWORD (required)
    """
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5432"))
    database = os.getenv("DB_NAME", "casare_rpa")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    if not password:
        logger.warning("DB_PASSWORD not set - database queries will fail")

    try:
        pool = await asyncpg.create_pool(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            min_size=2,
            max_size=10,
        )
        logger.info(f"Database pool created: {database}@{host}:{port}")
        yield pool
    finally:
        if pool:
            await pool.close()

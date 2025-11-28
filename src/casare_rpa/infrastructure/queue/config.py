"""
PgQueuer Configuration.

Configuration management for the PgQueuer-based job queue system.
"""

import os
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class QueueConfig:
    """
    Configuration for PgQueuer job queue.

    Attributes:
        database_url: PostgreSQL connection string
        queue_name: Name of the queue (allows multiple queues)
        max_concurrent_jobs: Maximum jobs to process concurrently per robot
        visibility_timeout: Default visibility timeout in seconds
        poll_interval: How often to poll for jobs (seconds)
        max_retries: Default max retries before DLQ
        enable_dlq: Enable Dead Letter Queue
        batch_size: Number of jobs to fetch per poll
        connection_pool_size: Database connection pool size
    """

    database_url: str
    queue_name: str = "casare_rpa_jobs"
    max_concurrent_jobs: int = 3
    visibility_timeout: int = 30  # 30 seconds default
    poll_interval: float = 1.0  # 1 second poll interval
    max_retries: int = 3
    enable_dlq: bool = True
    batch_size: int = 10
    connection_pool_size: int = 10

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "QueueConfig":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional .env file path

        Returns:
            QueueConfig instance

        Environment Variables:
            PGQUEUER_DATABASE_URL: PostgreSQL connection string (required)
            PGQUEUER_QUEUE_NAME: Queue name (default: casare_rpa_jobs)
            PGQUEUER_MAX_CONCURRENT: Max concurrent jobs (default: 3)
            PGQUEUER_VISIBILITY_TIMEOUT: Visibility timeout seconds (default: 30)
            PGQUEUER_POLL_INTERVAL: Poll interval seconds (default: 1.0)
            PGQUEUER_MAX_RETRIES: Max retries (default: 3)
            PGQUEUER_ENABLE_DLQ: Enable DLQ (default: true)
        """
        if env_file:
            from dotenv import load_dotenv

            load_dotenv(env_file)

        database_url = os.getenv("PGQUEUER_DATABASE_URL") or os.getenv(
            "DBOS_DATABASE_URL"
        )
        if not database_url:
            raise ValueError(
                "PGQUEUER_DATABASE_URL or DBOS_DATABASE_URL environment variable required"
            )

        config = cls(
            database_url=database_url,
            queue_name=os.getenv("PGQUEUER_QUEUE_NAME", "casare_rpa_jobs"),
            max_concurrent_jobs=int(os.getenv("PGQUEUER_MAX_CONCURRENT", "3")),
            visibility_timeout=int(os.getenv("PGQUEUER_VISIBILITY_TIMEOUT", "30")),
            poll_interval=float(os.getenv("PGQUEUER_POLL_INTERVAL", "1.0")),
            max_retries=int(os.getenv("PGQUEUER_MAX_RETRIES", "3")),
            enable_dlq=os.getenv("PGQUEUER_ENABLE_DLQ", "true").lower() == "true",
            batch_size=int(os.getenv("PGQUEUER_BATCH_SIZE", "10")),
            connection_pool_size=int(os.getenv("PGQUEUER_POOL_SIZE", "10")),
        )

        logger.info(
            f"PgQueuer Config loaded: queue={config.queue_name}, "
            f"concurrent={config.max_concurrent_jobs}, "
            f"visibility_timeout={config.visibility_timeout}s"
        )

        return config

    @classmethod
    def from_supabase(
        cls,
        supabase_url: str,
        supabase_db_password: str,
        **kwargs,
    ) -> "QueueConfig":
        """
        Create configuration for Supabase.

        Args:
            supabase_url: Supabase project URL
            supabase_db_password: Database password
            **kwargs: Override default config values

        Returns:
            QueueConfig instance
        """
        # Extract project ref from URL
        project_ref = supabase_url.replace("https://", "").split(".")[0]

        database_url = (
            f"postgresql://postgres:{supabase_db_password}"
            f"@db.{project_ref}.supabase.co:5432/postgres"
        )

        return cls(database_url=database_url, **kwargs)

    @classmethod
    def from_local_postgres(
        cls,
        host: str = "localhost",
        port: int = 5432,
        database: str = "casare_rpa",
        user: str = "postgres",
        password: str = "postgres",
        **kwargs,
    ) -> "QueueConfig":
        """
        Create configuration for local PostgreSQL.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            **kwargs: Override default config values

        Returns:
            QueueConfig instance
        """
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        return cls(database_url=database_url, **kwargs)

    def to_connection_kwargs(self) -> dict:
        """
        Convert to asyncpg connection kwargs.

        Returns:
            Dictionary for asyncpg.create_pool()
        """
        from urllib.parse import urlparse

        parsed = urlparse(self.database_url)

        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip("/"),
            "min_size": 2,
            "max_size": self.connection_pool_size,
        }

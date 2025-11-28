"""
DBOS Configuration for Project Aether.

Manages DBOS runtime configuration, database connections, and environment setup.
Supports both local development (local Postgres) and cloud (Supabase).
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path
from loguru import logger


@dataclass
class DBOSConfig:
    """
    Configuration for DBOS runtime.

    Attributes:
        database_url: PostgreSQL connection string (Supabase or local)
        app_name: Application name for DBOS
        app_version: Application version
        log_level: Logging level for DBOS
        enable_local_mode: Run in local dev mode (no cloud dependencies)
    """

    database_url: str
    app_name: str = "casare-rpa-aether"
    app_version: str = "3.0.0"
    log_level: str = "INFO"
    enable_local_mode: bool = False

    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "DBOSConfig":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional .env file path

        Returns:
            DBOSConfig instance

        Environment Variables:
            DBOS_DATABASE_URL: PostgreSQL connection string
            DBOS_APP_NAME: Application name
            DBOS_LOG_LEVEL: Log level
            DBOS_LOCAL_MODE: Enable local dev mode (true/false)
        """
        # Load .env file if specified
        if env_file:
            from dotenv import load_dotenv

            load_dotenv(env_file)

        database_url = os.getenv("DBOS_DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DBOS_DATABASE_URL environment variable is required. "
                "Set it to your Supabase connection string or local Postgres URL."
            )

        config = cls(
            database_url=database_url,
            app_name=os.getenv("DBOS_APP_NAME", "casare-rpa-aether"),
            app_version=os.getenv("DBOS_APP_VERSION", "3.0.0"),
            log_level=os.getenv("DBOS_LOG_LEVEL", "INFO"),
            enable_local_mode=os.getenv("DBOS_LOCAL_MODE", "false").lower() == "true",
        )

        logger.info(
            f"DBOS Config loaded: app={config.app_name}, "
            f"local_mode={config.enable_local_mode}"
        )

        return config

    @classmethod
    def from_supabase(
        cls,
        supabase_url: str,
        supabase_key: str,
        supabase_db_password: str,
    ) -> "DBOSConfig":
        """
        Create configuration for Supabase connection.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key
            supabase_db_password: Supabase database password

        Returns:
            DBOSConfig instance

        Note:
            Supabase connection string format:
            postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
        """
        # Extract project ref from Supabase URL
        # e.g., https://abcdefgh.supabase.co -> abcdefgh
        project_ref = supabase_url.replace("https://", "").split(".")[0]

        database_url = (
            f"postgresql://postgres:{supabase_db_password}"
            f"@db.{project_ref}.supabase.co:5432/postgres"
        )

        return cls(database_url=database_url, enable_local_mode=False)

    @classmethod
    def from_local_postgres(
        cls,
        host: str = "localhost",
        port: int = 5432,
        database: str = "casare_rpa",
        user: str = "postgres",
        password: str = "postgres",
    ) -> "DBOSConfig":
        """
        Create configuration for local PostgreSQL.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password

        Returns:
            DBOSConfig instance
        """
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        return cls(database_url=database_url, enable_local_mode=True)

    def to_yaml_config(self) -> str:
        """
        Generate dbos.yaml configuration content.

        Returns:
            YAML configuration string
        """
        return f"""# DBOS Configuration for Project Aether
# See: https://docs.dbos.dev/api-reference/configuration

name: {self.app_name}
language: python
version: {self.app_version}

database:
  hostname: {self._parse_db_url()['host']}
  port: {self._parse_db_url()['port']}
  username: {self._parse_db_url()['user']}
  password: ${{{{DB_PASSWORD}}}}  # Load from environment
  app_db_name: {self._parse_db_url()['database']}

runtimeConfig:
  entrypoints:
    - casare_rpa.infrastructure.dbos.workflow_runner
  port: 8000

logging:
  logLevel: {self.log_level}
  logDir: logs
"""

    def _parse_db_url(self) -> dict:
        """Parse database URL into components."""
        # postgresql://user:password@host:port/database
        from urllib.parse import urlparse

        parsed = urlparse(self.database_url)

        return {
            "host": parsed.hostname or "localhost",
            "port": parsed.port or 5432,
            "user": parsed.username or "postgres",
            "password": parsed.password or "",
            "database": parsed.path.lstrip("/") or "postgres",
        }

    def create_yaml_file(self, path: Optional[Path] = None) -> Path:
        """
        Create dbos.yaml configuration file.

        Args:
            path: Optional custom path (defaults to project root)

        Returns:
            Path to created file
        """
        if path is None:
            # Default to project root
            path = Path(__file__).parents[4] / "dbos.yaml"

        path.write_text(self.to_yaml_config(), encoding="utf-8")
        logger.info(f"Created DBOS config at: {path}")

        return path

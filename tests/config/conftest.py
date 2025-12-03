"""
Fixtures for config module tests.

Provides:
- Environment variable manipulation fixtures
- Config cleanup between tests
"""

import os
import pytest
from typing import Dict, Generator
from unittest.mock import patch


@pytest.fixture
def clean_env() -> Generator[Dict[str, str], None, None]:
    """
    Fixture to provide a clean environment for config tests.

    Backs up and clears all CASARE/DB/SUPABASE env vars,
    restores them after test.

    Yields:
        Dict of original environment variables.
    """
    # Keys to clear for config testing
    config_keys = [
        # Database
        "DATABASE_URL",
        "POSTGRES_URL",
        "PGQUEUER_DB_URL",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_ENABLED",
        "DB_POOL_MIN_SIZE",
        "DB_POOL_MAX_SIZE",
        "DB_COMMAND_TIMEOUT",
        "DB_MAX_INACTIVE_LIFETIME",
        # Supabase
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY",
        # Security
        "API_SECRET",
        "JWT_SECRET_KEY",
        "JWT_EXPIRATION_SECONDS",
        "ROBOT_AUTH_ENABLED",
        "VERIFY_SSL",
        "CASARE_CA_CERT_PATH",
        "CASARE_CLIENT_CERT_PATH",
        "CASARE_CLIENT_KEY_PATH",
        # Orchestrator
        "ORCHESTRATOR_HOST",
        "HOST",
        "API_HOST",
        "ORCHESTRATOR_PORT",
        "PORT",
        "API_PORT",
        "ORCHESTRATOR_WORKERS",
        "WORKERS",
        "CORS_ORIGINS",
        "SSL_KEYFILE",
        "SSL_CERTFILE",
        # Robot
        "ROBOT_ID",
        "CASARE_ROBOT_ID",
        "ROBOT_NAME",
        "CASARE_ROBOT_NAME",
        "ROBOT_ENVIRONMENT",
        "CASARE_ENVIRONMENT",
        "ROBOT_MAX_CONCURRENT_JOBS",
        "CASARE_MAX_CONCURRENT_JOBS",
        "ROBOT_HEARTBEAT_INTERVAL",
        "CASARE_HEARTBEAT_INTERVAL",
        "ROBOT_CAPABILITIES",
        "CASARE_CAPABILITIES",
        "ROBOT_TAGS",
        "CASARE_TAGS",
        "RECONNECT_DELAY",
        "MAX_RECONNECT_DELAY",
        "CASARE_JOB_TIMEOUT",
        # Logging
        "LOG_LEVEL",
        "LOG_FILE",
        "LOG_ROTATION_SIZE_MB",
        "LOG_RETENTION_DAYS",
        # Queue
        "USE_MEMORY_QUEUE",
        "JOB_POLL_INTERVAL",
        "JOB_TIMEOUT_DEFAULT",
        # Timeouts
        "ROBOT_HEARTBEAT_TIMEOUT",
        "WS_PING_INTERVAL",
        "WS_SEND_TIMEOUT",
        # Rate limiting
        "RATE_LIMIT_ENABLED",
        "RATE_LIMIT_REQUESTS_PER_MINUTE",
        # Metrics
        "METRICS_ENABLED",
        "METRICS_COLLECTION_INTERVAL",
        "EVENT_HISTORY_SIZE",
        # Vault
        "VAULT_ADDR",
        "VAULT_TOKEN",
        "VAULT_ROLE_ID",
        "VAULT_SECRET_ID",
        # Storage
        "WORKFLOWS_DIR",
        "WORKFLOW_BACKUP_ENABLED",
        # Cloudflare
        "CASARE_API_URL",
        "CASARE_WEBHOOK_URL",
        "CASARE_ROBOT_WS_URL",
        # Development
        "DEBUG",
        "RELOAD",
        "TENANT_ID",
    ]

    # Backup existing values
    backup = {}
    for key in config_keys:
        if key in os.environ:
            backup[key] = os.environ[key]
            del os.environ[key]

    yield backup

    # Restore original values
    for key in config_keys:
        if key in os.environ:
            del os.environ[key]
    for key, value in backup.items():
        os.environ[key] = value


@pytest.fixture
def reset_config_cache() -> Generator[None, None, None]:
    """
    Fixture to reset config cache before and after each test.

    Ensures tests don't affect each other through cached config.
    """
    from casare_rpa.config.loader import reset_config_manager

    reset_config_manager()
    yield
    reset_config_manager()


@pytest.fixture
def env_vars(clean_env: Dict[str, str]) -> Generator[Dict[str, str], None, None]:
    """
    Fixture providing a helper dict for setting environment variables.

    Usage:
        def test_something(env_vars):
            os.environ["MY_VAR"] = "value"
            # test code...

    Automatically cleans up via clean_env dependency.

    Yields:
        Original environment backup (for reference if needed).
    """
    yield clean_env


@pytest.fixture
def sample_database_env(clean_env: Dict[str, str]) -> Generator[None, None, None]:
    """
    Set up sample database environment variables.

    Provides a complete set of database config env vars for testing.
    """
    os.environ["DB_HOST"] = "testhost"
    os.environ["DB_PORT"] = "5433"
    os.environ["DB_NAME"] = "testdb"
    os.environ["DB_USER"] = "testuser"
    os.environ["DB_PASSWORD"] = "testpass"
    os.environ["DB_POOL_MIN_SIZE"] = "1"
    os.environ["DB_POOL_MAX_SIZE"] = "5"
    yield


@pytest.fixture
def sample_supabase_env(clean_env: Dict[str, str]) -> Generator[None, None, None]:
    """
    Set up sample Supabase environment variables.
    """
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-anon-key"
    os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
    yield


@pytest.fixture
def sample_security_env(clean_env: Dict[str, str]) -> Generator[None, None, None]:
    """
    Set up sample security environment variables.
    """
    os.environ["API_SECRET"] = "super-secret-key"
    os.environ["JWT_EXPIRATION_SECONDS"] = "7200"
    os.environ["ROBOT_AUTH_ENABLED"] = "true"
    yield

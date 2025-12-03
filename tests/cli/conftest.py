"""
Fixtures for CLI module tests.

Provides:
- Typer test runner
- Mock database connections
- Environment variable setup
"""

import os
import pytest
from typing import Dict, Generator
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """
    Provides a Typer CLI test runner.

    Returns:
        CliRunner instance for invoking CLI commands.
    """
    return CliRunner()


@pytest.fixture
def clean_env() -> Generator[Dict[str, str], None, None]:
    """
    Fixture to provide a clean environment for CLI tests.

    Clears database and orchestrator env vars.

    Yields:
        Dict of original environment variables.
    """
    config_keys = [
        "DATABASE_URL",
        "POSTGRES_URL",
        "PGQUEUER_DB_URL",
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "JWT_DEV_MODE",
    ]

    backup = {}
    for key in config_keys:
        if key in os.environ:
            backup[key] = os.environ[key]
            del os.environ[key]

    yield backup

    for key in config_keys:
        if key in os.environ:
            del os.environ[key]
    for key, value in backup.items():
        os.environ[key] = value


@pytest.fixture
def mock_asyncpg_connect() -> Generator[AsyncMock, None, None]:
    """
    Mock asyncpg.connect for database tests.

    Yields:
        AsyncMock connection object.
    """
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.close = AsyncMock()

    with patch("asyncpg.connect", return_value=mock_conn) as mock_connect:
        yield mock_conn


@pytest.fixture
def mock_subprocess_run() -> Generator[Mock, None, None]:
    """
    Mock subprocess.run for CLI tests that spawn processes.

    Yields:
        Mock subprocess.run function.
    """
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        yield mock_run


@pytest.fixture
def sample_db_env(clean_env: Dict[str, str]) -> Generator[None, None, None]:
    """
    Set up sample database environment for CLI tests.
    """
    os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost:5432/testdb"
    yield


@pytest.fixture
def mock_path_exists() -> Generator[Mock, None, None]:
    """
    Mock Path.exists() to return True for SQL files.

    Yields:
        Mock that tracks Path.exists() calls.
    """
    with patch("pathlib.Path.exists", return_value=True) as mock_exists:
        yield mock_exists


@pytest.fixture
def mock_path_read_text() -> Generator[Mock, None, None]:
    """
    Mock Path.read_text() to return sample SQL content.

    Yields:
        Mock that returns SQL content.
    """
    sample_sql = (
        "-- Sample SQL\nCREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY);"
    )
    with patch("pathlib.Path.read_text", return_value=sample_sql) as mock_read:
        yield mock_read


@pytest.fixture
def mock_dotenv_load() -> Generator[Mock, None, None]:
    """
    Mock dotenv.load_dotenv to prevent actual .env loading.

    Yields:
        Mock load_dotenv function.
    """
    with patch("dotenv.load_dotenv") as mock_load:
        yield mock_load


@pytest.fixture
def mock_shutil_which() -> Generator[Mock, None, None]:
    """
    Mock shutil.which for cloudflared checks.

    Yields:
        Mock that returns a path.
    """
    with patch("shutil.which", return_value="/usr/local/bin/cloudflared") as mock_which:
        yield mock_which

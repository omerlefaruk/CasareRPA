"""
Tests for database CLI commands.

Tests db.py:
- setup command success
- setup command failure (missing URL)
- setup command with --url option
- setup command with --supabase flag
- SQL file execution
"""

import os
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from pathlib import Path


class TestSetupDbCommand:
    """Tests for 'db setup' CLI command."""

    def test_setup_db_success(
        self,
        cli_runner,
        sample_db_env,
        mock_asyncpg_connect,
        mock_path_exists,
        mock_path_read_text,
        mock_dotenv_load,
    ):
        """db setup succeeds with valid DATABASE_URL."""
        from casare_rpa.cli.db import app

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = None
            result = cli_runner.invoke(app, ["setup"])

        # Should not exit with error
        assert result.exit_code == 0 or "setup complete" in result.output.lower()

    def test_setup_db_missing_url_fails(self, cli_runner, clean_env, mock_dotenv_load):
        """db setup fails when DATABASE_URL not provided."""
        from casare_rpa.cli.db import app

        result = cli_runner.invoke(app, ["setup"])

        assert result.exit_code == 1
        assert (
            "No database URL" in result.output
            or "DATABASE_URL not set" in result.output
        )

    def test_setup_db_with_url_option(
        self,
        cli_runner,
        clean_env,
        mock_asyncpg_connect,
        mock_path_exists,
        mock_path_read_text,
        mock_dotenv_load,
    ):
        """db setup uses --url option when provided."""
        from casare_rpa.cli.db import app

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = None
            result = cli_runner.invoke(
                app, ["setup", "--url", "postgresql://user:pass@host:5432/db"]
            )

        # Should attempt setup with provided URL
        # Check it didn't fail with "No database URL"
        assert "No database URL" not in result.output

    def test_setup_db_masks_credentials(
        self,
        cli_runner,
        clean_env,
        mock_asyncpg_connect,
        mock_path_exists,
        mock_path_read_text,
        mock_dotenv_load,
    ):
        """db setup masks credentials in output."""
        from casare_rpa.cli.db import app

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = None
            result = cli_runner.invoke(
                app,
                [
                    "setup",
                    "--url",
                    "postgresql://secretuser:secretpass@myhost:5432/mydb",
                ],
            )

        # Password should not appear in output
        assert "secretpass" not in result.output
        # Host should appear (masked URL shows host part)
        assert "myhost" in result.output or result.exit_code == 0


class TestRunSqlFile:
    """Tests for run_sql_file helper function."""

    @pytest.mark.asyncio
    async def test_run_sql_file_success(self, tmp_path):
        """run_sql_file executes SQL from file."""
        from casare_rpa.cli.db import run_sql_file

        # Create test SQL file
        sql_file = tmp_path / "test.sql"
        sql_file.write_text("CREATE TABLE test (id INT);")

        mock_conn = AsyncMock()

        await run_sql_file(mock_conn, sql_file)

        mock_conn.execute.assert_called_once_with("CREATE TABLE test (id INT);")

    @pytest.mark.asyncio
    async def test_run_sql_file_not_found(self, tmp_path, capsys):
        """run_sql_file handles missing file gracefully."""
        from casare_rpa.cli.db import run_sql_file

        mock_conn = AsyncMock()
        nonexistent_file = tmp_path / "nonexistent.sql"

        await run_sql_file(mock_conn, nonexistent_file)

        # Should not call execute
        mock_conn.execute.assert_not_called()

        # Should output error message
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "error" in captured.out.lower()

    @pytest.mark.asyncio
    async def test_run_sql_file_execution_error(self, tmp_path, capsys):
        """run_sql_file handles SQL execution errors."""
        from casare_rpa.cli.db import run_sql_file

        sql_file = tmp_path / "bad.sql"
        sql_file.write_text("INVALID SQL SYNTAX")

        mock_conn = AsyncMock()
        mock_conn.execute.side_effect = Exception("syntax error")

        await run_sql_file(mock_conn, sql_file)

        captured = capsys.readouterr()
        assert "error" in captured.out.lower()


class TestSetupPostgresAsync:
    """Tests for _setup_postgres async function."""

    @pytest.mark.asyncio
    async def test_setup_postgres_connects(self):
        """_setup_postgres establishes database connection."""
        from casare_rpa.cli.db import _setup_postgres

        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.close = AsyncMock()

        with patch("asyncpg.connect", return_value=mock_conn) as mock_connect:
            with patch.object(Path, "exists", return_value=True):
                with patch.object(Path, "read_text", return_value="-- SQL"):
                    await _setup_postgres("postgresql://user:pass@host:5432/db")

        mock_connect.assert_called_once_with("postgresql://user:pass@host:5432/db")
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_setup_postgres_connection_failure(self, capsys):
        """_setup_postgres handles connection failure."""
        from casare_rpa.cli.db import _setup_postgres
        import typer

        with patch("asyncpg.connect", side_effect=Exception("connection refused")):
            with pytest.raises(typer.Exit):
                await _setup_postgres("postgresql://user:pass@badhost:5432/db")

        captured = capsys.readouterr()
        assert "connection" in captured.out.lower() or "failed" in captured.out.lower()

    @pytest.mark.asyncio
    async def test_setup_postgres_finds_schema_file(self):
        """_setup_postgres looks for schema file in correct locations."""
        from casare_rpa.cli.db import _setup_postgres

        mock_conn = AsyncMock()

        # Track which paths are checked
        checked_paths = []

        def track_exists(self):
            checked_paths.append(str(self))
            return "supabase_schema.sql" in str(self)

        with patch("asyncpg.connect", return_value=mock_conn):
            with patch.object(Path, "exists", track_exists):
                with patch.object(Path, "read_text", return_value="-- SQL"):
                    await _setup_postgres("postgresql://user:pass@host:5432/db")

        # Should check for supabase_schema.sql
        assert any("supabase_schema.sql" in p for p in checked_paths)


class TestDbCliIntegration:
    """Integration tests for db CLI."""

    def test_db_cli_help(self, cli_runner):
        """db CLI shows help."""
        from casare_rpa.cli.db import app

        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "setup" in result.output

    def test_setup_command_help(self, cli_runner):
        """setup command shows help."""
        from casare_rpa.cli.db import app

        result = cli_runner.invoke(app, ["setup", "--help"])

        assert result.exit_code == 0
        assert "--url" in result.output
        assert "--supabase" in result.output


class TestDbCliEdgeCases:
    """Edge case tests for db CLI."""

    def test_setup_with_empty_url_env(self, cli_runner, clean_env, mock_dotenv_load):
        """setup handles empty DATABASE_URL."""
        os.environ["DATABASE_URL"] = ""

        from casare_rpa.cli.db import app

        result = cli_runner.invoke(app, ["setup"])

        # Empty string should be treated as not set
        assert result.exit_code == 1

    def test_setup_with_postgres_url_fallback(
        self,
        cli_runner,
        clean_env,
        mock_asyncpg_connect,
        mock_path_exists,
        mock_path_read_text,
        mock_dotenv_load,
    ):
        """setup falls back to POSTGRES_URL if DATABASE_URL not set."""
        os.environ["POSTGRES_URL"] = "postgresql://user:pass@host:5432/db"

        from casare_rpa.cli.db import app

        with patch("asyncio.run") as mock_run:
            mock_run.return_value = None
            result = cli_runner.invoke(app, ["setup"])

        # Should succeed using POSTGRES_URL
        assert "No database URL" not in result.output

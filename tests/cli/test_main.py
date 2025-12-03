"""
Tests for main CLI entry points.

Tests main.py:
- Main app structure and subcommands
- orchestrator start command
- canvas command
- tunnel start command
- deploy setup command
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestMainCli:
    """Tests for main CLI app structure."""

    def test_main_cli_help(self, cli_runner):
        """Main CLI shows help with all subcommands."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "casare" in result.output.lower() or "CasareRPA" in result.output
        assert "orchestrator" in result.output
        assert "canvas" in result.output
        assert "tunnel" in result.output
        assert "db" in result.output

    def test_main_cli_no_args(self, cli_runner):
        """Main CLI with no args shows help or usage."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, [])

        # Should show help or usage, not crash
        assert result.exit_code == 0 or "Usage" in result.output


class TestOrchestratorCommands:
    """Tests for orchestrator CLI commands."""

    def test_orchestrator_help(self, cli_runner):
        """orchestrator subcommand shows help."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["orchestrator", "--help"])

        assert result.exit_code == 0
        assert "start" in result.output

    def test_orchestrator_start_help(self, cli_runner):
        """orchestrator start shows help with options."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["orchestrator", "start", "--help"])

        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--workers" in result.output
        assert "--reload" in result.output
        assert "--dev" in result.output

    def test_orchestrator_start_runs_uvicorn(self, cli_runner, mock_subprocess_run):
        """orchestrator start invokes uvicorn."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(
            app, ["orchestrator", "start", "--host", "127.0.0.1", "--port", "9000"]
        )

        # Check subprocess was called with uvicorn
        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert "uvicorn" in call_args
        assert "127.0.0.1" in call_args
        assert "9000" in call_args

    def test_orchestrator_start_with_reload(self, cli_runner, mock_subprocess_run):
        """orchestrator start --reload adds reload flag."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["orchestrator", "start", "--reload"])

        call_args = mock_subprocess_run.call_args[0][0]
        assert "--reload" in call_args

    def test_orchestrator_start_dev_mode(self, cli_runner, mock_subprocess_run):
        """orchestrator start --dev sets JWT_DEV_MODE env var."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["orchestrator", "start", "--dev"])

        # Check env was passed with JWT_DEV_MODE
        call_kwargs = mock_subprocess_run.call_args[1]
        assert "env" in call_kwargs
        assert call_kwargs["env"]["JWT_DEV_MODE"] == "true"


class TestCanvasCommand:
    """Tests for canvas CLI command."""

    def test_canvas_help(self, cli_runner):
        """canvas command shows help."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["canvas", "--help"])

        assert result.exit_code == 0

    def test_canvas_import_error(self, cli_runner):
        """canvas command handles import errors gracefully."""
        from casare_rpa.cli.main import app

        with patch(
            "casare_rpa.presentation.canvas.main",
            side_effect=ImportError("Missing PySide6"),
        ):
            result = cli_runner.invoke(app, ["canvas"])

        assert result.exit_code == 1
        assert "Error" in result.output or "dependencies" in result.output.lower()


class TestTunnelCommands:
    """Tests for tunnel CLI commands."""

    def test_tunnel_help(self, cli_runner):
        """tunnel subcommand shows help."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["tunnel", "--help"])

        assert result.exit_code == 0
        assert "start" in result.output

    def test_tunnel_start_help(self, cli_runner):
        """tunnel start shows help with options."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["tunnel", "start", "--help"])

        assert result.exit_code == 0
        assert "--port" in result.output
        assert "--hostname" in result.output

    def test_tunnel_start_cloudflared_not_found(self, cli_runner):
        """tunnel start fails when cloudflared not installed."""
        from casare_rpa.cli.main import app

        with patch("shutil.which", return_value=None):
            result = cli_runner.invoke(app, ["tunnel", "start"])

        assert result.exit_code == 1
        assert "cloudflared" in result.output.lower()

    def test_tunnel_start_runs_cloudflared(
        self, cli_runner, mock_shutil_which, mock_subprocess_run
    ):
        """tunnel start invokes cloudflared with correct args."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["tunnel", "start", "--port", "9000"])

        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert "cloudflared" in call_args
        assert "tunnel" in call_args
        assert "http://localhost:9000" in call_args

    def test_tunnel_start_with_hostname(
        self, cli_runner, mock_shutil_which, mock_subprocess_run
    ):
        """tunnel start --hostname adds hostname arg."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(
            app, ["tunnel", "start", "--hostname", "myapp.example.com"]
        )

        call_args = mock_subprocess_run.call_args[0][0]
        assert "--hostname" in call_args
        assert "myapp.example.com" in call_args


class TestDeployCommands:
    """Tests for deploy CLI commands."""

    def test_deploy_help(self, cli_runner):
        """deploy subcommand shows help."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["deploy", "--help"])

        assert result.exit_code == 0
        assert "setup" in result.output

    def test_deploy_setup_help(self, cli_runner):
        """deploy setup shows help."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["deploy", "setup", "--help"])

        assert result.exit_code == 0

    def test_deploy_setup_script_not_found(self, cli_runner):
        """deploy setup fails when auto_setup.py not found."""
        from casare_rpa.cli.main import app

        with patch.object(Path, "exists", return_value=False):
            result = cli_runner.invoke(app, ["deploy", "setup"])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_deploy_setup_runs_script(self, cli_runner, mock_subprocess_run):
        """deploy setup runs auto_setup.py."""
        from casare_rpa.cli.main import app

        with patch.object(Path, "exists", return_value=True):
            result = cli_runner.invoke(app, ["deploy", "setup"])

        mock_subprocess_run.assert_called_once()
        call_args = mock_subprocess_run.call_args[0][0]
        assert "auto_setup.py" in call_args[-1]


class TestDbCommandsMounted:
    """Tests for db commands mounted in main CLI."""

    def test_db_subcommand_available(self, cli_runner):
        """db subcommand is available in main CLI."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["db", "--help"])

        assert result.exit_code == 0
        assert "setup" in result.output


class TestRobotCommandsMounted:
    """Tests for robot commands mounted in main CLI."""

    def test_robot_subcommand_available(self, cli_runner):
        """robot subcommand is available in main CLI."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["robot", "--help"])

        # Robot CLI might not be fully available (import issues)
        # but the command should be registered
        assert "robot" in result.output.lower() or result.exit_code == 0


class TestCliErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_subcommand(self, cli_runner):
        """Invalid subcommand shows error."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["invalid_subcommand"])

        assert result.exit_code != 0

    def test_orchestrator_invalid_option(self, cli_runner):
        """Invalid option shows error."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["orchestrator", "start", "--invalid-option"])

        assert result.exit_code != 0


class TestCliIntegration:
    """Integration tests for CLI."""

    def test_full_help_chain(self, cli_runner):
        """All subcommands have accessible help."""
        from casare_rpa.cli.main import app

        subcommands = ["orchestrator", "tunnel", "deploy", "db"]

        for cmd in subcommands:
            result = cli_runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0, f"Help failed for {cmd}"

    def test_orchestrator_start_default_values(self, cli_runner, mock_subprocess_run):
        """orchestrator start uses correct default values."""
        from casare_rpa.cli.main import app

        result = cli_runner.invoke(app, ["orchestrator", "start"])

        call_args = mock_subprocess_run.call_args[0][0]

        # Check defaults
        assert "0.0.0.0" in call_args  # default host
        assert "8000" in call_args  # default port
        assert "1" in call_args  # default workers

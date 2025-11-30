"""Tests for Robot CLI Playwright auto-install functionality."""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestEnsurePlaywrightBrowsers:
    """Test _ensure_playwright_browsers function."""

    def test_returns_true_when_browsers_available(self):
        """Test returns True when Playwright browsers are already installed."""
        mock_browser = MagicMock()
        mock_playwright = MagicMock()
        mock_playwright.chromium.launch.return_value = mock_browser

        with patch("playwright.sync_api.sync_playwright") as mock_sync:
            mock_sync.return_value.__enter__.return_value = mock_playwright

            from casare_rpa.robot.cli import _ensure_playwright_browsers

            result = _ensure_playwright_browsers()

            assert result is True
            mock_browser.close.assert_called_once()

    def test_auto_installs_when_browsers_missing(self):
        """Test auto-installs browsers when executable doesn't exist."""
        with (
            patch("playwright.sync_api.sync_playwright") as mock_sync,
            patch("subprocess.run") as mock_subprocess,
            patch("casare_rpa.robot.cli.console"),
        ):
            # Mock Playwright to raise "Executable doesn't exist" error
            mock_sync.return_value.__enter__.side_effect = Exception(
                "Executable doesn't exist at /path/to/chromium"
            )

            # Mock subprocess.run for successful install
            mock_subprocess.return_value = MagicMock(returncode=0, stderr="")

            from casare_rpa.robot.cli import _ensure_playwright_browsers

            result = _ensure_playwright_browsers()

            assert result is True
            mock_subprocess.assert_called_once_with(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                capture_output=True,
                text=True,
                timeout=300,
            )

    def test_returns_false_when_install_fails(self):
        """Test returns False when browser installation fails."""
        with (
            patch("playwright.sync_api.sync_playwright") as mock_sync,
            patch("subprocess.run") as mock_subprocess,
            patch("casare_rpa.robot.cli.console"),
            patch("casare_rpa.robot.cli.logger"),
        ):
            # Mock Playwright to raise error
            mock_sync.return_value.__enter__.side_effect = Exception(
                "playwright install"
            )

            # Mock subprocess.run for failed install
            mock_subprocess.return_value = MagicMock(
                returncode=1, stderr="Installation failed"
            )

            from casare_rpa.robot.cli import _ensure_playwright_browsers

            result = _ensure_playwright_browsers()

            assert result is False

    def test_returns_false_on_install_timeout(self):
        """Test returns False when installation times out."""
        with (
            patch("playwright.sync_api.sync_playwright") as mock_sync,
            patch("subprocess.run") as mock_subprocess,
            patch("casare_rpa.robot.cli.console"),
        ):
            # Mock Playwright to raise error
            mock_sync.return_value.__enter__.side_effect = Exception(
                "Executable doesn't exist"
            )

            # Mock subprocess.run to timeout
            mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="", timeout=300)

            from casare_rpa.robot.cli import _ensure_playwright_browsers

            result = _ensure_playwright_browsers()

            assert result is False

    def test_continues_on_non_browser_error(self):
        """Test continues (returns True) on non-browser Playwright errors."""
        with (
            patch("playwright.sync_api.sync_playwright") as mock_sync,
            patch("casare_rpa.robot.cli.logger"),
        ):
            # Mock Playwright to raise a different error
            mock_sync.return_value.__enter__.side_effect = Exception(
                "Some other error not related to missing browsers"
            )

            from casare_rpa.robot.cli import _ensure_playwright_browsers

            result = _ensure_playwright_browsers()

            # Should return True to allow non-browser workflows
            assert result is True

    def test_truncates_long_stderr_output(self):
        """Test truncates long stderr for user display."""
        with (
            patch("playwright.sync_api.sync_playwright") as mock_sync,
            patch("subprocess.run") as mock_subprocess,
            patch("casare_rpa.robot.cli.console") as mock_console,
            patch("casare_rpa.robot.cli.logger") as mock_logger,
        ):
            # Mock Playwright to raise error
            mock_sync.return_value.__enter__.side_effect = Exception(
                "Executable doesn't exist"
            )

            # Mock subprocess.run with long stderr
            long_stderr = "E" * 500  # 500 character error message
            mock_subprocess.return_value = MagicMock(returncode=1, stderr=long_stderr)

            from casare_rpa.robot.cli import _ensure_playwright_browsers

            result = _ensure_playwright_browsers()

            assert result is False

            # Verify console got truncated message
            console_call = mock_console.print.call_args_list[-1]
            console_msg = console_call[0][0]
            assert "..." in console_msg  # Truncated
            assert len(console_msg) < 300  # Not too long

            # Verify logger got full message
            mock_logger.error.assert_called_once()
            logger_msg = mock_logger.error.call_args[0][0]
            assert long_stderr in logger_msg  # Full error

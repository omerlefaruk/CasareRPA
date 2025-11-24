"""
Tests for robot/tray_icon.py - System tray icon functionality.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio


class TestRobotTrayApp:
    """Test RobotTrayApp class."""

    @pytest.fixture
    def mock_qt_app(self):
        """Mock QApplication to avoid GUI initialization."""
        with patch('casare_rpa.robot.tray_icon.QApplication') as mock:
            mock.return_value = MagicMock()
            yield mock

    @pytest.fixture
    def mock_tray_icon(self):
        """Mock QSystemTrayIcon."""
        with patch('casare_rpa.robot.tray_icon.QSystemTrayIcon') as mock:
            yield mock

    @pytest.fixture
    def mock_agent(self):
        """Mock RobotAgent."""
        with patch('casare_rpa.robot.tray_icon.RobotAgent') as mock:
            agent_instance = MagicMock()
            agent_instance.name = "TestRobot"
            agent_instance.connected = False
            agent_instance.running = False
            mock.return_value = agent_instance
            yield mock

    @pytest.fixture
    def mock_playwright_setup(self):
        """Mock Playwright setup."""
        with patch('casare_rpa.robot.tray_icon.ensure_playwright_ready') as mock:
            mock.return_value = True
            yield mock

    def test_tray_app_imports(self):
        """Test that tray app module can be imported."""
        from casare_rpa.robot import tray_icon
        assert hasattr(tray_icon, 'RobotTrayApp')
        assert hasattr(tray_icon, 'main')

    def test_tray_app_initialization(self, mock_qt_app, mock_tray_icon, mock_agent):
        """Test RobotTrayApp initialization."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()

        # Should create QApplication
        mock_qt_app.assert_called_once()

        # Should create agent
        mock_agent.assert_called_once()

        # Should create tray icon
        mock_tray_icon.assert_called_once()

    def test_tray_app_has_menu(self, mock_qt_app, mock_tray_icon, mock_agent):
        """Test that tray app has a context menu."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()

        assert hasattr(tray, 'menu')
        assert hasattr(tray, 'status_action')
        assert hasattr(tray, 'exit_action')

    def test_tray_app_tooltip_includes_agent_name(self, mock_qt_app, mock_tray_icon, mock_agent):
        """Test that tray tooltip includes agent name."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()

        # Check setToolTip was called with agent name
        tray.tray_icon.setToolTip.assert_called()
        call_args = tray.tray_icon.setToolTip.call_args[0][0]
        assert "TestRobot" in call_args

    def test_exit_app(self, mock_qt_app, mock_tray_icon, mock_agent):
        """Test exit_app stops agent and quits app."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()
        tray.exit_app()

        # Should stop agent
        tray.agent.stop.assert_called_once()

        # Should quit app
        tray.app.quit.assert_called_once()


class TestRobotTrayAppAsync:
    """Test async methods of RobotTrayApp."""

    @pytest.fixture
    def mock_setup(self):
        """Setup all mocks for async tests."""
        with patch('casare_rpa.robot.tray_icon.QApplication') as mock_app, \
             patch('casare_rpa.robot.tray_icon.QSystemTrayIcon') as mock_tray, \
             patch('casare_rpa.robot.tray_icon.RobotAgent') as mock_agent, \
             patch('casare_rpa.robot.tray_icon.ensure_playwright_ready') as mock_pw, \
             patch('casare_rpa.robot.tray_icon.QMessageBox'):

            agent_instance = MagicMock()
            agent_instance.name = "TestRobot"
            agent_instance.connected = False
            agent_instance.running = True
            agent_instance.start = AsyncMock()
            mock_agent.return_value = agent_instance
            mock_pw.return_value = True

            yield {
                'app': mock_app,
                'tray': mock_tray,
                'agent': mock_agent,
                'playwright': mock_pw
            }

    @pytest.mark.asyncio
    async def test_run_starts_agent(self, mock_setup):
        """Test that run() starts the agent."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()

        # Create a task that will be cancelled quickly
        async def run_with_timeout():
            run_task = asyncio.create_task(tray.run())
            await asyncio.sleep(0.1)
            tray.exit_app()
            try:
                await asyncio.wait_for(run_task, timeout=0.5)
            except asyncio.TimeoutError:
                run_task.cancel()

        await run_with_timeout()

        # Agent start should have been called
        tray.agent.start.assert_called()

    @pytest.mark.asyncio
    async def test_run_fails_without_playwright(self, mock_setup):
        """Test that run() fails gracefully without Playwright."""
        mock_setup['playwright'].return_value = False

        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()

        # Run should complete without error
        await asyncio.wait_for(tray.run(), timeout=1.0)

        # App should quit
        tray.app.quit.assert_called()

    @pytest.mark.asyncio
    async def test_update_status_online(self, mock_setup):
        """Test status updates when connected."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()
        tray.agent.connected = True
        tray.agent.running = True

        # Replace status_action with a mock
        mock_status_action = MagicMock()
        tray.status_action = mock_status_action

        # Run update once
        update_task = asyncio.create_task(tray.update_status())
        await asyncio.sleep(0.1)
        update_task.cancel()

        # Should show online status
        mock_status_action.setText.assert_called()

    @pytest.mark.asyncio
    async def test_update_status_connecting(self, mock_setup):
        """Test status updates when connecting."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()
        tray.agent.connected = False
        tray.agent.running = True

        # Replace status_action with a mock
        mock_status_action = MagicMock()
        tray.status_action = mock_status_action

        # Run update once
        update_task = asyncio.create_task(tray.update_status())
        await asyncio.sleep(0.1)
        update_task.cancel()

        # Status should be updated
        mock_status_action.setText.assert_called()

    @pytest.mark.asyncio
    async def test_update_status_stopped(self, mock_setup):
        """Test status updates when stopped."""
        from casare_rpa.robot.tray_icon import RobotTrayApp

        tray = RobotTrayApp()
        tray.agent.connected = False
        tray.agent.running = False

        # Replace status_action with a mock
        mock_status_action = MagicMock()
        tray.status_action = mock_status_action

        # Run update once
        update_task = asyncio.create_task(tray.update_status())
        await asyncio.sleep(0.1)
        update_task.cancel()

        # Status should be updated
        mock_status_action.setText.assert_called()


class TestTrayIconMain:
    """Test main entry point."""

    def test_main_function_exists(self):
        """Test that main function exists."""
        from casare_rpa.robot.tray_icon import main
        assert callable(main)

"""
System Tray Icon for CasareRPA Robot
"""

import asyncio
import sys

from dotenv import load_dotenv

load_dotenv()
import qasync
from loguru import logger
from PySide6.QtCore import QObject
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

from casare_rpa.robot.agent import RobotAgent, RobotConfig

# Try to import playwright setup, fall back to internal check
try:
    from casare_rpa.utils.playwright_setup import ensure_playwright_ready
except ImportError:

    def ensure_playwright_ready() -> bool:
        """Fallback playwright check."""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            return True
        except Exception:
            return False


class RobotTrayApp(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Initialize Agent with config from environment
        config = RobotConfig.from_env()
        self.agent = RobotAgent(config)

        # Setup Tray Icon
        self.tray_icon = QSystemTrayIcon(self.app)
        # Uses system theme icon as placeholder; custom icon can be loaded from assets
        self.tray_icon.setIcon(QIcon.fromTheme("computer"))
        self.tray_icon.setToolTip(f"CasareRPA Robot: {self.agent.name}")

        # Menu
        self.menu = QMenu()

        self.status_action = QAction("Status: Starting...", self.menu)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)

        self.menu.addSeparator()

        self.exit_action = QAction("Exit", self.menu)
        self.exit_action.triggered.connect(self.exit_app)
        self.menu.addAction(self.exit_action)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.show()

        logger.info("Tray application initialized.")

    def exit_app(self):
        logger.info("Exit requested.")
        self.agent.stop()
        if hasattr(self, "_exit_future"):
            self._exit_future.set_result(True)
        self.app.quit()

    async def run(self):
        """Run the application loop."""
        # Check and install Playwright browsers if needed
        logger.info("Checking Playwright browsers...")
        self.status_action.setText("Status: Checking browsers...")

        if not ensure_playwright_ready():
            # Show error message
            QMessageBox.critical(
                None,
                "Browser Installation Failed",
                "Failed to install Playwright browsers. Please check your internet connection and try again.",
            )
            self.app.quit()
            return

        # Start Agent in background
        asyncio.create_task(self.agent.start())

        # Update status loop
        asyncio.create_task(self.update_status())

        # Keep running until exit requested
        self._exit_future = asyncio.Future()
        await self._exit_future

    async def update_status(self):
        """Periodically update tray status."""
        while True:
            if self.agent.connected:
                self.status_action.setText("Status: Online")
            elif self.agent.running:
                self.status_action.setText("Status: Connecting...")
            else:
                self.status_action.setText("Status: Stopped")
            await asyncio.sleep(1)


def main():
    tray = RobotTrayApp()
    try:
        qasync.run(tray.run())
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    main()

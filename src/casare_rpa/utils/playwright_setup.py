"""
Playwright Browser Auto-Setup
Automatically installs Playwright browsers on first run.
Provides GUI dialogs when running in Canvas, silent install for Robot.
"""

import subprocess
import sys
import os
from pathlib import Path
from loguru import logger


def get_playwright_browsers_path() -> Path:
    """Get the path where Playwright stores browser binaries."""
    if sys.platform == "win32":
        local_appdata = os.environ.get("LOCALAPPDATA", "")
        if local_appdata:
            return Path(local_appdata) / "ms-playwright"
    return Path.home() / ".cache" / "ms-playwright"


def check_playwright_browsers() -> bool:
    """Check if Playwright browsers are installed."""
    browser_path = get_playwright_browsers_path()

    if not browser_path.exists():
        return False

    # Check specifically for chromium
    try:
        for item in browser_path.iterdir():
            if item.is_dir() and item.name.startswith("chromium-"):
                logger.debug(f"Found Chromium at: {item}")
                return True
    except Exception as e:
        logger.warning(f"Error checking browser path: {e}")

    return False


def install_playwright_browsers_silent() -> bool:
    """Install Playwright browsers silently (no GUI)."""
    logger.info("Installing Playwright browsers (this may take a few minutes)...")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        logger.info("Playwright browsers installed successfully!")
        logger.debug(f"Installation output: {result.stdout}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Playwright browsers: {e.stderr}")
        return False
    except subprocess.TimeoutExpired:
        logger.error("Browser installation timed out.")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during browser installation: {e}")
        return False


def install_playwright_browsers_gui(parent=None) -> bool:
    """
    Install Playwright browsers with GUI progress dialog.

    Args:
        parent: Parent widget for dialogs

    Returns:
        True if installation succeeded
    """
    try:
        from PySide6.QtWidgets import (
            QMessageBox,
            QDialog,
            QVBoxLayout,
            QLabel,
            QProgressBar,
            QApplication,
        )
        from PySide6.QtCore import Qt, QThread, Signal, QTimer

        class InstallWorker(QThread):
            """Worker thread for browser installation."""

            progress_update = Signal(str)
            finished_signal = Signal(bool, str)

            def run(self):
                try:
                    self.progress_update.emit("Starting Chromium browser download...")

                    process = subprocess.Popen(
                        [sys.executable, "-m", "playwright", "install", "chromium"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )

                    # Read output line by line
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            # Parse progress from playwright output
                            if "Downloading" in line:
                                self.progress_update.emit(line)
                            elif "%" in line:
                                self.progress_update.emit(line)
                            else:
                                self.progress_update.emit(line)

                    process.wait(timeout=600)

                    if process.returncode == 0:
                        self.finished_signal.emit(True, "Installation complete!")
                    else:
                        self.finished_signal.emit(
                            False,
                            f"Installation failed (exit code: {process.returncode})",
                        )

                except subprocess.TimeoutExpired:
                    self.finished_signal.emit(False, "Installation timed out")
                except Exception as e:
                    self.finished_signal.emit(False, str(e))

        class InstallDialog(QDialog):
            """Progress dialog for browser installation."""

            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("Installing Browser")
                self.setModal(True)
                self.setMinimumWidth(450)
                self.setMinimumHeight(120)
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

                layout = QVBoxLayout(self)
                layout.setSpacing(15)

                # Title
                title = QLabel("Installing Playwright Chromium Browser")
                title.setStyleSheet("font-weight: bold; font-size: 14px;")
                layout.addWidget(title)

                # Status label
                self.status_label = QLabel("Preparing download...")
                self.status_label.setWordWrap(True)
                layout.addWidget(self.status_label)

                # Progress bar (indeterminate)
                self.progress_bar = QProgressBar()
                self.progress_bar.setRange(0, 0)
                layout.addWidget(self.progress_bar)

                # Info label
                info = QLabel("This may take a few minutes depending on your internet connection.")
                info.setStyleSheet("color: gray; font-size: 11px;")
                layout.addWidget(info)

                self._success = False
                self._worker = None

            def start_installation(self):
                """Start the installation in background thread."""
                self._worker = InstallWorker()
                self._worker.progress_update.connect(self._on_progress)
                self._worker.finished_signal.connect(self._on_finished)
                self._worker.start()

            def _on_progress(self, message: str):
                self.status_label.setText(message)
                QApplication.processEvents()

            def _on_finished(self, success: bool, message: str):
                self._success = success
                self.status_label.setText(message)
                # Small delay before closing
                QTimer.singleShot(500, self.accept)

            @property
            def success(self) -> bool:
                return self._success

        # Show the installation dialog
        dialog = InstallDialog(parent)
        dialog.start_installation()
        dialog.exec()

        return dialog.success

    except ImportError:
        logger.warning("PySide6 not available, falling back to silent install")
        return install_playwright_browsers_silent()
    except Exception as e:
        logger.error(f"GUI installation error: {e}")
        return install_playwright_browsers_silent()


def ensure_playwright_ready(show_gui: bool = True, parent=None) -> bool:
    """
    Ensure Playwright browsers are installed, install if missing.

    Args:
        show_gui: Whether to show GUI dialogs (True for Canvas, False for Robot)
        parent: Parent widget for dialogs

    Returns:
        True if browsers are ready, False if installation failed or user declined
    """
    if check_playwright_browsers():
        logger.info("Playwright browsers already installed")
        return True

    logger.warning("Playwright browsers not found")

    if not show_gui:
        logger.info("Installing Playwright browsers silently...")
        return install_playwright_browsers_silent()

    # Try to show GUI dialog
    try:
        from PySide6.QtWidgets import QMessageBox

        # Ask user permission first
        reply = QMessageBox.question(
            parent,
            "Browser Installation Required",
            "CasareRPA needs to download the Chromium browser for web automation.\n\n"
            "This is a one-time download of approximately 150-200 MB.\n\n"
            "Would you like to install it now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply != QMessageBox.Yes:
            logger.info("User declined browser installation")
            QMessageBox.information(
                parent,
                "Browser Not Installed",
                "Web automation features will not work until the browser is installed.\n\n"
                "You can install it later by restarting the application.",
            )
            return False

        # Install with progress dialog
        success = install_playwright_browsers_gui(parent)

        if success:
            QMessageBox.information(
                parent,
                "Installation Complete",
                "Chromium browser has been installed successfully!\n\n"
                "You can now use web automation features.",
            )
        else:
            QMessageBox.warning(
                parent,
                "Installation Failed",
                "Failed to install the browser.\n\n"
                "You can try again by restarting the application,\n"
                "or run this command manually:\n\n"
                "playwright install chromium",
            )

        return success

    except ImportError:
        logger.warning("PySide6 not available, installing silently")
        return install_playwright_browsers_silent()
    except Exception as e:
        logger.error(f"Error showing installation dialog: {e}")
        return install_playwright_browsers_silent()

"""
Update Dialog UI Component.

Modal dialog for application update notifications and downloads.
Integrates with TUF UpdateManager for secure software updates.
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.infrastructure.updater.tuf_updater import (
    DownloadProgress,
    UpdateInfo,
)
from casare_rpa.infrastructure.updater.update_manager import (
    UpdateManager,
)


class UpdateDialog(QDialog):
    """
    Application update notification and download dialog.

    Features:
    - Display update availability with version info
    - Show release notes
    - Download progress with speed indicator
    - Skip version / Remind later options
    - Restart prompt after download

    Signals:
        update_accepted: Emitted when user clicks Download/Install
        update_skipped: Emitted when user clicks Skip This Version
        update_postponed: Emitted when user clicks Remind Later
    """

    update_accepted = Signal()
    update_skipped = Signal(str)  # version
    update_postponed = Signal()

    def __init__(
        self,
        update_info: UpdateInfo,
        update_manager: UpdateManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize update dialog.

        Args:
            update_info: Information about the available update
            update_manager: Optional update manager for download/install
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._update_info = update_info
        self._update_manager = update_manager
        self._is_downloading = False
        self._download_complete = False

        self.setWindowTitle("Update Available")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        logger.info(f"UpdateDialog opened for version {update_info.version}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header with icon and title
        header_layout = QHBoxLayout()

        # Update icon (using Unicode for simplicity)
        icon_label = QLabel("\u2b06")  # Up arrow
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet("color: #4CAF50;")
        header_layout.addWidget(icon_label)

        # Title and version info
        title_layout = QVBoxLayout()
        title_label = QLabel("A new version is available!")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)

        version_label = QLabel(f"Version {self._update_info.version} is ready to download")
        title_layout.addWidget(version_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Update details group
        details_group = QGroupBox("Update Details")
        details_layout = QVBoxLayout()

        # Size info
        size_mb = self._update_info.size_bytes / (1024 * 1024)
        size_label = QLabel(f"Download size: {size_mb:.1f} MB")
        details_layout.addWidget(size_label)

        # Release date
        if self._update_info.release_date:
            date_str = self._update_info.release_date.strftime("%B %d, %Y")
            date_label = QLabel(f"Released: {date_str}")
            details_layout.addWidget(date_label)

        # Critical update indicator
        if self._update_info.is_critical:
            critical_label = QLabel("\u26a0 This is a critical security update")
            critical_label.setStyleSheet("color: #FFA726; font-weight: bold; padding: 4px;")
            details_layout.addWidget(critical_label)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Release notes group
        if self._update_info.release_notes:
            notes_group = QGroupBox("What's New")
            notes_layout = QVBoxLayout()

            self._notes_text = QTextEdit()
            self._notes_text.setReadOnly(True)
            self._notes_text.setPlainText(self._update_info.release_notes)
            self._notes_text.setMaximumHeight(150)
            notes_layout.addWidget(self._notes_text)

            notes_group.setLayout(notes_layout)
            layout.addWidget(notes_group)

        # Progress section (initially hidden)
        self._progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout()

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("Preparing download...")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self._progress_label)

        self._progress_group.setLayout(progress_layout)
        self._progress_group.setVisible(False)
        layout.addWidget(self._progress_group)

        # Buttons
        button_layout = QHBoxLayout()

        self._skip_button = QPushButton("Skip This Version")
        self._skip_button.setToolTip("Don't notify about this version again")
        button_layout.addWidget(self._skip_button)

        self._remind_button = QPushButton("Remind Later")
        self._remind_button.setToolTip("Close and remind on next check")
        button_layout.addWidget(self._remind_button)

        button_layout.addStretch()

        self._download_button = QPushButton("Download && Install")
        self._download_button.setDefault(True)
        self._download_button.setMinimumWidth(150)
        self._download_button.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
            QPushButton:disabled {
                background: #666;
            }
        """)
        button_layout.addWidget(self._download_button)

        layout.addLayout(button_layout)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background: #252525;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTextEdit {
                background: #1e1e1e;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 8px;
            }
            QProgressBar {
                background: #1e1e1e;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #4CAF50;
                border-radius: 3px;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
            QPushButton:pressed {
                background: #5a5a5a;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def _connect_signals(self) -> None:
        """Connect button signals."""
        self._download_button.clicked.connect(self._on_download_clicked)
        self._skip_button.clicked.connect(self._on_skip_clicked)
        self._remind_button.clicked.connect(self._on_remind_clicked)

    @Slot()
    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        if self._download_complete:
            # Install and restart
            self._install_update()
        else:
            # Start download
            self._start_download()

    @Slot()
    def _on_skip_clicked(self) -> None:
        """Handle skip button click."""
        if self._update_manager:
            self._update_manager.skip_version(self._update_info.version)

        self.update_skipped.emit(self._update_info.version)
        logger.info(f"User skipped version {self._update_info.version}")
        self.reject()

    @Slot()
    def _on_remind_clicked(self) -> None:
        """Handle remind later button click."""
        self.update_postponed.emit()
        logger.info("User postponed update")
        self.reject()

    def _start_download(self) -> None:
        """Start the update download."""
        if not self._update_manager:
            logger.warning("No update manager available for download")
            return

        self._is_downloading = True

        # Update UI for download mode
        self._progress_group.setVisible(True)
        self._download_button.setEnabled(False)
        self._download_button.setText("Downloading...")
        self._skip_button.setEnabled(False)
        self._remind_button.setEnabled(False)

        # Start async download
        import asyncio

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Schedule download task
        # Note: In real app, use qasync for proper Qt+asyncio integration
        QTimer.singleShot(100, self._do_download)

    def _do_download(self) -> None:
        """Perform the download (sync wrapper for demo)."""
        import asyncio

        async def download():
            if self._update_manager:
                path = await self._update_manager.download_update()
                return path
            return None

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, we're in qasync context
                asyncio.ensure_future(self._async_download())
            else:
                loop.run_until_complete(download())
                self._on_download_complete()
        except Exception as e:
            logger.error(f"Download failed: {e}")
            self._on_download_error(str(e))

    async def _async_download(self) -> None:
        """Async download with progress updates."""
        if not self._update_manager:
            return

        try:
            path = await self._update_manager.download_update()
            if path:
                self._on_download_complete()
            else:
                self._on_download_error("Download failed")
        except Exception as e:
            self._on_download_error(str(e))

    def update_progress(self, progress: DownloadProgress) -> None:
        """
        Update download progress display.

        Args:
            progress: Current download progress
        """
        self._progress_bar.setValue(int(progress.percent))

        # Format speed
        speed_mbps = progress.speed_bps / (1024 * 1024)
        remaining_bytes = progress.total_bytes - progress.downloaded_bytes
        eta_seconds = remaining_bytes / progress.speed_bps if progress.speed_bps > 0 else 0

        if eta_seconds > 60:
            eta_str = f"{int(eta_seconds / 60)}m {int(eta_seconds % 60)}s"
        else:
            eta_str = f"{int(eta_seconds)}s"

        self._progress_label.setText(f"Downloading... {speed_mbps:.1f} MB/s - {eta_str} remaining")

    def _on_download_complete(self) -> None:
        """Handle download completion."""
        self._is_downloading = False
        self._download_complete = True

        self._progress_bar.setValue(100)
        self._progress_label.setText("Download complete! Ready to install.")

        self._download_button.setEnabled(True)
        self._download_button.setText("Install && Restart")
        self._remind_button.setEnabled(True)
        self._remind_button.setText("Install Later")

        self.update_accepted.emit()
        logger.info("Update download completed")

    def _on_download_error(self, error: str) -> None:
        """Handle download error."""
        self._is_downloading = False

        self._progress_label.setText(f"Download failed: {error}")
        self._progress_label.setStyleSheet("color: #EF5350;")

        self._download_button.setEnabled(True)
        self._download_button.setText("Retry Download")
        self._skip_button.setEnabled(True)
        self._remind_button.setEnabled(True)

        logger.error(f"Update download failed: {error}")

    def _install_update(self) -> None:
        """Install the downloaded update."""
        if not self._update_manager:
            return

        self._download_button.setEnabled(False)
        self._download_button.setText("Installing...")
        self._remind_button.setEnabled(False)

        import asyncio

        async def apply():
            if self._update_manager:
                success = await self._update_manager.apply_update(restart=True)
                return success
            return False

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(apply())
        except Exception as e:
            logger.error(f"Install failed: {e}")
            self._download_button.setEnabled(True)
            self._download_button.setText("Retry Install")
            self._remind_button.setEnabled(True)

    @property
    def update_info(self) -> UpdateInfo:
        """Get the update info."""
        return self._update_info

    @property
    def is_downloading(self) -> bool:
        """Check if download is in progress."""
        return self._is_downloading

    @property
    def is_download_complete(self) -> bool:
        """Check if download is complete."""
        return self._download_complete


class UpdateNotificationWidget(QWidget):
    """
    Small notification widget for status bar or toolbar.

    Shows when an update is available with a clickable label.

    Signals:
        clicked: Emitted when notification is clicked
    """

    clicked = Signal()

    def __init__(
        self,
        update_info: UpdateInfo | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize notification widget.

        Args:
            update_info: Optional update info
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._update_info = update_info

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        self._icon = QLabel("\u2b06")
        self._icon.setStyleSheet("color: #4CAF50;")
        layout.addWidget(self._icon)

        self._label = QLabel("Update available")
        self._label.setStyleSheet("color: #4CAF50; text-decoration: underline; cursor: pointer;")
        layout.addWidget(self._label)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(
            f"Version {update_info.version} is available" if update_info else "Update available"
        )

        self.setVisible(update_info is not None)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press."""
        self.clicked.emit()
        super().mousePressEvent(event)

    def set_update_info(self, update_info: UpdateInfo | None) -> None:
        """
        Set update info and update visibility.

        Args:
            update_info: Update info or None to hide
        """
        self._update_info = update_info
        self.setVisible(update_info is not None)
        if update_info:
            self.setToolTip(f"Version {update_info.version} is available")

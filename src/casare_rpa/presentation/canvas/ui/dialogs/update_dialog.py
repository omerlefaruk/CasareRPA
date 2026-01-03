"""
Update Dialog UI Component.

Modal dialog for application update notifications and downloads.
Integrates with TUF UpdateManager for secure software updates.

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
"""

from loguru import logger
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
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
from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)


class UpdateDialog(BaseDialogV2):
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

    Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.
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
        super().__init__(
            title="Update Available",
            parent=parent,
            size=DialogSizeV2.MD,
        )

        self._update_info = update_info
        self._update_manager = update_manager
        self._is_downloading = False
        self._download_complete = False

        self._setup_ui()
        self._connect_signals()

        # Set footer buttons
        self._download_button_ref = None
        self._skip_button_ref = None
        self._remind_button_ref = None

        self._update_buttons()

        logger.info(f"UpdateDialog opened for version {update_info.version}")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.lg)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with icon and title
        header_layout = QHBoxLayout()

        # Update icon (using Unicode for simplicity)
        icon_label = QLabel("\u2b06")  # Up arrow
        icon_font = QFont()
        icon_font.setPointSize(TOKENS_V2.typography.xl)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet(f"color: {THEME_V2.success};")
        header_layout.addWidget(icon_label)

        # Title and version info
        title_layout = QVBoxLayout()
        title_label = QLabel("A new version is available!")
        title_font = QFont()
        title_font.setPointSize(TOKENS_V2.typography.lg)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {THEME_V2.text_primary};")
        title_layout.addWidget(title_label)

        version_label = QLabel(f"Version {self._update_info.version} is ready to download")
        version_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        title_layout.addWidget(version_label)
        header_layout.addLayout(title_layout)

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Update details group
        details_group = QGroupBox("Update Details")
        self._style_group_box(details_group)
        details_layout = QVBoxLayout()

        # Size info
        size_mb = self._update_info.size_bytes / (1024 * 1024)
        size_label = QLabel(f"Download size: {size_mb:.1f} MB")
        size_label.setStyleSheet(f"color: {THEME_V2.text_primary};")
        details_layout.addWidget(size_label)

        # Release date
        if self._update_info.release_date:
            date_str = self._update_info.release_date.strftime("%B %d, %Y")
            date_label = QLabel(f"Released: {date_str}")
            date_label.setStyleSheet(f"color: {THEME_V2.text_primary};")
            details_layout.addWidget(date_label)

        # Critical update indicator
        if self._update_info.is_critical:
            critical_label = QLabel("\u26a0 This is a critical security update")
            critical_label.setStyleSheet(
                f"color: {THEME_V2.warning}; font-weight: bold; padding: {TOKENS_V2.spacing.xs}px;"
            )
            details_layout.addWidget(critical_label)

        details_group.setLayout(details_layout)
        layout.addWidget(details_group)

        # Release notes group
        if self._update_info.release_notes:
            notes_group = QGroupBox("What's New")
            self._style_group_box(notes_group)
            notes_layout = QVBoxLayout()

            self._notes_text = QTextEdit()
            self._notes_text.setReadOnly(True)
            self._notes_text.setPlainText(self._update_info.release_notes)
            self._notes_text.setMaximumHeight(TOKENS_V2.sizes.dialog_height_sm)
            self._style_text_edit(self._notes_text)
            notes_layout.addWidget(self._notes_text)

            notes_group.setLayout(notes_layout)
            layout.addWidget(notes_group)

        # Progress section (initially hidden)
        self._progress_group = QGroupBox("Download Progress")
        self._style_group_box(self._progress_group)
        progress_layout = QVBoxLayout()

        self._progress_bar = QProgressBar()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        self._style_progress_bar(self._progress_bar)
        progress_layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("Preparing download...")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        progress_layout.addWidget(self._progress_label)

        self._progress_group.setLayout(progress_layout)
        self._progress_group.setVisible(False)
        layout.addWidget(self._progress_group)

        layout.addStretch()

        self.set_body_widget(content)

    def _style_group_box(self, group: QGroupBox) -> None:
        """Apply v2 styling to group box."""
        group.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                margin-top: {TOKENS_V2.spacing.md}px;
                padding-top: {TOKENS_V2.spacing.md}px;
                font-weight: bold;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.md}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """)

    def _style_text_edit(self, edit: QTextEdit) -> None:
        """Apply v2 styling to text edit."""
        edit.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                color: {THEME_V2.text_primary};
                padding: {TOKENS_V2.spacing.sm}px;
            }}
        """)

    def _style_progress_bar(self, bar: QProgressBar) -> None:
        """Apply v2 styling to progress bar."""
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                height: {TOKENS_V2.sizes.progress_height}px;
                text-align: center;
                color: {THEME_V2.text_primary};
            }}
            QProgressBar::chunk {{
                background: {THEME_V2.success};
                border-radius: {TOKENS_V2.radius.sm}px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect button signals."""
        pass

    def _update_buttons(self) -> None:
        """Update footer buttons based on state."""
        if self._download_complete:
            self.set_primary_button("Install & Restart", self._on_install_clicked)
            self.set_secondary_button("Install Later", self._on_remind_clicked)
        else:
            self.set_primary_button("Download & Install", self._on_download_clicked)
            self.set_secondary_button("Remind Later", self._on_remind_clicked)
            self.set_tertiary_button("Skip This Version", self._on_skip_clicked)

    @Slot()
    def _on_download_clicked(self) -> None:
        """Handle download button click."""
        if self._download_complete:
            self._install_update()
        else:
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

    @Slot()
    def _on_install_clicked(self) -> None:
        """Handle install button click."""
        self._install_update()

    def _start_download(self) -> None:
        """Start the update download."""
        if not self._update_manager:
            logger.warning("No update manager available for download")
            return

        self._is_downloading = True

        # Update UI for download mode
        self._progress_group.setVisible(True)
        self._update_buttons()

        # Schedule download task
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

        self._update_buttons()
        self.update_accepted.emit()
        logger.info("Update download completed")

    def _on_download_error(self, error: str) -> None:
        """Handle download error."""
        self._is_downloading = False

        self._progress_label.setText(f"Download failed: {error}")
        self._progress_label.setStyleSheet(f"color: {THEME_V2.error};")

        self._update_buttons()
        logger.error(f"Update download failed: {error}")

    def _install_update(self) -> None:
        """Install the downloaded update."""
        if not self._update_manager:
            return

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

    Epic 7.x - Migrated to THEME_V2/TOKENS_V2.
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
        layout.setContentsMargins(
            TOKENS_V2.margin.sm, TOKENS_V2.margin.xs, TOKENS_V2.margin.sm, TOKENS_V2.margin.xs
        )

        self._icon = QLabel("\u2b06")
        self._icon.setStyleSheet(f"color: {THEME_V2.success};")
        layout.addWidget(self._icon)

        self._label = QLabel("Update available")
        self._label.setStyleSheet(
            f"color: {THEME_V2.success}; text-decoration: underline; cursor: pointer;"
        )
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


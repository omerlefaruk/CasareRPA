"""
Antigravity OAuth Flow Dialog for CasareRPA.

Provides a simplified OAuth dialog for connecting to Google's Antigravity API
using the built-in Antigravity credentials. Supports multi-account management
for load balancing and automatic failover.
"""

from __future__ import annotations

import asyncio
import webbrowser
from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from typing import Any


class OAuthWorker(QObject):
    finished = Signal(bool, str, object)
    progress = Signal(str)

    def __init__(self, code: str, state: str) -> None:
        super().__init__()
        self._code = code
        self._state = state

    def run(self) -> None:
        try:
            self.progress.emit("Exchanging authorization code for tokens...")

            from casare_rpa.infrastructure.security.antigravity_oauth import (
                AntigravityTokenFailure,
                AntigravityTokenSuccess,
                exchange_antigravity_token,
            )

            result = asyncio.run(exchange_antigravity_token(self._code, self._state))

            if isinstance(result, AntigravityTokenFailure):
                self.finished.emit(False, f"Token exchange failed: {result.error}", None)
                return

            token_data = {
                "refresh_token": result.refresh_token,
                "access_token": result.access_token,
                "expires_at": result.expires_at,
                "email": result.email,
                "project_id": result.project_id,
            }

            self.finished.emit(True, "Authorization successful!", token_data)

        except Exception as e:
            logger.error(f"Antigravity OAuth error: {e}")
            self.finished.emit(False, f"Error: {e}", None)


class OAuthThread(QThread):
    finished = Signal(bool, str, object)
    progress = Signal(str)

    def __init__(self, code: str, state: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker = OAuthWorker(code, state)

    def run(self) -> None:
        self._worker.finished.connect(self.finished.emit)
        self._worker.progress.connect(self.progress.emit)
        self._worker.run()


class AntigravityOAuthDialog(QDialog):
    credential_created = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._oauth_server = None
        self._oauth_thread: OAuthThread | None = None
        self._waiting_for_callback = False
        self._current_state: str | None = None

        self.setWindowTitle("Connect Antigravity Account")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setModal(True)

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()
        self._load_existing_accounts()

        logger.debug("AntigravityOAuthDialog opened")

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        header_label = QLabel("Connect to Antigravity")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(header_label)

        description = QLabel(
            "Sign in with your Google account to access Antigravity models like "
            "Gemini 3 Pro, Claude 4.5 Sonnet/Opus, and more. "
            "Add multiple accounts for load balancing."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888888; margin-bottom: 10px;")
        layout.addWidget(description)

        accounts_group = QGroupBox("Connected Accounts")
        accounts_layout = QVBoxLayout(accounts_group)

        self._accounts_list = QListWidget()
        self._accounts_list.setMinimumHeight(100)
        self._accounts_list.setMaximumHeight(150)
        accounts_layout.addWidget(self._accounts_list)

        accounts_btn_layout = QHBoxLayout()
        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.setEnabled(False)
        accounts_btn_layout.addWidget(self._remove_btn)
        accounts_btn_layout.addStretch()
        accounts_layout.addLayout(accounts_btn_layout)

        layout.addWidget(accounts_group)

        models_group = QGroupBox("Available Models")
        models_layout = QVBoxLayout(models_group)

        models_text = QLabel(
            "After connecting, you can use:\n"
            "  - Gemini 3 Pro High/Low, Gemini 3 Flash\n"
            "  - Claude Sonnet 4.5, Claude Opus 4.5 (with thinking)\n"
            "  - GPT-OSS 120B Medium"
        )
        models_text.setStyleSheet("color: #cccccc; font-size: 12px;")
        models_layout.addWidget(models_text)

        layout.addWidget(models_group)

        status_group = QGroupBox("Authorization Status")
        status_layout = QVBoxLayout(status_group)

        self._status_label = QLabel("Ready to connect")
        self._status_label.setStyleSheet("color: #888888;")
        status_layout.addWidget(self._status_label)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 0)
        self._progress_bar.setVisible(False)
        self._progress_bar.setMaximumHeight(6)
        status_layout.addWidget(self._progress_bar)

        layout.addWidget(status_group)

        button_layout = QHBoxLayout()

        self._add_account_btn = QPushButton("Add Google Account")
        self._add_account_btn.setDefault(True)
        self._add_account_btn.setMinimumHeight(40)
        self._add_account_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a95f5;
            }
            QPushButton:disabled {
                background-color: #2d5a9e;
            }
        """)

        self._done_btn = QPushButton("Done")
        self._done_btn.setMinimumHeight(40)

        button_layout.addWidget(self._done_btn)
        button_layout.addStretch()
        button_layout.addWidget(self._add_account_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        self._add_account_btn.clicked.connect(self._start_authorization)
        self._done_btn.clicked.connect(self.accept)
        self._remove_btn.clicked.connect(self._remove_selected_account)
        self._accounts_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _on_selection_changed(self) -> None:
        self._remove_btn.setEnabled(len(self._accounts_list.selectedItems()) > 0)

    def _load_existing_accounts(self) -> None:
        try:
            from casare_rpa.infrastructure.security.antigravity_accounts import (
                AntigravityAccountManager,
            )

            async def load():
                manager = await AntigravityAccountManager.load_from_disk()
                return manager.get_accounts()

            accounts = asyncio.run(load())

            self._accounts_list.clear()
            for acc in accounts:
                email = acc.email or f"Account {acc.index + 1}"
                item = QListWidgetItem(email)
                item.setData(256, acc.index)
                self._accounts_list.addItem(item)

            if accounts:
                self._update_status(f"{len(accounts)} account(s) connected", success=True)

        except Exception as e:
            logger.debug(f"Could not load existing accounts: {e}")

    def _remove_selected_account(self) -> None:
        selected = self._accounts_list.selectedItems()
        if not selected:
            return

        item = selected[0]
        account_index = item.data(256)

        reply = QMessageBox.question(
            self,
            "Remove Account",
            f"Remove {item.text()} from connected accounts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            from casare_rpa.infrastructure.security.antigravity_accounts import (
                AntigravityAccountManager,
            )

            async def remove():
                manager = await AntigravityAccountManager.load_from_disk()
                accounts = manager.get_accounts()
                for acc in accounts:
                    if acc.index == account_index:
                        manager.remove_account(acc)
                        await manager.save_to_disk()
                        return True
                return False

            if asyncio.run(remove()):
                self._accounts_list.takeItem(self._accounts_list.row(item))
                self._update_status("Account removed", success=True)

        except Exception as e:
            logger.error(f"Failed to remove account: {e}")
            self._update_status(f"Error: {e}", error=True)

    def _start_authorization(self) -> None:
        self._add_account_btn.setEnabled(False)
        self._progress_bar.setVisible(True)
        self._update_status("Starting authorization...")

        try:
            from casare_rpa.infrastructure.security.antigravity_oauth import (
                ANTIGRAVITY_REDIRECT_URI,
                build_antigravity_auth_url,
            )
            from casare_rpa.infrastructure.security.oauth_server import LocalOAuthServer

            auth = build_antigravity_auth_url()
            self._current_state = auth.url.split("state=")[1].split("&")[0]

            self._oauth_server = LocalOAuthServer(port=51121)
            self._oauth_server.start()

            self._update_status("Opening browser for authorization...")
            webbrowser.open(auth.url)

            self._update_status("Waiting for authorization... (check your browser)")
            self._waiting_for_callback = True

            asyncio.get_event_loop().create_task(self._wait_for_callback())

        except Exception as e:
            logger.error(f"Failed to start authorization: {e}")
            self._update_status(f"Error: {e}", error=True)
            self._add_account_btn.setEnabled(True)
            self._progress_bar.setVisible(False)

            if self._oauth_server:
                self._oauth_server.stop()
                self._oauth_server = None

    async def _wait_for_callback(self) -> None:
        try:
            auth_code, error = await self._oauth_server.wait_for_callback(timeout=300.0)

            if error:
                self._on_auth_error(error)
                return

            if auth_code:
                self._on_auth_code_received(auth_code)

        except Exception as e:
            self._on_auth_error(str(e))
        finally:
            self._waiting_for_callback = False
            if self._oauth_server:
                self._oauth_server.stop()
                self._oauth_server = None

    def _on_auth_code_received(self, auth_code: str) -> None:
        self._update_status("Authorization code received, exchanging for tokens...")

        if not self._current_state:
            self._on_auth_error("Missing OAuth state")
            return

        self._oauth_thread = OAuthThread(auth_code, self._current_state, parent=self)
        self._oauth_thread.finished.connect(self._on_token_exchange_complete)
        self._oauth_thread.progress.connect(self._update_status)
        self._oauth_thread.start()

    def _on_token_exchange_complete(
        self, success: bool, message: str, token_data: dict[str, Any] | None
    ) -> None:
        self._progress_bar.setVisible(False)

        if not success:
            self._on_auth_error(message)
            return

        self._update_status(message, success=True)

        try:
            from casare_rpa.infrastructure.security.antigravity_accounts import (
                AntigravityAccountManager,
            )
            from casare_rpa.infrastructure.security.antigravity_oauth import (
                parse_refresh_parts,
            )

            async def save_account():
                manager = await AntigravityAccountManager.load_from_disk()

                refresh_token, project_id, _ = parse_refresh_parts(token_data["refresh_token"])

                manager.add_account(
                    refresh_token=refresh_token,
                    project_id=project_id,
                    email=token_data.get("email"),
                    access_token=token_data.get("access_token"),
                    expires_at=token_data.get("expires_at"),
                )

                await manager.save_to_disk()
                return manager.get_account_count()

            count = asyncio.run(save_account())

            self._load_existing_accounts()

            email = token_data.get("email", "Unknown")
            QMessageBox.information(
                self,
                "Success",
                f"Account connected: {email}\n\n"
                f"Total accounts: {count}\n\n"
                "You can add more accounts for load balancing.",
            )

            self.credential_created.emit("antigravity")

        except Exception as e:
            logger.error(f"Failed to save account: {e}")
            self._on_auth_error(f"Failed to save account: {e}")

        self._add_account_btn.setEnabled(True)

    def _on_auth_error(self, error: str) -> None:
        self._update_status(f"Error: {error}", error=True)
        self._add_account_btn.setEnabled(True)
        self._progress_bar.setVisible(False)

        QMessageBox.warning(
            self,
            "Authorization Failed",
            f"Failed to connect account:\n\n{error}",
        )

    def _update_status(self, message: str, success: bool = False, error: bool = False) -> None:
        self._status_label.setText(message)

        if error:
            self._status_label.setStyleSheet("color: #f44336;")
        elif success:
            self._status_label.setStyleSheet("color: #4caf50;")
        else:
            self._status_label.setStyleSheet("color: #2196f3;")

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #e0e0e0;
            }
            QListWidget {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                color: #d4d4d4;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
                color: #888888;
            }
            QProgressBar {
                background-color: #3c3c3c;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4285f4;
                border-radius: 3px;
            }
            QLabel {
                color: #d4d4d4;
            }
        """)

    def closeEvent(self, event) -> None:
        if self._oauth_server:
            self._oauth_server.stop()
            self._oauth_server = None

        super().closeEvent(event)


__all__ = ["AntigravityOAuthDialog"]

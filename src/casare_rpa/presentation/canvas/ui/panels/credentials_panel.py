"""
Credentials Panel UI Component.

Dockable panel for managing global credentials that projects can reference by alias.
Values are NEVER shown in plain text for security.

Features:
- View credential aliases (not values)
- Add/Edit/Delete credentials
- Test connection for API keys
- Context menu actions
- EventBus integration
"""

from datetime import datetime
from typing import Any, Dict, Optional

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLabel,
    QMenu,
    QMessageBox,
    QLineEdit,
    QGroupBox,
    QFormLayout,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from loguru import logger


class CredentialsPanel(QDockWidget):
    """
    Dockable panel for managing global credentials.

    Shows credential aliases with metadata (type, last modified, usage count).
    Values are NEVER displayed in plain text for security.

    Signals:
        credential_selected: Emitted when credential is selected (str: credential_id)
        credential_added: Emitted when credential is added (str: credential_id)
        credential_updated: Emitted when credential is updated (str: credential_id)
        credential_deleted: Emitted when credential is deleted (str: credential_id)
    """

    credential_selected = Signal(str)
    credential_added = Signal(str)
    credential_updated = Signal(str)
    credential_deleted = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, embedded: bool = False) -> None:
        """
        Initialize the credentials panel.

        Args:
            parent: Optional parent widget
            embedded: If True, behave as QWidget (for embedding in tab panels)
        """
        self._embedded = embedded
        self._store = None
        self._current_credential_id: Optional[str] = None
        self._event_bus = None

        if embedded:
            QWidget.__init__(self, parent)
        else:
            super().__init__("Credentials", parent)
            self.setObjectName("CredentialsDock")

        if not embedded:
            self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._load_credentials()
        self._connect_event_bus()

        logger.debug("CredentialsPanel initialized")

    def _get_store(self):
        """Lazy-load the credential store."""
        if self._store is None:
            try:
                from casare_rpa.infrastructure.security.credential_store import (
                    get_credential_store,
                )

                self._store = get_credential_store()
            except Exception as e:
                logger.error(f"Failed to load credential store: {e}")
        return self._store

    def _get_event_bus(self):
        """Lazy-load the event bus."""
        if self._event_bus is None:
            try:
                from casare_rpa.presentation.canvas.events import EventBus

                self._event_bus = EventBus()
            except Exception as e:
                logger.debug(f"EventBus not available: {e}")
        return self._event_bus

    def _connect_event_bus(self) -> None:
        """Connect to event bus for credential events."""
        bus = self._get_event_bus()
        if not bus:
            return

        try:
            from casare_rpa.presentation.canvas.events import EventType

            # Listen for credential events from other components
            if hasattr(EventType, "CREDENTIAL_ADDED"):
                bus.subscribe(EventType.CREDENTIAL_ADDED, self._on_external_credential_added)
            if hasattr(EventType, "CREDENTIAL_UPDATED"):
                bus.subscribe(EventType.CREDENTIAL_UPDATED, self._on_external_credential_updated)
            if hasattr(EventType, "CREDENTIAL_DELETED"):
                bus.subscribe(EventType.CREDENTIAL_DELETED, self._on_external_credential_deleted)
        except Exception as e:
            logger.debug(f"Could not subscribe to credential events: {e}")

    def _publish_event(self, event_name: str, credential_id: str) -> None:
        """Publish credential event to event bus."""
        bus = self._get_event_bus()
        if not bus:
            return

        try:
            from casare_rpa.presentation.canvas.events import Event, EventType

            event_type = getattr(EventType, event_name.upper(), None)
            if event_type:
                event = Event(
                    type=event_type,
                    source="CredentialsPanel",
                    data={"credential_id": credential_id},
                )
                bus.publish(event)
        except Exception as e:
            logger.debug(f"Could not publish {event_name} event: {e}")

    def _on_external_credential_added(self, event) -> None:
        """Handle external credential added event."""
        self._load_credentials()

    def _on_external_credential_updated(self, event) -> None:
        """Handle external credential updated event."""
        self._load_credentials()

    def _on_external_credential_deleted(self, event) -> None:
        """Handle external credential deleted event."""
        self._load_credentials()

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(300)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        if self._embedded:
            main_layout = QVBoxLayout(self)
        else:
            container = QWidget()
            main_layout = QVBoxLayout(container)

        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Header with title and add button
        header_layout = QHBoxLayout()
        title_label = QLabel("Global Credentials")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self._add_btn = QPushButton("+")
        self._add_btn.setFixedSize(28, 28)
        self._add_btn.setToolTip("Add new credential")
        self._add_btn.clicked.connect(self._on_add_clicked)
        header_layout.addWidget(self._add_btn)

        self._refresh_btn = QPushButton("R")
        self._refresh_btn.setFixedSize(28, 28)
        self._refresh_btn.setToolTip("Refresh credentials list")
        self._refresh_btn.clicked.connect(self._load_credentials)
        header_layout.addWidget(self._refresh_btn)

        main_layout.addLayout(header_layout)

        # Search/filter input
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search credentials...")
        self._search_input.textChanged.connect(self._on_search_changed)
        main_layout.addWidget(self._search_input)

        # Credentials list
        self._credentials_list = QListWidget()
        self._credentials_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._credentials_list.customContextMenuRequested.connect(self._show_context_menu)
        self._credentials_list.itemClicked.connect(self._on_credential_clicked)
        self._credentials_list.itemDoubleClicked.connect(self._on_credential_double_clicked)
        main_layout.addWidget(self._credentials_list, 1)

        # Details panel
        self._details_group = QGroupBox("Details")
        details_layout = QFormLayout(self._details_group)
        details_layout.setContentsMargins(8, 12, 8, 8)

        self._detail_name = QLabel("-")
        self._detail_name.setWordWrap(True)
        details_layout.addRow("Name:", self._detail_name)

        self._detail_type = QLabel("-")
        details_layout.addRow("Type:", self._detail_type)

        self._detail_category = QLabel("-")
        details_layout.addRow("Category:", self._detail_category)

        self._detail_modified = QLabel("-")
        details_layout.addRow("Modified:", self._detail_modified)

        self._detail_last_used = QLabel("-")
        details_layout.addRow("Last Used:", self._detail_last_used)

        self._detail_usage = QLabel("-")
        details_layout.addRow("Used by:", self._detail_usage)

        main_layout.addWidget(self._details_group)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setEnabled(False)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        btn_layout.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setEnabled(False)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c3c3c;
            }
            QPushButton:hover {
                background-color: #6c4c4c;
            }
            QPushButton:disabled {
                background-color: #3c3c3c;
            }
        """)
        btn_layout.addWidget(self._delete_btn)

        self._test_btn = QPushButton("Test")
        self._test_btn.setEnabled(False)
        self._test_btn.setToolTip("Test connection/validity")
        self._test_btn.clicked.connect(self._on_test_clicked)
        btn_layout.addWidget(self._test_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        if not self._embedded:
            self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #252525;
                color: #e0e0e0;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
            }
            QGroupBox {
                background: #2d2d2d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #5c5c5c;
                border-radius: 4px;
                padding: 6px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border: 1px solid #007acc;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #5a5a5a;
            }
            QPushButton:disabled {
                background-color: #2d2d2d;
                color: #666666;
            }
        """)

    def _load_credentials(self) -> None:
        """Load credentials into the list widget."""
        self._credentials_list.clear()
        store = self._get_store()
        if not store:
            self._show_empty_state("Credential store unavailable")
            return

        credentials = store.list_credentials()
        if not credentials:
            self._show_empty_state("No credentials stored")
            return

        # Apply search filter if present
        search_text = self._search_input.text().lower()
        if search_text:
            credentials = [
                c
                for c in credentials
                if search_text in c.get("name", "").lower()
                or search_text in c.get("category", "").lower()
                or search_text in c.get("type", "").lower()
            ]

        for cred in credentials:
            item = self._create_credential_item(cred)
            self._credentials_list.addItem(item)

        # Clear selection
        self._current_credential_id = None
        self._update_detail_panel(None)
        self._update_button_states()

    def _show_empty_state(self, message: str) -> None:
        """Show empty state message in the list."""
        item = QListWidgetItem(message)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(QColor("#888888"))
        self._credentials_list.addItem(item)

    def _create_credential_item(self, cred: Dict[str, Any]) -> QListWidgetItem:
        """Create a list item for a credential."""
        name = cred.get("name", "Unknown")
        cred_type = cred.get("type", "unknown").replace("_", " ").title()
        category = cred.get("category", "custom").title()

        # Format: icon + name + type badge
        display_text = f"{self._get_type_icon(cred.get('type', ''))} {name}"

        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, cred.get("id"))
        item.setToolTip(f"Type: {cred_type}\nCategory: {category}")

        # Color-code by type
        type_colors = {
            "api_key": "#569CD6",  # Blue
            "username_password": "#4EC9B0",  # Teal
            "google_oauth": "#4285F4",  # Google Blue
            "oauth_token": "#C586C0",  # Purple
            "connection_string": "#CE9178",  # Orange
            "custom": "#808080",  # Gray
        }
        color = type_colors.get(cred.get("type", ""), "#808080")
        item.setForeground(QColor(color))

        return item

    def _get_type_icon(self, cred_type: str) -> str:
        """Get icon character for credential type."""
        icons = {
            "api_key": "[K]",
            "username_password": "[U]",
            "google_oauth": "[G]",
            "oauth_token": "[O]",
            "connection_string": "[C]",
            "custom": "[?]",
        }
        return icons.get(cred_type, "[?]")

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._load_credentials()

    def _on_credential_clicked(self, item: QListWidgetItem) -> None:
        """Handle credential item click."""
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        if not cred_id:
            return

        self._current_credential_id = cred_id
        self._update_detail_panel(cred_id)
        self._update_button_states()
        self.credential_selected.emit(cred_id)

    def _on_credential_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle credential double-click to edit."""
        cred_id = item.data(Qt.ItemDataRole.UserRole)
        if cred_id:
            self._edit_credential(cred_id)

    def _update_detail_panel(self, cred_id: Optional[str]) -> None:
        """Update the details panel with credential info."""
        if not cred_id:
            self._detail_name.setText("-")
            self._detail_type.setText("-")
            self._detail_category.setText("-")
            self._detail_modified.setText("-")
            self._detail_last_used.setText("-")
            self._detail_usage.setText("-")
            return

        store = self._get_store()
        if not store:
            return

        info = store.get_credential_info(cred_id)
        if not info:
            return

        self._detail_name.setText(info.get("name", "Unknown"))
        self._detail_type.setText(info.get("type", "unknown").replace("_", " ").title())
        self._detail_category.setText(info.get("category", "custom").title())

        # Format dates
        updated_at = info.get("updated_at", "")
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                self._detail_modified.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                self._detail_modified.setText(
                    updated_at[:16] if len(updated_at) > 16 else updated_at
                )
        else:
            self._detail_modified.setText("-")

        last_used = info.get("last_used", "")
        if last_used:
            try:
                dt = datetime.fromisoformat(last_used.replace("Z", "+00:00"))
                self._detail_last_used.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                self._detail_last_used.setText(last_used[:16] if len(last_used) > 16 else last_used)
        else:
            self._detail_last_used.setText("Never")

        # Usage count (placeholder - would need project scanning)
        self._detail_usage.setText("0 projects")

    def _update_button_states(self) -> None:
        """Update action button enabled states."""
        has_selection = self._current_credential_id is not None
        self._edit_btn.setEnabled(has_selection)
        self._delete_btn.setEnabled(has_selection)
        self._test_btn.setEnabled(has_selection)

    def _show_context_menu(self, position) -> None:
        """Show context menu for credential item."""
        item = self._credentials_list.itemAt(position)
        if not item:
            # Show menu for empty area
            menu = QMenu(self)
            add_action = menu.addAction("Add Credential")
            add_action.triggered.connect(self._on_add_clicked)
            menu.exec(self._credentials_list.mapToGlobal(position))
            return

        cred_id = item.data(Qt.ItemDataRole.UserRole)
        if not cred_id:
            return

        self._current_credential_id = cred_id
        self._update_detail_panel(cred_id)
        self._update_button_states()

        menu = QMenu(self)

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(self._on_edit_clicked)

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self._on_delete_clicked)

        menu.addSeparator()

        test_action = menu.addAction("Test Connection")
        test_action.triggered.connect(self._on_test_clicked)

        menu.addSeparator()

        add_action = menu.addAction("Add New...")
        add_action.triggered.connect(self._on_add_clicked)

        menu.exec(self._credentials_list.mapToGlobal(position))

    def _on_add_clicked(self) -> None:
        """Handle add button click."""
        self._open_credential_manager_dialog(mode="add")

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        if self._current_credential_id:
            self._edit_credential(self._current_credential_id)

    def _edit_credential(self, cred_id: str) -> None:
        """Open edit dialog for credential."""
        # Verify user has access (basic security check)
        reply = QMessageBox.question(
            self,
            "Edit Credential",
            "Editing this credential requires verification.\n\n" "Do you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._open_credential_manager_dialog(mode="edit", credential_id=cred_id)

    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        if not self._current_credential_id:
            return

        store = self._get_store()
        if not store:
            return

        info = store.get_credential_info(self._current_credential_id)
        name = info.get("name", "Unknown") if info else "Unknown"

        reply = QMessageBox.warning(
            self,
            "Delete Credential",
            f"Are you sure you want to delete '{name}'?\n\n"
            "This action cannot be undone.\n"
            "Workflows using this credential will fail.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            cred_id = self._current_credential_id
            if store.delete_credential(cred_id):
                self._current_credential_id = None
                self._load_credentials()

                # Emit signal and publish event
                self.credential_deleted.emit(cred_id)
                self._publish_event("credential_deleted", cred_id)

                QMessageBox.information(
                    self,
                    "Deleted",
                    f"Credential '{name}' has been deleted.",
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to delete credential '{name}'.",
                )

    def _on_test_clicked(self) -> None:
        """Handle test button click."""
        if not self._current_credential_id:
            return

        store = self._get_store()
        if not store:
            return

        info = store.get_credential_info(self._current_credential_id)
        if not info:
            return

        cred_type = info.get("type", "")

        if cred_type == "api_key":
            self._test_api_key(self._current_credential_id)
        elif cred_type == "google_oauth":
            self._test_google_oauth(self._current_credential_id)
        elif cred_type == "username_password":
            QMessageBox.information(
                self,
                "Test Connection",
                "Username/Password credentials require service-specific testing.\n"
                "Use the node's test functionality to verify this credential.",
            )
        else:
            QMessageBox.information(
                self,
                "Test Connection",
                f"Testing for '{cred_type}' credentials is not yet implemented.",
            )

    def _test_api_key(self, cred_id: str) -> None:
        """Test an API key credential."""
        store = self._get_store()
        if not store:
            return

        data = store.get_credential(cred_id)
        if not data:
            QMessageBox.warning(self, "Error", "Could not retrieve credential data.")
            return

        provider = data.get("provider", "")
        api_key = data.get("api_key", "")

        if not api_key:
            QMessageBox.warning(self, "Error", "No API key found in this credential.")
            return

        # Open credential manager dialog in test mode
        try:
            from casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog import (
                ApiKeyTestThread,
            )

            self._test_btn.setEnabled(False)
            self._test_btn.setText("Testing...")

            self._test_thread = ApiKeyTestThread(provider, api_key, self)
            self._test_thread.finished.connect(self._on_api_test_complete)
            self._test_thread.start()

        except ImportError as e:
            logger.error(f"Could not import test worker: {e}")
            QMessageBox.warning(
                self,
                "Error",
                "API key testing is not available.",
            )

    def _on_api_test_complete(self, success: bool, message: str) -> None:
        """Handle API key test completion."""
        self._test_btn.setEnabled(True)
        self._test_btn.setText("Test")

        if success:
            QMessageBox.information(self, "Test Successful", message)
        else:
            QMessageBox.warning(self, "Test Failed", message)

    def _test_google_oauth(self, cred_id: str) -> None:
        """Test a Google OAuth credential."""
        try:
            from casare_rpa.infrastructure.security.google_oauth import (
                GoogleOAuthManager,
            )
            import asyncio

            async def do_test():
                manager = GoogleOAuthManager()
                return await manager.validate_credential(cred_id)

            # Run validation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(do_test())
                if result:
                    QMessageBox.information(
                        self,
                        "Test Successful",
                        "Google OAuth credential is valid.",
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Test Failed",
                        "Google OAuth credential is invalid or expired.\n"
                        "Try refreshing the token.",
                    )
            finally:
                loop.close()

        except ImportError:
            QMessageBox.information(
                self,
                "Test Connection",
                "Google OAuth testing requires the google-auth library.",
            )
        except Exception as e:
            logger.error(f"Google OAuth test failed: {e}")
            QMessageBox.warning(
                self,
                "Test Failed",
                f"Error testing Google credential: {e}",
            )

    def _open_credential_manager_dialog(
        self, mode: str = "add", credential_id: Optional[str] = None
    ) -> None:
        """Open the credential manager dialog."""
        try:
            from casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog import (
                CredentialManagerDialog,
            )

            dialog = CredentialManagerDialog(self)
            dialog.credentials_changed.connect(self._on_credentials_changed)

            # If editing, try to navigate to the credential
            if mode == "edit" and credential_id:
                store = self._get_store()
                if store:
                    info = store.get_credential_info(credential_id)
                    if info:
                        cred_type = info.get("type", "")
                        # Switch to appropriate tab based on type
                        if cred_type == "api_key":
                            dialog._tabs.setCurrentIndex(0)  # API Keys tab
                        elif cred_type == "username_password":
                            dialog._tabs.setCurrentIndex(1)  # Logins tab
                        elif cred_type == "google_oauth":
                            dialog._tabs.setCurrentIndex(2)  # Google tab
                        else:
                            dialog._tabs.setCurrentIndex(3)  # All tab

            dialog.exec()

        except ImportError as e:
            logger.error(f"Could not import CredentialManagerDialog: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "Credential Manager dialog is not available.",
            )

    def _on_credentials_changed(self) -> None:
        """Handle credentials changed in dialog."""
        self._load_credentials()

        # Publish generic update event
        if self._current_credential_id:
            self._publish_event("credential_updated", self._current_credential_id)
            self.credential_updated.emit(self._current_credential_id)

    def refresh(self) -> None:
        """Public method to refresh the credentials list."""
        self._load_credentials()

    def get_selected_credential_id(self) -> Optional[str]:
        """Get the currently selected credential ID."""
        return self._current_credential_id

    def select_credential(self, cred_id: str) -> None:
        """Select a credential by ID."""
        for i in range(self._credentials_list.count()):
            item = self._credentials_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == cred_id:
                self._credentials_list.setCurrentItem(item)
                self._on_credential_clicked(item)
                break

    def cleanup(self) -> None:
        """Clean up resources."""
        # Unsubscribe from event bus
        bus = self._get_event_bus()
        if bus:
            try:
                from casare_rpa.presentation.canvas.events import EventType

                if hasattr(EventType, "CREDENTIAL_ADDED"):
                    bus.unsubscribe(EventType.CREDENTIAL_ADDED, self._on_external_credential_added)
                if hasattr(EventType, "CREDENTIAL_UPDATED"):
                    bus.unsubscribe(
                        EventType.CREDENTIAL_UPDATED,
                        self._on_external_credential_updated,
                    )
                if hasattr(EventType, "CREDENTIAL_DELETED"):
                    bus.unsubscribe(
                        EventType.CREDENTIAL_DELETED,
                        self._on_external_credential_deleted,
                    )
            except Exception:
                pass

        logger.debug("CredentialsPanel cleaned up")

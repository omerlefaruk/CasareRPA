"""
API Key Management Panel for Fleet Dashboard.

Provides UI for managing robot API keys including generation, revocation,
and viewing usage statistics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QComboBox,
    QLineEdit,
    QLabel,
    QMenu,
    QMessageBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QDateTimeEdit,
    QCheckBox,
    QTextEdit,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QTimer, QDateTime
from PySide6.QtGui import QColor, QBrush


if TYPE_CHECKING:
    pass


STATUS_COLORS = {
    "valid": QColor(0x4C, 0xAF, 0x50),  # Green
    "active": QColor(0x4C, 0xAF, 0x50),  # Green
    "revoked": QColor(0xF4, 0x43, 0x36),  # Red
    "expired": QColor(0xFF, 0xC1, 0x07),  # Yellow/Orange
}


class GenerateApiKeyDialog(QDialog):
    """Dialog for generating a new API key."""

    def __init__(
        self,
        robots: List[Dict[str, Any]],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._robots = robots
        self._generated_key: Optional[str] = None
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Generate API Key")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        form_group = QGroupBox("Key Configuration")
        form = QFormLayout(form_group)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Production Key")
        form.addRow("Name:", self._name_edit)

        self._description_edit = QTextEdit()
        self._description_edit.setMaximumHeight(60)
        self._description_edit.setPlaceholderText("Optional description...")
        form.addRow("Description:", self._description_edit)

        self._robot_combo = QComboBox()
        self._robot_combo.addItem("Select Robot...", "")
        for robot in self._robots:
            self._robot_combo.addItem(
                f"{robot['name']} ({robot['id'][:8]}...)", robot["id"]
            )
        form.addRow("Robot:", self._robot_combo)

        self._expires_check = QCheckBox("Set expiration")
        self._expires_check.stateChanged.connect(self._on_expires_changed)
        form.addRow("", self._expires_check)

        self._expires_edit = QDateTimeEdit()
        self._expires_edit.setDateTime(QDateTime.currentDateTime().addMonths(3))
        self._expires_edit.setEnabled(False)
        self._expires_edit.setCalendarPopup(True)
        form.addRow("Expires At:", self._expires_edit)

        layout.addWidget(form_group)

        # Generated key display (hidden initially)
        self._key_group = QGroupBox("Generated API Key")
        key_layout = QVBoxLayout(self._key_group)

        warning_label = QLabel("Save this key now. It will not be shown again!")
        warning_label.setStyleSheet("color: #FF6B6B; font-weight: bold;")
        key_layout.addWidget(warning_label)

        self._key_display = QTextEdit()
        self._key_display.setReadOnly(True)
        self._key_display.setMaximumHeight(50)
        self._key_display.setStyleSheet(
            "background: #1a1a1a; font-family: monospace; font-size: 12px;"
        )
        key_layout.addWidget(self._key_display)

        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(self._copy_key)
        key_layout.addWidget(copy_btn)

        self._key_group.setVisible(False)
        layout.addWidget(self._key_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self._generate_btn = QPushButton("Generate")
        self._generate_btn.clicked.connect(self._on_generate)
        button_layout.addWidget(self._generate_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QDialog {
                background: #252525;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #5a8a9a;
            }
        """)

    def _on_expires_changed(self, state: int) -> None:
        self._expires_edit.setEnabled(state == Qt.CheckState.Checked.value)

    def _on_generate(self) -> None:
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Key name is required.")
            return

        robot_id = self._robot_combo.currentData()
        if not robot_id:
            QMessageBox.warning(self, "Validation Error", "Please select a robot.")
            return

        # This will be connected to actual generation logic
        self._generate_btn.setEnabled(False)
        self._generate_btn.setText("Generating...")

    def set_generated_key(self, raw_key: str) -> None:
        """Display the generated key (called by parent after actual generation)."""
        self._generated_key = raw_key
        self._key_display.setText(raw_key)
        self._key_group.setVisible(True)
        self._generate_btn.setVisible(False)
        self._name_edit.setEnabled(False)
        self._description_edit.setEnabled(False)
        self._robot_combo.setEnabled(False)
        self._expires_check.setEnabled(False)
        self._expires_edit.setEnabled(False)

    def _copy_key(self) -> None:
        if self._generated_key:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._generated_key)
            QMessageBox.information(self, "Copied", "API key copied to clipboard.")

    def get_key_config(self) -> Dict[str, Any]:
        """Get key configuration from form."""
        expires_at = None
        if self._expires_check.isChecked():
            expires_at = self._expires_edit.dateTime().toPython()

        return {
            "name": self._name_edit.text().strip(),
            "description": self._description_edit.toPlainText().strip(),
            "robot_id": self._robot_combo.currentData(),
            "expires_at": expires_at,
        }


class ApiKeyPanel(QWidget):
    """
    Panel for managing robot API keys.

    Features:
    - List all API keys for tenant
    - Generate new API key
    - Revoke API key
    - Copy key to clipboard (one-time view)
    - Show key usage statistics

    Signals:
        key_generated: Emitted when new key requested (config_dict)
        key_revoked: Emitted when key revoked (key_id)
        key_rotated: Emitted when key rotation requested (key_id)
        refresh_requested: Emitted when refresh clicked
    """

    key_generated = Signal(dict)
    key_revoked = Signal(str)
    key_rotated = Signal(str)
    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._api_keys: List[Dict[str, Any]] = []
        self._robots: List[Dict[str, Any]] = []
        self._tenant_id: Optional[str] = None
        self._setup_ui()
        self._apply_styles()

        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._request_refresh)
        self._refresh_timer.start(60000)  # Refresh every minute

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Toolbar
        toolbar = QHBoxLayout()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search keys...")
        self._search_edit.textChanged.connect(self._apply_filters)
        self._search_edit.setMinimumWidth(200)
        toolbar.addWidget(self._search_edit)

        self._status_filter = QComboBox()
        self._status_filter.addItems(
            [
                "All Status",
                "Active",
                "Revoked",
                "Expired",
            ]
        )
        self._status_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._status_filter)

        self._robot_filter = QComboBox()
        self._robot_filter.addItem("All Robots", "")
        self._robot_filter.currentIndexChanged.connect(self._apply_filters)
        toolbar.addWidget(self._robot_filter)

        toolbar.addStretch()

        self._generate_btn = QPushButton("Generate Key")
        self._generate_btn.clicked.connect(self._on_generate_key)
        toolbar.addWidget(self._generate_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._request_refresh)
        toolbar.addWidget(self._refresh_btn)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            [
                "Name",
                "Robot",
                "Status",
                "Created",
                "Expires",
                "Last Used",
                "Usage Count",
                "Actions",
            ]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(7, 180)

        layout.addWidget(self._table)

        # Status bar
        status_layout = QHBoxLayout()

        self._status_label = QLabel("0 API keys")
        self._status_label.setStyleSheet("color: #888888;")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet("color: #888888;")
        status_layout.addWidget(self._stats_label)

        layout.addLayout(status_layout)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QTableWidget {
                background: #1e1e1e;
                border: 1px solid #3d3d3d;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
                alternate-background-color: #252525;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTableWidget::item:selected {
                background: #094771;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #a0a0a0;
                padding: 6px;
                border: none;
                border-bottom: 1px solid #3d3d3d;
                border-right: 1px solid #3d3d3d;
            }
            QLineEdit, QComboBox {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 4px 8px;
                min-height: 24px;
            }
            QPushButton {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #e0e0e0;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)

    def set_tenant(self, tenant_id: str) -> None:
        """Set current tenant for filtering."""
        self._tenant_id = tenant_id

    def update_robots(self, robots: List[Dict[str, Any]]) -> None:
        """Update available robots list."""
        self._robots = robots
        current = self._robot_filter.currentData()

        self._robot_filter.blockSignals(True)
        self._robot_filter.clear()
        self._robot_filter.addItem("All Robots", "")
        for robot in robots:
            self._robot_filter.addItem(robot["name"], robot["id"])

        # Restore selection
        for i in range(self._robot_filter.count()):
            if self._robot_filter.itemData(i) == current:
                self._robot_filter.setCurrentIndex(i)
                break

        self._robot_filter.blockSignals(False)

    def update_api_keys(self, api_keys: List[Dict[str, Any]]) -> None:
        """Update table with API key list."""
        self._api_keys = api_keys
        self._populate_table()
        self._update_status_label()
        self._update_stats()

    def _populate_table(self) -> None:
        """Populate table with API keys."""
        self._table.setRowCount(len(self._api_keys))

        for row, key in enumerate(self._api_keys):
            # Name
            name_item = QTableWidgetItem(key.get("name", "Unnamed"))
            name_item.setData(Qt.ItemDataRole.UserRole, key.get("id"))
            self._table.setItem(row, 0, name_item)

            # Robot
            robot_name = key.get("robot_name", key.get("robot_id", "")[:8] + "...")
            self._table.setItem(row, 1, QTableWidgetItem(robot_name))

            # Status
            status = key.get("status", "valid")
            status_item = QTableWidgetItem(status.title())
            status_color = STATUS_COLORS.get(status, STATUS_COLORS["valid"])
            status_item.setForeground(QBrush(status_color))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            self._table.setItem(row, 2, status_item)

            # Created
            created = key.get("created_at")
            if isinstance(created, str):
                created_str = created[:10]
            elif isinstance(created, datetime):
                created_str = created.strftime("%Y-%m-%d")
            else:
                created_str = "-"
            self._table.setItem(row, 3, QTableWidgetItem(created_str))

            # Expires
            expires = key.get("expires_at")
            if expires:
                if isinstance(expires, str):
                    expires_str = expires[:10]
                elif isinstance(expires, datetime):
                    expires_str = expires.strftime("%Y-%m-%d")
                else:
                    expires_str = "-"
            else:
                expires_str = "Never"
            self._table.setItem(row, 4, QTableWidgetItem(expires_str))

            # Last Used
            last_used = key.get("last_used_at")
            if last_used:
                if isinstance(last_used, str):
                    last_used_str = last_used[:10]
                elif isinstance(last_used, datetime):
                    last_used_str = last_used.strftime("%Y-%m-%d %H:%M")
                else:
                    last_used_str = "-"
            else:
                last_used_str = "Never"
            self._table.setItem(row, 5, QTableWidgetItem(last_used_str))

            # Usage Count (if available)
            usage_count = key.get("usage_count", "-")
            self._table.setItem(row, 6, QTableWidgetItem(str(usage_count)))

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)

            if status == "valid" or status == "active":
                revoke_btn = QPushButton("Revoke")
                revoke_btn.setMaximumHeight(24)
                revoke_btn.setProperty("key_id", key.get("id"))
                revoke_btn.clicked.connect(lambda _, k=key: self._on_revoke_key(k))
                actions_layout.addWidget(revoke_btn)

                rotate_btn = QPushButton("Rotate")
                rotate_btn.setMaximumHeight(24)
                rotate_btn.clicked.connect(lambda _, k=key: self._on_rotate_key(k))
                actions_layout.addWidget(rotate_btn)
            else:
                disabled_label = QLabel("Inactive")
                disabled_label.setStyleSheet("color: #888888;")
                actions_layout.addWidget(disabled_label)

            self._table.setCellWidget(row, 7, actions_widget)

        self._apply_filters()

    def _apply_filters(self) -> None:
        """Apply search and filters to table."""
        search_text = self._search_edit.text().lower()
        status_filter = self._status_filter.currentText().lower()
        robot_filter = self._robot_filter.currentData()

        visible_count = 0
        for row in range(self._table.rowCount()):
            key = self._api_keys[row] if row < len(self._api_keys) else None
            if key is None:
                self._table.setRowHidden(row, True)
                continue

            show = True

            # Search filter
            if search_text:
                name_match = search_text in key.get("name", "").lower()
                robot_match = search_text in key.get("robot_name", "").lower()
                if not (name_match or robot_match):
                    show = False

            # Status filter
            if show and status_filter != "all status":
                key_status = key.get("status", "valid").lower()
                if key_status != status_filter:
                    show = False

            # Robot filter
            if show and robot_filter:
                if key.get("robot_id") != robot_filter:
                    show = False

            self._table.setRowHidden(row, not show)
            if show:
                visible_count += 1

        self._update_status_label(visible_count)

    def _update_status_label(self, visible: Optional[int] = None) -> None:
        """Update status label."""
        total = len(self._api_keys)
        active = sum(
            1 for k in self._api_keys if k.get("status") in ("valid", "active")
        )
        revoked = sum(1 for k in self._api_keys if k.get("status") == "revoked")

        if visible is not None and visible != total:
            self._status_label.setText(
                f"Showing {visible} of {total} keys | Active: {active}, Revoked: {revoked}"
            )
        else:
            self._status_label.setText(
                f"{total} API keys | Active: {active}, Revoked: {revoked}"
            )

    def _update_stats(self) -> None:
        """Update statistics label."""
        if not self._api_keys:
            self._stats_label.setText("")
            return

        # Calculate usage stats
        used_today = 0
        total_usage = 0
        for key in self._api_keys:
            last_used = key.get("last_used_at")
            if last_used:
                if isinstance(last_used, datetime):
                    if last_used.date() == datetime.now().date():
                        used_today += 1
                elif isinstance(last_used, str):
                    if last_used[:10] == datetime.now().strftime("%Y-%m-%d"):
                        used_today += 1
            total_usage += key.get("usage_count", 0)

        self._stats_label.setText(f"Used today: {used_today}")

    def _show_context_menu(self, pos) -> None:
        """Show context menu for API key row."""
        item = self._table.itemAt(pos)
        if not item:
            return

        key_id = self._table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        key = next((k for k in self._api_keys if k.get("id") == key_id), None)
        if not key:
            return

        menu = QMenu(self)

        if key.get("status") in ("valid", "active"):
            revoke_action = menu.addAction("Revoke Key")
            revoke_action.triggered.connect(lambda: self._on_revoke_key(key))

            rotate_action = menu.addAction("Rotate Key")
            rotate_action.triggered.connect(lambda: self._on_rotate_key(key))

            menu.addSeparator()

        details_action = menu.addAction("View Details")
        details_action.triggered.connect(lambda: self._on_view_details(key))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _on_generate_key(self) -> None:
        """Open dialog to generate new API key."""
        dialog = GenerateApiKeyDialog(self._robots, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config = dialog.get_key_config()
            self.key_generated.emit(config)

    def _on_revoke_key(self, key: Dict[str, Any]) -> None:
        """Confirm and revoke API key."""
        reply = QMessageBox.question(
            self,
            "Revoke API Key",
            f"Are you sure you want to revoke '{key.get('name', 'this key')}'?\n\n"
            "The robot using this key will no longer be able to authenticate.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.key_revoked.emit(key.get("id"))

    def _on_rotate_key(self, key: Dict[str, Any]) -> None:
        """Confirm and rotate API key."""
        reply = QMessageBox.question(
            self,
            "Rotate API Key",
            f"Are you sure you want to rotate '{key.get('name', 'this key')}'?\n\n"
            "This will revoke the current key and generate a new one.\n"
            "You will need to update the robot's configuration.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.key_rotated.emit(key.get("id"))

    def _on_view_details(self, key: Dict[str, Any]) -> None:
        """Show key details in a dialog."""
        details = [
            f"Name: {key.get('name', 'Unnamed')}",
            f"ID: {key.get('id', 'N/A')}",
            f"Robot: {key.get('robot_name', key.get('robot_id', 'N/A'))}",
            f"Status: {key.get('status', 'Unknown')}",
            f"Created: {key.get('created_at', 'N/A')}",
            f"Created By: {key.get('created_by', 'N/A')}",
            f"Expires: {key.get('expires_at', 'Never')}",
            f"Last Used: {key.get('last_used_at', 'Never')}",
            f"Last Used IP: {key.get('last_used_ip', 'N/A')}",
        ]

        if key.get("is_revoked"):
            details.extend(
                [
                    f"Revoked At: {key.get('revoked_at', 'N/A')}",
                    f"Revoked By: {key.get('revoked_by', 'N/A')}",
                    f"Revoke Reason: {key.get('revoke_reason', 'N/A')}",
                ]
            )

        QMessageBox.information(self, "API Key Details", "\n".join(details))

    def _request_refresh(self) -> None:
        """Request API keys refresh."""
        self.refresh_requested.emit()

    def set_refreshing(self, refreshing: bool) -> None:
        """Set refresh button state."""
        self._refresh_btn.setEnabled(not refreshing)
        self._refresh_btn.setText("Refreshing..." if refreshing else "Refresh")


__all__ = [
    "ApiKeyPanel",
    "GenerateApiKeyDialog",
]

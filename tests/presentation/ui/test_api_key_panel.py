"""
Tests for ApiKeyPanel presentation widget.

Tests the UI for managing robot API keys including generation, revocation,
and display. Uses pytest-qt (qtbot) for Qt widget testing.
Heavy Qt components are mocked to keep tests fast.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

# Skip tests if Qt not available (CI environment)
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from casare_rpa.presentation.canvas.ui.panels.api_key_panel import (
    ApiKeyPanel,
    GenerateApiKeyDialog,
)


@pytest.fixture
def sample_api_keys() -> List[Dict[str, Any]]:
    """Sample API key data for testing."""
    return [
        {
            "id": "key-1",
            "name": "Production Key",
            "robot_id": "robot-123",
            "robot_name": "Main Robot",
            "status": "valid",
            "created_at": "2024-01-01T00:00:00Z",
            "expires_at": None,
            "last_used_at": "2024-06-15T12:00:00Z",
            "usage_count": 1500,
        },
        {
            "id": "key-2",
            "name": "Development Key",
            "robot_id": "robot-456",
            "robot_name": "Dev Robot",
            "status": "active",
            "created_at": "2024-02-01T00:00:00Z",
            "expires_at": "2024-12-31T23:59:59Z",
            "last_used_at": "2024-06-14T10:00:00Z",
            "usage_count": 50,
        },
        {
            "id": "key-3",
            "name": "Revoked Key",
            "robot_id": "robot-789",
            "robot_name": "Old Robot",
            "status": "revoked",
            "created_at": "2023-06-01T00:00:00Z",
            "expires_at": None,
            "last_used_at": "2024-01-01T00:00:00Z",
            "usage_count": 100,
            "is_revoked": True,
            "revoked_at": "2024-03-01T00:00:00Z",
            "revoked_by": "admin@test.com",
        },
    ]


@pytest.fixture
def sample_robots() -> List[Dict[str, Any]]:
    """Sample robot data for testing."""
    return [
        {"id": "robot-123", "name": "Main Robot"},
        {"id": "robot-456", "name": "Dev Robot"},
        {"id": "robot-789", "name": "Old Robot"},
    ]


class TestApiKeyPanelCreation:
    """Tests for ApiKeyPanel widget creation."""

    def test_panel_creates_successfully(self, qtbot) -> None:
        """ApiKeyPanel can be created."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        assert panel is not None

    def test_panel_has_table(self, qtbot) -> None:
        """ApiKeyPanel contains a table widget."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        assert panel._table is not None
        assert panel._table.columnCount() == 8

    def test_panel_has_toolbar_buttons(self, qtbot) -> None:
        """ApiKeyPanel has generate and refresh buttons."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        assert panel._generate_btn is not None
        assert panel._refresh_btn is not None

    def test_panel_has_filters(self, qtbot) -> None:
        """ApiKeyPanel has search and filter widgets."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        assert panel._search_edit is not None
        assert panel._status_filter is not None
        assert panel._robot_filter is not None


class TestApiKeyPanelDataUpdate:
    """Tests for updating panel with API key data."""

    def test_update_api_keys_populates_table(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """update_api_keys() populates table with key data."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        assert panel._table.rowCount() == 3

    def test_update_api_keys_displays_names(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Table displays key names."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        # First column should be name
        name_item = panel._table.item(0, 0)
        assert name_item is not None
        assert name_item.text() == "Production Key"

    def test_update_api_keys_displays_status(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Table displays key status with correct text."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        # Third column should be status
        status_item = panel._table.item(0, 2)
        assert status_item is not None
        # Status should be title-cased
        assert status_item.text().lower() == "valid"

    def test_update_api_keys_stores_key_id(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Table items store key ID in UserRole."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        name_item = panel._table.item(0, 0)
        key_id = name_item.data(Qt.ItemDataRole.UserRole)
        assert key_id == "key-1"

    def test_update_robots_populates_filter(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """update_robots() populates robot filter dropdown."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_robots(sample_robots)

        # "All Robots" + 3 robots = 4 items
        assert panel._robot_filter.count() == 4

    def test_update_robots_preserves_selection(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """update_robots() preserves current selection."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        # Initial populate
        panel.update_robots(sample_robots)
        panel._robot_filter.setCurrentIndex(2)  # Select second robot

        # Update again
        panel.update_robots(sample_robots)

        # Selection should be preserved
        assert panel._robot_filter.currentIndex() == 2


class TestApiKeyPanelFiltering:
    """Tests for filtering API keys."""

    def test_search_filter_hides_non_matching_rows(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Search filter hides non-matching rows."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        panel._search_edit.setText("Production")

        # Only "Production Key" should be visible
        visible_count = sum(
            1 for i in range(panel._table.rowCount()) if not panel._table.isRowHidden(i)
        )
        assert visible_count == 1

    def test_search_filter_case_insensitive(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Search filter is case insensitive."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        panel._search_edit.setText("production")

        visible_count = sum(
            1 for i in range(panel._table.rowCount()) if not panel._table.isRowHidden(i)
        )
        assert visible_count == 1

    def test_status_filter_shows_only_matching(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Status filter shows only matching status."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        # Select "Revoked" filter (index 2)
        panel._status_filter.setCurrentIndex(2)  # "Revoked"

        visible_count = sum(
            1 for i in range(panel._table.rowCount()) if not panel._table.isRowHidden(i)
        )
        assert visible_count == 1

    def test_clear_search_shows_all_rows(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Clearing search shows all rows again."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        panel._search_edit.setText("Production")
        panel._search_edit.clear()

        visible_count = sum(
            1 for i in range(panel._table.rowCount()) if not panel._table.isRowHidden(i)
        )
        assert visible_count == 3


class TestApiKeyPanelSignals:
    """Tests for ApiKeyPanel signals."""

    def test_refresh_signal_emitted_on_button_click(self, qtbot) -> None:
        """refresh_requested signal emitted on refresh button click."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        with qtbot.waitSignal(panel.refresh_requested, timeout=1000):
            panel._refresh_btn.click()

    @pytest.mark.skip(reason="Complex dialog creates Qt crash in test environment")
    def test_key_generated_signal_emitted(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """key_generated signal emitted when dialog accepted."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_robots(sample_robots)

        # Mock the dialog to return accepted
        with patch.object(
            GenerateApiKeyDialog, "exec", return_value=QDialog.DialogCode.Accepted
        ):
            with patch.object(
                GenerateApiKeyDialog,
                "get_key_config",
                return_value={
                    "name": "Test Key",
                    "robot_id": "robot-123",
                    "expires_at": None,
                },
            ):
                with qtbot.waitSignal(panel.key_generated, timeout=1000) as blocker:
                    panel._generate_btn.click()

        assert blocker.args[0]["name"] == "Test Key"

    def test_key_revoked_signal_emitted(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """key_revoked signal emitted on revoke confirmation."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        # Mock QMessageBox to auto-confirm
        with patch.object(
            QMessageBox,
            "question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            with qtbot.waitSignal(panel.key_revoked, timeout=1000) as blocker:
                panel._on_revoke_key(sample_api_keys[0])

        assert blocker.args[0] == "key-1"


class TestApiKeyPanelStatusLabel:
    """Tests for status label updates."""

    def test_status_label_shows_count(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Status label shows key count."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        assert "3" in panel._status_label.text()

    def test_status_label_shows_active_count(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Status label shows active key count."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        # 2 active (valid + active status)
        assert "Active: 2" in panel._status_label.text()

    def test_status_label_shows_revoked_count(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Status label shows revoked key count."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys(sample_api_keys)

        assert "Revoked: 1" in panel._status_label.text()


class TestApiKeyPanelRefreshState:
    """Tests for refresh state handling."""

    def test_set_refreshing_disables_button(self, qtbot) -> None:
        """set_refreshing(True) disables refresh button."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.set_refreshing(True)

        assert not panel._refresh_btn.isEnabled()
        assert "Refreshing" in panel._refresh_btn.text()

    def test_set_refreshing_enables_button(self, qtbot) -> None:
        """set_refreshing(False) enables refresh button."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.set_refreshing(True)
        panel.set_refreshing(False)

        assert panel._refresh_btn.isEnabled()
        assert "Refresh" in panel._refresh_btn.text()


class TestApiKeyPanelTenant:
    """Tests for tenant-related functionality."""

    def test_set_tenant_stores_tenant_id(self, qtbot) -> None:
        """set_tenant() stores tenant ID."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.set_tenant("tenant-123")

        assert panel._tenant_id == "tenant-123"


class TestGenerateApiKeyDialog:
    """Tests for GenerateApiKeyDialog."""

    def test_dialog_creates_successfully(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Dialog can be created with robot list."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        assert dialog is not None

    def test_dialog_has_name_field(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Dialog has name input field."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        assert dialog._name_edit is not None

    def test_dialog_has_robot_selector(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Dialog has robot selector."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        assert dialog._robot_combo is not None
        # "Select Robot..." + 3 robots = 4 items
        assert dialog._robot_combo.count() == 4

    def test_dialog_has_expiration_option(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Dialog has expiration checkbox and date picker."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        assert dialog._expires_check is not None
        assert dialog._expires_edit is not None

    def test_expiration_disabled_by_default(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Expiration date picker is disabled by default."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        assert not dialog._expires_check.isChecked()
        assert not dialog._expires_edit.isEnabled()

    def test_expiration_enabled_when_checked(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Expiration date picker enabled when checkbox checked."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        dialog._expires_check.setChecked(True)

        assert dialog._expires_edit.isEnabled()

    def test_get_key_config_returns_form_data(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """get_key_config() returns form data as dict."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        dialog._name_edit.setText("Test Key Name")
        dialog._robot_combo.setCurrentIndex(1)  # First robot

        config = dialog.get_key_config()

        assert config["name"] == "Test Key Name"
        assert config["robot_id"] == "robot-123"

    def test_get_key_config_without_expiration(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """get_key_config() returns None for expires_at when unchecked."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        dialog._name_edit.setText("Test Key")
        dialog._robot_combo.setCurrentIndex(1)

        config = dialog.get_key_config()

        assert config["expires_at"] is None

    def test_generated_key_display(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """set_generated_key() displays the key."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)
        dialog.show()  # Need to show dialog for visibility checks

        dialog.set_generated_key("crpa_test_key_abc123")

        assert dialog._key_group.isVisible()
        assert "crpa_test_key_abc123" in dialog._key_display.toPlainText()

    def test_generated_key_disables_form(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """set_generated_key() disables form inputs."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        dialog.set_generated_key("crpa_test_key")

        assert not dialog._name_edit.isEnabled()
        assert not dialog._robot_combo.isEnabled()

    def test_copy_key_copies_to_clipboard(
        self, qtbot, sample_robots: List[Dict[str, Any]]
    ) -> None:
        """Copying key puts it in clipboard."""
        dialog = GenerateApiKeyDialog(robots=sample_robots)
        qtbot.addWidget(dialog)

        test_key = "crpa_test_key_clipboard"
        dialog.set_generated_key(test_key)

        # Mock clipboard and QMessageBox
        with patch.object(QMessageBox, "information"):
            dialog._copy_key()

        clipboard = QApplication.clipboard()
        assert clipboard.text() == test_key


class TestApiKeyPanelEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_api_keys_list(self, qtbot) -> None:
        """Panel handles empty API keys list."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_api_keys([])

        assert panel._table.rowCount() == 0
        assert "0" in panel._status_label.text()

    def test_api_key_with_missing_fields(self, qtbot) -> None:
        """Panel handles API keys with missing optional fields."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        minimal_key = [{"id": "key-1", "name": "Minimal", "status": "valid"}]
        panel.update_api_keys(minimal_key)

        assert panel._table.rowCount() == 1

    def test_api_key_with_datetime_objects(self, qtbot) -> None:
        """Panel handles datetime objects (not just strings)."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        key_with_datetime = [
            {
                "id": "key-1",
                "name": "Test Key",
                "status": "valid",
                "created_at": datetime(2024, 1, 1, 0, 0, 0),
                "last_used_at": datetime(2024, 6, 15, 12, 0, 0),
            }
        ]
        panel.update_api_keys(key_with_datetime)

        assert panel._table.rowCount() == 1

    def test_robot_filter_with_empty_robots(self, qtbot) -> None:
        """Robot filter handles empty robot list."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)

        panel.update_robots([])

        # Should only have "All Robots" option
        assert panel._robot_filter.count() == 1


class TestApiKeyPanelActionsColumn:
    """Tests for the actions column in the table."""

    def test_valid_key_has_revoke_button(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Valid keys have a revoke button."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        # Get actions widget for first row (valid key)
        actions_widget = panel._table.cellWidget(0, 7)
        assert actions_widget is not None

        # Should contain a Revoke button
        buttons = actions_widget.findChildren(type(panel._generate_btn))
        button_texts = [b.text() for b in buttons]
        assert "Revoke" in button_texts

    def test_valid_key_has_rotate_button(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Valid keys have a rotate button."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        actions_widget = panel._table.cellWidget(0, 7)
        buttons = actions_widget.findChildren(type(panel._generate_btn))
        button_texts = [b.text() for b in buttons]
        assert "Rotate" in button_texts

    def test_revoked_key_shows_inactive_label(
        self, qtbot, sample_api_keys: List[Dict[str, Any]]
    ) -> None:
        """Revoked keys show 'Inactive' label instead of buttons."""
        panel = ApiKeyPanel()
        qtbot.addWidget(panel)
        panel.update_api_keys(sample_api_keys)

        # Third row is revoked key
        actions_widget = panel._table.cellWidget(2, 7)

        # Should not have Revoke/Rotate buttons
        from PySide6.QtWidgets import QPushButton

        buttons = actions_widget.findChildren(QPushButton)
        button_texts = [b.text() for b in buttons]
        assert "Revoke" not in button_texts
        assert "Rotate" not in button_texts

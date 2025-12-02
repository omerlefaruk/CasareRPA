"""
Tests for TenantSelectorWidget and TenantFilterWidget.

Tests the tenant selection UI for switching between tenants
and filtering data by tenant. Uses pytest-qt (qtbot) for Qt widget testing.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Skip tests if Qt not available (CI environment)
pytest.importorskip("PySide6")

from PySide6.QtCore import Qt

from casare_rpa.presentation.canvas.ui.widgets.tenant_selector import (
    TenantSelectorWidget,
    TenantFilterWidget,
)


@pytest.fixture
def sample_tenants() -> List[Dict[str, Any]]:
    """Sample tenant data for testing."""
    return [
        {"id": "tenant-1", "name": "Acme Corp", "robot_count": 5},
        {"id": "tenant-2", "name": "Beta Inc", "robot_count": 3},
        {"id": "tenant-3", "name": "Gamma LLC", "robot_count": 10},
    ]


class TestTenantSelectorWidgetCreation:
    """Tests for TenantSelectorWidget creation."""

    def test_widget_creates_successfully(self, qtbot) -> None:
        """TenantSelectorWidget can be created."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        assert widget is not None

    def test_widget_has_label(self, qtbot) -> None:
        """Widget has a label."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        assert widget._label is not None
        assert widget._label.text() == "Tenant:"

    def test_widget_custom_label(self, qtbot) -> None:
        """Widget accepts custom label text."""
        widget = TenantSelectorWidget(label_text="Select Tenant:")
        qtbot.addWidget(widget)

        assert widget._label.text() == "Select Tenant:"

    def test_widget_has_combo(self, qtbot) -> None:
        """Widget has a combo box."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        assert widget._combo is not None

    def test_widget_has_refresh_button(self, qtbot) -> None:
        """Widget has a refresh button (hidden by default)."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        assert widget._refresh_btn is not None
        assert not widget._refresh_btn.isVisible()

    def test_refresh_button_can_be_shown(self, qtbot) -> None:
        """Refresh button can be made visible."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.show()  # Need to show parent for child visibility

        widget.set_show_refresh(True)

        # Check that visibility flag is set (actual visibility depends on parent)
        assert widget._refresh_btn.isVisibleTo(widget)


class TestTenantSelectorWidgetData:
    """Tests for updating tenant data."""

    def test_update_tenants_populates_combo(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """update_tenants() populates combo box."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants(sample_tenants)

        # Should have 3 tenants (no All Tenants option by default for non-super admin)
        assert widget._combo.count() == 3

    def test_update_tenants_shows_robot_count(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Combo items show robot count."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants(sample_tenants)

        # First item text should include robot count
        first_text = widget._combo.itemText(0)
        assert "5 robots" in first_text

    def test_update_tenants_stores_tenant_id(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Combo items store tenant ID as data."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants(sample_tenants)

        tenant_id = widget._combo.itemData(0)
        assert tenant_id == "tenant-1"

    def test_update_tenants_preserves_selection(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """update_tenants() preserves current selection."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants(sample_tenants)
        widget._combo.setCurrentIndex(1)  # Select "Beta Inc"

        widget.update_tenants(sample_tenants)

        assert widget._combo.currentIndex() == 1


class TestTenantSelectorWidgetAllTenantsOption:
    """Tests for 'All Tenants' option."""

    def test_all_tenants_shown_for_super_admin(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """'All Tenants' option shown when super admin."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)

        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # "All Tenants" + 3 tenants = 4 items
        assert widget._combo.count() == 4
        assert widget._combo.itemText(0) == "All Tenants"

    def test_all_tenants_hidden_for_regular_user(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """'All Tenants' option hidden for non-super admin."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)

        widget.set_super_admin(False)
        widget.update_tenants(sample_tenants)

        assert widget._combo.count() == 3
        assert widget._combo.itemText(0) != "All Tenants"

    def test_all_tenants_disabled_via_parameter(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """'All Tenants' can be disabled via show_all_option."""
        widget = TenantSelectorWidget(show_all_option=False)
        qtbot.addWidget(widget)

        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # Should not have "All Tenants" even for super admin
        assert widget._combo.count() == 3

    def test_selecting_all_tenants_returns_none(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Selecting 'All Tenants' returns None for tenant_id."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)

        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)
        widget._combo.setCurrentIndex(0)  # "All Tenants"

        assert widget.get_current_tenant_id() is None


class TestTenantSelectorWidgetSignals:
    """Tests for widget signals."""

    def test_tenant_changed_signal_emitted(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """tenant_changed signal emitted on selection change."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.update_tenants(sample_tenants)

        with qtbot.waitSignal(widget.tenant_changed, timeout=1000) as blocker:
            widget._combo.setCurrentIndex(1)

        assert blocker.args[0] == "tenant-2"

    def test_tenant_changed_emits_none_for_all(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """tenant_changed emits None when 'All Tenants' selected."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)
        widget._combo.setCurrentIndex(1)  # Select a tenant first

        with qtbot.waitSignal(widget.tenant_changed, timeout=1000) as blocker:
            widget._combo.setCurrentIndex(0)  # "All Tenants"

        assert blocker.args[0] is None

    def test_refresh_signal_emitted(self, qtbot) -> None:
        """refresh_requested signal emitted on refresh click."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_show_refresh(True)

        with qtbot.waitSignal(widget.refresh_requested, timeout=1000):
            widget._refresh_btn.click()


class TestTenantSelectorWidgetMethods:
    """Tests for widget methods."""

    def test_get_current_tenant_id(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """get_current_tenant_id() returns selected tenant ID."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.update_tenants(sample_tenants)

        widget._combo.setCurrentIndex(1)

        assert widget.get_current_tenant_id() == "tenant-2"

    def test_get_current_tenant_name(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """get_current_tenant_name() returns display text."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.update_tenants(sample_tenants)

        widget._combo.setCurrentIndex(0)

        name = widget.get_current_tenant_name()
        assert "Acme Corp" in name

    def test_set_current_tenant(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """set_current_tenant() selects tenant by ID."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.update_tenants(sample_tenants)

        widget.set_current_tenant("tenant-3")

        assert widget.get_current_tenant_id() == "tenant-3"

    def test_set_current_tenant_to_all(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """set_current_tenant(None) selects 'All Tenants'."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)
        widget._combo.setCurrentIndex(1)  # Select a tenant first

        widget.set_current_tenant(None)

        assert widget.is_all_tenants_selected()

    def test_is_all_tenants_selected_true(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """is_all_tenants_selected() returns True when 'All Tenants' selected."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)
        widget._combo.setCurrentIndex(0)  # "All Tenants"

        assert widget.is_all_tenants_selected() is True

    def test_is_all_tenants_selected_false(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """is_all_tenants_selected() returns False when tenant selected."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)
        widget._combo.setCurrentIndex(1)  # Tenant, not "All Tenants"

        assert widget.is_all_tenants_selected() is False

    def test_count_excludes_all_tenants(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """count() returns tenant count excluding 'All Tenants' option."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # Combo has 4 items, but count() should return 3
        assert widget._combo.count() == 4
        assert widget.count() == 3


class TestTenantSelectorWidgetEnable:
    """Tests for enabling/disabling the widget."""

    def test_disable_widget(self, qtbot, sample_tenants: List[Dict[str, Any]]) -> None:
        """setEnabled(False) disables combo and refresh."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_show_refresh(True)
        widget.update_tenants(sample_tenants)

        widget.setEnabled(False)

        assert not widget._combo.isEnabled()
        assert not widget._refresh_btn.isEnabled()

    def test_enable_widget(self, qtbot, sample_tenants: List[Dict[str, Any]]) -> None:
        """setEnabled(True) enables combo and refresh."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)
        widget.set_show_refresh(True)
        widget.update_tenants(sample_tenants)
        widget.setEnabled(False)

        widget.setEnabled(True)

        assert widget._combo.isEnabled()
        assert widget._refresh_btn.isEnabled()


class TestTenantFilterWidget:
    """Tests for TenantFilterWidget (filter variant)."""

    def test_filter_widget_creates_successfully(self, qtbot) -> None:
        """TenantFilterWidget can be created."""
        widget = TenantFilterWidget()
        qtbot.addWidget(widget)

        assert widget is not None

    def test_filter_widget_has_filter_label(self, qtbot) -> None:
        """TenantFilterWidget has 'Filter by Tenant:' label."""
        widget = TenantFilterWidget()
        qtbot.addWidget(widget)

        assert "Filter by Tenant" in widget._label.text()

    def test_filter_widget_selects_all_by_default(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """TenantFilterWidget selects 'All Tenants' by default for super admin."""
        widget = TenantFilterWidget()
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # Should default to "All Tenants" (index 0)
        assert widget._combo.currentIndex() == 0
        assert widget.is_all_tenants_selected()

    def test_filter_widget_inherits_functionality(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """TenantFilterWidget inherits TenantSelectorWidget functionality."""
        widget = TenantFilterWidget()
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # Should have all base functionality
        assert hasattr(widget, "tenant_changed")
        assert hasattr(widget, "refresh_requested")
        assert hasattr(widget, "get_current_tenant_id")
        assert hasattr(widget, "set_current_tenant")


class TestTenantSelectorWidgetEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_tenants_list(self, qtbot) -> None:
        """Widget handles empty tenant list."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants([])

        assert widget._combo.count() == 0

    def test_single_tenant_auto_selects(self, qtbot) -> None:
        """Single tenant is auto-selected."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants([{"id": "t1", "name": "Only Tenant", "robot_count": 1}])

        assert widget._combo.currentIndex() == 0
        assert widget.get_current_tenant_id() == "t1"

    def test_tenant_missing_robot_count(self, qtbot) -> None:
        """Widget handles tenant without robot_count."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        widget.update_tenants([{"id": "t1", "name": "Test"}])

        assert widget._combo.count() == 1
        # Should show 0 robots
        assert "0 robots" in widget._combo.itemText(0)

    def test_super_admin_toggle_refreshes_dropdown(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Toggling super_admin status refreshes dropdown."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.update_tenants(sample_tenants)

        # Initially not super admin
        assert widget._combo.count() == 3

        # Become super admin
        widget.set_super_admin(True)

        # Should now have "All Tenants"
        assert widget._combo.count() == 4

        # Revoke super admin
        widget.set_super_admin(False)

        # Should no longer have "All Tenants"
        assert widget._combo.count() == 3

    def test_set_show_all_option_refreshes_dropdown(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Toggling show_all_option refreshes dropdown."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        assert widget._combo.count() == 4  # With "All Tenants"

        widget.set_show_all_option(False)

        assert widget._combo.count() == 3  # Without "All Tenants"

    def test_get_current_tenant_name_empty(self, qtbot) -> None:
        """get_current_tenant_name() returns empty string when no selection."""
        widget = TenantSelectorWidget()
        qtbot.addWidget(widget)

        # No tenants loaded, no selection
        name = widget.get_current_tenant_name()

        assert name == ""


class TestTenantSelectorWidgetIntegration:
    """Integration-style tests for tenant selector."""

    def test_super_admin_workflow(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Complete super admin workflow."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)

        # Step 1: Load as super admin
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # Verify "All Tenants" is available
        assert widget._combo.count() == 4
        assert widget._combo.itemText(0) == "All Tenants"

        # Step 2: Select "All Tenants"
        widget._combo.setCurrentIndex(0)
        assert widget.get_current_tenant_id() is None
        assert widget.is_all_tenants_selected()

        # Step 3: Switch to specific tenant
        widget._combo.setCurrentIndex(2)  # "Beta Inc"
        assert widget.get_current_tenant_id() == "tenant-2"
        assert not widget.is_all_tenants_selected()

        # Step 4: Use set_current_tenant
        widget.set_current_tenant("tenant-3")
        assert widget.get_current_tenant_id() == "tenant-3"

        # Step 5: Return to "All Tenants"
        widget.set_current_tenant(None)
        assert widget.is_all_tenants_selected()

    def test_regular_user_workflow(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Complete regular user workflow (no All Tenants)."""
        widget = TenantSelectorWidget(show_all_option=True)
        qtbot.addWidget(widget)

        # Step 1: Load as regular user
        widget.set_super_admin(False)
        widget.update_tenants(sample_tenants)

        # Verify no "All Tenants" option
        assert widget._combo.count() == 3
        assert widget._combo.itemText(0) != "All Tenants"

        # Step 2: Select first tenant - manually trigger selection changed
        widget._combo.setCurrentIndex(0)
        widget._on_selection_changed(0)  # Manually call handler like Qt would
        assert widget.get_current_tenant_id() == "tenant-1"

        # Step 3: Switch between tenants
        widget._combo.setCurrentIndex(1)
        widget._on_selection_changed(1)
        assert widget.get_current_tenant_id() == "tenant-2"

        widget.set_current_tenant("tenant-3")
        assert widget.get_current_tenant_id() == "tenant-3"

    def test_filter_widget_workflow(
        self, qtbot, sample_tenants: List[Dict[str, Any]]
    ) -> None:
        """Complete filter widget workflow."""
        widget = TenantFilterWidget()
        qtbot.addWidget(widget)

        # Setup as super admin
        widget.set_super_admin(True)
        widget.update_tenants(sample_tenants)

        # Should default to "All Tenants" for filtering
        assert widget.is_all_tenants_selected()

        # Filter by specific tenant
        widget._combo.setCurrentIndex(2)  # "Beta Inc"
        tenant_id = widget.get_current_tenant_id()
        assert tenant_id == "tenant-2"

        # Reset to show all
        widget._combo.setCurrentIndex(0)
        assert widget.is_all_tenants_selected()
        assert widget.get_current_tenant_id() is None

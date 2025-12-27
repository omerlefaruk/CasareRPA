"""
Tenant Selector Widget.

Provides a dropdown for admin users to switch between tenants.
Super admins can select "All Tenants" to view all robots.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME


class TenantSelectorWidget(QWidget):
    """
    Widget for selecting active tenant.

    Features:
    - Dropdown to switch between tenants
    - "All Tenants" option for super admin
    - Shows current tenant name
    - Refresh button

    Signals:
        tenant_changed: Emitted when tenant selection changes (tenant_id or None for all)
        refresh_requested: Emitted when refresh is clicked
    """

    tenant_changed = Signal(object)  # str tenant_id or None for "All Tenants"
    refresh_requested = Signal()

    # Special value for "All Tenants" selection
    ALL_TENANTS = "__ALL_TENANTS__"

    def __init__(
        self,
        parent: QWidget | None = None,
        show_all_option: bool = True,
        label_text: str = "Tenant:",
    ) -> None:
        """
        Initialize the tenant selector.

        Args:
            parent: Parent widget.
            show_all_option: Whether to show "All Tenants" option.
            label_text: Label text before dropdown.
        """
        super().__init__(parent)
        self._tenants: list[dict[str, Any]] = []
        self._show_all_option = show_all_option
        self._label_text = label_text
        self._current_tenant_id: str | None = None
        self._is_super_admin = False
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._label = QLabel(self._label_text)
        layout.addWidget(self._label)

        self._combo = QComboBox()
        self._combo.setMinimumWidth(200)
        self._combo.currentIndexChanged.connect(self._on_selection_changed)
        layout.addWidget(self._combo)

        self._refresh_btn = QPushButton()
        self._refresh_btn.setText("Refresh")
        self._refresh_btn.setMaximumWidth(80)
        self._refresh_btn.clicked.connect(self._on_refresh)
        self._refresh_btn.setVisible(False)  # Hidden by default
        layout.addWidget(self._refresh_btn)

    def _apply_styles(self) -> None:
        self.setStyleSheet(f"""
            QLabel {{
                color: {THEME.text_primary};
            }}
            QComboBox {{
                background: {THEME.bg_hover};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 4px 8px;
                min-height: 24px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {THEME.text_muted};
                margin-right: 6px;
            }}
            QComboBox QAbstractItemView {{
                background: {THEME.bg_hover};
                border: 1px solid {THEME.border};
                color: {THEME.text_primary};
                selection-background-color: {THEME.primary};
            }}
            QPushButton {{
                background: {THEME.bg_hover};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                color: {THEME.text_primary};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}
        """)

    def set_super_admin(self, is_super_admin: bool) -> None:
        """
        Set whether current user is a super admin.

        Super admins can see "All Tenants" option.

        Args:
            is_super_admin: True if user is super admin.
        """
        self._is_super_admin = is_super_admin
        self._refresh_dropdown()

    def set_show_all_option(self, show: bool) -> None:
        """
        Set whether to show "All Tenants" option.

        Args:
            show: True to show option.
        """
        self._show_all_option = show
        self._refresh_dropdown()

    def set_show_refresh(self, show: bool) -> None:
        """
        Set whether to show refresh button.

        Args:
            show: True to show button.
        """
        self._refresh_btn.setVisible(show)

    def update_tenants(self, tenants: list[dict[str, Any]]) -> None:
        """
        Update the list of available tenants.

        Args:
            tenants: List of tenant dictionaries with 'id' and 'name' keys.
        """
        self._tenants = tenants
        self._refresh_dropdown()

    def _refresh_dropdown(self) -> None:
        """Refresh the dropdown contents."""
        current_data = self._combo.currentData()

        self._combo.blockSignals(True)
        self._combo.clear()

        # Add "All Tenants" option if applicable
        if self._show_all_option and self._is_super_admin:
            self._combo.addItem("All Tenants", self.ALL_TENANTS)

        # Add each tenant
        for tenant in self._tenants:
            name = tenant.get("name", "Unknown")
            tenant_id = tenant.get("id", "")
            robot_count = tenant.get("robot_count", 0)

            display_text = f"{name} ({robot_count} robots)"
            self._combo.addItem(display_text, tenant_id)

        # Restore selection
        if current_data:
            for i in range(self._combo.count()):
                if self._combo.itemData(i) == current_data:
                    self._combo.setCurrentIndex(i)
                    break

        self._combo.blockSignals(False)

        # If no selection made and only one tenant, select it
        if self._combo.count() == 1:
            self._combo.setCurrentIndex(0)
            self._on_selection_changed(0)
        elif self._combo.count() > 0 and self._combo.currentIndex() == -1:
            self._combo.setCurrentIndex(0)

    def _on_selection_changed(self, index: int) -> None:
        """Handle dropdown selection change."""
        if index < 0:
            return

        tenant_id = self._combo.currentData()

        if tenant_id == self.ALL_TENANTS:
            self._current_tenant_id = None
            self.tenant_changed.emit(None)
            logger.debug("Tenant selection: All Tenants")
        else:
            self._current_tenant_id = tenant_id
            self.tenant_changed.emit(tenant_id)
            logger.debug(f"Tenant selection: {tenant_id}")

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        self.refresh_requested.emit()

    def get_current_tenant_id(self) -> str | None:
        """
        Get currently selected tenant ID.

        Returns:
            Tenant ID string, or None if "All Tenants" is selected.
        """
        return self._current_tenant_id

    def get_current_tenant_name(self) -> str:
        """
        Get currently selected tenant name.

        Returns:
            Tenant name or "All Tenants".
        """
        if self._combo.currentIndex() < 0:
            return ""
        return self._combo.currentText()

    def set_current_tenant(self, tenant_id: str | None) -> None:
        """
        Set current tenant selection programmatically.

        Args:
            tenant_id: Tenant ID to select, or None for "All Tenants".
        """
        target_data = self.ALL_TENANTS if tenant_id is None else tenant_id

        for i in range(self._combo.count()):
            if self._combo.itemData(i) == target_data:
                self._combo.setCurrentIndex(i)
                break

    def is_all_tenants_selected(self) -> bool:
        """
        Check if "All Tenants" is currently selected.

        Returns:
            True if "All Tenants" is selected.
        """
        return self._current_tenant_id is None and self._show_all_option

    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the selector."""
        super().setEnabled(enabled)
        self._combo.setEnabled(enabled)
        self._refresh_btn.setEnabled(enabled)

    def count(self) -> int:
        """Get number of tenants in dropdown (excluding 'All Tenants')."""
        count = self._combo.count()
        if self._show_all_option and self._is_super_admin and count > 0:
            count -= 1  # Subtract the "All Tenants" option
        return count


class TenantFilterWidget(TenantSelectorWidget):
    """
    Tenant filter widget variant for use in data tables.

    Same as TenantSelectorWidget but with "All Tenants" selected by default
    and designed for filtering lists rather than context switching.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        show_all_option: bool = True,
    ) -> None:
        super().__init__(
            parent=parent,
            show_all_option=show_all_option,
            label_text="Filter by Tenant:",
        )

    def _refresh_dropdown(self) -> None:
        """Refresh dropdown with filter-specific defaults."""
        super()._refresh_dropdown()

        # Select "All Tenants" by default for filtering
        if self._show_all_option and self._is_super_admin:
            self._combo.setCurrentIndex(0)


__all__ = [
    "TenantSelectorWidget",
    "TenantFilterWidget",
]

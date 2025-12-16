"""
API Keys Tab Widget for Fleet Dashboard.

Manages robot API keys with tenant isolation support.
"""

from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal


from casare_rpa.presentation.canvas.ui.panels.api_key_panel import ApiKeyPanel


class ApiKeysTabWidget(QWidget):
    """
    Widget for managing API keys in the fleet dashboard.

    Wraps ApiKeyPanel and adds tenant filtering support.

    Signals:
        key_generated: Emitted when new key requested (config_dict)
        key_revoked: Emitted when key revoked (key_id)
        key_rotated: Emitted when key rotation requested (key_id)
        refresh_requested: Emitted when refresh clicked
    """

    key_generated = Signal(dict)
    key_revoked = Signal(str)
    key_rotated = Signal(str)

    # FleetDashboardDialog expects these names
    api_key_generated = Signal(dict)
    api_key_revoked = Signal(str)
    api_key_rotated = Signal(str)

    refresh_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tenant_id: Optional[str] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._panel = ApiKeyPanel()
        self._panel.key_generated.connect(self.key_generated.emit)
        self._panel.key_generated.connect(self.api_key_generated.emit)

        self._panel.key_revoked.connect(self.key_revoked.emit)
        self._panel.key_revoked.connect(self.api_key_revoked.emit)

        self._panel.key_rotated.connect(self.key_rotated.emit)
        self._panel.key_rotated.connect(self.api_key_rotated.emit)

        self._panel.refresh_requested.connect(self.refresh_requested.emit)

        layout.addWidget(self._panel)

    def set_tenant(self, tenant_id: Optional[str]) -> None:
        """
        Set current tenant for filtering.

        Args:
            tenant_id: Tenant ID or None for all tenants.
        """
        self._tenant_id = tenant_id
        self._panel.set_tenant(tenant_id)

    def update_robots(self, robots: List[Dict[str, Any]]) -> None:
        """
        Update available robots list.

        Args:
            robots: List of robot dictionaries.
        """
        # Filter by tenant if set
        if self._tenant_id:
            robots = [r for r in robots if r.get("tenant_id") == self._tenant_id]
        self._panel.update_robots(robots)

    def update_api_keys(self, api_keys: List[Dict[str, Any]]) -> None:
        """
        Update API keys list.

        Args:
            api_keys: List of API key dictionaries.
        """
        # Filter by tenant if set
        if self._tenant_id:
            api_keys = [k for k in api_keys if k.get("tenant_id") == self._tenant_id]
        self._panel.update_api_keys(api_keys)

    def set_refreshing(self, refreshing: bool) -> None:
        """Set refresh button state."""
        self._panel.set_refreshing(refreshing)


__all__ = ["ApiKeysTabWidget"]

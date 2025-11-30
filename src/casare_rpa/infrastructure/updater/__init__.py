"""
CasareRPA Auto-Update Infrastructure.

Provides secure software distribution using TUF (The Update Framework):
- Cryptographically verified downloads
- Rollback protection
- Role separation (root, targets, snapshot, timestamp)
- Atomic updates
"""

from casare_rpa.infrastructure.updater.tuf_updater import TUFUpdater, UpdateInfo
from casare_rpa.infrastructure.updater.update_manager import UpdateManager

__all__ = ["TUFUpdater", "UpdateInfo", "UpdateManager"]

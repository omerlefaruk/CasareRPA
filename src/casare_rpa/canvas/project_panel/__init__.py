"""
CasareRPA - Project Panel UI Components

This module provides the left dock panel for managing projects and scenarios.

Uses Qt Model/View architecture:
- ProjectModel: QAbstractItemModel wrapping ProjectManager
- ProjectProxyModel: QSortFilterProxyModel for filtering
- ProjectTreeView: QTreeView for display
- ProjectPanelDock: Container dock widget
"""

from .project_panel_dock import ProjectPanelDock
from .project_model import ProjectModel, TreeItemType, TreeItem
from .project_proxy_model import ProjectProxyModel
from .project_tree_view import ProjectTreeView

# Backward compatibility alias - ProjectTreeWidget is now ProjectTreeView
# The old widget-based approach has been replaced with Model/View
ProjectTreeWidget = ProjectTreeView

__all__ = [
    "ProjectPanelDock",
    "ProjectModel",
    "ProjectProxyModel",
    "ProjectTreeView",
    "ProjectTreeWidget",  # Deprecated alias for backward compatibility
    "TreeItemType",
    "TreeItem",
]

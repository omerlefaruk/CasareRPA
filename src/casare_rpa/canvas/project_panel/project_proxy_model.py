"""
CasareRPA - Project Proxy Model (QSortFilterProxyModel)

Provides filtering capabilities for the project tree without modifying
the source model. Supports recursive filtering where matching children
keep their parents visible.
"""

from typing import Optional

from PySide6.QtCore import (
    Qt,
    QSortFilterProxyModel,
    QModelIndex,
    QRegularExpression,
)
from loguru import logger

from .project_model import ProjectModel, TreeItemType


class ProjectProxyModel(QSortFilterProxyModel):
    """
    Proxy model for filtering the project tree.

    Features:
    - Case-insensitive text filtering
    - Recursive filtering (parents visible if children match)
    - Headers always visible
    - Automatic expansion of matching branches
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # Enable recursive filtering - if a child matches, parent is visible
        self.setRecursiveFilteringEnabled(True)

        # Case insensitive filtering
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

        # Filter on display role (text)
        self.setFilterRole(Qt.ItemDataRole.DisplayRole)

        # Don't automatically filter on data changes (we control refresh)
        self.setDynamicSortFilter(False)

        self._filter_text: str = ""

    def setFilterText(self, text: str) -> None:
        """
        Set the filter text.

        Args:
            text: Text to filter by (empty string shows all)
        """
        self._filter_text = text.strip().lower()

        # Use beginFilterChange/endFilterChange for proper update
        self.beginFilterChange()
        # The actual filtering happens in filterAcceptsRow
        self.endFilterChange()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """
        Determine if a row should be shown.

        Args:
            source_row: Row in source model
            source_parent: Parent index in source model

        Returns:
            True if row should be visible
        """
        source_model = self.sourceModel()
        if not source_model:
            return True

        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return True

        # Get item type
        item_type = source_model.data(index, ProjectModel.ItemTypeRole)

        # Headers are always visible
        if item_type in (TreeItemType.PROJECTS_HEADER, TreeItemType.GLOBAL_HEADER):
            return True

        # If no filter, show everything
        if not self._filter_text:
            return True

        # Check if this item's text matches
        display_text = source_model.data(index, Qt.ItemDataRole.DisplayRole)
        if display_text and self._filter_text in display_text.lower():
            return True

        # Check if any child matches (recursive filtering handles parent visibility)
        # This is handled by Qt's recursive filtering when enabled
        return False

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """
        Compare two items for sorting.

        We don't actually sort the tree (order is determined by model),
        but this is required for QSortFilterProxyModel.
        """
        # Keep original order
        return left.row() < right.row()

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def getSourceIndex(self, proxy_index: QModelIndex) -> QModelIndex:
        """Convert proxy index to source model index."""
        return self.mapToSource(proxy_index)

    def getProxyIndex(self, source_index: QModelIndex) -> QModelIndex:
        """Convert source model index to proxy index."""
        return self.mapFromSource(source_index)

    def getItemType(self, proxy_index: QModelIndex) -> Optional[TreeItemType]:
        """Get item type from proxy index."""
        source_model = self.sourceModel()
        if not source_model or not proxy_index.isValid():
            return None

        source_index = self.mapToSource(proxy_index)
        return source_model.data(source_index, ProjectModel.ItemTypeRole)

    def getItemData(self, proxy_index: QModelIndex):
        """Get item data from proxy index."""
        source_model = self.sourceModel()
        if not source_model or not proxy_index.isValid():
            return None

        source_index = self.mapToSource(proxy_index)
        return source_model.data(source_index, ProjectModel.ItemDataRole)

    def clearFilter(self) -> None:
        """Clear the current filter."""
        self.setFilterText("")

    @property
    def hasFilter(self) -> bool:
        """Check if a filter is currently active."""
        return bool(self._filter_text)

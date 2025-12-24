"""
Icon texture atlas for efficient GPU rendering.

Combines all node icons into a single texture to reduce GPU state changes.
When rendering many nodes, drawing from a single atlas texture is more
efficient than switching textures for each node icon.

Performance benefits:
- Single texture bind per frame instead of per-node
- Better GPU cache utilization
- Reduced draw call overhead
- Less texture memory fragmentation
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QPixmap


class IconTextureAtlas:
    """
    Texture atlas combining all node icons.

    Icons are arranged in a grid within a single large QPixmap.
    Each icon gets a slot in the atlas, and drawing uses source
    rectangle from the atlas rather than individual pixmaps.

    Usage:
        # At startup
        atlas = get_icon_atlas()
        atlas.initialize()
        preload_node_icons()

        # In paint()
        atlas.draw_icon(painter, "ClickNode", target_rect)
    """

    _instance: Optional["IconTextureAtlas"] = None

    ATLAS_SIZE: int = 1024  # 1024x1024 atlas
    ICON_SIZE: int = 48  # 48x48 per icon (matches node icon size)
    ICONS_PER_ROW: int = 1024 // 48  # 21 icons per row

    def __new__(cls) -> "IconTextureAtlas":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._atlas: QPixmap | None = None
            cls._instance._icon_positions: dict[str, tuple[int, int]] = {}
            cls._instance._next_slot = 0
            cls._instance._initialized = False
        return cls._instance

    def initialize(self) -> None:
        """
        Initialize atlas pixmap. Call once at startup.

        Creates the atlas pixmap with transparent background.
        """
        if self._initialized:
            return

        self._atlas = QPixmap(self.ATLAS_SIZE, self.ATLAS_SIZE)
        self._atlas.fill(Qt.GlobalColor.transparent)
        self._initialized = True
        logger.debug("Icon texture atlas initialized")

    def add_icon(self, identifier: str, pixmap: QPixmap) -> tuple[int, int]:
        """
        Add icon to atlas.

        Args:
            identifier: Unique icon identifier (e.g., node type name)
            pixmap: Icon pixmap to add

        Returns:
            (x, y) position in atlas where icon was placed
        """
        if not self._initialized:
            self.initialize()

        if identifier in self._icon_positions:
            return self._icon_positions[identifier]

        # Calculate position in grid
        row = self._next_slot // self.ICONS_PER_ROW
        col = self._next_slot % self.ICONS_PER_ROW

        if row >= self.ICONS_PER_ROW:
            # Atlas full - could create second atlas or log warning
            logger.warning(f"Icon atlas full, cannot add icon: {identifier}")
            return (0, 0)

        x = col * self.ICON_SIZE
        y = row * self.ICON_SIZE

        # Draw icon to atlas
        painter = QPainter(self._atlas)

        # Scale icon to fit slot while maintaining aspect ratio
        scaled = pixmap.scaled(
            self.ICON_SIZE,
            self.ICON_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Center in slot
        offset_x = (self.ICON_SIZE - scaled.width()) // 2
        offset_y = (self.ICON_SIZE - scaled.height()) // 2
        painter.drawPixmap(x + offset_x, y + offset_y, scaled)
        painter.end()

        self._icon_positions[identifier] = (x, y)
        self._next_slot += 1

        return (x, y)

    def get_atlas(self) -> QPixmap | None:
        """
        Get the combined atlas pixmap.

        Returns:
            The atlas QPixmap or None if not initialized
        """
        return self._atlas

    def get_icon_rect(self, identifier: str) -> QRect:
        """
        Get source rect for icon in atlas.

        Args:
            identifier: Icon identifier

        Returns:
            QRect for source area in atlas (or default rect if not found)
        """
        if identifier not in self._icon_positions:
            return QRect(0, 0, self.ICON_SIZE, self.ICON_SIZE)

        x, y = self._icon_positions[identifier]
        return QRect(x, y, self.ICON_SIZE, self.ICON_SIZE)

    def has_icon(self, identifier: str) -> bool:
        """
        Check if icon is in atlas.

        Args:
            identifier: Icon identifier

        Returns:
            True if icon exists in atlas
        """
        return identifier in self._icon_positions

    def draw_icon(self, painter: QPainter, identifier: str, target_rect: QRect) -> bool:
        """
        Draw icon from atlas to target rect.

        This is the main method to use in paint() for efficient icon drawing.

        Args:
            painter: Active QPainter
            identifier: Icon identifier
            target_rect: Target rectangle to draw into

        Returns:
            True if icon was drawn, False if not found
        """
        if not self._atlas or identifier not in self._icon_positions:
            return False

        source_rect = self.get_icon_rect(identifier)
        painter.drawPixmap(target_rect, self._atlas, source_rect)
        return True

    def get_icon_pixmap(self, identifier: str) -> QPixmap | None:
        """
        Get a copy of an icon as a separate pixmap.

        Use this when you need the icon outside of atlas drawing.

        Args:
            identifier: Icon identifier

        Returns:
            QPixmap copy of the icon or None if not found
        """
        if not self._atlas or identifier not in self._icon_positions:
            return None

        source_rect = self.get_icon_rect(identifier)
        return self._atlas.copy(source_rect)

    def get_stats(self) -> dict:
        """
        Get atlas statistics.

        Returns:
            Dict with atlas info
        """
        return {
            "icons_loaded": len(self._icon_positions),
            "max_icons": self.ICONS_PER_ROW * self.ICONS_PER_ROW,
            "atlas_size": f"{self.ATLAS_SIZE}x{self.ATLAS_SIZE}",
            "icon_size": f"{self.ICON_SIZE}x{self.ICON_SIZE}",
            "initialized": self._initialized,
        }

    def clear(self) -> None:
        """
        Clear the atlas (call when resetting or cleaning up).
        """
        if self._atlas:
            self._atlas.fill(Qt.GlobalColor.transparent)
        self._icon_positions.clear()
        self._next_slot = 0


def get_icon_atlas() -> IconTextureAtlas:
    """
    Get singleton icon atlas instance.

    Returns:
        The IconTextureAtlas singleton
    """
    return IconTextureAtlas()


def preload_node_icons() -> None:
    """
    Preload all node type icons into atlas.

    Call during application startup after node types are registered.
    This ensures all icons are in the atlas before first paint.
    """
    atlas = get_icon_atlas()
    atlas.initialize()

    icons_loaded = 0

    # Import node registry and load icons
    try:
        from casare_rpa.presentation.canvas.graph.node_icons import (
            get_cached_node_icon,
        )
        from casare_rpa.presentation.canvas.graph.node_registry import (
            get_node_registry,
        )

        # Get all registered visual node types
        registry = get_node_registry()
        node_classes = registry.get_all_nodes()

        for node_class in node_classes:
            try:
                # Get node type name (class name without Visual prefix)
                class_name = node_class.__name__
                if class_name.startswith("Visual") and class_name.endswith("Node"):
                    node_type_name = class_name[6:]  # Remove "Visual" prefix
                else:
                    node_type_name = class_name

                # Get icon for this node type
                icon = get_cached_node_icon(node_type_name)
                if icon and not icon.isNull():
                    atlas.add_icon(node_type_name, icon)
                    icons_loaded += 1
            except Exception as e:
                logger.debug(f"Could not load icon for {node_class.__name__}: {e}")

        logger.debug(f"Preloaded {icons_loaded} node icons into texture atlas")

    except ImportError as e:
        logger.debug(f"Node registry not available for icon preload: {e}")
    except Exception as e:
        logger.warning(f"Failed to preload node icons: {e}")

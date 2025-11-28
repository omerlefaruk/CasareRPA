"""
Graph rendering components for CasareRPA visual workflow editor.

Provides custom NodeGraphQt rendering elements:
- CasareNodeItem: Custom node rendering with animations
- CasarePipe: Custom connection rendering with labels
- Node icons and port shapes for visual styling
"""

from .custom_node_item import CasareNodeItem, AnimationCoordinator
from .custom_pipe import (
    CasarePipe,
    set_show_connection_labels,
    get_show_connection_labels,
)
from .node_icons import (
    CATEGORY_COLORS,
    get_cached_node_icon,
    get_cached_node_icon_path,
    create_node_icon_pixmap,
    get_node_color,
    register_custom_icon,
)
from .port_shapes import (
    draw_port_shape,
    get_shape_for_type,
    get_shape_description,
)

__all__ = [
    # Custom rendering
    "CasareNodeItem",
    "AnimationCoordinator",
    "CasarePipe",
    "set_show_connection_labels",
    "get_show_connection_labels",
    # Icon system
    "CATEGORY_COLORS",
    "get_cached_node_icon",
    "get_cached_node_icon_path",
    "create_node_icon_pixmap",
    "get_node_color",
    "register_custom_icon",
    # Port shapes
    "draw_port_shape",
    "get_shape_for_type",
    "get_shape_description",
]

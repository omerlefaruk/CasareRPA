"""
Graph rendering components for CasareRPA visual workflow editor.

Provides custom NodeGraphQt rendering elements:
- CasareNodeItem: Custom node rendering with animations
- CasarePipe: Custom connection rendering with labels
- Node icons and port shapes for visual styling
- SelectionManager: Node selection handling
- CompositeNodeCreator: Composite node creation (For Loop, While Loop, Try/Catch)
- NodeCreationHelper: Node creation assistance (SetVariable, drag-drop)
"""

from casare_rpa.presentation.canvas.graph.composite_node_creator import (
    CompositeNodeCreator,
)
from casare_rpa.presentation.canvas.graph.custom_node_item import (
    AnimationCoordinator,
    CasareNodeItem,
)
from casare_rpa.presentation.canvas.graph.custom_pipe import (
    CasarePipe,
    get_show_connection_labels,
    set_show_connection_labels,
)
from casare_rpa.presentation.canvas.graph.event_filters import (
    ConnectionDropFilter,
    OutputPortMMBFilter,
    TooltipBlocker,
)
from casare_rpa.presentation.canvas.graph.node_creation_helper import (
    NodeCreationHelper,
)
from casare_rpa.presentation.canvas.graph.node_icons import (
    CATEGORY_COLORS,
    create_node_icon_pixmap,
    get_cached_node_icon,
    get_cached_node_icon_path,
    get_node_color,
    register_custom_icon,
)
from casare_rpa.presentation.canvas.graph.port_shapes import (
    draw_port_shape,
    get_shape_description,
    get_shape_for_type,
)
from casare_rpa.presentation.canvas.graph.selection_manager import SelectionManager

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
    # Managers
    "SelectionManager",
    "CompositeNodeCreator",
    "NodeCreationHelper",
    # Event filters
    "TooltipBlocker",
    "OutputPortMMBFilter",
    "ConnectionDropFilter",
]

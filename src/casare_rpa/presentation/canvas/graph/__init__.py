"""
Graph rendering components for CasareRPA visual workflow editor.

Provides custom NodeGraphQt rendering elements:
- CasareNodeItem: Custom node rendering with animations
- CasarePipe: Custom connection rendering with labels and flow animation
- RerouteNodeItem: Custom reroute/dot node rendering
- Node icons and port shapes for visual styling
- SelectionManager: Node selection handling
- CompositeNodeCreator: Composite node creation (For Loop, While Loop, Try/Catch)
- NodeCreationHelper: Node creation assistance (SetVariable, drag-drop)

GPU Optimization Modules:
- LODManager: Centralized Level-of-Detail management
- BackgroundCache: Pre-rendered node backgrounds
- IconAtlas: Single texture for all node icons
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
from casare_rpa.presentation.canvas.graph.reroute_node_item import (
    RerouteNodeItem,
)
from casare_rpa.presentation.canvas.graph.subflow_node_item import (
    SubflowNodeItem,
)

# GPU Optimization Modules
from casare_rpa.presentation.canvas.graph.lod_manager import (
    LODLevel,
    ViewportLODManager,
    get_lod_manager,
)
from casare_rpa.presentation.canvas.graph.background_cache import (
    NodeBackgroundCache,
    get_background_cache,
)
from casare_rpa.presentation.canvas.graph.icon_atlas import (
    IconTextureAtlas,
    get_icon_atlas,
    preload_node_icons,
)

__all__ = [
    # Custom rendering
    "CasareNodeItem",
    "AnimationCoordinator",
    "CasarePipe",
    "set_show_connection_labels",
    "get_show_connection_labels",
    # Reroute node
    "RerouteNodeItem",
    # Subflow node
    "SubflowNodeItem",
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
    # GPU Optimization
    "LODLevel",
    "ViewportLODManager",
    "get_lod_manager",
    "NodeBackgroundCache",
    "get_background_cache",
    "IconTextureAtlas",
    "get_icon_atlas",
    "preload_node_icons",
]

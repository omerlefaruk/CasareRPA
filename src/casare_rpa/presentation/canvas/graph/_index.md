# Canvas Graph Index

Quick reference for graph rendering components. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | Custom NodeGraphQt rendering elements for visual workflow editor |
| Files | 27 files |
| Exports | 39 total exports |

## Custom Rendering

| Export | Source | Description |
|--------|--------|-------------|
| `CasareNodeItem` | `custom_node_item.py` | Custom node rendering with animations |
| `AnimationCoordinator` | `custom_node_item.py` | Node animation state coordinator |
| `CasarePipe` | `custom_pipe.py` | Custom connection with labels/flow animation |
| `RerouteNodeItem` | `reroute_node_item.py` | Reroute/dot node rendering |
| `SubflowNodeItem` | `subflow_node_item.py` | Subflow node rendering |

## Connection Labels

| Export | Description |
|--------|-------------|
| `get_show_connection_labels()` | Get label visibility state |
| `set_show_connection_labels(bool)` | Set label visibility |

## Icon System

| Export | Description |
|--------|-------------|
| `CATEGORY_COLORS` | Category to color mapping |
| `get_cached_node_icon(name)` | Get cached QIcon |
| `get_cached_node_icon_path(name)` | Get cached icon path |
| `create_node_icon_pixmap(name, color)` | Create pixmap with color |
| `get_node_color(category)` | Get color for category |
| `register_custom_icon(name, path)` | Register custom icon |

## Port Shapes

| Export | Description |
|--------|-------------|
| `draw_port_shape(painter, rect, type)` | Draw port shape |
| `get_shape_for_type(type_name)` | Get shape enum for type |
| `get_shape_description(shape)` | Get shape description |

## Managers

| Export | Description |
|--------|-------------|
| `SelectionManager` | Node selection handling |
| `CompositeNodeCreator` | Create composite nodes (ForLoop, TryCatch) |
| `NodeCreationHelper` | Node creation assistance (SetVariable) |

## Event Filters

| Export | Description |
|--------|-------------|
| `TooltipBlocker` | Block unwanted tooltips |
| `OutputPortMMBFilter` | Middle-mouse button on output ports |
| `ConnectionDropFilter` | Handle connection drop events |

## GPU Optimization

### LOD Manager

| Export | Description |
|--------|-------------|
| `LODLevel` | Level-of-Detail enum (HIGH, MEDIUM, LOW, ICON) |
| `ViewportLODManager` | Centralized LOD management |
| `get_lod_manager()` | Get singleton LOD manager |

### Background Cache

| Export | Description |
|--------|-------------|
| `NodeBackgroundCache` | Pre-rendered node backgrounds |
| `get_background_cache()` | Get singleton background cache |

### Icon Atlas

| Export | Description |
|--------|-------------|
| `IconTextureAtlas` | Single texture for all icons |
| `get_icon_atlas()` | Get singleton icon atlas |
| `preload_node_icons()` | Preload all node icons |

## Key Files

| File | Contains |
|------|----------|
| `custom_node_item.py` | CasareNodeItem, AnimationCoordinator |
| `custom_graph.py` | CasareNodeGraph drag/drop + telemetry overrides |
| `custom_pipe.py` | CasarePipe connection rendering |
| `node_icons.py` | Icon system with caching |
| `port_shapes.py` | Port shape rendering |
| `selection_manager.py` | Selection handling |
| `lod_manager.py` | Level-of-detail management |
| `background_cache.py` | Pre-rendered backgrounds |
| `icon_atlas.py` | Texture atlas for icons |

## Usage Patterns

```python
# Custom node rendering
from casare_rpa.presentation.canvas.graph import (
    CasareNodeItem, CasarePipe, SelectionManager
)

# Icon management
from casare_rpa.presentation.canvas.graph import (
    get_cached_node_icon, get_node_color, CATEGORY_COLORS
)

icon = get_cached_node_icon("browser")
color = get_node_color("browser")

# GPU optimization
from casare_rpa.presentation.canvas.graph import (
    get_lod_manager, get_background_cache, preload_node_icons
)

lod = get_lod_manager()
lod.set_zoom_level(0.5)
current_lod = lod.get_current_lod()

# Preload for performance
preload_node_icons()
```

## Related Modules

| Module | Relation |
|--------|----------|
| `canvas.ui` | UI panels and widgets |
| `canvas.controllers.viewport_controller` | Viewport management |
| `canvas.visual_nodes` | Visual node implementations |

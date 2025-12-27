# Canvas Graph Index

```xml<graph_index>
  <!-- Quick reference for graph rendering components. Use for fast discovery. -->

  <overview>
    <p>Custom NodeGraphQt rendering elements for visual workflow editor</p>
    <files>27 files</files>
    <exports>39 total</exports>
  </overview>

  <custom_rendering>
    <e>CasareNodeItem</e>       <s>custom_node_item.py</s> <d>Custom node rendering with animations</d>
    <e>AnimationCoordinator</e> <s>custom_node_item.py</s> <d>Node animation state coordinator</d>
    <e>CasarePipe</e>           <s>custom_pipe.py</s>     <d>Custom connection with labels/flow animation</d>
    <e>RerouteNodeItem</e>      <s>reroute_node_item.py</s> <d>Reroute/dot node rendering</d>
    <e>SubflowNodeItem</e>      <s>subflow_node_item.py</s> <d>Subflow node rendering</d>
  </custom_rendering>

  <connection_labels>
    <e>get_show_connection_labels()</e>  <d>Get label visibility state</d>
    <e>set_show_connection_labels(bool)</e> <d>Set label visibility</d>
  </connection_labels>

  <icon_system>
    <e>CATEGORY_COLORS</e>              <d>Category to color mapping</d>
    <e>get_cached_node_icon(name)</e>   <d>Get cached QIcon</d>
    <e>get_cached_node_icon_path(name)</d> <d>Get cached icon path</d>
    <e>create_node_icon_pixmap(name, color)</e> <d>Create pixmap with color</d>
    <e>get_node_color(category)</e>     <d>Get color for category</d>
    <e>register_custom_icon(name, path)</e> <d>Register custom icon</d>
  </icon_system>

  <port_shapes>
    <e>draw_port_shape(painter, rect, type)</e> <d>Draw port shape</d>
    <e>get_shape_for_type(type_name)</e>        <d>Get shape enum for type</d>
    <e>get_shape_description(shape)</e>         <d>Get shape description</d>
  </port_shapes>

  <managers>
    <e>SelectionManager</e>       <d>Node selection handling</d>
    <e>CompositeNodeCreator</e>   <d>Create composite nodes (ForLoop, TryCatch)</d>
    <e>NodeCreationHelper</e>     <d>Node creation assistance (SetVariable)</d>
  </managers>

  <event_filters>
    <e>TooltipBlocker</e>         <d>Block unwanted tooltips</d>
    <e>OutputPortMMBFilter</e>    <d>Middle-mouse button on output ports</d>
    <e>ConnectionDropFilter</e>   <d>Handle connection drop events</d>
  </event_filters>

  <gpu_optimization>
    <lod>
      <e>LODLevel</e>              <d>HIGH, MEDIUM, LOW, ICON enum</d>
      <e>ViewportLODManager</e>    <d>Centralized LOD management</d>
      <e>get_lod_manager()</e>     <d>Get singleton LOD manager</d>
    </lod>
    <background>
      <e>NodeBackgroundCache</e>   <d>Pre-rendered node backgrounds</d>
      <e>get_background_cache()</e> <d>Get singleton background cache</d>
    </background>
    <atlas>
      <e>IconTextureAtlas</e>      <d>Single texture for all icons</d>
      <e>get_icon_atlas()</e>       <d>Get singleton icon atlas</d>
      <e>preload_node_icons()</e>  <d>Preload all node icons</d>
    </atlas>
  </gpu_optimization>

  <usage>
    <code>
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
preload_node_icons()
    </code>
  </usage>

  <related>
    <r>canvas.ui</r>                     <d>UI panels and widgets</d>
    <r>canvas.controllers.viewport_controller</r> <d>Viewport management</d>
    <r>canvas.visual_nodes</r>           <d>Visual node implementations</d>
  </related>
</graph_index>
```

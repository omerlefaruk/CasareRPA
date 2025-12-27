# Canvas Presentation Index

```xml
<canvas_index>
  <!-- Quick reference for UI components. Use for fast discovery. -->

  <dirs>
    <d name="graph/">     <p>Node graph widget, pipes, selection</p>     <x>graph/_index.md</x></d>
    <d name="managers/">  <p>Panel and popup management</p>             <i>PopupManager, PanelManager</i></d>
    <d name="ui/">        <p>Theme, panels, dialogs, widgets</p>        <x>ui/_index.md</x></d>
    <d name="controllers/"> <p>UI logic (MVC pattern)</p>               <x>controllers/_index.md</x></d>
    <d name="visual_nodes/"> <p>Visual wrappers (~405 nodes)</p>        <x>visual_nodes/_index.md</x></d>
    <d name="selectors/"> <p>Element picker, UI explorer</p>            <x>selectors/_index.md</x></d>
    <d name="events/">    <p>EventBus, Qt signal bridge</p>             <x>events/_index.md</x></d>
    <d name="debugger/">  <p>Debug controller, breakpoints</p>          <i>-</i></d>
    <d name="execution/"> <p>Execution panel runtime</p>                <i>-</i></d>
  </dirs>

  <key_files>
    <f>main_window.py</f>        <d>Main application window</d>        <l>~800</l>
    <f>app.py</f>                <d>Application initialization</d>      <l>~300</l>
    <f>managers/popup_manager.py</d> <p>Centralized popup lifecycle</p> <l>~200</l>
    <f>ui/theme.py</f>           <d>THEME.* constants + 2-level cache</d> <l>~400</l>
    <f>theme_system/stylesheet_cache.py</d> <p>Disk cache for QSS</p>  <l>~150</l>
    <f>graph/node_graph_widget.py</d> <d>Main canvas widget</d>        <l>~2400</l>
    <f>visual_nodes/__init__.py</d>  <d>_VISUAL_NODE_REGISTRY</d>      <l>~610</l>
  </key_files>

  <theme_system>
    <desc>Two-level caching for generated stylesheets</desc>
    <levels>
      <level name="memory">Module-level _CACHED_STYLESHEET in theme.py</level>
      <level name="disk">stylesheet_cache.py with version-based invalidation</level>
    </levels>
    <entry_point>from casare_rpa.presentation.canvas.theme import get_canvas_stylesheet</entry_point>
  </theme_system>

  <entry_points>
    <code>
# Theme colors (MANDATORY for all UI)
from casare_rpa.presentation.canvas.ui.theme import THEME
color = THEME.ACCENT_PRIMARY

# Event bus
from casare_rpa.presentation.canvas.events import EventBus
EventBus.emit("node_selected", node_id=id)

# Base classes
from casare_rpa.presentation.canvas.ui import BaseWidget, BaseDockWidget, BaseDialog

# Controller pattern
from casare_rpa.presentation.canvas.controllers import BaseController
    </code>
  </entry_points>

  <popup_manager>
    <desc>Centralized click-outside-to-close handling for all popup windows</desc>
    <usage>
PopupManager.register(self)     # In showEvent
PopupManager.unregister(self)   # In closeEvent
PopupManager.register(self, pinned=True)  # For pinned popups
    </usage>
    <features>
      <f>Single app-level event filter (efficient)</f>
      <f>WeakSet for automatic cleanup (no memory leaks)</f>
      <f>Pin state support</f>
      <f>close_popup(), close_all_popups() helpers</f>
    </features>
    <ref>.claude/rules/ui/popup-rules.md</ref>
  </popup_manager>

  <visual_nodes total="405">
    <cat name="basic/">     <c>3</c>  <e>VisualStartNode, VisualEndNode</e></cat>
    <cat name="browser/">   <c>23</c> <e>VisualNavigateNode, VisualClickNode</e></cat>
    <cat name="desktop_automation/"> <c>36</c> <e>VisualClickDesktopNode</e></cat>
    <cat name="system/">    <c>67</c> <e>VisualMessageBoxNode, VisualTooltipNode</e></cat>
    <cat name="data_operations/"> <c>32</c> <e>VisualSetVariableNode</e></cat>
  </visual_nodes>

  <registration>
    <s>1</s> <d>visual_nodes/{category}/nodes.py - Define class</d>
    <s>2</s> <d>visual_nodes/__init__.py - Add to _VISUAL_NODE_REGISTRY</d>
  </registration>

  <related>
    <r>../../nodes/_index.md</r>      <d>Domain node implementations</d>
    <r>../../domain/_index.md</r>     <d>Base classes, decorators</d>
    <r>../../infrastructure/_index.md</d> <d>External adapters</d>
  </related>
</canvas_index>
```

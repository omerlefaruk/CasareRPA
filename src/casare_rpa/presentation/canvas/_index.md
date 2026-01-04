# Canvas Presentation Index

```xml
<canvas_index>
  <!-- Quick reference for UI components. Use for fast discovery. -->

  <dirs>
    <d name="graph/">     <p>Node graph widget, pipes, selection</p>     <x>graph/_index.md</x></d>
    <d name="managers/">  <p>Popup management</p>                     <i>PopupManager</i></d>
    <d name="ui/">        <p>Theme, panels, dialogs, widgets</p>        <x>ui/_index.md</x></d>
    <d name="ui/widgets/popups/"> <p>V2 popup components</p>      <i>PopupWindowBase, DraggableHeader</i></d>
    <d name="ui/dialogs_v2/"> <p>V2 dialog framework (Epic 7.1)</p> <i>BaseDialogV2, MessageBoxV2, ConfirmDialogV2</i></d>
    <d name="ui/widgets/primitives/"> <p>UI Primitives v2 (Epic 5.2)</p>  <x>ui/widgets/primitives/_index.md</x></d>
    <d name="ui/chrome/">  <p>V2 Chrome components (Epic 4.2)</p>    <i>ToolbarV2, StatusBarV2</i></d>
    <d name="controllers/"> <p>UI logic (MVC pattern)</p>               <x>controllers/_index.md</x></d>
    <d name="visual_nodes/"> <p>Visual wrappers (~405 nodes)</p>        <x>visual_nodes/_index.md</x></d>
    <d name="selectors/"> <p>Element picker, UI explorer</p>            <x>selectors/_index.md</x></d>
    <d name="events/">    <p>EventBus, Qt signal bridge</p>             <x>events/_index.md</x></d>
    <d name="debugger/">  <p>Debug controller, breakpoints</p>          <i>-</i></d>
    <d name="execution/"> <p>Execution panel runtime</p>                <i>-</i></d>
    <d name="coordinators/"> <p>Signal coordination</p>               <i>SignalCoordinator</i></d>
  </dirs>

  <key_files>
    <f>new_main_window.py</f>    <d>Main window (V2 dock-only workspace)</d> <l>~1400</l>
    <f>app.py</f>                <d>Application initialization</d>      <l>~300</l>
    <f>managers/popup_manager.py</d> <p>Centralized popup lifecycle</p> <l>~200</l>
    <f>theme/tokens_v2.py</f> <d>Theme v2 colors + tokens</d> <l>~400</l>
    <f>graph/node_graph_widget.py</d> <d>Main canvas widget</d>        <l>~2400</l>
    <f>visual_nodes/__init__.py</d>  <d>_VISUAL_NODE_REGISTRY</d>      <l>~610</l>
  </key_files>

  <theme>
    <desc>Theme v2 tokens + stylesheet generator + font loader</desc>
    <levels>
      <level name="qss">styles_v2.py (get_canvas_stylesheet_v2)</level>
      <level name="fonts">font_loader.py for Geist Sans/Mono registration</level>
    </levels>
    <entry_point>from casare_rpa.presentation.canvas.theme import get_canvas_stylesheet_v2</entry_point>
    <font_loader>
      <desc>Register bundled fonts at app startup (Epic 1.2)</desc>
      <usage>ensure_font_registered()  # Call before QApplication creates widgets</usage>
      <families>
        <f>GEIST_SANS_FAMILY = "Geist Sans"</f>
        <f>GEIST_MONO_FAMILY = "Geist Mono"</f>
      </families>
      <fallback>Segoe UI (sans), Cascadia Code (mono)</fallback>
    </font_loader>
  </theme>

  <entry_points>
    <code>
# Theme colors (MANDATORY for all UI)
from casare_rpa.presentation.canvas.theme import THEME, TOKENS
color = THEME.primary

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

  <ui_primitives_v2 epic="5.2">
    <desc>Component Library v2 - 13 modules, ~65 components, all using THEME_V2/TOKENS_V2</desc>
    <modules>
      <m>base_primitive.py</m>   <e>BasePrimitive, SizeVariant, FontVariant, MarginPreset</e></m>
      <m>buttons.py</m>          <e>PushButton, ToolButton, ButtonGroup</e></m>
      <m>inputs.py</m>           <e>TextInput, SearchInput, SpinBox, DoubleSpinBox</e></m>
      <m>selects.py</m>          <e>Select, ComboBox, ItemList</e></m>
      <m>selection.py</m>        <e>CheckBox, Switch, RadioButton, RadioGroup</e></m>
      <m>range.py</m>            <e>Slider, ProgressBar, Dial</e></m>
      <m>tabs.py</m>             <e>TabWidget, TabBar, Tab dataclass</e></m>
      <m>lists.py</m>            <e>ListItem, TreeItem, TableHeader, style helpers</e></m>
      <m>structural.py</m>       <e>SectionHeader, Divider, EmptyState, Card</e></m>
      <m>feedback.py</m>         <e>Badge, InlineAlert, Breadcrumb, Avatar, set_tooltip</e></m>
      <m>loading.py</m>          <e>Skeleton, Spinner</e></m>
      <m>forms.py</m>            <e>FormField, FormRow, FormContainer, Fieldset, ReadOnlyField, validators</e></m>
      <m>pickers.py</m>          <e>FilePicker, FolderPicker, PathType, FileFilter</e></m>
    </modules>
    <gallery>
      <usage>from casare_rpa.presentation.canvas.theme import show_primitive_gallery_v2</usage>
      <show>show_primitive_gallery_v2()  # Displays all components in tabbed dialog</show>
      <ref>theme/primitive_gallery.py</ref>
    </gallery>
    <imports>
      <code>from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    PushButton, ToolButton, TextInput, CheckBox, Switch, Slider, ...
)</code>
    </imports>
  </ui_primitives_v2>

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

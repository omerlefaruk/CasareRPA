# Canvas Selectors Index

```xml<selectors_index>
  <!-- Quick reference for element selector UI components. Use for fast discovery. -->

  <overview>
    <p>UI components for element selection (browser/desktop)</p>
    <files>44 files across subdirectories</files>
    <exports>30 total</exports>
  </overview>

  <dirs>
    <d name="tabs/">        <n>6</n> <p>Selector mode tabs (Browser, Desktop, OCR, Image)</p></d>
    <d name="state/">       <n>2</n> <p>State management</p></d>
    <d name="widgets/">     <n>8</n> <p>Reusable selector widgets</p></d>
    <d name="ui_explorer/"> <n>16</n> <p>Advanced UI explorer</p></d>
  </dirs>

  <dialogs>
    <e>ElementSelectorDialog</e> <s>element_selector_dialog.py</s> <d>Streamlined element picker (recommended)</d>
    <e>UIExplorerDialog</e>      <s>ui_explorer/</s> <d>Advanced full-featured UI explorer</d>
    <e>UnifiedSelectorDialog</e> <s>unified_selector_dialog.py</s> <d>Legacy unified dialog</d>
    <e>UIExplorerToolbar</e>     <s>ui_explorer/toolbar.py</s> <d>UI explorer toolbar</d>
  </dialogs>

  <state>
    <e>ElementSelectorState</e> <s>state/selector_state.py</s> <d>Centralized selector state</d>
    <e>StateManager</e>         <s>state/selector_state.py</s> <d>Qt signals-based state management</d>
    <e>AttributeRow</e>         <s>state/selector_state.py</s> <d>Attribute row data</d>
    <e>ValidationStatus</e>     <s>state/selector_state.py</s> <d>VALID, INVALID, UNKNOWN</d>
    <e>PickingMode</e>          <s>state/selector_state.py</s> <d>BROWSER, DESKTOP, OCR, IMAGE</d>
  </state>

  <history>
    <e>SelectorHistory</e>       <s>selector_history.py</s> <d>JSON-based history storage</d>
    <e>SelectorHistoryEntry</e>  <s>selector_history.py</s> <d>History entry data</d>
    <e>get_selector_history()</e> <s>selector_history.py</s> <d>Get history singleton</d>
  </history>

  <widgets>
    <e>ToolbarWidget</e>         <s>widgets/toolbar_widget.py</s> <d>Pick/Stop/Mode controls</d>
    <e>ModeButton</e>            <s>widgets/toolbar_widget.py</s> <d>Mode selection button</d>
    <e>ElementPreviewWidget</e>  <s>widgets/element_preview_widget.py</s> <d>HTML preview with properties</d>
    <e>SelectorBuilderWidget</e> <s>widgets/selector_builder_widget.py</s> <d>Attribute rows with scores</d>
    <e>AttributeRowWidget</e>    <s>widgets/selector_builder_widget.py</s> <d>Single attribute row</d>
    <e>AnchorWidget</e>          <s>widgets/anchor_widget.py</s> <d>Anchor configuration</d>
    <e>AdvancedOptionsWidget</e> <s>widgets/advanced_options_widget.py</s> <d>Fuzzy/CV/Image options</d>
    <e>PickerToolbar</e>         <s>widgets/picker_toolbar.py</s> <d>Floating toolbar during picking</d>
  </widgets>

  <data_classes>
    <e>SelectorResult</e>        <s>tabs/base_tab.py</s> <d>Selector result data</d>
    <e>SelectorStrategy</e>      <s>tabs/base_tab.py</s> <d>Selection strategy enum</d>
    <e>AnchorData</e>            <s>tabs/base_tab.py</s> <d>Anchor element data</d>
  </data_classes>

  <ui_explorer>
    <panels>
      <e>VisualTreePanel</e>      <d>Element tree visualization</d>
      <e>PropertyExplorerPanel</e> <d>Property inspection</d>
      <e>SelectorEditorPanel</e>   <d>Selector editing</d>
      <e>SelectorPreviewPanel</e>  <d>Selector preview</d>
      <e>SelectedAttrsPanel</e>    <d>Selected attributes</d>
    </panels>
    <models>
      <e>ElementModel</e>          <d>Element data model</d>
      <e>SelectorModel</e>         <d>Selector data model</d>
      <e>AnchorModel</e>           <d>Anchor data model</d>
    </models>
    <widgets>
      <e>AttributeRow</e>          <d>Attribute row widget</d>
      <e>AnchorPanel</e>           <d>Anchor configuration panel</d>
      <e>XmlHighlighter</e>        <d>XML syntax highlighting</d>
      <e>StatusBarWidget</e>       <d>Status bar</d>
    </widgets>
  </ui_explorer>

  <modes>
    <m>BROWSER</m>  <d>Web element via Playwright</d>
    <m>DESKTOP</m>  <d>Windows UI element via UIA</d>
    <m>OCR</m>      <d>Text recognition</d>
    <m>IMAGE</m>    <d>Image matching</d>
  </modes>

  <usage>
    <code>
# Recommended: ElementSelectorDialog
from casare_rpa.presentation.canvas.selectors import ElementSelectorDialog, SelectorResult
dialog = ElementSelectorDialog(parent=self)
if dialog.exec():
    result: SelectorResult = dialog.get_result()
    selector = result.selector
    strategy = result.strategy

# Advanced: UIExplorerDialog
from casare_rpa.presentation.canvas.selectors import UIExplorerDialog
explorer = UIExplorerDialog(parent=self)
explorer.show()

# State management
from casare_rpa.presentation.canvas.selectors import (
    ElementSelectorState, StateManager, PickingMode
)
state = ElementSelectorState()
state.picking_mode = PickingMode.BROWSER
state.selector = "#my-element"

# History
from casare_rpa.presentation.canvas.selectors import (
    get_selector_history, SelectorHistoryEntry
)
history = get_selector_history()
entries = history.get_recent(10)
history.add(SelectorHistoryEntry(selector="#btn", mode="browser"))
    </code>
  </usage>

  <related>
    <r>canvas.controllers.selector_controller</r> <d>Selector coordination</d>
    <r>nodes.browser/</r>                     <d>Browser automation nodes</d>
    <r>nodes.desktop_nodes/</r>                <d>Desktop automation nodes</d>
    <r>desktop.context</r>                     <d>Desktop automation context</d>
  </related>
</selectors_index>
```

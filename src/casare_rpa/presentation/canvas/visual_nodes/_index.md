# Visual Nodes Index

```xml
<visual_nodes_index>
  <!-- Quick reference for visual node implementations. Use for fast discovery. -->

  <cats>
    <c name="basic/">           <n>3</n>  <e>VisualStartNode, VisualEndNode, VisualCommentNode</e></c>
    <c name="browser/">         <n>23</n> <e>LaunchBrowser, CloseBrowser, GoToURL, ClickElement, TypeText, ExtractText, TableScraper</e></c>
    <c name="control_flow/">    <n>16</n> <e>If, ForLoop, WhileLoop, Switch, Break, Continue, Merge, TryCatchFinally</e></c>
    <c name="data_operations/"> <n>33</n> <e>Concatenate, Regex, Math, List ops, Dict ops, DataCompare</e></c>
    <c name="desktop_automation/"> <n>36</n> <e>LaunchApplication, ActivateWindow, ClickElement, TypeText, SendKeys, OCR</e></c>
    <c name="email/">           <n>8</n>  <e>SendEmail, ReadEmails, GetEmailContent, FilterEmails</e></c>
    <c name="error_handling/">  <n>9</n>  <e>Retry, ThrowError, OnError, ErrorRecovery, Assert</e></c>
    <c name="file_operations/"> <n>42</n> <e>ReadFile, WriteFile, CSV, JSON, XML, PDF, FTP, VisualFileSystemSuperNode</e></c>
    <c name="google/">          <n>62</n> <e>Gmail (21), Sheets (21), Drive (20)</e></c>
    <c name="messaging/">       <n>16</n> <e>Telegram (9), WhatsApp (7)</e></c>
    <c name="office_automation/"> <n>12</n> <e>Excel, Word, Outlook</e></c>
    <c name="rest_api/">        <n>7</n>  <e>HttpRequest, SetHeaders, HttpAuth, DownloadFile</e></c>
    <c name="scripts/">         <n>5</n>  <e>RunPythonScript, RunBatchScript, RunJavaScript, EvalExpression</e></c>
    <c name="subflows/">        <n>1</n>  <e>VisualSubflowNode</e></c>
    <c name="system/">          <n>67</n> <e>Clipboard, Dialogs, Services, Process, FileWatcher, QRCode</e></c>
    <c name="triggers/">        <n>16</n> <e>Webhook, Schedule, FileWatch, Email, Telegram, Drive</e></c>
    <c name="utility/">         <n>27</n> <e>Random, DateTime, Text operations, Reroute</e></c>
    <c name="variable/">        <n>3</n>  <e>SetVariable, GetVariable, IncrementVariable</e></c>
  </cats>

  <super_nodes>
    <desc>Super Nodes use SuperNodeMixin for dynamic port management based on action selection</desc>
    <files>
      <f>mixins/super_node_mixin.py</f> <d>Base mixin for dynamic ports and conditional widget visibility</d>
      <f>file_operations/super_nodes.py</f> <d>Visual implementation for FileSystemSuperNode</d>
    </files>
    <features>
      <f>Dynamic port creation/deletion based on action dropdown</f>
      <f>Conditional widget visibility via display_when/hidden_when</f>
      <f>Port schema defined in domain layer (DynamicPortSchema)</f>
    </features>
    <ref>../../../../../.brain/docs/super-node-pattern.md</ref>
  </super_nodes>

  <key_files>
    <f>__init__.py</f>           <d>_VISUAL_NODE_REGISTRY - lazy loading, get_all_visual_node_classes()</d> <l>~610</l>
    <f>base_visual_node.py</f>   <d>VisualNode base class - bridges CasareRPA BaseNode with NodeGraphQt</d> <l>~1222</l>
  </key_files>

  <entry_points>
    <code>
# Import specific visual nodes (lazy-loaded)
from casare_rpa.presentation.canvas.visual_nodes import (
    VisualStartNode, VisualEndNode,
    VisualClickElementNode, VisualTypeTextNode,
)

# Get all visual node classes (triggers full load)
from casare_rpa.presentation.canvas.visual_nodes import get_all_visual_node_classes
all_nodes = get_all_visual_node_classes()

# Preload specific nodes for performance
from casare_rpa.presentation.canvas.visual_nodes import preload_visual_nodes
preload_visual_nodes(["VisualStartNode", "VisualEndNode"])

# Base class for creating new visual nodes
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode
    </code>
  </entry_points>

  <architecture>
    <base>VisualNode (base_visual_node.py)</base>
    <extends>NodeGraphQt.BaseNode</extends>
    <links_to>CasareRPA BaseNode (_casare_node)</links_to>
    <methods>
      <m>setup_ports() - Define exec/data ports</m>
      <m>setup_widgets() - Custom UI widgets</m>
      <m>_auto_create_widgets_from_schema() - Generate from @properties</m>
      <m>set_collapsed() / toggle_collapse() - Show/hide non-essential widgets</m>
      <m>update_status() - Visual execution feedback</m>
    </methods>
  </architecture>

  <registration>
    <s>1</s> <d>Create node class in appropriate category directory</d>
    <s>2</s> <d>Add to _VISUAL_NODE_REGISTRY in __init__.py</d>
    <s>3</s> <d>Map to CasareRPA node in graph/node_registry.py</d>
  </registration>

  <related>
    <r>../../../../../nodes/_index.md</r> <d>CasareRPA node implementations (execution logic)</d>
    <r>../../_index.md</r>               <d>Canvas presentation layer</d>
    <r>../../../../../domain/_index.md</r> <d>Domain layer entities and types</d>
  </related>
</visual_nodes_index>
```

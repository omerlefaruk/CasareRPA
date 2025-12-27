# Desktop Nodes Package Index

```xml<desktop_nodes_index>
  <!-- Windows desktop automation nodes using UIAutomation. -->

  <files>
    <f>__init__.py</f>                <e>All desktop nodes</e>
    <f>desktop_base.py</f>            <e>DesktopBaseNode</e>
    <f>element_nodes.py</f>           <e>FindElementNode</e>
    <f>interaction_nodes.py</f>       <e>ClickElementNode, TypeTextNode</e>
    <f>window_nodes.py</f>            <e>FindWindowNode, ActivateWindowNode</e>
    <f>mouse_keyboard_nodes.py</f>    <e>MouseClickNode, KeyboardTypeNode</e>
    <f>application_nodes.py</f>       <e>LaunchAppNode, CloseAppNode</e>
    <f>office_nodes.py</f>            <e>ExcelNode, WordNode</e>
    <f>screenshot_ocr_nodes.py</f>     <e>ScreenshotNode, OCRNode</e>
    <f>wait_verification_nodes.py</f> <e>WaitForWindowNode</e>
    <f>properties.py</f>              <e>Desktop property constants</e>
    <f>yolo_find_node.py</f>          <e>YoloFindNode</e>
  </files>

  <entry_points>
    <code>
from casare_rpa.nodes.desktop_nodes import (
    # Window operations
    FindWindowNode, ActivateWindowNode,
    # Element operations
    FindElementNode, ClickElementNode,
    TypeTextNode, GetElementTextNode,
)
    </code>
  </entry_points>

  <patterns>
    <p>1. Use UIAutomation library</p>
    <p>2. Support selector patterns</p>
    <p>3. Handle window focus</p>
    <p>4. Include retry logic</p>
  </patterns>
</desktop_nodes_index>
```

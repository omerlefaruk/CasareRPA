# Desktop Nodes Package Index

Windows desktop automation nodes using UIAutomation.

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `__init__.py` | Package exports | All desktop nodes |
| `desktop_base.py` | Base class | DesktopBaseNode |
| `element_nodes.py` | Element finding | FindElementNode |
| `interaction_nodes.py` | Click, type | ClickElementNode, TypeTextNode |
| `window_nodes.py` | Window management | FindWindowNode, ActivateWindowNode |
| `mouse_keyboard_nodes.py` | Input simulation | MouseClickNode, KeyboardTypeNode |
| `application_nodes.py` | App lifecycle | LaunchAppNode, CloseAppNode |
| `office_nodes.py` | Office automation | ExcelNode, WordNode |
| `screenshot_ocr_nodes.py` | Screen capture | ScreenshotNode, OCRNode |
| `wait_verification_nodes.py` | Wait/verify | WaitForWindowNode |
| `properties.py` | Shared properties | Desktop property constants |
| `yolo_find_node.py` | AI element finding | YoloFindNode |

## Entry Points

```python
from casare_rpa.nodes.desktop_nodes import (
    # Window operations
    FindWindowNode,
    ActivateWindowNode,
    # Element operations
    FindElementNode,
    ClickElementNode,
    TypeTextNode,
    GetElementTextNode,
)
```

## Key Patterns

All desktop nodes:
1. Use UIAutomation library
2. Support selector patterns
3. Handle window focus
4. Include retry logic

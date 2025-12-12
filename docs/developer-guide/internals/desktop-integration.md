# Desktop Integration Internals

This document describes CasareRPA's integration with Windows desktop automation via UIAutomation.

## Overview

CasareRPA uses the `uiautomation` library (wrapper around Windows UIAutomation API) and `pywinauto` for desktop automation. The integration provides:

- Window management
- Element finding and interaction
- Mouse and keyboard simulation
- Screen capture and OCR
- Form control interaction

## DesktopContext

**Location:** `src/casare_rpa/desktop/context.py`

Main entry point for desktop automation, managing windows and providing high-level API.

### Architecture

```
DesktopContext
    |
    +-> WindowManager        - Window operations
    +-> MouseController      - Mouse simulation
    +-> KeyboardController   - Keyboard input
    +-> FormInteractor       - Form control interaction
    +-> ScreenCapture        - Screenshots and OCR
    +-> WaitManager          - Element waiting
```

### Usage

```python
from casare_rpa.desktop import DesktopContext

# Sync API (backward compatible)
with DesktopContext() as ctx:
    window = ctx.find_window("Notepad")
    ctx.send_keys("Hello World!")

# Async API (preferred in workflows)
async with DesktopContext() as ctx:
    window = await ctx.async_find_window("Notepad")
    await ctx.async_send_keys("Hello World!")
```

### Sync/Async Bridge

The context provides both sync and async methods:

```python
def _run_async(coro):
    """Run async coroutine synchronously."""
    try:
        loop = asyncio.get_running_loop()
        # Inside async context - use thread pool
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running loop - use asyncio.run()
        return asyncio.run(coro)

class DesktopContext:
    # Sync version
    def find_window(self, title: str, ...) -> Optional[DesktopElement]:
        return _run_async(self._window_manager.find_window(title, ...))

    # Async version
    async def async_find_window(self, title: str, ...) -> Optional[DesktopElement]:
        return await self._window_manager.find_window(title, ...)
```

---

## Window Management

### WindowManager

**Location:** `src/casare_rpa/desktop/managers/window_manager.py`

```python
class WindowManager:
    async def find_window(
        self,
        title: str,
        exact: bool = False,
        timeout: float = 5.0
    ) -> Optional[DesktopElement]:
        """Find window by title."""

    async def launch_application(
        self,
        path: str,
        args: str = "",
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None,
        keep_open: bool = True
    ) -> DesktopElement:
        """Launch application and return main window."""

    async def close_application(
        self,
        window_or_pid: Union[DesktopElement, int, str],
        force: bool = False,
        timeout: float = 5.0
    ) -> bool:
        """Close application gracefully or forcefully."""
```

### Window Operations

```python
# Find window
window = await ctx.async_find_window("Notepad", exact=False)

# Get all windows
windows = ctx.get_all_windows(include_invisible=False)

# Launch application
app_window = await ctx.async_launch_application(
    path="notepad.exe",
    args="document.txt",
    working_dir="C:\\Documents",
    timeout=10.0
)

# Window manipulation
ctx.resize_window(window, width=800, height=600)
ctx.move_window(window, x=100, y=100)
ctx.maximize_window(window)
ctx.minimize_window(window)
ctx.restore_window(window)

# Get properties
props = ctx.get_window_properties(window)
# {
#     "title": "Untitled - Notepad",
#     "class_name": "Notepad",
#     "rect": {"left": 100, "top": 100, "right": 900, "bottom": 700},
#     "is_visible": True,
#     "is_enabled": True,
#     "process_id": 1234,
# }
```

---

## Element Finding

### DesktopElement

**Location:** `src/casare_rpa/desktop/element.py`

Wrapper around UIAutomation Control with chainable methods:

```python
class DesktopElement:
    def __init__(self, control: auto.Control):
        self._control = control

    def find_child(
        self,
        selector: Dict[str, Any],
        timeout: float = 5.0
    ) -> Optional["DesktopElement"]:
        """Find child element matching selector."""

    def find_children(
        self,
        selector: Dict[str, Any]
    ) -> List["DesktopElement"]:
        """Find all matching children."""

    def click(self) -> None:
        """Click the element."""

    def type_text(self, text: str, clear: bool = False) -> None:
        """Type text into the element."""

    @property
    def text(self) -> str:
        """Get element text content."""

    @property
    def bounds(self) -> Dict[str, int]:
        """Get element bounding rectangle."""
```

### Selector Syntax

**Location:** `src/casare_rpa/desktop/selector.py`

Desktop selectors use a dictionary format:

```python
# By control type
selector = {"control_type": "Button"}

# By name/text
selector = {"name": "Submit"}

# By automation ID
selector = {"automation_id": "btnSubmit"}

# By class name
selector = {"class_name": "Button"}

# Combined (AND logic)
selector = {
    "control_type": "Edit",
    "name": "Username"
}

# With index (when multiple matches)
selector = {
    "control_type": "ListItem",
    "index": 0
}

# With regex
selector = {
    "name_regex": r"Item \d+"
}
```

### Element Finding Methods

```python
# Find from context
element = ctx.find_element(
    selector={"automation_id": "txtUsername"},
    timeout=5.0,
    parent=window._control  # Optional parent
)

# Find from element (chainable)
window = await ctx.async_find_window("My App")
button = window.find_child({"name": "Submit"})

# Find multiple
items = window.find_children({"control_type": "ListItem"})
```

---

## Mouse and Keyboard Simulation

### MouseController

**Location:** `src/casare_rpa/desktop/managers/mouse_controller.py`

```python
class MouseController:
    async def move_mouse(
        self,
        x: int,
        y: int,
        duration: float = 0.0
    ) -> bool:
        """Move cursor to position with optional animation."""

    async def click(
        self,
        x: int = None,
        y: int = None,
        button: str = "left",
        click_type: str = "single"
    ) -> bool:
        """Click at position or current cursor location."""

    async def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        duration: float = 0.5
    ) -> bool:
        """Drag from start to end position."""

    async def get_position(self) -> tuple:
        """Get current cursor position."""
```

### Usage

```python
# Move mouse
ctx.move_mouse(x=500, y=300, duration=0.5)

# Click variations
ctx.click_mouse(x=500, y=300, button="left", click_type="single")
ctx.click_mouse(button="right", click_type="single")  # At current position
ctx.click_mouse(click_type="double")

# Drag
ctx.drag_mouse(
    start_x=100, start_y=100,
    end_x=500, end_y=500,
    button="left",
    duration=0.5
)

# Get position
x, y = ctx.get_mouse_position()
```

### KeyboardController

**Location:** `src/casare_rpa/desktop/managers/keyboard_controller.py`

```python
class KeyboardController:
    async def send_keys(
        self,
        keys: str,
        interval: float = 0.0
    ) -> bool:
        """Send keyboard input."""

    async def send_hotkey(self, *keys: str) -> bool:
        """Send key combination."""
```

### Key Syntax

```python
# Plain text
ctx.send_keys("Hello World")

# Special keys (using braces)
ctx.send_keys("{ENTER}")
ctx.send_keys("{TAB}")
ctx.send_keys("{BACKSPACE}")
ctx.send_keys("{DELETE}")
ctx.send_keys("{ESCAPE}")

# Modifiers
ctx.send_keys("{CTRL}a")  # Ctrl+A
ctx.send_keys("{ALT}{F4}")  # Alt+F4
ctx.send_keys("{SHIFT}hello")  # HELLO

# Hotkey combinations
ctx.send_hotkey("ctrl", "c")  # Ctrl+C
ctx.send_hotkey("ctrl", "shift", "s")  # Ctrl+Shift+S
ctx.send_hotkey("alt", "tab")  # Alt+Tab
```

---

## Screen Capture and OCR

### ScreenCapture

**Location:** `src/casare_rpa/desktop/managers/screen_capture.py`

```python
class ScreenCapture:
    async def capture_screenshot(
        self,
        file_path: str = None,
        region: Dict[str, int] = None,
        format: str = "PNG"
    ) -> Optional[Any]:
        """Capture screen or region."""

    async def capture_element_image(
        self,
        element: DesktopElement,
        file_path: str = None,
        padding: int = 0,
        format: str = "PNG"
    ) -> Optional[Any]:
        """Capture specific element."""

    async def ocr_extract_text(
        self,
        image: Any = None,
        image_path: str = None,
        region: Dict[str, int] = None,
        language: str = "eng",
        config: str = "",
        engine: str = "auto"
    ) -> Optional[str]:
        """Extract text using OCR."""

    async def compare_images(
        self,
        image1: Any = None,
        image2: Any = None,
        method: str = "ssim",
        threshold: float = 0.9
    ) -> Dict[str, Any]:
        """Compare two images for similarity."""
```

### Usage

```python
# Full screen
screenshot = ctx.capture_screenshot(file_path="screen.png")

# Region capture
screenshot = ctx.capture_screenshot(
    region={"x": 0, "y": 0, "width": 800, "height": 600}
)

# Element capture
element_img = ctx.capture_element_image(button, padding=5)

# OCR
text = ctx.ocr_extract_text(
    image=screenshot,
    language="eng",
    engine="auto"  # Uses Tesseract or Windows OCR
)

# Image comparison
result = ctx.compare_images(
    image1=baseline_img,
    image2=current_img,
    method="ssim",
    threshold=0.9
)
# {"match": True, "score": 0.95, "method": "ssim"}
```

---

## Form Control Interaction

### FormInteractor

**Location:** `src/casare_rpa/desktop/managers/form_interactor.py`

Specialized handling for form controls:

```python
class FormInteractor:
    async def select_from_dropdown(
        self,
        element: DesktopElement,
        value: str,
        by_text: bool = True
    ) -> bool:
        """Select dropdown item by text or value."""

    async def check_checkbox(
        self,
        element: DesktopElement,
        check: bool = True
    ) -> bool:
        """Check or uncheck checkbox."""

    async def select_radio_button(
        self,
        element: DesktopElement
    ) -> bool:
        """Select radio button."""

    async def select_tab(
        self,
        tab_control: DesktopElement,
        tab_name: str = None,
        tab_index: int = None
    ) -> bool:
        """Select tab by name or index."""

    async def expand_tree_item(
        self,
        element: DesktopElement,
        expand: bool = True
    ) -> bool:
        """Expand or collapse tree item."""

    async def scroll_element(
        self,
        element: DesktopElement,
        direction: str = "down",
        amount: Union[float, str] = 0.5
    ) -> bool:
        """Scroll scrollable element."""
```

### Usage

```python
# Dropdown selection
dropdown = window.find_child({"automation_id": "cmbCountry"})
ctx.select_from_dropdown(dropdown, "United States", by_text=True)

# Checkbox
checkbox = window.find_child({"name": "Accept Terms"})
ctx.check_checkbox(checkbox, check=True)

# Radio button
radio = window.find_child({"name": "Option A"})
ctx.select_radio_button(radio)

# Tab selection
tabs = window.find_child({"control_type": "Tab"})
ctx.select_tab(tabs, tab_name="Settings")
# Or by index
ctx.select_tab(tabs, tab_index=2)

# Tree expand/collapse
tree_item = window.find_child({"name": "Documents"})
ctx.expand_tree_item(tree_item, expand=True)

# Scrolling
scroll_view = window.find_child({"control_type": "ScrollBar"})
ctx.scroll_element(scroll_view, direction="down", amount=0.5)
```

---

## Wait Operations

### WaitManager

**Location:** `src/casare_rpa/desktop/managers/wait_manager.py`

```python
class WaitManager:
    async def wait_for_element(
        self,
        selector: Dict[str, Any],
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5,
        parent: auto.Control = None
    ) -> Optional[DesktopElement]:
        """Wait for element to reach state."""

    async def wait_for_window(
        self,
        title: str = None,
        title_regex: str = None,
        class_name: str = None,
        timeout: float = 10.0,
        state: str = "visible",
        poll_interval: float = 0.5
    ) -> Optional[auto.Control]:
        """Wait for window to appear."""

    async def element_exists(
        self,
        selector: Dict[str, Any],
        timeout: float = 0.0,
        parent: auto.Control = None
    ) -> bool:
        """Check if element exists."""

    async def verify_element_property(
        self,
        element: DesktopElement,
        property_name: str,
        expected_value: Any,
        comparison: str = "equals"
    ) -> bool:
        """Verify element property value."""
```

### State Options

| State | Description |
|-------|-------------|
| `visible` | Element is visible |
| `enabled` | Element is enabled |
| `exists` | Element exists in tree |
| `not_exists` | Element does not exist |
| `focused` | Element has focus |

### Usage

```python
# Wait for element
button = await ctx.async_wait_for_element(
    selector={"name": "Submit"},
    timeout=10.0,
    state="enabled"
)

# Wait for window
dialog = await ctx.async_wait_for_window(
    title="Save As",
    timeout=5.0,
    state="visible"
)

# Check existence
exists = ctx.element_exists(
    selector={"name": "Error Message"},
    timeout=2.0
)

# Verify property
is_correct = ctx.verify_element_property(
    element=status_label,
    property_name="text",
    expected_value="Complete",
    comparison="equals"  # or "contains", "startswith", "regex"
)
```

---

## Desktop Node Base Class

**Location:** `src/casare_rpa/nodes/desktop_nodes/desktop_base.py`

All desktop nodes inherit from DesktopNodeBase:

```python
class DesktopNodeBase(BaseNode):
    """Base class for desktop automation nodes."""

    DEFAULT_RETRY_COUNT: int = 0
    DEFAULT_RETRY_INTERVAL: float = 1.0
    DEFAULT_TIMEOUT: float = 5.0

    def get_desktop_context(self, context: Any) -> DesktopContext:
        """Get or create DesktopContext."""
        if context.desktop_context is None:
            context.desktop_context = DesktopContext()
        return context.desktop_context

    async def execute_with_retry(
        self,
        operation: Any,
        context: Any,
        retry_count: Optional[int] = None,
        retry_interval: Optional[float] = None,
        operation_name: str = "operation"
    ) -> Dict[str, Any]:
        """Execute with retry logic."""

    def success_result(self, **data) -> Dict[str, Any]:
        """Create success result."""
        return {"success": True, "next_nodes": ["exec_out"], **data}

    def error_result(self, error: str, **data) -> Dict[str, Any]:
        """Create error result."""
        return {"success": False, "error": error, **data}
```

### Element Interaction Mixin

```python
class ElementInteractionMixin:
    """Mixin for element-based nodes."""

    async def find_element_from_inputs(
        self,
        context: Any,
        desktop_ctx: DesktopContext,
        timeout: Optional[float] = None
    ) -> Any:
        """Find element from inputs (element port or window+selector)."""
        # Try direct element first
        element = self.get_input_value("element")
        if element:
            return element

        # Fall back to window + selector
        window = self.get_input_value("window")
        selector = self.get_parameter("selector", context)

        if not window or not selector:
            raise ValueError("Need 'element' or 'window' + 'selector'")

        return window.find_child(selector, timeout=timeout)
```

---

## Error Handling

### Common Desktop Errors

| Error | Error Code | Cause |
|-------|------------|-------|
| Window not found | `WINDOW_NOT_FOUND` | No matching window |
| App launch failed | `APPLICATION_LAUNCH_FAILED` | Could not start app |
| Element not found | `DESKTOP_ELEMENT_NOT_FOUND` | Selector didn't match |
| Element stale | `DESKTOP_ELEMENT_STALE` | Element was removed |
| Action failed | `DESKTOP_ACTION_FAILED` | Click/type operation failed |
| Keyboard failed | `KEYBOARD_INPUT_FAILED` | Key send error |
| Mouse failed | `MOUSE_ACTION_FAILED` | Click/move error |

### Cleanup

```python
# Automatic cleanup via context manager
async with DesktopContext() as ctx:
    # ... operations ...
# Cleanup called automatically

# Manual cleanup
ctx.cleanup()  # Releases COM objects, closes tracked apps
```

---

## Performance Tips

### Selector Optimization

```python
# Prefer automation_id (fastest)
{"automation_id": "btnSubmit"}

# Then name (medium)
{"name": "Submit"}

# Control type with name (slower)
{"control_type": "Button", "name": "Submit"}

# Avoid searching entire tree
parent_window = ctx.find_window("My App")
button = parent_window.find_child({"name": "Submit"})  # Scoped search
```

### Caching Elements

```python
# Cache frequently used elements
window = await ctx.async_find_window("App")
submit_btn = window.find_child({"automation_id": "btnSubmit"})
cancel_btn = window.find_child({"automation_id": "btnCancel"})

# Reuse cached references
await submit_btn.click()
```

---

## Related Documentation

- [Execution Engine](execution-engine.md) - Overall execution architecture
- [Browser Integration](browser-integration.md) - Playwright browser automation
- [Error Codes Reference](../../reference/error-codes.md) - Desktop error codes

# Desktop Automation Nodes

Desktop automation nodes provide Windows desktop application control using UIAutomation (via pywinauto). These nodes work with native Windows applications, Win32 controls, WPF, and UWP apps.

> **Note:** Desktop automation requires Windows OS and the `pywinauto` package.

## Overview

| Category | Nodes | Purpose |
|----------|-------|---------|
| Application | 4 | Launch, close, and manage applications |
| Window | 8 | Window manipulation and properties |
| Element | 5 | Find and interact with UI elements |
| Mouse/Keyboard | 6 | Direct input control |
| Interaction | 6 | Advanced UI control interactions |
| Wait/Verification | 4 | State checking and synchronization |
| Screen/OCR | 4 | Screenshots and text extraction |
| YOLO | 1 | AI-powered element detection |

---

## Application Management

### LaunchApplicationNode

Launch a Windows desktop application and return its main window.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| application_path | FILE_PATH | "" | Full path to executable (required) |
| arguments | STRING | "" | Command line arguments |
| working_directory | STRING | "" | Starting directory |
| timeout | FLOAT | 10.0 | Wait time for window (seconds) |
| window_title_hint | STRING | "" | Expected window title |
| window_state | CHOICE | "normal" | normal/maximized/minimized |
| keep_open | BOOLEAN | True | Keep app open when workflow ends |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | application_path | STRING | Path to executable |
| Input | arguments | STRING | Command line args |
| Output | window | ANY | Window object for automation |
| Output | process_id | INTEGER | Process ID |
| Output | window_title | STRING | Window title |

**Example:**

```python
# Launch Notepad
workflow.add_node(
    "LaunchApplicationNode",
    config={
        "application_path": "C:\\Windows\\System32\\notepad.exe",
        "window_title_hint": "Notepad",
        "window_state": "maximized",
    }
)
```

---

### CloseApplicationNode

Close a Windows desktop application gracefully or forcefully.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| force_close | BOOLEAN | False | Force terminate if graceful close fails |
| timeout | FLOAT | 5.0 | Maximum wait time (seconds) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window | ANY | Window object |
| Input | process_id | INTEGER | Process ID to close |
| Input | window_title | STRING | Window title to match |
| Output | success | BOOLEAN | Close succeeded |

> **Note:** Provide at least one of window, process_id, or window_title.

---

### ActivateWindowNode

Bring a window to the foreground and give it focus.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| match_partial | BOOLEAN | True | Allow partial title matching |
| timeout | FLOAT | 5.0 | Wait time for window |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window | ANY | Window object |
| Input | window_title | STRING | Window title |
| Output | success | BOOLEAN | Activation succeeded |
| Output | window | ANY | Activated window |

---

### GetWindowListNode

Get a list of all open Windows desktop windows.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| include_invisible | BOOLEAN | False | Include hidden windows |
| filter_title | STRING | "" | Filter by title substring |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | window_list | LIST | List of window info dicts |
| Output | window_count | INTEGER | Number of windows |

---

## Window Management

### ResizeWindowNode

Resize a window to specified dimensions.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| width | INTEGER | 800 | Target width (pixels) |
| height | INTEGER | 600 | Target height (pixels) |
| bring_to_front | BOOLEAN | False | Activate before resize |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window | ANY | Window object |
| Input | width | INTEGER | Target width |
| Input | height | INTEGER | Target height |
| Output | success | BOOLEAN | Operation succeeded |

---

### MoveWindowNode

Move a window to screen coordinates.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| x | INTEGER | 100 | Target X position |
| y | INTEGER | 100 | Target Y position |
| bring_to_front | BOOLEAN | False | Activate before move |

---

### MaximizeWindowNode / MinimizeWindowNode / RestoreWindowNode

Change window state.

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window | ANY | Window object |
| Output | success | BOOLEAN | Operation succeeded |

---

### GetWindowPropertiesNode

Get comprehensive window information.

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window | ANY | Window object |
| Output | properties | DICT | All window properties |
| Output | title | STRING | Window title |
| Output | x, y | INTEGER | Position |
| Output | width, height | INTEGER | Dimensions |
| Output | state | STRING | normal/maximized/minimized |
| Output | is_maximized | BOOLEAN | Maximized state |
| Output | is_minimized | BOOLEAN | Minimized state |

---

## Element Interaction

### FindElementNode

Find a desktop UI element within a window.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| selector | ANY | {} | Element selector dictionary |
| timeout | FLOAT | 5.0 | Wait time for element |
| throw_on_not_found | BOOLEAN | True | Raise error if not found |

**Selector Format:**

```python
# By name
selector = {"strategy": "name", "value": "Submit"}

# By automation ID
selector = {"strategy": "automationid", "value": "btnOK"}

# By control type
selector = {"strategy": "controltype", "value": "Button"}
```

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window | ANY | Parent window |
| Input | selector | ANY | Element selector |
| Output | element | ANY | Found element |
| Output | found | BOOLEAN | Element was found |

---

### ClickElementNode

Click a desktop UI element.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| simulate | BOOLEAN | False | Use simulated click |
| x_offset | INTEGER | 0 | Horizontal offset from center |
| y_offset | INTEGER | 0 | Vertical offset from center |
| timeout | FLOAT | 5.0 | Wait time for element |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | element | ANY | Element to click (direct) |
| Input | window | ANY | Parent window (for selector) |
| Input | selector | ANY | Element selector |
| Output | success | BOOLEAN | Click succeeded |

---

### TypeTextNode

Type text into a desktop UI element.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| text | STRING | "" | Text to type |
| clear_first | BOOLEAN | False | Clear existing text |
| interval | FLOAT | 0.01 | Delay between keystrokes |
| timeout | FLOAT | 5.0 | Wait time for element |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | element | ANY | Element to type into |
| Input | window | ANY | Parent window |
| Input | text | STRING | Text to type |
| Output | success | BOOLEAN | Operation succeeded |

---

### GetElementTextNode

Extract text content from a UI element.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| variable_name | STRING | "" | Store result in variable |
| timeout | FLOAT | 5.0 | Wait time |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | element | ANY | Element to read |
| Input | window | ANY | Parent window |
| Output | text | STRING | Extracted text |
| Output | element | ANY | Element object |

---

### GetElementPropertyNode

Get a property value from a UI element.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| property_name | STRING | "Name" | Property to retrieve |
| timeout | FLOAT | 5.0 | Wait time |

**Common Properties:**
- `Name` - Element name/text
- `AutomationId` - Unique identifier
- `ClassName` - Control class
- `IsEnabled` - Enabled state
- `Value` - Current value (for inputs)

---

## Mouse and Keyboard

### MoveMouseNode

Move the mouse cursor to a position.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| duration | FLOAT | 0.0 | Animation duration (seconds) |
| ease | CHOICE | "linear" | linear/ease_in/ease_out/ease_in_out |
| steps | INTEGER | 10 | Interpolation steps |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | x | INTEGER | Target X coordinate |
| Input | y | INTEGER | Target Y coordinate |
| Output | success | BOOLEAN | Operation succeeded |
| Output | final_x, final_y | INTEGER | Final position |

---

### MouseClickNode

Perform mouse clicks at a position.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| button | CHOICE | "left" | left/right/middle |
| click_type | CHOICE | "single" | single/double/triple |
| click_count | INTEGER | 1 | Number of clicks |
| with_ctrl | BOOLEAN | False | Hold Ctrl |
| with_shift | BOOLEAN | False | Hold Shift |
| with_alt | BOOLEAN | False | Hold Alt |
| delay | INTEGER | 0 | Delay between down/up (ms) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | x | INTEGER | X coordinate (optional) |
| Input | y | INTEGER | Y coordinate (optional) |
| Output | success | BOOLEAN | Click succeeded |
| Output | click_x, click_y | INTEGER | Click position |

---

### DragMouseNode

Drag the mouse from one position to another.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| button | CHOICE | "left" | Mouse button to hold |
| duration | FLOAT | 0.5 | Drag duration (seconds) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | start_x, start_y | INTEGER | Start coordinates |
| Input | end_x, end_y | INTEGER | End coordinates |
| Output | success | BOOLEAN | Operation succeeded |

---

### SendKeysNode

Send keyboard input.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| keys | STRING | "" | Keys to send |
| interval | FLOAT | 0.0 | Delay between keystrokes |
| with_shift | BOOLEAN | False | Hold Shift |
| with_ctrl | BOOLEAN | False | Hold Ctrl |
| with_alt | BOOLEAN | False | Hold Alt |
| press_enter_after | BOOLEAN | False | Press Enter after typing |
| clear_first | BOOLEAN | False | Clear field first |

**Special Keys:**
- `{Enter}`, `{Tab}`, `{Backspace}`, `{Delete}`
- `{Up}`, `{Down}`, `{Left}`, `{Right}`
- `{Home}`, `{End}`, `{PageUp}`, `{PageDown}`
- `{F1}` through `{F12}`
- `{Ctrl}`, `{Shift}`, `{Alt}`

---

### SendHotKeyNode

Send hotkey combinations (e.g., Ctrl+C, Alt+Tab).

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| modifier | CHOICE | "none" | Modifier key |
| key | STRING | "Enter" | Main key to press |
| keys | STRING | "" | Custom comma-separated keys |
| wait_time | FLOAT | 0.0 | Delay after sending |

**Example:**

```python
# Ctrl+S to save
config={"keys": "Ctrl,s"}

# Alt+F4 to close
config={"keys": "Alt,F4"}
```

---

### GetMousePositionNode

Get current mouse cursor position.

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | x | INTEGER | Current X coordinate |
| Output | y | INTEGER | Current Y coordinate |

---

## Advanced Interactions

### SelectFromDropdownNode

Select an item from a dropdown/combobox.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| by_text | BOOLEAN | True | Select by text vs index |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | element | ANY | Dropdown element |
| Input | value | STRING | Value to select |
| Output | success | BOOLEAN | Selection succeeded |

---

### CheckCheckboxNode

Check or uncheck a checkbox.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| check | BOOLEAN | True | Check vs uncheck |

---

### SelectRadioButtonNode

Select a radio button.

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | element | ANY | Radio button element |
| Output | success | BOOLEAN | Selection succeeded |

---

### SelectTabNode

Select a tab in a tab control.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| tab_name | STRING | "" | Tab name to select |
| tab_index | INTEGER | -1 | Tab index (-1 to use name) |

---

### ExpandTreeItemNode

Expand or collapse a tree item.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| expand | BOOLEAN | True | Expand vs collapse |

---

### ScrollElementNode

Scroll an element (scrollbar, list, window).

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| direction | CHOICE | "down" | up/down/left/right |
| amount | FLOAT | 0.5 | Scroll amount (0.0-1.0) |

---

## Wait and Verification

### WaitForElementNode

Wait for an element to reach a specific state.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| timeout | FLOAT | 10.0 | Maximum wait time |
| state | CHOICE | "visible" | visible/hidden/enabled/disabled |
| poll_interval | FLOAT | 0.5 | Check interval |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | selector | ANY | Element selector |
| Output | element | ANY | Found element |
| Output | success | BOOLEAN | Wait succeeded |

---

### WaitForWindowNode

Wait for a window to appear or disappear.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| timeout | FLOAT | 10.0 | Maximum wait time |
| state | CHOICE | "visible" | visible/hidden |
| poll_interval | FLOAT | 0.5 | Check interval |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | title | STRING | Window title (partial) |
| Input | title_regex | STRING | Title regex pattern |
| Input | class_name | STRING | Window class name |
| Output | window | ANY | Found window |
| Output | success | BOOLEAN | Wait succeeded |

---

### VerifyElementExistsNode

Check if an element exists.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| timeout | FLOAT | 0.0 | Search timeout (0 = immediate) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | selector | ANY | Element selector |
| Output | exists | BOOLEAN | Element exists |
| Output | element | ANY | Element if found |

---

### VerifyElementPropertyNode

Verify an element property has an expected value.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| comparison | CHOICE | "equals" | equals/contains/startswith/endswith/regex |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | element | ANY | Element to check |
| Input | property_name | STRING | Property name |
| Input | expected_value | ANY | Expected value |
| Output | result | BOOLEAN | Verification passed |
| Output | actual_value | ANY | Actual property value |

---

## Screen and OCR

### CaptureScreenshotNode

Capture a screenshot of the screen or a region.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| format | CHOICE | "PNG" | PNG/JPEG/BMP |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | file_path | STRING | Save path (optional) |
| Input | region | DICT | Region {x, y, width, height} |
| Output | image | ANY | PIL Image object |
| Output | file_path | STRING | Saved file path |
| Output | success | BOOLEAN | Capture succeeded |

---

### CaptureElementImageNode

Capture an image of a specific element.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| format | CHOICE | "PNG" | Image format |
| padding | INTEGER | 0 | Extra pixels around element |

---

### OCRExtractTextNode

Extract text from an image using OCR.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| engine | CHOICE | "auto" | auto/rapidocr/tesseract/winocr |
| language | STRING | "eng" | OCR language code |
| config | STRING | "" | Additional OCR options |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | image | ANY | PIL Image object |
| Input | image_path | STRING | Image file path |
| Input | region | DICT | Region to process |
| Output | text | STRING | Extracted text |
| Output | engine_used | STRING | OCR engine used |
| Output | success | BOOLEAN | Extraction succeeded |

---

### CompareImagesNode

Compare two images for similarity.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| method | CHOICE | "histogram" | ssim/histogram/pixel |
| threshold | FLOAT | 0.9 | Match threshold (0.0-1.0) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | image1, image2 | ANY | Images to compare |
| Input | image1_path, image2_path | STRING | Image paths |
| Output | similarity | FLOAT | Similarity score |
| Output | is_match | BOOLEAN | Images match |
| Output | method | STRING | Method used |

---

## AI-Powered Detection

### YOLOFindElementNode

Find UI elements using YOLOv8 object detection. Works without DOM/accessibility APIs - ideal for VDI, Citrix, legacy apps, and remote desktop.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| element_type | CHOICE | "button" | button/input/checkbox/radio/dropdown/link/icon/text/menu/tab/toggle |
| element_index | INTEGER | 0 | Which match to use (0 = first) |
| confidence_threshold | FLOAT | 0.5 | Minimum confidence (0.0-1.0) |
| region_x, region_y | INTEGER | 0 | Search region start |
| region_width, region_height | INTEGER | 0 | Search region size (0 = full screen) |
| click_after_find | BOOLEAN | False | Auto-click after finding |
| use_gpu | BOOLEAN | True | GPU acceleration |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | window_handle | INTEGER | Optional window to capture |
| Output | x, y | INTEGER | Element center coordinates |
| Output | width, height | INTEGER | Bounding box size |
| Output | confidence | FLOAT | Detection confidence |
| Output | found | BOOLEAN | Element was found |
| Output | all_elements | LIST | All detected elements |

**Example:**

```python
# Find and click a button in VDI
workflow.add_node(
    "YOLOFindElementNode",
    config={
        "element_type": "button",
        "confidence_threshold": 0.7,
        "click_after_find": True,
    }
)
```

> **Note:** Requires `ultralytics` and `opencv-python` packages.

---

## Complete Workflow Example

```python
# Desktop automation workflow: Launch Notepad, type text, save

# 1. Launch application
launch = workflow.add_node(
    "LaunchApplicationNode",
    config={
        "application_path": "C:\\Windows\\System32\\notepad.exe",
        "window_title_hint": "Notepad",
    }
)

# 2. Wait for window
wait = workflow.add_node(
    "WaitForWindowNode",
    config={"timeout": 10.0}
)
wait.set_input("title", "Notepad")

# 3. Type text
type_node = workflow.add_node(
    "TypeTextNode",
    config={"text": "Hello from CasareRPA!"}
)
type_node.set_input("window", launch.get_output("window"))

# 4. Save with Ctrl+S
save = workflow.add_node(
    "SendHotKeyNode",
    config={"keys": "Ctrl,s"}
)

# 5. Wait for Save dialog
wait_dialog = workflow.add_node(
    "WaitForWindowNode",
    config={"timeout": 5.0}
)
wait_dialog.set_input("title", "Save As")

# 6. Type filename and save
type_filename = workflow.add_node("TypeTextNode")
type_filename.set_input("text", "automation_test.txt")

enter = workflow.add_node(
    "SendHotKeyNode",
    config={"key": "Enter"}
)

# Connect flow
workflow.connect(launch, wait)
workflow.connect(wait, type_node)
workflow.connect(type_node, save)
workflow.connect(save, wait_dialog)
workflow.connect(wait_dialog, type_filename)
workflow.connect(type_filename, enter)
```

---

## Error Handling

Desktop automation can fail due to timing issues, unexpected dialogs, or application state changes. Best practices:

1. **Use appropriate timeouts** - Increase for slow applications
2. **Add wait nodes** - Synchronize with application state
3. **Handle not-found gracefully** - Use `throw_on_not_found: False` when appropriate
4. **Verify state** - Use verification nodes before critical actions
5. **Clean up resources** - Always close applications in finally blocks

---

## Related Documentation

- [Browser Automation](browser.md) - Web automation with Playwright
- [Control Flow](control-flow.md) - Loops and conditionals
- [Error Handling](error-handling.md) - Recovery strategies
- [System Nodes](system.md) - System-level operations

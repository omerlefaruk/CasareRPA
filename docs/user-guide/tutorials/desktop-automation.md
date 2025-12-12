# Desktop Application Automation Tutorial

Learn to automate Windows desktop applications: launch programs, find UI elements, click buttons, type text, and read results.

**Time required:** 25 minutes

**What you will build:**
A workflow that launches Notepad, types text, saves the file, then opens Calculator, performs a calculation, and reads the result.

## Prerequisites

- CasareRPA installed on Windows
- Windows 10 or later
- Administrator access (for some applications)

## Goals

By the end of this tutorial, you will:
- Launch Windows applications
- Find UI elements using selectors
- Click buttons and type text
- Read values from UI elements
- Send keyboard shortcuts
- Handle windows and dialogs

---

## Part 1: Notepad Automation

### Step 1: Create New Workflow

1. Open CasareRPA Canvas
2. **File** > **New Workflow**
3. Save as `desktop_automation_tutorial.json`

### Step 2: Add Start Node

1. Drag **Start** from **Basic** to position (100, 300)

### Step 3: Launch Notepad

1. Drag **Launch Application** from **Desktop** category
2. Position at (400, 300)
3. Connect: Start -> Launch Application

#### Configure Launch Application

| Property | Value |
|----------|-------|
| application_path | `C:\Windows\System32\notepad.exe` |
| window_title_hint | `Notepad` |
| window_state | `maximized` |
| timeout | `10.0` |
| keep_open | `true` |

```
[Launch Application]
    application_path: "C:\\Windows\\System32\\notepad.exe"
    window_title_hint: "Notepad"
    window_state: "maximized"
    timeout: 10.0
```

### Step 4: Wait for Window

Add a wait to ensure the window is ready:

1. Drag **Wait For Window** from **Desktop**
2. Position at (700, 300)
3. Connect: Launch Application -> Wait For Window

#### Configure Wait For Window

| Property | Value |
|----------|-------|
| timeout | `10.0` |
| state | `visible` |

Connect the `window_title` input from Launch Application's `window_title` output.

### Step 5: Type Text into Notepad

1. Drag **Type Text** from **Desktop**
2. Position at (1000, 300)
3. Connect: Wait For Window -> Type Text

#### Configure Type Text

| Property | Value |
|----------|-------|
| text | `Hello from CasareRPA!\n\nThis text was typed automatically.` |
| clear_first | `false` |
| interval | `0.02` |

Connect the `window` port from Launch Application's `window` output.

> **Note:** Use `\n` for newlines. The `interval` property adds a small delay between keystrokes for more human-like typing.

### Step 6: Save the File with Ctrl+S

1. Drag **Send Hot Key** from **Desktop**
2. Position at (1300, 300)
3. Connect: Type Text -> Send Hot Key

#### Configure Send Hot Key

| Property | Value |
|----------|-------|
| keys | `Ctrl,s` |
| wait_time | `0.5` |

### Step 7: Wait for Save Dialog

1. Drag **Wait For Window** from **Desktop**
2. Position at (1600, 300)
3. Connect: Send Hot Key -> Wait For Window

#### Configure Wait For Window

| Property | Value |
|----------|-------|
| title | `Save As` |
| timeout | `5.0` |
| state | `visible` |

### Step 8: Type Filename

1. Drag **Send Keys** from **Desktop**
2. Position at (1900, 300)
3. Connect: Wait For Window -> Send Keys

#### Configure Send Keys

| Property | Value |
|----------|-------|
| keys | `C:\temp\rpa_test.txt` |
| press_enter_after | `true` |

### Step 9: Close Notepad

1. Drag **Close Application** from **Desktop**
2. Position at (2200, 300)
3. Connect: Send Keys -> Close Application

#### Configure Close Application

| Property | Value |
|----------|-------|
| force_close | `false` |
| timeout | `5.0` |

---

## Part 2: Calculator Automation

### Step 10: Launch Calculator

1. Drag **Launch Application** from **Desktop**
2. Position at (400, 600)
3. Connect: Close Application (from Notepad) -> Launch Application

#### Configure Launch Application

| Property | Value |
|----------|-------|
| application_path | `calc.exe` |
| window_title_hint | `Calculator` |
| timeout | `10.0` |

> **Note:** For Calculator, you can use just `calc.exe` without the full path since it's in the system PATH.

### Step 11: Wait for Calculator

1. Drag **Wait For Window** from **Desktop**
2. Position at (700, 600)
3. Connect: Launch Application -> Wait For Window

| Property | Value |
|----------|-------|
| title | `Calculator` |
| timeout | `10.0` |

### Step 12: Click Number Buttons

We'll calculate: 25 + 17 = 42

Add a **Click Element** node for each button press:

#### Click "2"

1. Drag **Click Element** from **Desktop**
2. Position at (1000, 600)
3. Connect window port from Launch Application

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "num2Button"}` |
| timeout | `5.0` |

#### Click "5"

1. Drag another **Click Element**
2. Position at (1150, 600)

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "num5Button"}` |

#### Click "+" (Plus)

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "plusButton"}` |

#### Click "1"

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "num1Button"}` |

#### Click "7"

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "num7Button"}` |

#### Click "=" (Equals)

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "equalButton"}` |

### Step 13: Read the Result

1. Drag **Get Element Text** from **Desktop**
2. Connect after the equals button click

| Property | Value |
|----------|-------|
| selector | `{"strategy": "automationid", "value": "CalculatorResults"}` |

#### Output

The `text` output port will contain the result (e.g., "Display is 42").

### Step 14: Log the Result

1. Drag **Log** from **Basic**
2. Connect: Get Element Text -> Log

| Property | Value |
|----------|-------|
| message | `Calculator result: {{text}}` |
| level | `info` |

### Step 15: Close Calculator

1. Drag **Close Application** from **Desktop**
2. Connect: Log -> Close Application

### Step 16: Add End Node

1. Drag **End** from **Basic**
2. Connect: Close Application -> End

---

## Complete Workflow Diagram

```
                           NOTEPAD SECTION
[Start] --> [Launch App] --> [Wait Window] --> [Type Text] --> [Send Hot Key]
            (Notepad)                                           (Ctrl+S)
                                                                    |
                                                                    v
                         [Wait Window] <-- [Send Keys] <-- [Close App]
                         (Save As)        (filename)
                              |
                              v
                           CALCULATOR SECTION
                    [Launch App] --> [Wait Window] --> [Click 2] --> [Click 5]
                    (Calculator)                            |
                                                            v
[End] <-- [Close App] <-- [Log] <-- [Get Text] <-- [Click =] <-- [Click +]
                                                        ^            |
                                                        |            v
                                               [Click 7] <-- [Click 1]
```

---

## Understanding Desktop Selectors

Desktop automation uses UI Automation selectors to find elements.

### Selector Strategies

| Strategy | Description | Example |
|----------|-------------|---------|
| `name` | Element's Name property | `{"strategy": "name", "value": "Submit"}` |
| `automationid` | AutomationId property | `{"strategy": "automationid", "value": "btnOK"}` |
| `controltype` | Control type | `{"strategy": "controltype", "value": "Button"}` |
| `classname` | Win32 class name | `{"strategy": "classname", "value": "Edit"}` |

### Finding Selectors

Use the **UI Explorer** built into CasareRPA:

1. Open Canvas
2. **Tools** > **UI Explorer**
3. Click **Pick Element**
4. Click on the target element in any application
5. Copy the suggested selector

Or use external tools:
- **Inspect.exe** (Windows SDK)
- **FlaUI Inspect**
- **Accessibility Insights**

### Selector Examples

```json
// By AutomationId (most reliable)
{"strategy": "automationid", "value": "txtUsername"}

// By Name
{"strategy": "name", "value": "Save"}

// By Control Type + Name (combined)
{"strategy": "controltype", "value": "Button", "name": "OK"}

// Multiple criteria
{
    "strategy": "controltype",
    "value": "Edit",
    "parent": {"strategy": "name", "value": "Login"}
}
```

---

## Using Keyboard and Mouse

### SendKeysNode - Special Keys

```
{Enter}     - Enter key
{Tab}       - Tab key
{Backspace} - Backspace
{Delete}    - Delete key
{Escape}    - Escape key
{F1}-{F12}  - Function keys
{Up},{Down},{Left},{Right} - Arrow keys
{Home},{End},{PageUp},{PageDown} - Navigation
```

### SendHotKeyNode - Key Combinations

| Combination | Config |
|-------------|--------|
| Ctrl+C | `keys: "Ctrl,c"` |
| Ctrl+Shift+S | `keys: "Ctrl,Shift,s"` |
| Alt+F4 | `keys: "Alt,F4"` |
| Windows+D | `keys: "Win,d"` |

### Mouse Operations

```
[Move Mouse]
    x: 500
    y: 300
    duration: 0.5

[Mouse Click]
    button: "left"
    click_type: "double"
    x: 500
    y: 300

[Drag Mouse]
    start_x: 100
    start_y: 100
    end_x: 300
    end_y: 300
    duration: 1.0
```

---

## Handling Dialogs

### Message Box / Alert Detection

```
[Wait For Window]
    title: "Warning"
    timeout: 5.0
    state: "visible"
        |
        v
[Find Element]
    selector: {"strategy": "controltype", "value": "Button", "name": "OK"}
        |
        v
[Click Element]
```

### File Dialogs

```
[Send Hot Key]
    keys: "Ctrl,o"  # Open dialog
        |
        v
[Wait For Window]
    title: "Open"
        |
        v
[Send Keys]
    keys: "C:\\documents\\file.txt{Enter}"
```

---

## Advanced: Working with Complex Forms

### Filling a Login Form

```
[Launch Application]
    application_path: "C:\\Program Files\\App\\app.exe"
        |
        v
[Wait For Window]
    title: "Login"
        |
        v
[Find Element]
    selector: {"strategy": "automationid", "value": "txtUsername"}
        |
        v
[Type Text]
    text: "{{username}}"
    clear_first: true
        |
        v
[Find Element]
    selector: {"strategy": "automationid", "value": "txtPassword"}
        |
        v
[Type Text]
    text: "{{password}}"
        |
        v
[Click Element]
    selector: {"strategy": "automationid", "value": "btnLogin"}
```

### Using Variables

Store credentials securely:

```
[Get Variable]
    name: "app_username"
        |
        v
[Type Text]
    text: "{{app_username}}"
```

---

## Error Handling for Desktop Automation

Desktop automation is inherently flaky. Always add error handling:

```
[Try]
    |
  try_body
    |
[Launch Application]
    |
[Wait For Window]
    timeout: 15.0
    |
[Click Element]
    |
    +---(error)---> [Catch]
    |                   |
    |              catch_body
    |                   |
    |              [Capture Screenshot]
    |                   path: "C:\\errors\\{{timestamp}}.png"
    |                   |
    |              [Log Error]
    |                   |
    +--------+---------+
             |
         [Finally]
             |
        finally_body
             |
        [Close Application]
            force_close: true
```

---

## Best Practices

### 1. Use AutomationId When Available

AutomationId is the most stable selector - it doesn't change with UI language or theme.

### 2. Add Explicit Waits

```
[Wait For Window]   # Always wait for window to appear
    |
[Wait For Element]  # Wait for specific element to be ready
    state: "enabled"
```

### 3. Use Relative Coordinates Carefully

Prefer element selectors over coordinates. Coordinates break when:
- Screen resolution changes
- Window position changes
- DPI scaling differs

### 4. Handle Timing Issues

Set appropriate timeouts:
- Application launch: 10-30 seconds
- Element wait: 5-10 seconds
- Dialog appearance: 3-5 seconds

### 5. Clean Up Resources

Always close applications in Finally blocks.

### 6. Use Keep Open for Development

Set `keep_open: true` during development to inspect application state after errors.

---

## Troubleshooting

### Application doesn't launch

**Causes:**
- Path is incorrect
- Need administrator privileges
- Application already running

**Solutions:**
- Verify path exists
- Run CasareRPA as administrator
- Add check for existing process

### Element not found

**Causes:**
- Wrong selector
- Element not visible/enabled
- Window not focused

**Solutions:**
- Use UI Explorer to verify selector
- Add wait for element
- Use Activate Window node first

### Keyboard input not working

**Causes:**
- Window not focused
- Application captures input differently

**Solutions:**
- Add Activate Window before typing
- Try both Type Text and Send Keys
- Use slower typing interval

### Actions happening too fast

**Solution:** Add delays:

```
[Wait]
    seconds: 0.5

# Or use slow typing
[Type Text]
    interval: 0.05  # 50ms between keystrokes
```

---

## Node Reference

### LaunchApplicationNode

| Property | Type | Description |
|----------|------|-------------|
| application_path | FILE_PATH | Executable path |
| arguments | STRING | Command line args |
| working_directory | STRING | Start directory |
| window_title_hint | STRING | Expected window title |
| window_state | CHOICE | normal/maximized/minimized |
| timeout | FLOAT | Wait time (seconds) |
| keep_open | BOOLEAN | Keep open after workflow |

### ClickElementNode

| Property | Type | Description |
|----------|------|-------------|
| selector | ANY | Element selector |
| simulate | BOOLEAN | Use simulated click |
| x_offset | INTEGER | X offset from center |
| y_offset | INTEGER | Y offset from center |
| timeout | FLOAT | Wait timeout |

### TypeTextNode

| Property | Type | Description |
|----------|------|-------------|
| text | STRING | Text to type |
| clear_first | BOOLEAN | Clear field first |
| interval | FLOAT | Keystroke delay |
| timeout | FLOAT | Wait timeout |

### SendHotKeyNode

| Property | Type | Description |
|----------|------|-------------|
| keys | STRING | Comma-separated keys |
| wait_time | FLOAT | Delay after sending |

---

## Next Steps

- [Browser Automation](browser-automation.md) - Automate web applications
- [Email Processing](email-processing.md) - Process desktop email clients
- [Error Handling](error-handling.md) - Build resilient automations
- [Scheduled Workflows](scheduled-workflows.md) - Run automations automatically

---

## Summary

You learned how to:
1. Launch Windows applications with LaunchApplicationNode
2. Find UI elements using selectors
3. Type text and send keyboard shortcuts
4. Read values from UI elements
5. Handle dialogs and windows
6. Clean up resources properly

Desktop automation enables you to automate any Windows application, even those without APIs.

# CasareRPA Quick Start Guide

Get your first automation workflow running in under 10 minutes!

## Prerequisites

- CasareRPA installed (see [INSTALLATION.md](./INSTALLATION.md))
- Playwright browsers installed (`playwright install chromium`)

## Launch the Canvas

```powershell
cd casare-rpa
python run.py
```

The Canvas (visual workflow editor) will open.

## Tutorial 1: Hello World (2 minutes)

Let's create a simple workflow that logs a message.

### Step 1: Add a Start Node
1. Right-click on the canvas
2. Select **Control Flow > StartNode** (or press `Ctrl+Shift+F` to search)
3. A Start node appears - this is where every workflow begins

### Step 2: Add a Log Node
1. Right-click on the canvas again
2. Select **System > LogNode**
3. Click on the Log node to select it
4. In the Properties panel (right side), set:
   - **Message:** `Hello, CasareRPA!`
   - **Level:** `info`

### Step 3: Add an End Node
1. Right-click > **Control Flow > EndNode**

### Step 4: Connect the Nodes
1. Click and drag from **Start > exec_out** (right side)
2. Connect to **Log > exec_in** (left side)
3. Connect **Log > exec_out** to **End > exec_in**

### Step 5: Run the Workflow
1. Press `F5` or click the **Run** button in the toolbar
2. Check the Output panel at the bottom - you should see your message!

## Tutorial 2: Web Search Automation (5 minutes)

Let's create a workflow that opens a browser and performs a search.

### Step 1: Create the Workflow Structure
Add these nodes and connect them in order:
1. **StartNode**
2. **LaunchBrowserNode**
3. **GoToURLNode**
4. **TypeTextNode**
5. **ClickElementNode**
6. **TakeScreenshotNode**
7. **CloseBrowserNode**
8. **EndNode**

### Step 2: Configure LaunchBrowserNode
- **Browser:** `chromium`
- **Headless:** `false` (so you can see the browser)

### Step 3: Configure GoToURLNode
- **URL:** `https://www.google.com`

### Step 4: Configure TypeTextNode
- **Selector:** `textarea[name="q"]`
- **Text:** `CasareRPA automation`
- **Press Enter After:** `true`

### Step 5: Configure TakeScreenshotNode
- **File Path:** `search_results.png`
- **Full Page:** `false`

### Step 6: Run and Watch
Press `F5` - watch as the browser opens, navigates to Google, types your search, and captures a screenshot!

## Tutorial 3: Loop Through Data (3 minutes)

Let's iterate through a list of URLs.

### Step 1: Add Nodes
1. **StartNode**
2. **SetVariableNode** - to define our URL list
3. **ForEachNode** - to iterate
4. **LogNode** - inside the loop
5. **EndNode**

### Step 2: Configure SetVariableNode
- **Variable Name:** `urls`
- **Value:** `["https://google.com", "https://github.com", "https://python.org"]`
- **Data Type:** `list`

### Step 3: Configure ForEachNode
- **Items Variable:** `urls`
- **Item Variable Name:** `current_url`

### Step 4: Configure LogNode
- **Message:** `Processing: ${current_url}`

### Step 5: Connect the Loop
- StartNode > SetVariableNode > ForEachNode
- ForEachNode (loop_body) > LogNode
- LogNode > ForEachNode (loop_back)
- ForEachNode (exec_out) > EndNode

### Step 6: Run
You'll see three log messages, one for each URL!

## Key Concepts

### Node Types

| Category | Purpose | Examples |
|----------|---------|----------|
| Control Flow | Program flow | Start, End, If, Loop, TryCatch |
| Browser | Web automation | LaunchBrowser, Click, Type, Wait |
| Data | Variables & operations | SetVariable, String, Math, List |
| File | File operations | Read, Write, CSV, JSON |
| System | OS operations | Log, Delay, RunCommand |
| Desktop | Windows automation | ClickWindow, TypeInWindow |

### Connections

- **Exec ports** (triangles): Control flow - when to execute
- **Data ports** (circles): Data transfer between nodes

### Variables

- **${variableName}**: Use variables in text fields
- Variables are workflow-scoped (available everywhere)
- Use SetVariable to create, GetVariable to retrieve

### Error Handling

Wrap risky operations in TryCatch nodes:
```
TryCatchNode
  |
  +-- try_body --> (risky operations)
  |
  +-- catch_body --> (error handling)
```

## Saving and Loading

- **Save:** `Ctrl+S` or File > Save
- **Save As:** `Ctrl+Shift+S`
- **Open:** `Ctrl+O`
- Workflows are saved as `.json` files in the `workflows/` directory

## Debugging Tips

1. **Step Through:** Use `F10` to execute one node at a time
2. **Breakpoints:** Right-click a node > Toggle Breakpoint
3. **Variable Inspector:** View > Variable Inspector to see all variables
4. **Execution History:** View > Execution History for detailed logs

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+F` | Search nodes |
| `F5` | Run workflow |
| `F10` | Step to next node |
| `Shift+F5` | Stop execution |
| `Ctrl+S` | Save |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Delete` | Delete selected node |
| `Ctrl+C/V` | Copy/Paste nodes |

## Next Steps

1. **Explore Node Types:** Try different nodes from the context menu
2. **Read the Documentation:**
   - [WEB_AUTOMATION.md](./guides/WEB_AUTOMATION.md) for browser automation
   - [DESKTOP_AUTOMATION.md](./guides/DESKTOP_AUTOMATION.md) for Windows automation
3. **Check Examples:** Look in `workflows/examples/` for sample workflows
4. **Schedule Workflows:** Use the Orchestrator for scheduled execution

## Common Patterns

### Wait for Page Load
```
GoToURLNode --> WaitForNavigationNode --> (next action)
```

### Conditional Branching
```
IfNode
  |-- true_branch --> (action if true)
  |-- false_branch --> (action if false)
```

### Retry on Failure
```
RetryNode (max_attempts: 3, delay_seconds: 2)
  |-- body --> (operation that might fail)
```

### Extract and Process Data
```
GetElementTextNode --> StringOperationNode --> SetVariableNode
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Browser doesn't open | Check `headless` is `false` |
| Element not found | Verify selector, add WaitForElement |
| Workflow stops unexpectedly | Check Output panel for errors |
| Variables not working | Use `${varName}` syntax, check spelling |

See [ERROR_CODES.md](./ERROR_CODES.md) for detailed error solutions.

---

Congratulations! You've created your first CasareRPA workflows. Continue exploring and automating!

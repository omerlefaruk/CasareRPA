# Debugging Workflows

CasareRPA provides comprehensive debugging tools to help you identify and fix issues in your workflows. This guide covers all debugging features and techniques.

## Table of Contents

- [Debug Panel Overview](#debug-panel-overview)
- [Breakpoints](#breakpoints)
- [Step-Through Execution](#step-through-execution)
- [Variable Inspection](#variable-inspection)
- [Log Panel](#log-panel)
- [Debug Output](#debug-output)
- [Common Debugging Techniques](#common-debugging-techniques)

---

## Debug Panel Overview

The Debug Panel is your command center for workflow debugging. Access it via **View > Panels > Debug** or the default keyboard shortcut.

### Panel Tabs

| Tab | Purpose |
|-----|---------|
| **Logs** | Real-time execution logs with filtering |
| **Variables** | Live variable inspection with tree view |
| **Call Stack** | Current execution path visualization |
| **Watch** | User-defined expressions to monitor |
| **Breakpoints** | Manage all breakpoints in the workflow |
| **REPL** | Interactive Python console for evaluation |
| **Snapshots** | Save and restore execution state |

### Step Controls

The toolbar provides execution control buttons:

| Button | Shortcut | Action |
|--------|----------|--------|
| **Step Over** | F10 | Execute current node, pause at next |
| **Step Into** | F11 | Step into nested structures (subflows) |
| **Step Out** | Shift+F11 | Continue until exiting current scope |
| **Continue** | F5 | Resume until next breakpoint |

---

## Breakpoints

Breakpoints pause workflow execution at specific nodes, allowing you to inspect state.

### Setting Breakpoints

**Method 1: Right-Click Menu**
1. Right-click on any node
2. Select **Toggle Breakpoint**
3. A red indicator appears on the node

**Method 2: Breakpoints Panel**
1. Open the Debug Panel
2. Navigate to the **Breakpoints** tab
3. Right-click to add breakpoints by node ID

### Breakpoint Types

| Type | Description |
|------|-------------|
| **Regular** | Always pauses when hit |
| **Conditional** | Pauses only when condition is true |
| **Hit Count** | Pauses after N hits |

### Conditional Breakpoints

Set conditions that must be true for the breakpoint to trigger:

1. Right-click a breakpoint in the panel
2. Select **Edit Condition**
3. Enter a Python expression:
   ```python
   # Pause only when count exceeds 10
   count > 10

   # Pause on error status
   status == "error"

   # Pause when list is empty
   len(items) == 0
   ```

### Managing Breakpoints

From the Breakpoints tab:

| Action | Description |
|--------|-------------|
| **Enable/Disable** | Toggle checkbox to enable/disable |
| **Enable All** | Enable all breakpoints |
| **Disable All** | Disable all breakpoints |
| **Clear All** | Remove all breakpoints |
| **Edit Condition** | Set/modify condition expression |
| **Navigate** | Double-click to focus node on canvas |

### Breakpoint Indicators

On the canvas, breakpoints are shown as:
- **Red circle**: Active breakpoint
- **Red outline**: Disabled breakpoint
- **Yellow glow**: Currently paused at this node

---

## Step-Through Execution

When paused at a breakpoint, you can step through your workflow node by node.

### Starting Debug Mode

1. Set at least one breakpoint
2. Click **Run** or press F5
3. Execution pauses at the first breakpoint

### Step Commands

**Step Over (F10)**
- Executes the current node completely
- Pauses at the next node in sequence
- Treats subflows as single operations

**Step Into (F11)**
- If current node is a subflow, enters it
- Pauses at the first node inside the subflow
- For regular nodes, same as Step Over

**Step Out (Shift+F11)**
- Continues execution until current scope exits
- Pauses after returning from subflow
- Useful for quickly exiting nested structures

**Continue (F5)**
- Resumes normal execution
- Pauses at next enabled breakpoint
- If no more breakpoints, runs to completion

### Execution States

| State | Status Bar | Description |
|-------|------------|-------------|
| **Idle** | Gray | Not running |
| **Running** | Green | Executing normally |
| **Paused** | Yellow | Stopped at breakpoint |
| **Error** | Red | Execution failed |

---

## Variable Inspection

The Variables tab shows all variables in the current execution context.

### Variable Tree View

Variables are displayed in a hierarchical tree:

```
Variables
├── page (Page)
├── results (list, 5 items)
│   ├── [0] (dict)
│   │   ├── name: "Item 1"
│   │   └── price: 29.99
│   ├── [1] (dict)
│   └── ...
├── counter (int): 5
└── status (str): "success"
```

### Tree Navigation

- **Expand/Collapse**: Click arrows to expand nested structures
- **Expand All**: Button to expand entire tree
- **Collapse All**: Button to collapse entire tree
- **Search**: Filter variables by name or value

### Context Menu

Right-click any variable for options:

| Option | Description |
|--------|-------------|
| **Copy Name** | Copy variable name to clipboard |
| **Copy Value** | Copy variable value to clipboard |
| **Add to Watch** | Create watch expression for variable |

### Refreshing Variables

Variables update automatically during stepping. Click **Refresh** to manually update when paused.

### Variable Types Display

| Type | Display |
|------|---------|
| String | `"value"` with quotes |
| Number | `42` or `3.14` |
| Boolean | `True` or `False` |
| List | `list (N items)` with children |
| Dict | `dict (N items)` with key-value children |
| Object | Type name with attributes |
| None | `None` |

---

## Log Panel

The Logs tab provides real-time logging with filtering capabilities.

### Log Entry Format

Each log entry shows:

| Column | Description |
|--------|-------------|
| **Time** | Timestamp (HH:MM:SS.mmm) |
| **Level** | Info, Warning, Error, Success |
| **Node** | Node name or ID that generated the log |
| **Message** | Log message content |

### Log Levels

| Level | Color | Description |
|-------|-------|-------------|
| **Info** | Blue | General information |
| **Warning** | Yellow | Potential issues |
| **Error** | Red | Failures and exceptions |
| **Success** | Green | Successful completions |

### Filtering Logs

Use the filter dropdown to show only specific levels:

- **All**: Show all log entries
- **Info**: Information messages only
- **Warning**: Warnings only
- **Error**: Errors only
- **Success**: Success messages only

### Auto-Scroll

Toggle auto-scroll to automatically follow new log entries:

- **ON**: Automatically scrolls to latest log
- **OFF**: Maintains current scroll position

### Navigating to Nodes

Double-click any log entry to focus its source node on the canvas.

### Clearing Logs

Click **Clear** to remove all log entries. This doesn't affect the workflow state.

---

## Debug Output

Add explicit debug output to your workflows for troubleshooting.

### Using Log Nodes

Insert **Log Node** to output custom messages:

```python
# Log Node configuration:
message: "Processing item {{index}} of {{total}}"
level: "info"
```

### Using Tooltip Nodes

**Tooltip Node** displays values without pausing execution:

```python
# Tooltip Node configuration:
message: "Current value: {{my_variable}}"
duration: 3  # seconds
```

### Debug Variable Node

Use **Debug Variable** to log detailed variable information:

```python
# Outputs complete variable state including:
# - Variable name
# - Current value
# - Type
# - Size (for collections)
```

### Console Output

For advanced debugging, use **Run Script** node with print statements:

```python
# Script Node code:
print(f"DEBUG: items = {items}")
print(f"DEBUG: count = {len(items)}")
for i, item in enumerate(items):
    print(f"  [{i}] {item}")
```

---

## Common Debugging Techniques

### 1. Isolate the Problem

**Technique:** Binary search debugging

1. Set a breakpoint in the middle of your workflow
2. Run and check if the problem has occurred
3. If yes, problem is before this point
4. If no, problem is after this point
5. Repeat to narrow down

### 2. Check Variable Values

**Technique:** Watch critical variables

```python
# Add watch expressions for:
len(items)      # Collection sizes
status          # State variables
response.status_code  # API responses
error           # Error messages
```

### 3. Validate Node Outputs

**Technique:** Verify each node's output

1. Pause after a node
2. Check the output port values
3. Verify they match expectations
4. Check for None/null values

### 4. Handle Timing Issues

**Technique:** Add strategic waits

```python
# Common browser automation issues:
# - Element not yet loaded
# - Page still transitioning
# - Animation in progress

# Solutions:
# 1. Add Wait Node before interaction
# 2. Use Wait for Element node
# 3. Increase timeout values
```

### 5. Debug Browser Automation

**Technique:** Visual verification

1. Enable **Screenshot on Fail** in browser nodes
2. Check screenshots when errors occur
3. Compare expected vs actual page state
4. Look for popup dialogs, loading spinners

### 6. Debug API Calls

**Technique:** Log full request/response

```python
# HTTP Request Node configuration:
log_request: true
log_response: true

# Check logs for:
# - Request URL and headers
# - Request body
# - Response status code
# - Response body
```

### 7. Catch Silent Failures

**Technique:** Explicit error checking

```python
# After each critical operation, add:
# If Node: {{last_result.success}} == False
#   True: [Handle Error]
#   False: [Continue]
```

### 8. Use Snapshots for Complex Issues

**Technique:** Save state for comparison

1. Create snapshot before problematic section
2. Run and observe the error
3. Restore snapshot
4. Try different approach
5. Compare results

### 9. Debug Loops

**Technique:** Conditional breakpoints on loops

```python
# Break only on specific iteration:
index == 5

# Break on problematic data:
item.status == "error"

# Break after many iterations:
iteration >= 100
```

### 10. Debug Subflows

**Technique:** Use Step Into

1. Set breakpoint on SubflowNode
2. When paused, press F11 (Step Into)
3. Debug inside the subflow
4. Use Step Out (Shift+F11) to return

---

## Debug REPL Console

The REPL (Read-Eval-Print Loop) tab provides an interactive Python console.

### Using the REPL

1. Navigate to the **REPL** tab
2. Type Python expressions
3. Press Enter to evaluate
4. View results immediately

### Available Context

In the REPL, you have access to:

```python
# All workflow variables
>>> items
['item1', 'item2', 'item3']

>>> len(items)
3

>>> status
'success'

# Inspect complex objects
>>> type(page)
<class 'playwright.async_api._generated.Page'>

# Evaluate expressions
>>> sum([x['price'] for x in results])
149.95
```

### REPL History

- **Up Arrow**: Previous command
- **Down Arrow**: Next command
- **Clear**: Reset REPL output

---

## Execution Snapshots

Snapshots capture the entire execution state for later restoration.

### Creating Snapshots

1. Pause at a breakpoint
2. Go to **Snapshots** tab
3. Click **Create Snapshot**
4. Enter optional description
5. Snapshot is saved with timestamp

### Snapshot Contents

Each snapshot includes:
- All variable values
- Current node position
- Call stack state
- Browser state (if applicable)

### Restoring Snapshots

1. Select a snapshot
2. Click **Restore**
3. Execution rewinds to that state
4. Continue debugging from that point

### Managing Snapshots

| Action | Description |
|--------|-------------|
| **Create** | Save current state |
| **Restore** | Rewind to saved state |
| **Delete** | Remove snapshot |

---

## Troubleshooting Common Issues

### Breakpoint Not Triggering

**Causes:**
- Breakpoint is disabled
- Node is in a skipped branch
- Execution takes different path

**Solutions:**
1. Verify breakpoint is enabled (checkbox checked)
2. Check if condition is never true
3. Trace execution path with Step Over

### Variables Not Updating

**Causes:**
- Variable scope issue
- Variable overwritten
- Async timing issue

**Solutions:**
1. Refresh variables manually
2. Check for variable name conflicts
3. Add watch expressions

### Step Commands Not Working

**Causes:**
- Not paused at breakpoint
- Workflow completed or errored
- UI state out of sync

**Solutions:**
1. Ensure status shows "Paused"
2. Check for uncaught errors
3. Stop and restart debugging

---

## Related Guides

- [Control Flow Patterns](./control-flow.md) - Debug loops and conditions
- [Error Handling](./error-handling.md) - Handle and debug errors
- [Best Practices](./best-practices.md) - Preventive debugging practices

# Canvas Overview

The Canvas is CasareRPA's visual workflow designer. This guide walks you through every part of the interface so you can build automations efficiently.

## Main Window Layout

[Screenshot: Full Canvas window with all areas labeled]

The Canvas window is divided into these main areas:

| Area | Position | Purpose |
|------|----------|---------|
| Menu Bar | Top | File, Edit, View, Workflow, Tools, Help menus |
| Toolbar | Below menu | Quick access to common actions |
| Node Palette | Left panel | Browse and search available nodes |
| Canvas | Center | Visual workflow editing area |
| Properties Panel | Right panel | Configure selected node |
| Bottom Panel | Bottom | Logs, Variables, Breakpoints tabs |

## Menu Bar

### File Menu

| Action | Shortcut | Description |
|--------|----------|-------------|
| New Workflow | `Ctrl+N` | Create empty workflow |
| Open | `Ctrl+O` | Open existing workflow file |
| Save | `Ctrl+S` | Save current workflow |
| Save As | `Ctrl+Shift+S` | Save with new name |
| Import | - | Import workflow from template |
| Export | - | Export selected nodes |
| Recent Files | - | Quick access to recent workflows |
| Exit | `Alt+F4` | Close CasareRPA |

### Edit Menu

| Action | Shortcut | Description |
|--------|----------|-------------|
| Undo | `Ctrl+Z` | Undo last action |
| Redo | `Ctrl+Y` | Redo undone action |
| Cut | `Ctrl+X` | Cut selected nodes |
| Copy | `Ctrl+C` | Copy selected nodes |
| Paste | `Ctrl+V` | Paste copied nodes |
| Delete | `Delete` | Remove selected nodes |
| Select All | `Ctrl+A` | Select all nodes |
| Preferences | - | Open settings dialog |

### View Menu

| Action | Shortcut | Description |
|--------|----------|-------------|
| Zoom In | `Ctrl++` | Zoom into canvas |
| Zoom Out | `Ctrl+-` | Zoom out of canvas |
| Fit to View | `Ctrl+0` | Fit all nodes in view |
| Reset Zoom | `Ctrl+1` | Reset to 100% zoom |
| Toggle Node Palette | - | Show/hide left panel |
| Toggle Properties | - | Show/hide right panel |
| Toggle Log Panel | - | Show/hide bottom panel |

### Workflow Menu

| Action | Shortcut | Description |
|--------|----------|-------------|
| Run | `F5` | Execute the workflow |
| Run All | `Shift+F3` | Run all open workflows |
| Stop | `Shift+F5` | Stop running workflow |
| Pause | - | Pause at current node |
| Resume | - | Continue paused workflow |
| Validate | `Ctrl+F7` | Check workflow for errors |

## Toolbar

[Screenshot: Toolbar with buttons labeled]

The toolbar provides quick access to common actions:

| Button | Icon | Action | Shortcut |
|--------|------|--------|----------|
| New | Document icon | New workflow | `Ctrl+N` |
| Open | Folder icon | Open workflow | `Ctrl+O` |
| Save | Disk icon | Save workflow | `Ctrl+S` |
| Run | Green play | Execute workflow | `F5` |
| Stop | Red square | Stop execution | `Shift+F5` |
| Undo | Left arrow | Undo action | `Ctrl+Z` |
| Redo | Right arrow | Redo action | `Ctrl+Y` |

Additional toolbar buttons may include:
- **Zoom slider** - Adjust canvas zoom
- **Auto-arrange** - Organize nodes automatically
- **Validate** - Check for workflow errors

## Node Palette

[Screenshot: Node Palette panel expanded]

The Node Palette on the left side contains all available automation nodes organized by category.

### Categories

| Category | Description | Example Nodes |
|----------|-------------|---------------|
| **Basic** | Core workflow nodes | Start, End, Comment |
| **Browser** | Web automation | Launch Browser, Click, Type Text |
| **Desktop** | Windows UI automation | Find Element, Click, Send Keys |
| **File** | File operations | Read File, Write File, CSV, JSON |
| **Data** | Data manipulation | List operations, Math, Regex |
| **Control Flow** | Logic and loops | If, For Loop, While, Switch |
| **System** | System operations | Message Box, Input Dialog, Run Command |
| **HTTP** | API requests | HTTP Request, Download File |
| **Database** | SQL operations | Connect, Query, Execute |
| **Email** | Email automation | Send Email, Read Emails |
| **Error Handling** | Error recovery | Try-Catch, Retry, On Error |
| **Variable** | Variable management | Set Variable, Get Variable |

### Using the Node Palette

**To add a node:**
1. Expand a category by clicking its name
2. Find the node you want
3. Drag the node onto the canvas

**To search for nodes:**
1. Use the search box at the top of the palette
2. Type part of the node name
3. Matching nodes appear below
4. Drag the desired node onto canvas

[Screenshot: Searching for "click" in node palette]

## Canvas Area

[Screenshot: Canvas with multiple nodes and connections]

The canvas is your primary workspace for building workflows.

### Canvas Navigation

| Action | How To |
|--------|--------|
| Pan (move view) | Hold middle mouse button and drag, or hold `Space` and drag |
| Zoom in | Scroll wheel up, or `Ctrl++` |
| Zoom out | Scroll wheel down, or `Ctrl+-` |
| Fit all nodes | `Ctrl+0` or double-click empty canvas |
| Select node | Click on the node |
| Multi-select | Hold `Ctrl` and click nodes, or drag a selection box |
| Move node | Drag the node to new position |
| Delete node | Select and press `Delete` |

### Node Anatomy

[Screenshot: Close-up of a single node with parts labeled]

Each node has these elements:

| Part | Description |
|------|-------------|
| Title bar | Node name and collapse button |
| Input port (left triangle) | Receives execution flow |
| Output port (right triangle) | Sends execution flow |
| Data input ports | Receive data from other nodes (circles) |
| Data output ports | Send data to other nodes (circles) |
| Properties | Editable fields within the node |
| Status indicator | Shows running/completed/error state |

### Node Colors

Nodes are color-coded by category:

| Color | Category |
|-------|----------|
| Green | Basic (Start, End) |
| Blue | Browser automation |
| Orange | Desktop automation |
| Purple | Data operations |
| Yellow | Control flow |
| Gray | System utilities |
| Red | Error handling |

### Creating Connections

**Execution connections** (triangular ports):
1. Click the output triangle on the source node
2. Drag to the input triangle on the target node
3. Release to connect

**Data connections** (circular ports):
1. Click the output circle on the source node
2. Drag to the input circle on the target node
3. Release to connect

> **Note:** Data ports are typed. You can only connect compatible types (e.g., STRING to STRING).

**Removing connections:**
- Right-click the connection line and select **Delete**
- Or select the connection and press `Delete`

### Context Menu

Right-click on the canvas to access:

| Option | Description |
|--------|-------------|
| Add Node | Browse and add nodes |
| Paste | Paste copied nodes |
| Select All | Select all nodes |
| Fit View | Fit all nodes in view |

Right-click on a node to access:

| Option | Description |
|--------|-------------|
| Cut | Cut the node |
| Copy | Copy the node |
| Duplicate | Create a copy nearby |
| Delete | Remove the node |
| Collapse | Hide non-essential properties |
| Run from Here | Start execution from this node |

## Properties Panel

[Screenshot: Properties panel for a MessageBox node]

The Properties Panel on the right side lets you configure the selected node.

### Panel Sections

**Basic Properties:**
- Always visible
- Essential configuration for the node to function
- Marked with asterisk (*) if required

**Advanced Properties:**
- Hidden by default
- Click "Advanced" to expand
- Optional fine-tuning settings

### Property Types

| Type | Control | Example |
|------|---------|---------|
| String | Text input | URL, message text |
| Integer | Number input | Timeout, retry count |
| Boolean | Checkbox | Enable/disable options |
| Choice | Dropdown | Browser type, button type |
| File Path | Browse button | File locations |
| Selector | Selector picker | CSS/XPath selectors |

### Using Variables in Properties

You can use variables in text fields using `${variable_name}` syntax:

```
${username}
${file_path}
${results[0]}
```

[Screenshot: Property field with variable reference]

## Bottom Panel

[Screenshot: Bottom panel with tabs]

The bottom panel contains several tabs for monitoring and debugging.

### Log Tab

[Screenshot: Log tab with execution messages]

Shows real-time execution output:

| Log Level | Color | Meaning |
|-----------|-------|---------|
| INFO | White | Normal execution steps |
| SUCCESS | Green | Successful operations |
| WARNING | Yellow | Non-critical issues |
| ERROR | Red | Failed operations |

**Log controls:**
- **Clear** - Remove all log entries
- **Export** - Save log to file
- **Filter** - Show only specific levels

### Variables Tab

[Screenshot: Variables tab showing workflow variables]

Displays all workflow variables and their current values:

| Column | Description |
|--------|-------------|
| Name | Variable name |
| Value | Current value |
| Type | Data type (string, number, etc.) |
| Source | Node that set the variable |

You can:
- Watch variables change during execution
- Edit values manually for testing
- Add new variables

### Breakpoints Tab

[Screenshot: Breakpoints tab]

Lists all debug breakpoints in the workflow:

| Column | Description |
|--------|-------------|
| Node | Node with breakpoint |
| Enabled | Active or disabled |
| Condition | Optional condition expression |

## Keyboard Shortcuts Reference

### File Operations

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New workflow |
| `Ctrl+O` | Open workflow |
| `Ctrl+S` | Save workflow |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+W` | Close current workflow |

### Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+X` | Cut |
| `Ctrl+C` | Copy |
| `Ctrl+V` | Paste |
| `Delete` | Delete selected |
| `Ctrl+A` | Select all |
| `Ctrl+D` | Duplicate selection |

### Execution

| Shortcut | Action |
|----------|--------|
| `F5` | Run workflow |
| `Shift+F5` | Stop workflow |
| `F9` | Toggle breakpoint |
| `F10` | Step over |
| `F11` | Step into |

### Navigation

| Shortcut | Action |
|----------|--------|
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Fit to view |
| `Ctrl+1` | Reset zoom (100%) |
| `Space+Drag` | Pan canvas |
| `Home` | Go to Start node |

### Panels

| Shortcut | Action |
|----------|--------|
| `Ctrl+B` | Toggle Node Palette |
| `Ctrl+P` | Toggle Properties |
| `Ctrl+L` | Toggle Log Panel |

## Tips for Efficient Use

### Organizing Workflows

1. **Left to Right Flow** - Arrange nodes so execution flows left to right
2. **Group Related Nodes** - Keep related operations close together
3. **Use Comments** - Add Comment nodes to explain complex sections
4. **Align Nodes** - Use the alignment tools for a clean layout

### Quick Node Addition

- Press `Tab` on the canvas to open quick search
- Type the node name and press `Enter`
- The node appears at your cursor position

### Node Collapse

- Double-click a node's title to collapse it
- Collapsed nodes show only essential properties
- Useful for large workflows with many nodes

### Selection Tips

- `Ctrl+Click` to add nodes to selection
- Drag a box to select multiple nodes
- Selected nodes can be moved together

## Next Steps

Now that you understand the Canvas interface:

- [First Workflow Tutorial](first-workflow.md) - Build your first automation
- [Quickstart Examples](quickstart-examples.md) - Try practical examples
- Node Reference - Detailed documentation for each node type

---

> **Tip:** Spend time exploring each panel and menu. Familiarity with the interface makes workflow building much faster.

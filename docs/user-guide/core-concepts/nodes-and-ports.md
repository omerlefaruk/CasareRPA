# Nodes and Ports

Nodes are the building blocks of every workflow. Each node performs a specific action, and ports define how nodes connect and exchange data.

## What is a Node?

A node is a single step in your workflow that performs one action. Following the principle of **atomic design**, each node does one thing well:

- A **Click** node clicks an element
- A **Type Text** node enters text into a field
- A **Read File** node loads file contents into memory

This design makes workflows easier to understand, debug, and maintain.

## Node Structure

Every node has three main parts:

```
+---------------------------+
|       Node Header         |  <- Name and icon
+---------------------------+
|  [exec_in]     [exec_out] |  <- Execution ports
+---------------------------+
|  [input1]      [output1]  |  <- Data ports
|  [input2]      [output2]  |
+---------------------------+
|     Properties Panel      |  <- Configuration options
+---------------------------+
```

## Node Categories

CasareRPA includes 400+ nodes organized into categories:

| Category | Purpose | Example Nodes |
|----------|---------|---------------|
| **Browser** | Web automation with Playwright | LaunchBrowser, Click, TypeText, Navigate |
| **Desktop** | Windows desktop automation | FindElement, ClickElement, TypeKeys |
| **Data** | Data transformation | JSON Parse, CSV Read, Transform |
| **File** | File system operations | ReadFile, WriteFile, CopyFile, DeleteFile |
| **HTTP** | API and web requests | HTTP Request, Download File |
| **Email** | Email automation | SendEmail, ReadEmail, IMAP |
| **Database** | Database operations | ExecuteQuery, InsertRow |
| **Control Flow** | Logic and branching | If, Switch, ForLoop, While |
| **Variable** | Variable management | SetVariable, GetVariable |
| **System** | System operations | RunProcess, Clipboard, Dialog |
| **Messaging** | Chat platforms | Telegram, WhatsApp |
| **Google** | Google Workspace | Sheets, Drive, Gmail, Calendar |
| **Error Handling** | Exception management | TryCatch, Retry, Throw |
| **Triggers** | Workflow entry points | Schedule, Webhook, FileWatch |

## Ports

Ports are connection points on nodes. They define what data a node accepts and produces.

### Port Types

There are two categories of ports:

#### Execution Ports

Execution ports control the **order** of node execution:

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Where execution enters the node |
| `exec_out` | Output | Where execution exits after the node completes |

Execution ports appear at the top of the node and are typically colored white.

#### Data Ports

Data ports transfer **values** between nodes:

| Port | Type | Description |
|------|------|-------------|
| Input | Input | Receives data from other nodes |
| Output | Output | Sends data to other nodes |

Data ports appear below execution ports and are colored based on their data type.

### Data Types

Data ports are typed to ensure compatibility:

| Type | Description | Example Values |
|------|-------------|----------------|
| `STRING` | Text data | `"Hello World"`, `"https://example.com"` |
| `INTEGER` | Whole numbers | `42`, `-7`, `0` |
| `FLOAT` | Decimal numbers | `3.14`, `0.001` |
| `BOOLEAN` | True/False | `true`, `false` |
| `LIST` | Array of values | `["a", "b", "c"]`, `[1, 2, 3]` |
| `DICT` | Key-value pairs | `{"name": "John", "age": 30}` |
| `ANY` | Accepts any type | Any value |
| `PAGE` | Browser page | Playwright Page object |
| `ELEMENT` | Web element | Playwright Element handle |
| `DESKTOP_ELEMENT` | Desktop UI element | UIAutomation element |

### Port Colors

Ports use colors to indicate data type, making it easy to see compatible connections:

| Color | Data Type |
|-------|-----------|
| White | Execution (EXEC) |
| Green | String |
| Blue | Integer/Float |
| Red | Boolean |
| Yellow | List |
| Orange | Dict/Object |
| Purple | Browser/Page |
| Gray | Any |

## Connecting Nodes

To connect two nodes:

1. Click and hold on an output port
2. Drag to a compatible input port on another node
3. Release to create the connection

### Connection Rules

- **Execution to execution**: `exec_out` connects to `exec_in`
- **Data to data**: Output data ports connect to input data ports
- **Type compatibility**: The data types must be compatible (or one must be `ANY`)
- **No cycles in execution**: Execution flow cannot form loops (use loop nodes instead)

### Valid Connection Example

```
[LaunchBrowser]          [Navigate]
    [page] ----------------> [page]      # Page object flows
    [exec_out] ------------> [exec_in]   # Execution flows
```

### Invalid Connections

- Connecting `exec_out` to a data input port
- Connecting a STRING output to an INTEGER input (without conversion)
- Connecting an output to another output

## Node Properties

Every node has configurable properties accessed through the Properties Panel on the right side of the canvas.

### Property Types

| Property Type | Description | Example |
|---------------|-------------|---------|
| `STRING` | Single-line text input | URL, selector |
| `TEXT` | Multi-line text area | Script content, template |
| `INTEGER` | Numeric input (whole) | Timeout, retry count |
| `FLOAT` | Numeric input (decimal) | Delay seconds |
| `BOOLEAN` | Checkbox toggle | Headless mode, wait for selector |
| `CHOICE` | Dropdown selection | Browser type, HTTP method |
| `FILE_PATH` | File picker | Input file path |
| `DIRECTORY_PATH` | Folder picker | Output directory |
| `SELECTOR` | Element selector picker | CSS or XPath selector |
| `JSON` | JSON editor | Request body, configuration |

### Essential vs Advanced Properties

Properties marked as **essential** remain visible when the node is collapsed on the canvas. Advanced properties are only visible when you expand the node or open the full properties panel.

### Example: Click Node Properties

| Property | Type | Description |
|----------|------|-------------|
| `selector` | SELECTOR | CSS/XPath selector for the element (essential) |
| `click_type` | CHOICE | single, double, or right click |
| `timeout` | INTEGER | Maximum wait time in milliseconds |
| `force` | BOOLEAN | Click even if element is not visible |
| `modifiers` | STRING | Keyboard modifiers (Ctrl, Shift, Alt) |

## Working with Nodes in Canvas

### Adding Nodes

**From the Node Palette:**
1. Open the Node Palette (left sidebar)
2. Find the node category
3. Drag the node onto the canvas

**From the Context Menu:**
1. Right-click on the canvas
2. Select **Add Node**
3. Browse or search for the node

**Using Quick Add:**
1. Press `Space` or `Tab` on the canvas
2. Type the node name
3. Press `Enter` to add

### Selecting Nodes

- **Single node**: Click on the node
- **Multiple nodes**: `Ctrl+Click` or drag a selection box
- **All nodes**: `Ctrl+A`

### Moving Nodes

- Drag selected nodes to reposition them
- Use arrow keys for precise movement
- Hold `Shift` while dragging for axis-locked movement

### Deleting Nodes

- Select the node and press `Delete`
- Right-click and select **Delete**

### Copying and Pasting

- `Ctrl+C` to copy selected nodes
- `Ctrl+V` to paste
- `Ctrl+D` to duplicate in place

## Common Node Patterns

### Sequential Processing

```
[Start] --> [Read File] --> [Process Data] --> [Write File] --> [End]
```

Each node executes after the previous one completes.

### Conditional Branching

```
              +--> [Send Success Email] --> [End]
[If Node] ---+
              +--> [Send Error Email] --> [End]
```

The If node routes execution based on a condition.

### Loop Processing

```
[For Loop Start] --> [Process Item] --> [For Loop End]
       ^                                      |
       +---------- (automatic loop) ----------+
```

The loop processes each item in a collection.

### Parallel Data

```
                           +--> [Transform A]
[Extract Data] --> [Split] |
                           +--> [Transform B]
```

Data flows to multiple nodes simultaneously (execution still sequential).

## Best Practices

1. **Keep nodes focused**: One action per node
2. **Use meaningful names**: Rename nodes to describe their purpose
3. **Organize visually**: Group related nodes together
4. **Use frames**: Create visual groups for complex workflows
5. **Add comments**: Use Comment nodes to document sections
6. **Test incrementally**: Run and verify each node before building further

## Next Steps

- [Variables](variables.md): Learn how to pass data between nodes using variables
- [Triggers](triggers.md): Understand how workflows are started
- [Workflows](workflows.md): See how nodes combine into complete automations

# Workflows

A workflow is the fundamental building block of automation in CasareRPA. It defines a sequence of actions that the Robot executes to automate a business process.

## What is a Workflow?

A workflow is a visual representation of an automation process. Think of it as a flowchart where each step is a node, and arrows (connections) define the order of execution. When you run a workflow, CasareRPA executes each node in sequence, following the connections you have defined.

Workflows allow you to:
- Automate repetitive tasks without writing code
- Connect different applications and systems
- Process data through multiple transformation steps
- Handle errors and exceptions gracefully
- Reuse common patterns across multiple automations

## Workflow Components

Every workflow consists of two main elements:

### Nodes

Nodes are the individual steps in your workflow. Each node performs a specific action, such as:
- Opening a browser and navigating to a website
- Clicking a button or typing text
- Reading data from a file or database
- Sending an email or message
- Making decisions based on conditions

See the [Nodes and Ports](nodes-and-ports.md) guide for detailed information about node types.

### Connections (Wires)

Connections link nodes together and define:
- **Execution flow**: Which node runs next (via execution ports)
- **Data flow**: How data passes between nodes (via data ports)

Connections appear as wires on the canvas. You create them by dragging from an output port to an input port.

## Execution Flow

Workflows execute in a specific order determined by the execution connections:

```
[Start] --> [Node 1] --> [Node 2] --> [Node 3] --> [End]
```

### Start Node

Every workflow begins with a **Start** node. This special node:
- Has no input ports (nothing comes before it)
- Has one execution output port (`exec_out`)
- Marks the entry point of workflow execution

When you run a workflow, execution begins at the Start node.

### End Node

Workflows terminate at an **End** node. This node:
- Has one execution input port (`exec_in`)
- Has no output ports (nothing comes after it)
- Signals that the workflow has completed

A workflow can have multiple End nodes to handle different completion paths (success, error, etc.).

### Sequential Execution

By default, nodes execute one after another:

1. The Start node fires
2. Control flows to the first connected node
3. That node executes and passes control to the next
4. This continues until an End node is reached

### Branching

Workflows can branch using conditional nodes:

```
              +--> [Yes Branch] --> [End]
[If Node] ---+
              +--> [No Branch] --> [End]
```

The If node evaluates a condition and routes execution down the appropriate path.

### Loops

For repetitive operations, use loop nodes:

```
[For Loop Start] --> [Process Item] --> [For Loop End]
       ^                                      |
       +--------------------------------------+
```

The loop repeats until all items are processed, then continues to the next node after the loop.

## Workflow Files

CasareRPA stores workflows as JSON files with the `.json` extension. These files contain:

| Element | Description |
|---------|-------------|
| `nodes` | Array of node definitions with IDs, types, and configurations |
| `connections` | Array of port connections defining execution and data flow |
| `metadata` | Workflow name, description, version, and timestamps |
| `variables` | Defined workflow variables and their default values |
| `frames` | Visual grouping frames for organizing nodes |

### Example Workflow Structure

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "name": "My Automation",
    "description": "Automates the invoice processing workflow",
    "created": "2024-01-15T10:30:00Z",
    "modified": "2024-01-15T14:22:00Z"
  },
  "nodes": [
    {
      "id": "start_1",
      "type": "StartNode",
      "position": {"x": 100, "y": 300}
    },
    {
      "id": "browser_1",
      "type": "LaunchBrowserNode",
      "position": {"x": 400, "y": 300},
      "config": {
        "browser_type": "chromium",
        "headless": false
      }
    }
  ],
  "connections": [
    {
      "source": "start_1.exec_out",
      "target": "browser_1.exec_in"
    }
  ]
}
```

## Workflow Metadata

Each workflow includes metadata that helps you organize and identify it:

| Property | Description |
|----------|-------------|
| `name` | Display name of the workflow |
| `description` | Detailed description of what the workflow does |
| `created` | Timestamp when the workflow was first created |
| `modified` | Timestamp of the last modification |
| `version` | Schema version for compatibility |
| `author` | Who created or last modified the workflow |
| `tags` | Keywords for categorization and search |

### Best Practices for Workflow Metadata

1. **Use descriptive names**: "Process Monthly Invoices" is better than "Workflow 1"
2. **Write clear descriptions**: Explain what the workflow does and when to use it
3. **Use tags**: Group related workflows with consistent tags

## Working with Workflows in Canvas

The Canvas is the visual editor where you build and edit workflows.

### Creating a New Workflow

1. Open CasareRPA Canvas
2. Select **File > New Workflow** or press `Ctrl+N`
3. A new workflow opens with a Start node already placed

### Opening an Existing Workflow

1. Select **File > Open** or press `Ctrl+O`
2. Navigate to the workflow JSON file
3. Click Open

### Saving Workflows

- **Save**: `Ctrl+S` saves to the current file
- **Save As**: `Ctrl+Shift+S` saves to a new file

### Running Workflows

1. Click the **Play** button in the toolbar or press `F5`
2. The workflow executes starting from the Start node
3. Watch the execution progress as nodes highlight during execution
4. View results in the Log panel

## Subflows

Subflows are reusable workflow components. They allow you to:
- Extract common sequences into reusable modules
- Keep your main workflow clean and readable
- Share automation patterns across projects

To call a subflow, use the **Call Subflow** node and select the subflow to execute.

## Next Steps

- [Nodes and Ports](nodes-and-ports.md): Learn about different node types and how to connect them
- [Variables](variables.md): Understand how to store and use data in workflows
- [Triggers](triggers.md): Discover how to start workflows automatically
- [Execution Modes](execution-modes.md): Explore different ways to run workflows

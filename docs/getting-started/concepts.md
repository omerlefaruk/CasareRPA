# Core Concepts

## Nodes

Nodes are the building blocks of workflows. Each node performs a specific action.

### Node Types

| Type | Description | Example |
|------|-------------|---------|
| Basic | Workflow control | Start, End, Comment |
| Browser | Web automation | Navigate, Click, Fill |
| Desktop | Windows automation | Click Element, Type Text |
| Control Flow | Logic | If, Loop, Switch |
| Data | Data manipulation | Extract Text, Parse JSON |

### Ports

Nodes have ports for connections:

- **exec_in** - Execution input (when this node runs)
- **exec_out** - Execution output (next node to run)
- **Data ports** - Pass data between nodes

## Connections

Connections link nodes together:

- **Execution flow** - Orange lines showing order
- **Data flow** - Colored lines passing values

## Workflows

A workflow is a graph of connected nodes that defines an automation process.

### Execution Order

1. Start from Start node
2. Follow exec connections
3. Execute each node in order
4. End at End node

## Variables

Variables store data during workflow execution:

- Set with SetVariable node
- Access with ${variable_name} syntax
- Scoped to workflow execution

## Next Steps

- [Node Reference](../nodes/index.md)
- [User Guides](../guides/index.md)

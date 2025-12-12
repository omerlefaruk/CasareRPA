# Basic Nodes

Basic nodes provide fundamental workflow building blocks: entry points, exit points, documentation, and logging.

## Overview

| Node | Purpose |
|------|---------|
| [StartNode](#startnode) | Workflow entry point |
| [EndNode](#endnode) | Workflow termination |
| [CommentNode](#commentnode) | Documentation/notes |
| [LogNode](#lognode) | Log messages |
| [RerouteNode](#reroutenode) | Wire organization |

---

## StartNode

Entry point for workflow execution. Every workflow must have exactly one StartNode.

### Description

The StartNode marks where workflow execution begins. It has no inputs and only an execution output that connects to the first action in your workflow.

### Properties

*No configurable properties*

### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_out` | EXEC | Output | Execution flow to first node |

### Example Usage

```
[Start] --exec_out--> [LaunchBrowser] --exec_out--> [GoToURL]
```

### Code Example

```python
from casare_rpa.nodes import StartNode

# StartNode is automatically created when building a workflow
start = StartNode(node_id="start_1")

# Execute returns success and routes to exec_out
result = await start.execute(context)
# result = {"success": True, "data": {"message": "Workflow started"}, "next_nodes": ["exec_out"]}
```

---

## EndNode

Exit point for workflow execution. Workflows can have multiple EndNodes for different termination paths.

### Description

The EndNode marks workflow completion. When reached, it generates an execution summary. Multiple EndNodes can exist for different workflow branches (e.g., success path vs. error path).

### Properties

*No configurable properties*

### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow from previous node |

### Example Usage

```
[ProcessData] --exec_out--> [End]

# Multiple end points
[If] --true--> [SuccessAction] --exec_out--> [End_Success]
     --false-> [ErrorAction] --exec_out--> [End_Error]
```

### Code Example

```python
from casare_rpa.nodes import EndNode

end = EndNode(node_id="end_1")

# Execute returns success with execution summary
result = await end.execute(context)
# result = {"success": True, "data": {"message": "Workflow completed", "summary": {...}}, "next_nodes": []}
```

---

## CommentNode

Non-executable node for documentation and annotations.

### Description

CommentNodes add documentation, notes, or section headers to workflows. They are skipped during execution and don't affect workflow behavior. Use them to:
- Document complex workflow sections
- Add notes for other developers
- Create section headers for organization

### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `comment` | TEXT | No | `""` | Documentation or notes text |

### Ports

*CommentNode has no ports - it exists outside the execution flow*

### Example Usage

Place CommentNodes near related nodes to explain their purpose:

```
[Comment: "User Authentication Flow"]
    |
[LaunchBrowser] --> [GoToURL] --> [TypeText] --> [ClickElement]
```

### Code Example

```python
from casare_rpa.nodes import CommentNode

comment = CommentNode(
    node_id="comment_1",
    comment="This section handles user login with retry logic"
)

# CommentNode is skipped during execution
result = await comment.execute(context)
# result = {"success": True, "data": {"comment": "...", "skipped": True}, "next_nodes": []}
```

---

## LogNode

Explicit logging for debugging and audit trails.

### Description

LogNode outputs messages to the workflow log at configurable severity levels. Messages can include variable placeholders that are resolved at runtime. Useful for:
- Debugging workflow execution
- Creating audit trails
- Monitoring workflow progress

### Properties

| Property | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `message` | STRING | No | `""` | Message to log (supports `{variable}` placeholders) |
| `level` | CHOICE | No | `"critical"` | Log level: debug, info, warning, error, critical |
| `include_timestamp` | BOOLEAN | No | `true` | Include timestamp in message |
| `include_node_id` | BOOLEAN | No | `true` | Include node ID in message |

### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `exec_in` | EXEC | Input | Execution flow |
| `exec_out` | EXEC | Output | Continue execution |
| `message` | STRING | Input | Message override |
| `data` | ANY | Input | Additional data to log |

### Example Usage

```
[GetVariable] --value--> [Log: "User count: {user_count}"]
                            |
                         exec_out
                            |
                     [NextNode]
```

### Variable Placeholders

Use Python format syntax for variable substitution:

```
Message: "Processing user {username} (ID: {user_id})"
```

Variables are resolved from the execution context.

### Code Example

```python
from casare_rpa.nodes import LogNode

log = LogNode(
    node_id="log_1",
    config={
        "message": "Processing item {index} of {total}",
        "level": "info",
        "include_timestamp": True
    }
)

# With context variables set
context.variables["index"] = 5
context.variables["total"] = 100

result = await log.execute(context)
# Logs: "[log_1] Processing item 5 of 100"
```

### Log Levels

| Level | Use Case |
|-------|----------|
| `debug` | Detailed debugging information |
| `info` | General progress information |
| `warning` | Potential issues |
| `error` | Recoverable errors |
| `critical` | Workflow-level critical messages |

---

## RerouteNode

Houdini-style passthrough for organizing wire connections.

### Description

RerouteNode is a visual helper that passes data through unchanged. Use it to:
- Create clean wire routing
- Organize complex connection layouts
- Add clarity to data flow paths

### Properties

*No configurable properties*

### Ports

| Port | Type | Direction | Description |
|------|------|-----------|-------------|
| `in` | ANY | Input | Input data |
| `out` | ANY | Output | Passthrough output |

### Example Usage

```
[ExtractText] --text--> [Reroute] --out--> [WriteFile]
                            |
                            +--> [SendEmail]  (via another reroute)
```

### Code Example

```python
from casare_rpa.nodes import RerouteNode

reroute = RerouteNode(node_id="reroute_1")

# Input value passes through unchanged
reroute.set_input_value("in", "Hello World")
result = await reroute.execute(context)
# Output "out" = "Hello World"
```

---

## Best Practices

### Workflow Structure

```
[Start]
   |
[Comment: "Section 1: Setup"]
   |
[SetupNodes...]
   |
[Comment: "Section 2: Main Logic"]
   |
[MainLogicNodes...]
   |
[Log: "Workflow completed successfully"]
   |
[End]
```

### Logging Strategy

1. **Entry/Exit Logging**: Log at workflow entry and before exit
2. **Critical Steps**: Log before and after important operations
3. **Error Context**: Include relevant variables in error scenarios
4. **Performance**: Use `debug` level for verbose logging

### Comments Best Practices

1. **Section Headers**: Use comments to divide workflow into logical sections
2. **Complex Logic**: Explain non-obvious conditional logic
3. **External Dependencies**: Note external API requirements or credentials
4. **Maintenance Notes**: Document known issues or future improvements

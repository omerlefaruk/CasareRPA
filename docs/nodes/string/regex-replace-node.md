# RegexReplaceNode

Node that replaces text using regex.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.string_nodes`
**File:** `src\casare_rpa\nodes\string_nodes.py:210`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |
| `pattern` | INPUT | No | DataType.STRING |
| `replacement` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `ignore_case` | BOOLEAN | `False` | No | Perform case-insensitive replacement |
| `multiline` | BOOLEAN | `False` | No | ^ and $ match start/end of lines |
| `dotall` | BOOLEAN | `False` | No | . matches newline characters |
| `max_count` | INTEGER | `0` | No | Maximum number of replacements (0 = unlimited) (min: 0) |

## Inheritance

Extends: `BaseNode`

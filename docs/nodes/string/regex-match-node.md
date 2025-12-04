# RegexMatchNode

Node that searches for a regex pattern in a string.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.string_nodes`
**File:** `src\casare_rpa\nodes\string_nodes.py:117`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |
| `pattern` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `match_found` | OUTPUT | DataType.BOOLEAN |
| `first_match` | OUTPUT | DataType.STRING |
| `all_matches` | OUTPUT | DataType.LIST |
| `groups` | OUTPUT | DataType.LIST |
| `match_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `ignore_case` | BOOLEAN | `False` | No | Perform case-insensitive matching |
| `multiline` | BOOLEAN | `False` | No | ^ and $ match start/end of lines |
| `dotall` | BOOLEAN | `False` | No | . matches newline characters |

## Inheritance

Extends: `BaseNode`

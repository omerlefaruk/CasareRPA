# TextExtractNode

Extract text using regex with capture groups.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.text_nodes`
**File:** `src\casare_rpa\nodes\text_nodes.py:1120`


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
| `match` | OUTPUT | DataType.ANY |
| `groups` | OUTPUT | DataType.LIST |
| `found` | OUTPUT | DataType.BOOLEAN |
| `match_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `all_matches` | BOOLEAN | `False` | No | Return all matches instead of just first |
| `ignore_case` | BOOLEAN | `False` | No | Case-insensitive matching |
| `multiline` | BOOLEAN | `False` | No | ^ and $ match line boundaries |
| `dotall` | BOOLEAN | `False` | No | . matches newlines |

## Inheritance

Extends: `BaseNode`

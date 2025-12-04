# TextReplaceNode

Replace occurrences in a string.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.text_nodes`
**File:** `src\casare_rpa\nodes\text_nodes.py:153`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |
| `old_value` | INPUT | No | DataType.STRING |
| `new_value` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |
| `replacements` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `count` | INTEGER | `-1` | No | Maximum number of replacements (-1 for all) |
| `use_regex` | BOOLEAN | `False` | No | Use regex for matching |
| `ignore_case` | BOOLEAN | `False` | No | Case-insensitive matching |
| `multiline` | BOOLEAN | `False` | No | ^ and $ match line boundaries |
| `dotall` | BOOLEAN | `False` | No | . matches newlines |

## Inheritance

Extends: `BaseNode`

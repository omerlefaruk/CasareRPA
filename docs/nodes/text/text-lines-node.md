# TextLinesNode

Split text into lines or join lines into text.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.text_nodes`
**File:** `src\casare_rpa\nodes\text_nodes.py:797`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `input` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.ANY |
| `count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mode` | CHOICE | `split` | No | Split text into lines or join lines into text Choices: split, join |
| `line_separator` | STRING | `
` | No | Line separator for join mode |
| `keep_ends` | BOOLEAN | `False` | No | Keep line endings when splitting |

## Inheritance

Extends: `BaseNode`

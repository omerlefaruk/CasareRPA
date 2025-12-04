# TextPadNode

Pad a string to a certain length.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.text_nodes`
**File:** `src\casare_rpa\nodes\text_nodes.py:420`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |
| `length` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mode` | CHOICE | `left` | No | Pad left, right, or center Choices: left, right, center |
| `fill_char` | STRING | ` ` | No | Character to use for padding |

## Inheritance

Extends: `BaseNode`

# TextCaseNode

Change the case of a string.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.text_nodes`
**File:** `src\casare_rpa\nodes\text_nodes.py:341`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `case` | CHOICE | `lower` | No | Case transformation to apply Choices: upper, lower, title, capitalize, swapcase |

## Inheritance

Extends: `BaseNode`

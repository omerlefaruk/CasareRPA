# TooltipNode

Display a tooltip/notification.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.dialog_nodes`
**File:** `src\casare_rpa\nodes\system\dialog_nodes.py:571`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `title` | INPUT | No | DataType.STRING |
| `message` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `duration` | INTEGER | `3000` | No | Duration to show tooltip (min: 100) |
| `position` | CHOICE | `bottom_right` | No | Screen position for tooltip Choices: bottom_right, bottom_left, top_right, top_left |

## Inheritance

Extends: `BaseNode`

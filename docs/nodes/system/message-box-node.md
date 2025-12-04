# MessageBoxNode

Display a message box dialog.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.system.dialog_nodes`
**File:** `src\casare_rpa\nodes\system\dialog_nodes.py:93`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `message` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | OUTPUT | DataType.STRING |
| `accepted` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `title` | STRING | `Message` | No | Dialog title |
| `message` | STRING | `` | No | Message to display |
| `detailed_text` | STRING | `` | No | Expandable details section |
| `icon_type` | CHOICE | `information` | No | Dialog icon type Choices: information, warning, error, question |
| `buttons` | CHOICE | `ok` | No | Button configuration Choices: ok, ok_cancel, yes_no, yes_no_cancel |
| `default_button` | STRING | `` | No | Which button is focused by default |
| `always_on_top` | BOOLEAN | `True` | No | Keep dialog above other windows |
| `play_sound` | BOOLEAN | `False` | No | Play system sound when dialog appears |
| `auto_close_timeout` | INTEGER | `0` | No | Auto-dismiss after X seconds, 0 to disable (min: 0) |

## Inheritance

Extends: `BaseNode`

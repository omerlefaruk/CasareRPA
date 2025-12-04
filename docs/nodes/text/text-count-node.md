# TextCountNode

Count characters, words, or lines in text.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.text_nodes`
**File:** `src\casare_rpa\nodes\text_nodes.py:935`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `count` | OUTPUT | DataType.INTEGER |
| `characters` | OUTPUT | DataType.INTEGER |
| `words` | OUTPUT | DataType.INTEGER |
| `lines` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `mode` | CHOICE | `characters` | No | Count characters, words, or lines Choices: characters, words, lines |
| `exclude_whitespace` | BOOLEAN | `False` | No | Exclude whitespace from character count |

## Inheritance

Extends: `BaseNode`

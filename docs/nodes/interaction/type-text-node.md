# TypeTextNode

Type text node - types text into an input field.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.interaction_nodes`
**File:** `src\casare_rpa\nodes\interaction_nodes.py:350`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `selector` | SELECTOR | `` | No | CSS or XPath selector for the input element |
| `text` | STRING | `` | No | Text to type into the input field |
| `delay` | INTEGER | `0` | No | Delay between keystrokes in milliseconds (min: 0) |
| `clear_first` | BOOLEAN | `True` | No | Clear field before typing |
| `press_sequentially` | BOOLEAN | `False` | No | Use type() for character-by-character (overrides delay) |
| `press_enter_after` | BOOLEAN | `False` | No | Press Enter key after typing |
| `press_tab_after` | BOOLEAN | `False` | No | Press Tab key after typing |

## Inheritance

Extends: `BrowserBaseNode`

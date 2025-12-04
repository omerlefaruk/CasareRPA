# ClickElementNode

Click element node - clicks on a page element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.interaction_nodes`
**File:** `src\casare_rpa\nodes\interaction_nodes.py:127`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `selector` | SELECTOR | `` | No | CSS or XPath selector for the element to click |
| `button` | CHOICE | `left` | No | Which mouse button to click Choices: left, right, middle |
| `click_count` | INTEGER | `1` | No | Number of clicks (2 for double-click) (min: 1) |
| `delay` | INTEGER | `0` | No | Delay between mousedown and mouseup in milliseconds (min: 0) |
| `position_x` | FLOAT | `-` | No | Click position X offset (optional) |
| `position_y` | FLOAT | `-` | No | Click position Y offset (optional) |
| `modifiers` | MULTI_CHOICE | `[]` | No | Modifier keys to hold during click Choices: Alt, Control, Meta, Shift |
| `trial` | BOOLEAN | `False` | No | Perform actionability checks without clicking |
| `highlight_before_click` | BOOLEAN | `False` | No | Highlight element before clicking |

## Inheritance

Extends: `BrowserBaseNode`

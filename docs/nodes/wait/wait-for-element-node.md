# WaitForElementNode

Wait for element node - waits for an element to appear.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.wait_nodes`
**File:** `src\casare_rpa\nodes\wait_nodes.py:150`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `found` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `selector` | SELECTOR | `` | No | CSS or XPath selector for the element |
| `highlight_on_find` | BOOLEAN | `False` | No | Briefly highlight element when found |

## Inheritance

Extends: `BrowserBaseNode`

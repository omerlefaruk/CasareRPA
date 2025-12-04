# ExtractTextNode

Extract text node - extracts text content from an element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.data_nodes`
**File:** `src\casare_rpa\nodes\data_nodes.py:87`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `text` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `selector` | SELECTOR | `` | No | CSS or XPath selector for the element |
| `variable_name` | STRING | `extracted_text` | No | Name of variable to store result |
| `use_inner_text` | BOOLEAN | `False` | No | True = innerText (visible text), False = textContent (all text) |
| `trim_whitespace` | BOOLEAN | `True` | No | Trim leading/trailing whitespace from result |

## Inheritance

Extends: `BrowserBaseNode`

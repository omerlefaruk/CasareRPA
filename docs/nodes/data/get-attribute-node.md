# GetAttributeNode

Get attribute node - retrieves an attribute value from an element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.data_nodes`
**File:** `src\casare_rpa\nodes\data_nodes.py:233`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `attribute` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `selector` | SELECTOR | `` | No | CSS or XPath selector for the element |
| `attribute` | STRING | `` | No | Attribute name to retrieve (e.g., href, src, data-id) |
| `variable_name` | STRING | `attribute_value` | No | Name of variable to store result |

## Inheritance

Extends: `BrowserBaseNode`

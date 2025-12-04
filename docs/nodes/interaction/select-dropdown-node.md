# SelectDropdownNode

Select dropdown node - selects an option from a dropdown.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.interaction_nodes`
**File:** `src\casare_rpa\nodes\interaction_nodes.py:535`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `value` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `selector` | SELECTOR | `` | No | CSS or XPath selector for the select element |
| `value` | STRING | `` | No | Value, label, or index to select |
| `select_by` | CHOICE | `value` | No | Selection method (value, label, or index) Choices: value, label, index |

## Inheritance

Extends: `BrowserBaseNode`

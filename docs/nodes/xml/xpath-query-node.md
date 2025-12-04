# XPathQueryNode

Query XML using XPath.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.xml_nodes`
**File:** `src\casare_rpa\nodes\xml_nodes.py:301`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `xml_string` | INPUT | No | DataType.STRING |
| `xpath` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `results` | OUTPUT | DataType.LIST |
| `count` | OUTPUT | DataType.INTEGER |
| `first_text` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`

# GetXMLAttributeNode

Get an attribute value from an XML element.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.xml_nodes`
**File:** `src\casare_rpa\nodes\xml_nodes.py:478`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `xml_string` | INPUT | No | DataType.STRING |
| `xpath` | INPUT | No | DataType.STRING |
| `attribute_name` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `value` | OUTPUT | DataType.STRING |
| `found` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`

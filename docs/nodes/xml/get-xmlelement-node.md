# GetXMLElementNode

Get XML element by tag name.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.xml_nodes`
**File:** `src\casare_rpa\nodes\xml_nodes.py:392`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `xml_string` | INPUT | No | DataType.STRING |
| `tag_name` | INPUT | No | DataType.STRING |
| `index` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `tag` | OUTPUT | DataType.STRING |
| `text` | OUTPUT | DataType.STRING |
| `attributes` | OUTPUT | DataType.DICT |
| `child_count` | OUTPUT | DataType.INTEGER |
| `found` | OUTPUT | DataType.BOOLEAN |

## Inheritance

Extends: `BaseNode`

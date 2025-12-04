# WriteXMLFileNode

Write XML to a file.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.xml_nodes`
**File:** `src\casare_rpa\nodes\xml_nodes.py:213`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `file_path` | INPUT | No | DataType.STRING |
| `xml_string` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `file_path` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `encoding` | STRING | `utf-8` | No | File encoding for output |
| `pretty_print` | BOOLEAN | `True` | No | Format output with indentation |
| `xml_declaration` | BOOLEAN | `True` | No | Include <?xml version...?> declaration |

## Inheritance

Extends: `BaseNode`

# JsonToXMLNode

Convert JSON to XML.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.xml_nodes`
**File:** `src\casare_rpa\nodes\xml_nodes.py:671`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `json_data` | INPUT | No | DataType.ANY |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `xml_string` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `root_tag` | STRING | `root` | No | Name of the root XML element |
| `pretty_print` | BOOLEAN | `True` | No | Format XML output with indentation |

## Inheritance

Extends: `BaseNode`

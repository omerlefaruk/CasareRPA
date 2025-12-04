# XMLToJsonNode

Convert XML to JSON.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.xml_nodes`
**File:** `src\casare_rpa\nodes\xml_nodes.py:566`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `xml_string` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `json_data` | OUTPUT | DataType.DICT |
| `json_string` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `include_attributes` | BOOLEAN | `True` | No | Include element attributes in JSON output |
| `text_key` | STRING | `#text` | No | Key name for element text content in JSON |

## Inheritance

Extends: `BaseNode`

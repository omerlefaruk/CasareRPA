# DocsInsertTextNode

Insert text at a specific position in a Google Doc.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_write`
**File:** `src\casare_rpa\nodes\google\docs\docs_write.py:197`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `text` | INPUT | No | DataType.STRING |
| `index` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `text` | TEXT | `` | Yes | Text content to insert |
| `index` | INTEGER | `1` | Yes | Character index position (1-based) where text will be inserted |

## Inheritance

Extends: `DocsBaseNode`

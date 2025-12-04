# DocsInsertTableNode

Insert a table into a Google Doc.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_write`
**File:** `src\casare_rpa\nodes\google\docs\docs_write.py:564`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `rows` | INPUT | No | DataType.INTEGER |
| `columns` | INPUT | No | DataType.INTEGER |
| `index` | INPUT | No | DataType.INTEGER |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `rows` | INTEGER | `3` | Yes | Number of rows in the table |
| `columns` | INTEGER | `3` | Yes | Number of columns in the table |
| `index` | INTEGER | `1` | Yes | Character index position (1-based) where table will be inserted |

## Inheritance

Extends: `DocsBaseNode`

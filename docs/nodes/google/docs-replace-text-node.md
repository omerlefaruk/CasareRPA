# DocsReplaceTextNode

Find and replace text in a Google Doc.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_write`
**File:** `src\casare_rpa\nodes\google\docs\docs_write.py:419`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `search` | INPUT | No | DataType.STRING |
| `replace` | INPUT | No | DataType.STRING |
| `match_case` | INPUT | No | DataType.BOOLEAN |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `replacements_count` | OUTPUT | DataType.INTEGER |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `search` | STRING | `` | Yes | Text to search for in the document |
| `replace` | STRING | `` | Yes | Text to replace matches with |
| `match_case` | BOOLEAN | `True` | No | Whether to match case when searching |

## Inheritance

Extends: `DocsBaseNode`

# DocsCreateDocumentNode

Create a new Google Docs document.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_write`
**File:** `src\casare_rpa\nodes\google\docs\docs_write.py:85`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `access_token` | INPUT | No | DataType.STRING |
| `credential_name` | INPUT | No | DataType.STRING |
| `title` | INPUT | No | DataType.STRING |
| `content` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `document_id` | OUTPUT | DataType.STRING |
| `title` | OUTPUT | DataType.STRING |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `title` | STRING | `` | Yes | Title for the new document |
| `content` | TEXT | `` | No | Optional initial text content for the document |

## Inheritance

Extends: `DocsBaseNode`

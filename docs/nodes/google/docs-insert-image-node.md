# DocsInsertImageNode

Insert an image into a Google Doc.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_write`
**File:** `src\casare_rpa\nodes\google\docs\docs_write.py:712`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `image_url` | INPUT | No | DataType.STRING |
| `index` | INPUT | No | DataType.INTEGER |
| `width` | INPUT | No | DataType.FLOAT |
| `height` | INPUT | No | DataType.FLOAT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `image_url` | STRING | `` | Yes | Public URL of the image to insert |
| `index` | INTEGER | `1` | Yes | Character index position (1-based) where image will be inserted |
| `width` | FLOAT | `0` | No | Optional width in points (0 for auto) |
| `height` | FLOAT | `0` | No | Optional height in points (0 for auto) |

## Inheritance

Extends: `DocsBaseNode`

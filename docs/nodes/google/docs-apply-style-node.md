# DocsApplyStyleNode

Apply text formatting/styling to a range in a Google Doc.

`:material-play: Executable`


**Module:** `casare_rpa.nodes.google.docs.docs_write`
**File:** `src\casare_rpa\nodes\google\docs\docs_write.py:904`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `start_index` | INPUT | No | DataType.INTEGER |
| `end_index` | INPUT | No | DataType.INTEGER |
| `bold` | INPUT | No | DataType.BOOLEAN |
| `italic` | INPUT | No | DataType.BOOLEAN |
| `underline` | INPUT | No | DataType.BOOLEAN |
| `strikethrough` | INPUT | No | DataType.BOOLEAN |
| `font_size` | INPUT | No | DataType.INTEGER |
| `font_family` | INPUT | No | DataType.STRING |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `start_index` | INTEGER | `1` | Yes | Start of text range (1-based, inclusive) |
| `end_index` | INTEGER | `2` | Yes | End of text range (1-based, exclusive) |
| `bold` | BOOLEAN | `False` | No | Apply bold formatting |
| `italic` | BOOLEAN | `False` | No | Apply italic formatting |
| `underline` | BOOLEAN | `False` | No | Apply underline formatting |
| `strikethrough` | BOOLEAN | `False` | No | Apply strikethrough formatting |
| `font_size` | INTEGER | `0` | No | Font size in points (0 to keep current) |
| `font_family` | STRING | `` | No | Font family name (empty to keep current) |

## Inheritance

Extends: `DocsBaseNode`

# Data Processing Guide

Work with data in your workflows.

## Data Types

| Type | Description | Example |
|------|-------------|---------|
| STRING | Text | "hello" |
| INTEGER | Whole number | 42 |
| FLOAT | Decimal number | 3.14 |
| BOOLEAN | True/False | true |
| ARRAY | List of items | [1, 2, 3] |
| OBJECT | Key-value pairs | {"key": "value"} |

## Common Operations

### String Operations

| Node | Purpose |
|------|---------|
| ConcatenateNode | Join strings |
| TextSplitNode | Split by delimiter |
| RegexMatchNode | Pattern matching |
| TextReplaceNode | Find and replace |

### List Operations

| Node | Purpose |
|------|---------|
| ListAppendNode | Add item |
| ListGetItemNode | Get by index |
| ListFilterNode | Filter items |
| ListMapNode | Transform items |

### Dictionary Operations

| Node | Purpose |
|------|---------|
| DictGetNode | Get value by key |
| DictSetNode | Set value |
| DictMergeNode | Merge dicts |

### JSON Operations

| Node | Purpose |
|------|---------|
| JsonParseNode | Parse JSON string |
| DictToJsonNode | Convert to JSON |

## File Operations

| Node | Purpose |
|------|---------|
| ReadFileNode | Read text file |
| WriteFileNode | Write text file |
| ReadCSVNode | Read CSV |
| ReadJSONFileNode | Read JSON file |

## Related Nodes

- [Data Nodes](../nodes/data/index.md)
- [List Nodes](../nodes/list/index.md)
- [Dict Nodes](../nodes/dict/index.md)
- [File Nodes](../nodes/file/index.md)

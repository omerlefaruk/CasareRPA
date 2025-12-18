# Semantic Search Skill

Use the ChromaDB-powered codebase search to find relevant code by meaning.

## MCP Tool

**Tool:** `search_codebase`

```
search_codebase("browser automation click element", top_k=5)
```

## Example Queries

| Query | Finds |
|:---|:---|
| "BaseNode implementation" | Core node base class |
| "HTTP POST request" | HTTP nodes and client |
| "browser automation click" | Browser click nodes |
| "workflow execution" | Execution controller |
| "how to create a node" | Node creation patterns |

## Performance

- First query: ~800ms (model loading)
- Subsequent queries: <100ms

## When to Use

- Finding implementation patterns
- Locating classes/functions by *meaning*
- Exploring unfamiliar code areas
- Understanding how features work

## Maintenance

```bash
# Re-index after major changes
python scripts/index_codebase.py
```

## Best Practices

1. Use natural language queries
2. Start broad, then narrow down
3. Combine with `grep_search` for exact matches
4. Check `top_k` results before diving deeper

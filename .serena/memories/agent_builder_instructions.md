# Agent Instructions - Builder Agent

## Your Role
Write clean, minimal code following KISS and DDD principles.

## Serena Tools (USE AGGRESSIVELY)

### Before Implementing - Research Phase

1. **find_symbol** - Find existing implementations
```python
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="SimilarNode",
    relative_path="src/casare_rpa/nodes/browser/",
    include_body=True  # Get implementation to study
)
```

2. **find_referencing_symbols** - Find how symbols are used
```python
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="BaseNode",
    relative_path="src/casare_rpa/domain/entities/base_node.py"
)
```

3. **get_symbols_overview** - Understand file structure
```python
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/casare_rpa/nodes/browser/__init__.py"
)
```

### During Implementation - Edit Phase

4. **replace_symbol_body** - Replace entire symbol (method, class, function)
```python
mcp__plugin_serena_serena__replace_symbol_body(
    name_path="MyNode/execute",
    relative_path="src/casare_rpa/nodes/my_category/my_node.py",
    body="""async def execute(self, context):
        # Complete implementation
        ...
"""
)
```

5. **replace_content** - Regex-based file edits (for small changes)
```python
mcp__plugin_serena_serena__replace_content(
    relative_path="src/casare_rpa/nodes/my_node.py",
    needle=r"old_pattern.*?end_pattern",
    repl="new content",
    mode="regex"
)
```

6. **insert_after_symbol** - Add code after symbol
```python
mcp__plugin_serena_serena__insert_after_symbol(
    name_path="MyClass/last_method",
    relative_path="src/casare_rpa/my_module.py",
    body="    def new_method(self):\n        ..."
)
```

7. **insert_before_symbol** - Add code before symbol
```python
mcp__plugin_serena_serena__insert_before_symbol(
    name_path="MyClass/first_method",
    relative_path="src/casare_rpa/my_module.py",
    body="    async def new_async_method(self):\n        ..."
)
```

## Workflow

1. **Index-First**: Read relevant `_index.md` files
2. **Find Similar**: Use `find_symbol` to find existing patterns
3. **Study Pattern**: Use `get_symbols_overview` + `read_file`
4. **Implement**: Use symbolic edit tools
5. **Verify**: Check for references with `find_referencing_symbols`

## Edit Strategy

| Change Size | Tool |
|------------|------|
| Entire method/class | `replace_symbol_body` |
| Few lines in method | `replace_content` with regex |
| Add new method | `insert_after_symbol` or `insert_before_symbol` |
| Rename symbol | `rename_symbol` |

## Non-Negotiable Standards

- **Error Handling**: Wrap all external calls in try/except with loguru
- **Type Hints**: Required on all public signatures
- **Async**: Playwright ops must be async
- **Nodes**: Use `@properties()` + `get_parameter()`, never `self.config.get()`
- **UI**: Use `THEME.*` only, no hardcoded colors

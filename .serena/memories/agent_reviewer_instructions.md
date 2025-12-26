# Agent Instructions - Reviewer Agent

## Your Role
Code review gate - APPROVED or ISSUES with file:line references.

## Serena Tools (USE AGGRESSIVELY)

### For Symbol-Level Review

1. **find_referencing_symbols** - Find all uses of changed symbols
```python
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="ChangedClass",
    relative_path="src/casare_rpa/module/file.py",
    max_answer_chars=50000
)
```

2. **find_symbol** - Get symbol definition
```python
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="ClassName/method_name",
    relative_path="src/casare_rpa/module/file.py",
    include_body=True,
    depth=0
)
```

3. **get_symbols_overview** - Full file structure review
```python
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/casare_rpa/nodes/new_node.py",
    depth=2,
    max_answer_chars=50000
)
```

### For Pattern Analysis

4. **search_for_pattern** - Find anti-patterns
```python
# Find hardcoded colors
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})",
    relative_path="src/casare_rpa/presentation/canvas/",
    paths_include_glob="*.py"
)

# Find legacy config.get()
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"self\.config\.get\(",
    relative_path="src/casare_rpa/nodes/"
)
```

## Review Checklist

### Critical Issues (Must Fix)
- [ ] Silent failures (no try/except on external calls)
- [ ] Hardcoded colors (use THEME.*)
- [ ] Legacy patterns (`self.config.get()`)
- [ ] Missing error handling
- [ ] Type safety violations
- [ ] Async/await misuse
- [ ] Domain layer imports from infrastructure/presentation

### Style Issues
- [ ] Line length > 100
- [ ] Missing type hints on public APIs
- [ ] Unused imports/variables
- [ ] Inconsistent naming
- [ ] Missing docstrings on public functions

### Architecture Issues
- [ ] Violated DDD boundaries
- [ ] Missing EventBus usage for domain events
- [ ] Direct HTTP calls instead of UnifiedHttpClient
- [ ] Coupling between layers

## Output Format

```markdown
## Review Result: APPROVED / ISSUES FOUND

### Critical Issues
- file.py:42 - Silent failure: external call without error handling
- file.py:100 - Hardcoded color #FFFFFF, use THEME.background

### Style Issues
- file.py:15 - Missing type hint for `data` parameter

### Architecture Notes
- None / Suggestions...

### Summary
[Brief summary of changes]
```

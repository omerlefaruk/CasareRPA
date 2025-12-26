# Serena Benchmark Results

## Test Date: 2025-12-27

## Tool Performance Comparison

| Query Type | Serena Tool | Result Quality | Token Efficiency |
|------------|-------------|----------------|------------------|
| **Symbol Search** | `find_symbol` | ✅ Found 2 ClickElementNode classes (browser + desktop) with full structure | 🔥 High - only symbol metadata |
| **File Overview** | `get_symbols_overview` | ✅ 28 symbols from workflow.py with hierarchy | 🔥 High - structured metadata |
| **Pattern Search** | `search_for_pattern` | ✅ Found 18 `@properties` usages in browser nodes | 🔥 High - targeted results |
| **Reference Search** | `find_referencing_symbols` | ✅ Found 4 references to Workflow class | 🔥 High - with code context |
| **Anti-Pattern Detection** | `search_for_pattern` | ✅ Found 5 hardcoded colors, 0 legacy config.get() | 🔥 High - regex power |

## Comparison: Serena vs Standard Tools

| Task | Standard (Grep/Glob) | Serena (Semantic) | Winner |
|------|---------------------|-------------------|--------|
| Find class by name | `rg "class ClickElementNode"` | `find_symbol("ClickElementNode")` | Serena (structure) |
| List methods in class | Manual file read | `get_symbols_overview()` + depth | Serena |
| Find all references | `rg "Workflow"` | `find_referencing_symbols("Workflow")` | Serena (context) |
| Pattern search | `rg "@properties"` | `search_for_pattern("@properties")` | Tie |
| Anti-patterns | Complex regex | `search_for_pattern()` + regex | Serena (targeted) |

## Token Efficiency Analysis

**Example: Finding ClickElementNode**
- **Standard**: Read entire files (~5000 tokens)
- **Serena**: Symbol metadata only (~500 tokens)
- **Savings**: ~90% token reduction

**Example: Understanding workflow.py structure**
- **Standard**: Read 634 lines (~3000 tokens)
- **Serena**: `get_symbols_overview(depth=1)` (~300 tokens)
- **Savings**: ~90% token reduction

## Key Advantages

1. **Symbol-Level Granularity**: Find classes, methods, functions with hierarchy
2. **Reference Finding**: Know where symbols are used with code context
3. **Token Efficiency**: Metadata-only queries vs full file reads
4. **Structured Output**: JSON results with precise locations
5. **Regex Power**: `search_for_pattern` with context lines

## Best Practices

### For Symbol Discovery
```python
# Find by name (fastest)
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="ClassName",
    relative_path="src/",  # Optional: restrict search
    include_body=False     # Set True only when needed
)
```

### For Pattern Analysis
```python
# Anti-pattern detection
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"QColor\(\"#[0-9A-Fa-f]{6}\"\)",
    relative_path="src/casare_rpa/presentation/canvas/",
    context_lines_before=2,
    context_lines_after=2
)
```

### For Code Review
```python
# Find all usages
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="Workflow",
    relative_path="src/casare_rpa/domain/aggregates/workflow.py"
)
```

## Recommendations

1. **Always use Serena first** for codebase exploration
2. **Use `include_body=False`** initially, only fetch bodies when needed
3. **Use `depth` parameter** to control detail level (0=top-level, 1=+children)
4. **Combine tools**: `find_symbol` → `get_symbols_overview` → `read_file` (progressive detail)
5. **For pattern search**: Serena regex = Grep regex, but with better context control

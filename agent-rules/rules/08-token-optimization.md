# Token Optimization

Optimize for AI agent efficiency when working with codebase.

## `_index.md` Files

Every major directory should have `_index.md`:

```markdown
# [Module Name] Index

Quick reference for [purpose].

## Directory Structure
| Directory | Purpose | Key Exports |
|-----------|---------|-------------|
| ... | ... | ... |

## Key Files
| File | Contains | Lines |
|------|----------|-------|
| ... | ... | ~XXX |

## Entry Points
\`\`\`python
from module import X, Y, Z
\`\`\`
```

## `__all__` Exports

Every `__init__.py` must have explicit `__all__`:

```python
__all__ = [
    "ClassName",
    "function_name",
    "CONSTANT",
]
```

## Benefits
- Quick module discovery
- Reduced token consumption
- Clear public API
- Better IDE support

## Maintenance
Update `_index.md` when:
- Adding new files/directories
- Changing exports
- Major refactoring

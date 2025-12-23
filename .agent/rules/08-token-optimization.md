---
description: Strategies for optimizing token usage
---

# Token Optimization

## Principles

1. **Read selectively**: Don't dump 5000 line files if you need 10 lines.
2. **Use summaries**: Rely on _index.md files.
3. **Concise output**: Generate code, not essays.
4. **Structured formats**: Prefer tables or short lists; use XML blocks when it reduces tokens.

Example:
```xml
<rules>
  <rule id="flow">Plan -> Review -> Tests -> Implement -> Review -> QA -> Docs</rule>
</rules>
```

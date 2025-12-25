---
name: brain-updater
description: Update .brain/ context files after completing tasks. Templates for activeContext.md and systemPatterns.md updates.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: documentation
---

Update .brain/ files to maintain session context and discovered patterns.

## When to Update

| File | When to Update |
|------|----------------|
| `activeContext.md` | After completing any major task |
| `systemPatterns.md` | When discovering new patterns |
| `projectRules.md` | Rarely (source of truth, don't modify lightly) |
| `plans/{feature}.md` | During planning phase |

## activeContext.md Update Template

```markdown
## Recent Changes
- [Brief description of what was done]
- [Files modified]
- [Key decisions made]

**Files Modified**:
- `path/to/file.py` - What changed

## Active Tasks
- [x] Completed task
- [ ] Pending task

## Decisions Made
| Decision | Rationale | Impact |
|----------|-----------|--------|
| Decision text | Why we decided this | What it affects |
```

### Example Update

```markdown
## Recent Changes
- Implemented HTTPRequestNode for browser automation
- Added async HTTP client with connection pooling
- Created 15 pytest tests covering happy path, errors, edge cases

**Files Modified**:
- `src/casare_rpa/nodes/browser/http_node.py` - New node
- `tests/nodes/browser/test_http_node.py` - Tests
- `.brain/activeContext.md` - This update

## Active Tasks
- [x] Implement HTTPRequestNode
- [x] Create test suite
- [x] Pass code review
- [ ] Document API
```

## systemPatterns.md Update Template

Only add patterns when:
1. A new reusable pattern is discovered
2. An existing pattern is refined
3. A new architectural decision is made

```markdown
## N. Pattern Name

### When to Use
- Describe the situation

### Implementation
\`\`\`python
# Example code
\`\`\`

### Examples in Codebase
- `path/to/file.py:123` - How it's used
```

### Example Pattern Addition

```markdown
## 12. HTTP Client Pattern

### When to Use
- Async HTTP requests in nodes
- Connection pooling for performance

### Implementation
\`\`\`python
from aiohttp import ClientSession

class HTTPResourceManager:
    _session: ClientSession | None = None

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is None:
            cls._session = ClientSession()
        return cls._session

    @classmethod
    async def cleanup(cls):
        if cls._session:
            await cls._session.close()
            cls._session = None
\`\`\`

### Examples in Codebase
- `src/casare_rpa/infrastructure/resources/http_manager.py` - Main implementation
- `src/casare_rpa/nodes/browser/http_node.py:45` - Usage in node
```

## Decision Logging Format

When a significant decision is made, log it:

```markdown
## Decisions Made
| Decision | Rationale | Impact |
|----------|-----------|--------|
| Use aiohttp over httpx | Better connection pooling, smaller footprint | All HTTP nodes use aiohttp |
| Short agent names | Conciseness, faster typing | All agents renamed (no rpa- prefix) |
```

## Usage

After completing a task:

```python
# 1. Read current activeContext.md
# 2. Update the relevant sections
# 3. Write back

# Example agent completion report:
"""
## .brain Update

### activeContext.md Changes
- Added HTTPRequestNode to Recent Changes
- Marked "Implement HTTP node" task as complete

### systemPatterns.md Changes
- Added Section 12: HTTP Client Pattern
- Documented connection pooling approach

### Files Modified
- src/casare_rpa/nodes/browser/http_node.py (NEW)
- tests/nodes/browser/test_http_node.py (NEW)
"""
```

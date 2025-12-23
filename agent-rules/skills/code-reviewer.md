---
skill: code-reviewer
description: Structured code review output format for the reviewer agent. Provides APPROVED/ISSUES format with file:line references.
---

When reviewing code, follow this structured format:

## Review Checklist

### Code Quality
- [ ] Readable, self-documenting code
- [ ] Small, single-responsibility functions (<50 lines)
- [ ] No placeholder code (TODO, pass, ...)
- [ ] Proper error handling with loguru logging
- [ ] Complete type hints on all functions

### Architecture Compliance
- [ ] Follows Clean DDD layers
- [ ] Dependencies flow inward
- [ ] Domain layer has NO external dependencies
- [ ] Nodes have logic + visual wrappers separate

### Async Patterns
- [ ] All Playwright operations are async
- [ ] Consistent async/await usage
- [ ] No blocking calls in async functions

### Testing
- [ ] Tests cover happy path, error cases, edge cases
- [ ] Async tests use @pytest.mark.asyncio
- [ ] External APIs are mocked

### Security
- [ ] No hardcoded secrets
- [ ] Input validation at boundaries
- [ ] Proper credential handling

## Output Format

### If APPROVED

```markdown
## APPROVED

**Summary**: Brief description of what was reviewed

**Quality**: Good | Excellent
**Tests**: Adequate | Comprehensive
**Security**: No issues found

Proceed to QA phase.
```

### If ISSUES Found

```markdown
## ISSUES

### Critical (Must Fix)
1. **src/file.py:123** - Issue description
   - **Why**: Explanation of the problem
   - **Fix**: Suggested solution

### Major (Should Fix)
2. **src/file.py:456** - Issue description
   - **Why**: Explanation
   - **Fix**: Suggestion

### Minor (Consider)
3. **src/file.py:789** - Issue description
   - **Suggestion**: Improvement idea

## Next Steps
1. Return to architect agent to fix Critical and Major issues
2. Re-run quality agent for affected tests
3. Re-submit for review
```

## Severity Definitions

| Severity | Definition | Action |
|----------|------------|--------|
| **Critical** | Breaks functionality, security vulnerability, or violates architecture | Must fix before merge |
| **Major** | Reduces maintainability, missing tests, or poor patterns | Should fix |
| **Minor** | Style, naming, or minor improvements | Consider |

## Review Focus Areas

### For Node Implementations
- Correct port types (DataType enum)
- Proper async/await in execute()
- Error handling returns ExecutionResult
- Logging with loguru

### For Controllers
- Event bus subscriptions
- Graph manipulation patterns
- No direct Qt widget manipulation in business logic

### For Use Cases
- Repository interface usage
- Domain object handling
- Error propagation

### For Domain Entities
- No external dependencies
- Immutable value objects
- Business rule validation

## Usage

```python
# Invoke reviewer agent with this skill
Task(subagent_type="reviewer", prompt="""
Review the following changes for code quality, architecture compliance, and security:
- Files: src/casare_rpa/nodes/browser/http_node.py
- Tests: tests/nodes/browser/test_http_node.py

Output APPROVED or ISSUES using the code-reviewer skill format.
""")
```

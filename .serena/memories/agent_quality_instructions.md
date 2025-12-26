# Agent Instructions - Quality Agent

## Your Role
Testing, validation, and quality assurance.

## Serena Tools (USE AGGRESSIVELY)

### For Test Discovery

1. **find_symbol** - Find existing test patterns
```python
mcp__plugin_serena_serena__find_symbol(
    name_path_pattern="test_*",
    relative_path="tests/nodes/",
    include_body=True
)
```

2. **search_for_pattern** - Find test patterns
```python
mcp__plugin_serena_serena__search_for_pattern(
    substring_pattern=r"@pytest.mark.asyncio\s+async def test_",
    relative_path="tests/",
    context_lines_before=1,
    context_lines_after=10
)
```

3. **find_referencing_symbols** - Find what's tested
```python
mcp__plugin_serena_serena__find_referencing_symbols(
    name_path="MyNode",
    relative_path="src/casare_rpa/nodes/my_node.py"
)
```

### For Code Review

4. **get_symbols_overview** - Review code structure
```python
mcp__plugin_serena_serena__get_symbols_overview(
    relative_path="src/casare_rpa/nodes/new_node.py",
    depth=2  # Include all methods
)
```

## Testing Standards

### Framework: pytest
```bash
pytest tests/ -v
pytest tests/ -v -m "not slow"
pytest tests/ --cov=src/casare_rpa --cov-report=html
```

### Test Organization
| Layer | Strategy | Location |
|-------|----------|----------|
| Domain | No mocks - pure logic | `tests/domain/` |
| Application | Mock infrastructure | `tests/application/` |
| Infrastructure | Mock external services | `tests/infrastructure/` |
| Presentation | Mock Qt pieces | `tests/presentation/` |

### Key Test Patterns

**Domain Tests (Pure Logic)**:
```python
def test_workflow_add_node():
    workflow = Workflow(id=WorkflowId.generate(), name="Test")
    node_id = workflow.add_node("ClickNode", Position(100, 200))
    assert node_id is not None
```

**Node Tests**:
```python
@pytest.mark.asyncio
async def test_execute_success(mock_page):
    result = await node.execute(mock_context)
    assert result["success"] is True
```

## Quality Checklist

Before approving:
- [ ] Tests exist and pass
- [ ] No lint errors: `ruff check src/`
- [ ] Type hints complete: `mypy src/casare_rpa`
- [ ] All external calls have error handling
- [ ] No unused imports/variables
- [ ] Follows project patterns
- [ ] Docstrings for public functions

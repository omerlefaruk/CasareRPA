# AGENTS.md

Machine-readable instructions for AI coding agents working on CasareRPA.

## Project Overview

CasareRPA is an enterprise Windows RPA platform built with:
- **Python 3.12** with strict typing
- **PySide6** for desktop UI
- **Playwright** for browser automation
- **Domain-Driven Design (DDD)** architecture

## Build & Test Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/nodes/ -v
pytest tests/domain/ -v

# Type checking
mypy src/casare_rpa

# Linting
ruff check src/

# Format code
black src/ tests/

# Re-index codebase for semantic search
python scripts/index_codebase.py

# Launch application
python run.py

# Launch Canvas UI
python manage.py canvas
```

## Code Style Guidelines

1. **Type Hints Required**: Every function, method, and variable must have type hints
2. **Async-First**: Use `async/await` for all I/O operations
3. **Docstrings**: All public APIs must have docstrings
4. **Imports**: Use absolute imports, ordered as stdlib → third-party → local
5. **Error Handling**: Wrap all external calls in try/except, log via `loguru`

## Architecture (DDD Layers)

```
src/casare_rpa/
├── domain/          # Business logic, entities, value objects
├── application/     # Use cases, orchestration
├── infrastructure/  # External integrations, database, APIs
├── presentation/    # UI, canvas, widgets
└── nodes/           # Automation nodes (400+)
```

**Rules:**
- Domain layer has NO external dependencies
- Infrastructure implements domain interfaces
- Nodes extend `BaseNode` from domain

## Testing Instructions

- Use `pytest` with fixtures from `conftest.py`
- Test happy path, error cases, and edge cases
- Mock external dependencies in unit tests
- Aim for 80%+ coverage on new code

## Semantic Search

Use the MCP `search_codebase` tool for finding code by meaning:
```
search_codebase("browser automation click", top_k=5)
```

First query: ~800ms | Subsequent: <100ms

## Commit Message Format

```
<type>: <short description>

[optional body]

Types: feat, fix, refactor, test, docs, chore
```

## Security Notes

- Never commit API keys or secrets
- Use environment variables from `.env`
- JWT secrets must be 32+ characters in production
- Validate all user inputs

## Key Files

| Purpose | Location |
|:---|:---|
| Node base class | `src/casare_rpa/domain/entities/base_node.py` |
| Execution controller | `src/casare_rpa/application/execution/` |
| Browser automation | `src/casare_rpa/infrastructure/browser/` |
| Visual nodes | `src/casare_rpa/presentation/canvas/nodes/` |
| Tests | `tests/` |

## Adding New Nodes

When adding a new automation node, you MUST follow these 4 steps:

1.  **Create Backend Node:** Implement the node logic in `src/casare_rpa/nodes/<category>/`.
    - Inherit from appropriate base class (e.g., `BrowserBaseNode`).
    - Use `@properties` decorator for configuration.
    - Implement `async def execute()`.

2.  **Register Backend Node:** Add the class to `src/casare_rpa/nodes/registry_data.py`.
    - Key: Class Name
    - Value: Module path relative to `nodes` package.

3.  **Create Visual Node:** Implement the visual representation in `src/casare_rpa/presentation/canvas/visual_nodes/<category>/`.
    - Inherit from `VisualNode`.
    - Define `__identifier__`, `NODE_NAME`, `NODE_CATEGORY`, and `CASARE_NODE_CLASS`.
    - Implement `setup_ports()` matching backend inputs/outputs.

4.  **Register Visual Node:** Add the class to `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`.
    - Key: Visual Class Name
    - Value: Module path relative to `visual_nodes` package.

## Common Pitfalls & Solutions

| Issue | Symptom | Cause | Solution |
|-------|---------|-------|----------|
| **Silent Visual Node Failure** | Node logic is correct but node doesn't appear in Canvas/Tab menu. | Import error in visual node file (e.g., importing non-existent widget). | Check visual node imports. The lazy loader suppresses import errors. |
| **Invalid Workflow JSON** | `unexpected control character` error on load. | Unescaped newlines in JSON strings (e.g., scripts). | Use `\n` literal for newlines. Ensure JSON string values are valid one-liners. |
| **Circular Dependency** | `CIRCULAR_DEPENDENCY` validation error. | Using `IfNode` + connection to loop back. | Use `WhileLoop` or `ForLoop` nodes which handle loops internally without static graph cycles. |
| **Event Instantiation** | `unexpected keyword argument` error. | Passing raw objects (`page`) to Domain Events. | Pass only serializable data (`url`, `title`) matching event dataclass definition. |
| **Widget Imports** | `ImportError: cannot import name ...` | Trying to import specific widgets like `NodeTextWidget` that don't exist. | Use `@properties` for auto-generation or factory functions like `create_variable_text_widget`. |

## Skills Reference

Skills are located in `agent-rules/skills/`:
- `semantic-search.md` - Codebase search via ChromaDB
- `error-diagnosis.md` - Debugging methodology
- `performance-optimizer.md` - Bottleneck identification
- `api-integration.md` - HTTP client patterns
- `node-creator.md` - Node creation workflow
- `ui-widget.md` - PySide6 widget templates
- `import-fixer.md` - Import organization
- `test-generator.md` - Test file generation

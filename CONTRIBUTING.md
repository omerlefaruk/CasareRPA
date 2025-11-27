# Contributing to CasareRPA

Thank you for your interest in contributing to CasareRPA! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/CasareRPA.git
   cd CasareRPA
   ```
3. **Create a virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
4. **Install in development mode**:
   ```bash
   pip install -e .[dev]
   playwright install chromium
   ```

## Development Workflow

### 1. Create a Branch

Create a feature branch from `main`:
```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Test additions/updates

### 2. Make Your Changes

- Write clear, concise commit messages
- Follow the existing code style (PEP 8, type hints required)
- Add tests for new functionality
- Update documentation as needed

### 3. Code Quality

Before committing, ensure your code passes quality checks:

```bash
# Format code
black src/ tests/

# Type checking
mypy src/

# Linting
ruff check src/ tests/

# Run tests
pytest tests/ -v
```

### 4. Commit Your Changes

Use conventional commit messages:
```
feat: Add email automation nodes
fix: Handle browser disconnection in navigation
refactor: Extract control flow logic from WorkflowRunner
docs: Update README with installation instructions
test: Add chaos tests for browser failures
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- **Clear title** describing the change
- **Description** explaining what and why
- **Screenshots** (if UI changes)
- **Test plan** describing how to verify the changes

## Code Style Guidelines

### Python Code

- Follow **PEP 8** style guide
- Use **type hints** for all functions and methods
- Maximum line length: **100 characters** (configured in black)
- Use **docstrings** for all public modules, classes, and functions
- Prefer **composition over inheritance**
- Keep functions **small and focused** (<50 lines preferred)

Example:
```python
from typing import Optional
from loguru import logger

class NodeExecutor:
    """
    Executes individual workflow nodes with proper error handling.

    This class handles node execution in isolation, managing success/failure
    results and emitting execution events.
    """

    async def execute_node(
        self,
        node_id: str,
        context: ExecutionContext
    ) -> ExecutionResult:
        """
        Execute a single node and return the result.

        Args:
            node_id: Unique identifier of the node to execute
            context: Execution context with variables and resources

        Returns:
            ExecutionResult containing success status and output data

        Raises:
            NodeExecutionError: If node execution fails critically
        """
        logger.info(f"Executing node: {node_id}")
        # Implementation here...
```

### Architecture

Follow **Clean Architecture** principles:

```
domain/          # Pure business logic, no infrastructure dependencies
  ├── entities/    # Core business objects
  ├── services/    # Domain services
  └── ports/       # Interfaces (dependency inversion)

application/     # Use cases and application services
  ├── use_cases/   # Application-specific business rules
  ├── services/    # Application services (retry, events)
  └── dependency_injection/

infrastructure/  # Framework and external dependencies
  ├── execution/   # Concrete implementations
  ├── persistence/ # File I/O, database
  └── adapters/    # External library wrappers

presentation/    # UI layer
  └── canvas/      # Qt visual editor
```

**Rules**:
- Domain layer: ZERO infrastructure imports
- Application layer: Depends only on domain
- Infrastructure: Implements domain ports
- Presentation: Uses application use cases

## Adding New Features

### Adding a New Node

1. Create node logic in `src/casare_rpa/nodes/{category}_nodes.py`:
   ```python
   class MyNewNode(BaseNode):
       NODE_NAME = "My New Node"
       NODE_CATEGORY = "Utility"

       def __init__(self, node_id: str):
           super().__init__(node_id)
           self.add_port("input", PortType.IN)
           self.add_port("output", PortType.OUT)

       async def execute(self, context: ExecutionContext) -> ExecutionResult:
           # Implementation
           return {"success": True, "data": {}}
   ```

2. Create visual node in `src/casare_rpa/presentation/canvas/visual_nodes/{category}/`:
   ```python
   from casare_rpa.canvas.visual_nodes.base_visual_node import VisualNode

   class VisualMyNewNode(VisualNode):
       NODE_NAME = "My New Node"
       NODE_CATEGORY = "Utility"
       NODE_IDENTIFIER = "utility.my_new_node"
   ```

3. Add tests in `tests/test_{category}_nodes.py`:
   ```python
   @pytest.mark.asyncio
   async def test_my_new_node(execution_context):
       node = MyNewNode("test_node")
       result = await node.execute(execution_context)
       assert result["success"] is True
   ```

4. Update documentation in `docs/nodes/{category}.md`

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component interaction tests
├── e2e/           # End-to-end workflow tests
└── chaos/         # Failure scenario tests
```

### Writing Tests

- Use **pytest** and **pytest-asyncio**
- Follow **AAA pattern** (Arrange-Act-Assert)
- Use **fixtures** for common setup
- Mock external dependencies (Playwright, UIAutomation)
- Test both **success and failure** scenarios

Example:
```python
import pytest
from casare_rpa.nodes.browser_nodes import ClickNode
from casare_rpa.core.execution_context import ExecutionContext

@pytest.mark.asyncio
async def test_click_node_success(execution_context, mock_page):
    """Test ClickNode successfully clicks an element."""
    # Arrange
    node = ClickNode("test_click")
    node.set_input_value("selector", "button#submit")
    execution_context.active_page = mock_page

    # Act
    result = await node.execute(execution_context)

    # Assert
    assert result["success"] is True
    mock_page.click.assert_called_once_with("button#submit")
```

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No unnecessary dependencies added
- [ ] Commit messages are clear and descriptive

### PR Description Template

```markdown
## Description
Brief description of the changes

## Motivation
Why is this change needed?

## Changes Made
- List of key changes
- Another change

## Testing
How was this tested?
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing performed

## Screenshots (if applicable)
Add screenshots for UI changes

## Breaking Changes
List any breaking changes and migration path
```

## Need Help?

- **Questions**: Open a GitHub Discussion
- **Bugs**: Create an Issue with bug report template
- **Feature Requests**: Create an Issue with feature request template
- **Security**: See [SECURITY.md](SECURITY.md) for reporting vulnerabilities

## Code of Conduct

Please note we have a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to CasareRPA! 🚀

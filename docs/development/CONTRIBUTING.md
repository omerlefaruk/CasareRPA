# Contributing to CasareRPA

Thank you for your interest in contributing to CasareRPA! This guide covers development guidelines, coding standards, and the contribution process.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Environment](#development-environment)
3. [Architecture Guidelines](#architecture-guidelines)
4. [Coding Standards](#coding-standards)
5. [Pull Request Process](#pull-request-process)
6. [Testing Requirements](#testing-requirements)
7. [Documentation](#documentation)

---

## Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- Windows 10/11 (for full testing)
- Visual Studio Code (recommended)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/CasareRPA.git
cd CasareRPA

# Add upstream remote
git remote add upstream https://github.com/omerlefaruk/CasareRPA.git
```

### Setup Development Environment

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install in development mode
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Install pre-commit hooks
pre-commit install
```

---

## Development Environment

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "redhat.vscode-yaml"
  ]
}
```

### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

### Environment Variables

Create `.env` file for development:

```env
# Supabase (optional for local development)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
```

---

## Architecture Guidelines

### Clean Architecture Principles

CasareRPA follows Clean Architecture (DDD). Understand the layer dependencies:

```
Presentation -> Application -> Domain <- Infrastructure
```

#### Layer Rules

| Layer | Can Depend On | Cannot Depend On |
|-------|---------------|------------------|
| Domain | Nothing | All other layers |
| Application | Domain | Presentation, Infrastructure |
| Infrastructure | Domain | Presentation, Application |
| Presentation | Application | Domain directly |

### Adding New Features

#### 1. Define Domain Entities First

```python
# src/casare_rpa/domain/entities/new_feature.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class NewEntity:
    """Domain entity for new feature."""
    id: str
    name: str
    status: str

    def validate(self) -> bool:
        """Domain validation logic."""
        return bool(self.name)
```

#### 2. Create Application Use Cases

```python
# src/casare_rpa/application/use_cases/new_feature.py
from typing import Protocol
from ..domain.entities.new_feature import NewEntity

class NewFeatureRepository(Protocol):
    """Repository interface (defined in application layer)."""
    async def save(self, entity: NewEntity) -> None: ...
    async def find_by_id(self, id: str) -> Optional[NewEntity]: ...

class CreateNewFeatureUseCase:
    """Application use case."""

    def __init__(self, repository: NewFeatureRepository):
        self._repository = repository

    async def execute(self, name: str) -> NewEntity:
        entity = NewEntity(
            id=generate_id(),
            name=name,
            status="active"
        )
        if not entity.validate():
            raise ValueError("Invalid entity")
        await self._repository.save(entity)
        return entity
```

#### 3. Implement Infrastructure

```python
# src/casare_rpa/infrastructure/persistence/new_feature_repository.py
from ...application.use_cases.new_feature import NewFeatureRepository
from ...domain.entities.new_feature import NewEntity

class SupabaseNewFeatureRepository(NewFeatureRepository):
    """Infrastructure implementation."""

    def __init__(self, client):
        self._client = client

    async def save(self, entity: NewEntity) -> None:
        await self._client.table("new_features").insert({
            "id": entity.id,
            "name": entity.name,
            "status": entity.status
        }).execute()
```

#### 4. Create Presentation Components

```python
# src/casare_rpa/presentation/canvas/controllers/new_feature_controller.py
from ...application.use_cases.new_feature import CreateNewFeatureUseCase

class NewFeatureController:
    """Presentation controller."""

    def __init__(self, use_case: CreateNewFeatureUseCase):
        self._use_case = use_case

    async def create(self, name: str) -> dict:
        entity = await self._use_case.execute(name)
        return {"id": entity.id, "name": entity.name}
```

### Adding New Nodes

#### 1. Create Logic Node

```python
# src/casare_rpa/nodes/browser/new_action.py
from typing import Any, Dict
from loguru import logger
from ..base import BaseNode, NodeResult

class NewActionNode(BaseNode):
    """
    New browser action node.

    Performs [description of action].
    """

    # Node metadata
    NODE_NAME = "New Action"
    NODE_CATEGORY = "Browser"
    NODE_DESCRIPTION = "Performs a new action"

    # Property definitions
    PROPERTIES = {
        "selector": {
            "type": "string",
            "required": True,
            "description": "CSS selector for target element"
        },
        "timeout": {
            "type": "integer",
            "default": 30000,
            "description": "Timeout in milliseconds"
        }
    }

    async def execute(self, context: Dict[str, Any]) -> NodeResult:
        """
        Execute the action.

        Args:
            context: Execution context with variables and page

        Returns:
            NodeResult with success/failure status
        """
        selector = self.get_property("selector")
        timeout = self.get_property("timeout", 30000)

        try:
            page = context.get("page")
            if not page:
                return NodeResult(
                    success=False,
                    error="No page available in context"
                )

            # Perform action
            await page.wait_for_selector(selector, timeout=timeout)
            # ... implement action ...

            logger.info(f"New action completed on '{selector}'")
            return NodeResult(success=True, data={"selector": selector})

        except Exception as e:
            logger.error(f"New action failed: {e}")
            return NodeResult(success=False, error=str(e))
```

#### 2. Create Visual Node Wrapper

```python
# src/casare_rpa/presentation/canvas/visual_nodes/browser/new_action_visual.py
from NodeGraphQt import BaseNode as NgBaseNode
from ....nodes.browser.new_action import NewActionNode

class NewActionVisualNode(NgBaseNode):
    """Visual node for NewActionNode."""

    # NodeGraphQt metadata
    __identifier__ = "casare.browser"
    NODE_NAME = "New Action"

    def __init__(self):
        super().__init__()
        self._logic_node = NewActionNode()

        # Create ports
        self.add_input("input", color=(255, 255, 255))
        self.add_output("output", color=(255, 255, 255))
        self.add_output("error", color=(255, 100, 100))

        # Create property widgets
        self.add_text_input("selector", "Selector", text="")
        self.add_text_input("timeout", "Timeout (ms)", text="30000")

    @property
    def logic_node(self) -> NewActionNode:
        return self._logic_node

    def get_properties(self) -> dict:
        return {
            "selector": self.get_property("selector"),
            "timeout": int(self.get_property("timeout") or 30000)
        }
```

#### 3. Register the Node

```python
# src/casare_rpa/presentation/canvas/visual_nodes/browser/__init__.py
from .new_action_visual import NewActionVisualNode

BROWSER_NODES = [
    # ... existing nodes ...
    NewActionVisualNode,
]
```

---

## Coding Standards

### Type Hints (Required)

All functions must have complete type hints:

```python
# Good
def process_job(
    job_id: str,
    workflow: Dict[str, Any],
    timeout: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """Process a job and return (success, error_message)."""
    ...

# Bad - missing type hints
def process_job(job_id, workflow, timeout=None):
    ...
```

### Docstrings (Required for Public Functions)

Use Google-style docstrings:

```python
def submit_job(
    workflow_id: str,
    priority: JobPriority = JobPriority.NORMAL,
    params: Optional[Dict[str, Any]] = None
) -> Job:
    """
    Submit a job for execution.

    Args:
        workflow_id: Unique identifier of the workflow to execute.
        priority: Job priority level. Defaults to NORMAL.
        params: Optional parameters to pass to the workflow.

    Returns:
        The created Job instance.

    Raises:
        ValueError: If workflow_id is invalid.
        WorkflowNotFoundError: If workflow does not exist.

    Example:
        >>> job = await submit_job("wf-123", JobPriority.HIGH)
        >>> print(job.id)
    """
    ...
```

### Error Handling (Critical)

**All external interactions must have error handling:**

```python
# Good - comprehensive error handling
async def click_element(page: Page, selector: str) -> bool:
    """Click an element with proper error handling."""
    try:
        await page.wait_for_selector(selector, timeout=30000)
        await page.click(selector)
        logger.info(f"Clicked element: {selector}")
        return True

    except TimeoutError:
        logger.warning(
            f"Element not found within timeout: '{selector}'. "
            f"Page URL: {page.url}. Possible causes: page not loaded, "
            f"selector changed, element not visible."
        )
        return False

    except Exception as e:
        logger.error(
            f"Failed to click element '{selector}': {e}. "
            f"Context: page={page.url}, selector={selector}. "
            f"Recovery: will retry with extended timeout."
        )
        raise

# Bad - no error handling
async def click_element(page, selector):
    await page.click(selector)  # Will crash on any failure
```

### Async/Await (Consistency Required)

```python
# Good - consistent async usage
async def execute_workflow(workflow_json: str) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        try:
            await page.goto(url)
            result = await process_page(page)
            return result
        finally:
            await browser.close()

# Bad - mixing sync and async
def execute_workflow(workflow_json):
    p = sync_playwright().start()  # Mixing patterns
    ...
```

### Logging (Use Loguru)

```python
from loguru import logger

# Good - contextual logging
logger.info(f"Job {job_id[:8]} started on robot {robot_name}")
logger.warning(f"Retry {attempt}/3 for operation: {operation_name}")
logger.error(f"Failed to connect to {host}:{port}: {error}. Retrying in {delay}s.")

# Bad - generic or no logging
print("Error occurred")  # Don't use print
logger.error("Error")  # Too generic
```

### Code Completeness (No Placeholders)

```python
# Good - complete implementation
def calculate_next_run(frequency: ScheduleFrequency, cron: str) -> datetime:
    if frequency == ScheduleFrequency.DAILY:
        return datetime.now() + timedelta(days=1)
    elif frequency == ScheduleFrequency.CRON:
        return croniter(cron).get_next(datetime)
    else:
        raise ValueError(f"Unsupported frequency: {frequency}")

# Bad - placeholder code
def calculate_next_run(frequency, cron):
    # TODO: implement this
    pass
```

### Code Formatting

We use Black and Ruff:

```powershell
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Fix linting issues
ruff check --fix src/ tests/
```

### Import Order

```python
# 1. Standard library
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

# 2. Third-party
from loguru import logger
from pydantic import BaseModel
import orjson

# 3. Local application
from casare_rpa.domain.entities import Job
from casare_rpa.application.use_cases import ExecuteWorkflow
from .utils import helper_function
```

---

## Pull Request Process

### Branch Naming

```
feature/description-of-feature
fix/description-of-fix
docs/description-of-docs
refactor/description-of-refactor
```

### Commit Messages

Use conventional commits:

```
feat: add new browser action node
fix: resolve connection timeout on slow networks
docs: update API reference for webhooks
refactor: extract job state machine to separate module
test: add integration tests for scheduler
chore: update dependencies
```

### PR Checklist

Before submitting a PR:

- [ ] Code follows architecture guidelines
- [ ] All functions have type hints
- [ ] Public functions have docstrings
- [ ] Error handling is comprehensive
- [ ] Tests are added/updated
- [ ] Documentation is updated
- [ ] `black` and `ruff` pass
- [ ] All tests pass
- [ ] No TODO/FIXME/placeholder code

### PR Template

```markdown
## Summary
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring

## Testing
How was this tested?

## Checklist
- [ ] Code follows project guidelines
- [ ] Tests added/updated
- [ ] Documentation updated

## Screenshots (if applicable)
```

### Review Process

1. **Automated checks** - CI must pass
2. **Code review** - At least one approval required
3. **Testing** - Manual testing for UI changes
4. **Merge** - Squash and merge to main

---

## Testing Requirements

### Test Structure

```
tests/
    unit/
        domain/
        application/
        infrastructure/
    integration/
        orchestrator/
        robot/
    e2e/
        workflows/
```

### Writing Tests

```python
# tests/unit/application/test_execute_workflow.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase

class TestExecuteWorkflow:
    """Tests for ExecuteWorkflowUseCase."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        repo = MagicMock()
        repo.find_by_id = AsyncMock(return_value=sample_workflow())
        return repo

    @pytest.mark.asyncio
    async def test_execute_valid_workflow(self, mock_repository):
        """Test executing a valid workflow."""
        use_case = ExecuteWorkflowUseCase(mock_repository)
        result = await use_case.execute("workflow-123")

        assert result.success
        mock_repository.find_by_id.assert_called_once_with("workflow-123")

    @pytest.mark.asyncio
    async def test_execute_invalid_workflow_raises(self, mock_repository):
        """Test that invalid workflow raises ValueError."""
        mock_repository.find_by_id = AsyncMock(return_value=None)
        use_case = ExecuteWorkflowUseCase(mock_repository)

        with pytest.raises(ValueError, match="Workflow not found"):
            await use_case.execute("invalid-id")
```

### Running Tests

```powershell
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src/casare_rpa --cov-report=html

# Run specific test file
pytest tests/unit/application/test_execute_workflow.py -v

# Run tests matching pattern
pytest tests/ -k "test_execute" -v
```

### Coverage Requirements

- Minimum 80% coverage for new code
- Critical paths (error handling, security) require 100%

---

## Documentation

### When to Update Docs

- New features: Update user guide
- API changes: Update API reference
- Architecture changes: Update architecture docs
- Bug fixes: Update troubleshooting if applicable

### Documentation Style

- Use clear, concise language
- Include code examples
- Use mermaid for diagrams
- Keep documentation close to code

### Generating API Docs

```powershell
# Generate API documentation
pdoc --html src/casare_rpa -o docs/api/generated
```

---

## Questions?

- Check existing issues and discussions
- Open a new issue for questions
- Tag maintainers for urgent matters

Thank you for contributing to CasareRPA!

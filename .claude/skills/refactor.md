---
skill: refactor
description: Safe code refactoring following DDD principles with MCP codebase search and web research for patterns.
---

## MCP-First Refactoring Workflow

**Always use MCP servers in this order:**

1. **codebase** - Find current implementation patterns
   ```python
   search_codebase("class Extract Method pattern", top_k=10)
   ```

2. **sequential-thinking** - Plan refactoring steps
   ```python
   think_step_by_step("""
   Analyze current code:
   1. Identify code smells
   2. Find existing patterns in codebase
   3. Plan refactoring steps
   4. Verify no breaking changes
   """)
   ```

3. **git** - Check impact of changes
   ```python
   git_diff("HEAD~10..HEAD", file_pattern="**/*.py")
   git_log("-20", "--oneline")
   ```

4. **exa** - Research best practices
   ```python
   websearch("Python DDD refactoring patterns 2025", numResults=5)
   websearch("extract method design pattern Python", numResults=3)
   ```

5. **ref** - Library documentation
   ```python
   search_documentation("abc", library="python")
   ```

6. **filesystem** - Read files for analysis
   ```python
   read_file("src/casare_rpa/presentation/canvas/main_window.py")
   ```

## Refactoring Techniques

### 1. Extract Method

**When:**
- Function is too long (>50 lines)
- Repeated logic in multiple places
- Complex conditional logic

**MCP-Based Process:**
```python
# Step 1: Search for similar patterns
search_codebase("extract method refactoring pattern", top_k=10)

# Step 2: Read current implementation
read_file(f"{file_path}:{line_number - 50}:{line_number + 100}")

# Step 3: Identify extraction candidates
search_codebase(f"def {function_name}(", top_k=5)

# Step 4: Research best practices
websearch("Python extract method refactoring DDD", numResults=3)

# Step 5: Plan extraction
# - Create new private method
# - Replace inline code with call
# - Preserve behavior exactly
```

**Before/After:**
```python
# BEFORE: Long function
def process_workflow(workflow: Workflow):
    # 50 lines of validation
    # 30 lines of processing
    # 20 lines of result handling

# AFTER: Extracted methods
def process_workflow(workflow: Workflow):
    validated = self._validate_workflow(workflow)
    result = self._execute_workflow(validated)
    return self._handle_result(result)

def _validate_workflow(self, workflow: Workflow) -> Workflow:
    # Validation logic

def _execute_workflow(self, workflow: Workflow) -> Result:
    # Processing logic

def _handle_result(self, result: Result) -> dict:
    # Result handling
```

### 2. Introduce Design Pattern

**Common Patterns in CasareRPA:**
- Factory - Create objects (nodes, resources)
- Strategy - Pluggable algorithms
- Observer - Event bus subscriptions
- Repository - Data access abstraction

**MCP-Based Process:**
```python
# Step 1: Search for pattern examples
search_codebase("factory pattern", top_k=10)
search_codebase("strategy pattern", top_k=10)
search_codebase("observer pattern", top_k=10)

# Step 2: Research pattern implementation
websearch("Python factory pattern DDD implementation", numResults=5)

# Step 3: Read current code
read_file(f"{file_path}:{line_number - 30}:{line_number + 100}")

# Step 4: Apply pattern with ref tool
# Plan transformation
# Test changes
# Apply to codebase
```

**Factory Pattern Example:**
```python
# BEFORE: Direct instantiation
if node_type == "browser_click":
    node = ClickElementNode()
elif node_type == "browser_type":
    node = TypeTextElementNode()

# AFTER: Factory pattern
class NodeFactory:
    @classmethod
    def create(cls, node_type: str, properties: dict) -> BaseNode:
        # Search for node classes
        node_classes = {
            "browser_click": ClickElementNode,
            "browser_type": TypeTextElementNode,
        }
        return node_classes[node_type](**properties)

# Usage
node = NodeFactory.create(node_type, properties)
```

### 3. Extract Class/Module

**When:**
- God object with too many responsibilities
- Related functionality scattered
- Circular dependencies

**MCP-Based Process:**
```python
# Step 1: Identify dependencies
search_codebase(f"from {module_name}", top_k=20)

# Step 2: Check circular deps
search_codebase("circular import", top_k=10)
git_diff("HEAD~20..HEAD")

# Step 3: Plan extraction
# - Create new module
# - Move related code
# - Update imports
# - Add exports

# Step 4: Verify impact
git_status()
git_diff("HEAD")
```

### 4. Replace Inheritance with Composition

**When:**
- Deep inheritance hierarchies
- Fragile base classes
- Multiple inheritance abuse

**MCP-Based Process:**
```python
# Step 1: Search for inheritance usage
search_codebase("class.*Node.*BaseNode", top_k=20)

# Step 2: Analyze hierarchy
websearch("Python composition over inheritance DDD", numResults=5)

# Step 3: Identify composition opportunities
search_codebase("def __init__.*Node", top_k=10)

# Step 4: Refactor to composition
# - Use dependency injection
# - Prefer composition to inheritance
# - Mixins for shared behavior
```

**Before/After:**
```python
# BEFORE: Deep inheritance
class BrowserNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.browser = None
        self.page = None
        self.context = None

class ClickNode(BrowserNode):
    def __init__(self):
        super().__init__()
        self.selector = None

class TypeNode(BrowserNode):
    def __init__(self):
        super().__init__()
        self.text = None

# AFTER: Composition
class BrowserNode(BaseNode):
    def __init__(self, browser_provider: BrowserProvider):
        super().__init__()
        self.browser = browser_provider.get_browser()

class ClickNode(BaseNode):
    def __init__(self, browser_provider: BrowserProvider):
        super().__init__()
        self.browser = browser_provider.get_browser()

class TypeNode(BaseNode):
    def __init__(self, browser_provider: BrowserProvider):
        super().__init__()
        self.browser = browser_provider.get_browser()
```

## CasareRPA-Specific Refactorings

### 1. Controller Extraction

**Problem:** MainWindow is too large (1000+ lines)

**MCP-Based Process:**
```python
# Step 1: Analyze current structure
read_file("src/casare_rpa/presentation/canvas/main_window.py")
search_codebase("class MainWindow", top_k=5)

# Step 2: Identify responsibilities
search_codebase("def on_", top_k=50)  # Event handlers

# Step 3: Plan controller creation
websearch("Python MVC controller pattern PySide6", numResults=5)

# Step 4: Extract controllers
# - NodeController
# - GraphController
# - PropertyController
# - VariableController
```

### 2. Event Bus Implementation

**Problem:** Tight coupling between components

**MCP-Based Process:**
```python
# Step 1: Search for event patterns
search_codebase("class.*Event", top_k=20)
search_codebase("emit", top_k=30)
search_codebase("connect", top_k=30)

# Step 2: Research event bus patterns
websearch("Python observer pattern event bus implementation", numResults=5)

# Step 3: Implement typed events
search_codebase("TypedEvent", top_k=5)
```

### 3. Resource Manager Pattern

**Problem:** Resource leaks, inconsistent cleanup

**MCP-Based Process:**
```python
# Step 1: Search for resource usage
search_codebase("async with.*context", top_k=20)
search_codebase("class.*Manager", top_k=15)

# Step 2: Identify cleanup patterns
git_log("-30", "--all", "cleanup|close|release")

# Step 3: Research context managers
search_documentation("contextmanager", library="python")

# Step 4: Implement resource managers
# - BrowserResourceManager
# - DatabaseResourceManager
# - HTTPResourceManager
```

## Refactoring Safety Checks

### Pre-Refactor Checklist

```python
async def pre_refactor_check(file_path: str) -> dict:
    """Verify safe to refactor."""
    from mcp_tools import search_codebase, git_diff, read_file

    checks = {
        'tests_exist': False,
        'usages_identified': False,
        'impact_analyzed': False,
        'breaking_changes': []
    }

    # Check for tests
    test_file = file_path.replace('src/', 'tests/').replace('.py', '_test.py')
    search_codebase(f"test_{file_path.split('/')[-1]}", top_k=3)
    checks['tests_exist'] = True

    # Check usages
    class_name = file_path.split('/')[-1].replace('.py', '')
    search_codebase(f"from .*{class_name}", top_k=20)
    search_codebase(f"import {class_name}", top_k=20)
    checks['usages_identified'] = True

    # Analyze impact
    git_diff("HEAD~10..HEAD", file_pattern=f"**/{class_name}*")
    checks['impact_analyzed'] = True

    # Check for breaking changes
    search_codebase(f"def {class_name}(", top_k=5)
    # Add breaking change detection

    return checks
```

### Post-Refactor Verification

```python
async def verify_refactor(file_path: str) -> dict:
    """Verify refactoring didn't break behavior."""
    import subprocess

    verification = {
        'syntax_ok': False,
        'imports_ok': False,
        'tests_pass': False,
        'type_check': False
    }

    # Syntax check
    result = subprocess.run(['python', '-m', 'py_compile', file_path])
    verification['syntax_ok'] = result.returncode == 0

    # Import check
    result = subprocess.run(['python', '-c', f'import {".".join(file_path.split("/")[-2:])}'])
    verification['imports_ok'] = result.returncode == 0

    # Run tests
    result = subprocess.run(['pytest', file_path.replace('src/', 'tests/'), '-v'])
    verification['tests_pass'] = result.returncode == 0

    # Type check
    result = subprocess.run(['mypy', file_path])
    verification['type_check'] = result.returncode == 0

    return verification
```

## Rollback Strategy

```python
async def safe_refactor_with_rollback(func, *args) -> dict:
    """Execute refactor with automatic rollback on failure."""
    from mcp_tools import git_diff, git_reset

    # Store current state
    before_hash = await get_git_head()

    try:
        # Perform refactor
        result = await func(*args)

        # Verify
        verification = await verify_refactor(func.__name__)

        if not all(verification.values()):
            raise RefactorError("Verification failed")

        return result

    except Exception as e:
        # Rollback
        await git_reset(before_hash)
        return {'success': False, 'error': str(e), 'rolled_back': True}
```

## Common Refactoring Smells

| Smell | MCP Detection | Fix |
|--------|--------------|-----|
| Long method (>50 lines) | `search_codebase("def ", top_k=50)` and check lengths | Extract method |
| Duplicate code | `search_codebase()` for repeated patterns | Extract to shared function |
| God object | `search_codebase("class ", top_k=20)` and check attributes | Split responsibilities |
| Feature envy | `search_codebase("def ", top_k=50)` and check usage | Move method to data owner |
| Data clumps | `search_codebase("class ", top_k=20)` and check groupings | Extract class |
| Long parameter list (>5) | `search_codebase("def ", top_k=50)` | Use parameter object |
| Primitive obsession | `search_codebase("def ", top_k=50)` for lack of abstraction | Introduce value object |

## Refactoring Checklist

- [ ] Tests exist and pass
- [ ] All usages identified via `codebase` search
- [ ] Impact analyzed with `git` history
- [ ] Breaking changes documented
- [ ] Type hints updated
- [ ] Docstrings preserved/updated
- [ ] No behavior changes (tests verify)
- [ ] Performance not degraded
- [ ] Code is more readable
- [ ] DDD principles maintained

## Usage

Invoke this skill when:
- Code needs cleanup
- Technical debt reduction requested
- Design patterns need introduction
- Large classes need breaking down

```python
Task(subagent_type="refactor", prompt="""
Use refactor skill with MCP-first approach:

Target: Extract NodeController from MainWindow (800 lines)
Location: src/casare_rpa/presentation/canvas/main_window.py

MCP Workflow:
1. codebase: Search for controller patterns
2. filesystem: Read MainWindow around node-related methods
3. git: Check impact (who uses MainWindow)
4. exa: Research PySide6 controller patterns
5. sequential-thinking: Plan extraction steps

Apply extraction safely with:
- Preserved behavior
- Updated imports
- Tests passing
- No breaking changes
""")
```

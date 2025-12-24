---
skill: error-doctor
description: Systematic error diagnosis and resolution using MCP codebase search, web research, and structured analysis.
---

## MCP-First Approach

**Always use MCP servers in this order:**

1. **codebase** - Search for similar errors in codebase
   ```python
   search_codebase("runtime error port connection timeout", top_k=10)
   ```

2. **sequential-thinking** - For complex multi-step analysis
   ```python
   think_step_by_step("""
   Analyze error stack trace:
   1. Identify error type
   2. Locate in codebase
   3. Check common patterns
   4. Propose solutions
   """)
   ```

3. **exa** - Research error online if not in codebase
   ```python
   websearch("Python RuntimeError asyncio timeout fix 2025", numResults=5)
   ```

4. **ref** - Look up library documentation
   ```python
   search_documentation("asyncio.TimeoutError", library="python")
   ```

5. **git** - Check recent changes
   ```python
   git_diff("HEAD~5..HEAD", file_pattern="**/*.py")
   ```

6. **filesystem** - Read related files
   ```python
   read_file("src/casare_rpa/nodes/browser/click_node.py")
   ```

## Error Categories & Diagnosis Workflow

### 1. Import Errors

**Common Patterns:**
```
ModuleNotFoundError
ImportError
  ├─ Module not in dependencies
  ├─ Circular import
  ├─ Wrong import path
  └─ Virtual env issue
```

**MCP-Based Diagnosis:**
```python
# Step 1: Search codebase for module
search_codebase(f"from {missing_module}", top_k=10)

# Step 2: Check pyproject.toml for dependency
read_file("pyproject.toml")

# Step 3: Research online if needed
websearch(f"Python {missing_module} module not found fix", numResults=3)

# Step 4: Check if circular dependency
search_codebase("circular import", top_k=5)
```

**Quick Fixes:**

| Error | MCP Check | Fix |
|-------|------------|-----|
| `ModuleNotFoundError` | `search_codebase()` for imports | Install package: `pip install {module}` |
| `ImportError` | `git_diff()` for recent changes | Check circular deps, use TYPE_CHECKING |
| `AttributeError` | `read_file()` on module | Check `__init__.py` exports |

### 2. Type Errors

**Common Patterns:**
```
TypeError
AttributeError
  ├─ Wrong data type
  ├─ Missing attribute
  ├─ None access
  └─ Type mismatch in operation
```

**MCP-Based Diagnosis:**
```python
# Step 1: Locate error with codebase search
search_codebase(f"function {function_name}", top_k=5)

# Step 2: Read surrounding code
read_file(f"{file_path}:{line_number - 10}:{line_number + 10}")

# Step 3: Check type annotations
search_codebase(f"def {function_name}(", top_k=3)

# Step 4: Research common patterns
websearch(f"Python {error_type} {context} fix", numResults=3)
```

**Quick Fixes:**

| Error | MCP Check | Fix |
|-------|------------|-----|
| `'NoneType' object has no attribute` | `read_file()` on variable | Add `if var is not None` guard |
| `unsupported operand type` | `search_codebase()` for type hints | Use `isinstance()` or explicit conversion |
| `'str' object is not callable` | `read_file()` on definition | Check for variable/function name collision |

### 3. Async Errors

**Common Patterns:**
```
RuntimeWarning: coroutine never awaited
RuntimeError: This event loop is already running
TimeoutError
  ├─ Missing await
  ├─ Blocking call in async
  └─ Timeout exceeded
```

**MCP-Based Diagnosis:**
```python
# Step 1: Search for similar async patterns
search_codebase("await asyncio.gather", top_k=10)

# Step 2: Read async function
read_file(f"{file_path}:{line_number - 20}:{line_number + 20}")

# Step 3: Check event loop usage
search_codebase("asyncio.run(", top_k=5)

# Step 4: Research async best practices
websearch("Python async timeout error handling 2025", numResults=5)
```

**Quick Fixes:**

| Error | MCP Check | Fix |
|-------|------------|-----|
| `coroutine 'X' was never awaited` | `search_codebase()` for function | Add `await` before coroutine call |
| `This event loop is already running` | `read_file()` for event loop setup | Use `asyncio.create_task()` instead of `run()` |
| `BlockingIOError` in async | `search_codebase()` for I/O ops | Replace `time.sleep()` with `await asyncio.sleep()` |

### 4. Network/Timeout Errors

**Common Patterns:**
```
ConnectionError
TimeoutError
HTTP 429/500 errors
  ├─ Server unreachable
  ├─ Request timeout
  └─ Rate limiting
```

**MCP-Based Diagnosis:**
```python
# Step 1: Check connection usage
search_codebase("aiohttp.ClientSession", top_k=5)

# Step 2: Search timeout patterns
search_codebase("timeout=", top_k=10)

# Step 3: Research timeout best practices
websearch("aiohttp timeout retry pattern exponential backoff", numResults=5)

# Step 4: Check resource managers
read_file("src/casare_rpa/infrastructure/resources/http_manager.py")
```

**Quick Fixes:**

| Error | MCP Check | Fix |
|-------|------------|-----|
| `ServerConnectionError` | `read_file()` for client config | Add exponential backoff retry |
| `ReadTimeout` | `search_codebase()` for timeout values | Increase timeout or add retry logic |
| `HTTP 429 Too Many Requests` | `read_file()` for rate limiting | Add rate limiter / semaphore |

### 5. Node Execution Errors

**Common Patterns:**
```
NodeExecutionError
PortConnectionError
VariableResolutionError
  ├─ Node not found
  ├─ Port not connected
  ├─ Variable undefined
  └─ Type mismatch
```

**MCP-Based Diagnosis:**
```python
# Step 1: Search for node implementation
search_codebase(f"class {node_type}Node", top_k=3)

# Step 2: Read node code
read_file(f"src/casare_rpa/nodes/{category}/{node_name}_node.py")

# Step 3: Check port definitions
search_codebase(f"add_input.*{port_name}", top_k=5)

# Step 4: Search for similar issues
websearch(f"CasareRPA {node_type} node execution error", numResults=5)
```

**Quick Fixes:**

| Error | MCP Check | Fix |
|-------|------------|-----|
| `Port not found: {port_name}` | `search_codebase()` for port definition | Check `_define_ports()` method |
| `Variable not defined: {var_name}` | `read_file()` for node properties | Add variable reference or default value |
| `Type mismatch on port {port}` | `search_codebase()` for port types | Add type conversion node |

## Diagnostic Script Template

```python
async def diagnose_error(error: Exception, context: dict) -> dict:
    """Systematic error diagnosis using MCP servers."""
    from mcp_tools import search_codebase, websearch, read_file, git_diff

    diagnosis = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'mcp_used': [],
        'findings': [],
        'solutions': []
    }

    # Step 1: Search codebase for similar patterns
    query = f"{type(error).__name__} {context.get('function_name', '')}"
    search_results = await search_codebase(query, top_k=10)
    diagnosis['mcp_used'].append('codebase')
    diagnosis['findings'].append(f"Found {len(search_results)} similar patterns")

    # Step 2: Read problematic code
    file_path = context.get('file_path')
    line_number = context.get('line_number')
    if file_path and line_number:
        code = await read_file(f"{file_path}:{line_number-10}:{line_number+10}")
        diagnosis['mcp_used'].append('filesystem')
        diagnosis['findings'].append('Read surrounding code')

    # Step 3: Check recent changes
    recent_changes = await git_diff("HEAD~10..HEAD", file_pattern="**/*.py")
    diagnosis['mcp_used'].append('git')
    diagnosis['findings'].append(f"{len(recent_changes)} files changed recently")

    # Step 4: Research online
    search_query = f"Python {type(error).__name__} fix {context.get('context', '')}"
    web_results = await websearch(search_query, numResults=5)
    diagnosis['mcp_used'].append('exa')
    diagnosis['findings'].append(f"{len(web_results)} online resources found")

    # Step 5: Propose solutions
    if search_results:
        diagnosis['solutions'].append("Similar patterns found in codebase")
    if web_results:
        diagnosis['solutions'].append("Online solutions available")
    if recent_changes:
        diagnosis['solutions'].append("Check recent git changes")

    return diagnosis
```

## Error Prevention Strategies

**Proactive MCP Checks:**

Before running code:
```python
# Search for potential issues
search_codebase("TODO.*fix.*later", top_k=20)
search_codebase("except.*pass", top_k=20)
search_codebase("# type: ignore", top_k=20)

# Check for common anti-patterns
search_codebase("time.sleep(", top_k=10)
search_codebed("requests.get(", top_k=10)  # Should be aiohttp
```

## Testing Fixes

**After applying a fix:**

```python
# Step 1: Use filesystem to verify file
read_file(fixed_file_path)

# Step 2: Use git to see changes
git_diff("HEAD", file_path=fixed_file_path)

# Step 3: Run tests
import subprocess
subprocess.run(["pytest", f"tests/{test_file}.py", "-v"])

# Step 4: Search for similar errors
search_codebase(f"fixed.*{error_type}", top_k=5)
```

## Best Practices

1. **MCP-First**: Always try `codebase` search before grepping manually
2. **Sequential Thinking**: Use `sequential-thinking` for complex errors
3. **Web Research**: Use `exa` for latest solutions before guessing
4. **File Reading**: Use `filesystem` instead of `view_file` for large files
5. **Git History**: Use `git` to see when/why code changed
6. **Documentation**: Use `ref` for library API questions

## Common Error Dictionary

Search this dictionary first via `codebase`:
```python
# In .brain/errors.md:
{
  "PortConnectionError": {
    "mcp_search": "PortConnectionError fix",
    "common_fixes": [
      "Check port name spelling",
      "Verify port type matches",
      "Ensure node exists before connecting"
    ]
  },
  "VariableResolutionError": {
    "mcp_search": "VariableResolutionError undefined variable",
    "common_fixes": [
      "Add Set Variable node before use",
      "Check variable scope (workflow vs node)",
      "Verify variable name spelling"
    ]
  }
}
```

## Usage

Invoke this skill when:
- User reports an error with traceback
- Tests are failing with specific errors
- Runtime errors occur during workflow execution

```python
Task(subagent_type="refactor", prompt="""
Use error-doctor skill to diagnose:

Error: TypeError: 'NoneType' object has no attribute 'execute'
Location: src/casare_rpa/nodes/browser/click_node.py:42
Context: Workflow execution after browser open

Always use MCP servers first:
1. codebase: Search for similar errors
2. filesystem: Read click_node.py around line 42
3. git: Check recent changes
4. exa: Research online if needed

Return systematic diagnosis with fixes.
""")
```

# MCP Best Practices

Tool design, naming conventions, and error handling for Model Context Protocol servers.

## Tool Design Principles

### Single Responsibility
Each tool should do one thing well.

```python
# GOOD: Single purpose
@mcp.tool()
async def execute_workflow(workflow_id: str) -> Dict:
    """Execute a single workflow."""
    pass

@mcp.tool()
async def schedule_workflow(
    workflow_id: str,
    cron_expression: str
) -> Dict:
    """Schedule a workflow for later execution."""
    pass

# BAD: Multiple responsibilities
@mcp.tool()
async def workflow_manager(
    action: str,
    workflow_id: str,
    cron: str = None
) -> Dict:
    """Manage workflows (execute, schedule, list)."""
    pass
```

### Parameter Validation
Validate inputs early, return structured errors.

```python
from typing import Optional
from uuid import UUID

@mcp.tool()
async def execute_workflow(
    workflow_id: str,
    timeout_ms: Optional[int] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """Execute a workflow with optional timeout.

    Args:
        workflow_id: UUID of the workflow to execute
        timeout_ms: Maximum execution time in milliseconds
        ctx: MCP context for logging

    Returns:
        Result dict with status, workflow_id, output data
    """
    # Validate UUID format
    try:
        UUID(workflow_id)
    except ValueError:
        if ctx:
            await ctx.error(f"Invalid workflow_id format: {workflow_id}")
        return {
            "status": "error",
            "error": "invalid_uuid",
            "message": "workflow_id must be a valid UUID"
        }

    # Validate timeout
    if timeout_ms is not None and timeout_ms <= 0:
        if ctx:
            await ctx.error(f"Invalid timeout: {timeout_ms}")
        return {
            "status": "error",
            "error": "invalid_timeout",
            "message": "timeout_ms must be positive"
        }

    # Execute workflow...
```

### Idempotency
Design tools to be idempotent where possible.

```python
# GOOD: Idempotent - calling multiple times is safe
@mcp.tool()
async def ensure_workflow_stopped(workflow_id: str) -> Dict:
    """Stop workflow if running; no-op if already stopped."""
    if is_running(workflow_id):
        return await stop_workflow(workflow_id)
    return {"status": "already_stopped", "workflow_id": workflow_id}

# RISKY: Non-idempotent - may cause issues on retry
@mcp.tool()
async def increment_counter(counter_name: str) -> Dict:
    """Increment counter (changes state each call)."""
    pass
```

## Naming Conventions

### Tool Names
Use `verb_noun` pattern, lowercase with underscores.

| Domain | Verbs | Nouns |
|--------|-------|-------|
| Workflows | execute, schedule, stop, pause, resume | workflow, job, task |
| Robots | start, stop, status, list | robot, agent, executor |
| Data | get, set, list, delete | variable, parameter, config |
| Files | read, write, list, delete | file, directory, path |

```python
# GOOD: Clear, descriptive names
execute_workflow
schedule_workflow
get_robot_status
list_variables
set_variable

# BAD: Ambiguous or non-standard
run              # What runs?
workflow_exec    # Noun-first
getstatus        # Missing separator
data             # Too vague
```

### Resource Names
Use URI-like patterns with clear hierarchy.

```
workflow://{workflow_id}/status
workflow://{workflow_id}/logs
robot://{robot_id}/status
system://health
system://version
config://schema
```

```python
@mcp.resource("workflow://{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> Dict:
    """Get current status of a workflow."""
    pass

@mcp.resource("system://health")
async def get_system_health() -> Dict:
    """Get overall system health status."""
    pass
```

## Error Handling Patterns

### Error Categories

| Category | HTTP Analogy | Retryable | Example |
|----------|--------------|-----------|---------|
| Validation | 400 | No | Invalid UUID format |
| Not Found | 404 | No | Workflow doesn't exist |
| Conflict | 409 | No | Workflow already running |
| Rate Limit | 429 | Yes | Too many requests |
| Internal | 500 | Maybe | Database connection failed |

### Structured Error Responses

```python
from typing import Literal

@mcp.tool()
async def example_tool(param: str) -> Dict[str, Any]:
    """Tool with comprehensive error handling."""
    try:
        # Validation errors
        if not param or not param.strip():
            return {
                "status": "error",
                "error": "validation_failed",
                "message": "Parameter cannot be empty",
                "field": "param"
            }

        # Business logic errors
        result = await operation(param)
        if not result:
            return {
                "status": "error",
                "error": "not_found",
                "message": f"Resource not found: {param}",
                "field": "param"
            }

        # Success
        return {
            "status": "success",
            "data": result
        }

    except PermissionError as e:
        # Auth/permission errors
        return {
            "status": "error",
            "error": "permission_denied",
            "message": str(e),
            "retryable": False
        }
    except TimeoutError as e:
        # Timeout errors (retryable)
        return {
            "status": "error",
            "error": "timeout",
            "message": str(e),
            "retryable": True,
            "retry_after": 5  # seconds
        }
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in example_tool: {e}")
        return {
            "status": "error",
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "retryable": False
        }
```

### Context Logging

Use `Context` for structured logging at appropriate levels.

```python
@mcp.tool()
async def process_workflow(workflow_id: str, ctx: Context) -> Dict:
    # Debug: detailed diagnostic info
    await ctx.debug(f"Processing workflow: {workflow_id}")

    # Info: normal operation messages
    await ctx.info(f"Starting workflow execution")

    # Warning: something unexpected but not fatal
    await ctx.warning(f"Workflow taking longer than expected")

    # Error: operation failed
    await ctx.error(f"Failed to execute workflow: {error_message}")

    # Progress: long-running operations
    await ctx.report_progress(3, 10)  # 3 of 10 steps complete
```

## Response Patterns

### Standard Success Response
```python
{
    "status": "success",
    "data": {...},
    "metadata": {
        "timestamp": "2025-01-15T10:30:00Z",
        "execution_time_ms": 1250
    }
}
```

### Standard Error Response
```python
{
    "status": "error",
    "error": "error_code",
    "message": "Human-readable description",
    "details": {...},
    "retryable": False
}
```

### Paginated List Response
```python
{
    "status": "success",
    "data": [...],
    "pagination": {
        "total": 150,
        "offset": 0,
        "limit": 50,
        "has_more": True
    }
}
```

## Async Patterns

Always use async for I/O operations:

```python
# GOOD: Async I/O
@mcp.tool()
async def fetch_workflow_data(workflow_id: str) -> Dict:
    result = await db.fetch_workflow(workflow_id)
    status = await orchestrator.get_status(workflow_id)
    return {"workflow": result, "status": status}

# BAD: Blocking I/O
@mcp.tool()
def fetch_workflow_data_blocking(workflow_id: str) -> Dict:
    result = db.fetch_workflow_sync(workflow_id)  # Blocks!
    return result
```

For CPU-bound work, use `asyncio.to_thread`:

```python
import asyncio

@mcp.tool()
async def process_large_data(data: List[str]) -> Dict:
    # Offload CPU work to thread pool
    result = await asyncio.to_thread(cpu_intensive_function, data)
    return {"processed": result}
```

## References

- FastMCP official docs: https://gofastmcp.com/
- MCP spec: https://modelcontextprotocol.io/
- Error handling guide: https://mcpcat.io/guides/error-handling-custom-mcp-servers

# Python FastMCP Patterns

FastMCP-specific patterns for building MCP servers in Python.

## Basic Server Setup

```python
from fastmcp import FastMCP, Context
from typing import Dict, Any
from contextlib import asynccontextmanager
from loguru import logger

# Lifespan management for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastMCP):
    """Manage server lifecycle."""
    # Startup
    logger.info("Starting RPA MCP server")
    await connect_to_orchestrator()
    await connect_to_database()
    yield
    # Shutdown
    logger.info("Shutting down RPA MCP server")
    await disconnect_from_orchestrator()
    await disconnect_from_database()

# Create server
mcp = FastMCP(
    name="CasareRPA Server",
    instructions="""
    CasareRPA integration server for workflow execution and monitoring.

    Available tools:
    - execute_workflow: Run a workflow by ID
    - list_workflows: Get all available workflows
    - get_workflow_status: Check workflow execution status
    - stop_workflow: Stop a running workflow

    Available resources:
    - system://health: Server health status
    - workflow://{id}/status: Individual workflow status
    """,
    lifespan=lifespan,
    # Handle duplicate registrations
    on_duplicate_tools="error",
    on_duplicate_resources="warn",
)
```

## Tool Patterns

### With Context (Recommended)

```python
@mcp.tool()
async def execute_workflow(
    workflow_id: str,
    timeout_ms: int = 30000,
    ctx: Context = None
) -> Dict[str, Any]:
    """Execute a CasareRPA workflow.

    Args:
        workflow_id: UUID of the workflow to execute
        timeout_ms: Maximum execution time (default: 30000ms)
        ctx: FastMCP context for logging

    Returns:
        Execution result with status and output data
    """
    if ctx:
        await ctx.info(f"Starting workflow: {workflow_id}")
        await ctx.debug(f"Timeout: {timeout_ms}ms")

    try:
        # Execute workflow
        result = await orchestrator.execute(
            workflow_id,
            timeout_ms=timeout_ms
        )

        if ctx:
            await ctx.info(f"Workflow completed: {workflow_id}")
            await ctx.debug(f"Result: {result}")

        return {
            "status": "success",
            "workflow_id": workflow_id,
            "output": result.output,
            "execution_time_ms": result.execution_time
        }

    except WorkflowNotFoundError as e:
        if ctx:
            await ctx.error(f"Workflow not found: {workflow_id}")
        return {
            "status": "error",
            "error": "workflow_not_found",
            "message": str(e)
        }
    except TimeoutError as e:
        if ctx:
            await ctx.error(f"Workflow timeout: {workflow_id}")
        return {
            "status": "error",
            "error": "timeout",
            "message": f"Execution exceeded {timeout_ms}ms",
            "retryable": True
        }
```

### Progress Reporting

```python
@mcp.tool()
async def execute_long_workflow(
    workflow_id: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """Execute a workflow with progress updates."""
    if ctx:
        await ctx.info(f"Starting long workflow: {workflow_id}")

    # Get total steps
    total_steps = await get_workflow_step_count(workflow_id)
    completed = 0

    async for step_result in orchestrator.execute_stream(workflow_id):
        completed += 1
        if ctx:
            await ctx.info(f"Completed step {completed}: {step_result.name}")
            await ctx.report_progress(completed, total_steps)

    if ctx:
        await ctx.info(f"Workflow complete: {workflow_id}")

    return {"status": "success", "steps_completed": completed}
```

### Resource Access via Context

```python
@mcp.tool()
async def analyze_workflow_resources(
    workflow_id: str,
    ctx: Context = None
) -> Dict[str, Any]:
    """Analyze resources used by a workflow."""
    # Use context to read workflow resource
    if ctx:
        workflow_data = await ctx.read_resource(f"workflow://{workflow_id}")
        workflow_info = json.loads(workflow_data[0].text)

        # Use context to log analysis
        await ctx.info(f"Analyzing workflow: {workflow_info['name']}")

    return {
        "workflow_id": workflow_id,
        "resource_usage": analyze_resources(workflow_info)
    }
```

## Resource Patterns

### Dynamic Resources

```python
@mcp.resource("workflow://{workflow_id}/status")
async def get_workflow_status(workflow_id: str) -> str:
    """Get current status of a workflow.

    Args:
        workflow_id: UUID of the workflow

    Returns:
        JSON string with workflow status
    """
    status = await orchestrator.get_status(workflow_id)
    return json.dumps({
        "workflow_id": workflow_id,
        "status": status.state,
        "started_at": status.started_at.isoformat(),
        "current_node": status.current_node,
        "completed_nodes": status.completed_count,
        "total_nodes": status.total_count
    })
```

### Static Resources

```python
@mcp.resource("system://schema")
async def get_system_schema() -> str:
    """Get the workflow and data schema."""
    schema = {
        "version": "1.0",
        "types": {
            "workflow": {
                "properties": ["id", "name", "nodes", "connections"],
                "required": ["id", "name"]
            },
            "node": {
                "properties": ["id", "type", "position", "config"],
                "required": ["id", "type"]
            }
        }
    }
    return json.dumps(schema, indent=2)
```

### Health Check Resource

```python
@mcp.resource("system://health")
async def health_check() -> str:
    """System health status."""
    checks = {
        "orchestrator": await orchestrator.ping(),
        "database": await database.ping(),
        "robot_pool": await robot_pool.check_available()
    }

    all_healthy = all(checks.values())
    return json.dumps({
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    })
```

## Prompt Templates

```python
@mcp.prompt()
async def workflow_execution_summary(
    workflow_id: str
) -> str:
    """Generate a workflow execution summary prompt."""
    status = await orchestrator.get_status(workflow_id)
    return f"""
    Analyze the following workflow execution:

    Workflow: {workflow_id}
    Status: {status.state}
    Duration: {status.duration_ms}ms
    Nodes Executed: {status.completed_count}/{status.total_count}

    Please provide:
    1. Summary of what the workflow did
    2. Any errors or warnings encountered
    3. Performance assessment
    """
```

## Middleware

```python
from fastmcp import LoggingMiddleware

# Add logging middleware
mcp.add_middleware(LoggingMiddleware())

# Custom middleware for timing
import time
from fastmcp import Middleware

class TimingMiddleware(Middleware):
    async def on_tool_start(self, name: str, arguments: dict):
        self.start_time = time.time()
        logger.debug(f"Tool {name} started with args: {arguments}")

    async def on_tool_end(self, name: str, result: Any):
        duration = time.time() - self.start_time
        logger.info(f"Tool {name} completed in {duration:.2f}s")

mcp.add_middleware(TimingMiddleware())
```

## Transport Options

```python
if __name__ == "__main__":
    # STDIO (default) - for local development
    mcp.run(transport="stdio")

    # Streamable HTTP - for remote access
    mcp.run(transport="streamable-http", port=8080)

    # SSE - for server-sent events
    mcp.run(transport="sse", host="0.0.0.0", port=8080)
```

## Testing

```python
import pytest
from fastmcp import Client

@pytest.mark.asyncio
async def test_execute_workflow():
    """Test workflow execution tool."""
    # Create test server
    from my_server import mcp

    # Use FastMCP test client
    async with Client(mcp) as client:
        result = await client.call_tool(
            "execute_workflow",
            {"workflow_id": "test-id"}
        )

        assert result["status"] == "success"
        assert "workflow_id" in result

@pytest.mark.asyncio
async def test_workflow_resource():
    """Test workflow status resource."""
    from my_server import mcp

    async with Client(mcp) as client:
        resource = await client.read_resource(
            f"workflow://test-id/status"
        )

        status = json.loads(resource[0].text)
        assert status["workflow_id"] == "test-id"
```

## CLI Integration

```python
# server.py
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--health":
        # Simple health check command
        import asyncio
        asyncio.run(health_check_cli())
    else:
        mcp.run()

async def health_check_cli():
    """Run health check and exit."""
    checks = await run_health_checks()
    if all(checks.values()):
        print("OK")
        sys.exit(0)
    else:
        print("DEGRADED")
        sys.exit(1)
```

## References

- FastMCP docs: https://gofastmcp.com/
- FastMCP GitHub: https://github.com/jlowin/fastmcp
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk

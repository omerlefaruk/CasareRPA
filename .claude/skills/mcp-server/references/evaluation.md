# MCP Server Evaluation

Testing and evaluation checklist for MCP servers.

## Pre-Flight Checklist

### Configuration
- [ ] Server has descriptive name and instructions
- [ ] Lifespan configured for cleanup
- [ ] Duplicate handling strategy set
- [ ] Transport configured (stdio/http/sse)
- [ ] Error detail masking for production

### Dependencies
- [ ] `fastmcp` listed in requirements
- [ ] `loguru` for logging
- [ ] Pydantic for validation (if needed)
- [ ] All external deps documented

## Tool Evaluation

### Tool Signature
- [ ] Name follows `verb_noun` convention
- [ ] Has clear docstring describing purpose
- [ ] All parameters have type hints
- [ ] Parameters have descriptions in docstring
- [ ] Default values specified where appropriate
- [ ] Return type is `Dict[str, Any]` or compatible

### Parameter Validation
- [ ] Required parameters validated
- [ ] Optional parameters handled correctly
- [ ] Type checking on inputs
- [ ] Range validation on numbers
- [ ] UUID/email/url format validation where needed
- [ ] Early return on validation failure

### Error Handling
- [ ] All external calls in try/except
- [ ] Specific exceptions caught
- [ ] Structured error responses with status
- [ ] Error codes for different failure modes
- [ ] `retryable` flag for transient errors
- [ ] Context logging (ctx.error) for failures
- [ ] No raw exceptions leaked

### Context Usage
- [ ] `ctx.info()` for normal operations
- [ ] `ctx.debug()` for diagnostic info
- [ ] `ctx.warning()` for unexpected but non-fatal
- [ ] `ctx.error()` for failures
- [ ] `ctx.report_progress()` for long operations
- [ ] Progress token checked before reporting

### Response Format
- [ ] Success response has `status: "success"`
- [ ] Error response has `status: "error"`
- [ ] Error response includes `error` code
- [ ] Error response has human-readable `message`
- [ ] Data in `data` or `result` field
- [ ] Timestamps in ISO 8601 format
- [ ] Consistent field naming across tools

## Resource Evaluation

### Resource Signature
- [ ] URI follows clear pattern (`type://id/property`)
- [ ] Has clear docstring
- [ ] Returns JSON string or structured data
- [ ] URI parameters properly extracted

### Caching Strategy
- [ ] Static resources marked if cacheable
- [ ] Dynamic resources have appropriate TTL
- [ ] Cache invalidation strategy defined

### Error Handling
- [ ] Invalid URIs return error response
- [ ] Missing resources return 404-style error
- [ ] Access errors return permission denied
- [ ] Parse errors handled gracefully

## Integration Tests

```python
import pytest
from fastmcp import Client
from my_server import mcp

@pytest.mark.asyncio
class TestMCPServer:

    async def test_list_tools(self):
        """Server exposes correct tools."""
        async with Client(mcp) as client:
            tools = await client.list_tools()
            tool_names = {t.name for t in tools}
            assert "execute_workflow" in tool_names
            assert "list_workflows" in tool_names

    async def test_list_resources(self):
        """Server exposes correct resources."""
        async with Client(mcp) as client:
            resources = await client.list_resources()
            resource_uris = {r.uri for r in resources}
            assert "system://health" in resource_uris

    async def test_execute_workflow_success(self):
        """Tool succeeds with valid input."""
        async with Client(mcp) as client:
            result = await client.call_tool(
                "execute_workflow",
                {"workflow_id": "valid-id"}
            )
            assert result["status"] == "success"

    async def test_execute_workflow_validation(self):
        """Tool validates input correctly."""
        async with Client(mcp) as client:
            result = await client.call_tool(
                "execute_workflow",
                {"workflow_id": "invalid-uuid-format"}
            )
            assert result["status"] == "error"
            assert result["error"] == "validation_failed"

    async def test_resource_health(self):
        """Health resource returns valid data."""
        async with Client(mcp) as client:
            resource = await client.read_resource("system://health")
            data = json.loads(resource[0].text)
            assert "status" in data
            assert "checks" in data

    async def test_long_operation_progress(self):
        """Long operations report progress."""
        async with Client(mcp) as client:
            # Mock progress token in context
            result = await client.call_tool(
                "execute_long_workflow",
                {"workflow_id": "long-workflow"}
            )
            # Verify progress was reported
            assert result["status"] == "success"
```

## Manual Testing Checklist

### Startup
- [ ] Server starts without errors
- [ ] All tools registered successfully
- [ ] All resources registered successfully
- [ ] Lifespan startup tasks complete

### Tool Invocation
- [ ] Valid input produces success response
- [ ] Invalid input produces structured error
- [ ] Missing required parameter produces error
- [ ] Wrong type parameter produces error
- [ ] Concurrent requests handled correctly

### Resource Access
- [ ] Valid URI returns data
- [ ] Invalid URI returns error
- [ ] Dynamic resources update correctly
- [ ] Static resources are consistent

### Shutdown
- [ ] Graceful shutdown completes
- [ ] Lifespan cleanup tasks run
- [ ] Connections closed properly
- [ ] No resource warnings

## Performance Checks

- [ ] Tool response time < 1s for simple operations
- [ ] Progress updates every 1-2s for long operations
- [ ] Memory usage stable under load
- [ ] No memory leaks in lifespan
- [ ] Connection pooling for external services
- [ ] Proper timeout handling on external calls

## Security Checklist

- [ ] No secrets in error messages
- [ ] No stack traces to client
- [ ] Input sanitization on all parameters
- [ ] Path traversal protection
- [ ] Rate limiting on expensive operations
- [ ] Authentication/authorization where needed
- [ ] Mask error details in production

## Documentation

- [ ] README with setup instructions
- [ ] Example MCP client config
- [ ] Environment variables documented
- [ ] Tool catalog with examples
- [ ] Resource catalog with examples
- [ ] Error codes documented
- [ ] Changelog maintained

## Example MCP Config

```json
{
  "mcpServers": {
    "casare-rpa": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/CasareRPA",
        "run",
        "src/casare_rpa/infrastructure/mcp/server.py"
      ],
      "env": {
        "CASARE_LOG_LEVEL": "INFO",
        "CASARE_ORCHESTRATOR_URL": "http://localhost:8000"
      }
    }
  }
}
```

## Debugging Tips

1. **Enable FastMCP debug logging**
   ```bash
   FASTMCP_LOG_LEVEL=DEBUG python server.py
   ```

2. **Use MCP Inspector for testing**
   ```bash
   fastmcp dev server.py
   ```

3. **Check context is available**
   ```python
   if ctx is None:
       logger.warning("Context not available in tool call")
   ```

4. **Validate tool registration**
   ```python
   # In server startup
   logger.info(f"Registered {len(mcp._tool_manager._tools)} tools")
   logger.debug(f"Tools: {list(mcp._tool_manager._tools.keys())}")
   ```

## References

- FastMCP testing: https://gofastmcp.com/patterns/testing
- MCP inspector: https://modelcontextprotocol.io/inspector
- Server checklist: https://mcpcat.io/guides/developing-your-mcp-server

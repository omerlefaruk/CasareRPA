# Documentation Standards

**Part of:** `.brain/projectRules.md` | **See also:** `coding-standards.md`

## Docstring Format (Google Style)

```python
def execute_node(
    node_id: NodeId,
    context: ExecutionContext,
    timeout: int = 5000
) -> Dict[str, Any]:
    """Execute a single node in a workflow.

    Executes the node identified by node_id within the given execution
    context. Respects the provided timeout for the operation.

    Args:
        node_id: Unique identifier of the node to execute.
        context: Current execution context with variables and resources.
        timeout: Maximum execution time in milliseconds. Defaults to 5000.

    Returns:
        Dictionary with keys:
            - success (bool): Whether execution succeeded
            - result (Any): Node output value
            - error (str): Error message if failed

    Raises:
        NodeNotFoundError: If node_id does not exist in workflow.
        ExecutionTimeoutError: If execution exceeds timeout.

    Example:
        >>> context = ExecutionContext(variables={}, resources={})
        >>> result = await execute_node(NodeId("n1"), context)
        >>> print(result["success"])
        True
    """
    ...
```

## Inline Comments
- Only for "why", never "what" (code is self-documenting)
- Use sparingly

```python
# Good: Explains why
# Use exponential backoff to avoid overwhelming the service
retry_delay = min(2 ** attempt, 300)

# Bad: Explains what (code is already clear)
# Increment retry_delay
retry_delay = min(2 ** attempt, 300)
```

## README Structure

1. **Project Overview** - What is this project?
2. **Quick Start** - Install + run in 5 minutes
3. **Architecture** - Layer diagram + responsibility
4. **Development** - Setup, testing, contributing
5. **API Reference** - Link to docs/
6. **FAQ** - Common issues

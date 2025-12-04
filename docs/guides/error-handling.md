# Error Handling Guide

Handle errors gracefully in your workflows.

## Error Handling Nodes

| Node | Purpose |
|------|---------|
| TryNode | Start try block |
| CatchNode | Handle errors |
| FinallyNode | Cleanup code |
| RetryNode | Retry failed operations |
| ThrowErrorNode | Raise custom error |

## Try/Catch Pattern

```
Start → Try → [risky operation] → Finally → End
              ↓ (on error)
           Catch → [error handling] → Finally
```

## Retry Pattern

Use RetryNode to retry failed operations:

| Property | Description | Default |
|----------|-------------|---------|
| max_retries | Maximum attempts | 3 |
| retry_delay | Delay between retries (ms) | 1000 |
| backoff_multiplier | Exponential backoff | 2 |

## Best Practices

1. **Always use Try/Catch** for external operations
2. **Log errors** with LogErrorNode
3. **Use Finally** for cleanup
4. **Set reasonable retries** (3-5)
5. **Notify on failure** with WebhookNotifyNode

## Related Nodes

- [Error Handling Nodes](../nodes/error-handling/index.md)

# Performance & Security

**Part of:** `.brain/projectRules.md` | **See also:** `architecture.md`

## Performance Optimization

### When to Optimize
- **After profiling** (never guess)
- **For critical paths** (workflow execution, node setup)
- **For resource-intensive ops** (image processing, large loops)

### Async Best Practices
```python
# Good: Concurrent execution
tasks = [execute_node(n, ctx) for n in nodes]
results = await asyncio.gather(*tasks)

# Bad: Sequential (slow)
results = [await execute_node(n, ctx) for n in nodes]
```

### Resource Pooling
```python
# Good: Reuse connections
pool = ConnectionPool(max_size=10)
async with pool.get() as conn:
    await conn.execute(query)

# Bad: New connection per operation
conn = await create_connection()
await conn.execute(query)
await conn.close()
```

### Profiling Command
```bash
# Profile execution
python -m cProfile -s cumulative run.py

# Memory profiling
pip install memory-profiler
python -m memory_profiler script.py
```

## Security Considerations

### Input Validation
```python
# Always validate user input
def create_workflow(name: str) -> Workflow:
    if not name or len(name) > 255:
        raise ValidationError("Name must be 1-255 characters")
    return Workflow(name=name, description="")
```

### Secrets Management
- NO hardcoded secrets in code
- Use environment variables or `.env` (never commit)
- Validate in CI/pre-commit hooks

### Dependency Security
```bash
# Check for vulnerable dependencies
pip install safety
safety check

# Update security patches
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

---

**See:** `commands.md` for development workflow

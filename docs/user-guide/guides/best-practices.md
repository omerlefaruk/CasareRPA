# Workflow Design Best Practices

This guide covers best practices for designing reliable, maintainable, and efficient RPA workflows in CasareRPA.

---

## Design Principles

### 1. Single Responsibility

Each workflow should do one thing well.

```
# Good - focused workflow
"Process incoming invoices"

# Avoid - too many responsibilities
"Process invoices, update inventory, notify suppliers, and generate reports"
```

**Solution:** Break complex processes into multiple workflows that call each other using subflows.

### 2. Fail Fast, Recover Gracefully

Detect failures early and handle them appropriately.

```
[Validate Input] -> [Process Data] -> [Save Result]
       |
       v (invalid)
[Log Error] -> [Notify Admin]
```

### 3. Idempotency

Workflows should produce the same result when run multiple times with the same input.

```python
# Good - check before insert
if not database.exists(record_id):
    database.insert(record)

# Avoid - may create duplicates
database.insert(record)
```

---

## Workflow Structure

### Clear Entry Points

Every workflow should have a clear starting point:

```
[Trigger or StartNode]
        |
        v
[Validate Inputs]
        |
        v
[Main Processing]
        |
        v
[Handle Results]
```

### Logical Grouping

Group related nodes using frames:

```
+--[ Data Collection ]--+    +--[ Processing ]--+    +--[ Output ]--+
| [Navigate]            |    | [Parse Data]     |    | [Save File] |
| [Extract]             | -> | [Transform]      | -> | [Send Email]|
| [Validate]            |    | [Aggregate]      |    | [Log]       |
+----------------------+    +------------------+    +-------------+
```

### Consistent Flow Direction

Maintain left-to-right flow for readability:

```
[Start] -> [Step 1] -> [Step 2] -> [Step 3] -> [End]
```

For parallel branches, stack vertically:

```
              +-> [Branch A] -+
[Start] -> [Split]            [Merge] -> [End]
              +-> [Branch B] -+
```

---

## Error Handling

### Always Use Try-Catch

Wrap external operations in error handling:

```
[TryCatch Start]
    |
    +-> [External API Call]
    |
[Catch]
    |
    +-> [Log Error]
    +-> [Retry or Fallback]
    |
[Finally]
    |
    +-> [Cleanup]
```

### Implement Retry Logic

Use retry nodes for transient failures:

```python
# Node configuration
{
    "max_retries": 3,
    "retry_delay": 2000,
    "backoff_multiplier": 2.0,
    "retry_on_errors": ["TIMEOUT", "CONNECTION_REFUSED"]
}
```

### Graceful Degradation

Have fallback strategies:

```
[Primary Method]
       |
   (failure)
       |
       v
[Fallback Method]
       |
   (failure)
       |
       v
[Manual Queue]
```

---

## Browser Automation

### Use Dynamic Waits

```python
# Good - wait for specific condition
await page.wait_for_selector("#submit-button", timeout=10000)
await page.click("#submit-button")

# Avoid - fixed delay
await asyncio.sleep(5)  # Don't do this
await page.click("#submit-button")
```

### Reliable Selectors

Prefer stable selectors:

| Priority | Selector Type | Example |
|----------|--------------|---------|
| 1 | ID | `#submit-btn` |
| 2 | Data attributes | `[data-testid="submit"]` |
| 3 | Unique class | `.btn-primary.submit` |
| 4 | Text content | `text=Submit` |
| 5 | XPath | `//button[@type="submit"]` |

```python
# Good - stable selector
selector = '[data-automation-id="login-button"]'

# Avoid - fragile selector
selector = 'div.container > div:nth-child(3) > button'
```

### Handle Page States

```
[Navigate to Page]
        |
        v
[Wait for Page Load]
        |
        v
[Wait for Element Visible]
        |
        v
[Perform Action]
```

### Browser Resource Management

```
[Launch Browser]
        |
        v
[... workflow operations ...]
        |
        v
[Close Browser]  # Always clean up
```

Use `TryCatchFinally` to ensure browser closes:

```
[Try]
    |
    +-> [Launch Browser]
    +-> [Do Work]
    |
[Finally]
    |
    +-> [Close Browser]
```

---

## Desktop Automation

### Window Management

```
[Find Window]
        |
        v
[Activate Window]  # Ensure window is focused
        |
        v
[Wait for Ready]   # Wait for application to respond
        |
        v
[Perform Action]
```

### Input Timing

Add appropriate delays for UI interactions:

```python
# Between key presses for typing
type_delay = 50  # milliseconds

# After clicking before next action
click_delay = 200  # milliseconds

# After window operations
window_delay = 500  # milliseconds
```

### Screen Resolution Independence

Use relative positioning or UI Automation identifiers instead of screen coordinates:

```python
# Good - automation ID
element = window.ButtonControl(AutomationId="btnSubmit")

# Avoid - screen coordinates
click(x=450, y=320)  # Breaks on different resolutions
```

---

## Data Handling

### Validate Early

```
[Receive Input]
        |
        v
[Validate Schema]  # Check structure
        |
        v
[Validate Values]  # Check data quality
        |
        v
[Process Data]
```

### Type Safety

Always specify expected types:

```python
# Good - explicit type handling
count = int(inputs.get("count", 0))
items = list(inputs.get("items", []))
config = dict(inputs.get("config", {}))

# Avoid - assuming types
count = inputs["count"]  # May fail
```

### Handle Missing Data

```python
# Good - handle missing gracefully
email = customer.get("email", "")
if not email:
    log.warning(f"Customer {customer['id']} has no email")
    return NodeResult.skip("No email address")

# Avoid - fail on missing
email = customer["email"]  # Raises KeyError
```

---

## Variables and State

### Clear Naming

```python
# Good - descriptive names
customer_email = "john@example.com"
total_processed_count = 42
is_validation_successful = True

# Avoid - ambiguous names
data = "john@example.com"
cnt = 42
flag = True
```

### Scope Variables Appropriately

| Scope | Use Case | Lifetime |
|-------|----------|----------|
| Node output | Pass to next node | Until consumed |
| Workflow variable | Share across nodes | Workflow execution |
| Environment variable | Configuration | Application lifetime |
| Credential | Secrets | Encrypted storage |

### Initialize Variables

```
[Set Defaults]  # Initialize at start
        |
        +-> total_count = 0
        +-> error_list = []
        +-> start_time = now()
        |
        v
[Main Processing]
```

---

## Performance Optimization

### Batch Operations

```python
# Good - batch database inserts
records = [...]
database.insert_many(records)

# Avoid - individual inserts
for record in records:
    database.insert(record)  # N database calls
```

### Parallel Processing

Use parallel nodes for independent operations:

```
                +-> [Process Item 1] -+
[Get Items] -> [Parallel Split]        [Parallel Merge] -> [Aggregate]
                +-> [Process Item 2] -+
                +-> [Process Item 3] -+
```

### Minimize External Calls

```python
# Good - fetch once, use many times
user_data = api.get_user(user_id)
name = user_data["name"]
email = user_data["email"]

# Avoid - multiple API calls
name = api.get_user_name(user_id)
email = api.get_user_email(user_id)
```

### Resource Pooling

Configure appropriate pool sizes:

```yaml
resource_pools:
  browser_pool_size: 5      # Reuse browser instances
  db_pool_size: 10          # Connection pooling
  http_pool_size: 20        # HTTP session reuse
```

---

## Maintainability

### Document Your Workflows

Add descriptions to nodes:

```python
# In node configuration
{
    "description": "Fetches customer data from CRM API. Retries 3 times on failure.",
    "notes": "Requires CRM_API_KEY credential"
}
```

### Use Subflows

Extract reusable logic:

```
[Main Workflow]
        |
        +-> [Call: Login Subflow]
        +-> [Call: Data Extract Subflow]
        +-> [Call: Cleanup Subflow]
```

### Version Control

- Store workflows as JSON in git
- Use meaningful commit messages
- Review changes before deploying

### Logging

Add strategic log points:

```
[Start] -> [Log: "Starting process"]
        |
        v
[Process] -> [Log: "Processed {count} items"]
        |
        v
[End] -> [Log: "Completed successfully"]
```

---

## Testing

### Test in Isolation

```
# Create test workflow for each component
[Test: Login Flow]
[Test: Data Extraction]
[Test: Email Sending]
```

### Use Test Data

```python
# Test configuration
{
    "environment": "test",
    "use_mock_api": true,
    "target_url": "https://test.example.com"
}
```

### Validate Before Deploy

1. Run workflow in Canvas (development mode)
2. Test with sample data
3. Verify error handling
4. Check resource cleanup
5. Deploy to staging
6. Run full test suite
7. Deploy to production

---

## Security

### Never Hardcode Credentials

```python
# Good - use credential store
password = context.get_credential("db_password")

# Never do this
password = "super_secret_123"
```

### Sanitize Inputs

```python
# Validate and sanitize user input
email = inputs.get("email", "")
if not is_valid_email(email):
    raise ValueError("Invalid email format")
```

### Principle of Least Privilege

- Request only needed API permissions
- Use read-only access when possible
- Limit file system access paths

---

## Checklist

### Before Development

- [ ] Define clear success criteria
- [ ] Identify all data sources and targets
- [ ] List required credentials and permissions
- [ ] Plan error handling strategy

### During Development

- [ ] Use descriptive node names
- [ ] Add error handling for external calls
- [ ] Validate all inputs
- [ ] Add logging at key points
- [ ] Test happy path and edge cases

### Before Deployment

- [ ] Review all hardcoded values
- [ ] Verify credentials are from secure store
- [ ] Test in staging environment
- [ ] Document workflow purpose and configuration
- [ ] Set up monitoring and alerting

---

## Related Documentation

- [Error Handling](error-handling.md) - Detailed error handling patterns
- [Debugging](debugging.md) - Troubleshooting workflows
- [Subflows](subflows.md) - Creating reusable components
- [Variables](../core-concepts/variables.md) - Variable management

# Script Nodes

Script nodes enable execution of Python, JavaScript, and batch/shell scripts within workflows. They provide flexibility for custom logic, data transformations, and system integration.

## Overview

| Node | Language | Use Case |
|------|----------|----------|
| [RunPythonScriptNode](#runpythonscriptnode) | Python | Execute inline Python code |
| [RunPythonFileNode](#runpythonfilenode) | Python | Execute Python file |
| [EvalExpressionNode](#evalexpressionnode) | Python | Evaluate simple expressions |
| [RunBatchScriptNode](#runbatchscriptnode) | Batch/Shell | Execute system commands |
| [RunJavaScriptNode](#runjavascriptnode) | JavaScript | Execute JS via Node.js |

---

## RunPythonScriptNode

Execute inline Python code.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `timeout` | INTEGER | `60` | Execution timeout in seconds |
| `isolated` | BOOLEAN | `false` | Run in isolated subprocess |

### Ports

**Inputs:**
- `code` (STRING) - Python code to execute
- `variables` (DICT) - Variables to pass to script

**Outputs:**
- `result` (ANY) - Return value (`result` variable or last expression)
- `output` (STRING) - Captured print output
- `success` (BOOLEAN) - Execution success
- `error` (STRING) - Error message if failed

### Execution Modes

| Mode | `isolated` | Behavior |
|------|------------|----------|
| Inline | `false` | Executes in main process (faster, shared context) |
| Isolated | `true` | Executes in subprocess (safer, clean environment) |

### Example

```python
# Calculate statistics
calc_stats = RunPythonScriptNode(
    node_id="calc",
    config={
        "timeout": 30,
        "isolated": False
    }
)
# Connect code input:
"""
data = variables.get('data', [])
total = sum(data)
average = total / len(data) if data else 0
result = {
    'total': total,
    'average': average,
    'count': len(data)
}
print(f'Processed {len(data)} items')
"""
# Connect variables input: {"data": [10, 20, 30, 40]}
```

### Return Value

The script's return value is determined by:
1. The `result` variable if set
2. Otherwise, the value of the last expression

```python
# Method 1: Explicit result
result = {"name": "processed", "count": 42}

# Method 2: Last expression (not recommended for clarity)
{"name": "processed", "count": 42}
```

---

## RunPythonFileNode

Execute an external Python file.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `timeout` | INTEGER | `60` | Execution timeout in seconds |
| `python_path` | STRING | (current) | Python interpreter path |
| `retry_count` | INTEGER | `0` | Number of retries on failure |
| `retry_interval` | INTEGER | `1000` | Delay between retries (ms) |
| `retry_on_nonzero` | BOOLEAN | `false` | Retry if return code is non-zero |

### Ports

**Inputs:**
- `file_path` (STRING) - Path to Python file
- `args` (ANY) - Command line arguments (list or string)
- `working_dir` (STRING) - Working directory

**Outputs:**
- `stdout` (STRING) - Standard output
- `stderr` (STRING) - Standard error
- `return_code` (INTEGER) - Process return code
- `success` (BOOLEAN) - Execution success (return_code == 0)

### Example

```python
# Run data processing script
run_script = RunPythonFileNode(
    node_id="process",
    config={
        "timeout": 120,
        "retry_count": 2,
        "retry_on_nonzero": True
    }
)
# Connect file_path="C:\\Scripts\\process_data.py"
# Connect args=["--input", "{{input_file}}", "--output", "{{output_file}}"]
```

### Retry Behavior

When `retry_count > 0`:
1. Script executes
2. If it fails or returns non-zero (when `retry_on_nonzero: true`):
   - Wait `retry_interval` milliseconds
   - Retry up to `retry_count` times

---

## EvalExpressionNode

Evaluate a Python expression safely.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `expression` | STRING | `""` | Python expression to evaluate |

### Ports

**Outputs:**
- `result` (ANY) - Expression result
- `type` (STRING) - Result type name
- `success` (BOOLEAN) - Evaluation success
- `error` (STRING) - Error message if failed

### Safe Builtins

The expression runs with a restricted set of safe builtins:

| Category | Functions |
|----------|-----------|
| Math | `abs`, `pow`, `round`, `sum`, `min`, `max` |
| Type | `int`, `float`, `str`, `bool`, `list`, `dict`, `set`, `tuple`, `type` |
| Iteration | `range`, `enumerate`, `zip`, `map`, `filter`, `reversed`, `sorted` |
| Checks | `len`, `all`, `any` |
| Format | `bin`, `hex`, `oct`, `ord`, `chr`, `format`, `repr` |
| Constants | `True`, `False`, `None` |

> **Note:** File I/O, imports, and dangerous functions are not available.

### Example

```python
# Calculate total with tax
calc_total = EvalExpressionNode(
    node_id="calc_total",
    config={
        "expression": "round({{subtotal}} * 1.08, 2)"
    }
)
# With subtotal=100, result=108.0

# String manipulation
format_name = EvalExpressionNode(
    node_id="format",
    config={
        "expression": "'{{first_name}}'.upper() + ' ' + '{{last_name}}'.upper()"
    }
)
```

---

## RunBatchScriptNode

Execute batch scripts (Windows) or shell scripts (Unix/Mac).

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `timeout` | INTEGER | `60` | Execution timeout in seconds |
| `retry_count` | INTEGER | `0` | Number of retries on failure |
| `retry_interval` | INTEGER | `1000` | Delay between retries (ms) |
| `retry_on_nonzero` | BOOLEAN | `false` | Retry if return code is non-zero |

### Ports

**Inputs:**
- `script` (STRING) - Script content to execute
- `working_dir` (STRING) - Working directory

**Outputs:**
- `stdout` (STRING) - Standard output
- `stderr` (STRING) - Standard error
- `return_code` (INTEGER) - Process return code
- `success` (BOOLEAN) - Execution success

### Platform Behavior

| Platform | Extension | Execution |
|----------|-----------|-----------|
| Windows | `.bat` | `cmd /c script.bat` |
| Unix/Mac | `.sh` | `./script.sh` (with `#!/bin/bash`) |

### Example (Windows Batch)

```python
# Create directory and copy files
batch_script = RunBatchScriptNode(
    node_id="setup",
    config={"timeout": 30}
)
# Connect script input:
"""
@echo off
mkdir "{{output_dir}}" 2>nul
copy "{{source_file}}" "{{output_dir}}\\"
echo Files copied successfully
"""
```

### Example (Shell Script)

```python
# Linux/Mac file processing
shell_script = RunBatchScriptNode(
    node_id="process",
    config={"timeout": 60}
)
# Connect script input:
"""
#!/bin/bash
for file in {{input_dir}}/*.csv; do
    wc -l "$file"
done
"""
```

---

## RunJavaScriptNode

Execute JavaScript code using Node.js.

### Prerequisites

Node.js must be installed on the system.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `timeout` | INTEGER | `60` | Execution timeout in seconds |
| `node_path` | STRING | `node` | Path to Node.js executable |

### Ports

**Inputs:**
- `code` (STRING) - JavaScript code to execute
- `input_data` (ANY) - Data passed as `inputData` variable

**Outputs:**
- `result` (STRING) - Console output
- `success` (BOOLEAN) - Execution success
- `error` (STRING) - Error message if failed

### Example

```python
# Process data with JavaScript
run_js = RunJavaScriptNode(
    node_id="js_process",
    config={"timeout": 30}
)
# Connect code input:
"""
const data = inputData.items || [];
const processed = data.map(item => ({
    ...item,
    processedAt: new Date().toISOString()
}));
console.log(JSON.stringify(processed));
"""
# Connect input_data: {"items": [{"id": 1}, {"id": 2}]}
```

### Using Node.js Packages

You can use Node.js built-in modules:

```javascript
const fs = require('fs');
const path = require('path');

const filePath = path.join(__dirname, 'data.json');
console.log(`Processing: ${filePath}`);
```

> **Note:** For npm packages, ensure they are installed in the working directory or globally.

---

## Complete Examples

### Data Transformation Pipeline

```python
# 1. Read data (via other nodes)
# data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]

# 2. Transform with Python
transform = RunPythonScriptNode(
    node_id="transform",
    config={}
)
# code:
"""
data = variables.get('data', [])
result = []
for item in data:
    result.append({
        'full_name': item['name'].upper(),
        'age_group': 'young' if item['age'] < 30 else 'adult'
    })
print(f'Transformed {len(result)} records')
"""

# 3. Quick calculation
calc = EvalExpressionNode(
    node_id="calc",
    config={"expression": "len({{transformed_data}})"}
)
```

### System Automation

```python
# 1. Check disk space (Windows)
check_disk = RunBatchScriptNode(
    node_id="check_disk",
    config={"timeout": 10}
)
# script: "wmic logicaldisk get size,freespace,caption"

# 2. Parse with Python
parse_disk = RunPythonScriptNode(
    node_id="parse",
    config={}
)
# code:
"""
output = variables.get('disk_output', '')
lines = output.strip().split('\n')[1:]  # Skip header
result = []
for line in lines:
    parts = line.split()
    if len(parts) >= 3:
        result.append({
            'drive': parts[0],
            'free_gb': int(parts[1]) / (1024**3) if parts[1].isdigit() else 0,
            'total_gb': int(parts[2]) / (1024**3) if parts[2].isdigit() else 0
        })
"""
```

### API Data Processing

```python
# 1. Fetch data (via HTTP node)
# api_response = {"users": [...]}

# 2. Process with JavaScript
process_users = RunJavaScriptNode(
    node_id="process",
    config={}
)
# code:
"""
const users = inputData.users || [];
const active = users.filter(u => u.status === 'active');
const summary = {
    total: users.length,
    active: active.length,
    emails: active.map(u => u.email)
};
console.log(JSON.stringify(summary));
"""
```

---

## Best Practices

### Security

> **Warning:** Script execution is powerful but risky. Never execute untrusted code.

- Validate all inputs before script execution
- Use `isolated: true` for untrusted scripts
- Avoid hardcoding credentials in scripts
- Use variable placeholders (`{{var}}`) for dynamic values

### Performance

| Approach | Use When |
|----------|----------|
| Inline Python | Fast execution, simple transformations |
| Isolated Python | Untrusted code, memory isolation needed |
| Python File | Complex scripts, external dependencies |
| Expression | Simple calculations, no side effects |
| Batch/Shell | System commands, file operations |
| JavaScript | Node.js ecosystem, JSON processing |

### Error Handling

```python
# Always check success output
if outputs["success"]:
    result = outputs["result"]
else:
    error = outputs["error"]
    # Handle error appropriately
```

### Timeouts

- Set appropriate timeouts for your use case
- Long-running scripts should use larger timeouts
- Consider breaking long operations into smaller chunks

### Variable Passing

```python
# Pass data to scripts via variables input
variables = {
    "input_data": data,
    "config": {"threshold": 0.5},
    "file_path": "C:\\Data\\input.csv"
}

# Access in script via variables dict
# data = variables.get('input_data', [])
```

## Related Documentation

- [Data Operations](data-operations.md) - Data transformation without code
- [Control Flow](control-flow.md) - Workflow branching
- [System Nodes](system.md) - System commands

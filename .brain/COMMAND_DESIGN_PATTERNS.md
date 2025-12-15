# Command Design Patterns for CasareRPA

**Purpose**: Patterns and templates for designing new commands
**Audience**: Agent builders creating new slash commands
**Status**: Ready for use

---

## Pattern 1: Registry Validation Commands

**Use Case**: Validate that code registries match filesystem state

### Structure
```python
# 1. Scan filesystem
nodes = scan_directory("src/casare_rpa/nodes/")
# Returns: {"LaunchBrowserNode", "ClickElementNode", ...}

# 2. Load registry
from casare_rpa.nodes import _NODE_REGISTRY
registered = set(_NODE_REGISTRY.keys())

# 3. Compare
missing = nodes - registered        # In code, not registered
orphaned = registered - nodes       # In registry, not in code

# 4. Report
if missing:
    print("Missing from registry:", missing)
if orphaned:
    print("Orphaned in registry:", orphaned)
```

### Command Template
```bash
/validate-{registry_name}
  └─ Validates: {registry_type}
  └─ Checks: {condition}
  └─ Output: Issues + remediation
```

### Examples to Implement
- `/validate-registry` (nodes)
- `/validate-imports` (no circular dependencies)
- `/validate-decorators` (all nodes have @node)

---

## Pattern 2: Index Sync Commands

**Use Case**: Auto-update _index.md files from source code

### Structure
```python
# 1. Define scope
scope = "nodes"  # or "domain", "infrastructure", etc.
path = f"src/casare_rpa/{scope}/"

# 2. Scan and analyze
items = walk_directory(path)
categories = group_by_category(items)
counts = {cat: len(items) for cat, items in categories.items()}

# 3. Generate markdown
content = f"""
| Category | Count |
|----------|-------|
{generate_table_rows(counts)}

Total: {sum(counts.values())}
"""

# 4. Update index file
index_file = f"src/casare_rpa/{scope}/_index.md"
update_markdown_section(index_file, content)
```

### Command Template
```bash
/sync-{entity}-index [scope]
  └─ Scans: src/casare_rpa/{scope}/
  └─ Counts: entities, categories, exports
  └─ Updates: {scope}/_index.md
  └─ Reports: Changed lines, git diff preview
```

### Examples to Implement
- `/sync-nodes-index` - Update nodes/_index.md
- `/sync-domain-index` - Update domain/_index.md
- `/sync-all-indexes` - Bulk update all

---

## Pattern 3: Code Generation Commands

**Use Case**: Generate boilerplate code (tests, stubs, documentation)

### Structure
```python
# 1. Parse target
node_name = "LaunchBrowserNode"
node_file = find_node_file(node_name)

# 2. Analyze structure
source = read_file(node_file)
ast_tree = parse_python(source)
ports = extract_ports(ast_tree)
properties = extract_properties(ast_tree)

# 3. Generate from template
template = read_template("test_node.jinja2")
generated = template.render(
    node_name=node_name,
    ports=ports,
    properties=properties
)

# 4. Write output
output_file = f"tests/nodes/browser/test_{node_name}.py"
write_file(output_file, generated)
```

### Command Template
```bash
/{action}-{entity} [target] [options]
  └─ Analyzes: Target source code
  └─ Generates: {output_type}
  └─ Writes: Output file
  └─ Reports: Completion status + next steps
```

### Examples to Implement
- `/generate-test-skeleton [node-name]` - Node test boilerplate
- `/generate-visual-node [node-name]` - Visual node wrapper
- `/generate-docs [scope]` - API documentation

---

## Pattern 4: Quality/Audit Commands

**Use Case**: Run audits and generate reports (replace scattered scripts)

### Structure
```python
# 1. Select audits to run
audits = {
    "schemas": run_schema_audit,
    "consistency": run_consistency_audit,
    "metrics": run_metrics_audit,
}

# 2. Execute in parallel (up to 5)
results = run_parallel(
    [audits[category] for category in selected_categories],
    timeout=300,
    max_workers=5
)

# 3. Aggregate results
issues = combine_issues(results)
sorted_by_severity = sort_issues(issues)

# 4. Report
generate_report(sorted_by_severity)
```

### Command Template
```bash
/audit-{domain} [category] [--format json|text]
  └─ Runs: Up to 5 audits in parallel
  └─ Checks: {audit_types}
  └─ Output: Unified report (JSON or text)
  └─ Severity: Critical, Major, Minor
```

### Examples to Implement
- `/audit-quality [schemas|consistency|metrics|all]`
- `/audit-imports` - Check dependency rules
- `/audit-coverage` - Test coverage analysis

---

## Pattern 5: Performance Benchmark Commands

**Use Case**: Compare baseline vs current performance, flag regressions

### Structure
```python
# 1. Establish baseline
baseline_commit = run_git_cmd("rev-parse main")
baseline_results = checkout_and_measure(baseline_commit)

# 2. Measure current
current_results = measure_current()

# 3. Compare
delta = {
    metric: {
        "baseline": baseline_results[metric],
        "current": current_results[metric],
        "delta_pct": ((current - baseline) / baseline) * 100,
        "regression": current > baseline * 1.05,  # >5% slower
    }
    for metric in baseline_results.keys()
}

# 4. Report
for metric, comparison in delta.items():
    if comparison["regression"]:
        print(f"⚠️ REGRESSION: {metric}")
    else:
        print(f"✅ OK: {metric}")
```

### Command Template
```bash
/benchmark-{component} [--baseline main|HEAD^|{commit}]
  └─ Measures: Current performance
  └─ Compares: Against baseline
  └─ Flags: Regressions >5%
  └─ Output: Performance delta + investigation hints
```

### Examples to Implement
- `/benchmark-workflow-loading`
- `/benchmark-node-pooling`
- `/benchmark-ui-rendering`

---

## Pattern 6: Database/Schema Commands

**Use Case**: Safe database migrations with validation and rollback

### Structure
```python
# 1. Check status
current_version = read_schema_version()
pending = find_pending_migrations()

# 2. Pre-flight checks
check_backup_exists()
check_connection_valid()
check_no_active_transactions()

# 3. Execute with safety
for migration in pending:
    save_schema_backup()
    try:
        apply_migration(migration)
        validate_schema()
        log_success()
    except Exception as e:
        rollback_from_backup()
        raise

# 4. Post-flight validation
verify_all_tables()
verify_all_columns()
verify_constraints()
```

### Command Template
```bash
/manage-{system} [action] [--dry-run] [--force]
  └─ action = status | migrate | rollback | validate
  └─ --dry-run: Show what would happen
  └─ --force: Skip confirmation prompts
  └─ Output: Status report + change log
```

### Examples to Implement
- `/manage-database [status|migrate|rollback|validate]`
- `/manage-schema [status|upgrade|downgrade]`

---

## Pattern 7: Release/Versioning Commands

**Use Case**: Automate versioning, tagging, and release preparation

### Structure
```python
# 1. Parse current version
current_version = read_version_from_pyproject()
new_version = bump_version(current_version, semver_type)

# 2. Update files
update_file("pyproject.toml", "version", new_version)
update_file("src/casare_rpa/__init__.py", "__version__", new_version)

# 3. Generate changelog
commits = get_commits_since_tag(current_version)
changelog = generate_changelog(commits, new_version)
write_file("CHANGELOG.md", changelog)

# 4. Git operations
git_add(["pyproject.toml", "CHANGELOG.md"])
git_commit(f"chore: bump version to {new_version}")
git_tag(f"v{new_version}")

# 5. Build artifacts
build_docker_image(new_version)
```

### Command Template
```bash
/release {semver|--major|--minor|--patch} [--no-deploy]
  └─ Updates: Version in all files
  └─ Generates: CHANGELOG.md
  └─ Creates: Git tag
  └─ Builds: Docker image
  └─ Output: Release checklist
```

### Examples to Implement
- `/prepare-release [version|--major|--minor|--patch]`
- `/deploy-release [version]` - Triggers deployment

---

## Pattern 8: Parallel Agent Orchestration Commands

**Use Case**: Run multiple independent agents and aggregate results

### Structure
```python
# 1. Parse tasks
tasks = [
    ("explore", "Find pattern X"),
    ("researcher", "Research Y"),
    ("architect", "Design Z"),
]

# 2. Launch in parallel (up to 5)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = {
        executor.submit(run_agent, agent, prompt): name
        for agent, prompt in tasks
    }

    results = {}
    for future in futures:
        try:
            results[futures[future]] = future.result(timeout=300)
        except Exception as e:
            results[futures[future]] = {"error": str(e)}

# 3. Aggregate
final_result = combine_results(results)

# 4. Report
report_aggregated(final_result)
```

### Command Template
```bash
/run-parallel [task1] [task2] [task3] [--timeout 300] [--max-parallel 5]
  └─ Launches: Up to {max_parallel} independent agents
  └─ Timeout: {timeout} seconds per agent
  └─ Collects: Results from all agents
  └─ Output: Aggregated findings + report
```

### Examples to Implement
- `/run-parallel-agents [task1] [task2] ...`
- `/run-audits` (parallel audit execution)

---

## Common Command Utilities

### 1. Directory Scanning
```python
def scan_directory(root_path, pattern="*.py", exclude_dirs=None):
    """Recursively scan and return matching files."""
    if exclude_dirs is None:
        exclude_dirs = {"__pycache__", ".git", ".venv"}

    results = []
    for root, dirs, files in os.walk(root_path):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in fnmatch.filter(files, pattern):
            results.append(os.path.join(root, file))

    return sorted(results)
```

### 2. Markdown Table Generation
```python
def generate_markdown_table(headers, rows):
    """Generate markdown table from headers and rows."""
    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "|" + "|".join([" --- "] * len(headers)) + "|"

    data_lines = []
    for row in rows:
        data_lines.append("| " + " | ".join(str(v) for v in row) + " |")

    return "\n".join([header_line, separator_line] + data_lines)
```

### 3. File Parsing (AST)
```python
import ast

def extract_classes_from_file(file_path):
    """Extract class definitions from Python file."""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "bases": [b.id for b in node.bases if hasattr(b, 'id')],
            })

    return classes
```

### 4. Git Operations
```python
import subprocess

def run_git_cmd(cmd):
    """Run git command and return output."""
    result = subprocess.run(
        f"git {cmd}".split(),
        capture_output=True,
        text=True,
        cwd=os.getcwd()
    )
    if result.returncode != 0:
        raise RuntimeError(f"Git error: {result.stderr}")
    return result.stdout.strip()
```

### 5. Parallel Execution
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_parallel_tasks(tasks, timeout=300, max_workers=5):
    """Run tasks in parallel and aggregate results."""
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task["fn"], **task["args"]): task["name"]
                   for task in tasks}

        for future in as_completed(futures, timeout=timeout):
            task_name = futures[future]
            try:
                results[task_name] = future.result()
            except Exception as e:
                results[task_name] = {"error": str(e)}

    return results
```

---

## Best Practices for Command Design

### 1. Clear Input/Output Contract
```markdown
**Input**: What the user provides
**Output**: What the command returns
**Side Effects**: Files modified, git commits, etc.
```

### 2. Idempotency
Ensure commands are safe to run multiple times:
```python
# ❌ Bad: Appends to file each time
with open("file.txt", "a") as f:
    f.write("content")

# ✅ Good: Replaces idempotently
with open("file.txt", "w") as f:
    f.write("content")
```

### 3. Error Recovery
```python
# ✅ Good: Explicit error handling
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    suggest_fix(e)
    return {"status": "error", "message": str(e)}
```

### 4. Progress Reporting
```python
# ✅ Good: Show progress for long operations
total = count_items()
for i, item in enumerate(items):
    process(item)
    print(f"Progress: {i+1}/{total} ({(i+1)/total*100:.0f}%)")
```

### 5. Dry-Run Mode
```python
# ✅ Good: Allow preview before commit
if args.dry_run:
    print("Would apply these changes:")
    for change in changes:
        print(f"  - {change}")
    return

apply_changes(changes)
```

---

## Command Template (Boilerplate)

```markdown
# /{command-name} [{parameter}]

> **Usage**: `/{command-name} {example}` | `/{command-name} {example2}` | etc.

## What It Does

1 sentence description of purpose
2-3 sentences of detail about when to use

## Input

- `{parameter1}`: Description, valid values
- `{parameter2}`: Description, optional

## Output

- File changes: List of files modified
- Reports: Generated outputs
- Side effects: Git commits, etc.

## Examples

### Example 1
```bash
/{command-name} {example1}
# Output: Description
```

### Example 2
```bash
/{command-name} {example2} --option
# Output: Description
```

## Implementation Notes

- Key files: `path/to/file.py`
- References: Commands/patterns to reuse
- Dependencies: External tools/libraries
- Estimated effort: X hours

## Related

- `/other-command` - Related functionality
- `agent-rules/commands/` - Similar patterns
```

---

## Summary: 8 Commands for CasareRPA

| # | Command | Pattern | Effort | Impact |
|---|---------|---------|--------|--------|
| 1 | `/validate-registry` | Pattern 1 | 5h | Catch errors |
| 2 | `/sync-index-docs` | Pattern 2 | 10h | Keep docs fresh |
| 3 | `/generate-test-skeleton` | Pattern 3 | 15h | Test coverage |
| 4 | `/audit-quality` | Pattern 4 | 20h | Quality gates |
| 5 | `/benchmark-performance` | Pattern 5 | 15h | Protect wins |
| 6 | `/manage-database` | Pattern 6 | 30h | Safe scaling |
| 7 | `/prepare-release` | Pattern 7 | 25h | Automation |
| 8 | `/run-parallel-agents` | Pattern 8 | 25h | Orchestration |

---

**Status**: Ready for implementation
**Next Step**: Create command definition files (MDx in `agent-rules/commands/`)

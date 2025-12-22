# GEMINI.md

Configuration and capabilities for the Gemini AI Coding Agent.

## Modern Node Standard (2025)

All 430+ nodes follow **Schema-Driven Logic**:

```python
@properties(
    PropertyDef("url", PropertyType.STRING, required=True),
    PropertyDef("timeout", PropertyType.INTEGER, default=30000),
)
@node(category="browser")
class MyNode(BaseNode):
    async def execute(self, context):
        url = self.get_parameter("url")              # Auto-resolved!
        timeout = self.get_parameter("timeout", 30000)  # Auto-resolved!
```

**Requirements:**
- `@properties()` decorator (REQUIRED - even if empty)
- `get_parameter()` for ALL port/config values (dual-source pattern)
- **AUTO-RESOLUTION** (NEW 2025): `get_parameter()` now auto-resolves `{{variables}}` when context is available. Manual `context.resolve_value()` calls are **no longer needed** in most cases.
- **RAW VALUES**: Use `get_raw_parameter()` or `get_parameter(name, resolve=False)` when you need the un-resolved template string.
- **CACHE AWARENESS**: `VariableResolutionCache` is prefix-aware. Updating a parent dict (e.g. `node`) invalidates child paths (e.g. `node.result`).
- Explicit DataType on all ports (ANY is valid)
- NO `self.config.get()` calls (LEGACY)

**Audit:** `python scripts/audit_node_modernization.py` → 98%+ modern

## MCP Setup

MCP servers are configured in `./.mcp.json`.

- `filesystem` — safe file operations within allowed roots (Node, via `npx`)
- `git` — repository inspection/operations (requires `python -m pip install mcp-server-git`)
- `sequential-thinking` — structured reasoning tool (Node, via `npx`)

## Agent Capabilities


| Agent | Capability | Skill Mapping |
|-------|------------|---------------|
| `architect` | System design, DDD patterns, refactoring planning | `architect-design` |
| `builder` | Python 3.12+ implementation, PySide6 UI, Playwright, Browser Scripting | `code-implementation` |
| `docs` | Technical writing, docstring generation, README maintenance | `documentation` |
| `explore` | Codebase navigation, semantic search, dependency mapping | `semantic-search` |
| `integrations` | API client development, database schema design, Supabase | `api-integration` |
| `quality` | Test generation (pytest), bug reproduction, code review | `test-generator` |
| `refactor` | Code optimization, pattern modernization, clean architecture | `refactor-patterns` |
| `researcher` | Error diagnosis, requirement gathering, technology research | `error-diagnosis` |
| `reviewer` | PR review, security audit, style enforcement | `code-review` |
| `ui` | PySide6 widget development, CSS styling, UX optimization | `ui-widget` |

## Skill Mappings

| Skill | Description | Schema |
|-------|-------------|--------|
| `semantic-search` | Search codebase for patterns/meaning | `search_schema` |
| `test-generator` | Generate pytest files for nodes/domain | `test_schema` |
| `import-fixer` | Organize and fix Python imports | `import_schema` |
| `node-template-generator` | Scaffold new RPA nodes | `node_schema` |
| `error-diagnosis` | Analyze logs and tracebacks to find bugs | `error_schema` |
| `api-integration` | Create REST/GraphQL clients | `api_schema` |
| `ui-widget` | Create PySide6 custom widgets | `ui_schema` |
| `performance-optimizer` | Identify and fix performance bottlenecks | `perf_schema` |
| `node-creator` | Create complex RPA nodes with logic | `node_creator_schema` |

## Gemini API Integration Parameters

- **Model:** `gemini-2.0-flash-exp` (Primary), `gemini-1.5-pro` (Reasoning)
- **Temperature:** 0.0 (Strict), 0.7 (Creative)
- **Top-P:** 0.95
- **Top-K:** 40
- **Max Output Tokens:** 8192
- **Safety Settings:** `BLOCK_NONE`
- **Response MIME Type:** `text/plain` or `application/json`

## Interaction Schemas

### Skill Execution Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "skill_name": { "type": "string" },
    "parameters": { "type": "object" },
    "context": { "type": "object" }
  },
  "required": ["skill_name", "parameters"]
}
```

### Concrete Skill Schemas

#### semantic-search
```json
{
  "type": "object",
  "properties": {
    "query": { "type": "string" },
    "top_k": { "type": "integer", "default": 5 },
    "filter": { "type": "object" }
  },
  "required": ["query"]
}
```

#### test-generator
```json
{
  "type": "object",
  "properties": {
    "file_path": { "type": "string" },
    "test_type": { "enum": ["unit", "integration", "e2e"] },
    "mock_dependencies": { "type": "boolean", "default": true }
  },
  "required": ["file_path"]
}
```

#### performance-optimizer
```json
{
  "type": "object",
  "properties": {
    "target_file": { "type": "string" },
    "optimization_goal": { "enum": ["cpu", "memory", "latency"] }
  },
  "required": ["target_file"]
}
```

#### node-creator
```json
{
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "category": { "type": "string" },
    "inputs": { "type": "array", "items": { "type": "string" } },
    "outputs": { "type": "array", "items": { "type": "string" } }
  },
  "required": ["name", "category"]
}
```

### Agent Activity Log Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "timestamp": { "type": "string", "format": "date-time" },
    "agent": { "type": "string" },
    "action": { "type": "string" },
    "status": { "enum": ["success", "failure", "pending"] },
    "details": { "type": "string" }
  },
  "required": ["timestamp", "agent", "action", "status"]
}
```

## Error Handling Policy

1. **API Failures:** Retry with exponential backoff (max 3 retries).
2. **Skill Execution Failures:** Log error, notify user, and suggest alternative skill or manual intervention.
3. **Validation Failures:** Reject execution if parameters do not match schema.

## Lessons Learned (Stress Test Round 1)

1. **SERIAL EXECUTION IS MANDATORY**: All action nodes, including "data" nodes (`ComparisonNode`, `FormatStringNode`, etc.), must be part of the main `exec_out` -> `exec_in` chain. Orphan nodes run at start-time in parallel and usually fail due to missing data from the main chain.
2. **ROBUST DATA NODES**: Logic nodes should handle unresolved templates (e.g., `{{variable}}`) gracefully. If a variable is not ready (due to orphan execution), the node should log a warning and return a safe default instead of crashing the process.
3. **RECURSIVE RESOLUTION**: Nodes that accept dictionaries (like `FormatStringNode`'s `variables`) must use `resolve_dict_variables` to ensure nested templates are resolved before Use.
4. **TYPE COERCION in COMPARISON**: Comparison nodes should attempt to coerce numeric-looking strings to floats/ints before comparison to handle inputs like `"25" > 20`.
5. **JSON-LIKE BOOLEANS**: Safe evaluation should support `true`, `false`, and `null` as aliases for Python's `True`, `False`, `None` to improve compatibility with LLM-generated expressions.
6. **NO HARDCODED WAITS**: NEVER use `asyncio.sleep()` or `time.sleep()` with fixed durations. Instead, use smart waiting strategies:
   - `page.wait_for_load_state('networkidle')` - Wait for network to be idle
   - `page.wait_for_load_state('domcontentloaded')` - Wait for DOM ready
   - `locator.wait_for(state='visible')` - Wait for element visibility
   - `page.wait_for_selector(selector)` - Wait for element to appear
   - `page.expect_download()` - Wait for download events
   - `page.wait_for_url(pattern)` - Wait for URL change
   - Polling with exponential backoff for custom conditions

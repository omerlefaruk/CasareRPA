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
        url = self.get_parameter("url")              # required
        timeout = self.get_parameter("timeout", 30000)  # optional
```

**Requirements:**
- `@properties()` decorator (REQUIRED - even if empty)
- `get_parameter()` for optional properties (dual-source: port → config)
- Explicit DataType on all ports (ANY is valid)
- NO `self.config.get()` calls (LEGACY)

**Audit:** `python scripts/audit_node_modernization.py` → 98%+ modern

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

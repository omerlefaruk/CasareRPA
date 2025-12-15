# _index.md Quick Reference

## What Exists (22 Files)

### ALWAYS AVAILABLE (Start Here)
✓ `src/casare_rpa/domain/_index.md` - Core entities, events, value objects
✓ `src/casare_rpa/application/_index.md` - Use cases, services
✓ `src/casare_rpa/infrastructure/_index.md` - External adapters
✓ `src/casare_rpa/nodes/_index.md` - All node categories
✓ `src/casare_rpa/presentation/canvas/_index.md` - Canvas UI overview
✓ `src/casare_rpa/presentation/canvas/visual_nodes/_index.md` - 407 visual nodes

### SPECIALIZED INDEXES
✓ `src/casare_rpa/domain/ai/_index.md` - AI domain models
✓ `src/casare_rpa/infrastructure/ai/_index.md` - LLM integration
✓ `src/casare_rpa/infrastructure/resources/_index.md` - Google, Anthropic clients
✓ `src/casare_rpa/infrastructure/security/_index.md` - Vault, OAuth, RBAC
✓ `src/casare_rpa/nodes/browser/_index.md` - Browser nodes
✓ `src/casare_rpa/nodes/control_flow/_index.md` - Control flow
✓ `src/casare_rpa/nodes/desktop_nodes/_index.md` - Desktop automation
✓ `src/casare_rpa/nodes/file/_index.md` - File operations
✓ `src/casare_rpa/nodes/google/_index.md` - Google integration

### CANVAS SUBSYSTEMS
✓ `src/casare_rpa/presentation/canvas/controllers/_index.md`
✓ `src/casare_rpa/presentation/canvas/events/_index.md`
✓ `src/casare_rpa/presentation/canvas/graph/_index.md`
✓ `src/casare_rpa/presentation/canvas/selectors/_index.md`
✓ `src/casare_rpa/presentation/canvas/ui/_index.md`

### TOOLS & META
✓ `.brain/decisions/_index.md` - Decision trees
✓ `agent-rules/_index.md` - Agent definitions

---

## Critical Gaps (High Impact)

### MUST HAVE (Domain Foundation)
- ❌ `domain/aggregates/` - Workflow aggregate (impacts: persistence, events)
- ❌ `domain/entities/` - BaseNode, core entities
- ❌ `domain/events/` - Event classes and bus
- ❌ `domain/value_objects/` - DataType, PortType, Signal enums
- ❌ `domain/schemas/` - PropertyDef, port schemas
- ❌ `domain/interfaces/` - Port contracts

### MUST HAVE (Infrastructure)
- ❌ `infrastructure/orchestrator/` - Server, API, managers
- ❌ `infrastructure/execution/` - Execution engine
- ❌ `infrastructure/persistence/` - Database layer
- ❌ `infrastructure/http/` - UnifiedHttpClient
- ❌ `infrastructure/browser/` - Playwright integration

### SHOULD HAVE (Application)
- ❌ `application/use_cases/` - All use case implementations
- ❌ `application/execution/` - Execution coordination
- ❌ `application/orchestrator/` - Orchestration logic

### NODES (13 Categories with Zero Docs)
- ❌ `nodes/data/`, `nodes/database/`, `nodes/http/`, `nodes/llm/`
- ❌ `nodes/email/`, `nodes/document/`, `nodes/system/`, `nodes/text/`
- ❌ `nodes/workflow/`, `nodes/trigger_nodes/`, `nodes/error_handling/`
- ❌ `nodes/messaging/`, `nodes/data_operation/`

### UTILS (All Missing)
- ❌ `utils/performance/` - Node pooling, optimization
- ❌ `utils/workflow/` - Loaders, compressed I/O
- ❌ `utils/resilience/` - Retry patterns
- ❌ `utils/security/`, `utils/gpu/`, `utils/pooling/`, `utils/recording/`, `utils/selectors/`

---

## Coverage by Layer

| Layer | Total Dirs | With Docs | Gap |
|-------|-----------|-----------|-----|
| **Domain** | 14 | 2 | 12/14 (86% missing) |
| **Application** | 8 | 1 | 7/8 (88% missing) |
| **Infrastructure** | 23 | 4 | 19/23 (83% missing) |
| **Nodes** | 19 | 6 | 13/19 (68% missing) |
| **Presentation** | 21 | 7 | 14/21 (67% missing) |
| **Utils** | 9 | 0 | 9/9 (100% missing) |
| **Other** | 17 | 2 | 15/17 (88% missing) |

---

## How to Use This List

1. **Looking for documentation?**
   - Check "ALWAYS AVAILABLE" first
   - Then check "SPECIALIZED INDEXES"
   - If not found, likely needs to be created

2. **Want to create missing docs?**
   - Start with "MUST HAVE" section (high impact)
   - Then "SHOULD HAVE" (medium impact)
   - Then "NODES" categories (many small docs)

3. **Integration patterns?**
   - See: `src/casare_rpa/infrastructure/_index.md`
   - See: `src/casare_rpa/domain/_index.md`

4. **Node patterns?**
   - See: `src/casare_rpa/nodes/_index.md`
   - Then specific category (browser, file, google, etc.)

---

## Quick Stats

- **Total _index.md files**: 22 (17% coverage)
- **Most documented layer**: Presentation (33%, mostly canvas)
- **Least documented layer**: Utils (0%) & Tests (0%)
- **Biggest gap**: Infrastructure (20 missing) + Domain (12 missing)
- **Most complete**: Nodes (6/19, with visual_nodes having 407 nodes documented)

---

## Next Priority

If only 5 files could be created next:

1. `src/casare_rpa/domain/entities/_index.md` - BaseNode foundation
2. `src/casare_rpa/domain/events/_index.md` - Event system docs
3. `src/casare_rpa/infrastructure/orchestrator/_index.md` - Server/API
4. `src/casare_rpa/application/use_cases/_index.md` - Main workflows
5. `src/casare_rpa/utils/workflow/_index.md` - Loader patterns

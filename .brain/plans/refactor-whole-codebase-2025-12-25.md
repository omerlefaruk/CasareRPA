# CasareRPA Whole-Codebase Refactoring Plan

**Created**: 2025-12-25
**Status**: PLANNING
**Est. Duration**: 30 hours (4 phases)

---

## Executive Summary

This refactoring addresses code quality and architectural purity issues identified through codebase analysis:

| Issue | Count | Impact |
|-------|-------|--------|
| Unused imports | 75 F401 violations | Lint noise, minor bloat |
| Legacy type hints | 655 files with `typing` imports | Python 3.12+ inconsistency |
| Domain loguru imports | 12 domain files | **DDD violation** |
| Raw aiohttp usage | 29 files | Bypasses resilience patterns |
| TODO comments | 4 items | Technical debt markers |

**Risk Level**: Medium - changes span architectural boundaries
**Rollback**: Git-based, can revert per-phase

---

## Phase 1: Quick Wins (3 hours)

**Agent**: `refactor`
**Risk**: Low
**Parallelizable**: Yes

### 1.1 Remove Unused Imports (30 min)

| Metric | Value |
|--------|-------|
| Files affected | ~50 |
| Fixable automatically | 73/75 |
| Manual review required | 2 |

**Command**:
```bash
ruff check src/ --select F401 --fix
```

**Files requiring manual review**:
1. `src/casare_rpa/infrastructure/security/__init__.py` - TokenExpiredError, TokenRefreshError
2. `src/casare_rpa/infrastructure/http/unified_http_client.py` - verify logger import

**Acceptance**:
```bash
ruff check src/ --select F401  # Returns 0
```

### 1.2 Modernize Type Hints (2 hours)

**Target**: 18 high-priority files

**Pattern**:
```python
# OLD
from typing import Dict, List, Optional, Tuple

def foo(data: Optional[Dict[str, int]]) -> List[Tuple[str, int]]:
    ...

# NEW
def foo(data: dict[str, int] | None) -> list[tuple[str, int]]:
    ...
```

**Priority Files** (ordered by layer):

| Layer | Files |
|-------|-------|
| Domain | `domain/entities/chain_types.py`, `domain/entities/chain.py`, `domain/entities/base_node.py`, `domain/services/dependency_manager.py`, `domain/services/predictive_timer.py`, `domain/services/dynamic_loop_manager.py`, `domain/value_objects/types.py`, `domain/interfaces/execution_context.py` |
| Application | `application/dependency_injection/singleton.py`, `application/use_cases/variable_resolver.py`, `application/services/port_type_service.py` |
| Infrastructure | `infrastructure/agents/real_agent_orchestrator.py`, `infrastructure/caching/workflow_cache.py`, `infrastructure/execution/variable_cache.py` |
| Utils | `utils/selectors/selector_cache.py`, `utils/security/secrets_manager.py`, `utils/resilience/rate_limiter.py` |

**Script**:
```bash
# Use ruff's UP rules for type hint modernization
ruff check src/ --select UP006,UP007,UP013 --fix
```

### 1.3 Resolve TODO Comments (30 min)

**Files**:
1. `src/casare_rpa/presentation/canvas/ui/dialogs/credential_manager_dialog.py`
2. `src/casare_rpa/testing/node_test_generator.py`
3. `src/casare_rpa/presentation/canvas/ui/panels/variables_tab.py`

**Actions**: Implement or convert to GitHub issues

**Acceptance**:
```bash
rg "# TODO" --type py -l  # Returns 0
```

---

## Phase 2: Domain Layer Purity (8 hours)

**Agent**: `architect` + `reviewer`
**Risk**: Medium (architectural boundary)
**Parallelizable**: Limited (sequential refactoring)

### 2.1 Create DI Container for Logger (2 hours)

**Problem**: Domain layer imports loguru (external dependency)

**Solution**: Protocol-based injection

**New File**: `src/casare_rpa/domain/interfaces/logger.py`

```python
from typing import Protocol

class ILogger(Protocol):
    """Domain-agnostic logger protocol."""

    def debug(self, msg: str, **kwargs) -> None: ...
    def info(self, msg: str, **kwargs) -> None: ...
    def warning(self, msg: str, **kwargs) -> None: ...
    def error(self, msg: str, **kwargs) -> None: ...
    def critical(self, msg: str, **kwargs) -> None: ...

# Domain service for logger access
class LoggerService:
    _instance: ILogger | None = None

    @classmethod
    def get(cls) -> ILogger:
        if cls._instance is None:
            raise RuntimeError("Logger not configured. Call configure() first.")
        return cls._instance

    @classmethod
    def configure(cls, logger: ILogger) -> None:
        cls._instance = logger
```

**Infrastructure Implementation**: `src/casare_rpa/infrastructure/logging/loguru_adapter.py`

```python
from loguru import logger as _logger
from casare_rpa.domain.interfaces.logger import ILogger

class LoguruLogger(ILogger):
    def debug(self, msg: str, **kwargs) -> None:
        _logger.bind(**kwargs).debug(msg)

    def info(self, msg: str, **kwargs) -> None:
        _logger.bind(**kwargs).info(msg)

    def warning(self, msg: str, **kwargs) -> None:
        _logger.bind(**kwargs).warning(msg)

    def error(self, msg: str, **kwargs) -> None:
        _logger.bind(**kwargs).error(msg)

    def critical(self, msg: str, **kwargs) -> None:
        _logger.bind(**kwargs).critical(msg)

# Auto-configure on import
from casare_rpa.domain.interfaces.logger import LoggerService
LoggerService.configure(LoguruLogger())
```

### 2.2 Refactor Domain Files (4 hours)

**Files to migrate** (ordered by dependency):

| File | Lines to Change |
|------|-----------------|
| `domain/decorators/error_handler.py` | Replace `from loguru import logger` |
| `domain/ai/templates/common_templates.py` | Replace `from loguru import logger` |
| `domain/entities/resource_node.py` | Replace `from loguru import logger` |
| `domain/events/bus.py` | Replace `from loguru import logger` |
| `domain/services/dynamic_loop_manager.py` | Replace `from loguru import logger` + unused imports |
| `domain/services/dependency_manager.py` | Replace `from loguru import logger` + unused imports |
| `domain/services/workflow_validator.py` | Replace `from loguru import logger` |
| `domain/services/predictive_timer.py` | Replace `from loguru import logger` + unused imports |
| `domain/services/expression_evaluator.py` | Replace `from loguru import logger` |
| `domain/services/headless_validator.py` | Replace `from loguru import logger` |
| `domain/services/smart_chain_selector.py` | Replace `from loguru import logger` |
| `domain/services/chain_executor.py` | Replace `from loguru import logger` |

**Pattern**:
```python
# OLD
from loguru import logger

logger.info("Message")

# NEW
from casare_rpa.domain.interfaces.logger import LoggerService

logger = LoggerService.get()
logger.info("Message")
```

### 2.3 Validation Test (2 hours)

**New Test**: `tests/domain/services/test_logger_purity.py`

```python
"""Test that domain layer has no external imports."""

def test_domain_no_loguru_imports():
    """Domain layer must not import loguru directly."""
    import subprocess
    result = subprocess.run(
        ["rg", "from loguru import|import loguru", "src/casare_rpa/domain/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1, "Found loguru imports in domain layer"

def test_domain_no_infrastructure_imports():
    """Domain layer must not import infrastructure."""
    import subprocess
    result = subprocess.run(
        ["rg", "from casare_rpa.infrastructure", "src/casare_rpa/domain/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1, "Found infrastructure imports in domain layer"
```

---

## Phase 3: HTTP Client Consolidation (16 hours)

**Agent**: `integrations` + `reviewer`
**Risk**: Medium-High (affects external communication)
**Parallelizable**: Yes (file-by-file)

### 3.1 Audit UnifiedHttpClient Capabilities (2 hours)

**Verify**:
- [ ] GET, POST, PUT, DELETE, PATCH
- [ ] Headers, cookies, auth
- [ ] Streaming support
- [ ] File upload/download
- [ ] WebSocket support (if needed)
- [ ] Multipart form data
- [ ] JSON encoding/decoding

**Gap Analysis**: Create feature matrix vs current aiohttp usage

### 3.2 Migrate Files (12 hours)

**Priority Order** (by usage frequency):

| Priority | File | Complexity | Reason |
|----------|------|------------|--------|
| P0 | `infrastructure/http/unified_http_client.py` | N/A | Already uses UnifiedHttpClient |
| P1 | `infrastructure/security/openai_oauth.py` | Medium | API calls |
| P1 | `infrastructure/security/oauth_server.py` | Medium | OAuth flows |
| P1 | `infrastructure/orchestrator/client.py` | High | Orchestrator communication |
| P1 | `infrastructure/orchestrator/robot_job_consumer.py` | High | Job processing |
| P1 | `infrastructure/security/google_oauth.py` | Medium | Google OAuth |
| P1 | `infrastructure/security/gemini_oauth.py` | Medium | Gemini OAuth |
| P2 | `infrastructure/resources/google_sheets_client.py` | Medium | Google API |
| P2 | `infrastructure/resources/gmail_client.py` | Medium | Google API |
| P2 | `infrastructure/resources/google_drive_client.py` | Medium | Google API |
| P2 | `infrastructure/resources/google_client.py` | Low | Base client |
| P2 | `infrastructure/resources/whatsapp_client.py` | Medium | WhatsApp API |
| P2 | `infrastructure/resources/telegram_client.py` | Medium | Telegram API |
| P3 | `triggers/manager.py` | Low | Trigger management |
| P3 | `triggers/implementations/google_trigger_base.py` | Low | Google triggers |
| P3 | `triggers/implementations/rss_trigger.py` | Low | RSS polling |
| P3 | `triggers/implementations/sse_trigger.py` | Medium | SSE handling |
| P3 | `nodes/http/http_super_node.py` | High | HTTP node |
| P3 | `nodes/http/http_auth.py` | Medium | HTTP auth |
| P3 | `nodes/http/http_advanced.py` | High | Advanced HTTP |
| P3 | `nodes/error_handling_nodes.py` | Low | Error handling |
| P3 | `nodes/browser/captcha_ai.py` | Low | Captcha solving |
| P3 | `infrastructure/services/registry.py` | Low | Registry service |
| P3 | `infrastructure/updater/tuf_updater.py` | High | Updates |
| P3 | `utils/pooling/http_session_pool.py` | N/A | Keep (internal) |
| P3 | `robot/auto_discovery.py` | Low | Discovery |
| P3 | `presentation/canvas/controllers/robot_controller.py` | Low | Canvas control |

**Migration Pattern**:
```python
# OLD
import aiohttp

async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# NEW
from casare_rpa.infrastructure.http import get_unified_http_client

client = await get_unified_http_client()
result = await client.get(url)
data = result.json()
```

### 3.3 Integration Tests (2 hours)

**Test Coverage**:
- [ ] OAuth flows work end-to-end
- [ ] Google API calls succeed
- [ ] HTTP nodes execute correctly
- [ ] Circuit breaker triggers on failures
- [ ] Rate limiting works

---

## Phase 4: Code Quality (3 hours)

**Agent**: `quality` + `reviewer`
**Risk**: Low
**Parallelizable**: Yes

### 4.1 Add Missing Type Hints (1 hour)

**Target**: Functions without return types

**Command**:
```bash
ruff check src/ --select ANN001,ANN002,ANN003,ANN201,ANN202,ANN204,ANN206
```

**Fix**: Add appropriate type hints based on context

### 4.2 Run mypy Validation (1 hour)

**Setup**:
```bash
# Incremental strict mode
mypy src/ --incremental --ignore-missing-imports
```

**Fix**: Address mypy errors by priority:
1. Missing imports
2. Type incompatibilities
3. Unused ignores

### 4.3 Update Documentation (1 hour)

**Files to Update**:
1. `.brain/systemPatterns.md` - Add ILogger pattern
2. `.claude/rules/02-coding-standards.md` - Modern type hints
3. `.claude/rules/06-enforcement.md` - Domain layer rules
4. `docs/developer-guide/architecture/index.md` - DI container

---

## Agent Assignments

| Phase | Primary Agent | Review Agent | Parallel Workers |
|-------|---------------|--------------|------------------|
| Phase 1 | `refactor` | `reviewer` | 1 (sequential) |
| Phase 2 | `architect` | `reviewer` | 1 (sequential) |
| Phase 3 | `integrations` | `reviewer` | 2-3 (file-level parallelism) |
| Phase 4 | `quality` | `reviewer` | 2 (type hints + tests) |

---

## Parallel Opportunities

### Phase 1 (Sequential)
- Unused imports must run first (baseline cleanup)
- Type hints after imports fixed
- TODOs independent (can run parallel)

### Phase 2 (Sequential)
- DI container first (dependency)
- File migration sequential (avoid conflicts)
- Tests after all migrations

### Phase 3 (Parallel)
- Files can be migrated in parallel groups:
  - Group A: OAuth files (3 workers)
  - Group B: Google clients (3 workers)
  - Group C: HTTP nodes (2 workers)
  - Group D: Triggers (2 workers)

### Phase 4 (Parallel)
- Type hints + mypy (independent)
- Docs (can run alongside)

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| Phase 1 | Low | Automated fixes, manual review for 2 files |
| Phase 2 | Medium | DI injection pattern; unit tests validate |
| Phase 3 | High | Integration tests; feature flag if needed |
| Phase 4 | Low | Tool-assisted; non-functional changes |

### Specific Risks

**Domain Logger Refactoring**:
- Risk: Runtime errors if logger not configured
- Mitigation: Configure logger in application bootstrap; add startup check

**HTTP Client Migration**:
- Risk: Different error handling behavior
- Mitigation: UnifiedHttpClient wraps aiohttp; preserve error types

**Type Hint Modernization**:
- Risk: Breaking older Python versions (<3.9)
- Mitigation: Project requires Python 3.12+

---

## Rollback Strategy

### Per-Phase Rollback

```bash
# After each phase, create a checkpoint commit
git commit -m "refactor: phase X complete"

# If issues arise, reset to checkpoint
git reset --hard HEAD~1
```

### Feature Flags

For Phase 3 (HTTP migration), consider feature flag:

```python
# UnifiedHttpClient with fallback
USE_UNIFIED_CLIENT = os.getenv("USE_UNIFIED_CLIENT", "true") == "true"

if USE_UNIFIED_CLIENT:
    from casare_rpa.infrastructure.http import UnifiedHttpClient
else:
    import aiohttp  # Fallback
```

---

## Testing Approach

### Phase 1 Testing
```bash
# Quick smoke test
pytest tests/ -x -v --timeout=10

# Lint verification
ruff check src/
```

### Phase 2 Testing
```bash
# Domain layer tests
pytest tests/domain/ -v

# Purity validation
pytest tests/domain/services/test_logger_purity.py -v
```

### Phase 3 Testing
```bash
# Integration tests for HTTP
pytest tests/infrastructure/http/ -v

# OAuth integration tests
pytest tests/infrastructure/security/ -k oauth -v

# HTTP node tests
pytest tests/nodes/http/ -v
```

### Phase 4 Testing
```bash
# Full test suite
pytest tests/ -v --cov=casare_rpa

# Type checking
mypy src/
```

---

## Dependencies

```
Phase 1 (Quick Wins)
    ↓
Phase 2 (Domain Purity) ← depends on clean imports from Phase 1
    ↓
Phase 3 (HTTP Consolidation) ← independent of Phase 2
    ↓
Phase 4 (Code Quality) ← depends on clean codebase
```

**Critical Path**: Phase 1 → Phase 2 → Phase 4
**Parallel Track**: Phase 3 can start after Phase 1

---

## Execution Checklist

### Pre-Execution
- [ ] Create worktree branch: `python scripts/create_worktree.py "refactor-whole-codebase"`
- [ ] Verify not on main: `python scripts/check_not_main_branch.py`
- [ ] Run baseline tests: `pytest tests/ --baseline`

### Phase 1
- [ ] Run `ruff check src/ --select F401 --fix`
- [ ] Manually review 2 files
- [ ] Run `ruff check src/ --select UP006,UP007,UP013 --fix`
- [ ] Resolve TODO comments or create issues
- [ ] Verify: `ruff check src/ --select F401`

### Phase 2
- [ ] Create `domain/interfaces/logger.py`
- [ ] Create `infrastructure/logging/loguru_adapter.py`
- [ ] Migrate 12 domain files
- [ ] Create `test_logger_purity.py`
- [ ] Verify: `pytest tests/domain/ -v`

### Phase 3
- [ ] Audit UnifiedHttpClient features
- [ ] Migrate OAuth files (3 parallel)
- [ ] Migrate Google clients (3 parallel)
- [ ] Migrate HTTP nodes (2 parallel)
- [ ] Migrate remaining files (2 parallel)
- [ ] Verify: `pytest tests/infrastructure/http/ tests/nodes/http/ -v`

### Phase 4
- [ ] Add missing type hints
- [ ] Run mypy and fix errors
- [ ] Update documentation
- [ ] Verify: `pytest tests/ -v && mypy src/`

### Post-Execution
- [ ] Full test suite: `pytest tests/ -v --cov=casare_rpa`
- [ ] Lint check: `ruff check src/`
- [ ] Format check: `ruff format --check src/`
- [ ] Type check: `mypy src/`
- [ ] Update `.brain/context/current.md`

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Unused imports (F401) | 0 |
| TODO comments | 0 (or tracked in issues) |
| Domain loguru imports | 0 |
| Raw aiohttp in infra/nodes | 0 |
| Test coverage maintained | >= current |
| mypy errors | 0 |
| Pre-commit hooks | All passing |

---

## Notes

- **Time estimates** assume familiarity with codebase
- **Phase 3** may require additional time if UnifiedHttpClient lacks features
- **Domain purity** is non-negotiable; Phase 2 must complete
- **Rollback** is always available via git

---

**Status**: Ready for user approval to proceed to EXECUTE phase.

# Testing Rules

**Part of:** `.brain/projectRules.md` | **See also:** `architecture.md`, `mocking.md`

## Domain Layer Tests

**Location:** `tests/domain/`
**Principle:** NO mocks. Pure logic with real domain objects.

| Aspect | Rule |
|--------|------|
| **Mocks** | NEVER |
| **Fixtures** | Real domain objects |
| **Async** | No async tests (domain is sync) |
| **Coverage Target** | 90%+ |

## Application Layer Tests

**Location:** `tests/application/`
**Principle:** Mock infrastructure, real domain objects.

| Aspect | Rule |
|--------|------|
| **Mocks** | Infrastructure only (repos, adapters) |
| **Fixtures** | Real domain objects, AsyncMock for async deps |
| **Async** | @pytest.mark.asyncio |
| **Coverage Target** | 85%+ |

## Infrastructure Layer Tests

**Location:** `tests/infrastructure/` or `tests/nodes/`
**Principle:** Mock ALL external APIs (Playwright, UIAutomation, DB, HTTP).

| Aspect | Rule |
|--------|------|
| **Mocks** | External APIs (Playwright, win32, DB, HTTP) |
| **Fixtures** | Use category fixtures (browser, desktop, http) |
| **Async** | @pytest.mark.asyncio |
| **Coverage Target** | 70%+ |

**Fixture Locations:**
- `tests/conftest.py` - Global fixtures
- `tests/nodes/browser/conftest.py` - Browser mocks
- `tests/nodes/desktop/conftest.py` - Desktop mocks

## Presentation Layer Tests

**Location:** `tests/presentation/`
**Principle:** Controller/logic testing. Minimal Qt widget testing.

| Aspect | Rule |
|--------|------|
| **Mocks** | Heavy Qt components, Use Cases |
| **Fixtures** | qtbot (pytest-qt) |
| **Async** | Avoid (Qt event loop complexity) |
| **Coverage Target** | 50%+ (Qt testing difficult) |

## Node Tests

**Location:** `tests/nodes/{category}/`
**Principle:** Test 3 scenarios (SUCCESS, ERROR, EDGE_CASES).

| Aspect | Rule |
|--------|------|
| **Mocks** | External resources only |
| **Fixtures** | execution_context, category-specific mocks |
| **Async** | @pytest.mark.asyncio |
| **Coverage Target** | 80%+ |

**Test Scenarios:**
1. **SUCCESS:** Node executes normally
2. **ERROR:** Node handles exceptions gracefully
3. **EDGE_CASES:** Timeout, missing params, invalid input

## Async Testing Rules

### Decision Tree
```
Is the function async def?
├─ YES
│  ├─ Mark test: @pytest.mark.asyncio
│  ├─ Mock with: AsyncMock()
│  └─ Assert with: assert_awaited_once()
└─ NO
   ├─ Regular def test_*()
   ├─ Mock with: Mock()
   └─ Assert with: assert_called_once()
```

### Common Mistakes
| Mistake | Problem | Fix |
|---------|---------|-----|
| `mock = Mock()` for async function | Won't track awaits | Use `AsyncMock()` |
| No `@pytest.mark.asyncio` | Test runs sync, hangs | Add decorator |
| `mock.assert_called_once()` on async | Wrong assertion | Use `mock.assert_awaited_once()` |

## TDD Checklist

### Before Committing
- [ ] Red phase: Test fails with clear error
- [ ] Green phase: Implementation passes test
- [ ] All related tests pass: `pytest tests/ -v`
- [ ] Coverage meets target
- [ ] No console warnings/errors

### Commit Checklist
- [ ] Tests written first (for features) or after (for bugs)
- [ ] All tests pass locally
- [ ] Commit message clear: `feat:` or `fix:`
- [ ] No debug code
- [ ] No commented-out code
- [ ] Imports clean (no unused)

---

**See:** `mocking.md` for mock decision table

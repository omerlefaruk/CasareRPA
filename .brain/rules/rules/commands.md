# Command Reference

**Part of:** `.brain/projectRules.md` | **See also:** `testing.md`

## Development Commands

| Task | Command | Notes |
|------|---------|-------|
| **Run App** | `python run.py` | Launch Canvas + Robot |
| **Install** | `pip install -e .` | Development install (editable) |
| **Test (Fast)** | `pytest tests/ -v -m "not slow"` | Unit + fast integration |
| **Test (Full)** | `pytest tests/ -v` | All tests including slow |
| **Test (Coverage)** | `pytest tests/ -v --cov=casare_rpa --cov-report=html` | Generate coverage report |
| **Test (Single)** | `pytest tests/path/test_file.py::test_name -vv -s` | Single test with output |
| **Test (First Fail)** | `pytest tests/ -x` | Stop on first failure |

## Code Quality

| Task | Command | Purpose |
|------|---------|---------|
| **Lint** | `ruff check src/ tests/` | Check code style |
| **Format** | `ruff format src/ tests/` | Auto-format code |
| **Type Check** | `mypy src/` | Static type analysis |

## Git Workflow

| Task | Command | Notes |
|------|---------|-------|
| **Status** | `git status` | See changes |
| **Diff** | `git diff` | Staged changes |
| **Log** | `git log --oneline -10` | Recent commits |
| **Commit** | `git add . && git commit -m "..."` | Always after tests pass |
| **Push** | `git push origin {branch}` | Push to remote |

## Quick Tests (TDD Cycle)

```bash
# Red: Write failing test
pytest tests/path/test_file.py::test_name -vv

# Green: Implement + Run
pytest tests/path/test_file.py::test_name -v

# Refactor + Full Suite
pytest tests/ -v

# Commit
git add tests/ src/ && git commit -m "feat: description"
```

## Debug Flags

```bash
# Show all print statements
pytest tests/ -s

# Very verbose output
pytest tests/ -vv

# Show local variables on failure
pytest tests/ -l

# Stop on first failure
pytest tests/ -x

# Last 5 failures
pytest tests/ --lf --maxfail=5
```

## Commit Message Format

```
feat: add login node for web automation
fix: resolve timeout on element click
refactor: extract node execution logic
test: add coverage for workflow validation
docs: update API reference for Orchestrator

# Detailed message (when needed)
feat: add login node for web automation

- Supports username/password input
- Handles 2FA via OTP
- Integrates with secure credential storage
```

## Branch Naming

| Prefix | Example | Purpose |
|--------|---------|---------|
| `feat/` | `feat/node-versioning` | New feature |
| `fix/` | `fix/selector-timeout` | Bug fix |
| `refactor/` | `refactor/execution-engine` | Code restructure |
| `docs/` | `docs/api-reference` | Documentation |
| `test/` | `test/node-coverage` | Test improvements |

---

**See:** `testing.md` for TDD checklist

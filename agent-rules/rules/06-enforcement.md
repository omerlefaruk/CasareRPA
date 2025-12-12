# Enforcement

## Mandatory Checks

Before completing any task, verify:

### Code Quality
- [ ] Type hints on all functions
- [ ] Docstrings on public APIs
- [ ] No `# type: ignore` without justification
- [ ] Async for all I/O

### Testing
- [ ] Tests pass: `pytest tests/ -v`
- [ ] New code has tests
- [ ] Edge cases covered

### Architecture
- [ ] Domain layer has no external imports
- [ ] Infrastructure implements domain interfaces
- [ ] No circular imports

### Documentation
- [ ] `_index.md` updated if structure changed
- [ ] Docstrings match implementation
- [ ] CHANGELOG updated for features

## Blockers
If any check fails, STOP and fix before proceeding.

## Exceptions
Document exceptions with justification in commit message or plan.

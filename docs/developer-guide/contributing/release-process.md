# Release Process

This document describes the release workflow for CasareRPA, including version numbering, changelog updates, and distribution.

## Version Numbering (Semantic Versioning)

CasareRPA follows [Semantic Versioning](https://semver.org/) (SemVer):

```
MAJOR.MINOR.PATCH
```

| Component | When to Increment | Example |
|-----------|------------------|---------|
| **MAJOR** | Breaking changes | `2.0.0` -> `3.0.0` |
| **MINOR** | New features (backward compatible) | `3.0.0` -> `3.1.0` |
| **PATCH** | Bug fixes (backward compatible) | `3.1.0` -> `3.1.1` |

### Pre-release Versions

```
3.1.0-alpha.1    # Alpha release
3.1.0-beta.1     # Beta release
3.1.0-rc.1       # Release candidate
```

### Current Version

The current version is defined in `pyproject.toml`:

```toml
[project]
name = "casare-rpa"
version = "3.0.0"
```

## Release Types

### Patch Release (x.x.PATCH)

Bug fixes only, no new features.

```bash
# Example: 3.0.0 -> 3.0.1
```

- Fix critical bugs
- Security patches
- Documentation fixes
- No API changes

### Minor Release (x.MINOR.0)

New features, backward compatible.

```bash
# Example: 3.0.1 -> 3.1.0
```

- New nodes
- New UI features
- Enhanced functionality
- Deprecations (not removals)

### Major Release (MAJOR.0.0)

Breaking changes requiring migration.

```bash
# Example: 3.1.0 -> 4.0.0
```

- API changes
- Removed deprecated features
- Architecture changes
- Requires migration guide

## Changelog Updates

Maintain `CHANGELOG.md` using [Keep a Changelog](https://keepachangelog.com/) format:

### Format

```markdown
# Changelog

All notable changes to CasareRPA will be documented in this file.

## [Unreleased]

### Added
- New feature description

### Changed
- Modified behavior description

### Deprecated
- Features to be removed in future

### Removed
- Removed features

### Fixed
- Bug fix description

### Security
- Security fix description

## [3.1.0] - 2025-01-15

### Added
- PDF extraction node for document automation (#123)
- Dark mode toggle in settings (#456)

### Fixed
- Browser selector timeout on slow networks (#789)
- Memory leak in execution context cleanup (#101)

## [3.0.0] - 2024-12-01

### Changed
- BREAKING: Migrated to Clean DDD architecture
- See docs/MIGRATION_GUIDE_V3.md for migration steps
```

### Guidelines

- Write entries as you develop (not at release time)
- Use imperative mood ("Add", not "Added")
- Link to issues/PRs with `(#123)`
- Group by category (Added, Changed, Fixed, etc.)

## Release Workflow

### 1. Prepare Release

```bash
# Ensure on main branch
git checkout main
git pull origin main

# Verify all tests pass
pytest tests/ -v

# Check for security vulnerabilities
pip-audit

# Review unreleased changelog entries
cat CHANGELOG.md
```

### 2. Create Release Branch

For minor/major releases, create a release branch:

```bash
# Create release branch
git checkout -b release/3.1.0

# For patch releases, work directly on main
```

### 3. Update Version

Update version in `pyproject.toml`:

```toml
[project]
version = "3.1.0"
```

### 4. Update Changelog

Move entries from `[Unreleased]` to new version section:

```markdown
## [Unreleased]

## [3.1.0] - 2025-01-15

### Added
- PDF extraction node for document automation (#123)
...
```

### 5. Create Release Commit

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v3.1.0"
```

### 6. Create Git Tag

```bash
# Create annotated tag
git tag -a v3.1.0 -m "Release v3.1.0"

# Push tag
git push origin v3.1.0
```

### 7. Merge to Main (if on release branch)

```bash
git checkout main
git merge release/3.1.0
git push origin main
```

### 8. Create GitHub Release

```bash
# Via GitHub CLI
gh release create v3.1.0 \
  --title "v3.1.0" \
  --notes-file RELEASE_NOTES.md

# Or via GitHub UI
# 1. Go to Releases
# 2. Click "Create new release"
# 3. Select tag v3.1.0
# 4. Add release notes
# 5. Attach build artifacts
# 6. Publish
```

## Testing Requirements

Before any release:

### Required Checks

| Check | Command | Threshold |
|-------|---------|-----------|
| Unit tests | `pytest tests/ -v` | All pass |
| Coverage | `pytest --cov=casare_rpa` | >= 75% |
| Lint | `ruff check src/` | No errors |
| Security | `pip-audit` | No high/critical |
| Type check | `mypy src/` | Informational |

### Manual Testing Checklist

- [ ] Application launches successfully
- [ ] Can create/save/load workflows
- [ ] Browser automation nodes work
- [ ] Desktop automation nodes work
- [ ] Orchestrator server starts
- [ ] Robot agent connects to orchestrator
- [ ] No console errors/warnings

## Build Process

### Development Build

```bash
# Install in development mode
pip install -e ".[dev]"
```

### Production Build

```bash
# Build wheel and source distribution
python -m build

# Output in dist/
# casare_rpa-3.1.0-py3-none-any.whl
# casare_rpa-3.1.0.tar.gz
```

### Verify Build

```bash
# Create clean environment
python -m venv test_env
test_env\Scripts\activate

# Install from wheel
pip install dist/casare_rpa-3.1.0-py3-none-any.whl

# Verify
python -c "import casare_rpa; print(casare_rpa.__version__)"
```

## Distribution

### PyPI (Future)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### GitHub Releases

Attach build artifacts to GitHub releases:

1. Navigate to Releases
2. Edit the release
3. Attach `.whl` and `.tar.gz` files
4. Update release notes if needed

### Direct Installation

Users can install directly from GitHub:

```bash
pip install git+https://github.com/omerlefaruk/CasareRPA.git@v3.1.0
```

## Breaking Changes

For releases with breaking changes:

### 1. Document in Changelog

```markdown
## [4.0.0] - 2025-06-01

### Changed
- BREAKING: Renamed `ExecutionContext` to `RunContext`
- BREAKING: Changed `node.execute()` signature
```

### 2. Create Migration Guide

Create `docs/migrations/v4-migration.md`:

```markdown
# Migration Guide: v3.x to v4.0

## Breaking Changes

### ExecutionContext renamed to RunContext

**Before (v3.x):**
```python
from casare_rpa.infrastructure.execution import ExecutionContext

async def execute(self, context: ExecutionContext):
    ...
```

**After (v4.0):**
```python
from casare_rpa.domain.interfaces import RunContext

async def execute(self, context: RunContext):
    ...
```

### Migration Steps

1. Update imports...
2. Rename parameters...
```

### 3. Add Deprecation Warnings (if possible)

In v3.x, add warnings for features to be removed in v4.0:

```python
import warnings

class ExecutionContext:
    def __init__(self):
        warnings.warn(
            "ExecutionContext is deprecated, use RunContext instead",
            DeprecationWarning,
            stacklevel=2
        )
```

## Release Checklist

### Before Release

- [ ] All tests passing
- [ ] Coverage meets threshold
- [ ] No lint errors
- [ ] No security vulnerabilities
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Documentation current
- [ ] Breaking changes documented
- [ ] Migration guide (if needed)

### During Release

- [ ] Create release branch (minor/major)
- [ ] Update version in pyproject.toml
- [ ] Finalize changelog
- [ ] Create release commit
- [ ] Create annotated tag
- [ ] Push tag to origin
- [ ] Create GitHub release
- [ ] Attach build artifacts

### After Release

- [ ] Verify GitHub release published
- [ ] Test installation from release
- [ ] Announce release (if applicable)
- [ ] Close related milestone
- [ ] Update documentation site

## Hotfix Process

For critical bugs in production:

```bash
# Create hotfix branch from tag
git checkout -b hotfix/3.0.1 v3.0.0

# Make fix
# ... code changes ...

# Update version
# pyproject.toml: version = "3.0.1"

# Update changelog
# Add [3.0.1] section

# Commit and tag
git commit -m "fix: critical bug description"
git tag -a v3.0.1 -m "Hotfix v3.0.1"

# Merge to main
git checkout main
git merge hotfix/3.0.1
git push origin main v3.0.1

# Create release
gh release create v3.0.1 --title "v3.0.1 (Hotfix)"
```

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 3.0.0 | 2024-12-01 | Clean DDD architecture |
| 2.0.0 | 2024-06-01 | Orchestrator introduction |
| 1.0.0 | 2024-01-01 | Initial release |

## Related Documentation

- [Coding Standards](coding-standards.md) - Code quality requirements
- [Testing Guide](testing.md) - Testing requirements
- [Pull Request Guidelines](pull-requests.md) - PR process

---

**Questions?** Open an issue for release-related questions.

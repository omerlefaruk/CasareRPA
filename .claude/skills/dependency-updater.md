---
name: dependency-updater
description: Analyze, update, and manage Python dependencies in pyproject.toml, checking for version compatibility, security vulnerabilities, and suggesting upgrades.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: dependencies
---

When managing dependencies, follow this systematic approach:

## Dependency Analysis Process

### 1. Current Dependency Inventory

```bash
# List all installed packages with versions
pip list

# Show dependency tree
pip install pipdeptree
pipdeptree

# Check for outdated packages
pip list --outdated

# Show package details
pip show <package_name>
```

### 2. Security Vulnerability Check

```bash
# Check for known vulnerabilities (requires safety or pip-audit)
pip install pip-audit
pip-audit

# Alternative using safety
pip install safety
safety check
```

### 3. Compatibility Analysis

For each package, check:
- Python version compatibility (must support Python 3.12+)
- Dependency conflicts
- Breaking changes between versions
- Deprecation warnings

## Update Strategy

### Categorize Dependencies

**Core Framework** (most critical, update cautiously):
- `PySide6` - Qt GUI framework
- `NodeGraphQt` - Node graph visualization
- `Playwright` - Browser automation
- `qasync` - Qt + asyncio bridge

**Infrastructure**:
- `asyncpg` - PostgreSQL async driver
- `aiomysql` - MySQL async driver
- `aiohttp` - Async HTTP client/server
- `aioboto3` - AWS SDK

**Utilities**:
- `loguru` - Logging
- `orjson` - Fast JSON
- `psutil` - System utilities
- `python-dateutil` - Date parsing

**Development**:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `mypy` - Type checking

### Update Priority

1. **Critical Security Fixes** - Update immediately
2. **Bug Fixes** - Update in next patch release
3. **New Features** - Evaluate need, update in minor release
4. **Major Versions** - Plan migration, update in major release

### Version Pinning Strategy

```toml
[project]
# Core dependencies: Pin to minor version
dependencies = [
    "PySide6>=6.6.0,<6.7.0",  # Pin to 6.6.x
    "NodeGraphQt>=0.6.30,<0.7.0",  # Pin to 0.6.x
    "Playwright>=1.40.0,<1.41.0",  # Pin to 1.40.x

    # Infrastructure: Pin to patch version for stability
    "asyncpg>=0.29.0,<0.30.0",
    "aiohttp>=3.9.0,<3.10.0",

    # Utilities: Allow minor updates
    "loguru>=0.7.2",
    "orjson>=3.9.0",

    # Development: Latest compatible
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
```

## Update Workflow

### Step 1: Research Updates

For each outdated package:

```bash
# Check changelog on PyPI or GitHub
# Look for:
# - Breaking changes
# - Deprecations
# - New features relevant to CasareRPA
# - Bug fixes
# - Security patches

# Example: Check Playwright changelog
# Visit: https://github.com/microsoft/playwright-python/releases
```

### Step 2: Update pyproject.toml

```toml
[project]
name = "casare-rpa"
version = "2.1.0"
requires-python = ">=3.12"
dependencies = [
    # Update version constraints based on research
    "PySide6>=6.6.1,<6.7.0",  # Updated from 6.6.0
    "Playwright>=1.41.0,<1.42.0",  # Updated from 1.40.0

    # ... rest of dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",  # Updated
    "pytest-asyncio>=0.23.0",  # Updated
    "pytest-cov>=4.1.0",  # Updated
    "mypy>=1.8.0",  # Updated
]
```

### Step 3: Test Compatibility

```bash
# Create test environment
python -m venv venv_test
source venv_test/bin/activate  # or venv_test\Scripts\activate on Windows

# Install with updated dependencies
pip install -e .

# Run full test suite
pytest tests/ -v

# Check for deprecation warnings
pytest tests/ -v -W error::DeprecationWarning

# Test critical workflows manually
python run.py  # Start application
# Test: Create workflow, execute nodes, check UI

# Run type checker if available
mypy src/casare_rpa
```

### Step 4: Update Documentation

```markdown
# CHANGELOG.md

## [2.1.1] - 2025-XX-XX

### Dependencies
- Updated PySide6 from 6.6.0 to 6.6.1 (bug fixes)
- Updated Playwright from 1.40.0 to 1.41.0 (new features)
- Updated pytest from 7.4.0 to 8.0.0 (performance improvements)
- Updated asyncpg from 0.29.0 to 0.29.2 (security patch)

### Breaking Changes
None

### Migration Notes
None required - all updates are backwards compatible.
```

## Handling Breaking Changes

### Example: Major Version Update

```toml
# Updating from PySide6 6.6.x to 6.7.x (hypothetical)

# Step 1: Research breaking changes
# - Read migration guide
# - Identify deprecated APIs used in codebase

# Step 2: Create compatibility layer
# src/casare_rpa/compat/qt.py
try:
    from PySide6.QtCore import Qt as QtNamespace
    # PySide6 6.7+ uses QtNamespace
    Qt = QtNamespace
except ImportError:
    from PySide6.QtCore import Qt
    # PySide6 6.6 uses Qt directly

# Step 3: Update imports across codebase
# OLD: from PySide6.QtCore import Qt
# NEW: from casare_rpa.compat.qt import Qt

# Step 4: Update pyproject.toml
dependencies = [
    "PySide6>=6.7.0,<6.8.0",  # Updated to 6.7.x
]

# Step 5: Update CHANGELOG with migration guide
```

## Dependency Conflict Resolution

```bash
# If pip reports conflicts:
# ERROR: package-a 2.0 requires package-b<2.0, but you have package-b 2.1

# Strategy 1: Find compatible versions
pip install "package-a>=1.9,<2.0"  # Use older version of package-a

# Strategy 2: Check if newer version of package-a supports package-b 2.1
pip install --upgrade package-a

# Strategy 3: Use dependency resolver
pip install --use-feature=2020-resolver

# Strategy 4: If no resolution, consider alternatives
# Replace package-a with alternative-package
```

## Special Considerations for CasareRPA

### Playwright Updates

```bash
# After updating Playwright, reinstall browsers
playwright install chromium

# Test browser automation nodes
pytest tests/nodes/browser/ -v
```

### PySide6 Updates

```python
# Test GUI components after update
# - MainWindow initialization
# - NodeGraphQt integration
# - Property panels
# - Event handling

# Check for deprecation warnings
import warnings
warnings.filterwarnings('error', category=DeprecationWarning)

# Run application
python run.py
```

### Database Driver Updates

```bash
# Test database connections
pytest tests/infrastructure/resources/test_database_manager.py -v

# Test node execution
pytest tests/nodes/database/ -v
```

## Dependency Report Template

```markdown
# Dependency Update Report - <Date>

## Proposed Updates

| Package | Current | Latest | Type | Priority | Notes |
|---------|---------|--------|------|----------|-------|
| PySide6 | 6.6.0 | 6.6.1 | Patch | High | Bug fixes for Qt widgets |
| Playwright | 1.40.0 | 1.41.2 | Minor | Medium | New browser APIs |
| pytest | 7.4.0 | 8.0.0 | Major | Low | Performance improvements |

## Security Vulnerabilities

- **asyncpg 0.29.0**: CVE-2024-XXXXX (SQL injection fix in 0.29.2)
  - Severity: High
  - Action: Update immediately to 0.29.2

## Breaking Changes

### pytest 8.0.0
- Changed default test discovery pattern
- Impact: None (we use explicit test paths)
- Migration: No changes needed

## Test Results

- ✅ All 1,255 tests pass
- ✅ No new deprecation warnings
- ✅ Application starts successfully
- ✅ Critical workflows tested manually

## Recommendation

Proceed with updates. No breaking changes affecting CasareRPA.
```

## Usage

When user requests dependency updates:

1. Run dependency analysis commands
2. Check for security vulnerabilities
3. Research each update (changelogs, breaking changes)
4. Update `pyproject.toml` with new version constraints
5. Test in clean environment
6. Generate dependency update report
7. Update `CHANGELOG.md` if applicable
8. Commit with appropriate message:
   ```bash
   build: update dependencies for security and compatibility

   - Update asyncpg to 0.29.2 (security patch)
   - Update PySide6 to 6.6.1 (bug fixes)
   - Update Playwright to 1.41.0 (new features)

   All tests pass. No breaking changes.
   ```

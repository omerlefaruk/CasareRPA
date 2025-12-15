# CasareRPA Testing Documentation Index

Complete navigation guide for all testing-related documentation and patterns.

## Documents Overview

### 1. **TESTING_INDEX.md** (This File)
Navigation and overview of all testing documentation.

### 2. **TEST_IMPLEMENTATION_QUICK_START.md** ⭐ START HERE
- 5-minute overview
- Copy-paste templates for conftest.py, test_imports.py, test_node.py
- Step-by-step implementation guide
- Common patterns quick reference
- Troubleshooting section

**When to use**: You need to write tests NOW and want ready-to-use code.

### 3. **TESTING_PATTERNS.md**
Comprehensive guide covering:
- File structure and pytest configuration
- ExecutionContext setup and interface
- Fixture patterns (mock data, async clients, execution context)
- Async test patterns
- Mocking patterns (external clients, imports, side effects)
- Test organization
- Import verification tests
- Google and HTTP node testing patterns
- Error handling and running tests

**When to use**: You need to understand the full testing approach and architecture.

### 4. **GOOGLE_NODE_TEST_EXAMPLE.md**
Complete, runnable example tests including:
- conftest.py with mock data and fixtures
- test_drive_upload_node.py with execution tests
- test_drive_list_files_node.py with pagination tests
- test_google_imports.py with import verification

**When to use**: You're implementing Google API node tests and need real examples.

### 5. **TEST_PATTERNS_SUMMARY.md**
File reference and location guide:
- Index of existing test files
- Exact line numbers for each pattern
- File mapping for quick lookup
- Pattern index table

**When to use**: You need to find where a specific pattern is used in the codebase.

---

## Quick Navigation

### By Task

#### "I need to write tests for a new integration node"
1. Start: **TEST_IMPLEMENTATION_QUICK_START.md**
2. Reference: **TESTING_PATTERNS.md** sections on ExecutionContext and mocking
3. Learn by example: **GOOGLE_NODE_TEST_EXAMPLE.md**
4. Verify patterns: **TEST_PATTERNS_SUMMARY.md**

#### "I want to understand the testing architecture"
1. Start: **TESTING_PATTERNS.md** - ExecutionContext Setup section
2. Learn: TESTING_PATTERNS.md - DDD 2025 architecture sections
3. Review: Existing tests in `tests/infrastructure/ai/`

#### "I need to mock an external API client"
1. Quick ref: **TEST_IMPLEMENTATION_QUICK_START.md** - Mocking Patterns section
2. Full details: **TESTING_PATTERNS.md** - Mocking Patterns section
3. Example: **GOOGLE_NODE_TEST_EXAMPLE.md** - conftest.py fixtures

#### "I'm stuck with a test error"
1. Solutions: **TEST_IMPLEMENTATION_QUICK_START.md** - Troubleshooting section
2. Examples: **GOOGLE_NODE_TEST_EXAMPLE.md** - Real working code

#### "I need to find where pattern X is used"
1. Index: **TEST_PATTERNS_SUMMARY.md** - File Mapping section
2. Look up file and line numbers
3. View in codebase

### By Experience Level

#### Beginner (Never written these tests before)
**Follow this path**:
1. Read: TEST_IMPLEMENTATION_QUICK_START.md (5-10 min)
2. Copy: Templates for conftest.py, test_imports.py, test_node.py
3. Learn: Review GOOGLE_NODE_TEST_EXAMPLE.md
4. Do: Write first test file
5. Verify: Run `pytest tests/ -v`
6. Reference: Use TESTING_PATTERNS.md for deeper understanding

#### Intermediate (Written tests, need patterns)
**Follow this path**:
1. Quick ref: TEST_IMPLEMENTATION_QUICK_START.md quick reference tables
2. Copy: Pattern-specific examples from TESTING_PATTERNS.md
3. Adapt: Apply to your integration node
4. Verify: Check TEST_PATTERNS_SUMMARY.md for existing examples

#### Advanced (Familiar with codebase)
**Follow this path**:
1. Review: TESTING_PATTERNS.md for architecture details
2. Reference: TEST_PATTERNS_SUMMARY.md for file locations
3. Implement: Create test suite following established patterns
4. Extend: Use GOOGLE_NODE_TEST_EXAMPLE.md as reference

---

## Key Concepts

### ExecutionContext
**What**: Test execution environment that nodes receive
**Where**: `src/casare_rpa/infrastructure/execution/execution_context.py`
**Learn**: TESTING_PATTERNS.md - ExecutionContext Setup section
**Example**: GOOGLE_NODE_TEST_EXAMPLE.md - conftest.py fixture

### Async Tests with pytest-asyncio
**What**: Testing async methods using @pytest.mark.asyncio
**Where**: `tests/infrastructure/ai/test_playwright_mcp.py`
**Learn**: TESTING_PATTERNS.md - Async Test Pattern section
**Example**: Multiple examples in GOOGLE_NODE_TEST_EXAMPLE.md

### Mocking External Clients
**What**: Using AsyncMock to simulate external APIs
**Where**: `tests/infrastructure/ai/conftest.py` and test files
**Learn**: TESTING_PATTERNS.md - Mocking Patterns section
**Example**: GOOGLE_NODE_TEST_EXAMPLE.md - conftest.py fixtures

### Test Organization
**What**: Using test classes to group related tests
**Where**: `tests/infrastructure/ai/test_page_analyzer.py`
**Learn**: TESTING_PATTERNS.md - Test Organization section
**Example**: TEST_IMPLEMENTATION_QUICK_START.md - Pattern 4

### Pytest Configuration
**What**: pytest settings and markers
**Where**: `pyproject.toml` [tool.pytest.ini_options]
**Learn**: TESTING_PATTERNS.md - File Structure section
**Reference**: TEST_PATTERNS_SUMMARY.md - Pytest Configuration section

---

## Document Comparison

| Aspect | Quick Start | Full Patterns | Examples | Summary |
|--------|-----------|---------------|----------|---------|
| Length | Short | Long | Long | Medium |
| Code | Many | Some | All | None |
| Copy-paste ready | Yes | Partial | Yes | No |
| Explains why | No | Yes | Yes | No |
| Line references | No | Some | Some | Yes |
| Best for | Implementation | Understanding | Learning | Navigation |

---

## Folder Structure

```
CasareRPA/
├── TESTING_INDEX.md                 ← You are here
├── TEST_IMPLEMENTATION_QUICK_START.md
├── TESTING_PATTERNS.md
├── GOOGLE_NODE_TEST_EXAMPLE.md
├── TEST_PATTERNS_SUMMARY.md
│
├── tests/
│   └── infrastructure/
│       ├── ai/                       ← Reference implementation
│       │   ├── __init__.py
│       │   ├── conftest.py
│       │   ├── test_imports.py
│       │   ├── test_page_analyzer.py
│       │   ├── test_playwright_mcp.py
│       │   └── test_url_detection.py
│       └── (future: google/, http/, etc.)
│
├── src/
│   └── casare_rpa/
│       ├── domain/
│       │   ├── interfaces/execution_context.py
│       │   └── ...
│       ├── infrastructure/
│       │   ├── execution/execution_context.py
│       │   └── ...
│       └── nodes/
│           ├── google/
│           ├── http/
│           └── ...
│
└── pyproject.toml                   ← Pytest configuration
```

---

## Common Workflows

### Workflow 1: Create Tests for Google Drive Upload Node

**Time**: ~30 minutes

```
1. Read TEST_IMPLEMENTATION_QUICK_START.md (5 min)
   ↓
2. Copy templates and customize for Google module (5 min)
   ↓
3. Review GOOGLE_NODE_TEST_EXAMPLE.md test_drive_upload_node.py (10 min)
   ↓
4. Write conftest.py, test_imports.py, test_node.py (10 min)
   ↓
5. Run pytest tests/infrastructure/google/ -v
   ↓
6. Check coverage: pytest --cov
   ↓
7. Reference TESTING_PATTERNS.md for specific questions
```

### Workflow 2: Understand Test Architecture

**Time**: ~1 hour

```
1. Read TESTING_PATTERNS.md - ExecutionContext section (15 min)
   ↓
2. Review tests/infrastructure/ai/conftest.py (10 min)
   ↓
3. Read TESTING_PATTERNS.md - Async Test Pattern (15 min)
   ↓
4. Review tests/infrastructure/ai/test_playwright_mcp.py (15 min)
   ↓
5. Understand patterns in context (5 min)
```

### Workflow 3: Fix Test That's Failing

**Time**: ~15 minutes

```
1. Check TEST_IMPLEMENTATION_QUICK_START.md - Troubleshooting (5 min)
   ↓
2. If not found, search TEST_PATTERNS_SUMMARY.md - Pattern Index (5 min)
   ↓
3. Find file and line numbers
   ↓
4. Review working example
   ↓
5. Apply fix to your test
```

---

## Key Files in Codebase

### Test Files (Reference)
- `tests/infrastructure/ai/conftest.py` - Fixture patterns
- `tests/infrastructure/ai/test_imports.py` - Import verification
- `tests/infrastructure/ai/test_page_analyzer.py` - Test class organization
- `tests/infrastructure/ai/test_playwright_mcp.py` - Async testing patterns

### Implementation Files (Learn From)
- `src/casare_rpa/infrastructure/execution/execution_context.py` - ExecutionContext
- `src/casare_rpa/domain/interfaces/execution_context.py` - IExecutionContext
- `src/casare_rpa/nodes/google/google_base.py` - Google node base
- `src/casare_rpa/nodes/google/drive/drive_files.py` - Real node example
- `src/casare_rpa/infrastructure/resources/google_client.py` - API client

### Configuration
- `pyproject.toml` - Pytest configuration

---

## Search Within Documents

### In TEST_IMPLEMENTATION_QUICK_START.md, search for:
- "Copy-Paste Template" - Ready-to-use code
- "Step-by-Step" - Implementation guide
- "Common Patterns Quick Reference" - Pattern lookup
- "Troubleshooting" - Error solutions

### In TESTING_PATTERNS.md, search for:
- "ExecutionContext Setup" - How to initialize context
- "Fixture Patterns" - Different fixture types
- "Async Test Pattern" - Async test examples
- "For Google Nodes" - Node-specific guidance
- "Error Handling Tests" - Testing error scenarios

### In GOOGLE_NODE_TEST_EXAMPLE.md, search for:
- "conftest.py" - Fixture setup
- "TestDriveUploadFileNode" - Real test example
- "test_upload_file_success" - Success path test
- "test_upload_file_auth_error" - Error handling

### In TEST_PATTERNS_SUMMARY.md, search for:
- "File Mapping" - Where to find things
- "Quick Pattern Index" - Pattern lookup table
- "Existing Test Files" - Current tests

---

## Checklists

### Before Writing Tests
- [ ] Read TEST_IMPLEMENTATION_QUICK_START.md
- [ ] Understand ExecutionContext (TESTING_PATTERNS.md)
- [ ] Know which mocking pattern to use
- [ ] Have example node implementation

### While Writing Tests
- [ ] Create conftest.py with fixtures
- [ ] Create test_imports.py
- [ ] Create test_{node_name}.py
- [ ] Use @pytest.mark.asyncio for async tests
- [ ] Test success path
- [ ] Test error paths
- [ ] Test edge cases

### Before Submitting Tests
- [ ] Run: `pytest tests/ -v`
- [ ] Check coverage: `pytest tests/ --cov`
- [ ] Coverage >= 75%
- [ ] All tests pass
- [ ] No warnings or errors
- [ ] Docstrings for all tests
- [ ] Clear assertion messages

---

## Integration with CLAUDE.md

This testing guide complements the main **CLAUDE.md** documentation:
- CLAUDE.md: Overall architecture and DDD patterns
- This guide: Specific testing implementation patterns
- Cross-reference: CLAUDE.md links to testing rules in `.claude/rules/`

See CLAUDE.md section "On-Demand Docs" for other references.

---

## FAQ

**Q: Which document should I read first?**
A: TEST_IMPLEMENTATION_QUICK_START.md for a fast overview, then TESTING_PATTERNS.md for details.

**Q: Can I copy code from GOOGLE_NODE_TEST_EXAMPLE.md?**
A: Yes! It's designed for that. Replace placeholders with your module/class names.

**Q: Where is the existing test code?**
A: `tests/infrastructure/ai/` - use as reference for patterns.

**Q: How do I know my tests are good enough?**
A: Run `pytest tests/ --cov` - need 75%+ coverage. All tests should pass.

**Q: What's the difference between these docs?**
A: See "Document Comparison" table above for quick guide.

**Q: How long to write tests for a new node?**
A: ~30-45 minutes following the workflow in TEST_IMPLEMENTATION_QUICK_START.md

**Q: Can I use these patterns for non-Google nodes?**
A: Yes! Patterns are generic. GOOGLE_NODE_TEST_EXAMPLE.md is just an example.

---

## Version Info

- **Created**: December 2025
- **CasareRPA Version**: Current (Python 3.12, PySide6, Playwright)
- **Pytest Version**: 6.0+
- **Python Version**: 3.12+

---

## Support

If you need help:
1. Check TEST_IMPLEMENTATION_QUICK_START.md - Troubleshooting
2. Search documents for your question
3. Review working examples in `tests/infrastructure/ai/`
4. Check TESTING_PATTERNS.md detailed sections

---

## Document Maintenance

- Last updated: December 2025
- Tested with: Pytest 7.x, Python 3.12
- All examples verified to work with current codebase

To update these docs: Follow patterns in CLAUDE.md and maintain consistency with existing tests.

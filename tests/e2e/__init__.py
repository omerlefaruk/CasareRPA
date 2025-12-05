"""
CasareRPA - End-to-End (E2E) Test Suite.

E2E tests execute REAL workflows with no mocks. They validate:
- Complete workflow execution paths
- Node interactions and data flow
- Variable management
- Control flow (loops, conditionals)
- Browser automation (with real Playwright)

Unlike unit tests, E2E tests:
- Use real ExecutionContext (not mocked)
- Execute actual node logic
- Perform real browser operations (headless)
- Test complete workflows from Start to End

Configuration:
- Browser tests use pytest-aiohttp for test server
- HTTP tests use httpbin.org (external)
- Default workflow timeout: 30 seconds

Usage:
    pytest tests/e2e/ -v                    # Run all E2E tests
    pytest tests/e2e/ -v -m "not slow"      # Skip slow browser tests
    pytest tests/e2e/ -v -k "variable"      # Run only variable-related tests
"""

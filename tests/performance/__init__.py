"""
Performance tests for CasareRPA baseline measurements.

Modules:
- test_node_registry_perf: Node registry import and lookup performance
- test_http_client_perf: HTTP client, rate limiter, circuit breaker performance
- test_ui_performance: UI component initialization and dispatch latency
- test_import_times: Module import time analysis
- test_performance_regression: Regression guard tests
- test_workflow_performance: Workflow execution performance

Run all performance tests:
    pytest tests/performance/ -v

Run with benchmark comparison:
    pytest tests/performance/ -v --benchmark-compare

Run slow tests only:
    pytest tests/performance/ -v -m slow
"""

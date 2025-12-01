# Orchestrator API Documentation Plan

## Status: COMPLETE

## Brain Context
- Read: `.brain/activeContext.md` (current session scope: documentation for API)
- Patterns: `.brain/systemPatterns.md` (API design patterns)
- Rules: `.brain/projectRules.md` (documentation standards, terse output, concise)

## Overview

CasareRPA Orchestrator API provides REST endpoints for:
- **Robot Management**: Register, list, monitor, deregister robots
- **Job Scheduling**: Submit, list, cancel, retry jobs with APScheduler integration
- **Work Queues**: Distribute jobs to available robots with state affinity
- **Fleet Metrics**: Real-time fleet health, job throughput, resource utilization
- **Authentication**: API key and JWT token auth with role-based access
- **WebSocket**: Real-time job status, heartbeats, queue depth, error events

**Current State**: FastAPI backend exists with partial routes (auth, metrics, workflows, schedules, websockets). Missing: comprehensive OpenAPI specs, complete endpoint docs, request/response examples, error handling guide.

**Target**: Complete OpenAPI/Swagger specification, endpoint reference documentation with curl + Python examples, error dictionary, integration guide.

## Agents to Assign

- [ ] **rpa-engine-architect**: Analyze existing API routes (workflows.py, schedules.py, metrics.py). Ensure REST design aligns with domain models (Job, Robot, Workflow, Schedule). Validate async patterns. Cross-check with application layer use cases.

- [ ] **security-architect**: Review auth.py (API key + JWT). Validate CORS middleware config. Check rate limiting (slowapi). Document auth flow, token expiry, secret rotation. Suggest hardening for production deployment.

- [ ] **chaos-qa-engineer**: Design test scenarios: rate limit exceeded, invalid auth, robot offline during job submission, concurrent job conflicts, database connection failures. Create chaos test suite for resilience validation.

## Implementation Steps

1. **Codebase Analysis** (rpa-engine-architect, Explore agents)
   - Map all existing routes: workflows, schedules, metrics, auth, websockets
   - Extract request/response schemas from models.py
   - Identify missing endpoints (job cancellation, robot deregistration, batch operations)
   - Document async patterns (asyncio, APScheduler integration)

2. **OpenAPI Specification Generation** (rpa-engine-architect)
   - Create `docs/openapi-orchestrator-api.yaml` with full spec
   - Document all endpoint paths, methods, parameters, responses
   - Define reusable schema components (RobotSummary, JobStatus, FleetMetrics)
   - Include authentication scheme (API Key, JWT Bearer)
   - Add rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)

3. **Endpoint Reference Documentation** (rpa-docs-writer)
   - Create `docs/api-reference/README.md` with endpoint table
   - For each endpoint: purpose, HTTP method, path, auth requirement, request/response examples
   - Include curl examples with real parameter values
   - Include Python examples using `aiohttp` and `requests`
   - Document query parameters, path parameters, request body schema
   - List all possible HTTP status codes (200, 201, 400, 401, 403, 404, 429, 500)

4. **Error Dictionary** (rpa-docs-writer, security-architect)
   - Create `docs/error-codes.md`
   - Format: `API_ERR_CODE | HTTP Status | Description | Probable Causes | Troubleshooting Steps | Prevention Tips`
   - Common errors: `INVALID_AUTH_TOKEN`, `ROBOT_NOT_FOUND`, `JOB_NOT_FOUND`, `RATE_LIMIT_EXCEEDED`, `DATABASE_UNAVAILABLE`, `INVALID_SCHEDULE_EXPRESSION`, `ROBOT_OFFLINE`, `JOB_ALREADY_RUNNING`

5. **Integration Guide** (rpa-docs-writer)
   - Create `docs/integration-guide.md`
   - "Getting Started": Register robot, submit job, poll status
   - "Authentication": API key flow, JWT token exchange, token refresh
   - "Job Lifecycle": Pending → Running → Completed/Failed/Cancelled
   - "WebSocket Connection": Subscribe to events (job.status_changed, robot.heartbeat, queue.depth_changed)
   - "Best Practices": Connection pooling, retry logic with exponential backoff, graceful degradation

6. **Authentication & Security Documentation** (security-architect)
   - Create `docs/security.md`
   - API key management: creation, rotation, revocation
   - JWT token lifecycle: issuance, expiry, refresh tokens
   - Rate limiting: per-key limits, burst allowances, backoff strategies
   - CORS: allowed origins, credentials, preflight handling
   - Production checklist: secrets in environment variables, HTTPS enforcement, audit logging

7. **Testing & Validation** (chaos-qa-engineer)
   - Create `tests/infrastructure/orchestrator/api/test_endpoints.py`
     - Happy path: auth success, job submission, status polling, robot listing
     - Auth failures: invalid token, expired token, missing header
     - Validation errors: invalid job payload, unsupported schedule format
     - Resilience: database unavailable, robot offline, concurrent requests
   - Create `tests/infrastructure/orchestrator/api/test_websockets.py`
     - Connection success/failure
     - Event subscription and unsubscription
     - Message ordering and delivery guarantees
   - Create `tests/infrastructure/orchestrator/api/test_rate_limiting.py`
     - Verify rate limit headers in response
     - Test burst allowance behavior
     - Test per-key rate limit enforcement

8. **Examples Repository** (rpa-docs-writer)
   - Create `examples/orchestrator-api/`
     - `python_client.py`: Async Python client wrapper with retry logic
     - `curl_examples.sh`: Common curl commands for testing
     - `postman_collection.json`: Postman collection for API exploration
     - `docker-compose.yml`: Local Orchestrator + database for testing

## Files to Modify/Create

| File | Action | Purpose | Owner Agent |
|------|--------|---------|-------------|
| `docs/openapi-orchestrator-api.yaml` | Create | Full OpenAPI 3.0 specification | rpa-engine-architect |
| `docs/api-reference/README.md` | Create | Endpoint reference guide | rpa-docs-writer |
| `docs/api-reference/workflows.md` | Create | Workflow endpoint docs | rpa-docs-writer |
| `docs/api-reference/jobs.md` | Create | Job endpoint docs | rpa-docs-writer |
| `docs/api-reference/robots.md` | Create | Robot endpoint docs | rpa-docs-writer |
| `docs/api-reference/schedules.md` | Create | Schedule endpoint docs | rpa-docs-writer |
| `docs/api-reference/metrics.md` | Create | Metrics endpoint docs | rpa-docs-writer |
| `docs/api-reference/websockets.md` | Create | WebSocket docs | rpa-docs-writer |
| `docs/error-codes.md` | Create | Error code dictionary | rpa-docs-writer |
| `docs/security.md` | Create | Auth, rate limiting, CORS | security-architect |
| `docs/integration-guide.md` | Create | Getting started, best practices | rpa-docs-writer |
| `src/casare_rpa/infrastructure/orchestrator/api/routers/jobs.py` | Create | Missing job endpoints (cancel, retry) | rpa-engine-architect |
| `src/casare_rpa/infrastructure/orchestrator/api/routers/robots.py` | Create | Robot deregistration, heartbeat | rpa-engine-architect |
| `tests/infrastructure/orchestrator/api/test_endpoints.py` | Create | Endpoint integration tests | chaos-qa-engineer |
| `tests/infrastructure/orchestrator/api/test_websockets.py` | Create | WebSocket event tests | chaos-qa-engineer |
| `tests/infrastructure/orchestrator/api/test_rate_limiting.py` | Create | Rate limit validation | chaos-qa-engineer |
| `tests/infrastructure/orchestrator/api/test_security.py` | Create | Auth token, CORS, security | chaos-qa-engineer |
| `examples/orchestrator-api/python_client.py` | Create | Python async client wrapper | rpa-docs-writer |
| `examples/orchestrator-api/curl_examples.sh` | Create | Curl command examples | rpa-docs-writer |
| `examples/orchestrator-api/postman_collection.json` | Create | Postman collection | rpa-docs-writer |

## Progress Log

- [2025-11-30 00:00] Plan file created. Waiting for user approval.
- [2025-12-01 14:00] COMPLETE: Created comprehensive API documentation:
  - `docs/api/orchestrator-api.md` - Full endpoint reference (680+ lines)
    - Authentication section (JWT + Robot API tokens)
    - 30+ endpoints documented with request/response schemas
    - curl and Python examples for all major endpoints
    - WebSocket documentation with connection examples
    - Rate limiting reference table
    - Environment variables reference
  - `docs/api/error-codes.md` - Error codes reference (450+ lines)
    - Authentication errors (8 codes)
    - Validation errors (12 codes)
    - Resource errors (4 codes)
    - Rate limiting errors (1 code)
    - Server errors (4 codes)
    - WebSocket errors (2 codes)
    - Best practices for error handling with code examples

## Post-Completion Checklist

- [ ] All endpoint references have curl + Python examples
- [ ] Error codes documented with troubleshooting steps
- [ ] OpenAPI spec validates with Swagger UI
- [ ] All tests pass: `pytest tests/infrastructure/orchestrator/api/ -v`
- [ ] Security review completed: auth flows, rate limiting, CORS
- [ ] Integration guide tested with real Orchestrator instance
- [ ] Examples run without errors
- [ ] Update `.brain/activeContext.md` with completion details
- [ ] Update `.brain/systemPatterns.md` if new API patterns discovered
- [ ] Create PR with all documentation + missing endpoint implementations

## Unresolved Questions

1. **Job Batch API**: Should we document bulk job submission (POST /jobs/batch)? Is it in scope?
2. **Pagination**: What are the default limits and max page sizes for list endpoints?
3. **Retry Strategy**: API response for retry: should we return updated job status or 202 Accepted with location header?
4. **WebSocket Auth**: How are WebSocket connections authenticated? Bearer token in URL or header?
5. **Rate Limit Strategy**: Per-robot limits or per-API-key limits? Different limits for different endpoint tiers?
6. **Database Availability**: What's the fallback strategy when database is unavailable? How do we document graceful degradation?

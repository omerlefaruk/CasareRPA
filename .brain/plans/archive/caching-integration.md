# Caching Integration & Testing Plan

This plan outlines the systematic rollout of the tiered caching system across the CasareRPA codebase and the validation strategy.

## 1. Implementation Strategy

### A. Node Layer (Execution Caching)
- **Base Class Update**: Ensure `BaseNode` in `src/casare_rpa/domain/entities/base_node.py` has `cacheable: bool = False` and `cache_ttl: int = 3600`.
- **Node Executor**: The `NodeExecutor` in `src/casare_rpa/application/use_cases/node_executor.py` will act as the "Cache Proxy".
    - **Logic**:
        1. Generate key using `CacheKeyGenerator(node_type, input_data)`.
        2. Check `TieredCacheManager`.
        3. If hit: Return cached `output_data`.
        4. If miss: Execute node, then `cache_manager.set()`.
- **Node Audit & Enablement (NEW)**:
    - **Bulk Enablement**: Identify idempotent node categories and set `self.cacheable = True` in their constructors.
    - **Target Categories**:
        - `data/`, `string_nodes.py`, `math_nodes.py`, `dict_nodes.py`, `list_nodes.py`.
        - `http/` (Conditional: Only if method is `GET`).
    - **Safety Rule**: Never enable caching for `browser/`, `desktop_nodes/`, `database/` (writes), or `file/` (writes).

### B. API/HTTP Layer (Network Caching)
- **UnifiedHttpClient**: Integrate `TieredCacheManager` into `src/casare_rpa/infrastructure/http/unified_http_client.py`.
- **Response Wrapping**: Use `CachingResponseWrapper` to store serializable parts of `aiohttp.ClientResponse` (status, headers, body).
- **Policy**: Only cache `GET` requests with successful status codes (200-299).

### C. Orchestrator/Persistence Layer
- **Workflow Metadata**: Cache workflow structure lookups in `JsonUnitOfWork`.
- **Invalidation**: Ensure `CacheInvalidator` is registered in the main application startup to listen for `WorkflowStarted` or `ManualCacheClear` events.

---

## 2. Testing Plan

### Phase 1: Unit Tests (Deterministic Keys)
- **File**: `tests/infrastructure/test_cache_keys.py`
- **Scenarios**:
    - Verify same input dicts with different key orders produce identical hashes.
    - Verify nested structures (lists of dicts) are handled correctly.
    - Verify different node types with same inputs produce different hashes.

### Phase 2: Integration Tests (Tiered Logic)
- **File**: `tests/integration/test_cache_flow.py`
- **Scenarios**:
    - **L1/L2 Promotion**: Set value in L2 only -> Get value -> Verify it now exists in L1.
    - **EventBus Invalidation**: Set multiple keys -> Publish `WorkflowStarted` -> Verify keys are deleted.
    - **TTL Expiry**: Set with short TTL -> Wait -> Verify cache miss.

### Phase 3: Performance Tests (Benchmarks)
- **File**: `tests/performance/test_cache_benchmarks.py`
- **Scenarios**:
    - Measure L1 retrieval time (Target: < 0.5ms).
    - Measure L2 retrieval time (Target: < 5ms).
    - Compare "Cold Start" (No cache) vs "Warm Start" (L1 cache) for a complex node chain.

---

## 3. Success Criteria
1. **Zero Regressions**: Existing workflows run identically with caching enabled/disabled.
2. **Persistence**: Cache survives application restart (verified via L2).
3. **Safety**: No sensitive data (passwords/tokens) cached (enforced via `CacheKeyGenerator` filters).

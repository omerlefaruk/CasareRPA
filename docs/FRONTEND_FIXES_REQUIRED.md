# Frontend Fixes Required (Monitoring Dashboard)

**Repository**: Separate monitoring-dashboard React app
**Status**: Action items identified from code review
**Priority**: Medium (non-blocking for backend deployment)

---

## Required Fixes

### 1. WebSocket Hook Dependency Array (Memory Leak) ⚠️

**File**: `monitoring-dashboard/src/api/websockets.ts:106-109`

**Issue**: Effect re-runs when `connect`/`disconnect` change, causing unnecessary reconnects and memory leaks.

**Current Code**:
```typescript
useEffect(() => {
  connect();
  return () => disconnect();
}, [connect, disconnect]);  // ❌ Causes re-runs when callbacks change
```

**Fixed Code**:
```typescript
useEffect(() => {
  connect();
  return () => disconnect();
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []); // ✅ Only run once on mount
```

**Why**: `connect` and `disconnect` are `useCallback` hooks that change identity when their dependencies change, causing this effect to run multiple times.

---

### 2. Console Logging in Production 📊

**Files**:
- `monitoring-dashboard/src/api/client.ts:22`
- `monitoring-dashboard/src/api/websockets.ts:39,52,74`

**Issue**: Unguarded `console.log` calls create performance overhead and log spam in production.

**Current Code**:
```typescript
console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
console.log(`[WS] Connecting to ${url}`);
console.log(`[WS] Message from ${endpoint}:`, data);
```

**Fixed Code**:
```typescript
if (import.meta.env.DEV) {
  console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
}

if (import.meta.env.DEV) {
  console.log(`[WS] Connecting to ${url}`);
}

if (import.meta.env.DEV) {
  console.log(`[WS] Message from ${endpoint}:`, data);
}
```

**Alternative**: Use a proper logging library with log levels (e.g., `loglevel`, `winston`, `pino`).

---

### 3. Exponential Backoff for Reconnection ⏱️

**File**: `monitoring-dashboard/src/api/websockets.ts:63-65`

**Issue**: Fixed 3s reconnection delay without exponential backoff can hammer server during outages.

**Current Code**:
```typescript
reconnectTimeoutRef.current = setTimeout(() => {
  connect();
}, reconnectInterval);  // ❌ Always 3000ms
```

**Fixed Code**:
```typescript
// Exponential backoff: 3s, 6s, 12s, 24s, 30s (capped)
const delay = Math.min(
  reconnectInterval * Math.pow(2, reconnectCountRef.current - 1),
  30000
);

if (import.meta.env.DEV) {
  console.log(
    `[WS] Reconnecting in ${delay}ms... (${reconnectCountRef.current}/${reconnectAttempts})`
  );
}

reconnectTimeoutRef.current = setTimeout(() => {
  connect();
}, delay);
```

**Why**: Exponential backoff prevents connection storms during server downtime and respects server recovery time.

---

## Backend Changes Already Made ✅

These changes have already been applied to the backend to support the frontend:

### 1. FleetMetrics Schema Alignment ✅

**Added Fields**:
```python
# src/casare_rpa/orchestrator/api/models.py
class FleetMetrics(BaseModel):
    total_robots: int
    active_robots: int
    idle_robots: int
    offline_robots: int
    total_jobs_today: int  # ← NEW
    active_jobs: int
    queue_depth: int
    average_job_duration_seconds: float  # ← NEW
```

Frontend TypeScript interface already expects these fields, now backend provides them.

### 2. Rate Limiting Added ✅

All endpoints now have rate limits:
- `/metrics/fleet`: 100 req/min
- `/metrics/robots`: 100 req/min
- `/metrics/robots/{id}`: 200 req/min
- `/metrics/jobs`: 50 req/min (database query)
- `/metrics/jobs/{id}`: 200 req/min
- `/metrics/analytics`: 20 req/min (expensive query)

### 3. DB Pool Injection Standardized ✅

No more manual `set_db_pool()` calls - database pool automatically injected from request:
```python
# OLD (inconsistent)
collector.set_db_pool(db_pool)

# NEW (automatic)
collector = get_metrics_collector(request)  # Pool injected from app state
```

---

## Testing Checklist

After applying frontend fixes:

- [ ] WebSocket reconnects only once on mount (check DevTools Network tab)
- [ ] No console logs in production build (`npm run build && npm run preview`)
- [ ] Reconnection delays increase exponentially (3s → 6s → 12s → 24s → 30s)
- [ ] FleetMetrics displays `total_jobs_today` and `average_job_duration_seconds`
- [ ] No memory leaks in WebSocket connections (check Memory profiler)

---

## Implementation Priority

**High Priority**:
1. WebSocket dependency array fix (memory leak)
2. FleetMetrics type alignment (already done backend)

**Medium Priority**:
3. Console.log guards (production performance)
4. Exponential backoff (UX during outages)

**Low Priority**:
- Consider replacing `console.log` with proper logging library

---

## Clean Architecture Migration (Future)

**Not Included**: Moving `orchestrator/api` → `presentation/api` requires:
- Updating all import paths
- Ensuring layer dependencies follow Clean Architecture
- Testing entire stack after refactoring
- **Recommendation**: Do as separate refactoring PR after v3.0 release

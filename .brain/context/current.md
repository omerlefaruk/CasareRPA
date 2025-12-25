# Current Context

**Updated**: 2025-12-25 | **Branch**: perf-fix-auto-connect-lag

## Recent Work (Completed)
### Auto-Connect & Animation Performance Fix
- **Issue**: Lag during chain execution and node dragging with auto-connect enabled
- **Root cause**: Auto-connect event filter processing every mouse move (60ms throttle), multiple pipe animation timers
- **Fix**:
  - Increased auto-connect throttle to 100ms (40% fewer updates)
  - Disabled auto-connect ghost wire during workflow execution
  - Slowed flow animations to 20fps in high-performance mode (vs 60fps)
- **Files**:
  - `src/casare_rpa/presentation/canvas/connections/auto_connect.py`
  - `src/casare_rpa/presentation/canvas/graph/custom_pipe.py`
  - `src/casare_rpa/presentation/canvas/initializers/controller_registrar.py`

## Quick References
- **Context**: `.brain/context/current.md` (this file)
- **Patterns**: `.brain/systemPatterns.md`
- **Rules**: `.brain/projectRules.md`
- **Nodes Index**: `src/casare_rpa/nodes/_index.md`

---

**Note**: This file should stay under 50 lines. Archive completed work to `recent.md`.

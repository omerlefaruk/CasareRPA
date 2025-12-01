# Legacy Core and Visual_Nodes Removal Plan

## Status: PLANNING

## Brain Context
- Read: `.brain/activeContext.md` (current session state)
- Patterns: `.brain/systemPatterns.md` (v3.0 architecture patterns)
- Rules: `.brain/projectRules.md` (v3.0 standards)
- Related: Commit `afec0ba feat(v3)!: remove core/ compatibility layer (BREAKING)`

## Overview

Complete removal of legacy v2.x compatibility code:

1. **core/ compatibility layer** - Already mostly removed (per v3.0 refactoring)
   - Directory exists but should be eliminated
   - All imports redirected to domain layer
   - Tests gate v3.0 release in `tests/integration/test_v3_compatibility.py`

2. **visual_nodes.py monolith** - Already split into category modules
   - Monolith deleted but references may exist
   - Visual nodes now live in `presentation/canvas/visual_nodes/{category}/`
   - Verify all imports point to new structure

3. **Compatibility gates** - Ensure they all pass
   - `test_v3_compatibility.py` has gates for both removals
   - Manual verification may still be required

## Agents Assigned
- [ ] Explore: `test_v3_compatibility.py` test inventory + failure analysis
- [ ] rpa-refactoring-engineer: Core module cleanup + final deletion
- [ ] rpa-refactoring-engineer: Import migration verification
- [ ] chaos-qa-engineer: All compatibility gate tests passing

## Implementation Steps

### Phase 1: Inventory & Analysis
1. Run compatibility gate tests to identify actual failures
   ```bash
   pytest tests/integration/test_v3_compatibility.py -v
   ```
2. Document all failures + root causes
3. Scan codebase for remaining:
   - Imports from `casare_rpa.core.*`
   - References to legacy API patterns
   - Deprecation warnings

### Phase 2: Core Module Cleanup
1. Verify `src/casare_rpa/core/` contents
   - List all files still present
   - Check if any are actually used
2. For each file in core/:
   - Trace all imports across codebase
   - Verify equivalents exist in domain layer
   - Migrate references to domain imports
3. Delete core/ directory once empty
4. Run tests after deletion to ensure no import breakage

### Phase 3: Visual Nodes Verification
1. Verify visual_nodes.py monolith deleted from:
   - `src/casare_rpa/presentation/canvas/visual_nodes/`
2. Scan for any stray imports of monolith:
   ```bash
   grep -r "from.*visual_nodes.visual_nodes import" src/ tests/
   ```
3. Verify all visual node categories exist in:
   - `presentation/canvas/visual_nodes/{basic,browser,desktop_automation,etc}/`

### Phase 4: Import Path Validation
1. Run compatibility gate test suite:
   ```bash
   pytest tests/integration/test_v3_compatibility.py::TestCoreCompatibilityLayerRemoval -v
   pytest tests/integration/test_v3_compatibility.py::TestVisualNodesMonolithRemoval -v
   pytest tests/integration/test_v3_compatibility.py::TestNewImportsResolve -v
   ```
2. Fix any remaining imports manually
3. Verify full test suite passes:
   ```bash
   pytest tests/ -v --tb=short
   ```

### Phase 5: Cleanup & Documentation
1. Update migration guide (if exists)
2. Remove any v2 compatibility documentation
3. Update CHANGELOG for v3.0 release notes
4. Mark `.brain/plans/legacy-removal.md` as COMPLETE

## Files to Modify/Create

| File | Action | Owner Agent | Status |
|------|--------|-------------|--------|
| `src/casare_rpa/core/` | DELETE entire directory (after verifying imports) | rpa-refactoring-engineer | pending |
| `tests/integration/test_v3_compatibility.py` | RUN tests to validate gates | chaos-qa-engineer | pending |
| Various node imports | MIGRATE from `casare_rpa.core.*` to `casare_rpa.domain.*` | rpa-refactoring-engineer | pending |
| `src/casare_rpa/presentation/canvas/visual_nodes/` | VERIFY monolith deleted | rpa-refactoring-engineer | pending |
| `.brain/activeContext.md` | UPDATE after completion | rpa-refactoring-engineer | pending |

## Current Codebase State

### Test Gates Status
File: `/c/Users/Rau/Desktop/CasareRPA/tests/integration/test_v3_compatibility.py`

Test classes (all should pass):
- `TestCoreCompatibilityLayerRemoval` (4 tests)
  - `test_no_core_imports` - No imports from casare_rpa.core
  - `test_core_compatibility_layer_deleted` - core/ dir deleted
  - `test_no_core_types_import` - No casare_rpa.core.types imports
  - `test_no_core_base_node_import` - No casare_rpa.core.base_node imports

- `TestVisualNodesMonolithRemoval` (2 tests)
  - `test_visual_nodes_monolith_deleted` - No visual_nodes.py
  - `test_no_visual_nodes_monolith_imports` - No imports from monolith

- `TestNewImportsResolve` (5 tests) - Verify new import paths work
- `TestNodeModuleStructure` (3 tests) - Node exports validation
- `TestDeprecationWarnings` (1 test) - No deprecation warnings

### Known Directories
- Core modules: `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/core/` (TBD - check if empty)
- Visual nodes: `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/presentation/canvas/visual_nodes/` (split complete)
- Nodes: `/c/Users/Rau/Desktop/CasareRPA/src/casare_rpa/nodes/`

## Progress Log

- [2025-11-30] Plan created. Status: PLANNING. Ready for Explore agent analysis.
- [Pending] Run compatibility gates - identify failures
- [Pending] Clean core/ imports
- [Pending] Delete core/ directory
- [Pending] Verify visual_nodes structure
- [Pending] All tests passing
- [Pending] Plan marked COMPLETE

## Post-Completion Checklist

- [ ] All compatibility gate tests passing
  ```bash
  pytest tests/integration/test_v3_compatibility.py -v --tb=short
  ```
- [ ] No imports from `casare_rpa.core.*` anywhere in src/
  ```bash
  grep -r "from casare_rpa.core" src/ && echo "FOUND VIOLATIONS" || echo "CLEAN"
  ```
- [ ] `src/casare_rpa/core/` directory deleted
- [ ] Full test suite passes
  ```bash
  pytest tests/ -v --tb=line
  ```
- [ ] No deprecation warnings on import
- [ ] Git diff shows only deletions in core/ area
- [ ] Update `.brain/activeContext.md` with completion timestamp
- [ ] Mark this plan as `Status: COMPLETE`
- [ ] Optionally: Create release notes for v3.0 legacy removal
- [ ] Optionally: Close related GitHub issue if exists

## Unresolved Questions

1. **What's currently in `src/casare_rpa/core/`?**
   - Is it empty? Does it have stub files? How many Python files?

2. **Are there any runtime dependencies on core/ still active?**
   - Dynamic imports? Reflection-based lookups?

3. **Do visual_nodes categories have full coverage?**
   - Any category missing from the split? Any orphaned nodes?

4. **Are there any external packages importing from casare_rpa.core?**
   - Plugins? Third-party integrations?

## Related Work

- **Previous Refactoring**: Commit `afec0ba` removed core/ compatibility layer
- **Migration Guide**: May exist in docs/ - check for outdated references
- **Release Notes**: v3.0 should mention breaking changes (core/ removed)
- **CI/CD**: GitHub Actions should validate no core/ imports

---

**Last Updated**: 2025-11-30
**Created by**: Lead Technical Writer (Claude Code)
**Next Action**: Wait for Explore agent to analyze current state, then proceed to Phase 1

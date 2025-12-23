# Current Context

**Updated**: 2025-12-23 01:32 UTC | **Branch**: fix-file-drop-nodes

## Active Work
- **Focus**: Fix file drop handling (Excel + file read) and add tests
- **Status**: READY FOR REVIEW
- **Plan**: `.brain/plans/file-drop-node-handling.md`
- **Area**: `src/casare_rpa/presentation/canvas/graph/custom_graph.py`, `tests/presentation/canvas`

## Completed This Session
### Canvas File Drop Handling
- Updated CasareNodeGraph file drop handling to support QMimeData and map Excel vs file reads.
- Fixed CasareNodeGraph.create_node to forward `pos` correctly to NodeGraphQt.
- Added tests for drag/drop mapping: `tests/presentation/canvas/graph/test_custom_graph_drop.py`.
- Removed expand_clicked disconnect warnings and reran canvas tests (268 passed).
- Preserved NodeGraphQt session drops and reduced undo noise for drop-created nodes.
- Guarded session drop parsing by size to avoid blocking large files.


### Orchestrator-first Robot Job Execution (Foundation)

- Added robot-facing job lease endpoint: `POST /api/v1/jobs/{job_id}/extend-lease`.
- Implemented Orchestrator-backed robot consumer (no direct Postgres): `src/casare_rpa/infrastructure/orchestrator/robot_job_consumer.py`.
- Wired RobotAgent to prefer Orchestrator job consumer when `CASARE_ORCHESTRATOR_URL` + `CASARE_ORCHESTRATOR_API_KEY` are present and no `postgres_url` is configured.
- Added unit tests for the consumer: `tests/infrastructure/orchestrator/test_robot_job_consumer.py`.

### Windows Robot Enrollment (Automation)

- RobotAgent now accepts `CASARE_ORCHESTRATOR_URL` / `CASARE_ORCHESTRATOR_API_KEY` (keeps `ORCHESTRATOR_URL` / `ORCHESTRATOR_API_KEY` working).
- Added Windows helper script: `deploy/windows/enroll-orchestrator-robot.ps1` to set env vars and optionally start the agent.
- Updated Fleet Dashboard doc with the ready-to-run PowerShell command.

### Orchestrator Client Cleanup

- Fixed `aiohttp` session leak when Orchestrator is unreachable or `/health` fails.
- RobotAgent now disconnects Orchestrator client on failed registration and during shutdown.
- Added regression test: `tests/infrastructure/orchestrator/test_orchestrator_client_cleanup.py`.

### Fleet Dashboard UX Improvements (Partial)

- Added toast notifications (`ToastNotification`) and integrated into Fleet dashboard.
- Refactored `FleetDashboardDialog` to sidebar navigation + custom painted icons.
- Migrated Fleet Analytics tab styling to THEME tokens and added stat-card drilldown.
- Fixed Robots tab validation to use toast when available.

### Expression Editor Feature Implementation

Enhanced text editing for node properties with syntax highlighting, variable support, and multiple editor modes.

#### Files Created (~2,500 lines)

```
src/casare_rpa/presentation/canvas/ui/widgets/expression_editor/
├── __init__.py                    # Public exports
├── base_editor.py                 # EditorType enum, BaseExpressionEditor ABC
├── expression_editor_popup.py     # Main popup container (642 lines)
├── editor_factory.py              # Factory for creating editors
├── code_editor.py                 # Code editor with line numbers (368 lines)
├── markdown_editor.py             # Markdown editor with preview (471 lines)
├── rich_text_editor.py            # Rich text with variables (374 lines)
├── syntax/
│   ├── __init__.py
│   ├── python_highlighter.py      # Python syntax (VSCode Dark+)
│   ├── javascript_highlighter.py  # JavaScript syntax
│   └── markdown_highlighter.py    # Markdown syntax
└── widgets/
    ├── __init__.py
    ├── expand_button.py           # Trigger button (84 lines)
    ├── toolbar.py                 # Formatting toolbar
    └── variable_autocomplete.py   # Variable autocomplete
```

#### Key Classes

| Class | Purpose |
|-------|---------|
| `EditorType` | Enum: CODE_PYTHON, CODE_JAVASCRIPT, CODE_CMD, MARKDOWN, RICH_TEXT |
| `ExpressionEditorPopup` | Main popup following NodeOutputPopup pattern |
| `EditorFactory` | Factory for creating editors with property type mapping |
| `CodeExpressionEditor` | Code with line numbers and syntax highlighting |
| `MarkdownEditor` | Markdown with toolbar and live preview |
| `RichTextEditor` | Text with {{ variable autocomplete |
| `ExpandButton` | Small [...] button to trigger popup |

#### Integration Points

Modified `base_visual_node.py`:
- `_open_expression_editor()` - Opens popup for property
- `_get_editor_type_for_property()` - Maps property to editor type
- `_on_expression_editor_accepted()` - Handles accepted value

Node-specific overrides:
```python
{
    "EmailSendNode": {"body": EditorType.MARKDOWN},
    "BrowserEvaluateNode": {"script": EditorType.CODE_JAVASCRIPT},
    "RunPythonNode": {"code": EditorType.CODE_PYTHON},
    "CommandNode": {"command": EditorType.CODE_CMD},
}
```

#### Features

- **Popup Window**: Tool-style frameless, draggable, resizable, fade-in animation
- **Code Editor**: Line numbers, syntax highlighting, tab-to-spaces
- **Markdown Editor**: Toolbar (Bold/Italic/Heading/Link/Lists/Code), live preview
- **Rich Text Editor**: Variable autocomplete on {{ trigger, validation status
- **Keyboard Shortcuts**: Escape (cancel), Ctrl+Enter (accept), Ctrl+B/I/K (formatting)

#### Documentation Created

- `expression_editor/_index.md` - Package documentation
- `widgets/_index.md` - Widget catalog (created)

### Previous: Workflow Loading Performance Optimization (All Phases Complete)

### Workflow Loading Performance Optimization (All Phases A, B, C)
Implemented comprehensive performance optimizations for workflow loading:

#### Phase A: Quick Wins
1. **A1: Single-pass validation** - Added `__validated__` marker to skip redundant validation
2. **A3: Improved NODE_TYPE_MAP proxy** - Track accessed names, avoid loading all 400+ nodes
3. **A4: Module-level cache in deserializer** - `_NODE_TYPE_MAP_CACHE` for persistent caching

#### Phase B: Medium Effort
1. **B1: Workflow schema caching (LRU)** - Created `infrastructure/caching/workflow_cache.py`
   - Content fingerprinting (SHA-256) for cache keys
   - LRU eviction with configurable max size
   - Thread-safe with RLock
   - 12x faster repeated loads (0.07ms vs 0.87ms)
2. **B3: Streaming decompression** - Updated `compressed_io.py`
   - 64KB chunk streaming for gzip/zstd
   - Memory-mapped I/O for large JSON files
   - Auto-detection based on 1MB threshold

#### Phase C: Advanced (Previously Completed)

1. **Created**: `src/casare_rpa/utils/workflow/incremental_loader.py` (~400 lines)
   - `WorkflowSkeleton` dataclass for lightweight previews
   - `IncrementalLoader` class for skeleton-first loading
   - 20-50x faster for preview scenarios (~5-10ms vs 200-500ms)
   - `load_skeleton()` - Fast metadata extraction
   - `load_full()` - Deferred full loading
   - `scan_directory()` - Workflow browser support

2. **Modified**: `src/casare_rpa/utils/performance/object_pool.py`
   - Added `NodeInstancePool` class for node reuse
   - Thread-safe acquire/release with statistics
   - `get_node_instance_pool()` singleton

3. **Modified**: `src/casare_rpa/utils/workflow/workflow_loader.py`
   - Added `_batch_resolve_node_types()` - Single-pass alias resolution
   - Added `_preload_workflow_node_types()` - Batch preloading
   - Added `_instantiate_nodes_parallel()` - ThreadPoolExecutor for 50+ nodes
   - Added `use_parallel` and `use_pooling` parameters to `load_workflow_from_dict()`

4. **Created Tests**: `tests/performance/test_workflow_loading.py`
   - 70 comprehensive tests
   - Unit, integration, and performance benchmarks
   - All tests passing

### Key Performance Gains
| Optimization | Estimated Gain |
|--------------|----------------|
| Skeleton loading | 200ms+ (preview scenarios) |
| Parallel instantiation | 50-100ms (50+ nodes) |
| Node pooling | 30-50ms (repeated loads) |

### Previous Session: Super Node Documentation

### Super Node Feature Documentation
Created comprehensive documentation for the Super Node pattern:

1. **Created**: `.brain/docs/super-node-pattern.md` - Full implementation guide
   - What are Super Nodes (consolidated action-based nodes)
   - DynamicPortSchema for defining action-based ports
   - PropertyDef display_when/hidden_when for conditional widgets
   - SuperNodeMixin usage pattern
   - Step-by-step guide for creating new Super Nodes
   - Best practices and troubleshooting

2. **Updated**: `src/casare_rpa/nodes/_index.md`
   - Added Super Nodes section
   - Documented FileSystemSuperNode (12 actions)
   - Documented StructuredDataSuperNode (7 actions)
   - Added link to pattern documentation

3. **Updated**: `src/casare_rpa/presentation/canvas/visual_nodes/_index.md`
   - Added Super Nodes (Mixins) section
   - Documented mixins/super_node_mixin.py
   - Documented file_operations/super_nodes.py
   - Updated node count (405 -> 407)

### Key Files Documented

| File | Purpose |
|------|---------|
| `nodes/file/super_node.py` | FileSystemSuperNode, StructuredDataSuperNode implementations |
| `visual_nodes/mixins/super_node_mixin.py` | Mixin for dynamic port/widget management |
| `visual_nodes/file_operations/super_nodes.py` | Visual node implementations |
| `domain/value_objects/dynamic_port_config.py` | PortDef, ActionPortConfig, DynamicPortSchema |
| `domain/schemas/property_schema.py` | PropertyDef with display_when/hidden_when |

### Previous Session: AI Assistant Brain Context Documentation
Created comprehensive brain context file for CasareRPA Genius AI Assistant:
1. **Workflow JSON Schema**: Complete structure with security constraints
2. **Node Registry Reference**: All categories, port types, data types
3. **Common Node Signatures**: 25+ node types with ports and config
4. **Robustness Protocol**: TryCatch wrapper, validation patterns, error recovery
5. **Topology Rules**: 400px spacing, append area calculation, standard layouts
6. **Connection Patterns**: Exec flow, data ports, type compatibility
7. **Best Practices**: Naming conventions, variable patterns, complete examples

**Key File**: `docs/ai_context/workflow_standards.md` (1179 lines)

## Quick References
- **Context**: `.brain/context/current.md` (this file)
- **Patterns**: `.brain/systemPatterns.md`
- **Rules**: `.brain/projectRules.md`
- **Nodes Index**: `src/casare_rpa/nodes/_index.md`
- **Visual Nodes Index**: `src/casare_rpa/presentation/canvas/visual_nodes/_index.md`
- **Super Node Pattern**: `.brain/docs/super-node-pattern.md`

## Notes
<!-- Add session-specific notes here. Clear after session. -->

## Phase Report (2025-12-22 13:57 UTC)
Phase: Docs
In progress: rule automation updates
Completed: added scripts and command checklists
Next: await review

## Phase Report (2025-12-22 13:59 UTC)
Phase: Docs
In progress: automation enforcement + helper scripts
Completed: added review/qa/phase commands and CI checks
Next: await review

## Phase Report (2025-12-22 14:11 UTC)
Phase: Docs
In progress: tech stack + worktree rules
Completed: added worktree automation + chromadb guidance
Next: await review

## Phase Report (2025-12-22 14:25 UTC)
Phase: Docs
In progress: workflow and MCP rule updates
Completed: updated feature lifecycle, MCP usage, and token rules
Next: await review

## Phase Report (2025-12-22 14:46 UTC)
Phase: Docs
In progress: claude mirror + agent guide sync
Completed: added .claude mirror + sync script + pre-commit hook; updated AGENTS/CLAUDE/GEMINI + tool rules
Next: review changes

## Phase Report (2025-12-22 14:49 UTC)
Phase: Docs
In progress: claude mirror link mode
Completed: added --link support in sync_claude_dir.py and updated guide/tooling docs
Next: review changes

## Phase Report (2025-12-22 15:13 UTC)
Phase: Docs
In progress: agent/claude guide alignment + indexes
Completed: added rules/docs indexes, normalized .claude refs, added analysis banners, added .gitattributes + sync updates
Next: review changes

## Phase Report (2025-12-22 15:21 UTC)
Phase: Validate
In progress: pre-commit validation
Completed: pre-commit run in worktree; EOF normalized for .brain/analysis
Next: review suggestions

## Phase Report (2025-12-22 15:31 UTC)
Phase: Validate
In progress: rules validation
Completed: pre-commit run in worktree (agent-validate-2) passed; sync + path hygiene + index checks validated
Next: review changes

## Phase Report (2025-12-23 01:08 UTC)
Phase: QA
In progress: pytest tests/presentation/canvas/graph/test_custom_graph_drop.py

## Phase Report (2025-12-23 01:10 UTC)
Phase: Docs
In progress: context/plan/index updates

## Phase Report (2025-12-23 01:17 UTC)
Phase: QA
In progress: pytest tests/presentation/canvas/ -v

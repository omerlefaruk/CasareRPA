# Comprehensive Systems Refactoring Plan

**Date**: 2025-12-11
**Scope**: Canvas, UI, AI, Node-based Systems
**Status**: Ready for Implementation

---

## Executive Summary

Based on comprehensive exploration of the CasareRPA codebase, this plan identifies refactoring opportunities across four major systems. The codebase is mature with 278 Python files in canvas (~35,799 LOC), 280+ nodes, and sophisticated AI integration. Key themes: reducing monolithic files, improving decoupling, and enhancing testability.

---

## Part 1: Canvas System Refactoring

### 1.1 Critical Issues Identified

| Issue | File | LOC | Priority |
|-------|------|-----|----------|
| Monolithic NodeGraphWidget | graph/node_graph_widget.py | 2,685 | HIGH |
| Large visual_nodes/__init__.py | visual_nodes/__init__.py | 608 | MEDIUM |
| UnifiedSelectorDialog complexity | selectors/unified_selector_dialog.py | 2,598 | HIGH |
| ExecutionController size | controllers/execution_controller.py | 1,515 | MEDIUM |
| Circular import concerns | multiple files | - | HIGH |

### 1.2 Refactoring Tasks

#### Task C1: Split NodeGraphWidget (HIGH)
**Current**: 2,685 LOC handling graph setup, events, connections, culling, selection
**Target**: Extract into focused components

```
graph/node_graph_widget.py (800 LOC - core only)
├── graph/graph_setup.py (~400 LOC)
├── graph/connection_handler.py (~500 LOC)
├── graph/selection_handler.py (~400 LOC)
├── graph/event_filter.py (~300 LOC)
└── graph/culling_manager.py (~300 LOC) [existing]
```

#### Task C2: Split Visual Node Registry (MEDIUM)
**Current**: 608 LOC single file with 405 nodes
**Target**: Category-specific registry files

```
visual_nodes/
├── __init__.py (entry point, combines registries)
├── registries/
│   ├── browser_registry.py
│   ├── desktop_registry.py
│   ├── data_registry.py
│   ├── system_registry.py
│   ├── google_registry.py
│   └── ... (per category)
```

#### Task C3: Decompose UnifiedSelectorDialog (HIGH)
**Current**: 2,598 LOC with multiple responsibilities
**Target**: Extract picker, validator, preview

```
selectors/
├── unified_selector_dialog.py (1,000 LOC - orchestration)
├── selector_picker.py (~500 LOC)
├── selector_validator.py (~400 LOC)
├── selector_preview.py (~400 LOC)
└── selector_state.py (~300 LOC)
```

#### Task C4: Split ExecutionController (MEDIUM)
**Current**: 1,515 LOC handling execution, debugging, logging, terminal
**Target**: Separate concerns

```
controllers/
├── execution_controller.py (800 LOC - core execution)
├── debug_controller.py (~400 LOC)
└── log_bridge_controller.py (~300 LOC)
```

#### Task C5: Resolve Circular Imports (HIGH)
**Affected**: graph/custom_pipe.py, visual_nodes/base_visual_node.py, initializers/
**Solution**:
- Introduce abstraction layer between graph and visual_nodes
- Use TYPE_CHECKING imports
- Module-level lazy imports where needed

---

## Part 2: UI System Refactoring

### 2.1 Critical Issues Identified

| Issue | File | LOC | Priority |
|-------|------|-----|----------|
| MainWindow controller coupling | main_window.py | 1,099 | MEDIUM |
| Monolithic theme function | theme.py | 640 | MEDIUM |
| No dialog factory pattern | ui/dialogs/ | - | LOW |
| Panel tight coupling | DockCreator | - | MEDIUM |
| ResourceCache no cleanup | resources.py | - | LOW |

### 2.2 Refactoring Tasks

#### Task U1: Reduce MainWindow Coupling (MEDIUM)
**Current**: 12+ direct controller references
**Target**: Dependency injection via ControllerRegistry

```python
# Before
class MainWindow:
    def __init__(self):
        self._workflow_controller = WorkflowController(self)
        self._execution_controller = ExecutionController(self)
        # ... 10+ more

# After
class MainWindow:
    def __init__(self, controller_registry: ControllerRegistry):
        self._controllers = controller_registry
        # Access via: self._controllers.get(WorkflowController)
```

#### Task U2: Split Theme System (MEDIUM)
**Current**: 640 LOC single function generating 567 lines QSS
**Target**: Modular theme components

```
ui/theme/
├── __init__.py (ThemeManager, get_stylesheet)
├── colors.py (CanvasThemeColors, wire colors, status colors)
├── styles.py (widget QSS generators)
├── icons.py (icon color definitions)
└── animations.py (animation durations, easing)
```

#### Task U3: Create Panel Registry (MEDIUM)
**Current**: DockCreator creates and wires all panels
**Target**: Discoverable panel registration

```python
class PanelRegistry:
    def register(name: str, factory: Callable[[], QWidget])
    def get(name: str) -> QWidget
    def list_panels() -> list[str]
```

#### Task U4: Add Dialog Factory (LOW)
**Current**: 26 dialogs with individual instantiation
**Target**: Consistent dialog creation

```python
class DialogFactory:
    def create(dialog_type: DialogType, **kwargs) -> BaseDialog
    def show_modal(dialog_type: DialogType, **kwargs) -> DialogResult
```

#### Task U5: Resource Cache Improvements (LOW)
**Current**: No cleanup, 400-item max icons, 500-item pixmaps
**Target**: LRU with memory pressure handling

```python
class ResourceCache:
    def __init__(self, max_memory_mb: int = 100):
        self._icon_cache = LRUCache(maxsize=200)
        self._pixmap_cache = LRUCache(maxsize=300)

    def clear_unused(self) -> int  # Returns bytes freed
    def get_stats() -> CacheStats
```

---

## Part 3: AI System Refactoring

### 3.1 Current State (Strong Foundation)

The AI system is well-architected with:
- Multi-provider LLM support (11+ providers)
- Configurable behavior via AgentConfig
- Triple validation pipeline (schema → domain → Qt)
- Self-healing automation (4-tier healing chain)

### 3.2 Enhancement Tasks

#### Task A1: Add Structured Output Mode (MEDIUM)
**Current**: JSON extraction with regex
**Target**: Native structured output for OpenAI/Anthropic

```python
class SmartWorkflowAgent:
    async def generate_structured(
        self,
        prompt: str,
        response_format: Type[BaseModel]  # Pydantic model
    ) -> WorkflowGenerationResult
```

#### Task A2: Implement Conversational Refinement (MEDIUM)
**Current**: Single-shot generation
**Target**: Multi-turn workflow refinement

```python
class ConversationalWorkflowAgent:
    def __init__(self):
        self._history: ConversationHistory = []
        self._current_workflow: Optional[WorkflowSchema] = None

    async def refine(self, modification: str) -> WorkflowGenerationResult
    async def undo_last() -> WorkflowGenerationResult
```

#### Task A3: Add Intelligent Node Suggestions (LOW)
**Current**: Manual node selection
**Target**: Context-aware suggestions

```python
class NodeSuggestionService:
    def suggest_next(
        self,
        current_node: str,
        workflow_context: WorkflowSchema
    ) -> list[NodeSuggestion]

    def suggest_by_port(
        self,
        output_port: Port
    ) -> list[str]  # Compatible node types
```

#### Task A4: Enhance Vision Integration (LOW)
**Current**: Basic vision via LLM
**Target**: Dedicated vision nodes

```
nodes/ai/
├── image_classify_node.py
├── object_detect_node.py
├── screen_analyze_node.py
└── visual_find_node.py
```

---

## Part 4: Node System Refactoring

### 4.1 Current State (Solid Architecture)

The node system has:
- 280+ implemented nodes across 16 categories
- Clear domain/visual separation
- Lazy-loading registry
- Async-first execution

### 4.2 Refactoring Tasks

#### Task N1: Standardize Node File Organization (MEDIUM)
**Current**: Mix of single files and packages
**Target**: Consistent package structure

```
nodes/
├── browser/          # Package (good)
│   ├── __init__.py
│   ├── browser_base.py
│   ├── navigation/
│   ├── interaction/
│   └── extraction/
├── desktop/          # Rename from desktop_nodes (consistency)
│   ├── __init__.py
│   ├── desktop_base.py
│   └── ...
├── data/            # Rename from data_operation_nodes.py
│   ├── __init__.py
│   ├── string_nodes.py
│   ├── list_nodes.py
│   └── dict_nodes.py
├── control_flow/    # Extract from single file
│   ├── __init__.py
│   ├── conditionals.py (If, Switch)
│   ├── loops.py (For, While, Break, Continue)
│   └── error_handling.py (Try, Catch, Finally)
```

#### Task N2: Add Missing High-Priority Nodes (HIGH)
Based on competitive analysis:

**Browser Category**:
- ManageCookiesNode
- InterceptNetworkNode
- BrowserSessionNode

**Desktop Category**:
- ImageAutomationNode
- PDFFormFillNode
- CredentialManagerNode

**Data Category**:
- DataTableNode (comprehensive)
- ExcelModernNode (openpyxl)

**AI Category**:
- AIAgentNode
- EntityExtractionNode
- EmbeddingsNode + RAGNode

#### Task N3: Improve Node Base Classes (LOW)
**Current**: Some duplication in base classes
**Target**: Shared mixins for common patterns

```python
class RetryMixin:
    """Add retry capability to any node"""
    async def execute_with_retry(self, operation: Callable, **retry_config)

class TimeoutMixin:
    """Add timeout handling to any node"""
    async def execute_with_timeout(self, operation: Callable, timeout_ms: int)

class MetricsMixin:
    """Add execution metrics tracking"""
    def record_execution_time(self, duration_ms: float)
    def record_token_usage(self, tokens: int)
```

#### Task N4: Node Testing Infrastructure (MEDIUM)
**Current**: Some test coverage gaps
**Target**: Comprehensive test templates

```
tests/nodes/
├── conftest.py (shared fixtures)
├── browser/
│   ├── conftest.py (mock_page, mock_browser)
│   └── test_*.py
├── desktop/
│   ├── conftest.py (MockUIControl)
│   └── test_*.py
└── templates/
    └── node_test_template.py
```

---

## Part 5: Implementation Phases

### Phase 1: Critical Fixes (Week 1-2)
**Focus**: High-priority items blocking quality

| Task | System | Priority | Effort |
|------|--------|----------|--------|
| C1 | Canvas | HIGH | 3 days |
| C3 | Canvas | HIGH | 2 days |
| C5 | Canvas | HIGH | 2 days |
| N2 (partial) | Node | HIGH | 3 days |

### Phase 2: Architecture Improvements (Week 3-4)
**Focus**: Better separation of concerns

| Task | System | Priority | Effort |
|------|--------|----------|--------|
| C2 | Canvas | MEDIUM | 2 days |
| C4 | Canvas | MEDIUM | 1 day |
| U1 | UI | MEDIUM | 2 days |
| U2 | UI | MEDIUM | 2 days |
| N1 | Node | MEDIUM | 3 days |

### Phase 3: Enhancements (Week 5-6)
**Focus**: New capabilities and polish

| Task | System | Priority | Effort |
|------|--------|----------|--------|
| U3 | UI | MEDIUM | 1 day |
| A1 | AI | MEDIUM | 2 days |
| A2 | AI | MEDIUM | 3 days |
| N4 | Node | MEDIUM | 2 days |

### Phase 4: Future (Week 7+)
**Focus**: Nice-to-have improvements

| Task | System | Priority | Effort |
|------|--------|----------|--------|
| U4 | UI | LOW | 1 day |
| U5 | UI | LOW | 1 day |
| A3 | AI | LOW | 2 days |
| A4 | AI | LOW | 3 days |
| N3 | Node | LOW | 2 days |

---

## Part 6: Quality Gates

### For Each Refactoring Task

1. **Pre-Implementation**
   - [ ] Create branch from main
   - [ ] Review affected tests
   - [ ] Document current behavior

2. **Implementation**
   - [ ] Follow existing patterns
   - [ ] Maintain backward compatibility
   - [ ] Add type hints
   - [ ] Update docstrings

3. **Post-Implementation**
   - [ ] Run full test suite: `pytest tests/ -v`
   - [ ] Run linting: `ruff check src/`
   - [ ] Update _index.md files
   - [ ] Code review (reviewer agent)

---

## Part 7: Risk Mitigation

### Breaking Changes Prevention

1. **Public API Preservation**
   - Keep existing imports working via re-exports
   - Add deprecation warnings for moved items
   - Document migration path

2. **Testing Strategy**
   - Run existing tests after each change
   - Add integration tests for refactored components
   - Manual smoke test on canvas operations

3. **Rollback Plan**
   - Feature branches for each major refactor
   - PR-based workflow
   - Tag releases before major changes

---

## Summary

This refactoring plan addresses:

| System | Issues | Tasks | Est. Effort |
|--------|--------|-------|-------------|
| Canvas | 5 critical | 5 tasks | 10 days |
| UI | 5 issues | 5 tasks | 7 days |
| AI | Enhancement focused | 4 tasks | 7 days |
| Node | Mixed | 4 tasks | 10 days |

**Total Estimated Effort**: ~34 developer days across 6-7 weeks

**Key Benefits**:
- Reduced file sizes (avg 50% reduction for large files)
- Better testability through decoupling
- Clearer architecture and responsibilities
- Foundation for future features

---

*Plan created: 2025-12-11*
*Last updated: 2025-12-11*

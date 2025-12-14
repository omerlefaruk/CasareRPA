# Node Refactoring & Improvements Plan

**Generated:** 2025-12-14
**Status:** ANALYSIS COMPLETE - READY FOR IMPLEMENTATION

## Executive Summary

Analysis of 455+ nodes across 181 files reveals a **production-ready codebase** with targeted improvement opportunities.

| Metric | Current | Target |
|--------|---------|--------|
| @node decorator compliance | 81% (146/181 files) | 100% |
| Visual node coverage | 97.5% (424/435) | 100% |
| Test coverage by category | 28% (5/18 categories) | 80% |
| Modern exec port pattern | 21% (96 nodes) | 100% |
| Super Node consolidation | 3 nodes | 8 nodes |

---

## P0 - CRITICAL (Implement This Week)

### 1. Audit & Fix LLM/AI Node Decorators

**Issue:** LLM nodes missing @node/@properties decorators causes inconsistent registration.

**Files to audit:**
- `llm/llm_nodes.py`
- `llm/ai_condition_node.py`
- `llm/ai_switch_node.py`
- `llm/ai_decision_table_node.py`
- `llm/ai_agent_node.py`
- `llm/prompt_template_node.py`
- `llm/rag_nodes.py`

**Action:** Add missing @node(category="llm") and @properties(...) decorators.

**Effort:** 2-3 hours

---

### 2. Create Missing Visual Nodes for RAG/AI

**Gap:** 8 AI nodes lack visual wrappers.

**Missing visual nodes:**
| Logic Node | Visual Node Needed | Priority |
|------------|-------------------|----------|
| PromptTemplateNode | VisualPromptTemplateNode | HIGH |
| ListTemplatesNode | VisualListTemplatesNode | HIGH |
| GetTemplateInfoNode | VisualGetTemplateInfoNode | HIGH |
| EmbeddingNode | VisualEmbeddingNode | HIGH |
| RAGNode | VisualRAGNode | HIGH |
| VectorSearchNode | VisualVectorSearchNode | HIGH |
| VectorStoreAddNode | VisualVectorStoreAddNode | HIGH |
| VectorStoreDeleteNode | VisualVectorStoreDeleteNode | HIGH |

**Effort:** 4-5 hours

---

### 3. Critical Test Coverage

**Gap:** Browser, Desktop, Control Flow nodes have ZERO tests.

**Immediate test suites needed:**
| Category | Est. Tests | Template |
|----------|-----------|----------|
| Browser (LaunchBrowser, Click, Type) | 30+ | Use FileSystemSuperNode pattern |
| Control Flow (If, ForLoop, TryCatch) | 20+ | Use domain/test_property_schema.py pattern |
| Desktop (FindElement, ClickElement) | 15+ | Mock Windows APIs |

**Effort:** 8-12 hours

---

## P1 - HIGH PRIORITY (This Sprint)

### 4. Create Super Nodes to Consolidate Node Categories

**Opportunity:** Following FileSystemSuperNode success (12 ops in 1 node), consolidate more categories.

| Super Node | Replaces | Actions | Status |
|------------|----------|---------|--------|
| **HttpSuperNode** | HttpRequestNode, SetHttpHeadersNode, HttpAuthNode, BuildUrlNode, HttpDownloadFileNode, HttpUploadFileNode | GET, POST, PUT, DELETE, PATCH, Download, Upload, Auth | ✅ DONE |
| **DatabaseSuperNode** | DatabaseConnectNode, ExecuteQueryNode, ExecuteNonQueryNode, BeginTransactionNode, CommitTransactionNode, RollbackTransactionNode, CloseDatabaseNode | Connect, Query, Execute, Transaction, Close | ✅ DONE |
| **EmailSuperNode** | SendEmailNode, ReadEmailsNode, GetEmailContentNode, FilterEmailsNode, MarkEmailNode, DeleteEmailNode | Send, Read, Filter, Mark, Delete, Move | ✅ DONE |
| **ListSuperNode** | CreateListNode, ListGetItemNode, ListAppendNode, ListSliceNode, ListFilterNode, ListMapNode, etc. | Create, Get, Append, Slice, Filter, Map, Reduce, Sort, Unique | ✅ DONE |
| **DictSuperNode** | DictGetNode, DictSetNode, DictMergeNode, DictKeysNode, DictValuesNode, etc. | Get, Set, Remove, Merge, Keys, Values, Has, Items | ✅ DONE |

**Effort:** 12-16 hours total (2-3 hours each)

---

### 5. Extract Shared Base Classes

**Issue:** Code duplication in list_nodes.py (1,086 LOC) and dict_nodes.py.

**Solution:**
```python
# nodes/data/list_operation_base.py
class ListOperationBase(BaseNode):
    """Base class for list operations with common helpers."""

    def _resolve_list(self, context, port_name="list"):
        """Resolve list from port, parameter, or variable reference."""
        ...

    def _handle_empty_list(self, operation_name):
        """Standard handling for empty list edge case."""
        ...

# nodes/data/dict_operation_base.py
class DictOperationBase(BaseNode):
    """Base class for dict operations."""
    ...
```

**Effort:** 4-6 hours

---

### 6. Standardize Trigger Node Lifecycle

**Issue:** Mixed threading/async approaches in trigger nodes.

**Files:**
- `trigger_nodes/webhook_trigger_node.py`
- `trigger_nodes/schedule_trigger_node.py`
- `trigger_nodes/file_watch_trigger_node.py`
- `trigger_nodes/email_trigger_node.py`

**Standard pattern:**
```python
class BaseTriggerNode(BaseNode):
    """Standardized trigger with async lifecycle."""

    async def start(self) -> None:
        """Start listening for trigger events."""
        ...

    async def stop(self) -> None:
        """Clean shutdown with resource cleanup."""
        ...

    async def _on_triggered(self, payload: Dict[str, Any]) -> None:
        """Handle trigger event uniformly."""
        ...
```

**Effort:** 3-4 hours

---

### 7. Implement Placeholder Google Nodes

**Issue:** Registry contains entries for unimplemented nodes.

**Placeholders to implement or deprecate:**
| Node | Action | Status |
|------|--------|--------|
| DriveExportFileNode | IMPLEMENT (export Google Docs to PDF/Word) | ✅ DONE |
| DriveCreateShareLinkNode | IMPLEMENT (create shareable links) | ✅ DONE |

**Effort:** 2-3 hours

---

## P2 - MEDIUM PRIORITY (Next Sprint)

### 8. Migrate to Modern Exec Port Pattern

**Current (old):**
```python
self.add_input_port("exec_in", DataType.EXEC)
self.add_output_port("exec_out", DataType.EXEC)
```

**Target (modern):**
```python
self.add_exec_input("exec_in")
self.add_exec_output("exec_out")
```

**Impact:** 358+ nodes need update (cosmetic, no functional change)

**Strategy:** Create migration script to auto-update.

**Effort:** 4-6 hours (scripted)

---

### 9. Create Missing Parallel Execution Visual Nodes

**Gap:** ForkNode, JoinNode, ParallelForEachNode have logic but no visual wrappers.

**Effort:** 3-4 hours

---

### 10. Split Monolithic Files

**Files exceeding 1000 LOC:**
| File | Lines | Split Strategy |
|------|-------|---------------|
| `file/super_node.py` | 1,894 | Split by action groups (file ops, dir ops, structured data) |
| `system/dialogs/notification.py` | 1,258 | Split by dialog type |
| `google/sheets_nodes.py` | 1,042 | Already well-organized, optional |
| `text/super_node.py` | 1,004 | Already well-organized, optional |

**Effort:** 4-6 hours

---

## P3 - LOW PRIORITY (Backlog)

### 11. Cleanup Legacy Compatibility Modules

**Files that are now just re-exports:**
- `browser_nodes.py` - re-exports from browser/
- `data_operation_nodes.py` - re-exports from list_nodes, dict_nodes, etc.
- `interaction_nodes.py` - re-exports from browser/interaction
- `navigation_nodes.py` - re-exports from browser/navigation

**Action:** Add deprecation warnings, schedule removal in v3.0.

**Effort:** 1-2 hours

---

### 12. Additional Test Coverage

**Target: 80% category coverage**

| Category | Current Tests | Target Tests |
|----------|--------------|--------------|
| Data Operations | 0 | 40 |
| Email | 0 | 20 |
| HTTP/REST | 0 | 25 |
| LLM/AI | 0 | 30 |
| System | 0 | 25 |
| Triggers | 0 | 20 |

**Effort:** 20-30 hours total

---

## New Node Proposals

### High-Value New Nodes

| Node | Category | Description | Effort |
|------|----------|-------------|--------|
| **OAuthRefreshNode** | auth | Auto-refresh OAuth tokens | 3h |
| **APIRateLimiterNode** | http | Rate limiting for API calls | 2h |
| **DataValidationSuperNode** | data | Schema validation, type coercion | 4h |
| **RetryWithBackoffNode** | error_handling | Exponential backoff retry | 2h |
| **CacheLookupNode** | performance | In-memory caching for workflows | 3h |
| **AwsS3Node** | cloud | AWS S3 file operations | 4h |
| **AzureBlobNode** | cloud | Azure Blob storage | 4h |
| **SlackSuperNode** | messaging | Slack integration (send, read, react) | 4h |
| **DiscordSuperNode** | messaging | Discord integration | 4h |
| **NotionSuperNode** | productivity | Notion API integration | 5h |

---

## Implementation Order

### Week 1
1. P0-1: Audit LLM decorators (2-3h)
2. P0-2: Create RAG/AI visual nodes (4-5h)
3. P0-3: Browser test suite (4h)

### Week 2
4. P0-3: Control Flow test suite (3h)
5. P1-4: HttpSuperNode (3h)
6. P1-4: DatabaseSuperNode (3h)

### Week 3
7. P1-4: EmailSuperNode (2h)
8. P1-4: ListSuperNode (2h)
9. P1-5: Extract base classes (4h)

### Week 4
10. P1-6: Standardize triggers (3h)
11. P1-7: Google placeholder nodes (2h)
12. P2-8: Exec port migration script (4h)

---

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Decorator compliance | 81% | 100% |
| Visual coverage | 97.5% | 100% |
| Test coverage | 28% categories | 80% categories |
| Super Node consolidation | 3 | 8 |
| Code duplication | High in data ops | Minimal |
| Modern patterns | 21% | 100% |

---

## Related Documents

- `.brain/docs/super-node-pattern.md` - Super Node implementation guide
- `agent-rules/rules/03-nodes.md` - Node development standards
- `nodes/_index.md` - Node registry index
- `presentation/canvas/visual_nodes/_index.md` - Visual node index

# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---
# RAG/AI Visual Nodes - Quick Reference

**Status:** 55% complete (10/18 nodes have visual wrappers)

---

## At a Glance

### Existing (✓ Complete)
```
LLM Operations (6):     LLMCompletion, LLMChat, LLMExtractData,
                        LLMSummarize, LLMClassify, LLMTranslate

AI Control Flow (4):    AICondition, AISwitch, AIDecisionTable, AIAgent
```

### Missing (✗ Critical)
```
RAG Core (5):          Embedding, VectorStoreAdd, VectorSearch,
                       RAG (retrieve+generate), VectorStoreDelete

Templates (3):         PromptTemplate, ListTemplates, GetTemplateInfo
```

---

## Quick Implementation Summary

### Files to Create
1. `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/rag_nodes.py` (5 nodes, ~530 lines)
2. `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/template_nodes.py` (3 nodes, ~240 lines)

### Files to Update
1. `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/__init__.py` - Add imports/exports
2. `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py` - Register in `_VISUAL_NODE_REGISTRY`

### Estimated Effort
- RAG nodes: 1-1.5 days
- Template nodes: 0.5 days
- Testing: 1 day
- **Total: 2-3 days**

---

## RAG Nodes (Priority: CRITICAL)

| Node | Purpose | Key Ports | Status |
|------|---------|-----------|--------|
| **Embedding** | text → vector | IN: text, model<br/>OUT: embedding (LIST), dimensions | Missing |
| **VectorStoreAdd** | documents → store | IN: docs (LIST), collection_id, metadata<br/>OUT: vector_ids (LIST), count | Missing |
| **VectorSearch** | query → similar docs | IN: query (STRING), collection_id, top_k<br/>OUT: results (LIST), scores (LIST) | Missing |
| **RAG** | query → answer | IN: query, collection_id, model, system_prompt<br/>OUT: response, sources (LIST), confidence | **CRITICAL** |
| **VectorStoreDelete** | cleanup | IN: collection_id, doc_ids (LIST)<br/>OUT: deleted_count, success | Missing |

### RAG Node Workflow
```
Query → Search Vector Store → Retrieve Documents →
Augment Prompt with Sources → LLM Generation → Response + Citations
```

---

## Template Nodes (Priority: MEDIUM)

| Node | Purpose | Key Ports | Status |
|------|---------|-----------|--------|
| **PromptTemplate** | reuse templates | IN: template_id, variables (DICT)<br/>OUT: rendered_prompt, response | Missing |
| **ListTemplates** | discover | IN: (none)<br/>OUT: templates (LIST) | Missing |
| **GetTemplateInfo** | inspect | IN: template_id<br/>OUT: template_info (DICT) | Missing |

---

## Base Class & Mixin

### VisualNode (base_visual_node.py)
```python
class VisualNode(NodeGraphQt.BaseNode):
    def add_exec_input(self, name):      # Execution input port
    def add_exec_output(self, name):     # Execution output port
    def add_typed_input(self, name, DataType):
    def add_typed_output(self, name, DataType):

    def add_text_input(self, name, label, placeholder_text="")
    def add_combo_menu(self, name, label, items=[])
    def add_checkbox(self, name, label, text="", state=False)
```

### LLMVisualNodeMixin (ai_ml/nodes.py)
```python
class LLMVisualNodeMixin:
    def _setup_credential_model_link(self):
        # Auto-updates model dropdown when credential changes
```

---

## Code Template (Copy-Paste Ready)

```python
class VisualEmbeddingNode(VisualNode, LLMVisualNodeMixin):
    """Convert text to vector embeddings."""

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Embedding"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        self.add_text_input("text", "Text", placeholder_text="Text to embed...")

        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)

        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "text-embedding-3-small")

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        self.add_typed_input("text", DataType.STRING)
        self.add_typed_input("model", DataType.STRING)

        self.add_typed_output("embedding", DataType.LIST)
        self.add_typed_output("dimensions", DataType.INTEGER)
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
```

---

## Registration Checklist

- [ ] Create `rag_nodes.py` with 5 classes
- [ ] Create `template_nodes.py` with 3 classes
- [ ] Update `ai_ml/__init__.py` imports/exports
- [ ] Add entries to `_VISUAL_NODE_REGISTRY` in `visual_nodes/__init__.py`
- [ ] Test with: `get_all_visual_node_classes()` returns 18+ nodes
- [ ] Verify ports in canvas UI

---

## Key Differences from LLM Nodes

### RAG Nodes
- Output types: **LIST** (embeddings, search results), **DICT** (metadata)
- Credential optional: can use default provider
- No system_prompt widget (uses defaults)
- Collection management: collection_id is primary parameter

### Template Nodes
- Template ID selector (must load from template store)
- Variable input as DICT (Jinja2 templating)
- Optional execution (render-only mode)
- Metadata outputs: template info, variable requirements

---

## Testing Commands

```bash
# Test node discovery
python -c "from casare_rpa.presentation.canvas.visual_nodes import get_all_visual_node_classes; print(len([n for n in get_all_visual_node_classes() if n.NODE_CATEGORY == 'ai_ml']))"

# Expected: 18

# Test individual node
python -c "from casare_rpa.presentation.canvas.visual_nodes.ai_ml.rag_nodes import VisualRAGNode; n = VisualRAGNode(); print(n.NODE_NAME)"

# Expected: RAG (Retrieve & Generate)
```

---

## Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `ai_ml/nodes.py` | 761 | Current 10 visual nodes |
| `ai_ml/rag_nodes.py` | ~530 | NEW: 5 RAG nodes |
| `ai_ml/template_nodes.py` | ~240 | NEW: 3 template nodes |
| `ai_ml/__init__.py` | 41 | Update: add new imports |
| `visual_nodes/__init__.py` | 610 | Update: add registry entries |

---

## Next Steps

1. **Start with RAGNode** - most critical, teaches pattern for others
2. **Then EmbeddingNode** - foundational for vector operations
3. **Then remaining RAG nodes** - follow same pattern
4. **Finally template nodes** - different widget pattern but simpler

---

**Coverage Target:** 18/18 (100%)
**Priority:** RAG nodes first (they enable knowledge-base workflows)
**Complexity:** Medium (follow existing LLMVisualNodeMixin pattern)

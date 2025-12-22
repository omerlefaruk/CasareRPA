# RAG/AI Visual Nodes Analysis

**Date:** 2025-12-14
**Scope:** CasareRPA visual nodes vs logic nodes comparison
**Thoroughness:** Very thorough - all LLM/AI/RAG node implementations analyzed

---

## Executive Summary

| Category | Status | Count | Notes |
|----------|--------|-------|-------|
| **Existing Visual Nodes** | ✓ Complete | 10 | LLM + AI Condition nodes fully wrapped |
| **Missing Visual Nodes** | ⚠ Critical | 8 | RAG nodes (embeddings, vector store, search) + prompt template nodes |
| **Coverage** | 55% | 10/18 | Half of logic nodes missing visual wrappers |

---

## Part 1: Existing Visual Nodes

### Location
**Directory:** `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\presentation\canvas\visual_nodes\ai_ml\`

**Files:**
- `__init__.py` - Package exports
- `nodes.py` - All 10 visual node implementations (761 lines)

### Existing Visual Nodes (10 total)

#### A. Basic LLM Operations (6 nodes)

| Visual Node | Logic Node | Wrapper Status | Port Mapping |
|------------|-----------|-----------------|--------------|
| `VisualLLMCompletionNode` | `LLMCompletionNode` | ✓ Complete | exec + prompt, model, system_prompt, temperature, max_tokens → response, tokens_used, model_used, success, error |
| `VisualLLMChatNode` | `LLMChatNode` | ✓ Complete | exec + message, conversation_id, model, system_prompt, temperature, max_tokens → response, conversation_id, tokens_used, model_used, success, error |
| `VisualLLMExtractDataNode` | `LLMExtractDataNode` | ✓ Complete | exec + text, schema, model, temperature → extracted_data, raw_response, tokens_used, success, error |
| `VisualLLMSummarizeNode` | `LLMSummarizeNode` | ✓ Complete | exec + text, max_length, style, model, temperature → summary, original_length, summary_length, tokens_used, success, error |
| `VisualLLMClassifyNode` | `LLMClassifyNode` | ✓ Complete | exec + text, categories, multi_label, model, temperature → classification, classifications, confidence, tokens_used, success, error |
| `VisualLLMTranslateNode` | `LLMTranslateNode` | ✓ Complete | exec + text, target_language, source_language, model, temperature → translated_text, detected_language, tokens_used, success, error |

#### B. AI Condition/Control Flow (4 nodes)

| Visual Node | Logic Node | Wrapper Status | Port Mapping |
|------------|-----------|-----------------|--------------|
| `VisualAIConditionNode` | `AIConditionNode` | ✓ Complete | exec_in → exec_true/exec_false + condition, context, model, temperature → result, confidence, reasoning, success, error |
| `VisualAISwitchNode` | `AISwitchNode` | ✓ Complete | exec_in → exec_default + question, options, context, model, temperature → selected_option, confidence, reasoning, all_scores, success, error |
| `VisualAIDecisionTableNode` | `AIDecisionTableNode` | ✓ Complete | exec_in → exec_out + decision_table, context, model, temperature → matched_action, matched_rule_index, confidence, reasoning, all_matches, success, error |
| `VisualAIAgentNode` | `AIAgentNode` | ✓ Complete | exec_in → exec_out/exec_error + goal, context, available_tools, max_steps, timeout, model → result, steps_taken, step_count, total_tokens, execution_time, success, error |

### Key Features of Existing Visual Nodes

**Location:** `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\presentation\canvas\visual_nodes\ai_ml\nodes.py`

1. **LLMVisualNodeMixin** (lines 121-183)
   - Dynamic credential-to-model filtering
   - Auto-updates model dropdown when credential selection changes
   - Fallback to hardcoded LLM_MODELS dict if provider lookup fails
   - Handles both NodeGraphQt's `value_changed` and `currentTextChanged` signals

2. **Credential Management**
   - `get_llm_credentials()` - Fetches available LLM credentials from credential store
   - Support for auto-detect + provider-specific credentials
   - Model list: OpenAI, Anthropic, Google, Mistral, Groq, DeepSeek, Ollama

3. **Widget Creation Pattern**
   - All nodes implement `_create_widgets()` for UI configuration
   - Standard widgets: combo menus for credentials/models, text inputs for parameters
   - Each node calls `_setup_credential_model_link()` in `__init__`

4. **Port Setup Pattern**
   - Execution ports: `add_exec_input()` and `add_exec_output()` for single/branching flows
   - Data inputs: typed inputs matching node parameters
   - Data outputs: standardized success/error/tokens_used outputs
   - DataType mapping: STRING, FLOAT, INTEGER, BOOLEAN, DICT, LIST, ANY

---

## Part 2: Missing Visual Nodes (Critical)

### A. RAG Nodes (5 missing) - HIGHEST PRIORITY

**Location of Logic Nodes:** `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\nodes\llm\rag_nodes.py`

| Logic Node | Visual Wrapper | Missing | Criticality | Use Case |
|-----------|----------------|---------|-------------|----------|
| `EmbeddingNode` | ✗ Missing | `VisualEmbeddingNode` | HIGH | Convert text to vector embeddings for semantic search |
| `VectorStoreAddNode` | ✗ Missing | `VisualVectorStoreAddNode` | HIGH | Add/index documents to vector database |
| `VectorSearchNode` | ✗ Missing | `VisualVectorSearchNode` | HIGH | Semantic similarity search across vector store |
| `RAGNode` | ✗ Missing | `VisualRAGNode` | CRITICAL | Complete RAG pipeline: retrieve documents + generate response |
| `VectorStoreDeleteNode` | ✗ Missing | `VisualVectorStoreDeleteNode` | MEDIUM | Remove documents from vector store by ID/filter |

**Expected Implementation Pattern for RAG Nodes:**

```python
# Each RAG node should follow this structure:
class VisualEmbeddingNode(VisualNode, LLMVisualNodeMixin):
    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Embedding"
    NODE_CATEGORY = "ai_ml"

    def _create_widgets(self):
        # text input
        # model selector (embedding model)
        # optional: api_key

    def setup_ports(self):
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

**RAG Node Details:**

**EmbeddingNode (lines 26-109)**
- Inputs: text, model, api_key
- Outputs: embedding (LIST), dimensions, tokens_used, success, error
- External dependency: `EmbeddingManager` from `infrastructure.ai.embedding_manager`
- Default model: "text-embedding-3-small"

**VectorStoreAddNode (lines 114-223)**
- Inputs: documents (LIST), collection_id, metadata (DICT), chunk_size
- Outputs: vector_ids (LIST), tokens_used, success, error
- Implements document chunking and metadata attachment

**VectorSearchNode (lines 225-330)**
- Inputs: query (STRING), collection_id, top_k, filters (DICT)
- Outputs: results (LIST), scores (LIST), total_results, success, error
- Returns ranked semantic search results

**RAGNode (lines 332-483)**
- Inputs: query (STRING), collection_id, top_k, model, system_prompt, temperature, max_tokens
- Outputs: response (STRING), sources (LIST), confidence, tokens_used, success, error
- Full end-to-end: retrieve documents → augment prompt → generate response
- Critical for knowledge-base-driven workflows

**VectorStoreDeleteNode (lines 485-573)**
- Inputs: collection_id, document_ids (LIST), filter (DICT)
- Outputs: deleted_count (INTEGER), success, error
- Cleanup and management of vector store

---

### B. Prompt Template Nodes (3 missing) - MEDIUM PRIORITY

**Location of Logic Nodes:** `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\nodes\llm\prompt_template_node.py`

| Logic Node | Visual Wrapper | Missing | Criticality | Use Case |
|-----------|----------------|---------|-------------|----------|
| `PromptTemplateNode` | ✗ Missing | `VisualPromptTemplateNode` | MEDIUM | Execute reusable prompt templates with variable substitution |
| `ListTemplatesNode` | ✗ Missing | `VisualListTemplatesNode` | LOW | Browse available prompt templates |
| `GetTemplateInfoNode` | ✗ Missing | `VisualGetTemplateInfoNode` | LOW | Retrieve metadata about specific template |

**Expected Implementation Pattern:**

```python
class VisualPromptTemplateNode(VisualNode, LLMVisualNodeMixin):
    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "Prompt Template"
    NODE_CATEGORY = "ai_ml"

    def _create_widgets(self):
        # template_id selector (dropdown of available templates)
        # variables input (DICT or JSON string)
        # execute checkbox
        # model selector

    def setup_ports(self):
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")
        self.add_typed_input("template_id", DataType.STRING)
        self.add_typed_input("variables", DataType.DICT)
        self.add_typed_input("execute", DataType.BOOLEAN)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_output("rendered_prompt", DataType.STRING)
        self.add_typed_output("system_prompt", DataType.STRING)
        self.add_typed_output("response", DataType.STRING)
        self.add_typed_output("parsed_response", DataType.DICT)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
```

**Prompt Template Node Details:**

**PromptTemplateNode (lines 22-201)**
- Inputs: template_id, variables (DICT), execute (BOOLEAN), model, credential
- Outputs: rendered_prompt (STRING), system_prompt, response, parsed_response (DICT), tokens_used, success, error
- Use case: Reuse tested prompt templates across workflows
- Optional execution: can render without executing, or render + execute in one node

**ListTemplatesNode (lines 203-294)**
- Inputs: None (or category filter)
- Outputs: templates (LIST of IDs/names), total_count, success, error
- Used for discovering available templates

**GetTemplateInfoNode (lines 296-387)**
- Inputs: template_id
- Outputs: template_info (DICT with name, description, variables, etc), success, error
- Used for template introspection

---

## Part 3: Gap Analysis

### Missing Nodes Summary

**Total Logic Nodes:** 18
**Total Visual Nodes:** 10
**Missing Visual Nodes:** 8
**Coverage:** 55.6%

### Breakdown by Priority

#### CRITICAL (1) - Block RAG workflows
- `RAGNode` - No visual wrapper for complete RAG pipeline

#### HIGH (4) - Core RAG operations
- `EmbeddingNode` - Cannot create embeddings visually
- `VectorStoreAddNode` - Cannot populate vector stores visually
- `VectorSearchNode` - Cannot perform semantic search visually
- Already have: LLM completion, chat, extraction (for single-turn usage)

#### MEDIUM (3) - Template management
- `PromptTemplateNode` - Cannot reuse templates visually
- `ListTemplatesNode` - Cannot discover templates visually
- `GetTemplateInfoNode` - Cannot inspect templates visually

#### Existing nodes fully covered
- LLM Completion, Chat, ExtractData, Summarize, Classify, Translate (6/6)
- AI Condition, Switch, Decision Table, Agent (4/4)

---

## Part 4: Implementation Roadmap

### Phase 1: RAG Foundation (1-2 days)
Priority: CRITICAL
Files to create:
1. `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/rag_nodes.py`
   - `VisualEmbeddingNode` (80 lines)
   - `VisualVectorStoreAddNode` (120 lines)
   - `VisualVectorSearchNode` (100 lines)
   - `VisualRAGNode` (150 lines) ← Most important
   - `VisualVectorStoreDeleteNode` (80 lines)

2. Update `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/__init__.py`
   - Add RAG node imports and exports

3. Update `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`
   - Register RAG nodes in `_VISUAL_NODE_REGISTRY`

### Phase 2: Prompt Templates (1 day)
Priority: MEDIUM
Files to create:
1. `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/template_nodes.py`
   - `VisualPromptTemplateNode` (120 lines) ← Most used
   - `VisualListTemplatesNode` (60 lines)
   - `VisualGetTemplateInfoNode` (60 lines)

2. Update `src/casare_rpa/presentation/canvas/visual_nodes/ai_ml/__init__.py`
   - Add template node imports and exports

3. Update `src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`
   - Register template nodes in `_VISUAL_NODE_REGISTRY`

### Phase 3: Integration & Testing (1 day)
- Test complete RAG workflows in canvas
- Test prompt template reuse workflows
- Verify port connections and data flow
- Update documentation with RAG+Template examples

---

## Part 5: Detailed Implementation Guide

### Template for RAG Visual Nodes

All RAG visual nodes should inherit from `VisualNode` and optionally `LLMVisualNodeMixin`:

```python
from typing import Any, List
from loguru import logger
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

class VisualRAGNode(VisualNode, LLMVisualNodeMixin):
    """Visual representation of RAGNode.

    Complete RAG pipeline: retrieve semantically similar documents + generate response.
    """

    __identifier__ = "casare_rpa.ai_ml"
    NODE_NAME = "RAG (Retrieve & Generate)"
    NODE_CATEGORY = "ai_ml"

    def __init__(self) -> None:
        super().__init__()
        self._create_widgets()
        self._setup_credential_model_link()

    def _create_widgets(self) -> None:
        """Create node widgets for configuration."""
        # Collection/vector store selector
        self.add_text_input(
            "collection_id",
            "Collection ID",
            placeholder_text="my-docs, customer-kb, etc"
        )

        # Query input
        self.add_text_input(
            "query",
            "Query",
            placeholder_text="What is the return policy?"
        )

        # Search parameters
        self.add_text_input("top_k", "Top Results", text="5")

        # LLM parameters
        cred_items = [name for _, name in get_llm_credentials()]
        self.add_combo_menu("credential", "API Key", items=cred_items)
        self.add_combo_menu("model", "Model", items=ALL_MODELS)
        self.set_property("model", "gpt-4o-mini")

        self.add_text_input(
            "system_prompt",
            "System Prompt",
            placeholder_text="Answer based on provided documents..."
        )
        self.add_text_input("temperature", "Temperature", text="0.7")
        self.add_text_input("max_tokens", "Max Tokens", text="2000")

    def setup_ports(self) -> None:
        """Setup ports."""
        # Execution flow
        self.add_exec_input("exec_in")
        self.add_exec_output("exec_out")

        # Data inputs
        self.add_typed_input("query", DataType.STRING)
        self.add_typed_input("collection_id", DataType.STRING)
        self.add_typed_input("top_k", DataType.INTEGER)
        self.add_typed_input("model", DataType.STRING)
        self.add_typed_input("system_prompt", DataType.STRING)
        self.add_typed_input("temperature", DataType.FLOAT)
        self.add_typed_input("max_tokens", DataType.INTEGER)

        # Data outputs
        self.add_typed_output("response", DataType.STRING)  # Generated answer
        self.add_typed_output("sources", DataType.LIST)     # Retrieved documents
        self.add_typed_output("confidence", DataType.FLOAT) # Relevance score
        self.add_typed_output("tokens_used", DataType.INTEGER)
        self.add_typed_output("search_results_count", DataType.INTEGER)
        self.add_typed_output("success", DataType.BOOLEAN)
        self.add_typed_output("error", DataType.STRING)
```

### Widget Types to Use

Based on existing patterns in `nodes.py`:

| Widget Type | Method | Example | Use Case |
|------------|--------|---------|----------|
| Text Input | `add_text_input(name, label, text="", placeholder_text="")` | prompt, query, template_id | Simple string parameters |
| Combo Menu | `add_combo_menu(name, label, items=[...])` | model, credential, collection | Dropdown selections |
| Checkbox | `add_checkbox(name, label, text="", state=False)` | multi_label, execute | Boolean flags |
| Number Input | Text input with numeric validation | temperature, max_tokens | Numeric parameters |

### Port Naming Conventions

**Execution Ports:**
- Single flow: `exec_in` → `exec_out`
- Branching: `exec_in` → `exec_true`, `exec_false` (conditions)
- Multi-way: `exec_in` → `exec_default` (switches)
- Error handling: add `exec_error` output

**Data Ports:**
- Inputs: match widget names exactly
- Outputs: descriptive names (response, results, embedding, etc)
- Standardized error ports: always include `success` (BOOLEAN) and `error` (STRING)

---

## Part 6: Existing Code Patterns to Follow

### From VisualLLMCompletionNode (lines 185-237)

**Constructor Pattern:**
```python
def __init__(self) -> None:
    super().__init__()
    self._create_widgets()
    self._setup_credential_model_link()  # ← Required for credential-model linking
```

**Widget Creation:**
```python
def _create_widgets(self) -> None:
    cred_items = [name for _, name in get_llm_credentials()]
    self.add_combo_menu("credential", "API Key", items=cred_items)
    self.add_text_input("prompt", "Prompt", placeholder_text="...")
```

**Port Setup:**
```python
def setup_ports(self) -> None:
    self.add_exec_input("exec_in")
    self.add_exec_output("exec_out")

    # Data inputs (must match widget names)
    self.add_typed_input("prompt", DataType.STRING)

    # Data outputs (standardized)
    self.add_typed_output("response", DataType.STRING)
    self.add_typed_output("tokens_used", DataType.INTEGER)
    self.add_typed_output("model_used", DataType.STRING)
    self.add_typed_output("success", DataType.BOOLEAN)
    self.add_typed_output("error", DataType.STRING)
```

### From VisualAIConditionNode (lines 520-575)

**Branching Execution Pattern:**
```python
def setup_ports(self) -> None:
    # Branching outputs for control flow
    self.add_exec_input("exec_in")
    self.add_exec_output("exec_true")
    self.add_exec_output("exec_false")
```

### From LLMVisualNodeMixin (lines 121-183)

**Credential-Model Linking:**
```python
def _setup_credential_model_link(self) -> None:
    """Link credential changes to model dropdown updates."""
    cred_widget = self.get_widget("credential")
    model_widget = self.get_widget("model")

    if hasattr(cred_widget, "value_changed"):
        cred_widget.value_changed.connect(self._on_credential_changed)
```

---

## Part 7: File Structure

### Current Structure
```
src/casare_rpa/
├── nodes/llm/
│   ├── __init__.py              (18 exported nodes)
│   ├── llm_base.py              (base class)
│   ├── llm_nodes.py             (6 basic LLM nodes)
│   ├── ai_condition_node.py     (AIConditionNode)
│   ├── ai_switch_node.py        (AISwitchNode)
│   ├── ai_decision_table_node.py (AIDecisionTableNode)
│   ├── ai_agent_node.py         (AIAgentNode)
│   ├── prompt_template_node.py  (PromptTemplateNode + 2 others)
│   └── rag_nodes.py             (5 RAG nodes)
│
└── presentation/canvas/visual_nodes/
    └── ai_ml/
        ├── __init__.py          (10 exported visual nodes)
        └── nodes.py             (10 visual node implementations)
```

### After Implementation

```
src/casare_rpa/
└── presentation/canvas/visual_nodes/
    └── ai_ml/
        ├── __init__.py          (18 exported visual nodes)
        ├── nodes.py             (10 current nodes)
        ├── rag_nodes.py         (NEW: 5 RAG visual nodes)
        └── template_nodes.py    (NEW: 3 template visual nodes)
```

---

## Part 8: Testing Checklist

### RAG Nodes Testing
- [ ] EmbeddingNode
  - [ ] Text input → embedding output (correct vector dimensions)
  - [ ] Model parameter switching
  - [ ] Token counting accuracy
  - [ ] Error handling for invalid text

- [ ] VectorStoreAddNode
  - [ ] Document list → stored with collection ID
  - [ ] Metadata attachment
  - [ ] Chunk size parameter respected
  - [ ] Duplicate handling

- [ ] VectorSearchNode
  - [ ] Query → ranked results
  - [ ] Top-k parameter respected
  - [ ] Similarity scores returned
  - [ ] Filter parameter functionality

- [ ] RAGNode (CRITICAL)
  - [ ] End-to-end workflow: query → search → augment → generate
  - [ ] Sources properly cited in output
  - [ ] Token usage tracking
  - [ ] Model switching via credential
  - [ ] Long document handling (chunking)

- [ ] VectorStoreDeleteNode
  - [ ] Document removal
  - [ ] Batch deletion
  - [ ] Non-existent ID handling

### Template Nodes Testing
- [ ] PromptTemplateNode
  - [ ] Template loading by ID
  - [ ] Variable substitution (Jinja2 or similar)
  - [ ] Render without execute
  - [ ] Render + execute in single node

- [ ] ListTemplatesNode
  - [ ] Template discovery
  - [ ] Metadata retrieval

- [ ] GetTemplateInfoNode
  - [ ] Template introspection
  - [ ] Variable requirement detection

### Integration Testing
- [ ] Connect embedding output to RAG input
- [ ] Connect RAG output to subsequent nodes (summarize, translate)
- [ ] Port type matching validation
- [ ] Workflow serialization/deserialization

---

## Part 9: Registration Requirements

### 1. Update `ai_ml/__init__.py`

Add to imports and `__all__`:

```python
# Add to imports
from casare_rpa.presentation.canvas.visual_nodes.ai_ml.rag_nodes import (
    VisualEmbeddingNode,
    VisualVectorStoreAddNode,
    VisualVectorSearchNode,
    VisualRAGNode,
    VisualVectorStoreDeleteNode,
)
from casare_rpa.presentation.canvas.visual_nodes.ai_ml.template_nodes import (
    VisualPromptTemplateNode,
    VisualListTemplatesNode,
    VisualGetTemplateInfoNode,
)

# Add to __all__
__all__ = [
    # ... existing ...
    # RAG nodes
    "VisualEmbeddingNode",
    "VisualVectorStoreAddNode",
    "VisualVectorSearchNode",
    "VisualRAGNode",
    "VisualVectorStoreDeleteNode",
    # Template nodes
    "VisualPromptTemplateNode",
    "VisualListTemplatesNode",
    "VisualGetTemplateInfoNode",
]
```

### 2. Update `visual_nodes/__init__.py`

Add to `_VISUAL_NODE_REGISTRY` dict:

```python
_VISUAL_NODE_REGISTRY = {
    # ... existing ai_ml entries ...

    # RAG nodes
    "VisualEmbeddingNode": "ai_ml.rag_nodes",
    "VisualVectorStoreAddNode": "ai_ml.rag_nodes",
    "VisualVectorSearchNode": "ai_ml.rag_nodes",
    "VisualRAGNode": "ai_ml.rag_nodes",
    "VisualVectorStoreDeleteNode": "ai_ml.rag_nodes",

    # Template nodes
    "VisualPromptTemplateNode": "ai_ml.template_nodes",
    "VisualListTemplatesNode": "ai_ml.template_nodes",
    "VisualGetTemplateInfoNode": "ai_ml.template_nodes",
}
```

### 3. Verify Registration

Run this to verify all nodes are discoverable:

```python
from casare_rpa.presentation.canvas.visual_nodes import get_all_visual_node_classes

all_nodes = get_all_visual_node_classes()
ai_ml_nodes = [n for n in all_nodes if hasattr(n, 'NODE_CATEGORY') and n.NODE_CATEGORY == 'ai_ml']

print(f"Total AI/ML visual nodes: {len(ai_ml_nodes)}")
for node in sorted(ai_ml_nodes, key=lambda n: n.__name__):
    print(f"  - {node.__name__}: {node.NODE_NAME}")
```

Expected output after implementation:
```
Total AI/ML visual nodes: 18
  - VisualAIAgentNode: AI Agent
  - VisualAIConditionNode: AI Condition
  - VisualAIDecisionTableNode: AI Decision Table
  - VisualAISwitchNode: AI Switch
  - VisualEmbeddingNode: Embedding
  - VisualGetTemplateInfoNode: Get Template Info
  - VisualListTemplatesNode: List Templates
  - VisualLLMChatNode: LLM Chat
  - VisualLLMClassifyNode: LLM Classify
  - VisualLLMCompletionNode: LLM Completion
  - VisualLLMExtractDataNode: LLM Extract Data
  - VisualLLMSummarizeNode: LLM Summarize
  - VisualLLMTranslateNode: LLM Translate
  - VisualPromptTemplateNode: Prompt Template
  - VisualRAGNode: RAG (Retrieve & Generate)
  - VisualVectorSearchNode: Vector Search
  - VisualVectorStoreAddNode: Vector Store Add
  - VisualVectorStoreDeleteNode: Vector Store Delete
```

---

## Appendix A: Complete Node Inventory

### Logic Nodes (LLM) - 18 total

**File:** `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\nodes\llm\`

1. **llm_base.py** - Base class (LLMBaseNode)
2. **llm_nodes.py**
   - LLMCompletionNode (line 23)
   - LLMChatNode (line 110)
   - LLMExtractDataNode (line 205)
   - LLMSummarizeNode (line 318)
   - LLMClassifyNode (line 433)
   - LLMTranslateNode (line 589)
3. **ai_condition_node.py**
   - AIConditionNode (line 24)
4. **ai_switch_node.py**
   - AISwitchNode (line 24)
5. **ai_decision_table_node.py**
   - AIDecisionTableNode (line 24)
6. **ai_agent_node.py**
   - AIAgentNode (line 24)
7. **rag_nodes.py**
   - EmbeddingNode (line 26)
   - VectorStoreAddNode (line 114)
   - VectorSearchNode (line 225)
   - RAGNode (line 332)
   - VectorStoreDeleteNode (line 485)
8. **prompt_template_node.py**
   - PromptTemplateNode (line 22)
   - ListTemplatesNode (line 203)
   - GetTemplateInfoNode (line 296)

### Visual Nodes (AI/ML) - 10 current, 18 after implementation

**File:** `c:\Users\Rau\Desktop\CasareRPA\src\casare_rpa\presentation\canvas\visual_nodes\ai_ml\`

**Current (nodes.py):**
1. VisualLLMCompletionNode (line 185)
2. VisualLLMChatNode (line 239)
3. VisualLLMExtractDataNode (line 302)
4. VisualLLMSummarizeNode (line 356)
5. VisualLLMClassifyNode (line 409)
6. VisualLLMTranslateNode (line 462)
7. VisualAIConditionNode (line 520)
8. VisualAISwitchNode (line 577)
9. VisualAIDecisionTableNode (line 640)
10. VisualAIAgentNode (line 697)

**Missing (to implement):**
11. VisualEmbeddingNode (rag_nodes.py)
12. VisualVectorStoreAddNode (rag_nodes.py)
13. VisualVectorSearchNode (rag_nodes.py)
14. VisualRAGNode (rag_nodes.py)
15. VisualVectorStoreDeleteNode (rag_nodes.py)
16. VisualPromptTemplateNode (template_nodes.py)
17. VisualListTemplatesNode (template_nodes.py)
18. VisualGetTemplateInfoNode (template_nodes.py)

---

## Appendix B: Data Flow Examples

### Example 1: Complete RAG Workflow

```
[User Query] → [RAGNode] → [Retrieved Documents + Generated Answer]
                    ↓
              [Credential selector]
              [Model selector]
              [Collection ID]
              [Top-K parameter]
```

Ports flow:
- Input: query (STRING), collection_id (STRING), top_k (INTEGER), model (STRING)
- Output: response (STRING), sources (LIST), confidence (FLOAT), tokens_used (INTEGER)

### Example 2: Template-Based Generation + RAG

```
[PromptTemplateNode] → [rendered_prompt]
                          ↓
                     [RAGNode with custom prompt]
                          ↓
                     [response + sources]
```

### Example 3: Embedding Pipeline

```
[Documents] → [EmbeddingNode] → [embedding vectors]
                     ↓
                [VectorStoreAddNode] → [stored in collection]
                     ↓
            [Later: VectorSearchNode] → [similar docs]
```

---

## Appendix C: Dependencies & Imports

### Required Infrastructure

**RAG nodes depend on:**
- `casare_rpa.infrastructure.ai.embedding_manager` - EmbeddingManager class
- `casare_rpa.infrastructure.ai.vector_store` - VectorStore operations
- `casare_rpa.infrastructure.resources.llm_resource_manager` - LLMResourceManager

**Template nodes depend on:**
- `casare_rpa.infrastructure.ai.prompt_templates` - Template storage/retrieval
- Jinja2 or similar for variable substitution

**All visual nodes depend on:**
- `casare_rpa.presentation.canvas.visual_nodes.base_visual_node` - VisualNode base
- `casare_rpa.domain.value_objects.types` - DataType enum
- `loguru` - Logging

### Import Pattern

```python
from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import VisualNode

# For LLM nodes
from casare_rpa.presentation.canvas.visual_nodes.ai_ml.nodes import (
    get_llm_credentials,
    get_models_for_credential,
    LLMVisualNodeMixin,
    ALL_MODELS,
)
```

---

## Summary

| Aspect | Current | Target | Status |
|--------|---------|--------|--------|
| Visual Nodes | 10 | 18 | 55% complete |
| RAG Coverage | 0% | 100% | Missing (critical) |
| Template Coverage | 0% | 100% | Missing (important) |
| LLM Operations | 10/10 | 10/10 | Complete |
| Lines to Write | - | ~800-1000 | 3 new files |
| Estimated Effort | - | 2-3 days | Moderate |

---

**Report Generated:** 2025-12-14
**Analysis Scope:** Complete LLM/AI/RAG visual node ecosystem
**Confidence Level:** Very High (direct source inspection)

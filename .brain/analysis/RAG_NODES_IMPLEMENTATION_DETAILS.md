# Archived Analysis (Non-Normative)

This file is archived analysis. Do not treat as current rules. See .agent/, .claude/, and .brain/_index.md for active guidance.

---

# RAG Nodes Implementation Details

Complete specifications for creating missing RAG visual nodes.

---

## Node 1: VisualEmbeddingNode

### Purpose
Convert text to vector embeddings for semantic search operations.

### Logic Node Reference
**File:** `src/casare_rpa/nodes/llm/rag_nodes.py:26-109`
**Class:** `EmbeddingNode`

### Ports Specification

#### Execution Ports
- Input: `exec_in`
- Output: `exec_out`

#### Data Input Ports
| Port Name | Type | Required | Default | Widget Type |
|-----------|------|----------|---------|-------------|
| text | STRING | Yes | - | Text input |
| model | STRING | No | "text-embedding-3-small" | Combo menu |
| credential | STRING | No | "auto" | Combo menu |

#### Data Output Ports
| Port Name | Type | Purpose |
|-----------|------|---------|
| embedding | LIST | Vector representation of text (float array) |
| dimensions | INTEGER | Length of embedding vector |
| tokens_used | INTEGER | API tokens consumed |
| success | BOOLEAN | Execution status |
| error | STRING | Error message if failed |

### Widget Configuration
```python
def _create_widgets(self) -> None:
    self.add_text_input(
        "text",
        "Text",
        placeholder_text="Text to embed..."
    )

    cred_items = [name for _, name in get_llm_credentials()]
    self.add_combo_menu("credential", "API Key", items=cred_items)

    embedding_models = [
        "text-embedding-3-small",
        "text-embedding-3-large",
        "text-embedding-ada-002",
    ]
    self.add_combo_menu("model", "Model", items=embedding_models)
    self.set_property("model", "text-embedding-3-small")
```

### Expected Behavior
1. User provides text input
2. Selects embedding model (from provider)
3. Execution: calls `EmbeddingManager.embed_text()`
4. Returns: embedding vector + dimensions + tokens used
5. Success/error ports indicate completion status

### Example Workflow
```
[Text Input] → [Embedding] → [Vector List (1536 dims for ada)]
                              [Tokens Used: 10]
                              [Success: true]
                                    ↓
                            [VectorStoreAdd]
```

---

## Node 2: VisualVectorStoreAddNode

### Purpose
Add or update documents in a vector store collection (with embeddings and metadata).

### Logic Node Reference
**File:** `src/casare_rpa/nodes/llm/rag_nodes.py:114-223`
**Class:** `VectorStoreAddNode`

### Ports Specification

#### Execution Ports
- Input: `exec_in`
- Output: `exec_out`

#### Data Input Ports
| Port Name | Type | Required | Default | Widget Type | Notes |
|-----------|------|----------|---------|-------------|-------|
| documents | LIST | Yes | - | Text input (JSON) | Array of text or {id, text, metadata} |
| collection_id | STRING | Yes | - | Text input | Name of vector collection |
| metadata | DICT | No | {} | Text input (JSON) | Common metadata for all docs |
| chunk_size | INTEGER | No | 1000 | Text input | Split documents if larger |
| embedding_model | STRING | No | auto | Combo menu | Model to use for embeddings |

#### Data Output Ports
| Port Name | Type | Purpose |
|-----------|------|---------|
| vector_ids | LIST | IDs of stored vectors (for later deletion/search) |
| document_count | INTEGER | Number of documents processed |
| chunk_count | INTEGER | Total chunks created (if chunked) |
| tokens_used | INTEGER | API tokens for embeddings |
| success | BOOLEAN | Execution status |
| error | STRING | Error message if failed |

### Widget Configuration
```python
def _create_widgets(self) -> None:
    self.add_text_input(
        "documents",
        "Documents",
        placeholder_text='["doc1 text", "doc2 text"] or [{"id": "1", "text": "...", "source": "..."}]'
    )

    self.add_text_input(
        "collection_id",
        "Collection ID",
        placeholder_text="my-kb, customer-docs, etc"
    )

    self.add_text_input(
        "metadata",
        "Metadata (JSON)",
        placeholder_text='{"source": "pdf", "date": "2025-01-01"}'
    )

    self.add_text_input(
        "chunk_size",
        "Chunk Size",
        text="1000"
    )

    embedding_models = [
        "text-embedding-3-small",
        "text-embedding-3-large",
    ]
    self.add_combo_menu("embedding_model", "Model", items=embedding_models)
    self.set_property("embedding_model", "text-embedding-3-small")
```

### Expected Behavior
1. User provides documents (list of text or JSON objects)
2. Specifies collection ID (creates if doesn't exist)
3. Optional: metadata to attach to all documents
4. Execution: chunks documents if needed → generates embeddings → stores in vector DB
5. Returns: vector IDs, chunk count, token usage
6. Idempotent: can be called multiple times (upsert semantics)

### Example Workflow
```
[Customer Docs] → [VectorStoreAdd] → [Vector IDs: ["vec-1", "vec-2", ...]]
                  (collection: kb)   [Document Count: 5]
                  (metadata: src)    [Tokens Used: 150]
                                     [Success: true]
                                            ↓
                                    [VectorSearch]
```

---

## Node 3: VisualVectorSearchNode

### Purpose
Perform semantic similarity search across a vector store collection.

### Logic Node Reference
**File:** `src/casare_rpa/nodes/llm/rag_nodes.py:225-330`
**Class:** `VectorSearchNode`

### Ports Specification

#### Execution Ports
- Input: `exec_in`
- Output: `exec_out`

#### Data Input Ports
| Port Name | Type | Required | Default | Widget Type | Notes |
|-----------|------|----------|---------|-------------|-------|
| query | STRING | Yes | - | Text input | Search query |
| collection_id | STRING | Yes | - | Text input | Collection to search |
| top_k | INTEGER | No | 5 | Text input | Number of results to return |
| score_threshold | FLOAT | No | 0.0 | Text input | Minimum similarity score (0-1) |
| filter | DICT | No | {} | Text input (JSON) | Metadata filters |

#### Data Output Ports
| Port Name | Type | Purpose |
|-----------|------|---------|
| results | LIST | Retrieved documents [{id, text, score, metadata}, ...] |
| scores | LIST | Similarity scores (0-1, higher = more similar) |
| total_results | INTEGER | Total matching documents |
| query_embedding | LIST | Embedding of query (optional, for debugging) |
| search_time_ms | INTEGER | Milliseconds to execute search |
| success | BOOLEAN | Execution status |
| error | STRING | Error message if failed |

### Widget Configuration
```python
def _create_widgets(self) -> None:
    self.add_text_input(
        "query",
        "Query",
        placeholder_text="What documents match this query?"
    )

    self.add_text_input(
        "collection_id",
        "Collection ID",
        placeholder_text="my-kb"
    )

    self.add_text_input(
        "top_k",
        "Top K Results",
        text="5"
    )

    self.add_text_input(
        "score_threshold",
        "Min Score (0-1)",
        text="0.0"
    )

    self.add_text_input(
        "filter",
        "Metadata Filter (JSON)",
        placeholder_text='{"source": "pdf", "date": {"$gte": "2025-01-01"}}'
    )
```

### Expected Behavior
1. User provides search query
2. Specifies collection to search
3. Sets top_k (number of results) and optional filters
4. Execution: generates embedding for query → searches vector store → returns top matches with scores
5. Results ordered by similarity (highest first)
6. Fast operation (typically <100ms)

### Example Workflow
```
[Query: "How to reset password?"]
         ↓
[VectorSearch (collection: kb)]
         ↓
[Results: ["Setup guide", "FAQ page", "Help article"]]
[Scores: [0.95, 0.87, 0.72]]
         ↓
[Pass to RAGNode for generation]
```

---

## Node 4: VisualRAGNode (CRITICAL)

### Purpose
Complete RAG pipeline: retrieve semantically similar documents, augment prompt with sources, generate answer using LLM.

### Logic Node Reference
**File:** `src/casare_rpa/nodes/llm/rag_nodes.py:332-483`
**Class:** `RAGNode`

### Ports Specification

#### Execution Ports
- Input: `exec_in`
- Output: `exec_out`

#### Data Input Ports
| Port Name | Type | Required | Default | Widget Type | Notes |
|-----------|------|----------|---------|-------------|-------|
| query | STRING | Yes | - | Text input | User question/prompt |
| collection_id | STRING | Yes | - | Text input | Vector store collection |
| top_k | INTEGER | No | 5 | Text input | Documents to retrieve |
| credential | STRING | No | "auto" | Combo menu | LLM API credential |
| model | STRING | No | "gpt-4o-mini" | Combo menu | LLM model to use |
| system_prompt | STRING | No | (default) | Text input | Instructions for LLM |
| temperature | FLOAT | No | 0.7 | Text input | Creativity (0-2) |
| max_tokens | INTEGER | No | 2000 | Text input | Max response length |
| score_threshold | FLOAT | No | 0.0 | Text input | Min similarity (0-1) |

#### Data Output Ports
| Port Name | Type | Purpose |
|-----------|------|---------|
| response | STRING | Generated answer from LLM |
| sources | LIST | Retrieved documents [{id, text, score}, ...] |
| source_count | INTEGER | Number of documents used |
| confidence | FLOAT | Average similarity score of sources |
| tokens_used | INTEGER | Total tokens (search + generation) |
| model_used | STRING | Which LLM was used |
| execution_time_ms | INTEGER | Total time in milliseconds |
| success | BOOLEAN | Execution status |
| error | STRING | Error message if failed |

### Widget Configuration
```python
def _create_widgets(self) -> None:
    # Query input
    self.add_text_input(
        "query",
        "Query",
        placeholder_text="What is the return policy?"
    )

    # Vector store
    self.add_text_input(
        "collection_id",
        "Collection ID",
        placeholder_text="my-kb, customer-docs, etc"
    )

    # Search parameters
    self.add_text_input("top_k", "Top Results", text="5")
    self.add_text_input("score_threshold", "Min Score (0-1)", text="0.0")

    # LLM parameters
    cred_items = [name for _, name in get_llm_credentials()]
    self.add_combo_menu("credential", "API Key", items=cred_items)

    self.add_combo_menu("model", "Model", items=ALL_MODELS)
    self.set_property("model", "gpt-4o-mini")

    self.add_text_input(
        "system_prompt",
        "System Prompt",
        placeholder_text="Answer based on provided documents. If not found, say 'I don't know'."
    )

    self.add_text_input("temperature", "Temperature", text="0.7")
    self.add_text_input("max_tokens", "Max Tokens", text="2000")
```

### Expected Behavior
1. **Retrieval Phase:**
   - User provides query
   - Vector search finds top_k most similar documents
   - Filter by score_threshold

2. **Augmentation Phase:**
   - Prompt = system_prompt + "Context:\n" + source_documents + "\n\nQuestion:" + query
   - System message instructs LLM to cite sources

3. **Generation Phase:**
   - Send augmented prompt to LLM with specified model/temperature
   - LLM generates answer based on sources
   - Return response + sources + metadata

4. **Critical for:** Knowledge-base chatbots, FAQ automation, document Q&A

### Example Workflow
```
User: "What's the return policy?"
         ↓
[RAGNode: collection=kb, model=gpt-4o-mini, top_k=5]
         ↓
Step 1: Search finds [Policy Doc, FAQ Page, Help Article]
Step 2: Augment prompt with these sources
Step 3: LLM generates answer citing sources
         ↓
Response: "According to our policy [source: Policy Doc], you have 30 days..."
Sources: [{id: "doc-1", score: 0.98}, {id: "doc-2", score: 0.85}, ...]
Success: true
```

### Integration Points
- **Upstream:** EmbeddingNode (to populate vector store)
- **Upstream:** VectorStoreAddNode (to add documents)
- **Downstream:** Can chain multiple RAGNodes for multi-hop retrieval
- **Downstream:** LLMTranslateNode (to translate response to other language)
- **Downstream:** LLMSummarizeNode (to summarize response)

---

## Node 5: VisualVectorStoreDeleteNode

### Purpose
Remove documents from a vector store collection (cleanup, corrections, archiving).

### Logic Node Reference
**File:** `src/casare_rpa/nodes/llm/rag_nodes.py:485-573`
**Class:** `VectorStoreDeleteNode`

### Ports Specification

#### Execution Ports
- Input: `exec_in`
- Output: `exec_out`

#### Data Input Ports
| Port Name | Type | Required | Default | Widget Type | Notes |
|-----------|------|----------|---------|-------------|-------|
| collection_id | STRING | Yes | - | Text input | Collection to delete from |
| vector_ids | LIST | No | [] | Text input (JSON) | IDs of vectors to delete |
| filter | DICT | No | {} | Text input (JSON) | Delete by metadata filter |
| delete_all | BOOLEAN | No | false | Checkbox | Delete entire collection |

#### Data Output Ports
| Port Name | Type | Purpose |
|-----------|------|---------|
| deleted_count | INTEGER | Number of vectors deleted |
| collection_exists | BOOLEAN | Collection still exists after operation |
| success | BOOLEAN | Execution status |
| error | STRING | Error message if failed |

### Widget Configuration
```python
def _create_widgets(self) -> None:
    self.add_text_input(
        "collection_id",
        "Collection ID",
        placeholder_text="my-kb"
    )

    self.add_text_input(
        "vector_ids",
        "Vector IDs (JSON array)",
        placeholder_text='["vec-1", "vec-2", "vec-3"]'
    )

    self.add_text_input(
        "filter",
        "Metadata Filter (JSON)",
        placeholder_text='{"source": "old_import", "date": {"$lt": "2025-01-01"}}'
    )

    self.add_checkbox(
        "delete_all",
        "Delete All",
        text="Delete entire collection",
        state=False
    )
```

### Expected Behavior
1. User specifies collection
2. Deletion mode:
   - **By ID:** vector_ids parameter
   - **By Filter:** metadata filter (e.g., source=old, date<2025)
   - **All:** delete_all=true (careful!)
3. Execution: removes documents from vector store
4. Returns: count deleted, whether collection still exists
5. Idempotent: deleting non-existent IDs doesn't error

### Example Workflow
```
[Cleanup old documents]
         ↓
[VectorStoreDelete:
 collection=kb,
 filter={"source": "v1"}]
         ↓
[Deleted Count: 47]
[Collection Exists: true]
[Success: true]
```

### Safety Notes
- `delete_all=true` is dangerous - requires explicit toggle
- Filter-based deletion is safer than ID-based
- Cannot recover deleted vectors (no undo)

---

## Cross-Node Integration

### Scenario 1: Build Knowledge Base
```
[Load PDF]
   ↓
[Split into chunks]
   ↓
[Add to Vector Store]
   ↓
[RAGNode] → Answers user questions
```

### Scenario 2: Multi-Hop RAG
```
[Query 1]
   ↓
[RAGNode: KB1] → [Response + Sources]
   ↓
[Query 2] (based on Response 1)
   ↓
[RAGNode: KB2] → [Final Answer]
```

### Scenario 3: Filtered Search
```
[Query]
   ↓
[VectorSearch:
 filter={source: "policy"}]
   ↓
[Top 3 policy documents]
   ↓
[Manual review or auto-processing]
```

---

## Testing Checklist

### EmbeddingNode
- [ ] Text input produces valid embedding vector
- [ ] Embedding dimensions match model (ada: 1536, small: 1536, large: 3072)
- [ ] Different texts produce different embeddings
- [ ] Token counting is accurate
- [ ] Error handling for invalid text

### VectorStoreAddNode
- [ ] Documents stored with correct collection_id
- [ ] Metadata attached to documents
- [ ] Chunking works for large documents
- [ ] Duplicate IDs are upserted (not duplicated)
- [ ] Returns valid vector_ids for later reference

### VectorSearchNode
- [ ] Query returns top_k results sorted by score
- [ ] Score threshold filters correctly
- [ ] Metadata filters work
- [ ] Similarity scores between 0 and 1
- [ ] Empty query returns error

### RAGNode (CRITICAL)
- [ ] End-to-end: query → search → generate
- [ ] Sources correctly cited in response
- [ ] Temperature changes affect response variety
- [ ] Model switching works (via credential)
- [ ] Long documents are handled (chunking)
- [ ] No sources returns graceful error
- [ ] Token counting includes search + generation

### VectorStoreDeleteNode
- [ ] Delete by ID removes correct documents
- [ ] Delete by filter removes matching documents
- [ ] Delete non-existent ID doesn't error
- [ ] delete_all=true removes everything

---

## Performance Considerations

### Embedding
- Typical time: 100-500ms per document
- Batch if possible (not yet exposed in visual nodes)
- Cost: proportional to token count

### Vector Search
- Typical time: 10-100ms (in-memory)
- Typical time: 100-1000ms (cloud)
- Scales: O(1) with top_k (is approximate search)

### RAG Node
- Typical time: 500ms - 5 seconds
  - Search: 100-200ms
  - LLM: 1-5 seconds
  - Overhead: <100ms

### Optimization Tips
- Batch documents in VectorStoreAdd
- Use score_threshold to reduce results passed to LLM
- Use smaller models (gpt-4o-mini) for RAG
- Pre-compute embeddings offline when possible

---

## DataType Reference

All nodes must use correct DataType enums:

```python
from casare_rpa.domain.value_objects.types import DataType

# Basic types
DataType.STRING       # Text
DataType.INTEGER      # Whole numbers
DataType.FLOAT        # Decimal numbers
DataType.BOOLEAN      # True/False

# Collections
DataType.LIST         # Array of items
DataType.DICT         # Key-value pairs

# Special
DataType.ANY          # Accept anything
DataType.BYTES        # Binary data (embeddings)
```

For embeddings specifically:
- Vector: `DataType.LIST` (list of floats)
- Metadata: `DataType.DICT`
- IDs: `DataType.STRING` or `DataType.LIST`

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| "Collection not found" | VectorStoreAdd not run first | Ensure VectorStoreAdd runs before VectorSearch |
| "No matching documents" | Query too specific or low top_k | Increase top_k, lower threshold |
| "Embedding dimensions mismatch" | Using different embedding models | Use same model in Add and Search |
| "Out of memory" | Embedding too many documents at once | Chunk documents smaller, embed batch-by-batch |
| "API rate limit" | Too many requests | Add delay nodes between operations |

---

**Implementation Status:** Ready to implement
**Estimated LOC:** ~800 lines total
**Test Coverage:** ~30 test cases per node
**Documentation:** Complete with examples

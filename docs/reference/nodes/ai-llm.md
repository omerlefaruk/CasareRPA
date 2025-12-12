# AI/LLM Nodes

AI/LLM nodes integrate Large Language Models for intelligent text processing, generation, and analysis. These nodes support multiple LLM providers and include RAG (Retrieval-Augmented Generation) capabilities.

## Overview

| Category | Nodes |
|----------|-------|
| **Generation** | LLMCompletionNode, LLMChatNode |
| **Analysis** | LLMExtractDataNode, LLMClassifyNode, LLMSummarizeNode, LLMTranslateNode |
| **RAG** | EmbeddingNode, VectorStoreAddNode, VectorSearchNode, RAGNode, VectorStoreDeleteNode |
| **Agents** | AIAgentNode |

---

## Common Properties

All LLM nodes share these configuration properties:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `model` | STRING | `gpt-4o-mini` | LLM model identifier |
| `temperature` | FLOAT | `0.7` | Creativity (0.0-2.0) |
| `max_tokens` | INTEGER | `1000` | Maximum response tokens |
| `system_prompt` | TEXT | `""` | System/persona instruction |
| `api_key` | STRING | `""` | API key (or use credential_name) |
| `credential_name` | STRING | `""` | Vault credential name |

### Supported Models

- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3-5-sonnet-20241022, claude-3-haiku
- **Local**: Ollama models via API endpoint

---

## Generation Nodes

### LLMCompletionNode

Generate text completion from a single prompt.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `prompt` | TEXT | (required) | Input prompt text |
| `model` | STRING | `gpt-4o-mini` | LLM model |
| `temperature` | FLOAT | `0.7` | Response creativity |
| `max_tokens` | INTEGER | `1000` | Max response length |
| `system_prompt` | TEXT | `""` | System instruction |

#### Ports

**Inputs:**
- `prompt` (STRING) - Prompt text

**Outputs:**
- `response` (STRING) - Generated text
- `tokens_used` (INTEGER) - Total tokens consumed
- `model_used` (STRING) - Model that was used
- `success` (BOOLEAN) - Completion success
- `error` (STRING) - Error message

#### Example

```python
# Generate product description
completion = LLMCompletionNode(
    node_id="generate_description",
    config={
        "prompt": "Write a compelling product description for: {{product_name}}. Features: {{features}}",
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "max_tokens": 200,
        "system_prompt": "You are a creative marketing copywriter."
    }
)
```

---

### LLMChatNode

Multi-turn chat conversation maintaining history.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `message` | TEXT | (required) | User message |
| `conversation_id` | STRING | `""` | Conversation ID (auto-generated if empty) |
| `model` | STRING | `gpt-4o-mini` | LLM model |
| `temperature` | FLOAT | `0.7` | Response creativity |
| `max_tokens` | INTEGER | `1000` | Max response length |
| `system_prompt` | TEXT | `""` | Persona/context |

#### Ports

**Inputs:**
- `message` (STRING) - User message
- `conversation_id` (STRING) - Existing conversation ID

**Outputs:**
- `response` (STRING) - AI response
- `conversation_id` (STRING) - Conversation ID for continuation
- `tokens_used` (INTEGER) - Tokens consumed
- `model_used` (STRING) - Model used
- `success` (BOOLEAN) - Success status

#### Example

```python
# Customer support chatbot
chat = LLMChatNode(
    node_id="support_chat",
    config={
        "message": "{{customer_message}}",
        "conversation_id": "{{session_id}}",
        "model": "gpt-4o-mini",
        "system_prompt": "You are a helpful customer support agent for {{company_name}}. Be polite and concise."
    }
)
```

---

## Analysis Nodes

### LLMExtractDataNode

Extract structured data from unstructured text using JSON schema.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | TEXT | (required) | Text to extract from |
| `schema` | JSON | (required) | JSON schema defining fields |
| `model` | STRING | `gpt-4o-mini` | LLM model |
| `temperature` | FLOAT | `0.0` | Low for accuracy |

#### Ports

**Inputs:**
- `text` (STRING) - Source text
- `schema` (DICT) - Extraction schema

**Outputs:**
- `extracted_data` (DICT) - Extracted structured data
- `raw_response` (STRING) - Raw JSON string
- `tokens_used` (INTEGER) - Tokens consumed
- `success` (BOOLEAN) - Extraction success
- `error` (STRING) - Error message

#### Schema Example

```json
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "order_total": "number",
  "items": ["string"]
}
```

#### Example

```python
# Extract invoice data
extract = LLMExtractDataNode(
    node_id="extract_invoice",
    config={
        "text": "{{email_body}}",
        "schema": {
            "invoice_number": "string",
            "amount": "number",
            "due_date": "string",
            "vendor": "string"
        },
        "temperature": 0.0
    }
)
```

---

### LLMClassifyNode

Classify text into predefined categories.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | TEXT | (required) | Text to classify |
| `categories` | LIST | (required) | Available categories |
| `multi_label` | BOOLEAN | `false` | Allow multiple categories |
| `model` | STRING | `gpt-4o-mini` | LLM model |
| `temperature` | FLOAT | `0.0` | Low for consistency |

#### Ports

**Inputs:**
- `text` (STRING) - Text to classify
- `categories` (LIST) - Category options
- `multi_label` (BOOLEAN) - Multi-label mode

**Outputs:**
- `classification` (STRING) - Primary category
- `classifications` (LIST) - All assigned categories
- `confidence` (DICT) - Confidence scores
- `tokens_used` (INTEGER) - Tokens consumed
- `success` (BOOLEAN) - Classification success

#### Example

```python
# Classify support tickets
classify = LLMClassifyNode(
    node_id="classify_ticket",
    config={
        "text": "{{ticket_content}}",
        "categories": ["billing", "technical", "general", "complaint", "feature_request"],
        "multi_label": False,
        "temperature": 0.0
    }
)
```

---

### LLMSummarizeNode

Summarize text in different styles.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | TEXT | (required) | Text to summarize |
| `max_length` | INTEGER | `200` | Target word count |
| `style` | STRING | `paragraph` | Style: paragraph, bullet_points, key_points |
| `model` | STRING | `gpt-4o-mini` | LLM model |
| `temperature` | FLOAT | `0.5` | Creativity level |

#### Ports

**Inputs:**
- `text` (STRING) - Source text
- `max_length` (INTEGER) - Maximum words
- `style` (STRING) - Summarization style

**Outputs:**
- `summary` (STRING) - Generated summary
- `original_length` (INTEGER) - Original text length
- `summary_length` (INTEGER) - Summary length
- `tokens_used` (INTEGER) - Tokens consumed
- `success` (BOOLEAN) - Summarization success

#### Example

```python
# Summarize meeting notes
summarize = LLMSummarizeNode(
    node_id="summarize_meeting",
    config={
        "text": "{{meeting_transcript}}",
        "max_length": 150,
        "style": "bullet_points"
    }
)
```

---

### LLMTranslateNode

Translate text between languages.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | TEXT | (required) | Text to translate |
| `target_language` | STRING | (required) | Target language |
| `source_language` | STRING | `""` | Source language (auto-detect if empty) |
| `model` | STRING | `gpt-4o-mini` | LLM model |
| `temperature` | FLOAT | `0.3` | Translation fidelity |

#### Ports

**Inputs:**
- `text` (STRING) - Source text
- `target_language` (STRING) - Target language
- `source_language` (STRING) - Source language (optional)

**Outputs:**
- `translated_text` (STRING) - Translation
- `detected_language` (STRING) - Source language
- `tokens_used` (INTEGER) - Tokens consumed
- `success` (BOOLEAN) - Translation success

#### Example

```python
# Translate customer message
translate = LLMTranslateNode(
    node_id="translate_message",
    config={
        "text": "{{customer_message}}",
        "target_language": "English",
        "temperature": 0.2
    }
)
```

---

## RAG Nodes

Retrieval-Augmented Generation nodes enable semantic search and context-aware responses.

### EmbeddingNode

Generate vector embeddings from text.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `text` | TEXT | (required) | Text to embed |
| `model` | STRING | `text-embedding-3-small` | Embedding model |
| `api_key` | STRING | `""` | API key |

#### Ports

**Inputs:**
- `text` (STRING) - Text to embed

**Outputs:**
- `embedding` (LIST) - Vector embedding
- `dimensions` (INTEGER) - Embedding dimensions
- `tokens_used` (INTEGER) - Tokens consumed
- `success` (BOOLEAN) - Success status

#### Example

```python
# Generate embedding for document
embed = EmbeddingNode(
    node_id="embed_doc",
    config={
        "text": "{{document_content}}",
        "model": "text-embedding-3-small"
    }
)
```

---

### VectorStoreAddNode

Add documents to vector store collection.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `documents` | LIST | (required) | Documents to add |
| `collection` | STRING | `default` | Collection name |
| `embeddings` | LIST | `[]` | Pre-computed embeddings |

#### Document Format

```json
[
  {
    "id": "doc1",
    "content": "Document text content",
    "metadata": {"source": "email", "date": "2024-01-15"}
  }
]
```

#### Ports

**Inputs:**
- `documents` (LIST) - Document list
- `collection` (STRING) - Collection name
- `embeddings` (LIST) - Pre-computed embeddings

**Outputs:**
- `count` (INTEGER) - Documents added
- `collection_name` (STRING) - Collection used
- `success` (BOOLEAN) - Success status

---

### VectorSearchNode

Perform semantic search in vector store.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `query` | TEXT | (required) | Search query |
| `collection` | STRING | `default` | Collection to search |
| `top_k` | INTEGER | `5` | Number of results |
| `filter` | JSON | `{}` | Metadata filter |

#### Ports

**Inputs:**
- `query` (STRING) - Search query
- `collection` (STRING) - Collection name
- `top_k` (INTEGER) - Result count
- `filter` (DICT) - Metadata filter
- `query_embedding` (LIST) - Pre-computed query embedding

**Outputs:**
- `results` (LIST) - Search results with scores
- `top_result` (DICT) - Best match
- `result_count` (INTEGER) - Number of results
- `success` (BOOLEAN) - Search success

---

### RAGNode

Full RAG pipeline: retrieve context, then generate response.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `question` | TEXT | (required) | User question |
| `collection` | STRING | `default` | Vector collection |
| `top_k` | INTEGER | `3` | Context documents |
| `prompt_template` | TEXT | (default template) | RAG prompt template |
| `model` | STRING | `gpt-4o-mini` | Generation model |
| `temperature` | FLOAT | `0.7` | Response creativity |

#### Default Prompt Template

```
Use the following context to answer the question.
If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:
```

#### Ports

**Inputs:**
- `question` (STRING) - User question
- `collection` (STRING) - Collection name
- `top_k` (INTEGER) - Context count
- `prompt_template` (STRING) - Custom template

**Outputs:**
- `answer` (STRING) - Generated answer
- `context` (STRING) - Retrieved context
- `sources` (LIST) - Source documents
- `tokens_used` (INTEGER) - Tokens consumed
- `success` (BOOLEAN) - Success status

#### Example

```python
# Knowledge base Q&A
rag = RAGNode(
    node_id="kb_answer",
    config={
        "question": "{{user_question}}",
        "collection": "company_docs",
        "top_k": 3,
        "model": "gpt-4o-mini",
        "system_prompt": "You are a helpful assistant answering questions about our company policies."
    }
)
```

---

### VectorStoreDeleteNode

Delete documents from vector store.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `document_ids` | LIST | (required) | Document IDs to delete |
| `collection` | STRING | `default` | Collection name |

#### Ports

**Outputs:**
- `deleted_count` (INTEGER) - Documents deleted
- `success` (BOOLEAN) - Deletion success

---

## Agent Nodes

### AIAgentNode

Autonomous AI agent with multi-step reasoning and tool use.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `goal` | TEXT | (required) | Task goal description |
| `context` | ANY | `null` | Initial context/data |
| `available_tools` | LIST | `[]` | Available tool names |
| `max_steps` | INTEGER | `10` | Maximum reasoning steps |
| `timeout` | FLOAT | `300.0` | Timeout in seconds |
| `model` | STRING | `gpt-4o-mini` | LLM model |

#### ReAct Pattern

The agent uses the ReAct pattern:
1. **Reason**: Analyze the goal and current state
2. **Act**: Choose and execute a tool
3. **Observe**: Process tool results
4. **Repeat**: Continue until goal achieved or limit reached

#### Ports

**Inputs:**
- `goal` (STRING) - Task description
- `context` (ANY) - Initial context
- `available_tools` (LIST) - Tool names
- `max_steps` (INTEGER) - Step limit
- `timeout` (FLOAT) - Timeout seconds

**Outputs:**
- `result` (ANY) - Final result
- `steps_taken` (LIST) - Execution trace
- `step_count` (INTEGER) - Steps taken
- `total_tokens` (INTEGER) - Total tokens used
- `execution_time` (FLOAT) - Duration
- `success` (BOOLEAN) - Task success
- `error` (STRING) - Error message

#### Example

```python
# Complex data processing agent
agent = AIAgentNode(
    node_id="data_agent",
    config={
        "goal": "Download the sales report from {{report_url}}, extract the monthly totals, and send a summary to {{email}}",
        "available_tools": ["http_download", "pdf_extract", "email_send"],
        "max_steps": 10,
        "timeout": 300.0,
        "model": "gpt-4o"
    }
)
```

---

## Complete Example: Document Q&A System

```python
# 1. Add documents to vector store
add_docs = VectorStoreAddNode(
    node_id="index_docs",
    config={
        "documents": "{{documents}}",
        "collection": "knowledge_base"
    }
)

# 2. Search for relevant context
search = VectorSearchNode(
    node_id="search_context",
    config={
        "query": "{{user_question}}",
        "collection": "knowledge_base",
        "top_k": 5
    }
)

# 3. Generate answer with context
answer = RAGNode(
    node_id="generate_answer",
    config={
        "question": "{{user_question}}",
        "collection": "knowledge_base",
        "model": "gpt-4o-mini",
        "temperature": 0.7
    }
)
```

---

## Best Practices

### Temperature Guidelines

| Use Case | Temperature |
|----------|-------------|
| Data extraction | 0.0 |
| Classification | 0.0-0.2 |
| Translation | 0.2-0.4 |
| Summarization | 0.4-0.6 |
| Creative writing | 0.7-1.0 |
| Brainstorming | 1.0-1.5 |

### Token Management

- Monitor `tokens_used` output for cost tracking
- Use `max_tokens` to limit responses
- Smaller models (gpt-4o-mini) for simple tasks
- Larger models (gpt-4o) for complex reasoning

### Error Handling

All LLM nodes output `success` and `error`:

```python
# Always check success before using response
if outputs["success"]:
    answer = outputs["response"]
else:
    log_error(outputs["error"])
    # Handle gracefully
```

### RAG Best Practices

1. **Chunk Size**: Split documents into 500-1000 token chunks
2. **Overlap**: Use 10-20% overlap between chunks
3. **Metadata**: Include source, date, category in metadata
4. **top_k**: Start with 3-5, adjust based on accuracy

### Security

> **Warning:** Never hardcode API keys. Use:
> - `credential_name` for vault lookup
> - Environment variables
> - Variable placeholders (`{{api_key}}`)

## Related Documentation

- [HTTP Nodes](http.md) - External API calls
- [Data Operations](data-operations.md) - Process LLM outputs
- [Control Flow](control-flow.md) - Conditional logic based on classifications

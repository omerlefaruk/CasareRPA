# Qdrant Debugging & Verification Guide

## Health Check

### 1. Verify Indexing

**Check if index exists:**
```bash
# From CasareRPA root
ls -la .qdrant/

# Should show:
# - config.json
# - collections/
#   └── casare_codebase/
```

**Verify index size:**
```bash
# Windows PowerShell
(Get-Item ".qdrant" -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

# Expected: 50-100 MB
```

### 2. Verify MCP Server Configuration

**Check .mcp.json:**
```bash
cat .mcp.json

# Verify:
# - qdrant.command exists (mcp-server-qdrant.exe)
# - qdrant.env.QDRANT_LOCAL_PATH = "C:/Users/Rau/Desktop/CasareRPA/.qdrant"
# - qdrant.env.COLLECTION_NAME = "casare_codebase"
# - qdrant.env.EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

### 3. Verify Embedding Model

**Check installed packages:**
```bash
pip list | grep -E "(fastembed|sentence-transformers|qdrant)"

# Expected:
# fastembed            (version)
# sentence-transformers (version)
# qdrant-client        (version)
# mcp-server-qdrant    (version)
```

### 4. Test MCP Server Directly

**Windows Command Prompt:**
```cmd
# Start MCP server
set QDRANT_LOCAL_PATH=C:/Users/Rau/Desktop/CasareRPA/.qdrant
set COLLECTION_NAME=casare_codebase
set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
mcp-server-qdrant
```

**Should show (no errors):**
```
# Server should initialize and wait for stdin
# No error messages
```

**Kill server:**
```
Ctrl+C
```

## Indexing Troubleshooting

### Issue: Indexer Crashes

**Symptom:**
```
Traceback:
ModuleNotFoundError: No module named 'qdrant_client'
```

**Fix:**
```bash
pip install qdrant-client fastembed sentence-transformers
python scripts/index_codebase_qdrant.py
```

### Issue: Embedding Model Download Fails

**Symptom:**
```
Loading embedding model...
Traceback: ConnectionError
```

**Fix:**
```bash
# Install model manually
pip install sentence-transformers
python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')"

# Then try indexing again
python scripts/index_codebase_qdrant.py
```

### Issue: Collection Not Created

**Symptom:**
```
Creating collection: casare_codebase
Traceback: QdrantError
```

**Fix:**
```bash
# Delete corrupted collection
rm -r .qdrant/

# Re-run indexer
python scripts/index_codebase_qdrant.py
```

### Issue: Vector Name Mismatch

**Symptom:**
- Indexer runs successfully
- MCP server returns empty results
- No errors in MCP logs

**Root Cause:**
```python
# Indexer creates:
vector_name = "fast-all-minilm-l6-v2"

# Server tries to use:
vector_name = "all-minilm-l6-v2"  # DIFFERENT!

# Result: Collection appears empty
```

**Debug:**
```bash
# Check indexer vector name
grep "VECTOR_NAME =" scripts/index_codebase_qdrant.py
# Expected: VECTOR_NAME = "fast-all-minilm-l6-v2"

# Check embedding model in MCP config
cat .mcp.json | grep EMBEDDING_MODEL
# Should contain: "sentence-transformers/all-MiniLM-L6-v2"
```

**Fix:**
```bash
# Re-index (this will auto-set correct vector name)
python scripts/index_codebase_qdrant.py

# Restart Claude Code to reload MCP
```

## MCP Server Troubleshooting

### Issue: MCP Server Doesn't Start

**Symptom:**
```
Claude Code: MCP Server Error - qdrant
MCP Server crashed
```

**Check:**
```bash
# 1. Verify .mcp.json syntax
python -m json.tool .mcp.json

# 2. Verify .qdrant directory exists
ls .qdrant/

# 3. Try running server directly
mcp-server-qdrant --help
```

**Fix:**
```bash
# Check for .qdrant corruption
rm -r .qdrant/
python scripts/index_codebase_qdrant.py

# Restart Claude Code
```

### Issue: Slow Search Performance

**Symptom:**
```
qdrant-find: "search query"
# Takes >5 seconds to respond
```

**Causes:**
1. Large collection (>5000 chunks)
2. Slow embedding provider (first query)
3. Network latency (stdio communication)

**Debug:**
```bash
# Check collection size
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(path='.qdrant')
points = client.count('casare_codebase')
print(f'Total points: {points.count}')
"

# Check index integrity
python -c "
from qdrant_client import QdrantClient
client = QdrantClient(path='.qdrant')
info = client.get_collection('casare_codebase')
print(f'Vectors config: {info.config.vectors_config}')
"
```

**Performance Tips:**
- First query is slow (model load): ~2s
- Subsequent queries: ~500ms
- Large collections (>10k chunks) may be slow
- Normal: 500ms-1s per query

## Direct Python Testing

### Test 1: Verify Index Contents

```python
from qdrant_client import QdrantClient

# Connect to local Qdrant
client = QdrantClient(path=".qdrant")

# Check collection exists
collections = client.get_collections()
collection_names = [c.name for c in collections.collections]
print(f"Collections: {collection_names}")

# Check point count
points = client.count("casare_codebase")
print(f"Total points: {points.count}")

# Get sample point
sample = client.scroll("casare_codebase", limit=1)
if sample[0]:
    print(f"\nSample point:")
    print(f"  ID: {sample[0][0].id}")
    print(f"  Payload: {sample[0][0].payload}")
```

### Test 2: Verify Embedding Model

```python
from fastembed import TextEmbedding

# Load model
model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

# Test embedding
text = "browser automation click element"
embeddings = list(model.embed([text]))
embedding = embeddings[0]

print(f"Query: {text}")
print(f"Vector size: {len(embedding)}")
print(f"Vector (first 10): {embedding[:10]}")
```

### Test 3: Verify Search

```python
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

client = QdrantClient(path=".qdrant")
model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

# Embed query
query = "browser click automation"
query_vector = list(model.embed([query]))[0]

# Search
results = client.search(
    collection_name="casare_codebase",
    query_vector=query_vector,
    using="fast-all-minilm-l6-v2",
    limit=5
)

print(f"Query: {query}")
print(f"Results: {len(results)}")
for result in results:
    print(f"\n  Score: {result.score:.3f}")
    print(f"  Name: {result.payload.get('name')}")
    print(f"  Type: {result.payload.get('type')}")
    print(f"  Path: {result.payload.get('path')}")
```

## Verification Checklist

- [ ] `.qdrant/` directory exists
- [ ] `.qdrant/config.json` is valid
- [ ] `.qdrant/collections/casare_codebase/` exists
- [ ] `.mcp.json` has valid qdrant config
- [ ] Environment variables correct in `.mcp.json`
- [ ] Embedding model installed: `pip list | grep sentence-transformers`
- [ ] MCP server binary exists: `which mcp-server-qdrant`
- [ ] Test search returns results (see Test 3 above)
- [ ] Vector name matches: `fast-all-minilm-l6-v2`
- [ ] Collection name correct: `casare_codebase`

## Re-Index Procedure

When to re-index:
- After significant code changes (>50 new files)
- After moving/renaming files
- After major refactoring
- If search results become irrelevant
- If "collection appears empty" error

**Full re-index:**
```bash
# 1. Remove old index
rm -r .qdrant/

# 2. Run indexer
python scripts/index_codebase_qdrant.py

# 3. Verify success
ls .qdrant/collections/casare_codebase/

# 4. Restart Claude Code
# (To reload MCP server with new index)
```

**Expected output:**
```
Indexing CasareRPA codebase into Qdrant
  Source: src/
  Qdrant path: .qdrant
  Collection: casare_codebase

Loading embedding model...
  Embedding dimension: 384

Initializing Qdrant...
  Creating collection: casare_codebase
  Vector name: fast-all-minilm-l6-v2

Extracting code chunks...
  Processing: src/casare_rpa/domain/...

Found 2000+ chunks from 280+ files

Generating embeddings and upserting...
  Upserted 100/2000+ points
  ...

Indexing complete!
  Total points: 2000+
  Collection: casare_codebase

Restart Claude Code to load the new MCP server.
```

## Debugging MCP Server Logs

### Capture MCP Server Output

**Windows Command Prompt:**
```cmd
# Redirect stderr and stdout
mcp-server-qdrant 2>&1 | tee mcp_server.log

# Will create: mcp_server.log
```

### Check for Common Errors

```bash
# Look for vector name errors
grep -i "vector.*name" mcp_server.log

# Look for embedding errors
grep -i "embedding" mcp_server.log

# Look for connection errors
grep -i "connection\|timeout" mcp_server.log
```

## Performance Profiling

### Measure Index Size

```bash
# Total size
du -sh .qdrant/

# By component
du -sh .qdrant/collections/
du -sh .qdrant/snapshots/
```

### Measure Query Performance

```python
import time
from qdrant_client import QdrantClient
from fastembed import TextEmbedding

client = QdrantClient(path=".qdrant")
model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

query = "browser automation"

# Measure embedding time
start = time.time()
query_vector = list(model.embed([query]))[0]
embed_time = time.time() - start

# Measure search time
start = time.time()
results = client.search(
    collection_name="casare_codebase",
    query_vector=query_vector,
    using="fast-all-minilm-l6-v2",
    limit=10
)
search_time = time.time() - start

print(f"Embedding time: {embed_time*1000:.1f}ms")
print(f"Search time: {search_time*1000:.1f}ms")
print(f"Total: {(embed_time+search_time)*1000:.1f}ms")
```

**Expected results:**
- Embedding: 100-200ms (first time), 50-100ms (cached)
- Search: 300-500ms
- Total: 400-700ms

## Summary

| Issue | Debug Command | Expected |
|-------|---|---|
| Index doesn't exist | `ls .qdrant/` | Directory present |
| MCP config broken | `python -m json.tool .mcp.json` | Valid JSON |
| Vector name wrong | `grep VECTOR_NAME scripts/` | `fast-all-minilm-l6-v2` |
| Model not installed | `pip list \| grep sentence` | Package listed |
| Search returns nothing | Run Test 3 | Results shown |
| Search is slow | Measure timing | <1s typical |

## When to Ask for Help

If after trying above steps:
1. Index still won't build → Check system Python version (3.12+)
2. MCP server crashes → Check .qdrant corruption
3. Search returns empty → Verify vector name (see above)
4. Search is irrelevant → Re-index with latest code

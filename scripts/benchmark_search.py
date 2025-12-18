"""
Benchmark script for the ChromaDB semantic search.
"""

import asyncio
import time
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from casare_rpa.infrastructure.ai.vector_store import get_vector_store
from fastembed import TextEmbedding

PERSIST_PATH = str(project_root / ".chroma")
COLLECTION = "casare_codebase"


async def benchmark_search():
    queries = [
        "BaseNode implementation",
        "how to create a node",
        "browser automation click",
        "HTTP POST request",
        "workflow execution",
    ]

    print("=== ChromaDB Search Benchmark ===\n")

    # Cold start
    print("1. Cold Start (first load)...")
    start = time.perf_counter()
    vector_store = get_vector_store(persist_path=PERSIST_PATH)
    embed_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    cold_init = time.perf_counter() - start
    print(f"   Initialization: {cold_init:.3f}s\n")

    # Warm searches
    print("2. Warm Searches (after init)...")
    times = []
    for query in queries:
        start = time.perf_counter()
        embeddings = list(embed_model.embed([query]))
        query_embedding = embeddings[0].tolist()

        results = await vector_store.search(
            query=query, collection=COLLECTION, top_k=5, query_embedding=query_embedding
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        print(f"   '{query[:30]}...': {elapsed*1000:.1f}ms ({len(results)} results)")

    avg = sum(times) / len(times)
    print(f"\n   Average warm search: {avg*1000:.1f}ms")
    print(f"   Total benchmark time: {cold_init + sum(times):.2f}s")


if __name__ == "__main__":
    asyncio.run(benchmark_search())

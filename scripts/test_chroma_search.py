import asyncio
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from casare_rpa.infrastructure.ai.vector_store import get_vector_store
from fastembed import TextEmbedding


async def test_search():
    persist_path = str(project_root / ".chroma")
    vector_store = get_vector_store(persist_path=persist_path)
    embed_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    query = "BaseNode implementation"
    print(f"Searching for: {query}")

    embeddings = list(embed_model.embed([query]))
    query_embedding = embeddings[0].tolist()

    results = await vector_store.search(
        query=query,
        collection="casare_codebase",
        top_k=3,
        query_embedding=query_embedding,
    )

    for i, res in enumerate(results):
        print(f"\nResult {i+1}: {res.metadata.get('path')} - {res.metadata.get('name')}")
        print(f"Score: {res.score:.3f}")
        print(f"Content: {res.content[:200]}...")


if __name__ == "__main__":
    asyncio.run(test_search())

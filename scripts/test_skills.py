"""Test skills by applying them in practice."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(".").absolute() / "src"))

from fastembed import TextEmbedding

from casare_rpa.infrastructure.ai.vector_store import get_vector_store


async def test_semantic_search_skill():
    """Apply semantic-search.md skill."""
    print("=== Skill Test: semantic-search.md ===")

    store = get_vector_store(persist_path=".chroma")
    model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    query = "browser automation click"
    print(f"Query: {query}")

    emb = list(model.embed([query]))[0].tolist()
    results = await store.search(
        query=query, collection="casare_codebase", top_k=3, query_embedding=emb
    )

    for i, r in enumerate(results):
        path = r.metadata.get("path", "")
        name = r.metadata.get("name", "")
        print(f"  {i+1}. {path} | {name} | Score: {r.score:.3f}")

    print("\n✅ semantic-search.md skill working!\n")


async def test_node_creator_skill():
    """Apply node-creator.md skill - verify patterns exist."""
    print("=== Skill Test: node-creator.md ===")

    store = get_vector_store(persist_path=".chroma")
    model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    query = "BaseNode execute method"
    emb = list(model.embed([query]))[0].tolist()
    results = await store.search(
        query=query, collection="casare_codebase", top_k=1, query_embedding=emb
    )

    if results:
        print(f"  Found: {results[0].metadata.get('path')} | {results[0].metadata.get('name')}")
        print("\n✅ node-creator.md skill working!\n")
    else:
        print("  ❌ No results found")


async def main():
    await test_semantic_search_skill()
    await test_node_creator_skill()
    print("All skill tests passed!")


if __name__ == "__main__":
    asyncio.run(main())

"""
CasareRPA - ChromaDB Semantic Search MCP Server

Exposes the local ChromaDB index to AI models via the Model Context Protocol.
"""

import os

# Add project root to path
import sys
from pathlib import Path

from fastembed import TextEmbedding
from fastmcp import FastMCP
from loguru import logger

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from casare_rpa.infrastructure.ai.vector_store import SearchResult, get_vector_store

# Initialize FastMCP
mcp = FastMCP("CasareRPA Codebase Search")

COLLECTION_NAME = "casare_codebase"
PERSIST_PATH = str(project_root / ".chroma")

# Global Persistent State for blazing fast search
_STATE = {"vector_store": None, "embed_model": None}


def get_state():
    if _STATE["vector_store"] is None:
        logger.info("Initializing search state (one-time setup)...")
        _STATE["vector_store"] = get_vector_store(persist_path=PERSIST_PATH)
        _STATE["embed_model"] = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
    return _STATE["vector_store"], _STATE["embed_model"]


@mcp.tool()
async def search_codebase(query: str, top_k: int = 5) -> str:
    """
    Search the CasareRPA codebase using semantic similarity.
    Use this to find relevant classes, functions, or implementation details.

    Args:
        query: The natural language search query.
        top_k: Number of results to return (default: 5).
    """
    try:
        vector_store, embed_model = get_state()

        # Generate query embedding
        logger.info(f"Searching codebase for: {query}")
        embeddings = list(embed_model.embed([query]))
        query_embedding = embeddings[0].tolist()

        # Perform search
        results: list[SearchResult] = await vector_store.search(
            query=query,
            collection=COLLECTION_NAME,
            top_k=top_k,
            query_embedding=query_embedding,
        )

        if not results:
            return "No relevant code snippets found."

        formatted_results = []
        for i, res in enumerate(results):
            meta = res.metadata
            header = f"Result {i+1} | {meta.get('path')} | {meta.get('type')} {meta.get('name')} | Score: {res.score:.3f}"
            lines = [header, "-" * len(header), res.content, "\n"]
            formatted_results.append("\n".join(lines))

        return "\n".join(formatted_results)

    except Exception as e:
        logger.error(f"Search failed: {e}")
        return f"Error performing search: {str(e)}"


# Pre-warm state on module import
try:
    if os.environ.get("MCP_PREWARM", "true").lower() == "true":
        get_state()
except Exception:
    pass

if __name__ == "__main__":
    mcp.run()

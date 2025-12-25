"""Enhanced ChromaDB RAG usage for efficient code search.

Provides semantic search utilities to replace full code loading.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings


class CodeRAGSystem:
    """Retrieval-Augmented Generation for code search.

    Uses vector embeddings to find relevant code snippets
    instead of loading entire files.

    Features:
    - Semantic search (find related code)
    - Hybrid search (semantic + keyword)
    - Top-K retrieval (only fetch what's needed)
    - Chunk-level retrieval (fine-grained results)
    """

    def __init__(
        self,
        collection_name: str = "casare_rpa_code",
        persist_directory: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """Initialize Code RAG system.

        Args:
            collection_name: ChromaDB collection name.
            persist_directory: Path to persist vector DB.
            embedding_model: Sentence transformer model for embeddings.
        """
        self.embedding_model = embedding_model

        if persist_directory:
            settings = Settings(anonymized_telemetry=False, allow_reset=True)
            self.client = chromadb.PersistentClient(path=persist_directory, settings=settings)
        else:
            self.client = chromadb.Client()

        try:
            self.collection = self.client.get_collection(collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name, metadata={"hnsw:space": "cosine"}
            )

    def index_file(self, file_path: str, chunk_size: int = 500) -> int:
        """Index a code file for semantic search.

        Args:
            file_path: Path to code file.
            chunk_size: Maximum characters per chunk.

        Returns:
            Number of chunks indexed.
        """
        path = Path(file_path)
        if not path.exists():
            return 0

        content = path.read_text(encoding="utf-8")
        chunks = self._chunk_code(content, chunk_size)

        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{path.name}:{i}"

            embedding = self._get_embedding(chunk)

            if not embedding:
                continue

            ids.append(chunk_id)
            embeddings.append(embedding)
            metadatas.append(
                {"file": str(path), "chunk_index": i, "language": self._detect_language(path)}
            )
            documents.append(chunk)

        if ids:
            self.collection.add(
                ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
            )

        return len(chunks)

    def _chunk_code(self, code: str, chunk_size: int) -> list[str]:
        """Chunk code into semantic units.

        Tries to break at logical boundaries:
        - Function/class definitions
        - Import statements
        - Empty lines

        Args:
            code: Code content.
            chunk_size: Maximum chunk size.

        Returns:
            List of code chunks.
        """
        import re

        lines = code.split("\n")
        chunks = []
        current_chunk = []

        for line in lines:
            current_chunk.append(line)

            chunk_text = "\n".join(current_chunk)

            if len(chunk_text) >= chunk_size:
                chunks.append(chunk_text)
                current_chunk = []

            elif re.match(r"^(def |class |import |from |$)", line):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _get_embedding(self, text: str) -> list[float]:
        """Get embedding for text.

        Args:
            text: Text to embed.

        Returns:
            Vector embedding.
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return []

        try:
            model = SentenceTransformer(self.embedding_model)
            return model.encode(text).tolist()
        except (RuntimeError, ValueError, AttributeError):
            return []

    def _detect_language(self, path: Path) -> str:
        """Detect programming language from file extension.

        Args:
            path: File path.

        Returns:
            Language name.
        """
        ext_map = {
            ".py": "python",
            ".ts": "typescript",
            ".js": "javascript",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
        }

        return ext_map.get(path.suffix, "unknown")

    def search(
        self, query: str, top_k: int = 5, filter_metadata: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Search code semantically.

        Args:
            query: Search query text.
            top_k: Number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of results with relevance scores.
        """
        query_embedding = self._get_embedding(query)

        if not query_embedding:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k, where=filter_metadata
        )

        formatted_results = []

        if results.get("ids") and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                formatted_results.append(
                    {
                        "id": doc_id,
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i] if "distances" in results else 0.0,
                    }
                )

        return formatted_results

    def hybrid_search(
        self, query: str, top_k: int = 5, semantic_weight: float = 0.7, keyword_weight: float = 0.3
    ) -> list[dict[str, Any]]:
        """Hybrid semantic + keyword search.

        Combines vector search with keyword matching.

        Args:
            query: Search query.
            top_k: Number of results.
            semantic_weight: Weight for semantic search (0-1).
            keyword_weight: Weight for keyword matching (0-1).

        Returns:
            Combined results.
        """
        semantic_results = self.search(query, top_k=top_k)

        keyword_results = self.collection.query(query_texts=[query], n_results=top_k)

        combined = {}

        for result in semantic_results:
            content_hash = hash(result["content"])
            if content_hash not in combined:
                combined[content_hash] = {
                    **result,
                    "semantic_score": 1.0 - result["score"],
                    "keyword_score": 0.0,
                }
            combined[content_hash]["semantic_score"] = min(
                combined[content_hash]["semantic_score"] * semantic_weight, 1.0
            )

        if keyword_results.get("ids") and keyword_results["ids"]:
            for i, doc_id in enumerate(keyword_results["ids"][0]):
                content = keyword_results["documents"][0][i]
                content_hash = hash(content)

                if content_hash not in combined:
                    combined[content_hash] = {
                        "id": doc_id,
                        "content": content,
                        "metadata": keyword_results["metadatas"][0][i],
                        "semantic_score": 0.0,
                        "keyword_score": 1.0,
                    }
                else:
                    combined[content_hash]["keyword_score"] = min(
                        combined[content_hash].get("keyword_score", 0.0) + keyword_weight, 1.0
                    )

        if keyword_results["ids"]:
            for i, doc_id in enumerate(keyword_results["ids"][0]):
                content = keyword_results["documents"][0][i]
                content_hash = hash(content)

                if content_hash not in combined:
                    combined[content_hash] = {
                        "id": doc_id,
                        "content": content,
                        "metadata": keyword_results["metadatas"][0][i],
                        "semantic_score": 0.0,
                        "keyword_score": 1.0,
                    }
                else:
                    combined[content_hash]["keyword_score"] = min(
                        combined[content_hash].get("keyword_score", 0.0) + keyword_weight, 1.0
                    )

        final_results = []

        for item in combined.values():
            total_score = (
                item["semantic_score"] * semantic_weight + item["keyword_score"] * keyword_weight
            )
            item["combined_score"] = total_score
            final_results.append(item)

        final_results.sort(key=lambda x: x["combined_score"], reverse=True)

        return final_results[:top_k]

    def get_context_for_query(self, query: str, max_context_tokens: int = 2000) -> str:
        """Get relevant code context for query.

        Args:
            query: Search query.
            max_context_tokens: Maximum tokens for context.

        Returns:
            Formatted context string.
        """
        results = self.search(query, top_k=5)

        context_parts = []
        current_tokens = 0

        for result in results:
            content = result["content"]
            file_path = result["metadata"].get("file", "unknown")
            chunk_idx = result["metadata"].get("chunk_index", 0)

            tokens = len(content) // 4

            if current_tokens + tokens > max_context_tokens:
                truncated = content[: (max_context_tokens - current_tokens) * 4]
                context_parts.append(f"// File: {file_path} (chunk {chunk_idx})\n{truncated}\n")
                break

            context_parts.append(f"// File: {file_path} (chunk {chunk_idx})\n{content}\n")
            current_tokens += tokens

        return "\n".join(context_parts)

    def index_directory(
        self, directory: str, pattern: str = "*.py", chunk_size: int = 500
    ) -> dict[str, int]:
        """Index all files in directory.

        Args:
            directory: Directory path.
            pattern: Glob pattern for files.
            chunk_size: Maximum chunk size.

        Returns:
            Dictionary of files and chunk counts.
        """
        base_path = Path(directory)
        results = {}

        for file_path in base_path.rglob(pattern):
            chunk_count = self.index_file(str(file_path), chunk_size)
            results[str(file_path)] = chunk_count

        return results

    def reset_collection(self) -> None:
        """Clear all indexed data."""
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.create_collection(
            name=self.collection.name, metadata={"hnsw:space": "cosine"}
        )

    def get_stats(self) -> dict[str, Any]:
        """Get collection statistics.

        Returns:
            Dictionary with stats.
        """
        return {
            "count": self.collection.count(),
            "name": self.collection.name,
            "metadata": self.collection.metadata,
        }


def rag_search_code(
    query: str, codebase_path: str, top_k: int = 5, persist_dir: Optional[str] = None
) -> list[dict[str, Any]]:
    """Convenience function for code search.

    Args:
        query: Search query.
        codebase_path: Path to codebase.
        top_k: Number of results.
        persist_dir: Optional persistence directory.

    Returns:
        Search results.
    """
    rag = CodeRAGSystem(persist_directory=persist_dir)

    stats = rag.get_stats()
    if stats.get("count", 0) == 0:
        rag.index_directory(codebase_path)

    return rag.search(query, top_k=top_k)

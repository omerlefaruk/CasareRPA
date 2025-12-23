"""
CasareRPA - Infrastructure: Vector Store

Persistent vector storage using ChromaDB for semantic search and RAG operations.
Supports lazy loading to avoid startup overhead.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    import chromadb
    from chromadb.api.models.Collection import Collection


@dataclass
class Document:
    """Document to store in vector database."""

    id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None  # Pre-computed embedding


@dataclass
class SearchResult:
    """Result from vector similarity search."""

    id: str
    content: str
    metadata: dict[str, Any]
    score: float  # Similarity score (higher = more similar)
    distance: float  # Distance (lower = more similar)


@dataclass
class VectorStoreMetrics:
    """Track vector store usage."""

    total_adds: int = 0
    total_searches: int = 0
    total_deletes: int = 0
    total_documents: int = 0
    last_operation_time: float | None = None

    def add_operation(self, operation: str, count: int = 1) -> None:
        """Record an operation."""
        if operation == "add":
            self.total_adds += count
            self.total_documents += count
        elif operation == "search":
            self.total_searches += 1
        elif operation == "delete":
            self.total_deletes += count
            self.total_documents = max(0, self.total_documents - count)
        self.last_operation_time = time.time()


class VectorStore:
    """
    Persistent vector storage using ChromaDB.

    Features:
    - Lazy loading of ChromaDB to minimize startup impact
    - Multiple collection support
    - Automatic embedding via embedding function or pre-computed
    - Metadata filtering
    - Persistence to disk
    """

    DEFAULT_COLLECTION = "default"

    def __init__(
        self,
        persist_path: str | None = None,
        embedding_function: Any | None = None,
    ) -> None:
        """
        Initialize vector store.

        Args:
            persist_path: Directory for persistent storage
            embedding_function: ChromaDB embedding function (optional)
        """
        self._persist_path = persist_path
        self._embedding_function = embedding_function
        self._client: chromadb.Client | None = None
        self._collections: dict[str, Collection] = {}
        self._metrics = VectorStoreMetrics()
        self._initialized = False

    def _ensure_initialized(self) -> chromadb.Client:
        """Lazy-load ChromaDB client."""
        if self._initialized and self._client is not None:
            return self._client

        try:
            import chromadb
            from chromadb.config import Settings

            if self._persist_path:
                # Ensure directory exists
                Path(self._persist_path).mkdir(parents=True, exist_ok=True)

                self._client = chromadb.PersistentClient(
                    path=self._persist_path,
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True,
                    ),
                )
                logger.debug(f"ChromaDB initialized: persist_path={self._persist_path}")
            else:
                # In-memory client for testing
                self._client = chromadb.Client(
                    Settings(
                        anonymized_telemetry=False,
                    )
                )
                logger.debug("ChromaDB initialized: in-memory mode")

            self._initialized = True
            return self._client

        except ImportError as e:
            raise ImportError(
                "ChromaDB is required for vector store. "
                "Install it with: pip install chromadb>=0.4.0"
            ) from e

    def _get_collection(
        self,
        collection_name: str,
        create: bool = True,
    ) -> Collection:
        """Get or create a collection."""
        if collection_name in self._collections:
            return self._collections[collection_name]

        client = self._ensure_initialized()

        try:
            if create:
                collection = client.get_or_create_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function,
                    metadata={"created_at": time.time()},
                )
            else:
                collection = client.get_collection(
                    name=collection_name,
                    embedding_function=self._embedding_function,
                )

            self._collections[collection_name] = collection
            return collection

        except Exception as e:
            logger.error(f"Failed to get collection '{collection_name}': {e}")
            raise

    async def add_documents(
        self,
        documents: list[Document],
        collection: str = DEFAULT_COLLECTION,
    ) -> int:
        """
        Add documents to a collection.

        Args:
            documents: List of documents to add
            collection: Collection name

        Returns:
            Number of documents added
        """
        if not documents:
            return 0

        coll = self._get_collection(collection)

        ids = []
        contents = []
        metadatas = []
        embeddings = []
        has_embeddings = False

        for doc in documents:
            ids.append(doc.id)
            contents.append(doc.content)
            metadatas.append(doc.metadata or {})
            if doc.embedding:
                embeddings.append(doc.embedding)
                has_embeddings = True

        try:
            if has_embeddings and len(embeddings) == len(documents):
                coll.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
            else:
                coll.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas,
                )

            self._metrics.add_operation("add", len(documents))
            logger.debug(f"Added {len(documents)} documents to collection '{collection}'")
            return len(documents)

        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise

    async def add_document(
        self,
        document: Document,
        collection: str = DEFAULT_COLLECTION,
    ) -> bool:
        """Add a single document."""
        count = await self.add_documents([document], collection)
        return count == 1

    async def search(
        self,
        query: str,
        collection: str = DEFAULT_COLLECTION,
        top_k: int = 5,
        where: dict[str, Any] | None = None,
        where_document: dict[str, Any] | None = None,
        query_embedding: list[float] | None = None,
    ) -> list[SearchResult]:
        """
        Semantic search in a collection.

        Args:
            query: Search query text
            collection: Collection to search
            top_k: Number of results to return
            where: Metadata filter (ChromaDB where clause)
            where_document: Document content filter
            query_embedding: Pre-computed embedding for query

        Returns:
            List of SearchResult ordered by relevance
        """
        coll = self._get_collection(collection, create=False)

        try:
            kwargs: dict[str, Any] = {
                "n_results": top_k,
                "include": ["documents", "metadatas", "distances"],
            }

            if query_embedding:
                kwargs["query_embeddings"] = [query_embedding]
            else:
                kwargs["query_texts"] = [query]

            if where:
                kwargs["where"] = where
            if where_document:
                kwargs["where_document"] = where_document

            results = coll.query(**kwargs)

            self._metrics.add_operation("search")

            # Convert to SearchResult objects
            search_results = []
            if results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]

                for i, doc_id in enumerate(ids):
                    # Convert distance to similarity score (1 - normalized distance)
                    distance = distances[i] if i < len(distances) else 0.0
                    score = max(0.0, 1.0 - (distance / 2.0))  # Normalize

                    search_results.append(
                        SearchResult(
                            id=doc_id,
                            content=documents[i] if i < len(documents) else "",
                            metadata=metadatas[i] if i < len(metadatas) else {},
                            score=score,
                            distance=distance,
                        )
                    )

            logger.debug(
                f"Search in '{collection}': query='{query[:50]}...', "
                f"results={len(search_results)}"
            )
            return search_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    async def delete_documents(
        self,
        ids: list[str],
        collection: str = DEFAULT_COLLECTION,
    ) -> int:
        """
        Delete documents by ID.

        Args:
            ids: List of document IDs to delete
            collection: Collection name

        Returns:
            Number of documents deleted
        """
        if not ids:
            return 0

        coll = self._get_collection(collection, create=False)

        try:
            coll.delete(ids=ids)
            self._metrics.add_operation("delete", len(ids))
            logger.debug(f"Deleted {len(ids)} documents from '{collection}'")
            return len(ids)

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise

    async def delete_collection(self, collection: str) -> bool:
        """Delete an entire collection."""
        client = self._ensure_initialized()

        try:
            client.delete_collection(name=collection)
            if collection in self._collections:
                del self._collections[collection]
            logger.debug(f"Deleted collection '{collection}'")
            return True

        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            return False

    async def get_document(
        self,
        doc_id: str,
        collection: str = DEFAULT_COLLECTION,
    ) -> Document | None:
        """Get a document by ID."""
        coll = self._get_collection(collection, create=False)

        try:
            results = coll.get(
                ids=[doc_id],
                include=["documents", "metadatas", "embeddings"],
            )

            if results["ids"]:
                return Document(
                    id=results["ids"][0],
                    content=results["documents"][0] if results.get("documents") else "",
                    metadata=(results["metadatas"][0] if results.get("metadatas") else {}),
                    embedding=(results["embeddings"][0] if results.get("embeddings") else None),
                )
            return None

        except Exception as e:
            logger.error(f"Get document failed: {e}")
            raise

    async def count_documents(self, collection: str = DEFAULT_COLLECTION) -> int:
        """Get document count in a collection."""
        coll = self._get_collection(collection, create=False)
        return coll.count()

    async def list_collections(self) -> list[str]:
        """List all collection names."""
        client = self._ensure_initialized()
        collections = client.list_collections()
        return [c.name for c in collections]

    async def collection_exists(self, collection: str) -> bool:
        """Check if a collection exists."""
        collections = await self.list_collections()
        return collection in collections

    async def update_document(
        self,
        document: Document,
        collection: str = DEFAULT_COLLECTION,
    ) -> bool:
        """Update an existing document."""
        coll = self._get_collection(collection, create=False)

        try:
            kwargs: dict[str, Any] = {
                "ids": [document.id],
                "documents": [document.content],
                "metadatas": [document.metadata],
            }
            if document.embedding:
                kwargs["embeddings"] = [document.embedding]

            coll.update(**kwargs)
            logger.debug(f"Updated document '{document.id}' in '{collection}'")
            return True

        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False

    def reset(self) -> bool:
        """Reset the vector store (delete all data)."""
        client = self._ensure_initialized()

        try:
            client.reset()
            self._collections.clear()
            self._metrics = VectorStoreMetrics()
            logger.warning("Vector store reset - all data deleted")
            return True

        except Exception as e:
            logger.error(f"Reset failed: {e}")
            return False

    @property
    def metrics(self) -> VectorStoreMetrics:
        """Get usage metrics."""
        return self._metrics

    @property
    def persist_path(self) -> str | None:
        """Get persistence path."""
        return self._persist_path

    @property
    def is_persistent(self) -> bool:
        """Check if store is persistent."""
        return self._persist_path is not None

    def __repr__(self) -> str:
        """String representation."""
        mode = "persistent" if self._persist_path else "in-memory"
        return (
            f"VectorStore(mode={mode}, "
            f"collections={len(self._collections)}, "
            f"total_docs={self._metrics.total_documents})"
        )


# Default store path
def get_default_persist_path() -> str:
    """Get default persistence path for vector store."""
    from pathlib import Path

    return str(Path.home() / ".casare_rpa" / "vector_store")


# Module-level singleton
_default_store: VectorStore | None = None


def get_vector_store(persist_path: str | None = None) -> VectorStore:
    """Get or create the default vector store."""
    global _default_store
    if _default_store is None:
        path = persist_path or get_default_persist_path()
        _default_store = VectorStore(persist_path=path)
    return _default_store


__all__ = [
    "VectorStore",
    "Document",
    "SearchResult",
    "VectorStoreMetrics",
    "get_vector_store",
    "get_default_persist_path",
]

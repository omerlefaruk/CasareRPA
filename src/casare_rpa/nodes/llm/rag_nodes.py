"""
CasareRPA - RAG Nodes

Nodes for Retrieval-Augmented Generation operations:
- EmbeddingNode: Generate text embeddings
- VectorStoreAddNode: Add documents to vector store
- VectorSearchNode: Semantic search
- RAGNode: Full RAG pipeline (retrieve + generate)
"""

from __future__ import annotations

import json
from typing import Any

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.llm.llm_base import LLMBaseNode


@properties(
    PropertyDef(
        "text",
        PropertyType.TEXT,
        default="",
        label="Text",
        placeholder="Text to embed...",
        tooltip="Text to convert to embeddings",
        essential=True,
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="text-embedding-3-small",
        label="Model",
        tooltip="Embedding model to use",
    ),
)
@node(category="llm")
class EmbeddingNode(LLMBaseNode):
    """
    Generate embeddings for text using LLM embedding models.

    Converts text to vector representation for semantic operations.
    """

    NODE_NAME = "Embedding"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Generate text embeddings for semantic operations"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("text", DataType.STRING)
        self.add_input_port("model", DataType.STRING, required=False)
        self.add_input_port("api_key", DataType.STRING, required=False)

        # Outputs
        self.add_output_port("embedding", DataType.LIST)
        self.add_output_port("dimensions", DataType.INTEGER)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute embedding generation."""
        from casare_rpa.infrastructure.ai.embedding_manager import (
            EmbeddingConfig,
            EmbeddingManager,
        )

        text = self.get_parameter("text")

        if not text:
            self.set_output_value("success", False)
            self.set_output_value("error", "Text is required")
            self.set_output_value("embedding", [])
            return {"success": False, "error": "Text is required", "next_nodes": []}

        model = self.get_parameter("model") or "text-embedding-3-small"
        api_key = self.get_parameter("api_key")

        try:
            # Create embedding manager
            config = EmbeddingConfig(model=model, api_key=api_key)
            embed_manager = EmbeddingManager(config)

            result = await embed_manager.embed_text(text, model=model)

            self.set_output_value("embedding", result.embedding)
            self.set_output_value("dimensions", len(result.embedding))
            self.set_output_value("tokens_used", result.tokens_used)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(
                f"Embedding generated: dims={len(result.embedding)}, "
                f"tokens={result.tokens_used}"
            )

            return {
                "success": True,
                "data": {
                    "embedding": result.embedding,
                    "dimensions": len(result.embedding),
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("embedding", [])
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "documents",
        PropertyType.LIST,
        required=True,
        label="Documents",
        tooltip="List of documents to add to vector store",
    ),
    PropertyDef(
        "collection",
        PropertyType.STRING,
        default="default",
        label="Collection",
        placeholder="my_collection",
        tooltip="Vector store collection name",
    ),
)
@node(category="llm")
class VectorStoreAddNode(LLMBaseNode):
    """
    Add documents to a vector store collection.

    Supports adding single or multiple documents with metadata.
    """

    NODE_NAME = "Vector Store Add"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Add documents to vector store for semantic search"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("documents", DataType.LIST)
        self.add_input_port("collection", DataType.STRING, required=False)
        self.add_input_port("embeddings", DataType.LIST, required=False)

        # Outputs
        self.add_output_port("count", DataType.INTEGER)
        self.add_output_port("collection_name", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute document addition to vector store."""
        from casare_rpa.infrastructure.ai.vector_store import (
            Document,
            get_vector_store,
        )

        documents = self.get_parameter("documents")
        collection = self.get_parameter("collection") or "default"
        embeddings = self.get_parameter("embeddings")

        if not documents:
            self.set_output_value("success", False)
            self.set_output_value("error", "Documents are required")
            self.set_output_value("count", 0)
            return {
                "success": False,
                "error": "Documents are required",
                "next_nodes": [],
            }

        # Parse documents if string
        if isinstance(documents, str):
            try:
                documents = json.loads(documents)
            except json.JSONDecodeError:
                documents = [{"id": "doc1", "content": documents}]

        # Normalize document format
        docs_to_add: list[Document] = []
        for i, doc in enumerate(documents):
            if isinstance(doc, str):
                doc = {"id": f"doc_{i}", "content": doc}

            doc_id = doc.get("id", f"doc_{i}")
            content = doc.get("content", doc.get("text", str(doc)))
            metadata = doc.get("metadata", {})

            embedding = None
            if embeddings and i < len(embeddings):
                embedding = embeddings[i]

            docs_to_add.append(
                Document(
                    id=doc_id,
                    content=content,
                    metadata=metadata,
                    embedding=embedding,
                )
            )

        try:
            store = get_vector_store()
            count = await store.add_documents(docs_to_add, collection=collection)

            self.set_output_value("count", count)
            self.set_output_value("collection_name", collection)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Added {count} documents to collection '{collection}'")

            return {
                "success": True,
                "data": {"count": count, "collection": collection},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("count", 0)
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "query",
        PropertyType.TEXT,
        default="",
        label="Query",
        placeholder="Search query...",
        tooltip="Semantic search query",
        essential=True,
    ),
    PropertyDef(
        "collection",
        PropertyType.STRING,
        default="default",
        label="Collection",
        tooltip="Vector store collection to search",
    ),
    PropertyDef(
        "top_k",
        PropertyType.INTEGER,
        default=5,
        min_value=1,
        max_value=100,
        label="Top K",
        tooltip="Number of results to return",
    ),
)
@node(category="llm")
class VectorSearchNode(LLMBaseNode):
    """
    Perform semantic search in a vector store.

    Returns the most similar documents to the query.
    """

    NODE_NAME = "Vector Search"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Semantic search in vector store"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("query", DataType.STRING)
        self.add_input_port("collection", DataType.STRING, required=False)
        self.add_input_port("top_k", DataType.INTEGER, required=False)
        self.add_input_port("filter", DataType.DICT, required=False)
        self.add_input_port("query_embedding", DataType.LIST, required=False)

        # Outputs
        self.add_output_port("results", DataType.LIST)
        self.add_output_port("top_result", DataType.DICT)
        self.add_output_port("result_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute vector search."""
        from casare_rpa.infrastructure.ai.vector_store import get_vector_store

        query = self.get_parameter("query")

        if not query:
            self.set_output_value("success", False)
            self.set_output_value("error", "Query is required")
            self.set_output_value("results", [])
            return {"success": False, "error": "Query is required", "next_nodes": []}

        collection = self.get_parameter("collection") or "default"
        top_k = self.get_parameter("top_k") or 5
        filter_dict = self.get_parameter("filter")
        query_embedding = self.get_parameter("query_embedding")

        try:
            store = get_vector_store()

            results = await store.search(
                query=query,
                collection=collection,
                top_k=int(top_k),
                where=filter_dict,
                query_embedding=query_embedding,
            )

            # Convert to serializable format
            results_list = [
                {
                    "id": r.id,
                    "content": r.content,
                    "metadata": r.metadata,
                    "score": r.score,
                    "distance": r.distance,
                }
                for r in results
            ]

            top_result = results_list[0] if results_list else {}

            self.set_output_value("results", results_list)
            self.set_output_value("top_result", top_result)
            self.set_output_value("result_count", len(results_list))
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Vector search: query='{query[:30]}...', " f"results={len(results_list)}")

            return {
                "success": True,
                "data": {"results": results_list, "count": len(results_list)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("results", [])
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "question",
        PropertyType.TEXT,
        default="",
        label="Question",
        placeholder="Ask a question...",
        tooltip="Question to answer using RAG",
        essential=True,
    ),
    PropertyDef(
        "collection",
        PropertyType.STRING,
        default="default",
        label="Collection",
        tooltip="Vector store collection for context",
    ),
    PropertyDef(
        "top_k",
        PropertyType.INTEGER,
        default=3,
        min_value=1,
        max_value=20,
        label="Context Documents",
        tooltip="Number of context documents to retrieve",
    ),
    PropertyDef(
        "model",
        PropertyType.STRING,
        default="gpt-4o-mini",
        label="Model",
        tooltip="LLM model for generation",
    ),
    PropertyDef(
        "temperature",
        PropertyType.FLOAT,
        default=0.7,
        min_value=0.0,
        max_value=2.0,
        label="Temperature",
        tooltip="Creativity/randomness (0-2)",
    ),
    PropertyDef(
        "max_tokens",
        PropertyType.INTEGER,
        default=1000,
        min_value=1,
        label="Max Tokens",
        tooltip="Maximum response length",
    ),
)
@node(category="llm")
class RAGNode(LLMBaseNode):
    """
    Full RAG (Retrieval-Augmented Generation) pipeline.

    Retrieves relevant context from vector store and generates response.
    """

    NODE_NAME = "RAG"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Retrieval-Augmented Generation: search context then generate"

    DEFAULT_RAG_TEMPLATE = """Use the following context to answer the question. If the context doesn't contain relevant information, say so.

Context:
{context}

Question: {question}

Answer:"""

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("question", DataType.STRING)
        self.add_input_port("collection", DataType.STRING, required=False)
        self.add_input_port("top_k", DataType.INTEGER, required=False)
        self.add_input_port("prompt_template", DataType.STRING, required=False)
        self._define_common_input_ports()

        # Outputs
        self.add_output_port("answer", DataType.STRING)
        self.add_output_port("context", DataType.STRING)
        self.add_output_port("sources", DataType.LIST)
        self.add_output_port("tokens_used", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute RAG pipeline."""
        from casare_rpa.infrastructure.ai.vector_store import get_vector_store

        question = self.get_parameter("question")

        if not question:
            self.set_output_value("success", False)
            self.set_output_value("error", "Question is required")
            return {"success": False, "error": "Question is required", "next_nodes": []}

        collection = self.get_parameter("collection") or "default"
        top_k = self.get_parameter("top_k") or 3
        prompt_template = self.get_parameter("prompt_template") or self.DEFAULT_RAG_TEMPLATE

        model = self.get_parameter("model") or self.DEFAULT_MODEL
        temperature = self.get_parameter("temperature") or 0.7
        max_tokens = self.get_parameter("max_tokens") or 1000
        system_prompt = self.get_parameter("system_prompt")

        try:
            # Step 1: Retrieve relevant documents
            store = get_vector_store()
            search_results = await store.search(
                query=question,
                collection=collection,
                top_k=int(top_k),
            )

            # Build context from retrieved documents
            context_parts = []
            sources = []
            for i, result in enumerate(search_results):
                context_parts.append(f"[{i+1}] {result.content}")
                sources.append(
                    {
                        "id": result.id,
                        "content": result.content[:200] + "..."
                        if len(result.content) > 200
                        else result.content,
                        "score": result.score,
                        "metadata": result.metadata,
                    }
                )

            context_text = (
                "\n\n".join(context_parts) if context_parts else "No relevant context found."
            )

            # Step 2: Build prompt with context
            final_prompt = prompt_template.format(
                context=context_text,
                question=question,
            )

            # Step 3: Generate response
            llm_manager = await self._get_llm_manager(context)

            response = await llm_manager.completion(
                prompt=final_prompt,
                model=model,
                system_prompt=system_prompt
                or "You are a helpful assistant that answers questions based on the provided context.",
                temperature=float(temperature),
                max_tokens=int(max_tokens),
            )

            self.set_output_value("answer", response.content)
            self.set_output_value("context", context_text)
            self.set_output_value("sources", sources)
            self.set_output_value("tokens_used", response.total_tokens)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(
                f"RAG: question='{question[:30]}...', "
                f"sources={len(sources)}, tokens={response.total_tokens}"
            )

            return {
                "success": True,
                "data": {
                    "answer": response.content,
                    "sources": sources,
                    "context_length": len(context_text),
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("answer", "")
            return {"success": False, "error": error_msg, "next_nodes": []}


@properties(
    PropertyDef(
        "document_ids",
        PropertyType.LIST,
        required=True,
        label="Document IDs",
        tooltip="List of document IDs to delete",
    ),
    PropertyDef(
        "collection",
        PropertyType.STRING,
        default="default",
        label="Collection",
        tooltip="Vector store collection to delete from",
    ),
)
@node(category="llm")
class VectorStoreDeleteNode(LLMBaseNode):
    """
    Delete documents from a vector store collection.
    """

    NODE_NAME = "Vector Store Delete"
    NODE_CATEGORY = "AI/ML"
    NODE_DESCRIPTION = "Delete documents from vector store"

    def __init__(self, node_id: str, **kwargs: Any) -> None:
        super().__init__(node_id, name=self.NODE_NAME, **kwargs)
        self._define_ports()

    def _define_ports(self) -> None:
        """Define node ports."""
        # Inputs
        self.add_input_port("document_ids", DataType.LIST)
        self.add_input_port("collection", DataType.STRING, required=False)

        # Outputs
        self.add_output_port("deleted_count", DataType.INTEGER)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("error", DataType.STRING)

    async def _execute_llm(
        self,
        context: ExecutionContext,
        manager: Any,
    ) -> ExecutionResult:
        """Execute document deletion."""
        from casare_rpa.infrastructure.ai.vector_store import get_vector_store

        document_ids = self.get_parameter("document_ids")
        collection = self.get_parameter("collection") or "default"

        if not document_ids:
            self.set_output_value("success", False)
            self.set_output_value("error", "Document IDs are required")
            self.set_output_value("deleted_count", 0)
            return {
                "success": False,
                "error": "Document IDs required",
                "next_nodes": [],
            }

        # Normalize IDs
        if isinstance(document_ids, str):
            document_ids = [document_ids]

        try:
            store = get_vector_store()
            count = await store.delete_documents(document_ids, collection=collection)

            self.set_output_value("deleted_count", count)
            self.set_output_value("success", True)
            self.set_output_value("error", "")

            logger.info(f"Deleted {count} documents from '{collection}'")

            return {
                "success": True,
                "data": {"deleted_count": count},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            error_msg = str(e)
            self.set_output_value("success", False)
            self.set_output_value("error", error_msg)
            self.set_output_value("deleted_count", 0)
            return {"success": False, "error": error_msg, "next_nodes": []}


__all__ = [
    "EmbeddingNode",
    "VectorStoreAddNode",
    "VectorSearchNode",
    "RAGNode",
    "VectorStoreDeleteNode",
]

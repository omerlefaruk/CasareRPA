"""
CasareRPA - RAG System Test Script

Tests the complete RAG pipeline:
1. EmbeddingManager - Generate text embeddings
2. VectorStore - Store and search documents
3. Full RAG pipeline - Retrieve context + generate answer

Prerequisites:
- Add OPENAI_API_KEY to your .env file
- chromadb>=0.4.0 installed
- litellm>=1.50.0 installed

Usage:
    python scripts/test_rag_system.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv

load_dotenv(project_root / ".env")


async def test_embedding_manager():
    """Test the EmbeddingManager for generating embeddings."""
    print("\n" + "=" * 60)
    print("  TEST 1: EmbeddingManager")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.embedding_manager import (
        EmbeddingManager,
        EmbeddingConfig,
    )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found in environment!")
        print("Add to your .env file: OPENAI_API_KEY=sk-...")
        return False

    # Create config with your API key
    config = EmbeddingConfig(
        model="text-embedding-3-small",
        api_key=api_key,
        enable_cache=True,
    )

    manager = EmbeddingManager(config)

    # Test single embedding
    print("\n[1.1] Testing single text embedding...")
    test_text = "CasareRPA is a visual RPA platform for workflow automation"

    try:
        result = await manager.embed_text(test_text)
        print("  [OK] Embedding generated!")
        print(f"       Model: {result.model}")
        print(f"       Dimensions: {len(result.embedding)}")
        print(f"       Tokens used: {result.tokens_used}")
        print(f"       First 5 values: {result.embedding[:5]}")
    except Exception as e:
        print(f"  [FAILED] {e}")
        return False

    # Test batch embedding
    print("\n[1.2] Testing batch embedding...")
    texts = [
        "Browser automation with Playwright",
        "Desktop automation with Windows UI",
        "File operations and data processing",
    ]

    try:
        batch_result = await manager.embed_batch(texts)
        print("  [OK] Batch embeddings generated!")
        print(f"       Count: {batch_result.count}")
        print(f"       Total tokens: {batch_result.total_tokens}")
    except Exception as e:
        print(f"  [FAILED] {e}")
        return False

    # Test cache
    print("\n[1.3] Testing embedding cache...")
    cached_result = await manager.embed_text(test_text)
    print(f"  [OK] Cached: {cached_result.cached}")
    print(f"       Cache size: {manager.cache_size}")

    # Print metrics
    print("\n[1.4] Manager metrics:")
    print(f"       Total requests: {manager.metrics.total_requests}")
    print(f"       Total tokens: {manager.metrics.total_tokens}")
    print(f"       Cache hits: {manager.metrics.cache_hits}")

    return True


async def test_vector_store():
    """Test the VectorStore for document storage and search."""
    print("\n" + "=" * 60)
    print("  TEST 2: VectorStore (ChromaDB)")
    print("=" * 60)

    from casare_rpa.infrastructure.ai.vector_store import (
        VectorStore,
        Document,
    )

    # Use in-memory store for testing
    store = VectorStore(persist_path=None)  # In-memory mode

    # Sample documents about CasareRPA
    documents = [
        Document(
            id="doc_1",
            content="CasareRPA is a visual RPA platform built with Python and PySide6. It features a node-based workflow editor where users can drag and drop nodes to create automation workflows.",
            metadata={"category": "overview", "version": "2.0"},
        ),
        Document(
            id="doc_2",
            content="Browser automation in CasareRPA uses Playwright for reliable web interactions. You can navigate pages, click elements, fill forms, and extract data from websites.",
            metadata={"category": "browser", "version": "2.0"},
        ),
        Document(
            id="doc_3",
            content="Desktop automation supports Windows applications through UI Automation. You can launch applications, send keystrokes, click buttons, and interact with native Windows controls.",
            metadata={"category": "desktop", "version": "2.0"},
        ),
        Document(
            id="doc_4",
            content="The RAG system in CasareRPA uses ChromaDB for vector storage and LiteLLM for embeddings. It supports semantic search and retrieval-augmented generation.",
            metadata={"category": "ai", "version": "2.0"},
        ),
        Document(
            id="doc_5",
            content="Workflow execution is orchestrated by the ExecutionOrchestrator which manages node execution order, handles errors, and tracks execution state.",
            metadata={"category": "execution", "version": "2.0"},
        ),
    ]

    # Add documents
    print("\n[2.1] Adding documents to vector store...")
    try:
        count = await store.add_documents(documents, collection="casare_docs")
        print(f"  [OK] Added {count} documents to 'casare_docs' collection")
    except Exception as e:
        print(f"  [FAILED] {e}")
        return False

    # Search documents
    print("\n[2.2] Testing semantic search...")
    queries = [
        "How do I automate web browsers?",
        "What is the architecture of CasareRPA?",
        "How does the AI system work?",
    ]

    for query in queries:
        print(f"\n  Query: '{query}'")
        try:
            results = await store.search(
                query=query,
                collection="casare_docs",
                top_k=2,
            )
            for i, r in enumerate(results):
                print(f"    [{i+1}] Score: {r.score:.3f} | {r.content[:60]}...")
        except Exception as e:
            print(f"    [FAILED] {e}")
            return False

    # Test metadata filtering
    print("\n[2.3] Testing metadata filter...")
    try:
        results = await store.search(
            query="automation",
            collection="casare_docs",
            top_k=3,
            where={"category": "browser"},
        )
        print(f"  [OK] Found {len(results)} results with category='browser'")
        for r in results:
            print(f"       - {r.content[:50]}...")
    except Exception as e:
        print(f"  [FAILED] {e}")

    # Count documents
    print("\n[2.4] Collection stats:")
    count = await store.count_documents("casare_docs")
    print(f"  Documents in collection: {count}")
    print(f"  Store metrics: {store.metrics}")

    return True


async def test_full_rag_pipeline():
    """Test the complete RAG pipeline with retrieval and generation."""
    print("\n" + "=" * 60)
    print("  TEST 3: Full RAG Pipeline")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found!")
        return False

    from casare_rpa.infrastructure.ai.vector_store import (
        VectorStore,
        Document,
    )
    from casare_rpa.infrastructure.ai.embedding_manager import (
        EmbeddingManager,
        EmbeddingConfig,
    )

    # Setup embedding manager
    embed_config = EmbeddingConfig(
        model="text-embedding-3-small",
        api_key=api_key,
    )
    embed_manager = EmbeddingManager(embed_config)

    # Setup vector store (in-memory for test)
    store = VectorStore(persist_path=None)

    # Add knowledge base documents
    print("\n[3.1] Building knowledge base...")
    knowledge_docs = [
        Document(
            id="kb_1",
            content="""To create a browser automation workflow in CasareRPA:
1. Add a LaunchBrowserNode to open Chrome or Firefox
2. Use NavigateNode to go to a URL
3. Add ClickNode or TypeNode to interact with elements
4. Use ExtractDataNode to scrape information
5. Connect nodes with execution flow connections""",
            metadata={"topic": "browser_guide"},
        ),
        Document(
            id="kb_2",
            content="""Error handling in CasareRPA workflows:
- Use TryCatchNode to wrap risky operations
- Add RetryNode for transient failures
- Use ConditionalNode to check success/failure
- Log errors with LogNode for debugging
- Set workflow-level error policies in settings""",
            metadata={"topic": "error_handling"},
        ),
        Document(
            id="kb_3",
            content="""Variables in CasareRPA workflows:
- Create variables in the Variables panel
- Use SetVariableNode to assign values
- Reference variables with ${variable_name} syntax
- Variables can be strings, numbers, lists, or objects
- Scope can be workflow-level or node-level""",
            metadata={"topic": "variables"},
        ),
    ]

    # Generate embeddings and add documents
    for doc in knowledge_docs:
        embed_result = await embed_manager.embed_text(doc.content)
        doc.embedding = embed_result.embedding

    await store.add_documents(knowledge_docs, collection="knowledge_base")
    print(f"  [OK] Added {len(knowledge_docs)} documents with embeddings")

    # Test RAG query
    print("\n[3.2] Testing RAG query...")
    question = "How do I handle errors in my automation workflow?"

    # Step 1: Generate query embedding
    query_embed = await embed_manager.embed_text(question)

    # Step 2: Search for relevant context
    results = await store.search(
        query=question,
        collection="knowledge_base",
        top_k=2,
        query_embedding=query_embed.embedding,
    )

    print(f"  Query: '{question}'")
    print(f"  Found {len(results)} relevant documents:")

    # Build context
    context_parts = []
    for i, r in enumerate(results):
        print(f"    [{i+1}] Score: {r.score:.3f}")
        context_parts.append(f"[{i+1}] {r.content}")

    context = "\n\n".join(context_parts)

    # Step 3: Generate response using LiteLLM
    print("\n[3.3] Generating answer with LLM...")
    try:
        import litellm

        prompt = f"""Use the following context to answer the question. Be concise and helpful.

Context:
{context}

Question: {question}

Answer:"""

        response = await litellm.acompletion(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant for CasareRPA, an RPA automation platform.",
                },
                {"role": "user", "content": prompt},
            ],
            api_key=api_key,
            max_tokens=500,
            temperature=0.7,
        )

        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens

        print(f"\n  [OK] Answer generated ({tokens} tokens):")
        print("-" * 40)
        print(answer)
        print("-" * 40)

    except Exception as e:
        print(f"  [FAILED] LLM generation error: {e}")
        return False

    return True


async def test_rag_nodes():
    """Test the RAG nodes directly."""
    print("\n" + "=" * 60)
    print("  TEST 4: RAG Node Classes")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not found!")
        return False

    from casare_rpa.nodes.llm.rag_nodes import (
        EmbeddingNode,
        VectorStoreAddNode,
        VectorSearchNode,
    )
    from casare_rpa.infrastructure.execution import ExecutionContext

    # Test EmbeddingNode
    print("\n[4.1] Testing EmbeddingNode...")
    embed_node = EmbeddingNode("test_embed")
    embed_node.set_parameter("text", "Test embedding for CasareRPA automation")
    embed_node.set_parameter("api_key", api_key)
    embed_node.set_parameter("model", "text-embedding-3-small")

    # Create minimal execution context
    class MinimalContext:
        def resolve_value(self, v):
            return v

    context = MinimalContext()

    try:
        result = await embed_node._execute_llm(context, None)
        print(f"  [OK] EmbeddingNode executed: success={result.get('success')}")
        dims = embed_node.get_output_value("dimensions")
        print(f"       Dimensions: {dims}")
    except Exception as e:
        print(f"  [FAILED] {e}")
        return False

    print("\n[4.2] RAG nodes verified!")
    return True


async def interactive_rag_demo():
    """Interactive demo where you can ask questions."""
    print("\n" + "=" * 60)
    print("  INTERACTIVE RAG DEMO")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY required for interactive demo")
        return

    from casare_rpa.infrastructure.ai.vector_store import VectorStore, Document
    from casare_rpa.infrastructure.ai.embedding_manager import (
        EmbeddingManager,
        EmbeddingConfig,
    )
    import litellm

    # Setup
    embed_manager = EmbeddingManager(
        EmbeddingConfig(
            model="text-embedding-3-small",
            api_key=api_key,
        )
    )
    store = VectorStore(persist_path=None)

    # Add sample knowledge
    docs = [
        Document(
            id="d1",
            content="CasareRPA supports browser automation using Playwright for Chrome, Firefox, and Edge.",
        ),
        Document(
            id="d2",
            content="Desktop automation uses Windows UI Automation to control native applications.",
        ),
        Document(
            id="d3",
            content="Workflows are created visually by connecting nodes in the canvas editor.",
        ),
        Document(
            id="d4",
            content="The orchestrator manages robot agents and schedules workflow executions.",
        ),
        Document(
            id="d5",
            content="Variables can store data between nodes using the Variables panel.",
        ),
    ]

    for doc in docs:
        embed = await embed_manager.embed_text(doc.content)
        doc.embedding = embed.embedding

    await store.add_documents(docs, collection="demo")
    print(f"Loaded {len(docs)} documents into RAG system.\n")

    print("Ask questions about CasareRPA (type 'quit' to exit):")
    print("-" * 40)

    while True:
        try:
            question = input("\nYou: ").strip()
            if question.lower() in ("quit", "exit", "q"):
                break
            if not question:
                continue

            # Search
            query_embed = await embed_manager.embed_text(question)
            results = await store.search(
                query=question,
                collection="demo",
                top_k=2,
                query_embedding=query_embed.embedding,
            )

            context = "\n".join([f"- {r.content}" for r in results])

            # Generate
            response = await litellm.acompletion(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Answer based on the context. Be brief.",
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {question}",
                    },
                ],
                api_key=api_key,
                max_tokens=200,
            )

            print(f"\nAssistant: {response.choices[0].message.content}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\nDemo ended.")


async def main():
    """Run all RAG tests."""
    print("\n" + "=" * 60)
    print("  CasareRPA RAG System Tests")
    print("=" * 60)

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[WARNING] OPENAI_API_KEY not found in .env file!")
        print("\nTo test the RAG system, add this line to your .env file:")
        print("  OPENAI_API_KEY=sk-your-api-key-here")
        print("\nYou can get an API key from: https://platform.openai.com/api-keys")
        return

    print(f"\n[OK] Found OPENAI_API_KEY: {api_key[:8]}...{api_key[-4:]}")

    results = []

    # Run tests
    results.append(("EmbeddingManager", await test_embedding_manager()))
    results.append(("VectorStore", await test_vector_store()))
    results.append(("Full RAG Pipeline", await test_full_rag_pipeline()))
    results.append(("RAG Nodes", await test_rag_nodes()))

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n[SUCCESS] All RAG tests passed!")
        print("\nWould you like to try the interactive demo? (y/n): ", end="")
        try:
            if input().strip().lower() == "y":
                await interactive_rag_demo()
        except (KeyboardInterrupt, EOFError):
            pass
    else:
        print("\n[WARNING] Some tests failed. Check the output above.")


if __name__ == "__main__":
    asyncio.run(main())

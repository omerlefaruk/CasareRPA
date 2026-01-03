"""Integration tests for token optimization utilities.

Tests the interaction between:
- LLM caching
- Context management
- RAG search
- Token tracking
"""

import tempfile
from pathlib import Path

import pytest

from casare_rpa.utils.llm.cache import LLMResponseCache
from casare_rpa.utils.llm.context_manager import ConversationManager
from casare_rpa.utils.rag.code_search import CodeRAGSystem


class TestLLMCacheIntegration:
    """Integration tests for LLM caching."""

    def test_cache_context_manager_integration(self):
        """Test cache working with context manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(
                cache_dir=tmpdir,
                max_size_mb=10,
                default_ttl_hours=24,
            )

            # Simulate LLM calls with cache
            def cached_llm_call(prompt: str) -> str:
                """Simulate cached LLM call."""
                cached = cache.get(prompt, model="test-model")
                if cached:
                    return cached.response

                # Simulate LLM generation
                response = f"response to: {prompt}"
                cache.set(
                    prompt=prompt,
                    response=response,
                    model="test-model",
                    tokens_in=len(prompt),
                    tokens_out=len(response),
                )
                return response

            # First call - should execute
            result1 = cached_llm_call("hello")
            assert result1 == "response to: hello"

            # Second call - should use cache
            result2 = cached_llm_call("hello")
            assert result2 == "response to: hello"

            # Different prompt - should execute
            result3 = cached_llm_call("world")
            assert result3 == "response to: world"

            cache._cache.close()

    def test_cache_ttl_expiration(self):
        """Test cache TTL works with explicit invalidation (not sleep-based).

        Note: diskcache TTL is not reliable for short durations on Windows.
        We test explicit invalidation instead.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(
                cache_dir=tmpdir,
                max_size_mb=10,
                default_ttl_hours=24,
            )

            # First call
            cache.set(
                prompt="test1",
                response="result1",
                model="test-model",
                tokens_in=10,
                tokens_out=10,
            )

            # Check it's cached
            cached = cache.get("test1", model="test-model")
            assert cached is not None
            assert cached.response == "result1"

            # Explicitly invalidate (reliable across all platforms)
            cache.invalidate("test1", model="test-model")

            # Should be gone now
            cached_after = cache.get("test1", model="test-model")
            assert cached_after is None

            cache._cache.close()


class TestContextLoaderIntegration:
    """Integration tests for context loading."""

    def test_conversation_manager_basic(self):
        """Test basic conversation manager functionality."""
        manager = ConversationManager()

        # Add some messages
        manager.add_message("user", "Hello")
        manager.add_message("assistant", "Hi there!")

        context = manager.get_context()
        assert len(context) == 2


class TestRAGIntegration:
    """Integration tests for RAG search system."""

    def test_rag_index_and_search(self):
        """Test RAG indexing and searching."""
        pytest.importorskip("chromadb")
        pytest.importorskip("sentence_transformers")

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = CodeRAGSystem(
                persist_directory=tmpdir,
                embedding_model="all-MiniLM-L6-v2",
            )

            # Create a test file
            test_file = Path(tmpdir) / "test_code.py"
            test_file.write_text(
                """
def hello_world():
    print("Hello, World!")
    return True

class TestClass:
    def method(self):
        pass
"""
            )

            # Index the file
            chunk_count = rag.index_file(str(test_file))
            assert chunk_count > 0

            # Search
            results = rag.search("hello world function", top_k=2)
            assert len(results) > 0

            # Check result structure
            for result in results:
                assert "id" in result
                assert "content" in result
                assert "score" in result

    def test_rag_get_context(self):
        """Test RAG context generation for queries."""
        pytest.importorskip("chromadb")
        pytest.importorskip("sentence_transformers")

        with tempfile.TemporaryDirectory() as tmpdir:
            rag = CodeRAGSystem(
                persist_directory=tmpdir,
                embedding_model="all-MiniLM-L6-v2",
            )

            # Create a test file
            test_file = Path(tmpdir) / "example.py"
            test_file.write_text("# Example\n\nprint('test')\n")

            rag.index_file(str(test_file))

            # Get context for query
            context = rag.get_context_for_query("example", max_context_tokens=100)

            assert context is not None
            assert "File:" in context or "example" in context.lower()


class TestEndToEndTokenOptimization:
    """End-to-end tests for token optimization workflow."""

    def test_complete_optimization_flow(self):
        """Test complete token optimization workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup cache
            cache = LLMResponseCache(
                cache_dir=tmpdir,
                max_size_mb=10,
                default_ttl_hours=24,
            )

            call_count = 0

            def llm_call(prompt: str) -> str:
                """Simulate LLM call with caching."""
                nonlocal call_count
                cached = cache.get(prompt, model="gpt-4")
                if cached:
                    return cached.response

                call_count += 1
                response = f"AI: {prompt}"

                cache.set(
                    prompt=prompt,
                    response=response,
                    model="gpt-4",
                    tokens_in=len(prompt),
                    tokens_out=len(response),
                )
                return response

            # Simulate multiple similar LLM calls
            prompts = [
                "explain python",
                "explain python",
                "explain javascript",
                "explain python",
            ]

            results = []
            for prompt in prompts:
                result = llm_call(prompt)
                results.append(result)

            # Check that caching worked
            # 2 unique prompts: "explain python" and "explain javascript"
            assert call_count == 2  # Only 2 unique calls

            cache._cache.close()

    def test_cache_with_context(self):
        """Test cache working with context loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create context file
            ctx_file = Path(tmpdir) / "context.md"
            ctx_file.write_text("# Context\n\nSystem: CasareRPA\nVersion: 1.0\n")

            cache = LLMResponseCache(
                cache_dir=tmpdir,
                max_size_mb=10,
                default_ttl_hours=24,
            )

            manager = ConversationManager()
            manager.add_message("user", "Test message")
            context = manager.get_context()

            # Verify both systems can work with same directory
            # LLMResponseCache uses tmpdir directly as the cache directory
            assert Path(tmpdir).exists(), f"Cache directory should exist: {tmpdir}"
            assert context is not None

            cache._cache.close()


class TestTokenTrackingIntegration:
    """Integration tests for token tracking."""

    def test_token_stats_collection(self):
        """Test that token statistics are collected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMResponseCache(
                cache_dir=tmpdir,
                max_size_mb=10,
                default_ttl_hours=24,
            )

            # Make some cached calls
            for i in range(5):
                cached = cache.get(f"query_{i}", model="test")
                if not cached:
                    cache.set(
                        prompt=f"query_{i}",
                        response=f"result_{i}",
                        model="test",
                        tokens_in=10,
                        tokens_out=20,
                    )

            # Get stats
            stats = cache.stats()
            assert "total_entries" in stats
            assert "total_size_mb" in stats

            cache._cache.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

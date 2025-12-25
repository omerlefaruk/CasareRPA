"""Tests for RAG code search with ChromaDB."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Mock ChromaDB if not installed
try:
    from chromadb import ChromaDB

    CHROMADB_AVAILABLE = True
except ImportError:
    ChromaDB = None  # type: ignore
    CHROMADB_AVAILABLE = False


@pytest.fixture
def temp_persist_dir():
    """Create temporary persist directory for ChromaDB."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestCodeRAGSystem:
    """Tests for CodeRAGSystem."""

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_system_initialization(self, temp_persist_dir):
        """Test RAG system initializes correctly."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        # Mock embedding model (requires actual model)
        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            assert system.collection_name == "test_collection"
            assert system.persist_dir == temp_persist_dir

            # Clean up
            system.client.delete_collection("test_collection")

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_index_file(self, temp_persist_dir):
        """Test file indexing."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create temporary test file
            test_file = Path(temp_persist_dir) / "test.py"
            test_file.write_text(
                '''def hello_world():
    """Say hello."""
    print("Hello, World!")
    return 42
'''
            )

            # Mock embedding model
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Index the file
            count = system.index_files([str(test_file)])

            assert count == 1

            # Clean up
            system.client.delete_collection("test_collection")
            test_file.unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_index_multiple_files(self, temp_persist_dir):
        """Test indexing multiple files."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create temporary test files
            file1 = Path(temp_persist_dir) / "file1.py"
            file2 = Path(temp_persist_dir) / "file2.py"

            file1.write_text("def func1(): pass")
            file2.write_text("def func2(): pass")

            # Mock embedding model
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0], [3.0, 4.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            count = system.index_files([str(file1), str(file2)])

            assert count == 2

            # Clean up
            system.client.delete_collection("test_collection")
            file1.unlink()
            file2.unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_semantic_search(self, temp_persist_dir):
        """Test semantic search functionality."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create and index a test file
            test_file = Path(temp_persist_dir) / "test.py"
            test_file.write_text("def test_function(): pass")

            # Mock embedding model
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Index file
            system.index_files([str(test_file)])

            # Search for "test_function"
            results = system.search("test_function", top_k=3)

            assert len(results) == 1
            assert results[0]["file_path"] == str(test_file)

            # Clean up
            system.client.delete_collection("test_collection")
            test_file.unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_hybrid_search(self, temp_persist_dir):
        """Test hybrid search (semantic + keyword)."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create test files
            file1 = Path(temp_persist_dir) / "data_processing.py"
            file2 = Path(temp_persist_dir) / "api_handler.py"

            file1.write_text("def process_data(): pass")
            file2.write_text("def handle_api(): pass")

            # Mock embedding model
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0], [3.0, 4.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Index files
            system.index_files([str(file1), str(file2)])

            # Search with query that matches one file
            results = system.search("process", top_k=5)

            # Should find both files (one has "process" in name)
            assert len(results) >= 1
            file_paths = [r["file_path"] for r in results]
            assert str(file1) in file_paths

            # Clean up
            system.client.delete_collection("test_collection")
            file1.unlink()
            file2.unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_top_k_limit(self, temp_persist_dir):
        """Test top_k parameter limits results."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create multiple test files
            files = []
            for i in range(5):
                test_file = Path(temp_persist_dir) / f"file{i}.py"
                test_file.write_text(f"def func{i}(): pass")
                files.append(str(test_file))

            # Mock embedding model
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0], [4.0, 5.0], [6.0, 7.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Index files
            system.index_files(files)

            # Request top_k=3
            results = system.search("func", top_k=3)

            assert len(results) == 3

            # Clean up
            system.client.delete_collection("test_collection")
            for test_file in files:
                Path(test_file).unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_persistence_across_instances(self, temp_persist_dir):
        """Test that indexed data persists across instances."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create and index a file with first instance
            test_file = Path(temp_persist_dir) / "test.py"
            test_file.write_text("def persisted_function(): pass")

            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system1 = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )
            system1.index_files([str(test_file)])

            # Create second instance (should load existing data)
            system2 = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Search with second instance
            results = system2.search("persisted_function", top_k=3)

            assert len(results) == 1
            assert results[0]["file_path"] == str(test_file)

            # Clean up
            system1.client.delete_collection("test_collection")
            test_file.unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_clear_collection(self, temp_persist_dir):
        """Test clearing collection."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Add some data
            system.client.get_or_create_collection("test_collection").add(
                documents=["test"],
                ids=["test"],
                embeddings=[[1.0, 2.0, 3.0]],
            )

            # Verify data exists
            collection = system.client.get_collection("test_collection")
            assert collection.count() == 1

            # Clear collection
            system.clear_collection()

            # Verify data is gone
            collection = system.client.get_collection("test_collection")
            assert collection.count() == 0

            # Clean up
            system.client.delete_collection("test_collection")


class TestRAGUtilities:
    """Tests for RAG utility functions."""

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_chunk_text(self):
        """Test text chunking."""
        from casare_rpa.utils.rag.code_search import chunk_text

        text = "This is a long piece of text that should be split into multiple chunks."

        chunks = chunk_text(text, max_chunk_size=50, overlap=10)

        assert len(chunks) > 1
        # First chunk should have about 50 characters
        assert len(chunks[0]) <= 50 + 10  # Allow for overlap
        assert all(isinstance(c, str) for c in chunks)

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_extract_functions_and_classes(self):
        """Test extracting functions and classes from code."""
        from casare_rpa.utils.rag.code_search import extract_functions_and_classes

        code = '''
def function1():
    """Function one."""
    pass

class Class1:
    """Class one."""
    pass

def function2():
    """Function two."""
    pass

class Class2:
    """Class two."""
    pass
'''

        functions, classes = extract_functions_and_classes(code)

        assert len(functions) == 2
        assert "function1" in functions
        assert "function2" in functions

        assert len(classes) == 2
        assert "Class1" in classes
        assert "Class2" in classes

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_compute_similarity(self):
        """Test computing similarity between embeddings."""
        from casare_rpa.utils.rag.code_search import compute_similarity

        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [1.0, 0.0, 1.0]

        similarity = compute_similarity(embedding1, embedding2)

        assert 0.0 <= similarity <= 1.0

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_empty_query_handling(self, temp_persist_dir):
        """Test handling of empty queries."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            # Create test file
            test_file = Path(temp_persist_dir) / "test.py"
            test_file.write_text("def test_function(): pass")

            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Index file
            system.index_files([str(test_file)])

            # Search with empty query
            results = system.search("", top_k=5)

            assert len(results) == 0

            # Clean up
            system.client.delete_collection("test_collection")
            test_file.unlink()

    @pytest.mark.skipif(not CHROMADB_AVAILABLE, reason="ChromaDB not installed")
    def test_nonexistent_file_error(self, temp_persist_dir):
        """Test error handling for nonexistent files."""
        from casare_rpa.utils.rag.code_search import CodeRAGSystem

        with patch("casare_rpa.utils.rag.code_search.SentenceTransformer") as mock_transformer:
            mock_instance = Mock()
            mock_instance.encode.return_value = [[1.0, 2.0, 3.0]]
            mock_transformer.return_value = mock_instance

            system = CodeRAGSystem(
                persist_dir=temp_persist_dir,
                collection_name="test_collection",
                embedding_model_name="all-MiniLM-L6-v2",
            )

            # Try to index nonexistent file
            count = system.index_files(["nonexistent.py"])

            assert count == 0

            # Clean up
            system.client.delete_collection("test_collection")

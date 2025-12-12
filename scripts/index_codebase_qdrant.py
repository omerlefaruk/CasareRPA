"""
Index CasareRPA codebase into Qdrant for semantic search.

Usage:
    python scripts/index_codebase_qdrant.py

This script:
1. Walks through the src/ directory
2. Chunks Python files intelligently (by class/function)
3. Stores embeddings in Qdrant for semantic search via MCP
"""

import os
import re
import ast
from pathlib import Path
from typing import Generator

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from fastembed import TextEmbedding
except ImportError:
    print("Installing required packages...")
    import subprocess

    subprocess.check_call(["pip", "install", "qdrant-client", "fastembed"])
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from fastembed import TextEmbedding


# Configuration
QDRANT_PATH = Path(__file__).parent.parent / ".qdrant"
COLLECTION_NAME = "casare_codebase"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SRC_DIR = Path(__file__).parent.parent / "src"

# File patterns to index
INCLUDE_PATTERNS = ["*.py"]
EXCLUDE_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".qdrant"}
EXCLUDE_FILES = {"__init__.py"}  # Usually just imports


def extract_code_chunks(filepath: Path) -> Generator[dict, None, None]:
    """Extract meaningful chunks from a Python file."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Skipping {filepath}: {e}")
        return

    try:
        tree = ast.parse(content)
    except SyntaxError:
        # If AST parsing fails, treat whole file as one chunk
        yield {
            "type": "file",
            "name": filepath.stem,
            "path": str(filepath.relative_to(SRC_DIR.parent)),
            "content": content[:2000],  # Limit size
            "line_start": 1,
            "line_end": len(content.splitlines()),
        }
        return

    lines = content.splitlines()

    # Extract module docstring
    if ast.get_docstring(tree):
        yield {
            "type": "module",
            "name": filepath.stem,
            "path": str(filepath.relative_to(SRC_DIR.parent)),
            "content": ast.get_docstring(tree),
            "line_start": 1,
            "line_end": 10,
        }

    # Extract classes and functions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Get class definition with docstring
            start = node.lineno - 1
            end = min(start + 50, len(lines))  # First 50 lines of class
            chunk_content = "\n".join(lines[start:end])

            docstring = ast.get_docstring(node) or ""

            yield {
                "type": "class",
                "name": node.name,
                "path": str(filepath.relative_to(SRC_DIR.parent)),
                "content": f"class {node.name}\n\n{docstring}\n\n{chunk_content}",
                "line_start": node.lineno,
                "line_end": end + 1,
            }

        elif isinstance(node, ast.FunctionDef) or isinstance(
            node, ast.AsyncFunctionDef
        ):
            # Skip private methods except execute
            if node.name.startswith("_") and node.name not in (
                "__init__",
                "_define_ports",
            ):
                continue

            start = node.lineno - 1
            end = min(start + 30, len(lines))  # First 30 lines of function
            chunk_content = "\n".join(lines[start:end])

            docstring = ast.get_docstring(node) or ""
            func_type = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"

            yield {
                "type": "function",
                "name": node.name,
                "path": str(filepath.relative_to(SRC_DIR.parent)),
                "content": f"{func_type} {node.name}\n\n{docstring}\n\n{chunk_content}",
                "line_start": node.lineno,
                "line_end": end + 1,
            }


def collect_python_files(src_dir: Path) -> Generator[Path, None, None]:
    """Collect all Python files to index."""
    for pattern in INCLUDE_PATTERNS:
        for filepath in src_dir.rglob(pattern):
            # Skip excluded directories
            if any(part in EXCLUDE_DIRS for part in filepath.parts):
                continue
            # Skip excluded files
            if filepath.name in EXCLUDE_FILES:
                continue
            yield filepath


def main():
    print("Indexing CasareRPA codebase into Qdrant")
    print(f"  Source: {SRC_DIR}")
    print(f"  Qdrant path: {QDRANT_PATH}")
    print(f"  Collection: {COLLECTION_NAME}")
    print()

    # Ensure qdrant directory exists
    QDRANT_PATH.mkdir(parents=True, exist_ok=True)

    # Initialize embedding model
    print("Loading embedding model...")
    embedding_model = TextEmbedding(EMBEDDING_MODEL)

    # Get embedding dimension
    test_embedding = list(embedding_model.embed(["test"]))[0]
    vector_size = len(test_embedding)
    print(f"  Embedding dimension: {vector_size}")

    # Initialize Qdrant client with local storage
    print("Initializing Qdrant...")
    client = QdrantClient(path=str(QDRANT_PATH))

    # Recreate collection (fresh index)
    if client.collection_exists(COLLECTION_NAME):
        print(f"  Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)

    print(f"  Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )

    # Collect all chunks
    print("\nExtracting code chunks...")
    chunks = []
    file_count = 0

    for filepath in collect_python_files(SRC_DIR):
        file_count += 1
        print(f"  Processing: {filepath.relative_to(SRC_DIR.parent)}")

        for chunk in extract_code_chunks(filepath):
            chunks.append(chunk)

    print(f"\nFound {len(chunks)} chunks from {file_count} files")

    # Generate embeddings and upsert in batches
    print("\nGenerating embeddings and upserting...")
    batch_size = 100
    total_points = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        # Create text for embedding (combine type, name, and content)
        texts = [
            f"{c['type']} {c['name']} in {c['path']}: {c['content'][:500]}"
            for c in batch
        ]

        # Generate embeddings
        embeddings = list(embedding_model.embed(texts))

        # Create points
        points = [
            PointStruct(
                id=i + j,
                vector=embeddings[j].tolist(),
                payload={
                    "type": batch[j]["type"],
                    "name": batch[j]["name"],
                    "path": batch[j]["path"],
                    "content": batch[j]["content"],
                    "line_start": batch[j]["line_start"],
                    "line_end": batch[j]["line_end"],
                },
            )
            for j in range(len(batch))
        ]

        # Upsert to Qdrant
        client.upsert(collection_name=COLLECTION_NAME, points=points)
        total_points += len(points)
        print(f"  Upserted {total_points}/{len(chunks)} points")

    print("\nIndexing complete!")
    print(f"  Total points: {total_points}")
    print(f"  Collection: {COLLECTION_NAME}")
    print("\nYou can now use Qdrant MCP for semantic search.")
    print("Restart Claude Code to load the new MCP server.")


if __name__ == "__main__":
    main()

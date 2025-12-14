"""
Index CasareRPA codebase into Qdrant for semantic search.

Usage:
    python scripts/index_codebase_qdrant.py

This script:
1. Walks through the src/ directory
2. Chunks Python files intelligently (by class/function)
3. Extracts rich metadata for better AI retrieval
4. Stores embeddings in Qdrant for semantic search via MCP

AI-HINT: This script creates the semantic search index used by qdrant-find.
AI-CONTEXT: Run after significant code changes to update the index.
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
QDRANT_PATH = Path(__file__).parent.parent / ".qdrant_new"
COLLECTION_NAME = "casare_codebase"
# Must match fastembed model naming for MCP server compatibility
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# Vector name used by mcp-server-qdrant (fastembed naming convention)
VECTOR_NAME = "fast-all-minilm-l6-v2"
SRC_DIR = Path(__file__).parent.parent / "src"

# File patterns to index
INCLUDE_PATTERNS = ["*.py"]
EXCLUDE_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".qdrant"}
EXCLUDE_FILES = {"__init__.py"}  # Usually just imports


def _detect_layer(filepath: Path) -> str:
    """Detect which DDD layer a file belongs to."""
    path_str = str(filepath).lower()
    if "/domain/" in path_str or "\\domain\\" in path_str:
        return "domain"
    elif "/application/" in path_str or "\\application\\" in path_str:
        return "application"
    elif "/infrastructure/" in path_str or "\\infrastructure\\" in path_str:
        return "infrastructure"
    elif "/presentation/" in path_str or "\\presentation\\" in path_str:
        return "presentation"
    elif "/nodes/" in path_str or "\\nodes\\" in path_str:
        return "nodes"
    return "other"


def _detect_category(filepath: Path, class_name: str = "") -> str:
    """Detect the category/purpose of a file or class."""
    path_str = str(filepath).lower()
    name_lower = class_name.lower()

    # Node categories
    if "browser" in path_str or "browser" in name_lower:
        return "browser"
    elif "desktop" in path_str or "desktop" in name_lower:
        return "desktop"
    elif "http" in path_str or "http" in name_lower:
        return "http"
    elif "control_flow" in path_str or "if" in name_lower or "loop" in name_lower:
        return "control_flow"
    elif "event" in path_str or "event" in name_lower:
        return "events"
    elif "visual" in path_str:
        return "visual_nodes"
    elif "canvas" in path_str:
        return "canvas"
    elif "ui" in path_str:
        return "ui"
    elif "test" in path_str:
        return "tests"
    return "general"


def _extract_base_classes(node: ast.ClassDef) -> list[str]:
    """Extract base class names from a class definition."""
    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(base.attr)
    return bases


def _extract_decorators(node) -> list[str]:
    """Extract decorator names from a class or function."""
    decorators = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            decorators.append(dec.id)
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Name):
                decorators.append(dec.func.id)
            elif isinstance(dec.func, ast.Attribute):
                decorators.append(dec.func.attr)
    return decorators


def _has_ai_hint(content: str) -> bool:
    """Check if content contains AI-HINT comment."""
    return "AI-HINT" in content or "AI-CONTEXT" in content or "AI-WARNING" in content


def extract_code_chunks(filepath: Path) -> Generator[dict, None, None]:
    """Extract meaningful chunks from a Python file with rich metadata."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Skipping {filepath}: {e}")
        return

    layer = _detect_layer(filepath)
    rel_path = str(filepath.relative_to(SRC_DIR.parent))

    try:
        tree = ast.parse(content)
    except SyntaxError:
        # If AST parsing fails, treat whole file as one chunk
        yield {
            "type": "file",
            "name": filepath.stem,
            "path": rel_path,
            "content": content[:2000],  # Limit size
            "line_start": 1,
            "line_end": len(content.splitlines()),
            "layer": layer,
            "category": _detect_category(filepath),
            "has_ai_hint": _has_ai_hint(content[:2000]),
            "exported": False,
        }
        return

    lines = content.splitlines()

    # Extract module docstring
    module_docstring = ast.get_docstring(tree)
    if module_docstring:
        yield {
            "type": "module",
            "name": filepath.stem,
            "path": rel_path,
            "content": module_docstring,
            "line_start": 1,
            "line_end": 10,
            "layer": layer,
            "category": _detect_category(filepath),
            "has_ai_hint": _has_ai_hint(module_docstring),
            "exported": False,
        }

    # Extract classes and functions
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Get class definition with docstring
            start = node.lineno - 1
            end = min(start + 50, len(lines))  # First 50 lines of class
            chunk_content = "\n".join(lines[start:end])

            docstring = ast.get_docstring(node) or ""
            base_classes = _extract_base_classes(node)
            decorators = _extract_decorators(node)

            # Determine if it's a node class
            is_node = (
                any(
                    b in ["BaseNode", "BrowserBaseNode", "VisualNodeBase"]
                    for b in base_classes
                )
                or "node" in decorators
            )

            yield {
                "type": "class",
                "name": node.name,
                "path": rel_path,
                "content": f"class {node.name}\n\n{docstring}\n\n{chunk_content}",
                "line_start": node.lineno,
                "line_end": end + 1,
                "layer": layer,
                "category": _detect_category(filepath, node.name),
                "base_classes": base_classes,
                "decorators": decorators,
                "is_node": is_node,
                "has_ai_hint": _has_ai_hint(chunk_content),
                "exported": not node.name.startswith("_"),
            }

        elif isinstance(node, ast.FunctionDef) or isinstance(
            node, ast.AsyncFunctionDef
        ):
            # Skip private methods except key ones
            if node.name.startswith("_") and node.name not in (
                "__init__",
                "_define_ports",
                "__call__",
            ):
                continue

            start = node.lineno - 1
            end = min(start + 30, len(lines))  # First 30 lines of function
            chunk_content = "\n".join(lines[start:end])

            docstring = ast.get_docstring(node) or ""
            func_type = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            decorators = _extract_decorators(node)

            yield {
                "type": "function",
                "name": node.name,
                "path": rel_path,
                "content": f"{func_type} {node.name}\n\n{docstring}\n\n{chunk_content}",
                "line_start": node.lineno,
                "line_end": end + 1,
                "layer": layer,
                "category": _detect_category(filepath),
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": decorators,
                "has_ai_hint": _has_ai_hint(chunk_content),
                "exported": not node.name.startswith("_"),
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
    print(f"  Vector name: {VECTOR_NAME}")
    # Use named vector to match mcp-server-qdrant expectations
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            VECTOR_NAME: VectorParams(size=vector_size, distance=Distance.COSINE)
        },
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

        # Create text for embedding (combine type, name, layer, and content)
        texts = []
        for c in batch:
            # Build rich embedding text for better semantic search
            parts = [
                f"{c['type']} {c['name']}",
                f"in {c['path']}",
                f"layer: {c.get('layer', 'unknown')}",
                f"category: {c.get('category', 'general')}",
            ]
            if c.get("base_classes"):
                parts.append(f"extends: {', '.join(c['base_classes'])}")
            if c.get("decorators"):
                parts.append(f"decorators: {', '.join(c['decorators'])}")
            if c.get("is_node"):
                parts.append("(automation node)")
            if c.get("is_async"):
                parts.append("(async)")
            parts.append(c["content"][:500])
            texts.append(" | ".join(parts))

        # Generate embeddings
        embeddings = list(embedding_model.embed(texts))

        # Create points with named vector for mcp-server-qdrant compatibility
        points = []
        for j in range(len(batch)):
            chunk = batch[j]
            payload = {
                # MCP server expects "document" field for content
                "document": chunk["content"],
                "type": chunk["type"],
                "name": chunk["name"],
                "path": chunk["path"],
                "line_start": chunk["line_start"],
                "line_end": chunk["line_end"],
                # New rich metadata for AI retrieval
                "layer": chunk.get("layer", "unknown"),
                "category": chunk.get("category", "general"),
                "exported": chunk.get("exported", True),
                "has_ai_hint": chunk.get("has_ai_hint", False),
            }
            # Add optional fields if present
            if chunk.get("base_classes"):
                payload["base_classes"] = chunk["base_classes"]
            if chunk.get("decorators"):
                payload["decorators"] = chunk["decorators"]
            if chunk.get("is_node"):
                payload["is_node"] = chunk["is_node"]
            if chunk.get("is_async"):
                payload["is_async"] = chunk["is_async"]

            points.append(
                PointStruct(
                    id=i + j,
                    vector={VECTOR_NAME: embeddings[j].tolist()},
                    payload=payload,
                )
            )

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

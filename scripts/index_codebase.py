"""
Index CasareRPA codebase into ChromaDB for semantic search.

Usage:
    python scripts/index_codebase.py

This script:
1. Walks through the src/ directory
2. Chunks Python files intelligently (by class/function)
3. Extracts rich metadata for better AI retrieval
4. Stores embeddings in ChromaDB via the internal VectorStore.
"""

import os
import ast
import json
import asyncio
import hashlib
from pathlib import Path
from typing import Generator, List, Dict, Any

from loguru import logger
from fastembed import TextEmbedding

# Add project root to path
import sys

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from casare_rpa.infrastructure.ai.vector_store import get_vector_store, Document
from casare_rpa.infrastructure.ai.embedding_manager import get_embedding_manager

# Configuration
COLLECTION_NAME = "casare_codebase"
SRC_DIR = project_root / "src"
PERSIST_PATH = str(project_root / ".chroma")
CACHE_FILE = project_root / ".chroma" / "index_cache.json"


def get_file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_cache() -> Dict[str, str]:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, str]):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


# File patterns to index
INCLUDE_PATTERNS = ["*.py"]
EXCLUDE_DIRS = {
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "node_modules",
    ".qdrant",
    ".chroma",
}
EXCLUDE_FILES = {"__init__.py"}


def _detect_layer(filepath: Path) -> str:
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
    path_str = str(filepath).lower()
    name_lower = class_name.lower()
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


def _extract_base_classes(node: ast.ClassDef) -> List[str]:
    bases = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            bases.append(base.id)
        elif isinstance(base, ast.Attribute):
            bases.append(base.attr)
    return bases


def _extract_decorators(node) -> List[str]:
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


def extract_code_chunks(filepath: Path) -> Generator[Dict[str, Any], None, None]:
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        logger.warning(f"Skipping {filepath}: {e}")
        return

    layer = _detect_layer(filepath)
    rel_path = str(filepath.relative_to(SRC_DIR.parent))

    try:
        tree = ast.parse(content)
    except SyntaxError:
        yield {
            "type": "file",
            "name": filepath.stem,
            "path": rel_path,
            "content": content[:2000],
            "line_start": 1,
            "line_end": len(content.splitlines()),
            "layer": layer,
            "category": _detect_category(filepath),
        }
        return

    lines = content.splitlines()

    # Module docstring
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
        }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            start = node.lineno - 1
            end = min(start + 50, len(lines))
            chunk_content = "\n".join(lines[start:end])
            docstring = ast.get_docstring(node) or ""
            base_classes = _extract_base_classes(node)
            decorators = _extract_decorators(node)

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
            }

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_") and node.name not in (
                "__init__",
                "_define_ports",
            ):
                continue

            start = node.lineno - 1
            end = min(start + 30, len(lines))
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
            }


def collect_python_files(src_dir: Path) -> Generator[Path, None, None]:
    for pattern in INCLUDE_PATTERNS:
        for filepath in src_dir.rglob(pattern):
            if any(part in EXCLUDE_DIRS for part in filepath.parts):
                continue
            if filepath.name in EXCLUDE_FILES:
                continue
            yield filepath


async def main():
    logger.info("Indexing CasareRPA codebase into ChromaDB (Full Local)")

    # Ensure Chroma directory exists
    Path(PERSIST_PATH).mkdir(parents=True, exist_ok=True)

    vector_store = get_vector_store(persist_path=PERSIST_PATH)
    cache = load_cache()
    new_cache = {}

    logger.info("Loading local embedding model (fastembed)...")
    embed_model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    logger.info(f"Extracting code chunks from {SRC_DIR}...")
    all_chunks = []
    file_count = 0
    skipped_count = 0

    for filepath in collect_python_files(SRC_DIR):
        file_count += 1
        rel_path = str(filepath.relative_to(SRC_DIR.parent))
        file_hash = get_file_hash(filepath)

        if cache.get(rel_path) == file_hash:
            skipped_count += 1
            new_cache[rel_path] = file_hash
            continue

        file_chunks = list(extract_code_chunks(filepath))
        if file_chunks:
            all_chunks.extend(file_chunks)
            new_cache[rel_path] = file_hash

    if skipped_count:
        logger.info(f"Skipped {skipped_count} unchanged files.")

    if not all_chunks:
        logger.info("Nothing to update.")
        save_cache(new_cache)
        return

    logger.info(f"Indexing {len(all_chunks)} new/changed chunks...")

    # Generate embeddings and upsert in batches
    batch_size = 50
    total_processed = 0

    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]

        # Build embedding texts
        texts = []
        for c in batch:
            parts = [
                f"{c['type']} {c['name']} in {c['path']}",
                f"layer: {c['layer']}",
                c["content"][:300],
            ]
            texts.append(" | ".join(parts))

        try:
            # Generate embeddings
            embeddings = list(embed_model.embed(texts))

            # Prepare documents for ChromaDB
            documents = []
            for j, chunk in enumerate(batch):
                # Use a stable hash-based ID for chunks to allow updates without duplicates
                # Adding line_start to avoid collisions for same-named entities in same file
                ID_BASE = f"{chunk['path']}:{chunk['type']}:{chunk['name']}:{chunk['line_start']}"
                chunk_id = hashlib.md5(ID_BASE.encode()).hexdigest()

                # Cleanup metadata for ChromaDB (must be str, int, float, or bool)
                metadata = {
                    "type": str(chunk.get("type", "")),
                    "name": str(chunk.get("name", "")),
                    "path": str(chunk.get("path", "")),
                    "layer": str(chunk.get("layer", "")),
                    "category": str(chunk.get("category", "")),
                    "line_start": int(chunk.get("line_start", 0)),
                    "line_end": int(chunk.get("line_end", 0)),
                }

                documents.append(
                    Document(
                        id=chunk_id,
                        content=chunk["content"],
                        metadata=metadata,
                        embedding=embeddings[j].tolist(),
                    )
                )

            await vector_store.upsert_documents(documents, collection=COLLECTION_NAME)
            total_processed += len(batch)
            logger.info(f"Indexed {total_processed}/{len(all_chunks)} chunks...")

        except Exception as e:
            logger.error(f"Batch processing failed at {i}: {e}")
            continue

    save_cache(new_cache)
    logger.info("Indexing complete!")


if __name__ == "__main__":
    asyncio.run(main())
